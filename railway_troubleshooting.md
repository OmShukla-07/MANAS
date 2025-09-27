# Quick Fix for Railway Deployment

## If you're still getting "site can't be reached", add this environment variable:

ALLOWED_HOSTS=manas-production.up.railway.app,*.up.railway.app,localhost,127.0.0.1

## Or update your Django settings to handle Railway URLs better:

1. Go to Variables tab in Railway
2. Add: RAILWAY_STATIC_URL=manas-production.up.railway.app
3. Make sure PORT=8000 is set (Railway usually handles this automatically)

## Check Deployment Logs:
1. Go to "Observability" tab
2. Click "Logs" 
3. Look for errors like:
   - "Port already in use"
   - "Database connection failed"
   - "Module not found"
   - "Environment variable missing"

## Test Commands (after variables are added):
curl https://manas-production.up.railway.app/
curl https://manas-production.up.railway.app/api/v1/core/supabase/status/