"""
Descarga protegida de archivos subidos (planos, adjuntos de SM, facturas).

Antes los archivos se enlazaban directo a /media/…: cualquiera con la URL los
bajaba sin iniciar sesión. Ahora cada descarga pasa por una vista que revisa
permisos y entrega el archivo con esta función.

En producción (DEBUG=False, nginx delante) conviene que nginx sirva el archivo:
con ARCHIVOS_X_ACCEL=True la respuesta sólo lleva el encabezado
X-Accel-Redirect hacia la ubicación interna /protegido/ (despliegue/nginx-m5.conf).
"""
import mimetypes
import os
from urllib.parse import quote

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse


def descargar_archivo(campo, nombre=None, en_linea=False):
    if not campo:
        raise Http404("Archivo no encontrado.")
    nombre = nombre or os.path.basename(campo.name)
    disposicion = "inline" if en_linea else "attachment"
    cabecera = f"{disposicion}; filename*=UTF-8''{quote(nombre)}"

    if getattr(settings, "ARCHIVOS_X_ACCEL", False):
        respuesta = HttpResponse()
        respuesta["X-Accel-Redirect"] = "/protegido/" + quote(campo.name)
        respuesta["Content-Type"] = mimetypes.guess_type(nombre)[0] or "application/octet-stream"
        respuesta["Content-Disposition"] = cabecera
        return respuesta

    try:
        archivo = campo.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("El archivo ya no está en el servidor.")
    respuesta = FileResponse(archivo, as_attachment=not en_linea, filename=nombre)
    return respuesta
