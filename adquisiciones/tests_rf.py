"""
Reglas de los Módulos 4 y 5 contrastadas con el documento (RF-16 a RF-25, RF-35).
"""
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inventario.models import Material
from proveedores.models import Proveedor
from proyectos.models import Itemizado, Proyecto
from solicitudes.models import SolicitudDetalle, SolicitudMaterial
from usuarios.models import Notificacion, Usuario
from .models import Cotizacion, CotizacionLinea, OrdenCompra, OrdenCompraLinea

E = SolicitudMaterial.Estado
OC = OrdenCompra.Estado


class BaseRF(TestCase):
    def setUp(self):
        self.ea = Usuario.objects.create_user("ea_rf", password="x", email="ea@m5.cl",
                                              rol="ENCARGADO_ADQUISICIONES")
        self.jp = Usuario.objects.create_user("jp_rf", password="x", email="jp@m5.cl",
                                              rol="JEFE_PROYECTO")
        self.bod = Usuario.objects.create_user("bod_rf", password="x", email="b@m5.cl",
                                               rol="BODEGUERO")
        self.obra = Proyecto.objects.create(nombre="Obra RF", mandante="M",
                                            fecha_inicio=date(2026, 1, 1),
                                            estado=Proyecto.Estado.EJECUCION)
        self.obra.jefes.add(self.jp)
        self.partida = Itemizado.objects.create(proyecto=self.obra, codigo_partida="1",
                                                descripcion="x", unidad_medida="saco",
                                                cant_presupuestada=1000)
        self.prov = Proveedor.objects.create(nombre="Prov RF", rut="11111111-1",
                                             correo="p@rf.cl", direccion="Calle 1", giro="G")
        self.mat = Material.objects.create(nombre="Cemento RF", unidad_medida="saco")
        self.sm = SolicitudMaterial.objects.create(proyecto=self.obra, emisor=self.jp,
                                                   estado=E.EMITIDA)
        self.det = SolicitudDetalle.objects.create(solicitud=self.sm, material=self.mat,
                                                   cantidad_solicitada=10, partida=self.partida)

    def como(self, u):
        self.client.force_login(u)

    def cotizar_y_aprobar(self, proveedor=None, vu=5000):
        cot = Cotizacion.objects.create(solicitud=self.sm, proveedor=proveedor or self.prov,
                                        creada_por=self.ea, costo_despacho=1000)
        linea = CotizacionLinea.objects.create(cotizacion=cot, solicitud_detalle=self.det,
                                               valor_unitario=vu)
        self.como(self.ea)
        self.client.post(reverse("adquisiciones:cotizacion_sm", args=[self.sm.pk]),
                         {"accion": "aprobar_linea", "linea_id": linea.pk})
        return linea

    def oc(self, estado=OC.BORRADOR, recibido=0):
        orden = OrdenCompra.objects.create(solicitud=self.sm, proveedor=self.prov,
                                           creada_por=self.ea, estado=estado)
        OrdenCompraLinea.objects.create(orden=orden, material=self.mat, descripcion="Cemento",
                                        cantidad=10, unidad_medida="saco", valor_unitario=5000,
                                        cantidad_recibida=recibido)
        return orden


class BandejaRF16Test(BaseRF):
    def test_rf16_solo_emitidas_y_de_la_mas_antigua_a_la_mas_reciente(self):
        nueva = SolicitudMaterial.objects.create(proyecto=self.obra, emisor=self.jp, estado=E.EMITIDA)
        SolicitudMaterial.objects.filter(pk=nueva.pk).update(fecha=timezone.now() + timedelta(days=1))
        borrador = SolicitudMaterial.objects.create(proyecto=self.obra, emisor=self.jp)
        self.como(self.ea)
        resp = self.client.get(reverse("adquisiciones:cotizacion_bandeja"))
        lista = list(resp.context["solicitudes"])
        self.assertEqual(lista, [self.sm, nueva])
        self.assertNotIn(borrador, lista)

    def test_cu16_bandeja_vacia_lo_dice(self):
        SolicitudMaterial.objects.all().update(estado=E.RECIBIDA)
        self.como(self.ea)
        self.assertContains(self.client.get(reverse("adquisiciones:cotizacion_bandeja")),
                            "No hay solicitudes pendientes")


class CotizacionRF17a20Test(BaseRF):
    def test_rf17_cotizacion_nace_pendiente_y_exige_valor(self):
        self.como(self.ea)
        self.client.post(reverse("adquisiciones:cotizacion_sm", args=[self.sm.pk]), {
            "accion": "agregar_cotizacion", "proveedor": self.prov.pk,
            "costo_despacho": 0, "tiempo_entrega_dias": 2, f"vu_{self.det.pk}": "4500"})
        cot = Cotizacion.objects.get()
        self.assertEqual(cot.estado, Cotizacion.Estado.PENDIENTE)

    def test_rf18_total_es_cantidad_por_valor_mas_despacho(self):
        linea = self.cotizar_y_aprobar(vu=4500)
        self.assertEqual(linea.cotizacion.valor_total, 10 * 4500 + 1000)

    def test_rf20_al_aprobar_todo_pasa_a_en_cotizacion_y_avisa_al_jefe(self):
        self.cotizar_y_aprobar()
        self.sm.refresh_from_db()
        self.assertEqual(self.sm.estado, E.EN_COTIZACION)
        self.assertTrue(Notificacion.objects.filter(usuario=self.jp, titulo__contains="cotización").exists())


class GenerarOcRF21Test(BaseRF):
    def test_rf21_copia_datos_del_proveedor_incluida_la_direccion(self):
        self.cotizar_y_aprobar()
        self.client.post(reverse("adquisiciones:cotizacion_sm", args=[self.sm.pk]), {"accion": "generar_oc"})
        orden = OrdenCompra.objects.get()
        self.assertEqual((orden.estado, orden.proveedor_razon_social), (OC.BORRADOR, "Prov RF"))
        self.assertIn("Calle 1", orden.proveedor_direccion)
        self.assertTrue(orden.folio)

    def test_cu21_exc1_sin_direccion_del_proveedor_no_se_genera(self):
        sin_dir = Proveedor.objects.create(nombre="Sin Dir", rut="22222222-2", correo="s@d.cl")
        self.cotizar_y_aprobar(proveedor=sin_dir)
        resp = self.client.post(reverse("adquisiciones:cotizacion_sm", args=[self.sm.pk]),
                                {"accion": "generar_oc"}, follow=True)
        self.assertFalse(OrdenCompra.objects.exists())
        self.assertContains(resp, "dirección de Sin Dir")

    def test_rf21_folio_no_editable(self):
        self.assertFalse(OrdenCompra._meta.get_field("folio").editable)
        self.assertFalse(OrdenCompra._meta.get_field("correlativo").editable)

    def test_rf21_folios_unicos_y_correlativos(self):
        a, b = self.oc(), self.oc()
        self.assertEqual(b.folio, a.folio + 1)


class AprobacionRF22Test(BaseRF):
    def test_rf22_rechazo_notifica_a_quien_genero_la_oc(self):
        orden = self.oc()
        self.como(self.jp)
        self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                         {"accion": "rechazar", "motivo": "Precio alto"})
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OC.RECHAZADA)
        self.assertIn("Precio alto", Notificacion.objects.get(usuario=self.ea).mensaje)

    def test_jefe_ajeno_no_aprueba(self):
        ajeno = Usuario.objects.create_user("jp_aj", password="x", email="aj@m5.cl", rol="JEFE_PROYECTO")
        orden = self.oc()
        self.como(ajeno)
        resp = self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]), {"accion": "aprobar"})
        self.assertEqual(resp.status_code, 403)

    def test_bodega_y_contabilidad_no_aprueban(self):
        cont = Usuario.objects.create_user("cont_rf", password="x", email="c@m5.cl", rol="CONTABILIDAD")
        orden = self.oc()
        for u in (self.bod, cont):
            self.como(u)
            self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]), {"accion": "aprobar"})
            orden.refresh_from_db()
            self.assertEqual(orden.estado, OC.BORRADOR)


class PdfRF24Test(BaseRF):
    def test_cu24_exc1_borrador_no_se_exporta(self):
        orden = self.oc()
        self.como(self.ea)
        resp = self.client.get(reverse("adquisiciones:orden_pdf", args=[orden.pk]))
        self.assertRedirects(resp, reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                             fetch_redirect_response=False)

    def test_rf24_aprobada_se_exporta_con_pdf(self):
        orden = self.oc(OC.ENVIADA)
        self.como(self.jp)
        resp = self.client.get(reverse("adquisiciones:orden_pdf", args=[orden.pk]))
        self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_jefe_ajeno_no_descarga_el_pdf(self):
        ajeno = Usuario.objects.create_user("jp_pdf", password="x", email="jpdf@m5.cl", rol="JEFE_PROYECTO")
        orden = self.oc(OC.ENVIADA)
        self.como(ajeno)
        self.assertEqual(self.client.get(reverse("adquisiciones:orden_pdf", args=[orden.pk])).status_code, 403)


class EnvioRF25Test(BaseRF):
    def test_rf25_al_aprobar_se_envia_con_pdf_y_queda_enviada(self):
        from django.core import mail
        orden = self.oc()
        self.como(self.jp)
        self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]), {"accion": "aprobar"})
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OC.ENVIADA)
        correo = [m for m in mail.outbox if "p@rf.cl" in m.to][0]
        self.assertEqual(correo.attachments[0][2], "application/pdf")


class RecepcionRF35Test(BaseRF):
    def _recepcion(self, orden, estado):
        self.como(self.ea)
        return self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                                {"accion": "recepcion", "estado": estado}, follow=True)

    def test_cu36_exc1_parcial_sin_cantidades_se_bloquea(self):
        orden = self.oc(OC.ENVIADA)
        resp = self._recepcion(orden, OC.RECEPCION_PARCIAL)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OC.ENVIADA)
        self.assertContains(resp, "tiene que haber cantidades recibidas")

    def test_parcial_con_cantidades_avisa_al_jefe_con_cantidades(self):
        orden = self.oc(OC.ENVIADA, recibido=4)
        self._recepcion(orden, OC.RECEPCION_PARCIAL)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OC.RECEPCION_PARCIAL)
        aviso = Notificacion.objects.filter(usuario=self.jp, titulo__contains=orden.correlativo).first()
        self.assertIn("4 de 10", aviso.mensaje)

    def test_recibida_exige_todo_recibido(self):
        orden = self.oc(OC.ENVIADA, recibido=4)
        self._recepcion(orden, OC.RECIBIDA)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OC.ENVIADA)

    def test_no_recibida_con_material_ya_recibido_no_corresponde(self):
        orden = self.oc(OC.ENVIADA, recibido=4)
        self._recepcion(orden, OC.NO_RECIBIDA)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OC.ENVIADA)

    def test_no_recibida_sin_entregas(self):
        orden = self.oc(OC.ENVIADA)
        self._recepcion(orden, OC.NO_RECIBIDA)
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OC.NO_RECIBIDA)

    def test_rf36_sm_muestra_la_recepcion_de_cada_oc(self):
        self.oc(OC.RECIBIDA, recibido=10)
        self.oc(OC.ENVIADA)
        self.como(self.jp)
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.sm.pk]))
        self.assertContains(resp, "Recibida")
        self.assertContains(resp, "Pendiente de recepción")


class PreciosOcultosABodegaTest(BaseRF):
    def test_rf26_bodega_ve_la_oc_sin_precios(self):
        orden = self.oc(OC.ENVIADA)
        self.como(self.bod)
        resp = self.client.get(reverse("adquisiciones:orden_detalle", args=[orden.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "V. unitario")
        self.assertNotContains(resp, "TOTAL")
