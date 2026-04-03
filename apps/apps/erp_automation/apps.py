from django.apps import AppConfig


class ErpAutomationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.erp_automation"
    verbose_name = "ERP Automation"

    def ready(self):
        pass  # Import signals here if needed
