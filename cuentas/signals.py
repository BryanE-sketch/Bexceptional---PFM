from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import RegistroAcceso


def obtener_ip(request):
    """IP del visitante. En producción (Render) llega en la cabecera X-Forwarded-For."""
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def registrar_inicio_de_sesion(sender, request, user, **kwargs):
    """Guarda fecha, IP y navegador cada vez que alguien inicia sesión."""
    if request is None:
        return
    RegistroAcceso.objects.create(
        usuario=user,
        ip=obtener_ip(request),
        dispositivo=request.META.get("HTTP_USER_AGENT", "")[:255],
    )