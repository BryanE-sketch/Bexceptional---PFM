from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from carrito.models import LineaCarrito
from catalogo.models import Categoria, Color, Producto, Talla, Variante


class AnadirAlCarritoVistaTests(TestCase):
    """CU-02 desde la web: el formulario de la ficha de producto."""

    def setUp(self):
        producto = Producto.objects.create(
            nombre="Camiseta Areté", slug="camiseta-arete", descripcion="-", precio=Decimal("29.90"),
            categoria=Categoria.objects.create(nombre="Camisetas", slug="camisetas"),
        )
        self.variante = Variante.objects.create(
            producto=producto, talla=Talla.objects.create(nombre="M"),
            color=Color.objects.create(nombre="Negro", codigo_hex="#121214"), sku="N-M", stock=2,
        )
        self.url = reverse("carrito:anadir")

    def test_con_htmx_anade_y_actualiza_el_contador(self):
        respuesta = self.client.post(self.url, {"variante": self.variante.pk, "cantidad": 2}, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, "Añadido al carrito")
        self.assertContains(respuesta, 'hx-swap-oob="true"')
        self.assertEqual(LineaCarrito.objects.get().cantidad, 2)

    def test_no_permite_superar_el_stock(self):
        respuesta = self.client.post(self.url, {"variante": self.variante.pk, "cantidad": 3}, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, "Solo quedan 2 unidades")
        self.assertFalse(LineaCarrito.objects.exists())

    def test_sin_talla_muestra_un_error(self):
        respuesta = self.client.post(self.url, {"cantidad": 1}, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, "Elige una talla")

    def test_sin_javascript_redirige_a_una_pagina_de_la_tienda(self):
        respuesta = self.client.post(
            self.url, {"variante": self.variante.pk, "cantidad": 1}, HTTP_REFERER="https://web-maliciosa.com/"
        )
        self.assertRedirects(respuesta, reverse("catalogo:inicio"), fetch_redirect_response=False)

    def test_no_acepta_peticiones_get(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)