from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, PerfilJefeProyecto, PerfilEncargadoAdquisiciones, PerfilBodeguero,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "estado", "is_staff")
    list_filter = ("rol", "estado", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Datos del proyecto", {"fields": ("telefono", "rol", "estado")}),
    )


admin.site.register(PerfilJefeProyecto)
admin.site.register(PerfilEncargadoAdquisiciones)
admin.site.register(PerfilBodeguero)
