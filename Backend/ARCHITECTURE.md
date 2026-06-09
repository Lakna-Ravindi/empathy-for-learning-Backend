# SEEK Empathy Support System - Architecture Guide

## Overview

The SEEK system is an AI-powered emotional support platform that combines emotion detection, skill mapping, knowledge retrieval, and response generation to provide empathetic support to users.

## System Architecture

```
User Message
    ↓
Safety Service (SafetyService)
    ↓ [Check for high-risk keywords]
Emotion Detection (EmotionService → Gemini)
    ↓ [Classify emotion using AI]
Skill Mapping (SkillService)
    ↓ [Map emotion to coping skill]
Knowledge Retrieval (RAGService → FAISS)
    ↓ [Retrieve relevant knowledge chunks]
Prompt Building (GeminiService)
    ↓ [Build context-aware prompt]
Response Generation (GeminiService → Gemini)
    ↓ [Generate empathetic response]
Database Storage (MongoDB)
    ↓
Return Response to User
```

## Module Structure

### New Services (`app/services/`)

#### 1. **EmotionService** (`emotion_service.py`)
- **Purpose**: Detect and classify emotions from user messages
- **Technology**: Google Gemini API
- **Key Method**: `detect_emotion(message: str)`
- **Output**: `{"emotion": str, "confidence": float, "reasoning": str}`
- **Emotions Supported**: sadness, anxiety, anger, fear, loneliness, hopelessness, stress, joy, calm, frustration

**Usage**:
```python
emotion_service = EmotionService()
result = emotion_service.detect_emotion("I feel so alone")
# {"emotion": "loneliness", "confidence": 0.95, "reasoning": "..."}
```

#### 2. **SkillService** (`skill_service.py`)
- **Purpose**: Map detected emotions to coping skills
- **Data Source**: `app/knowledge/skills.json`
- **Key Method**: `get_skill(emotion: str)`
- **Output**: Skill configuration with guidance and description
- **Skills Available**: 
  - Breathing Exercises
  - Grounding Techniques
  - Cognitive Reframing
  - Social Connection
  - Self-Compassion
  - Mindfulness
  - Progressive Muscle Relaxation
  - Journaling
  - Values & Purpose

**Usage**:
```python
skill_service = SkillService()
skill = skill_service.get_skill("anxiety")
# {
#   "skill_id": "breathing",
#   "skill": "Breathing Exercises",
#   "emotions": ["anxiety", ...],
#   "ai_guidance": {"tone": "calm", "focus": "..."},
#   "description": "..."
# }
```

#### 3. **SafetyService** (`safety_service.py`)
- **Purpose**: Detect high-risk content (self-harm, suicide indicators)
- **Method**: Keyword matching + pattern detection
- **Risk Levels**: low, moderate, high
- **Key Method**: `check(message: str)`
- **Features**:
  - High-risk keyword detection
  - Moderate-risk phrase detection
  - Automatic crisis resource suggestions
  - Crisis hotline information

**Usage**:
```python
safety_service = SafetyService()
result = safety_service.check("I want to hurt myself")
# {
#   "risk": "high",
#   "needs_intervention": True,
#   "message": "I hear that you're in pain...",
#   "resources": [...]
# }
```

#### 4. **RAGService** (`rag_service.py`)
- **Purpose**: Retrieve Augmented Generation - find relevant knowledge for context
- **Data Source**: `app/knowledge/seek_chunks.json` or default knowledge base
- **Technology**: FAISS (optional) or keyword matching (fallback)
- **Key Method**: `search(query: str, skill: str, top_k: int)`
- **Output**: List of relevant knowledge chunks

**Usage**:
```python
rag_service = RAGService()
context = rag_service.search(
    query="feeling anxious",
    skill="Breathing Exercises",
    top_k=5
)
# [
#   {"skill": "Breathing Exercises", "content": "Box breathing..."},
#   ...
# ]
```

#### 5. **GeminiService** (`gemini_service.py`)
- **Purpose**: Interface with Google Gemini for emotion detection and response generation
- **Technology**: Google Generative AI API
- **Key Methods**:
  - `build_prompt(message, emotion, skill, context)` - Build comprehensive prompt
  - `generate(prompt, temperature)` - Generate response from prompt
  - `generate_structured(prompt, output_format)` - Generate JSON response

**Usage**:
```python
gemini_service = GeminiService()
prompt = gemini_service.build_prompt(
    message="I'm feeling overwhelmed",
    emotion={"emotion": "stress", "confidence": 0.9},
    skill=skill_obj,
    context=context_chunks
)
response = gemini_service.generate(prompt)
```

### Knowledge Base (`app/knowledge/`)

#### **skills.json**
- Maps emotions to coping skills
- Contains AI guidance (tone, focus)
- Skill descriptions and IDs
- Easily updateable without redeployment

**Structure**:
```json
{
  "skill_id": "breathing",
  "skill": "Breathing Exercises",
  "emotions": ["anxiety", "stress", "fear"],
  "ai_guidance": {
    "tone": "calm and supportive",
    "focus": "grounding and relaxation"
  },
  "description": "Guided breathing exercises..."
}
```

#### **seek_chunks.json** (Optional)
- Knowledge chunks for RAG retrieval
- Can be replaced with actual SEEK curriculum content
- Format:
  ```json
  {
    "skill": "Breathing Exercises",
    "content": "Box breathing technique...",
    "topic": "anxiety relief"
  }
  ```

### RAG Module (`app/rag/`)

#### **embedder.py**
- Converts text to embeddings
- Uses `sentence-transformers` for production
- Fallback to hash-based method if unavailable
- Supports batch embedding

**Usage**:
```python
from app.rag.embedder import Embedder

embedder = Embedder()
vector = embedder.embed("I'm feeling anxious")  # -> numpy array
```

#### **faiss_index.py**
- FAISS index wrapper for similarity search
- Supports L2 and inner-product metrics
- Graceful fallback to naive search
- Save/load capabilities for persistence

**Usage**:
```python
from app.rag.faiss_index import FAISSIndex

index = FAISSIndex(dimension=384)
index.add(embeddings, documents)
distances, results = index.search(query_embedding, k=5)
```

### Chat Routes (`app/routes/chat_routes.py`)

New REST API endpoints for the chat system:

#### **POST `/api/chat/message`**
Main chat endpoint. Processes user message through entire pipeline.

**Request**:
```json
{
  "message": "I'm feeling really stressed lately",
  "user_id": "optional_override",
  "session_id": "optional_session"
}
```

**Response**:
```json
{
  "emotion": "stress",
  "skill": "Breathing Exercises",
  "response": "I understand you're feeling stressed. Let's work through this...",
  "risk_level": "low",
  "confidence": 0.92
}
```

#### **GET `/api/chat/history`**
Retrieve chat history for current user.

**Query Parameters**:
- `limit`: Number of messages (default: 50)

#### **GET `/api/chat/stats`**
Get emotion statistics for current user.

**Response**:
```json
{
  "stress": 12,
  "anxiety": 8,
  "sadness": 5
}
```

#### **GET `/api/chat/crisis-resources`**
Get crisis resources and emergency contacts.

#### **POST `/api/chat/feedback`**
Submit feedback on response quality.

## Database Collections

The system uses MongoDB with these collections:

- **chat_history**: Stores all chat messages and responses
  ```
  {
    user_id, session_id, message, emotion, confidence,
    skill, risk_level, response, timestamp
  }
  ```

- **emotion_logs**: Analytics on emotion patterns
  ```
  {
    user_id, emotion, confidence, timestamp
  }
  ```

- **risk_logs**: High-risk messages for monitoring
  ```
  {
    user_id, message, risk_level, resources, timestamp
  }
  ```

- **feedback**: User feedback on responses
  ```
  {
    user_id, feedback, timestamp
  }
  ```

## Configuration

### Environment Variables Required

Create a `.env` file:

```
# Gemini AI
GOOGLE_API_KEY=your_gemini_api_key_here

# MongoDB
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/empathy_db
MONGODB_DB=empathy_for_learning

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# JWT
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
```

### Getting Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` as `GOOGLE_API_KEY`

## Dependencies

New dependencies added to `requirements.txt`:

- **google-generativeai**: Gemini API client
- **sentence-transformers**: Embedding models
- **faiss-cpu**: Vector similarity search (use faiss-gpu for GPU support)
- **numpy**: Numerical operations

Install all:
```bash
pip install -r requirements.txt
```

## How It All Connects

### Message Processing Flow

1. **User sends message** → Chat endpoint receives request
2. **Safety check** → SafetyService scans for high-risk keywords
3. **Emotion detection** → EmotionService calls Gemini API
4. **Skill mapping** → SkillService maps emotion from skills.json
5. **Knowledge retrieval** → RAGService searches knowledge base
6. **Prompt building** → GeminiService builds context-aware prompt
7. **Response generation** → GeminiService calls Gemini API for response
8. **Database storage** → Save to MongoDB collections
9. **Return response** → Send back to user

### Authentication & Authorization

- Uses existing auth dependency: `get_current_user`
- All chat endpoints require authentication
- User data isolated per user_id

## Integration with Existing System

The new chat system integrates seamlessly with your existing infrastructure:

- **Database**: Uses same MongoDB instance
- **Authentication**: Reuses auth_routes and dependencies
- **Middleware**: Uses same CORS and error handling
- **Structure**: Follows same patterns as auth routes

## Monitoring & Logging

- High-risk messages logged separately for safety monitoring
- Emotion statistics collected for research/analysis
- Response feedback tracked for model improvement
- Error logging for debugging

## Future Enhancements

1. **Fine-tuning**: Train Gemini on SEEK-specific responses
2. **Multi-language**: Support for multiple languages
3. **Advanced RAG**: Pre-compute embeddings, optimize FAISS index
4. **Analytics Dashboard**: Visualize emotion patterns
5. **A/B Testing**: Test different response strategies
6. **Integration**: Connect to mental health professionals
7. **Offline Mode**: Cached responses for connectivity issues

## Testing the System

```bash
# Start the server
cd Backend
uvicorn app.main:app --reload

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "I feel anxious"}'
```

## Troubleshooting

### Gemini API Errors
- Check `GOOGLE_API_KEY` is set correctly
- Verify API quota hasn't exceeded
- Check API key has Generative Language API enabled

### MongoDB Connection Issues
- Verify `MONGODB_URL` in `.env`
- Check network access is allowed in MongoDB Atlas
- Ensure database user has proper permissions

### FAISS Installation Issues
- Use `faiss-cpu` for CPU-only systems
- For GPU: install `faiss-gpu` (requires CUDA)
- Fallback uses keyword matching if FAISS unavailable

## Files Checklist

✅ `app/services/emotion_service.py`
✅ `app/services/skill_service.py`
✅ `app/services/safety_service.py`
✅ `app/services/rag_service.py`
✅ `app/services/gemini_service.py`
✅ `app/knowledge/skills.json`
✅ `app/knowledge/__init__.py`
✅ `app/rag/embedder.py`
✅ `app/rag/faiss_index.py`
✅ `app/rag/__init__.py`
✅ `app/routes/chat_routes.py`
✅ `app/main.py` (updated)
✅ `requirements.txt` (updated)

All new modules are ready to use! 🎉
