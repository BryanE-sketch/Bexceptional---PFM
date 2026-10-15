from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Categoria(models.Model):
    """Tipo de prenda o accesorio. Admite subcategorías (Ropa › Camisetas)."""

    nombre = models.CharField("nombre", max_length=80)
    slug = models.SlugField("slug", max_length=90, unique=True)
    padre = models.ForeignKey(
        "self",
        verbose_name="categoría padre",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="subcategorias",
    )
    imagen = models.ImageField("imagen", upload_to="categorias/", blank=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return f"{self.padre} › {self.nombre}" if self.padre else self.nombre


class Disciplina(models.Model):
    """Actividad deportiva: levantar pesas, correr, HIIT, descanso activo…"""

    nombre = models.CharField("nombre", max_length=60, unique=True)
    slug = models.SlugField("slug", max_length=70, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    imagen = models.ImageField("imagen", upload_to="disciplinas/", blank=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Talla(models.Model):
    nombre = models.CharField("nombre", max_length=20, unique=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "talla"
        verbose_name_plural = "tallas"
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class Color(models.Model):
    nombre = models.CharField("nombre", max_length=40, unique=True)
    codigo_hex = models.CharField(
        "código hexadecimal",
        max_length=7,
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Usa el formato #RRGGBB, por ejemplo #121214.")],
    )

    class Meta:
        verbose_name = "color"
        verbose_name_plural = "colores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    class Publico(models.TextChoices):
        MUJER = "mujer", "Mujer"
        HOMBRE = "hombre", "Hombre"
        UNISEX = "unisex", "Unisex"

    nombre = models.CharField("nombre", max_length=120)
    slug = models.SlugField("slug", max_length=140, unique=True)
    descripcion = models.TextField("descripción")
    precio = models.DecimalField(
        "precio (€)",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    categoria = models.ForeignKey(
        Categoria, verbose_name="categoría", on_delete=models.PROTECT, related_name="productos"
    )
    disciplinas = models.ManyToManyField(
        Disciplina, verbose_name="disciplinas", blank=True, related_name="productos"
    )
    publico = models.CharField("público", max_length=10, choices=Publico.choices, default=Publico.UNISEX)
    activo = models.BooleanField("activo", default=True, help_text="Desmárcalo para ocultarlo de la tienda.")
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["-creado"]
        constraints = [
            # Segunda barrera en la base de datos: ningún precio puede ser 0 o negativo
            models.CheckConstraint(condition=models.Q(precio__gt=0), name="precio_positivo"),
        ]

    def __str__(self):
        return self.nombre


class Variante(models.Model):
    """Combinación concreta que se vende: producto + talla + color, con su stock."""

    producto = models.ForeignKey(
        Producto, verbose_name="producto", on_delete=models.CASCADE, related_name="variantes"
    )
    talla = models.ForeignKey(Talla, verbose_name="talla", on_delete=models.PROTECT)
    color = models.ForeignKey(Color, verbose_name="color", on_delete=models.PROTECT)
    sku = models.CharField("SKU", max_length=40, unique=True, help_text="Código interno, p. ej. BX-CAM-NEG-M")
    stock = models.PositiveIntegerField("stock", default=0)

    class Meta:
        verbose_name = "variante"
        verbose_name_plural = "variantes"
        ordering = ["producto", "color", "talla__orden"]
        constraints = [
            models.UniqueConstraint(fields=["producto", "talla", "color"], name="variante_unica"),
        ]

    def __str__(self):
        return f"{self.producto} · {self.color} · {self.talla}"


class ImagenProducto(models.Model):
    producto = models.ForeignKey(
        Producto, verbose_name="producto", on_delete=models.CASCADE, related_name="imagenes"
    )
    color = models.ForeignKey(
        Color,
        verbose_name="color",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Opcional: muestra esta imagen al elegir este color.",
    )
    imagen = models.ImageField("imagen", upload_to="productos/")
    texto_alternativo = models.CharField(
        "texto alternativo", max_length=150, help_text="Describe la imagen para lectores de pantalla."
    )
    orden = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "imagen"
        verbose_name_plural = "imágenes"
        ordering = ["orden"]

    def __str__(self):
        return f"Imagen de {self.producto}"


class Favorito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="usuario", on_delete=models.CASCADE, related_name="favoritos"
    )
    producto = models.ForeignKey(
        Producto, verbose_name="producto", on_delete=models.CASCADE, related_name="favoritos"
    )
    creado = models.DateTimeField("añadido", auto_now_add=True)

    class Meta:
        verbose_name = "favorito"
        verbose_name_plural = "favoritos"
        constraints = [
            models.UniqueConstraint(fields=["usuario", "producto"], name="favorito_unico"),
        ]

    def __str__(self):
        return f"{self.usuario} ♥ {self.producto}"