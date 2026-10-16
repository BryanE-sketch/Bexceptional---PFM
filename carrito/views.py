from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AnadirAlCarritoForm
from .services import StockInsuficienteError, anadir_al_carrito, cantidad_en_carrito, obtener_carrito


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