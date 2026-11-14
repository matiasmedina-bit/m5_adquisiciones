"""
Trazabilidad de punta a punta, cada paso con el rol que lo hace en M5:

  Administrador: proveedor-proyecto-itemizado-JP  →  JP: SM emitida
  →  Adquisiciones: cotiza, aprueba líneas, genera OC  →  JP: rechaza y luego
  aprueba (se envía al proveedor)  →  Bodega: recepción parcial y total
  →  stock  →  Contabilidad: factura  →  cuentas por pagar  →  reportes
  →  buscador de trazabilidad (RF-46) reconstruye toda la cadena.

Ningún paso usa la cuenta del administrador salvo los que el documento le da.
"""
from datetime import date, timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from facturacion.models import Factura
from inventario.models import Material, MovimientoInventario
from proveedores.models import Proveedor
from proyectos.models import Itemizado, Proyecto
from solicitudes.models import SolicitudMaterial
from usuarios.models import Notificacion, Usuario
from .models import CotizacionLinea, OrdenCompra

E = SolicitudMaterial.Estado
OC = OrdenCompra.Estado


class CadenaCompletaTest(TestCase):
    def setUp(self):
        mk = Usuario.objects.create_user
        self.admin = mk("admin_e2e", password="x", email="admin@m-5.cl", rol="ADMIN")
        self.jp = mk("jp_e2e", password="x", email="jp@m-5.cl", rol="JEFE_PROYECTO")
        self.ea = mk("ea_e2e", password="x", email="ea@m-5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.bod = mk("bod_e2e", password="x", email="bod@m-5.cl", rol="BODEGUERO")
        self.cont = mk("cont_e2e", password="x", email="cont@m-5.cl", rol="CONTABILIDAD")
        self.cemento = Material.objects.create(nombre="Cemento Portland 25 kg", unidad_medida="saco")
        self.fierro = Material.objects.create(nombre="Fierro 12 mm", unidad_medida="barra")

    def como(self, u):
        self.client.force_login(u)

    def post(self, nombre, *args, datos=None, **kw):
        return self.client.post(reverse(nombre, args=args), datos or {}, **kw)

    def test_cadena_completa(self):
        # 1. Adquisiciones registra a los proveedores (RF-01)
        self.como(self.ea)
        for nombre, rut in (("Ferretería Andes", "11.111.111-1"), ("Aceros Sur", "12.345.678-5")):
            r = self.post("proveedores:crear", datos={
                "nombre": nombre, "rut": rut, "correo": f"{rut[:2]}@prov.cl", "telefono": "22223333",
                "direccion": "Av. Uno 100", "comuna": "Santiago", "giro": "Materiales",
                "condicion_pago": "30_DIAS", "estado": "on"})
            self.assertEqual(r.status_code, 302, r.content[:400])
        andes, sur = Proveedor.objects.get(rut="111111111"), Proveedor.objects.get(rut="123456785")

        # 2. El Administrador registra la obra con su itemizado y su JP (RF-07 a RF-10)
        self.como(self.admin)
        r = self.post("proyectos:crear", datos={
            "nombre": "Edificio Aurora", "mandante": "Inmobiliaria", "centro_costo": "CC-E2E",
            "fecha_inicio": "2026-01-01", "fecha_termino": "2027-01-01", "presupuesto_total": "1000000",
            "jefes": [self.jp.pk],
            "itemizados-TOTAL_FORMS": "1", "itemizados-INITIAL_FORMS": "0",
            "itemizados-MIN_NUM_FORMS": "0", "itemizados-MAX_NUM_FORMS": "1000",
            "itemizados-0-codigo_partida": "OG-01", "itemizados-0-descripcion": "Obra gruesa",
            "itemizados-0-unidad_medida": "un", "itemizados-0-cant_presupuestada": "500"})
        self.assertEqual(r.status_code, 302)
        obra = Proyecto.objects.get(centro_costo="CC-E2E")
        partida = Itemizado.objects.get(proyecto=obra)
        self.assertEqual(obra.estado, Proyecto.Estado.PLANIFICACION)
        self.post("proyectos:cambiar_estado", obra.pk, datos={"estado": "EJECUCION"})

        # 3. El JP crea la SM y la emite (RF-12): recibe correlativo, queda Emitida
        self.como(self.jp)
        r = self.post("solicitudes:crear", datos={
            "proyecto": obra.pk, "observaciones": "",
            "detalles-TOTAL_FORMS": "2", "detalles-INITIAL_FORMS": "0",
            "detalles-MIN_NUM_FORMS": "0", "detalles-MAX_NUM_FORMS": "1000",
            "detalles-0-material": self.cemento.pk, "detalles-0-cantidad_solicitada": "100",
            "detalles-0-partida": partida.pk, "detalles-0-nombre_libre": "Cemento",
            "detalles-1-material": self.fierro.pk, "detalles-1-cantidad_solicitada": "50",
            "detalles-1-partida": partida.pk, "detalles-1-nombre_libre": "Fierro"})
        self.assertEqual(r.status_code, 302)
        sm = SolicitudMaterial.objects.get()
        self.assertIsNone(sm.correlativo)
        self.post("solicitudes:emitir", sm.pk)
        sm.refresh_from_db()
        self.assertEqual(sm.estado, E.EMITIDA)
        self.assertTrue(sm.correlativo.startswith("SM-"))
        d_cem, d_fie = sm.detalles.get(material=self.cemento), sm.detalles.get(material=self.fierro)

        # 4. Adquisiciones la ve en la bandeja, cotiza a dos proveedores (RF-16, RF-17)
        self.como(self.ea)
        self.assertIn(sm, self.client.get(reverse("adquisiciones:cotizacion_bandeja")).context["solicitudes"])
        for prov, vu_c, vu_f in ((andes, "4500", "9900"), (sur, "4700", "9500")):
            self.post("adquisiciones:cotizacion_sm", sm.pk, datos={
                "accion": "agregar_cotizacion", "proveedor": prov.pk, "costo_despacho": "10000",
                "tiempo_entrega_dias": "3", f"vu_{d_cem.pk}": vu_c, f"vu_{d_fie.pk}": vu_f})
        # 5. Aprueba la más conveniente por material, de proveedores distintos (RF-19, RF-20)
        barata_cem = CotizacionLinea.objects.get(solicitud_detalle=d_cem, cotizacion__proveedor=andes)
        barata_fie = CotizacionLinea.objects.get(solicitud_detalle=d_fie, cotizacion__proveedor=sur)
        for linea in (barata_cem, barata_fie):
            self.post("adquisiciones:cotizacion_sm", sm.pk, datos={"accion": "aprobar_linea", "linea_id": linea.pk})
        self.assertEqual(CotizacionLinea.objects.filter(estado="DESCARTADA").count(), 2)
        sm.refresh_from_db()
        self.assertEqual(sm.estado, E.EN_COTIZACION)

        # 6. Genera un borrador de OC por proveedor (RF-21), con folios únicos
        self.post("adquisiciones:cotizacion_sm", sm.pk, datos={"accion": "generar_oc"})
        sm.refresh_from_db()
        self.assertEqual(sm.estado, E.OC_GENERADA)
        oc_andes, oc_sur = OrdenCompra.objects.get(proveedor=andes), OrdenCompra.objects.get(proveedor=sur)
        self.assertNotEqual(oc_andes.folio, oc_sur.folio)
        self.assertEqual({oc_andes.estado, oc_sur.estado}, {OC.BORRADOR})

        # 7. El JP rechaza una (RF-22), Adquisiciones la corrige (RF-23), el JP aprueba ambas
        self.como(self.jp)
        self.post("adquisiciones:orden_detalle", oc_sur.pk, datos={"accion": "rechazar", "motivo": "Revisar precio"})
        self.assertTrue(Notificacion.objects.filter(usuario=self.ea, titulo__contains="rechazada").exists())
        self.como(self.ea)
        self.post("adquisiciones:orden_detalle", oc_sur.pk, datos={"accion": "devolver_borrador"})
        self.como(self.jp)
        mail.outbox.clear()
        for oc in (oc_andes, oc_sur):
            self.post("adquisiciones:orden_detalle", oc.pk, datos={"accion": "aprobar"})
            oc.refresh_from_db()
            self.assertEqual(oc.estado, OC.ENVIADA)          # RF-25: salió por correo
        self.assertEqual(sum(1 for m in mail.outbox if m.attachments), 2)
        # RF-24: el PDF se puede exportar
        self.assertTrue(self.client.get(reverse("adquisiciones:orden_pdf", args=[oc_andes.pk])).content.startswith(b"%PDF"))

        # 8. Bodega recibe: parcial y luego total (RF-26, RF-27, RF-29)
        self.como(self.bod)
        def entrada(oc, material, cantidad):
            return self.post("inventario:entrada_crear", datos={
                "origen": "OC", "orden_compra": oc.pk, "material": material.pk,
                "cantidad": cantidad, "ubicacion": "Estante A"})
        entrada(oc_andes, self.cemento, 60)
        oc_andes.refresh_from_db()
        sm.refresh_from_db()
        self.assertEqual((oc_andes.estado, sm.estado), (OC.RECEPCION_PARCIAL, E.RECEPCION_PARCIAL))
        r = entrada(oc_andes, self.cemento, 41)                 # RF-27: más de lo pendiente
        self.assertEqual(r.status_code, 200)
        entrada(oc_andes, self.cemento, 40)
        entrada(oc_sur, self.fierro, 50)
        for oc in (oc_andes, oc_sur):
            oc.refresh_from_db()
            self.assertEqual(oc.estado, OC.RECIBIDA)
        sm.refresh_from_db()
        self.assertEqual(sm.estado, E.RECIBIDA)
        self.cemento.refresh_from_db()
        self.assertEqual(self.cemento.stock_actual, 100)
        self.assertEqual(MovimientoInventario.objects.filter(tipo="ENTRADA").count(), 3)
        # El JP recibió un aviso por cada cambio de estado de su SM (RF-15)
        estados_avisados = Notificacion.objects.filter(usuario=self.jp, titulo__startswith="Solicitud").count()
        self.assertGreaterEqual(estados_avisados, 5)

        # 9. Contabilidad registra la factura de Andes (RF-37) y aparece en cuentas por pagar (RF-39)
        self.como(self.cont)
        total = int(oc_andes.total_con_iva)
        r = self.post("facturacion:crear", datos={
            "numero": "F-100", "proveedor": andes.pk, "ordenes": [oc_andes.pk],
            "fecha_emision": date.today().isoformat(),
            "fecha_vencimiento": (date.today() + timedelta(days=30)).isoformat(),
            "monto_total": total, "observacion": ""})
        self.assertEqual(r.status_code, 302)
        factura = Factura.objects.get()
        oc_andes.refresh_from_db()
        self.assertEqual((factura.estado, oc_andes.facturada), (Factura.Estado.REGISTRADA, True))
        self.assertEqual(oc_andes.estado, OC.RECIBIDA)          # facturada es independiente
        filas = self.client.get(reverse("facturacion:cuentas_por_pagar")).context["filas"]
        self.assertEqual([f["factura"] for f in filas], [factura])

        # 10. Reportes (RF-41, RF-42, RF-44)
        self.como(self.ea)
        consumo = self.client.get(reverse("reportes:consumo"), {"proyecto": obra.pk}).context["reporte"]
        self.assertEqual(len(consumo["filas"]), 2)
        desviacion = self.client.get(reverse("reportes:desviacion"), {"proyecto": obra.pk}).context["reporte"]
        self.assertEqual(desviacion["filas"][0]["comprado"], 150)
        compras = self.client.get(reverse("reportes:compras")).context["reporte"]
        self.assertEqual({f["proveedor"] for f in compras["filas"]}, {"Ferretería Andes", "Aceros Sur"})

        # 11. Trazabilidad (RF-46): por SM, por folio de OC y por código de material
        for q in (sm.correlativo, str(oc_sur.folio), self.cemento.codigo_interno):
            res = self.client.get(reverse("adquisiciones:trazabilidad"), {"q": q}).context["resultado"]
            self.assertTrue(res["cadenas"], q)
            cadena = res["cadenas"][0]
            self.assertEqual(cadena["solicitud"], sm)                     # quién lo pidió
            self.assertEqual(len(cadena["cotizaciones"]), 2)              # cuándo se cotizó
            self.assertEqual({o.proveedor for o in cadena["ordenes"]}, {andes, sur})  # a quién se compró
            self.assertEqual({o.estado for o in cadena["ordenes"]}, {OC.RECIBIDA})    # estado final
            self.assertEqual(cadena["facturas"], [factura])


class TrazabilidadRF46Test(TestCase):
    def setUp(self):
        from proveedores.models import ProveedorMaterial
        self.jp = Usuario.objects.create_user("jp46", password="x", email="jp46@m5.cl", rol="JEFE_PROYECTO")
        self.ajeno = Usuario.objects.create_user("aj46", password="x", email="aj46@m5.cl", rol="JEFE_PROYECTO")
        self.obra = Proyecto.objects.create(nombre="Obra 46", mandante="M", fecha_inicio=date(2026, 1, 1))
        self.obra.jefes.add(self.jp)
        self.mat = Material.objects.create(nombre="Yeso", unidad_medida="saco")
        prov = Proveedor.objects.create(nombre="P46", rut="11111111-1")
        ProveedorMaterial.objects.create(proveedor=prov, codigo="YES-77", descripcion="Yeso",
                                         unidad_medida="saco", material=self.mat)
        self.sm = SolicitudMaterial.objects.create(proyecto=self.obra, emisor=self.jp, estado=E.EMITIDA)
        self.sm.detalles.create(material=self.mat, cantidad_solicitada=3)

    def _buscar(self, usuario, q):
        self.client.force_login(usuario)
        return self.client.get(reverse("adquisiciones:trazabilidad"), {"q": q}).context["resultado"]

    def test_por_codigo_interno(self):
        self.assertEqual(self._buscar(self.jp, self.mat.codigo_interno)["cadenas"][0]["solicitud"], self.sm)

    def test_por_codigo_del_proveedor(self):
        self.assertEqual(self._buscar(self.jp, "YES-77")["cadenas"][0]["solicitud"], self.sm)

    def test_el_jefe_no_ve_cadenas_de_obras_ajenas(self):
        self.assertEqual(self._buscar(self.ajeno, self.sm.correlativo)["tipo"], "sin_resultados")
        self.assertEqual(self._buscar(self.ajeno, "Yeso")["cadenas"], [])


class ReportesRF42RF43Test(TestCase):
    def setUp(self):
        self.ea = Usuario.objects.create_user("ea42", password="x", email="ea42@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.bod = Usuario.objects.create_user("bod43", password="x", email="b43@m5.cl", rol="BODEGUERO")
        self.obra = Proyecto.objects.create(nombre="Obra 42", mandante="M", fecha_inicio=date(2026, 1, 1))
        self.otra = Proyecto.objects.create(nombre="Otra 42", mandante="M", fecha_inicio=date(2026, 1, 1))
        self.mat = Material.objects.create(nombre="Pintura", unidad_medida="gl", stock_actual=10,
                                           precio_referencia=1000)

    def test_rf43_mermas_se_filtran_por_proyecto(self):
        from reportes.consultas import mermas_y_perdidas
        for obra in (self.obra, self.otra):
            MovimientoInventario.objects.create(tipo="MERMA", material=self.mat, cantidad=1,
                                                motivo="DANO", proyecto=obra, registrado_por=self.bod)
        reporte = mermas_y_perdidas(proyecto=self.obra)
        self.assertEqual([f["proyecto"] for f in reporte["filas"]], ["Obra 42"])

    def test_rf42_lo_comprado_incluye_compras_anticipadas(self):
        from adquisiciones.models import OrdenCompraLinea
        from reportes.consultas import desviacion_presupuestaria
        partida = Itemizado.objects.create(proyecto=self.obra, codigo_partida="T-1", descripcion="Term.",
                                           unidad_medida="gl", cant_presupuestada=20)
        sm = SolicitudMaterial.objects.create(proyecto=self.obra, emisor=self.ea, estado=E.EMITIDA)
        sm.detalles.create(material=self.mat, cantidad_solicitada=5, partida=partida)
        prov = Proveedor.objects.create(nombre="P42", rut="11111111-1")
        anticipada = OrdenCompra.objects.create(proyecto=self.obra, proveedor=prov,
                                                creada_por=self.ea, estado=OC.ENVIADA)
        OrdenCompraLinea.objects.create(orden=anticipada, material=self.mat, descripcion="Pintura",
                                        cantidad=7, valor_unitario=1000)
        self.assertEqual(desviacion_presupuestaria(self.obra)["filas"][0]["comprado"], 7)
