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
