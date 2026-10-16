from django.contrib import admin

from .models import Resena


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("producto", "usuario", "puntuacion", "titulo", "aprobada", "es_demo", "creado")
    list_filter = ("aprobada", "puntuacion", "es_demo", "creado")
    search_fields = ("titulo", "texto", "usuario__email", "producto__nombre")
    actions = ["aprobar", "retirar"]
    # El administrador modera, pero no puede escribir ni alterar opiniones de clientes
    readonly_fields = ("usuario", "producto", "puntuacion", "titulo", "texto", "foto", "es_demo", "creado")

    def has_add_permission(self, request):
        return False  # las reseñas solo las escriben clientes con compra verificada

    @admin.action(description="Aprobar y publicar las reseñas seleccionadas")
    def aprobar(self, request, queryset):
        self.message_user(request, f"{queryset.update(aprobada=True)} reseña(s) aprobada(s).")

    @admin.action(description="Retirar de la web las reseñas seleccionadas")
    def retirar(self, request, queryset):
        self.message_user(request, f"{queryset.update(aprobada=False)} reseña(s) retirada(s).")