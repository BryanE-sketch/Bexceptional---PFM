from django.urls import path

from . import views

app_name = "contenido"

urlpatterns = [
    path("habitos/", views.habitos, name="habitos"),
    # Las rutas fijas van ANTES que la de la disciplina: si no, "articulos" se tomaría por un slug
    path("habitos/articulos/<slug:slug>/", views.articulo, name="articulo"),
    path("habitos/descargas/<slug:slug>/", views.descargar, name="descargar"),
    path("habitos/<slug:slug>/", views.disciplina, name="disciplina"),
]
