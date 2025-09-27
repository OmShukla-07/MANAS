# 🚨 Railway Server Error 500 - Diagnostic Guide

## 🔍 **Check Railway Logs Immediately:**

1. **Railway Dashboard** → **Your MANAS Project** → **"Logs" tab**
2. **Look for these error patterns:**

### **Common Error Patterns to Find:**

```bash
# Database Errors:
❌ "django.db.utils.OperationalError"
❌ "could not translate host name"
❌ "connection refused"

# Environment Variable Errors:
❌ "DisallowedHost"
❌ "Invalid URL"
❌ "KeyError: 'SUPABASE_PROJECT_URL'"

# Template Errors:
❌ "TemplateDoesNotExist"
❌ "NoReverseMatch"

# Import Errors:
❌ "ModuleNotFoundError"
❌ "ImportError"
```

## 🔧 **Quick Fixes Based on Error Type:**

### **1. If "DisallowedHost" Error:**
**Missing:** `ALLOWED_HOSTS` in Railway variables
**Add:** `ALLOWED_HOSTS=localhost,127.0.0.1,.up.railway.app,.railway.app`

### **2. If Database Connection Error:**
**Check Railway Variables:**
```bash
DATABASE_URL=postgresql://postgres.llkdmzd...@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
```

### **3. If "Invalid URL" (Supabase):**
**Missing:** Supabase environment variables
**Add to Railway:**
```bash
SUPABASE_PROJECT_URL=https://llkdmzdhnppvnlclcapv.supabase.co
SUPABASE_API_KEY=[your-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[your-service-key]
```

### **4. If Template Error:**
**Check:** Frontend views trying to load missing templates

## 🎯 **Expected Railway Variables (Complete List):**

```bash
# Core Django
DEBUG=False
SECRET_KEY=[your-secret-key]
ALLOWED_HOSTS=localhost,127.0.0.1,.up.railway.app,.railway.app
PORT=8080

# Database
DATABASE_URL=postgresql://postgres.llkdmzdhnppvnlclcapv:[password]@aws-1-ap-south-1.pooler.supabase.com:6543/postgres

# Supabase (for AI features)
SUPABASE_PROJECT_URL=https://llkdmzdhnppvnlclcapv.supabase.co
SUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optional
OPENAI_API_KEY=[if-you-have-one]
```

## 🆘 **Immediate Action Plan:**

1. **Check Railway Logs** - Find the exact error message
2. **Verify Environment Variables** - Make sure all required variables are set
3. **Test Simple URL** - Try `/admin/` to see if it's a specific view issue

## 📊 **Debugging Steps:**

### **Step 1: Try Admin URL**
Visit: `https://manas-production-7ee4.up.railway.app/admin/`
- If this works → Frontend view issue
- If this fails → Core Django/database issue

### **Step 2: Check Environment Variables**
In Railway dashboard, verify you have **at least 8-10 variables** set

### **Step 3: Look at Latest Logs**
The logs will show the exact Python error causing the 500

## 🎯 **What to Tell Me:**

**Please check your Railway logs and tell me:**
1. What **exact error message** appears after gunicorn starts?
2. Do you have **ALLOWED_HOSTS** set in Railway variables?
3. How many **environment variables** do you see in Railway?

This will help me give you the exact fix needed!