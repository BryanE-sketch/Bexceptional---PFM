from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    # Provisionales: se sustituirán por las vistas reales en las próximas sesiones
    path("tienda/", views.proximamente, {"titulo": "Tienda"}, name="tienda"),
    path("favoritos/", views.proximamente, {"titulo": "Favoritos"}, name="favoritos"),
]