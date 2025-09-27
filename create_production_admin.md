# Create Production Admin User

## Method 1: Using Railway CLI (Recommended)
```bash
# Install Railway CLI if not installed
npm install -g @railway/cli

# Login to Railway
railway login

# Connect to your project
railway link

# Create superuser in production
railway run python manage.py createsuperuser
```

## Method 2: Using Django Shell in Production
```bash
# Open Django shell in production
railway run python manage.py shell

# In the shell, run:
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@manas.com', 'your-secure-password')
exit()
```

## Method 3: Add to Your Code (Temporary)
Create a management command to create admin user automatically:

1. Create the file: `core/management/commands/create_admin.py`
2. Add code to create admin user
3. Run: `railway run python manage.py create_admin`

## Admin Access
After creating the admin user, access your admin panel at:
`https://your-railway-url.up.railway.app/admin/`