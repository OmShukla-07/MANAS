# 🚀 MANAS Supabase Integration Guide

## Overview
Supabase is a PostgreSQL-based backend-as-a-service that provides a production-ready database with real-time features, authentication, and file storage. This guide will help you integrate Supabase with your MANAS platform.

## 📋 Prerequisites
- Python 3.8+ with Django 5.2.6
- MANAS backend properly set up
- Supabase account (free tier available)

## 🔧 Step-by-Step Setup

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in to your account
3. Click **"New Project"**
4. Choose your organization
5. Set project name: `manas-production`
6. Generate a strong database password (save this!)
7. Select region closest to your users
8. Click **"Create new project"**

### 2. Get Project Credentials
1. Go to **Project Settings** → **API**
2. Copy the following values:
   - **Project URL**: `https://your-project-ref.supabase.co`
   - **anon public key**: Used for frontend/user operations
   - **service_role key**: Used for admin operations (keep secret!)

### 3. Get Database Connection String
1. Go to **Project Settings** → **Database**
2. Copy the **Connection string** → **URI**
3. It looks like: `postgresql://postgres:[password]@[host]:[port]/postgres`
4. Replace `[password]` with your database password

### 4. Update Environment Variables
Create or update your `.env` file with:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Database URL (PostgreSQL)
DATABASE_URL=postgresql://postgres:your-password@your-host:5432/postgres

# Keep existing configurations
GOOGLE_API_KEY=your_google_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
DEBUG=False
SECRET_KEY=your-super-secret-key-here
```

### 5. Install Dependencies
Dependencies are already included! If needed:
```bash
pip install supabase psycopg2-binary python-decouple dj-database-url
```

### 6. Run Migration Command
Execute the automated setup:
```bash
python manage.py setup_supabase
```

This command will:
- Test Supabase connection
- Run Django migrations
- Create database tables
- Verify AI system
- Create superuser if needed

### 7. Verify Setup
1. Check the admin dashboard: `/admin/supabase/dashboard/`
2. Test API endpoint: `/api/v1/core/supabase/status/`
3. Verify tables in Supabase dashboard
4. Test MANAS AI companions

## 🛠️ Manual Commands

### Check Supabase Status Only
```bash
python manage.py setup_supabase --check-only
```

### Force Migration (if errors)
```bash
python manage.py setup_supabase --force
```

### Standard Django Operations
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

## 🌟 Features Enabled

### ✅ Production Database
- PostgreSQL with automatic backups
- Connection pooling and optimization
- Horizontal scaling capabilities
- 99.9% uptime SLA

### ✅ Real-time Features
- Live chat message updates
- Crisis alert notifications
- System status monitoring
- User activity tracking

### ✅ Built-in Security
- Row-level security (RLS)
- JWT-based authentication
- SSL/TLS encryption
- IP whitelisting support

### ✅ File Storage
- CDN-backed storage
- Image optimization
- Direct uploads from frontend
- Automatic backups

### ✅ Database Dashboard
- Visual query builder
- Table editor
- Performance monitoring
- User management

## 🔍 Troubleshooting

### Connection Failed
- **Issue**: `connection to server failed`
- **Solution**: Check DATABASE_URL and ensure your IP is whitelisted in Supabase Project Settings → Authentication → URL Configuration

### Migration Errors
- **Issue**: `relation already exists`
- **Solution**: Database not empty. Use `--force` flag or reset database

### Authentication Errors
- **Issue**: `JWT invalid`
- **Solution**: Verify SUPABASE_SERVICE_ROLE_KEY is correct and hasn't been regenerated

### Performance Issues
- **Issue**: Slow database queries
- **Solution**: Ensure database region matches your deployment region

### Import Errors
- **Issue**: `No module named 'supabase'`
- **Solution**: Run `pip install supabase psycopg2-binary`

## 📊 Monitoring & Maintenance

### Database Health
Monitor your database in Supabase dashboard:
- Query performance
- Connection usage
- Storage usage
- API requests

### Backup Strategy
Supabase automatically:
- Creates daily backups
- Retains backups for 7 days (free tier)
- Provides point-in-time recovery

### Scaling
- **Vertical**: Upgrade compute in Project Settings
- **Horizontal**: Enable read replicas
- **Storage**: Automatically scales

## 🚀 Production Deployment

### Environment Variables for Production
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://postgres:password@host:port/postgres
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SECRET_KEY=your-super-secret-production-key
```

### SSL Configuration
Supabase provides SSL by default. Ensure your Django settings:
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Final Checklist
- [ ] Supabase project created
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] AI system functional
- [ ] Real-time features tested
- [ ] SSL/HTTPS enabled
- [ ] Backups verified
- [ ] Monitoring set up

## 💡 Benefits of Supabase Integration

1. **Reliability**: 99.9% uptime with automatic failover
2. **Performance**: Optimized PostgreSQL with global CDN
3. **Security**: Enterprise-grade security features
4. **Scalability**: Automatic scaling based on usage
5. **Real-time**: WebSocket support for live features
6. **Cost-effective**: Free tier for development, pay-as-you-scale
7. **Developer Experience**: Intuitive dashboard and APIs
8. **Backup & Recovery**: Automated backups and point-in-time recovery

## 🆘 Support
- **Supabase Documentation**: [docs.supabase.com](https://docs.supabase.com)
- **MANAS Support**: Check our GitHub issues
- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com)

---

## ✅ Success! 
Your MANAS platform is now powered by Supabase with enterprise-grade database infrastructure, real-time capabilities, and production-ready scaling! 🎉