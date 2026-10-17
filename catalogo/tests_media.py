"""Test del comando limpiar_media: borra lo que nadie usa y respeta lo que sí."""
import tempfile
from io import StringIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from catalogo.models import Categoria

MEDIA_TEMPORAL = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class LimpiarMediaTests(TestCase):
    def test_borra_huerfanos_y_conserva_los_usados(self):
        categoria = Categoria.objects.create(
            nombre="Gorras", slug="gorras", imagen=SimpleUploadedFile("gorras.webp", b"img", content_type="image/webp"))
        huerfano = Path(MEDIA_TEMPORAL) / "productos" / "viejo.webp"
        huerfano.parent.mkdir(parents=True, exist_ok=True)
        huerfano.write_bytes(b"img")

        call_command("limpiar_media", stdout=StringIO())        # sin --borrar: solo lista
        self.assertTrue(huerfano.exists())

        call_command("limpiar_media", "--borrar", stdout=StringIO())
        self.assertFalse(huerfano.exists())
        self.assertTrue((Path(MEDIA_TEMPORAL) / categoria.imagen.name).exists())
