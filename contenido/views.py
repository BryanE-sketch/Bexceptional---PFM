from django.db.models import F, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogo.models import Disciplina, ImagenProducto, Producto

from .models import Articulo, Consejo, Recurso


def _disciplinas_con_contenido():
    """Disciplinas activas que tienen algo que contar (consejos o artículos publicados)."""
    return (
        Disciplina.objects.filter(activa=True)
        .filter(pk__in=Consejo.objects.filter(activo=True).values("disciplina"))
        .order_by("orden", "nombre")
    )


def habitos(request):
    """Portada de Hábitos: las disciplinas, los descargables y los artículos."""
    contexto = {
        "disciplinas": _disciplinas_con_contenido(),
        "recursos": Recurso.objects.filter(publicado=True),
        "articulos": Articulo.objects.publicados().select_related("disciplina"),
    }
    return render(request, "contenido/habitos.html", contexto)


def disciplina(request, slug):
    """Apartado de una disciplina: consejos con su fuente, artículo y productos para practicarla."""
    disciplina = get_object_or_404(Disciplina, slug=slug, activa=True)
    productos = (
        Producto.objects.filter(activo=True, disciplinas=disciplina)
        .select_related("categoria")
        .prefetch_related(Prefetch("imagenes", queryset=ImagenProducto.objects.order_by("orden", "pk")))[:4]
    )
    contexto = {
        "disciplina": disciplina,
        "consejos": disciplina.consejos.filter(activo=True),
        "articulos": Articulo.objects.publicados().filter(disciplina=disciplina).prefetch_related("fuentes"),
        "productos": productos,
        "otras": _disciplinas_con_contenido().exclude(pk=disciplina.pk),
    }
    return render(request, "contenido/disciplina.html", contexto)


def articulo(request, slug):
    """Artículo completo con sus fuentes. Los borradores no son visibles (404)."""
    articulo = get_object_or_404(
        Articulo.objects.publicados().select_related("disciplina").prefetch_related("fuentes"), slug=slug
    )
    otros = Articulo.objects.publicados().exclude(pk=articulo.pk)[:3]
    return render(request, "contenido/articulo.html", {"articulo": articulo, "otros": otros})


@require_POST
def descargar(request, slug):
    """
    Cuenta la descarga y redirige al PDF. Es POST para que los buscadores y las
    vistas previas de enlaces no inflen el contador.
    """
    recurso = get_object_or_404(Recurso, slug=slug, publicado=True)
    # F() suma en la base de datos: dos descargas a la vez no se pisan
    Recurso.objects.filter(pk=recurso.pk).update(descargas=F("descargas") + 1)
    return redirect(recurso.archivo.url)
