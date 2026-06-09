#!/usr/bin/env python3
"""
Test script for emotion detection service
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.emotion_service import EmotionService

# Test messages
test_messages = [
    "This is absolutely infuriating! I can't take it anymore!",
    "I've been feeling really sad and hopeless lately",
    "This is absolutely infuriating! I can't take it anymore!",
    "I'm so worried about everything",
    "Hello, how are you?",
]

emotion_service = EmotionService()

print("=" * 80)
print("EMOTION DETECTION TEST")
print("=" * 80)

for msg in test_messages:
    print(f"\nMessage: '{msg}'")
    result = emotion_service.detect_emotion(msg)
    print(f"  Emotion: {result['emotion']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Reasoning: {result['reasoning']}")
    print("-" * 80)

print("\nTest complete!")
