"""
Vistas de Proyectos e Itemizado.
CU-06 Registrando proyecto    CU-07 Editando proyecto
CU-08 Consultando proyecto    CU-09 Agregando itemizado al proyecto
CU-10 Editando itemizado
CU-54 Almacenando archivo y clasificándolo por tipo de documento (RF-51)
"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from usuarios.permisos import RolRequeridoMixin, rol_requerido
from .models import Proyecto, Itemizado, TipoDocumento, ArchivoProyecto
from .forms import (ProyectoForm, ItemizadoForm,
                    ArchivoProyectoForm, TipoDocumentoForm)

ROLES_GESTION = ["JEFE_PROYECTO"]
# CU-54: quiénes pueden almacenar documentos en la carpeta del proyecto.
# ADMIN entra siempre por la regla general de usuarios.permisos.
ROLES_ARCHIVO = ["JEFE_PROYECTO", "ENCARGADO_ADQUISICIONES", "CONTABILIDAD"]


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
    """CU-08 Consultando proyecto (con su itemizado y sus archivos)."""
    roles_permitidos = ROLES_GESTION + ["ENCARGADO_ADQUISICIONES", "CONTABILIDAD"]
    model = Proyecto
    template_name = "proyectos/proyecto_detail.html"
    context_object_name = "proyecto"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # CU-54: la carpeta de documentos del proyecto
        ctx["archivos"] = self.object.archivos.select_related("tipo", "subido_por")
        ctx["hay_catalogo"] = TipoDocumento.hay_catalogo()
        ctx["puede_subir"] = self.request.user.rol in ROLES_ARCHIVO or self.request.user.rol == "ADMIN"
        ctx["form_archivo"] = ArchivoProyectoForm()
        return ctx


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


# --------------------------------------------------------------------------
# CU-54 (RF-51) — Almacenando archivo y clasificándolo por tipo de documento
# --------------------------------------------------------------------------
@rol_requerido(*ROLES_ARCHIVO)
def archivo_subir(request, proyecto_pk):
    """
    Flujo principal: el actor elige el archivo, le pone nombre y selecciona el
    tipo de documento del catálogo; el sistema lo almacena asociado al proyecto.

    Excepción 1: si no selecciona tipo —o el catálogo está vacío— el sistema
    bloquea la carga y lo avisa, en vez de guardar un archivo sin clasificar.
    """
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)

    if not TipoDocumento.hay_catalogo():
        messages.error(
            request,
            "No hay tipos de documento en el catálogo. No se puede clasificar "
            "el archivo: pide a un administrador que cargue el catálogo primero."
        )
        return redirect("proyectos:detalle", pk=proyecto.pk)

    if request.method != "POST":
        return redirect("proyectos:detalle", pk=proyecto.pk)

    form = ArchivoProyectoForm(request.POST, request.FILES)
    if form.is_valid():
        archivo = form.save(commit=False)
        archivo.proyecto = proyecto
        archivo.subido_por = request.user
        archivo.save()
        messages.success(
            request,
            f"Archivo «{archivo.nombre}» almacenado y clasificado como {archivo.tipo}."
        )
        return redirect("proyectos:detalle", pk=proyecto.pk)

    # Vuelve a la ficha con los errores a la vista (no se guardó nada)
    messages.error(request, "No se pudo almacenar el archivo. Revisa los datos.")
    return render(request, "proyectos/proyecto_detail.html", {
        "proyecto": proyecto,
        "archivos": proyecto.archivos.select_related("tipo", "subido_por"),
        "hay_catalogo": True,
        "puede_subir": True,
        "form_archivo": form,
    })


@rol_requerido(*ROLES_ARCHIVO)
def archivo_eliminar(request, pk):
    """Quita un documento de la carpeta del proyecto."""
    archivo = get_object_or_404(ArchivoProyecto, pk=pk)
    proyecto_pk = archivo.proyecto_id
    if request.method == "POST":
        archivo.archivo.delete(save=False)
        archivo.delete()
        messages.success(request, "Documento eliminado.")
    return redirect("proyectos:detalle", pk=proyecto_pk)


class TipoDocumentoListView(RolRequeridoMixin, ListView):
    """Catálogo de tipos de documento (lo que destraba la Excepción 1)."""
    roles_permitidos = ROLES_ARCHIVO
    model = TipoDocumento
    template_name = "proyectos/tipodocumento_list.html"
    context_object_name = "tipos"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = TipoDocumentoForm()
        return ctx


@rol_requerido("ADMIN", "JEFE_PROYECTO")
def tipo_documento_crear(request):
    """Alta de un tipo en el catálogo."""
    if request.method == "POST":
        form = TipoDocumentoForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            messages.success(request, f"Tipo de documento «{tipo.nombre}» agregado al catálogo.")
        else:
            messages.error(request, "No se pudo agregar el tipo: " +
                           "; ".join(f"{c}: {e[0]}" for c, e in form.errors.items()))
    return redirect("proyectos:tipos_documento")
