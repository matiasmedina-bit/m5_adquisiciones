"""
Pruebas unitarias del módulo de Proveedores.
Cubre CU-01 (registrar), CU-02 (validar RUT), CU-03 (anti-duplicado), CU-05 (inactivar)
y el Incremento 2: RF-05 (agregar material), RF-06 (marcar no disponible), RF-07 (editar).
"""
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario
from .models import Proveedor, ProveedorMaterial
from .forms import ProveedorForm, ProveedorMaterialForm


class ProveedorModelTest(TestCase):

    def test_rut_se_normaliza_al_guardar(self):
        p = Proveedor.objects.create(nombre="Ferretería Sur", rut="11.111.111-1")
        self.assertEqual(p.rut, "111111111")  # sin puntos ni guion

    def test_rut_formateado(self):
        p = Proveedor.objects.create(nombre="Aceros Norte", rut="11111111-1")
        self.assertEqual(p.rut_formateado, "11.111.111-1")


class ProveedorFormTest(TestCase):
    """CU-02 y CU-03: validación de RUT y duplicados a través del formulario."""

    def test_form_rechaza_rut_invalido(self):
        form = ProveedorForm(data={"nombre": "X", "rut": "11.111.111-9", "condicion_pago": "CONTADO"})
        self.assertFalse(form.is_valid())
        self.assertIn("rut", form.errors)

    def test_form_rechaza_rut_duplicado(self):
        Proveedor.objects.create(nombre="Existe", rut="11111111-1")
        form = ProveedorForm(data={"nombre": "Nuevo", "rut": "11.111.111-1", "condicion_pago": "CONTADO"})
        self.assertFalse(form.is_valid())
        self.assertIn("rut", form.errors)

    def test_form_acepta_rut_valido_nuevo(self):
        form = ProveedorForm(data={"nombre": "Valido", "rut": "11.111.111-1", "condicion_pago": "CONTADO"})
        self.assertTrue(form.is_valid())


class ProveedorVistaTest(TestCase):
    """CU-05: inactivar proveedor."""

    def setUp(self):
        self.client = Client()
        Usuario.objects.create_user(username="ea", password="clave12345",
                                    email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea", password="clave12345")
        self.prov = Proveedor.objects.create(nombre="Test", rut="11111111-1")

    def test_inactivar_cambia_estado(self):
        self.assertTrue(self.prov.estado)
        self.client.get(reverse("proveedores:inactivar", args=[self.prov.pk]))
        self.prov.refresh_from_db()
        self.assertFalse(self.prov.estado)


class ProveedorMaterialTest(TestCase):
    """RF-05 / RF-06 / RF-07 — listado de materiales del proveedor."""

    def setUp(self):
        self.client = Client()
        Usuario.objects.create_user(username="ea", password="clave12345",
                                    email="ea@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea", password="clave12345")
        self.prov = Proveedor.objects.create(nombre="Ferretería Test", rut="11111111-1")

    def test_rf05_agregar_material(self):
        self.client.post(
            reverse("proveedores:material_agregar", args=[self.prov.pk]),
            {"codigo": "A-100", "descripcion": "Cemento 25kg", "unidad_medida": "saco", "disponible": "on"},
        )
        self.assertEqual(self.prov.materiales.count(), 1)

    def test_rf05_codigo_duplicado_por_proveedor(self):
        ProveedorMaterial.objects.create(proveedor=self.prov, codigo="A-100",
                                         descripcion="X", unidad_medida="un")
        form = ProveedorMaterialForm(
            data={"codigo": "A-100", "descripcion": "Y", "unidad_medida": "un", "disponible": True},
            proveedor=self.prov,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("codigo", form.errors)

    def test_rf06_marcar_no_disponible_no_borra(self):
        m = ProveedorMaterial.objects.create(proveedor=self.prov, codigo="A-1",
                                             descripcion="X", unidad_medida="un")
        self.client.get(reverse("proveedores:material_disponibilidad", args=[m.pk]))
        m.refresh_from_db()
        self.assertFalse(m.disponible)
        self.assertTrue(ProveedorMaterial.objects.filter(pk=m.pk).exists())

    def test_rf07_editar_actualiza_fecha_modificacion(self):
        m = ProveedorMaterial.objects.create(proveedor=self.prov, codigo="A-1",
                                             descripcion="X", unidad_medida="un")
        modificado_original = m.modificado
        self.client.post(
            reverse("proveedores:material_editar", args=[m.pk]),
            {"codigo": "A-1", "descripcion": "X mejorado", "unidad_medida": "kg", "disponible": "on"},
        )
        m.refresh_from_db()
        self.assertEqual(m.descripcion, "X mejorado")
        self.assertEqual(m.unidad_medida, "kg")
        self.assertGreaterEqual(m.modificado, modificado_original)

    def test_paginas_renderizan(self):
        ProveedorMaterial.objects.create(proveedor=self.prov, codigo="A-1",
                                         descripcion="X", unidad_medida="un")
        self.assertEqual(
            self.client.get(reverse("proveedores:detalle", args=[self.prov.pk])).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("proveedores:material_agregar", args=[self.prov.pk])).status_code, 200)
