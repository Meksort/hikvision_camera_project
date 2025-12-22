from django.apps import AppConfig
import os


class CameraEventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "camera_events"
    
    def ready(self):
        """Подключаем сигналы при запуске приложения."""
        import camera_events.signals  # noqa

