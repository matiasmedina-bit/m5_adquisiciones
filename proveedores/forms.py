"""Formularios de Proveedores (CU-01 Registrar, CU-04 Editar, RF-05/06/07)."""
from django import forms
from .models import Proveedor, ProveedorMaterial
from usuarios.validators import validar_rut, limpiar_rut


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "rut", "correo", "telefono", "condicion_pago", "estado"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Razón social"}),
            "rut": forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "condicion_pago": forms.Select(attrs={"class": "form-select"}),
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


class ProveedorMaterialForm(forms.ModelForm):
    """
    RF-05 Agregar material al listado de un proveedor.
    RF-07 Editar código / unidad / descripción (la fecha de última modificación
    se guarda sola vía auto_now en el modelo).
    """
    class Meta:
        model = ProveedorMaterial
        fields = ["codigo", "descripcion", "unidad_medida", "disponible"]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Cód. proveedor"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Descripción del material"}),
            "unidad_medida": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "un, kg, m2..."}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, proveedor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._proveedor = proveedor
        if self._proveedor is None and getattr(self.instance, "proveedor_id", None):
            self._proveedor = self.instance.proveedor

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
