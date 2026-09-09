"""
Módulo de Adquisiciones — Incremento 2.

Cotizaciones (RF-19 a RF-22):
    Cotizacion        -> una por proveedor y solicitud, con costo de despacho
                         y tiempo de entrega.
    CotizacionLinea   -> valor unitario ofertado para cada material de la SM.
                         El usuario de Adquisiciones aprueba, por cada material,
                         la línea más conveniente (RF-22); las demás quedan
                         descartadas.

Órdenes de Compra (RF-23 a RF-27, RF-38, RF-39):
    OrdenCompra       -> borrador generado por proveedor con líneas aprobadas;
                         correlativo automático e irrepetible; aprobación del
                         Jefe de Proyecto; envío por correo; estado de recepción.
    OrdenCompraLinea  -> material, cantidad, valor unitario y cantidad recibida.
"""
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction

from proveedores.models import Proveedor
from solicitudes.models import SolicitudMaterial, SolicitudDetalle
from inventario.models import Material


class Cotizacion(models.Model):
    """RF-20: cotización de un proveedor para una Solicitud de Materiales."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PARCIAL = "PARCIAL", "Con líneas aprobadas"
        DESCARTADA = "DESCARTADA", "Descartada"

    solicitud = models.ForeignKey(SolicitudMaterial, on_delete=models.CASCADE, related_name="cotizaciones")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="cotizaciones")
    costo_despacho = models.DecimalField("Costo de despacho (CLP)", max_digits=12, decimal_places=0, default=0)
    tiempo_entrega_dias = models.PositiveSmallIntegerField("Tiempo de entrega (días hábiles)", default=1)
    estado = models.CharField("Estado", max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cotizaciones_creadas")
    fecha = models.DateTimeField("Fecha de registro", auto_now_add=True)

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ["solicitud", "proveedor"]
        unique_together = ("solicitud", "proveedor")

    def __str__(self):
        return f"Cotización {self.proveedor.nombre} · {self.solicitud.correlativo}"

    @property
    def subtotal_lineas(self):
        return sum((l.valor_total for l in self.lineas.all()), Decimal("0"))

    @property
    def valor_total(self):
        """RF-21: Σ(cantidad × valor unitario) + costo de despacho."""
        return self.subtotal_lineas + self.costo_despacho


class CotizacionLinea(models.Model):
    """Valor unitario ofertado por un proveedor para un material de la SM."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADA = "APROBADA", "Aprobada"
        DESCARTADA = "DESCARTADA", "Descartada"

    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name="lineas")
    solicitud_detalle = models.ForeignKey(SolicitudDetalle, on_delete=models.CASCADE, related_name="lineas_cotizacion")
    valor_unitario = models.DecimalField("Valor unitario ofertado (CLP)", max_digits=12, decimal_places=0)
    estado = models.CharField("Estado", max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)

    class Meta:
        verbose_name = "Línea de cotización"
        verbose_name_plural = "Líneas de cotización"
        unique_together = ("cotizacion", "solicitud_detalle")

    def __str__(self):
        return f"{self.solicitud_detalle.material.nombre} @ {self.valor_unitario}"

    @property
    def valor_total(self):
        return self.solicitud_detalle.cantidad_solicitada * self.valor_unitario

    @transaction.atomic
    def aprobar(self):
        """RF-22: aprueba esta línea y descarta las demás del mismo material."""
        (CotizacionLinea.objects
            .filter(cotizacion__solicitud=self.cotizacion.solicitud,
                    solicitud_detalle=self.solicitud_detalle)
            .exclude(pk=self.pk)
            .update(estado=CotizacionLinea.Estado.DESCARTADA))
        self.estado = CotizacionLinea.Estado.APROBADA
        self.save(update_fields=["estado"])
        self.cotizacion.estado = Cotizacion.Estado.PARCIAL
        self.cotizacion.save(update_fields=["estado"])


class OrdenCompra(models.Model):
    """RF-23: borrador de Orden de Compra por proveedor con líneas aprobadas."""

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        ENVIADA = "ENVIADA", "Enviada al proveedor"
        RECEPCION_PARCIAL = "RECEPCION_PARCIAL", "Recepción parcial"
        RECIBIDA = "RECIBIDA", "Recibida"
        NO_RECIBIDA = "NO_RECIBIDA", "No recibida"

    correlativo = models.CharField("Correlativo", max_length=20, unique=True, editable=False)
    solicitud = models.ForeignKey(SolicitudMaterial, on_delete=models.PROTECT, related_name="ordenes_compra")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="ordenes_compra")
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.PROTECT, related_name="ordenes_compra", null=True, blank=True)
    costo_despacho = models.DecimalField("Costo de despacho (CLP)", max_digits=12, decimal_places=0, default=0)
    estado = models.CharField("Estado", max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    facturada = models.BooleanField("Facturada", default=False)  # RF-40 (independiente de la recepción)
    motivo_rechazo = models.TextField("Motivo de rechazo", blank=True)

    # Datos snapshot para el documento (RF-23: autocompletado desde la BD)
    proveedor_rut = models.CharField("RUT proveedor", max_length=15, blank=True)
    proveedor_razon_social = models.CharField("Razón social proveedor", max_length=150, blank=True)
    proveedor_condicion_pago = models.CharField("Condición de pago", max_length=20, blank=True)

    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ordenes_creadas")
    fecha = models.DateTimeField("Fecha de creación", auto_now_add=True)
    aprobada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="ordenes_aprobadas")
    fecha_aprobacion = models.DateTimeField("Fecha de aprobación", null=True, blank=True)
    fecha_envio = models.DateTimeField("Fecha de envío", null=True, blank=True)

    class Meta:
        verbose_name = "Orden de compra"
        verbose_name_plural = "Órdenes de compra"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.correlativo} - {self.proveedor.nombre}"

    def save(self, *args, **kwargs):
        if not self.correlativo:
            ultimo = OrdenCompra.objects.order_by("-id").first()
            siguiente = (ultimo.id + 1) if ultimo else 1
            self.correlativo = f"OC-{siguiente:06d}"
        # Snapshot de datos del proveedor
        if self.proveedor_id and not self.proveedor_rut:
            self.proveedor_rut = self.proveedor.rut_formateado
            self.proveedor_razon_social = self.proveedor.nombre
            self.proveedor_condicion_pago = self.proveedor.get_condicion_pago_display()
        super().save(*args, **kwargs)

    @property
    def subtotal_lineas(self):
        return sum((l.valor_total for l in self.lineas.all()), Decimal("0"))

    @property
    def total(self):
        return self.subtotal_lineas + self.costo_despacho

    @property
    def editable(self):
        """RF-25: solo se puede editar una OC rechazada (para devolverla a borrador)."""
        return self.estado in (self.Estado.BORRADOR, self.Estado.RECHAZADA)

    @property
    def recepcion_completa(self):
        return all(l.cantidad_recibida >= l.cantidad for l in self.lineas.all())

    @property
    def recepcion_iniciada(self):
        return any(l.cantidad_recibida > 0 for l in self.lineas.all())


class OrdenCompraLinea(models.Model):
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name="lineas")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="lineas_orden_compra")
    descripcion = models.CharField("Descripción", max_length=200)
    cantidad = models.DecimalField("Cantidad", max_digits=12, decimal_places=2)
    unidad_medida = models.CharField("Unidad de medida", max_length=20, blank=True)
    valor_unitario = models.DecimalField("Valor unitario (CLP)", max_digits=12, decimal_places=0)
    cantidad_recibida = models.DecimalField("Cantidad recibida", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Línea de orden de compra"
        verbose_name_plural = "Líneas de orden de compra"

    def __str__(self):
        return f"{self.descripcion} x {self.cantidad}"

    @property
    def valor_total(self):
        return self.cantidad * self.valor_unitario

    @property
    def cantidad_pendiente(self):
        return self.cantidad - self.cantidad_recibida
