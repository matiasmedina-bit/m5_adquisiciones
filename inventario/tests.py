"""
Pruebas del módulo de Inventario / Bodega (Incremento 2).
RF-32 stock en tiempo real · RF-29 validación de cantidad recibida ·
RF-33/34 préstamos · RF-35 mermas · RF-37 alerta de stock mínimo.
"""
from datetime import date, timedelta
from django.test import TestCase, Client
from django.urls import reverse

from usuarios.models import Usuario
from proveedores.models import Proveedor
from proyectos.models import Proyecto
from solicitudes.models import SolicitudMaterial, SolicitudDetalle
from adquisiciones.models import OrdenCompra, OrdenCompraLinea
from .models import Material, MovimientoInventario, PrestamoHerramienta
from .forms import EntradaForm


class StockTiempoRealTest(TestCase):
    """RF-32: cada entrada/salida ajusta el stock de inmediato."""

    def setUp(self):
        self.user = Usuario.objects.create_user("bod", password="x", email="b@m5.cl", rol="BODEGUERO")
        self.mat = Material.objects.create(nombre="Cemento", unidad_medida="saco",
                                           stock_actual=100, precio_referencia=4500)

    def test_entrada_suma_stock(self):
        MovimientoInventario.objects.create(
            tipo=MovimientoInventario.Tipo.ENTRADA, material=self.mat,
            cantidad=40, registrado_por=self.user)
        self.mat.refresh_from_db()
        self.assertEqual(self.mat.stock_actual, 140)

    def test_salida_resta_stock(self):
        MovimientoInventario.objects.create(
            tipo=MovimientoInventario.Tipo.SALIDA, material=self.mat,
            cantidad=30, registrado_por=self.user)
        self.mat.refresh_from_db()
        self.assertEqual(self.mat.stock_actual, 70)

    def test_merma_resta_stock(self):
        MovimientoInventario.objects.create(
            tipo=MovimientoInventario.Tipo.MERMA, material=self.mat,
            cantidad=10, motivo="DANO", registrado_por=self.user)
        self.mat.refresh_from_db()
        self.assertEqual(self.mat.stock_actual, 90)

    def test_rf37_bajo_stock_minimo(self):
        self.mat.stock_minimo = 120
        self.mat.save()
        self.assertTrue(self.mat.bajo_stock_minimo)
        self.mat.stock_minimo = 50
        self.mat.save()
        self.assertFalse(self.mat.bajo_stock_minimo)


class EntradaOCTest(TestCase):
    """RF-29: la cantidad recibida no puede superar la de la OC."""

    def setUp(self):
        self.ea = Usuario.objects.create_user("ea", password="x", email="e@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.prov = Proveedor.objects.create(nombre="P", rut="11111111-1")
        self.proy = Proyecto.objects.create(nombre="Obra", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.mat = Material.objects.create(nombre="Cemento", unidad_medida="saco")
        self.sm = SolicitudMaterial.objects.create(proyecto=self.proy, emisor=self.ea)
        self.oc = OrdenCompra.objects.create(solicitud=self.sm, proveedor=self.prov,
                                             creada_por=self.ea, estado=OrdenCompra.Estado.ENVIADA)
        OrdenCompraLinea.objects.create(orden=self.oc, material=self.mat, descripcion="Cemento",
                                        cantidad=50, valor_unitario=4600)

    def test_cantidad_excedida_es_invalida(self):
        form = EntradaForm(data={
            "origen": "OC", "orden_compra": self.oc.pk, "material": self.mat.pk,
            "cantidad": "80", "ubicacion": "A1", "observacion": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)

    def test_cantidad_dentro_de_la_oc_es_valida(self):
        form = EntradaForm(data={
            "origen": "OC", "orden_compra": self.oc.pk, "material": self.mat.pk,
            "cantidad": "50", "ubicacion": "A1", "observacion": "",
        })
        self.assertTrue(form.is_valid(), form.errors)


class PrestamoTest(TestCase):
    """RF-33 / RF-34: préstamo y devolución de herramientas."""

    def setUp(self):
        self.client = Client()
        self.bod = Usuario.objects.create_user("bod", password="clave12345", email="b@m5.cl", rol="BODEGUERO")
        self.jefe = Usuario.objects.create_user("jp", password="x", email="j@m5.cl", rol="JEFE_PROYECTO")
        self.proy = Proyecto.objects.create(nombre="Obra", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.herr = Material.objects.create(nombre="Taladro", unidad_medida="unidad",
                                            tipo="HERRAMIENTA", stock_actual=3, codigo_activo="H-1")
        self.client.login(username="bod", password="clave12345")

    def test_paginas_bodega_renderizan(self):
        for name in ["bodega_panel", "movimiento_lista", "entrada_crear", "salida_crear",
                     "merma_crear", "devolucion_proveedor_crear", "prestamo_lista", "prestamo_crear"]:
            resp = self.client.get(reverse(f"inventario:{name}"))
            self.assertEqual(resp.status_code, 200, name)

    def test_prestamo_descuenta_una_unidad_y_devolucion_la_repone(self):
        self.client.post(reverse("inventario:prestamo_crear"), {
            "herramienta": self.herr.pk, "jefe_proyecto": self.jefe.pk, "proyecto": self.proy.pk,
            "fecha_salida": date.today().isoformat(),
            "fecha_devolucion_esperada": (date.today() + timedelta(days=10)).isoformat(),
        })
        self.herr.refresh_from_db()
        self.assertEqual(self.herr.stock_actual, 2)
        prestamo = PrestamoHerramienta.objects.get()
        self.client.get(reverse("inventario:prestamo_devolver", args=[prestamo.pk]))
        prestamo.refresh_from_db(); self.herr.refresh_from_db()
        self.assertEqual(prestamo.estado, PrestamoHerramienta.Estado.DEVUELTA)
        self.assertEqual(self.herr.stock_actual, 3)
