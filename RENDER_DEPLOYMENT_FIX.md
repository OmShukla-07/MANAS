# Deployment Fixes for Render

## Changes Made:

### 1. Fixed Memory Issues
- **Workers reduced**: 2 → 1 (saves memory)
- **Timeout increased**: 30s → 120s (allows model loading)
- **Added `--preload` flag**: Loads app before forking workers

### 2. Lazy Loading
- Hugging Face model now loads only when first needed
- Reduces startup memory by ~400MB
- Prevents timeout during initialization

### 3. Health Check Endpoint
- Added `/api/health/` endpoint
- Doesn't load heavy models
- Allows Render to detect the service is running

### 4. NLP Chatbot Fallback
- Automatically uses lightweight NLP chatbot on Render
- Set via `DISABLE_HUGGINGFACE=true` environment variable
- Uses only 50MB vs 500MB for Hugging Face

### 5. Configuration
```yaml
# render.yaml updated
workers: 1
timeout: 120
threads: 2
healthCheckPath: /api/health/
```

## Deploy to Render:
```bash
git add .
git commit -m "Fix memory issues for Render deployment"
git push origin main
```

Render will auto-deploy and should work now! ✅
