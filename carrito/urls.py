from django.urls import path

from catalogo.views import proximamente

app_name = "carrito"

urlpatterns = [
    path("carrito/", proximamente, {"titulo": "Carrito"}, name="detalle"),
]