"""Lógica del carrito, separada de las vistas para poder reutilizarla y probarla."""

from django.db import transaction

from .models import Carrito, LineaCarrito

SESION_CARRITO = "carrito_id"


class StockInsuficienteError(Exception):
    """Se intenta añadir más unidades de las disponibles."""


def obtener_carrito(request):
    """Devuelve el carrito del usuario o del visitante, y lo crea si no existe."""
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        return carrito

    carrito_id = request.session.get(SESION_CARRITO)
    if carrito_id:
        carrito = Carrito.objects.filter(pk=carrito_id, usuario__isnull=True).first()
        if carrito:
            return carrito
    carrito = Carrito.objects.create()
    request.session[SESION_CARRITO] = carrito.pk
    return carrito


def anadir_al_carrito(carrito, variante, cantidad=1):
    """Suma unidades de una variante sin superar el stock disponible."""
    if cantidad < 1:
        raise ValueError("La cantidad debe ser al menos 1.")
    if not variante.producto.activo:
        raise StockInsuficienteError("Este producto ya no está disponible.")

    linea = LineaCarrito.objects.filter(carrito=carrito, variante=variante).first()
    nueva_cantidad = (linea.cantidad if linea else 0) + cantidad
    if nueva_cantidad > variante.stock:
        raise StockInsuficienteError(f"Solo quedan {variante.stock} unidades.")

    if linea:
        linea.cantidad = nueva_cantidad
        linea.save(update_fields=["cantidad"])
    else:
        linea = LineaCarrito.objects.create(carrito=carrito, variante=variante, cantidad=cantidad)
    return linea


@transaction.atomic
def fusionar_carrito_de_visitante(request, usuario):
    """Al iniciar sesión, pasa los productos del carrito de visitante a la cuenta."""
    carrito_id = request.session.pop(SESION_CARRITO, None)
    if not carrito_id:
        return
    visitante = Carrito.objects.filter(pk=carrito_id, usuario__isnull=True).first()
    if not visitante:
        return

    carrito_cliente, _ = Carrito.objects.get_or_create(usuario=usuario)
    for linea in visitante.lineas.select_related("variante"):
        existente = carrito_cliente.lineas.filter(variante=linea.variante).first()
        total = (existente.cantidad if existente else 0) + linea.cantidad
        total = min(total, linea.variante.stock)  # nunca más que el stock
        if total < 1:
            continue
        LineaCarrito.objects.update_or_create(
            carrito=carrito_cliente, variante=linea.variante, defaults={"cantidad": total}
        )
    visitante.delete()
    


def cantidad_en_carrito(request):
    """Número de artículos del carrito, SIN crearlo (para el icono de la cabecera)."""
    from django.db.models import Sum

    if request.user.is_authenticated:
        lineas = LineaCarrito.objects.filter(carrito__usuario=request.user)
    else:
        carrito_id = request.session.get(SESION_CARRITO)
        if not carrito_id:
            return 0
        lineas = LineaCarrito.objects.filter(carrito_id=carrito_id, carrito__usuario__isnull=True)
    return lineas.aggregate(total=Sum("cantidad"))["total"] or 0