from django.apps import AppConfig


class PostulacionesConfig(AppConfig):
    name = 'postulaciones'

    def ready(self):
        from . import signals  # noqa: F401  (registra los receptores de señales)
