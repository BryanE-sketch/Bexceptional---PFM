from django.test import SimpleTestCase
from django.urls import reverse


class SaludTests(SimpleTestCase):
    """SimpleTestCase falla si se consulta la base de datos: así comprobamos que la vista no lo hace."""

    def test_responde_ok_sin_consultar_la_base_de_datos(self):
        respuesta = self.client.get(reverse("salud"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.content, b"ok")

    def test_solo_acepta_get(self):
        respuesta = self.client.post(reverse("salud"))

        self.assertEqual(respuesta.status_code, 405)