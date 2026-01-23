"""
Simple FastAPI server for Hugging Face model inference
This runs on HF Space and provides AI predictions via API
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import logging
import re

app = FastAPI(title="MANAS AI Model API")
logger = logging.getLogger(__name__)

# Global model instance (loaded once on startup)
emotion_pipeline = None

class PredictionRequest(BaseModel):
    text: str
    max_length: int = 512

class PredictionResponse(BaseModel):
    emotion: str
    confidence: float
    is_crisis: bool
    all_scores: list

@app.on_event("startup")
async def load_model():
    """Load model on startup"""
    global emotion_pipeline
    try:
        logger.info("Loading emotion classification model...")
        emotion_pipeline = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None
        )
        logger.info("✅ Model loaded successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MANAS AI Model API",
        "model": "emotion-english-distilroberta-base"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "model_loaded": emotion_pipeline is not None}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
