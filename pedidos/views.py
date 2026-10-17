from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from carrito.services import buscar_carrito, resumen_carrito
from cuentas.models import Direccion

from .forms import CheckoutForm
from .models import Pedido
from .services import CarritoVacioError, PagoRechazadoError, StockInsuficienteError, crear_pedido

SESION_PEDIDO_NUEVO = "pedido_confirmado"


@login_required
def checkout(request):
    """CU-04: dirección + pago simulado → pedido. Si no hay sesión, @login_required manda a entrar y vuelve aquí."""
    carrito = buscar_carrito(request)
    resumen = resumen_carrito(carrito)
    if not resumen["lineas"]:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("carrito:detalle")
    if not resumen["se_puede_pagar"]:
        messages.error(request, "Algún artículo ya no tiene stock suficiente. Revisa tu carrito.")
        return redirect("carrito:detalle")

    # Rellenamos la dirección con la predeterminada del cliente, si la tiene
    predeterminada = request.user.direcciones.filter(predeterminada=True).first()
    inicial = predeterminada.datos_envio() if predeterminada else {"nombre_destinatario": request.user.get_full_name()}

    form = CheckoutForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        try:
            pedido = crear_pedido(
                usuario=request.user,
                carrito=carrito,
                datos_envio=form.datos_envio(),
                metodo_pago=form.cleaned_data["metodo"],
                numero_tarjeta=form.cleaned_data["numero_tarjeta"],
            )
        except PagoRechazadoError as error:
            # El pedido NO se ha creado y el stock no ha cambiado (la transacción se deshizo)
            form.add_error(None, f"{error} Prueba con otra tarjeta u otro método de pago.")
        except StockInsuficienteError as error:
            messages.error(request, f"{error} Hemos actualizado tu carrito.")
            return redirect("carrito:detalle")
        except CarritoVacioError:
            # Doble clic en «Pagar»: el primer envío ya creó el pedido y vació el carrito
            return redirect("cuentas:perfil")
        else:
            if form.cleaned_data["guardar_direccion"]:
                guardar_direccion_predeterminada(request.user, form.datos_envio())
            request.session[SESION_PEDIDO_NUEVO] = pedido.numero
            return redirect("pedidos:detalle", numero=pedido.numero)

    return render(request, "pedidos/checkout.html", {"form": form, **resumen})


@transaction.atomic
def guardar_direccion_predeterminada(usuario, datos):
    """Solo puede haber una predeterminada (lo exige una restricción de la base de datos)."""
    usuario.direcciones.filter(predeterminada=True).update(predeterminada=False)
    Direccion.objects.create(usuario=usuario, predeterminada=True, **datos)


@login_required
def detalle(request, numero):
    """Detalle de un pedido. Solo su dueño puede verlo (si no, 404: ni siquiera revelamos que existe)."""
    pedido = get_object_or_404(
        Pedido.objects.select_related("pago").prefetch_related("lineas"), numero=numero, usuario=request.user
    )
    recien_creado = request.session.pop(SESION_PEDIDO_NUEVO, None) == pedido.numero
    return render(request, "pedidos/detalle.html", {"pedido": pedido, "recien_creado": recien_creado})
