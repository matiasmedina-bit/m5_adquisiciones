"""
CU-53 (RF-50) — Consulta de la bitácora de auditoría.

La bitácora sólo se lee. No hay pantalla para crear, editar ni borrar líneas:
el actor del caso de uso es el Sistema y una bitácora que se puede retocar no
sirve como evidencia. Acá sólo se consulta y se filtra.
"""
from datetime import datetime, time

from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView

from usuarios.models import Usuario
from usuarios.permisos import RolRequeridoMixin
from .models import RegistroAuditoria


class BitacoraListView(RolRequeridoMixin, ListView):
    """
    Listado filtrable de la bitácora. La revisan Administración y Contabilidad,
    que son quienes responden por la trazabilidad de lo que pasó en el sistema.
    """
    roles_permitidos = ["CONTABILIDAD"]
    model = RegistroAuditoria
    template_name = "auditoria/bitacora_list.html"
    context_object_name = "registros"
    paginate_by = 50

    def get_queryset(self):
        qs = RegistroAuditoria.objects.select_related("usuario")
        g = self.request.GET

        modulo = (g.get("modulo") or "").strip()
        if modulo:
            qs = qs.filter(modulo=modulo)

        accion = (g.get("accion") or "").strip()
        if accion:
            qs = qs.filter(accion=accion)

        usuario = (g.get("usuario") or "").strip()
        if usuario.isdigit():
            qs = qs.filter(usuario_id=int(usuario))

        texto = (g.get("q") or "").strip()
        if texto:
            qs = qs.filter(
                Q(descripcion__icontains=texto)
                | Q(referencia__icontains=texto)
                | Q(usuario_nombre__icontains=texto)
            )

        # Rango de fechas: 'desde' incluye el día completo, 'hasta' también.
        desde = self._fecha(g.get("desde"))
        if desde:
            qs = qs.filter(fecha__gte=desde)
        hasta = self._fecha(g.get("hasta"), fin_del_dia=True)
        if hasta:
            qs = qs.filter(fecha__lte=hasta)

        return qs

    @staticmethod
    def _fecha(valor, fin_del_dia=False):
        """Convierte 'AAAA-MM-DD' del input date a un datetime con zona."""
        if not valor:
            return None
        try:
            dia = datetime.strptime(valor.strip(), "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            return None
        momento = datetime.combine(dia, time.max if fin_del_dia else time.min)
        if timezone.is_naive(momento):
            momento = timezone.make_aware(momento, timezone.get_current_timezone())
        return momento

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modulos"] = RegistroAuditoria.Modulo.choices
        ctx["acciones"] = RegistroAuditoria.Accion.choices
        ctx["usuarios"] = Usuario.objects.filter(
            registros_auditoria__isnull=False).distinct().order_by("username")
        ctx["filtros"] = {
            "modulo": self.request.GET.get("modulo", ""),
            "accion": self.request.GET.get("accion", ""),
            "usuario": self.request.GET.get("usuario", ""),
            "desde": self.request.GET.get("desde", ""),
            "hasta": self.request.GET.get("hasta", ""),
            "q": self.request.GET.get("q", ""),
        }
        ctx["hay_filtros"] = any(ctx["filtros"].values())
        ctx["total_filtrado"] = self.get_queryset().count()
        return ctx
