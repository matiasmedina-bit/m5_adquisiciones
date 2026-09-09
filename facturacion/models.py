"""
Módulo de Facturación y Contabilidad — Incremento 2 (RF-40 a RF-44).

Factura -> el rol Contabilidad recepciona la factura de un proveedor y la vincula
a una o más Órdenes de Compra (RF-40). El sistema valida el monto contra el de
las OC y, si excede la tolerancia parametrizable, la deja BLOQUEADA hasta que
Administración la desbloquee (RF-41 / RF-42). La vista "Cuentas por Pagar" ordena
por fecha de vencimiento (RF-43) y el listado se exporta a CSV (RF-44).
"""
from decimal import Decimal

from django.conf import settings
from django.db import models

from proveedores.models import Proveedor
from adquisiciones.models import OrdenCompra


def ruta_archivo_factura(instance, filename):
    return f"facturas/{instance.proveedor_id}/{filename}"


class Factura(models.Model):

    class Estado(models.TextChoices):
        REGISTRADA = "REGISTRADA", "Registrada"
        BLOQUEADA = "BLOQUEADA", "Bloqueada por diferencia de monto"

    numero = models.CharField("N° de factura", max_length=40)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="facturas")
    ordenes = models.ManyToManyField(OrdenCompra, related_name="facturas", verbose_name="Órdenes de compra")
    fecha_emision = models.DateField("Fecha de emisión")
    fecha_vencimiento = models.DateField("Fecha de vencimiento")
    monto_total = models.DecimalField("Monto total (CLP)", max_digits=15, decimal_places=0)
    archivo = models.FileField("Archivo digital (PDF/XML)", upload_to=ruta_archivo_factura, blank=True)
    estado = models.CharField("Estado", max_length=12, choices=Estado.choices, default=Estado.REGISTRADA)
    diferencia_pct = models.DecimalField("Diferencia % vs OC", max_digits=6, decimal_places=2, default=0)
    observacion = models.TextField("Observación / justificación", blank=True)

    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="facturas_registradas")
    creada = models.DateTimeField("Fecha de registro", auto_now_add=True)
    desbloqueada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="facturas_desbloqueadas",
    )
    fecha_desbloqueo = models.DateTimeField("Fecha de desbloqueo", null=True, blank=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["fecha_vencimiento"]
        unique_together = ("proveedor", "numero")

    def __str__(self):
        return f"Factura {self.numero} - {self.proveedor.nombre}"

    @property
    def total_ordenes(self):
        return sum((oc.total for oc in self.ordenes.all()), Decimal("0"))

    @property
    def esta_bloqueada(self):
        return self.estado == self.Estado.BLOQUEADA
