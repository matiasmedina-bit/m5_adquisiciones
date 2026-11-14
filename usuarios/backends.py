"""
RF-47 / CU-48 — Autenticación con correo institucional y contraseña.
RNF-08 — Bloqueo temporal de la cuenta tras 5 intentos fallidos (15 minutos).

Se reemplaza el backend por defecto de Django por uno que:

  · acepta como credencial sólo el correo electrónico institucional (RF-47).
    El nombre de usuario ya no sirve para entrar;
  · cuenta los intentos fallidos consecutivos por cuenta y, al quinto, la deja
    bloqueada 15 minutos. Durante el bloqueo ni siquiera la contraseña correcta
    entra: si entrara, el bloqueo no detendría a quien está probando claves.

Al estar en el backend, el bloqueo aplica a cualquier puerta de entrada: la
pantalla de login, el admin de Django y ``Client.login`` en los tests.
"""
from django.contrib.auth.backends import ModelBackend

from .models import IntentoAcceso, Usuario


def clave_de_intentos(identificador):
    """La cuenta si el correo existe; si no, el texto escrito (en minúsculas)."""
    identificador = (identificador or "").strip()
    usuario = buscar_usuario(identificador)
    if usuario is not None:
        return f"u{usuario.pk}"
    return identificador.lower()[:160]


def buscar_usuario(identificador):
    identificador = (identificador or "").strip()
    if not identificador:
        return None
    # RF-47: sólo el correo institucional (único en el sistema)
    return Usuario.objects.filter(email__iexact=identificador).first()


class CorreoInstitucionalBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identificador = username if username is not None else kwargs.get("email")
        if not identificador or password is None:
            return None

        clave = clave_de_intentos(identificador)
        hasta = IntentoAcceso.bloqueado(clave)
        if hasta:
            if request is not None:
                request.acceso_bloqueado_hasta = hasta
            return None

        usuario = buscar_usuario(identificador)
        if usuario is None:
            # Igual que ModelBackend: se calcula un hash para no delatar por tiempo
            # de respuesta que la cuenta no existe.
            Usuario().set_password(password)
            self._fallo(request, clave)
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            IntentoAcceso.limpiar(clave)
            return usuario

        self._fallo(request, clave)
        return None

    @staticmethod
    def _fallo(request, clave):
        registro = IntentoAcceso.registrar_fallo(clave)
        if registro.bloqueado_hasta and request is not None:
            request.acceso_bloqueado_hasta = registro.bloqueado_hasta
