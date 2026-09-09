"""Incremento 2 — solicitudes:
RF-16 (partida + justificación por exceso de itemizado),
RF-17 (adjuntos PDF/JPG),
estados adicionales del flujo de cotización / OC / recepción.
"""
import django.db.models.deletion
import solicitudes.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("solicitudes", "0002_initial"),
        ("proyectos", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="solicitudmaterial",
            name="estado",
            field=models.CharField(
                choices=[
                    ("BORRADOR", "Borrador"),
                    ("ENVIADA", "Enviada"),
                    ("APROBADA", "Aprobada"),
                    ("RECHAZADA", "Rechazada"),
                    ("EN_COTIZACION", "En cotización"),
                    ("OC_GENERADA", "OC generada"),
                    ("RECEPCION_PARCIAL", "Entregada parcialmente"),
                    ("RECIBIDA", "Entregada"),
                ],
                default="BORRADOR",
                max_length=20,
                verbose_name="Estado",
            ),
        ),
        migrations.AddField(
            model_name="solicituddetalle",
            name="partida",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="lineas_solicitud",
                to="proyectos.itemizado",
                verbose_name="Partida del itemizado",
            ),
        ),
        migrations.AddField(
            model_name="solicituddetalle",
            name="justificacion",
            field=models.TextField(blank=True, verbose_name="Justificación (exceso de itemizado)"),
        ),
        migrations.CreateModel(
            name="SolicitudAdjunto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("archivo", models.FileField(upload_to=solicitudes.models.ruta_adjunto_solicitud, verbose_name="Archivo")),
                ("nombre", models.CharField(blank=True, max_length=150, verbose_name="Nombre / descripción")),
                ("fecha", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de carga")),
                ("solicitud", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="adjuntos", to="solicitudes.solicitudmaterial")),
                ("subido_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="adjuntos_subidos", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Adjunto de solicitud",
                "verbose_name_plural": "Adjuntos de solicitud",
                "ordering": ["fecha"],
            },
        ),
    ]
