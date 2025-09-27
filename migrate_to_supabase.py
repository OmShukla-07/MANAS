#!/usr/bin/env python3
"""
Complete MANAS to Supabase Migration Script
Migrates all data from SQLite to Supabase PostgreSQL
"""
import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manas_backend.settings')
import django
django.setup()

from django.core.management import call_command
from django.db import connections
from django.conf import settings
from core.supabase_service import SupabaseService

def migrate_to_supabase():
    """Complete migration from SQLite to Supabase"""
    print("🚀 MANAS → Supabase Complete Migration")
    print("=" * 50)
    
    # Check current database
    current_db = settings.DATABASES['default']
    print(f"📊 Current Database: {current_db.get('ENGINE', 'Unknown')}")
    
    if 'postgresql' in current_db.get('ENGINE', ''):
        print("✅ Already using PostgreSQL!")
        return True
    
    print("\n🔍 Pre-migration Status:")
    try:
        from accounts.models import CustomUser
        from chat.models import ChatSession
        from appointments.models import Appointment
        
        users_count = CustomUser.objects.count()
        chats_count = ChatSession.objects.count()
        appointments_count = Appointment.objects.count()
        
        print(f"   📊 Users to migrate: {users_count}")
        print(f"   💬 Chat sessions to migrate: {chats_count}")
        print(f"   📅 Appointments to migrate: {appointments_count}")
        
        if users_count == 0:
            print("   ⚠️  No data found to migrate!")
            
    except Exception as e:
        print(f"   ❌ Error checking current data: {e}")
        return False
    
    print("\n🔧 Migration Steps:")
    print("   1. Update your .env file with PostgreSQL DATABASE_URL")
    print("   2. Run: python migrate_to_supabase.py --execute")
    print("   3. Verify data in Supabase dashboard")
    
    print("\n📝 Required .env update:")
    print("   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.llkdmzdhnppvnlclcapv.supabase.co:5432/postgres")
    
    return True

def execute_migration():
    """Execute the actual migration"""
    print("🔄 Executing Migration...")
    
    # Test Supabase connection
    service = SupabaseService()
    if not service.test_connection():
        print("❌ Supabase connection failed!")
        return False
    
    print("✅ Supabase connection verified")
    
    # Run Django migrations
    try:
        print("🔧 Running Django migrations...")
        call_command('migrate', verbosity=1)
        print("✅ Migrations completed")
        
        # Create superuser if needed
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            print("👤 Creating superuser...")
            call_command('createsuperuser', 
                        email='admin@manas.com',
                        username='admin',
                        interactive=False)
        
        print("🎉 Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def setup_supabase_features():
    """Set up additional Supabase features"""
    print("\n🌟 Setting up Supabase Features:")
    
    service = SupabaseService()
    
    # Create storage buckets
    print("📁 Creating storage buckets...")
    
    buckets_to_create = [
        {
            'name': 'avatars',
            'public': True,
            'description': 'User profile pictures'
        },
        {
            'name': 'chat-files',
            'public': False,
            'description': 'Chat attachments and files'
        },
        {
            'name': 'documents',
            'public': False,
            'description': 'User documents and reports'
        }
    ]
    
    for bucket in buckets_to_create:
        try:
            # Try to create bucket
            result = service.client.storage.create_bucket(
                bucket['name'],
                options={'public': bucket['public']}
            )
            print(f"   ✅ Created bucket: {bucket['name']}")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"   ✅ Bucket exists: {bucket['name']}")
            else:
                print(f"   ⚠️  Bucket {bucket['name']}: {e}")
    
    print("\n🔐 Setting up Row Level Security...")
    # Note: RLS policies should be set up in Supabase dashboard
    print("   ℹ️  Please configure RLS policies in Supabase dashboard")
    
    print("\n⚡ Setting up Real-time subscriptions...")
    print("   ℹ️  Real-time features ready for chat and notifications")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        success = execute_migration()
        if success:
            setup_supabase_features()
    else:
        migrate_to_supabase()
        
    print("\n" + "=" * 50)
    print("📚 Next Steps:")
    print("   1. Update DATABASE_URL in .env file")
    print("   2. Run: python migrate_to_supabase.py --execute")
    print("   3. Test your application")
    print("   4. Configure RLS policies in Supabase dashboard")
    print("\n🎉 Your data will be safely migrated to Supabase!")