from decimal import Decimal

from django.conf import settings
from django.db import models


class Carrito(models.Model):
    """Carrito de un cliente o de un visitante.

    - Cliente: el carrito está ligado a su usuario.
    - Visitante: usuario vacío; su id se guarda en la sesión del navegador.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carrito",
    )
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "carrito"
        verbose_name_plural = "carritos"

    def __str__(self):
        return f"Carrito de {self.usuario}" if self.usuario else f"Carrito de visitante #{self.pk}"

    @property
    def total(self):
        return sum((linea.subtotal for linea in self.lineas.all()), Decimal("0.00"))

    @property
    def num_articulos(self):
        return sum(linea.cantidad for linea in self.lineas.all())


class LineaCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, verbose_name="carrito", on_delete=models.CASCADE, related_name="lineas")
    variante = models.ForeignKey("catalogo.Variante", verbose_name="variante", on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField("cantidad", default=1)

    class Meta:
        verbose_name = "línea de carrito"
        verbose_name_plural = "líneas de carrito"
        constraints = [
            models.UniqueConstraint(fields=["carrito", "variante"], name="linea_carrito_unica"),
            models.CheckConstraint(condition=models.Q(cantidad__gte=1), name="cantidad_minima_1"),
        ]

    def __str__(self):
        return f"{self.cantidad} × {self.variante}"

    @property
    def subtotal(self):
        return self.variante.producto.precio * self.cantidad