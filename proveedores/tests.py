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


# ==========================================================================
#  Catálogo del proveedor: precio y condición por material + carga por Excel
# ==========================================================================
class CondicionPagoPorMaterialTest(TestCase):
    """La condición de pago se negocia por material; el proveedor sólo aporta
    un valor por defecto cuando el material no define el suyo."""

    def setUp(self):
        self.prov = Proveedor.objects.create(
            nombre="Ferretería Test", rut="11111111-1", condicion_pago="30_DIAS")

    def test_registro_no_pide_condicion_de_pago(self):
        self.assertNotIn("condicion_pago", ProveedorForm().fields)

    def test_registro_ofrece_carga_de_catalogo(self):
        self.assertIn("catalogo", ProveedorForm().fields)

    def test_material_sin_condicion_hereda_la_del_proveedor(self):
        m = ProveedorMaterial.objects.create(
            proveedor=self.prov, codigo="A-1", descripcion="X", unidad_medida="un")
        self.assertEqual(m.condicion_pago_efectiva, "30 días")

    def test_material_con_condicion_propia_manda(self):
        m = ProveedorMaterial.objects.create(
            proveedor=self.prov, codigo="A-2", descripcion="Y", unidad_medida="un",
            condicion_pago="CONTADO")
        self.assertEqual(m.condicion_pago_efectiva, "Contado")

    def test_precio_es_opcional_al_agregar_material(self):
        form = ProveedorMaterialForm(
            data={"codigo": "A-3", "descripcion": "Z", "unidad_medida": "un", "disponible": True},
            proveedor=self.prov,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["precio"], 0)

    def test_precio_negativo_es_invalido(self):
        form = ProveedorMaterialForm(
            data={"codigo": "A-4", "descripcion": "Z", "unidad_medida": "un",
                  "precio": "-100", "disponible": True},
            proveedor=self.prov,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("precio", form.errors)


class CatalogoExcelTest(TestCase):
    """Carga del catálogo desde la planilla que envía el proveedor."""

    def setUp(self):
        self.prov = Proveedor.objects.create(
            nombre="Ferretería Excel", rut="11111111-1", condicion_pago="CONTADO")

    @staticmethod
    def _planilla(filas, encabezados=None, filas_previas=0):
        """Arma un .xlsx en memoria, opcionalmente con filas de relleno arriba."""
        from io import BytesIO
        from openpyxl import Workbook
        libro = Workbook()
        hoja = libro.active
        for _ in range(filas_previas):
            hoja.append(["Constructora ejemplo", None, None])
        hoja.append(encabezados or ["Código", "Descripción", "Unidad", "Precio", "Condición de pago"])
        for fila in filas:
            hoja.append(fila)
        buffer = BytesIO()
        libro.save(buffer)
        buffer.seek(0)
        return buffer

    def test_carga_crea_materiales(self):
        from .catalogo_excel import importar_catalogo
        archivo = self._planilla([
            ["CEM-001", "Cemento Portland 25 kg", "saco", 5490, "30 días"],
            ["FIE-014", "Fierro estriado 8 mm", "un", 3990, "Contado"],
        ])
        resultado = importar_catalogo(self.prov, archivo)
        self.assertEqual(resultado.creados, 2)
        self.assertEqual(self.prov.materiales.count(), 2)
        cemento = self.prov.materiales.get(codigo="CEM-001")
        self.assertEqual(cemento.precio, 5490)
        self.assertEqual(cemento.condicion_pago, "30_DIAS")
        self.assertEqual(cemento.unidad_medida, "saco")

    def test_precio_con_formato_chileno(self):
        from .catalogo_excel import importar_catalogo
        archivo = self._planilla([["X-1", "Material", "un", "$ 1.234.500", "contado"]])
        importar_catalogo(self.prov, archivo)
        self.assertEqual(self.prov.materiales.get(codigo="X-1").precio, 1234500)

    def test_encabezados_equivalentes_y_filas_de_relleno(self):
        """Las planillas reales traen el logo arriba y encabezados distintos."""
        from .catalogo_excel import importar_catalogo
        archivo = self._planilla(
            [["SKU-9", "Arena gruesa", "m3", "18990", "60 dias corridos"]],
            encabezados=["Cod.", "Detalle", "U.M.", "Valor unitario", "Forma de pago"],
            filas_previas=3,
        )
        resultado = importar_catalogo(self.prov, archivo)
        self.assertEqual(resultado.creados, 1)
        material = self.prov.materiales.get(codigo="SKU-9")
        self.assertEqual(material.precio, 18990)
        self.assertEqual(material.condicion_pago, "60_DIAS")

    def test_codigo_existente_se_actualiza_no_se_duplica(self):
        from .catalogo_excel import importar_catalogo
        ProveedorMaterial.objects.create(
            proveedor=self.prov, codigo="CEM-001", descripcion="Antigua",
            unidad_medida="un", precio=1000)
        archivo = self._planilla([["CEM-001", "Cemento Portland 25 kg", "saco", 5490, ""]])
        resultado = importar_catalogo(self.prov, archivo)
        self.assertEqual(resultado.creados, 0)
        self.assertEqual(resultado.actualizados, 1)
        self.assertEqual(self.prov.materiales.count(), 1)
        self.assertEqual(self.prov.materiales.first().precio, 5490)

    def test_filas_invalidas_se_omiten_con_motivo(self):
        from .catalogo_excel import importar_catalogo
        archivo = self._planilla([
            ["", "Sin código", "un", 100, ""],
            ["OK-1", "", "un", 100, ""],
            ["OK-2", "Válido", "un", 100, ""],
        ])
        resultado = importar_catalogo(self.prov, archivo)
        self.assertEqual(resultado.creados, 1)
        self.assertEqual(len(resultado.omitidos), 2)

    def test_reemplazar_marca_no_disponibles_sin_borrar(self):
        """RF-06: nunca se elimina, para no romper el historial de OC."""
        from .catalogo_excel import importar_catalogo
        viejo = ProveedorMaterial.objects.create(
            proveedor=self.prov, codigo="VIEJO-1", descripcion="Descontinuado",
            unidad_medida="un")
        archivo = self._planilla([["NUEVO-1", "Vigente", "un", 100, ""]])
        resultado = importar_catalogo(self.prov, archivo, reemplazar=True)
        viejo.refresh_from_db()
        self.assertFalse(viejo.disponible)
        self.assertEqual(resultado.retirados, 1)
        self.assertTrue(ProveedorMaterial.objects.filter(pk=viejo.pk).exists())

    def test_planilla_sin_columnas_minimas_avisa(self):
        from .catalogo_excel import ErrorCatalogo, importar_catalogo
        archivo = self._planilla(
            [["algo", "otra cosa"]], encabezados=["Columna A", "Columna B"])
        with self.assertRaises(ErrorCatalogo):
            importar_catalogo(self.prov, archivo)

    def test_descarga_de_plantilla(self):
        Usuario.objects.create_user(username="ea2", password="clave12345",
                                    email="ea2@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea2", password="clave12345")
        resp = self.client.get(reverse("proveedores:catalogo_plantilla"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("spreadsheetml", resp["Content-Type"])


class CatalogoExcelVistasTest(TestCase):
    """La carga por Excel a través de las pantallas reales (multipart)."""

    def setUp(self):
        Usuario.objects.create_user(username="ea3", password="clave12345",
                                    email="ea3@m5.cl", rol="ENCARGADO_ADQUISICIONES")
        self.client.login(username="ea3", password="clave12345")

    @staticmethod
    def _archivo(filas):
        from django.core.files.uploadedfile import SimpleUploadedFile
        buffer = CatalogoExcelTest._planilla(filas)
        return SimpleUploadedFile(
            "catalogo.xlsx", buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_registrar_proveedor_con_catalogo_adjunto(self):
        resp = self.client.post(reverse("proveedores:crear"), {
            "nombre": "Comercial Andes", "rut": "11.111.111-1",
            "correo": "ventas@andes.cl", "telefono": "+56 9 1111 1111",
            "estado": "on",
            "catalogo": self._archivo([
                ["AND-1", "Perfil metálico 100x50", "un", "12.900", "30 días"],
                ["AND-2", "Plancha zinc 0.35", "un", "8.490", "contado"],
            ]),
        })
        self.assertEqual(resp.status_code, 302)
        proveedor = Proveedor.objects.get(rut="111111111")
        self.assertEqual(proveedor.materiales.count(), 2)
        self.assertEqual(proveedor.materiales.get(codigo="AND-1").precio, 12900)
        # Redirige a la ficha para que se vea el catálogo recién cargado
        self.assertEqual(resp["Location"], reverse("proveedores:detalle", args=[proveedor.pk]))

    def test_registrar_proveedor_sin_catalogo_sigue_funcionando(self):
        resp = self.client.post(reverse("proveedores:crear"), {
            "nombre": "Sin Catálogo", "rut": "11.111.111-1", "estado": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Proveedor.objects.filter(rut="111111111").exists())

    def test_cargar_catalogo_desde_la_ficha(self):
        proveedor = Proveedor.objects.create(nombre="Ya Existe", rut="11111111-1")
        resp = self.client.post(
            reverse("proveedores:catalogo_cargar", args=[proveedor.pk]),
            {"archivo": self._archivo([["Z-1", "Material nuevo", "un", 500, ""]])},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(proveedor.materiales.count(), 1)

    def test_archivo_que_no_es_xlsx_se_rechaza(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        proveedor = Proveedor.objects.create(nombre="Otro", rut="11111111-1")
        malo = SimpleUploadedFile("lista.csv", b"codigo,descripcion", content_type="text/csv")
        self.client.post(
            reverse("proveedores:catalogo_cargar", args=[proveedor.pk]),
            {"archivo": malo},
        )
        self.assertEqual(proveedor.materiales.count(), 0)
