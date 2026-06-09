"""
Emotion detection service (Hybrid: Rules + Keywords + Intensity signals).
Upgraded with Gemini AI classification and a production-ready fallback.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmotionService:
    """Service for detecting emotions in user messages using hybrid rules and keywords."""

    # -----------------------------
    # Weighted keyword model
    # -----------------------------
    EMOTION_KEYWORDS = {
        "anger": {
            "angry": 1.2,
            "furious": 1.8,
            "infuriating": 2.0,
            "rage": 2.2,
            "mad": 1.0,
            "hate": 1.5
        },
        "frustration": {
            "frustrated": 1.5,
            "annoying": 1.2,
            "irritating": 1.3,
            "ugh": 0.8,
            "argh": 0.9
        },
        "anxiety": {
            "worried": 1.2,
            "anxious": 1.5,
            "nervous": 1.2,
            "panic": 1.8,
            "stressed": 1.3,
            "scared": 1.4
        },
        "sadness": {
            "sad": 1.0,
            "depressed": 2.0,
            "miserable": 1.8,
            "heartbroken": 2.0,
            "hopeless": 1.9
        },
        "joy": {
            "happy": 1.0,
            "excited": 1.3,
            "amazing": 1.2,
            "great": 1.0,
            "fantastic": 1.5
        },
        "calm": {
            "calm": 1.0,
            "peaceful": 1.2,
            "relaxed": 1.2,
            "serene": 1.5,
            "tranquil": 1.5,
            "content": 1.0,
            "ok": 0.8,
            "fine": 0.8
        },
        "fear": {
            "scared": 1.2,
            "frightened": 1.3,
            "terrified": 1.8,
            "horrified": 1.8,
            "dread": 1.5,
            "fearful": 1.4
        },
        "loneliness": {
            "lonely": 1.5,
            "alone": 1.0,
            "isolated": 1.8,
            "abandoned": 1.8,
            "left": 0.8,
            "forgotten": 1.2
        },
        "hopelessness": {
            "hopeless": 1.8,
            "despair": 1.8,
            "give up": 1.5,
            "pointless": 1.5,
            "worthless": 1.5,
            "no point": 1.4
        },
        "stress": {
            "stressed": 1.3,
            "stressed out": 1.5,
            "overwhelmed": 1.8,
            "pressure": 1.2,
            "tense": 1.2,
            "tight": 1.0
        },
        # --- newly added emotions ---
        "jealousy": {
            "jealous": 1.8,
            "envious": 1.5,
            "possessive": 1.3,
            "suspicious": 1.0,
            "threatened": 1.2,
            "insecure": 1.2
        },
        "envy": {
            "envy": 1.8,
            "envious": 1.6,
            "covet": 1.5,
            "wish i had": 1.4,
            "why do they get": 1.3,
            "not fair": 1.2,
            "lucky them": 1.0
        },
        "self_criticism": {
            "worthless": 1.8,
            "failure": 1.5,
            "useless": 1.7,
            "hate myself": 2.0,
            "stupid": 1.2,
            "pathetic": 1.6,
            "loser": 1.5,
            "not good enough": 1.8,
            "disappointing": 1.3
        },
        "perfectionism": {
            "perfect": 1.0,
            "perfectionist": 1.8,
            "never good enough": 1.8,
            "flawless": 1.2,
            "mistake": 1.0,
            "messed up": 1.3,
            "wrong again": 1.4,
            "should have done better": 1.6
        },
        "overwhelmed": {
            "overwhelmed": 2.0,
            "too much": 1.5,
            "can't cope": 1.8,
            "drowning": 1.7,
            "swamped": 1.5,
            "buried": 1.3,
            "no bandwidth": 1.4,
            "overloaded": 1.6
        },
        "burnout": {
            "burnout": 2.0,
            "burnt out": 2.0,
            "burned out": 2.0,
            "exhausted": 1.8,
            "drained": 1.7,
            "depleted": 1.6,
            "empty": 1.3,
            "running on fumes": 1.8,
            "can't do this anymore": 1.9,
            "checked out": 1.5
        },
        "panic": {
            "panicking": 2.0,
            "panic attack": 2.2,
            "heart racing": 1.8,
            "can't breathe": 1.9,
            "losing control": 1.8,
            "freaking out": 1.7,
            "spiraling": 1.6,
            "about to break": 1.7
        }
    }

    # -----------------------------
    # Phrase-level detection (VERY important)
    # -----------------------------
    EMOTION_PHRASES = {
        "anger": [
            "can't take it anymore",
            "so angry",
            "fed up",
            "pissed off"
        ],
        "sadness": [
            "feeling down",
            "broken inside",
            "no point anymore"
        ],
        "anxiety": [
            "can't stop worrying",
            "overthinking everything",
            "panic attack"
        ],
        "loneliness": [
            "feel so alone",
            "nobody cares",
            "no one understands"
        ],
        "hopelessness": [
            "want to give up",
            "nothing goes right",
            "whats the point",
            "what's the point"
        ],
        "stress": [
            "too much pressure",
            "at my limit",
            "breaking point"
        ],
        # --- newly added phrases ---
        "jealousy": [
            "why does he get to",
            "why does she get to",
            "can't stand seeing them together",
            "she's always flirting",
            "he's always around her",
            "don't trust them"
        ],
        "envy": [
            "wish i had what they have",
            "why not me",
            "everyone else has it easy",
            "they don't deserve it",
            "i want what they have"
        ],
        "self_criticism": [
            "i'm such a failure",
            "i always mess up",
            "i'm so stupid",
            "i hate who i am",
            "i'm not good enough",
            "i let everyone down"
        ],
        "perfectionism": [
            "it has to be perfect",
            "i can't make a single mistake",
            "nothing i do is ever good enough",
            "i should have done better",
            "why can't i just get it right"
        ],
        "overwhelmed": [
            "i can't handle all of this",
            "too many things at once",
            "i don't know where to start",
            "everything is piling up",
            "i feel like i'm drowning"
        ],
        "burnout": [
            "i have nothing left",
            "i'm completely done",
            "i just don't care anymore",
            "i'm so tired of everything",
            "i can't keep going like this",
            "i've been running on empty"
        ],
        "panic": [
            "i'm having a panic attack",
            "i can't calm down",
            "my heart is racing",
            "i feel like i'm going crazy",
            "everything is spinning out of control"
        ]
    }

    def __init__(self):
        """Initialize the Emotion Service."""

    def detect_emotion(self, message: str) -> Dict[str, Any]:
        """
        Detect emotion from user message using hybrid rules and keywords.

        Args:
            message: User's message text

        Returns:
            Dict with emotion, confidence, and reasoning
        """
        return self._hybrid_fallback_detection(message)

    def _hybrid_fallback_detection(self, message: str) -> Dict[str, Any]:
        """
        Fallback hybrid keyword + rules-based emotion detection when Gemini API fails.
        """
        message_lower = message.lower()
        scores = {emotion: 0.0 for emotion in self.EMOTION_KEYWORDS.keys()}

        # 1. Phrase matching (high weight)
        for emotion, phrases in self.EMOTION_PHRASES.items():
            for phrase in phrases:
                if phrase in message_lower:
                    scores[emotion] += 2.5

        # 2. Keyword weighted matching
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword, weight in keywords.items():
                if keyword in message_lower:
                    scores[emotion] += weight

        # 3. Intensity signals
        intensity_boost = self._get_intensity_boost(message)

        # apply boost to all detected emotions
        for emotion in scores:
            if scores[emotion] > 0:
                scores[emotion] += intensity_boost

        # 4. Decide final emotion
        best_emotion = max(scores, key=scores.get)
        best_score = scores[best_emotion]

        if best_score == 0:
            return {
                "emotion": "neutral",
                "confidence": 0.5,
                "reasoning": "No emotional signals detected"
            }

        # 5. Normalize confidence
        confidence = self._normalize_confidence(best_score)

        # Boost confidence to 1.0 for direct, unambiguous emotional statements
        verbal_forms = {
            "jealousy": ["jealous"],
            "envy": ["envious", "jealous"],
            "anger": ["angry", "mad", "furious"],
            "sadness": ["sad", "depressed"],
            "anxiety": ["anxious", "worried", "nervous"],
            "stress": ["stressed", "overwhelmed"],
            "fear": ["scared", "terrified", "frightened"],
            "loneliness": ["lonely", "alone"],
            "hopelessness": ["hopeless"],
            "frustration": ["frustrated"]
        }
        
        if best_emotion in verbal_forms:
            for form in verbal_forms[best_emotion]:
                pattern = rf"\b(feel|feeling|am|gets|feelings of)\b.*\b{form}\b"
                if re.search(pattern, message_lower):
                    confidence = 1.0
                    break

        return {
            "emotion": best_emotion,
            "confidence": round(confidence, 3),
            "reasoning": f"Score={best_score:.2f} (keyword + phrase + intensity)"
        }

    def _get_intensity_boost(self, message: str) -> float:
        """Intensity detection boost based on punctuations and text patterns."""
        boost = 0.0

        # Exclamation marks
        exclamations = message.count("!")
        boost += min(exclamations * 0.1, 0.3)

        # ALL CAPS (strong emotion)
        if message.isupper() and len(message) > 3:
            boost += 0.3

        # repeated letters (soooo, nooo)
        if re.search(r"(.)\1{2,}", message.lower()):
            boost += 0.2

        # emotional amplifiers
        if any(word in message.lower() for word in ["so", "very", "really", "extremely"]):
            boost += 0.1

        return min(boost, 0.6)

    def _normalize_confidence(self, score: float) -> float:
        """Normalize scores into a confidence range [0.0, 0.95]."""
        confidence = 1 - (1 / (1 + score))
        return max(0.0, min(confidence, 0.95))