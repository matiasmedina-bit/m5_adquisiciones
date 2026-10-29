"""Formularios del módulo de Adquisiciones (RF-20 a RF-27, RF-38)."""
from django import forms
from django.forms import modelformset_factory

from inventario.models import Material
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


class OrdenDirectaForm(forms.ModelForm):
    """
    Compra que decide Adquisiciones, sin que ninguna obra la haya pedido.

    Es el caso de adelantarse: comprar el fierro antes de que la obra parta,
    tomar un precio que está bueno hoy, o reponer lo que siempre se gasta. Pide
    la obra a la que se imputa —para que el gasto no quede en el aire— y el
    proveedor, que es con quien se cierra el trato.
    """
    class Meta:
        model = OrdenCompra
        fields = ["proyecto", "proveedor", "costo_despacho"]
        labels = {
            "proyecto": "Obra a la que se carga",
            "proveedor": "Proveedor",
            "costo_despacho": "Costo de despacho (CLP)",
        }
        widgets = {
            "proyecto": forms.Select(attrs={"class": "form-select"}),
            "proveedor": forms.Select(attrs={"class": "form-select"}),
            "costo_despacho": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from proyectos.models import Proyecto
        self.fields["proyecto"].queryset = Proyecto.objects.exclude(
            estado=Proyecto.Estado.FINALIZADO).order_by("nombre")
        self.fields["proyecto"].required = True
        self.fields["proveedor"].queryset = Proveedor.objects.filter(
            estado=True).order_by("nombre")
        self.fields["costo_despacho"].required = False


class OrdenDirectaLineaForm(forms.ModelForm):
    """Un material de la compra anticipada, con lo que se acordó pagar por él."""
    class Meta:
        model = OrdenCompraLinea
        fields = ["material", "cantidad", "valor_unitario"]
        widgets = {
            "material": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "cantidad": forms.NumberInput(attrs={
                "class": "form-control form-control-sm", "min": "0.01", "step": "0.01"}),
            "valor_unitario": forms.NumberInput(attrs={
                "class": "form-control form-control-sm", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["material"].queryset = Material.objects.order_by("nombre")
        for campo in self.fields.values():
            campo.required = False

    def clean(self):
        datos = super().clean()
        material = datos.get("material")
        cantidad = datos.get("cantidad")
        valor = datos.get("valor_unitario")
        # Una fila vacía es sólo una fila que no se usó: se descarta sin ruido.
        if not material and not cantidad and valor in (None, ""):
            return datos
        if not material:
            self.add_error("material", "Elige el material.")
        if not cantidad or cantidad <= 0:
            self.add_error("cantidad", "Indica una cantidad mayor que cero.")
        if valor in (None, "") or valor < 0:
            self.add_error("valor_unitario", "Indica el valor unitario.")
        return datos


OrdenDirectaLineaFormSet = modelformset_factory(
    OrdenCompraLinea, form=OrdenDirectaLineaForm, extra=5, can_delete=False,
)
