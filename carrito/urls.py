from django.urls import path

from . import views

app_name = "carrito"

urlpatterns = [
    path("carrito/", views.detalle, name="detalle"),
    path("carrito/anadir/", views.anadir, name="anadir"),
    path("carrito/linea/<int:linea_id>/actualizar/", views.actualizar, name="actualizar"),
    path("carrito/linea/<int:linea_id>/eliminar/", views.eliminar, name="eliminar"),
]
