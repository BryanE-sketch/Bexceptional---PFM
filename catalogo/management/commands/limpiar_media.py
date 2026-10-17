"""
Busca archivos de media/ que ya no usa ningún registro de la base de datos (huérfanos).

    python manage.py limpiar_media            # solo los lista (no borra nada)
    python manage.py limpiar_media --borrar   # los borra

Aparecen, por ejemplo, al borrar un producto desde el panel (Django no borra su foto)
o al volver a cargar los datos de demostración.
"""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand
from django.db.models import FileField


class Command(BaseCommand):
    help = "Lista (o borra con --borrar) los archivos de media/ que no usa ningún registro."

    def add_arguments(self, parser):
        parser.add_argument("--borrar", action="store_true", help="Borra los archivos huérfanos.")

    def handle(self, *args, **opciones):
        # En producción los archivos están en Cloudinary, no en disco: este comando no aplica
        if not isinstance(default_storage, FileSystemStorage):
            self.stdout.write("Los archivos no están en disco (Cloudinary): este comando solo sirve en local.")
            return
        raiz = Path(settings.MEDIA_ROOT)
        if not raiz.is_dir():
            self.stdout.write("No hay carpeta media/.")
            return

        # 1) Todos los archivos que SÍ usa la base de datos (cualquier FileField o ImageField de cualquier modelo)
        en_uso = set()
        for modelo in apps.get_models():
            campos = [c.name for c in modelo._meta.get_fields() if isinstance(c, FileField)]
            for campo in campos:
                en_uso.update(n for n in modelo.objects.values_list(campo, flat=True) if n)

        # 2) Los que hay en disco y no están en esa lista
        huerfanos = [r for r in raiz.rglob("*") if r.is_file() and r.relative_to(raiz).as_posix() not in en_uso]
        tamano = sum(r.stat().st_size for r in huerfanos) / 1_048_576

        for ruta in huerfanos[:20]:
            self.stdout.write(f"  {ruta.relative_to(raiz)}")
        if len(huerfanos) > 20:
            self.stdout.write(f"  … y {len(huerfanos) - 20} más")

        if not opciones["borrar"]:
            self.stdout.write(self.style.WARNING(
                f"{len(huerfanos)} archivos huérfanos ({tamano:.1f} MB). Ejecuta con --borrar para eliminarlos."))
            return
        for ruta in huerfanos:
            ruta.unlink()
        self.stdout.write(self.style.SUCCESS(f"Borrados {len(huerfanos)} archivos ({tamano:.1f} MB)."))
