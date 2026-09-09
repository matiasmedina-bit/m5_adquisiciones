"""Incremento 2 — RF-05/06/07: listado de materiales que suministra el proveedor."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proveedores", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProveedorMaterial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=40, verbose_name="Código del proveedor")),
                ("descripcion", models.CharField(max_length=200, verbose_name="Descripción")),
                ("unidad_medida", models.CharField(max_length=20, verbose_name="Unidad de medida")),
                ("disponible", models.BooleanField(default=True, verbose_name="Disponible")),
                ("creado", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de alta")),
                ("modificado", models.DateTimeField(auto_now=True, verbose_name="Última modificación")),
                ("proveedor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="materiales", to="proveedores.proveedor")),
            ],
            options={
                "verbose_name": "Material del proveedor",
                "verbose_name_plural": "Materiales del proveedor",
                "ordering": ["descripcion"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="proveedormaterial",
            unique_together={("proveedor", "codigo")},
        ),
    ]
