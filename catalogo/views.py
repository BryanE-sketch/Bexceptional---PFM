from django.db.models import Prefetch, Sum
from django.shortcuts import get_object_or_404, render

from carrito.forms import AnadirAlCarritoForm
from contenido.models import Consejo, Recurso
from resenas.services import resumen_valoraciones

from .models import Disciplina, Producto, Variante


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


def detalle_producto(request, slug):
    """Ficha de producto: imágenes, colores, tallas con stock y reseñas aprobadas."""
    producto = get_object_or_404(
        Producto.objects.select_related("categoria", "categoria__padre").prefetch_related(
            "disciplinas",
            "imagenes",
            Prefetch("variantes", queryset=Variante.objects.select_related("talla", "color").order_by("talla__orden")),
        ),
        slug=slug,
        activo=True,  # un producto desactivado no existe para el público
    )
    variantes = list(producto.variantes.all())

    # Colores disponibles (sin repetir, en orden) y color elegido (?color=<id>)
    colores = list(dict.fromkeys(v.color for v in variantes))
    elegido = request.GET.get("color")
    color = next((c for c in colores if str(c.pk) == elegido), colores[0] if colores else None)

    tallas = [v for v in variantes if color and v.color_id == color.pk]
    imagenes = [i for i in producto.imagenes.all() if color is None or i.color_id in (None, color.pk)]

    contexto = {
        "producto": producto,
        "colores": colores,
        "color": color,
        "tallas": tallas,
        "imagenes": imagenes or list(producto.imagenes.all()),
        "form": AnadirAlCarritoForm(),
        "valoraciones": resumen_valoraciones(producto),
        "resenas": producto.resenas.filter(aprobada=True).select_related("usuario")[:6],
    }
    return render(request, "catalogo/producto.html", contexto)


def proximamente(request, titulo):
    """Página provisional para las secciones que aún estamos construyendo."""
    return render(request, "paginas/proximamente.html", {"titulo": titulo})