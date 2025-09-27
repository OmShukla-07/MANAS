# ✅ Railway Database URL Update

## Correct IPv4 Connection String Found:
```
postgresql://postgres.llkdmzdhnppvnlclcapv:Shukla@160705@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
```

## Key Differences:
- ❌ **Old (IPv6):** `db.llkdmzdhnppvnlclcapv.supabase.co:5432`
- ✅ **New (IPv4):** `aws-1-ap-south-1.pooler.supabase.com:6543`

## Next Steps:

### 1. Update Railway Environment Variable:
1. Go to your Railway project dashboard: https://railway.app/dashboard
2. Select your MANAS project
3. Click on the "Variables" tab
4. Find the `SUPABASE_URL` variable
5. Replace the current value with:
   ```
   postgresql://postgres.llkdmzdhnppvnlclcapv:Shukla@160705@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
   ```
6. Click "Save" or "Update"

### 2. Automatic Redeployment:
- Railway will automatically trigger a new deployment with the updated URL
- This should resolve the IPv6 connectivity issues

### 3. Monitor Deployment:
- Watch the deployment logs in Railway
- The "Network is unreachable" errors should disappear
- Your application should start successfully

## Expected Result:
Your Django application will now connect to Supabase using IPv4, which Railway supports, eliminating the database connection failures.

## Verification:
Once deployed successfully, your MANAS Mental Health Platform will be live at:
`https://manas-production-7ee4.up.railway.app`