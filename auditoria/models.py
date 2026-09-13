"""
CU-53 (RF-50) — Registrando en bitácora de auditoría.

El actor del caso de uso es el **Sistema**: nadie escribe la bitácora a mano.
Cada vez que ocurre una acción auditable el sistema deja constancia de quién la
hizo, cuándo y sobre qué. Las acciones auditables son las que el requisito
enumera:

  · movimientos de inventario (entradas, salidas, mermas, devoluciones)
  · emisión de solicitudes de material y de órdenes de compra
  · recepción de facturas
  · gestión de cuentas de usuario (alta, aprobación, cambio de rol, baja)

Excepción 1 del CU-53: una acción que no está en esa lista no genera registro.
Por eso `registrar()` valida la acción contra `Accion` y devuelve None en vez de
guardar cualquier cosa que se le pase — la bitácora tiene que ser exacta para
servir de evidencia.
"""
from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    """Una línea de la bitácora. Sólo se escribe; nunca se edita ni se borra."""

    class Accion(models.TextChoices):
        # --- Inventario (RF-28 a RF-37) ---
        MOV_INVENTARIO = "MOV_INVENTARIO", "Movimiento de inventario"
        PRESTAMO_HERRAMIENTA = "PRESTAMO_HERRAMIENTA", "Préstamo de herramienta"
        # --- Solicitudes (CU-11 a CU-17) ---
        SM_EMITIDA = "SM_EMITIDA", "Solicitud de material emitida"
        SM_APROBADA = "SM_APROBADA", "Solicitud de material aprobada"
        SM_RECHAZADA = "SM_RECHAZADA", "Solicitud de material rechazada"
        # --- Órdenes de compra (RF-19 a RF-27) ---
        OC_EMITIDA = "OC_EMITIDA", "Orden de compra emitida"
        OC_APROBADA = "OC_APROBADA", "Orden de compra aprobada"
        OC_ENVIADA = "OC_ENVIADA", "Orden de compra enviada al proveedor"
        # --- Facturación (RF-40 a RF-44) ---
        FACTURA_RECIBIDA = "FACTURA_RECIBIDA", "Factura recibida"
        FACTURA_BLOQUEADA = "FACTURA_BLOQUEADA", "Factura bloqueada por diferencia"
        FACTURA_DESBLOQUEADA = "FACTURA_DESBLOQUEADA", "Factura desbloqueada"
        # --- Cuentas de usuario (CU-50 a CU-52) ---
        USUARIO_CREADO = "USUARIO_CREADO", "Cuenta de usuario creada"
        USUARIO_APROBADO = "USUARIO_APROBADO", "Cuenta de usuario aprobada"
        USUARIO_RECHAZADO = "USUARIO_RECHAZADO", "Cuenta de usuario rechazada"
        USUARIO_MODIFICADO = "USUARIO_MODIFICADO", "Cuenta de usuario modificada"

    class Modulo(models.TextChoices):
        INVENTARIO = "INVENTARIO", "Inventario"
        SOLICITUDES = "SOLICITUDES", "Solicitudes"
        ADQUISICIONES = "ADQUISICIONES", "Adquisiciones"
        FACTURACION = "FACTURACION", "Facturación"
        USUARIOS = "Usuarios", "Usuarios"

    # Qué módulo agrupa cada acción. Se deduce sola, para que quien llama a
    # registrar() no tenga que acordarse.
    MODULO_DE = {
        Accion.MOV_INVENTARIO: Modulo.INVENTARIO,
        Accion.PRESTAMO_HERRAMIENTA: Modulo.INVENTARIO,
        Accion.SM_EMITIDA: Modulo.SOLICITUDES,
        Accion.SM_APROBADA: Modulo.SOLICITUDES,
        Accion.SM_RECHAZADA: Modulo.SOLICITUDES,
        Accion.OC_EMITIDA: Modulo.ADQUISICIONES,
        Accion.OC_APROBADA: Modulo.ADQUISICIONES,
        Accion.OC_ENVIADA: Modulo.ADQUISICIONES,
        Accion.FACTURA_RECIBIDA: Modulo.FACTURACION,
        Accion.FACTURA_BLOQUEADA: Modulo.FACTURACION,
        Accion.FACTURA_DESBLOQUEADA: Modulo.FACTURACION,
        Accion.USUARIO_CREADO: Modulo.USUARIOS,
        Accion.USUARIO_APROBADO: Modulo.USUARIOS,
        Accion.USUARIO_RECHAZADO: Modulo.USUARIOS,
        Accion.USUARIO_MODIFICADO: Modulo.USUARIOS,
    }

    # El usuario puede quedar en null: si se da de baja la cuenta, la bitácora
    # no se borra con ella. Por eso además se guarda su nombre en texto.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="registros_auditoria", verbose_name="Usuario")
    usuario_nombre = models.CharField("Usuario (texto)", max_length=150, blank=True)
    accion = models.CharField("Acción", max_length=30, choices=Accion.choices)
    modulo = models.CharField("Módulo", max_length=20, choices=Modulo.choices)
    descripcion = models.CharField("Descripción", max_length=250)
    # Referencia legible al objeto afectado: "SM-000012", "OC-000004", …
    referencia = models.CharField("Referencia", max_length=60, blank=True)
    fecha = models.DateTimeField("Fecha y hora", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Bitácora de auditoría"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["accion"]),
            models.Index(fields=["modulo", "fecha"]),
        ]

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y %H:%M} · {self.get_accion_display()} · {self.referencia}"

    @property
    def actor(self):
        """Nombre a mostrar, resista o no la cuenta original."""
        if self.usuario_id:
            return self.usuario.get_full_name() or self.usuario.username
        return self.usuario_nombre or "—"


def registrar(usuario, accion, descripcion, referencia=""):
    """
    Escribe una línea en la bitácora. Es el único punto de entrada.

    Excepción 1 del CU-53: si la acción no está en el catálogo de acciones
    auditables, no se genera ningún registro y se devuelve None. Callar es
    correcto acá: una bitácora con entradas inventadas no sirve como evidencia.
    """
    if accion not in RegistroAuditoria.Accion.values:
        return None

    nombre = ""
    if usuario is not None and getattr(usuario, "pk", None):
        nombre = usuario.get_full_name() or usuario.username
    else:
        usuario = None

    return RegistroAuditoria.objects.create(
        usuario=usuario,
        usuario_nombre=nombre,
        accion=accion,
        modulo=RegistroAuditoria.MODULO_DE.get(accion, RegistroAuditoria.Modulo.USUARIOS),
        descripcion=descripcion[:250],
        referencia=referencia[:60],
    )
