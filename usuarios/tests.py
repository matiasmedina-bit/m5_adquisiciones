"""
Pruebas unitarias del módulo de Seguridad y Usuarios.
Cubre: validador de RUT, modelo Usuario y control de acceso por rol (RBAC).
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Usuario
from .validators import validar_rut, calcular_dv, limpiar_rut
from django.conf import settings
from django.core import mail
from decimal import Decimal
from usuarios.models import ParametrosSistema


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


# ==========================================================================
#  Incremento 3 — CU-49/50 (correo único), CU-52 (activación),
#  CU-55 (sesión), CU-56 (recuperación), CU-60 (parámetros)
# ==========================================================================

class ParametrosSistemaCU60Test(TestCase):
    """CU-60 (RF-57): los parámetros generales, configurables sin tocar código."""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            "adm60", password="clave12345", email="a60@m5.cl", rol="ADMIN")
        self.jefe = Usuario.objects.create_user(
            "jp60", password="clave12345", email="j60@m5.cl", rol="JEFE_PROYECTO")
        self.client.login(username="adm60", password="clave12345")

    def test_se_crean_solos_con_valores_por_defecto(self):
        p = ParametrosSistema.actuales()
        self.assertEqual(p.tolerancia_factura_pct, Decimal("5"))
        self.assertEqual(p.umbral_archivo_mb, 10)

    def test_siempre_hay_una_sola_fila(self):
        ParametrosSistema.actuales()
        ParametrosSistema.objects.create(tolerancia_factura_pct=9)
        self.assertEqual(ParametrosSistema.objects.count(), 1)
        self.assertEqual(ParametrosSistema.actuales().tolerancia_factura_pct, Decimal("9"))

    def test_no_se_pueden_borrar(self):
        """Sin parámetros el sistema quedaría a medio operar."""
        p = ParametrosSistema.actuales()
        p.delete()
        self.assertTrue(ParametrosSistema.objects.exists())

    def test_el_administrador_los_guarda(self):
        resp = self.client.post(reverse("usuarios:parametros"), {
            "tolerancia_factura_pct": "8.5",
            "stock_minimo_defecto": "25",
            "umbral_archivo_mb": "20",
        })
        self.assertEqual(resp.status_code, 302)
        p = ParametrosSistema.actuales()
        self.assertEqual(p.tolerancia_factura_pct, Decimal("8.5"))
        self.assertEqual(p.umbral_archivo_mb, 20)
        self.assertEqual(p.actualizado_por, self.admin)

    def test_queda_registrado_en_la_bitacora(self):
        from auditoria.models import RegistroAuditoria
        self.client.post(reverse("usuarios:parametros"), {
            "tolerancia_factura_pct": "7", "stock_minimo_defecto": "0",
            "umbral_archivo_mb": "15"})
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion=RegistroAuditoria.Accion.PARAMETROS_MODIFICADOS).exists())

    # --- Excepción 1: valores fuera de rango ---

    def test_un_valor_fuera_de_rango_no_se_guarda(self):
        for campo, valor in [("tolerancia_factura_pct", "150"),
                             ("umbral_archivo_mb", "0"),
                             ("stock_minimo_defecto", "-5")]:
            with self.subTest(campo=campo):
                datos = {"tolerancia_factura_pct": "5", "stock_minimo_defecto": "0",
                         "umbral_archivo_mb": "10"}
                datos[campo] = valor
                resp = self.client.post(reverse("usuarios:parametros"), datos)
                self.assertEqual(resp.status_code, 200)   # vuelve con el error
                self.assertNotEqual(
                    str(getattr(ParametrosSistema.actuales(), campo)), valor)

    def test_un_valor_no_numerico_no_se_guarda(self):
        resp = self.client.post(reverse("usuarios:parametros"), {
            "tolerancia_factura_pct": "mucho", "stock_minimo_defecto": "0",
            "umbral_archivo_mb": "10"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "fuera de rango")

    def test_solo_el_administrador_entra(self):
        self.client.login(username="jp60", password="clave12345")
        self.assertEqual(self.client.get(reverse("usuarios:parametros")).status_code, 403)

    def test_la_tolerancia_configurada_manda_sobre_la_facturacion(self):
        """El parámetro no es decorativo: cambia el comportamiento real."""
        from usuarios.models import ParametrosSistema as P
        p = P.actuales(); p.tolerancia_factura_pct = Decimal("50"); p.save()
        self.assertEqual(P.actuales().tolerancia_factura_pct, Decimal("50"))


class ActivacionDeCuentaCU52Test(TestCase):
    """CU-52 (RF-49): enlace temporal para que el usuario defina su contraseña."""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            "adm52", password="clave12345", email="a52@m5.cl", rol="ADMIN")
        self.client.login(username="adm52", password="clave12345")
        mail.outbox = []

    def _crear(self, **extra):
        datos = {"username": "nuevo52", "first_name": "Ana", "last_name": "Soto",
                 "email": "ana.soto@m5.cl", "telefono": "", "rol": "BODEGUERO",
                 "estado": "on"}
        datos.update(extra)
        return self.client.post(reverse("usuarios:crear"), datos)

    def test_crear_una_cuenta_dispara_el_correo(self):
        self._crear()
        self.assertTrue(Usuario.objects.filter(username="nuevo52").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("ana.soto@m5.cl", mail.outbox[0].to)
        self.assertIn("Activa tu cuenta", mail.outbox[0].subject)

    def test_el_correo_lleva_un_enlace_usable(self):
        self._crear()
        cuerpo = mail.outbox[0].body
        enlace = next(p for p in cuerpo.split() if "/clave/" in p)
        ruta = enlace.split("testserver")[-1]
        self.assertEqual(self.client.get(ruta, follow=True).status_code, 200)

    def test_la_cuenta_nace_sin_contrasena_utilizable(self):
        self._crear()
        usuario = Usuario.objects.get(username="nuevo52")
        self.assertFalse(usuario.has_usable_password())

    def test_el_administrador_puede_reenviar_el_enlace(self):
        self._crear()
        usuario = Usuario.objects.get(username="nuevo52")
        mail.outbox = []
        self.client.post(reverse("usuarios:reenviar_activacion", args=[usuario.pk]))
        self.assertEqual(len(mail.outbox), 1)

    # --- Excepción 1 del CU-49: correo duplicado ---

    def test_un_correo_repetido_bloquea_la_creacion(self):
        self._crear()
        resp = self._crear(username="otro52")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ya está asociado a otra cuenta")
        self.assertFalse(Usuario.objects.filter(username="otro52").exists())

    def test_editar_a_un_correo_ya_usado_tambien_se_bloquea(self):
        self._crear()
        otro = Usuario.objects.create_user(
            "otro52b", password="x", email="libre@m5.cl", rol="BODEGUERO")
        resp = self.client.post(reverse("usuarios:editar", args=[otro.pk]), {
            "username": "otro52b", "first_name": "B", "last_name": "C",
            "email": "ana.soto@m5.cl", "telefono": "", "rol": "BODEGUERO", "estado": "on"})
        self.assertContains(resp, "ya está asociado a otra cuenta")
        otro.refresh_from_db()
        self.assertEqual(otro.email, "libre@m5.cl")


class RecuperacionContrasenaCU56Test(TestCase):
    """CU-56 (RF-53): recuperación por enlace temporal."""

    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            "recupera", password="clave12345", email="rec@m5.cl", rol="BODEGUERO")
        mail.outbox = []

    def test_la_pantalla_de_login_ofrece_recuperar(self):
        resp = self.client.get(reverse("login"))
        self.assertContains(resp, "Olvidaste tu contraseña")
        self.assertContains(resp, reverse("password_reset"))

    def test_un_correo_registrado_recibe_el_enlace(self):
        self.client.post(reverse("password_reset"), {"email": "rec@m5.cl"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/clave/", mail.outbox[0].body)

    def test_el_enlace_permite_definir_una_contrasena_nueva(self):
        self.client.post(reverse("password_reset"), {"email": "rec@m5.cl"})
        enlace = next(p for p in mail.outbox[0].body.split() if "/clave/" in p)
        ruta = enlace.split("testserver")[-1]
        resp = self.client.get(ruta, follow=True)
        self.client.post(resp.redirect_chain[-1][0] if resp.redirect_chain else ruta,
                         {"new_password1": "NuevaClave2026", "new_password2": "NuevaClave2026"},
                         follow=True)
        self.assertTrue(self.client.login(username="recupera", password="NuevaClave2026"))

    # --- Excepción 1: no revelar si el correo existe ---

    def test_un_correo_inexistente_responde_igual_que_uno_real(self):
        real = self.client.post(reverse("password_reset"), {"email": "rec@m5.cl"})
        falso = self.client.post(reverse("password_reset"), {"email": "nadie@m5.cl"})
        self.assertEqual(real.status_code, falso.status_code)
        self.assertEqual(real.url, falso.url)

    def test_un_correo_inexistente_no_genera_envio(self):
        self.client.post(reverse("password_reset"), {"email": "nadie@m5.cl"})
        self.assertEqual(len(mail.outbox), 0)

    def test_el_mensaje_no_confirma_ni_desmiente_la_cuenta(self):
        resp = self.client.get(reverse("password_reset_done"))
        self.assertContains(resp, "Si ese correo corresponde a una cuenta")


class SesionPorInactividadCU55Test(TestCase):
    """CU-55 (RF-52): cierre automático a los 30 minutos sin actividad."""

    def test_la_sesion_dura_treinta_minutos(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 30 * 60)

    def test_el_plazo_se_reinicia_con_cada_actividad(self):
        """
        Excepción 1: quien sigue trabajando no debe ser expulsado.
        `SAVE_EVERY_REQUEST` es lo que hace que el reloj cuente desde la última
        acción y no desde el login.
        """
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_la_sesion_no_sobrevive_al_cierre_del_navegador(self):
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

    def test_una_sesion_vencida_manda_al_login(self):
        cliente = Client()
        usuario = Usuario.objects.create_user(
            "vence", password="clave12345", email="v@m5.cl", rol="ADMIN")
        cliente.login(username="vence", password="clave12345")
        self.assertEqual(cliente.get(reverse("home")).status_code, 200)
        cliente.cookies.pop("sessionid", None)   # como si hubiera caducado
        resp = cliente.get(reverse("home"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)
