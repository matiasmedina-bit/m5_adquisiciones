def pendientes_count(request):
    if request.user.is_authenticated and getattr(request.user, "rol", None) == "ADMIN":
        from .models import Usuario
        return {"pendientes_count": Usuario.objects.filter(pendiente_aprobacion=True).count()}
    return {"pendientes_count": 0}
