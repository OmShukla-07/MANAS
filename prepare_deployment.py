#!/usr/bin/env python3
"""
Production deployment script for MANAS
Prepares the app for deployment on Railway, Render, or similar platforms
"""
import os
import subprocess
import sys

def update_settings_for_production():
    """Update Django settings for production deployment"""
    
    settings_updates = """
# Add this to your manas_backend/settings.py for production

# Production Security Settings
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 31536000
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# Static Files Configuration for Production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add WhiteNoise to Middleware (add after SecurityMiddleware)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Production Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
"""
    
    print("📋 Production Settings Configuration:")
    print(settings_updates)
    print("\n✅ Copy the above settings to your manas_backend/settings.py")

def create_production_env_template():
    """Create production environment template"""
    
    prod_env = """# Production Environment Variables
# Set these in your Railway/Render dashboard

DEBUG=False
SECRET_KEY=your-super-secret-production-key-here-change-this
ALLOWED_HOSTS=*.railway.app,*.render.com,your-domain.com

# Database (Your Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:your-password@db.llkdmzdhnppvnlclcapv.supabase.co:5432/postgres

# Supabase Configuration
SUPABASE_URL=https://llkdmzdhnppvnlclcapv.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# AI Configuration
GEMINI_API_KEY=your-gemini-key
GEMINI_API_KEY_BACKUP=your-backup-gemini-key
OPENAI_API_KEY=your-openai-key

# Optional: Translation
GOOGLE_TRANSLATE_API_KEY=your-google-translate-key
GOOGLE_TRANSLATE_PROJECT_ID=your-project-id

# Frontend
FRONTEND_URL=https://your-frontend-domain.com
"""
    
    with open('.env.production', 'w') as f:
        f.write(prod_env)
    
    print("✅ Created .env.production template")
    print("📝 Update the values and use them in your deployment platform")

def main():
    """Main deployment preparation function"""
    print("🚀 MANAS Production Deployment Preparation")
    print("=" * 50)
    
    print("\n1. 📋 Production Settings Guide:")
    update_settings_for_production()
    
    print("\n2. 🔧 Environment Variables Template:")
    create_production_env_template()
    
    print("\n3. 📦 Deployment Files Status:")
    files_to_check = [
        'requirements.txt',
        'railway.toml', 
        'wsgi.py',
        'FREE_DEPLOYMENT_GUIDE.md'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Follow FREE_DEPLOYMENT_GUIDE.md")
    print("2. Use Railway.app (recommended)")
    print("3. Set environment variables in platform dashboard")
    print("4. Deploy and test your live app!")
    print("\n🚀 Your MANAS platform will be live in minutes!")

if __name__ == "__main__":
    main()