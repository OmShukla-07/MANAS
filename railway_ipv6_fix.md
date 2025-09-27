# Railway IPv6 Database Connection Fix

## Problem
Your deployment is failing because Railway doesn't support IPv6 connections to Supabase, but your database URL is resolving to an IPv6 address.

## Solution
Update your `SUPABASE_URL` in Railway to use the IPv4 endpoint:

### Current URL (IPv6 - causing issues):
```
postgresql://postgres.[your-ref]:[password]@db.llkdmzdhnppvnlclcapv.supabase.co:5432/postgres
```

### Updated URL (IPv4 - will work):
```
postgresql://postgres.[your-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

## Steps to Fix:

### 1. Get Your Correct Connection String from Supabase Dashboard:
1. Go to your Supabase project dashboard
2. Click on "Settings" → "Database" 
3. Look for "Connection string" section
4. Copy the **"Connection pooling"** string (this uses IPv4)
5. It should look like: `postgresql://postgres.[your-ref]:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

### 2. Update Railway Environment Variable:
1. Go to your Railway dashboard
2. Select your project
3. Go to Variables tab  
4. Find `SUPABASE_URL`
5. Replace the value with the IPv4 connection string from step 1
6. Save the changes

### 3. Redeploy:
Railway will automatically redeploy with the new connection string.

## Alternative Endpoints to Try:
If the pooler endpoint doesn't work, try these IPv4 endpoints:
- `aws-0-us-east-1.pooler.supabase.com` (Connection pooling - recommended)
- `db.[your-project-id].supabase.co` with port `5432` (Direct connection)

## Verification:
After updating, your deployment should start successfully without the "Network is unreachable" IPv6 errors.

## Note:
The issue is that Railway's infrastructure doesn't support IPv6 connections, but your current Supabase URL is resolving to IPv6. Using the connection pooling endpoint ensures IPv4 connectivity.