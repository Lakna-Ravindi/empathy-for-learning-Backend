# SEEK Backend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` file in the Backend directory:

```
# Gemini AI Configuration
GOOGLE_API_KEY=your_api_key_here

# MongoDB Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/empathy_db
MONGODB_DB=empathy_for_learning

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# JWT Configuration
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and paste into `.env` as `GOOGLE_API_KEY`

**Note**: Free tier provides 60 requests per minute

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

Server will be available at `http://localhost:8000`

- **API Docs**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Authentication (Existing)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Chat (New)
- `POST /api/chat/message` - Send message and get response
- `GET /api/chat/history` - Get chat history
- `GET /api/chat/stats` - Get emotion statistics
- `GET /api/chat/crisis-resources` - Get crisis resources
- `POST /api/chat/feedback` - Submit feedback

## Testing with cURL

### 1. Register User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "full_name": "Test User"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

Response includes `access_token`. Copy it for next requests.

### 3. Send Chat Message
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "message": "I feel really anxious about my exams",
    "session_id": "session_123"
  }'
```

### 4. Get Chat History
```bash
curl -X GET "http://localhost:8000/api/chat/history?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Get Emotion Stats
```bash
curl -X GET http://localhost:8000/api/chat/stats \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Get Crisis Resources
```bash
curl -X GET http://localhost:8000/api/chat/crisis-resources
```

## Project Structure

```
Backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   │
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   ├── security.py        # Security utilities
│   │   └── validators.py      # Input validators
│   │
│   ├── db/
│   │   └── database.py        # MongoDB connection
│   │
│   ├── models/
│   │   ├── auth_models.py     # Auth models
│   │   ├── user_models.py     # User models
│   │   └── profile_models.py  # Profile models
│   │
│   ├── services/              # ✨ NEW
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── emotion_service.py # ✨ Emotion detection (Gemini)
│   │   ├── skill_service.py   # ✨ Skill mapping (JSON)
│   │   ├── rag_service.py     # ✨ Knowledge retrieval (FAISS)
│   │   ├── gemini_service.py  # ✨ Gemini integration
│   │   └── safety_service.py  # ✨ Risk detection
│   │
│   ├── routes/
│   │   ├── auth_routes.py     # Auth endpoints
│   │   ├── profile_routes.py  # Profile endpoints
│   │   └── chat_routes.py     # ✨ Chat endpoints
│   │
│   ├── knowledge/             # ✨ NEW
│   │   ├── __init__.py
│   │   └── skills.json        # ✨ Emotion → Skill mapping
│   │
│   ├── rag/                   # ✨ NEW
│   │   ├── __init__.py
│   │   ├── embedder.py        # ✨ Text to embeddings
│   │   └── faiss_index.py     # ✨ Vector search
│   │
│   └── dependencies/
│       └── auth_dependency.py # Auth middleware
│
├── requirements.txt            # Dependencies
├── .env                       # Environment variables (create this)
├── .env.example              # Example .env template
└── ARCHITECTURE.md           # System architecture guide
```

## Customizing skills.json

Edit `app/knowledge/skills.json` to add/modify skills:

```json
{
  "skill_id": "your_skill_id",
  "skill": "Skill Name",
  "emotions": ["emotion1", "emotion2"],
  "ai_guidance": {
    "tone": "descriptive tone",
    "focus": "what to focus on"
  },
  "description": "Description of the skill"
}
```

Changes take effect on next app reload (no redeployment needed).

## Adding Knowledge Chunks

Create `app/knowledge/seek_chunks.json` with content chunks:

```json
[
  {
    "skill": "Breathing Exercises",
    "content": "Box breathing technique: Inhale for 4, hold for 4, exhale for 4...",
    "topic": "anxiety relief"
  },
  ...
]
```

Format: Each object with `skill`, `content`, and `topic` fields.

## Monitoring

### View Logs
```bash
# Watch logs in real-time
tail -f Backend/logs/app.log
```

### Check Database Collections
```bash
# Using MongoDB compass or CLI
mongosh <connection_string>
use empathy_for_learning
db.chat_history.count()
db.emotion_logs.find().limit(5)
```

### Monitor API Health
```bash
curl http://localhost:8000/
```

## Common Issues & Solutions

### 1. "ModuleNotFoundError: No module named 'google'"
**Solution**: Run `pip install -r requirements.txt`

### 2. "GOOGLE_API_KEY not found"
**Solution**: Create `.env` file with GOOGLE_API_KEY in Backend directory

### 3. "Cannot connect to MongoDB"
**Solution**: 
- Check `MONGODB_URL` in `.env`
- Verify network access is allowed in MongoDB Atlas
- Test connection: `mongosh <connection_string>`

### 4. "FAISS not installed / import error"
**Solution**: 
- Run `pip install faiss-cpu`
- Or for GPU: `pip install faiss-gpu` (requires CUDA)
- System will fallback to keyword matching if unavailable

### 5. "401 Unauthorized on chat endpoints"
**Solution**: 
- Get access_token from login endpoint
- Include in header: `Authorization: Bearer <token>`

## Development Tips

### Enable Debug Mode
```python
# In main.py
app = FastAPI(debug=True)
```

### View Request/Response Logs
```python
# In emotion_service.py, gemini_service.py etc.
import logging
logger = logging.getLogger(__name__)
logger.info(f"Emotion detected: {emotion}")
```

### Hot Reload
Server automatically reloads when you modify files (use `--reload` flag)

## Performance Notes

- **Emotion Detection**: ~1-2 seconds (Gemini API call)
- **Skill Mapping**: <10ms (JSON lookup)
- **RAG Retrieval**: <100ms (keyword search) or ~50ms (FAISS)
- **Response Generation**: ~2-3 seconds (Gemini API call)

**Total latency**: ~4-6 seconds per chat message

## Security Considerations

1. **API Keys**: Never commit `.env` to git
2. **Passwords**: Using Argon2 hashing (passlib)
3. **Tokens**: JWT with 30-minute expiration
4. **CORS**: Restrict to frontend domain in production
5. **MongoDB**: Use connection string with credentials
6. **Rate Limiting**: Consider adding in production

## Deployment Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Update `CORS_ORIGINS` to production domain
- [ ] Enable MongoDB authentication
- [ ] Set `GOOGLE_API_KEY` in production environment
- [ ] Test all endpoints in production
- [ ] Set up monitoring/alerting
- [ ] Configure backups for MongoDB
- [ ] Add rate limiting
- [ ] Enable HTTPS/TLS
- [ ] Document any custom configurations

## Support & Debugging

For issues, check:
1. Error message in terminal output
2. Browser console for API errors
3. MongoDB logs for database issues
4. Google Gemini API quota/limits
5. Network connectivity issues

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure `.env`
3. ✅ Run server: `uvicorn app.main:app --reload`
4. ✅ Test with provided cURL examples
5. ✅ Connect frontend to these endpoints
6. ✅ Deploy to production

Happy building! 🚀
