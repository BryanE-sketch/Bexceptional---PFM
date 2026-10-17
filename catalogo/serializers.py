"""
Serializadores de la API del catálogo.

Un serializador traduce un objeto de Django (un Producto) a JSON, que es lo que
entiende React. Solo exponemos lo que la tienda necesita: nunca el SKU interno
ni el stock exacto de cada variante en el listado.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Categoria, Color, Disciplina, Producto, Talla, Variante


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ["id", "nombre", "codigo_hex"]


class TallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Talla
        fields = ["id", "nombre"]


class CategoriaResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["nombre", "slug"]


class DisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disciplina
        fields = ["nombre", "slug"]


class ProductoListaSerializer(serializers.ModelSerializer):
    """Lo justo para pintar una tarjeta de producto en la tienda."""

    url = serializers.CharField(source="get_absolute_url", read_only=True)
    categoria = CategoriaResumenSerializer(read_only=True)
    imagen = serializers.SerializerMethodField()
    imagenes_por_color = serializers.SerializerMethodField()
    colores = serializers.SerializerMethodField()
    agotado = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ["id", "nombre", "slug", "url", "precio", "publico", "categoria",
                  "imagen", "imagenes_por_color", "colores", "agotado"]

    # Todos estos métodos usan .all() sobre datos ya precargados con prefetch_related
    # en la vista, así que NO lanzan consultas nuevas por cada producto (evita el N+1).

    @extend_schema_field(OpenApiTypes.STR)
    def get_imagen(self, producto):
        """Foto principal: la del primer color que se ofrece, para que coincidan foto y muestra."""
        colores = self._colores(producto)
        por_color = self.get_imagenes_por_color(producto)
        if colores and colores[0].pk in por_color:
            return por_color[colores[0].pk]
        primera = next(iter(producto.imagenes.all()), None)
        return primera.imagen.url if primera else None

    @extend_schema_field({"type": "object", "additionalProperties": {"type": "string"}})
    def get_imagenes_por_color(self, producto):
        """{id_color: url} para cambiar la foto al pasar por encima de un color."""
        resultado = {}
        for img in producto.imagenes.all():
            if img.color_id and img.color_id not in resultado:
                resultado[img.color_id] = img.imagen.url
        return resultado

    @staticmethod
    def _colores(producto):
        # dict.fromkeys quita duplicados y conserva el orden
        return list(dict.fromkeys(v.color for v in producto.variantes.all()))

    @extend_schema_field(ColorSerializer(many=True))
    def get_colores(self, producto):
        return ColorSerializer(self._colores(producto), many=True).data

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_agotado(self, producto):
        return not any(v.stock for v in producto.variantes.all())


class VarianteSerializer(serializers.ModelSerializer):
    talla = TallaSerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    disponible = serializers.SerializerMethodField()

    class Meta:
        model = Variante
        # Mostramos "disponible" (sí/no) en lugar del número exacto de unidades
        fields = ["id", "talla", "color", "disponible"]

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_disponible(self, variante):
        return variante.stock > 0


class ProductoDetalleSerializer(ProductoListaSerializer):
    """La ficha completa: añade descripción, disciplinas, variantes e imágenes."""

    disciplinas = DisciplinaSerializer(many=True, read_only=True)
    variantes = VarianteSerializer(many=True, read_only=True)
    imagenes = serializers.SerializerMethodField()

    class Meta(ProductoListaSerializer.Meta):
        fields = ProductoListaSerializer.Meta.fields + ["descripcion", "disciplinas", "variantes", "imagenes"]

    @extend_schema_field({"type": "array", "items": {"type": "object"}})
    def get_imagenes(self, producto):
        return [
            {"url": img.imagen.url, "texto_alternativo": img.texto_alternativo, "color": img.color_id}
            for img in producto.imagenes.all()
        ]
