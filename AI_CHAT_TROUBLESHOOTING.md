# 🤖 AI Chat Troubleshooting Guide

## 🚨 **Current AI Issues from Railway Logs:**

```
❌ WARNING Unauthorized: /api/v1/chat/translation/languages/
❌ WARNING Bad Request: /api/v1/chat/manas/sessions/.../message/
```

## 🔧 **Required Railway Environment Variables for AI:**

### **1. Supabase Configuration (CRITICAL):**
```bash
# Fix the Supabase URL (currently wrong)
SUPABASE_URL=https://llkdmzdhnppvnlclcapv.supabase.co
# NOT: postgresql://postgres... (that's DATABASE_URL)

# Add missing Supabase keys
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxsa2RtemRobnBwdm5sY2xjYXB2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5OTk4MTIsImV4cCI6MjA3NDU3NTgxMn0.vbx8DmTi5M2Fi7o6YZimzY2nZEVoABiLIFHwe63k6tI

SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxsa2RtemRobnBwdm5sY2xjYXB2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODk5OTgxMiwiZXhwIjoyMDc0NTc1ODEyfQ.HnX6EigrszqrWe1t30JaESzvnq5cU1O0wqLHTMZxB6g
```

### **2. OpenAI Configuration (Optional but Recommended):**
```bash
# Add OpenAI API key for enhanced AI features
OPENAI_API_KEY=[your-openai-api-key-if-you-have-one]
```

## 🎯 **Step-by-Step Fix:**

### **Step 1: Fix Supabase URL**
1. Go to **Railway Dashboard** → **Variables**
2. **Find SUPABASE_URL** variable
3. **Change from:** `postgresql://postgres...` 
4. **Change to:** `https://llkdmzdhnppvnlclcapv.supabase.co`

### **Step 2: Add Missing Variables**
Add these new variables:
- `SUPABASE_KEY` = [anon key from above]
- `SUPABASE_SERVICE_ROLE_KEY` = [service key from above]

### **Step 3: Test After Redeploy**
After Railway redeploys (2-3 minutes):
1. Login to your app
2. Try the AI chat feature
3. Check Railway logs for success

## 📊 **Expected Results After Fix:**

### **Before (Current):**
```
❌ WARNING Unauthorized: /api/v1/chat/translation/languages/
❌ WARNING Bad Request: /api/v1/chat/manas/sessions/.../message/
```

### **After (Fixed):**
```
✅ INFO Supabase client initialized successfully
✅ INFO AI chat session created
✅ INFO Message processed successfully
```

## 🧪 **Test AI Features:**

Once fixed, test these:
- **MANAS AI Chat** - Should respond to messages
- **Language Translation** - Should work without "Unauthorized"
- **Session Management** - Should create/maintain chat sessions

## ⚠️ **If Still Not Working:**

The AI might also need:
1. **OpenAI API key** (for advanced AI responses)
2. **Proper user authentication** (make sure you're logged in)
3. **Supabase RLS policies** (database permissions)

## 🎯 **Priority Actions:**

1. **Fix SUPABASE_URL** (most critical)
2. **Add missing Supabase keys**
3. **Test AI chat after redeploy**
4. **Add OpenAI key if needed**

**Your app is working great! Just need to fix the AI configuration.** 🚀