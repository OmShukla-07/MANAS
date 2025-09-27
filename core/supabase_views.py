"""
Supabase Configuration and Status API Views
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from core.supabase_service import supabase_service
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def supabase_status(request):
    """Get Supabase connection status and configuration"""
    try:
        # Get connection status
        connection_test = supabase_service.test_connection()
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        db_engine = db_config.get('ENGINE', 'unknown')
        
        # Determine database type
        if 'sqlite' in db_engine:
            db_type = 'SQLite (Local)'
            db_status = 'local'
        elif 'postgresql' in db_engine:
            db_type = 'PostgreSQL (Supabase)'
            db_status = 'supabase'
        else:
            db_type = f'Other ({db_engine})'
            db_status = 'other'
        
        # Get AI providers status
        ai_status = 'unknown'
        ai_providers = []
        try:
            from chat.enhanced_ai_service import enhanced_manas_ai_service
            ai_providers = enhanced_manas_ai_service.get_available_providers()
            ai_status = 'available' if ai_providers else 'no_providers'
        except Exception as e:
            ai_status = f'error: {str(e)}'
        
        return Response({
            'success': True,
            'supabase': {
                'configured': supabase_service.is_available(),
                'connection_status': connection_test,
                'url': supabase_service.url if supabase_service.url else None,
                'has_admin_client': supabase_service.admin_client is not None
            },
            'database': {
                'type': db_type,
                'status': db_status,
                'engine': db_engine
            },
            'ai_system': {
                'status': ai_status,
                'providers': ai_providers
            },
            'deployment_status': {
                'debug_mode': settings.DEBUG,
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'ready_for_production': not settings.DEBUG and db_status == 'supabase'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting Supabase status: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to get system status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def migrate_to_supabase(request):
    """Trigger migration to Supabase database"""
    try:
        # Check if Supabase is configured
        if not supabase_service.is_available():
            return Response({
                'success': False,
                'error': 'Supabase not configured. Please set SUPABASE_URL and SUPABASE_KEY environment variables.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Test connection
        connection_test = supabase_service.test_connection()
        if connection_test['status'] != 'connected':
            return Response({
                'success': False,
                'error': f'Supabase connection failed: {connection_test["message"]}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already using PostgreSQL
        db_config = settings.DATABASES['default']
        if 'sqlite' in db_config.get('ENGINE', ''):
            return Response({
                'success': False,
                'error': 'Please update DATABASE_URL environment variable to use PostgreSQL connection string'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Supabase is properly configured. Run migrations using: python manage.py setup_supabase'
        })
        
    except Exception as e:
        logger.error(f"Error in migrate_to_supabase: {str(e)}")
        return Response({
            'success': False,
            'error': 'Migration check failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def supabase_setup_guide(request):
    """Get step-by-step setup guide for Supabase integration"""
    return Response({
        'success': True,
        'setup_guide': {
            'title': 'MANAS Supabase Integration Setup',
            'steps': [
                {
                    'step': 1,
                    'title': 'Create Supabase Project',
                    'description': 'Go to https://supabase.com and create a new project',
                    'details': [
                        'Sign up/login to Supabase',
                        'Click "New Project"',
                        'Choose organization and set project name',
                        'Generate a strong database password',
                        'Select region closest to your users'
                    ]
                },
                {
                    'step': 2,
                    'title': 'Get Project Credentials',
                    'description': 'Copy your project URL and API keys',
                    'details': [
                        'Go to Project Settings > API',
                        'Copy Project URL',
                        'Copy anon/public key',
                        'Copy service_role key (keep this secret!)'
                    ]
                },
                {
                    'step': 3,
                    'title': 'Update Environment Variables',
                    'description': 'Add Supabase credentials to your .env file',
                    'env_vars': {
                        'SUPABASE_URL': 'https://your-project-ref.supabase.co',
                        'SUPABASE_KEY': 'your-anon-key',
                        'SUPABASE_SERVICE_ROLE_KEY': 'your-service-role-key',
                        'DATABASE_URL': 'postgresql://postgres:[password]@[host]:[port]/postgres'
                    }
                },
                {
                    'step': 4,
                    'title': 'Get Database Connection String',
                    'description': 'Get PostgreSQL connection details',
                    'details': [
                        'Go to Project Settings > Database',
                        'Copy Connection string (URI)',
                        'Replace [password] with your database password',
                        'Update DATABASE_URL in your .env file'
                    ]
                },
                {
                    'step': 5,
                    'title': 'Run Migration Command',
                    'description': 'Execute the setup command',
                    'command': 'python manage.py setup_supabase',
                    'details': [
                        'This will test your Supabase connection',
                        'Run Django migrations to create tables',
                        'Verify AI system functionality',
                        'Create superuser if needed'
                    ]
                },
                {
                    'step': 6,
                    'title': 'Verify Setup',
                    'description': 'Test your Supabase integration',
                    'details': [
                        'Check this API endpoint for green status',
                        'Login to Supabase dashboard and verify tables created',
                        'Test MANAS AI companions functionality',
                        'Verify real-time features work'
                    ]
                }
            ],
            'benefits': [
                'Production-ready PostgreSQL database',
                'Real-time subscriptions for live updates',
                'Built-in authentication and row-level security',
                'File storage with CDN',
                'Automatic backups and scaling',
                'Dashboard for database management'
            ],
            'troubleshooting': {
                'connection_failed': 'Check your DATABASE_URL and ensure IP is whitelisted in Supabase',
                'migration_errors': 'Ensure database is empty or use --force flag',
                'auth_errors': 'Verify SUPABASE_SERVICE_ROLE_KEY is correct',
                'performance_issues': 'Check your database location matches your deployment region'
            }
        }
    })

def supabase_dashboard_view(request):
    """Simple HTML view for Supabase setup dashboard"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Admin access required'}, status=403)
    
    from django.shortcuts import render
    return render(request, 'admin/supabase_dashboard.html', {
        'title': 'MANAS Supabase Integration',
        'supabase_configured': supabase_service.is_available()
    })