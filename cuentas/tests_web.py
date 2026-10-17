"""Tests de registro, inicio y cierre de sesión y Mi cuenta."""
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from carrito.models import Carrito, LineaCarrito
from carrito.services import SESION_CARRITO
from catalogo.models import Categoria, Color, Producto, Talla, Variante
from cuentas.models import RegistroAcceso, Usuario

CLAVE = "Fenix-2026-segura"


class RegistroTests(TestCase):
    def datos(self, **cambios):
        return {"first_name": "Laura", "email": "Laura@Ejemplo.com", "password1": CLAVE, "password2": CLAVE,
                "acepta_privacidad": "on", **cambios}

    def test_registro_crea_la_cuenta_en_minusculas_e_inicia_sesion(self):
        respuesta = self.client.post(reverse("cuentas:registro"), self.datos())
        self.assertRedirects(respuesta, reverse("cuentas:perfil"))
        usuario = Usuario.objects.get()
        self.assertEqual(usuario.email, "laura@ejemplo.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)
        self.assertEqual(RegistroAcceso.objects.filter(usuario=usuario).count(), 1)  # la señal registró el acceso

    def test_no_permite_correo_repetido_aunque_cambien_mayusculas(self):
        Usuario.objects.create_user(email="laura@ejemplo.com", password=CLAVE)
        respuesta = self.client.post(reverse("cuentas:registro"), self.datos(email="LAURA@ejemplo.com"))
        self.assertContains(respuesta, "Ya existe una cuenta con este correo")
        self.assertEqual(Usuario.objects.count(), 1)

    def test_exige_consentimiento_y_contrasena_segura(self):
        respuesta = self.client.post(reverse("cuentas:registro"),
                                     self.datos(acepta_privacidad="", password1="12345678", password2="12345678"))
        self.assertContains(respuesta, "Necesitamos tu consentimiento")
        self.assertContains(respuesta, "demasiado común")
        self.assertFalse(Usuario.objects.exists())

    def test_vuelve_a_la_pagina_de_origen_pero_nunca_a_otra_web(self):
        respuesta = self.client.post(reverse("cuentas:registro"), self.datos(next="/carrito/"))
        self.assertRedirects(respuesta, "/carrito/")
        self.client.logout()
        respuesta = self.client.post(reverse("cuentas:registro"),
                                     self.datos(email="otra@ejemplo.com", next="https://web-maliciosa.com/"))
        self.assertRedirects(respuesta, reverse("cuentas:perfil"))


class AccesoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.usuario = Usuario.objects.create_user(email="juan@ejemplo.com", password=CLAVE, first_name="Juan")

    def entrar(self, password=CLAVE, email="JUAN@ejemplo.com", **extra):
        return self.client.post(reverse("cuentas:entrar"), {"username": email, "password": password, **extra})

    def test_entrar_con_correo_sin_importar_mayusculas(self):
        respuesta = self.entrar()
        self.assertRedirects(respuesta, reverse("cuentas:perfil"))

    def test_contrasena_incorrecta(self):
        self.assertContains(self.entrar(password="mala"), "Correo o contraseña incorrectos")

    def test_bloqueo_tras_5_intentos_fallidos(self):
        for _ in range(5):
            self.entrar(password="mala")
        respuesta = self.entrar()  # incluso con la contraseña buena
        self.assertContains(respuesta, "Demasiados intentos fallidos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_al_entrar_se_fusiona_el_carrito_de_visitante(self):
        variante = Variante.objects.create(
            producto=Producto.objects.create(nombre="Gorra", slug="gorra", descripcion="-", precio=Decimal("20"),
                                             categoria=Categoria.objects.create(nombre="Gorras", slug="gorras")),
            talla=Talla.objects.create(nombre="Única"), color=Color.objects.create(nombre="Negro", codigo_hex="#121214"),
            sku="G", stock=5)
        visitante = Carrito.objects.create()
        LineaCarrito.objects.create(carrito=visitante, variante=variante, cantidad=2)
        sesion = self.client.session
        sesion[SESION_CARRITO] = visitante.pk
        sesion.save()

        self.entrar(next="/carrito/")
        self.assertEqual(self.usuario.carrito.lineas.get().cantidad, 2)

    def test_mi_cuenta_exige_sesion(self):
        respuesta = self.client.get(reverse("cuentas:perfil"))
        self.assertRedirects(respuesta, f"{reverse('cuentas:entrar')}?next={reverse('cuentas:perfil')}")

    def test_mi_cuenta_muestra_los_datos(self):
        self.entrar()
        respuesta = self.client.get(reverse("cuentas:perfil"))
        self.assertContains(respuesta, "Hola, Juan")
        self.assertContains(respuesta, "Todavía no has hecho ningún pedido")

    def test_cerrar_sesion_solo_con_post(self):
        self.entrar()
        self.assertEqual(self.client.get(reverse("cuentas:salir")).status_code, 405)
        respuesta = self.client.post(reverse("cuentas:salir"))
        self.assertRedirects(respuesta, reverse("catalogo:inicio"))
        self.assertNotIn("_auth_user_id", self.client.session)
