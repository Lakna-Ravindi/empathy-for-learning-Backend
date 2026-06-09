"""
Chat routes for the empathy support system.
Handles incoming chat requests and orchestrates the AI pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Optional, Dict
import logging
from bson import ObjectId

from app.services.rag_service import RAGService
from app.services.gemini_service import GeminiService
from app.services.safety_service import SafetyService
from app.db.database import db
from app.dependencies.auth_dependency import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def convert_objectid_to_string(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId fields to strings for JSON serialization."""
    if isinstance(doc, dict):
        return {key: str(value) if isinstance(value, ObjectId) else value 
                for key, value in doc.items()}
    return doc


# Initialize services
rag_service = RAGService()
gemini_service = GeminiService()
safety_service = SafetyService()


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    emotion: str
    skill: str
    response: str
    risk_level: str
    confidence: float


@router.post("/message", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user = Depends(get_current_user)):
    """
    Process chat message and return empathetic response.
    
    Flow:
    1. Safety check
    2. RAG retrieval
    3. Single Gemini response generation
    4. Storage
    
    Args:
        request: Chat request with message
        current_user: Authenticated user
        
    Returns:
        ChatResponse with emotion, skill, and response
    """
    message = request.message.strip()
    
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    user_id = current_user.username if current_user else request.user_id
    session_id = request.session_id or "default"
    
    try:
        # 1. Safety check first
        safety_check = safety_service.check(message)
        risk_level = safety_check.get("risk", "low")
        
        if risk_level == "high":
            # Log high-risk message
            if db is not None:
                db.risk_logs.insert_one({
                    "user_id": user_id,
                    "message": message,
                    "risk_level": risk_level,
                    "resources": safety_check.get("resources", []),
                    "timestamp": None  # Would use datetime in production
                })
            
            return ChatResponse(
                emotion="crisis",
                skill="Crisis Support",
                response=safety_check.get("message", 
                    "I hear that you're struggling. Please reach out for help."),
                risk_level="high",
                confidence=1.0
            )
        
# 2. Retrieve relevant knowledge
        context = rag_service.search(
            query=message,
            top_k=5
        )

        logger.debug("RAG context (top chunk): %s", context[0] if context else None)

        fallback_bundle = gemini_service.build_fallback_response(
            risk_level=risk_level,
            message=message,
        )

        # 3. Generate a single structured response from Gemini, with a local fallback
        structured = gemini_service.generate_structured(
            message=message,
            context=context,
            safety=safety_check,
            fallback_bundle=fallback_bundle,
        )
        logger.debug("Gemini structured output: %s", structured)

        if isinstance(structured, dict):
            emotion = structured.get("emotion", "neutral")
            confidence = structured.get("confidence", 0.5)
            skill_name = structured.get("skill", "General Support")
            response_text = structured.get("response", fallback_bundle["response"])
        else:
            emotion = "neutral"
            confidence = 0.5
            skill_name = "General Support"
            response_text = fallback_bundle["response"]

        logger.debug("Generated response: %s", response_text)
        
        # 7. Save to database
        if db is not None:
            db.chat_history.insert_one({
                "user_id": user_id,
                "session_id": session_id,
                "message": message,
                "emotion": emotion,
                "confidence": confidence,
                "skill": skill_name,
                "risk_level": risk_level,
                "response": response_text,
                "timestamp": None  # Would use datetime in production
            })
            
            # Log emotion for analytics
            db.emotion_logs.insert_one({
                "user_id": user_id,
                "emotion": emotion,
                "confidence": confidence,
                "timestamp": None  # Would use datetime in production
            })
        
        return ChatResponse(
            emotion=emotion,
            skill=skill_name,
            response=response_text,
            risk_level=risk_level,
            confidence=confidence
        )
    
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_chat_history(
    current_user = Depends(get_current_user),
    limit: int = 50
):
    """
    Get chat history for current user.
    
    Args:
        current_user: Authenticated user
        limit: Maximum number of messages to return
        
    Returns:
        List of chat messages
    """
    user_id = current_user.username
    
    try:
        if db is None:
            return []
        
        history = db.chat_history.find(
            {"user_id": user_id}
        ).sort("_id", -1).limit(limit)
        
        # Convert ObjectId to string for JSON serialization
        return [convert_objectid_to_string(doc) for doc in history]
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_emotion_stats(current_user = Depends(get_current_user)):
    """
    Get emotion statistics for current user.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Emotion statistics
    """
    user_id = current_user.username
    
    try:
        if db is None:
            return {}
        
        emotions = db.emotion_logs.find({"user_id": user_id})
        
        stats = {}
        for log in emotions:
            emotion = log.get("emotion")
            stats[emotion] = stats.get(emotion, 0) + 1
        
        return stats
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crisis-resources")
async def get_crisis_resources():
    """
    Get crisis resources and emergency contacts.
    
    Returns:
        Crisis resources for different risk levels
    """
    return {
        "high": safety_service.get_resources("high"),
        "moderate": safety_service.get_resources("moderate"),
        "resources": {
            "national_hotline": "988",
            "crisis_text_line": "Text HOME to 741741",
            "international": "https://www.iasp.info/resources/Crisis_Centres/"
        }
    }


@router.post("/feedback")
async def submit_feedback(
    feedback: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """
    Submit feedback on response quality.
    
    Args:
        feedback: Feedback data
        current_user: Authenticated user
        
    Returns:
        Confirmation
    """
    user_id = current_user.username
    
    try:
        if db is not None:
            db.feedback.insert_one({
                "user_id": user_id,
                "feedback": feedback,
                "timestamp": None  # Would use datetime in production
            })
        
        return {"status": "success", "message": "Feedback received"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
