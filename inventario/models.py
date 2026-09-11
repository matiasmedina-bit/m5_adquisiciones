"""
Modelo Material del MERE (catálogo) + gestión de bodega del Incremento 2.

Catálogo:
  Material  -> subtipos Herramienta / Material_Consumible (discriminador 'tipo').

Bodega (Incremento 2):
  MovimientoInventario -> entradas (RF-28..RF-30), salidas (RF-31),
                          mermas (RF-35) y devoluciones a proveedor (RF-36).
                          Cada movimiento ajusta el stock en tiempo real (RF-32).
  PrestamoHerramienta  -> préstamo (RF-33) y devolución (RF-34) de activos fijos.
  RF-37 -> alerta de stock mínimo (campo 'stock_minimo').
"""
from django.conf import settings
from django.db import models


class Material(models.Model):
    """Entidad Material: catálogo de materiales/herramientas de la constructora."""

    class Tipo(models.TextChoices):
        CONSUMIBLE = "CONSUMIBLE", "Material consumible"
        HERRAMIENTA = "HERRAMIENTA", "Herramienta"

    nombre = models.CharField("Nombre del material", max_length=150)
    unidad_medida = models.CharField("Unidad de medida", max_length=20)
    stock_actual = models.DecimalField("Stock actual", max_digits=12, decimal_places=2, default=0)
    # RF-37: nivel de stock mínimo para la alerta de material crítico
    stock_minimo = models.DecimalField("Stock mínimo", max_digits=12, decimal_places=2, default=0)
    # RF-30: ubicación física principal del material en bodega
    ubicacion = models.CharField("Ubicación en bodega", max_length=80, blank=True)
    precio_referencia = models.DecimalField("Precio de referencia (CLP)", max_digits=12, decimal_places=0, default=0)
    tipo = models.CharField("Tipo", max_length=12, choices=Tipo.choices, default=Tipo.CONSUMIBLE)
    # Atributos de subtipo (opcionales según el tipo)
    codigo_activo = models.CharField("Código de activo (herramienta)", max_length=40, blank=True)
    fecha_vencimiento = models.DateField("Fecha de vencimiento (consumible)", null=True, blank=True)
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida})"

    @property
    def bajo_stock_minimo(self):
        """RF-37: True si el stock cayó al nivel mínimo configurado (y hay mínimo)."""
        return self.stock_minimo > 0 and self.stock_actual <= self.stock_minimo

    @property
    def herramienta_prestada(self):
        return self.prestamos.filter(estado=PrestamoHerramienta.Estado.PRESTADA).exists()


class MovimientoInventario(models.Model):
    """
    Movimiento de bodega. Al crearse ajusta Material.stock_actual (RF-32).
      ENTRADA              -> recepción desde proveedor (asociada a una OC) o
                              retorno de sobrantes desde una obra (RF-28).
      SALIDA               -> despacho de material hacia una obra (RF-31).
      MERMA                -> pérdida por daño o robo (RF-35).
      DEVOLUCION_PROVEEDOR -> devolución de material a un proveedor (RF-36).
    """

    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada a bodega"
        SALIDA = "SALIDA", "Salida a obra"
        MERMA = "MERMA", "Merma / pérdida"
        DEVOLUCION_PROVEEDOR = "DEVOLUCION_PROVEEDOR", "Devolución a proveedor"

    class MotivoMerma(models.TextChoices):
        DANO = "DANO", "Daño"
        ROBO = "ROBO", "Robo"

    class MotivoDevolucion(models.TextChoices):
        EQUIVOCADO = "EQUIVOCADO", "Material equivocado"
        DEFECTUOSO = "DEFECTUOSO", "Material defectuoso"
        EXCEDENTE = "EXCEDENTE", "Excedente no requerido"

    tipo = models.CharField("Tipo", max_length=20, choices=Tipo.choices)
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="movimientos")
    cantidad = models.DecimalField("Cantidad", max_digits=12, decimal_places=2)
    # Origen / destino según el tipo
    orden_compra = models.ForeignKey(
        "adquisiciones.OrdenCompra", on_delete=models.PROTECT, null=True, blank=True,
        related_name="recepciones", verbose_name="Orden de compra",
    )
    proyecto = models.ForeignKey(
        "proyectos.Proyecto", on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimientos_inventario", verbose_name="Proyecto",
    )
    jefe_proyecto = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimientos_como_jefe", verbose_name="Jefe de proyecto",
        limit_choices_to={"rol": "JEFE_PROYECTO", "estado": True,
                          "pendiente_aprobacion": False},
    )
    ubicacion = models.CharField("Ubicación física", max_length=80, blank=True)
    guia_despacho = models.CharField("N° guía de despacho", max_length=40, blank=True)
    motivo = models.CharField("Motivo", max_length=20, blank=True)
    observacion = models.TextField("Observación", blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="movimientos_registrados",
    )
    fecha = models.DateTimeField("Fecha", auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.material.nombre} x {self.cantidad}"

    @property
    def suma_stock(self):
        """+cantidad si suma stock, -cantidad si lo descuenta."""
        return self.cantidad if self.tipo == self.Tipo.ENTRADA else -self.cantidad

    def save(self, *args, **kwargs):
        nuevo = self._state.adding
        super().save(*args, **kwargs)
        if nuevo:
            # RF-32: actualización del stock en tiempo real
            Material.objects.filter(pk=self.material_id).update(
                stock_actual=models.F("stock_actual") + self.suma_stock
            )
            if self.tipo == self.Tipo.ENTRADA and self.ubicacion and not self.material.ubicacion:
                Material.objects.filter(pk=self.material_id).update(ubicacion=self.ubicacion)


class PrestamoHerramienta(models.Model):
    """RF-33 / RF-34: préstamo y devolución de herramientas (activos fijos)."""

    class Estado(models.TextChoices):
        PRESTADA = "PRESTADA", "Prestada"
        DEVUELTA = "DEVUELTA", "Devuelta / disponible en bodega"

    herramienta = models.ForeignKey(
        Material, on_delete=models.PROTECT, related_name="prestamos",
        limit_choices_to={"tipo": "HERRAMIENTA"},
    )
    jefe_proyecto = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="prestamos_recibidos",
        limit_choices_to={"rol": "JEFE_PROYECTO", "estado": True,
                          "pendiente_aprobacion": False},
        verbose_name="Jefe de proyecto",
    )
    proyecto = models.ForeignKey(
        "proyectos.Proyecto", on_delete=models.PROTECT, related_name="prestamos_herramienta",
        verbose_name="Obra de destino",
    )
    fecha_salida = models.DateField("Fecha de salida")
    fecha_devolucion_esperada = models.DateField("Fecha de devolución esperada")
    fecha_devolucion_real = models.DateField("Fecha de devolución real", null=True, blank=True)
    estado = models.CharField("Estado", max_length=10, choices=Estado.choices, default=Estado.PRESTADA)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="prestamos_registrados",
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Préstamo de herramienta"
        verbose_name_plural = "Préstamos de herramienta"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.herramienta.nombre} → {self.proyecto.nombre} ({self.get_estado_display()})"
