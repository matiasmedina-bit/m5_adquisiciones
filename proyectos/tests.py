"""
Pruebas unitarias del módulo de Proyectos e Itemizado (CU-06 a CU-10).
"""
from datetime import date
from django.test import TestCase
from django.db import IntegrityError
from .models import Proyecto, Itemizado
from .forms import ProyectoForm


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
