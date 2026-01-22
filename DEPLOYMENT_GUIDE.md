# MANAS - Mental Health Support Platform

## 🚀 Render Deployment Guide

### Prerequisites
1. GitHub account with repository
2. Render.com account (free)
3. Google Gemini API key ([Get here](https://aistudio.google.com/app/apikey))

### Step-by-Step Deployment

#### 1. Prepare Repository
```bash
# Commit all changes
git add -A
git commit -m "Production ready for Render deployment"
git push origin main
```

#### 2. Deploy on Render

1. **Go to [Render Dashboard](https://dashboard.render.com/)**

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the MANAS repository

3. **Configure Web Service**
   - **Name**: `manas-mental-health`
   - **Region**: Singapore (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command**: 
     ```bash
     gunicorn manas_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
     ```
   - **Plan**: Free

4. **Add Environment Variables** (in Environment tab)
   - `PYTHON_VERSION` = `3.12.0`
   - `DEBUG` = `False`
   - `RENDER` = `true`
   - `SECRET_KEY` = (Click "Generate" button)
   - `ALLOWED_HOSTS` = `*.onrender.com`
   - `GEMINI_API_KEY` = (Your Google Gemini API key)
   - `DATABASE_URL` = (Auto-added when you create database below)

5. **Create PostgreSQL Database**
   - In same Render dashboard, click "New +" → "PostgreSQL"
   - **Name**: `manas-postgres`
   - **Database**: `manas_db`
   - **User**: `manas_user`
   - **Region**: Singapore
   - **Plan**: Free
   - Click "Create Database"
   - Copy the **Internal Database URL**

6. **Link Database to Web Service**
   - Go back to your Web Service
   - In Environment tab, add:
     - `DATABASE_URL` = (Paste the Internal Database URL)

7. **Deploy!**
   - Click "Manual Deploy" → "Deploy latest commit"
   - Wait 5-10 minutes for first deployment
   - Your app will be live at: `https://manas-mental-health.onrender.com`

### Important Notes

⚠️ **Free Tier Limitations:**
- Spins down after 15 minutes of inactivity
- First request after spin-down takes 50+ seconds
- 750 hours/month free

✅ **What's Included:**
- Hugging Face AI emotion detection
- Multi-language support (18 languages)
- Chat history persistence
- Crisis detection system
- PostgreSQL database

### Post-Deployment

1. **Create Admin User** (via Render Shell):
   ```bash
   python manage.py createsuperuser
   ```

2. **Access Admin Panel**:
   - Visit: `https://your-app.onrender.com/admin/`

3. **Test the App**:
   - Visit: `https://your-app.onrender.com/`
   - Sign up as student
   - Test MANAS AI chat

### Troubleshooting

**Build Fails:**
- Check requirements.txt has all dependencies
- Check Python version matches (3.12.0)

**Database Connection Error:**
- Verify DATABASE_URL is set correctly
- Make sure PostgreSQL instance is running

**Static Files Not Loading:**
- Check ALLOWED_HOSTS includes `*.onrender.com`
- Verify collectstatic ran in build command

**AI Not Responding:**
- Verify GEMINI_API_KEY is set
- Check API key is valid at Google AI Studio

### Need Help?
- Check Render logs: Dashboard → Logs tab
- View Django errors in real-time
- Contact: [Your email/GitHub issues]

---

## Features
- 🤖 AI-powered emotional support (Hugging Face transformers)
- 🌍 18 language support
- 💬 Chat history with sessions
- 🚨 Crisis detection and alerts
- 👤 User profiles with avatars
- 📊 Counselor dashboard

## Tech Stack
- Django 5.2.6
- PostgreSQL (Render)
- Hugging Face Transformers
- Gunicorn WSGI server
- Bootstrap 5 UI
