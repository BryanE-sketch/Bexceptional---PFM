from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from carrito.models import Carrito
from carrito.services import StockInsuficienteError as StockCarritoError
from carrito.services import anadir_al_carrito, fusionar_carrito_de_visitante
from catalogo.models import Categoria, Color, Producto, Talla, Variante
from pedidos import services
from pedidos.models import Pago, Pedido

DATOS_ENVIO = {
    "nombre_destinatario": "Laura Pérez",
    "direccion": "Calle Mayor 1",
    "ciudad": "Madrid",
    "codigo_postal": "28001",
    "provincia": "Madrid",
    "telefono": "600000000",
}


class CompraTests(TestCase):
    """Casos de uso CU-02, CU-03, CU-04 y CU-07."""

    def setUp(self):
        self.cliente = get_user_model().objects.create_user("laura@test.com", "ClaveSegura123!")
        categoria = Categoria.objects.create(nombre="Camisetas", slug="camisetas")
        self.producto = Producto.objects.create(
            nombre="Camiseta Areté", slug="camiseta-arete", descripcion="-",
            precio=Decimal("29.90"), categoria=categoria,
        )
        self.variante = Variante.objects.create(
            producto=self.producto,
            talla=Talla.objects.create(nombre="M", orden=3),
            color=Color.objects.create(nombre="Negro", codigo_hex="#121214"),
            sku="BX-ARE-NEG-M",
            stock=3,
        )
        self.carrito = Carrito.objects.create(usuario=self.cliente)

    # CU-02 · Añadir al carrito
    def test_no_se_puede_anadir_mas_que_el_stock(self):
        with self.assertRaises(StockCarritoError):
            anadir_al_carrito(self.carrito, self.variante, cantidad=4)

    def test_anadir_dos_veces_suma_cantidades(self):
        anadir_al_carrito(self.carrito, self.variante, 1)
        anadir_al_carrito(self.carrito, self.variante, 2)
        self.assertEqual(self.carrito.lineas.get().cantidad, 3)

    # CU-03 · Al iniciar sesión, el carrito del visitante pasa a la cuenta
    def test_carrito_de_visitante_se_fusiona_al_iniciar_sesion(self):
        visitante = Carrito.objects.create()
        anadir_al_carrito(visitante, self.variante, 2)
        request = RequestFactory().get("/")
        request.session = {"carrito_id": visitante.pk}
        fusionar_carrito_de_visitante(request, self.cliente)
        self.assertEqual(self.carrito.lineas.get().cantidad, 2)
        self.assertFalse(Carrito.objects.filter(pk=visitante.pk).exists())

    # CU-04 · Comprar
    def test_compra_crea_pedido_descuenta_stock_y_vacia_carrito(self):
        anadir_al_carrito(self.carrito, self.variante, 2)
        pedido = services.crear_pedido(self.cliente, self.carrito, DATOS_ENVIO, Pago.Metodo.PAYPAL)

        self.variante.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.PAGADO)
        self.assertEqual(self.variante.stock, 1)
        self.assertEqual(pedido.subtotal, Decimal("59.80"))
        self.assertEqual(pedido.gastos_envio, Decimal("0.00"))  # envío gratis desde 50 €
        self.assertEqual(pedido.lineas.get().precio_unitario, Decimal("29.90"))
        self.assertFalse(self.carrito.lineas.exists())

    def test_pago_rechazado_no_crea_pedido_ni_toca_el_stock(self):
        anadir_al_carrito(self.carrito, self.variante, 1)
        with self.assertRaises(services.PagoRechazadoError):
            services.crear_pedido(
                self.cliente, self.carrito, DATOS_ENVIO, Pago.Metodo.TARJETA,
                numero_tarjeta=services.TARJETA_RECHAZADA,
            )
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 3)
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertTrue(self.carrito.lineas.exists())  # el carrito se conserva

    def test_si_otro_cliente_compro_antes_no_se_vende_sin_stock(self):
        anadir_al_carrito(self.carrito, self.variante, 3)
        Variante.objects.filter(pk=self.variante.pk).update(stock=1)  # otro cliente compró 2
        with self.assertRaises(services.StockInsuficienteError):
            services.crear_pedido(self.cliente, self.carrito, DATOS_ENVIO, Pago.Metodo.PAYPAL)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_el_precio_del_pedido_no_cambia_si_cambia_el_producto(self):
        anadir_al_carrito(self.carrito, self.variante, 1)
        pedido = services.crear_pedido(self.cliente, self.carrito, DATOS_ENVIO, Pago.Metodo.APPLE_PAY)
        Producto.objects.filter(pk=self.producto.pk).update(precio=Decimal("99.00"))
        self.assertEqual(pedido.lineas.get().precio_unitario, Decimal("29.90"))
        self.assertEqual(pedido.gastos_envio, Decimal("4.95"))  # por debajo de 50 €

    # CU-07 · Cancelar repone el stock
    def test_cancelar_pedido_repone_el_stock(self):
        anadir_al_carrito(self.carrito, self.variante, 2)
        pedido = services.crear_pedido(self.cliente, self.carrito, DATOS_ENVIO, Pago.Metodo.PAYPAL)
        services.cancelar_pedido(pedido)
        services.cancelar_pedido(pedido)  # cancelar dos veces no repone dos veces
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 3)
        self.assertEqual(pedido.estado, Pedido.Estado.CANCELADO)