from django.db.models import Sum
from django.shortcuts import render

from contenido.models import Consejo, Recurso

from .models import Disciplina, Producto


def inicio(request):
    """Portada: disciplinas, novedades y la invitación a la sección Hábitos."""
    novedades = (
        Producto.objects.filter(activo=True)
        .select_related("categoria")
        .prefetch_related("imagenes")
        .annotate(stock_total=Sum("variantes__stock"))[:8]
    )
    contexto = {
        "disciplinas": Disciplina.objects.filter(activa=True)[:4],
        "novedades": novedades,
        "consejos": Consejo.objects.filter(activo=True)[:3],
        "recurso": Recurso.objects.filter(publicado=True).first(),
    }
    return render(request, "catalogo/inicio.html", contexto)


def proximamente(request, titulo):
    """Página provisional para las secciones que aún estamos construyendo."""
    return render(request, "paginas/proximamente.html", {"titulo": titulo})