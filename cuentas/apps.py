from django.apps import AppConfig


class CuentasConfig(AppConfig):
    name = 'cuentas'

    def ready(self):
        from . import signals  # noqa: F401  (registra los receptores de señales)
