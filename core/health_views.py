"""
Health check view for deployment monitoring
"""

from django.http import JsonResponse
from django.views import View
import sys


class HealthCheckView(View):
    """Simple health check endpoint that doesn't load heavy models"""
    
    def get(self, request):
        """Return health status"""
        return JsonResponse({
            'status': 'healthy',
            'service': 'MANAS Mental Health Platform',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        })
