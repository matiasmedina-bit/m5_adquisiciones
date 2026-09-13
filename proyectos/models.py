"""
Modelos Proyecto e Itemizado del MERE.
Relación: Proyecto --Contiene--> Itemizado (1:N). Cubre CU-06 a CU-10.

CU-54 (RF-51) — Almacenando archivo y clasificándolo por tipo de documento:
  TipoDocumento  (catálogo)  --Clasifica--> ArchivoProyecto
  Proyecto       --Almacena--> ArchivoProyecto (1:N)
"""
import os
from django.conf import settings
from django.core.exceptions import ValidationError
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


# ==========================================================================
#  CU-54 (RF-51) — Almacenando archivo y clasificándolo por tipo de documento
# ==========================================================================

class TipoDocumento(models.Model):
    """
    Catálogo de tipos de documento con que se clasifica cada archivo del
    proyecto: plano, contrato, permiso municipal, acta de recepción…

    Es un catálogo administrable y no una lista fija en el código porque cada
    obra llega con su propia papelería; el CU-54 lo exige explícitamente
    («seleccionar el tipo desde un catálogo»). Si el catálogo está vacío, la
    Excepción 1 del caso de uso impide subir archivos hasta que se cargue.
    """
    nombre = models.CharField("Tipo de documento", max_length=80, unique=True)
    descripcion = models.CharField("Descripción", max_length=200, blank=True)
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Tipo de documento"
        verbose_name_plural = "Tipos de documento"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @classmethod
    def hay_catalogo(cls):
        """Excepción 1 del CU-54: sin catálogo no se puede clasificar nada."""
        return cls.objects.filter(activo=True).exists()


def ruta_archivo_proyecto(instance, filename):
    return f"proyectos/{instance.proyecto_id}/{filename}"


class ArchivoProyecto(models.Model):
    """
    Archivo almacenado contra un proyecto, obligatoriamente clasificado con un
    TipoDocumento. Lo suben Administrador, Adquisiciones, Contabilidad y el
    Jefe de Proyecto; queda registrado quién y cuándo, para que la carpeta del
    proyecto sea rastreable y no un montón de archivos sueltos.
    """
    EXT_PERMITIDAS = (".pdf", ".jpg", ".jpeg", ".png", ".dwg",
                      ".xlsx", ".xls", ".docx", ".doc")
    TAM_MAX_MB = 10

    proyecto = models.ForeignKey(
        Proyecto, on_delete=models.CASCADE, related_name="archivos")
    tipo = models.ForeignKey(
        TipoDocumento, on_delete=models.PROTECT, related_name="archivos",
        verbose_name="Tipo de documento")
    nombre = models.CharField("Nombre del documento", max_length=150)
    archivo = models.FileField("Archivo", upload_to=ruta_archivo_proyecto)
    observaciones = models.CharField("Observaciones", max_length=250, blank=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="archivos_proyecto_subidos")
    fecha = models.DateTimeField("Fecha de carga", auto_now_add=True)

    class Meta:
        verbose_name = "Archivo del proyecto"
        verbose_name_plural = "Archivos del proyecto"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

    @property
    def extension(self):
        return os.path.splitext(self.archivo.name)[1].lower().lstrip(".")

    @property
    def tamano_kb(self):
        try:
            return round(self.archivo.size / 1024)
        except (OSError, ValueError):
            return 0

    def clean(self):
        if not self.archivo:
            return
        ext = os.path.splitext(self.archivo.name)[1].lower()
        if ext not in self.EXT_PERMITIDAS:
            raise ValidationError(
                "Formato no permitido. Se aceptan: "
                + ", ".join(e.lstrip(".") for e in self.EXT_PERMITIDAS) + "."
            )
        if self.archivo.size and self.archivo.size > self.TAM_MAX_MB * 1024 * 1024:
            raise ValidationError(
                f"El archivo supera el tamaño máximo de {self.TAM_MAX_MB} MB.")
