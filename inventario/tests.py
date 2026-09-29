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
from decimal import Decimal
from usuarios.models import ParametrosSistema
from .forms import MaterialForm


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
        self.client.post(reverse("inventario:prestamo_devolver", args=[prestamo.pk]))
        prestamo.refresh_from_db(); self.herr.refresh_from_db()
        self.assertEqual(prestamo.estado, PrestamoHerramienta.Estado.DEVUELTA)
        self.assertEqual(self.herr.stock_actual, 3)


# ==========================================================================
#  Incremento 4 — CU-61, CU-62, CU-63 (catálogo maestro)
# ==========================================================================

class CatalogoMaestroCU61Test(TestCase):
    """CU-61 (RF-58): clasificación explícita material / herramienta."""

    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            "adm61", password="clave12345", email="a61@m5.cl", rol="ADMIN")
        self.client.login(username="adm61", password="clave12345")

    def _datos(self, **extra):
        datos = {"nombre": "Ladrillo fiscal", "tipo": "CONSUMIBLE",
                 "categoria": "ALBANILERIA", "unidad_medida": "un",
                 "stock_actual": "0", "stock_minimo": "", "ubicacion": "",
                 "precio_referencia": "350", "codigo_activo": "",
                 "fecha_vencimiento": "", "activo": "on"}
        datos.update(extra)
        return datos

    def test_el_selector_no_viene_preseleccionado(self):
        form = MaterialForm()
        self.assertEqual(form.fields["tipo"].choices[0][0], "")

    # --- Excepción 1: sin clasificación no se registra ---

    def test_sin_clasificacion_no_se_registra(self):
        form = MaterialForm(data=self._datos(tipo=""))
        self.assertFalse(form.is_valid())
        self.assertIn("tipo", form.errors)
        self.assertIn("material consumible o una herramienta", str(form.errors["tipo"]))

    def test_con_clasificacion_se_registra(self):
        form = MaterialForm(data=self._datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_una_herramienta_exige_codigo_de_activo(self):
        """Sin código no se puede prestar, que es para lo que existe."""
        form = MaterialForm(data=self._datos(tipo="HERRAMIENTA", codigo_activo=""))
        self.assertFalse(form.is_valid())
        self.assertIn("codigo_activo", form.errors)

    def test_una_herramienta_no_lleva_stock_minimo(self):
        form = MaterialForm(data=self._datos(
            tipo="HERRAMIENTA", codigo_activo="HER-9", stock_minimo="50"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["stock_minimo"], 0)

    def test_el_stock_minimo_vacio_hereda_el_valor_configurado(self):
        p = ParametrosSistema.actuales()
        p.stock_minimo_defecto = Decimal("15")
        p.save()
        material = Material.objects.create(
            nombre="Con minimo heredado", unidad_medida="un", tipo="CONSUMIBLE")
        self.assertEqual(material.stock_minimo, Decimal("15"))


class CodigoInternoCU62Test(TestCase):
    """CU-62 (RF-59): código interno único, independiente del código del proveedor."""

    def test_se_asigna_solo_al_crear(self):
        m = Material.objects.create(nombre="Arena", unidad_medida="m3", tipo="CONSUMIBLE")
        self.assertTrue(m.codigo_interno)
        self.assertTrue(m.codigo_interno.startswith("MAT-"))

    def test_las_herramientas_llevan_su_propia_serie(self):
        h = Material.objects.create(nombre="Taladro", unidad_medida="un", tipo="HERRAMIENTA")
        self.assertTrue(h.codigo_interno.startswith("HER-"))

    def test_los_codigos_no_se_repiten(self):
        codigos = {Material.objects.create(
            nombre=f"Material {i}", unidad_medida="un", tipo="CONSUMIBLE").codigo_interno
            for i in range(10)}
        self.assertEqual(len(codigos), 10)

    def test_el_codigo_no_cambia_al_editar(self):
        """Se imprime en órdenes de compra y guías: tiene que ser estable."""
        m = Material.objects.create(nombre="Estable", unidad_medida="un", tipo="CONSUMIBLE")
        original = m.codigo_interno
        m.nombre = "Renombrado"
        m.precio_referencia = 9999
        m.save()
        m.refresh_from_db()
        self.assertEqual(m.codigo_interno, original)

    # --- Excepción 1: colisión ---

    def test_una_colision_avanza_al_siguiente_libre(self):
        primero = Material.objects.create(nombre="A", unidad_medida="un", tipo="CONSUMIBLE")
        # Se ocupa a mano el correlativo que vendría después
        siguiente = int(primero.codigo_interno.split("-")[1]) + 1
        Material.objects.create(nombre="Intruso", unidad_medida="un", tipo="CONSUMIBLE",
                                codigo_interno=f"MAT-{siguiente:05d}")
        tercero = Material.objects.create(nombre="C", unidad_medida="un", tipo="CONSUMIBLE")
        self.assertNotEqual(tercero.codigo_interno, f"MAT-{siguiente:05d}")
        self.assertEqual(Material.objects.filter(
            codigo_interno=tercero.codigo_interno).count(), 1)

    def test_es_independiente_del_codigo_del_proveedor(self):
        """El proveedor puede llamarle CEM-25 a lo que internamente es MAT-00001."""
        from proveedores.models import Proveedor, ProveedorMaterial
        material = Material.objects.create(
            nombre="Cemento 25kg", unidad_medida="saco", tipo="CONSUMIBLE")
        proveedor = Proveedor.objects.create(
            nombre="Ferretería", rut="11111111-1", correo="f@x.cl")
        oferta = ProveedorMaterial.objects.create(
            proveedor=proveedor, codigo="CEM-25", descripcion="Cemento 25kg",
            unidad_medida="saco", precio=5000, material=material)
        self.assertNotEqual(oferta.codigo, material.codigo_interno)


class BuscadorCatalogoCU63Test(TestCase):
    """CU-63 (RF-60): búsqueda y filtros del catálogo maestro."""

    def setUp(self):
        self.client = Client()
        self.bodeguero = Usuario.objects.create_user(
            "bod63", password="clave12345", email="b63@m5.cl", rol="BODEGUERO")
        self.cemento = Material.objects.create(
            nombre="Cemento Portland", unidad_medida="saco", tipo="CONSUMIBLE",
            categoria="CEMENTOS", ubicacion="Estante A1", stock_actual=100,
            precio_referencia=5000)
        self.taladro = Material.objects.create(
            nombre="Taladro percutor", unidad_medida="un", tipo="HERRAMIENTA",
            categoria="HERRAMIENTA_ELECTRICA", ubicacion="Pañol", stock_actual=2,
            codigo_activo="HER-001")
        self.agotado = Material.objects.create(
            nombre="Clavos 2 pulgadas", unidad_medida="kg", tipo="CONSUMIBLE",
            categoria="ALBANILERIA", ubicacion="Estante A1", stock_actual=0)
        self.client.login(username="bod63", password="clave12345")

    def _buscar(self, **filtros):
        return self.client.get(reverse("inventario:lista"), filtros)

    def test_busca_por_codigo_interno(self):
        resp = self._buscar(q=self.cemento.codigo_interno)
        self.assertEqual(list(resp.context["materiales"]), [self.cemento])

    def test_busca_por_descripcion(self):
        resp = self._buscar(q="taladro")
        self.assertEqual(list(resp.context["materiales"]), [self.taladro])

    def test_filtra_por_categoria(self):
        resp = self._buscar(categoria="CEMENTOS")
        self.assertEqual(list(resp.context["materiales"]), [self.cemento])

    def test_filtra_por_ubicacion(self):
        resp = self._buscar(ubicacion="Estante A1")
        nombres = {m.nombre for m in resp.context["materiales"]}
        self.assertEqual(nombres, {"Cemento Portland", "Clavos 2 pulgadas"})

    def test_filtra_por_disponibilidad(self):
        con_stock = {m.nombre for m in self._buscar(estado="disponible").context["materiales"]}
        self.assertNotIn("Clavos 2 pulgadas", con_stock)
        agotados = {m.nombre for m in self._buscar(estado="agotado").context["materiales"]}
        self.assertEqual(agotados, {"Clavos 2 pulgadas"})

    def test_separa_materiales_de_herramientas(self):
        materiales = {m.nombre for m in self._buscar(tipo="CONSUMIBLE").context["materiales"]}
        self.assertNotIn("Taladro percutor", materiales)
        herramientas = {m.nombre for m in self._buscar(tipo="HERRAMIENTA").context["materiales"]}
        self.assertEqual(herramientas, {"Taladro percutor"})

    def test_los_filtros_se_combinan(self):
        resp = self._buscar(categoria="ALBANILERIA", ubicacion="Estante A1")
        self.assertEqual(list(resp.context["materiales"]), [self.agotado])

    # --- Excepción 1 ---

    def test_sin_coincidencias_muestra_mensaje_no_tabla_vacia(self):
        resp = self._buscar(q="destornillador sónico")
        self.assertEqual(len(resp.context["materiales"]), 0)
        self.assertContains(resp, "Ningún ítem coincide")

    def test_el_listado_muestra_codigo_y_categoria(self):
        resp = self._buscar()
        self.assertContains(resp, self.cemento.codigo_interno)
        self.assertContains(resp, "Cementos y morteros")
