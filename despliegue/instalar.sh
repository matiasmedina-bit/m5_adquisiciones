#!/usr/bin/env bash
# ============================================================
#  Appliance M5 - Instalar lo que le falta a la VM
#
#  Correr UNA VEZ dentro de la VM, antes de volver a sellarla y
#  exportar el OVA definitivo.
#
#  Deja tres cosas:
#    1. /opt/m5/set_ip.sh          - adaptar la IP en un comando
#    2. /etc/cron.daily/m5-backup  - respaldo diario de base Y archivos
#    3. El bloque EMAIL_* en el .env, listo para completar con los
#       datos que entregue TI de M5
#
#  Uso:
#     cd /tmp/m5_extras
#     bash instalar.sh
# ============================================================
set -euo pipefail

APP=/opt/m5/app
ENV=$APP/.env
AQUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

verde() { printf "\033[1;32m%s\033[0m\n" "$*"; }
rojo()  { printf "\033[1;31m%s\033[0m\n" "$*"; }

echo
echo "############################################################"
echo "  Appliance M5 - instalacion de extras"
echo "############################################################"
echo

if [ ! -d /opt/m5 ]; then
    rojo "No existe /opt/m5. ¿Estas dentro de la VM del appliance?"
    exit 1
fi

# ------------------------------------------------------------
# 1. set_ip.sh
# ------------------------------------------------------------
echo "==> 1/3  set_ip.sh"
sudo cp "$AQUI/set_ip.sh" /opt/m5/set_ip.sh
sudo chmod 755 /opt/m5/set_ip.sh
sudo chown root:root /opt/m5/set_ip.sh
verde "    Instalado en /opt/m5/set_ip.sh"
echo "    Al importar el OVA en M5:  bash /opt/m5/set_ip.sh <ip>"

# ------------------------------------------------------------
# 2. Respaldo diario
# ------------------------------------------------------------
echo
echo "==> 2/3  Respaldo diario"
sudo cp "$AQUI/m5-backup" /etc/cron.daily/m5-backup
sudo chmod 755 /etc/cron.daily/m5-backup
sudo chown root:root /etc/cron.daily/m5-backup
sudo mkdir -p /var/backups/m5
sudo chmod 700 /var/backups/m5
verde "    Instalado en /etc/cron.daily/m5-backup"
echo "    Ahora respalda la base Y la carpeta de archivos subidos."

echo "    Probandolo (puede demorar unos segundos)..."
if sudo /etc/cron.daily/m5-backup; then
    verde "    Respaldo de prueba correcto:"
    sudo ls -lh /var/backups/m5 | tail -3
else
    rojo "    El respaldo de prueba fallo. Revisa:  journalctl -t m5-backup"
fi

# ------------------------------------------------------------
# 3. Bloque de correo en el .env
# ------------------------------------------------------------
echo
echo "==> 3/3  Correo saliente"

if sudo grep -q '^EMAIL_HOST=' "$ENV" 2>/dev/null; then
    verde "    El .env ya tiene configuracion de correo. No se toca."
else
    sudo cp "$ENV" "$ENV.bak-$(date +%Y%m%d-%H%M%S)"
    sudo tee -a "$ENV" >/dev/null <<'BLOQUE'

# ------------------------------------------------------------
# Correo saliente
#
# Mientras estas lineas esten comentadas, el sistema NO envia
# correos: los escribe en el log del servidor. Eso significa que
# recuperar contrasena y activar cuentas nuevas no funcionan para
# el usuario final.
#
# Para activarlo, pedirle a TI de M5 los datos del buzon
# adquisiciones@m-5.cl, descomentar estas lineas, completarlas y:
#     sudo systemctl restart gunicorn
#
# Google Workspace    -> EMAIL_HOST=smtp.gmail.com        EMAIL_PORT=587
# Microsoft 365       -> EMAIL_HOST=smtp.office365.com    EMAIL_PORT=587
# Hosting propio      -> lo que indique el proveedor
# ------------------------------------------------------------
#EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#EMAIL_HOST=
#EMAIL_PORT=587
#EMAIL_HOST_USER=adquisiciones@m-5.cl
#EMAIL_HOST_PASSWORD=
#EMAIL_USE_TLS=True
#DEFAULT_FROM_EMAIL=adquisiciones@m-5.cl
BLOQUE
    sudo chmod 600 "$ENV"
    verde "    Bloque agregado al .env, comentado y listo para completar."
fi

# ------------------------------------------------------------
echo
echo "############################################################"
verde "  Extras instalados."
echo "############################################################"
echo
echo "  Comprobacion rapida:"
ls -la /opt/m5/ | grep -E 'set_ip|actualizar' || true
echo
echo "  Lo que sigue, para dejar el OVA definitivo:"
echo "    1. Borra este /tmp/m5_extras y el sellar.sh viejo si quedo:"
echo "         rm -rf /tmp/m5_extras"
echo "    2. Vuelve a sellar:"
echo "         bash /opt/m5/sellar.sh"
echo "       (en el paso 3 puedes decir que NO: la clave ya se roto)"
echo "    3. Apaga, y en VirtualBox:"
echo "       Configuracion -> General -> Version: Ubuntu (64-bit)"
echo "       Archivo -> Exportar, OVF 2.0, quitar todas las MAC"
echo
