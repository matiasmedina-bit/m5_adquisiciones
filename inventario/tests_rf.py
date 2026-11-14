"""
Reglas de Bodega (RF-26 a RF-34) y del Catálogo Maestro (RF-58 a RF-60).
"""
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from adquisiciones.models import OrdenCompra, OrdenCompraLinea
from proveedores.models import Proveedor
from proyectos.models import Proyecto
from usuarios.models import Notificacion, Usuario
from .forms import DevolucionProveedorForm, EntradaForm, MaterialForm, MermaForm, SalidaForm
from .models import Material, MovimientoInventario, PrestamoHerramienta

T = MovimientoInventario.Tipo


class BaseBodega(TestCase):
    def setUp(self):
        self.bod = Usuario.objects.create_user("bod6", password="x", email="b6@m5.cl", rol="BODEGUERO")
        self.ea = Usuario.objects.create_user("ea6", password="x", email="e6@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.jp = Usuario.objects.create_user("jp6", password="x", email="j6@m5.cl", rol="JEFE_PROYECTO")
        self.admin = Usuario.objects.create_user("ad6", password="x", email="a6@m5.cl", rol="ADMIN")
        self.obra = Proyecto.objects.create(nombre="Obra 6", mandante="M", fecha_inicio=date(2026, 1, 1),
                                            estado=Proyecto.Estado.EJECUCION)
        self.obra.jefes.add(self.jp)
        self.prov = Proveedor.objects.create(nombre="Prov 6", rut="11111111-1", direccion="x")
        self.mat = Material.objects.create(nombre="Arena", unidad_medida="m3", stock_actual=10)
        self.oc = OrdenCompra.objects.create(proyecto=self.obra, proveedor=self.prov,
                                             creada_por=self.ea, estado=OrdenCompra.Estado.ENVIADA)
        self.linea = OrdenCompraLinea.objects.create(orden=self.oc, material=self.mat, descripcion="Arena",
                                                     cantidad=20, valor_unitario=15000)

    def mov(self, tipo, cantidad, **kw):
        return MovimientoInventario.objects.create(tipo=tipo, material=self.mat, cantidad=cantidad,
                                                   registrado_por=self.bod, **kw)


class StockRF29Test(BaseBodega):
    def test_rf29_entradas_suman_y_salidas_restan_en_tiempo_real(self):
        self.mov(T.ENTRADA, 5, orden_compra=self.oc)
        self.mov(T.SALIDA, 3, proyecto=self.obra, jefe_proyecto=self.jp, guia_despacho="G1")
        self.mov(T.MERMA, 2, motivo="DANO")
        self.mat.refresh_from_db()
        self.assertEqual(self.mat.stock_actual, 10 + 5 - 3 - 2)

    def test_cu30_exc1_el_stock_nunca_queda_negativo(self):
        with self.assertRaises(ValidationError):
            self.mov(T.SALIDA, 11, proyecto=self.obra, jefe_proyecto=self.jp, guia_despacho="G1")
        self.mat.refresh_from_db()
        self.assertEqual(self.mat.stock_actual, 10)
        self.assertFalse(MovimientoInventario.objects.filter(tipo=T.SALIDA).exists())

    def test_rf26_la_entrada_registra_la_ubicacion_en_el_material(self):
        self.mov(T.ENTRADA, 1, orden_compra=self.oc, ubicacion="Estante 4")
        self.mat.refresh_from_db()
        self.assertEqual(self.mat.ubicacion, "Estante 4")

    def test_rf58_el_stock_no_se_edita_desde_el_catalogo(self):
        self.assertNotIn("stock_actual", MaterialForm().fields)

    def test_rf34_alerta_bajo_minimo(self):
        self.mat.stock_minimo = 10
        self.mat.save()
        self.assertTrue(self.mat.bajo_stock_minimo)
        self.client.force_login(self.bod)
        self.assertContains(self.client.get(reverse("inventario:bodega_panel")), "Arena")


class EntradaRF26Test(BaseBodega):
    def _form(self, **d):
        datos = {"origen": "OC", "orden_compra": self.oc.pk, "material": self.mat.pk,
                 "cantidad": 5, "ubicacion": "E1"}
        datos.update(d)
        return EntradaForm(data=datos)

    def test_rf27_no_supera_lo_pendiente_de_la_oc(self):
        self.assertFalse(self._form(cantidad=21).is_valid())
        self.assertTrue(self._form(cantidad=20).is_valid())

    def test_material_ajeno_a_la_oc_se_rechaza(self):
        otro = Material.objects.create(nombre="Otro", unidad_medida="u")
        self.assertIn("material", self._form(material=otro.pk).errors)

    def test_cu26_exc1_sin_oc_enviada_no_hay_recepcion_desde_proveedor(self):
        OrdenCompra.objects.update(estado=OrdenCompra.Estado.BORRADOR)
        form = self._form(orden_compra="")
        self.assertFalse(form.is_valid())
        self.assertIn("Enviada", str(form.non_field_errors()))

    def test_cu27_devolucion_desde_obra_exige_el_proyecto(self):
        form = EntradaForm(data={"origen": "PROYECTO", "material": self.mat.pk, "cantidad": 2, "ubicacion": "E1"})
        self.assertIn("proyecto", form.errors)

    def test_entrada_desde_oc_actualiza_recepcion_y_avisa_al_jefe(self):
        self.client.force_login(self.bod)
        self.client.post(reverse("inventario:entrada_crear"), {
            "origen": "OC", "orden_compra": self.oc.pk, "material": self.mat.pk,
            "cantidad": 5, "ubicacion": "E1"})
        self.oc.refresh_from_db()
        self.assertEqual(self.oc.estado, OrdenCompra.Estado.RECEPCION_PARCIAL)
        self.assertTrue(Notificacion.objects.filter(usuario=self.jp).exists())


class SalidaRF28Test(BaseBodega):
    def setUp(self):
        super().setUp()
        from proyectos.models import Itemizado
        self.partida = Itemizado.objects.create(proyecto=self.obra, codigo_partida="P-6",
                                                descripcion="Rellenos", unidad_medida="m3",
                                                cant_presupuestada=50)
        otra = Proyecto.objects.create(nombre="Otra 6", mandante="M", fecha_inicio=date(2026, 1, 1))
        self.partida_ajena = Itemizado.objects.create(proyecto=otra, codigo_partida="X",
                                                      descripcion="x", unidad_medida="m3",
                                                      cant_presupuestada=1)

    def _datos(self, **d):
        datos = {"material": self.mat.pk, "cantidad": 2, "proyecto": self.obra.pk,
                 "jefe_proyecto": self.jp.pk, "guia_despacho": "GD-1",
                 "partida": self.partida.pk}
        datos.update(d)
        return datos

    def test_rf28_partida_obligatoria_y_de_la_obra_elegida(self):
        self.assertTrue(SalidaForm(data=self._datos()).is_valid())
        opciones = list(SalidaForm(data=self._datos()).fields["partida"].queryset)
        self.assertEqual(opciones, [self.partida])
        self.assertIn("partida", SalidaForm(data=self._datos(partida=self.partida_ajena.pk)).errors)

    def test_rf28_la_salida_guarda_la_partida_y_alimenta_el_consumo(self):
        self.client.force_login(self.bod)
        self.client.post(reverse("inventario:salida_crear"), self._datos(cantidad=3))
        mov = MovimientoInventario.objects.get(tipo=T.SALIDA)
        self.assertEqual(mov.partida, self.partida)
        self.assertEqual(self.partida.cantidad_consumida, 3)

    def test_bodega_consulta_las_partidas_de_la_obra(self):
        self.client.force_login(self.bod)
        datos = self.client.get(reverse("solicitudes:api_partidas"), {"proyecto": self.obra.pk}).json()
        self.assertEqual([p["codigo"] for p in datos["partidas"]], ["P-6"])

    def test_rf28_jefe_de_proyecto_y_guia_obligatorios(self):
        for falta in ("jefe_proyecto", "guia_despacho", "partida"):
            datos = self._datos()
            datos.pop(falta)
            self.assertIn(falta, SalidaForm(data=datos).errors)

    def test_el_jefe_tiene_que_estar_asignado_a_la_obra(self):
        ajeno = Usuario.objects.create_user("jp_aj6", password="x", email="aj6@m5.cl", rol="JEFE_PROYECTO")
        self.assertIn("jefe_proyecto", SalidaForm(data=self._datos(jefe_proyecto=ajeno.pk)).errors)

    def test_cu29_exc1_no_supera_el_stock(self):
        self.assertIn("cantidad", SalidaForm(data=self._datos(cantidad=11)).errors)


class PrestamoRF30Test(BaseBodega):
    def setUp(self):
        super().setUp()
        self.herr = Material.objects.create(nombre="Taladro", unidad_medida="u", tipo="HERRAMIENTA",
                                            codigo_activo="H-9", stock_actual=0)

    def _post(self):
        self.client.force_login(self.bod)
        return self.client.post(reverse("inventario:prestamo_crear"), {
            "herramienta": self.herr.pk, "jefe_proyecto": self.jp.pk, "proyecto": self.obra.pk,
            "fecha_salida": date.today().isoformat(),
            "fecha_devolucion_esperada": (date.today() + timedelta(days=5)).isoformat()})

    def test_cu31_exc1_herramienta_fuera_de_bodega_no_se_presta(self):
        self._post()
        self.assertFalse(PrestamoHerramienta.objects.exists())
        self.herr.refresh_from_db()
        self.assertEqual(self.herr.stock_actual, 0)

    def test_rf30_prestamo_notifica_a_administracion(self):
        self.herr.stock_actual = 1
        self.herr.save()
        self._post()
        self.assertTrue(PrestamoHerramienta.objects.exists())
        self.assertTrue(Notificacion.objects.filter(usuario=self.admin, titulo__contains="Taladro").exists())

    def test_rf31_devolucion_la_deja_disponible(self):
        self.herr.stock_actual = 1
        self.herr.save()
        self._post()
        p = PrestamoHerramienta.objects.get()
        self.client.post(reverse("inventario:prestamo_devolver", args=[p.pk]))
        p.refresh_from_db()
        self.herr.refresh_from_db()
        self.assertEqual((p.estado, self.herr.stock_actual), (PrestamoHerramienta.Estado.DEVUELTA, 1))


class MermaRF32Test(BaseBodega):
    def test_cu33_exc1_motivo_obligatorio(self):
        form = MermaForm(data={"material": self.mat.pk, "cantidad": 1, "motivo": ""})
        self.assertIn("motivo", form.errors)

    def test_rf32_registra_proyecto_y_descuenta(self):
        self.client.force_login(self.bod)
        self.client.post(reverse("inventario:merma_crear"), {
            "material": self.mat.pk, "cantidad": 2, "motivo": "ROBO", "proyecto": self.obra.pk})
        m = MovimientoInventario.objects.get(tipo=T.MERMA)
        self.mat.refresh_from_db()
        self.assertEqual((m.proyecto, self.mat.stock_actual), (self.obra, 8))


class DevolucionProveedorRF33Test(BaseBodega):
    def _form(self, **d):
        datos = {"orden_compra": self.oc.pk, "material": self.mat.pk, "cantidad": 3,
                 "guia_despacho": "GD-9", "motivo": "DEFECTUOSO"}
        datos.update(d)
        return DevolucionProveedorForm(data=datos)

    def test_sin_recepcion_la_oc_no_admite_devolucion(self):
        self.assertIn("orden_compra", self._form().errors)

    def test_no_se_devuelve_mas_de_lo_recibido(self):
        self.linea.cantidad_recibida = 5
        self.linea.save()
        self.assertTrue(self._form(cantidad=5).is_valid())
        self.assertIn("cantidad", self._form(cantidad=6).errors)

    def test_cu34_exc1_motivo_obligatorio(self):
        self.linea.cantidad_recibida = 5
        self.linea.save()
        self.assertIn("motivo", self._form(motivo="").errors)


class RolesBodegaTest(BaseBodega):
    def test_adquisiciones_consulta_pero_no_registra_movimientos(self):
        self.client.force_login(self.ea)
        self.assertEqual(self.client.get(reverse("inventario:bodega_panel")).status_code, 200)
        resp = self.client.post(reverse("inventario:salida_crear"), {
            "material": self.mat.pk, "cantidad": 1, "proyecto": self.obra.pk,
            "jefe_proyecto": self.jp.pk, "guia_despacho": "x"})
        self.assertEqual(resp.status_code, 403)

    def test_cu61_solo_administracion_registra_items_en_el_catalogo(self):
        for u in (self.bod, self.ea, self.jp):
            self.client.force_login(u)
            self.assertEqual(self.client.get(reverse("inventario:crear")).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("inventario:crear")).status_code, 200)

    def test_rf33_bodega_no_ve_precios_en_el_catalogo(self):
        self.client.force_login(self.bod)
        resp = self.client.get(reverse("inventario:lista"))
        self.assertTrue(resp.context["oculta_precios"])
