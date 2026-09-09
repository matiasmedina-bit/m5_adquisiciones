"""Formularios de Solicitudes (CU-11 Generar, CU-12 Agregar ítems, CU-14 Editar).
Incremento 2: RF-16 (justificación por exceso de itemizado), RF-17 (adjuntos)."""
import os
from django import forms
from django.forms import inlineformset_factory
from .models import SolicitudMaterial, SolicitudDetalle, SolicitudAdjunto
from inventario.models import Material
from proyectos.models import Itemizado


class SolicitudForm(forms.ModelForm):
    """CU-11 Generando solicitud (cabecera)."""
    class Meta:
        model = SolicitudMaterial
        fields = ["proyecto", "observaciones"]
        widgets = {
            "proyecto": forms.Select(attrs={"class": "form-select"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from proyectos.models import Proyecto
        self.fields["proyecto"].queryset = Proyecto.objects.exclude(
            estado=Proyecto.Estado.FINALIZADO
        )

    def clean_proyecto(self):
        proyecto = self.cleaned_data["proyecto"]
        if proyecto and proyecto.esta_finalizado:
            raise forms.ValidationError(
                "No se pueden generar solicitudes para un proyecto finalizado."
            )
        return proyecto


class SolicitudDetalleForm(forms.ModelForm):
    """CU-12 Agregando ítems (líneas) a la solicitud.
    RF-16: si la cantidad supera el saldo de la partida del itemizado, exige justificación."""

    nombre_libre = forms.CharField(
        label="O escribir nombre del material",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "Ej: Tornillo 1/2 pulgada",
        }),
    )

    class Meta:
        model = SolicitudDetalle
        fields = ["material", "cantidad_solicitada", "unidad_medida", "partida", "justificacion"]
        widgets = {
            "material": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "cantidad_solicitada": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": "0.01", "step": "0.01"}),
            "unidad_medida": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "unidad (ej: kg, m2)"}),
            "partida": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "justificacion": forms.Textarea(attrs={"class": "form-control form-control-sm", "rows": 2,
                                                   "placeholder": "Requerida si la cantidad supera el saldo del itemizado"}),
        }

    def __init__(self, *args, solicitud=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._solicitud = solicitud
        if self._solicitud is None and getattr(self.instance, "solicitud_id", None):
            self._solicitud = self.instance.solicitud
        self.fields["material"].queryset = Material.objects.filter(activo=True)
        self.fields["material"].empty_label = "— Seleccionar del catálogo —"
        self.fields["material"].required = False
        self.fields["unidad_medida"].required = False
        self.fields["partida"].required = False
        self.fields["justificacion"].required = False
        if self._solicitud is not None:
            self.fields["partida"].queryset = Itemizado.objects.filter(
                proyecto=self._solicitud.proyecto
            )
            self.fields["partida"].empty_label = "— Sin partida —"
        else:
            self.fields["partida"].queryset = Itemizado.objects.none()

    def clean_cantidad_solicitada(self):
        cantidad = self.cleaned_data.get("cantidad_solicitada")
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return cantidad

    def clean(self):
        cleaned = super().clean()
        material = cleaned.get("material")
        nombre_libre = cleaned.get("nombre_libre", "").strip()

        if not material and not nombre_libre:
            # fila completamente vacía → la ignoramos (formset extra vacío)
            return cleaned

        if not material and nombre_libre:
            unidad = cleaned.get("unidad_medida") or "unidad"
            material_obj, _ = Material.objects.get_or_create(
                nombre__iexact=nombre_libre,
                defaults={"nombre": nombre_libre, "unidad_medida": unidad},
            )
            cleaned["material"] = material_obj

        # RF-16: alerta / justificación obligatoria si excede el saldo del itemizado
        partida = cleaned.get("partida")
        cantidad = cleaned.get("cantidad_solicitada")
        justificacion = (cleaned.get("justificacion") or "").strip()
        if partida and cantidad is not None and cantidad > partida.saldo_disponible and not justificacion:
            self.add_error(
                "justificacion",
                f"La cantidad ({cantidad}) supera el saldo de la partida "
                f"«{partida.codigo_partida}» ({partida.saldo_disponible}). "
                f"Debes ingresar una justificación.",
            )
        return cleaned


class SolicitudAdjuntoForm(forms.ModelForm):
    """RF-17: subir un archivo de respaldo (PDF/JPG, máx 5 MB, hasta 3 por SM)."""
    class Meta:
        model = SolicitudAdjunto
        fields = ["archivo", "nombre"]
        widgets = {
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control form-control-sm",
                                                       "accept": ".pdf,.jpg,.jpeg"}),
            "nombre": forms.TextInput(attrs={"class": "form-control form-control-sm",
                                             "placeholder": "Ej: Planimetría rectificada"}),
        }

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if not archivo:
            return archivo
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in SolicitudAdjunto.EXT_PERMITIDAS:
            raise forms.ValidationError("Formato no permitido. Solo se aceptan PDF y JPG.")
        if archivo.size > SolicitudAdjunto.TAM_MAX_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"El archivo supera el tamaño máximo permitido de {SolicitudAdjunto.TAM_MAX_MB} MB."
            )
        return archivo


SolicitudDetalleFormSet = inlineformset_factory(
    SolicitudMaterial,
    SolicitudDetalle,
    form=SolicitudDetalleForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
