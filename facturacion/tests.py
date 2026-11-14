"""
Pruebas del módulo de Facturación (Incremento 2).
RF-40 recepción de factura + marca OC como facturada ·
RF-41 bloqueo por diferencia de monto · RF-42 desbloqueo por Administración ·
RF-43 cuentas por pagar · RF-44 export CSV.
"""
from datetime import date, timedelta
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from usuarios.models import Usuario
from proveedores.models import Proveedor
from proyectos.models import Proyecto
from inventario.models import Material
from solicitudes.models import SolicitudMaterial
from adquisiciones.models import OrdenCompra, OrdenCompraLinea
from .models import Factura


class FacturaTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cont = Usuario.objects.create_user("cont", password="clave12345", email="c@m5.cl", rol="CONTABILIDAD")
        self.admin = Usuario.objects.create_user("adm", password="clave12345", email="a@m5.cl", rol="ADMIN")
        self.ea = Usuario.objects.create_user("ea", password="x", email="e@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.prov = Proveedor.objects.create(nombre="Prov", rut="11111111-1")
        self.proy = Proyecto.objects.create(nombre="Obra", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.mat = Material.objects.create(nombre="Cemento", unidad_medida="saco")
        self.sm = SolicitudMaterial.objects.create(proyecto=self.proy, emisor=self.ea)
        self.oc = OrdenCompra.objects.create(solicitud=self.sm, proveedor=self.prov,
                                             creada_por=self.ea, estado=OrdenCompra.Estado.ENVIADA)
        OrdenCompraLinea.objects.create(orden=self.oc, material=self.mat, descripcion="Cemento",
                                        cantidad=100, valor_unitario=5000)  # OC: neto 500.000, con IVA 595.000

    def _crear(self, monto):
        self.client.login(username=Usuario.objects.get(username="cont").email, password="clave12345")
        return self.client.post(reverse("facturacion:crear"), {
            "numero": f"F-{monto}", "proveedor": self.prov.pk, "ordenes": [self.oc.pk],
            "fecha_emision": date.today().isoformat(),
            "fecha_vencimiento": (date.today() + timedelta(days=30)).isoformat(),
            "monto_total": monto, "observacion": "",
        })

    def test_rf40_monto_ok_marca_oc_facturada(self):
        self._crear(595000)
        f = Factura.objects.get()
        self.oc.refresh_from_db()
        self.assertEqual(f.estado, Factura.Estado.REGISTRADA)
        self.assertTrue(self.oc.facturada)

    def test_rf41_diferencia_excesiva_bloquea(self):
        self._crear(720000)  # +21% sobre 595.000 > 5%
        f = Factura.objects.get()
        self.oc.refresh_from_db()
        self.assertEqual(f.estado, Factura.Estado.BLOQUEADA)
        self.assertFalse(self.oc.facturada)

    def test_rf42_admin_desbloquea(self):
        self._crear(720000)
        f = Factura.objects.get()
        self.client.login(username=Usuario.objects.get(username="adm").email, password="clave12345")
        self.client.post(reverse("facturacion:desbloquear", args=[f.pk]),
                         {"justificacion": "Diferencia autorizada por contrato."})
        f.refresh_from_db(); self.oc.refresh_from_db()
        self.assertEqual(f.estado, Factura.Estado.REGISTRADA)
        self.assertTrue(self.oc.facturada)

    def test_rf43_cuentas_por_pagar_ordena_por_vencimiento(self):
        self._crear(595000)
        self.client.login(username=Usuario.objects.get(username="cont").email, password="clave12345")
        resp = self.client.get(reverse("facturacion:cuentas_por_pagar"))
        self.assertEqual(resp.status_code, 200)

    def test_rf44_export_csv(self):
        self._crear(595000)
        self.client.login(username=Usuario.objects.get(username="cont").email, password="clave12345")
        resp = self.client.get(reverse("facturacion:export_csv"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])
        self.assertIn(b"F-595000", resp.content)

    def test_paginas_renderizan(self):
        self._crear(720000)  # deja una factura bloqueada
        f = Factura.objects.get()
        self.client.login(username=Usuario.objects.get(username="cont").email, password="clave12345")
        for url in [reverse("facturacion:lista"), reverse("facturacion:crear"),
                    reverse("facturacion:cuentas_por_pagar"),
                    reverse("facturacion:detalle", args=[f.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.client.login(username=Usuario.objects.get(username="adm").email, password="clave12345")
        self.assertEqual(
            self.client.get(reverse("facturacion:detalle", args=[f.pk])).status_code, 200)


class ToleranciaFacturaRF37Test(FacturaTest):
    """RF-37: el monto de la factura (con IVA) se compara con el total de la OC con IVA."""

    def test_factura_correcta_con_iva_no_se_bloquea(self):
        self._crear(595000)
        self.assertEqual(Factura.objects.get().estado, Factura.Estado.REGISTRADA)

    def test_justo_en_la_tolerancia_pasa_y_sobre_ella_se_bloquea(self):
        self._crear(624750)            # +5,00 %
        self.assertEqual(Factura.objects.get(numero="F-624750").estado, Factura.Estado.REGISTRADA)
        self.oc.facturada = False
        self.oc.save()
        self._crear(624751)            # +5,0002 %
        self.assertEqual(Factura.objects.get(numero="F-624751").estado, Factura.Estado.BLOQUEADA)

    def test_la_tolerancia_es_parametrizable(self):
        from usuarios.models import ParametrosSistema
        p = ParametrosSistema.actuales()
        p.tolerancia_factura_pct = 25
        p.save()
        self._crear(720000)
        self.assertEqual(Factura.objects.get().estado, Factura.Estado.REGISTRADA)

    def test_cu38_vincula_solo_oc_enviadas_no_facturadas(self):
        from .forms import FacturaForm
        borrador = OrdenCompra.objects.create(proveedor=self.prov, creada_por=self.ea,
                                              proyecto=self.proy)
        opciones = list(FacturaForm().fields["ordenes"].queryset)
        self.assertIn(self.oc, opciones)
        self.assertNotIn(borrador, opciones)

    def test_cu41_exc1_sin_facturas_no_baja_un_csv_vacio(self):
        self.client.login(username=Usuario.objects.get(username="cont").email, password="clave12345")
        resp = self.client.get(reverse("facturacion:export_csv"), follow=True)
        self.assertContains(resp, "No hay facturas registradas")
