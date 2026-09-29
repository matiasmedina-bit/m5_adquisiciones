"""
Pruebas unitarias del módulo de Proyectos e Itemizado (CU-06 a CU-10, CU-54).
"""
import tempfile
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.db import IntegrityError
from django.urls import reverse
from usuarios.models import Usuario, ParametrosSistema
from .models import Proyecto, Itemizado, TipoDocumento, ArchivoProyecto
from .forms import ProyectoForm, ArchivoProyectoForm


class ProyectoModelTest(TestCase):

    def setUp(self):
        self.proyecto = Proyecto.objects.create(
            nombre="Edificio Aurora", mandante="Inmobiliaria X",
            fecha_inicio=date(2026, 6, 1), presupuesto_total=1000000,
        )

    def test_creacion_proyecto(self):
        self.assertEqual(str(self.proyecto), "Edificio Aurora")
        self.assertEqual(self.proyecto.estado, Proyecto.Estado.PLANIFICACION)

    def test_itemizado_saldo(self):
        item = Itemizado.objects.create(
            proyecto=self.proyecto, codigo_partida="P-01", descripcion="Hormigón",
            unidad_medida="m3", cant_presupuestada=100, cant_ejecutada=30,
        )
        self.assertEqual(item.saldo_disponible, 70)

    def test_codigo_partida_unico_por_proyecto(self):
        Itemizado.objects.create(
            proyecto=self.proyecto, codigo_partida="P-01", descripcion="A",
            unidad_medida="m3", cant_presupuestada=1)
        with self.assertRaises(IntegrityError):
            Itemizado.objects.create(
                proyecto=self.proyecto, codigo_partida="P-01", descripcion="B",
                unidad_medida="m3", cant_presupuestada=1)


class ProyectoFormTest(TestCase):
    """CU-06: validación de fechas."""

    def test_fecha_termino_anterior_a_inicio_invalida(self):
        form = ProyectoForm(data={
            "nombre": "X", "mandante": "Y",
            "fecha_inicio": "2026-06-10", "fecha_termino": "2026-06-01",
            "estado": "PLANIFICACION", "presupuesto_total": 0,
        })
        self.assertFalse(form.is_valid())


class CentroCostoTest(TestCase):
    """RF-14: el centro de costo no puede repetirse en otro proyecto."""

    def setUp(self):
        Proyecto.objects.create(
            nombre="Obra 1", mandante="M", fecha_inicio=date(2026, 6, 1),
            centro_costo="CC-001")

    def test_centro_costo_duplicado_es_invalido(self):
        form = ProyectoForm(data={
            "nombre": "Obra 2", "mandante": "M", "centro_costo": "cc-001",
            "fecha_inicio": "2026-06-01", "estado": "PLANIFICACION",
            "presupuesto_total": 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("centro_costo", form.errors)

    def test_centro_costo_nuevo_es_valido(self):
        form = ProyectoForm(data={
            "nombre": "Obra 2", "mandante": "M", "centro_costo": "CC-002",
            "fecha_inicio": "2026-06-01", "estado": "PLANIFICACION",
            "presupuesto_total": 0,
        })
        self.assertTrue(form.is_valid())


class JefeProyectoTest(TestCase):
    """CU-08: asignación de jefe de proyecto."""

    def test_asignar_jefe_de_proyecto(self):
        from usuarios.models import Usuario
        jefe = Usuario.objects.create_user(
            username="jp08", password="x", email="jp08@m5.cl", rol="JEFE_PROYECTO")
        p = Proyecto.objects.create(
            nombre="Obra con Jefe", mandante="M", fecha_inicio=date(2026, 6, 1),
            jefe_proyecto=jefe)
        self.assertEqual(p.jefe_proyecto.username, "jp08")
        self.assertEqual(p.jefe_proyecto.rol, "JEFE_PROYECTO")


# ==========================================================================
#  Asignación de jefe de proyecto y exportación de la ficha a PDF
# ==========================================================================
class JefeProyectoAsignableTest(TestCase):
    """Un usuario que todavía espera aprobación (CU-52) no puede recibir
    asignaciones: no debe aparecer en el selector de jefe de proyecto."""

    def setUp(self):
        from usuarios.models import Usuario
        self.aprobado = Usuario.objects.create_user(
            username="jefe_ok", password="clave12345", email="ok@m5.cl",
            rol="JEFE_PROYECTO")
        self.pendiente = Usuario.objects.create_user(
            username="jefe_pend", password="clave12345", email="pend@m5.cl",
            rol="JEFE_PROYECTO", pendiente_aprobacion=True)
        self.inactivo = Usuario.objects.create_user(
            username="jefe_off", password="clave12345", email="off@m5.cl",
            rol="JEFE_PROYECTO", estado=False)

    def test_selector_solo_muestra_jefes_aprobados_y_activos(self):
        opciones = list(ProyectoForm().fields["jefe_proyecto"].queryset)
        self.assertIn(self.aprobado, opciones)
        self.assertNotIn(self.pendiente, opciones)
        self.assertNotIn(self.inactivo, opciones)

    def test_jefe_ya_asignado_se_conserva_aunque_quede_inactivo(self):
        """Editar un proyecto antiguo no debe borrarle el jefe en silencio."""
        proyecto = Proyecto.objects.create(
            nombre="Obra antigua", mandante="M", fecha_inicio=date(2026, 1, 10),
            jefe_proyecto=self.inactivo)
        opciones = list(ProyectoForm(instance=proyecto).fields["jefe_proyecto"].queryset)
        self.assertIn(self.inactivo, opciones)
        self.assertIn(self.aprobado, opciones)
        self.assertNotIn(self.pendiente, opciones)

    def test_helper_filtra_por_rol(self):
        from usuarios.models import Usuario, usuarios_asignables
        Usuario.objects.create_user(
            username="bodega_ok", password="clave12345", email="b@m5.cl",
            rol="BODEGUERO")
        asignables = usuarios_asignables("JEFE_PROYECTO")
        self.assertEqual(list(asignables), [self.aprobado])


class ProyectoPDFTest(TestCase):
    """Exportación de la ficha del proyecto para compartir con el mandante."""

    def setUp(self):
        from usuarios.models import Usuario
        self.jefe = Usuario.objects.create_user(
            username="jefe_pdf", password="clave12345", email="pdf@m5.cl",
            rol="JEFE_PROYECTO", first_name="Camila", last_name="Rojas")
        self.client.login(username="jefe_pdf", password="clave12345")
        self.proyecto = Proyecto.objects.create(
            nombre="Edificio Aurora", mandante="Inmobiliaria Vista SpA",
            centro_costo="CC-2026-014", jefe_proyecto=self.jefe,
            fecha_inicio=date(2026, 6, 1), presupuesto_total=125000000)
        Itemizado.objects.create(
            proyecto=self.proyecto, codigo_partida="02.03",
            descripcion="Estructura metálica", unidad_medida="kg",
            cant_presupuestada=1500, cant_ejecutada=400)

    def test_descarga_pdf(self):
        from django.urls import reverse
        resp = self.client.get(reverse("proyectos:pdf", args=[self.proyecto.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))
        self.assertIn("edificio-aurora", resp["Content-Disposition"])

    def test_pdf_funciona_sin_itemizado_ni_jefe(self):
        vacio = Proyecto.objects.create(
            nombre="Obra sin datos", mandante="M", fecha_inicio=date(2026, 7, 1))
        from django.urls import reverse
        resp = self.client.get(reverse("proyectos:pdf", args=[vacio.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_boton_de_exportar_aparece_en_el_detalle(self):
        from django.urls import reverse
        resp = self.client.get(reverse("proyectos:detalle", args=[self.proyecto.pk]))
        self.assertContains(resp, reverse("proyectos:pdf", args=[self.proyecto.pk]))


# ==========================================================================
#  CU-54 (RF-51) — Almacenando archivo y clasificándolo por tipo de documento
# ==========================================================================

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ArchivoProyectoCU54Test(TestCase):
    """
    Flujo principal: el actor sube un archivo, le pone nombre y lo clasifica con
    un tipo del catálogo; el sistema lo almacena contra el proyecto.
    Excepción 1: sin tipo seleccionado —o con el catálogo vacío— la carga se
    bloquea y el archivo no queda guardado.
    """

    def setUp(self):
        self.client = Client()
        self.jefe = Usuario.objects.create_user(
            username="jefe54", password="clave12345", email="j54@m5.cl",
            rol="JEFE_PROYECTO")
        self.conta = Usuario.objects.create_user(
            username="conta54", password="clave12345", email="c54@m5.cl",
            rol="CONTABILIDAD")
        self.bodega = Usuario.objects.create_user(
            username="bod54", password="clave12345", email="b54@m5.cl",
            rol="BODEGUERO")
        self.proyecto = Proyecto.objects.create(
            nombre="Torre Poniente", mandante="Inmobiliaria X",
            fecha_inicio=date(2026, 6, 1))
        self.tipo = TipoDocumento.objects.create(
            nombre="Plano", descripcion="Planimetría")
        self.client.login(username="jefe54", password="clave12345")

    def _pdf(self, nombre="plano.pdf"):
        return SimpleUploadedFile(nombre, b"%PDF-1.4 contenido", content_type="application/pdf")

    def _url(self):
        return reverse("proyectos:archivo_subir", args=[self.proyecto.pk])

    # --- catálogo ---

    def test_el_catalogo_responde_si_hay_tipos_activos(self):
        self.assertTrue(TipoDocumento.hay_catalogo())
        self.tipo.activo = False
        self.tipo.save()
        self.assertFalse(TipoDocumento.hay_catalogo())

    def test_el_formulario_solo_ofrece_tipos_activos(self):
        TipoDocumento.objects.create(nombre="Obsoleto", activo=False)
        form = ArchivoProyectoForm()
        nombres = [t.nombre for t in form.fields["tipo"].queryset]
        self.assertIn("Plano", nombres)
        self.assertNotIn("Obsoleto", nombres)

    # --- flujo principal ---

    def test_sube_y_clasifica_el_archivo(self):
        resp = self.client.post(self._url(), {
            "tipo": self.tipo.pk,
            "nombre": "Plano de emplazamiento rev. C",
            "archivo": self._pdf(),
            "observaciones": "Entregado por arquitectura",
        })
        self.assertRedirects(resp, reverse("proyectos:detalle", args=[self.proyecto.pk]))
        archivo = ArchivoProyecto.objects.get()
        self.assertEqual(archivo.proyecto, self.proyecto)
        self.assertEqual(archivo.tipo, self.tipo)
        self.assertEqual(archivo.subido_por, self.jefe)
        self.assertEqual(archivo.extension, "pdf")

    def test_el_archivo_aparece_en_la_ficha_del_proyecto(self):
        self.client.post(self._url(), {
            "tipo": self.tipo.pk, "nombre": "Contrato firmado",
            "archivo": self._pdf("contrato.pdf")})
        resp = self.client.get(reverse("proyectos:detalle", args=[self.proyecto.pk]))
        self.assertContains(resp, "Contrato firmado")
        self.assertContains(resp, "Plano")  # el tipo con que quedó clasificado

    def test_contabilidad_tambien_puede_almacenar(self):
        self.client.login(username="conta54", password="clave12345")
        self.client.post(self._url(), {
            "tipo": self.tipo.pk, "nombre": "Factura 1234",
            "archivo": self._pdf("f.pdf")})
        self.assertEqual(ArchivoProyecto.objects.count(), 1)

    def test_un_rol_ajeno_no_puede_almacenar(self):
        self.client.login(username="bod54", password="clave12345")
        resp = self.client.post(self._url(), {
            "tipo": self.tipo.pk, "nombre": "X", "archivo": self._pdf()})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(ArchivoProyecto.objects.count(), 0)

    # --- Excepción 1 ---

    def test_sin_tipo_no_se_almacena(self):
        resp = self.client.post(self._url(), {
            "tipo": "", "nombre": "Plano sin clasificar", "archivo": self._pdf()})
        self.assertEqual(resp.status_code, 200)   # vuelve a la ficha con el error
        self.assertEqual(ArchivoProyecto.objects.count(), 0)
        self.assertContains(resp, "selecciona un tipo")

    def test_con_el_catalogo_vacio_la_carga_queda_bloqueada(self):
        TipoDocumento.objects.all().delete()
        resp = self.client.post(self._url(), {
            "nombre": "Cualquiera", "archivo": self._pdf()}, follow=True)
        self.assertEqual(ArchivoProyecto.objects.count(), 0)
        self.assertContains(resp, "catálogo")

    def test_la_ficha_avisa_cuando_el_catalogo_esta_vacio(self):
        TipoDocumento.objects.all().delete()
        resp = self.client.get(reverse("proyectos:detalle", args=[self.proyecto.pk]))
        self.assertContains(resp, "No se pueden almacenar archivos todav")
        self.assertNotContains(resp, "Almacenar archivo</button>")

    def test_formato_no_permitido_se_rechaza(self):
        malo = SimpleUploadedFile("script.exe", b"MZ", content_type="application/octet-stream")
        resp = self.client.post(self._url(), {
            "tipo": self.tipo.pk, "nombre": "Ejecutable", "archivo": malo})
        self.assertEqual(ArchivoProyecto.objects.count(), 0)
        self.assertContains(resp, "Formato no permitido")

    def test_sin_nombre_no_se_almacena(self):
        resp = self.client.post(self._url(), {
            "tipo": self.tipo.pk, "nombre": "   ", "archivo": self._pdf()})
        self.assertEqual(ArchivoProyecto.objects.count(), 0)
        self.assertContains(resp, "nombre al documento")

    # --- catálogo administrable ---

    def test_agregar_un_tipo_destraba_el_catalogo(self):
        TipoDocumento.objects.all().delete()
        self.client.post(reverse("proyectos:tipo_documento_crear"),
                         {"nombre": "Permiso municipal", "activo": "on"})
        self.assertTrue(TipoDocumento.hay_catalogo())

    def test_el_listado_del_catalogo_se_muestra(self):
        resp = self.client.get(reverse("proyectos:tipos_documento"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Plano")

    def test_eliminar_saca_el_documento_de_la_carpeta(self):
        self.client.post(self._url(), {
            "tipo": self.tipo.pk, "nombre": "Borrable", "archivo": self._pdf()})
        archivo = ArchivoProyecto.objects.get()
        self.client.post(reverse("proyectos:archivo_eliminar", args=[archivo.pk]))
        self.assertEqual(ArchivoProyecto.objects.count(), 0)


# ==========================================================================
#  CU-57 / CU-58 / CU-59 — Umbral de tamaño y edición offline con bloqueo
# ==========================================================================

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class EdicionOfflineTest(TestCase):
    """
    CU-58 (RF-55) y CU-59 (RF-56): el archivo se bloquea mientras alguien lo
    tiene fuera del sistema, y se libera al subir la versión editada.
    """

    def setUp(self):
        self.client = Client()
        self.jefe = Usuario.objects.create_user(
            "jp_off", password="clave12345", email="j@m5.cl", rol="JEFE_PROYECTO")
        self.conta = Usuario.objects.create_user(
            "cont_off", password="clave12345", email="c@m5.cl", rol="CONTABILIDAD")
        self.admin = Usuario.objects.create_user(
            "adm_off", password="clave12345", email="a@m5.cl", rol="ADMIN")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra Offline", mandante="M5", fecha_inicio=date(2026, 6, 1))
        self.tipo = TipoDocumento.objects.create(nombre="Plano")
        self.archivo = ArchivoProyecto.objects.create(
            proyecto=self.proyecto, tipo=self.tipo, nombre="Plano estructura",
            archivo=SimpleUploadedFile("plano.dwg", b"contenido dwg"),
            subido_por=self.jefe)
        self.client.login(username="jp_off", password="clave12345")

    # --- CU-58 ---

    def test_bloquear_deja_el_archivo_a_nombre_del_actor(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        self.archivo.refresh_from_db()
        self.assertEqual(self.archivo.bloqueado_por, self.jefe)
        self.assertIsNotNone(self.archivo.bloqueado_desde)
        self.assertTrue(self.archivo.bloqueado)

    def test_la_ficha_muestra_quien_lo_tiene(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        self.client.login(username="cont_off", password="clave12345")
        resp = self.client.get(reverse("proyectos:detalle", args=[self.proyecto.pk]))
        self.assertContains(resp, "jp_off")

    # --- Excepción 1 del CU-58: ya bloqueado por otro ---

    def test_otro_usuario_no_lo_puede_tomar_y_se_le_dice_quien_lo_tiene(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        self.client.login(username="cont_off", password="clave12345")
        resp = self.client.post(
            reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]), follow=True)
        self.assertContains(resp, "jp_off")
        self.archivo.refresh_from_db()
        self.assertEqual(self.archivo.bloqueado_por, self.jefe)   # no cambió de dueño

    # --- CU-59 ---

    def test_subir_la_version_editada_reemplaza_y_libera(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        resp = self.client.post(
            reverse("proyectos:archivo_version", args=[self.archivo.pk]),
            {"archivo": SimpleUploadedFile("plano.dwg", b"version corregida")},
            follow=True)
        self.archivo.refresh_from_db()
        self.assertFalse(self.archivo.bloqueado)
        self.assertEqual(self.archivo.version, 2)
        self.assertContains(resp, "versión 2")

    def test_no_se_puede_subir_sin_haber_bloqueado(self):
        resp = self.client.post(
            reverse("proyectos:archivo_version", args=[self.archivo.pk]),
            {"archivo": SimpleUploadedFile("plano.dwg", b"x")}, follow=True)
        self.assertContains(resp, "Primero tienes que bloquear")
        self.archivo.refresh_from_db()
        self.assertEqual(self.archivo.version, 1)

    def test_no_se_puede_subir_sobre_el_bloqueo_de_otro(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        self.client.login(username="cont_off", password="clave12345")
        self.client.post(reverse("proyectos:archivo_version", args=[self.archivo.pk]),
                         {"archivo": SimpleUploadedFile("plano.dwg", b"x")})
        self.archivo.refresh_from_db()
        self.assertEqual(self.archivo.version, 1)

    # --- Excepción 1 del CU-59: formato distinto ---

    def test_una_version_en_otro_formato_se_rechaza(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        resp = self.client.post(
            reverse("proyectos:archivo_version", args=[self.archivo.pk]),
            {"archivo": SimpleUploadedFile("plano.pdf", b"%PDF-1.4")}, follow=True)
        self.assertContains(resp, "tiene que venir en .dwg")
        self.archivo.refresh_from_db()
        self.assertEqual(self.archivo.version, 1)
        self.assertTrue(self.archivo.bloqueado)   # sigue tomado

    # --- liberar sin subir ---

    def test_se_puede_liberar_sin_subir_nada(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        self.client.post(reverse("proyectos:archivo_liberar", args=[self.archivo.pk]))
        self.archivo.refresh_from_db()
        self.assertFalse(self.archivo.bloqueado)

    def test_el_administrador_destraba_un_archivo_ajeno(self):
        """Alguien se fue de la empresa con un archivo tomado: hay que poder soltarlo."""
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        self.client.login(username="adm_off", password="clave12345")
        self.client.post(reverse("proyectos:archivo_liberar", args=[self.archivo.pk]))
        self.archivo.refresh_from_db()
        self.assertFalse(self.archivo.bloqueado)

    def test_un_usuario_cualquiera_no_destraba_lo_ajeno(self):
        self.client.post(reverse("proyectos:archivo_bloquear", args=[self.archivo.pk]))
        self.client.login(username="cont_off", password="clave12345")
        self.client.post(reverse("proyectos:archivo_liberar", args=[self.archivo.pk]))
        self.archivo.refresh_from_db()
        self.assertTrue(self.archivo.bloqueado)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class UmbralTamanoCU57Test(TestCase):
    """CU-57 (RF-54): advertir sobre el umbral, sin prohibir."""

    def setUp(self):
        self.client = Client()
        self.jefe = Usuario.objects.create_user(
            "jp57", password="clave12345", email="j57@m5.cl", rol="JEFE_PROYECTO")
        self.proyecto = Proyecto.objects.create(
            nombre="Obra Umbral", mandante="M5", fecha_inicio=date(2026, 6, 1))
        self.tipo = TipoDocumento.objects.create(nombre="Plano")
        # Umbral bajo para no tener que generar archivos enormes en la prueba
        parametros = ParametrosSistema.actuales()
        parametros.umbral_archivo_mb = 1
        parametros.save()
        self.client.login(username="jp57", password="clave12345")

    def _subir(self, tamano_bytes, **extra):
        datos = {"tipo": self.tipo.pk, "nombre": "Plano pesado",
                 "archivo": SimpleUploadedFile("grande.pdf", b"x" * tamano_bytes)}
        datos.update(extra)
        return self.client.post(
            reverse("proyectos:archivo_subir", args=[self.proyecto.pk]), datos, follow=True)

    def test_bajo_el_umbral_sube_sin_molestar(self):
        self._subir(1000)
        self.assertEqual(ArchivoProyecto.objects.count(), 1)

    # --- Excepción 1: sobre el umbral se advierte ---

    def test_sobre_el_umbral_advierte_y_no_sube_todavia(self):
        resp = self._subir(2 * 1024 * 1024)
        self.assertEqual(ArchivoProyecto.objects.count(), 0)
        self.assertContains(resp, "comprimirlo")
        self.assertContains(resp, "subir de todas formas")

    def test_confirmando_sube_igual(self):
        """Advertir no es prohibir: un plano pesado a veces tiene que subir pesado."""
        self._subir(2 * 1024 * 1024, confirmar_tamano="1")
        self.assertEqual(ArchivoProyecto.objects.count(), 1)

    def test_el_umbral_sale_de_los_parametros_configurados(self):
        parametros = ParametrosSistema.actuales()
        parametros.umbral_archivo_mb = 50
        parametros.save()
        self._subir(2 * 1024 * 1024)
        self.assertEqual(ArchivoProyecto.objects.count(), 1)   # ya no lo advierte
