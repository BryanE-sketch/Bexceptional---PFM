from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Prefetch, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from carrito.forms import AnadirAlCarritoForm
from contenido.models import Consejo, Recurso
from resenas.services import resumen_valoraciones

from .models import Disciplina, Favorito, ImagenProducto, Producto, Variante


def inicio(request):
    """Portada: disciplinas, novedades y la invitación a la sección Hábitos."""
    novedades = (
        Producto.objects.filter(activo=True)
        .select_related("categoria")
        .prefetch_related("imagenes")
        .annotate(stock_total=Sum("variantes__stock"))[:8]
    )
    contexto = {
        # Solo disciplinas con consejos: cada tarjeta lleva a su apartado de Hábitos
        "disciplinas": Disciplina.objects.filter(activa=True, consejos__activo=True).distinct()[:4],
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
        "es_favorito": request.user.is_authenticated
        and Favorito.objects.filter(usuario=request.user, producto=producto).exists(),
    }
    return render(request, "catalogo/producto.html", contexto)


def tienda(request):
    """
    Página de la tienda. Django solo pone la estructura (cabecera, pie, carrito);
    el listado con filtros lo pinta React pidiendo los datos a la API (/api/productos/).
    """
    return render(request, "catalogo/tienda.html")


@login_required
def favoritos(request):
    """Mis favoritos: los productos guardados, del más reciente al más antiguo."""
    favoritos = (
        Favorito.objects.filter(usuario=request.user, producto__activo=True)
        .select_related("producto__categoria")
        .prefetch_related(Prefetch("producto__imagenes", queryset=ImagenProducto.objects.order_by("orden", "pk")))
        .order_by("-creado")
    )
    return render(request, "catalogo/favoritos.html", {"favoritos": favoritos})


@require_POST
def alternar_favorito(request, producto_id):
    """
    Añade o quita un producto de favoritos (el corazón de la ficha).
    - Con HTMX devuelve solo el botón actualizado.
    - Sin sesión, manda a iniciar sesión y vuelve a la ficha del producto.
    """
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    if not request.user.is_authenticated:
        if request.htmx:
            # HTMX no sigue redirecciones de página completa: se lo pedimos con esta cabecera
            respuesta = HttpResponse(status=204)
            respuesta["HX-Redirect"] = f"{reverse('cuentas:entrar')}?next={producto.get_absolute_url()}"
            return respuesta
        return redirect_to_login(producto.get_absolute_url())

    favorito, creado = Favorito.objects.get_or_create(usuario=request.user, producto=producto)
    if not creado:
        favorito.delete()
    es_favorito = creado

    if request.htmx:
        if request.POST.get("origen") == "lista":
            # Desde la página de favoritos: la tarjeta desaparece (respuesta vacía)
            return HttpResponse("")
        return render(request, "catalogo/_boton_favorito.html", {"producto": producto, "es_favorito": es_favorito})
    destino = "catalogo:favoritos" if request.POST.get("origen") == "lista" else producto.get_absolute_url()
    return redirect(destino)


def proximamente(request, titulo):
    """Página provisional para las secciones que aún estamos construyendo."""
    return render(request, "paginas/proximamente.html", {"titulo": titulo})
