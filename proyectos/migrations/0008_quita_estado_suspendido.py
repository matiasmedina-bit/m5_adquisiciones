# RF-10: el documento sólo admite tres estados operativos para una obra
# ("En planificación", "En ejecución", "Finalizado"). El estado extra
# "Suspendido" se elimina; las obras que lo tuvieran vuelven a "En
# planificación", que es el estado que tampoco admite solicitudes de material
# (RF-12 exige "En ejecución") y que el Administrador puede volver a cambiar.

from django.db import migrations, models


def suspendidas_a_planificacion(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    Proyecto.objects.filter(estado="SUSPENDIDO").update(estado="PLANIFICACION")


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0007_proyecto_jefes'),
    ]

    operations = [
        migrations.RunPython(suspendidas_a_planificacion, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='proyecto',
            name='estado',
            field=models.CharField(choices=[('PLANIFICACION', 'En planificación'), ('EJECUCION', 'En ejecución'), ('FINALIZADO', 'Finalizado')], default='PLANIFICACION', max_length=15, verbose_name='Estado'),
        ),
    ]
