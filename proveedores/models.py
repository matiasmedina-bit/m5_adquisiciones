"""
Modelo Proveedor del MERE. Cubre los CU-01 a CU-05.
"""
from django.db import models
from usuarios.validators import validar_rut, limpiar_rut, formatear_rut


class Proveedor(models.Model):
    """Entidad Proveedor (Proveedor_id, nombre, rut, correo, telefono, condicion_pago, estado)."""

    class CondicionPago(models.TextChoices):
        CONTADO = "CONTADO", "Contado"
        DIAS_30 = "30_DIAS", "30 días"
        DIAS_60 = "60_DIAS", "60 días"
        DIAS_90 = "90_DIAS", "90 días"

    nombre = models.CharField("Nombre / Razón social", max_length=150)
    # RUT único: garantiza el control anti-duplicado a nivel de BD (CU-03)
    rut = models.CharField("RUT", max_length=12, unique=True, validators=[validar_rut])
    correo = models.EmailField("Correo electrónico", blank=True)
    telefono = models.CharField("Teléfono", max_length=20, blank=True)
    condicion_pago = models.CharField(
        "Condición de pago", max_length=10,
        choices=CondicionPago.choices, default=CondicionPago.CONTADO,
    )
    estado = models.BooleanField("Activo", default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.rut_formateado})"

    def save(self, *args, **kwargs):
        # Normaliza el RUT antes de guardar (clave para el anti-duplicado CU-03)
        self.rut = limpiar_rut(self.rut)
        super().save(*args, **kwargs)

    @property
    def rut_formateado(self):
        try:
            return formatear_rut(self.rut)
        except (ValueError, IndexError):
            return self.rut

    @property
    def materiales_disponibles(self):
        return self.materiales.filter(disponible=True)


class ProveedorMaterial(models.Model):
    """
    Listado de materiales que un proveedor suministra (RF-05, RF-06, RF-07).
    Cada renglón guarda el código con que el proveedor identifica el material,
    su unidad de medida y descripción, y si sigue disponible para nuevas
    órdenes de compra. Al marcarlo como no disponible NO se borra el registro,
    de modo que el historial de OC asociadas queda intacto (RF-06).
    """
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.CASCADE, related_name="materiales"
    )
    codigo = models.CharField("Código del proveedor", max_length=40)
    descripcion = models.CharField("Descripción", max_length=200)
    unidad_medida = models.CharField("Unidad de medida", max_length=20)
    # Precio unitario ofertado por el proveedor para este material. Sirve para
    # precargar el valor al cotizar y para que el Jefe de Proyecto vea el monto
    # estimado antes de aprobar una solicitud.
    precio = models.DecimalField(
        "Precio unitario (CLP)", max_digits=12, decimal_places=0, default=0
    )
    # La condición de pago se negocia por producto, no por proveedor: un mismo
    # proveedor puede vender cemento a 30 días y arriendo de maquinaria al
    # contado. Si queda en blanco, la orden de compra usa la del proveedor.
    condicion_pago = models.CharField(
        "Condición de pago", max_length=10,
        choices=Proveedor.CondicionPago.choices, blank=True,
        help_text="Si se deja vacía, se usa la condición por defecto del proveedor.",
    )
    # Puente hacia el catálogo general de materiales. Se deja vacío al cargar
    # el Excel y se completa la primera vez que este ítem se usa en una
    # solicitud: así el catálogo del proveedor y el de la constructora se van
    # amarrando solos, sin tener que mapearlos a mano ni duplicar materiales.
    material = models.ForeignKey(
        "inventario.Material", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="ofertas",
        verbose_name="Material del catálogo",
    )
    disponible = models.BooleanField("Disponible", default=True)
    creado = models.DateTimeField("Fecha de alta", auto_now_add=True)
    modificado = models.DateTimeField("Última modificación", auto_now=True)

    class Meta:
        verbose_name = "Material del proveedor"
        verbose_name_plural = "Materiales del proveedor"
        ordering = ["descripcion"]
        # RF: no repetir el mismo código dentro del catálogo de un proveedor
        unique_together = ("proveedor", "codigo")

    def __str__(self):
        return f"{self.codigo} · {self.descripcion}"

    @property
    def condicion_pago_efectiva(self):
        """Condición propia del material; si no tiene, la del proveedor."""
        if self.condicion_pago:
            return self.get_condicion_pago_display()
        return self.proveedor.get_condicion_pago_display()

    def resolver_material(self):
        """
        Devuelve el Material del catálogo general que corresponde a esta oferta,
        creándolo la primera vez a partir de la descripción del proveedor.

        Sin esto, cada solicitud que usara un ítem del catálogo de un proveedor
        crearía un Material nuevo y el catálogo de la constructora se llenaría
        de duplicados ("Cemento 25kg", "Cemento Portland 25 kg", ...).
        """
        from inventario.models import Material

        if self.material_id:
            return self.material

        nombre = self.descripcion.strip()
        material = Material.objects.filter(nombre__iexact=nombre).first()
        if material is None:
            material = Material.objects.create(
                nombre=nombre,
                unidad_medida=self.unidad_medida or "un",
                precio_referencia=self.precio or 0,
            )
        self.material = material
        self.save(update_fields=["material", "modificado"])
        return material
