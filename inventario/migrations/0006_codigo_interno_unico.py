"""
CU-62: recién ahora se impone la unicidad del código interno.

Va después de la migración de datos a propósito: si la restricción se aplicara
al crear el campo, todas las filas existentes quedarían con cadena vacía y la
segunda ya violaría el índice único.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0005_codigos_internos_existentes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="material",
            name="codigo_interno",
            field=models.CharField(
                blank=True, editable=False, max_length=20,
                unique=True, verbose_name="Código interno",
            ),
        ),
    ]
