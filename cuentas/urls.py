from django.urls import path

from catalogo.views import proximamente

app_name = "cuentas"

urlpatterns = [
    path("cuenta/", proximamente, {"titulo": "Mi cuenta"}, name="perfil"),
]