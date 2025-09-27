# Required Environment Variables for Railway

## Go to Railway Dashboard → Your Project → Variables Tab

Add these environment variables:

### Essential Variables
```
DEBUG=False
ALLOWED_HOSTS=your-railway-url.up.railway.app,127.0.0.1,localhost
SECRET_KEY=your-super-secret-django-key-here
```

### Supabase Configuration
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

### Database Configuration (Already using Supabase PostgreSQL)
```
DATABASE_URL=postgresql://[user]:[password]@[host]:[port]/[database]
```

### AI Service Keys (Optional - for AI features)
```
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
```

### Email Configuration (Optional)
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

## How to Add Variables in Railway:
1. Go to https://railway.app/dashboard
2. Click on your MANAS project
3. Click on your service
4. Go to "Variables" tab
5. Click "New Variable"
6. Add each variable name and value