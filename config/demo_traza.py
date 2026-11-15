"""
Modo demo (solo con MOSTRAR_SQL=True): muestra en la consola del servidor qué
controlador atiende cada petición y qué responde, para seguir el diagrama de
secuencia en vivo: vista -> controlador -> ORM (SQL) -> respuesta.
"""
import sys

_IGNORAR = ("/static/", "/media/", "/.well-known/", "/favicon")


class TrazaControladorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "_traza_demo", False):
            destino = response.get("Location", "")
            linea = f"RESPUESTA< {response.status_code}"
            if destino:
                linea += f" -> redirige a {destino}"
            sys.stderr.write(linea + "\n")
            sys.stderr.flush()
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith(_IGNORAR):
            return None
        clase = getattr(view_func, "view_class", None)
        nombre = clase.__name__ if clase else getattr(view_func, "__name__", str(view_func))
        sys.stderr.write(f"\nCONTROLADOR> {request.method} {request.path} -> "
                         f"{view_func.__module__}.{nombre}\n")
        sys.stderr.flush()
        request._traza_demo = True
        return None
