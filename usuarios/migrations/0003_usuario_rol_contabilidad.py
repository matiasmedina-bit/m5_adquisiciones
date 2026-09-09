"""Incremento 2: agrega el rol CONTABILIDAD al RBAC (RF-54)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0002_usuario_pendiente_aprobacion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Administrador"),
                    ("JEFE_PROYECTO", "Jefe de Proyecto"),
                    ("ENCARGADO_ADQUISICIONES", "Encargado de Adquisiciones"),
                    ("BODEGUERO", "Bodeguero"),
                    ("CONTABILIDAD", "Contabilidad"),
                ],
                default="BODEGUERO",
                max_length=30,
                verbose_name="Rol",
            ),
        ),
    ]
