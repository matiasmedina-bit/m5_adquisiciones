"""
CU-53 — Captura automática de los movimientos de bodega.

Los movimientos de inventario se crean desde cuatro pantallas distintas
(entrada, salida, merma, devolución) y el modelo ya guarda quién los registró.
En vez de repetir la llamada a `registrar()` en cada vista —y arriesgarse a que
una futura se olvide y quede fuera de la bitácora— se escucha el post_save del
modelo: así ningún movimiento puede existir sin su línea de auditoría, ni
siquiera uno creado desde el admin de Django.

Las emisiones de SM y OC, la recepción de facturas y la gestión de cuentas sí
se auditan desde sus vistas, porque ahí lo auditable no es que el registro
exista sino el cambio de estado y quién lo hizo, dato que el modelo no guarda.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from inventario.models import MovimientoInventario, PrestamoHerramienta
from .models import RegistroAuditoria, registrar


@receiver(post_save, sender=MovimientoInventario)
def auditar_movimiento(sender, instance, created, **kwargs):
    """Toda entrada, salida, merma o devolución queda en la bitácora."""
    if not created:
        return
    registrar(
        instance.registrado_por,
        RegistroAuditoria.Accion.MOV_INVENTARIO,
        f"{instance.get_tipo_display()} de {instance.cantidad:g} "
        f"{instance.material.unidad_medida} de {instance.material.nombre}.",
        instance.material.nombre,
    )


@receiver(post_save, sender=PrestamoHerramienta)
def auditar_prestamo(sender, instance, created, **kwargs):
    """Salida y devolución de herramientas: es movimiento de inventario igual."""
    if created:
        descripcion = (f"Prestó {instance.herramienta.nombre} a "
                       f"{instance.jefe_proyecto.get_full_name() or instance.jefe_proyecto.username}.")
    elif instance.estado == PrestamoHerramienta.Estado.DEVUELTA:
        descripcion = f"Recibió la devolución de {instance.herramienta.nombre}."
    else:
        return
    registrar(
        instance.registrado_por,
        RegistroAuditoria.Accion.PRESTAMO_HERRAMIENTA,
        descripcion,
        instance.herramienta.codigo_activo or instance.herramienta.nombre,
    )
