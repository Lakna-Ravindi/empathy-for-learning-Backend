# SEEK Chat System - Quick Reference Guide

## System Overview

```
┌─────────────┐
│   User      │
│ Sends Msg   │
└──────┬──────┘
       │ "I feel anxious about exams"
       ↓
┌──────────────────────────────────────┐
│  1. Safety Check                     │
│  - Check high-risk keywords          │
│  - Detect self-harm indicators       │
└──────────────────────────────────────┘
       │ risk_level = "low"
       ↓
┌──────────────────────────────────────┐
│  2. Emotion Detection                │
│  - Call Gemini API                   │
│  - Classify emotion                  │
│  - Get confidence score              │
└──────────────────────────────────────┘
       │ emotion = "anxiety"
       ↓
┌──────────────────────────────────────┐
│  3. Skill Mapping                    │
│  - Look up in skills.json            │
│  - Get coping strategy               │
│  - Get AI guidance                   │
└──────────────────────────────────────┘
       │ skill = "Breathing Exercises"
       ↓
┌──────────────────────────────────────┐
│  4. Knowledge Retrieval (RAG)        │
│  - Search knowledge base             │
│  - Find relevant chunks              │
│  - Get top-k results                 │
└──────────────────────────────────────┘
       │ context = [chunk1, chunk2, ...]
       ↓
┌──────────────────────────────────────┐
│  5. Prompt Building                  │
│  - Combine all context               │
│  - Create system prompt              │
│  - Add user message                  │
└──────────────────────────────────────┘
       │ prompt = "You are SEEK..."
       ↓
┌──────────────────────────────────────┐
│  6. Response Generation              │
│  - Call Gemini API                   │
│  - Generate empathetic response      │
│  - Return to user                    │
└──────────────────────────────────────┘
       │ response = "I understand your anxiety..."
       ↓
┌──────────────────────────────────────┐
│  7. Storage                          │
│  - Save to chat_history              │
│  - Log emotions                      │
│  - Track risk incidents              │
└──────────────────────────────────────┘
       │
       ↓
┌─────────────┐
│   API       │
│  Response   │
└─────────────┘
```

## Code Flow Example

### Step 1: User Sends Message
```json
POST /api/chat/message
{
  "message": "I feel really anxious about upcoming exams",
  "session_id": "session_abc123"
}
```

### Step 2: Safety Check
```python
safety_check = safety_service.check(message)
# Returns: {"risk": "low", "needs_intervention": False}

# If risk == "high" → Return crisis response immediately
# If risk == "moderate" → Return with resources suggestion
```

### Step 3: Emotion Detection
```python
emotion_result = emotion_service.detect_emotion(message)
# Returns: {
#   "emotion": "anxiety",
#   "confidence": 0.95,
#   "reasoning": "User mentions anxiety and exam stress"
# }
```

### Step 4: Skill Mapping
```python
skill_obj = skill_service.get_skill("anxiety")
# Returns: {
#   "skill_id": "breathing",
#   "skill": "Breathing Exercises",
#   "emotions": ["anxiety", "stress", "fear"],
#   "ai_guidance": {
#     "tone": "calm and supportive",
#     "focus": "grounding and relaxation"
#   }
# }
```

### Step 5: Knowledge Retrieval
```python
context = rag_service.search(
    query="I feel anxious about exams",
    skill="Breathing Exercises",
    top_k=5
)
# Returns: [
#   {
#     "skill": "Breathing Exercises",
#     "content": "Box breathing: 4-4-4-4 counts...",
#     "topic": "anxiety relief"
#   },
#   ...
# ]
```

### Step 6: Build Prompt
```python
prompt = gemini_service.build_prompt(
    message="I feel really anxious about upcoming exams",
    emotion={"emotion": "anxiety", "confidence": 0.95},
    skill=skill_obj,
    context=context
)

# Prompt becomes:
"""
You are SEEK, an empathetic emotional support assistant...

User's Emotion: anxiety (confidence: 95%)

Recommended Approach: Breathing Exercises
Tone: calm and supportive
Focus: grounding and relaxation

Relevant Information:
• Box breathing: Inhale for 4, hold for 4, exhale for 4...
• 4-7-8 breathing helps calm the nervous system...
...

User Message:
"I feel really anxious about upcoming exams"

Provide a supportive, empathetic response...
"""
```

### Step 7: Generate Response
```python
response = gemini_service.generate(prompt)

# Returns something like:
"""
I hear that exam anxiety is weighing on you. That's completely natural and 
valid. Let me share a technique that many find helpful:

Try box breathing: Breathe in for 4 counts, hold for 4, breathe out for 4, 
hold for 4. This signals your nervous system that you're safe. Try this 
a few times when you feel anxious.

Remember, you've prepared, and it's okay to feel nervous. That means you 
care about doing well. Take it one question at a time.
"""
```

### Step 8: Store & Return
```python
# Stored in MongoDB:
db.chat_history.insert_one({
  "user_id": "user_123",
  "session_id": "session_abc123",
  "message": "I feel really anxious about upcoming exams",
  "emotion": "anxiety",
  "confidence": 0.95,
  "skill": "Breathing Exercises",
  "risk_level": "low",
  "response": "I hear that exam anxiety...",
  "timestamp": datetime.now()
})

# Returned to user:
{
  "emotion": "anxiety",
  "skill": "Breathing Exercises",
  "response": "I hear that exam anxiety...",
  "risk_level": "low",
  "confidence": 0.95
}
```

## Service Interactions

### EmotionService ↔ GeminiService
```
EmotionService.detect_emotion()
    ↓
GeminiService.generate()
    ↓
Returns emotion classification
```

### SkillService ↔ skills.json
```
SkillService.get_skill("anxiety")
    ↓
Loads and searches skills.json
    ↓
Returns matching skill config
```

### RAGService ↔ Knowledge Base
```
RAGService.search()
    ↓
Searches seek_chunks.json
    ↓
Performs keyword/embedding matching
    ↓
Returns relevant chunks
```

### GeminiService ↔ Gemini API
```
GeminiService.build_prompt()
    ↓
GeminiService.generate()
    ↓
Calls Gemini API
    ↓
Returns generated text
```

## Configuration Files

### skills.json Structure
```json
{
  "skill_id": "unique_id",
  "skill": "Human Readable Name",
  "emotions": ["emotion1", "emotion2"],
  "ai_guidance": {
    "tone": "How to speak (calm, warm, etc)",
    "focus": "What to focus on"
  },
  "description": "What does this skill do"
}
```

### seek_chunks.json Structure
```json
[
  {
    "skill": "Breathing Exercises",
    "content": "The actual knowledge content",
    "topic": "Categorization"
  }
]
```

## Error Handling

### High-Risk Detection
```
message = "I want to kill myself"
    ↓
SafetyService detects risk keyword
    ↓
Returns: {"risk": "high", "needs_intervention": true}
    ↓
ChatRoute returns crisis response immediately
    ↓
Logs to risk_logs collection
```

### API Failures
```
GeminiService.generate() fails
    ↓
Except block catches error
    ↓
Returns fallback message
    ↓
Logs error for debugging
```

## Data Flow Diagram

```
Request Input
    ↓
┌─ SafetyService
│       ↓ (if risk <= moderate)
├─ EmotionService
│       ↓ (gets emotion)
├─ SkillService
│       ↓ (gets skill)
├─ RAGService
│       ↓ (gets context)
├─ GeminiService
│       ├─ build_prompt()
│       └─ generate()
├─ Database
│       ├─ chat_history
│       ├─ emotion_logs
│       └─ risk_logs (if needed)
    ↓
Response Output
```

## Performance Metrics

| Step | Service | Time | Notes |
|------|---------|------|-------|
| Safety Check | SafetyService | <5ms | Local processing |
| Emotion Detection | GeminiService | 1-2s | API call |
| Skill Mapping | SkillService | <10ms | JSON lookup |
| RAG Retrieval | RAGService | 50-200ms | Search + matching |
| Prompt Building | GeminiService | <10ms | String operations |
| Response Generation | GeminiService | 2-3s | API call |
| Database Storage | MongoDB | 10-50ms | Write operation |
| **TOTAL** | | **~4-6 seconds** | Per message |

## Testing Checklist

- [ ] Send low-risk message → Check emotion detected correctly
- [ ] Send high-risk message → Check crisis response returned
- [ ] Check chat_history collection updated
- [ ] Check emotion_logs collection updated
- [ ] Test all emotions: anxiety, stress, sadness, etc.
- [ ] Test all skills map correctly
- [ ] Get chat history endpoint works
- [ ] Get stats endpoint works
- [ ] Check RAG retrieves relevant chunks
- [ ] Check response generated empathetically
- [ ] Verify timestamps saved
- [ ] Test with multiple users/sessions

## Common Scenarios

### Scenario 1: Student with Exam Anxiety
```
Input: "I'm so stressed about my final exam"
→ Emotion: stress/anxiety (95% confidence)
→ Skill: Breathing Exercises + Cognitive Reframing
→ Context: Breathing techniques, test tips
→ Response: Calm, supportive, practical tips
```

### Scenario 2: Lonely Student
```
Input: "I feel so alone, no one understands me"
→ Emotion: loneliness (88% confidence)
→ Skill: Social Connection
→ Context: Connection tips, reaching out strategies
→ Response: Validating, encouraging connection
```

### Scenario 3: High-Risk Situation
```
Input: "I want to hurt myself"
→ Safety: HIGH RISK detected
→ Response: Crisis resources immediately
→ Storage: Logged to risk_logs
→ User gets: Hotline numbers, emergency contacts
```

### Scenario 4: General Frustration
```
Input: "Everything is going wrong"
→ Emotion: frustration/hopelessness (76% confidence)
→ Skill: Self-Compassion + Values Alignment
→ Context: Self-kindness exercises, finding meaning
→ Response: Validating, reframing perspective
```

## Database Queries

### View Recent Chats
```javascript
db.chat_history
  .find({})
  .sort({timestamp: -1})
  .limit(10)
```

### Emotion Trends
```javascript
db.emotion_logs
  .aggregate([
    {$group: {
      _id: "$emotion",
      count: {$sum: 1}
    }},
    {$sort: {count: -1}}
  ])
```

### High-Risk Incidents
```javascript
db.risk_logs.find({risk_level: "high"})
```

### User Session Analysis
```javascript
db.chat_history
  .find({user_id: "user_123", session_id: "session_abc"})
```

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Create `.env` with Gemini API key
3. Start server: `uvicorn app.main:app --reload`
4. Test endpoints with provided examples
5. Customize `skills.json` with your skills
6. Add `seek_chunks.json` with curriculum content
7. Monitor and iterate based on user feedback

## Support Resources

- **Gemini Docs**: https://ai.google.dev/tutorials
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **MongoDB Docs**: https://docs.mongodb.com/
- **FAISS Docs**: https://github.com/facebookresearch/faiss

---

**Questions?** Check ARCHITECTURE.md for detailed information about each component.
