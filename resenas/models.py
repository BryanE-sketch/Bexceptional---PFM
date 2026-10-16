from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Resena(models.Model):
    """Opinión de un cliente con COMPRA VERIFICADA. Se publica cuando el administrador la aprueba."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="cliente", on_delete=models.CASCADE, related_name="resenas"
    )
    producto = models.ForeignKey(
        "catalogo.Producto", verbose_name="producto", on_delete=models.CASCADE, related_name="resenas"
    )
    puntuacion = models.PositiveSmallIntegerField(
        "puntuación", validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    titulo = models.CharField("título", max_length=120)
    texto = models.TextField("opinión", max_length=2000)
    foto = models.ImageField("foto", upload_to="resenas/", blank=True)
    aprobada = models.BooleanField("aprobada", default=False)
    es_demo = models.BooleanField(
        "dato de demostración",
        default=False,
        help_text="Marca las reseñas de los usuarios de prueba; la web las señala como demostración.",
    )
    creado = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        verbose_name = "reseña"
        verbose_name_plural = "reseñas"
        ordering = ["-creado"]
        constraints = [
            models.UniqueConstraint(fields=["usuario", "producto"], name="una_resena_por_producto"),
            models.CheckConstraint(
                condition=models.Q(puntuacion__gte=1, puntuacion__lte=5), name="puntuacion_entre_1_y_5"
            ),
        ]

    def __str__(self):
        return f"{self.producto} · {self.puntuacion}★ · {self.usuario}"

    def clean(self):
        from .services import puede_resenar  # import local: evita importaciones circulares

        if self.usuario_id and self.producto_id and not puede_resenar(self.usuario, self.producto):
            raise ValidationError("Solo puedes reseñar productos que hayas comprado y recibido.")