"""Rutas de la API del catálogo. Se incluyen bajo /api/ en config/urls.py."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import FiltrosView, ProductoViewSet

app_name = "api"

# El router crea solo las dos rutas: /productos/ y /productos/<slug>/
router = DefaultRouter()
router.register("productos", ProductoViewSet, basename="producto")

urlpatterns = [
    path("filtros/", FiltrosView.as_view(), name="filtros"),
    *router.urls,
]
