# RF-51: el catálogo parte con los tipos de documento del requerimiento.
# Administración puede agregar, editar o deshabilitar tipos después (RF-57).
# get_or_create: no duplica ni pisa los que ya existan con el mismo nombre.

from django.db import migrations

TIPOS = [
    ("Contrato", "Contratos con el mandante, subcontratos y anexos"),
    ("Especificación Técnica", "Especificaciones técnicas de la obra"),
    ("Plano 2D", "Planimetría en 2D (DWG, DXF, PDF)"),
    ("Plano 3D", "Modelos 3D (IFC, RVT, SKP)"),
    ("Fotografía", "Registro fotográfico de la obra"),
    ("Videos", "Registro en video de la obra"),
]


def cargar(apps, schema_editor):
    TipoDocumento = apps.get_model("proyectos", "TipoDocumento")
    for nombre, descripcion in TIPOS:
        TipoDocumento.objects.get_or_create(nombre=nombre, defaults={"descripcion": descripcion})


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0008_quita_estado_suspendido'),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
