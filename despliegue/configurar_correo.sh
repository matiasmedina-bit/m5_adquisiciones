#!/usr/bin/env bash
# ============================================================
#  Appliance M5 - Conectar el sistema al correo de la empresa
#
#  Mientras esto no este hecho, el sistema NO manda correos: los
#  escribe en el log del servidor. Eso deja sin funcionar:
#     - recuperar contrasena olvidada
#     - el enlace de activacion de cuentas nuevas
#     - el envio de la orden de compra al proveedor
#     - los avisos de recepcion al jefe de obra
#
#  Uso:
#     bash /opt/m5/configurar_correo.sh
#
#  Pregunta los datos, los guarda, reinicia el servicio y manda un
#  correo de prueba de verdad. Si el correo no sale, deja el .env
#  como estaba: no te quedas peor que antes.
# ============================================================
set -euo pipefail

APP=/opt/m5/app
ENV=$APP/.env
PY=/opt/m5/venv/bin/python
SELLO=$(date +%Y%m%d-%H%M%S)

rojo()  { printf "\033[1;31m%s\033[0m\n" "$*"; }
verde() { printf "\033[1;32m%s\033[0m\n" "$*"; }
titulo(){ printf "\n\033[1;36m%s\033[0m\n" "$*"; }

if [ ! -f "$ENV" ]; then
    rojo "No existe $ENV. ¿Estas dentro de la VM del appliance?"
    exit 1
fi

echo
echo "############################################################"
echo "  Appliance M5 - correo saliente"
echo "############################################################"

# ------------------------------------------------------------
# 1. De quien es el correo
# ------------------------------------------------------------
titulo "1/5  Donde tiene M5 su correo"
echo "   1) Google Workspace   (correo en Gmail con dominio propio)"
echo "   2) Microsoft 365      (Outlook / Exchange Online)"
echo "   3) Hosting propio     (el que provee la pagina web)"
echo "   4) Otro / lo se de memoria"
echo
read -r -p "   Elige 1-4: " OPCION

case "$OPCION" in
    1) HOST="smtp.gmail.com";       PUERTO=587; CIFRADO=tls
       echo
       echo "   OJO con Google: si la cuenta tiene verificacion en dos pasos"
       echo "   —y hoy casi todas la tienen— la clave normal NO sirve. Hay que"
       echo "   generar una CONTRASENA DE APLICACION de 16 letras desde la"
       echo "   cuenta de Google, en Seguridad, y usar esa."
       ;;
    2) HOST="smtp.office365.com";   PUERTO=587; CIFRADO=tls
       echo
       echo "   OJO con Microsoft 365: viene con SMTP AUTH apagado por defecto."
       echo "   Si da error de autenticacion, el administrador tiene que"
       echo "   habilitarlo para ESTE buzon en el centro de administracion."
       ;;
    3) read -r -p "   Servidor SMTP (ej: mail.m-5.cl): " HOST
       read -r -p "   Puerto [587]: " PUERTO; PUERTO=${PUERTO:-587}
       if [ "$PUERTO" = "465" ]; then CIFRADO=ssl; else CIFRADO=tls; fi
       ;;
    *) read -r -p "   Servidor SMTP: " HOST
       read -r -p "   Puerto [587]: " PUERTO; PUERTO=${PUERTO:-587}
       read -r -p "   ¿Cifrado ssl o tls? [tls]: " CIFRADO; CIFRADO=${CIFRADO:-tls}
       ;;
esac

# ------------------------------------------------------------
# 2. La cuenta
# ------------------------------------------------------------
titulo "2/5  La cuenta desde la que sale el correo"
read -r -p "   Correo (ej: adquisiciones@m-5.cl): " USUARIO
read -r -s -p "   Contrasena: " CLAVE; echo
read -r -p "   Direccion que vera quien reciba [$USUARIO]: " REMITENTE
REMITENTE=${REMITENTE:-$USUARIO}

if [ -z "$HOST" ] || [ -z "$USUARIO" ] || [ -z "$CLAVE" ]; then
    rojo "Faltan datos. No se cambio nada."
    exit 1
fi

# ------------------------------------------------------------
# 3. Guardar, con respaldo
# ------------------------------------------------------------
titulo "3/5  Guardando la configuracion"
sudo cp "$ENV" "$ENV.bak-$SELLO"
sudo chmod 600 "$ENV.bak-$SELLO"
echo "   Respaldo: $ENV.bak-$SELLO"

sudo sed -i '/^#*EMAIL_BACKEND=/d;/^#*EMAIL_HOST=/d;/^#*EMAIL_PORT=/d' "$ENV"
sudo sed -i '/^#*EMAIL_HOST_USER=/d;/^#*EMAIL_HOST_PASSWORD=/d' "$ENV"
sudo sed -i '/^#*EMAIL_USE_TLS=/d;/^#*EMAIL_USE_SSL=/d;/^#*DEFAULT_FROM_EMAIL=/d' "$ENV"

if [ "$CIFRADO" = "ssl" ]; then USA_SSL=True; USA_TLS=False
else USA_SSL=False; USA_TLS=True; fi

sudo tee -a "$ENV" >/dev/null <<EOF
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=$HOST
EMAIL_PORT=$PUERTO
EMAIL_HOST_USER=$USUARIO
EMAIL_HOST_PASSWORD=$CLAVE
EMAIL_USE_TLS=$USA_TLS
EMAIL_USE_SSL=$USA_SSL
DEFAULT_FROM_EMAIL=$REMITENTE
EOF
sudo chmod 600 "$ENV"
verde "   Guardado: $HOST:$PUERTO ($CIFRADO) como $USUARIO"

# ------------------------------------------------------------
# 4. Reiniciar
# ------------------------------------------------------------
titulo "4/5  Reiniciando el servicio"
sudo systemctl restart gunicorn
sleep 3
CODIGO=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/ || echo 000)
if [ "$CODIGO" != "200" ] && [ "$CODIGO" != "302" ]; then
    rojo "   El sistema responde HTTP $CODIGO. Volviendo al .env anterior."
    sudo cp "$ENV.bak-$SELLO" "$ENV"
    sudo systemctl restart gunicorn
    rojo "   Revisa:  sudo journalctl -u gunicorn -n 40 --no-pager"
    exit 1
fi
verde "   El sistema responde HTTP $CODIGO."

# ------------------------------------------------------------
# 5. La prueba que vale: mandar un correo de verdad
# ------------------------------------------------------------
titulo "5/5  Correo de prueba"
read -r -p "   ¿A que direccion lo mando? [$USUARIO]: " DESTINO
DESTINO=${DESTINO:-$USUARIO}

cd "$APP"
set +e
SALIDA=$($PY - <<PYEOF 2>&1
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.core.mail import send_mail
from django.conf import settings
send_mail(
    subject="Prueba de correo - Sistema M5",
    message=(
        "Si estas leyendo esto, el sistema de adquisiciones de M5 ya puede "
        "enviar correos.\n\n"
        "Desde ahora funcionan: recuperar contrasena, el enlace de activacion "
        "de cuentas nuevas, el envio de ordenes de compra a proveedores y los "
        "avisos de recepcion."
    ),
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=["$DESTINO"],
    fail_silently=False,
)
print("ENVIADO")
PYEOF
)
ESTADO=$?
set -e

echo
if echo "$SALIDA" | grep -q "ENVIADO"; then
    echo "############################################################"
    verde "  Correo enviado a $DESTINO"
    echo "############################################################"
    echo
    echo "  Revisa la bandeja (y la carpeta de spam la primera vez)."
    echo "  Si llego, el sistema ya manda correos:"
    echo "     - recuperar contrasena"
    echo "     - activacion de cuentas nuevas"
    echo "     - ordenes de compra al proveedor"
    echo "     - avisos de recepcion al jefe de obra"
    echo
else
    rojo "  El correo NO salio. El .env quedo configurado igual,"
    rojo "  pero hay que corregir algo. Esto dijo el servidor:"
    echo
    echo "$SALIDA" | tail -12
    echo
    echo "  Lo que suele ser:"
    echo "   · 535 / authentication failed"
    echo "       Google: hay que usar contrasena de aplicacion, no la normal."
    echo "       Microsoft: falta habilitar SMTP AUTH para ese buzon."
    echo "   · Connection refused / timed out"
    echo "       El Fortinet bloquea la salida al puerto $PUERTO."
    echo "       Hay que pedir que la permitan para la IP de esta maquina."
    echo "   · certificate verify failed"
    echo "       Servidor con certificado propio: confirmar puerto y cifrado."
    echo
    echo "  Para volver atras:"
    echo "     sudo cp $ENV.bak-$SELLO $ENV && sudo systemctl restart gunicorn"
    echo
    exit 1
fi
