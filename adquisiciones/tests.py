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
from .models import Cotizacion, CotizacionLinea, OrdenCompra, OrdenCompraLinea


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


# ==========================================================================
#  CU-47 — Buscando trazabilidad de material u Orden de Compra
# ==========================================================================

class TrazabilidadCU47Test(BaseAdq):
    """
    Las tres puertas de entrada (correlativo de SM, de OC, o nombre del
    material) tienen que llevar a la misma cadena, y la cadena tiene que
    mostrar hasta dónde llegó la compra.
    """

    def setUp(self):
        super().setUp()
        from inventario.models import MovimientoInventario
        from facturacion.models import Factura

        self.bodeguero = Usuario.objects.create_user(
            "bod47", password="clave12345", email="b47@m5.cl", rol="BODEGUERO")

        # Cadena completa: cotización → OC → recepción → factura
        self.cotizacion = Cotizacion.objects.create(
            solicitud=self.sm, proveedor=self.prov1, creada_por=self.ea)
        CotizacionLinea.objects.create(
            cotizacion=self.cotizacion, solicitud_detalle=self.d_a,
            valor_unitario=4500, estado=CotizacionLinea.Estado.APROBADA)
        self.orden = OrdenCompra.objects.create(
            solicitud=self.sm, proveedor=self.prov1, cotizacion=self.cotizacion,
            creada_por=self.ea)
        self.movimiento = MovimientoInventario.objects.create(
            tipo=MovimientoInventario.Tipo.ENTRADA, material=self.mat_a,
            cantidad=100, orden_compra=self.orden, registrado_por=self.bodeguero,
            guia_despacho="G-8899")
        self.factura = Factura.objects.create(
            numero="F-4477", proveedor=self.prov1, fecha_emision=date(2026, 7, 1),
            fecha_vencimiento=date(2026, 8, 1), monto_total=450000,
            registrado_por=self.ea)
        self.factura.ordenes.add(self.orden)

        self.client.login(username="ea", password="clave12345")

    def _buscar(self, q):
        return self.client.get(reverse("adquisiciones:trazabilidad"), {"q": q})

    # --- puerta 1: por solicitud ---

    def test_por_correlativo_de_sm_devuelve_la_cadena(self):
        resp = self._buscar(self.sm.correlativo)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["resultado"]["tipo"], "sm")
        cadena = resp.context["resultado"]["cadenas"][0]
        self.assertEqual(cadena["solicitud"], self.sm)
        self.assertIn(self.orden, cadena["ordenes"])
        self.assertIn(self.movimiento, cadena["movimientos"])
        self.assertIn(self.factura, cadena["facturas"])
        self.assertIn(self.cotizacion, cadena["cotizaciones"])

    # --- puerta 2: por orden de compra ---

    def test_por_correlativo_de_oc_llega_a_la_misma_cadena(self):
        resp = self._buscar(self.orden.correlativo)
        self.assertEqual(resp.context["resultado"]["tipo"], "oc")
        cadena = resp.context["resultado"]["cadenas"][0]
        self.assertEqual(cadena["solicitud"], self.sm)
        self.assertEqual(cadena["orden_buscada"], self.orden)

    def test_la_busqueda_de_oc_tolera_minusculas_y_espacios(self):
        resp = self._buscar(f"  {self.orden.correlativo.lower()}  ")
        self.assertEqual(resp.context["resultado"]["tipo"], "oc")

    # --- puerta 3: por material ---

    def test_por_nombre_de_material_encuentra_sus_solicitudes(self):
        resp = self._buscar("cemento")
        datos = resp.context["resultado"]
        self.assertEqual(datos["tipo"], "material")
        self.assertEqual(datos["materiales"][0]["material"], self.mat_a)
        self.assertEqual(datos["cadenas"][0]["solicitud"], self.sm)

    def test_el_resumen_del_material_trae_lo_pedido_y_el_stock(self):
        resp = self._buscar("cemento")
        fila = resp.context["resultado"]["materiales"][0]
        self.assertEqual(fila["pedido"], 100)
        self.assertEqual(fila["movimientos"], 1)

    # --- la pantalla ---

    def test_la_pantalla_muestra_los_cinco_eslabones(self):
        resp = self._buscar(self.sm.correlativo)
        self.assertContains(resp, "Solicitud de material")
        self.assertContains(resp, "Cotizaciones")
        self.assertContains(resp, "Órdenes de compra")
        self.assertContains(resp, "Recepción en bodega")
        self.assertContains(resp, "Facturas")
        self.assertContains(resp, self.orden.correlativo)
        self.assertContains(resp, "F-4477")
        self.assertContains(resp, "G-8899")

    def test_sin_busqueda_no_muestra_resultados_vacios(self):
        resp = self.client.get(reverse("adquisiciones:trazabilidad"))
        self.assertEqual(resp.context["resultado"]["tipo"], "vacio")
        self.assertContains(resp, "Escribe algo arriba")

    def test_algo_que_no_existe_lo_dice_con_todas_sus_letras(self):
        resp = self._buscar("OC-999999")
        self.assertEqual(resp.context["resultado"]["tipo"], "sin_resultados")
        self.assertContains(resp, "Sin resultados")

    def test_una_cadena_cortada_se_ve_donde_se_corto(self):
        """Una SM sin OC todavía: la pantalla lo dice, no deja el hueco mudo."""
        sm2 = SolicitudMaterial.objects.create(
            proyecto=self.proyecto, emisor=self.ea,
            estado=SolicitudMaterial.Estado.ENVIADA)
        SolicitudDetalle.objects.create(
            solicitud=sm2, material=self.mat_b, cantidad_solicitada=10,
            unidad_medida="barra")
        resp = self._buscar(sm2.correlativo)
        cadena = resp.context["resultado"]["cadenas"][0]
        self.assertTrue(cadena["sin_ordenes"])
        self.assertTrue(cadena["sin_factura"])
        self.assertContains(resp, "Sin orden de compra emitida")

    def test_bodega_tambien_puede_consultar_la_trazabilidad(self):
        self.client.login(username="bod47", password="clave12345")
        self.assertEqual(self._buscar(self.sm.correlativo).status_code, 200)

    def test_la_trazabilidad_exige_sesion(self):
        self.client.logout()
        self.assertNotEqual(self._buscar("cemento").status_code, 200)


# ==========================================================================
#  Cortes de flujo corregidos — cadena de estados SM / OC
# ==========================================================================

class CortesDeFlujoTest(BaseAdq):
    """
    Los tres puntos donde la cadena de estados se quedaba sin salida.
    Cada prueba fija un comportamiento que antes dejaba trabajo atascado.
    """

    def setUp(self):
        super().setUp()
        from proveedores.models import Proveedor
        self.sin_correo = Proveedor.objects.create(
            nombre="Áridos Sin Correo", rut="22222222-2", correo="")
        self.client.login(username="jp", password="clave12345")

    def _oc(self, proveedor, estado=None):
        orden = OrdenCompra.objects.create(
            solicitud=self.sm, proveedor=proveedor, creada_por=self.ea,
            estado=estado or OrdenCompra.Estado.BORRADOR)
        OrdenCompraLinea.objects.create(
            orden=orden, material=self.mat_a, descripcion="Cemento",
            cantidad=10, unidad_medida="saco", valor_unitario=5000)
        return orden

    # --- Corte 1: proveedor sin correo dejaba la OC congelada en APROBADA ---

    def test_una_oc_sin_correo_de_proveedor_igual_queda_emitida(self):
        orden = self._oc(self.sin_correo)
        self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                         {"accion": "aprobar"})
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.Estado.ENVIADA)
        self.assertIsNotNone(orden.fecha_envio)

    def test_esa_oc_sí_se_puede_recepcionar_despues(self):
        """Era el síntoma real: bodega no podía recibir el material."""
        orden = self._oc(self.sin_correo)
        self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                         {"accion": "aprobar"})
        self.client.login(username="ea", password="clave12345")
        self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                         {"accion": "recepcion", "estado": OrdenCompra.Estado.RECIBIDA})
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.Estado.RECIBIDA)

    def test_el_sistema_avisa_que_hay_que_entregarla_por_otra_via(self):
        orden = self._oc(self.sin_correo)
        resp = self.client.post(
            reverse("adquisiciones:orden_detalle", args=[orden.pk]),
            {"accion": "aprobar"}, follow=True)
        self.assertContains(resp, "no tiene correo registrado")

    # --- Corte 2: NO_RECIBIDA era terminal ---

    def test_una_oc_no_recibida_admite_la_entrega_atrasada(self):
        orden = self._oc(self.prov1, estado=OrdenCompra.Estado.NO_RECIBIDA)
        self.client.login(username="ea", password="clave12345")
        self.client.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                         {"accion": "recepcion", "estado": OrdenCompra.Estado.RECIBIDA})
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.Estado.RECIBIDA)

    def test_una_oc_no_recibida_deja_la_sm_pendiente_no_muda(self):
        from adquisiciones.views import _refrescar_estado_recepcion_sm
        self._oc(self.prov1, estado=OrdenCompra.Estado.NO_RECIBIDA)
        _refrescar_estado_recepcion_sm(self.sm)
        self.sm.refresh_from_db()
        self.assertEqual(self.sm.estado, SolicitudMaterial.Estado.OC_GENERADA)


class SolicitudRechazadaTest(BaseAdq):
    """Corte 3: una SM rechazada no se podía corregir y había que rehacerla."""

    def setUp(self):
        super().setUp()
        self.sm.estado = SolicitudMaterial.Estado.ENVIADA
        self.sm.save()

    def test_el_rechazo_guarda_el_motivo(self):
        self.client.login(username="jp", password="clave12345")
        self.client.post(reverse("solicitudes:resolver", args=[self.sm.pk, "rechazar"]),
                         {"motivo": "La cantidad de cemento no calza con el itemizado"})
        self.sm.refresh_from_db()
        self.assertEqual(self.sm.estado, SolicitudMaterial.Estado.RECHAZADA)
        self.assertIn("no calza", self.sm.motivo_rechazo)

    def test_el_encargado_ve_por_qué_se_la_rechazaron(self):
        self.client.login(username="jp", password="clave12345")
        self.client.post(reverse("solicitudes:resolver", args=[self.sm.pk, "rechazar"]),
                         {"motivo": "Falta la justificación de la partida OG-02"})
        self.client.login(username="ea", password="clave12345")
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.sm.pk]))
        self.assertContains(resp, "Falta la justificación")

    def test_puede_devolverla_a_borrador_conservando_todo(self):
        self.sm.estado = SolicitudMaterial.Estado.RECHAZADA
        self.sm.motivo_rechazo = "corregir cantidades"
        self.sm.save()
        lineas_antes = self.sm.detalles.count()
        correlativo = self.sm.correlativo

        self.client.login(username="ea", password="clave12345")
        self.client.post(reverse("solicitudes:devolver_borrador", args=[self.sm.pk]))

        self.sm.refresh_from_db()
        self.assertEqual(self.sm.estado, SolicitudMaterial.Estado.BORRADOR)
        self.assertEqual(self.sm.motivo_rechazo, "")
        self.assertEqual(self.sm.correlativo, correlativo)      # no se pierde
        self.assertEqual(self.sm.detalles.count(), lineas_antes)

    def test_solo_se_devuelve_una_rechazada(self):
        self.client.login(username="ea", password="clave12345")
        self.client.post(reverse("solicitudes:devolver_borrador", args=[self.sm.pk]))
        self.sm.refresh_from_db()
        self.assertEqual(self.sm.estado, SolicitudMaterial.Estado.ENVIADA)  # sin cambios

    def test_el_boton_aparece_en_la_pantalla(self):
        self.sm.estado = SolicitudMaterial.Estado.RECHAZADA
        self.sm.save()
        self.client.login(username="ea", password="clave12345")
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.sm.pk]))
        self.assertContains(resp, "Corregir y volver a enviar")


class LecturaEntreModulosTest(BaseAdq):
    """
    Bodega y Contabilidad llegaban desde la trazabilidad y desde la factura a
    pantallas que les devolvían 403. Ahora pueden leer lo que necesitan.
    """

    def setUp(self):
        super().setUp()
        self.bodeguero = Usuario.objects.create_user(
            "bod_lec", password="clave12345", email="b@m5.cl", rol="BODEGUERO")
        self.contador = Usuario.objects.create_user(
            "cont_lec", password="clave12345", email="c@m5.cl", rol="CONTABILIDAD")
        self.orden = OrdenCompra.objects.create(
            solicitud=self.sm, proveedor=self.prov1, creada_por=self.ea,
            estado=OrdenCompra.Estado.ENVIADA)

    def test_bodega_abre_la_solicitud_desde_la_trazabilidad(self):
        self.client.login(username="bod_lec", password="clave12345")
        self.assertEqual(
            self.client.get(reverse("solicitudes:detalle", args=[self.sm.pk])).status_code, 200)

    def test_bodega_abre_la_orden_de_compra(self):
        self.client.login(username="bod_lec", password="clave12345")
        self.assertEqual(
            self.client.get(reverse("adquisiciones:orden_detalle", args=[self.orden.pk])).status_code, 200)

    def test_contabilidad_abre_la_oc_que_tiene_que_validar(self):
        self.client.login(username="cont_lec", password="clave12345")
        self.assertEqual(
            self.client.get(reverse("adquisiciones:orden_detalle", args=[self.orden.pk])).status_code, 200)

    def test_pero_bodega_no_puede_aprobar_una_oc(self):
        """Abrir para leer no es poder actuar."""
        self.client.login(username="bod_lec", password="clave12345")
        self.client.post(reverse("adquisiciones:orden_detalle", args=[self.orden.pk]),
                         {"accion": "aprobar"})
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.estado, OrdenCompra.Estado.ENVIADA)
