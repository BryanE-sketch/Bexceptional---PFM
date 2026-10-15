"""Creación y cancelación de pedidos.

Todo ocurre dentro de transacciones: o se completa entero, o no se guarda nada.
"""

import secrets
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from catalogo.models import Variante

from .models import LineaPedido, Pago, Pedido

GASTOS_ENVIO = Decimal("4.95")
ENVIO_GRATIS_DESDE = Decimal("50.00")

# Tarjeta de prueba que SIEMPRE se rechaza (para demostrar el error de pago)
TARJETA_RECHAZADA = "4000000000000002"


class CarritoVacioError(Exception):
    pass


class StockInsuficienteError(Exception):
    def __init__(self, variante):
        self.variante = variante
        super().__init__(f"No hay stock suficiente de {variante}.")


class PagoRechazadoError(Exception):
    pass


def calcular_gastos_envio(subtotal):
    return Decimal("0.00") if subtotal >= ENVIO_GRATIS_DESDE else GASTOS_ENVIO


def simular_pago(metodo, importe, numero_tarjeta=""):
    """Simula la pasarela de pago y devuelve una referencia ficticia."""
    if metodo == Pago.Metodo.TARJETA and numero_tarjeta.replace(" ", "") == TARJETA_RECHAZADA:
        raise PagoRechazadoError("El banco ha rechazado el pago (tarjeta de prueba).")
    return f"SIM-{secrets.token_hex(6).upper()}"


@transaction.atomic
def crear_pedido(usuario, carrito, datos_envio, metodo_pago, numero_tarjeta=""):
    """Convierte el carrito en un pedido pagado y descuenta el stock.

    1. Bloquea las filas de las variantes (select_for_update): si otro cliente
       intenta comprar las mismas a la vez, espera a que esta compra termine.
    2. Comprueba el stock con los datos ya bloqueados.
    3. Simula el pago. Si falla, la transacción se deshace: ni pedido ni stock cambian.
    4. Crea el pedido con los datos copiados, descuenta el stock y vacía el carrito.
    """
    lineas = list(carrito.lineas.select_related("variante"))
    if not lineas:
        raise CarritoVacioError("El carrito está vacío.")

    variantes = {
        v.pk: v
        for v in Variante.objects.select_for_update(of=("self",))
        .select_related("producto", "talla", "color")
        .filter(pk__in=[linea.variante_id for linea in lineas])
        .order_by("pk")  # mismo orden de bloqueo siempre: evita bloqueos cruzados
    }

    for linea in lineas:
        variante = variantes[linea.variante_id]
        if not variante.producto.activo or variante.stock < linea.cantidad:
            raise StockInsuficienteError(variante)

    subtotal = sum(
        (variantes[linea.variante_id].producto.precio * linea.cantidad for linea in lineas), Decimal("0.00")
    )
    gastos_envio = calcular_gastos_envio(subtotal)
    total = subtotal + gastos_envio

    referencia = simular_pago(metodo_pago, total, numero_tarjeta)

    pedido = Pedido.objects.create(
        usuario=usuario,
        estado=Pedido.Estado.PAGADO,
        subtotal=subtotal,
        gastos_envio=gastos_envio,
        total=total,
        **datos_envio,
    )
    for linea in lineas:
        variante = variantes[linea.variante_id]
        LineaPedido.objects.create(
            pedido=pedido,
            variante=variante,
            nombre_producto=variante.producto.nombre,
            talla=variante.talla.nombre,
            color=variante.color.nombre,
            precio_unitario=variante.producto.precio,
            cantidad=linea.cantidad,
        )
        # F() hace la resta dentro de la base de datos: stock = stock - cantidad
        Variante.objects.filter(pk=variante.pk).update(stock=F("stock") - linea.cantidad)

    Pago.objects.create(pedido=pedido, metodo=metodo_pago, referencia=referencia, importe=total)
    carrito.lineas.all().delete()
    return pedido


@transaction.atomic
def reponer_stock(pedido):
    """Devuelve al stock las unidades de un pedido que se cancela."""
    for linea in pedido.lineas.select_related("variante"):
        if linea.variante_id:
            Variante.objects.filter(pk=linea.variante_id).update(stock=F("stock") + linea.cantidad)


@transaction.atomic
def cancelar_pedido(pedido):
    """Cancela un pedido pagado y repone su stock. No hace nada si ya estaba cancelado."""
    if pedido.estado == Pedido.Estado.CANCELADO:
        return pedido
    if pedido.estado in (Pedido.Estado.PAGADO, Pedido.Estado.ENVIADO):
        reponer_stock(pedido)
    pedido.estado = Pedido.Estado.CANCELADO
    pedido.save(update_fields=["estado", "actualizado"])
    return pedido