"""Tests de la API del catálogo."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Color, Disciplina, Producto, Talla, Variante


class ApiCatalogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ropa = Categoria.objects.create(nombre="Ropa", slug="ropa")
        camisetas = Categoria.objects.create(nombre="Camisetas", slug="camisetas", padre=ropa)
        accesorios = Categoria.objects.create(nombre="Accesorios", slug="accesorios")
        gorras = Categoria.objects.create(nombre="Gorras", slug="gorras", padre=accesorios)
        cls.negro = Color.objects.create(nombre="Negro", codigo_hex="#121214")
        cls.blanco = Color.objects.create(nombre="Blanco", codigo_hex="#FFFFFF")
        cls.m = Talla.objects.create(nombre="M", orden=3)
        cls.unica = Talla.objects.create(nombre="Única", orden=20)
        running = Disciplina.objects.create(nombre="Correr", slug="running")

        def producto(nombre, categoria, precio, publico="unisex", activo=True):
            return Producto.objects.create(nombre=nombre, slug=nombre.lower().replace(" ", "-"),
                                           descripcion=f"Descripción de {nombre}", precio=Decimal(precio),
                                           categoria=categoria, publico=publico, activo=activo)

        cls.camiseta = producto("Camiseta Unisex", camisetas, "30")
        cls.top = producto("Top Mujer", camisetas, "25", publico="mujer")
        cls.gorra = producto("Gorra Running", gorras, "20")
        cls.oculto = producto("Producto Oculto", gorras, "10", activo=False)
        cls.gorra.disciplinas.add(running)

        # Camiseta: M negra agotada, M blanca con stock
        Variante.objects.create(producto=cls.camiseta, talla=cls.m, color=cls.negro, sku="C-N-M", stock=0)
        Variante.objects.create(producto=cls.camiseta, talla=cls.m, color=cls.blanco, sku="C-B-M", stock=12)
        Variante.objects.create(producto=cls.top, talla=cls.m, color=cls.negro, sku="T-N-M", stock=15)
        Variante.objects.create(producto=cls.gorra, talla=cls.unica, color=cls.negro, sku="G-N-U", stock=0)

    def listar(self, **params):
        respuesta = self.client.get(reverse("api:producto-list"), params)
        self.assertEqual(respuesta.status_code, 200)
        return {p["nombre"] for p in respuesta.json()["results"]}

    def test_solo_muestra_productos_activos(self):
        self.assertEqual(self.listar(), {"Camiseta Unisex", "Top Mujer", "Gorra Running"})

    def test_unisex_aparece_en_mujer_y_en_hombre(self):
        self.assertEqual(self.listar(publico="mujer"), {"Camiseta Unisex", "Top Mujer", "Gorra Running"})
        self.assertEqual(self.listar(publico="hombre"), {"Camiseta Unisex", "Gorra Running"})

    def test_la_categoria_padre_incluye_sus_subcategorias(self):
        self.assertEqual(self.listar(categoria="accesorios"), {"Gorra Running"})
        self.assertEqual(self.listar(categoria="ropa"), {"Camiseta Unisex", "Top Mujer"})

    def test_color_talla_y_stock_se_cumplen_en_la_misma_variante(self):
        # La camiseta tiene M en negro, pero agotada: no debe salir
        self.assertEqual(self.listar(color=self.negro.pk, talla=self.m.pk, en_stock="true"), {"Top Mujer"})
        self.assertEqual(self.listar(color=f"{self.negro.pk},{self.blanco.pk}", talla=self.m.pk, en_stock="true"),
                         {"Camiseta Unisex", "Top Mujer"})

    def test_busqueda_disciplina_y_precio(self):
        self.assertEqual(self.listar(q="gorra"), {"Gorra Running"})
        self.assertEqual(self.listar(disciplina="running"), {"Gorra Running"})
        self.assertEqual(self.listar(precio_min=21, precio_max=29), {"Top Mujer"})

    def test_orden_por_precio(self):
        respuesta = self.client.get(reverse("api:producto-list"), {"orden": "-precio"})
        self.assertEqual([p["nombre"] for p in respuesta.json()["results"]],
                         ["Camiseta Unisex", "Top Mujer", "Gorra Running"])

    def test_agotado_y_ficha_sin_stock_exacto(self):
        respuesta = self.client.get(reverse("api:producto-detail", args=["gorra-running"]))
        datos = respuesta.json()
        self.assertTrue(datos["agotado"])
        self.assertNotIn("stock", datos["variantes"][0])  # no revelamos cuántas unidades hay
        self.assertFalse(datos["variantes"][0]["disponible"])

    def test_producto_inactivo_da_404(self):
        respuesta = self.client.get(reverse("api:producto-detail", args=["producto-oculto"]))
        self.assertEqual(respuesta.status_code, 404)

    def test_la_api_es_de_solo_lectura(self):
        respuesta = self.client.post(reverse("api:producto-list"), {"nombre": "Hack"})
        self.assertEqual(respuesta.status_code, 405)

    def test_filtros_disponibles(self):
        datos = self.client.get(reverse("api:filtros")).json()
        self.assertEqual([c["slug"] for c in datos["categorias"]], ["accesorios", "ropa"])
        self.assertEqual({c["nombre"] for c in datos["colores"]}, {"Negro", "Blanco"})
        self.assertEqual(datos["precio"], {"minimo": "20.00", "maximo": "30.00"})

    def test_listado_sin_consultas_n_mas_1(self):
        # El número de consultas no debe crecer con el número de productos
        with self.assertNumQueries(5):
            self.client.get(reverse("api:producto-list"))

    def test_documentacion_disponible(self):
        self.assertEqual(self.client.get(reverse("docs")).status_code, 200)
        self.assertEqual(self.client.get(reverse("esquema")).status_code, 200)
