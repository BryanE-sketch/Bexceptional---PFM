from django.contrib import admin, messages

from . import services
from .models import LineaPedido, Pago, Pedido


class LineaPedidoInline(admin.TabularInline):
    model = LineaPedido
    extra = 0
    can_delete = False
    readonly_fields = ("nombre_producto", "talla", "color", "precio_unitario", "cantidad")
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


class PagoInline(admin.StackedInline):
    model = Pago
    extra = 0
    can_delete = False
    readonly_fields = ("metodo", "referencia", "importe", "creado")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("numero", "usuario", "estado", "total", "creado")
    list_filter = ("estado", "creado")
    search_fields = ("numero", "usuario__email", "nombre_destinatario")
    date_hierarchy = "creado"
    inlines = [LineaPedidoInline, PagoInline]
    actions = ["cancelar_seleccionados"]
    readonly_fields = ("numero", "usuario", "subtotal", "gastos_envio", "total", "creado", "actualizado")
    fieldsets = (
        (None, {"fields": ("numero", "usuario", "estado")}),
        ("Envío", {"fields": ("nombre_destinatario", "direccion", "ciudad", "codigo_postal", "provincia", "telefono")}),
        ("Importes", {"fields": ("subtotal", "gastos_envio", "total")}),
        ("Fechas", {"fields": ("creado", "actualizado")}),
    )

    def has_add_permission(self, request):
        return False  # los pedidos solo se crean desde la tienda

    def save_model(self, request, obj, form, change):
        # Si el administrador cambia el estado a "cancelado", se repone el stock
        if change and "estado" in form.changed_data and obj.estado == Pedido.Estado.CANCELADO:
            anterior = Pedido.objects.get(pk=obj.pk)
            if anterior.estado in (Pedido.Estado.PAGADO, Pedido.Estado.ENVIADO):
                services.reponer_stock(anterior)
                messages.info(request, "Se ha repuesto el stock de los productos del pedido.")
        super().save_model(request, obj, form, change)

    @admin.action(description="Cancelar los pedidos seleccionados (repone el stock)")
    def cancelar_seleccionados(self, request, queryset):
        for pedido in queryset:
            services.cancelar_pedido(pedido)
        self.message_user(request, f"{queryset.count()} pedido(s) cancelado(s) y stock repuesto.")