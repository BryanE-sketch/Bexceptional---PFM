from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class ArticuloQuerySet(models.QuerySet):
    def publicados(self):
        """Solo lo que el público puede ver: publicado y con fecha ya alcanzada."""
        return self.filter(estado=Articulo.Estado.PUBLICADO, publicado_en__lte=timezone.now())


class Articulo(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PUBLICADO = "publicado", "Publicado"

    titulo = models.CharField("título", max_length=160)
    slug = models.SlugField("slug", max_length=180, unique=True)
    disciplina = models.ForeignKey(
        "catalogo.Disciplina",
        verbose_name="disciplina",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articulos",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="autor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articulos",
    )
    portada = models.ImageField("imagen de portada", upload_to="articulos/", blank=True)
    resumen = models.CharField("resumen", max_length=300, help_text="Una o dos frases para el listado.")
    cuerpo = models.TextField("texto", help_text="Texto plano: los saltos de línea separan párrafos.")
    estado = models.CharField("estado", max_length=10, choices=Estado.choices, default=Estado.BORRADOR)
    publicado_en = models.DateTimeField(
        "fecha de publicación",
        null=True,
        blank=True,
        help_text="Si la dejas vacía, se usa el momento en que se publica. Una fecha futura lo programa.",
    )
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    objects = ArticuloQuerySet.as_manager()

    class Meta:
        verbose_name = "artículo"
        verbose_name_plural = "artículos"
        ordering = ["-publicado_en", "-creado"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if self.estado == self.Estado.PUBLICADO and self.publicado_en is None:
            self.publicado_en = timezone.now()
        super().save(*args, **kwargs)


class FuenteArticulo(models.Model):
    """Fuente científica citada en un artículo (con su enlace «Ver más»)."""

    articulo = models.ForeignKey(Articulo, verbose_name="artículo", on_delete=models.CASCADE, related_name="fuentes")
    nombre = models.CharField("nombre de la fuente", max_length=200, help_text="p. ej. Lally et al. (2010)")
    url = models.URLField("enlace")

    class Meta:
        verbose_name = "fuente"
        verbose_name_plural = "fuentes"

    def __str__(self):
        return self.nombre


class Consejo(models.Model):
    """Dato breve de evidencia para la sección Hábitos, con su botón «Ver más»."""

    titulo = models.CharField("título", max_length=120)
    texto = models.CharField("texto", max_length=400)
    disciplina = models.ForeignKey(
        "catalogo.Disciplina",
        verbose_name="disciplina",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consejos",
    )
    fuente_nombre = models.CharField("nombre de la fuente", max_length=200)
    fuente_url = models.URLField("enlace a la fuente")
    orden = models.PositiveSmallIntegerField("orden", default=0)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "consejo"
        verbose_name_plural = "consejos"
        ordering = ["orden", "titulo"]

    def __str__(self):
        return self.titulo


class Recurso(models.Model):
    """Archivo descargable de la sección Hábitos (rastreadores, plantillas, guías)."""

    class Tipo(models.TextChoices):
        RASTREADOR = "rastreador", "Rastreador de hábitos"
        PLANTILLA = "plantilla", "Plantilla"
        GUIA = "guia", "Guía"

    titulo = models.CharField("título", max_length=120)
    slug = models.SlugField("slug", max_length=140, unique=True)
    descripcion = models.CharField("descripción", max_length=300)
    tipo = models.CharField("tipo", max_length=12, choices=Tipo.choices, default=Tipo.RASTREADOR)
    archivo = models.FileField(
        "archivo PDF",
        upload_to="recursos/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    imagen_previa = models.ImageField("imagen de vista previa", upload_to="recursos/previas/", blank=True)
    publicado = models.BooleanField("publicado", default=True)
    descargas = models.PositiveIntegerField("descargas", default=0, editable=False)
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "recurso descargable"
        verbose_name_plural = "recursos descargables"
        ordering = ["-creado"]

    def __str__(self):
        return self.titulo