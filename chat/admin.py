from django.contrib import admin
from django.utils.html import format_html
from .models import ChatSession, Message
from crisis.models import CrisisAlert


@admin.register(CrisisAlert)
class CrisisAlertAdmin(admin.ModelAdmin):
    """Admin interface for crisis alerts"""
    list_display = ['user', 'severity_level', 'status', 'source', 'created_at']
    list_filter = ['status', 'source', 'severity_level']
    search_fields = ['user__username', 'user__email', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['id', 'created_at', 'acknowledged_at', 'resolved_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'crisis_type', 'assigned_counselor')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_type', 'status', 'crisis_level', 'created_at']
    list_filter = ['session_type', 'status', 'requires_intervention']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'sender', 'message_type', 'created_at']
    list_filter = ['message_type']
