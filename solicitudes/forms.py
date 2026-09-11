"""Formularios de Solicitudes (CU-11 Generar, CU-12 Agregar ítems, CU-14 Editar).
Incremento 2: RF-16 (justificación por exceso de itemizado), RF-17 (adjuntos)."""
import os
from django import forms
from django.forms import inlineformset_factory
from .models import SolicitudMaterial, SolicitudDetalle, SolicitudAdjunto
from inventario.models import Material
from proyectos.models import Itemizado
from proveedores.models import Proveedor, ProveedorMaterial


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
    """
    CU-12 Agregando ítems (líneas) a la solicitud.

    La línea parte por el proveedor y sigue por el material: quien pide sabe a
    quién comprarle, y el catálogo de ese proveedor ya trae la unidad y el
    precio. El buscador funciona en los dos sentidos — con proveedor elegido
    busca sólo en su catálogo; si se escribe el material primero, el selector
    de proveedor se reduce a los que lo ofrecen. Ese cruce lo resuelve la API
    (solicitudes/api.py); este formulario recibe el resultado ya elegido.

    La unidad de medida dejó de escribirse a mano: se hereda del catálogo y se
    muestra junto a la cantidad. Ese espacio lo ocupa ahora «detalle».

    RF-16: si la cantidad supera el saldo de la partida, exige justificación.
    """

    nombre_libre = forms.CharField(
        label="Material",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm buscador-material",
            "placeholder": "Escribe para buscar\u2026",
            "autocomplete": "off",
        }),
    )

    class Meta:
        model = SolicitudDetalle
        fields = ["proveedor", "proveedor_material", "material", "cantidad_solicitada",
                  "unidad_medida", "valor_unitario", "detalle", "partida", "justificacion"]
        widgets = {
            "proveedor": forms.Select(attrs={"class": "form-select form-select-sm selector-proveedor"}),
            "proveedor_material": forms.HiddenInput(attrs={"class": "campo-oferta"}),
            "material": forms.HiddenInput(attrs={"class": "campo-material"}),
            "cantidad_solicitada": forms.NumberInput(attrs={
                "class": "form-control form-control-sm campo-cantidad",
                "min": "0.01", "step": "0.01", "placeholder": "0"}),
            "unidad_medida": forms.HiddenInput(attrs={"class": "campo-unidad"}),
            "valor_unitario": forms.NumberInput(attrs={
                "class": "form-control form-control-sm campo-valor",
                "min": "0", "step": "1", "placeholder": "0"}),
            "detalle": forms.TextInput(attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Ej: para la losa del 3er piso"}),
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
        self.fields["proveedor"].queryset = Proveedor.objects.filter(estado=True)
        self.fields["proveedor"].empty_label = "\u2014 Cualquier proveedor \u2014"
        self.fields["proveedor_material"].queryset = ProveedorMaterial.objects.filter(
            disponible=True, proveedor__estado=True)
        for opcional in ("material", "proveedor", "proveedor_material", "unidad_medida",
                         "valor_unitario", "detalle", "partida", "justificacion"):
            self.fields[opcional].required = False

        if self._solicitud is not None:
            self.fields["partida"].queryset = Itemizado.objects.filter(
                proyecto=self._solicitud.proyecto)
            self.fields["partida"].empty_label = "\u2014 Sin partida \u2014"
        else:
            self.fields["partida"].queryset = Itemizado.objects.none()

        # Al editar, el buscador muestra lo que ya estaba elegido
        if self.instance.pk and not self.initial.get("nombre_libre"):
            if self.instance.proveedor_material_id:
                self.initial["nombre_libre"] = self.instance.proveedor_material.descripcion
            elif self.instance.material_id:
                self.initial["nombre_libre"] = self.instance.material.nombre

    def clean_cantidad_solicitada(self):
        cantidad = self.cleaned_data.get("cantidad_solicitada")
        if cantidad is not None and cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor que cero.")
        return cantidad

    def clean_valor_unitario(self):
        valor = self.cleaned_data.get("valor_unitario")
        if valor is None:
            return 0
        if valor < 0:
            raise forms.ValidationError("El valor no puede ser negativo.")
        return valor

    def clean(self):
        cleaned = super().clean()
        oferta = cleaned.get("proveedor_material")
        material = cleaned.get("material")
        nombre_libre = (cleaned.get("nombre_libre") or "").strip()

        if not oferta and not material and not nombre_libre:
            # fila completamente vacía → la ignoramos (formset extra vacío)
            return cleaned

        if oferta:
            # Vino del catálogo de un proveedor: ese ítem manda
            cleaned["material"] = oferta.resolver_material()
            cleaned["proveedor"] = oferta.proveedor
            if not cleaned.get("unidad_medida"):
                cleaned["unidad_medida"] = oferta.unidad_medida
            if not cleaned.get("valor_unitario"):
                cleaned["valor_unitario"] = oferta.precio or 0
        elif not material and nombre_libre:
            # Material que no está en ningún catálogo: se crea en el general
            material_obj = Material.objects.filter(nombre__iexact=nombre_libre).first()
            if material_obj is None:
                material_obj = Material.objects.create(
                    nombre=nombre_libre,
                    unidad_medida=cleaned.get("unidad_medida") or "un")
            cleaned["material"] = material_obj

        material_final = cleaned.get("material")
        if material_final and not cleaned.get("unidad_medida"):
            cleaned["unidad_medida"] = material_final.unidad_medida

        if not cleaned.get("cantidad_solicitada"):
            self.add_error("cantidad_solicitada", "Indica cuánto necesitas.")

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
