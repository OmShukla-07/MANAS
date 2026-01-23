"""
MANAS AI Model API - Emotion Detection + Conversational AI
This runs on HF Space and provides AI predictions via API
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import logging

app = FastAPI(title="MANAS AI Model API")
logger = logging.getLogger(__name__)

# Global model instances (loaded once on startup)
emotion_pipeline = None
conversational_pipeline = None

class PredictionRequest(BaseModel):
    text: str
    max_length: int = 512

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []
    max_length: int = 80

class PredictionResponse(BaseModel):
    emotion: str
    confidence: float
    is_crisis: bool
    all_scores: list

class ChatResponse(BaseModel):
    response: str
    emotion: str
    confidence: float

@app.on_event("startup")
async def load_model():
    """Load models on startup"""
    global emotion_pipeline, conversational_pipeline
    try:
        logger.info("Loading emotion classification model...")
        emotion_pipeline = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None
        )
        logger.info("✅ Emotion model loaded!")
        
        logger.info("Loading conversational model...")
        conversational_pipeline = pipeline(
            "text-generation",
            model="microsoft/DialoGPT-small"  # Small version for faster loading
        )
        logger.info("✅ Conversational model loaded!")
        
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MANAS AI Model API",
        "models": {
            "emotion": "emotion-english-distilroberta-base",
            "conversation": "DialoGPT-small"
        }
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok", 
        "emotion_loaded": emotion_pipeline is not None,
        "conversation_loaded": conversational_pipeline is not None
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Get emotion prediction for text
    
    Args:
        text: Input text to analyze
        
    Returns:
        Emotion classification with confidence scores
    """
    if not emotion_pipeline:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Crisis detection keywords
        crisis_keywords = [
            'suicide', 'suicidal', 'kill myself', 'end my life', 'want to die',
            'better off dead', 'hurt myself', 'self harm'
        ]
        
        # Check for crisis
        text_lower = request.text.lower()
        is_crisis = any(keyword in text_lower for keyword in crisis_keywords)
        
        # Get emotion prediction
        result = emotion_pipeline(request.text, truncation=True, max_length=request.max_length)
        
        # Parse results
        if isinstance(result[0], list):
            scores = sorted(result[0], key=lambda x: x['score'], reverse=True)
            top_emotion = scores[0]['label']
            confidence = scores[0]['score']
            all_scores = [{"label": s['label'], "score": s['score']} for s in scores]
        else:
            top_emotion = result[0]['label']
            confidence = result[0]['score']
            all_scores = [{"label": result[0]['label'], "score": result[0]['score']}]
        
        return PredictionResponse(
            emotion=top_emotion,
            confidence=confidence,
            is_crisis=is_crisis,
            all_scores=all_scores
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Generate conversational AI response
    
    Args:
        message: Current user message
        conversation_history: Previous messages (list of dicts with role/content)
        max_length: Maximum response length
        
    Returns:
        AI-generated response with emotion analysis
    """
    if not conversational_pipeline or not emotion_pipeline:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    try:
        # Get emotion first
        emotion_result = emotion_pipeline(request.message, truncation=True)
        if isinstance(emotion_result[0], list):
            emotion = emotion_result[0][0]['label']
            confidence = emotion_result[0][0]['score']
        else:
            emotion = emotion_result[0]['label']
            confidence = emotion_result[0]['score']
        
        # Build conversation context
        context = ""
        if request.conversation_history:
            # Include last 4 messages for context
            recent = request.conversation_history[-4:]
            for msg in recent:
                content = msg.get('content', '')[:100]  # Limit each message
                context += content + " "
        
        # Add current message
        full_input = (context + request.message).strip()
        
        # Generate response
        result = conversational_pipeline(
            full_input,
            max_length=len(full_input.split()) + request.max_length,
            num_return_sequences=1,
            pad_token_id=50256,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.2
        )
        
        response_text = result[0]['generated_text']
        
        # Extract only the new generated part (remove input context)
        if full_input in response_text:
            response_text = response_text.replace(full_input, '').strip()
        
        # Clean up response
        response_text = response_text.split('\n')[0].strip()  # Take first line
        
        if not response_text or len(response_text) < 5:
            response_text = "I'm here to listen. Tell me more about what you're experiencing."
        
        return ChatResponse(
            response=response_text,
            emotion=emotion,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
