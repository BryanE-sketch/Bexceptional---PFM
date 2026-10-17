from django import forms
from django.contrib.auth.forms import AdminUserCreationForm, AuthenticationForm, BaseUserCreationForm, UserChangeForm
from django.core.cache import cache

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


# ── Formularios de la web ─────────────────────────────────────

class RegistroForm(BaseUserCreationForm):
    """
    Alta de clientes. BaseUserCreationForm ya trae las dos contraseñas y aplica
    los validadores de AUTH_PASSWORD_VALIDATORS (longitud, contraseñas comunes...).
    """

    acepta_privacidad = forms.BooleanField(
        label="He leído y acepto que Bexceptional trate mis datos para gestionar mi cuenta y mis pedidos.",
        error_messages={"required": "Necesitamos tu consentimiento para crear la cuenta."},
    )

    class Meta:
        model = Usuario
        fields = ("first_name", "email")
        labels = {"first_name": "Nombre", "email": "Correo electrónico"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["email"].widget.attrs.update(autocomplete="email")
        self.fields["first_name"].widget.attrs.update(autocomplete="given-name")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        # Comparación sin mayúsculas: Ana@x.com y ana@x.com son la misma cuenta
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo. ¿Quieres iniciar sesión?")
        return email


class AccesoForm(AuthenticationForm):
    """
    Inicio de sesión con correo + límite de intentos fallidos.
    Tras 5 fallos seguidos para el mismo correo, se bloquea 15 minutos
    para frenar ataques de fuerza bruta (probar contraseñas sin parar).
    """

    MAX_INTENTOS = 5
    BLOQUEO_SEGUNDOS = 15 * 60

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Correo o contraseña incorrectos.",
        "bloqueado": "Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget.input_type = "email"  # teclado de correo en el móvil
        self.fields["username"].widget.attrs.update(autocomplete="email")

    def _clave(self):
        return f"intentos-acceso:{(self.data.get('username') or '').strip().lower()}"

    def clean(self):
        if cache.get(self._clave(), 0) >= self.MAX_INTENTOS:
            raise forms.ValidationError(self.error_messages["bloqueado"], code="bloqueado")
        try:
            datos = super().clean()
        except forms.ValidationError:
            intentos = cache.get(self._clave(), 0) + 1
            cache.set(self._clave(), intentos, self.BLOQUEO_SEGUNDOS)
            raise
        cache.delete(self._clave())  # acierto: contador a cero
        return datos
