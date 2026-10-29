"""
Vistas de Solicitudes de Material.
CU-11 Generando solicitud de materiales
CU-12 Agregando materiales a la solicitud
CU-14 Editando solicitud (en borrador)
CU-16 Registrando emisor y fecha de la solicitud (asignados automáticamente al crear)
CU-17 Visualizando estado de la solicitud
Flujo de estados (enviar / aprobar / rechazar) que apoya la visualización del CU-17.
"""
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from auditoria.models import RegistroAuditoria, registrar
from .models import SolicitudMaterial, SolicitudDetalle, SolicitudAdjunto
from .forms import (
    SolicitudForm, SolicitudDetalleForm, SolicitudDetalleFormSet, SolicitudAdjuntoForm,
)


def _exigir_propiedad(usuario, solicitud):
    """
    Un Jefe de Proyecto trabaja lo suyo: las solicitudes que él emitió y las de
    las obras que dirige. Sin esto, cualquier jefe podría editar o enviar el
    pedido de la obra de otro, que es plata de un presupuesto que no maneja.

    Adquisiciones y Administración no tienen esta restricción: su trabajo es
    justamente mirar las solicitudes de todas las obras.
    """
    if usuario.rol != "JEFE_PROYECTO":
        return
    es_suya = solicitud.emisor_id == usuario.pk
    dirige_la_obra = solicitud.proyecto.jefe_proyecto_id == usuario.pk
    if not (es_suya or dirige_la_obra):
        raise PermissionDenied(
            "Esta solicitud es de otra obra. Solo puedes trabajar las de los "
            "proyectos que diriges.")


def _avisar_a_adquisiciones(solicitud):
    """
    Avisa que hay una solicitud esperando cotización.

    No es lo que hace llegar el pedido —para eso basta con que quede en estado
    aprobado y aparezca en la bandeja de cotizaciones— sino el empujón para que
    nadie tenga que estar mirando la pantalla. Si el correo no está configurado
    el pedido llega igual, sólo que sin aviso.
    """
    from usuarios.models import Usuario

    destinos = list(
        Usuario.objects
        .filter(rol="ENCARGADO_ADQUISICIONES", estado=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not destinos:
        return
    try:
        send_mail(
            subject=f"Solicitud {solicitud.correlativo} lista para cotizar",
            message=(
                f"{solicitud.emisor.get_full_name() or solicitud.emisor.username} "
                f"emitió la solicitud {solicitud.correlativo} para "
                f"{solicitud.proyecto.nombre}, con {solicitud.total_items} ítem(s).\n\n"
                f"Queda esperando cotización en el sistema."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinos,
            fail_silently=True,
        )
    except Exception:  # pragma: no cover - el aviso nunca bloquea la solicitud
        pass


class SolicitudListView(RolRequeridoMixin, ListView):
    """CU-17 Consultando solicitudes (listado)."""
    # Bodega y Contabilidad ya pueden abrir una solicitud concreta; sin el
    # listado tenían que llegar a ella de memoria, por la URL. Bodega necesita
    # ver qué se pidió para saber qué le va a llegar, y Contabilidad para cruzar
    # la factura con lo que se encargó.
    roles_permitidos = ["ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO",
                        "BODEGUERO", "CONTABILIDAD", "ADMIN"]
    model = SolicitudMaterial
    template_name = "solicitudes/solicitud_list.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        qs = super().get_queryset()
        estado = self.request.GET.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        todas = SolicitudMaterial.objects.all()
        ctx["metricas"] = {
            "total": todas.count(),
            "borradores": todas.filter(estado=SolicitudMaterial.Estado.BORRADOR).count(),
            "enviadas": todas.filter(estado=SolicitudMaterial.Estado.ENVIADA).count(),
            "aprobadas": todas.filter(estado=SolicitudMaterial.Estado.APROBADA).count(),
            "rechazadas": todas.filter(estado=SolicitudMaterial.Estado.RECHAZADA).count(),
        }
        ctx["estado_filtro"] = self.request.GET.get("estado", "")
        ctx["estados"] = SolicitudMaterial.Estado
        return ctx


@rol_requerido("ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO")
def solicitud_crear(request):
    """
    CU-11 Generando solicitud de materiales. CU-12 Agregar ítems en la misma pantalla.

    La origina quien detecta la falta. En la obra ese es el Jefe de Proyecto, que
    sabe qué material se está acabando; en la oficina, el Encargado de
    Adquisiciones, cuando el pedido le llega por teléfono o se adelanta a una
    obra que todavía no parte. Los dos pueden emitirla.
    """
    if request.method == "POST":
        form = SolicitudForm(request.POST, usuario=request.user)
        formset = SolicitudDetalleFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            solicitud = form.save(commit=False)
            solicitud.emisor = request.user
            solicitud.save()
            formset.instance = solicitud
            formset.save()
            messages.success(request, f"Solicitud {solicitud.correlativo} creada.")
            return redirect("solicitudes:detalle", pk=solicitud.pk)
    else:
        form = SolicitudForm(usuario=request.user)
        formset = SolicitudDetalleFormSet()
    return render(request, "solicitudes/solicitud_form.html", {"form": form, "formset": formset})


@rol_requerido("ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO", "CONTABILIDAD", "BODEGUERO")
def solicitud_detalle(request, pk):
    """CU-17 Consultando solicitud (cabecera + líneas) y CU-12 agregar ítems.
    Inc.2: RF-16 (justificación por exceso de itemizado) y RF-17 (adjuntos)."""
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    detalle_form = SolicitudDetalleForm(solicitud=solicitud)
    cab_form = SolicitudForm(instance=solicitud, usuario=request.user)
    adjunto_form = SolicitudAdjuntoForm()

    if request.method == "POST":
        accion = request.POST.get("accion")

        # RF-17: adjuntar archivo de respaldo (permitido mientras la SM no esté cerrada)
        if accion == "adjuntar":
            if solicitud.total_adjuntos >= SolicitudAdjunto.MAX_POR_SOLICITUD:
                messages.error(
                    request,
                    f"La solicitud ya tiene el máximo de {SolicitudAdjunto.MAX_POR_SOLICITUD} archivos.",
                )
                return redirect("solicitudes:detalle", pk=solicitud.pk)
            adjunto_form = SolicitudAdjuntoForm(request.POST, request.FILES)
            if adjunto_form.is_valid():
                adjunto = adjunto_form.save(commit=False)
                adjunto.solicitud = solicitud
                adjunto.subido_por = request.user
                adjunto.save()
                messages.success(request, "Archivo adjuntado.")
                return redirect("solicitudes:detalle", pk=solicitud.pk)

        elif solicitud.editable and accion == "agregar_material":
            detalle_form = SolicitudDetalleForm(request.POST, solicitud=solicitud)
            if detalle_form.is_valid():
                detalle = detalle_form.save(commit=False)
                detalle.solicitud = solicitud
                detalle.save()
                messages.success(request, "Material agregado.")
                return redirect("solicitudes:detalle", pk=solicitud.pk)

        elif solicitud.editable and accion == "editar_cabecera":
            cab_form = SolicitudForm(request.POST, instance=solicitud, usuario=request.user)
            if cab_form.is_valid():
                cab_form.save()
                messages.success(request, "Solicitud actualizada.")
                return redirect("solicitudes:detalle", pk=solicitud.pk)

    E = SolicitudMaterial.Estado
    orden = [E.BORRADOR, E.ENVIADA, E.APROBADA, E.EN_COTIZACION, E.OC_GENERADA, E.RECIBIDA]
    iconos = {
        "BORRADOR": "✏", "ENVIADA": "📤", "APROBADA": "✓", "RECHAZADA": "✗",
        "EN_COTIZACION": "$", "OC_GENERADA": "🧾", "RECEPCION_PARCIAL": "◧", "RECIBIDA": "📦",
    }
    labels = {
        "BORRADOR": "Borrador", "ENVIADA": "Enviada", "APROBADA": "Aprobada", "RECHAZADA": "Rechazada",
        "EN_COTIZACION": "En cotización", "OC_GENERADA": "OC generada",
        "RECEPCION_PARCIAL": "Entrega parcial", "RECIBIDA": "Entregada",
    }
    estado_actual = solicitud.estado
    if estado_actual == E.RECHAZADA:
        pasos = [E.BORRADOR, E.ENVIADA, E.RECHAZADA]
    elif estado_actual == E.RECEPCION_PARCIAL:
        pasos = [E.BORRADOR, E.ENVIADA, E.APROBADA, E.EN_COTIZACION, E.OC_GENERADA, E.RECEPCION_PARCIAL]
    else:
        pasos = orden
    idx_actual = pasos.index(estado_actual) if estado_actual in pasos else len(pasos)
    estados_progreso = [
        (labels[e], iconos[e], e == estado_actual, pasos.index(e) < idx_actual)
        for e in pasos
    ]

    return render(request, "solicitudes/solicitud_detail.html", {
        "solicitud": solicitud,
        "form": detalle_form,
        "cab_form": cab_form,
        "adjunto_form": adjunto_form,
        "estados_progreso": estados_progreso,
        "max_adjuntos": SolicitudAdjunto.MAX_POR_SOLICITUD,
        # Las plantillas comparaban el rol a mano y dejaban al ADMIN sin botones,
        # aunque el decorador sí lo deja pasar. Se calcula aquí, con la misma
        # regla que usuarios.permisos: ADMIN siempre puede.
        # Los botones de trabajar la solicitud (agregar material, editar, enviar)
        # los ve Adquisiciones siempre, y el Jefe de Proyecto sobre lo suyo: su
        # propio pedido o el de una obra que dirige.
        "puede_gestionar": (
            request.user.rol in ("ENCARGADO_ADQUISICIONES", "ADMIN")
            or (request.user.rol == "JEFE_PROYECTO"
                and (solicitud.emisor_id == request.user.pk
                     or solicitud.proyecto.jefe_proyecto_id == request.user.pk))
        ),
        "puede_resolver": request.user.rol in ("JEFE_PROYECTO", "ADMIN"),
        # RF-39: órdenes de compra generadas a partir de esta SM y su recepción
        "ordenes_compra": solicitud.ordenes_compra.all() if hasattr(solicitud, "ordenes_compra") else [],
    })


@rol_requerido("ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO", "ADMIN")
@require_POST
def adjunto_eliminar(request, pk):
    """RF-17: quitar un archivo adjunto de la solicitud."""
    adjunto = get_object_or_404(SolicitudAdjunto, pk=pk)
    solicitud = adjunto.solicitud
    adjunto.archivo.delete(save=False)
    adjunto.delete()
    messages.success(request, "Archivo eliminado.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)


@rol_requerido("ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO")
def solicitud_editar(request, pk):
    """CU-14 Editando solicitud (solo en borrador)."""
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    _exigir_propiedad(request.user, solicitud)
    if not solicitud.editable:
        messages.error(request, "Solo se pueden editar solicitudes en borrador.")
        return redirect("solicitudes:detalle", pk=solicitud.pk)
    if request.method == "POST":
        form = SolicitudForm(request.POST, instance=solicitud, usuario=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Solicitud actualizada.")
            return redirect("solicitudes:detalle", pk=solicitud.pk)
    else:
        form = SolicitudForm(instance=solicitud, usuario=request.user)
    return render(request, "solicitudes/solicitud_form.html", {"form": form, "solicitud": solicitud})


@rol_requerido("ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO")
@require_POST
def detalle_eliminar(request, pk):
    """CU-14: quitar una línea de la solicitud mientras está en borrador."""
    detalle = get_object_or_404(SolicitudDetalle, pk=pk)
    solicitud = detalle.solicitud
    _exigir_propiedad(request.user, solicitud)
    if solicitud.editable:
        detalle.delete()
        messages.success(request, "Material quitado de la solicitud.")
    else:
        messages.error(request, "No se puede modificar una solicitud que ya fue enviada.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)


@rol_requerido("ENCARGADO_ADQUISICIONES", "JEFE_PROYECTO")
@require_POST
def solicitud_enviar(request, pk):
    """CU-16: enviar la solicitud para aprobación (BORRADOR -> ENVIADA)."""
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    _exigir_propiedad(request.user, solicitud)
    if solicitud.estado != SolicitudMaterial.Estado.BORRADOR:
        messages.error(request, "La solicitud ya fue enviada.")
    elif solicitud.total_items == 0:
        messages.error(request, "No puedes enviar una solicitud sin materiales.")
    else:
        # Quién la ESCRIBIÓ decide si necesita visto bueno, no quién aprieta el
        # botón: la autorización es sobre el pedido, no sobre el clic.
        #
        # El Jefe de Proyecto responde por el presupuesto de su obra, así que lo
        # que él pide ya está autorizado y pasa derecho a Adquisiciones para
        # cotizar. Cualquier otro —Adquisiciones adelantándose, Administración
        # registrando un pedido que llegó por teléfono— compromete plata de una
        # obra que dirige otro, y por eso se manda a aprobar.
        propia = solicitud.emisor.rol == "JEFE_PROYECTO"
        if propia:
            solicitud.estado = SolicitudMaterial.Estado.APROBADA
            aviso = (f"Solicitud {solicitud.correlativo} enviada a Adquisiciones "
                     f"para cotizar.")
        else:
            solicitud.estado = SolicitudMaterial.Estado.ENVIADA
            aviso = f"Solicitud {solicitud.correlativo} enviada para aprobación."
        solicitud.save()
        # CU-53: la emisión de una SM es una acción auditable
        registrar(request.user, RegistroAuditoria.Accion.SM_EMITIDA,
                  f"Emitió la solicitud de material para {solicitud.proyecto.nombre} "
                  f"({solicitud.total_items} ítem(s)).", solicitud.correlativo)
        if propia:
            _avisar_a_adquisiciones(solicitud)
        messages.success(request, aviso)
    return redirect("solicitudes:detalle", pk=solicitud.pk)


@rol_requerido("JEFE_PROYECTO")
@require_POST
def solicitud_resolver(request, pk, accion):
    """CU-16: el Jefe de Proyecto aprueba o rechaza (ENVIADA -> APROBADA/RECHAZADA)."""
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    if solicitud.estado != SolicitudMaterial.Estado.ENVIADA:
        messages.error(request, "Solo se pueden resolver solicitudes enviadas.")
    elif accion == "aprobar":
        solicitud.estado = SolicitudMaterial.Estado.APROBADA
        solicitud.save()
        registrar(request.user, RegistroAuditoria.Accion.SM_APROBADA,
                  f"Aprobó la solicitud de {solicitud.proyecto.nombre}.",
                  solicitud.correlativo)
        messages.success(request, f"Solicitud {solicitud.correlativo} aprobada.")
    elif accion == "rechazar":
        solicitud.estado = SolicitudMaterial.Estado.RECHAZADA
        solicitud.motivo_rechazo = (request.POST.get("motivo") or "").strip()
        solicitud.save()
        registrar(request.user, RegistroAuditoria.Accion.SM_RECHAZADA,
                  f"Rechazó la solicitud de {solicitud.proyecto.nombre}"
                  + (f": {solicitud.motivo_rechazo}" if solicitud.motivo_rechazo else "."),
                  solicitud.correlativo)
        messages.warning(request, f"Solicitud {solicitud.correlativo} rechazada.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)


@rol_requerido("ENCARGADO_ADQUISICIONES")
@require_POST
def solicitud_devolver_borrador(request, pk):
    """
    Una SM rechazada vuelve a borrador para corregirla.

    El Jefe de Proyecto rechaza casi siempre por un detalle —una cantidad mal
    puesta, una justificación que falta— y antes de esto la única salida era
    rehacer la solicitud entera: se perdía el correlativo, las líneas y los
    adjuntos. La Orden de Compra ya tenía esta vuelta; la Solicitud no, y no
    había ninguna razón para la asimetría.
    """
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    if solicitud.estado != SolicitudMaterial.Estado.RECHAZADA:
        messages.error(request, "Sólo se corrige una solicitud rechazada.")
    else:
        solicitud.estado = SolicitudMaterial.Estado.BORRADOR
        solicitud.motivo_rechazo = ""
        solicitud.save(update_fields=["estado", "motivo_rechazo"])
        messages.success(
            request,
            f"Solicitud {solicitud.correlativo} devuelta a borrador. "
            f"Corrige lo que corresponda y vuelve a enviarla.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)
