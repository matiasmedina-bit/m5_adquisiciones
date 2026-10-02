"""
Vistas de Proyectos e Itemizado.
CU-06 Registrando proyecto    CU-07 Editando proyecto
CU-08 Consultando proyecto    CU-09 Agregando itemizado al proyecto
CU-10 Editando itemizado
CU-54 Almacenando archivo y clasificándolo por tipo de documento (RF-51)
CU-57 Advirtiendo tamaño de archivo sobre el umbral (RF-54)
CU-58 Descargando y bloqueando archivo para edición offline (RF-55)
CU-59 Subiendo versión editada y liberando bloqueo (RF-56)
"""
import os

from django.contrib import messages
from django.utils import timezone
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from usuarios.models import ParametrosSistema
from usuarios.permisos import RolRequeridoMixin, rol_requerido
from .models import Proyecto, Itemizado, TipoDocumento, ArchivoProyecto
from .forms import (ProyectoForm, ItemizadoForm,
                    ArchivoProyectoForm, TipoDocumentoForm)

ROLES_GESTION = ["JEFE_PROYECTO"]
# CU-54: quiénes pueden almacenar documentos en la carpeta del proyecto.
# ADMIN entra siempre por la regla general de usuarios.permisos.
ROLES_ARCHIVO = ["JEFE_PROYECTO", "ENCARGADO_ADQUISICIONES", "CONTABILIDAD"]


class ProyectoListView(RolRequeridoMixin, ListView):
    # CONTABILIDAD entra porque puede almacenar documentos del proyecto (CU-54);
    # sin el listado tenía el permiso concedido y ninguna puerta para usarlo.
    roles_permitidos = ROLES_GESTION + ["ENCARGADO_ADQUISICIONES", "CONTABILIDAD"]
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
        ctx["umbral_mb"] = ParametrosSistema.actuales().umbral_archivo_mb
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
        # CU-57 (RF-54): sobre el umbral se advierte, no se bloquea. El caso de
        # uso pide "ofrecer comprimir o reducir la resolución antes de completar
        # la carga" — o sea, una decisión del usuario, no una prohibición: un
        # plano pesado a veces tiene que subir pesado.
        subido = form.cleaned_data["archivo"]
        parametros = ParametrosSistema.actuales()
        if subido.size > parametros.umbral_archivo_bytes and not request.POST.get("confirmar_tamano"):
            messages.warning(
                request,
                f"«{subido.name}» pesa {subido.size / 1024 / 1024:.1f} MB y el máximo "
                f"recomendado es {parametros.umbral_archivo_mb} MB. Comprímelo o baja "
                f"la resolución, o marca «subir de todas formas» y vuelve a enviarlo.")
            return render(request, "proyectos/proyecto_detail.html", {
                "proyecto": proyecto,
                "archivos": proyecto.archivos.select_related("tipo", "subido_por"),
                "hay_catalogo": True,
                "puede_subir": True,
                "form_archivo": form,
                "advertencia_tamano": True,
                "umbral_mb": parametros.umbral_archivo_mb,
            })

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


@rol_requerido("JEFE_PROYECTO")
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


# --------------------------------------------------------------------------
# CU-58 (RF-55) — Descargando y bloqueando archivo para edición offline
# CU-59 (RF-56) — Subiendo versión editada y liberando bloqueo
# --------------------------------------------------------------------------
@rol_requerido(*ROLES_ARCHIVO)
@require_POST
def archivo_bloquear(request, pk):
    """
    El actor se lleva el archivo para editarlo fuera del sistema y queda tomado
    a su nombre.

    Excepción 1: si otro lo tiene bloqueado, no se descarga en modo edición y se
    dice **quién** lo tiene. Decir sólo "está bloqueado" obliga a preguntar por
    el pasillo; decir el nombre resuelve el problema en un mensaje.
    """
    archivo = get_object_or_404(ArchivoProyecto, pk=pk)
    if archivo.bloqueado_para(request.user):
        quien = archivo.bloqueado_por.get_full_name() or archivo.bloqueado_por.username
        messages.error(
            request,
            f"«{archivo.nombre}» lo tiene {quien} desde el "
            f"{archivo.bloqueado_desde:%d/%m/%Y a las %H:%M}.")
        return redirect("proyectos:detalle", pk=archivo.proyecto_id)

    archivo.bloqueado_por = request.user
    archivo.bloqueado_desde = timezone.now()
    archivo.save(update_fields=["bloqueado_por", "bloqueado_desde"])
    messages.success(
        request,
        f"«{archivo.nombre}» quedó bloqueado a tu nombre. Descárgalo, edítalo y "
        f"sube la versión nueva para liberarlo.")
    return redirect("proyectos:detalle", pk=archivo.proyecto_id)


@rol_requerido(*ROLES_ARCHIVO)
@require_POST
def archivo_liberar(request, pk):
    """Suelta el bloqueo sin subir nada, cuando al final no se editó."""
    archivo = get_object_or_404(ArchivoProyecto, pk=pk)
    # El administrador puede destrabar un archivo que quedó tomado por alguien
    # que se fue de la empresa; cualquier otro sólo suelta el suyo.
    if archivo.bloqueado_para(request.user) and request.user.rol != "ADMIN":
        quien = archivo.bloqueado_por.get_full_name() or archivo.bloqueado_por.username
        messages.error(request, f"Ese archivo lo tiene bloqueado {quien}, no tú.")
    else:
        archivo.bloqueado_por = None
        archivo.bloqueado_desde = None
        archivo.save(update_fields=["bloqueado_por", "bloqueado_desde"])
        messages.success(request, f"«{archivo.nombre}» quedó libre para todos.")
    return redirect("proyectos:detalle", pk=archivo.proyecto_id)


@rol_requerido(*ROLES_ARCHIVO)
@require_POST
def archivo_subir_version(request, pk):
    """
    Reemplaza el archivo por la versión editada y suelta el bloqueo.

    Excepción 1: si el archivo que suben no es del mismo formato que el que se
    descargó, se rechaza y se dice cuál se esperaba. Cambiar un .dwg por un .pdf
    con el mismo nombre no es una versión nueva, es otro documento.
    """
    archivo = get_object_or_404(ArchivoProyecto, pk=pk)

    if not archivo.bloqueado:
        messages.error(request, "Primero tienes que bloquear el archivo para editarlo.")
        return redirect("proyectos:detalle", pk=archivo.proyecto_id)
    if archivo.bloqueado_para(request.user):
        quien = archivo.bloqueado_por.get_full_name() or archivo.bloqueado_por.username
        messages.error(request, f"No puedes subir sobre un archivo que tiene bloqueado {quien}.")
        return redirect("proyectos:detalle", pk=archivo.proyecto_id)

    nuevo = request.FILES.get("archivo")
    if not nuevo:
        messages.error(request, "Elige el archivo editado antes de subirlo.")
        return redirect("proyectos:detalle", pk=archivo.proyecto_id)

    esperada = archivo.extension_esperada
    recibida = os.path.splitext(nuevo.name)[1].lower().lstrip(".")
    if esperada and recibida != esperada:
        messages.error(
            request,
            f"La versión editada tiene que venir en .{esperada} y subiste un "
            f".{recibida}. Si es otro documento, cárgalo como archivo nuevo.")
        return redirect("proyectos:detalle", pk=archivo.proyecto_id)

    # CU-57: el umbral también se respeta al subir una versión
    limite = ParametrosSistema.actuales().umbral_archivo_bytes
    if nuevo.size > limite and not request.POST.get("confirmar_tamano"):
        mb = ParametrosSistema.actuales().umbral_archivo_mb
        messages.warning(
            request,
            f"El archivo pesa {nuevo.size / 1024 / 1024:.1f} MB y el umbral está en "
            f"{mb} MB. Comprímelo o baja la resolución, o vuelve a enviarlo marcando "
            f"«subir de todas formas».")
        return redirect("proyectos:detalle", pk=archivo.proyecto_id)

    archivo.archivo.delete(save=False)
    archivo.archivo = nuevo
    archivo.version += 1
    archivo.bloqueado_por = None
    archivo.bloqueado_desde = None
    archivo.subido_por = request.user
    archivo.save()
    messages.success(
        request,
        f"«{archivo.nombre}» quedó en la versión {archivo.version} y liberado "
        f"para el resto del equipo.")
    return redirect("proyectos:detalle", pk=archivo.proyecto_id)
