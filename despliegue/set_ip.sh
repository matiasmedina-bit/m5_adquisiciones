#!/usr/bin/env bash
# ============================================================
#  Appliance M5 - Ajustar la IP del sistema
#
#  Al importar el OVA en otra maquina la VM toma una IP distinta,
#  y Django rechaza todo con DisallowedHost hasta que esa IP este
#  en ALLOWED_HOSTS. Este script lo resuelve en un comando.
#
#  Uso:
#     bash /opt/m5/set_ip.sh                    -> detecta la IP sola
#     bash /opt/m5/set_ip.sh 10.0.0.25          -> la fija a mano
#     bash /opt/m5/set_ip.sh 10.0.0.25 26.1.2.3 -> varias direcciones
#
#  La segunda forma con varias direcciones es para cuando al sistema
#  se entra por mas de una via: la IP de la red local de la empresa y
#  la IP con que lo ven los equipos conectados por VPN desde terreno.
#  Si falta una de las dos, Django rechaza esa via con DisallowedHost
#  aunque la red este bien armada.
#
#  Se puede correr las veces que haga falta: no duplica entradas.
# ============================================================
set -euo pipefail

ENV=/opt/m5/app/.env
FIJAS="m5-app,localhost,127.0.0.1"

echo
echo "############################################################"
echo "  Appliance M5 - ajuste de IP"
echo "############################################################"
echo

# ------------------------------------------------------------
# 1. Que IP usamos
# ------------------------------------------------------------
if [ $# -ge 1 ]; then
    # Acepta "10.0.0.25 26.1.2.3" y tambien "10.0.0.25,26.1.2.3"
    ENTRADA=$(echo "$*" | tr ' ,' '\n\n')
else
    # La IP con la que esta maquina sale a la red
    ENTRADA=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
    if [ -z "${ENTRADA:-}" ]; then
        ENTRADA=$(hostname -I | awk '{print $1}')
    fi
fi

IP=""
for DIR in $ENTRADA; do
    if ! echo "$DIR" | grep -qE '^[0-9]{1,3}(\.[0-9]{1,3}){3}$'; then
        echo "ERROR: '$DIR' no parece una direccion IPv4."
        echo "       Mira cual es con:  ip -4 addr"
        echo "       y vuelve a correr:  bash /opt/m5/set_ip.sh <ip> [<ip>...]"
        exit 1
    fi
    IP="${IP:+$IP,}$DIR"
done

# La primera es la que se usa para comprobar al final
PRIMERA=$(echo "$IP" | cut -d, -f1)

echo "==> 1/4  Direcciones del sistema: $IP"

# ------------------------------------------------------------
# 2. Respaldo del .env
# ------------------------------------------------------------
if [ ! -f "$ENV" ]; then
    echo "ERROR: no existe $ENV"
    exit 1
fi
SELLO=$(date +%Y%m%d-%H%M%S)
sudo cp "$ENV" "$ENV.bak-$SELLO"
sudo chmod 600 "$ENV.bak-$SELLO"
echo "==> 2/4  Respaldo: $ENV.bak-$SELLO"

# ------------------------------------------------------------
# 3. Reescribir ALLOWED_HOSTS
#    CSRF_TRUSTED_ORIGINS se deduce solo en settings.py, asi que
#    esa linea se elimina: si quedara escrita a mano, mandaria
#    ella y volveria a dejar el sistema con error 403.
# ------------------------------------------------------------
sudo sed -i '/^ALLOWED_HOSTS=/d;/^CSRF_TRUSTED_ORIGINS=/d' "$ENV"
echo "ALLOWED_HOSTS=$IP,$FIJAS" | sudo tee -a "$ENV" >/dev/null
sudo chmod 600 "$ENV"
echo "==> 3/4  ALLOWED_HOSTS=$IP,$FIJAS"

# ------------------------------------------------------------
# 4. Reiniciar y comprobar
# ------------------------------------------------------------
echo "==> 4/4  Reiniciando el servicio"
sudo systemctl restart gunicorn
sleep 3

CODIGO=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $PRIMERA" "http://127.0.0.1/" || echo "000")

echo
if [ "$CODIGO" = "200" ] || [ "$CODIGO" = "302" ]; then
    echo "  LISTO. El sistema responde HTTP $CODIGO."
    echo
    echo "  Abrelo desde cualquier equipo de la red:"
    for DIR in $(echo "$IP" | tr ',' ' '); do
        echo "     http://$DIR/"
    done
    echo
else
    echo "  El sistema respondio HTTP $CODIGO, que no es lo esperado."
    echo
    echo "  Revisa:"
    echo "     sudo systemctl status gunicorn"
    echo "     sudo journalctl -u gunicorn -n 40 --no-pager"
    echo
    echo "  Para volver al .env anterior:"
    echo "     sudo cp $ENV.bak-$SELLO $ENV && sudo systemctl restart gunicorn"
    echo
    exit 1
fi
