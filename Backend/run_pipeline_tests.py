#!/usr/bin/env python3
"""
Diagnostic test script to verify skill and emotion detection pipeline.
Supports both live Gemini API mode and offline/hybrid rules fallback mode.
"""
import sys
import os
import argparse
import json

# Ensure parent directory is in path so app imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from app.services.emotion_service import EmotionService
from app.services.skill_service import SkillService
from app.services.gemini_service import GeminiService
from app.services.safety_service import SafetyService
import app.services.gemini_service as gemini_service_mod

# List of comprehensive test cases covering each skill and key associated emotions
TEST_CASES = [
    # 1. Calming the Body and Mind
    {
        "expected_skill": "Calming the Body and Mind",
        "expected_emotion": "stress",
        "message": "I have so much pressure on me right now with school and work, and I feel like I'm at my breaking point."
    },
    {
        "expected_skill": "Calming the Body and Mind",
        "expected_emotion": "anxiety",
        "message": "I can't stop worrying and overthinking everything. My mind is constantly racing."
    },
    {
        "expected_skill": "Calming the Body and Mind",
        "expected_emotion": "panic",
        "message": "I'm having a panic attack! My heart is racing, I can't breathe, and everything is spinning."
    },
    {
        "expected_skill": "Calming the Body and Mind",
        "expected_emotion": "overwhelmed",
        "message": "I can't handle all of this. There are too many things happening at once and everything is piling up."
    },
    {
        "expected_skill": "Calming the Body and Mind",
        "expected_emotion": "fear",
        "message": "I am absolutely terrified of losing my job, the uncertainty is frightening."
    },

    # 2. Ethical Mindfulness
    {
        "expected_skill": "Ethical Mindfulness",
        "expected_emotion": "anger",
        "message": "I'm so angry at my brother! He took my car without asking and I'm absolutely furious!"
    },
    {
        "expected_skill": "Ethical Mindfulness",
        "expected_emotion": "regret",
        "message": "I feel so much regret for how I shouted at my mom. I shouldn't have reacted so impulsively."
    },
    {
        "expected_skill": "Ethical Mindfulness",
        "expected_emotion": "embarrassment",
        "message": "I made a huge mistake in front of everyone and felt so embarrassed."
    },

    # 3. Emotional Awareness
    {
        "expected_skill": "Emotional Awareness",
        "expected_emotion": "jealousy",
        "message": "I get so jealous when I see my partner talking or flirting with others, it makes me feel insecure."
    },
    {
        "expected_skill": "Emotional Awareness",
        "expected_emotion": "resentment",
        "message": "I feel so much resentment and bitterness towards my old boss for passing me over for a promotion."
    },

    # 4. Self Compassion
    {
        "expected_skill": "Self Compassion",
        "expected_emotion": "self_criticism",
        "message": "I'm such a failure. I always mess up and I feel like I'm not good enough."
    },
    {
        "expected_skill": "Self Compassion",
        "expected_emotion": "perfectionism",
        "message": "It has to be perfect, I can't afford to make a single mistake or it's a disaster."
    },

    # 5. Impartiality and Common Humanity
    {
        "expected_skill": "Impartiality and Common Humanity",
        "expected_emotion": "bias",
        "message": "I catch myself judging people from other departments and showing favoritism to my own team."
    },

    # 6. Forgiveness and Gratitude
    {
        "expected_skill": "Forgiveness and Gratitude",
        "expected_emotion": "gratitude",
        "message": "I am so full of gratitude for the kind gestures and support from my friends during this tough month."
    },

    # 7. Empathic Concern
    {
        "expected_skill": "Empathic Concern",
        "expected_emotion": "envy",
        "message": "I wish I had what they have. Why does everyone else get it easy while I struggle?"
    },

    # 8. Compassion
    {
        "expected_skill": "Compassion",
        "expected_emotion": "apathy",
        "message": "There is so much suffering and bad news everywhere, I just feel powerlessness and apathy."
    }
]

def main():
    parser = argparse.ArgumentParser(description="Run skill and emotion detection tests.")
    parser.add_argument(
        "--mode",
        choices=["auto", "gemini", "hybrid"],
        default="auto",
        help="Detection mode. 'auto' uses Gemini and falls back to hybrid. 'gemini' forces Gemini. 'hybrid' forces the offline rules/keyword model."
    )
    parser.add_argument(
        "--only-emotion",
        type=str,
        help="Only run tests matching this expected emotion (e.g. stress, jealousy, anger)."
    )
    args = parser.parse_args()

    # Configure modes
    if args.mode == "hybrid":
        gemini_service_mod.GEMINI_DISABLED = True
        print("[Mode Settings] FORCING Offline Hybrid/Keyword Detection Rules.")
    elif args.mode == "gemini":
        gemini_service_mod.GEMINI_DISABLED = False
        print("[Mode Settings] FORCING Live Gemini API Detection.")
    else:
        print("[Mode Settings] AUTO Mode (Gemini API with rate-limit fallback).")

    # Initialize services
    emotion_service = EmotionService()
    skill_service = SkillService()
    gemini_service = GeminiService()
    safety_service = SafetyService()

    # Filter test cases if requested
    cases_to_run = TEST_CASES
    if args.only_emotion:
        target = args.only_emotion.lower().replace("-", "_")
        cases_to_run = [c for c in TEST_CASES if c["expected_emotion"] == target]
        if not cases_to_run:
            print(f"No test cases found matching emotion: '{target}'")
            return

    print("=" * 100)
    print(f"RUNNING EMOTION & SKILL DETECTION TEST SUITE ({len(cases_to_run)} cases)")
    print("=" * 100)

    success_count = 0

    for idx, case in enumerate(cases_to_run, 1):
        msg = case["message"]
        expected_emo = case["expected_emotion"]
        expected_skill = case["expected_skill"]

        print(f"\n[{idx}] Test Message: \"{msg}\"")
        
        # 1. Safety check
        safety_check = safety_service.check(msg)
        risk_level = safety_check.get("risk", "low")

        # 2. Emotion detection
        emotion_res = emotion_service.detect_emotion(msg)
        detected_emo = emotion_res.get("emotion", "neutral")
        confidence = emotion_res.get("confidence", 0.0)
        reasoning = emotion_res.get("reasoning", "")

        # 3. Skill mapping
        skill_obj = skill_service.get_skill(detected_emo)
        detected_skill = skill_obj.get("skill", "General Support") if skill_obj else "General Support"

        # Check match
        emotion_match = detected_emo == expected_emo
        skill_match = detected_skill == expected_skill

        status_str = "PASS" if (emotion_match and skill_match) else "MISMATCH"
        if emotion_match and skill_match:
            success_count += 1
            print(f"  Result: \033[92m✅ {status_str}\033[0m")
        else:
            print(f"  Result: \033[91m❌ {status_str}\033[0m")

        print(f"  Expected: Emotion = {expected_emo:<15} | Skill = {expected_skill}")
        print(f"  Detected: Emotion = {detected_emo:<15} | Skill = {detected_skill}")
        print(f"  Confidence: {confidence:.2f} | Risk Level: {risk_level}")
        print(f"  Reasoning: {reasoning}")

        # Get response
        fallback_bundle = gemini_service.build_fallback_response(
            emotion=emotion_res,
            skill=skill_obj,
            risk_level=risk_level,
            message=msg
        )

        # Generate response
        if gemini_service_mod.GEMINI_DISABLED or args.mode == "hybrid":
            resp_source = "Offline Fallback Pool"
            response_text = fallback_bundle["response"]
        else:
            resp_source = "Live Gemini API"
            structured = gemini_service.generate_structured(
                message=msg,
                context=[],
                safety=safety_check,
                fallback_bundle=fallback_bundle,
            )
            response_text = structured.get("response", fallback_bundle["response"])

        print(f"  Response ({resp_source}): \"{response_text}\"")
        print("-" * 100)

    print("\n" + "=" * 100)
    print(f"TEST RUN SUMMARY: {success_count}/{len(cases_to_run)} passed (Exact matches for both emotion and skill)")
    print("=" * 100)

if __name__ == "__main__":
    main()
