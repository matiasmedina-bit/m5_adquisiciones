"""
Filtro para leer una clave variable de un diccionario dentro de la plantilla.

Las plantillas de Django resuelven `fila.codigo`, pero no `fila[c.clave]`, y el
reporte es genérico: las columnas se deciden en tiempo de ejecución. Sin esto
habría que escribir una plantilla por reporte, que es justo lo que la estructura
común de consultas.py existe para evitar.
"""
from django import template

register = template.Library()


@register.filter
def dictkey(diccionario, clave):
    """`{{ fila|dictkey:c.clave }}` — devuelve None si la clave no está."""
    if hasattr(diccionario, "get"):
        return diccionario.get(clave)
    return None
