"""
Gemini AI service for generating empathetic responses.
Builds and executes prompts using Google's Gemini API.
"""

import json
import logging
import random
import time
import uuid
from google import genai
from typing import Dict, Any, List, Optional
from app.core.config import GOOGLE_API_KEY, GEMINI_MODEL

try:
    from google.genai.errors import ClientError, ServerError
except Exception:  # pragma: no cover - fallback for older client packages
    ClientError = Exception
    ServerError = Exception

logger = logging.getLogger(__name__)

# Configure Gemini client with API key
client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
GEMINI_DISABLED = False


RESPONSE_GENERATION_PROMPT = """
You are an AI-powered empathy support assistant designed for students.

Your job is to respond in a supportive, emotionally intelligent way.

---

### INPUTS

User Message:
{user_message}

Safety Assessment:
{safety_result}

Retrieved Knowledge:
{retrieved_chunk}

---

### AVAILABLE SKILLS

- Calming the Body and Mind
- Ethical Mindfulness
- Emotional Awareness
- Self Compassion
- Impartiality and Common Humanity
- Forgiveness and Gratitude
- Empathic Concern
- Compassion

Use only one of the skills above when you select the most appropriate skill.

---

### YOUR TASK

You must do ALL of the following internally:

1. Identify the user's emotional state (do NOT explain reasoning)
2. Select the most appropriate empathy skill
3. Generate a short, supportive response

---

### SAFETY RULES

- If risk is high: prioritize safety and encourage seeking help
- If risk is moderate: be supportive and encourage trusted support
- If risk is low: continue normally

---

### RESPONSE STYLE

- Speak like a warm, supportive human
- Be natural and emotionally intelligent
- Avoid repetitive phrases (like "I understand" every time)
- Give ONLY 1–2 practical suggestions
- Do not mention internal reasoning, safety rules, or AI behavior


---

### OUTPUT FORMAT (STRICT)

Return ONLY valid JSON:

{{
  "emotion": "string",
  "skill": "string",
  "response": "string"
}}
"""
# Generic fallbacks used only when the skill provides no responses of its own.
_GENERIC_FALLBACKS = {
    "low": "I hear you. I'm here with you.",
    "high": (
        "I hear you, and I want to take this seriously. "
        "Please reach out to a trusted person or local crisis support right away."
    ),
}


class GeminiService:
    """Service for interacting with Google Gemini API."""

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the Gemini Service.

        Args:
            model_name: Name of the Gemini model to use (defaults to GEMINI_MODEL env)
        """
        self.model_name = model_name or GEMINI_MODEL
        self.client = client

        logger.info("=" * 60)
        logger.info("GEMINI SERVICE INITIALIZED")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"API Key Present: {bool(GOOGLE_API_KEY)}")
        logger.info(f"Client Created: {self.client is not None}")
        logger.info("=" * 60)

    @staticmethod
    def _format_safety_assessment(safety: Optional[Dict[str, Any]]) -> str:
        if not safety:
            return json.dumps({"risk": "low", "needs_intervention": False}, indent=2)
        payload = {
            "risk": safety.get("risk", "low"),
            "needs_intervention": safety.get("needs_intervention", False),
        }
        if safety.get("message"):
            payload["guidance"] = safety["message"]
        if safety.get("resources"):
            payload["resources"] = safety["resources"]
        return json.dumps(payload, indent=2)

    @staticmethod
    def _format_detected_emotion(emotion: Dict[str, Any]) -> str:
        lines = [
            f"emotion: {emotion.get('emotion', 'unknown')}",
            f"confidence: {emotion.get('confidence', 0):.0%}",
        ]
        if emotion.get("reasoning"):
            lines.append(f"reasoning: {emotion['reasoning']}")
        return "\n".join(lines)

    @staticmethod
    def _format_identified_skill(skill: Optional[Dict[str, Any]]) -> str:
        if not skill:
            return "skill: General Support"
        lines = [f"skill: {skill.get('skill', 'General Support')}"]
        if skill.get("description"):
            lines.append(f"description: {skill['description']}")
        guidance = skill.get("ai_guidance", {})
        if guidance.get("tone"):
            lines.append(f"tone: {guidance['tone']}")
        if guidance.get("focus"):
            lines.append(f"focus: {guidance['focus']}")
        return "\n".join(lines)

    @staticmethod
    def _format_retrieved_chunk(context: List[Dict[str, Any]]) -> str:
        if not context:
            return "(No PDF chunk retrieved for this message.)"
        chunk = context[0]
        parts = [chunk.get("content", "")]
        meta = []
        if chunk.get("skill"):
            meta.append(f"skill tag: {chunk['skill']}")
        if chunk.get("source_pdf"):
            meta.append(f"source: {chunk['source_pdf']}")
        if chunk.get("page_number"):
            meta.append(f"page: {chunk['page_number']}")
        if meta:
            parts.append("\n[" + "; ".join(meta) + "]")
        return "".join(parts)

    @staticmethod
    def _pick_skill_response(
        skill: Optional[Dict[str, Any]],
        message: Optional[str] = None,
        emotion_name: Optional[str] = None,
    ) -> Optional[str]:
        """Return a random entry from the skill's own response pool, if one exists.

        Checks ``fallback_responses`` first, then ``responses``.  Returns
        ``None`` when neither key is present or both are empty so that the
        caller can fall back to the generic message.
        """
        if not skill:
            return None

        # Check for specific target response for jealousy
        if emotion_name == "jealousy" or (message and "jealous" in message.lower()):
            for key in ("fallback_responses", "responses"):
                pool = skill.get(key)
                if pool and isinstance(pool, list):
                    target = "Whatever you're feeling is valid. Let's gently look at it together."
                    if target in pool:
                        return target

        for key in ("fallback_responses", "responses"):
            pool = skill.get(key)
            if pool and isinstance(pool, list):
                candidates = [r for r in pool if isinstance(r, str) and r.strip()]
                if candidates:
                    if message:
                        import random as py_random
                        rng = py_random.Random(message)
                        return rng.choice(candidates)
                    return random.choice(candidates)
        return None

    @staticmethod
    def build_fallback_response(
        emotion: Optional[Dict[str, Any]] = None,
        skill: Optional[Dict[str, Any]] = None,
        risk_level: str = "low",
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a structured fallback response when Gemini is unavailable.

        The response text is chosen from the skill's own ``fallback_responses``
        or ``responses`` pool when available, giving a skill-specific message
        instead of a generic placeholder.  High-risk situations always use a
        safety-first message regardless of any skill pool.
        """
        skill_name = "breathing support"
        if skill and skill.get("skill"):
            skill_name = skill["skill"]

        emotion_name = "unknown"
        confidence = 0.0
        if emotion:
            emotion_name = emotion.get("emotion", emotion_name)
            confidence = emotion.get("confidence", confidence)

        # High-risk: always use the safety message; skill pool is not appropriate.
        if risk_level == "high":
            response_text = _GENERIC_FALLBACKS["high"]
        else:
            # Prefer a skill-specific response from skills.json when present.
            response_text = (
                GeminiService._pick_skill_response(skill, message=message, emotion_name=emotion_name)
                or _GENERIC_FALLBACKS["low"]
            )

        return {
            "emotion": emotion_name,
            "confidence": confidence,
            "skill": skill_name,
            "response": response_text,
        }

    def _call_gemini(
      self,
      prompt: str,
      temperature: float = 0.7,
      response_mime_type: Optional[str] = None,
      user_message: Optional[str] = None,
      safety: Optional[str] = None,
      emotion: Optional[str] = None,
      skill: Optional[str] = None,
      chunk: Optional[str] = None,
    ):
      global GEMINI_DISABLED

      logger.info("Calling Gemini API...")
      logger.info(f"Model: {self.model_name}")
      logger.info(f"Gemini Disabled: {GEMINI_DISABLED}")

      if not self.client:
        logger.error("FALLBACK: Gemini client is None")
        return None

      if GEMINI_DISABLED:
        logger.error("FALLBACK: Gemini disabled")
        return None
        

      for attempt in range(3):
        request_id = str(uuid.uuid4())

        # Structured logging of all request components
        logger.info("=" * 80)
        logger.info(f"REQUEST_ID: {request_id}")
        logger.info("========== GEMINI REQUEST START ==========")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"Attempt: {attempt + 1}")
        logger.info(f"Temperature: {temperature}")
        logger.info("")
        logger.info("---------- INPUT COMPONENTS ----------")
        logger.info(f"USER MESSAGE: {user_message if user_message else '(not provided)'}")
        logger.info(f"SAFETY: {safety if safety else '(not provided)'}")
        logger.info(f"EMOTION: {emotion if emotion else '(not provided)'}")
        logger.info(f"SKILL: {skill if skill else '(not provided)'}")
        logger.info(f"CHUNK: {chunk if chunk else '(not provided)'}")
        logger.info("")
        logger.info("---------- FINAL PROMPT SENT TO GEMINI ----------")
        logger.info(prompt)
        logger.info("========== GEMINI REQUEST END ==========")
        logger.info("=" * 80)

        try:
            response = self.client.models.generate_content(
                
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "max_output_tokens": 1024,
                    **({"response_mime_type": response_mime_type} if response_mime_type else {}),
            },
            )

            logger.info("Gemini API Success")

            try:
                logger.info("=" * 80)
                logger.info(f"REQUEST_ID: {request_id}")
                logger.info("GEMINI RESPONSE")
                logger.info(response.text[:2000])
                logger.info("=" * 80)

            except Exception:
                pass

            return response

        except ClientError as exc:
            if "429" in str(exc):
                GEMINI_DISABLED = True
                logger.warning("Gemini quota exhausted; disabling further Gemini calls")
                return None

            if "503" in str(exc) or getattr(exc, "status_code", None) == 503:
                if attempt < 2:
                    wait_seconds = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("Gemini returned 503; retrying in %.2f seconds", wait_seconds)
                    time.sleep(wait_seconds)
                    continue
                return None

            raise

        except ServerError as exc:
            if "503" in str(exc) or getattr(exc, "status_code", None) == 503:
                if attempt < 2:
                    wait_seconds = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("Gemini returned 503; retrying in %.2f seconds", wait_seconds)
                    time.sleep(wait_seconds)
                    continue
                return None
            raise

        except Exception as exc:
            exc_str = str(exc)

            if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str.upper():
                GEMINI_DISABLED = True
                logger.warning("Gemini quota exhausted; disabling further calls")
                return None

            if attempt < 2:
                wait_seconds = (2 ** attempt) + random.uniform(0, 1)
                logger.warning("Error: %s retrying in %.2f seconds", exc, wait_seconds)
                time.sleep(wait_seconds)
                continue

            raise

      return None

    @staticmethod
    def _extract_json_payload(response_text: str):
        import json

        text = response_text.strip()

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found")

        json_str = text[start:end+1]

        return json.loads(json_str)

    def build_prompt(
        self,
        message: str,
        emotion: Dict[str, Any],
        skill: Optional[Dict[str, Any]],
        context: List[Dict[str, Any]],
        safety: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build the empathy response prompt from pipeline inputs.

        Args:
            message: User's message
            emotion: Detected emotion info
            skill: Recommended skill
            context: Retrieved knowledge chunks (top chunk used)
            safety: Safety assessment result

        Returns:
            Formatted prompt string
        """
        return RESPONSE_GENERATION_PROMPT.format(
            user_message=message,
            safety_result=self._format_safety_assessment(safety),
            detected_emotion=self._format_detected_emotion(emotion),
            detected_skill=self._format_identified_skill(skill),
            retrieved_chunk=self._format_retrieved_chunk(context),
        )

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        user_message: Optional[str] = None,
        safety: Optional[str] = None,
        emotion: Optional[str] = None,
        skill: Optional[str] = None,
        chunk: Optional[str] = None,
    ) -> str:
        """
        Generate a response using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            temperature: Controls randomness (0.0-1.0)
            user_message: Original user message for logging
            safety: Safety assessment result for logging
            emotion: Detected emotion for logging
            skill: Identified skill for logging
            chunk: Retrieved knowledge chunk for logging

        Returns:
            Generated response text
        """
        try:
            response = self._call_gemini(
                prompt,
                temperature=temperature,
                user_message=user_message,
                safety=safety,
                emotion=emotion,
                skill=skill,
                chunk=chunk,
            )

            if response is None:
                logger.warning("Gemini unavailable, falling back to safe default response")
                return (
                    "I'm here to listen. Could you tell me more about what you're feeling?"
                )

            # Log model raw response at debug level for troubleshooting
            try:
                logger.debug("Gemini raw response object: %s", repr(response))
            except Exception:
                # ignore logging errors
                pass

            response_text = (response.text or "").strip()
            if not response_text:
                logger.warning("Gemini returned empty response text (model=%s)", self.model_name)
                return (
                    "I'm here to listen. Could you tell me more about what you're feeling?"
                )

            return response_text
        except Exception:
            # Log full stack trace to help diagnose API/auth/network issues
            logger.exception("Gemini generate failed (model=%s)", self.model_name)
            return (
                "I'm here to listen. Could you tell me more about what you're feeling?"
            )

    def generate_structured(
        self,
        message: str,
        context: List[Dict[str, Any]],
        safety: Optional[Dict[str, Any]] = None,
        fallback_bundle: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured response (JSON format) using a single Gemini call.

        Args:
            message: The user's message
            context: Retrieved knowledge chunks
            safety: Safety assessment result
            fallback_bundle: Fallback response if Gemini fails

        Returns:
            Parsed response as dictionary
        """
        try:
            if fallback_bundle and (not self.client or GEMINI_DISABLED):
                return fallback_bundle

            formatted_prompt = RESPONSE_GENERATION_PROMPT.format(
                user_message=message,
                safety_result=self._format_safety_assessment(safety),
                retrieved_chunk=self._format_retrieved_chunk(context),
            )

            response = self._call_gemini(
                formatted_prompt,
                response_mime_type="application/json",
                user_message=message,
                safety=safety,
                chunk=context,
            )

            if response is None:
                logger.error("FALLBACK USED: response is None")
                if fallback_bundle:
                    return fallback_bundle
                raise ValueError("Empty structured response from Gemini")

            try:
                logger.debug("Gemini structured raw response object: %s", repr(response))
            except Exception:
                pass

            response_text = (response.text or "").strip()
            if not response_text:
                logger.warning("Gemini returned empty structured text before JSON parsing")
                if fallback_bundle:
                    return fallback_bundle
                raise ValueError("Empty structured response from Gemini")

            try:
                payload = self._extract_json_payload(response_text)
                if fallback_bundle:
                    merged = dict(fallback_bundle)
                    merged.update({
                        "emotion": payload.get("emotion", merged.get("emotion", "unknown")),
                        "skill": payload.get("skill", merged.get("skill", "breathing support")),
                        "response": payload.get("response", merged.get("response", "I hear you. I'm here with you.")),
                    })
                    return merged
                return payload
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.error("=" * 60)
                logger.error("INVALID JSON FROM GEMINI")
                logger.error(f"Parse Error: {parse_error}")
                logger.error(f"Raw Response: {response_text}")
                logger.error("=" * 60)

                if fallback_bundle:
                    logger.debug(
                        "Gemini structured response was not valid JSON; using fallback: %s",
                        parse_error,
                    )
                    return fallback_bundle
                logger.warning(
                    "Gemini structured response was not valid JSON: %s",
                    parse_error,
                )
                return {
                    "error": str(parse_error),
                    "raw_response": response,
                }
        except Exception as e:
            logger.exception("STRUCTURED GENERATION FAILED")
            print(f"Error generating structured response: {e}")
            if fallback_bundle:
                return fallback_bundle
            return {"error": str(e)}
