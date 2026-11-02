"""
Una obra pasa a tener varios jefes de proyecto, no uno.

El campo antiguo se conserva hasta después de copiar los datos: en producción
ya hay obras con su jefe asignado y perder esa asignación dejaría a esos jefes
sin poder emitir solicitudes de su propia obra.
"""
from django.conf import settings
from django.db import migrations, models


def copiar_el_jefe_actual(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    for proyecto in Proyecto.objects.exclude(jefe_proyecto__isnull=True):
        proyecto.jefes.add(proyecto.jefe_proyecto_id)


def devolver_el_primer_jefe(apps, schema_editor):
    """Marcha atrás: el campo único se queda con el primero de la lista."""
    Proyecto = apps.get_model("proyectos", "Proyecto")
    for proyecto in Proyecto.objects.all():
        primero = proyecto.jefes.first()
        if primero is not None:
            proyecto.jefe_proyecto_id = primero.pk
            proyecto.save(update_fields=["jefe_proyecto"])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("proyectos", "0006_archivoproyecto_bloqueado_desde_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="proyecto",
            name="jefes",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "estado": True,
                    "pendiente_aprobacion": False,
                    "rol": "JEFE_PROYECTO",
                },
                related_name="proyectos_a_cargo_nuevo",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Jefes de proyecto",
            ),
        ),
        migrations.RunPython(copiar_el_jefe_actual, devolver_el_primer_jefe),
        migrations.RemoveField(model_name="proyecto", name="jefe_proyecto"),
        migrations.AlterField(
            model_name="proyecto",
            name="jefes",
            field=models.ManyToManyField(
                blank=True,
                limit_choices_to={
                    "estado": True,
                    "pendiente_aprobacion": False,
                    "rol": "JEFE_PROYECTO",
                },
                related_name="proyectos_a_cargo",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Jefes de proyecto",
            ),
        ),
    ]
