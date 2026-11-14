"""
Tests de seguridad: RF-47 (login con correo), RNF-08 (bloqueo por intentos)
y RNF-09 (sin borrado físico de registros críticos).
"""
from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .integridad import BorradoFisicoNoPermitido, borrado_fisico_permitido
from .models import IntentoAcceso, Usuario


class LoginConCorreoTests(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user(
            username="jperez", email="jperez@m-5.cl", password="Clave-segura-123",
            rol=Usuario.Rol.JEFE_PROYECTO)

    def _login(self, ident, clave="Clave-segura-123"):
        return self.client.post(reverse("login"), {"username": ident, "password": clave})

    def test_rf47_entra_con_correo_institucional(self):
        r = self._login("jperez@m-5.cl")
        self.assertRedirects(r, "/", fetch_redirect_response=False)

    def test_rf47_correo_no_distingue_mayusculas(self):
        r = self._login("JPerez@M-5.cl")
        self.assertEqual(r.status_code, 302)

    def test_cu48_error_no_dice_que_campo_fallo(self):
        r = self._login("jperez@m-5.cl", "mala")
        self.assertContains(r, "Correo o contraseña incorrectos.")

    def test_rf47_el_nombre_de_usuario_ya_no_sirve_para_entrar(self):
        r = self._login("jperez")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Correo o contraseña incorrectos.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cuenta_deshabilitada_no_entra(self):
        self.u.estado = False
        self.u.save()
        r = self._login("jperez@m-5.cl")
        self.assertEqual(r.status_code, 200)


class BloqueoPorIntentosTests(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user(
            username="ana", email="ana@m-5.cl", password="Clave-segura-123",
            rol=Usuario.Rol.BODEGUERO)

    def _login(self, ident="ana@m-5.cl", clave="mala"):
        return self.client.post(reverse("login"), {"username": ident, "password": clave})

    def test_rnf08_cuatro_fallos_no_bloquean(self):
        for _ in range(4):
            self._login()
        self.assertEqual(self._login(clave="Clave-segura-123").status_code, 302)

    def test_rnf08_quinto_fallo_bloquea_incluso_con_clave_correcta(self):
        for _ in range(5):
            r = self._login()
        self.assertContains(r, "Demasiados intentos fallidos")
        r = self._login(clave="Clave-segura-123")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "bloqueado hasta")

    def test_rnf08_el_correo_cuenta_igual_con_mayusculas(self):
        for ident in ("ana@m-5.cl", "ANA@m-5.cl", "Ana@M-5.cl", "ana@m-5.cl", "ANA@M-5.CL"):
            self._login(ident)
        self.assertIsNotNone(IntentoAcceso.bloqueado(f"u{self.u.pk}"))

    def test_rnf08_bloqueo_dura_15_minutos(self):
        for _ in range(5):
            self._login()
        despues = timezone.now() + timedelta(minutes=15, seconds=1)
        with mock.patch("django.utils.timezone.now", return_value=despues):
            r = self._login(clave="Clave-segura-123")
        self.assertEqual(r.status_code, 302)

    def test_rnf08_login_correcto_reinicia_el_contador(self):
        for _ in range(4):
            self._login()
        self._login(clave="Clave-segura-123")
        self.client.logout()
        for _ in range(4):
            self._login()
        self.assertEqual(self._login(clave="Clave-segura-123").status_code, 302)

    def test_rnf08_bloquea_identificadores_inexistentes_sin_delatarlos(self):
        for _ in range(5):
            r = self._login("nadie@m-5.cl")
        self.assertContains(r, "Demasiados intentos fallidos")


class SinBorradoFisicoTests(TestCase):
    def setUp(self):
        from proveedores.models import Proveedor
        self.prov = Proveedor.objects.create(nombre="Prov", rut="11.111.111-1")

    def test_rnf09_instancia_no_se_borra(self):
        with self.assertRaises(BorradoFisicoNoPermitido):
            self.prov.delete()

    def test_rnf09_queryset_no_se_borra(self):
        from proveedores.models import Proveedor
        with self.assertRaises(BorradoFisicoNoPermitido):
            Proveedor.objects.all().delete()

    def test_rnf09_admin_no_ofrece_borrar(self):
        from django.contrib import admin
        from adquisiciones.models import OrdenCompra
        from facturacion.models import Factura
        from inventario.models import MovimientoInventario
        from proveedores.models import Proveedor
        for modelo in (OrdenCompra, Factura, MovimientoInventario, Proveedor):
            self.assertFalse(admin.site._registry[modelo].has_delete_permission(None))

    def test_rnf09_salida_explicita_para_preparar_produccion(self):
        from proveedores.models import Proveedor
        with borrado_fisico_permitido():
            self.prov.delete()
        self.assertFalse(Proveedor.objects.exists())
