from django.contrib import admin
from .models import Material, MovimientoInventario, PrestamoHerramienta


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "unidad_medida", "stock_actual", "stock_minimo",
                    "ubicacion", "precio_referencia", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("nombre", "codigo_activo")


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "tipo", "material", "cantidad", "proyecto",
                    "orden_compra", "registrado_por")
    list_filter = ("tipo",)
    search_fields = ("material__nombre", "guia_despacho")
    readonly_fields = ("fecha",)


@admin.register(PrestamoHerramienta)
class PrestamoHerramientaAdmin(admin.ModelAdmin):
    list_display = ("herramienta", "proyecto", "jefe_proyecto", "estado",
                    "fecha_salida", "fecha_devolucion_esperada", "fecha_devolucion_real")
    list_filter = ("estado",)
