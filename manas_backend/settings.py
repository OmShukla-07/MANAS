"""
Django settings for MANAS Mental Health Platform Backend.

Production-ready configuration with Supabase PostgreSQL, Redis caching,
WebSocket support, JWT authentication, and deployment optimization.
"""

import os
from pathlib import Path

# Enhanced environment variable loading for Railway and other platforms
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from decouple import config
except ImportError:
    def config(key, default=None, cast=None):
        """Fallback config function that supports cast parameter"""
        value = os.environ.get(key, default)
        if cast and value is not None:
            try:
                return cast(value)
            except (ValueError, TypeError):
                return default
        return value

# Import required for database configuration
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY') or config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes') if os.environ.get('DEBUG') else config('DEBUG', default=True, cast=bool)

# Render.com, Railway, and Hugging Face Space deployment support
if os.environ.get('RENDER'):
    ALLOWED_HOSTS = ['*']  # Render handles HTTPS termination
elif os.environ.get('RAILWAY_ENVIRONMENT'):
    ALLOWED_HOSTS = ['*']  # Railway handles HTTPS termination
elif os.environ.get('SPACE_ID'):  # Hugging Face Space
    ALLOWED_HOSTS = ['*']  # HF Space handles HTTPS termination
else:
    ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if os.environ.get('ALLOWED_HOSTS') else config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])


# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'django_celery_beat',
]

LOCAL_APPS = [
    'accounts',
    'chat',
    'appointments',
    'crisis',
    'core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files for production
    'corsheaders.middleware.CorsMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "manas_backend.urls"

# Django Channels ASGI Configuration
ASGI_APPLICATION = "manas_backend.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "manas_backend.wsgi.application"

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',  # Custom email authentication
    'django.contrib.auth.backends.ModelBackend',  # Default fallback
]


# Database Configuration
# Production: Supabase PostgreSQL, Development: SQLite
DATABASE_URL = os.environ.get('DATABASE_URL') or config('DATABASE_URL', default='sqlite:///db.sqlite3')

if DATABASE_URL.startswith('sqlite'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================================================================
# DJANGO REST FRAMEWORK CONFIGURATION
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# ==============================================================================
# JWT AUTHENTICATION CONFIGURATION
# ==============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ==============================================================================
# REDIS & CACHING CONFIGURATION
# ==============================================================================

REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Use different caching backends for development vs production
if DEBUG:
    # Use in-memory cache for development (no Redis required)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    # Use database sessions for development
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
else:
    # Use database cache for production (Railway compatible)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
        }
    }
    # Use database sessions for production (Railway compatible)
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ==============================================================================
# CHANNELS & WEBSOCKET CONFIGURATION
# ==============================================================================

# Use in-memory channel layer for development (Redis for production)
if DEBUG:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
else:
    # Use in-memory channels for production (Railway compatible)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ==============================================================================
# CELERY CONFIGURATION
# ==============================================================================

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ==============================================================================
# AI INTEGRATION CONFIGURATION
# ==============================================================================

# Google Gemini AI
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or config('GEMINI_API_KEY', default='')
GEMINI_API_KEY_BACKUP = os.environ.get('GEMINI_API_KEY_BACKUP') or config('GEMINI_API_KEY_BACKUP', default='')
GEMINI_MODEL = 'gemini-pro'
GEMINI_MODEL_ADVANCED = config('GEMINI_MODEL_ADVANCED', default='gemini-pro')

# Google Cloud Translation API
GOOGLE_TRANSLATE_API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY') or config('GOOGLE_TRANSLATE_API_KEY', default='')
GOOGLE_TRANSLATE_PROJECT_ID = os.environ.get('GOOGLE_TRANSLATE_PROJECT_ID') or config('GOOGLE_TRANSLATE_PROJECT_ID', default='')

# AI Chatbot Models Configuration
AI_CHATBOT_MODELS = {
    'supportive': {
        'name': 'Supportive Companion',
        'personality': 'empathetic, encouraging, gentle',
        'approach': 'validation and support focused'
    },
    'analytical': {
        'name': 'Analytical Guide', 
        'personality': 'logical, structured, solution-oriented',
        'approach': 'problem-solving and goal-setting focused'
    },
    'mindful': {
        'name': 'Mindfulness Coach',
        'personality': 'calm, present-focused, wisdom-oriented',
        'approach': 'mindfulness and self-awareness focused'
    }
}

# OpenAI (Backup)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or config('OPENAI_API_KEY', default='')

# ==============================================================================
# STATIC FILES & MEDIA CONFIGURATION
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files directories
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# WhiteNoise configuration for static files (production)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'manas_backend.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'manas_backend': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': True,
        },
    },
}

# ==============================================================================
# SECURITY CONFIGURATION
# ==============================================================================

if not DEBUG:
    # HTTPS settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_REDIRECT_EXEMPT = []
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_SSL_REDIRECT = False  # Railway handles HTTPS termination
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Railway proxy
    
    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_AGE = 3600  # 1 hour
    
    # CSRF protection
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True

# ==============================================================================
# INTERNATIONALIZATION & LOCALIZATION
# ==============================================================================

# Support for multiple languages
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('hi', 'Hindi'),
    ('zh', 'Chinese'),
]

# Default language for AI responses
DEFAULT_LANGUAGE = 'en'

# ==============================================================================
# CUSTOM MANAS SETTINGS
# ==============================================================================

# Crisis detection settings
CRISIS_KEYWORDS = [
    'suicide', 'kill myself', 'end it all', 'no point living',
    'self harm', 'hurt myself', 'can\'t go on', 'hopeless',
    'want to die', 'better off dead', 'end my life'
]

CRISIS_ESCALATION_THRESHOLD = config('CRISIS_ESCALATION_THRESHOLD', default=0.7, cast=float)

CRISIS_SEVERITY_LEVELS = [
    ('low', 'Low'),
    ('medium', 'Medium'), 
    ('high', 'High'),
    ('critical', 'Critical'),
]

# Wellness tracking settings
MOOD_SCALE_RANGE = (1, 10)
WELLNESS_STREAK_RESET_HOURS = 36  # Reset streak if no activity for 36 hours

# Analytics settings
ANALYTICS_RETENTION_DAYS = 365  # Keep analytics data for 1 year
DASHBOARD_REFRESH_INTERVAL = 30  # seconds

# Frontend URL for CORS and redirects
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')
