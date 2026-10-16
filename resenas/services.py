from django.db.models import Avg, Count

from pedidos.models import Pedido


def puede_resenar(usuario, producto):
    """Compra verificada: solo quien ha RECIBIDO el producto puede opinar sobre él."""
    if not usuario.is_authenticated:
        return False
    return Pedido.objects.filter(
        usuario=usuario,
        estado=Pedido.Estado.ENTREGADO,
        lineas__variante__producto=producto,
    ).exists()


def resumen_valoraciones(producto):
    """Media y número de reseñas APROBADAS de un producto."""
    datos = producto.resenas.filter(aprobada=True).aggregate(media=Avg("puntuacion"), total=Count("id"))
    media = round(datos["media"], 1) if datos["media"] is not None else None
    return {"media": media, "total": datos["total"]}