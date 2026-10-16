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