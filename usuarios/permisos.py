"""
Control de acceso basado en roles (RBAC) - CU-52 'Gestionando roles'.
Provee un mixin y un decorador para restringir vistas según el rol del usuario.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin


class RolRequeridoMixin(LoginRequiredMixin):
    """
    Mixin para vistas basadas en clases. Define 'roles_permitidos' en la vista.
    El rol ADMIN siempre tiene acceso.
    """
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.rol == "ADMIN" or request.user.rol in self.roles_permitidos:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied("No tienes permisos para acceder a esta sección.")


def rol_requerido(*roles):
    """Decorador para vistas basadas en funciones."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Debes iniciar sesión.")
            if request.user.rol == "ADMIN" or request.user.rol in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("No tienes permisos para acceder a esta sección.")
        return _wrapped
    return decorator
