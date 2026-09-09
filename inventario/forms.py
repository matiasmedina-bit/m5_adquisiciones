"""Formularios de Inventario / Bodega.
Catálogo (Inc.1) + movimientos y préstamos del Incremento 2 (RF-28 a RF-37)."""
from django import forms

from proyectos.models import Proyecto
from adquisiciones.models import OrdenCompra
from .models import Material, MovimientoInventario, PrestamoHerramienta


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["nombre", "unidad_medida", "stock_actual", "stock_minimo", "ubicacion",
                  "precio_referencia", "tipo", "codigo_activo", "fecha_vencimiento", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "unidad_medida": forms.TextInput(attrs={"class": "form-control"}),
            "stock_actual": forms.NumberInput(attrs={"class": "form-control"}),
            "stock_minimo": forms.NumberInput(attrs={"class": "form-control"}),
            "ubicacion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Estante 3 - Bodega central"}),
            "precio_referencia": forms.NumberInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "codigo_activo": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_vencimiento": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class EntradaForm(forms.Form):
    """RF-28/29/30: entrada de materiales (recepción de OC o retorno de obra)."""
    ORIGENES = [("OC", "Recepción desde proveedor (Orden de Compra)"),
                ("PROYECTO", "Retorno de sobrantes desde una obra")]
    origen = forms.ChoiceField(label="Origen de la entrada", choices=ORIGENES,
                               widget=forms.Select(attrs={"class": "form-select"}))
    orden_compra = forms.ModelChoiceField(
        label="Orden de compra", required=False,
        queryset=OrdenCompra.objects.filter(
            estado__in=[OrdenCompra.Estado.ENVIADA, OrdenCompra.Estado.RECEPCION_PARCIAL]),
        widget=forms.Select(attrs={"class": "form-select"}))
    proyecto = forms.ModelChoiceField(
        label="Proyecto de origen", required=False,
        queryset=Proyecto.objects.exclude(estado=Proyecto.Estado.FINALIZADO),
        widget=forms.Select(attrs={"class": "form-select"}))
    material = forms.ModelChoiceField(
        label="Material", queryset=Material.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}))
    cantidad = forms.DecimalField(
        label="Cantidad recibida", min_value=0.01, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    ubicacion = forms.CharField(
        label="Ubicación física", max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Contenedor Obra A, Estante 3"}))
    observacion = forms.CharField(
        label="Observación", required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))

    def clean(self):
        cleaned = super().clean()
        origen = cleaned.get("origen")
        oc = cleaned.get("orden_compra")
        proyecto = cleaned.get("proyecto")
        material = cleaned.get("material")
        cantidad = cleaned.get("cantidad")

        if origen == "OC":
            if not oc:
                self.add_error("orden_compra", "Selecciona la orden de compra recibida.")
            elif material and cantidad is not None:
                # RF-29: la cantidad recibida no puede superar la cantidad de la OC
                linea = oc.lineas.filter(material=material).first()
                if not linea:
                    self.add_error("material", "Ese material no pertenece a la orden de compra seleccionada.")
                else:
                    pendiente = linea.cantidad - linea.cantidad_recibida
                    if cantidad > pendiente:
                        self.add_error(
                            "cantidad",
                            f"La cantidad ({cantidad}) supera lo pendiente de la OC "
                            f"para este material ({pendiente}).",
                        )
        elif origen == "PROYECTO" and not proyecto:
            self.add_error("proyecto", "Selecciona el proyecto de origen.")
        return cleaned


class SalidaForm(forms.Form):
    """RF-31: salida de materiales/herramientas de bodega hacia una obra."""
    material = forms.ModelChoiceField(
        label="Material / herramienta", queryset=Material.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}))
    cantidad = forms.DecimalField(
        label="Cantidad", min_value=0.01, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    proyecto = forms.ModelChoiceField(
        label="Proyecto destino",
        queryset=Proyecto.objects.exclude(estado=Proyecto.Estado.FINALIZADO),
        widget=forms.Select(attrs={"class": "form-select"}))
    jefe_proyecto = forms.ModelChoiceField(
        label="Jefe de proyecto asignado", required=False,
        queryset=None, widget=forms.Select(attrs={"class": "form-select"}))
    guia_despacho = forms.CharField(
        label="N° guía de despacho", max_length=40,
        widget=forms.TextInput(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from usuarios.models import Usuario
        self.fields["jefe_proyecto"].queryset = Usuario.objects.filter(
            rol="JEFE_PROYECTO", estado=True)

    def clean(self):
        cleaned = super().clean()
        material = cleaned.get("material")
        cantidad = cleaned.get("cantidad")
        if material and cantidad is not None and cantidad > material.stock_actual:
            self.add_error("cantidad",
                           f"Stock insuficiente. Disponible: {material.stock_actual}.")
        return cleaned


class MermaForm(forms.Form):
    """RF-35: merma o pérdida de material (motivo Daño / Robo)."""
    material = forms.ModelChoiceField(
        label="Material / herramienta", queryset=Material.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}))
    cantidad = forms.DecimalField(
        label="Cantidad", min_value=0.01, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    motivo = forms.ChoiceField(
        label="Motivo", choices=MovimientoInventario.MotivoMerma.choices,
        widget=forms.Select(attrs={"class": "form-select"}))
    observacion = forms.CharField(
        label="Observación", required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))

    def clean(self):
        cleaned = super().clean()
        material = cleaned.get("material")
        cantidad = cleaned.get("cantidad")
        if material and cantidad is not None and cantidad > material.stock_actual:
            self.add_error("cantidad",
                           f"No puedes registrar más merma que el stock actual ({material.stock_actual}).")
        return cleaned


class DevolucionProveedorForm(forms.Form):
    """RF-36: devolución de material a un proveedor, asociada a una OC."""
    orden_compra = forms.ModelChoiceField(
        label="Orden de compra de origen",
        queryset=OrdenCompra.objects.exclude(estado=OrdenCompra.Estado.BORRADOR),
        widget=forms.Select(attrs={"class": "form-select"}))
    material = forms.ModelChoiceField(
        label="Material", queryset=Material.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}))
    cantidad = forms.DecimalField(
        label="Cantidad devuelta", min_value=0.01, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    guia_despacho = forms.CharField(
        label="N° guía de despacho", max_length=40,
        widget=forms.TextInput(attrs={"class": "form-control"}))
    motivo = forms.ChoiceField(
        label="Motivo", choices=MovimientoInventario.MotivoDevolucion.choices,
        widget=forms.Select(attrs={"class": "form-select"}))

    def clean(self):
        cleaned = super().clean()
        material = cleaned.get("material")
        cantidad = cleaned.get("cantidad")
        if material and cantidad is not None and cantidad > material.stock_actual:
            self.add_error("cantidad",
                           f"Stock insuficiente para devolver ({material.stock_actual} disponibles).")
        return cleaned


class PrestamoForm(forms.ModelForm):
    """RF-33: registrar el préstamo de una herramienta (activo fijo)."""
    class Meta:
        model = PrestamoHerramienta
        fields = ["herramienta", "jefe_proyecto", "proyecto",
                  "fecha_salida", "fecha_devolucion_esperada"]
        widgets = {
            "herramienta": forms.Select(attrs={"class": "form-select"}),
            "jefe_proyecto": forms.Select(attrs={"class": "form-select"}),
            "proyecto": forms.Select(attrs={"class": "form-select"}),
            "fecha_salida": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_devolucion_esperada": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["herramienta"].queryset = Material.objects.filter(
            tipo=Material.Tipo.HERRAMIENTA, activo=True)
        self.fields["proyecto"].queryset = Proyecto.objects.exclude(
            estado=Proyecto.Estado.FINALIZADO)

    def clean(self):
        cleaned = super().clean()
        salida = cleaned.get("fecha_salida")
        esperada = cleaned.get("fecha_devolucion_esperada")
        if salida and esperada and esperada < salida:
            self.add_error("fecha_devolucion_esperada",
                           "La devolución esperada no puede ser anterior a la salida.")
        herramienta = cleaned.get("herramienta")
        if herramienta and herramienta.herramienta_prestada:
            self.add_error("herramienta", "Esta herramienta ya está prestada.")
        return cleaned
