from django.contrib import admin
from django.utils import timezone

from .models import Articulo, Consejo, FuenteArticulo, Recurso


class FuenteInline(admin.TabularInline):
    model = FuenteArticulo
    extra = 1


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ("titulo", "disciplina", "estado", "publicado_en", "autor")
    list_filter = ("estado", "disciplina", "publicado_en")
    search_fields = ("titulo", "resumen", "cuerpo")
    prepopulated_fields = {"slug": ("titulo",)}
    date_hierarchy = "publicado_en"
    inlines = [FuenteInline]
    readonly_fields = ("autor", "creado", "actualizado")
    actions = ["publicar", "pasar_a_borrador"]

    def save_model(self, request, obj, form, change):
        if obj.autor_id is None:
            obj.autor = request.user  # el autor es quien lo crea
        super().save_model(request, obj, form, change)

    @admin.action(description="Publicar ahora los artículos seleccionados")
    def publicar(self, request, queryset):
        actualizados = queryset.update(estado=Articulo.Estado.PUBLICADO, publicado_en=timezone.now())
        self.message_user(request, f"{actualizados} artículo(s) publicado(s).")

    @admin.action(description="Pasar a borrador")
    def pasar_a_borrador(self, request, queryset):
        actualizados = queryset.update(estado=Articulo.Estado.BORRADOR)
        self.message_user(request, f"{actualizados} artículo(s) en borrador.")


@admin.register(Consejo)
class ConsejoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "disciplina", "fuente_nombre", "orden", "activo")
    list_editable = ("orden", "activo")
    list_filter = ("activo", "disciplina")
    search_fields = ("titulo", "texto", "fuente_nombre")


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "publicado", "descargas", "creado")
    list_editable = ("publicado",)
    list_filter = ("tipo", "publicado")
    search_fields = ("titulo", "descripcion")
    prepopulated_fields = {"slug": ("titulo",)}
    readonly_fields = ("descargas", "creado")