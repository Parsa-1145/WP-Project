from django.apps import AppConfig


class PaymetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"

    def ready(self):
        import payments.submissiontypes


