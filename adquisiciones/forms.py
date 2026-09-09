"""Formularios del módulo de Adquisiciones (RF-20 a RF-27, RF-38)."""
from django import forms
from django.forms import modelformset_factory

from proveedores.models import Proveedor
from .models import Cotizacion, OrdenCompra, OrdenCompraLinea


class CotizacionForm(forms.ModelForm):
    """RF-20: cabecera de la cotización (proveedor, despacho, tiempo de entrega)."""
    class Meta:
        model = Cotizacion
        fields = ["proveedor", "costo_despacho", "tiempo_entrega_dias"]
        widgets = {
            "proveedor": forms.Select(attrs={"class": "form-select"}),
            "costo_despacho": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "tiempo_entrega_dias": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, solicitud=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._solicitud = solicitud
        qs = Proveedor.objects.filter(estado=True)
        if solicitud is not None:
            ya_cotizaron = solicitud.cotizaciones.values_list("proveedor_id", flat=True)
            qs = qs.exclude(pk__in=list(ya_cotizaron))
        self.fields["proveedor"].queryset = qs


class OrdenRechazoForm(forms.Form):
    """RF-24: el Jefe de Proyecto rechaza el borrador de OC indicando el motivo."""
    motivo = forms.CharField(
        label="Motivo del rechazo",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )


class OrdenLineaEditForm(forms.ModelForm):
    """RF-25: editar cantidad / valor unitario de una OC rechazada."""
    class Meta:
        model = OrdenCompraLinea
        fields = ["cantidad", "valor_unitario"]
        widgets = {
            "cantidad": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": "0.01", "step": "0.01"}),
            "valor_unitario": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": 0}),
        }


OrdenLineaFormSet = modelformset_factory(
    OrdenCompraLinea, form=OrdenLineaEditForm, extra=0
)


class RecepcionEstadoForm(forms.Form):
    """RF-38: Adquisiciones actualiza el estado de recepción de una OC enviada."""
    ESTADOS = [
        (OrdenCompra.Estado.RECIBIDA, "Recibida"),
        (OrdenCompra.Estado.RECEPCION_PARCIAL, "Recepción parcial"),
        (OrdenCompra.Estado.NO_RECIBIDA, "No recibida"),
    ]
    estado = forms.ChoiceField(choices=ESTADOS, widget=forms.Select(attrs={"class": "form-select"}))
    nota = forms.CharField(
        required=False, label="Nota (opcional)",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
