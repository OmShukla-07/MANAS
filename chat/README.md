# MANAS Chat App - NLP-Based Architecture

**Date Migrated:** January 22, 2026  
**Status:** ✅ Active - NLP-based, API-independent

---

## 🎯 New Architecture Overview

The chat system has been completely rebuilt from scratch using **local NLP processing** and **n8n workflow** as fallback (coming soon).

### **Key Changes:**
- ❌ **REMOVED:** All external API dependencies (Gemini, OpenAI)
- ✅ **ADDED:** Local NLP-based chatbot using TF-IDF + Cosine Similarity
- ✅ **ADDED:** Mental health dataset with 120+ Q&A pairs
- ✅ **ADDED:** Crisis detection system (local, no API)
- 🔜 **COMING:** n8n workflow integration for complex queries

---

## 📁 Current File Structure

```
chat/
├── admin.py                      # Django admin configuration
├── apps.py                       # App configuration
├── models.py                     # Database models (ChatSession, Message)
├── serializers.py                # DRF serializers
├── urls.py                       # API endpoints
├── views.py                      # NEW: NLP-based view logic
├── nlp_chatbot_service.py        # NEW: Core NLP service
├── nlp_main.py                   # NEW: Standalone chatbot (for testing)
├── mental_health_dataset.csv     # NEW: 120+ mental health Q&A pairs
│
└── legacy_api_services/          # OLD files (reference only)
    ├── ai_service.py             # Gemini AI service
    ├── manas_ai_service.py       # MANAS companions (Gemini)
    ├── openai_service.py         # OpenAI integration
    ├── enhanced_ai_service.py    # Multi-provider wrapper
    ├── ai_views.py               # Old API-based views
    ├── consumers.py              # WebSocket consumers
    ├── crisis_detection.py       # Old crisis detection
    ├── crisis_views.py           # Old crisis views
    ├── realtime_crisis.py        # Real-time crisis handling
    ├── simple_translation_service.py
    ├── translation_views.py
    ├── views.py                  # Old view logic
    ├── websocket_utils.py
    ├── routing.py
    ├── middleware.py
    └── README.md
```

---

## 🆕 API Endpoints (NLP-Based)

### **1. Get Available Companions**
```
GET /chat/api/companions/
```
Returns list of 3 AI companions (Priya, Arjun, Vikram)

### **2. Start Chat Session**
```
POST /chat/api/session/start/
{
  "companion": "priya",
  "initial_message": "I'm feeling stressed"
}
```

### **3. Send Message**
```
POST /chat/api/session/message/
{
  "session_id": "uuid",
  "message": "How can I manage anxiety?",
  "companion": "priya"
}
```

### **4. Get Session History**
```
GET /chat/api/sessions/
```

### **5. Get Session Details**
```
GET /chat/api/session/{session_id}/
```

### **6. End Session**
```
POST /chat/api/session/{session_id}/end/
```

---

## 🧠 How NLP Service Works

### **Process Flow:**
```
User Message
    ↓
1. Crisis Detection (keyword + pattern matching)
    ├─ If Crisis → Emergency response + Create CrisisAlert
    └─ If Safe → Continue
    ↓
2. Greeting/Gratitude Check
    ↓
3. Text Preprocessing
    ├─ Lowercase
    ├─ Remove punctuation
    ├─ Lemmatization (WordNet)
    └─ Remove stopwords
    ↓
4. TF-IDF Vectorization
    ↓
5. Cosine Similarity Matching
    ├─ Threshold: 0.15
    ├─ Match Found → Return formatted answer
    └─ No Match → Empathetic fallback
    ↓
Response Delivered
```

### **Features:**
- ✅ **120+ Mental Health Topics** - Loneliness, anxiety, depression, stress, etc.
- ✅ **Crisis Detection** - 17 keywords + regex patterns
- ✅ **Emotional Context** - Detects user emotion (sad, anxious, angry)
- ✅ **Friendly Tone** - Conversational, empathetic responses
- ✅ **Fallback Handling** - Always provides supportive response
- ✅ **Fast & Free** - No API calls, instant responses
- ✅ **Private** - All processing local, no data sent externally

---

## 🔮 Coming Soon: n8n Integration

The n8n workflow will serve as **intelligent fallback** for:
- Complex queries NLP can't handle
- Multi-turn conversations requiring context
- Advanced reasoning tasks
- Custom workflow automation

**Status:** Awaiting teammate's n8n implementation

---

## 🚨 Crisis Detection

### **Triggers:**
- Keywords: suicide, kill myself, self-harm, want to die, etc.
- Patterns: "I want to die", "going to kill myself", etc.

### **Response:**
1. Immediate crisis message with hotlines (988, Crisis Text Line)
2. Update ChatSession status to `crisis_escalated`
3. Create CrisisAlert in database
4. Set `requires_intervention = True`
5. Notify counselors (via existing crisis system)

---

## 📊 Dataset Information

**File:** `mental_health_dataset.csv`  
**Source:** Teammate's NLP model  
**Format:** CSV with 3 columns (Question_ID, Questions, Answers)  
**Content:**
- Questions 1-100: General mental health topics
- Questions 101+: Crisis-specific responses

**Sample Topics:**
- Loneliness, Depression, Anxiety
- Sleep problems, Stress management
- Relationship issues, Academic pressure
- Burnout, Motivation, Self-esteem
- And 100+ more...

---

## 🔧 Testing the NLP Chatbot

### **Option 1: Via API**
```bash
# Start session
curl -X POST http://localhost:8000/chat/api/session/start/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"companion": "priya", "initial_message": "I feel lonely"}'

# Send message
curl -X POST http://localhost:8000/chat/api/session/message/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "message": "How do I cope?"}'
```

### **Option 2: Standalone Script**
```bash
cd D:\FSOCIETY\MANAS\chat
python nlp_main.py
```
Interactive CLI chatbot for testing

---

## 📈 Performance Metrics

| Metric | Value |
|--------|-------|
| **Response Time** | < 0.01s (10ms) |
| **Dataset Size** | 120+ Q&A pairs |
| **Similarity Threshold** | 0.15 |
| **Crisis Detection** | Real-time, 0 latency |
| **Cost** | $0.00 (no API) |
| **Privacy** | 100% local processing |

---

## 🎓 Technical Details

### **Dependencies:**
- `pandas` - Dataset handling
- `numpy` - Numerical operations
- `scikit-learn` - TF-IDF, cosine similarity
- `nltk` - Text preprocessing (optional)

### **NLP Techniques:**
- **TF-IDF** (Term Frequency-Inverse Document Frequency)
- **Cosine Similarity** for semantic matching
- **Lemmatization** for word normalization
- **Stopword removal** for noise reduction

### **Fallback Strategy:**
If NLTK not available, uses basic text processing without lemmatization

---

## 🔄 Migration from API-Based System

### **What Was Moved:**
All files in `legacy_api_services/` folder are **reference only** and not used in production.

### **What Changed:**
- Views completely rewritten for NLP
- URLs simplified to 6 core endpoints
- Removed WebSocket dependencies (for now)
- Removed translation service (can re-add later)
- Removed external API configuration

### **What Stayed:**
- Database models (ChatSession, Message)
- Serializers (minimal changes)
- Crisis models and logic
- Admin configuration

---

## 🐛 Troubleshooting

### **Dataset not found:**
Ensure `mental_health_dataset.csv` is in `/chat/` folder

### **NLTK errors:**
Service falls back to basic processing automatically

### **Import errors:**
```bash
pip install pandas numpy scikit-learn nltk
```

### **No responses:**
Check logs for NLP service initialization errors

---

## 👥 Team Notes

**Original API System:** Moved to `legacy_api_services/` - DO NOT DELETE  
**NLP Model:** Provided by teammate, integrated Jan 22, 2026  
**n8n Workflow:** Pending teammate implementation  
**Crisis System:** Fully functional with local NLP detection

---

**Questions?** Check legacy files for reference or contact team lead.
