# 🔧 Railway Database Connection Fix

## Issue: Railway can't connect to Supabase PostgreSQL
Error: "Network is unreachable" when connecting to db.llkdmzdhnppvnlclcapv.supabase.co

## Solution Options:

### Option 1: Add Missing SUPABASE_URL (Required!)
Add this variable in Railway Variables tab:
- Variable Name: SUPABASE_URL
- Value: https://llkdmzdhnppvnlclcapv.supabase.co

### Option 2: Use Connection Pooler URL
Update DATABASE_URL in Railway to use pooler:
```
postgresql://postgres.llkdmzdhnppvnlclcapv:Shukla@160705@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

### Option 3: Check Supabase Network Settings
1. Go to Supabase Dashboard
2. Settings → Database
3. Check "Network restrictions"
4. Either disable restrictions OR add Railway IPs

### Option 4: Alternative CONNECTION_URL Format
Try this format instead:
```
postgres://postgres:Shukla@160705@db.llkdmzdhnppvnlclcapv.supabase.co:5432/postgres?sslmode=require
```

## Next Steps:
1. Add SUPABASE_URL variable first
2. If still failing, try the connection pooler URL
3. Check Supabase network settings
4. Test different connection string formats

## Expected Fix:
After adding SUPABASE_URL, the "Supabase credentials not configured" error should disappear, and database connection should work.