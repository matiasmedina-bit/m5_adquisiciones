"""
Vistas de Solicitudes de Material — Módulo 3 (RF-12 a RF-15).

CU-12 Creando Solicitud de Materiales (Jefe de Proyecto, obra "En ejecución")
CU-13 Justificando exceso de itemizado (en SolicitudDetalleForm)
CU-14 Adjuntando archivos de respaldo (hasta 3, PDF/JPG, 5 MB)
CU-15 Notificando cambios de estado (SolicitudMaterial.cambiar_estado)

Ciclo de vida (RF-15):

    Borrador ──emitir──► Emitida ──(todas las líneas aprobadas)──► En cotización
       ▲                   │                                           │
       │                   └──────── rechazar (Adquisiciones) ─────────┤
       └── corregir ── Rechazada ◄─────────────────────────────────────┘
                                         En cotización ──► OC generada
                          OC generada ──► Entregada parcialmente ──► Entregada

"Borrador" es el estado previo a la confirmación que pide el RF-12: mientras la
SM se arma no tiene número ni la ve Adquisiciones. Al emitirla recibe su
correlativo y queda "Emitida".
"""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from auditoria.models import RegistroAuditoria, registrar
from usuarios.notificaciones import notificar, usuarios_con_rol
from usuarios.permisos import RolRequeridoMixin, rol_requerido
from .forms import (
    SolicitudAdjuntoForm, SolicitudDetalleForm, SolicitudDetalleFormSet, SolicitudForm,
)
from .models import SolicitudAdjunto, SolicitudDetalle, SolicitudMaterial

E = SolicitudMaterial.Estado
EA = "ENCARGADO_ADQUISICIONES"
# Quiénes consultan solicitudes. Bodega y Contabilidad sólo leen (Bodega sin
# precios): necesitan saber qué se pidió para recibirlo y para cruzar facturas.
ROLES_CONSULTA = ["JEFE_PROYECTO", EA, "BODEGUERO", "CONTABILIDAD"]


# ---------------------------------------------------------------------------
# Reglas de acceso
# ---------------------------------------------------------------------------
def es_responsable(usuario, solicitud):
    """El Jefe de Proyecto que la emitió o que dirige la obra (o el ADMIN)."""
    if usuario.rol == "ADMIN":
        return True
    if usuario.rol != "JEFE_PROYECTO":
        return False
    return solicitud.emisor_id == usuario.pk or solicitud.proyecto.dirigida_por(usuario)


def exigir_lectura(usuario, solicitud):
    """Un Jefe de Proyecto sólo ve las solicitudes de sus obras."""
    if usuario.rol == "JEFE_PROYECTO" and not es_responsable(usuario, solicitud):
        raise PermissionDenied(
            "Esta solicitud es de otra obra. Solo puedes ver las de los proyectos que diriges.")


def exigir_responsable(usuario, solicitud):
    """Armar, emitir, adjuntar o corregir la SM es del Jefe de Proyecto responsable."""
    if not es_responsable(usuario, solicitud):
        raise PermissionDenied(
            "Solo el Jefe de Proyecto responsable de la obra puede modificar esta solicitud.")


def solicitudes_visibles(usuario):
    qs = SolicitudMaterial.objects.select_related("proyecto", "emisor")
    if usuario.rol == "JEFE_PROYECTO":
        qs = qs.filter(Q(emisor=usuario) | Q(proyecto__jefes=usuario)).distinct()
    elif usuario.rol != "ADMIN":
        # Los borradores no existen todavía para el resto: no están confirmados.
        qs = qs.exclude(estado=E.BORRADOR)
    return qs


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------
class SolicitudListView(RolRequeridoMixin, ListView):
    roles_permitidos = ROLES_CONSULTA
    model = SolicitudMaterial
    template_name = "solicitudes/solicitud_list.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        qs = solicitudes_visibles(self.request.user)
        estado = self.request.GET.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        todas = solicitudes_visibles(self.request.user)
        ctx["metricas"] = {
            "total": todas.count(),
            "borradores": todas.filter(estado=E.BORRADOR).count(),
            "emitidas": todas.filter(estado=E.EMITIDA).count(),
            "en_curso": todas.filter(estado__in=[E.EN_COTIZACION, E.OC_GENERADA,
                                                 E.RECEPCION_PARCIAL]).count(),
            "entregadas": todas.filter(estado=E.RECIBIDA).count(),
            "rechazadas": todas.filter(estado=E.RECHAZADA).count(),
        }
        ctx["estado_filtro"] = self.request.GET.get("estado", "")
        ctx["estado_filtro_label"] = dict(E.choices).get(ctx["estado_filtro"], "")
        ctx["estados"] = E.choices
        ctx["puede_crear"] = self.request.user.rol in ("JEFE_PROYECTO", "ADMIN")
        return ctx


# ---------------------------------------------------------------------------
# CU-12 — Crear (borrador) y emitir
# ---------------------------------------------------------------------------
@rol_requerido("JEFE_PROYECTO")
def solicitud_crear(request):
    """
    CU-12: el Jefe de Proyecto elige una obra "En ejecución" que tiene asignada
    y agrega una o más líneas (material del catálogo, cantidad, partida). La
    SM queda en borrador hasta que la emite (confirma) desde su detalle, donde
    además puede adjuntar los respaldos (CU-14).
    """
    if request.method == "POST":
        form = SolicitudForm(request.POST, usuario=request.user)
        proyecto = form.cleaned_data["proyecto"] if form.is_valid() else None
        # Con el proyecto ya conocido, cada línea valida su partida contra
        # el itemizado de esa obra (RF-12) y su saldo (RF-13).
        formset = SolicitudDetalleFormSet(request.POST, form_kwargs={"proyecto": proyecto})
        if form.is_valid() and formset.is_valid():
            solicitud = form.save(commit=False)
            solicitud.emisor = request.user
            solicitud.estado = E.BORRADOR
            solicitud.save()
            formset.instance = solicitud
            formset.save()
            messages.success(
                request,
                "Solicitud guardada en borrador. Revisa las líneas, adjunta los "
                "respaldos si corresponde y presiona «Emitir solicitud» para confirmarla.")
            return redirect("solicitudes:detalle", pk=solicitud.pk)
    else:
        form = SolicitudForm(usuario=request.user)
        formset = SolicitudDetalleFormSet()
    return render(request, "solicitudes/solicitud_form.html", {
        "form": form, "formset": formset,
        "sin_proyectos": not form.fields["proyecto"].queryset.exists(),
    })


@rol_requerido("JEFE_PROYECTO")
@require_POST
def solicitud_emitir(request, pk):
    """
    RF-12: al confirmar, el sistema asigna el correlativo y la SM queda
    "Emitida". Se revalida todo: entre que se armó el borrador y se emite,
    otra solicitud pudo consumir el saldo de la partida (RF-13).
    """
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    exigir_responsable(request.user, solicitud)
    if solicitud.estado != E.BORRADOR:
        messages.error(request, "Esta solicitud ya fue emitida.")
        return redirect("solicitudes:detalle", pk=solicitud.pk)
    if not solicitud.proyecto.admite_solicitudes:
        messages.error(
            request,
            "El proyecto está finalizado: no admite nuevas solicitudes de materiales."
            if solicitud.proyecto.esta_finalizado else
            "El proyecto ya no está «En ejecución»: no se puede emitir la solicitud.")
        return redirect("solicitudes:detalle", pk=solicitud.pk)

    detalles = list(solicitud.detalles.select_related("partida", "material"))
    problemas = []
    if not detalles:
        problemas.append("Agrega al menos un material.")
    for d in detalles:
        if not d.partida_id:
            problemas.append(f"«{d.material.nombre}» no está vinculado a una partida del itemizado.")
        elif d.excede_itemizado and not d.justificacion.strip():
            problemas.append(
                f"«{d.material.nombre}» supera el saldo restante de la partida "
                f"{d.partida.codigo_partida} y no tiene justificación.")
    if problemas:
        for p in problemas:
            messages.error(request, p)
        return redirect("solicitudes:detalle", pk=solicitud.pk)

    solicitud.cambiar_estado(
        E.EMITIDA, f"Emitida por {request.user.get_full_name() or request.user.username}, "
                   f"con {len(detalles)} ítem(s).")
    # CU-53: la emisión de una SM es una acción auditable
    registrar(request.user, RegistroAuditoria.Accion.SM_EMITIDA,
              f"Emitió la solicitud de material para {solicitud.proyecto.nombre} "
              f"({len(detalles)} ítem(s)).", solicitud.correlativo)
    # Aviso a Adquisiciones: la SM entró a su bandeja (RF-16)
    notificar(usuarios_con_rol(EA),
              f"Solicitud {solicitud.correlativo} lista para cotizar",
              f"{request.user.get_full_name() or request.user.username} emitió la solicitud "
              f"{solicitud.correlativo} para {solicitud.proyecto.nombre}, con "
              f"{len(detalles)} ítem(s).",
              url=reverse("adquisiciones:cotizacion_sm", args=[solicitud.pk]))
    messages.success(
        request, f"Solicitud emitida con el número {solicitud.correlativo}. "
                 f"Adquisiciones ya la tiene en su bandeja.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)


# ---------------------------------------------------------------------------
# Detalle (consulta + edición del borrador + adjuntos)
# ---------------------------------------------------------------------------
@rol_requerido(*ROLES_CONSULTA)
def solicitud_detalle(request, pk):
    solicitud = get_object_or_404(
        SolicitudMaterial.objects.select_related("proyecto", "emisor"), pk=pk)
    exigir_lectura(request.user, solicitud)
    if solicitud.estado == E.BORRADOR and not es_responsable(request.user, solicitud):
        raise PermissionDenied("Esta solicitud todavía no fue emitida.")

    responsable = es_responsable(request.user, solicitud)
    detalle_form = SolicitudDetalleForm(solicitud=solicitud)
    cab_form = SolicitudForm(instance=solicitud, usuario=request.user)
    adjunto_form = SolicitudAdjuntoForm()

    if request.method == "POST":
        # Todas las acciones de esta pantalla modifican la SM: sólo el
        # responsable (Excepción: Adquisiciones trabaja la SM desde la
        # pantalla de cotización, no desde aquí).
        exigir_responsable(request.user, solicitud)
        accion = request.POST.get("accion")

        # CU-14: adjuntar archivo de respaldo
        if accion == "adjuntar":
            if solicitud.total_adjuntos >= SolicitudAdjunto.MAX_POR_SOLICITUD:
                # CU-14 Excepción 3
                messages.error(
                    request,
                    f"La solicitud ya tiene el máximo de {SolicitudAdjunto.MAX_POR_SOLICITUD} "
                    f"archivos. Elimina uno para agregar otro.")
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
                if not detalle_form.cleaned_data.get("material"):
                    detalle_form.add_error("nombre_libre", "Elige un material del catálogo.")
                elif solicitud.detalles.filter(material=detalle_form.cleaned_data["material"]).exists():
                    detalle_form.add_error(
                        "nombre_libre", "Ese material ya está en la solicitud: edita su cantidad.")
                else:
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

        elif accion in ("agregar_material", "editar_cabecera"):
            messages.error(request, "Una solicitud emitida ya no se modifica.")
            return redirect("solicitudes:detalle", pk=solicitud.pk)

    # Línea de progreso
    iconos = {
        "BORRADOR": "✏", "EMITIDA": "📤", "RECHAZADA": "✗", "EN_COTIZACION": "$",
        "OC_GENERADA": "🧾", "RECEPCION_PARCIAL": "◧", "RECIBIDA": "📦",
    }
    if solicitud.estado == E.RECHAZADA:
        pasos = [E.BORRADOR, E.EMITIDA, E.RECHAZADA]
    elif solicitud.estado == E.RECEPCION_PARCIAL:
        pasos = [E.BORRADOR, E.EMITIDA, E.EN_COTIZACION, E.OC_GENERADA, E.RECEPCION_PARCIAL]
    else:
        pasos = [E.BORRADOR, E.EMITIDA, E.EN_COTIZACION, E.OC_GENERADA, E.RECIBIDA]
    idx = pasos.index(solicitud.estado) if solicitud.estado in pasos else len(pasos)
    estados_progreso = [
        (E(e).label, iconos[e], e == solicitud.estado, pasos.index(e) < idx) for e in pasos
    ]

    return render(request, "solicitudes/solicitud_detail.html", {
        "solicitud": solicitud,
        "form": detalle_form,
        "cab_form": cab_form,
        "adjunto_form": adjunto_form,
        "estados_progreso": estados_progreso,
        "max_adjuntos": SolicitudAdjunto.MAX_POR_SOLICITUD,
        "puede_gestionar": responsable,
        # RF-26/RF-33: Bodega no ve precios
        "oculta_precios": request.user.rol == "BODEGUERO",
        "puede_cotizar": request.user.rol in (EA, "ADMIN") and solicitud.puede_cotizarse,
        "puede_rechazar": request.user.rol in (EA, "ADMIN") and solicitud.rechazable,
        # RF-36: OC generadas a partir de esta SM, cada una con su recepción
        "ordenes_compra": solicitud.ordenes_compra.select_related("proveedor").all(),
    })


@rol_requerido("JEFE_PROYECTO")
def solicitud_editar(request, pk):
    """Editar los datos generales del borrador."""
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    exigir_responsable(request.user, solicitud)
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


@rol_requerido("JEFE_PROYECTO")
@require_POST
def detalle_eliminar(request, pk):
    """Quitar una línea mientras la solicitud está en borrador."""
    detalle = get_object_or_404(SolicitudDetalle, pk=pk)
    solicitud = detalle.solicitud
    exigir_responsable(request.user, solicitud)
    if solicitud.editable:
        detalle.delete()
        messages.success(request, "Material quitado de la solicitud.")
    else:
        messages.error(request, "No se puede modificar una solicitud que ya fue emitida.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)


@rol_requerido("JEFE_PROYECTO")
@require_POST
def adjunto_eliminar(request, pk):
    """CU-14 Excepción 3: quitar un adjunto para poder subir otro."""
    adjunto = get_object_or_404(SolicitudAdjunto, pk=pk)
    solicitud = adjunto.solicitud
    exigir_responsable(request.user, solicitud)
    adjunto.archivo.delete(save=False)
    adjunto.delete()
    messages.success(request, "Archivo eliminado.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)


# ---------------------------------------------------------------------------
# Rechazo (Adquisiciones) y corrección (Jefe de Proyecto)
# ---------------------------------------------------------------------------
@rol_requerido(EA)
@require_POST
def solicitud_rechazar(request, pk):
    """
    Adquisiciones rechaza una SM emitida que no puede atender (por ejemplo,
    materiales mal especificados). El motivo es obligatorio y viaja en la
    notificación al Jefe de Proyecto (RF-15: "Rechazada" con descripción).
    """
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    motivo = (request.POST.get("motivo") or "").strip()
    if not solicitud.rechazable:
        messages.error(request, "Solo se rechaza una solicitud emitida que aún no tiene orden de compra.")
    elif not motivo:
        messages.error(request, "Indica el motivo del rechazo.")
    else:
        solicitud.motivo_rechazo = motivo
        solicitud.cambiar_estado(E.RECHAZADA, f"Motivo: {motivo}", campos_extra=["motivo_rechazo"])
        registrar(request.user, RegistroAuditoria.Accion.SM_RECHAZADA,
                  f"Rechazó la solicitud de {solicitud.proyecto.nombre}: {motivo}",
                  solicitud.correlativo)
        messages.warning(request, f"Solicitud {solicitud.correlativo} rechazada. Se notificó al Jefe de Proyecto.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)


@rol_requerido("JEFE_PROYECTO")
@require_POST
def solicitud_devolver_borrador(request, pk):
    """
    Una SM rechazada vuelve a borrador para corregirla y emitirla de nuevo,
    conservando su número, líneas y adjuntos (no hay que rehacerla entera).
    """
    solicitud = get_object_or_404(SolicitudMaterial, pk=pk)
    exigir_responsable(request.user, solicitud)
    if solicitud.estado != E.RECHAZADA:
        messages.error(request, "Sólo se corrige una solicitud rechazada.")
    else:
        solicitud.estado = E.BORRADOR
        solicitud.motivo_rechazo = ""
        solicitud.save(update_fields=["estado", "motivo_rechazo"])
        messages.success(
            request,
            f"Solicitud {solicitud.numero} devuelta a borrador. Corrige lo que "
            f"corresponda y vuelve a emitirla.")
    return redirect("solicitudes:detalle", pk=solicitud.pk)
