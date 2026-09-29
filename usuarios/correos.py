"""
CU-52 (RF-49) — Enviando enlace temporal de activación de cuenta.

El actor del caso de uso es el Sistema: nadie manda este correo a mano. Cuando
el Administrador crea una cuenta, el sistema genera un enlace temporal y se lo
envía al correo institucional del nuevo usuario para que defina su contraseña.

El enlace usa el mismo mecanismo que la recuperación de contraseña de Django
(`default_token_generator`): un token firmado, de un solo uso, que caduca solo.
Es deliberado que sean el mismo mecanismo — dos sistemas de tokens distintos
son dos superficies que mantener y una que se va a quedar sin parchar.
"""
import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)

# Cuántas veces se reintenta antes de avisarle al administrador (Excepción 1)
REINTENTOS = 2


def _url_activacion(request, usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    ruta = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    if request is not None:
        return request.build_absolute_uri(ruta)
    return ruta


def enviar_enlace_activacion(request, usuario, creado_por=None):
    """
    Manda el enlace y devuelve True si salió.

    Excepción 1 del CU-52: si el envío falla se reintenta, y si el error
    persiste se le avisa al Administrador que creó la cuenta —que es quien
    puede hacer algo al respecto— en vez de dejar al usuario nuevo esperando
    un correo que nunca va a llegar.
    """
    if not usuario.email:
        logger.warning("Cuenta %s creada sin correo: no hay dónde mandar el enlace.",
                       usuario.username)
        return False

    enlace = _url_activacion(request, usuario)
    nombre = usuario.get_full_name() or usuario.username
    asunto = "Activa tu cuenta — Sistema de Adquisiciones M5"
    cuerpo = (
        f"Hola {nombre},\n\n"
        f"Se creó tu cuenta en el Sistema de Gestión de Adquisiciones e Inventario "
        f"de Constructora M5 SpA, con el rol de {usuario.get_rol_display()}.\n\n"
        f"Para entrar necesitas definir tu contraseña. Usa este enlace:\n\n"
        f"{enlace}\n\n"
        f"El enlace es de un solo uso y caduca. Si expira, puedes pedir uno nuevo "
        f"desde «¿Olvidaste tu contraseña?» en la pantalla de inicio de sesión.\n\n"
        f"Tu nombre de usuario es: {usuario.username}\n\n"
        f"— Constructora M5 SpA"
    )

    for intento in range(1, REINTENTOS + 1):
        try:
            send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL,
                      [usuario.email], fail_silently=False)
            return True
        except Exception as exc:  # smtp caído, credenciales malas, DNS…
            logger.warning("Intento %s de enviar la activación a %s falló: %s",
                           intento, usuario.email, exc)

    _avisar_fallo(request, usuario, creado_por)
    return False


def _avisar_fallo(request, usuario, creado_por):
    """Le dice al administrador que el correo no salió y qué hacer."""
    if not (creado_por and creado_por.email):
        return
    try:
        send_mail(
            f"No se pudo enviar la activación de {usuario.username}",
            f"El enlace de activación para {usuario.email} no se pudo enviar "
            f"después de {REINTENTOS} intentos.\n\n"
            f"La cuenta quedó creada pero sin contraseña, así que el usuario todavía "
            f"no puede entrar. Puedes reenviarle el enlace desde la ficha de la "
            f"cuenta, o pedirle que use «¿Olvidaste tu contraseña?».\n\n"
            f"— Sistema de Adquisiciones M5",
            settings.DEFAULT_FROM_EMAIL, [creado_por.email], fail_silently=True)
    except Exception:
        logger.exception("Tampoco se pudo avisar al administrador del fallo de envío.")
