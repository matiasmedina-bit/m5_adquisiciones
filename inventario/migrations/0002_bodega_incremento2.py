"""Incremento 2 — Bodega:
RF-30/37 -> campos ubicacion y stock_minimo en Material
RF-28..RF-36 -> MovimientoInventario
RF-33/RF-34 -> PrestamoHerramienta
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0001_initial"),
        ("proyectos", "0002_initial"),
        ("adquisiciones", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="material",
            name="stock_minimo",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Stock mínimo"),
        ),
        migrations.AddField(
            model_name="material",
            name="ubicacion",
            field=models.CharField(blank=True, max_length=80, verbose_name="Ubicación en bodega"),
        ),
        migrations.CreateModel(
            name="MovimientoInventario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("ENTRADA", "Entrada a bodega"), ("SALIDA", "Salida a obra"), ("MERMA", "Merma / pérdida"), ("DEVOLUCION_PROVEEDOR", "Devolución a proveedor")], max_length=20, verbose_name="Tipo")),
                ("cantidad", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Cantidad")),
                ("ubicacion", models.CharField(blank=True, max_length=80, verbose_name="Ubicación física")),
                ("guia_despacho", models.CharField(blank=True, max_length=40, verbose_name="N° guía de despacho")),
                ("motivo", models.CharField(blank=True, max_length=20, verbose_name="Motivo")),
                ("observacion", models.TextField(blank=True, verbose_name="Observación")),
                ("fecha", models.DateTimeField(auto_now_add=True, verbose_name="Fecha")),
                ("jefe_proyecto", models.ForeignKey(blank=True, limit_choices_to={"rol": "JEFE_PROYECTO"}, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="movimientos_como_jefe", to=settings.AUTH_USER_MODEL, verbose_name="Jefe de proyecto")),
                ("material", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movimientos", to="inventario.material")),
                ("orden_compra", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="recepciones", to="adquisiciones.ordencompra", verbose_name="Orden de compra")),
                ("proyecto", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="movimientos_inventario", to="proyectos.proyecto", verbose_name="Proyecto")),
                ("registrado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movimientos_registrados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Movimiento de inventario",
                "verbose_name_plural": "Movimientos de inventario",
                "ordering": ["-fecha"],
            },
        ),
        migrations.CreateModel(
            name="PrestamoHerramienta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fecha_salida", models.DateField(verbose_name="Fecha de salida")),
                ("fecha_devolucion_esperada", models.DateField(verbose_name="Fecha de devolución esperada")),
                ("fecha_devolucion_real", models.DateField(blank=True, null=True, verbose_name="Fecha de devolución real")),
                ("estado", models.CharField(choices=[("PRESTADA", "Prestada"), ("DEVUELTA", "Devuelta / disponible en bodega")], default="PRESTADA", max_length=10, verbose_name="Estado")),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("herramienta", models.ForeignKey(limit_choices_to={"tipo": "HERRAMIENTA"}, on_delete=django.db.models.deletion.PROTECT, related_name="prestamos", to="inventario.material")),
                ("jefe_proyecto", models.ForeignKey(limit_choices_to={"rol": "JEFE_PROYECTO"}, on_delete=django.db.models.deletion.PROTECT, related_name="prestamos_recibidos", to=settings.AUTH_USER_MODEL, verbose_name="Jefe de proyecto")),
                ("proyecto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prestamos_herramienta", to="proyectos.proyecto", verbose_name="Obra de destino")),
                ("registrado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="prestamos_registrados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Préstamo de herramienta",
                "verbose_name_plural": "Préstamos de herramienta",
                "ordering": ["-creado"],
            },
        ),
    ]
