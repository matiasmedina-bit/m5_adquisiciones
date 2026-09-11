"""
Vistas de Proyectos e Itemizado.
CU-06 Registrando proyecto    CU-07 Editando proyecto
CU-08 Consultando proyecto    CU-09 Agregando itemizado al proyecto
CU-10 Editando itemizado
"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from .models import Proyecto, Itemizado
from .forms import ProyectoForm, ItemizadoForm

ROLES_GESTION = ["JEFE_PROYECTO"]


class ProyectoListView(RolRequeridoMixin, ListView):
    roles_permitidos = ROLES_GESTION + ["ENCARGADO_ADQUISICIONES"]
    model = Proyecto
    template_name = "proyectos/proyecto_list.html"
    context_object_name = "proyectos"


class ProyectoCreateView(RolRequeridoMixin, SuccessMessageMixin, CreateView):
    """CU-06 Registrando proyecto."""
    roles_permitidos = ROLES_GESTION
    model = Proyecto
    form_class = ProyectoForm
    template_name = "proyectos/proyecto_form.html"
    success_url = reverse_lazy("proyectos:lista")
    success_message = "Proyecto registrado correctamente."


class ProyectoUpdateView(RolRequeridoMixin, SuccessMessageMixin, UpdateView):
    """CU-07 Editando proyecto."""
    roles_permitidos = ROLES_GESTION
    model = Proyecto
    form_class = ProyectoForm
    template_name = "proyectos/proyecto_form.html"
    success_url = reverse_lazy("proyectos:lista")
    success_message = "Proyecto actualizado correctamente."


class ProyectoDetailView(RolRequeridoMixin, DetailView):
    """CU-08 Consultando proyecto (con su itemizado)."""
    roles_permitidos = ROLES_GESTION + ["ENCARGADO_ADQUISICIONES"]
    model = Proyecto
    template_name = "proyectos/proyecto_detail.html"
    context_object_name = "proyecto"


@rol_requerido("JEFE_PROYECTO")
def itemizado_crear(request, proyecto_pk):
    """CU-09 Agregando itemizado (partida) a un proyecto."""
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)
    if request.method == "POST":
        form = ItemizadoForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.proyecto = proyecto
            item.save()
            messages.success(request, "Partida agregada al itemizado.")
            return redirect("proyectos:detalle", pk=proyecto.pk)
    else:
        form = ItemizadoForm()
    return render(request, "proyectos/itemizado_form.html", {"form": form, "proyecto": proyecto})


@rol_requerido("JEFE_PROYECTO")
def itemizado_editar(request, pk):
    """CU-10 Editando itemizado."""
    item = get_object_or_404(Itemizado, pk=pk)
    if request.method == "POST":
        form = ItemizadoForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Partida actualizada.")
            return redirect("proyectos:detalle", pk=item.proyecto.pk)
    else:
        form = ItemizadoForm(instance=item)
    return render(request, "proyectos/itemizado_form.html", {"form": form, "proyecto": item.proyecto})


# --------------------------------------------------------------------------
# Exportación de la ficha del proyecto a PDF (para compartir con el mandante)
# --------------------------------------------------------------------------
@rol_requerido("JEFE_PROYECTO", "ENCARGADO_ADQUISICIONES", "ADMIN")
def proyecto_pdf(request, pk):
    """Descarga la ficha completa del proyecto: datos, itemizado y solicitudes."""
    from django.http import HttpResponse
    from django.utils.text import slugify
    from .pdf import ReportlabNoInstalado, generar_pdf_proyecto

    proyecto = get_object_or_404(Proyecto, pk=pk)
    try:
        contenido = generar_pdf_proyecto(proyecto)
    except ReportlabNoInstalado as exc:
        messages.error(request, str(exc))
        return redirect("proyectos:detalle", pk=proyecto.pk)

    nombre = slugify(proyecto.nombre) or f"proyecto-{proyecto.pk}"
    respuesta = HttpResponse(contenido, content_type="application/pdf")
    respuesta["Content-Disposition"] = f'inline; filename="ficha-{nombre}.pdf"'
    return respuesta
