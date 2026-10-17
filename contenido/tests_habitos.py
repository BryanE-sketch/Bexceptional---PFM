"""Tests de la sección Hábitos: portada, disciplinas, artículos, descargas y contenido de demostración."""
import tempfile
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from catalogo.models import Disciplina
from contenido.models import Articulo, Consejo, Recurso


# Los archivos que se suben en los tests van a una carpeta temporal, no a tu carpeta media/
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class HabitosTests(TestCase):
    def setUp(self):
        call_command("cargar_habitos_demo", stdout=StringIO())

    def test_carga_las_4_disciplinas_con_3_consejos_y_su_articulo(self):
        for slug in ["levantar-pesas", "correr", "alimentacion-balanceada", "descanso-activo"]:
            disciplina = Disciplina.objects.get(slug=slug)
            self.assertEqual(disciplina.consejos.count(), 3)
            self.assertEqual(disciplina.articulos.count(), 1)
        # Todos los consejos y artículos citan su fuente
        self.assertFalse(Consejo.objects.filter(fuente_url="").exists())
        self.assertFalse(Articulo.objects.filter(fuentes__isnull=True).exists())

    def test_el_comando_no_duplica_si_se_ejecuta_dos_veces(self):
        antes = (Consejo.objects.count(), Articulo.objects.count())
        call_command("cargar_habitos_demo", stdout=StringIO())
        self.assertEqual((Consejo.objects.count(), Articulo.objects.count()), antes)

    def test_portada_de_habitos_enlaza_a_cada_disciplina(self):
        respuesta = self.client.get(reverse("contenido:habitos"))
        for slug in ["levantar-pesas", "correr", "alimentacion-balanceada", "descanso-activo"]:
            self.assertContains(respuesta, reverse("contenido:disciplina", args=[slug]))

    def test_pagina_de_disciplina_con_consejos_fuentes_y_articulo(self):
        respuesta = self.client.get(reverse("contenido:disciplina", args=["correr"]))
        self.assertContains(respuesta, "La mayoría de tus kilómetros, suaves")
        self.assertContains(respuesta, "https://pubmed.ncbi.nlm.nih.gov/20861519/")
        self.assertContains(respuesta, reverse("contenido:articulo", args=["correr-mas-lesionarte-menos"]))

    def test_articulo_muestra_sus_fuentes(self):
        respuesta = self.client.get(reverse("contenido:articulo", args=["comer-para-rendir"]))
        self.assertContains(respuesta, "Fuentes y para saber más")
        self.assertContains(respuesta, "https://www.who.int/news-room/fact-sheets/detail/healthy-diet")

    def test_los_borradores_no_se_ven(self):
        Articulo.objects.filter(slug="comer-para-rendir").update(estado=Articulo.Estado.BORRADOR)
        respuesta = self.client.get(reverse("contenido:articulo", args=["comer-para-rendir"]))
        self.assertEqual(respuesta.status_code, 404)

    def test_disciplina_desactivada_da_404(self):
        Disciplina.objects.filter(slug="correr").update(activa=False)
        self.assertEqual(self.client.get(reverse("contenido:disciplina", args=["correr"])).status_code, 404)

    def test_la_portada_de_la_tienda_enlaza_las_disciplinas_a_habitos(self):
        respuesta = self.client.get(reverse("catalogo:inicio"))
        self.assertContains(respuesta, reverse("contenido:disciplina", args=["levantar-pesas"]))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DescargasTests(TestCase):
    def test_descargar_cuenta_y_redirige_al_pdf(self):
        recurso = Recurso.objects.create(
            titulo="Rastreador", slug="rastreador", descripcion="-",
            archivo=SimpleUploadedFile("rastreador.pdf", b"%PDF-1.4 prueba", content_type="application/pdf"),
        )
        respuesta = self.client.post(reverse("contenido:descargar", args=["rastreador"]))
        self.assertRedirects(respuesta, recurso.archivo.url, fetch_redirect_response=False)
        recurso.refresh_from_db()
        self.assertEqual(recurso.descargas, 1)

    def test_descargar_con_get_no_cuenta(self):
        self.assertEqual(self.client.get(reverse("contenido:descargar", args=["x"])).status_code, 405)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FotoDisciplinaTests(TestCase):
    """La foto de cada disciplina se toma de demo/disciplinas/<slug>.webp si existe."""

    def test_usa_la_foto_de_demo_y_no_pisa_una_existente(self):
        from pathlib import Path

        from contenido.management.commands.cargar_habitos_demo import Command

        base = Path(tempfile.mkdtemp())
        (base / "demo" / "disciplinas").mkdir(parents=True)
        (base / "demo" / "disciplinas" / "correr.webp").write_bytes(b"foto")
        correr = Disciplina.objects.create(nombre="Correr", slug="correr")
        pesas = Disciplina.objects.create(nombre="Levantar pesas", slug="levantar-pesas")
        comando = Command(stdout=StringIO())

        with override_settings(BASE_DIR=base):
            comando.foto_disciplina(correr)
            comando.foto_disciplina(pesas)          # no tiene archivo: se queda sin foto (fénix)
        self.assertTrue(correr.imagen.name.startswith("disciplinas/correr"))
        self.assertFalse(pesas.imagen)

        # Una foto subida desde el panel no se reemplaza
        nombre = correr.imagen.name
        with override_settings(BASE_DIR=base):
            comando.foto_disciplina(correr)
        self.assertEqual(correr.imagen.name, nombre)
