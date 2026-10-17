"""Tests de la página del carrito (CU-03): ver, cambiar cantidades y eliminar."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from carrito.models import Carrito, LineaCarrito
from carrito.services import SESION_CARRITO
from catalogo.models import Categoria, Color, Producto, Talla, Variante


class PaginaCarritoTests(TestCase):
    def setUp(self):
        categoria = Categoria.objects.create(nombre="Camisetas", slug="camisetas")
        color = Color.objects.create(nombre="Negro", codigo_hex="#121214")
        talla = Talla.objects.create(nombre="M")
        self.camiseta = Producto.objects.create(nombre="Camiseta Areté", slug="camiseta-arete", descripcion="-",
                                                precio=Decimal("20.00"), categoria=categoria)
        self.variante = Variante.objects.create(producto=self.camiseta, talla=talla, color=color, sku="C-N-M", stock=5)

        # Carrito de visitante guardado en la sesión del cliente de pruebas
        self.carrito = Carrito.objects.create()
        sesion = self.client.session
        sesion[SESION_CARRITO] = self.carrito.pk
        sesion.save()
        self.linea = LineaCarrito.objects.create(carrito=self.carrito, variante=self.variante, cantidad=2)

    def url(self, nombre):
        return reverse(f"carrito:{nombre}", args=[self.linea.pk])

    def test_muestra_lineas_y_totales_con_envio(self):
        respuesta = self.client.get(reverse("carrito:detalle"))
        self.assertContains(respuesta, "Camiseta Areté")
        self.assertEqual(respuesta.context["subtotal"], Decimal("40.00"))
        self.assertEqual(respuesta.context["envio"], Decimal("4.95"))
        self.assertEqual(respuesta.context["total"], Decimal("44.95"))
        self.assertEqual(respuesta.context["falta_para_envio_gratis"], Decimal("10.00"))

    def test_envio_gratis_desde_50(self):
        self.client.post(self.url("actualizar"), {"cantidad": 3})
        respuesta = self.client.get(reverse("carrito:detalle"))
        self.assertEqual(respuesta.context["envio"], Decimal("0.00"))
        self.assertContains(respuesta, "Tienes envío gratis")

    def test_cambiar_cantidad_con_htmx_devuelve_bloque_y_contador(self):
        respuesta = self.client.post(self.url("actualizar"), {"cantidad": 4}, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, 'id="carrito-contenido"')
        self.assertContains(respuesta, 'id="contador-carrito" hx-swap-oob="true"')
        self.linea.refresh_from_db()
        self.assertEqual(self.linea.cantidad, 4)

    def test_no_permite_superar_el_stock(self):
        respuesta = self.client.post(self.url("actualizar"), {"cantidad": 6}, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, "Solo quedan 5 unidades")
        self.linea.refresh_from_db()
        self.assertEqual(self.linea.cantidad, 2)

    def test_cantidad_no_valida(self):
        respuesta = self.client.post(self.url("actualizar"), {"cantidad": "abc"}, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, "Indica una cantidad válida")

    def test_eliminar_linea(self):
        respuesta = self.client.post(self.url("eliminar"), HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, "Tu carrito está vacío")
        self.assertFalse(LineaCarrito.objects.exists())

    def test_no_se_puede_tocar_el_carrito_de_otra_persona(self):
        # Otro navegador (sin la sesión) intenta cambiar y borrar nuestra línea
        otro = self.client_class()
        self.assertEqual(otro.post(self.url("actualizar"), {"cantidad": 1}).status_code, 404)
        self.assertEqual(otro.post(self.url("eliminar")).status_code, 404)
        self.assertTrue(LineaCarrito.objects.filter(pk=self.linea.pk, cantidad=2).exists())

    def test_sin_javascript_redirige_al_carrito(self):
        respuesta = self.client.post(self.url("actualizar"), {"cantidad": 3})
        self.assertRedirects(respuesta, reverse("carrito:detalle"))

    def test_avisa_si_un_articulo_se_ha_agotado_y_bloquea_el_pago(self):
        Variante.objects.filter(pk=self.variante.pk).update(stock=0)
        respuesta = self.client.get(reverse("carrito:detalle"))
        self.assertContains(respuesta, "Agotado")
        self.assertFalse(respuesta.context["se_puede_pagar"])

    def test_visitar_el_carrito_no_crea_carritos_vacios(self):
        antes = Carrito.objects.count()
        self.client_class().get(reverse("carrito:detalle"))
        self.assertEqual(Carrito.objects.count(), antes)

    def test_solo_acepta_post(self):
        self.assertEqual(self.client.get(self.url("eliminar")).status_code, 405)
