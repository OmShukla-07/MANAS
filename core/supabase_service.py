"""
Supabase Integration Service for MANAS Platform
Handles database connections, authentication, and real-time features
"""

import os
from supabase import create_client, Client
from django.conf import settings
from decouple import config
import logging

# Try to load environment variables from .env file if available (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use system environment variables directly
    pass

logger = logging.getLogger(__name__)

class SupabaseService:
    """
    Supabase service integration for MANAS platform
    """
    
    def __init__(self):
        # Try multiple methods to get environment variables
        self.url = os.environ.get('SUPABASE_URL') or config('SUPABASE_URL', default=None)
        self.key = os.environ.get('SUPABASE_KEY') or config('SUPABASE_KEY', default=None)
        self.service_role_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or config('SUPABASE_SERVICE_ROLE_KEY', default=None)
        self.storage_bucket = os.environ.get('SUPABASE_STORAGE_BUCKET') or config('SUPABASE_STORAGE_BUCKET', default='manas-files')
        
        # Debug logging for Railway
        logger.info(f"Supabase URL configured: {'Yes' if self.url else 'No'}")
        logger.info(f"Supabase Key configured: {'Yes' if self.key else 'No'}")
        logger.info(f"Service Role Key configured: {'Yes' if self.service_role_key else 'No'}")
        
        # Initialize Supabase client if credentials are available
        self.client = None
        self.admin_client = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully")
                
                # Initialize admin client with service role key if available
                if self.service_role_key:
                    self.admin_client = create_client(self.url, self.service_role_key)
                    logger.info("Supabase admin client initialized successfully")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
        else:
            logger.warning("Supabase credentials not configured, using local database only")
    
    def is_available(self) -> bool:
        """Check if Supabase is properly configured and available"""
        return self.client is not None
    
    def get_client(self) -> Client:
        """Get the standard Supabase client (user-level permissions)"""
        return self.client
    
    def get_admin_client(self) -> Client:
        """Get the admin Supabase client (service role permissions)"""
        return self.admin_client or self.client
    
    def test_connection(self) -> dict:
        """Test the Supabase connection and return status"""
        if not self.is_available():
            return {
                'status': 'not_configured',
                'message': 'Supabase credentials not configured'
            }
        
        try:
            # Test basic connection by querying auth users (if admin client available)
            if self.admin_client:
                result = self.admin_client.auth.admin.list_users()
                return {
                    'status': 'connected',
                    'message': 'Supabase connection successful',
                    'database_url': self.url,
                    'users_count': len(result.users) if hasattr(result, 'users') else 'unknown'
                }
            else:
                # Test with regular client
                auth_user = self.client.auth.get_user()
                return {
                    'status': 'connected',
                    'message': 'Supabase connection successful (limited permissions)',
                    'database_url': self.url
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Supabase connection failed: {str(e)}',
                'database_url': self.url
            }
    
    def upload_file(self, bucket_name: str, file_path: str, file_data: bytes) -> dict:
        """Upload a file to Supabase Storage"""
        if not self.is_available():
            return {'success': False, 'error': 'Supabase not configured'}
        
        try:
            result = self.client.storage.from_(bucket_name).upload(file_path, file_data)
            return {
                'success': True,
                'file_path': file_path,
                'bucket': bucket_name,
                'url': f"{self.url}/storage/v1/object/public/{bucket_name}/{file_path}"
            }
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_file_url(self, bucket_name: str, file_path: str) -> str:
        """Get public URL for a file in Supabase Storage"""
        if not self.is_available():
            return None
        
        try:
            result = self.client.storage.from_(bucket_name).get_public_url(file_path)
            return result['publicURL'] if 'publicURL' in result else result
        except Exception as e:
            logger.error(f"Get file URL failed: {str(e)}")
            return None
    
    def create_realtime_channel(self, table_name: str, callback=None):
        """Create a real-time subscription to a table"""
        if not self.is_available():
            return None
        
        try:
            channel = self.client.channel(f'{table_name}_channel')
            if callback:
                channel.on('*', callback)
            channel.subscribe()
            return channel
        except Exception as e:
            logger.error(f"Real-time channel creation failed: {str(e)}")
            return None
    
    def execute_sql(self, query: str, params: dict = None) -> dict:
        """Execute raw SQL query (admin client required)"""
        if not self.admin_client:
            return {'success': False, 'error': 'Admin client required for SQL execution'}
        
        try:
            result = self.admin_client.rpc('execute_sql', {'query': query, 'params': params or {}})
            return {'success': True, 'data': result.data}
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            return {'success': False, 'error': str(e)}

# Global Supabase service instance
supabase_service = SupabaseService()

# Utility functions for easy access
def get_supabase_client():
    """Get Supabase client instance"""
    return supabase_service.get_client()

def get_supabase_admin_client():
    """Get Supabase admin client instance"""
    return supabase_service.get_admin_client()

def is_supabase_available():
    """Check if Supabase is available"""
    return supabase_service.is_available()