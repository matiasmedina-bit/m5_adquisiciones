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


# ==========================================================================
#  CU-52 — Revisión de solicitudes de acceso antes de aprobarlas
# ==========================================================================
class RevisionSolicitudTest(TestCase):
    """El administrador puede ver la solicitud completa y corregirla antes
    de decidir. El caso frecuente es el rol mal elegido por el solicitante."""

    def setUp(self):
        self.client = Client()
        Usuario.objects.create_user(
            username="admin1", password="clave12345", email="admin1@m5.cl", rol="ADMIN")
        self.client.login(username="admin1", password="clave12345")
        self.solicitud = Usuario.objects.create_user(
            username="felipeproyecto", password="clave12345",
            email="felipe@gmail.com", first_name="Felipe", last_name="Gutiérrez",
            rol="BODEGUERO", estado=False, pendiente_aprobacion=True)

    def _url(self):
        return reverse("usuarios:revisar", args=[self.solicitud.pk])

    def _datos(self, **cambios):
        datos = {
            "username": self.solicitud.username,
            "first_name": self.solicitud.first_name,
            "last_name": self.solicitud.last_name,
            "email": self.solicitud.email,
            "telefono": "",
            "rol": self.solicitud.rol,
        }
        datos.update(cambios)
        return datos

    def test_pantalla_muestra_los_datos_del_solicitante(self):
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "felipeproyecto")
        self.assertContains(resp, "felipe@gmail.com")

    def test_corregir_el_rol_y_aprobar(self):
        """Pidió Bodeguero pero es jefe de obra: se corrige al aprobar."""
        resp = self.client.post(
            self._url(), self._datos(rol="JEFE_PROYECTO", accion="aprobar"))
        self.assertEqual(resp.status_code, 302)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.rol, "JEFE_PROYECTO")
        self.assertFalse(self.solicitud.pendiente_aprobacion)
        self.assertTrue(self.solicitud.estado)
        self.assertTrue(self.solicitud.is_active)

    def test_corregir_correo_sin_aprobar_deja_pendiente(self):
        resp = self.client.post(
            self._url(), self._datos(email="felipe.gutierrez@m5.cl", accion="guardar"))
        self.assertEqual(resp.status_code, 302)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.email, "felipe.gutierrez@m5.cl")
        self.assertTrue(self.solicitud.pendiente_aprobacion)
        self.assertFalse(self.solicitud.estado)

    def test_rechazar_desde_la_ficha_elimina(self):
        resp = self.client.post(self._url(), {"accion": "rechazar"})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Usuario.objects.filter(username="felipeproyecto").exists())

    def test_datos_invalidos_no_aprueban(self):
        self.client.post(self._url(), self._datos(email="no-es-un-correo", accion="aprobar"))
        self.solicitud.refresh_from_db()
        self.assertTrue(self.solicitud.pendiente_aprobacion)

    def test_usuario_ya_aprobado_no_tiene_ficha_de_revision(self):
        aprobado = Usuario.objects.create_user(
            username="yaesta", password="clave12345", email="ya@m5.cl", rol="BODEGUERO")
        resp = self.client.get(reverse("usuarios:revisar", args=[aprobado.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_solo_el_administrador_puede_revisar(self):
        Usuario.objects.create_user(
            username="bodega1", password="clave12345", email="b1@m5.cl", rol="BODEGUERO")
        self.client.login(username="bodega1", password="clave12345")
        resp = self.client.get(self._url())
        self.assertNotEqual(resp.status_code, 200)

    def test_aprobar_y_rechazar_no_responden_a_GET(self):
        """Aprobar y rechazar cambian datos: un enlace GET puede dispararse
        solo (prefetch del navegador, un bot) y rechazar además borra."""
        resp = self.client.get(reverse("usuarios:aprobar", args=[self.solicitud.pk]))
        self.assertEqual(resp.status_code, 405)
        resp = self.client.get(reverse("usuarios:rechazar", args=[self.solicitud.pk]))
        self.assertEqual(resp.status_code, 405)
        self.solicitud.refresh_from_db()
        self.assertTrue(self.solicitud.pendiente_aprobacion)

    def test_aprobar_por_POST_funciona(self):
        resp = self.client.post(reverse("usuarios:aprobar", args=[self.solicitud.pk]))
        self.assertEqual(resp.status_code, 302)
        self.solicitud.refresh_from_db()
        self.assertFalse(self.solicitud.pendiente_aprobacion)
        self.assertTrue(self.solicitud.estado)

    def test_el_listado_enlaza_a_la_ficha_de_revision(self):
        resp = self.client.get(reverse("usuarios:lista"))
        self.assertContains(resp, self._url())
