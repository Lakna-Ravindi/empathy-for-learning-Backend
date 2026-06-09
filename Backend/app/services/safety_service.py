"""
Safety service for detecting high-risk content.
Performs keyword matching and content analysis for user safety.
"""

from typing import Dict, Any
import re


class SafetyService:
    """Service for detecting high-risk content in user messages."""
    
    # Keywords indicating high risk (self-harm, suicide)
    HIGH_RISK_KEYWORDS = [
        "suicide",
        "kill myself",
        "self harm",
        "end my life",
        "want to die",
        "no point in living",
        "better off dead",
        "should kill myself",
        "hurt myself",
        "cut myself",
        "self-injury",
        "self-injure"
    ]
    
    # Keywords indicating moderate risk (crisis, emergency)
    MODERATE_RISK_KEYWORDS = [
        "crisis",
        "emergency",
        "panic attack",
        "can't breathe",
        "can't think",
        "can't function",
        "breaking down",
        "losing it",
        "falling apart"
    ]
    
    # Resource suggestions by risk level
    RESOURCES = {
        "high": {
            "response": "I hear that you're in pain. Please reach out for immediate help. You're not alone.",
            "resources": [
                "National Suicide Prevention Lifeline: 988 (US)",
                "Crisis Text Line: Text HOME to 741741",
                "International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/"
            ]
        },
        "moderate": {
            "response": "You seem to be in a tough situation. Let's work through this together, but please consider reaching out to a trusted person or professional.",
            "resources": [
                "Speak with a school counselor or trusted adult",
                "Call your local mental health crisis line",
                "Visit your nearest emergency room if you feel unsafe"
            ]
        },
        "low": {
            "response": None,
            "resources": []
        }
    }
    
    def __init__(self):
        """Initialize the Safety Service."""
        self.high_risk_pattern = self._compile_pattern(self.HIGH_RISK_KEYWORDS)
        self.moderate_risk_pattern = self._compile_pattern(self.MODERATE_RISK_KEYWORDS)
    
    def _compile_pattern(self, keywords: list) -> re.Pattern:
        """
        Compile regex pattern for keyword matching.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            Compiled regex pattern
        """
        escaped_keywords = [re.escape(kw) for kw in keywords]
        pattern = r'\b(' + '|'.join(escaped_keywords) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def check(self, message: str) -> Dict[str, Any]:
        """
        Check message for high-risk content.
        
        Args:
            message: User message to analyze
            
        Returns:
            Dict with risk level and appropriate response
        """
        if not message:
            return {"risk": "low", "needs_intervention": False}
        
        message_lower = message.lower()
        
        # Check for high-risk keywords
        if self.high_risk_pattern.search(message_lower):
            return {
                "risk": "high",
                "needs_intervention": True,
                "message": self.RESOURCES["high"]["response"],
                "resources": self.RESOURCES["high"]["resources"]
            }
        
        # Check for moderate-risk keywords
        if self.moderate_risk_pattern.search(message_lower):
            return {
                "risk": "moderate",
                "needs_intervention": True,
                "message": self.RESOURCES["moderate"]["response"],
                "resources": self.RESOURCES["moderate"]["resources"]
            }
        
        return {
            "risk": "low",
            "needs_intervention": False
        }
    
    def get_resources(self, risk_level: str) -> Dict[str, Any]:
        """
        Get crisis resources for a risk level.
        
        Args:
            risk_level: Risk level (high, moderate, low)
            
        Returns:
            Resources dictionary
        """
        return self.RESOURCES.get(risk_level, self.RESOURCES["low"])
