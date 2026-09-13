"""
Vistas del módulo de Adquisiciones — Incremento 2.
RF-19 Bandeja de solicitudes por cotizar
RF-20 Registrar cotizaciones          RF-21 Valor total automático
RF-22 Aprobar línea de cotización     RF-23 Generar Orden(es) de Compra
RF-24 Aprobar / rechazar OC (Jefe)    RF-25 Editar OC rechazada
RF-26 Exportar OC a PDF               RF-27 Enviar OC por correo al proveedor
RF-38 Actualizar estado de recepción de la OC
RF-39 Estado de recepción por OC (se muestra en el detalle de la SM)
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from auditoria.models import RegistroAuditoria, registrar
from usuarios.permisos import rol_requerido
from solicitudes.models import SolicitudMaterial
from .models import Cotizacion, CotizacionLinea, OrdenCompra, OrdenCompraLinea  # noqa: F401
from .forms import CotizacionForm, OrdenLineaFormSet, RecepcionEstadoForm
from .pdf import generar_pdf_orden, ReportlabNoInstalado

EA = "ENCARGADO_ADQUISICIONES"


# ----------------------------------------------------------------------------
# RF-19 — Bandeja de solicitudes en estado "Emitida" (aprobadas por el Jefe)
# ----------------------------------------------------------------------------
@rol_requerido(EA)
def cotizacion_bandeja(request):
    solicitudes = (SolicitudMaterial.objects
                   .filter(estado__in=[SolicitudMaterial.Estado.APROBADA,
                                       SolicitudMaterial.Estado.EN_COTIZACION])
                   .select_related("proyecto", "emisor")
                   .order_by("fecha"))  # cronológico ascendente
    return render(request, "adquisiciones/cotizacion_bandeja.html", {"solicitudes": solicitudes})


# ----------------------------------------------------------------------------
# RF-20/21/22/23 — Registrar cotizaciones, aprobar líneas y generar OC
# ----------------------------------------------------------------------------
@rol_requerido(EA)
def cotizacion_sm(request, pk):
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    if not solicitud.puede_cotizarse:
        messages.error(request, "Esta solicitud no está disponible para cotización.")
        return redirect("solicitudes:detalle", pk=solicitud.pk)

    cot_form = CotizacionForm(solicitud=solicitud)
    detalles = list(solicitud.detalles.select_related("material"))

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "agregar_cotizacion":
            cot_form = CotizacionForm(request.POST, solicitud=solicitud)
            if cot_form.is_valid():
                with transaction.atomic():
                    cotizacion = cot_form.save(commit=False)
                    cotizacion.solicitud = solicitud
                    cotizacion.creada_por = request.user
                    cotizacion.save()
                    creadas = 0
                    for d in detalles:
                        raw = request.POST.get(f"vu_{d.pk}", "").strip()
                        if not raw:
                            continue
                        try:
                            valor = int(round(float(raw)))
                        except ValueError:
                            continue
                        if valor <= 0:
                            continue
                        CotizacionLinea.objects.create(
                            cotizacion=cotizacion, solicitud_detalle=d, valor_unitario=valor)
                        creadas += 1
                if creadas == 0:
                    messages.warning(request, "Cotización creada, pero sin valores unitarios cargados.")
                else:
                    messages.success(request, f"Cotización de {cotizacion.proveedor.nombre} registrada ({creadas} líneas).")
                return redirect("adquisiciones:cotizacion_sm", pk=solicitud.pk)

        elif accion == "aprobar_linea":
            linea = get_object_or_404(
                CotizacionLinea, pk=request.POST.get("linea_id"),
                cotizacion__solicitud=solicitud)
            linea.aprobar()  # RF-22
            _refrescar_estado_cotizacion(solicitud)
            messages.success(request, f"Línea aprobada: {linea.solicitud_detalle.material.nombre}.")
            return redirect("adquisiciones:cotizacion_sm", pk=solicitud.pk)

        elif accion == "generar_oc":
            if not _todas_las_lineas_aprobadas(solicitud):
                messages.error(request, "Faltan materiales por aprobar una línea de cotización.")
                return redirect("adquisiciones:cotizacion_sm", pk=solicitud.pk)
            ordenes = _generar_ordenes_compra(solicitud, request.user)
            messages.success(
                request,
                f"Se generó {len(ordenes)} orden(es) de compra: "
                + ", ".join(o.correlativo for o in ordenes),
            )
            return redirect("solicitudes:detalle", pk=solicitud.pk)

    # Contexto para la plantilla
    detalle_ids_aprobados = list(
        CotizacionLinea.objects
        .filter(cotizacion__solicitud=solicitud, estado=CotizacionLinea.Estado.APROBADA)
        .values_list("solicitud_detalle_id", flat=True)
    )
    return render(request, "adquisiciones/cotizacion_sm.html", {
        "solicitud": solicitud,
        "detalles": detalles,
        "cotizaciones": solicitud.cotizaciones.select_related("proveedor").prefetch_related("lineas__solicitud_detalle__material"),
        "cot_form": cot_form,
        "detalle_ids_aprobados": detalle_ids_aprobados,
        "puede_generar_oc": _todas_las_lineas_aprobadas(solicitud),
    })


def _todas_las_lineas_aprobadas(solicitud):
    detalle_ids = set(solicitud.detalles.values_list("pk", flat=True))
    if not detalle_ids:
        return False
    aprobadas = set(
        CotizacionLinea.objects
        .filter(cotizacion__solicitud=solicitud, estado=CotizacionLinea.Estado.APROBADA)
        .values_list("solicitud_detalle_id", flat=True)
    )
    return detalle_ids.issubset(aprobadas)


def _refrescar_estado_cotizacion(solicitud):
    """RF-22: cuando todos los materiales tienen línea aprobada, la SM pasa a 'En cotización'."""
    if _todas_las_lineas_aprobadas(solicitud) and solicitud.estado == SolicitudMaterial.Estado.APROBADA:
        solicitud.estado = SolicitudMaterial.Estado.EN_COTIZACION
        solicitud.save(update_fields=["estado"])


@transaction.atomic
def _generar_ordenes_compra(solicitud, usuario):
    """RF-23: un borrador de OC por cada proveedor con líneas aprobadas."""
    aprobadas = (CotizacionLinea.objects
                 .filter(cotizacion__solicitud=solicitud, estado=CotizacionLinea.Estado.APROBADA)
                 .select_related("cotizacion__proveedor", "solicitud_detalle__material"))
    por_cotizacion = {}
    for cl in aprobadas:
        por_cotizacion.setdefault(cl.cotizacion, []).append(cl)

    ordenes = []
    for cotizacion, lineas in por_cotizacion.items():
        orden = OrdenCompra.objects.create(
            solicitud=solicitud, proveedor=cotizacion.proveedor, cotizacion=cotizacion,
            costo_despacho=cotizacion.costo_despacho, creada_por=usuario,
        )
        for cl in lineas:
            d = cl.solicitud_detalle
            OrdenCompraLinea.objects.create(
                orden=orden, material=d.material, descripcion=d.material.nombre,
                cantidad=d.cantidad_solicitada, unidad_medida=d.unidad_medida,
                valor_unitario=cl.valor_unitario,
            )
        # CU-53: la emisión de una OC es una acción auditable
        registrar(usuario, RegistroAuditoria.Accion.OC_EMITIDA,
                  f"Emitió la orden de compra a {orden.proveedor.nombre} "
                  f"por la solicitud {solicitud.correlativo}.", orden.correlativo)
        ordenes.append(orden)

    solicitud.estado = SolicitudMaterial.Estado.OC_GENERADA
    solicitud.save(update_fields=["estado"])
    return ordenes


# ----------------------------------------------------------------------------
# Órdenes de Compra
# ----------------------------------------------------------------------------
@rol_requerido(EA, "JEFE_PROYECTO")
def orden_lista(request):
    ordenes = OrdenCompra.objects.select_related("proveedor", "solicitud__proyecto")
    estado = request.GET.get("estado")
    if estado:
        ordenes = ordenes.filter(estado=estado)
    if request.user.rol == "JEFE_PROYECTO":
        ordenes = ordenes.filter(solicitud__proyecto__jefe_proyecto=request.user)
    return render(request, "adquisiciones/orden_lista.html", {
        "ordenes": ordenes, "estado_filtro": estado or "",
        "estados": OrdenCompra.Estado.choices,
    })


@rol_requerido(EA, "JEFE_PROYECTO")
def orden_detalle(request, pk):
    orden = get_object_or_404(
        OrdenCompra.objects.select_related("proveedor", "solicitud__proyecto"), pk=pk)
    if request.user.rol == "JEFE_PROYECTO" and orden.solicitud.proyecto.jefe_proyecto_id != request.user.pk:
        raise PermissionDenied("Esta orden de compra pertenece a otro proyecto.")
    recepcion_form = RecepcionEstadoForm()

    if request.method == "POST":
        accion = request.POST.get("accion")

        # RF-24: el Jefe de Proyecto aprueba o rechaza el borrador
        if accion == "aprobar" and request.user.rol in ("JEFE_PROYECTO", "ADMIN"):
            if orden.estado != OrdenCompra.Estado.BORRADOR:
                messages.error(request, "Solo se puede aprobar una OC en borrador.")
            else:
                orden.estado = OrdenCompra.Estado.APROBADA
                orden.aprobada_por = request.user
                orden.fecha_aprobacion = timezone.now()
                orden.save(update_fields=["estado", "aprobada_por", "fecha_aprobacion"])
                registrar(request.user, RegistroAuditoria.Accion.OC_APROBADA,
                          f"Aprobó la orden de compra a {orden.proveedor.nombre}.",
                          orden.correlativo)
                _enviar_orden_al_proveedor(request, orden)  # RF-27
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)

        if accion == "rechazar" and request.user.rol in ("JEFE_PROYECTO", "ADMIN"):
            motivo = request.POST.get("motivo", "").strip()
            if orden.estado != OrdenCompra.Estado.BORRADOR:
                messages.error(request, "Solo se puede rechazar una OC en borrador.")
            elif not motivo:
                messages.error(request, "Debes indicar el motivo del rechazo.")
            else:
                orden.estado = OrdenCompra.Estado.RECHAZADA
                orden.motivo_rechazo = motivo
                orden.save(update_fields=["estado", "motivo_rechazo"])
                _notificar(
                    [orden.creada_por.email],
                    f"OC {orden.correlativo} rechazada",
                    f"El Jefe de Proyecto rechazó la orden {orden.correlativo}.\nMotivo: {motivo}",
                )
                messages.warning(request, f"Orden {orden.correlativo} rechazada.")
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)

        # RF-25: devolver una OC rechazada a borrador
        if accion == "devolver_borrador" and request.user.rol in (EA, "ADMIN"):
            if orden.estado == OrdenCompra.Estado.RECHAZADA:
                orden.estado = OrdenCompra.Estado.BORRADOR
                orden.motivo_rechazo = ""
                orden.save(update_fields=["estado", "motivo_rechazo"])
                messages.success(request, "La OC volvió a estado borrador para su corrección.")
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)

        # RF-38: actualizar el estado de recepción
        if accion == "recepcion" and request.user.rol in (EA, "ADMIN"):
            recepcion_form = RecepcionEstadoForm(request.POST)
            if orden.estado not in (OrdenCompra.Estado.ENVIADA, OrdenCompra.Estado.RECEPCION_PARCIAL):
                messages.error(request, "Solo se actualiza la recepción de una OC enviada.")
            elif recepcion_form.is_valid():
                nuevo = recepcion_form.cleaned_data["estado"]
                orden.estado = nuevo
                orden.save(update_fields=["estado"])
                _refrescar_estado_recepcion_sm(orden.solicitud)
                jefe = orden.solicitud.proyecto.jefe_proyecto
                if jefe and jefe.email:
                    detalle = "; ".join(
                        f"{l.descripcion}: {l.cantidad_recibida}/{l.cantidad}" for l in orden.lineas.all())
                    _notificar(
                        [jefe.email],
                        f"OC {orden.correlativo}: {orden.get_estado_display()}",
                        f"La orden {orden.correlativo} cambió a «{orden.get_estado_display()}».\n{detalle}",
                    )
                messages.success(request, f"Recepción actualizada a «{orden.get_estado_display()}».")
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)

    return render(request, "adquisiciones/orden_detalle.html", {
        "orden": orden,
        "recepcion_form": recepcion_form,
        "empresa": {
            "razon_social": _empresa("EMPRESA_RAZON_SOCIAL"),
            "rut": _empresa("EMPRESA_RUT"),
            "giro": _empresa("EMPRESA_GIRO"),
            "direccion": _empresa("EMPRESA_DIRECCION"),
        },
    })


def _empresa(clave):
    from django.conf import settings
    return getattr(settings, clave, "")


@rol_requerido(EA)
def orden_editar(request, pk):
    """RF-25: editar líneas de una OC rechazada y devolverla a borrador."""
    orden = get_object_or_404(OrdenCompra, pk=pk)
    if orden.estado != OrdenCompra.Estado.RECHAZADA:
        messages.error(request, "Solo se pueden editar órdenes rechazadas.")
        return redirect("adquisiciones:orden_detalle", pk=orden.pk)

    qs = orden.lineas.all()
    if request.method == "POST":
        formset = OrdenLineaFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            orden.estado = OrdenCompra.Estado.BORRADOR
            orden.motivo_rechazo = ""
            orden.save(update_fields=["estado", "motivo_rechazo"])
            messages.success(request, "Orden corregida y enviada nuevamente a aprobación.")
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)
    else:
        formset = OrdenLineaFormSet(queryset=qs)
    return render(request, "adquisiciones/orden_editar.html", {"orden": orden, "formset": formset})


@rol_requerido(EA, "JEFE_PROYECTO")
def orden_pdf(request, pk):
    """RF-26: exporta la OC a PDF con el logotipo corporativo."""
    orden = get_object_or_404(OrdenCompra, pk=pk)
    try:
        pdf_bytes = generar_pdf_orden(orden)
    except ReportlabNoInstalado as exc:
        return HttpResponse(str(exc), status=503, content_type="text/plain; charset=utf-8")
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{orden.correlativo}.pdf"'
    return resp


# ----------------------------------------------------------------------------
# Helpers de correo / estado
# ----------------------------------------------------------------------------
def _notificar(destinatarios, asunto, cuerpo, adjunto=None):
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return
    try:
        msg = EmailMessage(subject=asunto, body=cuerpo, to=destinatarios)
        if adjunto:
            nombre, contenido, mime = adjunto
            msg.attach(nombre, contenido, mime)
        msg.send(fail_silently=True)
    except Exception:  # pragma: no cover - el backend de consola no falla
        pass


def _enviar_orden_al_proveedor(request, orden):
    """RF-27: adjunta el PDF de la OC y la envía al correo del proveedor."""
    adjunto = None
    try:
        adjunto = (f"{orden.correlativo}.pdf", generar_pdf_orden(orden), "application/pdf")
    except ReportlabNoInstalado:
        messages.warning(request, "Se envió la OC sin PDF adjunto (falta la librería reportlab).")

    if orden.proveedor.correo:
        _notificar(
            [orden.proveedor.correo],
            f"Orden de Compra {orden.correlativo} — Constructora M5 SpA",
            f"Estimado proveedor,\n\nAdjuntamos la Orden de Compra {orden.correlativo} "
            f"por un total de ${orden.total:,.0f}.\n\nSaludos,\nDepartamento de Adquisiciones — M5 SpA",
            adjunto=adjunto,
        )
        orden.estado = OrdenCompra.Estado.ENVIADA
        orden.fecha_envio = timezone.now()
        orden.save(update_fields=["estado", "fecha_envio"])
        registrar(request.user, RegistroAuditoria.Accion.OC_ENVIADA,
                  f"Envió la orden de compra a {orden.proveedor.nombre} "
                  f"({orden.proveedor.correo}).", orden.correlativo)
        # La SM queda con OC generada/enviada
        if orden.solicitud.estado in (SolicitudMaterial.Estado.EN_COTIZACION,
                                      SolicitudMaterial.Estado.APROBADA,
                                      SolicitudMaterial.Estado.OC_GENERADA):
            orden.solicitud.estado = SolicitudMaterial.Estado.OC_GENERADA
            orden.solicitud.save(update_fields=["estado"])
        messages.success(request, f"OC {orden.correlativo} aprobada y enviada a {orden.proveedor.correo}.")
    else:
        messages.warning(
            request,
            f"OC {orden.correlativo} aprobada, pero el proveedor no tiene correo registrado. No se envió.",
        )


def _refrescar_estado_recepcion_sm(solicitud):
    """RF-39: refleja en la SM el estado global de recepción de sus OC."""
    ordenes = solicitud.ordenes_compra.all()
    if not ordenes:
        return
    estados = set(o.estado for o in ordenes)
    if estados <= {OrdenCompra.Estado.RECIBIDA}:
        solicitud.estado = SolicitudMaterial.Estado.RECIBIDA
    elif estados & {OrdenCompra.Estado.RECEPCION_PARCIAL, OrdenCompra.Estado.RECIBIDA}:
        solicitud.estado = SolicitudMaterial.Estado.RECEPCION_PARCIAL
    else:
        return
    solicitud.save(update_fields=["estado"])


# ----------------------------------------------------------------------------
# CU-47 — Buscando trazabilidad de material u Orden de Compra
# ----------------------------------------------------------------------------
@rol_requerido(EA, "JEFE_PROYECTO", "CONTABILIDAD", "BODEGUERO")
def trazabilidad_buscar(request):
    """
    Una sola caja de búsqueda: correlativo de SM, correlativo de OC o nombre
    del material. La cadena completa se arma en adquisiciones/trazabilidad.py.
    """
    from .trazabilidad import buscar

    resultado = buscar(request.GET.get("q", ""))
    return render(request, "adquisiciones/trazabilidad.html", {
        "resultado": resultado,
        "termino": resultado["termino"],
    })
