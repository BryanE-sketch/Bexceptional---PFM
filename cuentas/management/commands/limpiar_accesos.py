from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cuentas.models import RegistroAcceso

DIAS_CONSERVACION = 90


class Command(BaseCommand):
    help = f"Borra los inicios de sesión con más de {DIAS_CONSERVACION} días (protección de datos)."

    def handle(self, *args, **options):
        limite = timezone.now() - timedelta(days=DIAS_CONSERVACION)
        borrados, _ = RegistroAcceso.objects.filter(fecha__lt=limite).delete()
        self.stdout.write(self.style.SUCCESS(f"Registros de acceso borrados: {borrados}"))