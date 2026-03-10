from django.apps import AppConfig


class SpectacularConfig(AppConfig):
    name = 'drf_spectacular_extended'
    verbose_name = "drf-spectacular"

    def ready(self):
        import drf_spectacular_extended.checks  # noqa: F401
