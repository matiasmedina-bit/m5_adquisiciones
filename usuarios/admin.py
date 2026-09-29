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


# --- CU-60: parámetros generales del sistema ---
from .models import ParametrosSistema


@admin.register(ParametrosSistema)
class ParametrosSistemaAdmin(admin.ModelAdmin):
    """Fila única: no se agrega ni se borra, sólo se edita."""
    list_display = ("tolerancia_factura_pct", "stock_minimo_defecto",
                    "umbral_archivo_mb", "actualizado", "actualizado_por")

    def has_add_permission(self, request):
        return not ParametrosSistema.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
