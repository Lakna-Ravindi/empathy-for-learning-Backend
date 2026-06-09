"""
Skill mapping service.
Maps detected emotions to appropriate skills from the knowledge base.
"""

import json
import os
from typing import Dict, Any, Optional


class SkillService:
    """Service for mapping emotions to skills."""
    
    def __init__(self):
        """Initialize the Skill Service and load skills database."""
        self.skills_path = os.path.join(
            os.path.dirname(__file__),
            "../knowledge/skills.json"
        )
        self.skills = self._load_skills()
    
    def _load_skills(self) -> list:
        """
        Load skills database from JSON file.
        
        Returns:
            List of skill configurations
        """
        try:
            if os.path.exists(self.skills_path):
                with open(self.skills_path, "r") as f:
                    return json.load(f)
            else:
                print(f"Skills file not found at {self.skills_path}")
                return self._get_default_skills()
        except Exception as e:
            print(f"Error loading skills: {e}")
            return self._get_default_skills()
    
    def get_skill(self, emotion: str) -> Optional[Dict[str, Any]]:
        """
        Get the appropriate skill for a given emotion.
        
        Args:
            emotion: Detected emotion
            
        Returns:
            Skill configuration dict or None if not found
        """
        emotion_lower = emotion.lower()
        
        for skill in self.skills:
            emotions = [e.lower() for e in skill.get("emotions", [])]
            if emotion_lower in emotions:
                return skill
        
        return None
    
    def get_all_skills(self) -> list:
        """
        Get all available skills.
        
        Returns:
            List of all skills
        """
        return self.skills
    
    def _get_default_skills(self) -> list:
        """
        Get default skills configuration if file not found.
        
        Returns:
            Default skills list
        """
        return [
            {
                "skill": "Calming the Body and Mind",
                "description": "Helps users recognize body sensations, regulate emotions, and return to a calm resilient state using body literacy and regulation tools.",
                "emotions": ["stress", "anxiety", "panic", "overwhelmed", "nervous", "fear", "emotional overload", "irritated", "numb"],
                "ai_guidance": {
                    "tone": "calm, supportive, non-judgmental",
                    "style": "SEEK emotional coaching approach"
                }
            },
            {
                "skill": "Ethical Mindfulness",
                "description": "Develops the ability to act according to core values even under stress through heedfulness, mindfulness, awareness, and attention stability.",
                "emotions": ["anger", "regret", "embarrassment", "impulse", "aggression"],
                "ai_guidance": {
                    "tone": "balanced, value-centered",
                    "style": "SEEK ethical coaching"
                }
            },
            {
                "skill": "Emotional Awareness",
                "description": "Builds ability to observe emotions and mental states clearly, create space between trigger and response, and prevent emotional escalation.",
                "emotions": ["anger", "gratitude", "jealousy", "resentment", "anxiety"],
                "ai_guidance": {
                    "tone": "observant and gentle",
                    "style": "SEEK awareness coaching"
                }
            },
            {
                "skill": "Self Compassion",
                "description": "Helps overcome thinking traps, perfectionism, and self-criticism to build healthier self-relationship and emotional well-being.",
                "emotions": ["self-criticism", "perfectionism", "inferiority", "superiority", "unrealistic pressure"],
                "ai_guidance": {
                    "tone": "warm, kind, understanding",
                    "style": "SEEK self-compassion coaching"
                }
            },
            {
                "skill": "Impartiality and Common Humanity",
                "description": "Reduces bias, stereotypes, and prejudice by recognizing shared human experiences and practicing impartial compassion.",
                "emotions": ["bias", "prejudice", "in-group favoritism"],
                "ai_guidance": {
                    "tone": "inclusive and fair",
                    "style": "SEEK impartiality coaching"
                }
            },
            {
                "skill": "Forgiveness and Gratitude",
                "description": "Cultivates forgiveness by letting go of resentment and builds gratitude to improve emotional well-being and relationships.",
                "emotions": ["resentment", "anger", "gratitude", "bitterness"],
                "ai_guidance": {
                    "tone": "gentle and healing",
                    "style": "SEEK forgiveness & gratitude coaching"
                }
            },
            {
                "skill": "Empathic Concern",
                "description": "Develops healthy empathy by distinguishing affective/cognitive empathy, avoiding empathic distress, and cultivating sympathetic joy.",
                "emotions": ["empathic distress", "envy", "emotional contagion", "burnout"],
                "ai_guidance": {
                    "tone": "caring yet balanced",
                    "style": "SEEK empathic concern coaching"
                }
            },
            {
                "skill": "Compassion",
                "description": "Cultivates genuine compassion as a strength, with clear boundaries, agency, and action across wishing, aspiring, and engaged levels.",
                "emotions": ["apathy", "powerlessness", "compassion fatigue"],
                "ai_guidance": {
                    "tone": "wise and courageous",
                    "style": "SEEK compassion coaching"
                }
            }
        ]
