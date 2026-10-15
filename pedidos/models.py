import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def generar_numero_pedido():
    """Número legible y difícil de adivinar, p. ej. BX261015-4F9A2C."""
    return f"BX{timezone.now():%y%m%d}-{secrets.token_hex(3).upper()}"


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PAGADO = "pagado", "Pagado"
        ENVIADO = "enviado", "Enviado"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    numero = models.CharField("número", max_length=20, unique=True, default=generar_numero_pedido, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="cliente", on_delete=models.PROTECT, related_name="pedidos"
    )
    estado = models.CharField("estado", max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)

    # Dirección COPIADA en el momento de la compra: si el cliente la cambia después,
    # el pedido conserva la dirección a la que realmente se envió.
    nombre_destinatario = models.CharField("destinatario", max_length=120)
    direccion = models.CharField("dirección", max_length=200)
    ciudad = models.CharField("ciudad", max_length=80)
    codigo_postal = models.CharField("código postal", max_length=10)
    provincia = models.CharField("provincia", max_length=80)
    telefono = models.CharField("teléfono", max_length=20)

    subtotal = models.DecimalField("subtotal (€)", max_digits=10, decimal_places=2)
    gastos_envio = models.DecimalField("gastos de envío (€)", max_digits=6, decimal_places=2)
    total = models.DecimalField("total (€)", max_digits=10, decimal_places=2)

    creado = models.DateTimeField("fecha", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-creado"]

    def __str__(self):
        return f"Pedido {self.numero}"


class LineaPedido(models.Model):
    pedido = models.ForeignKey(Pedido, verbose_name="pedido", on_delete=models.CASCADE, related_name="lineas")
    # Si algún día se borra la variante, la línea se conserva gracias a los datos copiados
    variante = models.ForeignKey(
        "catalogo.Variante", verbose_name="variante", on_delete=models.SET_NULL, null=True, blank=True
    )
    nombre_producto = models.CharField("producto", max_length=120)
    talla = models.CharField("talla", max_length=20)
    color = models.CharField("color", max_length=40)
    precio_unitario = models.DecimalField("precio unitario (€)", max_digits=8, decimal_places=2)
    cantidad = models.PositiveIntegerField("cantidad")

    class Meta:
        verbose_name = "línea de pedido"
        verbose_name_plural = "líneas de pedido"

    def __str__(self):
        return f"{self.cantidad} × {self.nombre_producto} ({self.color}, {self.talla})"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad


class Pago(models.Model):
    """Pago SIMULADO: no se envían ni se guardan datos reales de tarjeta."""

    class Metodo(models.TextChoices):
        TARJETA = "tarjeta", "Tarjeta bancaria"
        PAYPAL = "paypal", "PayPal"
        APPLE_PAY = "apple_pay", "Apple Pay"

    pedido = models.OneToOneField(Pedido, verbose_name="pedido", on_delete=models.CASCADE, related_name="pago")
    metodo = models.CharField("método", max_length=12, choices=Metodo.choices)
    referencia = models.CharField("referencia simulada", max_length=30, unique=True)
    importe = models.DecimalField("importe (€)", max_digits=10, decimal_places=2)
    creado = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"

    def __str__(self):
        return f"{self.get_metodo_display()} · {self.referencia}"