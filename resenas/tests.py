from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from carrito.models import Carrito
from carrito.services import anadir_al_carrito
from catalogo.models import Categoria, Color, Producto, Talla, Variante
from pedidos import services as pedidos
from pedidos.models import Pago, Pedido
from resenas.models import Resena
from resenas.services import puede_resenar, resumen_valoraciones

ENVIO = dict(nombre_destinatario="Juan", direccion="C/ Sol 1", ciudad="Madrid",
             codigo_postal="28001", provincia="Madrid", telefono="600000000")


class ResenasTests(TestCase):
    def setUp(self):
        self.juan = get_user_model().objects.create_user("juan@test.com", "ClaveSegura123!")
        self.producto = Producto.objects.create(
            nombre="Shorts Ascenso", slug="shorts-ascenso", descripcion="-", precio=Decimal("24.90"),
            categoria=Categoria.objects.create(nombre="Shorts", slug="shorts"),
        )
        variante = Variante.objects.create(
            producto=self.producto, talla=Talla.objects.create(nombre="L"),
            color=Color.objects.create(nombre="Negro", codigo_hex="#121214"), sku="BX-ASC-NEG-L", stock=5,
        )
        carrito = Carrito.objects.create(usuario=self.juan)
        anadir_al_carrito(carrito, variante, 1)
        self.pedido = pedidos.crear_pedido(self.juan, carrito, ENVIO, Pago.Metodo.PAYPAL)

    def nueva(self, usuario, puntuacion=5):
        return Resena(usuario=usuario, producto=self.producto, puntuacion=puntuacion, titulo="-", texto="-")

    def test_no_puede_resenar_si_el_pedido_aun_no_se_ha_entregado(self):
        self.assertFalse(puede_resenar(self.juan, self.producto))
        with self.assertRaises(ValidationError):
            self.nueva(self.juan).full_clean()

    def test_puede_resenar_cuando_lo_ha_recibido(self):
        Pedido.objects.filter(pk=self.pedido.pk).update(estado=Pedido.Estado.ENTREGADO)
        self.nueva(self.juan).full_clean()  # no lanza error

    def test_quien_no_lo_compro_no_puede_resenar(self):
        ana = get_user_model().objects.create_user("ana@test.com", "ClaveSegura123!")
        self.assertFalse(puede_resenar(ana, self.producto))

    def test_puntuacion_fuera_de_rango_bloqueada_por_la_base_de_datos(self):
        with self.assertRaises(IntegrityError):
            self.nueva(self.juan, puntuacion=6).save()

    def test_la_media_solo_cuenta_resenas_aprobadas(self):
        ana = get_user_model().objects.create_user("ana@test.com", "ClaveSegura123!")
        Resena.objects.create(usuario=self.juan, producto=self.producto, puntuacion=4, titulo="-", texto="-", aprobada=True)
        Resena.objects.create(usuario=ana, producto=self.producto, puntuacion=1, titulo="-", texto="-", aprobada=False)
        self.assertEqual(resumen_valoraciones(self.producto), {"media": 4.0, "total": 1})