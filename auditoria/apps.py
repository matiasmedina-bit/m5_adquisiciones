from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditoria"
    verbose_name = "Bitácora de auditoría"

    def ready(self):
        # Conecta los receivers que capturan los movimientos de bodega (CU-53)
        from . import signals  # noqa: F401
