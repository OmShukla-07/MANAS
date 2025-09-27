# Generated migration for CounselorProfile model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CounselorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('license_number', models.CharField(blank=True, max_length=100)),
                ('specializations', models.TextField(blank=True, help_text='Areas of specialization')),
                ('years_of_experience', models.PositiveIntegerField(default=0)),
                ('education', models.TextField(blank=True)),
                ('bio', models.TextField(blank=True)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('office_location', models.CharField(blank=True, max_length=200)),
                ('max_daily_appointments', models.PositiveIntegerField(default=8)),
                ('preferred_session_duration', models.PositiveIntegerField(default=60)),
                ('available_for_emergency', models.BooleanField(default=True)),
                ('accepts_new_students', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(limit_choices_to={'role': 'counselor'}, on_delete=django.db.models.deletion.CASCADE, related_name='counselor_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]