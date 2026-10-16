from django.urls import path

from catalogo.views import proximamente

app_name = "contenido"

urlpatterns = [
    path("habitos/", proximamente, {"titulo": "Hábitos"}, name="habitos"),
]