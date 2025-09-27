from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "User Accounts & Authentication"
    
    def ready(self):
        # Import signal handlers
        try:
            import accounts.signals
        except ImportError:
            pass
