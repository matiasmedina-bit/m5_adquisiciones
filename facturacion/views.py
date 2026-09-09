"""
Vistas de Facturación y Contabilidad — Incremento 2.
RF-40 Recepcionar factura (vincular a OC, marcarlas como Facturadas)
RF-41 Validar monto factura vs OC; bloquear si excede la tolerancia
RF-42 Desbloquear factura (Administración)
RF-43 Vista "Cuentas por Pagar" ordenada por vencimiento
RF-44 Exportar listado de facturas a CSV
"""
import csv
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from usuarios.permisos import rol_requerido
from .models import Factura
from .forms import FacturaForm, DesbloqueoForm

CONT = "CONTABILIDAD"


@rol_requerido(CONT)
def factura_lista(request):
    facturas = Factura.objects.select_related("proveedor").prefetch_related("ordenes")
    estado = request.GET.get("estado")
    if estado:
        facturas = facturas.filter(estado=estado)
    return render(request, "facturacion/factura_lista.html", {
        "facturas": facturas.order_by("-creada"),
        "estado_filtro": estado or "",
        "estados": Factura.Estado.choices,
        "bloqueadas": Factura.objects.filter(estado=Factura.Estado.BLOQUEADA).count(),
    })


@rol_requerido(CONT)
def factura_crear(request):
    if request.method == "POST":
        form = FacturaForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                factura = form.save(commit=False)
                factura.registrado_por = request.user
                factura.save()
                form.save_m2m()

                # RF-41: comparar monto de la factura con el total de las OC
                total_oc = factura.total_ordenes
                if total_oc > 0:
                    dif = abs(factura.monto_total - total_oc) / total_oc * 100
                else:
                    dif = 0
                factura.diferencia_pct = round(dif, 2)

                if dif > settings.FACTURA_TOLERANCIA_PCT:
                    factura.estado = Factura.Estado.BLOQUEADA
                    factura.save(update_fields=["diferencia_pct", "estado"])
                    messages.warning(
                        request,
                        f"Factura registrada pero BLOQUEADA: la diferencia con las OC es "
                        f"{factura.diferencia_pct}% (tolerancia {settings.FACTURA_TOLERANCIA_PCT}%). "
                        f"Administración debe desbloquearla.",
                    )
                else:
                    factura.save(update_fields=["diferencia_pct"])
                    _marcar_oc_facturadas(factura)
                    messages.success(request, f"Factura {factura.numero} registrada. OC marcadas como facturadas.")
            return redirect("facturacion:detalle", pk=factura.pk)
    else:
        form = FacturaForm()
    return render(request, "facturacion/factura_form.html", {
        "form": form, "tolerancia": settings.FACTURA_TOLERANCIA_PCT,
    })


@rol_requerido(CONT, "ADMIN")
def factura_detalle(request, pk):
    factura = get_object_or_404(
        Factura.objects.select_related("proveedor").prefetch_related("ordenes"), pk=pk)
    return render(request, "facturacion/factura_detalle.html", {
        "factura": factura,
        "desbloqueo_form": DesbloqueoForm(),
        "tolerancia": settings.FACTURA_TOLERANCIA_PCT,
    })


@rol_requerido("ADMIN")
def factura_desbloquear(request, pk):
    """RF-42: Administración desbloquea una factura bloqueada por diferencia de monto."""
    factura = get_object_or_404(Factura, pk=pk)
    if factura.estado != Factura.Estado.BLOQUEADA:
        messages.info(request, "Esta factura no está bloqueada.")
        return redirect("facturacion:detalle", pk=factura.pk)
    if request.method == "POST":
        form = DesbloqueoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                factura.estado = Factura.Estado.REGISTRADA
                factura.desbloqueada_por = request.user
                factura.fecha_desbloqueo = timezone.now()
                factura.observacion = (
                    factura.observacion + "\n" if factura.observacion else ""
                ) + f"[Desbloqueo] {form.cleaned_data['justificacion']}"
                factura.save(update_fields=["estado", "desbloqueada_por",
                                            "fecha_desbloqueo", "observacion"])
                _marcar_oc_facturadas(factura)
            messages.success(request, f"Factura {factura.numero} desbloqueada y registrada.")
    return redirect("facturacion:detalle", pk=factura.pk)


def _marcar_oc_facturadas(factura):
    """RF-40: marca como Facturada cada OC vinculada (campo independiente de la recepción)."""
    factura.ordenes.update(facturada=True)


@rol_requerido(CONT, "ADMIN")
def cuentas_por_pagar(request):
    """RF-43: facturas registradas ordenadas por fecha de vencimiento (asc)."""
    facturas = (Factura.objects
                .filter(estado=Factura.Estado.REGISTRADA)
                .select_related("proveedor")
                .order_by("fecha_vencimiento"))
    hoy = date.today()
    limite = hoy + timedelta(days=7)
    filas = []
    for f in facturas:
        dias = (f.fecha_vencimiento - hoy).days
        filas.append({
            "factura": f,
            "dias_restantes": dias,
            "vencida": dias < 0,
            "por_vencer": 0 <= dias <= 7,
        })
    total = sum(f.monto_total for f in facturas)
    return render(request, "facturacion/cuentas_por_pagar.html", {
        "filas": filas, "total": total, "hoy": hoy, "limite": limite,
    })


@rol_requerido(CONT, "ADMIN")
def factura_export_csv(request):
    """RF-44: exporta el listado de facturas a CSV (formato Transtecnia)."""
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="facturas.csv"'
    resp.write("﻿")  # BOM para Excel
    w = csv.writer(resp, delimiter=";")
    w.writerow(["N Factura", "RUT Proveedor", "Razon Social", "Fecha Emision",
                "Fecha Vencimiento", "Monto Total", "Estado", "Ordenes de Compra"])
    for f in Factura.objects.select_related("proveedor").prefetch_related("ordenes").order_by("fecha_emision"):
        w.writerow([
            f.numero,
            f.proveedor.rut_formateado,
            f.proveedor.nombre,
            f.fecha_emision.strftime("%d-%m-%Y"),
            f.fecha_vencimiento.strftime("%d-%m-%Y"),
            int(f.monto_total),
            f.get_estado_display(),
            " ".join(o.correlativo for o in f.ordenes.all()),
        ])
    return resp
