"""
Vistas del módulo de usuarios.
CU-50 Autenticando usuario (login lo maneja config/urls con auth_views)
CU-51 Gestionando cuentas de usuario
CU-52 Gestionando roles
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from auditoria.models import RegistroAuditoria, registrar
from .models import Usuario, ParametrosSistema, SolicitudCambioPerfil
from .forms import (
    UsuarioCreateForm, UsuarioUpdateForm, RegistroSolicitudForm,
    RevisionSolicitudForm, ParametrosSistemaForm,
    MiPerfilForm, SolicitudCambioPerfilForm,
)
from .correos import enviar_enlace_activacion
from .permisos import RolRequeridoMixin, rol_requerido


def registro_solicitud(request):
    """Registro público: crea cuenta inactiva pendiente de aprobación del admin."""
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegistroSolicitudForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.estado = False
            user.pendiente_aprobacion = True
            user.is_active = False
            user.save()
            messages.success(request, "Solicitud enviada. El administrador revisará tu acceso en breve.")
            return redirect("login")
    else:
        form = RegistroSolicitudForm()
    return render(request, "registration/registro.html", {"form": form})


@rol_requerido("ADMIN")
@require_POST
def aprobar_registro(request, pk):
    """Aprueba la solicitud de registro de un usuario pendiente."""
    usuario = get_object_or_404(Usuario, pk=pk, pendiente_aprobacion=True)
    usuario.estado = True
    usuario.pendiente_aprobacion = False
    usuario.save()
    # CU-53: la gestión de cuentas es una acción auditable
    registrar(request.user, RegistroAuditoria.Accion.USUARIO_APROBADO,
              f"Aprobó la cuenta de {usuario.username} como {usuario.get_rol_display()}.",
              usuario.username)
    messages.success(request, f"Cuenta de {usuario.username} aprobada.")
    return redirect("usuarios:lista")


@rol_requerido("ADMIN")
@require_POST
def rechazar_registro(request, pk):
    """Rechaza y elimina la solicitud de registro."""
    usuario = get_object_or_404(Usuario, pk=pk, pendiente_aprobacion=True)
    nombre = usuario.username
    usuario.delete()
    registrar(request.user, RegistroAuditoria.Accion.USUARIO_RECHAZADO,
              f"Rechazó y eliminó la solicitud de acceso de {nombre}.", nombre)
    messages.warning(request, f"Solicitud de {nombre} rechazada y eliminada.")
    return redirect("usuarios:lista")


@rol_requerido("ADMIN")
def revisar_solicitud(request, pk):
    """
    CU-52: ficha de una solicitud de acceso pendiente.

    Muestra todo lo que declaró el solicitante y permite corregirlo antes de
    decidir: el rol mal elegido, un correo con un typo, el nombre incompleto.
    Desde la misma pantalla se guarda, se aprueba (guardando los cambios) o
    se rechaza.
    """
    usuario = get_object_or_404(Usuario, pk=pk, pendiente_aprobacion=True)
    accion = request.POST.get("accion", "")

    if request.method == "POST" and accion == "rechazar":
        nombre = usuario.username
        usuario.delete()
        registrar(request.user, RegistroAuditoria.Accion.USUARIO_RECHAZADO,
                  f"Rechazó y eliminó la solicitud de acceso de {nombre}.", nombre)
        messages.warning(request, f"Solicitud de {nombre} rechazada y eliminada.")
        return redirect("usuarios:lista")

    if request.method == "POST":
        form = RevisionSolicitudForm(request.POST, instance=usuario)
        if form.is_valid():
            rol_original = Usuario.objects.get(pk=usuario.pk).get_rol_display()
            rol_cambiado = form.rol_cambiado
            usuario = form.save(commit=False)

            if accion == "aprobar":
                usuario.estado = True
                usuario.pendiente_aprobacion = False
                usuario.save()
                registrar(
                    request.user, RegistroAuditoria.Accion.USUARIO_APROBADO,
                    f"Aprobó la cuenta de {usuario.username} como "
                    f"{usuario.get_rol_display()}"
                    + (f" (había solicitado {rol_original})." if rol_cambiado else "."),
                    usuario.username)
                if rol_cambiado:
                    messages.success(
                        request,
                        f"Cuenta de {usuario.username} aprobada como "
                        f"{usuario.get_rol_display()} (había solicitado {rol_original}).",
                    )
                else:
                    messages.success(request, f"Cuenta de {usuario.username} aprobada.")
                return redirect("usuarios:lista")

            usuario.save()
            messages.success(
                request,
                f"Cambios guardados. La solicitud de {usuario.username} sigue pendiente.",
            )
            return redirect("usuarios:revisar", pk=usuario.pk)
    else:
        form = RevisionSolicitudForm(instance=usuario)

    return render(request, "usuarios/usuario_revisar.html",
                  {"form": form, "solicitante": usuario})


@login_required
def home(request):
    """
    Dashboard de inicio (CU-50).

    Cada rol ve lo que le toca hacer hoy. Antes todos veían las mismas cuatro
    métricas, que sólo aplicaban a Administración, Adquisiciones y Jefatura:
    Bodega y Contabilidad entraban a una fila vacía y tenían que adivinar por
    dónde empezar. Los conteos además se calculan sólo para el rol que los va a
    ver, en vez de consultar nueve tablas para todos.
    """
    from django.db.models import F
    from proveedores.models import Proveedor
    from proyectos.models import Proyecto
    from solicitudes.models import SolicitudMaterial
    from inventario.models import Material, PrestamoHerramienta
    from adquisiciones.models import OrdenCompra
    from facturacion.models import Factura

    rol = request.user.rol
    es_admin = rol == "ADMIN"
    stats = {}

    if es_admin:
        stats["usuarios"] = Usuario.objects.count()
        stats["pendientes"] = Usuario.objects.filter(pendiente_aprobacion=True).count()

    if rol in ("ENCARGADO_ADQUISICIONES",) or es_admin:
        stats["proveedores"] = Proveedor.objects.count()
        stats["cotizar"] = SolicitudMaterial.objects.filter(
            estado__in=[SolicitudMaterial.Estado.APROBADA,
                        SolicitudMaterial.Estado.EN_COTIZACION]).count()
        stats["oc_borrador"] = OrdenCompra.objects.filter(
            estado=OrdenCompra.Estado.BORRADOR).count()

    if rol in ("JEFE_PROYECTO", "ENCARGADO_ADQUISICIONES", "CONTABILIDAD") or es_admin:
        proyectos = Proyecto.objects.exclude(estado="FINALIZADO")
        if rol == "JEFE_PROYECTO":
            proyectos = proyectos.filter(jefe_proyecto=request.user)
        stats["proyectos"] = proyectos.count()

    if rol in ("JEFE_PROYECTO", "ENCARGADO_ADQUISICIONES") or es_admin:
        stats["solicitudes_pendientes"] = SolicitudMaterial.objects.filter(
            estado=SolicitudMaterial.Estado.ENVIADA).count()

    if rol in ("BODEGUERO", "ENCARGADO_ADQUISICIONES") or es_admin:
        stats["materiales_criticos"] = Material.objects.filter(
            stock_minimo__gt=0, stock_actual__lte=F("stock_minimo")).count()

    if rol == "BODEGUERO" or es_admin:
        stats["prestamos_activos"] = PrestamoHerramienta.objects.filter(
            estado=PrestamoHerramienta.Estado.PRESTADA).count()
        stats["por_recibir"] = OrdenCompra.objects.filter(
            estado__in=[OrdenCompra.Estado.ENVIADA,
                        OrdenCompra.Estado.RECEPCION_PARCIAL]).count()

    if rol == "CONTABILIDAD" or es_admin:
        stats["facturas_bloqueadas"] = Factura.objects.filter(
            estado=Factura.Estado.BLOQUEADA).count()
        stats["facturas_total"] = Factura.objects.count()
        stats["por_facturar"] = OrdenCompra.objects.filter(
            estado__in=[OrdenCompra.Estado.RECIBIDA,
                        OrdenCompra.Estado.RECEPCION_PARCIAL],
            facturada=False).count()

    return render(request, "home.html", {
        "stats": stats,
        "pendientes_count": stats.get("pendientes", 0) if es_admin else 0,
    })


class UsuarioListView(RolRequeridoMixin, ListView):
    """CU-51: Listar cuentas de usuario. Solo ADMIN.

    El listado se secciona por rol (puede haber varios usuarios con el mismo
    rol) y admite búsqueda por texto y filtros por rol y estado.
    """
    roles_permitidos = ["ADMIN"]
    model = Usuario
    template_name = "usuarios/usuario_list.html"
    context_object_name = "usuarios"

    def _filtros(self):
        return {
            "q": self.request.GET.get("q", "").strip(),
            "rol": self.request.GET.get("rol", "").strip(),
            "estado": self.request.GET.get("estado", "").strip(),
        }

    def get_queryset(self):
        qs = Usuario.objects.filter(pendiente_aprobacion=False)
        f = self._filtros()
        if f["q"]:
            qs = qs.filter(
                Q(username__icontains=f["q"])
                | Q(first_name__icontains=f["q"])
                | Q(last_name__icontains=f["q"])
                | Q(email__icontains=f["q"])
                | Q(telefono__icontains=f["q"])
            )
        if f["rol"]:
            qs = qs.filter(rol=f["rol"])
        if f["estado"] == "activo":
            qs = qs.filter(estado=True)
        elif f["estado"] == "inactivo":
            qs = qs.filter(estado=False)
        return qs.order_by("rol", "username")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = self._filtros()
        usuarios = list(ctx["usuarios"])

        # Agrupar el resultado filtrado por rol, respetando el orden declarado
        # en Usuario.Rol.choices. Cada sección lleva su propio conteo.
        grupos = []
        for valor, etiqueta in Usuario.Rol.choices:
            miembros = [u for u in usuarios if u.rol == valor]
            if miembros:
                grupos.append({"valor": valor, "etiqueta": etiqueta, "usuarios": miembros})
        ctx["grupos"] = grupos

        # Panel de resumen: total por rol sobre el universo completo de cuentas
        base = Usuario.objects.filter(pendiente_aprobacion=False)
        ctx["resumen_roles"] = [
            {"valor": valor, "etiqueta": etiqueta, "total": base.filter(rol=valor).count()}
            for valor, etiqueta in Usuario.Rol.choices
        ]
        ctx["total_general"] = base.count()
        ctx["total_filtrado"] = len(usuarios)
        ctx["total_activos"] = base.filter(estado=True).count()
        ctx["total_inactivos"] = base.filter(estado=False).count()

        ctx["roles"] = Usuario.Rol.choices
        ctx["f_q"] = f["q"]
        ctx["f_rol"] = f["rol"]
        ctx["f_estado"] = f["estado"]
        ctx["hay_filtros"] = bool(f["q"] or f["rol"] or f["estado"])
        ctx["pendientes"] = Usuario.objects.filter(pendiente_aprobacion=True)
        ctx["cambios_pendientes"] = (
            SolicitudCambioPerfil.objects
            .filter(estado=SolicitudCambioPerfil.Estado.PENDIENTE)
            .select_related("usuario")
        )
        return ctx


class UsuarioCreateView(RolRequeridoMixin, SuccessMessageMixin, CreateView):
    """CU-51: Crear cuenta de usuario."""
    roles_permitidos = ["ADMIN"]
    model = Usuario
    form_class = UsuarioCreateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:lista")
    success_message = "Cuenta de usuario creada correctamente."

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        registrar(self.request.user, RegistroAuditoria.Accion.USUARIO_CREADO,
                  f"Creó la cuenta de {self.object.username} "
                  f"({self.object.get_rol_display()}).", self.object.username)
        # CU-52: el sistema manda el enlace temporal para definir la contraseña
        if enviar_enlace_activacion(self.request, self.object, creado_por=self.request.user):
            messages.info(
                self.request,
                f"Se envió a {self.object.email} el enlace para definir su contraseña.")
        else:
            messages.warning(
                self.request,
                f"La cuenta quedó creada, pero no se pudo enviar el enlace a "
                f"{self.object.email or 'su correo'}. Puedes reenviarlo desde la ficha "
                f"de la cuenta.")
        return respuesta


class UsuarioUpdateView(RolRequeridoMixin, SuccessMessageMixin, UpdateView):
    """CU-51 / CU-52: Editar cuenta y/o cambiar rol del usuario."""
    roles_permitidos = ["ADMIN"]
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:lista")
    success_message = "Cuenta de usuario actualizada correctamente."

    def form_valid(self, form):
        cambios = ", ".join(form.changed_data) or "sin cambios"
        respuesta = super().form_valid(form)
        registrar(self.request.user, RegistroAuditoria.Accion.USUARIO_MODIFICADO,
                  f"Modificó la cuenta de {self.object.username}: {cambios}.",
                  self.object.username)
        return respuesta


class UsuarioDetailView(RolRequeridoMixin, DetailView):
    roles_permitidos = ["ADMIN"]
    model = Usuario
    template_name = "usuarios/usuario_detail.html"
    context_object_name = "usuario_obj"


@rol_requerido("ADMIN")
@require_POST
def usuario_cambiar_estado(request, pk):
    """CU-51: Activar/Inactivar una cuenta (en lugar de eliminarla)."""
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.estado = not usuario.estado
    usuario.save()
    estado_txt = "activada" if usuario.estado else "inactivada"
    registrar(request.user, RegistroAuditoria.Accion.USUARIO_MODIFICADO,
              f"Cuenta de {usuario.username} {estado_txt}.", usuario.username)
    messages.success(request, f"Cuenta {usuario.username} {estado_txt}.")
    return redirect("usuarios:lista")


# --------------------------------------------------------------------------
# CU-60 (RF-57) — Configurando parámetros generales del sistema
# --------------------------------------------------------------------------
@rol_requerido("ADMIN")
def parametros_sistema(request):
    """
    Los cuatro parámetros que el RF-57 exige poder configurar, en una pantalla.

    El catálogo de tipos de documento es el cuarto parámetro, pero se administra
    desde su propia pantalla (ya existe, CU-54); acá se muestra el resumen y el
    enlace, en vez de duplicar el CRUD.
    """
    from proyectos.models import TipoDocumento

    parametros = ParametrosSistema.actuales()
    if request.method == "POST":
        form = ParametrosSistemaForm(request.POST, instance=parametros)
        if form.is_valid():
            guardado = form.save(commit=False)
            guardado.actualizado_por = request.user
            guardado.save()
            registrar(request.user, RegistroAuditoria.Accion.PARAMETROS_MODIFICADOS,
                      "Actualizó los parámetros generales: "
                      + ", ".join(form.changed_data) if form.changed_data
                      else "Guardó los parámetros generales sin cambios.",
                      "Parámetros")
            messages.success(
                request,
                "Parámetros actualizados. Se aplican de inmediato a las validaciones "
                "de factura, a las alertas de stock y a las cargas de archivo.")
            return redirect("usuarios:parametros")
        messages.error(request, "Revisa los valores marcados: alguno está fuera de rango.")
    else:
        form = ParametrosSistemaForm(instance=parametros)

    return render(request, "usuarios/parametros.html", {
        "form": form,
        "parametros": parametros,
        "tipos_documento": TipoDocumento.objects.all(),
        "tipos_activos": TipoDocumento.objects.filter(activo=True).count(),
    })


@rol_requerido("ADMIN")
@require_POST
def reenviar_activacion(request, pk):
    """
    Vuelve a mandar el enlace de activación.

    Hace falta porque el correo se cae (SMTP mal configurado, buzón lleno, un
    typo en la dirección que se corrigió después) y sin esto la única salida
    era borrar la cuenta y crearla de nuevo, perdiendo su historial.
    """
    usuario = get_object_or_404(Usuario, pk=pk)
    if enviar_enlace_activacion(request, usuario, creado_por=request.user):
        messages.success(request, f"Enlace reenviado a {usuario.email}.")
    else:
        messages.error(
            request,
            f"No se pudo enviar el correo a {usuario.email or 'la cuenta'}. "
            f"Revisa la configuración de correo del servidor.")
    return redirect("usuarios:detalle", pk=usuario.pk)


# ==========================================================================
#  Mi perfil
# ==========================================================================

@login_required
def mi_perfil(request):
    """
    La cuenta vista por su propio dueño.

    Acá cada uno corrige lo suyo —cómo se escribe su nombre, su teléfono, su
    foto— sin tener que pedírselo a nadie. Lo que toca el acceso (correo,
    nombre de usuario y rol) se pide con el formulario de más abajo y lo
    resuelve un administrador.
    """
    form = MiPerfilForm(instance=request.user)
    form_cambio = SolicitudCambioPerfilForm(usuario=request.user)

    if request.method == "POST":
        if request.POST.get("accion") == "pedir_cambio":
            form_cambio = SolicitudCambioPerfilForm(request.POST, usuario=request.user)
            if form_cambio.is_valid():
                solicitud = form_cambio.save(commit=False)
                solicitud.usuario = request.user
                if solicitud.campo == SolicitudCambioPerfil.Campo.ROL:
                    solicitud.valor_solicitado = solicitud.valor_solicitado.upper()
                solicitud.valor_actual = str(
                    getattr(request.user, solicitud.campo, "") or ""
                )[:150]
                # Si ya había un pedido pendiente del mismo dato, este lo
                # reemplaza: al administrador le sirve el último, no los dos.
                SolicitudCambioPerfil.objects.filter(
                    usuario=request.user, campo=solicitud.campo,
                    estado=SolicitudCambioPerfil.Estado.PENDIENTE,
                ).delete()
                solicitud.save()
                registrar(request.user, RegistroAuditoria.Accion.CAMBIO_PERFIL_PEDIDO,
                          f"{request.user.username} pide cambiar su "
                          f"{solicitud.get_campo_display().lower()} a «{solicitud.valor_solicitado}»",
                          referencia=str(solicitud.pk))
                messages.success(
                    request,
                    "Pedido enviado. Un administrador lo va a revisar; mientras "
                    "tanto tus datos quedan como están.",
                )
                return redirect("usuarios:mi_perfil")
        else:
            form = MiPerfilForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Perfil actualizado.")
                return redirect("usuarios:mi_perfil")

    return render(request, "usuarios/mi_perfil.html", {
        "form": form,
        "form_cambio": form_cambio,
        "solicitudes": request.user.cambios_solicitados.all()[:10],
        "pendientes_propias": request.user.cambios_solicitados.filter(
            estado=SolicitudCambioPerfil.Estado.PENDIENTE),
    })


@login_required
@require_POST
def cancelar_cambio_perfil(request, pk):
    """El propio solicitante se arrepiente antes de que lo resuelvan."""
    solicitud = get_object_or_404(
        SolicitudCambioPerfil, pk=pk, usuario=request.user,
        estado=SolicitudCambioPerfil.Estado.PENDIENTE,
    )
    solicitud.delete()
    messages.info(request, "Pedido cancelado.")
    return redirect("usuarios:mi_perfil")


@rol_requerido("ADMIN")
@require_POST
def resolver_cambio_perfil(request, pk):
    """El administrador aprueba o rechaza un pedido de cambio de datos."""
    solicitud = get_object_or_404(SolicitudCambioPerfil, pk=pk)
    if not solicitud.pendiente:
        messages.warning(request, "Ese pedido ya estaba resuelto.")
        return redirect("usuarios:lista")

    aprobar = request.POST.get("decision") == "aprobar"
    comentario = (request.POST.get("comentario") or "").strip()[:250]
    usuario = solicitud.usuario

    if aprobar:
        # Revalidar contra la base: entre que pidió y que el administrador
        # aprueba, otro pudo tomarse ese correo o ese nombre de usuario.
        valor = solicitud.valor_solicitado
        campo = solicitud.campo
        choque = None
        if campo == SolicitudCambioPerfil.Campo.EMAIL:
            choque = Usuario.objects.filter(email__iexact=valor).exclude(pk=usuario.pk).exists()
        elif campo == SolicitudCambioPerfil.Campo.USERNAME:
            choque = Usuario.objects.filter(username__iexact=valor).exclude(pk=usuario.pk).exists()
        elif campo == SolicitudCambioPerfil.Campo.ROL:
            if valor not in dict(Usuario.Rol.choices):
                messages.error(request, f"«{valor}» no es un rol válido.")
                return redirect("usuarios:lista")

        if choque:
            messages.error(
                request,
                f"No se pudo aprobar: «{valor}» ya está ocupado por otra cuenta. "
                "El pedido queda pendiente.",
            )
            return redirect("usuarios:lista")

        setattr(usuario, campo, valor)
        usuario.save(update_fields=[campo])
        solicitud.estado = SolicitudCambioPerfil.Estado.APROBADA
        messages.success(
            request,
            f"{usuario.username}: {solicitud.get_campo_display().lower()} actualizado a «{valor}».",
        )
    else:
        solicitud.estado = SolicitudCambioPerfil.Estado.RECHAZADA
        messages.info(request, f"Pedido de {usuario.username} rechazado.")

    solicitud.comentario = comentario
    solicitud.resuelta = timezone.now()
    solicitud.resuelta_por = request.user
    solicitud.save()
    registrar(request.user, RegistroAuditoria.Accion.CAMBIO_PERFIL_RESUELTO,
              f"{solicitud.get_estado_display()}: {usuario.username} pedía cambiar su "
              f"{solicitud.get_campo_display().lower()} a «{solicitud.valor_solicitado}»",
              referencia=str(solicitud.pk))
    return redirect("usuarios:lista")


@rol_requerido("ADMIN")
@require_POST
def usuario_eliminar(request, pk):
    """
    Borrado definitivo de una cuenta.

    Sólo procede si la cuenta no dejó nada escrito. Las relaciones hacia
    Usuario son PROTECT porque una solicitud o una orden de compra tienen que
    seguir diciendo quién las hizo; borrar a la persona dejaría documentos
    huérfanos o, peor, arrastraría el historial con ella. Cuando hay historial
    se explica qué la retiene y se ofrece inactivarla, que es lo que
    corresponde: la persona deja de entrar, el registro queda.
    """
    usuario = get_object_or_404(Usuario, pk=pk)

    if usuario.pk == request.user.pk:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
        return redirect("usuarios:lista")

    if usuario.rol == Usuario.Rol.ADMIN:
        otros_admin = Usuario.objects.filter(
            rol=Usuario.Rol.ADMIN, estado=True
        ).exclude(pk=usuario.pk).count()
        if not otros_admin:
            messages.error(
                request,
                "Es el último administrador activo. Si lo eliminas, nadie puede "
                "volver a administrar el sistema. Crea otro administrador primero.",
            )
            return redirect("usuarios:lista")

    retienen = usuario.registros_que_impiden_borrarlo()
    if retienen:
        detalle = ", ".join(f"{total} {etiqueta}" for etiqueta, total in retienen)
        messages.error(
            request,
            f"No se puede eliminar a {usuario.username}: tiene {detalle} a su nombre. "
            "Esos registros tienen que seguir diciendo quién los hizo. "
            "Inactiva la cuenta: la persona deja de entrar y el historial queda intacto.",
        )
        return redirect("usuarios:lista")

    nombre = usuario.username
    registrar(request.user, RegistroAuditoria.Accion.USUARIO_ELIMINADO,
              f"Cuenta «{nombre}» ({usuario.get_rol_display()}) eliminada definitivamente",
              referencia=str(usuario.pk))
    usuario.delete()
    messages.success(request, f"Cuenta «{nombre}» eliminada definitivamente.")
    return redirect("usuarios:lista")
