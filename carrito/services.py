"""Lógica del carrito, separada de las vistas para poder reutilizarla y probarla."""

from decimal import Decimal

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


# ── Página del carrito ────────────────────────────────────────

CANTIDAD_MAXIMA = 10  # tope por línea, igual que en la ficha de producto


def buscar_carrito(request):
    """Como obtener_carrito, pero SIN crearlo: ver la página del carrito no debe generar filas vacías."""
    if request.user.is_authenticated:
        return Carrito.objects.filter(usuario=request.user).first()
    carrito_id = request.session.get(SESION_CARRITO)
    if not carrito_id:
        return None
    return Carrito.objects.filter(pk=carrito_id, usuario__isnull=True).first()


def cambiar_cantidad(carrito, linea_id, cantidad):
    """
    Fija la cantidad de una línea. Solo puede tocar líneas de SU carrito:
    filtrar por carrito evita que alguien cambie el carrito de otra persona
    adivinando números de línea (vulnerabilidad IDOR).
    """
    linea = LineaCarrito.objects.select_related("variante__producto").get(pk=linea_id, carrito=carrito)
    if cantidad < 1:
        raise ValueError("La cantidad mínima es 1.")
    if cantidad > CANTIDAD_MAXIMA:
        raise StockInsuficienteError(f"Puedes comprar como máximo {CANTIDAD_MAXIMA} unidades de cada artículo.")
    if cantidad > linea.variante.stock:
        raise StockInsuficienteError(f"Solo quedan {linea.variante.stock} unidades.")
    linea.cantidad = cantidad
    linea.save(update_fields=["cantidad"])
    return linea


def eliminar_linea(carrito, linea_id):
    """Borra una línea de SU carrito. Devuelve True si existía."""
    borradas, _ = LineaCarrito.objects.filter(pk=linea_id, carrito=carrito).delete()
    return borradas > 0


def resumen_carrito(carrito):
    """
    Todo lo que necesita la página del carrito en una sola estructura:
    líneas (con su foto y avisos de stock), subtotal, envío y total.
    """
    from django.db.models import Prefetch

    from catalogo.models import ImagenProducto
    from pedidos.services import ENVIO_GRATIS_DESDE, calcular_gastos_envio

    lineas = []
    if carrito:
        lineas = list(
            carrito.lineas.select_related("variante__producto", "variante__talla", "variante__color")
            .prefetch_related(Prefetch("variante__producto__imagenes",
                                       queryset=ImagenProducto.objects.order_by("orden", "pk")))
            .order_by("pk")
        )
    for linea in lineas:
        variante = linea.variante
        imagenes = list(variante.producto.imagenes.all())
        # La foto del mismo color que eligió el cliente; si no hay, la primera
        linea.imagen = next((i for i in imagenes if i.color_id == variante.color_id), imagenes[0] if imagenes else None)
        linea.disponible = variante.producto.activo and variante.stock > 0
        linea.sin_stock_suficiente = linea.disponible and variante.stock < linea.cantidad
        linea.maximo = min(variante.stock, CANTIDAD_MAXIMA)

    subtotal = sum((linea.subtotal for linea in lineas), Decimal("0.00"))
    envio = calcular_gastos_envio(subtotal) if lineas else Decimal("0.00")
    return {
        "lineas": lineas,
        "num_articulos": sum(linea.cantidad for linea in lineas),
        "subtotal": subtotal,
        "envio": envio,
        "total": subtotal + envio,
        "falta_para_envio_gratis": max(ENVIO_GRATIS_DESDE - subtotal, Decimal("0.00")),
        "envio_gratis_desde": ENVIO_GRATIS_DESDE,
        # Se puede pagar solo si todas las líneas tienen stock suficiente
        "se_puede_pagar": bool(lineas) and all(l.disponible and not l.sin_stock_suficiente for l in lineas),
    }
