"""Formularios de Proyectos e Itemizado (CU-06 a CU-10)."""
from django import forms
from .models import Proyecto, Itemizado


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ["nombre", "mandante", "centro_costo", "jefe_proyecto",
                  "fecha_inicio", "fecha_termino", "estado", "presupuesto_total"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "mandante": forms.TextInput(attrs={"class": "form-control"}),
            "centro_costo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: CC-2026-014"}),
            "jefe_proyecto": forms.Select(attrs={"class": "form-select"}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_termino": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
            "presupuesto_total": forms.NumberInput(attrs={"class": "form-control"}),
        }

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
