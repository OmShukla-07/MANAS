---
title: MANAS AI Model API
emoji: 🧠
colorFrom: green
colorTo: green
sdk: docker
sdk_version: "4.36.0"
app_file: app_hf.py
app_port: 7860
pinned: false
license: mit
---

# MANAS AI Model API

This Space provides **AI model inference only** for the MANAS Mental Health Platform.

## 🎯 What This Does
This is the **AI brain** of MANAS - it:
- Receives text input via API
- Analyzes emotion using BERT
- Detects crisis situations
- Returns predictions to the main app

## 🔌 API Endpoints

### `POST /predict`
```json
{
  "text": "I'm feeling anxious about my exams"
}
```

**Response:**
```json
{
  "emotion": "fear",
  "confidence": 0.87,
  "is_crisis": false,
  "all_scores": [...]
}
```

### `GET /health`
Check if model is loaded

## 🌐 Integration
The main MANAS app on Render calls this API for all AI predictions.

**Main App:** https://manas-mental-health.onrender.com
**AI API:** https://huggingface.co/spaces/OmShukla16/Manas-edu
