from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = 'api'
    verbose_name = 'The Poppins Club'

    def ready(self):
        from . import signals  # noqa: F401  (підключає сигнали)
