# 🔧 Railway Deployment Troubleshooting

## 🚨 **Common Issues & Solutions:**

### **1. "Application failed to respond"**
**Cause:** ALLOWED_HOSTS not including Railway domain
**Solution:** 
```bash
ALLOWED_HOSTS=localhost,127.0.0.1,.up.railway.app,.railway.app
```

### **2. "Static files not loading (CSS/JS missing)"**
**Cause:** WhiteNoise not configured properly
**Solution:** Already fixed in our code - should work automatically

### **3. "Database connection errors"**
**Cause:** Using old IPv6 endpoint
**Solution:** Verify DATABASE_URL uses IPv4 pooler:
```bash
DATABASE_URL=postgresql://postgres.llkdmzdhnppvnlclcapv:[password]@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
```

### **4. "404 on frontend pages"**
**Cause:** Frontend URLs only in DEBUG mode
**Solution:** Already fixed - frontend URLs now available in production

## 📊 **Expected Deployment Flow:**

1. **Build Phase** (2-3 minutes):
   ```
   Installing dependencies...
   Collecting static files... (192 files)
   Running migrations...
   ```

2. **Deploy Phase** (1-2 minutes):
   ```
   Starting gunicorn...
   Listening on port 8080...
   ```

3. **Success Indicators**:
   ```
   ✅ Build completed
   ✅ Deploy completed  
   ✅ Healthy
   ```

## 🌐 **Testing Checklist:**

- [ ] Landing page loads with styling
- [ ] Login page accessible
- [ ] Student dashboard redirects properly
- [ ] Admin panel accessible
- [ ] No console errors for static files
- [ ] Database queries working

## 🆘 **If Still Having Issues:**

1. **Check Railway Logs:**
   - Go to Railway Dashboard
   - Click "View Logs" 
   - Look for error messages

2. **Verify Environment Variables:**
   - All 10+ variables set correctly
   - No typos in ALLOWED_HOSTS
   - PORT set to 8080

3. **Domain Issues:**
   - Check "Domains" tab in Railway
   - Ensure public domain is generated
   - Try both HTTP and HTTPS