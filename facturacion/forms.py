"""Formularios de Facturación (RF-40, RF-41)."""
import os
from django import forms

from proveedores.models import Proveedor
from adquisiciones.models import OrdenCompra
from .models import Factura


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ["numero", "proveedor", "ordenes", "fecha_emision",
                  "fecha_vencimiento", "monto_total", "archivo", "observacion"]
        widgets = {
            "numero": forms.TextInput(attrs={"class": "form-control"}),
            "proveedor": forms.Select(attrs={"class": "form-select"}),
            "ordenes": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "fecha_emision": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_vencimiento": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "monto_total": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.xml"}),
            "observacion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["proveedor"].queryset = Proveedor.objects.filter(estado=True)
        # RF-40: OC en estado Enviada (o con recepción) que aún no están facturadas
        self.fields["ordenes"].queryset = OrdenCompra.objects.filter(
            estado__in=[OrdenCompra.Estado.ENVIADA, OrdenCompra.Estado.RECEPCION_PARCIAL,
                        OrdenCompra.Estado.RECIBIDA],
            facturada=False,
        ).select_related("proveedor")

    def clean_numero(self):
        return (self.cleaned_data.get("numero") or "").strip()

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if not archivo:
            return archivo
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in (".pdf", ".xml"):
            raise forms.ValidationError("El archivo de la factura debe ser PDF o XML (RNF-11).")
        return archivo

    def clean(self):
        cleaned = super().clean()
        proveedor = cleaned.get("proveedor")
        ordenes = cleaned.get("ordenes")
        numero = cleaned.get("numero")
        emision = cleaned.get("fecha_emision")
        vencimiento = cleaned.get("fecha_vencimiento")

        if proveedor and numero:
            qs = Factura.objects.filter(proveedor=proveedor, numero__iexact=numero)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("numero", "Ya existe una factura con ese número para este proveedor.")

        if ordenes and proveedor:
            ajenas = [o.correlativo for o in ordenes if o.proveedor_id != proveedor.pk]
            if ajenas:
                self.add_error("ordenes", f"Estas OC no son del proveedor seleccionado: {', '.join(ajenas)}.")

        if emision and vencimiento and vencimiento < emision:
            self.add_error("fecha_vencimiento", "El vencimiento no puede ser anterior a la emisión.")

        return cleaned


class DesbloqueoForm(forms.Form):
    """RF-42: Administración desbloquea una factura bloqueada por diferencia de monto."""
    justificacion = forms.CharField(
        label="Justificación del desbloqueo",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
