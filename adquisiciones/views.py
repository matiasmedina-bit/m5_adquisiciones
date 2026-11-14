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
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from auditoria.models import RegistroAuditoria, registrar
from usuarios.notificaciones import notificar, usuarios_con_rol
from usuarios.permisos import rol_requerido
from solicitudes.models import SolicitudMaterial
from .models import Cotizacion, CotizacionLinea, OrdenCompra, OrdenCompraLinea, cant  # noqa: F401
from .forms import (
    CotizacionForm, OrdenDirectaForm, OrdenDirectaLineaFormSet,
    OrdenLineaFormSet, RecepcionEstadoForm,
)
from .pdf import generar_pdf_orden, ReportlabNoInstalado

EA = "ENCARGADO_ADQUISICIONES"


# ----------------------------------------------------------------------------
# RF-19 — Bandeja de solicitudes en estado "Emitida" (aprobadas por el Jefe)
# ----------------------------------------------------------------------------
@rol_requerido(EA)
def cotizacion_bandeja(request):
    base = (SolicitudMaterial.objects
            .select_related("proyecto", "emisor")
            .order_by("fecha", "pk"))  # RF-16: cronológico, de la más antigua a la más reciente
    emitidas = base.filter(estado=SolicitudMaterial.Estado.EMITIDA)
    en_cotizacion = base.filter(estado=SolicitudMaterial.Estado.EN_COTIZACION)
    return render(request, "adquisiciones/cotizacion_bandeja.html", {
        "solicitudes": emitidas, "en_cotizacion": en_cotizacion})


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
                # Los precios se leen ANTES de crear nada. Una cotización sin
                # valores no se puede aprobar, y como la orden de compra exige
                # que todos los materiales tengan línea aprobada, una cotización
                # vacía dejaba el botón de generar la OC apagado para siempre,
                # sin forma de saber por qué ni de deshacerlo.
                precios = {}
                for d in detalles:
                    raw = (request.POST.get(f"vu_{d.pk}") or "").strip()
                    if not raw:
                        continue
                    try:
                        valor = int(round(float(raw)))
                    except ValueError:
                        continue
                    if valor > 0:
                        precios[d.pk] = valor

                if not precios:
                    messages.error(
                        request,
                        "No se guardó la cotización: falta el valor unitario. "
                        "Pon el precio de al menos un material; los que el "
                        "proveedor no cotice se dejan en blanco.")
                    return redirect("adquisiciones:cotizacion_sm", pk=solicitud.pk)

                with transaction.atomic():
                    cotizacion = cot_form.save(commit=False)
                    cotizacion.solicitud = solicitud
                    cotizacion.creada_por = request.user
                    cotizacion.save()
                    for d in detalles:
                        if d.pk in precios:
                            CotizacionLinea.objects.create(
                                cotizacion=cotizacion, solicitud_detalle=d,
                                valor_unitario=precios[d.pk])
                faltan = len(detalles) - len(precios)
                aviso = (f"Cotización de {cotizacion.proveedor.nombre} registrada "
                         f"({len(precios)} material{'es' if len(precios) != 1 else ''}).")
                if faltan:
                    aviso += (f" Quedaron {faltan} sin cotizar: necesitas el precio "
                              f"de todos para generar la orden de compra.")
                messages.success(request, aviso)
                return redirect("adquisiciones:cotizacion_sm", pk=solicitud.pk)

        elif accion == "eliminar_cotizacion":
            # Una cotización mal cargada tiene que poder borrarse; si no, queda
            # ensuciando la comparación de precios para siempre.
            cotizacion = get_object_or_404(
                Cotizacion, pk=request.POST.get("cotizacion_id"), solicitud=solicitud)
            if cotizacion.lineas.filter(estado=CotizacionLinea.Estado.APROBADA).exists():
                messages.error(
                    request,
                    "Esa cotización ya tiene líneas aprobadas y no se puede borrar. "
                    "Aprueba la línea de otro proveedor para reemplazarla.")
            else:
                nombre = cotizacion.proveedor.nombre
                cotizacion.delete()
                messages.success(request, f"Cotización de {nombre} eliminada.")
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
            # CU-21 Excepción 1: sin los datos para autocompletar no se genera
            faltan = _faltantes_para_oc(solicitud)
            if faltan:
                messages.error(
                    request,
                    "No se puede generar la orden de compra: falta " + "; ".join(faltan)
                    + ". Complétalo en la ficha del proveedor (o en la configuración de M5) "
                      "y vuelve a intentarlo.")
                return redirect("adquisiciones:cotizacion_sm", pk=solicitud.pk)
            ordenes = _generar_ordenes_compra(
                solicitud, request.user, folio_con_punto=_folio_con_punto(request))
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
        # Decir «faltan materiales» sin decir cuáles obliga a ir comparando la
        # tabla a ojo. Con el nombre, se ve al tiro qué queda por hacer.
        "materiales_sin_aprobar": [
            d.material.nombre for d in detalles
            if d.pk not in detalle_ids_aprobados
        ],
        **_contexto_folio(),
    })


def _folio_con_punto(request):
    """Lo que eligió el usuario al generar: «13285» (junto) o «13.285» (punto)."""
    return request.POST.get("formato_folio") == "punto"


def _contexto_folio():
    """Datos para el selector de formato de folio en las pantallas que generan OC."""
    from usuarios.models import ParametrosSistema

    siguiente = max(ParametrosSistema.actuales().siguiente_folio_oc,
                    OrdenCompra.ultimo_folio_usado() + 1)
    return {
        "folio_siguiente": siguiente,
        "folio_ejemplo_junto": OrdenCompra.formatear_folio(siguiente, False),
        "folio_ejemplo_punto": OrdenCompra.formatear_folio(siguiente, True),
        "folio_con_punto_preferido": OrdenCompra.folio_con_punto_preferido(),
    }


def _faltantes_para_oc(solicitud):
    """Datos faltantes de cada proveedor con líneas aprobadas (CU-21 Exc. 1)."""
    proveedores = {cl.cotizacion.proveedor for cl in CotizacionLinea.objects
                   .filter(cotizacion__solicitud=solicitud, estado=CotizacionLinea.Estado.APROBADA)
                   .select_related("cotizacion__proveedor")}
    faltan = []
    for proveedor in sorted(proveedores, key=lambda p: p.nombre):
        for dato in OrdenCompra.datos_faltantes(proveedor):
            if dato not in faltan:
                faltan.append(dato)
    return faltan


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
    """RF-20 / CU-20: cuando todos los materiales tienen línea aprobada, la SM
    pasa a 'En cotización' (se notifica al JP) y se habilita generar la OC."""
    if _todas_las_lineas_aprobadas(solicitud) and solicitud.estado == SolicitudMaterial.Estado.EMITIDA:
        solicitud.cambiar_estado(
            SolicitudMaterial.Estado.EN_COTIZACION,
            "Todos los materiales tienen una cotización aprobada. Adquisiciones "
            "ya puede generar la orden de compra.")


@transaction.atomic
def _generar_ordenes_compra(solicitud, usuario, folio_con_punto=False):
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
            folio_con_punto=folio_con_punto,
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

    solicitud.cambiar_estado(
        SolicitudMaterial.Estado.OC_GENERADA,
        "Órdenes de compra generadas: "
        + ", ".join(f"{o.correlativo} ({o.proveedor.nombre})" for o in ordenes)
        + ". Quedan en borrador esperando la aprobación del Jefe de Proyecto.")
    return ordenes


# ----------------------------------------------------------------------------
# Órdenes de Compra
# ----------------------------------------------------------------------------
@rol_requerido(EA)
def orden_crear(request):
    """
    Compra anticipada: Adquisiciones emite una orden sin que ninguna obra la
    haya pedido.

    Es el caso de adelantarse a la obra —comprar el fierro antes de que parta,
    tomar un precio que hoy está bueno— y el de reponer lo que siempre se gasta.
    Como la decisión es de Adquisiciones, el Encargado la deja en borrador y la
    autoriza él mismo desde el detalle; no hay a quién pedirle permiso cuando
    nadie la pidió.
    """
    if request.method == "POST":
        form = OrdenDirectaForm(request.POST)
        formset = OrdenDirectaLineaFormSet(
            request.POST, queryset=OrdenCompraLinea.objects.none())
        if form.is_valid() and formset.is_valid():
            lineas = [
                f.cleaned_data for f in formset.forms
                if f.cleaned_data.get("material") and f.cleaned_data.get("cantidad")
            ]
            faltan = OrdenCompra.datos_faltantes(form.cleaned_data["proveedor"])
            if not lineas:
                messages.error(request, "Agrega al menos un material a la orden.")
            elif faltan:
                messages.error(
                    request, "No se puede emitir la orden: falta " + "; ".join(faltan) + ".")
            else:
                with transaction.atomic():
                    orden = form.save(commit=False)
                    orden.solicitud = None
                    orden.creada_por = request.user
                    orden.estado = OrdenCompra.Estado.BORRADOR
                    orden.folio_con_punto = _folio_con_punto(request)
                    orden.save()
                    for datos in lineas:
                        material = datos["material"]
                        OrdenCompraLinea.objects.create(
                            orden=orden,
                            material=material,
                            descripcion=material.nombre,
                            cantidad=datos["cantidad"],
                            unidad_medida=getattr(material, "unidad_medida", "") or "",
                            valor_unitario=datos["valor_unitario"],
                        )
                registrar(request.user, RegistroAuditoria.Accion.OC_EMITIDA,
                          f"Emitió una compra anticipada a {orden.proveedor.nombre} "
                          f"para {orden.proyecto.nombre}.", orden.correlativo)
                messages.success(
                    request,
                    f"Orden {orden.correlativo} creada en borrador. "
                    f"Revísala y apruébala para enviarla al proveedor.")
                return redirect("adquisiciones:orden_detalle", pk=orden.pk)
    else:
        form = OrdenDirectaForm()
        formset = OrdenDirectaLineaFormSet(queryset=OrdenCompraLinea.objects.none())

    contexto = {"form": form, "formset": formset, **_contexto_folio()}
    if request.method == "POST":
        contexto["folio_con_punto_preferido"] = _folio_con_punto(request)
    return render(request, "adquisiciones/orden_crear.html", contexto)


@rol_requerido(EA, "JEFE_PROYECTO")
def orden_lista(request):
    ordenes = OrdenCompra.objects.select_related(
        "proveedor", "proyecto", "solicitud__proyecto")
    estado = request.GET.get("estado")
    if estado:
        ordenes = ordenes.filter(estado=estado)
    if request.user.rol == "JEFE_PROYECTO":
        ordenes = ordenes.filter(proyecto__jefes=request.user).distinct()
    return render(request, "adquisiciones/orden_lista.html", {
        "ordenes": ordenes, "estado_filtro": estado or "",
        "estados": OrdenCompra.Estado.choices,
        "ultimo_folio": OrdenCompra.ultimo_folio_usado(),
        **_contexto_folio(),
    })


@rol_requerido(EA)
def folio_configurar(request):
    """
    Fija con qué folio sale la próxima OC.

    M5 numeraba sus órdenes a mano antes del sistema; esto permite empalmar
    con esa numeración (p. ej. seguir desde el 12.395) y, desde ahí, el folio
    sube solo. No se acepta un número ya usado o menor: dos órdenes con el
    mismo folio serían dos documentos distintos con la misma identidad.
    """
    from usuarios.models import ParametrosSistema

    if request.method != "POST":
        return redirect("adquisiciones:orden_lista")
    texto = (request.POST.get("siguiente_folio") or "").replace(".", "").strip()
    ultimo = OrdenCompra.ultimo_folio_usado()
    try:
        numero = int(texto)
    except ValueError:
        messages.error(request, "El folio debe ser un número entero, por ejemplo 12395.")
        return redirect("adquisiciones:orden_lista")
    if numero < 1 or numero > 999_999_999:
        messages.error(request, "El folio debe estar entre 1 y 999.999.999.")
    elif numero <= ultimo:
        messages.error(
            request,
            f"El folio {OrdenCompra.formatear_folio(ultimo, True)} ya fue usado. "
            f"El próximo tiene que ser mayor.")
    else:
        parametros = ParametrosSistema.actuales()
        anterior = parametros.siguiente_folio_oc
        parametros.siguiente_folio_oc = numero
        parametros.actualizado_por = request.user
        parametros.save()
        registrar(request.user, RegistroAuditoria.Accion.PARAMETROS_MODIFICADOS,
                  f"Cambió el próximo folio de OC de {anterior} a {numero}.", "Folio OC")
        messages.success(
            request,
            f"Listo: la próxima orden de compra saldrá con el folio {numero} "
            f"y desde ahí seguirá en ascenso automático.")
    return redirect("adquisiciones:orden_lista")


@rol_requerido(EA, "JEFE_PROYECTO", "CONTABILIDAD", "BODEGUERO")
def orden_detalle(request, pk):
    orden = get_object_or_404(
        OrdenCompra.objects.select_related(
            "proveedor", "proyecto", "solicitud__proyecto"), pk=pk)
    obra = orden.obra
    if (request.user.rol == "JEFE_PROYECTO"
            and (obra is None or not obra.dirigida_por(request.user))):
        raise PermissionDenied("Esta orden de compra pertenece a otro proyecto.")
    recepcion_form = RecepcionEstadoForm()

    if request.method == "POST":
        accion = request.POST.get("accion")

        # Quién puede dar el visto bueno depende de quién pidió la compra. Si
        # nació de una solicitud, la autoriza el Jefe de Proyecto de esa obra,
        # que es quien responde por el presupuesto. Si es una compra anticipada
        # que decidió Adquisiciones, la emite el propio Encargado: nadie se la
        # pidió, así que no hay a quién pedirle permiso.
        puede_autorizar = (
            request.user.rol in ("JEFE_PROYECTO", "ADMIN")
            or (orden.es_anticipada and request.user.rol == EA)
        )

        # RF-24: aprobar o rechazar el borrador
        if accion == "aprobar" and puede_autorizar:
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
                _enviar_orden_al_proveedor(request, orden)  # RF-25
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)

        # CU-25 Excepción 1: el envío falló o el proveedor no tiene correo. La OC
        # sigue "Aprobada"; Adquisiciones reintenta o la entrega por otra vía.
        if accion in ("reintentar_envio", "envio_manual") and request.user.rol in (EA, "ADMIN"):
            if orden.estado != OrdenCompra.Estado.APROBADA:
                messages.error(request, "Solo se gestiona el envío de una OC aprobada que no salió.")
            elif accion == "reintentar_envio":
                _enviar_orden_al_proveedor(request, orden)
            else:
                medio = (request.POST.get("medio") or "").strip()
                if not medio:
                    messages.error(request, "Indica cómo se entregó la OC al proveedor.")
                else:
                    orden.estado = OrdenCompra.Estado.ENVIADA
                    orden.fecha_envio = timezone.now()
                    orden.save(update_fields=["estado", "fecha_envio"])
                    registrar(request.user, RegistroAuditoria.Accion.OC_ENVIADA,
                              f"Registró la entrega manual de la OC a {orden.proveedor.nombre}: {medio}",
                              orden.correlativo)
                    _avanzar_sm_por_envio(orden)
                    messages.success(request, f"OC {orden.correlativo} marcada como enviada ({medio}).")
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)

        if accion == "rechazar" and puede_autorizar:
            motivo = request.POST.get("motivo", "").strip()
            if orden.estado != OrdenCompra.Estado.BORRADOR:
                messages.error(request, "Solo se puede rechazar una OC en borrador.")
            elif not motivo:
                messages.error(request, "Debes indicar el motivo del rechazo.")
            else:
                orden.estado = OrdenCompra.Estado.RECHAZADA
                orden.motivo_rechazo = motivo
                orden.save(update_fields=["estado", "motivo_rechazo"])
                # RF-22: se notifica al usuario de Adquisiciones que generó la OC
                notificar(
                    [orden.creada_por],
                    f"OC {orden.correlativo} rechazada",
                    f"{request.user.get_full_name() or request.user.username} rechazó la orden "
                    f"{orden.correlativo} a {orden.proveedor.nombre}.\nMotivo: {motivo}\n\n"
                    f"Puedes corregirla y devolverla a borrador para reenviarla a aprobación.",
                    url=reverse("adquisiciones:orden_detalle", args=[orden.pk]))
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
            recepcion_form = RecepcionEstadoForm(request.POST, orden=orden)
            # NO_RECIBIDA se incluye a propósito: es el estado que se pone cuando
            # el proveedor no entregó a tiempo, y la entrega atrasada es el caso
            # normal. Si fuera terminal, una entrega tardía no se podría registrar.
            if orden.estado not in (OrdenCompra.Estado.ENVIADA,
                                    OrdenCompra.Estado.RECEPCION_PARCIAL,
                                    OrdenCompra.Estado.NO_RECIBIDA):
                messages.error(
                    request,
                    "La recepción sólo se actualiza sobre una OC ya emitida al proveedor.")
            elif recepcion_form.is_valid():
                nuevo = recepcion_form.cleaned_data["estado"]
                orden.estado = nuevo
                orden.save(update_fields=["estado"])
                if orden.solicitud_id:
                    _refrescar_estado_recepcion_sm(orden.solicitud)
                notificar_recepcion(orden, recepcion_form.cleaned_data.get("nota", ""))
                messages.success(request, f"Recepción actualizada a «{orden.get_estado_display()}».")
            else:
                for error in recepcion_form.non_field_errors():
                    messages.error(request, error)
                return redirect("adquisiciones:orden_detalle", pk=orden.pk)
            return redirect("adquisiciones:orden_detalle", pk=orden.pk)

    return render(request, "adquisiciones/orden_detalle.html", {
        "orden": orden,
        "obra": obra,
        "recepcion_form": recepcion_form,
        # La plantilla decide con esto si muestra los botones de autorizar.
        "puede_autorizar": (
            request.user.rol in ("JEFE_PROYECTO", "ADMIN")
            or (orden.es_anticipada and request.user.rol == EA)
        ),
        # RF-26 / RF-33: Bodega no ve precios unitarios ni totales
        "oculta_precios": request.user.rol == "BODEGUERO",
        "puede_gestionar_envio": request.user.rol in (EA, "ADMIN"),
        "puede_pdf": orden.autorizada and request.user.rol in (EA, "JEFE_PROYECTO", "ADMIN"),
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
    """RF-24 / CU-24: exporta la OC aprobada a PDF con el logotipo corporativo."""
    orden = get_object_or_404(OrdenCompra, pk=pk)
    obra = orden.obra
    if request.user.rol == "JEFE_PROYECTO" and (obra is None or not obra.dirigida_por(request.user)):
        raise PermissionDenied("Esta orden de compra pertenece a otro proyecto.")
    if not orden.autorizada:
        # CU-24 Excepción 1
        messages.error(request, "La orden de compra debe estar aprobada para exportarla a PDF.")
        return redirect("adquisiciones:orden_detalle", pk=orden.pk)
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
    """
    Correo saliente. Devuelve True si el servidor de correo lo aceptó.
    Las fallas ya no se silencian: el RF-25 depende de saber si salió.
    """
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        return False
    # Reply-To: el correo sale desde la casilla del sistema, pero las
    # respuestas del proveedor tienen que llegarle a una persona.
    responder_a = [settings.EMAIL_REPLY_TO] if settings.EMAIL_REPLY_TO else None
    msg = EmailMessage(subject=asunto, body=cuerpo, to=destinatarios, reply_to=responder_a)
    if adjunto:
        nombre, contenido, mime = adjunto
        msg.attach(nombre, contenido, mime)
    try:
        return msg.send(fail_silently=False) > 0
    except Exception:
        return False


def _avanzar_sm_por_envio(orden):
    """La SM queda con OC generada cuando su OC sale al proveedor."""
    if orden.solicitud_id and orden.solicitud.estado in (
            SolicitudMaterial.Estado.EN_COTIZACION,
            SolicitudMaterial.Estado.EMITIDA):
        orden.solicitud.cambiar_estado(SolicitudMaterial.Estado.OC_GENERADA)


def _enviar_orden_al_proveedor(request, orden):
    """
    RF-25 / CU-25: al aprobarse, la OC sale en PDF al correo del proveedor y,
    completado el envío, pasa a "Enviada".

    Excepción 1: si el proveedor no tiene correo o el envío falla, la OC queda
    "Aprobada" y se notifica a Adquisiciones para que la gestione a mano
    (reintentar el envío o registrar que la entregó por otra vía). Así ninguna
    OC figura como enviada sin haber salido.
    """
    adjunto = None
    try:
        adjunto = (f"{orden.correlativo}.pdf", generar_pdf_orden(orden), "application/pdf")
    except ReportlabNoInstalado:
        adjunto = None

    enviado = False
    if orden.proveedor.correo and adjunto:
        total_txt = f"{orden.total_con_iva:,.0f}".replace(",", ".")
        enviado = _notificar(
            [orden.proveedor.correo],
            f"Orden de Compra {orden.correlativo} — Constructora M5 SpA",
            f"Estimado proveedor,\n\nAdjuntamos la Orden de Compra {orden.correlativo} "
            f"por un total de ${total_txt} (IVA incluido).\n\n"
            f"Saludos,\nDepartamento de Adquisiciones — M5 SpA",
            adjunto=adjunto,
        )

    if enviado:
        orden.estado = OrdenCompra.Estado.ENVIADA
        orden.fecha_envio = timezone.now()
        orden.save(update_fields=["estado", "fecha_envio"])
        registrar(request.user, RegistroAuditoria.Accion.OC_ENVIADA,
                  f"Envió la orden de compra a {orden.proveedor.nombre} "
                  f"({orden.proveedor.correo}).", orden.correlativo)
        _avanzar_sm_por_envio(orden)
        messages.success(request, f"OC {orden.correlativo} aprobada y enviada a {orden.proveedor.correo}.")
        return True

    if not orden.proveedor.correo:
        motivo = f"{orden.proveedor.nombre} no tiene correo registrado"
    elif adjunto is None:
        motivo = "no se pudo generar el PDF (falta la librería reportlab)"
    else:
        motivo = f"el correo a {orden.proveedor.correo} no se pudo enviar"
    destinatarios = usuarios_con_rol(EA)
    if orden.creada_por not in destinatarios:
        destinatarios.append(orden.creada_por)
    notificar(
        destinatarios,
        f"OC {orden.correlativo} aprobada pero NO enviada",
        f"La orden {orden.correlativo} a {orden.proveedor.nombre} fue aprobada, pero {motivo}. "
        f"Sigue en estado «Aprobada»: reintenta el envío o entrégala por otra vía y "
        f"registra la entrega en el sistema.",
        url=reverse("adquisiciones:orden_detalle", args=[orden.pk]))
    messages.warning(
        request,
        f"OC {orden.correlativo} aprobada, pero no se envió: {motivo}. Queda «Aprobada» y se "
        f"avisó a Adquisiciones para que gestione el envío.")
    return False


def notificar_recepcion(orden, nota=""):
    """
    RF-35: avisa a los Jefes de Proyecto de la obra el nuevo estado de
    recepción de la OC, con la cantidad recibida de cada material.
    """
    obra = orden.obra
    if obra is None:
        return
    detalle = "\n".join(
        f"· {l.descripcion}: {cant(l.cantidad_recibida)} de {cant(l.cantidad)} {l.unidad_medida}"
        for l in orden.lineas.all())
    cuerpo = (f"La orden {orden.correlativo} ({orden.proveedor.nombre}) quedó "
              f"«{orden.get_estado_display()}».\n\nCantidades recibidas:\n{detalle}")
    if nota:
        cuerpo += f"\n\nNota: {nota}"
    notificar(list(obra.jefes.all()), f"OC {orden.correlativo}: {orden.get_estado_display()}",
              cuerpo, url=reverse("adquisiciones:orden_detalle", args=[orden.pk]))


def _refrescar_estado_recepcion_sm(solicitud):
    """RF-39: refleja en la SM el estado global de recepción de sus OC."""
    ordenes = solicitud.ordenes_compra.all()
    if not ordenes:
        return
    # Las OC rechazadas o en borrador todavía no son una entrega pendiente
    # de nadie; el estado de la SM lo deciden las que salieron al proveedor.
    vigentes = [o for o in ordenes if o.estado not in (
        OrdenCompra.Estado.BORRADOR, OrdenCompra.Estado.RECHAZADA)]
    if not vigentes:
        return
    estados = set(o.estado for o in vigentes)
    if estados <= {OrdenCompra.Estado.RECIBIDA}:
        nuevo = SolicitudMaterial.Estado.RECIBIDA
    elif estados & {OrdenCompra.Estado.RECEPCION_PARCIAL, OrdenCompra.Estado.RECIBIDA}:
        nuevo = SolicitudMaterial.Estado.RECEPCION_PARCIAL
    elif estados & {OrdenCompra.Estado.NO_RECIBIDA}:
        # Alguna OC no llegó: la SM vuelve a OC_GENERADA para que se vea que
        # sigue pendiente, en vez de quedarse muda esperando.
        nuevo = SolicitudMaterial.Estado.OC_GENERADA
    else:
        return
    detalle = "; ".join(f"{o.correlativo}: {o.get_estado_display()}" for o in vigentes)
    solicitud.cambiar_estado(nuevo, f"Estado de recepción de sus órdenes de compra: {detalle}.")


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
