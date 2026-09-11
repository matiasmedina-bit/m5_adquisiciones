"""
Pruebas unitarias del módulo de Solicitudes de Material (CU-11, 12, 14, 16, 17).
"""
import tempfile
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from usuarios.models import Usuario
from proyectos.models import Proyecto, Itemizado
from inventario.models import Material
from .models import SolicitudMaterial, SolicitudDetalle, SolicitudAdjunto
from .forms import SolicitudDetalleForm, SolicitudAdjuntoForm


class SolicitudModelTest(TestCase):

    def setUp(self):
        self.ea = Usuario.objects.create_user(
            username="ea", password="x", email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra A", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.material = Material.objects.create(
            nombre="Clavos", unidad_medida="kg", precio_referencia=1500)

    def test_correlativo_autogenerado(self):
        s = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        self.assertTrue(s.correlativo.startswith("SM-"))

    def test_solicitud_borrador_es_editable(self):
        s = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        self.assertTrue(s.editable)

    def test_detalle_hereda_unidad_del_material(self):
        s = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)
        d = SolicitudDetalle.objects.create(solicitud=s, material=self.material, cantidad_solicitada=10)
        self.assertEqual(d.unidad_medida, "kg")


class SolicitudFlujoTest(TestCase):
    """CU-16: flujo de estados (enviar / aprobar / rechazar)."""

    def setUp(self):
        self.client = Client()
        self.ea = Usuario.objects.create_user(
            username="ea", password="clave12345", email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.jp = Usuario.objects.create_user(
            username="jp", password="clave12345", email="jp@m5.cl", rol="JEFE_PROYECTO")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra B", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.material = Material.objects.create(
            nombre="Pintura", unidad_medida="gl", precio_referencia=12000)
        self.sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)

    def test_no_se_puede_enviar_sin_items(self):
        self.client.login(username="ea", password="clave12345")
        self.client.get(reverse("solicitudes:enviar", args=[self.sol.pk]))
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, SolicitudMaterial.Estado.BORRADOR)

    def test_enviar_con_items_cambia_estado(self):
        SolicitudDetalle.objects.create(solicitud=self.sol, material=self.material, cantidad_solicitada=5)
        self.client.login(username="ea", password="clave12345")
        self.client.get(reverse("solicitudes:enviar", args=[self.sol.pk]))
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, SolicitudMaterial.Estado.ENVIADA)

    def test_jefe_aprueba_solicitud_enviada(self):
        SolicitudDetalle.objects.create(solicitud=self.sol, material=self.material, cantidad_solicitada=5)
        self.sol.estado = SolicitudMaterial.Estado.ENVIADA
        self.sol.save()
        self.client.login(username="jp", password="clave12345")
        self.client.get(reverse("solicitudes:resolver", args=[self.sol.pk, "aprobar"]))
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, SolicitudMaterial.Estado.APROBADA)


class SolicitudProyectoFinalizadoTest(TestCase):
    """PU-06 (CU-10): el sistema bloquea generar solicitudes en proyecto finalizado."""

    def setUp(self):
        self.proyecto_fin = Proyecto.objects.create(
            nombre="Obra Terminada", mandante="M", fecha_inicio=date(2025, 1, 1),
            estado=Proyecto.Estado.FINALIZADO)

    def test_form_rechaza_proyecto_finalizado(self):
        from .forms import SolicitudForm
        form = SolicitudForm(data={"proyecto": self.proyecto_fin.pk, "observaciones": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("proyecto", form.errors)

    def test_proyecto_finalizado_no_esta_en_opciones(self):
        from .forms import SolicitudForm
        form = SolicitudForm()
        self.assertNotIn(self.proyecto_fin, list(form.fields["proyecto"].queryset))


class JustificacionItemizadoTest(TestCase):
    """RF-16: si la cantidad supera el saldo de la partida, se exige justificación."""

    def setUp(self):
        self.ea = Usuario.objects.create_user(
            username="ea", password="x", email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra J", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.material = Material.objects.create(
            nombre="Cemento", unidad_medida="saco", precio_referencia=4500)
        self.partida = Itemizado.objects.create(
            proyecto=self.proyecto, codigo_partida="P-01", descripcion="Hormigón",
            unidad_medida="saco", cant_presupuestada=100, cant_ejecutada=90)  # saldo 10
        self.sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)

    def _data(self, cantidad, justificacion=""):
        return {
            "material": self.material.pk,
            "cantidad_solicitada": cantidad,
            "unidad_medida": "saco",
            "partida": self.partida.pk,
            "justificacion": justificacion,
            "nombre_libre": "",
        }

    def test_exceso_sin_justificacion_es_invalido(self):
        form = SolicitudDetalleForm(data=self._data(50), solicitud=self.sol)
        self.assertFalse(form.is_valid())
        self.assertIn("justificacion", form.errors)

    def test_exceso_con_justificacion_es_valido(self):
        form = SolicitudDetalleForm(
            data=self._data(50, "Rectificación de metraje en terreno"), solicitud=self.sol)
        self.assertTrue(form.is_valid(), form.errors)

    def test_dentro_del_saldo_no_requiere_justificacion(self):
        form = SolicitudDetalleForm(data=self._data(5), solicitud=self.sol)
        self.assertTrue(form.is_valid(), form.errors)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AdjuntosSolicitudTest(TestCase):
    """RF-17: adjuntar hasta 3 archivos PDF/JPG (máx 5 MB) a una solicitud."""

    def setUp(self):
        self.client = Client()
        self.ea = Usuario.objects.create_user(
            username="ea", password="clave12345", email="ea@m5.cl",
            rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea", password="clave12345")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra A", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.ea)

    def test_formato_no_permitido_es_rechazado(self):
        f = SimpleUploadedFile("nota.txt", b"hola", content_type="text/plain")
        form = SolicitudAdjuntoForm(data={"nombre": "x"}, files={"archivo": f})
        self.assertFalse(form.is_valid())

    def test_archivo_pdf_valido(self):
        f = SimpleUploadedFile("plano.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        form = SolicitudAdjuntoForm(data={"nombre": "Plano"}, files={"archivo": f})
        self.assertTrue(form.is_valid(), form.errors)

    def test_maximo_3_adjuntos(self):
        for i in range(3):
            SolicitudAdjunto.objects.create(
                solicitud=self.sol, subido_por=self.ea,
                archivo=SimpleUploadedFile(f"p{i}.jpg", b"data", content_type="image/jpeg"))
        f = SimpleUploadedFile("p4.jpg", b"data", content_type="image/jpeg")
        self.client.post(reverse("solicitudes:detalle", args=[self.sol.pk]),
                         {"accion": "adjuntar", "archivo": f, "nombre": "cuarto"})
        self.assertEqual(self.sol.adjuntos.count(), 3)

    def test_detalle_renderiza_en_varios_estados(self):
        for estado in ("BORRADOR", "APROBADA", "EN_COTIZACION", "OC_GENERADA",
                       "RECEPCION_PARCIAL", "RECIBIDA", "RECHAZADA"):
            self.sol.estado = estado
            self.sol.save(update_fields=["estado"])
            resp = self.client.get(reverse("solicitudes:detalle", args=[self.sol.pk]))
            self.assertEqual(resp.status_code, 200, estado)


# ==========================================================================
#  CU-12 — Proveedor primero, buscador de materiales y valor por línea
# ==========================================================================
class BuscadorMaterialesTest(TestCase):
    """La búsqueda funciona en los dos sentidos: filtrando por proveedor, o
    partiendo del material para ver quién lo ofrece y a qué precio."""

    def setUp(self):
        from proveedores.models import Proveedor, ProveedorMaterial
        self.client = Client()
        Usuario.objects.create_user(username="ea_b", password="clave12345",
                                    email="eab@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea_b", password="clave12345")

        self.andes = Proveedor.objects.create(
            nombre="Ferretería Andes", rut="11111111-1", condicion_pago="30_DIAS")
        self.sur = Proveedor.objects.create(
            nombre="Comercial Sur", rut="22222222-2", condicion_pago="CONTADO")

        self.cemento_andes = ProveedorMaterial.objects.create(
            proveedor=self.andes, codigo="CEM-001",
            descripcion="Cemento Portland 25 kg", unidad_medida="saco", precio=5490)
        self.cemento_sur = ProveedorMaterial.objects.create(
            proveedor=self.sur, codigo="C-9",
            descripcion="Cemento Portland 25 kg", unidad_medida="saco", precio=5200)
        ProveedorMaterial.objects.create(
            proveedor=self.andes, codigo="FIE-014",
            descripcion="Fierro estriado 8 mm", unidad_medida="barra", precio=3990)

    def _buscar(self, **params):
        resp = self.client.get(reverse("solicitudes:api_materiales"), params)
        self.assertEqual(resp.status_code, 200)
        return resp.json()["resultados"]

    def test_busqueda_sin_proveedor_ve_todos_los_catalogos(self):
        nombres = {r["proveedor_nombre"] for r in self._buscar(q="cemento")}
        self.assertIn("Ferretería Andes", nombres)
        self.assertIn("Comercial Sur", nombres)

    def test_elegir_proveedor_restringe_la_busqueda(self):
        resultados = self._buscar(q="cemento", proveedor=self.andes.pk)
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["proveedor_nombre"], "Ferretería Andes")
        self.assertEqual(resultados[0]["precio"], 5490)
        self.assertEqual(resultados[0]["unidad"], "saco")

    def test_la_busqueda_tambien_encuentra_por_codigo(self):
        resultados = self._buscar(q="FIE-014")
        self.assertEqual(resultados[0]["codigo"], "FIE-014")

    def test_material_primero_devuelve_proveedores_del_mas_barato(self):
        resp = self.client.get(reverse("solicitudes:api_proveedores"), {"q": "cemento"})
        self.assertEqual(resp.status_code, 200)
        lista = resp.json()["proveedores"]
        self.assertEqual([p["nombre"] for p in lista], ["Comercial Sur", "Ferretería Andes"])
        self.assertEqual(lista[0]["precio"], 5200)

    def test_la_condicion_de_pago_viaja_en_el_resultado(self):
        resultados = self._buscar(q="cemento", proveedor=self.andes.pk)
        self.assertEqual(resultados[0]["condicion"], "30 días")

    def test_material_no_disponible_no_aparece(self):
        self.cemento_sur.disponible = False
        self.cemento_sur.save()
        nombres = {r["proveedor_nombre"] for r in self._buscar(q="cemento")}
        self.assertNotIn("Comercial Sur", nombres)

    def test_la_api_exige_sesion(self):
        self.client.logout()
        resp = self.client.get(reverse("solicitudes:api_materiales"), {"q": "cemento"})
        self.assertNotEqual(resp.status_code, 200)


class LineaConProveedorTest(TestCase):
    """Guardar una línea desde el catálogo de un proveedor: la unidad y el
    precio se heredan solos y no hay que escribirlos."""

    def setUp(self):
        from proveedores.models import Proveedor, ProveedorMaterial
        from proyectos.models import Proyecto
        from datetime import date

        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username="ea_l", password="clave12345", email="eal@m5.cl",
            rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea_l", password="clave12345")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra Buscador", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.proveedor = Proveedor.objects.create(
            nombre="Ferretería Andes", rut="11111111-1", condicion_pago="30_DIAS")
        self.oferta = ProveedorMaterial.objects.create(
            proveedor=self.proveedor, codigo="CEM-001",
            descripcion="Cemento Portland 25 kg", unidad_medida="saco", precio=5490)
        self.solicitud = SolicitudMaterial.objects.create(
            proyecto=self.proyecto, emisor=self.usuario)

    def _agregar(self, **extra):
        datos = {"accion": "agregar_material", "cantidad_solicitada": "20"}
        datos.update(extra)
        return self.client.post(
            reverse("solicitudes:detalle", args=[self.solicitud.pk]), datos)

    def test_desde_el_catalogo_hereda_unidad_precio_y_proveedor(self):
        self._agregar(proveedor_material=self.oferta.pk)
        linea = self.solicitud.detalles.get()
        self.assertEqual(linea.proveedor, self.proveedor)
        self.assertEqual(linea.unidad_medida, "saco")
        self.assertEqual(linea.valor_unitario, 5490)
        self.assertEqual(linea.material.nombre, "Cemento Portland 25 kg")

    def test_el_valor_escrito_a_mano_manda_sobre_el_del_catalogo(self):
        self._agregar(proveedor_material=self.oferta.pk, valor_unitario="4800")
        self.assertEqual(self.solicitud.detalles.get().valor_unitario, 4800)

    def test_el_catalogo_general_no_se_llena_de_duplicados(self):
        from inventario.models import Material
        self._agregar(proveedor_material=self.oferta.pk)
        self.solicitud.detalles.all().delete()
        self._agregar(proveedor_material=self.oferta.pk)
        self.assertEqual(
            Material.objects.filter(nombre__iexact="Cemento Portland 25 kg").count(), 1)
        self.oferta.refresh_from_db()
        self.assertIsNotNone(self.oferta.material_id)

    def test_material_libre_sigue_funcionando_sin_proveedor(self):
        self._agregar(nombre_libre="Tornillo autoperforante")
        linea = self.solicitud.detalles.get()
        self.assertIsNone(linea.proveedor_id)
        self.assertEqual(linea.material.nombre, "Tornillo autoperforante")

    def test_el_detalle_opcional_se_guarda(self):
        self._agregar(proveedor_material=self.oferta.pk, detalle="para la losa del 3er piso")
        self.assertEqual(self.solicitud.detalles.get().detalle, "para la losa del 3er piso")

    def test_total_estimado_de_la_solicitud(self):
        self._agregar(proveedor_material=self.oferta.pk)          # 20 x 5490
        self.assertEqual(self.solicitud.total_estimado, 20 * 5490)

    def test_sin_cantidad_no_guarda(self):
        self.client.post(reverse("solicitudes:detalle", args=[self.solicitud.pk]),
                         {"accion": "agregar_material", "proveedor_material": self.oferta.pk})
        self.assertEqual(self.solicitud.detalles.count(), 0)


class AccionesDelBorradorTest(TestCase):
    """El borrador tiene que ofrecer editar y enviar, también al ADMIN."""

    def setUp(self):
        from proyectos.models import Proyecto
        from inventario.models import Material
        from datetime import date

        self.client = Client()
        self.admin = Usuario.objects.create_user(
            username="admin_sm", password="clave12345", email="as@m5.cl", rol="ADMIN")
        self.client.login(username="admin_sm", password="clave12345")
        proyecto = Proyecto.objects.create(
            nombre="Obra Acciones", mandante="M", fecha_inicio=date(2026, 6, 1))
        self.solicitud = SolicitudMaterial.objects.create(
            proyecto=proyecto, emisor=self.admin)
        material = Material.objects.create(nombre="Clavos", unidad_medida="kg")
        SolicitudDetalle.objects.create(
            solicitud=self.solicitud, material=material, cantidad_solicitada=5)

    def test_el_admin_ve_editar_y_enviar_en_el_borrador(self):
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.solicitud.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("solicitudes:editar", args=[self.solicitud.pk]))
        self.assertContains(resp, reverse("solicitudes:enviar", args=[self.solicitud.pk]))

    def test_el_admin_puede_enviar(self):
        self.client.get(reverse("solicitudes:enviar", args=[self.solicitud.pk]))
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, SolicitudMaterial.Estado.ENVIADA)

    def test_enviada_deja_de_ofrecer_edicion(self):
        self.solicitud.estado = SolicitudMaterial.Estado.ENVIADA
        self.solicitud.save()
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.solicitud.pk]))
        self.assertNotContains(resp, reverse("solicitudes:editar", args=[self.solicitud.pk]))

    def test_la_pantalla_de_creacion_arma_el_buscador(self):
        resp = self.client.get(reverse("solicitudes:crear"))
        self.assertEqual(resp.status_code, 200)
        # columnas nuevas y columna 'Unidad' retirada del formulario
        self.assertContains(resp, "Proveedor")
        self.assertContains(resp, "Valor unitario")
        self.assertContains(resp, "Detalle")
        self.assertContains(resp, "Siguiente")
        self.assertNotContains(resp, "unidad (ej: kg, m2)")
        # el buscador y su API quedan cableados
        self.assertContains(resp, "buscador-material")
        self.assertContains(resp, reverse("solicitudes:api_materiales"))
        self.assertContains(resp, reverse("solicitudes:api_proveedores"))
