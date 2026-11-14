"""
Control de acceso basado en roles (RBAC) - CU-52 'Gestionando roles'.
Provee un mixin y un decorador para restringir vistas según el rol del usuario.
"""
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


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
                # CU-55: una sesión vencida por inactividad vuelve al login
                # (y después a donde iba), no a una página de error.
                return redirect_to_login(request.get_full_path())
            if request.user.rol == "ADMIN" or request.user.rol in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("No tienes permisos para acceder a esta sección.")
        return _wrapped
    return decorator
