"""Tests de la página de la tienda (la parte de Django que monta React)."""
from django.test import TestCase
from django.urls import reverse


class PaginaTiendaTests(TestCase):
    def test_la_tienda_carga_y_pasa_las_urls_de_la_api_a_react(self):
        respuesta = self.client.get(reverse("catalogo:tienda"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'id="tienda"')
        self.assertContains(respuesta, f'data-url-productos="{reverse("api:producto-list")}"')
        self.assertContains(respuesta, f'data-url-filtros="{reverse("api:filtros")}"')

    def test_incluye_el_script_de_react(self):
        respuesta = self.client.get(reverse("catalogo:tienda"))
        self.assertContains(respuesta, 'type="module"')

    def test_sin_javascript_hay_un_mensaje_alternativo(self):
        respuesta = self.client.get(reverse("catalogo:tienda"))
        self.assertContains(respuesta, "<noscript>")
