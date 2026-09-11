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
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .models import Usuario
from .forms import (
    UsuarioCreateForm, UsuarioUpdateForm, RegistroSolicitudForm,
    RevisionSolicitudForm,
)
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
    messages.success(request, f"Cuenta de {usuario.username} aprobada.")
    return redirect("usuarios:lista")


@rol_requerido("ADMIN")
@require_POST
def rechazar_registro(request, pk):
    """Rechaza y elimina la solicitud de registro."""
    usuario = get_object_or_404(Usuario, pk=pk, pendiente_aprobacion=True)
    nombre = usuario.username
    usuario.delete()
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
    """Dashboard de inicio (CU-50)."""
    from django.db.models import F
    from proveedores.models import Proveedor
    from proyectos.models import Proyecto
    from solicitudes.models import SolicitudMaterial
    from inventario.models import Material
    from adquisiciones.models import OrdenCompra
    from facturacion.models import Factura
    stats = {
        "usuarios": Usuario.objects.count(),
        "pendientes": Usuario.objects.filter(pendiente_aprobacion=True).count(),
        "proveedores": Proveedor.objects.count(),
        "proyectos": Proyecto.objects.exclude(estado="FINALIZADO").count(),
        "solicitudes_pendientes": SolicitudMaterial.objects.filter(estado=SolicitudMaterial.Estado.ENVIADA).count(),
        # Incremento 2
        "cotizar": SolicitudMaterial.objects.filter(
            estado__in=[SolicitudMaterial.Estado.APROBADA, SolicitudMaterial.Estado.EN_COTIZACION]).count(),
        "oc_borrador": OrdenCompra.objects.filter(estado=OrdenCompra.Estado.BORRADOR).count(),
        "materiales_criticos": Material.objects.filter(
            stock_minimo__gt=0, stock_actual__lte=F("stock_minimo")).count(),
        "facturas_bloqueadas": Factura.objects.filter(estado=Factura.Estado.BLOQUEADA).count(),
    }
    pendientes_count = stats["pendientes"] if request.user.rol == "ADMIN" else 0
    return render(request, "home.html", {"stats": stats, "pendientes_count": pendientes_count})


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
        return ctx


class UsuarioCreateView(RolRequeridoMixin, SuccessMessageMixin, CreateView):
    """CU-51: Crear cuenta de usuario."""
    roles_permitidos = ["ADMIN"]
    model = Usuario
    form_class = UsuarioCreateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:lista")
    success_message = "Cuenta de usuario creada correctamente."


class UsuarioUpdateView(RolRequeridoMixin, SuccessMessageMixin, UpdateView):
    """CU-51 / CU-52: Editar cuenta y/o cambiar rol del usuario."""
    roles_permitidos = ["ADMIN"]
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:lista")
    success_message = "Cuenta de usuario actualizada correctamente."


class UsuarioDetailView(RolRequeridoMixin, DetailView):
    roles_permitidos = ["ADMIN"]
    model = Usuario
    template_name = "usuarios/usuario_detail.html"
    context_object_name = "usuario_obj"


@rol_requerido("ADMIN")
def usuario_cambiar_estado(request, pk):
    """CU-51: Activar/Inactivar una cuenta (en lugar de eliminarla)."""
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.estado = not usuario.estado
    usuario.save()
    estado_txt = "activada" if usuario.estado else "inactivada"
    messages.success(request, f"Cuenta {usuario.username} {estado_txt}.")
    return redirect("usuarios:lista")
