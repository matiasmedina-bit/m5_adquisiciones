"""
CU-53 (RF-50) — Registrando en bitácora de auditoría.

Flujo principal: ocurre una acción auditable y el sistema deja constancia del
usuario, la fecha, la hora y la acción realizada.
Excepción 1: una acción que no es auditable no genera ningún registro.
"""
from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from usuarios.models import Usuario
from proyectos.models import Proyecto
from inventario.models import Material, MovimientoInventario
from solicitudes.models import SolicitudMaterial, SolicitudDetalle
from .models import RegistroAuditoria, registrar


class RegistrarHelperTest(TestCase):
    """El único punto de escritura de la bitácora."""

    def setUp(self):
        self.user = Usuario.objects.create_user(
            username="ana", password="x", email="a@m5.cl", rol="ADMIN",
            first_name="Ana", last_name="Soto")

    def test_registra_usuario_fecha_hora_y_accion(self):
        antes = timezone.now()
        reg = registrar(self.user, RegistroAuditoria.Accion.SM_EMITIDA,
                        "Emitió la solicitud.", "SM-000001")
        self.assertIsNotNone(reg)
        self.assertEqual(reg.usuario, self.user)
        self.assertEqual(reg.accion, RegistroAuditoria.Accion.SM_EMITIDA)
        self.assertEqual(reg.referencia, "SM-000001")
        self.assertGreaterEqual(reg.fecha, antes)

    def test_el_modulo_se_deduce_de_la_accion(self):
        reg = registrar(self.user, RegistroAuditoria.Accion.OC_EMITIDA, "x", "OC-1")
        self.assertEqual(reg.modulo, RegistroAuditoria.Modulo.ADQUISICIONES)
        reg = registrar(self.user, RegistroAuditoria.Accion.MOV_INVENTARIO, "x")
        self.assertEqual(reg.modulo, RegistroAuditoria.Modulo.INVENTARIO)

    def test_guarda_el_nombre_del_usuario_en_texto(self):
        reg = registrar(self.user, RegistroAuditoria.Accion.USUARIO_CREADO, "x")
        self.assertEqual(reg.usuario_nombre, "Ana Soto")

    def test_la_bitacora_sobrevive_a_la_baja_de_la_cuenta(self):
        reg = registrar(self.user, RegistroAuditoria.Accion.USUARIO_CREADO, "x", "ana")
        self.user.delete()
        reg.refresh_from_db()
        self.assertIsNone(reg.usuario_id)
        self.assertEqual(reg.actor, "Ana Soto")   # sigue diciendo quién fue

    # --- Excepción 1 ---

    def test_una_accion_no_auditable_no_genera_registro(self):
        reg = registrar(self.user, "CONSULTO_UNA_PANTALLA", "Abrió el listado.")
        self.assertIsNone(reg)
        self.assertEqual(RegistroAuditoria.objects.count(), 0)

    def test_una_accion_inventada_no_genera_registro(self):
        self.assertIsNone(registrar(self.user, "", "x"))
        self.assertIsNone(registrar(self.user, "SM_BORRADA", "x"))
        self.assertEqual(RegistroAuditoria.objects.count(), 0)


class AuditoriaDeAccionesTest(TestCase):
    """Las acciones que el RF-50 enumera tienen que quedar registradas."""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            username="admin53", password="clave12345", email="ad@m5.cl", rol="ADMIN")
        self.ea = Usuario.objects.create_user(
            username="ea53", password="clave12345", email="ea@m5.cl",
            rol="ENCARGADO_ADQUISICIONES")
        self.jp = Usuario.objects.create_user(
            username="jp53", password="clave12345", email="jp@m5.cl",
            rol="JEFE_PROYECTO")
        self.bodeguero = Usuario.objects.create_user(
            username="bod53", password="clave12345", email="b@m5.cl", rol="BODEGUERO")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra Auditada", mandante="M5", fecha_inicio=date(2026, 6, 1))
        self.material = Material.objects.create(
            nombre="Cemento", unidad_medida="saco", precio_referencia=4500)

    # --- movimientos de inventario (por señal) ---

    def test_un_movimiento_de_inventario_queda_registrado(self):
        MovimientoInventario.objects.create(
            tipo=MovimientoInventario.Tipo.ENTRADA, material=self.material,
            cantidad=50, registrado_por=self.bodeguero)
        reg = RegistroAuditoria.objects.get(accion=RegistroAuditoria.Accion.MOV_INVENTARIO)
        self.assertEqual(reg.usuario, self.bodeguero)
        self.assertIn("Cemento", reg.descripcion)
        self.assertEqual(reg.modulo, RegistroAuditoria.Modulo.INVENTARIO)

    def test_editar_un_movimiento_no_duplica_el_registro(self):
        mov = MovimientoInventario.objects.create(
            tipo=MovimientoInventario.Tipo.ENTRADA, material=self.material,
            cantidad=10, registrado_por=self.bodeguero)
        mov.observacion = "corrección"
        mov.save()
        self.assertEqual(
            RegistroAuditoria.objects.filter(
                accion=RegistroAuditoria.Accion.MOV_INVENTARIO).count(), 1)

    # --- emisión de solicitudes ---

    def test_la_emision_de_una_sm_queda_registrada(self):
        sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        SolicitudDetalle.objects.create(
            solicitud=sol, material=self.material, cantidad_solicitada=5)
        self.client.login(username="ea53", password="clave12345")
        self.client.get(reverse("solicitudes:enviar", args=[sol.pk]))
        reg = RegistroAuditoria.objects.get(accion=RegistroAuditoria.Accion.SM_EMITIDA)
        self.assertEqual(reg.usuario, self.ea)
        self.assertEqual(reg.referencia, sol.correlativo)

    def test_la_aprobacion_de_una_sm_queda_registrada_con_su_jefe(self):
        sol = SolicitudMaterial.objects.create(
            proyecto=self.proyecto, emisor=self.ea,
            estado=SolicitudMaterial.Estado.ENVIADA)
        SolicitudDetalle.objects.create(
            solicitud=sol, material=self.material, cantidad_solicitada=5)
        self.client.login(username="jp53", password="clave12345")
        self.client.get(reverse("solicitudes:resolver", args=[sol.pk, "aprobar"]))
        reg = RegistroAuditoria.objects.get(accion=RegistroAuditoria.Accion.SM_APROBADA)
        self.assertEqual(reg.usuario, self.jp)

    def test_una_sm_que_no_se_puede_enviar_no_ensucia_la_bitacora(self):
        """Excepción 1 en la práctica: si la acción no ocurre, no hay registro."""
        sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        self.client.login(username="ea53", password="clave12345")
        self.client.get(reverse("solicitudes:enviar", args=[sol.pk]))  # sin ítems
        self.assertEqual(RegistroAuditoria.objects.count(), 0)

    # --- gestión de cuentas ---

    def test_aprobar_una_cuenta_queda_registrado(self):
        pendiente = Usuario.objects.create_user(
            username="nuevo", password="x", email="n@m5.cl",
            rol="BODEGUERO", pendiente_aprobacion=True, estado=False)
        self.client.login(username="admin53", password="clave12345")
        self.client.post(reverse("usuarios:aprobar", args=[pendiente.pk]))
        reg = RegistroAuditoria.objects.get(accion=RegistroAuditoria.Accion.USUARIO_APROBADO)
        self.assertEqual(reg.usuario, self.admin)
        self.assertEqual(reg.referencia, "nuevo")
        self.assertEqual(reg.modulo, RegistroAuditoria.Modulo.USUARIOS)

    def test_activar_o_inactivar_una_cuenta_queda_registrado(self):
        self.client.login(username="admin53", password="clave12345")
        self.client.get(reverse("usuarios:cambiar_estado", args=[self.bodeguero.pk]))
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion=RegistroAuditoria.Accion.USUARIO_MODIFICADO).exists())


class BitacoraPantallaTest(TestCase):
    """La pantalla de consulta y sus filtros."""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            username="adm", password="clave12345", email="adm@m5.cl", rol="ADMIN")
        self.conta = Usuario.objects.create_user(
            username="cont", password="clave12345", email="c@m5.cl", rol="CONTABILIDAD")
        self.bodeguero = Usuario.objects.create_user(
            username="bod", password="clave12345", email="b@m5.cl", rol="BODEGUERO")

        registrar(self.admin, RegistroAuditoria.Accion.SM_EMITIDA,
                  "Emitió la solicitud de la obra norte.", "SM-000001")
        registrar(self.conta, RegistroAuditoria.Accion.FACTURA_RECIBIDA,
                  "Recibió la factura de Ferretería Andes.", "F-12345")
        registrar(self.bodeguero, RegistroAuditoria.Accion.MOV_INVENTARIO,
                  "Entrada de 50 saco de Cemento.", "Cemento")
        self.client.login(username="adm", password="clave12345")

    def _url(self, **filtros):
        base = reverse("auditoria:bitacora")
        if not filtros:
            return base
        from urllib.parse import urlencode
        return f"{base}?{urlencode(filtros)}"

    def test_la_pantalla_lista_todo_sin_filtros(self):
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["registros"]), 3)
        self.assertContains(resp, "Ferretería Andes")

    def test_filtra_por_modulo(self):
        resp = self.client.get(self._url(modulo=RegistroAuditoria.Modulo.FACTURACION))
        self.assertEqual(len(resp.context["registros"]), 1)
        self.assertEqual(resp.context["registros"][0].referencia, "F-12345")

    def test_filtra_por_accion(self):
        resp = self.client.get(self._url(accion=RegistroAuditoria.Accion.MOV_INVENTARIO))
        self.assertEqual(len(resp.context["registros"]), 1)

    def test_filtra_por_usuario(self):
        resp = self.client.get(self._url(usuario=self.conta.pk))
        self.assertEqual(len(resp.context["registros"]), 1)
        self.assertEqual(resp.context["registros"][0].usuario, self.conta)

    def test_busca_por_texto_y_referencia(self):
        resp = self.client.get(self._url(q="SM-000001"))
        self.assertEqual(len(resp.context["registros"]), 1)
        resp = self.client.get(self._url(q="cemento"))
        self.assertEqual(len(resp.context["registros"]), 1)

    def test_filtra_por_rango_de_fechas(self):
        hoy = timezone.localdate()
        resp = self.client.get(self._url(desde=hoy.isoformat(), hasta=hoy.isoformat()))
        self.assertEqual(len(resp.context["registros"]), 3)
        manana = (hoy + timedelta(days=1)).isoformat()
        resp = self.client.get(self._url(desde=manana))
        self.assertEqual(len(resp.context["registros"]), 0)

    def test_una_fecha_mal_escrita_no_rompe_la_pantalla(self):
        resp = self.client.get(self._url(desde="ayer po"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["registros"]), 3)

    def test_contabilidad_puede_revisar_la_bitacora(self):
        self.client.login(username="cont", password="clave12345")
        self.assertEqual(self.client.get(self._url()).status_code, 200)

    def test_un_rol_ajeno_no_entra_a_la_bitacora(self):
        self.client.login(username="bod", password="clave12345")
        self.assertEqual(self.client.get(self._url()).status_code, 403)

    def test_la_bitacora_no_se_puede_editar_desde_el_admin(self):
        from django.contrib.admin.sites import site
        from .models import RegistroAuditoria as R
        opciones = site._registry[R]
        self.assertFalse(opciones.has_add_permission(None))
        self.assertFalse(opciones.has_change_permission(None))
        self.assertFalse(opciones.has_delete_permission(None))
