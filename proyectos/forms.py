"""Formularios de Proyectos e Itemizado (CU-06 a CU-10, CU-54)."""
import os
from django import forms
from django.forms import inlineformset_factory
from .models import Proyecto, Itemizado, TipoDocumento, ArchivoProyecto


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["nombre", "mandante", "centro_costo", "jefes",
                  "fecha_inicio", "fecha_termino", "estado", "presupuesto_total"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "mandante": forms.TextInput(attrs={"class": "form-control"}),
            "centro_costo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: CC-2026-014"}),
            "jefes": forms.CheckboxSelectMultiple(),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_termino": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "presupuesto_total": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sólo jefes de proyecto activos y ya aprobados (CU-52). Se conservan
        # los que el proyecto ya tuviera asignados, para no perderlos al editar
        # si alguno quedó inactivo después.
        from django.db.models import Q
        from usuarios.models import usuarios_asignables
        qs = usuarios_asignables("JEFE_PROYECTO")
        if self.instance.pk:
            ya_asignados = self.instance.jefes.values_list("pk", flat=True)
            qs = (usuarios_asignables("JEFE_PROYECTO").model.objects
                  .filter(Q(pk__in=qs.values("pk")) | Q(pk__in=list(ya_asignados)))
                  .order_by("first_name", "last_name", "username"))
        self.fields["jefes"].queryset = qs
        self.fields["jefes"].required = False
        self.fields["jefes"].help_text = (
            "Marca a todos los que llevan la obra. Cualquiera de ellos puede "
            "emitir solicitudes de material para este proyecto.")

    def clean_centro_costo(self):
        """RF-14: el centro de costo no puede repetirse en otro proyecto."""
        centro = (self.cleaned_data.get("centro_costo") or "").strip()
        if not centro:
            return centro
        qs = Proyecto.objects.filter(centro_costo__iexact=centro)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "Ya existe otro proyecto con este centro de costo."
            )
        return centro

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("fecha_inicio")
        termino = cleaned.get("fecha_termino")
        if inicio and termino and termino < inicio:
            raise forms.ValidationError("La fecha de término no puede ser anterior a la de inicio.")
        return cleaned


class ItemizadoForm(forms.ModelForm):
    class Meta:
        model = Itemizado
        fields = ["codigo_partida", "descripcion", "unidad_medida", "cant_presupuestada", "cant_ejecutada"]
        widgets = {
            "codigo_partida": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control"}),
            "unidad_medida": forms.TextInput(attrs={"class": "form-control", "placeholder": "m3, kg, un..."}),
            "cant_presupuestada": forms.NumberInput(attrs={"class": "form-control"}),
            "cant_ejecutada": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ItemizadoEnLineaForm(ItemizadoForm):
    """
    La misma partida, pero en la fila de una tabla: campos chicos y sin
    «cantidad ejecutada», que al crear la obra siempre es cero y sólo estorba.
    """
    class Meta(ItemizadoForm.Meta):
        fields = ["codigo_partida", "descripcion", "unidad_medida", "cant_presupuestada"]
        widgets = {
            "codigo_partida": forms.TextInput(attrs={
                "class": "form-control form-control-sm", "placeholder": "Ej: 1.2.3"}),
            "descripcion": forms.TextInput(attrs={
                "class": "form-control form-control-sm", "placeholder": "Ej: Hormigón fundaciones"}),
            "unidad_medida": forms.TextInput(attrs={
                "class": "form-control form-control-sm", "placeholder": "m3"}),
            "cant_presupuestada": forms.NumberInput(attrs={
                "class": "form-control form-control-sm", "placeholder": "0"}),
        }

    CAMPOS = ("codigo_partida", "descripcion", "unidad_medida", "cant_presupuestada")

    def has_changed(self):
        """
        Una fila en blanco es una fila en blanco.

        Django la daría por modificada: «cantidad presupuestada» tiene 0 por
        defecto en el modelo y el navegador manda el campo vacío, así que la
        compara contra el 0 y concluye que cambió. Resultado: al guardar la
        obra exigía llenar las cinco filas aunque sólo se usaran dos.
        """
        if not self.instance.pk:
            escrito = [(self.data.get(self.add_prefix(c)) or "").strip()
                       for c in self.CAMPOS]
            if not any(escrito):
                return False
        return super().has_changed()


# El itemizado se carga junto con la obra. Antes había que crear el proyecto y
# después acordarse de entrar a agregar las partidas una por una; como casi
# nadie lo hacía, las solicitudes de esa obra salían sin partida y el control
# presupuestario del itemizado no servía de nada.
ItemizadoFormSet = inlineformset_factory(
    Proyecto, Itemizado,
    form=ItemizadoEnLineaForm,
    extra=5, can_delete=True, min_num=0, validate_min=False,
)


# ==========================================================================
#  CU-54 (RF-51) — Almacenando archivo y clasificándolo por tipo de documento
# ==========================================================================

class ArchivoProyectoForm(forms.ModelForm):
    """
    Subida de un archivo del proyecto. El tipo de documento es obligatorio: sin
    clasificar, el archivo no entra (Excepción 1 del CU-54). El selector sólo
    ofrece tipos activos del catálogo.
    """
    class Meta:
        model = ArchivoProyecto
        fields = ["tipo", "nombre", "archivo", "observaciones"]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "nombre": forms.TextInput(attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Ej: Plano de emplazamiento rev. C"}),
            "archivo": forms.ClearableFileInput(attrs={"class": "form-control form-control-sm"}),
            "observaciones": forms.TextInput(attrs={
                "class": "form-control form-control-sm",
                "placeholder": "Opcional"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].queryset = TipoDocumento.objects.filter(activo=True)
        self.fields["tipo"].empty_label = "— Selecciona el tipo —"
        self.fields["tipo"].required = True
        # El mensaje genérico de Django («Este campo es obligatorio») no dice
        # de qué se trata. La Excepción 1 del CU-54 merece decirlo con todas
        # sus letras, porque es la regla del caso de uso y no un descuido.
        self.fields["tipo"].error_messages["required"] = (
            "Debes clasificar el archivo: selecciona un tipo de documento.")
        self.fields["nombre"].error_messages["required"] = (
            "Ponle un nombre al documento.")
        self.fields["archivo"].error_messages["required"] = (
            "Elige el archivo que quieres almacenar.")

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if not archivo:
            return archivo
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in ArchivoProyecto.EXT_PERMITIDAS:
            raise forms.ValidationError(
                "Formato no permitido. Se aceptan: "
                + ", ".join(e.lstrip(".") for e in ArchivoProyecto.EXT_PERMITIDAS) + "."
            )
        if archivo.size > ArchivoProyecto.TAM_MAX_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"El archivo supera el tamaño máximo de {ArchivoProyecto.TAM_MAX_MB} MB.")
        return archivo

    def clean_nombre(self):
        """Un nombre de puros espacios no es un nombre."""
        nombre = (self.cleaned_data.get("nombre") or "").strip()
        if not nombre:
            raise forms.ValidationError("Ponle un nombre al documento.")
        return nombre


class TipoDocumentoForm(forms.ModelForm):
    """Alta de un tipo en el catálogo, para destrabar la Excepción 1."""
    class Meta:
        model = TipoDocumento
        fields = ["nombre", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control",
                                             "placeholder": "Ej: Plano"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control",
                                                  "placeholder": "Opcional"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
