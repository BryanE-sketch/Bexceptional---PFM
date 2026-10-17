"""
Filtros de la tienda (django-filter).

Cada filtro se corresponde con un parámetro de la URL, por ejemplo:

    /api/productos/?publico=mujer&categoria=accesorios&color=1,3&talla=4&en_stock=true&orden=precio

Así la tienda se puede enlazar y compartir: la URL guarda la búsqueda completa.
"""
from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Categoria, Producto, Variante


class NumerosFilter(filters.BaseInFilter, filters.NumberFilter):
    """Acepta varios números separados por comas: ?color=1,3"""


class TextosFilter(filters.BaseInFilter, filters.CharFilter):
    """Acepta varios textos separados por comas: ?disciplina=running,gimnasio"""


def ids_con_descendientes(slug):
    """
    Devuelve el id de la categoría y el de todas sus subcategorías (a cualquier profundidad).
    Así ?categoria=accesorios incluye riñoneras, gorras, calcetines...
    """
    raiz = Categoria.objects.filter(slug=slug, activa=True).values_list("pk", flat=True).first()
    if raiz is None:
        return []
    ids, pendientes = {raiz}, [raiz]
    while pendientes:  # recorrido por niveles; "ids" evita bucles aunque los datos estén mal
        hijas = set(Categoria.objects.filter(padre_id__in=pendientes, activa=True).values_list("pk", flat=True))
        pendientes = list(hijas - ids)
        ids |= hijas
    return list(ids)


class ProductoFilter(filters.FilterSet):
    q = filters.CharFilter(method="filtrar_texto", label="Buscar")
    publico = filters.ChoiceFilter(choices=Producto.Publico.choices, method="filtrar_publico")
    categoria = filters.CharFilter(method="filtrar_categoria", label="Categoría (slug)")
    disciplina = TextosFilter(field_name="disciplinas__slug", label="Disciplinas (slugs separados por comas)",
                              distinct=True)
    precio_min = filters.NumberFilter(field_name="precio", lookup_expr="gte")
    precio_max = filters.NumberFilter(field_name="precio", lookup_expr="lte")

    # Estos tres se aplican JUNTOS en filter_queryset (ver abajo), por eso su método no hace nada
    color = NumerosFilter(method="aplicar_despues", label="Colores (ids separados por comas)")
    talla = NumerosFilter(method="aplicar_despues", label="Tallas (ids separados por comas)")
    en_stock = filters.BooleanFilter(method="aplicar_despues", label="Solo con stock")

    orden = filters.OrderingFilter(
        fields=(("precio", "precio"), ("creado", "novedad"), ("nombre", "nombre")),
        label="Orden: precio, -precio, -novedad, nombre",
    )

    class Meta:
        model = Producto
        fields = []  # todos los filtros están declarados arriba

    def filtrar_texto(self, queryset, name, valor):
        palabras = valor.split()[:5]  # límite razonable para no generar consultas enormes
        for palabra in palabras:
            queryset = queryset.filter(
                Q(nombre__icontains=palabra) | Q(descripcion__icontains=palabra) | Q(categoria__nombre__icontains=palabra)
            )
        return queryset

    def filtrar_publico(self, queryset, name, valor):
        # Decisión de negocio: lo unisex aparece tanto en Mujeres como en Hombres
        if valor in (Producto.Publico.MUJER, Producto.Publico.HOMBRE):
            return queryset.filter(publico__in=[valor, Producto.Publico.UNISEX])
        return queryset.filter(publico=valor)

    def filtrar_categoria(self, queryset, name, slug):
        return queryset.filter(categoria_id__in=ids_con_descendientes(slug))

    def aplicar_despues(self, queryset, name, valor):
        return queryset

    def filter_queryset(self, queryset):
        """
        Color, talla y stock deben cumplirse en LA MISMA variante.
        Ejemplo: "negro + talla M + con stock" no debe devolver una camiseta que
        tenga la M agotada en negro aunque tenga la M en blanco.
        """
        queryset = super().filter_queryset(queryset)
        datos = self.form.cleaned_data
        variantes = Variante.objects.all()
        if datos.get("color"):
            variantes = variantes.filter(color_id__in=datos["color"])
        if datos.get("talla"):
            variantes = variantes.filter(talla_id__in=datos["talla"])
        if datos.get("en_stock"):
            variantes = variantes.filter(stock__gt=0)
        if datos.get("color") or datos.get("talla") or datos.get("en_stock"):
            # Subconsulta (pk__in) en lugar de JOIN: así no se duplican productos
            queryset = queryset.filter(pk__in=variantes.values("producto_id"))
        return queryset
