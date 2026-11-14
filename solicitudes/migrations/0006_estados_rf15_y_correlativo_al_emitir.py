# RF-12 / RF-15: la SM sigue los estados del documento.
#
#  · "Aprobada" (aprobada por el Jefe de Proyecto) era el equivalente a
#    "Emitida": es la SM que entra a la bandeja de Adquisiciones.
#  · "Enviada" (esperando el visto bueno del Jefe de Proyecto) desaparece:
#    ahora la SM la emite el propio Jefe de Proyecto, así que no hay a quién
#    pedirle aprobación. Las que estaban esperando pasan a "Emitida".
#  · El correlativo se asigna al emitir; por eso pasa a admitir NULL (borrador).
#    Las SM existentes conservan su número.

from django.db import migrations, models


def a_emitida(apps, schema_editor):
    SolicitudMaterial = apps.get_model("solicitudes", "SolicitudMaterial")
    SolicitudMaterial.objects.filter(estado__in=["APROBADA", "ENVIADA"]).update(estado="EMITIDA")


class Migration(migrations.Migration):

    dependencies = [
        ('solicitudes', '0005_solicitudmaterial_motivo_rechazo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitudmaterial',
            name='correlativo',
            field=models.CharField(blank=True, editable=False, max_length=20, null=True, unique=True, verbose_name='Correlativo'),
        ),
        migrations.RunPython(a_emitida, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='solicitudmaterial',
            name='estado',
            field=models.CharField(choices=[('BORRADOR', 'Borrador'), ('EMITIDA', 'Emitida'), ('EN_COTIZACION', 'En cotización'), ('OC_GENERADA', 'OC generada'), ('RECHAZADA', 'Rechazada'), ('RECEPCION_PARCIAL', 'Entregada parcialmente'), ('RECIBIDA', 'Entregada')], default='BORRADOR', max_length=20, verbose_name='Estado'),
        ),
    ]
