# 🎯 Quick Manual Migration Steps

## 📊 Your Exported Data:
- ✅ **File**: `manas_supabase_export.json`
- ✅ **Records**: 18 users, 39 chats, 4 appointments

## 🔧 Dashboard Migration (15 minutes):

### Step 1: Go to Supabase
1. Visit: https://supabase.com/dashboard
2. Select project: `llkdmzdhnppvnlclcapv`
3. Click **"Table Editor"**

### Step 2: Create Tables
Click **"New Table"** and create:

#### Table 1: `auth_user`
```
Columns:
- id (int8, primary key, auto-increment)  
- username (text, unique)
- email (text, unique)
- first_name (text)
- last_name (text)
- role (text, default: 'student')
- is_active (bool, default: true)
- created_at (timestamptz, default: now())
```

#### Table 2: `chat_chatsession`  
```
Columns:
- id (uuid, primary key)
- user_id (int8, foreign key to auth_user)
- title (text)
- session_type (text, default: 'ai_chat')
- status (text, default: 'active')
- created_at (timestamptz, default: now())
```

#### Table 3: `appointments_appointment`
```
Columns:
- id (int8, primary key, auto-increment)
- student_id (int8, foreign key to auth_user)
- counselor_id (int8, foreign key to auth_user)
- title (text)
- scheduled_date (timestamptz)
- status (text, default: 'scheduled')
- created_at (timestamptz, default: now())
```

### Step 3: Import Data
1. **Table Editor** → Select table → **Insert** → **Import CSV**
2. Convert JSON sections to CSV format
3. Import users first, then sessions, then appointments

## 🚀 Alternative: Try Different Network

- **Mobile Hotspot**: Use phone's internet
- **Different Location**: Coffee shop, library, office
- **VPN**: If available, try connecting through VPN

## ✅ After Migration:
```bash
# Test the connection
python manage.py migrate
python manage.py setup_supabase --check-only
```

Your data is safely backed up, so no rush! 😊