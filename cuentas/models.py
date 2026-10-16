from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower


class UsuarioManager(BaseUserManager):
    """Crea usuarios y superusuarios usando el correo como identificador."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email).lower()  # siempre en minúsculas
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # guarda el hash, nunca la contraseña en claro
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        """Inicio de sesión sin distinguir mayúsculas: Ana@x.com = ana@x.com."""
        return self.get(email__iexact=email)


class Usuario(AbstractUser):
    """Usuario de Bexceptional: inicia sesión con su correo electrónico."""

    username = None
    email = models.EmailField("correo electrónico", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            # La base de datos impide dos cuentas con el mismo correo,
            # aunque cambien mayúsculas y minúsculas
            models.UniqueConstraint(Lower("email"), name="correo_unico_sin_mayusculas"),
        ]

    def clean(self):
        super().clean()
        self.email = self.email.lower()

    def __str__(self):
        return self.email
    


class Direccion(models.Model):
    """Direcciones de envío guardadas por el cliente para no reescribirlas en cada compra."""

    usuario = models.ForeignKey(
        Usuario, verbose_name="usuario", on_delete=models.CASCADE, related_name="direcciones"
    )
    nombre_destinatario = models.CharField("destinatario", max_length=120)
    direccion = models.CharField("dirección", max_length=200)
    ciudad = models.CharField("ciudad", max_length=80)
    codigo_postal = models.CharField(
        "código postal",
        max_length=5,
        validators=[RegexValidator(r"^\d{5}$", "El código postal debe tener 5 cifras.")],
    )
    provincia = models.CharField("provincia", max_length=80)
    telefono = models.CharField(
        "teléfono",
        max_length=20,
        validators=[RegexValidator(r"^\+?[\d\s]{9,15}$", "Introduce un teléfono válido.")],
    )
    predeterminada = models.BooleanField("predeterminada", default=False)

    class Meta:
        verbose_name = "dirección"
        verbose_name_plural = "direcciones"
        constraints = [
            # Cada usuario puede tener como mucho UNA dirección predeterminada
            models.UniqueConstraint(
                fields=["usuario"],
                condition=models.Q(predeterminada=True),
                name="una_direccion_predeterminada",
            ),
        ]

    def __str__(self):
        return f"{self.nombre_destinatario}, {self.direccion} ({self.ciudad})"

    def datos_envio(self):
        """Devuelve los datos en el formato que espera pedidos.services.crear_pedido."""
        return {
            "nombre_destinatario": self.nombre_destinatario,
            "direccion": self.direccion,
            "ciudad": self.ciudad,
            "codigo_postal": self.codigo_postal,
            "provincia": self.provincia,
            "telefono": self.telefono,
        }


class RegistroAcceso(models.Model):
    """Historial de inicios de sesión. Se borra automáticamente a los 90 días (RGPD)."""

    usuario = models.ForeignKey(
        Usuario, verbose_name="usuario", on_delete=models.CASCADE, related_name="accesos"
    )
    fecha = models.DateTimeField("fecha", auto_now_add=True, db_index=True)
    ip = models.GenericIPAddressField("dirección IP", null=True, blank=True)
    dispositivo = models.CharField("dispositivo / navegador", max_length=255, blank=True)

    class Meta:
        verbose_name = "inicio de sesión"
        verbose_name_plural = "historial de inicios de sesión"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario} · {self.fecha:%d/%m/%Y %H:%M}"