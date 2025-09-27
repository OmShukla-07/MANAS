"""
URL configuration for MANAS Mental Health Platform Backend.

Main URL routing for all apps and API endpoints.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Main URL patterns
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Authentication endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # App API endpoints
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/chat/', include('chat.urls')),
    path('api/v1/appointments/', include('appointments.urls')),
    path('api/v1/crisis/', include('crisis.urls')),
    path('api/v1/core/', include('core.urls')),
]

# Frontend URLs (always available)
from core.frontend_views import home_view
urlpatterns += [
    path('', home_view, name='home'),
    
    # Include frontend URLs
    path('', include('core.frontend_urls')),
]

# Add media files handling for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
