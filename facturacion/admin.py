from django.contrib import admin
from .models import Factura


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("numero", "proveedor", "fecha_emision", "fecha_vencimiento",
                    "monto_total", "estado", "diferencia_pct")
    list_filter = ("estado",)
    search_fields = ("numero", "proveedor__nombre")
    filter_horizontal = ("ordenes",)
    readonly_fields = ("creada", "diferencia_pct")
