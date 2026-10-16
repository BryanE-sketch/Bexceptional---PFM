from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import Direccion, RegistroAcceso, Usuario


class DireccionInline(admin.StackedInline):
    model = Direccion
    extra = 0


class RegistroAccesoInline(admin.TabularInline):
    """Últimos inicios de sesión del cliente, solo lectura."""

    model = RegistroAcceso
    extra = 0
    can_delete = False
    readonly_fields = ("fecha", "ip", "dispositivo")
    fields = readonly_fields
    max_num = 0  # no permite añadir registros a mano


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    inlines = [DireccionInline, RegistroAccesoInline]
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    model = Usuario

    # Listado: los registros más recientes primero (seguimiento de clientes)
    list_display = ("email", "first_name", "last_name", "is_staff", "date_joined", "last_login")
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

    # Ficha de edición
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("date_joined", "last_login")}),
    )

    # Formulario de alta
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "usable_password", "password1", "password2"),
        }),
    )


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "fecha", "ip", "dispositivo")
    list_filter = ("fecha",)
    search_fields = ("usuario__email", "ip")
    date_hierarchy = "fecha"
    readonly_fields = ("usuario", "fecha", "ip", "dispositivo")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False