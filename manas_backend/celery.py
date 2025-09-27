"""
Celery configuration for MANAS Mental Health Platform Backend.

Background task processing for analytics, notifications, and data processing.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manas_backend.settings')

app = Celery('manas_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'update-wellness-streaks': {
        'task': 'wellness.tasks.update_wellness_streaks',
        'schedule': 60.0 * 60,  # Every hour
    },
    'process-analytics': {
        'task': 'core.tasks.process_daily_analytics',
        'schedule': 60.0 * 60 * 6,  # Every 6 hours
    },
    'cleanup-old-sessions': {
        'task': 'chat.tasks.cleanup_old_chat_sessions',
        'schedule': 60.0 * 60 * 24,  # Daily
    },
    'check-crisis-alerts': {
        'task': 'crisis.tasks.check_pending_crisis_alerts',
        'schedule': 60.0 * 5,  # Every 5 minutes
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')