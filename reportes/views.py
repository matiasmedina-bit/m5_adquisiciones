"""
Módulo de Reportes — CU-42 a CU-46 (RF-41 a RF-45).

Las cuatro consultas viven en `consultas.py` y la exportación en `exportar.py`.
Acá sólo se resuelve quién puede ver qué, se leen los filtros de la URL y se
elige entre dibujar la pantalla o entregar el archivo.

El mismo parámetro `?formato=xlsx|pdf` sirve en los cuatro reportes: exportar
es el mismo gesto en todos, que es lo que pide el CU-46.
"""
from datetime import datetime

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from proyectos.models import Proyecto
from usuarios.permisos import rol_requerido

from . import consultas
from .exportar import FormatoNoSoportado, LibreriaFaltante, exportar

# RF-41 a RF-43: Jefe de Proyecto, Adquisiciones y Administración
ROLES_REPORTES = ("JEFE_PROYECTO", "ENCARGADO_ADQUISICIONES")
# RF-44: el historial de compras es sólo de Adquisiciones y Administración
ROLES_COMPRAS = ("ENCARGADO_ADQUISICIONES",)


def _fecha(valor):
    """'AAAA-MM-DD' del input date, o None si viene vacío o mal escrito."""
    if not valor:
        return None
    try:
        return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def _entregar(request, reporte, formato):
    """
    Exporta si se pidió un formato; si no, devuelve None y la vista sigue
    dibujando la pantalla.
    """
    if not formato:
        return None
    try:
        contenido, nombre, tipo = exportar(reporte, formato)
    except FormatoNoSoportado as exc:
        messages.error(request, str(exc))
        return "error"
    except LibreriaFaltante as exc:
        messages.error(request, str(exc))
        return "error"
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return respuesta


@rol_requerido(*ROLES_REPORTES)
def panel(request):
    """Portada del módulo: los cuatro reportes y para qué sirve cada uno."""
    return render(request, "reportes/panel.html", {
        "proyectos": consultas.proyectos_visibles(request.user),
        "puede_compras": request.user.rol in ROLES_COMPRAS + ("ADMIN",),
    })


# --------------------------------------------------------------------------
# CU-42 (RF-41) — Consumo consolidado por proyecto
# --------------------------------------------------------------------------
@rol_requerido(*ROLES_REPORTES)
def consumo(request):
    proyectos = consultas.proyectos_visibles(request.user)
    proyecto_id = (request.GET.get("proyecto") or "").strip()

    reporte = None
    proyecto = None
    if proyecto_id.isdigit():
        # Excepción 1: el Jefe de Proyecto que pide un proyecto ajeno no recibe
        # un 403 confuso; simplemente no está en su listado y se le dice.
        proyecto = proyectos.filter(pk=int(proyecto_id)).first()
        if proyecto is None:
            messages.warning(
                request,
                "Ese proyecto no está entre los que tienes asignados.")
        else:
            reporte = consultas.consumo_por_proyecto(proyecto)
            salida = _entregar(request, reporte, request.GET.get("formato"))
            if salida == "error":
                return redirect(f"{request.path}?proyecto={proyecto.pk}")
            if salida:
                return salida

    return render(request, "reportes/reporte.html", {
        "reporte": reporte,
        "proyectos": proyectos,
        "proyecto_sel": proyecto,
        "pide_proyecto": True,
        "pide_fechas": False,
        "url_actual": request.path,
        "titulo_pantalla": "Consumo consolidado por proyecto",
        "ayuda": "Qué se pidió, qué se despachó a la obra y cuánto costó, "
                 "material por material.",
    })


# --------------------------------------------------------------------------
# CU-43 (RF-42) — Desviación presupuestaria
# --------------------------------------------------------------------------
@rol_requerido(*ROLES_REPORTES)
def desviacion(request):
    proyectos = consultas.proyectos_visibles(request.user)
    proyecto_id = (request.GET.get("proyecto") or "").strip()

    reporte = None
    proyecto = None
    if proyecto_id.isdigit():
        proyecto = proyectos.filter(pk=int(proyecto_id)).first()
        if proyecto is None:
            messages.warning(request, "Ese proyecto no está entre los que tienes asignados.")
        else:
            reporte = consultas.desviacion_presupuestaria(proyecto)
            salida = _entregar(request, reporte, request.GET.get("formato"))
            if salida == "error":
                return redirect(f"{request.path}?proyecto={proyecto.pk}")
            if salida:
                return salida

    return render(request, "reportes/reporte.html", {
        "reporte": reporte,
        "proyectos": proyectos,
        "proyecto_sel": proyecto,
        "pide_proyecto": True,
        "pide_fechas": False,
        "url_actual": request.path,
        "titulo_pantalla": "Desviación presupuestaria",
        "ayuda": "El itemizado original contra lo realmente comprado y consumido.",
    })


# --------------------------------------------------------------------------
# CU-44 (RF-43) — Mermas y pérdidas
# --------------------------------------------------------------------------
@rol_requerido(*ROLES_REPORTES)
def mermas(request):
    proyectos = consultas.proyectos_visibles(request.user)
    proyecto_id = (request.GET.get("proyecto") or "").strip()
    proyecto = proyectos.filter(pk=int(proyecto_id)).first() if proyecto_id.isdigit() else None
    desde = _fecha(request.GET.get("desde"))
    hasta = _fecha(request.GET.get("hasta"))

    # Este reporte sí se puede pedir sin elegir proyecto: "¿cuánto perdimos en
    # total este mes?" es la pregunta natural de administración.
    reporte = consultas.mermas_y_perdidas(proyecto=proyecto, desde=desde, hasta=hasta)
    if request.user.rol == "JEFE_PROYECTO" and proyecto is None:
        # Sin proyecto elegido, el jefe vería mermas de obras ajenas
        reporte["filas"] = [f for f in reporte["filas"]
                            if f["proyecto"] in {p.nombre for p in proyectos}]
        reporte["vacio"] = not reporte["filas"]
        reporte["totales"]["valorizacion"] = sum(
            (f["valorizacion"] for f in reporte["filas"]), 0)

    salida = _entregar(request, reporte, request.GET.get("formato"))
    if salida == "error":
        return redirect(request.path)
    if salida:
        return salida

    return render(request, "reportes/reporte.html", {
        "reporte": reporte,
        "proyectos": proyectos,
        "proyecto_sel": proyecto,
        "pide_proyecto": True,
        "proyecto_opcional": True,
        "pide_fechas": True,
        "f_desde": request.GET.get("desde", ""),
        "f_hasta": request.GET.get("hasta", ""),
        "url_actual": request.path,
        "titulo_pantalla": "Mermas y pérdidas",
        "ayuda": "Material perdido por daño o robo, valorizado en pesos.",
    })


# --------------------------------------------------------------------------
# CU-45 (RF-44) — Historial de compras por proveedor
# --------------------------------------------------------------------------
@rol_requerido(*ROLES_COMPRAS)
def compras(request):
    desde = _fecha(request.GET.get("desde"))
    hasta = _fecha(request.GET.get("hasta"))
    reporte = consultas.compras_por_proveedor(desde=desde, hasta=hasta)

    salida = _entregar(request, reporte, request.GET.get("formato"))
    if salida == "error":
        return redirect(request.path)
    if salida:
        return salida

    return render(request, "reportes/reporte.html", {
        "reporte": reporte,
        "pide_proyecto": False,
        "pide_fechas": True,
        "f_desde": request.GET.get("desde", ""),
        "f_hasta": request.GET.get("hasta", ""),
        "url_actual": request.path,
        "titulo_pantalla": "Historial de compras por proveedor",
        "ayuda": "Cuánto se le compró a cada proveedor y en cuántas órdenes.",
    })
