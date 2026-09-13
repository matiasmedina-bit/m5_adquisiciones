from django.contrib import admin
from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """
    Sólo lectura, también acá. La bitácora es evidencia: si se pudiera editar
    desde el admin, dejaría de servir para lo que existe.
    """
    list_display = ("fecha", "actor", "get_accion_display", "referencia", "descripcion")
    list_filter = ("modulo", "accion", "fecha")
    search_fields = ("descripcion", "referencia", "usuario_nombre")
    date_hierarchy = "fecha"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
