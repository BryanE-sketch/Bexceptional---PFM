from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services import fusionar_carrito_de_visitante


@receiver(user_logged_in)
def al_iniciar_sesion(sender, request, user, **kwargs):
    """Se ejecuta automáticamente cada vez que alguien inicia sesión."""
    if request is not None:
        fusionar_carrito_de_visitante(request, user)