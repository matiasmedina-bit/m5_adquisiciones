"""
Vistas de Proveedores.
CU-01 Registrando proveedor      CU-02 Validando RUT (en el form)
CU-03 Verificando duplicado      CU-04 Editando proveedor
CU-05 Inactivando proveedor
"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from usuarios.validators import limpiar_rut
from .models import Proveedor, ProveedorMaterial
from .forms import ProveedorForm, ProveedorMaterialForm

ROLES_GESTION = ["ENCARGADO_ADQUISICIONES"]


class ProveedorListView(RolRequeridoMixin, ListView):
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    template_name = "proveedores/proveedor_list.html"
    context_object_name = "proveedores"

    def _filtros(self):
        return {
            "q": self.request.GET.get("q", "").strip(),
            "cond": self.request.GET.get("cond", "").strip(),
            "estado": self.request.GET.get("estado", "").strip(),
        }

    def get_queryset(self):
        qs = Proveedor.objects.all()
        f = self._filtros()
        if f["q"]:
            cond = Q(nombre__icontains=f["q"]) | Q(correo__icontains=f["q"]) | Q(telefono__icontains=f["q"])
            rut_limpio = limpiar_rut(f["q"])
            if rut_limpio:
                cond |= Q(rut__icontains=rut_limpio)
            qs = qs.filter(cond)
        if f["cond"]:
            qs = qs.filter(condicion_pago=f["cond"])
        if f["estado"] == "activo":
            qs = qs.filter(estado=True)
        elif f["estado"] == "inactivo":
            qs = qs.filter(estado=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = self._filtros()
        base = Proveedor.objects.all()
        ctx["metricas"] = {
            "total": base.count(),
            "activos": base.filter(estado=True).count(),
            "inactivos": base.filter(estado=False).count(),
        }
        ctx["total_filtrado"] = ctx["proveedores"].count() if hasattr(ctx["proveedores"], "count") else len(ctx["proveedores"])
        ctx["condiciones"] = Proveedor.CondicionPago.choices
        ctx["f_q"] = f["q"]
        ctx["f_cond"] = f["cond"]
        ctx["f_estado"] = f["estado"]
        ctx["hay_filtros"] = bool(f["q"] or f["cond"] or f["estado"])
        return ctx


class ProveedorCreateView(RolRequeridoMixin, SuccessMessageMixin, CreateView):
    """CU-01 Registrando proveedor."""
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedores/proveedor_form.html"
    success_url = reverse_lazy("proveedores:lista")
    success_message = "Proveedor registrado correctamente."


class ProveedorUpdateView(RolRequeridoMixin, SuccessMessageMixin, UpdateView):
    """CU-04 Editando proveedor."""
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedores/proveedor_form.html"
    success_url = reverse_lazy("proveedores:lista")
    success_message = "Proveedor actualizado correctamente."


class ProveedorDetailView(RolRequeridoMixin, DetailView):
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    template_name = "proveedores/proveedor_detail.html"
    context_object_name = "proveedor"


@rol_requerido("ENCARGADO_ADQUISICIONES")
def proveedor_inactivar(request, pk):
    """CU-05 Inactivando proveedor (no se elimina, se desactiva)."""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.estado = not proveedor.estado
    proveedor.save()
    estado_txt = "activado" if proveedor.estado else "inactivado"
    messages.success(request, f"Proveedor {proveedor.nombre} {estado_txt}.")
    return redirect("proveedores:lista")


# --------------------------------------------------------------------------
# RF-05 / RF-06 / RF-07 — Listado de materiales que suministra el proveedor
# --------------------------------------------------------------------------
@rol_requerido("ENCARGADO_ADQUISICIONES")
def proveedor_material_agregar(request, proveedor_pk):
    """RF-05: agregar un material al listado del proveedor."""
    proveedor = get_object_or_404(Proveedor, pk=proveedor_pk)
    if request.method == "POST":
        form = ProveedorMaterialForm(request.POST, proveedor=proveedor)
        if form.is_valid():
            material = form.save(commit=False)
            material.proveedor = proveedor
            material.save()
            messages.success(request, "Material agregado al listado del proveedor.")
            return redirect("proveedores:detalle", pk=proveedor.pk)
    else:
        form = ProveedorMaterialForm(proveedor=proveedor)
    return render(request, "proveedores/proveedor_material_form.html",
                  {"form": form, "proveedor": proveedor})


@rol_requerido("ENCARGADO_ADQUISICIONES")
def proveedor_material_editar(request, pk):
    """RF-07: editar código, unidad de medida o descripción de un material."""
    material = get_object_or_404(ProveedorMaterial, pk=pk)
    if request.method == "POST":
        form = ProveedorMaterialForm(request.POST, instance=material, proveedor=material.proveedor)
        if form.is_valid():
            form.save()  # 'modificado' se actualiza solo (auto_now)
            messages.success(request, "Material actualizado.")
            return redirect("proveedores:detalle", pk=material.proveedor.pk)
    else:
        form = ProveedorMaterialForm(instance=material, proveedor=material.proveedor)
    return render(request, "proveedores/proveedor_material_form.html",
                  {"form": form, "proveedor": material.proveedor, "material": material})


@rol_requerido("ENCARGADO_ADQUISICIONES")
def proveedor_material_disponibilidad(request, pk):
    """RF-06: marcar / reactivar un material como (no) disponible, sin borrarlo."""
    material = get_object_or_404(ProveedorMaterial, pk=pk)
    material.disponible = not material.disponible
    material.save()
    estado_txt = "disponible" if material.disponible else "no disponible"
    messages.success(request, f"Material «{material.descripcion}» marcado como {estado_txt}.")
    return redirect("proveedores:detalle", pk=material.proveedor.pk)
