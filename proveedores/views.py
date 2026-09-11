"""
Vistas de Proveedores.
CU-01 Registrando proveedor      CU-02 Validando RUT (en el form)
CU-03 Verificando duplicado      CU-04 Editando proveedor
CU-05 Inactivando proveedor
"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from usuarios.validators import limpiar_rut
from .models import Proveedor, ProveedorMaterial
from .forms import ProveedorForm, ProveedorMaterialForm, CatalogoExcelForm
from .catalogo_excel import ErrorCatalogo, generar_plantilla, importar_catalogo

ROLES_GESTION = ["ENCARGADO_ADQUISICIONES"]


def _reportar_carga(request, resultado):
    """Traduce el resultado de la importación a mensajes para el usuario."""
    messages.success(request, resultado.resumen())
    for nro, motivo in resultado.omitidos[:5]:
        messages.warning(request, f"Fila {nro} omitida: {motivo}.")
    if len(resultado.omitidos) > 5:
        messages.warning(
            request,
            f"…y {len(resultado.omitidos) - 5} fila(s) más omitidas por el mismo tipo de problema.",
        )


class ProveedorListView(RolRequeridoMixin, ListView):
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    template_name = "proveedores/proveedor_list.html"
    context_object_name = "proveedores"

    def _filtros(self):
        return {
            "q": self.request.GET.get("q", "").strip(),
            "cat": self.request.GET.get("cat", "").strip(),
            "estado": self.request.GET.get("estado", "").strip(),
        }

    def get_queryset(self):
        # El conteo de materiales disponibles reemplaza a la condición de pago
        # como dato de cabecera: ahora lo que distingue a un proveedor es qué
        # ofrece, no cómo cobra (la condición se negocia por material).
        qs = Proveedor.objects.annotate(
            n_materiales=Count("materiales", filter=Q(materiales__disponible=True))
        )
        f = self._filtros()
        if f["q"]:
            cond = Q(nombre__icontains=f["q"]) | Q(correo__icontains=f["q"]) | Q(telefono__icontains=f["q"])
            rut_limpio = limpiar_rut(f["q"])
            if rut_limpio:
                cond |= Q(rut__icontains=rut_limpio)
            # También busca dentro del catálogo del proveedor
            cond |= Q(materiales__descripcion__icontains=f["q"])
            cond |= Q(materiales__codigo__icontains=f["q"])
            qs = qs.filter(cond).distinct()
        if f["cat"] == "con":
            qs = qs.filter(n_materiales__gt=0)
        elif f["cat"] == "sin":
            qs = qs.filter(n_materiales=0)
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
        ctx["f_q"] = f["q"]
        ctx["f_cat"] = f["cat"]
        ctx["f_estado"] = f["estado"]
        ctx["hay_filtros"] = bool(f["q"] or f["cat"] or f["estado"])
        return ctx


class _CargaCatalogoMixin:
    """
    Si el formulario trae una planilla, la importa después de guardar al
    proveedor. Un error en la planilla nunca pierde el registro del proveedor:
    se avisa y el usuario puede reintentar la carga desde la ficha.
    """

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        archivo = form.cleaned_data.get("catalogo")
        if archivo:
            try:
                resultado = importar_catalogo(self.object, archivo)
            except ErrorCatalogo as exc:
                messages.warning(
                    self.request,
                    f"El proveedor se guardó, pero el catálogo no se pudo cargar: {exc}",
                )
            else:
                _reportar_carga(self.request, resultado)
        return respuesta

    def get_success_url(self):
        # Ir a la ficha para ver el catálogo recién cargado
        return reverse("proveedores:detalle", args=[self.object.pk])


class ProveedorCreateView(_CargaCatalogoMixin, RolRequeridoMixin, SuccessMessageMixin, CreateView):
    """CU-01 Registrando proveedor (+ carga opcional del catálogo en Excel)."""
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedores/proveedor_form.html"
    success_message = "Proveedor registrado correctamente."


class ProveedorUpdateView(_CargaCatalogoMixin, RolRequeridoMixin, SuccessMessageMixin, UpdateView):
    """CU-04 Editando proveedor."""
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    form_class = ProveedorForm
    template_name = "proveedores/proveedor_form.html"
    success_message = "Proveedor actualizado correctamente."


class ProveedorDetailView(RolRequeridoMixin, DetailView):
    roles_permitidos = ROLES_GESTION
    model = Proveedor
    template_name = "proveedores/proveedor_detail.html"
    context_object_name = "proveedor"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_catalogo"] = CatalogoExcelForm()
        return ctx


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


# --------------------------------------------------------------------------
# Carga del catálogo desde Excel
# --------------------------------------------------------------------------
@rol_requerido("ENCARGADO_ADQUISICIONES")
def proveedor_catalogo_cargar(request, pk):
    """
    Carga (o actualiza) el catálogo de un proveedor ya registrado desde un
    .xlsx. Es la misma importación que ofrece el formulario de registro, pero
    disponible en cualquier momento: los proveedores mandan listas nuevas.
    """
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method != "POST":
        return redirect("proveedores:detalle", pk=proveedor.pk)

    form = CatalogoExcelForm(request.POST, request.FILES)
    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return redirect("proveedores:detalle", pk=proveedor.pk)

    try:
        resultado = importar_catalogo(
            proveedor,
            form.cleaned_data["archivo"],
            reemplazar=form.cleaned_data.get("reemplazar", False),
        )
    except ErrorCatalogo as exc:
        messages.error(request, str(exc))
    else:
        _reportar_carga(request, resultado)
    return redirect("proveedores:detalle", pk=proveedor.pk)


@rol_requerido("ENCARGADO_ADQUISICIONES")
def catalogo_plantilla(request):
    """Descarga la planilla de ejemplo para enviársela al proveedor."""
    try:
        contenido = generar_plantilla()
    except ImportError:
        messages.error(
            request,
            "Falta la librería 'openpyxl'. Ejecuta: pip install -r requirements.txt",
        )
        return redirect("proveedores:lista")
    respuesta = HttpResponse(
        contenido,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta["Content-Disposition"] = 'attachment; filename="plantilla_catalogo_proveedor.xlsx"'
    return respuesta
