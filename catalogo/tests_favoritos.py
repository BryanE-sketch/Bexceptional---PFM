"""Tests de favoritos: guardar y quitar con el corazón, y la página Mis favoritos."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Favorito, Producto
from cuentas.models import Usuario


class FavoritosTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(email="ana@ejemplo.com", password="Fenix-2026-segura")
        self.producto = Producto.objects.create(nombre="Gorra", slug="gorra", descripcion="-", precio=Decimal("20"),
                                                categoria=Categoria.objects.create(nombre="Gorras", slug="gorras"))
        self.url = reverse("catalogo:alternar_favorito", args=[self.producto.pk])

    def test_el_corazon_guarda_y_quita_con_htmx(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, 'aria-pressed="true"')
        self.assertTrue(Favorito.objects.filter(usuario=self.usuario, producto=self.producto).exists())
        respuesta = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertContains(respuesta, 'aria-pressed="false"')
        self.assertFalse(Favorito.objects.exists())

    def test_sin_sesion_pide_entrar_y_vuelve_al_producto(self):
        respuesta = self.client.post(self.url, HTTP_HX_REQUEST="true")
        self.assertEqual(respuesta["HX-Redirect"], f"{reverse('cuentas:entrar')}?next=/producto/gorra/")
        respuesta = self.client.post(self.url)  # sin JavaScript
        self.assertRedirects(respuesta, f"{reverse('cuentas:entrar')}?next=/producto/gorra/", fetch_redirect_response=False)
        self.assertFalse(Favorito.objects.exists())

    def test_pagina_de_favoritos(self):
        self.client.force_login(self.usuario)
        self.assertContains(self.client.get(reverse("catalogo:favoritos")), "Aún no tienes favoritos")
        Favorito.objects.create(usuario=self.usuario, producto=self.producto)
        self.assertContains(self.client.get(reverse("catalogo:favoritos")), "Gorra")

    def test_quitar_desde_la_lista_hace_desaparecer_la_tarjeta(self):
        self.client.force_login(self.usuario)
        Favorito.objects.create(usuario=self.usuario, producto=self.producto)
        respuesta = self.client.post(self.url, {"origen": "lista"}, HTTP_HX_REQUEST="true")
        self.assertEqual(respuesta.content, b"")
        self.assertFalse(Favorito.objects.exists())

    def test_la_ficha_muestra_si_ya_es_favorito(self):
        self.client.force_login(self.usuario)
        Favorito.objects.create(usuario=self.usuario, producto=self.producto)
        respuesta = self.client.get(self.producto.get_absolute_url())
        self.assertContains(respuesta, "Quitar de favoritos")

    def test_favoritos_exige_sesion_y_solo_post(self):
        self.assertEqual(self.client.get(reverse("catalogo:favoritos")).status_code, 302)
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(self.url).status_code, 405)
