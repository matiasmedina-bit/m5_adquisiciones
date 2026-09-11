"""
Modelos Proyecto e Itemizado del MERE.
Relación: Proyecto --Contiene--> Itemizado (1:N). Cubre CU-06 a CU-10.
"""
from django.conf import settings
from django.db import models


class Proyecto(models.Model):
    """Entidad Proyecto."""

    class Estado(models.TextChoices):
        PLANIFICACION = "PLANIFICACION", "En planificación"
        EJECUCION = "EJECUCION", "En ejecución"
        FINALIZADO = "FINALIZADO", "Finalizado"
        SUSPENDIDO = "SUSPENDIDO", "Suspendido"

    nombre = models.CharField("Nombre del proyecto", max_length=150)
    mandante = models.CharField("Mandante", max_length=150)
    # RF-14: centro de costo. No debe repetirse en otro proyecto (se valida en
    # el formulario, ignorando los que quedaron en blanco por datos previos).
    centro_costo = models.CharField("Centro de costo", max_length=50, blank=True)
    # CU-08: jefe de proyecto asignado (Usuario con rol Jefe de Proyecto)
    jefe_proyecto = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proyectos_a_cargo",
        verbose_name="Jefe de proyecto",
        null=True, blank=True,
        # Sólo jefes activos y ya aprobados por un administrador (CU-52)
        limit_choices_to={"rol": "JEFE_PROYECTO", "estado": True,
                          "pendiente_aprobacion": False},
    )
    fecha_inicio = models.DateField("Fecha de inicio")
    fecha_termino = models.DateField("Fecha de término", null=True, blank=True)
    estado = models.CharField("Estado", max_length=15, choices=Estado.choices, default=Estado.PLANIFICACION)
    presupuesto_total = models.DecimalField("Presupuesto total (CLP)", max_digits=15, decimal_places=0, default=0)

    @property
    def esta_finalizado(self):
        """CU-10: un proyecto finalizado no admite nuevas solicitudes."""
        return self.estado == self.Estado.FINALIZADO

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return self.nombre

    @property
    def total_itemizado(self):
        """Suma de las cantidades presupuestadas del itemizado."""
        return sum(item.cant_presupuestada for item in self.itemizados.all())


class Itemizado(models.Model):
    """
    Entidad Itemizado (partidas presupuestarias de un proyecto).
    Proyecto --Contiene--> Itemizado.
    """
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name="itemizados")
    codigo_partida = models.CharField("Código de partida", max_length=30)
    descripcion = models.CharField("Descripción", max_length=200)
    unidad_medida = models.CharField("Unidad de medida", max_length=20)
    cant_presupuestada = models.DecimalField("Cantidad presupuestada", max_digits=12, decimal_places=2, default=0)
    cant_ejecutada = models.DecimalField("Cantidad ejecutada", max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Itemizado"
        verbose_name_plural = "Itemizados"
        ordering = ["codigo_partida"]
        # No repetir el mismo código de partida dentro de un proyecto
        unique_together = ("proyecto", "codigo_partida")

    def __str__(self):
        return f"{self.codigo_partida} - {self.descripcion}"

    @property
    def saldo_disponible(self):
        return self.cant_presupuestada - self.cant_ejecutada
