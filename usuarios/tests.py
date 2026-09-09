"""
Pruebas unitarias del módulo de Seguridad y Usuarios.
Cubre: validador de RUT, modelo Usuario y control de acceso por rol (RBAC).
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Usuario
from .validators import validar_rut, calcular_dv, limpiar_rut


class ValidadorRutTest(TestCase):
    """CU-02: validación de RUT chileno (módulo 11)."""

    def test_dv_correcto(self):
        # 11.111.111-1 es un RUT con DV válido
        self.assertEqual(calcular_dv("11111111"), "1")

    def test_dv_k(self):
        # Caso en que el dígito verificador es K
        self.assertEqual(calcular_dv("12345678"), "5")

    def test_rut_valido_no_lanza(self):
        try:
            validar_rut("11.111.111-1")
        except ValidationError:
            self.fail("validar_rut lanzó error con un RUT válido")

    def test_rut_invalido_lanza(self):
        with self.assertRaises(ValidationError):
            validar_rut("11.111.111-9")

    def test_limpiar_rut(self):
        self.assertEqual(limpiar_rut("12.345.678-k"), "12345678K")


class UsuarioModelTest(TestCase):
    """CU-51 / CU-52: modelo de usuario y sincronización de estado."""

    def test_estado_sincroniza_is_active(self):
        u = Usuario.objects.create_user(username="ana", password="x", email="a@a.cl", estado=False)
        self.assertFalse(u.is_active)
        u.estado = True
        u.save()
        self.assertTrue(u.is_active)

    def test_rol_por_defecto(self):
        u = Usuario.objects.create_user(username="bob", password="x", email="b@b.cl")
        self.assertEqual(u.rol, Usuario.Rol.BODEGUERO)


class RBACTest(TestCase):
    """CU-52: solo ADMIN puede acceder a la gestión de usuarios."""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            username="admin", password="clave12345", email="admin@m5.cl", rol="ADMIN")
        self.bodeguero = Usuario.objects.create_user(
            username="bode", password="clave12345", email="bode@m5.cl", rol="BODEGUERO")

    def test_anonimo_redirige_a_login(self):
        resp = self.client.get(reverse("usuarios:lista"))
        self.assertEqual(resp.status_code, 302)  # redirige a login

    def test_bodeguero_sin_permiso(self):
        self.client.login(username="bode", password="clave12345")
        resp = self.client.get(reverse("usuarios:lista"))
        self.assertEqual(resp.status_code, 403)  # PermissionDenied

    def test_admin_con_permiso(self):
        self.client.login(username="admin", password="clave12345")
        resp = self.client.get(reverse("usuarios:lista"))
        self.assertEqual(resp.status_code, 200)
