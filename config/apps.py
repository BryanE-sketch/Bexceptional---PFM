"""Configuración propia de la app de estáticos de Django."""
from django.contrib.staticfiles.apps import StaticFilesConfig


class EstaticosConfig(StaticFilesConfig):
    # static/src/ guarda el CÓDIGO FUENTE de Tailwind (lo compila "npm run css:build" a static/css/).
    # No debe publicarse: collectstatic lo ignora.
    ignore_patterns = StaticFilesConfig.ignore_patterns + ["src"]
