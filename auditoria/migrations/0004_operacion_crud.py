# RF-50: cada registro de la bitácora indica si la acción fue Crear, Editar o
# Eliminar. Los registros existentes se clasifican según su acción.

from django.db import migrations, models

OPERACION_DE = {
    "MOV_INVENTARIO": "CREAR", "PRESTAMO_HERRAMIENTA": "CREAR",
    "SM_EMITIDA": "CREAR", "SM_APROBADA": "EDITAR", "SM_RECHAZADA": "EDITAR",
    "OC_EMITIDA": "CREAR", "OC_APROBADA": "EDITAR", "OC_ENVIADA": "EDITAR",
    "FACTURA_RECIBIDA": "CREAR", "FACTURA_BLOQUEADA": "EDITAR", "FACTURA_DESBLOQUEADA": "EDITAR",
    "USUARIO_CREADO": "CREAR", "USUARIO_APROBADO": "EDITAR", "USUARIO_RECHAZADO": "ELIMINAR",
    "USUARIO_MODIFICADO": "EDITAR", "USUARIO_ELIMINADO": "ELIMINAR",
    "CAMBIO_PERFIL_PEDIDO": "CREAR", "CAMBIO_PERFIL_RESUELTO": "EDITAR",
    "PARAMETROS_MODIFICADOS": "EDITAR",
}


def clasificar(apps, schema_editor):
    Registro = apps.get_model("auditoria", "RegistroAuditoria")
    for accion, operacion in OPERACION_DE.items():
        Registro.objects.filter(accion=accion).update(operacion=operacion)
    # La devolución de una herramienta es una modificación del préstamo
    Registro.objects.filter(accion="PRESTAMO_HERRAMIENTA",
                            descripcion__startswith="Recibió la devolución").update(operacion="EDITAR")


class Migration(migrations.Migration):

    dependencies = [
        ('auditoria', '0003_alter_registroauditoria_accion'),
    ]

    operations = [
        migrations.AddField(
            model_name='registroauditoria',
            name='operacion',
            field=models.CharField(choices=[('CREAR', 'Crear'), ('EDITAR', 'Editar'), ('ELIMINAR', 'Eliminar')], default='CREAR', max_length=10, verbose_name='Operación'),
        ),
        migrations.RunPython(clasificar, migrations.RunPython.noop),
    ]
