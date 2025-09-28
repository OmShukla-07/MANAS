#!/usr/bin/env python
"""
Pre-deployment check script for MANAS backend
Validates critical configurations before deployment
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.core.exceptions import ImproperlyConfigured

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    # Critical environment variables for production
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment variables check passed")
    return True

def check_django_setup():
    """Check if Django can be set up properly"""
    print("🔍 Checking Django setup...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manas_backend.settings')
        django.setup()
        print("✅ Django setup successful")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def check_database():
    """Check database connection"""
    print("🔍 Checking database connection...")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_static_files():
    """Check if static files are collected"""
    print("🔍 Checking static files...")
    
    try:
        from django.conf import settings
        static_root = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT
        
        if os.path.exists(static_root):
            print("✅ Static files directory exists")
            return True
        else:
            print("⚠️  Static files directory not found - run collectstatic")
            return False
    except Exception as e:
        print(f"❌ Static files check failed: {e}")
        return False

def check_templates():
    """Check if critical templates exist and are valid"""
    print("🔍 Checking critical templates...")
    
    critical_templates = [
        'learn_more.html',
        'base.html',
        'auth/choose_user.html',
        'index.html'
    ]
    
    from django.conf import settings
    template_dirs = [os.path.join(settings.BASE_DIR, 'templates')]
    
    missing_templates = []
    for template in critical_templates:
        template_found = False
        for template_dir in template_dirs:
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                template_found = True
                break
        
        if not template_found:
            missing_templates.append(template)
    
    if missing_templates:
        print(f"❌ Missing templates: {', '.join(missing_templates)}")
        return False
    
    print("✅ Critical templates exist")
    return True

def check_imports():
    """Check if all critical imports work"""
    print("🔍 Checking critical imports...")
    
    try:
        # Test critical app imports
        import accounts
        import chat
        import core
        import appointments
        import crisis
        print("✅ All app imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run all pre-deployment checks"""
    print("🚀 MANAS Pre-Deployment Check Starting...")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        check_django_setup,
        check_imports,
        check_templates,
        check_static_files,
        check_database,
    ]
    
    for check in checks:
        try:
            if not check():
                all_checks_passed = False
        except Exception as e:
            print(f"❌ Check failed with exception: {e}")
            all_checks_passed = False
        print("-" * 30)
    
    # Final result
    if all_checks_passed:
        print("🎉 ALL CHECKS PASSED - READY FOR DEPLOYMENT!")
        print("✅ You can safely deploy the application")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED - PLEASE FIX ISSUES BEFORE DEPLOYMENT")
        print("❌ Do not deploy until all issues are resolved")
        return 1

if __name__ == "__main__":
    sys.exit(main())