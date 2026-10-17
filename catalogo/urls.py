from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("producto/<slug:slug>/", views.detalle_producto, name="producto"),
    # Provisionales: se sustituirán por las vistas reales en las próximas sesiones
    path('tienda/', views.tienda, name='tienda'),
    path("favoritos/", views.proximamente, {"titulo": "Favoritos"}, name="favoritos"),
]