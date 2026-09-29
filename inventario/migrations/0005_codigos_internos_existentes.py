"""
CU-62 (RF-59): asigna código interno a los materiales que ya estaban en el
catálogo antes de que el campo existiera.

Sin esto, `codigo_interno` es unique y todos los registros previos quedan con
cadena vacía: la segunda fila revienta la restricción. Se numeran por familia
respetando el orden de creación, así los códigos siguen la historia real del
catálogo en vez de repartirse al azar.
"""
from django.db import migrations


def asignar_codigos(apps, schema_editor):
    Material = apps.get_model("inventario", "Material")
    prefijos = {"CONSUMIBLE": "MAT", "HERRAMIENTA": "HER"}
    contadores = {"MAT": 0, "HER": 0}
    for material in Material.objects.order_by("pk"):
        if material.codigo_interno:
            continue
        prefijo = prefijos.get(material.tipo, "MAT")
        contadores[prefijo] += 1
        material.codigo_interno = f"{prefijo}-{contadores[prefijo]:05d}"
        material.save(update_fields=["codigo_interno"])


def quitar_codigos(apps, schema_editor):
    """Al revertir se vacían: el campo desaparece en la migración anterior."""
    Material = apps.get_model("inventario", "Material")
    Material.objects.update(codigo_interno="")


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0004_material_categoria_material_codigo_interno"),
    ]

    operations = [
        migrations.RunPython(asignar_codigos, quitar_codigos),
    ]
