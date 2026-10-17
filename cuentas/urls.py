from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("cuenta/", views.perfil, name="perfil"),
    path("cuenta/entrar/", views.EntrarView.as_view(), name="entrar"),
    path("cuenta/registro/", views.registro, name="registro"),
    # Desde Django 5, cerrar sesión solo se permite con POST (un enlace no basta: protege de CSRF)
    path("cuenta/salir/", LogoutView.as_view(), name="salir"),
]
