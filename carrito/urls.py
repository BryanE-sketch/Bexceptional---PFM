from django.urls import path

from catalogo.views import proximamente

from . import views

app_name = "carrito"

urlpatterns = [
    path("carrito/", proximamente, {"titulo": "Carrito"}, name="detalle"),
    path("carrito/anadir/", views.anadir, name="anadir"),
]