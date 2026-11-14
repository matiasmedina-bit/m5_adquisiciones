"""
Punto único para avisarle algo a uno o varios usuarios.

Lo usan los cambios de estado de la SM (RF-15, RF-20), el rechazo de una OC
(RF-22), la falla del envío de una OC al proveedor (RF-25 / CU-25 Exc. 1), el
préstamo de herramientas (RF-30) y el cambio de estado de recepción de una OC
(RF-35). Cada aviso queda como Notificacion (campana de la barra superior) y
además sale por correo. El correo nunca bloquea la operación: si el servidor
de correo falla, el aviso igual queda en el sistema.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notificar(destinatarios, titulo, mensaje="", url="", correo=True):
    """
    destinatarios: usuarios (o None, que se ignoran). Se descartan repetidos y
    cuentas inactivas. Devuelve la cantidad de notificaciones creadas.
    """
    from .models import Notificacion

    unicos = {}
    for usuario in destinatarios or []:
        if usuario is not None and getattr(usuario, "pk", None) and usuario.estado:
            unicos[usuario.pk] = usuario
    if not unicos:
        return 0

    Notificacion.objects.bulk_create([
        Notificacion(usuario=u, titulo=titulo[:150], mensaje=mensaje, url=url[:250])
        for u in unicos.values()
    ])

    if correo:
        correos = [u.email for u in unicos.values() if u.email]
        if correos:
            try:
                send_mail(
                    subject=f"[M5 Adquisiciones] {titulo}",
                    message=mensaje or titulo,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=correos,
                    fail_silently=False,
                )
            except Exception:  # el aviso en el sistema ya quedó guardado
                logger.exception("No se pudo enviar el correo de la notificación «%s».", titulo)
    return len(unicos)


def usuarios_con_rol(rol):
    from .models import usuarios_asignables
    return list(usuarios_asignables(rol))
