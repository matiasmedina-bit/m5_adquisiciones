from django.contrib import admin
from .models import Proveedor, ProveedorMaterial


class ProveedorMaterialInline(admin.TabularInline):
    model = ProveedorMaterial
    extra = 1


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut_formateado", "correo", "condicion_pago", "estado")
    list_filter = ("estado", "condicion_pago")
    search_fields = ("nombre", "rut")
    inlines = [ProveedorMaterialInline]


@admin.register(ProveedorMaterial)
class ProveedorMaterialAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descripcion", "proveedor", "unidad_medida", "disponible", "modificado")
    list_filter = ("disponible", "proveedor")
    search_fields = ("codigo", "descripcion")
