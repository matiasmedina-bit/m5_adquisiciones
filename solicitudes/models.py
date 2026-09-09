"""
Modelos Solicitud_Material y su detalle (relación Solicita N:M con Material).
Relaciones del MERE:
  Usuario --Emite--> Solicitud_Material (1:N)
  Proyecto --Genera--> Solicitud_Material (1:N)
  Solicitud_Material --Solicita--> Material (N:M) con cantidad_solicitada y unidad_medida
Cubre CU-11, CU-12, CU-14, CU-16, CU-17.
Incremento 2:
  RF-16 -> campo 'justificacion' cuando la cantidad supera el saldo del itemizado
  RF-17 -> modelo SolicitudAdjunto (hasta 3 archivos PDF/JPG por solicitud)
  Estados adicionales para el flujo de cotización / orden de compra / recepción.
"""
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from proyectos.models import Proyecto, Itemizado
from inventario.models import Material


class SolicitudMaterial(models.Model):
    """Entidad Solicitud_Material (cabecera de la solicitud)."""

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        ENVIADA = "ENVIADA", "Enviada"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        # --- Incremento 2 (Adquisiciones / Bodega) ---
        EN_COTIZACION = "EN_COTIZACION", "En cotización"
        OC_GENERADA = "OC_GENERADA", "OC generada"
        RECEPCION_PARCIAL = "RECEPCION_PARCIAL", "Entregada parcialmente"
        RECIBIDA = "RECIBIDA", "Entregada"

    correlativo = models.CharField("Correlativo", max_length=20, unique=True, editable=False)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name="solicitudes")
    # Usuario que emite la solicitud (Encargado de Adquisiciones)
    emisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes_emitidas")
    fecha = models.DateTimeField("Fecha de creación", auto_now_add=True)
    estado = models.CharField("Estado", max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    observaciones = models.TextField("Observaciones", blank=True)

    class Meta:
        verbose_name = "Solicitud de material"
        verbose_name_plural = "Solicitudes de material"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.correlativo} - {self.proyecto.nombre}"

    def save(self, *args, **kwargs):
        if not self.correlativo:
            # Genera correlativo tipo SM-000001
            ultimo = SolicitudMaterial.objects.order_by("-id").first()
            siguiente = (ultimo.id + 1) if ultimo else 1
            self.correlativo = f"SM-{siguiente:06d}"
        super().save(*args, **kwargs)

    @property
    def editable(self):
        """Solo se puede editar/agregar ítems mientras está en borrador (CU-14)."""
        return self.estado == self.Estado.BORRADOR

    @property
    def total_items(self):
        return self.detalles.count()

    @property
    def puede_cotizarse(self):
        """RF-19: una SM aprobada por el Jefe de Proyecto entra a la bandeja
        de Adquisiciones para cotizar (equivale al estado 'Emitida' del documento)."""
        return self.estado in (
            self.Estado.APROBADA, self.Estado.EN_COTIZACION,
        )

    @property
    def total_adjuntos(self):
        return self.adjuntos.count()


class SolicitudDetalle(models.Model):
    """
    Tabla intermedia de la relación 'Solicita' (Solicitud_Material N:M Material).
    Atributos de la relación: cantidad_solicitada y unidad_medida.
    """
    solicitud = models.ForeignKey(SolicitudMaterial, on_delete=models.CASCADE, related_name="detalles")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="solicitudes_detalle")
    cantidad_solicitada = models.DecimalField("Cantidad solicitada", max_digits=12, decimal_places=2)
    unidad_medida = models.CharField("Unidad de medida", max_length=20)
    # RF-16: vínculo con la partida del itemizado y justificación si se excede el saldo
    partida = models.ForeignKey(
        Itemizado, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lineas_solicitud", verbose_name="Partida del itemizado",
    )
    justificacion = models.TextField("Justificación (exceso de itemizado)", blank=True)

    class Meta:
        verbose_name = "Detalle de solicitud"
        verbose_name_plural = "Detalles de solicitud"
        unique_together = ("solicitud", "material")

    def __str__(self):
        return f"{self.material.nombre} x {self.cantidad_solicitada} {self.unidad_medida}"

    @property
    def excede_itemizado(self):
        """RF-16: True si la cantidad pedida supera el saldo disponible de la partida."""
        if not self.partida:
            return False
        return self.cantidad_solicitada > self.partida.saldo_disponible

    def save(self, *args, **kwargs):
        # Si no se especifica unidad, hereda la del material
        if not self.unidad_medida:
            self.unidad_medida = self.material.unidad_medida
        super().save(*args, **kwargs)


def ruta_adjunto_solicitud(instance, filename):
    return f"solicitudes/{instance.solicitud.correlativo}/{filename}"


class SolicitudAdjunto(models.Model):
    """
    RF-17: archivos de respaldo de una solicitud (planimetrías, rectificaciones
    de terreno). Hasta 3 por solicitud, formato PDF o JPG, máximo 5 MB c/u.
    Los límites de cantidad se validan en la vista; formato y tamaño aquí.
    """
    EXT_PERMITIDAS = (".pdf", ".jpg", ".jpeg")
    TAM_MAX_MB = 5
    MAX_POR_SOLICITUD = 3

    solicitud = models.ForeignKey(SolicitudMaterial, on_delete=models.CASCADE, related_name="adjuntos")
    archivo = models.FileField("Archivo", upload_to=ruta_adjunto_solicitud)
    nombre = models.CharField("Nombre / descripción", max_length=150, blank=True)
    subido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="adjuntos_subidos")
    fecha = models.DateTimeField("Fecha de carga", auto_now_add=True)

    class Meta:
        verbose_name = "Adjunto de solicitud"
        verbose_name_plural = "Adjuntos de solicitud"
        ordering = ["fecha"]

    def __str__(self):
        return self.nombre or os.path.basename(self.archivo.name)

    def clean(self):
        archivo = self.archivo
        if not archivo:
            return
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in self.EXT_PERMITIDAS:
            raise ValidationError("Formato no permitido. Solo se aceptan PDF y JPG.")
        if archivo.size and archivo.size > self.TAM_MAX_MB * 1024 * 1024:
            raise ValidationError(f"El archivo supera el tamaño máximo de {self.TAM_MAX_MB} MB.")
