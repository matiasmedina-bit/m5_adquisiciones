"""
RF-50 (tipo de operación en la bitácora) y descargas protegidas de archivos.
"""
import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from inventario.models import Material, MovimientoInventario, PrestamoHerramienta
from proyectos.models import ArchivoProyecto, Proyecto, TipoDocumento
from usuarios.models import Usuario
from .models import RegistroAuditoria, registrar

Op = RegistroAuditoria.Operacion


class OperacionRF50Test(TestCase):
    def setUp(self):
        self.bod = Usuario.objects.create_user("bod50", password="x", email="b50@m5.cl", rol="BODEGUERO")
        self.jp = Usuario.objects.create_user("jp50", password="x", email="j50@m5.cl", rol="JEFE_PROYECTO")
        self.mat = Material.objects.create(nombre="Taladro", unidad_medida="u", tipo="HERRAMIENTA",
                                           stock_actual=1, codigo_activo="T-1")

    def test_cada_registro_tiene_usuario_fecha_hora_y_operacion(self):
        reg = registrar(self.bod, RegistroAuditoria.Accion.OC_APROBADA, "x", "1")
        self.assertEqual((reg.usuario, reg.operacion), (self.bod, Op.EDITAR))
        self.assertIsNotNone(reg.fecha)

    def test_movimiento_de_inventario_es_crear(self):
        MovimientoInventario.objects.create(tipo="ENTRADA", material=self.mat, cantidad=1,
                                            registrado_por=self.bod)
        self.assertEqual(RegistroAuditoria.objects.get().operacion, Op.CREAR)

    def test_devolucion_de_prestamo_es_editar(self):
        obra = Proyecto.objects.create(nombre="O50", mandante="M", fecha_inicio=date(2026, 1, 1))
        p = PrestamoHerramienta.objects.create(
            herramienta=self.mat, jefe_proyecto=self.jp, proyecto=obra, registrado_por=self.bod,
            fecha_salida=date.today(), fecha_devolucion_esperada=date.today())
        p.estado = PrestamoHerramienta.Estado.DEVUELTA
        p.save()
        self.assertEqual(
            list(RegistroAuditoria.objects.order_by("fecha", "pk").values_list("operacion", flat=True)),
            [Op.CREAR, Op.EDITAR])

    def test_eliminar_cuenta_es_eliminar(self):
        reg = registrar(self.bod, RegistroAuditoria.Accion.USUARIO_ELIMINADO, "x")
        self.assertEqual(reg.operacion, Op.ELIMINAR)

    def test_todas_las_acciones_tienen_operacion(self):
        for accion in RegistroAuditoria.Accion.values:
            self.assertIn(accion, RegistroAuditoria.OPERACION_DE, accion)

    def test_la_bitacora_filtra_por_operacion(self):
        registrar(self.bod, RegistroAuditoria.Accion.USUARIO_ELIMINADO, "borrado")
        registrar(self.bod, RegistroAuditoria.Accion.OC_EMITIDA, "emitida")
        self.client.force_login(Usuario.objects.create_user("ad50", password="x", email="a50@m5.cl", rol="ADMIN"))
        resp = self.client.get(reverse("auditoria:bitacora"), {"operacion": "ELIMINAR"})
        self.assertEqual([r.descripcion for r in resp.context["registros"]], ["borrado"])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DescargaProtegidaTest(TestCase):
    def setUp(self):
        self.jp = Usuario.objects.create_user("jp_d", password="x", email="jd@m5.cl", rol="JEFE_PROYECTO")
        self.ajeno = Usuario.objects.create_user("jp_aj_d", password="x", email="jad@m5.cl", rol="JEFE_PROYECTO")
        self.bod = Usuario.objects.create_user("bod_d", password="x", email="bd@m5.cl", rol="BODEGUERO")
        obra = Proyecto.objects.create(nombre="O-D", mandante="M", fecha_inicio=date(2026, 1, 1))
        obra.jefes.add(self.jp)
        tipo = TipoDocumento.objects.get(nombre="Contrato")
        self.archivo = ArchivoProyecto.objects.create(
            proyecto=obra, tipo=tipo, nombre="Contrato", subido_por=self.jp,
            archivo=SimpleUploadedFile("contrato.pdf", b"%PDF-1.4 secreto"))
        self.url = reverse("proyectos:archivo_descargar", args=[self.archivo.pk])

    def _get(self):
        resp = self.client.get(self.url)
        if resp.status_code != 200:
            return resp.status_code, b""
        contenido = resp.getvalue()
        if getattr(resp, "file_to_stream", None):
            resp.file_to_stream.close()
        return resp.status_code, contenido

    def test_sin_sesion_no_se_descarga(self):
        self.assertEqual(self._get()[0], 302)

    def test_jefe_ajeno_y_bodega_no_descargan(self):
        for u in (self.ajeno, self.bod):
            self.client.force_login(u)
            self.assertEqual(self._get()[0], 403)

    def test_el_jefe_de_la_obra_descarga(self):
        self.client.force_login(self.jp)
        self.assertEqual(self._get(), (200, b"%PDF-1.4 secreto"))

    @override_settings(ARCHIVOS_X_ACCEL=True)
    def test_con_nginx_se_delega_con_x_accel(self):
        self.client.force_login(self.jp)
        resp = self.client.get(self.url)
        self.assertTrue(resp["X-Accel-Redirect"].startswith("/protegido/proyectos/"))
