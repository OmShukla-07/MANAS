# Get Your Railway Deployment URL

## Method 1: From Railway Dashboard
1. Go to https://railway.app/dashboard
2. Click on your MANAS project
3. Click on your service
4. Go to "Settings" tab
5. Find "Public Networking" section
6. Your URL will be something like: `https://your-app-name.up.railway.app`

## Method 2: From Railway CLI (if installed)
```bash
railway status
```

## Your Production URL Format
Your MANAS platform will be accessible at:
`https://[random-name].up.railway.app`

## Test Your Deployment
Once you have the URL, test these endpoints:
- `https://your-url.up.railway.app/` - Landing page
- `https://your-url.up.railway.app/admin/` - Admin panel
- `https://your-url.up.railway.app/api/v1/core/supabase/status/` - Supabase connection status