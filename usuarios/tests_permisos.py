"""
Matriz rol × funcionalidad (requerimientos y casos de uso).

Cada fila dice qué roles pueden entrar a una URL; todos los demás deben
recibir 403 al entrar por la URL directa (o ser enviados al login si no
iniciaron sesión). Es la protección en el backend: los botones ocultos en la
plantilla no cuentan.
"""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from adquisiciones.models import OrdenCompra, OrdenCompraLinea
from facturacion.models import Factura
from inventario.models import Material
from proveedores.models import Proveedor
from proyectos.models import Itemizado, Proyecto
from solicitudes.models import SolicitudMaterial
from usuarios.models import Usuario

ROLES = ["ADMIN", "JEFE_PROYECTO", "ENCARGADO_ADQUISICIONES", "BODEGUERO", "CONTABILIDAD"]
ADM, JP, EA, BOD, CONT = ROLES


class MatrizPermisosTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = {r: Usuario.objects.create_user(
            f"u_{r.lower()}", password="x", email=f"{r.lower()}@m5.cl", rol=r) for r in ROLES}
        cls.proyecto = Proyecto.objects.create(
            nombre="Obra Matriz", mandante="M", centro_costo="CC-M",
            fecha_inicio=date(2026, 1, 1), estado=Proyecto.Estado.EJECUCION)
        cls.proyecto.jefes.add(cls.u[JP])
        cls.partida = Itemizado.objects.create(
            proyecto=cls.proyecto, codigo_partida="1", descripcion="x",
            unidad_medida="u", cant_presupuestada=10)
        cls.prov = Proveedor.objects.create(
            nombre="Prov M", rut="11111111-1", correo="p@m.cl", direccion="Calle 1",
            giro="Ferretería", telefono="1")
        cls.material = Material.objects.create(nombre="Mat M", unidad_medida="u")
        cls.sm = SolicitudMaterial.objects.create(
            proyecto=cls.proyecto, emisor=cls.u[JP], estado=SolicitudMaterial.Estado.EMITIDA)
        cls.oc = OrdenCompra.objects.create(
            solicitud=cls.sm, proveedor=cls.prov, creada_por=cls.u[EA],
            estado=OrdenCompra.Estado.ENVIADA)
        OrdenCompraLinea.objects.create(orden=cls.oc, material=cls.material, descripcion="Mat",
                                        cantidad=1, valor_unitario=100)
        cls.factura = Factura.objects.create(
            numero="1", proveedor=cls.prov, fecha_emision=date(2026, 1, 1),
            fecha_vencimiento=date(2026, 2, 1), monto_total=119, registrado_por=cls.u[CONT])

    def _codigo(self, rol, url):
        self.client.force_login(self.u[rol])
        return self.client.get(url).status_code

    def verificar(self, url, permitidos):
        for rol in ROLES:
            codigo = self._codigo(rol, url)
            if rol in permitidos:
                self.assertNotEqual(codigo, 403, f"{rol} debería entrar a {url}")
            else:
                self.assertEqual(codigo, 403, f"{rol} NO debería entrar a {url} (recibió {codigo})")

    # ---------------------------------------------------------------- Módulo 1
    def test_m1_proveedores(self):
        for url in (reverse("proveedores:lista"), reverse("proveedores:crear"),
                    reverse("proveedores:editar", args=[self.prov.pk])):
            self.verificar(url, {ADM, EA})

    # ---------------------------------------------------------------- Módulo 2
    def test_m2_gestion_de_proyectos_solo_administrador(self):
        for url in (reverse("proyectos:crear"),
                    reverse("proyectos:editar", args=[self.proyecto.pk]),
                    reverse("proyectos:itemizado_crear", args=[self.proyecto.pk])):
            self.verificar(url, {ADM})

    def test_m2_consulta_de_proyectos(self):
        self.verificar(reverse("proyectos:detalle", args=[self.proyecto.pk]), {ADM, JP, EA, CONT})

    # ---------------------------------------------------------------- Módulo 3
    def test_m3_crear_solicitud_solo_jefe(self):
        self.verificar(reverse("solicitudes:crear"), {ADM, JP})

    # ---------------------------------------------------------------- Módulo 4
    def test_m4_bandeja_y_cotizacion_solo_adquisiciones(self):
        self.verificar(reverse("adquisiciones:cotizacion_bandeja"), {ADM, EA})
        self.verificar(reverse("adquisiciones:cotizacion_sm", args=[self.sm.pk]), {ADM, EA})

    # ---------------------------------------------------------------- Módulo 5
    def test_m5_ordenes(self):
        self.verificar(reverse("adquisiciones:orden_lista"), {ADM, EA, JP})
        self.verificar(reverse("adquisiciones:orden_crear"), {ADM, EA})
        self.verificar(reverse("adquisiciones:orden_pdf", args=[self.oc.pk]), {ADM, EA, JP})

    # ---------------------------------------------------------------- Módulo 6
    def test_m6_movimientos_de_bodega_solo_bodega(self):
        for nombre in ("entrada_crear", "salida_crear", "merma_crear",
                       "devolucion_proveedor_crear", "prestamo_crear"):
            self.verificar(reverse(f"inventario:{nombre}"), {ADM, BOD})

    def test_m6_consulta_de_bodega(self):
        self.verificar(reverse("inventario:bodega_panel"), {ADM, BOD, EA})

    # ---------------------------------------------------------------- Módulo 7
    def test_m7_facturacion_solo_contabilidad(self):
        for url in (reverse("facturacion:lista"), reverse("facturacion:crear"),
                    reverse("facturacion:cuentas_por_pagar"), reverse("facturacion:export_csv")):
            self.verificar(url, {ADM, CONT})

    def test_m7_desbloqueo_solo_administracion(self):
        self.verificar(reverse("facturacion:desbloquear", args=[self.factura.pk]), {ADM})

    # ---------------------------------------------------------------- Módulo 8
    def test_m8_reportes(self):
        for nombre in ("consumo", "desviacion", "mermas"):
            self.verificar(reverse(f"reportes:{nombre}"), {ADM, JP, EA})
        self.verificar(reverse("reportes:compras"), {ADM, EA})

    def test_m8_trazabilidad(self):
        self.verificar(reverse("adquisiciones:trazabilidad"), {ADM, JP, EA})

    # ---------------------------------------------------------------- Módulo 9
    def test_m9_usuarios_y_parametros_solo_administrador(self):
        for url in (reverse("usuarios:lista"), reverse("usuarios:crear"),
                    reverse("usuarios:parametros")):
            self.verificar(url, {ADM})

    # --------------------------------------------------------------- Módulo 10
    def test_m10_catalogo(self):
        self.verificar(reverse("inventario:lista"), {ADM, JP, EA, BOD})
        self.verificar(reverse("inventario:crear"), {ADM})
        self.verificar(reverse("inventario:editar", args=[self.material.pk]), {ADM})

    # ------------------------------------------------------- sin iniciar sesión
    def test_sin_sesion_no_entra_a_nada(self):
        self.client.logout()
        for url in (reverse("home"), reverse("solicitudes:lista"), reverse("proyectos:lista"),
                    reverse("adquisiciones:orden_lista"), reverse("facturacion:lista")):
            codigo = self.client.get(url).status_code
            self.assertIn(codigo, (302, 403), url)
