"""Formularios de Proveedores (CU-01 Registrar, CU-04 Editar, RF-05/06/07)."""
import os
from django import forms
from .models import Proveedor, ProveedorMaterial
from usuarios.validators import validar_rut, limpiar_rut


class ProveedorForm(forms.ModelForm):
    """
    CU-01 / CU-04. El registro pide sólo los datos identificatorios del
    proveedor. La condición de pago dejó de pedirse aquí: se negocia por
    material, en el catálogo (ver ProveedorMaterial.condicion_pago). El campo
    del modelo se conserva como valor por defecto para las órdenes de compra.

    En su lugar se ofrece cargar el catálogo del proveedor desde una planilla
    Excel, que es como los proveedores envían sus listas de precios.
    """

    EXT_PERMITIDAS = (".xlsx",)
    TAM_MAX_MB = 5

    catalogo = forms.FileField(
        label="Catálogo del proveedor (Excel)",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": ".xlsx",
        }),
        help_text=(
            "Opcional. Planilla .xlsx con las columnas: código, descripción, "
            "unidad, precio y condición de pago."
        ),
    )

    class Meta:
        model = Proveedor
        fields = ["nombre", "rut", "correo", "telefono", "estado"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Razón social"}),
            "rut": forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "estado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_rut(self):
        """CU-02 Validando RUT + CU-03 verificación anti-duplicado."""
        rut = self.cleaned_data["rut"]
        validar_rut(rut)  # CU-02
        rut_limpio = limpiar_rut(rut)
        # CU-03: no permitir RUT repetido (excluyendo el propio registro al editar)
        qs = Proveedor.objects.filter(rut=rut_limpio)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un proveedor registrado con este RUT.")
        return rut_limpio

    def clean_catalogo(self):
        archivo = self.cleaned_data.get("catalogo")
        if not archivo:
            return archivo
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in self.EXT_PERMITIDAS:
            raise forms.ValidationError(
                "Formato no permitido. La planilla debe ser .xlsx "
                "(en Excel: Archivo → Guardar como → Libro de Excel)."
            )
        if archivo.size > self.TAM_MAX_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"La planilla supera el tamaño máximo de {self.TAM_MAX_MB} MB."
            )
        return archivo


class ProveedorMaterialForm(forms.ModelForm):
    """
    RF-05 Agregar material al listado de un proveedor.
    RF-07 Editar código / unidad / descripción / precio / condición de pago
    (la fecha de última modificación se guarda sola vía auto_now en el modelo).
    """
    class Meta:
        model = ProveedorMaterial
        fields = ["codigo", "descripcion", "unidad_medida", "precio",
                  "condicion_pago", "disponible"]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Cód. proveedor"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Descripción del material"}),
            "unidad_medida": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "un, kg, m2..."}),
            "precio": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": "0", "step": "1"}),
            "condicion_pago": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, proveedor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._proveedor = proveedor
        if self._proveedor is None and getattr(self.instance, "proveedor_id", None):
            self._proveedor = self.instance.proveedor
        self.fields["condicion_pago"].required = False
        # El precio puede no conocerse al dar de alta el material (se completa
        # al recibir la lista del proveedor o al cotizar): queda en 0.
        self.fields["precio"].required = False
        if self._proveedor is not None:
            self.fields["condicion_pago"].widget.choices = [
                ("", f"— Usar la del proveedor ({self._proveedor.get_condicion_pago_display()}) —"),
            ] + list(ProveedorMaterial._meta.get_field("condicion_pago").choices)

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip()
        if not self._proveedor:
            return codigo
        qs = ProveedorMaterial.objects.filter(proveedor=self._proveedor, codigo__iexact=codigo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este proveedor ya tiene un material con ese código.")
        return codigo

    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio is None:
            return 0
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio


class CatalogoExcelForm(forms.Form):
    """Carga del catálogo desde la ficha de un proveedor ya registrado."""

    EXT_PERMITIDAS = ProveedorForm.EXT_PERMITIDAS
    TAM_MAX_MB = ProveedorForm.TAM_MAX_MB

    archivo = forms.FileField(
        label="Planilla del catálogo (.xlsx)",
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control form-control-sm",
            "accept": ".xlsx",
        }),
    )
    reemplazar = forms.BooleanField(
        label="Reemplazar el catálogo actual",
        required=False,
        help_text="Si se marca, los materiales que no vengan en la planilla quedan como no disponibles.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in self.EXT_PERMITIDAS:
            raise forms.ValidationError(
                "Formato no permitido. La planilla debe ser .xlsx."
            )
        if archivo.size > self.TAM_MAX_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"La planilla supera el tamaño máximo de {self.TAM_MAX_MB} MB."
            )
        return archivo
