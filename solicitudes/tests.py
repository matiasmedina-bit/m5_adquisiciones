"""
Pruebas del módulo de Solicitudes de Material (RF-12 a RF-15, CU-11 a CU-15).
"""
import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from inventario.models import Material
from proyectos.models import Itemizado, Proyecto
from usuarios.models import Notificacion, Usuario
from .forms import SolicitudAdjuntoForm, SolicitudDetalleForm, SolicitudForm
from .models import SolicitudAdjunto, SolicitudDetalle, SolicitudMaterial

E = SolicitudMaterial.Estado


class BaseSM(TestCase):
    """Obra en ejecución con un JP asignado, una partida y un material."""

    def setUp(self):
        self.client = Client()
        self.jp = Usuario.objects.create_user(
            username="jp", password="clave12345", email="jp@m5.cl", rol="JEFE_PROYECTO")
        self.ea = Usuario.objects.create_user(
            username="ea", password="clave12345", email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra A", mandante="M", fecha_inicio=date(2026, 6, 1),
            estado=Proyecto.Estado.EJECUCION)
        self.proyecto.jefes.add(self.jp)
        self.partida = Itemizado.objects.create(
            proyecto=self.proyecto, codigo_partida="P-01", descripcion="Hormigón",
            unidad_medida="saco", cant_presupuestada=100)
        self.material = Material.objects.create(
            nombre="Cemento", unidad_medida="saco", precio_referencia=4500)
        self.sol = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.jp)

    def login(self, usuario):
        self.client.force_login(usuario)

    def linea(self, cantidad=5, sol=None, **extra):
        return SolicitudDetalle.objects.create(
            solicitud=sol or self.sol, material=extra.pop("material", self.material),
            cantidad_solicitada=cantidad, partida=extra.pop("partida", self.partida), **extra)

    def emitir(self, sol=None):
        return self.client.post(reverse("solicitudes:emitir", args=[(sol or self.sol).pk]))


# --------------------------------------------------------------------------
#  RF-12 — creación, correlativo al confirmar y estado "Emitida"
# --------------------------------------------------------------------------
class CorrelativoTest(BaseSM):
    def test_borrador_no_tiene_numero_todavia(self):
        self.assertIsNone(self.sol.correlativo)
        self.assertIn("Borrador", self.sol.numero)

    def test_rf12_al_emitir_recibe_correlativo_y_queda_emitida(self):
        self.linea()
        self.login(self.jp)
        self.emitir()
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.EMITIDA)
        self.assertRegex(self.sol.correlativo, r"^SM-\d{6}$")

    def test_rf12_correlativo_secuencial_y_unico(self):
        a = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.jp, estado=E.EMITIDA)
        b = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.jp, estado=E.EMITIDA)
        na, nb = int(a.correlativo[3:]), int(b.correlativo[3:])
        self.assertEqual(nb, na + 1)

    def test_rf12_correlativo_no_editable(self):
        self.assertFalse(SolicitudMaterial._meta.get_field("correlativo").editable)
        self.assertNotIn("correlativo", SolicitudForm().fields)

    def test_reemitir_conserva_el_numero(self):
        self.linea()
        self.login(self.jp)
        self.emitir()
        self.sol.refresh_from_db()
        numero = self.sol.correlativo
        self.sol.estado = E.RECHAZADA
        self.sol.save()
        self.client.post(reverse("solicitudes:devolver_borrador", args=[self.sol.pk]))
        self.emitir()
        self.sol.refresh_from_db()
        self.assertEqual((self.sol.estado, self.sol.correlativo), (E.EMITIDA, numero))

    def test_detalle_hereda_unidad_del_material(self):
        d = SolicitudDetalle.objects.create(solicitud=self.sol, material=self.material, cantidad_solicitada=10)
        self.assertEqual(d.unidad_medida, "saco")

    def test_borrador_es_editable(self):
        self.assertTrue(self.sol.editable)


class CreacionReglasRF12Test(BaseSM):
    def test_solo_el_jefe_de_proyecto_crea_solicitudes(self):
        for rol in ("ENCARGADO_ADQUISICIONES", "BODEGUERO", "CONTABILIDAD"):
            u = Usuario.objects.create_user(f"u_{rol}", password="x", email=f"{rol}@m5.cl", rol=rol)
            self.login(u)
            self.assertEqual(self.client.get(reverse("solicitudes:crear")).status_code, 403, rol)
        self.login(self.jp)
        self.assertEqual(self.client.get(reverse("solicitudes:crear")).status_code, 200)

    def test_solo_obras_en_ejecucion_asignadas(self):
        planif = Proyecto.objects.create(nombre="Planif", mandante="M", fecha_inicio=date(2026, 1, 1))
        planif.jefes.add(self.jp)
        ajena = Proyecto.objects.create(nombre="Ajena", mandante="M", fecha_inicio=date(2026, 1, 1),
                                        estado=Proyecto.Estado.EJECUCION)
        opciones = list(SolicitudForm(usuario=self.jp).fields["proyecto"].queryset)
        self.assertEqual(opciones, [self.proyecto])
        self.assertNotIn(planif, opciones)
        self.assertNotIn(ajena, opciones)

    def test_cu11_proyecto_finalizado_bloqueado(self):
        fin = Proyecto.objects.create(nombre="Fin", mandante="M", fecha_inicio=date(2025, 1, 1),
                                      estado=Proyecto.Estado.FINALIZADO)
        fin.jefes.add(self.jp)
        form = SolicitudForm(data={"proyecto": fin.pk}, usuario=self.jp)
        self.assertFalse(form.is_valid())
        self.assertIn("proyecto", form.errors)

    def test_cu11_no_se_emite_si_la_obra_se_finalizo_despues(self):
        self.linea()
        self.proyecto.estado = Proyecto.Estado.FINALIZADO
        self.proyecto.save()
        self.login(self.jp)
        resp = self.emitir()
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.BORRADOR)
        self.assertIn("finalizado", [str(m) for m in resp.wsgi_request._messages][0])

    def test_cu12_exc1_no_se_emite_sin_lineas(self):
        self.login(self.jp)
        self.emitir()
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.BORRADOR)

    def test_cu12_exc1_partida_obligatoria(self):
        form = SolicitudDetalleForm(data={
            "material": self.material.pk, "cantidad_solicitada": 3, "nombre_libre": ""},
            solicitud=self.sol)
        self.assertFalse(form.is_valid())
        self.assertIn("partida", form.errors)

    def test_cu12_no_se_emite_una_linea_sin_partida(self):
        SolicitudDetalle.objects.create(solicitud=self.sol, material=self.material, cantidad_solicitada=3)
        self.login(self.jp)
        self.emitir()
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.BORRADOR)

    def test_rf12_material_libre_no_crea_catalogo(self):
        form = SolicitudDetalleForm(data={
            "nombre_libre": "Tornillo inventado", "cantidad_solicitada": 3,
            "partida": self.partida.pk}, solicitud=self.sol)
        self.assertFalse(form.is_valid())
        self.assertIn("nombre_libre", form.errors)
        self.assertFalse(Material.objects.filter(nombre="Tornillo inventado").exists())

    def test_crear_con_lineas_valida_la_partida_del_proyecto(self):
        otro = Proyecto.objects.create(nombre="Otro", mandante="M", fecha_inicio=date(2026, 1, 1))
        ajena = Itemizado.objects.create(proyecto=otro, codigo_partida="X", descripcion="x",
                                         unidad_medida="u", cant_presupuestada=1)
        self.login(self.jp)
        datos = {
            "proyecto": self.proyecto.pk, "observaciones": "",
            "detalles-TOTAL_FORMS": "1", "detalles-INITIAL_FORMS": "0",
            "detalles-MIN_NUM_FORMS": "0", "detalles-MAX_NUM_FORMS": "1000",
            "detalles-0-material": self.material.pk, "detalles-0-cantidad_solicitada": "2",
            "detalles-0-partida": ajena.pk, "detalles-0-nombre_libre": "Cemento",
        }
        resp = self.client.post(reverse("solicitudes:crear"), datos)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(SolicitudMaterial.objects.count(), 1)  # sólo la del setUp
        datos["detalles-0-partida"] = self.partida.pk
        resp = self.client.post(reverse("solicitudes:crear"), datos)
        self.assertEqual(resp.status_code, 302)
        nueva = SolicitudMaterial.objects.latest("pk")
        self.assertEqual((nueva.estado, nueva.detalles.get().partida), (E.BORRADOR, self.partida))


# --------------------------------------------------------------------------
#  RF-13 — justificación por exceso del saldo restante
# --------------------------------------------------------------------------
class ExcesoItemizadoRF13Test(BaseSM):
    def _form(self, cantidad, justificacion="", sol=None):
        return SolicitudDetalleForm(data={
            "material": self.material.pk, "cantidad_solicitada": cantidad,
            "partida": self.partida.pk, "justificacion": justificacion, "nombre_libre": "",
        }, solicitud=sol or self.sol)

    def test_dentro_del_saldo_no_pide_justificacion(self):
        self.assertTrue(self._form(100).is_valid())

    def test_exceso_sin_justificacion_es_invalido_y_dice_la_partida(self):
        form = self._form(101)
        self.assertFalse(form.is_valid())
        self.assertIn("P-01", form.errors["justificacion"][0])

    def test_exceso_con_justificacion_es_valido(self):
        self.assertTrue(self._form(150, "Rectificación de metraje en terreno").is_valid())

    def test_lo_ejecutado_descuenta_saldo(self):
        self.partida.cant_ejecutada = 90
        self.partida.save()
        self.assertFalse(self._form(11).is_valid())
        self.assertTrue(self._form(10).is_valid())

    def test_rf13_lo_pedido_en_otras_sm_emitidas_descuenta_saldo(self):
        previa = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.jp, estado=E.EMITIDA)
        self.linea(80, sol=previa)
        self.assertEqual(self.partida.saldo_restante(), 20)
        self.assertFalse(self._form(30).is_valid())
        self.assertTrue(self._form(20).is_valid())

    def test_borradores_y_rechazadas_no_comprometen_saldo(self):
        for estado in (E.BORRADOR, E.RECHAZADA):
            s = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.jp, estado=estado)
            self.linea(80, sol=s)
        self.assertEqual(self.partida.saldo_restante(), 100)

    def test_la_propia_linea_no_cuenta_contra_si_misma(self):
        d = self.linea(100, sol=SolicitudMaterial.objects.create(
            proyecto=self.proyecto, emisor=self.jp, estado=E.EMITIDA))
        self.assertFalse(d.excede_itemizado)

    def test_al_emitir_se_revalida_el_saldo(self):
        self.linea(60)            # dentro del saldo cuando se armó el borrador
        previa = SolicitudMaterial.objects.create(proyecto=self.proyecto, emisor=self.jp, estado=E.EMITIDA)
        self.linea(60, sol=previa)  # otra SM consumió saldo entretanto
        self.login(self.jp)
        self.emitir()
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.BORRADOR)

    def test_api_entrega_saldo_restante(self):
        self.login(self.jp)
        datos = self.client.get(reverse("solicitudes:api_partidas"), {"proyecto": self.proyecto.pk}).json()
        self.assertEqual(datos["partidas"][0]["saldo"], 100)

    def test_pantallas_ofrecen_la_partida(self):
        self.login(self.jp)
        resp = self.client.get(reverse("solicitudes:crear"))
        self.assertContains(resp, "celda-partida")
        self.assertContains(resp, reverse("solicitudes:api_partidas"))
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.sol.pk]))
        self.assertContains(resp, "Partida del itemizado")


# --------------------------------------------------------------------------
#  RF-14 — adjuntos
# --------------------------------------------------------------------------
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AdjuntosRF14Test(BaseSM):
    def _subir(self, nombre="plano.pdf", contenido=b"%PDF-1.4 test"):
        return self.client.post(reverse("solicitudes:detalle", args=[self.sol.pk]), {
            "accion": "adjuntar", "nombre": "x",
            "archivo": SimpleUploadedFile(nombre, contenido)})

    def test_formato_no_permitido_es_rechazado(self):
        form = SolicitudAdjuntoForm(data={"nombre": "x"},
                                    files={"archivo": SimpleUploadedFile("nota.txt", b"hola")})
        self.assertFalse(form.is_valid())

    def test_pdf_valido(self):
        form = SolicitudAdjuntoForm(data={"nombre": "Plano"},
                                    files={"archivo": SimpleUploadedFile("plano.pdf", b"%PDF-1.4")})
        self.assertTrue(form.is_valid(), form.errors)

    def test_mas_de_5mb_es_rechazado(self):
        grande = SimpleUploadedFile("foto.jpg", b"0" * (5 * 1024 * 1024 + 1))
        form = SolicitudAdjuntoForm(data={"nombre": "x"}, files={"archivo": grande})
        self.assertFalse(form.is_valid())

    def test_el_jefe_responsable_adjunta(self):
        self.login(self.jp)
        self._subir()
        self.assertEqual(self.sol.adjuntos.count(), 1)

    def test_maximo_3_adjuntos(self):
        for i in range(3):
            SolicitudAdjunto.objects.create(
                solicitud=self.sol, subido_por=self.jp,
                archivo=SimpleUploadedFile(f"p{i}.jpg", b"data"))
        self.login(self.jp)
        self._subir("p4.jpg", b"data")
        self.assertEqual(self.sol.adjuntos.count(), 3)

    def test_otros_roles_y_jefes_ajenos_no_adjuntan(self):
        self.sol.estado = E.EMITIDA
        self.sol.save()
        ajeno = Usuario.objects.create_user("jp2", password="x", email="jp2@m5.cl", rol="JEFE_PROYECTO")
        bodega = Usuario.objects.create_user("bod", password="x", email="b@m5.cl", rol="BODEGUERO")
        for u in (ajeno, bodega, self.ea):
            self.login(u)
            self.assertEqual(self._subir().status_code, 403, u.rol)
        self.assertEqual(self.sol.adjuntos.count(), 0)

    def test_detalle_renderiza_en_todos_los_estados(self):
        self.login(self.jp)
        for estado, _ in E.choices:
            self.sol.estado = estado
            self.sol.save()
            resp = self.client.get(reverse("solicitudes:detalle", args=[self.sol.pk]))
            self.assertEqual(resp.status_code, 200, estado)


# --------------------------------------------------------------------------
#  RF-15 — notificaciones al Jefe de Proyecto
# --------------------------------------------------------------------------
class NotificacionesRF15Test(BaseSM):
    def _avisos_jp(self):
        return Notificacion.objects.filter(usuario=self.jp)

    def test_cada_cambio_de_estado_notifica_al_jefe(self):
        self.sol.cambiar_estado(E.EMITIDA)
        self.sol.cambiar_estado(E.EN_COTIZACION, "Todas las líneas aprobadas")
        self.sol.cambiar_estado(E.OC_GENERADA)
        self.sol.cambiar_estado(E.RECEPCION_PARCIAL)
        self.sol.cambiar_estado(E.RECIBIDA)
        titulos = list(self._avisos_jp().order_by("fecha", "pk").values_list("titulo", flat=True))
        self.assertEqual(len(titulos), 5)
        self.assertIn("Entregada", titulos[-1])

    def test_la_descripcion_viaja_en_la_notificacion(self):
        self.sol.cambiar_estado(E.EMITIDA, "Motivo de prueba")
        self.assertIn("Motivo de prueba", self._avisos_jp().get().mensaje)

    def test_cu15_exc1_sin_descripcion_notifica_solo_el_estado(self):
        self.sol.cambiar_estado(E.EMITIDA)
        aviso = self._avisos_jp().get()
        self.assertIn("Emitida", aviso.mensaje)

    def test_emitir_notifica_al_jefe_y_a_adquisiciones(self):
        self.linea()
        self.login(self.jp)
        self.emitir()
        self.assertTrue(self._avisos_jp().exists())
        self.assertTrue(Notificacion.objects.filter(usuario=self.ea).exists())

    def test_todos_los_jefes_de_la_obra_reciben_el_aviso(self):
        otro = Usuario.objects.create_user("jp_b", password="x", email="jpb@m5.cl", rol="JEFE_PROYECTO")
        self.proyecto.jefes.add(otro)
        self.sol.cambiar_estado(E.EMITIDA)
        self.assertTrue(Notificacion.objects.filter(usuario=otro).exists())

    def test_la_campana_muestra_los_avisos(self):
        self.sol.cambiar_estado(E.EMITIDA)
        self.login(self.jp)
        resp = self.client.get(reverse("usuarios:notificaciones"))
        self.assertContains(resp, "Emitida")
        aviso = self._avisos_jp().get()
        self.client.get(reverse("usuarios:notificacion_abrir", args=[aviso.pk]))
        aviso.refresh_from_db()
        self.assertTrue(aviso.leida)

    def test_no_se_leen_avisos_ajenos(self):
        self.sol.cambiar_estado(E.EMITIDA)
        aviso = self._avisos_jp().get()
        self.login(self.ea)
        resp = self.client.get(reverse("usuarios:notificacion_abrir", args=[aviso.pk]))
        self.assertEqual(resp.status_code, 404)


# --------------------------------------------------------------------------
#  Rechazo por Adquisiciones y corrección por el Jefe de Proyecto
# --------------------------------------------------------------------------
class RechazoTest(BaseSM):
    def setUp(self):
        super().setUp()
        self.linea()
        self.sol.cambiar_estado(E.EMITIDA)
        Notificacion.objects.all().delete()

    def test_adquisiciones_rechaza_con_motivo_y_se_notifica(self):
        self.login(self.ea)
        self.client.post(reverse("solicitudes:rechazar", args=[self.sol.pk]), {"motivo": "Material mal especificado"})
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.RECHAZADA)
        self.assertIn("mal especificado", Notificacion.objects.get(usuario=self.jp).mensaje)

    def test_rechazo_sin_motivo_no_procede(self):
        self.login(self.ea)
        self.client.post(reverse("solicitudes:rechazar", args=[self.sol.pk]), {"motivo": " "})
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.EMITIDA)

    def test_el_jefe_no_rechaza(self):
        self.login(self.jp)
        resp = self.client.post(reverse("solicitudes:rechazar", args=[self.sol.pk]), {"motivo": "x"})
        self.assertEqual(resp.status_code, 403)

    def test_no_se_rechaza_con_oc_generada(self):
        self.sol.cambiar_estado(E.OC_GENERADA)
        self.login(self.ea)
        self.client.post(reverse("solicitudes:rechazar", args=[self.sol.pk]), {"motivo": "x"})
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.OC_GENERADA)

    def test_el_jefe_corrige_y_vuelve_a_borrador(self):
        self.sol.estado = E.RECHAZADA
        self.sol.save()
        self.login(self.jp)
        self.client.post(reverse("solicitudes:devolver_borrador", args=[self.sol.pk]))
        self.sol.refresh_from_db()
        self.assertEqual(self.sol.estado, E.BORRADOR)


# --------------------------------------------------------------------------
#  Acceso: propiedad, borradores y precios
# --------------------------------------------------------------------------
class AccesoSolicitudTest(BaseSM):
    def setUp(self):
        super().setUp()
        self.linea(valor_unitario=4321)
        self.ajeno = Usuario.objects.create_user("jp_x", password="x", email="x@m5.cl", rol="JEFE_PROYECTO")
        self.bodega = Usuario.objects.create_user("bod_x", password="x", email="bx@m5.cl", rol="BODEGUERO")

    def test_jefe_ajeno_no_ve_ni_modifica(self):
        self.sol.cambiar_estado(E.EMITIDA)
        self.login(self.ajeno)
        url = reverse("solicitudes:detalle", args=[self.sol.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertNotContains(self.client.get(reverse("solicitudes:lista")), self.sol.correlativo)

    def test_borrador_solo_lo_ve_su_jefe(self):
        self.login(self.ea)
        self.assertEqual(
            self.client.get(reverse("solicitudes:detalle", args=[self.sol.pk])).status_code, 403)

    def test_nadie_mas_agrega_lineas_al_borrador(self):
        for u in (self.ajeno, self.ea, self.bodega):
            self.login(u)
            resp = self.client.post(reverse("solicitudes:detalle", args=[self.sol.pk]), {
                "accion": "agregar_material", "material": self.material.pk,
                "cantidad_solicitada": 1, "partida": self.partida.pk})
            self.assertEqual(resp.status_code, 403, u.rol)

    def test_rf26_bodega_no_ve_precios(self):
        self.sol.cambiar_estado(E.EMITIDA)
        self.login(self.bodega)
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.sol.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "4.321")
        self.assertNotContains(resp, "Valor unit.")

    def test_emitida_ya_no_se_edita(self):
        self.sol.cambiar_estado(E.EMITIDA)
        self.login(self.jp)
        resp = self.client.get(reverse("solicitudes:detalle", args=[self.sol.pk]))
        self.assertNotContains(resp, reverse("solicitudes:editar", args=[self.sol.pk]))


# --------------------------------------------------------------------------
#  Buscador de materiales y líneas desde el catálogo del proveedor
# --------------------------------------------------------------------------
class BuscadorMaterialesTest(TestCase):
    def setUp(self):
        from proveedores.models import Proveedor, ProveedorMaterial
        self.client = Client()
        self.client.force_login(Usuario.objects.create_user(
            username="jp_b", password="clave12345", email="jpb@m5.cl", rol="JEFE_PROYECTO"))
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
        self.assertEqual(nombres >= {"Ferretería Andes", "Comercial Sur"}, True)

    def test_elegir_proveedor_restringe_la_busqueda(self):
        resultados = self._buscar(q="cemento", proveedor=self.andes.pk)
        self.assertEqual(len(resultados), 1)
        self.assertEqual((resultados[0]["precio"], resultados[0]["unidad"]), (5490, "saco"))

    def test_la_busqueda_tambien_encuentra_por_codigo(self):
        self.assertEqual(self._buscar(q="FIE-014")[0]["codigo"], "FIE-014")

    def test_material_primero_devuelve_proveedores_del_mas_barato(self):
        lista = self.client.get(reverse("solicitudes:api_proveedores"), {"q": "cemento"}).json()["proveedores"]
        self.assertEqual([p["nombre"] for p in lista], ["Comercial Sur", "Ferretería Andes"])

    def test_la_condicion_de_pago_viaja_en_el_resultado(self):
        self.assertEqual(self._buscar(q="cemento", proveedor=self.andes.pk)[0]["condicion"], "30 días")

    def test_material_no_disponible_no_aparece(self):
        self.cemento_sur.disponible = False
        self.cemento_sur.save()
        self.assertNotIn("Comercial Sur", {r["proveedor_nombre"] for r in self._buscar(q="cemento")})

    def test_la_api_exige_sesion(self):
        self.client.logout()
        self.assertNotEqual(
            self.client.get(reverse("solicitudes:api_materiales"), {"q": "x"}).status_code, 200)


class LineaConProveedorTest(BaseSM):
    def setUp(self):
        super().setUp()
        from proveedores.models import Proveedor, ProveedorMaterial
        self.proveedor = Proveedor.objects.create(
            nombre="Ferretería Andes", rut="11111111-1", condicion_pago="30_DIAS")
        self.oferta = ProveedorMaterial.objects.create(
            proveedor=self.proveedor, codigo="CEM-001",
            descripcion="Cemento Portland 25 kg", unidad_medida="saco", precio=5490)
        self.login(self.jp)

    def _agregar(self, **extra):
        datos = {"accion": "agregar_material", "cantidad_solicitada": "20", "partida": self.partida.pk}
        datos.update(extra)
        return self.client.post(reverse("solicitudes:detalle", args=[self.sol.pk]), datos)

    def test_desde_el_catalogo_hereda_unidad_precio_y_proveedor(self):
        self._agregar(proveedor_material=self.oferta.pk)
        linea = self.sol.detalles.get()
        self.assertEqual((linea.proveedor, linea.unidad_medida, linea.valor_unitario),
                         (self.proveedor, "saco", 5490))
        self.assertEqual(linea.material.nombre, "Cemento Portland 25 kg")

    def test_el_valor_escrito_a_mano_manda_sobre_el_del_catalogo(self):
        self._agregar(proveedor_material=self.oferta.pk, valor_unitario="4800")
        self.assertEqual(self.sol.detalles.get().valor_unitario, 4800)

    def test_el_catalogo_maestro_no_se_llena_de_duplicados(self):
        self._agregar(proveedor_material=self.oferta.pk)
        self.sol.detalles.all().delete()
        self._agregar(proveedor_material=self.oferta.pk)
        self.assertEqual(Material.objects.filter(nombre__iexact="Cemento Portland 25 kg").count(), 1)
        self.oferta.refresh_from_db()
        self.assertIsNotNone(self.oferta.material_id)

    def test_el_detalle_opcional_se_guarda(self):
        self._agregar(proveedor_material=self.oferta.pk, detalle="para la losa del 3er piso")
        self.assertEqual(self.sol.detalles.get().detalle, "para la losa del 3er piso")

    def test_total_estimado_de_la_solicitud(self):
        self._agregar(proveedor_material=self.oferta.pk)
        self.assertEqual(self.sol.total_estimado, 20 * 5490)

    def test_sin_cantidad_no_guarda(self):
        self.client.post(reverse("solicitudes:detalle", args=[self.sol.pk]),
                         {"accion": "agregar_material", "proveedor_material": self.oferta.pk,
                          "partida": self.partida.pk})
        self.assertEqual(self.sol.detalles.count(), 0)

    def test_la_pantalla_de_creacion_arma_el_buscador(self):
        resp = self.client.get(reverse("solicitudes:crear"))
        self.assertContains(resp, "buscador-material")
        self.assertContains(resp, reverse("solicitudes:api_materiales"))
        self.assertContains(resp, reverse("solicitudes:api_proveedores"))
