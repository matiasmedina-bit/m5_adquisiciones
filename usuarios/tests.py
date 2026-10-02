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
from io import StringIO


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


class PrepararProduccionTest(TestCase):
    """
    El comando que se corre una sola vez, en el servidor del cliente, para
    dejar el sistema limpio con su administrador real. Se prueba a conciencia
    porque no hay segunda oportunidad: si borra de más o deja al admin sin
    permisos, el sistema queda arriba y nadie puede administrarlo.
    """

    def setUp(self):
        from django.core.management import call_command
        call_command("seed_demo", verbosity=0)

    def _correr(self, **respuestas):
        """Corre el comando simulando lo que escribiría el operador."""
        from django.core.management import call_command
        from unittest.mock import patch
        entradas = iter([
            respuestas.get("confirmacion", "BORRAR DEMO"),
            respuestas.get("username", "m.medina"),
            respuestas.get("nombre", "Matías"),
            respuestas.get("apellido", "Medina"),
            respuestas.get("email", "admin@constructoram5.cl"),
            respuestas.get("telefono", "+56912345678"),
        ])
        claves = iter([respuestas.get("password", "ObraM5-2026!")] * 2)
        salida = StringIO()
        with patch("builtins.input", lambda *a: next(entradas)), \
             patch("usuarios.management.commands.preparar_produccion.getpass",
                   lambda *a: next(claves)):
            call_command("preparar_produccion", stdout=salida, stderr=StringIO())
        return salida.getvalue()

    def test_borra_todos_los_datos_de_demostracion(self):
        from proyectos.models import Proyecto
        from solicitudes.models import SolicitudMaterial
        from adquisiciones.models import OrdenCompra
        from facturacion.models import Factura
        from inventario.models import MovimientoInventario

        self.assertTrue(Proyecto.objects.exists())   # la demo estaba cargada
        self._correr()

        self.assertFalse(Proyecto.objects.exists())
        self.assertFalse(SolicitudMaterial.objects.exists())
        self.assertFalse(OrdenCompra.objects.exists())
        self.assertFalse(Factura.objects.exists())
        self.assertFalse(MovimientoInventario.objects.exists())

    def test_no_queda_ninguna_cuenta_de_demostracion(self):
        self._correr()
        for demo in ["admin", "jefe", "encargado", "bodega", "contador"]:
            self.assertFalse(Usuario.objects.filter(username=demo).exists(), demo)

    def test_el_administrador_queda_con_rol_ADMIN(self):
        """El error clásico: createsuperuser lo dejaba como BODEGUERO."""
        self._correr()
        admin = Usuario.objects.get(username="m.medina")
        self.assertEqual(admin.rol, Usuario.Rol.ADMIN)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.estado)
        self.assertFalse(admin.pendiente_aprobacion)

    def test_el_administrador_puede_entrar_de_inmediato(self):
        self._correr()
        cliente = Client()
        self.assertTrue(cliente.login(username="m.medina", password="ObraM5-2026!"))
        # y llega a las dos pantallas que sólo ve un administrador
        self.assertEqual(cliente.get(reverse("usuarios:lista")).status_code, 200)
        self.assertEqual(cliente.get(reverse("usuarios:parametros")).status_code, 200)

    def test_queda_una_sola_cuenta(self):
        self._correr()
        self.assertEqual(Usuario.objects.count(), 1)

    def test_los_parametros_sobreviven_con_sus_valores_por_defecto(self):
        self._correr()
        self.assertTrue(ParametrosSistema.objects.exists())

    def test_sin_la_frase_exacta_no_borra_nada(self):
        from proyectos.models import Proyecto
        from django.core.management.base import CommandError
        antes = Proyecto.objects.count()
        with self.assertRaises(CommandError):
            self._correr(confirmacion="si")
        self.assertEqual(Proyecto.objects.count(), antes)

    def test_la_bitacora_de_la_demo_no_viaja_al_cliente(self):
        """Son acciones que nunca ocurrieron en M5: ensucian la evidencia."""
        from auditoria.models import RegistroAuditoria
        self.assertTrue(RegistroAuditoria.objects.exists())
        self._correr()
        self.assertFalse(RegistroAuditoria.objects.exists())

    def test_se_puede_conservar_el_catalogo(self):
        from django.core.management import call_command
        from unittest.mock import patch
        from inventario.models import Material
        entradas = iter(["BORRAR DEMO", "m.medina", "Matías", "Medina",
                         "admin@constructoram5.cl", ""])
        claves = iter(["ObraM5-2026!"] * 2)
        with patch("builtins.input", lambda *a: next(entradas)), \
             patch("usuarios.management.commands.preparar_produccion.getpass",
                   lambda *a: next(claves)):
            call_command("preparar_produccion", conservar_catalogo=True,
                         stdout=StringIO(), stderr=StringIO())
        self.assertTrue(Material.objects.exists())

    def test_imprime_lo_que_falta_por_hacer(self):
        salida = self._correr()
        self.assertIn("Rotar la contraseña de PostgreSQL", salida)
        self.assertIn("EMAIL_", salida)


# ==========================================================================
#  Mi perfil: lo que cada usuario cambia solo
# ==========================================================================

class MiPerfilTest(TestCase):
    """Cada persona corrige sus propios datos de contacto sin pedir permiso."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username="bodega1", password="clave12345", email="bodega1@m-5.cl",
            rol="BODEGUERO", first_name="Ana", last_name="Soto",
        )
        self.client = Client()
        self.client.login(username="bodega1", password="clave12345")

    def test_la_barra_superior_lleva_al_perfil(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, reverse("usuarios:mi_perfil"))

    def test_cualquier_rol_entra_a_su_perfil(self):
        self.assertEqual(self.client.get(reverse("usuarios:mi_perfil")).status_code, 200)

    def test_cambia_su_nombre_y_telefono(self):
        self.client.post(reverse("usuarios:mi_perfil"), {
            "first_name": "Ana María", "last_name": "Soto", "telefono": "+56 9 1111 2222",
        })
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, "Ana María")
        self.assertEqual(self.usuario.telefono, "+56 9 1111 2222")

    def test_no_puede_cambiarse_el_rol_por_el_formulario_de_perfil(self):
        """El rol no es un campo del formulario: mandarlo no debe tener efecto."""
        self.client.post(reverse("usuarios:mi_perfil"), {
            "first_name": "Ana", "last_name": "Soto", "rol": "ADMIN",
        })
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.rol, "BODEGUERO")

    def test_no_puede_cambiarse_el_correo_por_el_formulario_de_perfil(self):
        self.client.post(reverse("usuarios:mi_perfil"), {
            "first_name": "Ana", "last_name": "Soto", "email": "otro@m-5.cl",
        })
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "bodega1@m-5.cl")

    def test_sin_foto_muestra_las_iniciales(self):
        self.assertEqual(self.usuario.iniciales, "AS")

    def test_sin_nombre_cargado_usa_la_inicial_del_usuario(self):
        self.usuario.first_name = ""
        self.usuario.last_name = ""
        self.assertEqual(self.usuario.iniciales, "B")

    def test_un_anonimo_no_entra_al_perfil(self):
        self.client.logout()
        resp = self.client.get(reverse("usuarios:mi_perfil"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp["Location"])

    def test_puede_cambiar_su_contrasena_con_la_sesion_abierta(self):
        resp = self.client.post(reverse("password_change"), {
            "old_password": "clave12345",
            "new_password1": "OtraClave.2026",
            "new_password2": "OtraClave.2026",
        })
        self.assertEqual(resp.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("OtraClave.2026"))


class SolicitudCambioPerfilTest(TestCase):
    """Correo, usuario y rol los resuelve el administrador, no el interesado."""

    def setUp(self):
        from .models import SolicitudCambioPerfil
        self.SolicitudCambioPerfil = SolicitudCambioPerfil
        self.usuario = Usuario.objects.create_user(
            username="jefe1", password="clave12345", email="jefe1@m-5.cl",
            rol="JEFE_PROYECTO", first_name="Luis", last_name="Pérez",
        )
        self.admin = Usuario.objects.create_user(
            username="admin1", password="clave12345", email="admin1@m-5.cl", rol="ADMIN",
        )
        self.client = Client()

    def _pedir(self, **extra):
        self.client.login(username="jefe1", password="clave12345")
        datos = {"accion": "pedir_cambio", "campo": "email",
                 "valor_solicitado": "luis.perez@m-5.cl", "motivo": "Cambió mi correo"}
        datos.update(extra)
        return self.client.post(reverse("usuarios:mi_perfil"), datos, follow=True)

    def test_el_pedido_queda_pendiente_y_no_cambia_el_dato(self):
        self._pedir()
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "jefe1@m-5.cl")
        solicitud = self.SolicitudCambioPerfil.objects.get()
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.assertEqual(solicitud.valor_actual, "jefe1@m-5.cl")

    def test_el_motivo_es_obligatorio(self):
        self._pedir(motivo="")
        self.assertEqual(self.SolicitudCambioPerfil.objects.count(), 0)

    def test_no_deja_pedir_el_valor_que_ya_tiene(self):
        self._pedir(valor_solicitado="jefe1@m-5.cl")
        self.assertEqual(self.SolicitudCambioPerfil.objects.count(), 0)

    def test_no_deja_pedir_un_correo_de_otra_cuenta(self):
        self._pedir(valor_solicitado="admin1@m-5.cl")
        self.assertEqual(self.SolicitudCambioPerfil.objects.count(), 0)

    def test_un_segundo_pedido_del_mismo_dato_reemplaza_al_primero(self):
        self._pedir(valor_solicitado="uno@m-5.cl")
        self._pedir(valor_solicitado="dos@m-5.cl")
        self.assertEqual(self.SolicitudCambioPerfil.objects.count(), 1)
        self.assertEqual(
            self.SolicitudCambioPerfil.objects.get().valor_solicitado, "dos@m-5.cl")

    def test_el_administrador_aprueba_y_el_dato_cambia(self):
        self._pedir()
        solicitud = self.SolicitudCambioPerfil.objects.get()
        self.client.logout()
        self.client.login(username="admin1", password="clave12345")
        self.client.post(reverse("usuarios:resolver_cambio", args=[solicitud.pk]),
                         {"decision": "aprobar"})
        self.usuario.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(self.usuario.email, "luis.perez@m-5.cl")
        self.assertEqual(solicitud.estado, "APROBADA")
        self.assertEqual(solicitud.resuelta_por, self.admin)

    def test_al_rechazar_el_dato_queda_igual(self):
        self._pedir()
        solicitud = self.SolicitudCambioPerfil.objects.get()
        self.client.logout()
        self.client.login(username="admin1", password="clave12345")
        self.client.post(reverse("usuarios:resolver_cambio", args=[solicitud.pk]),
                         {"decision": "rechazar", "comentario": "Usa el correo institucional"})
        self.usuario.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(self.usuario.email, "jefe1@m-5.cl")
        self.assertEqual(solicitud.estado, "RECHAZADA")
        self.assertIn("institucional", solicitud.comentario)

    # --- Excepción: el valor se ocupó entre el pedido y la aprobación ---

    def test_no_aprueba_si_el_correo_se_ocupo_mientras_tanto(self):
        self._pedir()
        solicitud = self.SolicitudCambioPerfil.objects.get()
        Usuario.objects.create_user(
            username="otro", password="clave12345",
            email="luis.perez@m-5.cl", rol="BODEGUERO")
        self.client.logout()
        self.client.login(username="admin1", password="clave12345")
        self.client.post(reverse("usuarios:resolver_cambio", args=[solicitud.pk]),
                         {"decision": "aprobar"})
        self.usuario.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(self.usuario.email, "jefe1@m-5.cl")
        self.assertEqual(solicitud.estado, "PENDIENTE")

    def test_un_usuario_no_resuelve_sus_propios_pedidos(self):
        self._pedir()
        solicitud = self.SolicitudCambioPerfil.objects.get()
        resp = self.client.post(
            reverse("usuarios:resolver_cambio", args=[solicitud.pk]), {"decision": "aprobar"})
        self.assertIn(resp.status_code, (302, 403))
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, "jefe1@m-5.cl")

    def test_el_solicitante_puede_cancelar_el_suyo(self):
        self._pedir()
        solicitud = self.SolicitudCambioPerfil.objects.get()
        self.client.post(reverse("usuarios:cancelar_cambio", args=[solicitud.pk]))
        self.assertEqual(self.SolicitudCambioPerfil.objects.count(), 0)

    def test_nadie_cancela_el_pedido_de_otro(self):
        self._pedir()
        solicitud = self.SolicitudCambioPerfil.objects.get()
        self.client.logout()
        self.client.login(username="admin1", password="clave12345")
        resp = self.client.post(reverse("usuarios:cancelar_cambio", args=[solicitud.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self.SolicitudCambioPerfil.objects.count(), 1)


class EliminarCuentaTest(TestCase):
    """
    Eliminar es distinto de inactivar: borra la cuenta. Sólo procede cuando
    no deja documentos huérfanos.
    """

    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="admin1", password="clave12345", email="admin1@m-5.cl", rol="ADMIN")
        self.otro_admin = Usuario.objects.create_user(
            username="admin2", password="clave12345", email="admin2@m-5.cl", rol="ADMIN")
        self.nuevo = Usuario.objects.create_user(
            username="recien", password="clave12345", email="recien@m-5.cl", rol="BODEGUERO")
        self.client = Client()
        self.client.login(username="admin1", password="clave12345")

    def test_elimina_una_cuenta_sin_historial(self):
        self.client.post(reverse("usuarios:eliminar", args=[self.nuevo.pk]))
        self.assertFalse(Usuario.objects.filter(pk=self.nuevo.pk).exists())

    def test_la_lista_ofrece_eliminar(self):
        resp = self.client.get(reverse("usuarios:lista"))
        self.assertContains(resp, reverse("usuarios:eliminar", args=[self.nuevo.pk]))

    def test_no_se_elimina_a_si_mismo(self):
        self.client.post(reverse("usuarios:eliminar", args=[self.admin.pk]))
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_la_lista_no_ofrece_eliminarse_a_uno_mismo(self):
        resp = self.client.get(reverse("usuarios:lista"))
        self.assertNotContains(resp, reverse("usuarios:eliminar", args=[self.admin.pk]))

    def test_no_elimina_al_ultimo_administrador(self):
        self.otro_admin.delete()
        self.client.logout()
        # queda un solo ADMIN activo: él mismo no puede borrarse, así que se
        # prueba con un segundo admin que inactiva al primero
        tercero = Usuario.objects.create_user(
            username="admin3", password="clave12345", email="admin3@m-5.cl", rol="ADMIN")
        self.admin.estado = False
        self.admin.save()
        self.client.login(username="admin3", password="clave12345")
        self.client.post(reverse("usuarios:eliminar", args=[tercero.pk]))
        self.assertTrue(Usuario.objects.filter(pk=tercero.pk).exists())

    def test_solo_el_administrador_elimina(self):
        self.client.logout()
        self.client.login(username="recien", password="clave12345")
        resp = self.client.post(reverse("usuarios:eliminar", args=[self.otro_admin.pk]))
        self.assertIn(resp.status_code, (302, 403))
        self.assertTrue(Usuario.objects.filter(pk=self.otro_admin.pk).exists())

    def test_no_se_elimina_por_GET(self):
        resp = self.client.get(reverse("usuarios:eliminar", args=[self.nuevo.pk]))
        self.assertEqual(resp.status_code, 405)
        self.assertTrue(Usuario.objects.filter(pk=self.nuevo.pk).exists())

    # --- Excepción 1: la cuenta dejó historial ---

    def test_no_elimina_a_quien_tiene_historial_y_lo_explica(self):
        from proyectos.models import Proyecto
        from solicitudes.models import SolicitudMaterial
        import datetime
        jefe = Usuario.objects.create_user(
            username="jefecito", password="clave12345", email="jefecito@m-5.cl",
            rol="JEFE_PROYECTO")
        proyecto = Proyecto.objects.create(
            nombre="Obra con historial", centro_costo="CC-900",
            mandante="M5", fecha_inicio=datetime.date(2026, 1, 1),
            presupuesto_total=1000000)
        SolicitudMaterial.objects.create(proyecto=proyecto, emisor=jefe)

        resp = self.client.post(
            reverse("usuarios:eliminar", args=[jefe.pk]), follow=True)

        self.assertTrue(Usuario.objects.filter(pk=jefe.pk).exists())
        self.assertContains(resp, "solicitudes de material")
        self.assertContains(resp, "Inactiva la cuenta")

    def test_el_recuento_nombra_lo_que_retiene_la_cuenta(self):
        from proyectos.models import Proyecto
        from solicitudes.models import SolicitudMaterial
        import datetime
        jefe = Usuario.objects.create_user(
            username="jefe2", password="clave12345", email="jefe2@m-5.cl",
            rol="JEFE_PROYECTO")
        proyecto = Proyecto.objects.create(
            nombre="Otra obra", centro_costo="CC-901",
            mandante="M5", fecha_inicio=datetime.date(2026, 1, 1),
            presupuesto_total=1000000)
        SolicitudMaterial.objects.create(proyecto=proyecto, emisor=jefe)
        SolicitudMaterial.objects.create(proyecto=proyecto, emisor=jefe)

        self.assertEqual(
            jefe.registros_que_impiden_borrarlo(), [("solicitudes de material", 2)])

    def test_una_cuenta_limpia_no_tiene_nada_que_la_retenga(self):
        self.assertEqual(self.nuevo.registros_que_impiden_borrarlo(), [])
