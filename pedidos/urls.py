from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("finalizar-compra/", views.checkout, name="checkout"),
    path("cuenta/pedidos/<str:numero>/", views.detalle, name="detalle"),
]
