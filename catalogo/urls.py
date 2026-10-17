from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("producto/<slug:slug>/", views.detalle_producto, name="producto"),
    path("tienda/", views.tienda, name="tienda"),
    path("favoritos/", views.favoritos, name="favoritos"),
    path("favoritos/<int:producto_id>/alternar/", views.alternar_favorito, name="alternar_favorito"),
]
