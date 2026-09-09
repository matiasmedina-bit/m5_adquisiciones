"""
Pruebas del módulo de Adquisiciones (Incremento 2).
RF-19 bandeja · RF-21 valor total · RF-22 aprobar línea · RF-23 generar OC ·
RF-24 aprobar/rechazar OC · RF-25 editar OC rechazada.
"""
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse

from usuarios.models import Usuario
from proveedores.models import Proveedor
from proyectos.models import Proyecto
from inventario.models import Material
from solicitudes.models import SolicitudMaterial, SolicitudDetalle
from .models import Cotizacion, CotizacionLinea, OrdenCompra


class BaseAdq(TestCase):
    def setUp(self):
        self.client = Client()
        self.ea = Usuario.objects.create_user("ea", password="clave12345",
                                              email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.jefe = Usuario.objects.create_user("jp", password="clave12345",
                                                email="jp@m5.cl", rol="JEFE_PROYECTO")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra", mandante="M", fecha_inicio=date(2026, 6, 1), jefe_proyecto=self.jefe)
        self.prov1 = Proveedor.objects.create(nombre="Prov 1", rut="11111111-1", correo="p1@x.cl")
        self.prov2 = Proveedor.objects.create(nombre="Prov 2", rut="12345678-5", correo="p2@x.cl")
        self.mat_a = Material.objects.create(nombre="Cemento", unidad_medida="saco", precio_referencia=4500)
        self.mat_b = Material.objects.create(nombre="Fierro", unidad_medida="barra", precio_referencia=8900)
        self.sm = SolicitudMaterial.objects.create(
            proyecto=self.proyecto, emisor=self.ea, estado=SolicitudMaterial.Estado.APROBADA)
        self.d_a = SolicitudDetalle.objects.create(
            solicitud=self.sm, material=self.mat_a, cantidad_solicitada=100, unidad_medida="saco")
        self.d_b = SolicitudDetalle.objects.create(
            solicitud=self.sm, material=self.mat_b, cantidad_solicitada=50, unidad_medida="barra")


class CotizacionTest(BaseAdq):

    def test_rf19_bandeja_muestra_sm_aprobadas(self):
        self.client.login(username="ea", password="clave12345")
        resp = self.client.get(reverse("adquisiciones:cotizacion_bandeja"))
        self.assertContains(resp, self.sm.correlativo)

    def test_rf21_valor_total_cotizacion(self):
        cot = Cotizacion.objects.create(solicitud=self.sm, proveedor=self.prov1,
                                        creada_por=self.ea, costo_despacho=10000)
        CotizacionLinea.objects.create(cotizacion=cot, solicitud_detalle=self.d_a, valor_unitario=5000)
        CotizacionLinea.objects.create(cotizacion=cot, solicitud_detalle=self.d_b, valor_unitario=9000)
        # 100*5000 + 50*9000 + 10000 = 500000 + 450000 + 10000
        self.assertEqual(cot.valor_total, 960000)

    def test_rf22_aprobar_linea_descarta_las_demas(self):
        c1 = Cotizacion.objects.create(solicitud=self.sm, proveedor=self.prov1, creada_por=self.ea)
        c2 = Cotizacion.objects.create(solicitud=self.sm, proveedor=self.prov2, creada_por=self.ea)
        l1 = CotizacionLinea.objects.create(cotizacion=c1, solicitud_detalle=self.d_a, valor_unitario=5000)
        l2 = CotizacionLinea.objects.create(cotizacion=c2, solicitud_detalle=self.d_a, valor_unitario=4800)
        l2.aprobar()
        l1.refresh_from_db(); l2.refresh_from_db()
        self.assertEqual(l2.estado, CotizacionLinea.Estado.APROBADA)
        self.assertEqual(l1.estado, CotizacionLinea.Estado.DESCARTADA)

    def test_rf23_generar_oc_una_por_proveedor(self):
        self.client.login(username="ea", password="clave12345")
        c1 = Cotizacion.objects.create(solicitud=self.sm, proveedor=self.prov1, creada_por=self.ea)
        c2 = Cotizacion.objects.create(solicitud=self.sm, proveedor=self.prov2, creada_por=self.ea)
        CotizacionLinea.objects.create(cotizacion=c1, solicitud_detalle=self.d_a, valor_unitario=5000).aprobar()
        CotizacionLinea.objects.create(cotizacion=c2, solicitud_detalle=self.d_b, valor_unitario=9000).aprobar()
        self.client.post(reverse("adquisiciones:cotizacion_sm", args=[self.sm.pk]),
                         {"accion": "generar_oc"})
        self.sm.refresh_from_db()
        self.assertEqual(OrdenCompra.objects.filter(solicitud=self.sm).count(), 2)
        self.assertEqual(self.sm.estado, SolicitudMaterial.Estado.OC_GENERADA)


class OrdenCompraTest(BaseAdq):

    def _oc_borrador(self):
        c1 = Cotizacion.objects.create(solicitud=self.sm, proveedor=self.prov1, creada_por=self.ea)
        cl = CotizacionLinea.objects.create(cotizacion=c1, solicitud_detalle=self.d_a, valor_unitario=5000)
        cl.aprobar()
        CotizacionLinea.objects.create(cotizacion=c1, solicitud_detalle=self.d_b, valor_unitario=9000).aprobar()
        from .views import _generar_ordenes_compra
        return _generar_ordenes_compra(self.sm, self.ea)[0]

    def test_rf23_correlativo_automatico(self):
        oc = self._oc_borrador()
        self.assertTrue(oc.correlativo.startswith("OC-"))

    def test_rf24_jefe_aprueba_y_se_envia(self):
        oc = self._oc_borrador()
        self.client.login(username="jp", password="clave12345")
        self.client.post(reverse("adquisiciones:orden_detalle", args=[oc.pk]), {"accion": "aprobar"})
        oc.refresh_from_db()
        self.assertEqual(oc.estado, OrdenCompra.Estado.ENVIADA)  # proveedor tiene correo

    def test_rf24_rechazo_exige_motivo(self):
        oc = self._oc_borrador()
        self.client.login(username="jp", password="clave12345")
        self.client.post(reverse("adquisiciones:orden_detalle", args=[oc.pk]),
                         {"accion": "rechazar", "motivo": ""})
        oc.refresh_from_db()
        self.assertEqual(oc.estado, OrdenCompra.Estado.BORRADOR)
        self.client.post(reverse("adquisiciones:orden_detalle", args=[oc.pk]),
                         {"accion": "rechazar", "motivo": "Precio fuera de mercado"})
        oc.refresh_from_db()
        self.assertEqual(oc.estado, OrdenCompra.Estado.RECHAZADA)

    def test_rf25_devolver_rechazada_a_borrador(self):
        oc = self._oc_borrador()
        oc.estado = OrdenCompra.Estado.RECHAZADA
        oc.save()
        self.client.login(username="ea", password="clave12345")
        self.client.post(reverse("adquisiciones:orden_detalle", args=[oc.pk]),
                         {"accion": "devolver_borrador"})
        oc.refresh_from_db()
        self.assertEqual(oc.estado, OrdenCompra.Estado.BORRADOR)

    def test_paginas_renderizan(self):
        """Smoke test: las plantillas del módulo se renderizan sin error."""
        self.client.login(username="ea", password="clave12345")
        # con la SM aún en APROBADA se puede abrir la pantalla de cotización
        for url in [
            reverse("adquisiciones:cotizacion_bandeja"),
            reverse("adquisiciones:cotizacion_sm", args=[self.sm.pk]),
            reverse("adquisiciones:orden_lista"),
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        oc = self._oc_borrador()
        self.assertEqual(
            self.client.get(reverse("adquisiciones:orden_detalle", args=[oc.pk])).status_code, 200)
        # OC rechazada -> pantalla de edición
        oc.estado = OrdenCompra.Estado.RECHAZADA
        oc.save()
        self.assertEqual(
            self.client.get(reverse("adquisiciones:orden_editar", args=[oc.pk])).status_code, 200)
