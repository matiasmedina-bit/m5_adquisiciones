def pendientes_count(request):
    if request.user.is_authenticated and getattr(request.user, "rol", None) == "ADMIN":
        from .models import Usuario
        return {"pendientes_count": Usuario.objects.filter(pendiente_aprobacion=True).count()}
    return {"pendientes_count": 0}


def notificaciones(request):
    """Cuántos avisos sin leer tiene el usuario, para la campana de la barra."""
    if request.user.is_authenticated:
        return {"notificaciones_sin_leer": request.user.notificaciones.filter(leida=False).count()}
    return {"notificaciones_sin_leer": 0}
