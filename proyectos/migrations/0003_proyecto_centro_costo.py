"""Incremento 2 — RF-14: centro de costo del proyecto."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proyectos", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="proyecto",
            name="centro_costo",
            field=models.CharField(blank=True, max_length=50, verbose_name="Centro de costo"),
        ),
    ]
