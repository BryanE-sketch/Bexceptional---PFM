from django.contrib import admin
from django.db.models import Sum

from .models import Categoria, Color, Disciplina, Favorito, ImagenProducto, Producto, Talla, Variante


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "padre", "orden", "activa")
    list_editable = ("orden", "activa")
    list_filter = ("activa", "padre")
    search_fields = ("nombre",)
    prepopulated_fields = {"slug": ("nombre",)}


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden", "activa")
    list_editable = ("orden", "activa")
    search_fields = ("nombre",)
    prepopulated_fields = {"slug": ("nombre",)}


@admin.register(Talla)
class TallaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden")
    list_editable = ("orden",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo_hex")
    search_fields = ("nombre",)


class VarianteInline(admin.TabularInline):
    """Tallas, colores y stock se editan dentro de la ficha del producto."""

    model = Variante
    extra = 1
    fields = ("talla", "color", "sku", "stock")


class ImagenInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1
    fields = ("imagen", "color", "texto_alternativo", "orden")


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "publico", "precio", "stock_total", "activo")
    list_editable = ("precio", "activo")
    list_filter = ("activo", "publico", "categoria", "disciplinas")
    search_fields = ("nombre", "descripcion", "variantes__sku")
    prepopulated_fields = {"slug": ("nombre",)}
    filter_horizontal = ("disciplinas",)
    inlines = [VarianteInline, ImagenInline]

    def get_queryset(self, request):
        # Suma el stock de todas las variantes en UNA consulta (evita el problema N+1)
        return super().get_queryset(request).annotate(_stock_total=Sum("variantes__stock"))

    @admin.display(description="stock total", ordering="_stock_total")
    def stock_total(self, obj):
        return obj._stock_total or 0


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "producto", "creado")
    list_filter = ("creado",)
    search_fields = ("usuario__email", "producto__nombre")