from django.contrib import admin

from .models import Carrito, LineaCarrito


class LineaCarritoInline(admin.TabularInline):
    model = LineaCarrito
    extra = 0
    readonly_fields = ("variante", "cantidad")
    can_delete = False


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "num_articulos", "actualizado")
    list_filter = ("actualizado",)
    search_fields = ("usuario__email",)
    inlines = [LineaCarritoInline]
    readonly_fields = ("usuario", "creado", "actualizado")

    def has_add_permission(self, request):
        return False  # los carritos se crean desde la tienda, no a mano