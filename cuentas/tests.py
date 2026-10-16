from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from cuentas.models import Direccion, RegistroAcceso


class CuentasTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user("Juan@Test.com", "ClaveSegura123!")

    def test_el_correo_se_guarda_en_minusculas(self):
        self.assertEqual(self.usuario.email, "juan@test.com")

    def test_no_se_puede_registrar_el_mismo_correo_con_mayusculas(self):
        with self.assertRaises(IntegrityError):
            get_user_model().objects.create(email="JUAN@test.com")

    def test_el_inicio_de_sesion_queda_registrado(self):
        # Iniciamos sesión con un formulario real (el del panel), como haría un usuario normal, para que se cree el registro de acceso
        self.usuario.is_staff = True
        self.usuario.save()
        self.client.post(
            "/admin/login/",
            {"username": "juan@test.com", "password": "ClaveSegura123!"},
            HTTP_USER_AGENT="Safari en macOS",
        )
        registro = RegistroAcceso.objects.get(usuario=self.usuario)
        self.assertEqual(registro.ip, "127.0.0.1")
        self.assertEqual(registro.dispositivo, "Safari en macOS")

    def test_limpiar_accesos_borra_solo_los_de_mas_de_90_dias(self):
        antiguo = RegistroAcceso.objects.create(usuario=self.usuario)
        RegistroAcceso.objects.filter(pk=antiguo.pk).update(fecha=timezone.now() - timedelta(days=91))
        reciente = RegistroAcceso.objects.create(usuario=self.usuario)
        call_command("limpiar_accesos", stdout=StringIO())
        self.assertEqual(list(RegistroAcceso.objects.values_list("pk", flat=True)), [reciente.pk])

    def test_solo_una_direccion_predeterminada_por_usuario(self):
        datos = dict(nombre_destinatario="Juan", direccion="C/ Sol 1", ciudad="Madrid",
                     codigo_postal="28001", provincia="Madrid", telefono="600000000")
        Direccion.objects.create(usuario=self.usuario, predeterminada=True, **datos)
        with self.assertRaises(IntegrityError):
            Direccion.objects.create(usuario=self.usuario, predeterminada=True, **datos)