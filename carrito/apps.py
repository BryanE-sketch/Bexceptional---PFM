from django.apps import AppConfig


class CarritoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "carrito"
    verbose_name = "Carrito"

    def ready(self):
        from . import signals  # noqa: F401  (registra las señales)