from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from contenido.models import Articulo, Recurso


class ContenidoTests(TestCase):
    def crear(self, titulo, **extra):
        return Articulo.objects.create(titulo=titulo, slug=titulo.lower(), resumen="-", cuerpo="-", **extra)

    def test_solo_se_muestran_los_articulos_publicados(self):
        publicado = self.crear("Sueno", estado=Articulo.Estado.PUBLICADO)
        self.crear("Borrador")
        self.crear("Programado", estado=Articulo.Estado.PUBLICADO,
                   publicado_en=timezone.now() + timedelta(days=3))
        self.assertEqual(list(Articulo.objects.publicados()), [publicado])

    def test_al_publicar_se_guarda_la_fecha_automaticamente(self):
        articulo = self.crear("Hidratacion", estado=Articulo.Estado.PUBLICADO)
        self.assertIsNotNone(articulo.publicado_en)

    def test_un_recurso_solo_admite_pdf(self):
        recurso = Recurso(titulo="Malicioso", slug="malicioso", descripcion="-",
                          archivo=SimpleUploadedFile("virus.exe", b"x"))
        with self.assertRaises(ValidationError):
            recurso.full_clean()