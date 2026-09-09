"""
Pruebas unitarias del módulo de Solicitudes de Material (CU-11, 12, 14, 16, 17).
"""
import tempfile
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from usuarios.models import Usuario
from proyectos.models import Proyecto, Itemizado
from inventario.models import Material
from .models import SolicitudMaterial, SolicitudDetalle, SolicitudAdjunto
from .forms import SolicitudDetalleForm, SolicitudAdjuntoForm


class SolicitudModelTest(TestCase):

    def setUp(self):
        self.ea = Usuario.objects.create_user(
            username="ea", password="x", email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra A", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.material = Material.objects.create(
            nombre="Clavos", unidad_medida="kg", precio_referencia=1500)

    def test_correlativo_autogenerado(self):
        s = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        self.assertTrue(s.correlativo.startswith("SM-"))

    def test_solicitud_borrador_es_editable(self):
        s = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        self.assertTrue(s.editable)

    def test_detalle_hereda_unidad_del_material(self):
        s = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        d = SolicitudDetalle.objects.create(solicitud=s, material=self.material, cantidad_solicitada=10)
        self.assertEqual(d.unidad_medida, "kg")


class SolicitudFlujoTest(TestCase):
    """CU-16: flujo de estados (enviar / aprobar / rechazar)."""

    def setUp(self):
        self.client = Client()
        self.ea = Usuario.objects.create_user(
            username="ea", password="clave12345", email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.jp = Usuario.objects.create_user(
            username="jp", password="clave12345", email="jp@m5.cl", rol="JEFE_PROYECTO")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra B", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.material = Material.objects.create(
            nombre="Pintura", unidad_medida="gl", precio_referencia=12000)
        self.sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)

    def test_no_se_puede_enviar_sin_items(self):
        self.client.login(username="ea", password="clave12345")
        self.client.get(reverse("solicitudes:enviar", args=[self.sol.pk]))
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, SolicitudMaterial.Estado.BORRADOR)

    def test_enviar_con_items_cambia_estado(self):
        SolicitudDetalle.objects.create(solicitud=self.sol, material=self.material, cantidad_solicitada=5)
        self.client.login(username="ea", password="clave12345")
        self.client.get(reverse("solicitudes:enviar", args=[self.sol.pk]))
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, SolicitudMaterial.Estado.ENVIADA)

    def test_jefe_aprueba_solicitud_enviada(self):
        SolicitudDetalle.objects.create(solicitud=self.sol, material=self.material, cantidad_solicitada=5)
        self.sol.estado = SolicitudMaterial.Estado.ENVIADA
        self.sol.save()
        self.client.login(username="jp", password="clave12345")
        self.client.get(reverse("solicitudes:resolver", args=[self.sol.pk, "aprobar"]))
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, SolicitudMaterial.Estado.APROBADA)


class SolicitudProyectoFinalizadoTest(TestCase):
    """PU-06 (CU-10): el sistema bloquea generar solicitudes en proyecto finalizado."""

    def setUp(self):
        self.proyecto_fin = Proyecto.objects.create(
            nombre="Obra Terminada", mandante="M", fecha_inicio=date(2025, 1, 1),
            estado=Proyecto.Estado.FINALIZADO)

    def test_form_rechaza_proyecto_finalizado(self):
        from .forms import SolicitudForm
        form = SolicitudForm(data={"proyecto": self.proyecto_fin.pk, "observaciones": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("proyecto", form.errors)

    def test_proyecto_finalizado_no_esta_en_opciones(self):
        from .forms import SolicitudForm
        form = SolicitudForm()
        self.assertNotIn(self.proyecto_fin, list(form.fields["proyecto"].queryset))


class JustificacionItemizadoTest(TestCase):
    """RF-16: si la cantidad supera el saldo de la partida, se exige justificación."""

    def setUp(self):
        self.ea = Usuario.objects.create_user(
            username="ea", password="x", email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra J", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.material = Material.objects.create(
            nombre="Cemento", unidad_medida="saco", precio_referencia=4500)
        self.partida = Itemizado.objects.create(
            proyecto=self.proyecto, codigo_partida="P-01", descripcion="Hormigón",
            unidad_medida="saco", cant_presupuestada=100, cant_ejecutada=90)  # saldo 10
        self.sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)

    def _data(self, cantidad, justificacion=""):
        return {
            "material": self.material.pk,
            "cantidad_solicitada": cantidad,
            "unidad_medida": "saco",
            "partida": self.partida.pk,
            "justificacion": justificacion,
            "nombre_libre": "",
        }

    def test_exceso_sin_justificacion_es_invalido(self):
        form = SolicitudDetalleForm(data=self._data(50), solicitud=self.sol)
        self.assertFalse(form.is_valid())
        self.assertIn("justificacion", form.errors)

    def test_exceso_con_justificacion_es_valido(self):
        form = SolicitudDetalleForm(
            data=self._data(50, "Rectificación de metraje en terreno"), solicitud=self.sol)
        self.assertTrue(form.is_valid(), form.errors)

    def test_dentro_del_saldo_no_requiere_justificacion(self):
        form = SolicitudDetalleForm(data=self._data(5), solicitud=self.sol)
        self.assertTrue(form.is_valid(), form.errors)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AdjuntosSolicitudTest(TestCase):
    """RF-17: adjuntar hasta 3 archivos PDF/JPG (máx 5 MB) a una solicitud."""

    def setUp(self):
        self.client = Client()
        self.ea = Usuario.objects.create_user(
            username="ea", password="clave12345", email="ea@m5.cl",
            rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea", password="clave12345")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra A", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)

    def test_formato_no_permitido_es_rechazado(self):
        f = SimpleUploadedFile("nota.txt", b"hola", content_type="text/plain")
        form = SolicitudAdjuntoForm(data={"nombre": "x"}, files={"archivo": f})
        self.assertFalse(form.is_valid())

    def test_archivo_pdf_valido(self):
        f = SimpleUploadedFile("plano.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        form = SolicitudAdjuntoForm(data={"nombre": "Plano"}, files={"archivo": f})
        self.assertTrue(form.is_valid(), form.errors)

    def test_maximo_3_adjuntos(self):
        for i in range(3):
            SolicitudAdjunto.objects.create(
                solicitud=self.sol, subido_por=self.ea,
                archivo=SimpleUploadedFile(f"p{i}.jpg", b"data", content_type="image/jpeg"))
        f = SimpleUploadedFile("p4.jpg", b"data", content_type="image/jpeg")
        self.client.post(reverse("solicitudes:detalle", args=[self.sol.pk]),
                         {"accion": "adjuntar", "archivo": f, "nombre": "cuarto"})
        self.assertEqual(self.sol.adjuntos.count(), 3)

    def test_detalle_renderiza_en_varios_estados(self):
        for estado in ("BORRADOR", "APROBADA", "EN_COTIZACION", "OC_GENERADA",
                       "RECEPCION_PARCIAL", "RECIBIDA", "RECHAZADA"):
            self.sol.estado = estado
            self.sol.save(update_fields=["estado"])
            resp = self.client.get(reverse("solicitudes:detalle", args=[self.sol.pk]))
            self.assertEqual(resp.status_code, 200, estado)
