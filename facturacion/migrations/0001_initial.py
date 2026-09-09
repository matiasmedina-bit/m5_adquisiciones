"""Incremento 2 — Facturación y Contabilidad (RF-40 a RF-44)."""
import django.db.models.deletion
import facturacion.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("proveedores", "0001_initial"),
        ("adquisiciones", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Factura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero", models.CharField(max_length=40, verbose_name="N° de factura")),
                ("fecha_emision", models.DateField(verbose_name="Fecha de emisión")),
                ("fecha_vencimiento", models.DateField(verbose_name="Fecha de vencimiento")),
                ("monto_total", models.DecimalField(decimal_places=0, max_digits=15, verbose_name="Monto total (CLP)")),
                ("archivo", models.FileField(blank=True, upload_to=facturacion.models.ruta_archivo_factura, verbose_name="Archivo digital (PDF/XML)")),
                ("estado", models.CharField(choices=[("REGISTRADA", "Registrada"), ("BLOQUEADA", "Bloqueada por diferencia de monto")], default="REGISTRADA", max_length=12, verbose_name="Estado")),
                ("diferencia_pct", models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name="Diferencia % vs OC")),
                ("observacion", models.TextField(blank=True, verbose_name="Observación / justificación")),
                ("creada", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")),
                ("fecha_desbloqueo", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de desbloqueo")),
                ("desbloqueada_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="facturas_desbloqueadas", to=settings.AUTH_USER_MODEL)),
                ("ordenes", models.ManyToManyField(related_name="facturas", to="adquisiciones.ordencompra", verbose_name="Órdenes de compra")),
                ("proveedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="facturas", to="proveedores.proveedor")),
                ("registrado_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="facturas_registradas", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Factura",
                "verbose_name_plural": "Facturas",
                "ordering": ["fecha_vencimiento"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="factura",
            unique_together={("proveedor", "numero")},
        ),
    ]
