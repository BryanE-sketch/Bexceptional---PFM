from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import Usuario


class UsuarioCreationForm(AdminUserCreationForm):
    """Formulario para crear usuarios desde el panel de administración."""

    class Meta:
        model = Usuario
        fields = ("email",)


class UsuarioChangeForm(UserChangeForm):
    """Formulario para editar usuarios desde el panel de administración."""

    class Meta:
        model = Usuario
        fields = ("email", "first_name", "last_name")