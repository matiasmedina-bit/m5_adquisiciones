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


# ==========================================================================
#  El ciclo completo, cada rol haciendo lo suyo
#
#  Estas pruebas no usan la cuenta de administrador a propósito. El admin pasa
#  por todas las vistas (así está el decorador), así que probar con ella da un
#  falso verde: el sistema puede estar impidiéndole trabajar a todo el resto y
#  la prueba igual pasa. Acá cada paso lo da el rol que lo daría en M5.
# ==========================================================================
class FlujoPorRolTest(TestCase):

    def setUp(self):
        self.jefe = Usuario.objects.create_user(
            "jefe_obra", password="clave12345", email="jefe@m5.cl", rol="JEFE_PROYECTO")
        self.ea = Usuario.objects.create_user(
            "compras", password="clave12345", email="compras@m5.cl",
            rol="ENCARGADO_ADQUISICIONES")
        self.bodega = Usuario.objects.create_user(
            "bodega", password="clave12345", email="bodega@m5.cl", rol="BODEGUERO")
        self.obra = Proyecto.objects.create(
            nombre="Edificio Los Aromos", mandante="M5",
            fecha_inicio=date(2026, 6, 1), jefe_proyecto=self.jefe)
        self.prov = Proveedor.objects.create(
            nombre="Ferretería Central", rut="11111111-1", correo="vende@prov.cl")
        self.material = Material.objects.create(
            nombre="Cemento", unidad_medida="saco", precio_referencia=4500)

    def _entrar(self, usuario):
        c = Client()
        self.assertTrue(c.login(username=usuario.username, password="clave12345"))
        return c

    # --- Lo que reportó M5: el jefe de obra no podía pedir material ---

    def test_el_jefe_de_proyecto_puede_abrir_el_formulario_de_solicitud(self):
        resp = self._entrar(self.jefe).get(reverse("solicitudes:crear"))
        self.assertEqual(resp.status_code, 200)

    def test_el_jefe_de_proyecto_emite_una_solicitud_y_queda_lista_para_cotizar(self):
        """Lo que él pide no espera visto bueno: responde por su propia obra."""
        c = self._entrar(self.jefe)
        sm = SolicitudMaterial.objects.create(
            proyecto=self.obra, emisor=self.jefe,
            estado=SolicitudMaterial.Estado.BORRADOR)
        SolicitudDetalle.objects.create(
            solicitud=sm, material=self.material, cantidad_solicitada=80,
            unidad_medida="saco")

        c.post(reverse("solicitudes:enviar", args=[sm.pk]))

        sm.refresh_from_db()
        self.assertEqual(sm.estado, SolicitudMaterial.Estado.APROBADA)

    def test_la_solicitud_del_jefe_le_aparece_a_adquisiciones(self):
        sm = SolicitudMaterial.objects.create(
            proyecto=self.obra, emisor=self.jefe,
            estado=SolicitudMaterial.Estado.BORRADOR)
        SolicitudDetalle.objects.create(
            solicitud=sm, material=self.material, cantidad_solicitada=80,
            unidad_medida="saco")
        self._entrar(self.jefe).post(reverse("solicitudes:enviar", args=[sm.pk]))

        bandeja = self._entrar(self.ea).get(reverse("adquisiciones:cotizacion_bandeja"))
        self.assertContains(bandeja, sm.correlativo)

    def test_lo_que_arma_adquisiciones_si_pasa_por_el_jefe(self):
        """Compromete plata de una obra que dirige otro, así que se le consulta."""
        c = self._entrar(self.ea)
        sm = SolicitudMaterial.objects.create(
            proyecto=self.obra, emisor=self.ea,
            estado=SolicitudMaterial.Estado.BORRADOR)
        SolicitudDetalle.objects.create(
            solicitud=sm, material=self.material, cantidad_solicitada=10,
            unidad_medida="saco")

        c.post(reverse("solicitudes:enviar", args=[sm.pk]))

        sm.refresh_from_db()
        self.assertEqual(sm.estado, SolicitudMaterial.Estado.ENVIADA)

    def test_un_jefe_no_toca_la_solicitud_de_la_obra_de_otro(self):
        otro = Usuario.objects.create_user(
            "jefe2", password="clave12345", email="j2@m5.cl", rol="JEFE_PROYECTO")
        obra_ajena = Proyecto.objects.create(
            nombre="Obra ajena", mandante="M5", fecha_inicio=date(2026, 6, 1),
            jefe_proyecto=otro)
        sm = SolicitudMaterial.objects.create(
            proyecto=obra_ajena, emisor=otro,
            estado=SolicitudMaterial.Estado.BORRADOR)
        SolicitudDetalle.objects.create(
            solicitud=sm, material=self.material, cantidad_solicitada=5,
            unidad_medida="saco")

        resp = self._entrar(self.jefe).post(reverse("solicitudes:enviar", args=[sm.pk]))

        self.assertEqual(resp.status_code, 403)
        sm.refresh_from_db()
        self.assertEqual(sm.estado, SolicitudMaterial.Estado.BORRADOR)

    # --- De la solicitud a la orden, sin pasar por el administrador ---

    def test_ciclo_completo_pedido_cotizacion_orden_y_recepcion(self):
        # 1. El jefe de obra pide
        cj = self._entrar(self.jefe)
        sm = SolicitudMaterial.objects.create(
            proyecto=self.obra, emisor=self.jefe,
            estado=SolicitudMaterial.Estado.BORRADOR)
        detalle = SolicitudDetalle.objects.create(
            solicitud=sm, material=self.material, cantidad_solicitada=80,
            unidad_medida="saco")
        cj.post(reverse("solicitudes:enviar", args=[sm.pk]))

        # 2. Adquisiciones cotiza
        ce = self._entrar(self.ea)
        ce.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]), {
            "accion": "agregar_cotizacion",
            "proveedor": self.prov.pk,
            "costo_despacho": 0,
            "tiempo_entrega_dias": 5,
            f"vu_{detalle.pk}": "4800",
        })
        linea = CotizacionLinea.objects.get(cotizacion__solicitud=sm)

        # 3. Adquisiciones elige esa oferta y genera la orden
        ce.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]),
                {"accion": "aprobar_linea", "linea_id": linea.pk})
        ce.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]),
                {"accion": "generar_oc"})

        orden = OrdenCompra.objects.get(solicitud=sm)
        self.assertEqual(orden.estado, OrdenCompra.Estado.BORRADOR)
        self.assertEqual(orden.obra, self.obra)

        # 4. El jefe de obra autoriza la compra de su obra
        cj.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                {"accion": "aprobar"})
        orden.refresh_from_db()
        self.assertIn(orden.estado,
                      (OrdenCompra.Estado.APROBADA, OrdenCompra.Estado.ENVIADA))

        # 5. Bodega ve la orden para recibir el material
        resp = self._entrar(self.bodega).get(
            reverse("adquisiciones:orden_detalle", args=[orden.pk]))
        self.assertEqual(resp.status_code, 200)

    # --- Compra anticipada: Adquisiciones se adelanta a la obra ---

    def test_adquisiciones_emite_una_compra_sin_que_nadie_se_la_pida(self):
        c = self._entrar(self.ea)
        resp = c.post(reverse("adquisiciones:orden_crear"), {
            "proyecto": self.obra.pk,
            "proveedor": self.prov.pk,
            "costo_despacho": 0,
            "form-TOTAL_FORMS": "5",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-material": self.material.pk,
            "form-0-cantidad": "200",
            "form-0-valor_unitario": "4400",
            "form-1-material": "", "form-1-cantidad": "", "form-1-valor_unitario": "",
            "form-2-material": "", "form-2-cantidad": "", "form-2-valor_unitario": "",
            "form-3-material": "", "form-3-cantidad": "", "form-3-valor_unitario": "",
            "form-4-material": "", "form-4-cantidad": "", "form-4-valor_unitario": "",
        })
        self.assertEqual(resp.status_code, 302)

        orden = OrdenCompra.objects.get(solicitud__isnull=True)
        self.assertTrue(orden.es_anticipada)
        self.assertEqual(orden.obra, self.obra)
        self.assertEqual(orden.lineas.count(), 1)
        self.assertEqual(orden.total, 200 * 4400)

    def test_la_compra_anticipada_la_autoriza_el_propio_encargado(self):
        """Nadie se la pidió, así que no hay a quién pedirle permiso."""
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea)
        OrdenCompraLinea.objects.create(
            orden=orden, material=self.material, descripcion="Cemento",
            cantidad=200, unidad_medida="saco", valor_unitario=4400)

        self._entrar(self.ea).post(
            reverse("adquisiciones:orden_detalle", args=[orden.pk]),
            {"accion": "aprobar"})

        orden.refresh_from_db()
        self.assertIn(orden.estado,
                      (OrdenCompra.Estado.APROBADA, OrdenCompra.Estado.ENVIADA))

    def test_una_orden_que_nacio_de_un_pedido_no_la_aprueba_adquisiciones(self):
        """Ahí sí hay un jefe de obra que responde por ese presupuesto."""
        sm = SolicitudMaterial.objects.create(
            proyecto=self.obra, emisor=self.jefe,
            estado=SolicitudMaterial.Estado.APROBADA)
        orden = OrdenCompra.objects.create(
            solicitud=sm, proveedor=self.prov, creada_por=self.ea)
        OrdenCompraLinea.objects.create(
            orden=orden, material=self.material, descripcion="Cemento",
            cantidad=10, unidad_medida="saco", valor_unitario=4500)

        self._entrar(self.ea).post(
            reverse("adquisiciones:orden_detalle", args=[orden.pk]),
            {"accion": "aprobar"})

        orden.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.Estado.BORRADOR)

    def test_el_pdf_de_una_compra_anticipada_sale_igual(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea)
        OrdenCompraLinea.objects.create(
            orden=orden, material=self.material, descripcion="Cemento",
            cantidad=200, unidad_medida="saco", valor_unitario=4400)

        resp = self._entrar(self.ea).get(
            reverse("adquisiciones:orden_pdf", args=[orden.pk]))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")


# ==========================================================================
#  Todo lo que el Encargado de Adquisiciones tiene que poder hacer
#
#  Una por una, las funciones de su módulo, ejecutadas con su cuenta y
#  comprobando el efecto —no que la pantalla cargue—. Si mañana alguien le
#  cierra una puerta por accidente, acá se cae.
# ==========================================================================
class EncargadoAdquisicionesTest(TestCase):

    def setUp(self):
        self.ea = Usuario.objects.create_user(
            "compras", password="clave12345", email="compras@m5.cl",
            rol="ENCARGADO_ADQUISICIONES")
        self.jefe = Usuario.objects.create_user(
            "jefe_obra", password="clave12345", email="jefe@m5.cl",
            rol="JEFE_PROYECTO")
        self.obra = Proyecto.objects.create(
            nombre="Edificio Central", mandante="M5",
            fecha_inicio=date(2026, 6, 1), jefe_proyecto=self.jefe)
        self.prov = Proveedor.objects.create(
            nombre="Ferretería Central", rut="11111111-1", correo="vende@prov.cl")
        self.otro_prov = Proveedor.objects.create(
            nombre="Comercial Sur", rut="12345678-5", correo="sur@prov.cl")
        self.material = Material.objects.create(
            nombre="Cemento", unidad_medida="saco", precio_referencia=4500)

        self.c = Client()
        self.assertTrue(self.c.login(username="compras", password="clave12345"))

    def _solicitud_lista_para_cotizar(self):
        sm = SolicitudMaterial.objects.create(
            proyecto=self.obra, emisor=self.jefe,
            estado=SolicitudMaterial.Estado.APROBADA)
        detalle = SolicitudDetalle.objects.create(
            solicitud=sm, material=self.material, cantidad_solicitada=100,
            unidad_medida="saco")
        return sm, detalle

    # ---------------------------------------------------------------- cotizar

    def test_ve_la_bandeja_de_solicitudes_por_cotizar(self):
        sm, _ = self._solicitud_lista_para_cotizar()
        resp = self.c.get(reverse("adquisiciones:cotizacion_bandeja"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, sm.correlativo)

    def test_abre_la_pantalla_para_cotizar_una_solicitud(self):
        sm, _ = self._solicitud_lista_para_cotizar()
        resp = self.c.get(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_registra_la_cotizacion_de_un_proveedor(self):
        sm, detalle = self._solicitud_lista_para_cotizar()
        self.c.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]), {
            "accion": "agregar_cotizacion", "proveedor": self.prov.pk,
            "costo_despacho": 15000, "tiempo_entrega_dias": 5,
            f"vu_{detalle.pk}": "4800",
        })
        cot = Cotizacion.objects.get(solicitud=sm, proveedor=self.prov)
        self.assertEqual(cot.lineas.count(), 1)
        self.assertEqual(cot.valor_total, 100 * 4800 + 15000)

    def test_compara_dos_proveedores_para_el_mismo_material(self):
        sm, detalle = self._solicitud_lista_para_cotizar()
        for prov, valor in ((self.prov, "4800"), (self.otro_prov, "4600")):
            self.c.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]), {
                "accion": "agregar_cotizacion", "proveedor": prov.pk,
                "costo_despacho": 0, "tiempo_entrega_dias": 3,
                f"vu_{detalle.pk}": valor,
            })
        self.assertEqual(sm.cotizaciones.count(), 2)

    def test_elige_una_oferta_y_descarta_la_otra(self):
        sm, detalle = self._solicitud_lista_para_cotizar()
        for prov, valor in ((self.prov, "4800"), (self.otro_prov, "4600")):
            self.c.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]), {
                "accion": "agregar_cotizacion", "proveedor": prov.pk,
                "costo_despacho": 0, "tiempo_entrega_dias": 3,
                f"vu_{detalle.pk}": valor,
            })
        barata = CotizacionLinea.objects.get(cotizacion__proveedor=self.otro_prov)
        cara = CotizacionLinea.objects.get(cotizacion__proveedor=self.prov)

        self.c.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]),
                    {"accion": "aprobar_linea", "linea_id": barata.pk})

        barata.refresh_from_db(); cara.refresh_from_db()
        self.assertEqual(barata.estado, CotizacionLinea.Estado.APROBADA)
        self.assertEqual(cara.estado, CotizacionLinea.Estado.DESCARTADA)

    def test_genera_la_orden_de_compra_desde_lo_cotizado(self):
        sm, detalle = self._solicitud_lista_para_cotizar()
        self.c.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]), {
            "accion": "agregar_cotizacion", "proveedor": self.prov.pk,
            "costo_despacho": 0, "tiempo_entrega_dias": 3,
            f"vu_{detalle.pk}": "4800",
        })
        linea = CotizacionLinea.objects.get(cotizacion__solicitud=sm)
        self.c.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]),
                    {"accion": "aprobar_linea", "linea_id": linea.pk})

        self.c.post(reverse("adquisiciones:cotizacion_sm", args=[sm.pk]),
                    {"accion": "generar_oc"})

        orden = OrdenCompra.objects.get(solicitud=sm)
        self.assertEqual(orden.proveedor, self.prov)
        self.assertEqual(orden.lineas.count(), 1)
        self.assertEqual(orden.obra, self.obra)

    # --------------------------------------------------------------- órdenes

    def test_lista_las_ordenes_y_filtra_por_estado(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea)
        resp = self.c.get(reverse("adquisiciones:orden_lista"))
        self.assertContains(resp, orden.correlativo)
        resp = self.c.get(reverse("adquisiciones:orden_lista"), {"estado": "BORRADOR"})
        self.assertContains(resp, orden.correlativo)

    def test_abre_el_formulario_de_compra_anticipada(self):
        resp = self.c.get(reverse("adquisiciones:orden_crear"))
        self.assertEqual(resp.status_code, 200)

    def test_emite_una_compra_anticipada(self):
        resp = self.c.post(reverse("adquisiciones:orden_crear"), {
            "proyecto": self.obra.pk, "proveedor": self.prov.pk,
            "costo_despacho": 5000,
            "form-TOTAL_FORMS": "5", "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
            "form-0-material": self.material.pk,
            "form-0-cantidad": "300", "form-0-valor_unitario": "4300",
            **{f"form-{i}-{campo}": ""
               for i in range(1, 5)
               for campo in ("material", "cantidad", "valor_unitario")},
        })
        self.assertEqual(resp.status_code, 302)
        orden = OrdenCompra.objects.get(solicitud__isnull=True)
        self.assertEqual(orden.total, 300 * 4300 + 5000)

    def test_no_emite_una_compra_sin_materiales(self):
        resp = self.c.post(reverse("adquisiciones:orden_crear"), {
            "proyecto": self.obra.pk, "proveedor": self.prov.pk,
            "costo_despacho": 0,
            "form-TOTAL_FORMS": "5", "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
            **{f"form-{i}-{campo}": ""
               for i in range(5)
               for campo in ("material", "cantidad", "valor_unitario")},
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(OrdenCompra.objects.exists())

    def test_abre_el_detalle_de_una_orden(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea)
        resp = self.c.get(reverse("adquisiciones:orden_detalle", args=[orden.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_devuelve_a_borrador_una_orden_rechazada(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea,
            estado=OrdenCompra.Estado.RECHAZADA, motivo_rechazo="Muy caro")
        self.c.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                    {"accion": "devolver_borrador"})
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.Estado.BORRADOR)
        self.assertEqual(orden.motivo_rechazo, "")

    def test_corrige_los_valores_de_una_orden_rechazada(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea,
            estado=OrdenCompra.Estado.RECHAZADA, motivo_rechazo="Revisar precio")
        linea = OrdenCompraLinea.objects.create(
            orden=orden, material=self.material, descripcion="Cemento",
            cantidad=100, unidad_medida="saco", valor_unitario=5000)

        resp = self.c.post(reverse("adquisiciones:orden_editar", args=[orden.pk]), {
            "form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000",
            "form-0-id": linea.pk, "form-0-cantidad": "90",
            "form-0-valor_unitario": "4700",
        })
        self.assertEqual(resp.status_code, 302)
        linea.refresh_from_db()
        self.assertEqual(linea.valor_unitario, 4700)
        self.assertEqual(linea.cantidad, 90)

    def test_registra_el_estado_de_recepcion(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea,
            estado=OrdenCompra.Estado.ENVIADA)
        OrdenCompraLinea.objects.create(
            orden=orden, material=self.material, descripcion="Cemento",
            cantidad=100, unidad_medida="saco", valor_unitario=4500)

        self.c.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                    {"accion": "recepcion", "estado": OrdenCompra.Estado.RECIBIDA})

        orden.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.Estado.RECIBIDA)

    def test_descarga_el_pdf_de_la_orden(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea)
        OrdenCompraLinea.objects.create(
            orden=orden, material=self.material, descripcion="Cemento",
            cantidad=100, unidad_medida="saco", valor_unitario=4500)
        resp = self.c.get(reverse("adquisiciones:orden_pdf", args=[orden.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")

    # ---------------------------------------------------------- trazabilidad

    def test_rastrea_una_orden_por_su_correlativo(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea)
        resp = self.c.get(reverse("adquisiciones:trazabilidad"),
                          {"q": orden.correlativo})
        self.assertEqual(resp.status_code, 200)

    def test_rastrea_un_material_por_su_nombre(self):
        resp = self.c.get(reverse("adquisiciones:trazabilidad"), {"q": "Cemento"})
        self.assertEqual(resp.status_code, 200)

    # ------------------------------------------- proveedores, su herramienta

    def test_registra_un_proveedor_nuevo(self):
        resp = self.c.post(reverse("proveedores:crear"), {
            "nombre": "Aceros del Sur", "rut": "22.222.222-2",
            "correo": "ventas@aceros.cl", "telefono": "+56 9 1111 1111",
            "condicion_pago": "30_DIAS", "estado": "on",
        })
        self.assertIn(resp.status_code, (200, 302))
        self.assertTrue(Proveedor.objects.filter(nombre="Aceros del Sur").exists())

    def test_edita_un_proveedor(self):
        resp = self.c.post(reverse("proveedores:editar", args=[self.prov.pk]), {
            "nombre": "Ferretería Central SpA", "rut": self.prov.rut,
            "correo": "nuevo@prov.cl", "telefono": "",
            "condicion_pago": "60_DIAS", "estado": "on",
        })
        self.assertIn(resp.status_code, (200, 302))
        self.prov.refresh_from_db()
        self.assertEqual(self.prov.nombre, "Ferretería Central SpA")

    def test_agrega_un_material_al_catalogo_del_proveedor(self):
        resp = self.c.post(
            reverse("proveedores:material_agregar", args=[self.prov.pk]), {
                "codigo": "CEM-001", "descripcion": "Cemento Portland 25 kg",
                "unidad_medida": "saco", "precio": "4800", "disponible": "on",
            })
        self.assertIn(resp.status_code, (200, 302))
        self.assertTrue(self.prov.materiales.filter(codigo="CEM-001").exists())

    def test_descarga_la_plantilla_de_catalogo(self):
        resp = self.c.get(reverse("proveedores:catalogo_plantilla"))
        self.assertEqual(resp.status_code, 200)

    def test_carga_el_catalogo_del_proveedor_por_excel(self):
        from io import BytesIO
        from openpyxl import Workbook
        from django.core.files.uploadedfile import SimpleUploadedFile

        libro = Workbook(); hoja = libro.active
        hoja.append(["Código", "Descripción", "Unidad", "Precio"])
        hoja.append(["FIE-001", "Fierro estriado 8 mm", "un", 3990])
        hoja.append(["ARE-001", "Arena gruesa", "m3", 18990])
        buffer = BytesIO(); libro.save(buffer); buffer.seek(0)

        resp = self.c.post(
            reverse("proveedores:catalogo_cargar", args=[self.prov.pk]),
            {"archivo": SimpleUploadedFile(
                "catalogo.xlsx", buffer.getvalue(),
                content_type=("application/vnd.openxmlformats-officedocument"
                              ".spreadsheetml.sheet"))})

        self.assertIn(resp.status_code, (200, 302))
        self.assertEqual(self.prov.materiales.count(), 2)

    def test_inactiva_un_proveedor_sin_borrarlo(self):
        self.c.post(reverse("proveedores:inactivar", args=[self.otro_prov.pk]))
        self.otro_prov.refresh_from_db()
        self.assertFalse(self.otro_prov.estado)

    # --------------------------------- lo que NO le toca, para que quede fijo

    def test_no_aprueba_una_orden_que_pidio_una_obra(self):
        """Esa la autoriza el jefe de esa obra, que responde por el presupuesto."""
        sm, _ = self._solicitud_lista_para_cotizar()
        orden = OrdenCompra.objects.create(
            solicitud=sm, proveedor=self.prov, creada_por=self.ea)
        self.c.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                    {"accion": "aprobar"})
        orden.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.Estado.BORRADOR)

    def test_si_autoriza_la_compra_que_el_mismo_decidio(self):
        orden = OrdenCompra.objects.create(
            proyecto=self.obra, proveedor=self.prov, creada_por=self.ea)
        OrdenCompraLinea.objects.create(
            orden=orden, material=self.material, descripcion="Cemento",
            cantidad=50, unidad_medida="saco", valor_unitario=4400)
        self.c.post(reverse("adquisiciones:orden_detalle", args=[orden.pk]),
                    {"accion": "aprobar"})
        orden.refresh_from_db()
        self.assertIn(orden.estado,
                      (OrdenCompra.Estado.APROBADA, OrdenCompra.Estado.ENVIADA))
