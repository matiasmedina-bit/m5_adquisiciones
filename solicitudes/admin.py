from django.contrib import admin
from .models import SolicitudMaterial, SolicitudDetalle, SolicitudAdjunto


class SolicitudDetalleInline(admin.TabularInline):
    model = SolicitudDetalle
    extra = 1


class SolicitudAdjuntoInline(admin.TabularInline):
    model = SolicitudAdjunto
    extra = 0
    readonly_fields = ("subido_por", "fecha")


@admin.register(SolicitudMaterial)
class SolicitudMaterialAdmin(admin.ModelAdmin):
    list_display = ("correlativo", "proyecto", "emisor", "estado", "fecha")
    list_filter = ("estado", "proyecto")
    search_fields = ("correlativo",)
    inlines = [SolicitudDetalleInline, SolicitudAdjuntoInline]
