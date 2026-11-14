from django.contrib import admin
from usuarios.integridad import SinBorradoAdminMixin
from .models import Cotizacion, CotizacionLinea, OrdenCompra, OrdenCompraLinea


class CotizacionLineaInline(admin.TabularInline):
    model = CotizacionLinea
    extra = 0


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ("solicitud", "proveedor", "costo_despacho", "tiempo_entrega_dias", "estado", "fecha")
    list_filter = ("estado",)
    inlines = [CotizacionLineaInline]


class OrdenCompraLineaInline(admin.TabularInline):
    model = OrdenCompraLinea
    extra = 0
    can_delete = False  # RNF-09


@admin.register(OrdenCompra)
class OrdenCompraAdmin(SinBorradoAdminMixin, admin.ModelAdmin):
    list_display = ("correlativo", "proveedor", "solicitud", "estado", "facturada", "fecha")
    list_filter = ("estado", "facturada")
    search_fields = ("correlativo",)
    inlines = [OrdenCompraLineaInline]
    readonly_fields = ("correlativo",)
