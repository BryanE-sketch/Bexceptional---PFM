from django.core.exceptions import ValidationError
from django.test import TestCase

from catalogo.models import Categoria


class CategoriaTests(TestCase):
    def setUp(self):
        self.ropa = Categoria.objects.create(nombre="Ropa", slug="ropa")
        self.camisetas = Categoria.objects.create(nombre="Camisetas", slug="camisetas", padre=self.ropa)

    def test_el_nombre_muestra_la_ruta(self):
        self.assertEqual(str(self.camisetas), "Ropa › Camisetas")

    def test_una_categoria_no_puede_ser_su_propio_padre(self):
        self.ropa.padre = self.ropa
        with self.assertRaises(ValidationError):
            self.ropa.full_clean()

    def test_no_se_permiten_bucles_entre_categorias(self):
        self.ropa.padre = self.camisetas  # Ropa -> Camisetas -> Ropa
        with self.assertRaises(ValidationError):
            self.ropa.full_clean()

    def test_un_bucle_ya_guardado_no_rompe_el_nombre(self):
        Categoria.objects.filter(pk=self.ropa.pk).update(padre=self.camisetas)
        self.ropa.refresh_from_db()
        self.assertEqual(str(self.ropa), "Camisetas › Ropa")  # sin RecursionError


class FichaProductoTests(TestCase):
    def setUp(self):
        from decimal import Decimal

        from catalogo.models import Color, Producto, Talla, Variante

        categoria = Categoria.objects.create(nombre="Camisetas", slug="camisetas")
        self.producto = Producto.objects.create(
            nombre="Camiseta Areté", slug="camiseta-arete", descripcion="Tejido técnico.",
            precio=Decimal("29.90"), categoria=categoria,
        )
        negro = Color.objects.create(nombre="Negro", codigo_hex="#121214")
        self.blanco = Color.objects.create(nombre="Blanco", codigo_hex="#F2EDE4")
        Variante.objects.create(producto=self.producto, talla=Talla.objects.create(nombre="M", orden=3),
                                color=negro, sku="N-M", stock=5)
        Variante.objects.create(producto=self.producto, talla=Talla.objects.create(nombre="L", orden=4),
                                color=self.blanco, sku="B-L", stock=0)

    def test_la_ficha_muestra_el_producto(self):
        respuesta = self.client.get(self.producto.get_absolute_url())
        self.assertContains(respuesta, "Camiseta Areté")
        self.assertContains(respuesta, "29,90")

    def test_un_producto_desactivado_devuelve_404(self):
        self.producto.activo = False
        self.producto.save()
        self.assertEqual(self.client.get(self.producto.get_absolute_url()).status_code, 404)

    def test_una_talla_agotada_aparece_deshabilitada(self):
        respuesta = self.client.get(f"{self.producto.get_absolute_url()}?color={self.blanco.pk}")
        self.assertContains(respuesta, "(agotada)")


class CargarCatalogoDemoTests(TestCase):
    """El comando de datos de demostración debe ser fiable: se ejecuta en cada despliegue nuevo."""

    def setUp(self):
        from io import StringIO
        from django.core.management import call_command
        from catalogo.models import Color
        self.call_command, self.StringIO = call_command, StringIO
        Categoria.objects.create(nombre="Accesorios", slug="accesorios")
        Color.objects.create(nombre="Magenta", codigo_hex="#C2185B")

    def cargar(self, *args):
        self.call_command("cargar_catalogo_demo", *args, stdout=self.StringIO())

    def test_crea_15_productos_con_tres_colores(self):
        from catalogo.models import Producto, Variante
        self.cargar()
        self.assertEqual(Producto.objects.count(), 15)
        colores = set(Variante.objects.values_list("color__nombre", flat=True))
        self.assertEqual(colores, {"Negro", "Blanco", "Gris"})

    def test_una_variante_agotada_por_categoria_y_el_resto_con_mas_de_10(self):
        from catalogo.models import Variante
        self.cargar()
        for slug in ["camisetas", "rinoneras", "calcetines", "gorras", "agarraderas"]:
            variantes = Variante.objects.filter(producto__categoria__slug=slug)
            self.assertEqual(variantes.filter(stock=0).count(), 1, slug)
            self.assertFalse(variantes.filter(stock__gt=0, stock__lte=10).exists(), slug)

    def test_se_puede_ejecutar_dos_veces_sin_duplicar(self):
        from catalogo.models import ImagenProducto, Variante
        self.cargar()
        antes = (Variante.objects.count(), ImagenProducto.objects.count())
        self.cargar()
        self.assertEqual((Variante.objects.count(), ImagenProducto.objects.count()), antes)
        self.assertEqual(antes[1], 45)

    def test_retirar_color_borra_el_magenta(self):
        from catalogo.models import Color
        self.cargar("--retirar-color", "Magenta")
        self.assertFalse(Color.objects.filter(nombre="Magenta").exists())
