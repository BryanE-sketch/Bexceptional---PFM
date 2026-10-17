"""Tests del proceso de compra en la web (CU-04): checkout, pago simulado y detalle del pedido."""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from carrito.models import Carrito, LineaCarrito
from catalogo.models import Categoria, Color, Producto, Talla, Variante
from cuentas.models import Direccion, Usuario
from pedidos.forms import luhn_valido
from pedidos.models import Pedido

ANIO_FUTURO = str(date.today().year + 2)[-2:]


class CheckoutTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(email="laura@ejemplo.com", password="Fenix-2026-segura",
                                                   first_name="Laura")
        self.client.force_login(self.usuario)
        producto = Producto.objects.create(nombre="Camiseta Areté", slug="camiseta-arete", descripcion="-",
                                           precio=Decimal("29.95"),
                                           categoria=Categoria.objects.create(nombre="Camisetas", slug="camisetas"))
        self.variante = Variante.objects.create(producto=producto, talla=Talla.objects.create(nombre="M"),
                                                color=Color.objects.create(nombre="Negro", codigo_hex="#121214"),
                                                sku="C-N-M", stock=3)
        carrito = Carrito.objects.create(usuario=self.usuario)
        LineaCarrito.objects.create(carrito=carrito, variante=self.variante, cantidad=1)
        self.url = reverse("pedidos:checkout")

    def datos(self, **cambios):
        return {
            "nombre_destinatario": "Laura Gómez", "direccion": "Calle Mayor 1", "codigo_postal": "28013",
            "ciudad": "Madrid", "provincia": "Madrid", "telefono": "600 123 456",
            "metodo": "tarjeta", "titular": "Laura Gómez", "numero_tarjeta": "4242 4242 4242 4242",
            "caducidad": f"12/{ANIO_FUTURO}", "cvc": "123", **cambios,
        }

    def test_exige_iniciar_sesion(self):
        self.client.logout()
        respuesta = self.client.get(self.url)
        self.assertRedirects(respuesta, f"{reverse('cuentas:entrar')}?next={self.url}")

    def test_compra_completa_con_tarjeta(self):
        respuesta = self.client.post(self.url, self.datos())
        pedido = Pedido.objects.get()
        self.assertRedirects(respuesta, reverse("pedidos:detalle", args=[pedido.numero]),
                             fetch_redirect_response=False)  # sin visitarla aún
        self.assertEqual(pedido.total, Decimal("34.90"))  # 29,95 + 4,95 de envío
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 2)
        # La página de confirmación muestra el agradecimiento solo la primera vez
        self.assertContains(self.client.get(respuesta.url), "Pedido confirmado")
        self.assertNotContains(self.client.get(respuesta.url), "Pedido confirmado")

    def test_tarjeta_rechazada_no_crea_pedido_ni_toca_stock(self):
        respuesta = self.client.post(self.url, self.datos(numero_tarjeta="4000 0000 0000 0002"))
        self.assertContains(respuesta, "El banco ha rechazado el pago")
        self.assertFalse(Pedido.objects.exists())
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 3)

    def test_valida_los_datos_de_la_tarjeta(self):
        respuesta = self.client.post(self.url, self.datos(numero_tarjeta="1234 5678 9012 3456",
                                                          caducidad="01/20", cvc="1"))
        self.assertContains(respuesta, "El número de tarjeta no es válido")
        self.assertContains(respuesta, "La tarjeta está caducada")
        self.assertContains(respuesta, "El CVC son 3 o 4 cifras")
        self.assertFalse(Pedido.objects.exists())

    def test_paypal_no_pide_datos_de_tarjeta(self):
        self.client.post(self.url, self.datos(metodo="paypal", numero_tarjeta="", titular="", caducidad="", cvc=""))
        self.assertEqual(Pedido.objects.get().pago.metodo, "paypal")

    def test_valida_la_direccion(self):
        respuesta = self.client.post(self.url, self.datos(codigo_postal="280", telefono="abc"))
        self.assertContains(respuesta, "El código postal debe tener 5 cifras")
        self.assertContains(respuesta, "Introduce un teléfono válido")

    def test_guardar_direccion_y_reutilizarla(self):
        self.client.post(self.url, self.datos(guardar_direccion="on"))
        self.assertTrue(Direccion.objects.get(usuario=self.usuario).predeterminada)
        # En la siguiente compra el formulario aparece relleno
        carrito = Carrito.objects.get(usuario=self.usuario)
        LineaCarrito.objects.create(carrito=carrito, variante=self.variante, cantidad=1)
        self.assertContains(self.client.get(self.url), 'value="Calle Mayor 1"')

    def test_carrito_vacio_vuelve_al_carrito(self):
        LineaCarrito.objects.all().delete()
        self.assertRedirects(self.client.get(self.url), reverse("carrito:detalle"))

    def test_nadie_puede_ver_el_pedido_de_otra_persona(self):
        self.client.post(self.url, self.datos())
        pedido = Pedido.objects.get()
        otro = Usuario.objects.create_user(email="otro@ejemplo.com", password="Fenix-2026-segura")
        self.client.force_login(otro)
        self.assertEqual(self.client.get(reverse("pedidos:detalle", args=[pedido.numero])).status_code, 404)

    def test_algoritmo_de_luhn(self):
        self.assertTrue(luhn_valido("4242424242424242"))
        self.assertTrue(luhn_valido("4000000000000002"))
        self.assertFalse(luhn_valido("4242424242424241"))
