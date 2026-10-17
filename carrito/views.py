from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AnadirAlCarritoForm
from .models import LineaCarrito
from .services import (
    StockInsuficienteError,
    anadir_al_carrito,
    buscar_carrito,
    cambiar_cantidad,
    cantidad_en_carrito,
    eliminar_linea,
    obtener_carrito,
    resumen_carrito,
)


@require_POST
def anadir(request):
    """Añade una variante al carrito. Responde con un fragmento HTML si la petición viene de HTMX."""
    form = AnadirAlCarritoForm(request.POST)
    ok = False
    if form.is_valid():
        variante = form.cleaned_data["variante"]
        try:
            anadir_al_carrito(obtener_carrito(request), variante, form.cleaned_data["cantidad"])
            ok = True
            mensaje = f"Añadido al carrito: {variante.producto.nombre} · {variante.color} · {variante.talla}"
        except StockInsuficienteError as error:
            mensaje = str(error)
    else:
        # Primer error del formulario, para mostrarlo en una sola línea
        mensaje = next(iter(form.errors.values()))[0]

    if request.htmx:
        contexto = {"ok": ok, "mensaje": mensaje, "carrito_cantidad": cantidad_en_carrito(request)}
        return render(request, "carrito/_respuesta_anadir.html", contexto)

    # Sin JavaScript: mensaje + volver a la página anterior
    (messages.success if ok else messages.error)(request, mensaje)
    destino = request.META.get("HTTP_REFERER", "")
    # Seguridad: solo volvemos a páginas de NUESTRA web (evita redirecciones abiertas)
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        destino = "catalogo:inicio"
    return redirect(destino)


def detalle(request):
    """Página del carrito (CU-03): revisar, cambiar cantidades y eliminar artículos."""
    return render(request, "carrito/detalle.html", resumen_carrito(buscar_carrito(request)))


def _respuesta_carrito(request, aviso="", error=False):
    """
    Respuesta común de «actualizar» y «eliminar»:
    - Con HTMX: solo el bloque del carrito + el contador de la cabecera (fuera de banda).
    - Sin JavaScript: mensaje y vuelta a la página del carrito.
    """
    if request.htmx:
        contexto = resumen_carrito(buscar_carrito(request))
        contexto.update(aviso=aviso, aviso_error=error, carrito_cantidad=contexto["num_articulos"])
        return render(request, "carrito/_respuesta_contenido.html", contexto)
    if aviso:
        (messages.error if error else messages.success)(request, aviso)
    return redirect("carrito:detalle")


@require_POST
def actualizar(request, linea_id):
    carrito = buscar_carrito(request)
    try:
        cantidad = int(request.POST.get("cantidad", ""))
        cambiar_cantidad(carrito, linea_id, cantidad)
        return _respuesta_carrito(request)
    except LineaCarrito.DoesNotExist:
        raise Http404("Esa línea no está en tu carrito.")
    except (ValueError, StockInsuficienteError) as error:
        texto = str(error) if isinstance(error, StockInsuficienteError) else "Indica una cantidad válida."
        return _respuesta_carrito(request, texto, error=True)


@require_POST
def eliminar(request, linea_id):
    if not eliminar_linea(buscar_carrito(request), linea_id):
        raise Http404("Esa línea no está en tu carrito.")
    return _respuesta_carrito(request, "Artículo eliminado del carrito.")
