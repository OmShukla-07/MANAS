# 🚀 Free Production Deployment Guide

## Your Best Options (No Credit Card Required):

### 🏆 **Option 1: Railway.app (RECOMMENDED)**

**Why Railway is Perfect:**
- ✅ No credit card required
- ✅ $5/month free credits  
- ✅ PostgreSQL included
- ✅ Auto-detects Django
- ✅ GitHub integration

**Deploy Steps:**
1. **Go to**: https://railway.app
2. **Sign up with GitHub** (no card needed)
3. **New Project** → **Deploy from GitHub**
4. **Select your MANAS repository**
5. **Railway automatically detects Django and deploys!**

**Environment Variables to Set in Railway:**
```
SUPABASE_URL=https://llkdmzdhnppvnlclcapv.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:password@db.llkdmzdhnppvnlclcapv.supabase.co:5432/postgres
DEBUG=False
ALLOWED_HOSTS=*.railway.app,your-custom-domain.com
SECRET_KEY=your-production-secret-key
```

---

### 🥈 **Option 2: Render.com**

**Deploy Steps:**
1. **Go to**: https://render.com  
2. **Sign up with GitHub**
3. **New Web Service** → **Connect Repository**
4. **Settings:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python manage.py migrate && gunicorn manas_backend.wsgi:application`
   - **Python Version**: 3.11

---

### 🥉 **Option 3: Heroku (Free Tier Alternative)**

Use **Railway** or **Render** instead - they're better for Django apps and don't require cards.

---

## 🔧 **Pre-Deployment Checklist:**

### ✅ **Your Django App is Ready:**
- ✅ Supabase PostgreSQL configured
- ✅ Production dependencies in requirements.txt
- ✅ gunicorn included for WSGI server
- ✅ Environment variables properly set
- ✅ Static files configuration ready

### ✅ **What Happens During Deployment:**
1. **Railway/Render pulls your code** from GitHub
2. **Installs dependencies** from requirements.txt  
3. **Runs migrations** to set up database tables
4. **Collects static files** for CSS/JS/images
5. **Starts gunicorn server** to serve your app
6. **Provides you a live URL!**

---

## 🎯 **After Deployment:**

### **Test Your Live App:**
- **Homepage**: `https://your-app.railway.app/`
- **Admin Panel**: `https://your-app.railway.app/admin/`
- **AI Chat**: `https://your-app.railway.app/student/manas-ai/`
- **API Status**: `https://your-app.railway.app/api/v1/core/supabase/status/`

### **Custom Domain (Optional):**
- Both Railway and Render support custom domains
- Add your domain in platform settings
- Update ALLOWED_HOSTS in environment variables

---

## 💡 **Pro Tips:**

1. **Use Railway** - it's the easiest for Django + PostgreSQL
2. **Environment variables** are set in the platform dashboard
3. **Monitor usage** - free tiers have limits but are generous
4. **Upgrade later** - when you need more resources
5. **SSL/HTTPS** - automatically provided by both platforms

---

## 🚨 **If You Get Stuck:**

1. **Check logs** in Railway/Render dashboard
2. **Verify environment variables** are set correctly  
3. **Ensure Supabase connection** is working
4. **Check ALLOWED_HOSTS** includes your deployment domain

---

## 🎉 **Ready to Deploy?**

**Choose Railway.app** and follow the steps above - you'll have your MANAS platform live in under 10 minutes! 🚀

Your mental health platform will be helping students worldwide! 🌟