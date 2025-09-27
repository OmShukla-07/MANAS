# 🚀 MANAS Manual Migration to Supabase Guide

## 🎯 Your Current Status:
- ✅ **Supabase Project**: Created and configured
- ✅ **API Keys**: Working perfectly  
- ✅ **Local Data**: 18 users, 39 chats, 4 appointments
- ❌ **Network Issue**: Can't reach PostgreSQL database directly

## 📊 **Manual Migration Steps**

### **Step 1: Create Tables in Supabase Dashboard**

1. **Go to Supabase Dashboard**: https://supabase.com/dashboard
2. **Select Your Project**: `llkdmzdhnppvnlclcapv`
3. **Go to Table Editor** (left sidebar)
4. **Create these tables**:

#### **Users Table (auth_user)**
```sql
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT true,
    is_staff BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    date_joined TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    password VARCHAR(128) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    phone_number VARCHAR(17),
    date_of_birth DATE,
    is_verified BOOLEAN DEFAULT false,
    profile_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_ip INET
);
```

#### **Chat Sessions Table**
```sql
CREATE TABLE chat_chatsession (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    session_type VARCHAR(20) DEFAULT 'regular',
    total_messages INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT NOW()
);
```

#### **Chat Messages Table**
```sql
CREATE TABLE chat_chatmessage (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_chatsession(id),
    message TEXT NOT NULL,
    response TEXT,
    sender VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    message_type VARCHAR(20) DEFAULT 'text',
    is_flagged BOOLEAN DEFAULT false,
    confidence_score DECIMAL(3,2),
    processing_time DECIMAL(5,3)
);
```

#### **Appointments Table**
```sql
CREATE TABLE appointments_appointment (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES auth_user(id),
    counselor_id INTEGER REFERENCES auth_user(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    scheduled_date TIMESTAMP NOT NULL,
    duration INTEGER DEFAULT 60,
    status VARCHAR(20) DEFAULT 'scheduled',
    meeting_type VARCHAR(20) DEFAULT 'video',
    meeting_link VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    reminder_sent BOOLEAN DEFAULT false,
    cancellation_reason TEXT
);
```

### **Step 2: Export Data from SQLite**

Run this command to export your data:

```python
python -c "
import os
import json
import django
from django.conf import settings

# Use SQLite for export
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manas_backend.settings')
django.setup()

from accounts.models import CustomUser
from chat.models import ChatSession, ChatMessage  
from appointments.models import Appointment

# Export to JSON
data = {
    'users': list(CustomUser.objects.values()),
    'chat_sessions': list(ChatSession.objects.values()),
    'chat_messages': list(ChatMessage.objects.values()),
    'appointments': list(Appointment.objects.values())
}

with open('manas_export.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)

print('✅ Data exported to manas_export.json')
"
```

### **Step 3: Import Data via Supabase Dashboard**

1. **Convert JSON to CSV** for each table
2. **Use Table Editor** → **Insert** → **Import from CSV**
3. **Map columns** correctly
4. **Import in order**: Users → Chat Sessions → Messages → Appointments

### **Step 4: Create Storage Buckets**

1. **Go to Storage** in Supabase dashboard
2. **Create New Bucket**: `manas-uploads`
3. **Set Policies**:
   - Public bucket for profile pictures
   - Private bucket for sensitive documents

### **Step 5: Configure Row Level Security**

Enable RLS on all tables:
```sql
ALTER TABLE auth_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_chatsession ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_chatmessage ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments_appointment ENABLE ROW LEVEL SECURITY;
```

## 🔄 **Alternative: Wait and Retry**

The network issue might be temporary. You can:

1. **Wait 30 minutes** and try again
2. **Restart your router/modem**
3. **Check if Supabase has any service outages**
4. **Try from a different device**

## 📞 **Need Help?**

If you get stuck:
1. Share screenshots of any errors
2. Try the manual dashboard approach first
3. We can troubleshoot the network issue later

Your data is safe in SQLite, so there's no rush! 🛡️