"""
Vistas de la API del catálogo (solo lectura).

    GET /api/productos/          listado con filtros, búsqueda, orden y paginación
    GET /api/productos/<slug>/   ficha de un producto
    GET /api/filtros/            opciones disponibles para pintar los filtros
"""
from decimal import Decimal

from django.db.models import Max, Min, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import ProductoFilter
from .models import Categoria, Color, Disciplina, ImagenProducto, Producto, Talla, Variante
from .serializers import (
    CategoriaResumenSerializer,
    ColorSerializer,
    DisciplinaSerializer,
    ProductoDetalleSerializer,
    ProductoListaSerializer,
    TallaSerializer,
)


class PaginacionTienda(PageNumberPagination):
    page_size = 12                      # productos por página
    page_query_param = "pagina"         # ?pagina=2
    page_size_query_param = "por_pagina"
    max_page_size = 48                  # nadie puede pedir 10 000 de golpe


def productos_publicados():
    """Productos activos con TODO lo que necesitan los serializadores ya precargado."""
    return (
        Producto.objects.filter(activo=True, categoria__activa=True)
        .select_related("categoria")
        .prefetch_related(
            Prefetch("variantes", queryset=Variante.objects.select_related("talla", "color")
                     .order_by("color__nombre", "talla__orden")),
            Prefetch("imagenes", queryset=ImagenProducto.objects.order_by("orden", "pk")),
            "disciplinas",
        )
        .order_by("-creado", "pk")      # orden por defecto: novedades primero
    )


class ProductoViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo público. ReadOnly: la API no permite crear, editar ni borrar."""

    lookup_field = "slug"
    pagination_class = PaginacionTienda
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductoFilter

    def get_queryset(self):
        return productos_publicados()

    def get_serializer_class(self):
        return ProductoDetalleSerializer if self.action == "retrieve" else ProductoListaSerializer


class FiltrosView(APIView):
    """Solo devuelve opciones que tienen algún producto publicado (sin filtros vacíos)."""

    @extend_schema(responses=inline_serializer("Filtros", {
        "categorias": serializers.ListField(),
        "disciplinas": DisciplinaSerializer(many=True),
        "colores": ColorSerializer(many=True),
        "tallas": TallaSerializer(many=True),
        "precio": serializers.DictField(),
        "publicos": serializers.ListField(),
    }))
    def get(self, request):
        publicados = Producto.objects.filter(activo=True, categoria__activa=True)
        variantes = Variante.objects.filter(producto__in=publicados)

        # Árbol de categorías: raíces con sus subcategorías que tengan productos
        con_productos = set(publicados.values_list("categoria_id", flat=True))
        raices = Categoria.objects.filter(padre__isnull=True, activa=True).prefetch_related(
            Prefetch("subcategorias", queryset=Categoria.objects.filter(activa=True))
        )
        categorias = []
        for raiz in raices:
            hijas = [h for h in raiz.subcategorias.all() if h.pk in con_productos]
            if hijas or raiz.pk in con_productos:
                categorias.append({
                    **CategoriaResumenSerializer(raiz).data,
                    "subcategorias": CategoriaResumenSerializer(hijas, many=True).data,
                })

        precios = publicados.aggregate(minimo=Min("precio"), maximo=Max("precio"))
        # Mismo formato que el campo "precio" de los productos: texto con 2 decimales
        precios = {clave: f"{Decimal(valor):.2f}" if valor is not None else None for clave, valor in precios.items()}
        return Response({
            "categorias": categorias,
            "disciplinas": DisciplinaSerializer(
                Disciplina.objects.filter(activa=True, productos__in=publicados).distinct(), many=True).data,
            "colores": ColorSerializer(
                Color.objects.filter(variante__in=variantes).distinct(), many=True).data,
            "tallas": TallaSerializer(
                Talla.objects.filter(variante__in=variantes).distinct().order_by("orden"), many=True).data,
            "precio": precios,
            "publicos": [{"valor": v, "nombre": n} for v, n in Producto.Publico.choices],
        })
