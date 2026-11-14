# RF-42: las salidas a obra registradas antes de exigir la partida (RF-28) no
# la tienen. Se completa sólo cuando no hay duda: si en esa obra el material
# se pidió (en SM no rechazadas) contra UNA única partida, la salida se imputa
# a esa partida. Si se pidió contra varias, o nunca se pidió, la salida queda
# sin partida y el reporte de desviación la muestra en la fila «(sin partida)»:
# repartirla a ojo inventaría un consumo que nadie registró.

from django.db import migrations


def completar(apps, schema_editor):
    Movimiento = apps.get_model("inventario", "MovimientoInventario")
    SolicitudDetalle = apps.get_model("solicitudes", "SolicitudDetalle")
    pendientes = Movimiento.objects.filter(tipo="SALIDA", partida__isnull=True, proyecto__isnull=False)
    for mov in pendientes:
        partidas = set(
            SolicitudDetalle.objects
            .filter(solicitud__proyecto_id=mov.proyecto_id, material_id=mov.material_id,
                    partida__isnull=False)
            .exclude(solicitud__estado="RECHAZADA")
            .values_list("partida_id", flat=True))
        if len(partidas) == 1:
            # update() directo: el save() del modelo volvería a mover el stock
            Movimiento.objects.filter(pk=mov.pk).update(partida_id=partidas.pop())


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0007_salida_partida'),
        ('solicitudes', '0006_estados_rf15_y_correlativo_al_emitir'),
    ]

    operations = [
        migrations.RunPython(completar, migrations.RunPython.noop),
    ]
