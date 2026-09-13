from django.contrib import admin
from .models import Proyecto, Itemizado, TipoDocumento, ArchivoProyecto


class ItemizadoInline(admin.TabularInline):
    model = Itemizado
    extra = 1


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "mandante", "estado", "fecha_inicio", "presupuesto_total")
    list_filter = ("estado",)
    search_fields = ("nombre", "mandante")
    inlines = [ItemizadoInline]


@admin.register(Itemizado)
class ItemizadoAdmin(admin.ModelAdmin):
    list_display = ("codigo_partida", "descripcion", "proyecto", "cant_presupuestada", "cant_ejecutada")
    search_fields = ("codigo_partida", "descripcion")


# --- CU-54: catálogo de tipos de documento y archivos del proyecto ---

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(ArchivoProyecto)
class ArchivoProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "proyecto", "subido_por", "fecha")
    list_filter = ("tipo", "proyecto")
    search_fields = ("nombre", "observaciones")
