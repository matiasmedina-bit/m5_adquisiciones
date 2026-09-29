"""Formularios del módulo de usuarios (CU-51 Gestionando cuentas)."""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario, ParametrosSistema


class RegistroSolicitudForm(UserCreationForm):
    """
    Formulario público de solicitud de acceso, pendiente de aprobación del
    administrador. Acá el interesado **sí** define su propia contraseña: nadie
    se la manda, porque la cuenta todavía no existe formalmente en la empresa.
    """
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
        self.fields["email"].required = True
        # No dejar elegir ADMIN desde el formulario público
        self.fields["rol"].choices = [
            c for c in Usuario.Rol.choices if c[0] != Usuario.Rol.ADMIN
        ]

    def clean_email(self):
        """Un correo no puede quedar en dos cuentas, ni siquiera pendientes."""
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Ese correo ya está asociado a una cuenta del sistema.")
        return email


class RevisionSolicitudForm(forms.ModelForm):
    """
    CU-52: revisión de una solicitud de acceso antes de aprobarla.

    Quien se registra escribe sus propios datos y elige su rol, y se equivoca:
    pide «Bodeguero» cuando es jefe de obra, o escribe mal el correo. El
    administrador corrige aquí y aprueba en el mismo paso, en vez de aprobar
    primero y tener que ir a editar la cuenta después.

    A diferencia del formulario público, sí permite asignar el rol
    Administrador: quien revisa ya es administrador, y concederlo es una
    decisión deliberada suya, no algo que el solicitante pueda pedir.
    """

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "telefono", "rol"]
        widgets = {
            "username":   forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name":  forms.TextInput(attrs={"class": "form-control"}),
            "email":      forms.EmailInput(attrs={"class": "form-control"}),
            "telefono":   forms.TextInput(attrs={"class": "form-control", "placeholder": "+56 9 xxxxxxxx"}),
            "rol":        forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True

    @property
    def rol_cambiado(self):
        """True si el administrador modificó el rol que había pedido el usuario."""
        return "rol" in self.changed_data


class UsuarioCreateForm(forms.ModelForm):
    """
    CU-49 (RF-48): el Administrador crea la cuenta con nombre completo, correo
    institucional y rol. **No define la contraseña**: el sistema le manda al
    nuevo usuario un enlace temporal para que la ponga él (CU-52).

    Que el administrador no elija la clave no es un detalle de comodidad: una
    contraseña que pasó por un tercero deja de servir como prueba de quién hizo
    qué, y la bitácora de auditoría (CU-53) depende justamente de eso.
    """

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
        for campo in ("first_name", "last_name", "email"):
            self.fields[campo].required = True
        self.fields["email"].help_text = (
            "Correo institucional. Ahí llega el enlace para definir la contraseña.")
        self.fields["rol"].choices = [("", "— Selecciona el rol —")] + [
            (v, e) for v, e in Usuario.Rol.choices]

    def clean_email(self):
        """Excepción 1 del CU-49/CU-50: un correo no puede estar en dos cuentas."""
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo institucional es obligatorio.")
        existentes = Usuario.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            existentes = existentes.exclude(pk=self.instance.pk)
        if existentes.exists():
            raise forms.ValidationError(
                "Ese correo ya está asociado a otra cuenta del sistema.")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # Sin contraseña utilizable: sólo se puede entrar tras activar la cuenta
        usuario.set_unusable_password()
        if commit:
            usuario.save()
        return usuario


class UsuarioUpdateForm(UserChangeForm):
    """CU-50 (RF-48): editar nombre, correo y rol. Oculta el campo password."""
    password = None

    def clean_email(self):
        """Excepción 1 del CU-50: el correo no puede quedar duplicado."""
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email:
            otros = Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
            if otros.exists():
                raise forms.ValidationError(
                    "Ese correo ya está asociado a otra cuenta del sistema.")
        return email

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


class ParametrosSistemaForm(forms.ModelForm):
    """
    CU-60: los parámetros generales. Los rangos válidos están en los validadores
    del modelo, así que un valor fuera de rango no llega a guardarse ni por el
    formulario ni por el admin (Excepción 1 del caso de uso).
    """
    class Meta:
        model = ParametrosSistema
        fields = ["tolerancia_factura_pct", "stock_minimo_defecto", "umbral_archivo_mb"]
        widgets = {
            "tolerancia_factura_pct": forms.NumberInput(attrs={
                "class": "form-control", "step": "0.5", "min": "0", "max": "100"}),
            "stock_minimo_defecto": forms.NumberInput(attrs={
                "class": "form-control", "step": "1", "min": "0"}),
            "umbral_archivo_mb": forms.NumberInput(attrs={
                "class": "form-control", "step": "1", "min": "1", "max": "500"}),
        }
