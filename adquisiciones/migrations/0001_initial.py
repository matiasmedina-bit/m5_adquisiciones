"""Incremento 2 — Adquisiciones: cotizaciones y órdenes de compra (RF-19 a RF-27, RF-38)."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("proveedores", "0001_initial"),
        ("inventario", "0001_initial"),
        ("solicitudes", "0003_incremento2_justificacion_adjuntos"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Cotizacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("costo_despacho", models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name="Costo de despacho (CLP)")),
                ("tiempo_entrega_dias", models.PositiveSmallIntegerField(default=1, verbose_name="Tiempo de entrega (días hábiles)")),
                ("estado", models.CharField(choices=[("PENDIENTE", "Pendiente"), ("PARCIAL", "Con líneas aprobadas"), ("DESCARTADA", "Descartada")], default="PENDIENTE", max_length=12, verbose_name="Estado")),
                ("fecha", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")),
                ("creada_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cotizaciones_creadas", to=settings.AUTH_USER_MODEL)),
                ("proveedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cotizaciones", to="proveedores.proveedor")),
                ("solicitud", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cotizaciones", to="solicitudes.solicitudmaterial")),
            ],
            options={
                "verbose_name": "Cotización",
                "verbose_name_plural": "Cotizaciones",
                "ordering": ["solicitud", "proveedor"],
            },
        ),
        migrations.CreateModel(
            name="OrdenCompra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("correlativo", models.CharField(editable=False, max_length=20, unique=True, verbose_name="Correlativo")),
                ("costo_despacho", models.DecimalField(decimal_places=0, default=0, max_digits=12, verbose_name="Costo de despacho (CLP)")),
                ("estado", models.CharField(choices=[("BORRADOR", "Borrador"), ("APROBADA", "Aprobada"), ("RECHAZADA", "Rechazada"), ("ENVIADA", "Enviada al proveedor"), ("RECEPCION_PARCIAL", "Recepción parcial"), ("RECIBIDA", "Recibida"), ("NO_RECIBIDA", "No recibida")], default="BORRADOR", max_length=20, verbose_name="Estado")),
                ("facturada", models.BooleanField(default=False, verbose_name="Facturada")),
                ("motivo_rechazo", models.TextField(blank=True, verbose_name="Motivo de rechazo")),
                ("proveedor_rut", models.CharField(blank=True, max_length=15, verbose_name="RUT proveedor")),
                ("proveedor_razon_social", models.CharField(blank=True, max_length=150, verbose_name="Razón social proveedor")),
                ("proveedor_condicion_pago", models.CharField(blank=True, max_length=20, verbose_name="Condición de pago")),
                ("fecha", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")),
                ("fecha_aprobacion", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de aprobación")),
                ("fecha_envio", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de envío")),
                ("aprobada_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="ordenes_aprobadas", to=settings.AUTH_USER_MODEL)),
                ("cotizacion", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="ordenes_compra", to="adquisiciones.cotizacion")),
                ("creada_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ordenes_creadas", to=settings.AUTH_USER_MODEL)),
                ("proveedor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ordenes_compra", to="proveedores.proveedor")),
                ("solicitud", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ordenes_compra", to="solicitudes.solicitudmaterial")),
            ],
            options={
                "verbose_name": "Orden de compra",
                "verbose_name_plural": "Órdenes de compra",
                "ordering": ["-fecha"],
            },
        ),
        migrations.CreateModel(
            name="OrdenCompraLinea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("descripcion", models.CharField(max_length=200, verbose_name="Descripción")),
                ("cantidad", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Cantidad")),
                ("unidad_medida", models.CharField(blank=True, max_length=20, verbose_name="Unidad de medida")),
                ("valor_unitario", models.DecimalField(decimal_places=0, max_digits=12, verbose_name="Valor unitario (CLP)")),
                ("cantidad_recibida", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Cantidad recibida")),
                ("material", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lineas_orden_compra", to="inventario.material")),
                ("orden", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lineas", to="adquisiciones.ordencompra")),
            ],
            options={
                "verbose_name": "Línea de orden de compra",
                "verbose_name_plural": "Líneas de orden de compra",
            },
        ),
        migrations.CreateModel(
            name="CotizacionLinea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("valor_unitario", models.DecimalField(decimal_places=0, max_digits=12, verbose_name="Valor unitario ofertado (CLP)")),
                ("estado", models.CharField(choices=[("PENDIENTE", "Pendiente"), ("APROBADA", "Aprobada"), ("DESCARTADA", "Descartada")], default="PENDIENTE", max_length=10, verbose_name="Estado")),
                ("cotizacion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lineas", to="adquisiciones.cotizacion")),
                ("solicitud_detalle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lineas_cotizacion", to="solicitudes.solicituddetalle")),
            ],
            options={
                "verbose_name": "Línea de cotización",
                "verbose_name_plural": "Líneas de cotización",
            },
        ),
        migrations.AlterUniqueTogether(
            name="cotizacion",
            unique_together={("solicitud", "proveedor")},
        ),
        migrations.AlterUniqueTogether(
            name="cotizacionlinea",
            unique_together={("cotizacion", "solicitud_detalle")},
        ),
    ]
