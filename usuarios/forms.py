"""Formularios del módulo de usuarios (CU-51 Gestionando cuentas)."""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario


class RegistroSolicitudForm(UserCreationForm):
    """Formulario público de solicitud de acceso (pendiente de aprobación admin)."""
    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "telefono", "rol"]
        widgets = {
            "username":   forms.TextInput(attrs={"class": "form-control", "placeholder": "nombre.apellido"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name":  forms.TextInput(attrs={"class": "form-control"}),
            "email":      forms.EmailInput(attrs={"class": "form-control"}),
            "telefono":   forms.TextInput(attrs={"class": "form-control", "placeholder": "+56 9 xxxxxxxx"}),
            "rol":        forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        # No dejar elegir ADMIN desde el formulario público
        self.fields["rol"].choices = [
            c for c in Usuario.Rol.choices if c[0] != Usuario.Rol.ADMIN
        ]


class UsuarioCreateForm(UserCreationForm):
    """Formulario para crear cuentas de usuario (CU-51)."""

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "telefono", "rol", "estado"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "rol": forms.Select(attrs={"class": "form-select"}),
            "estado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


class UsuarioUpdateForm(UserChangeForm):
    """Formulario para editar cuentas (CU-51). Oculta el campo password."""
    password = None

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "telefono", "rol", "estado"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "rol": forms.Select(attrs={"class": "form-select"}),
            "estado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
