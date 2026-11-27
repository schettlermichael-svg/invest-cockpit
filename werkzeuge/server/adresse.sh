#!/bin/bash
# Eigene Adresse (Micky 27.11.2026): die App auch unter invest.themaraga-group.de. Wartet, bis der A-Eintrag bei Strato
# auf diesen Server zeigt; dann kommt der Name in die erste Zeile der Caddyfile neben die sslip-Adresse (beide gelten,
# Passwort und Ausweis bleiben), Caddy holt das https-Zertifikat selbst. Vor dem Umschalten prüft Caddy die neue
# Einstellung; ist sie fehlerhaft, bleibt die alte Tür. Nur einmal. Aufgerufen von aktualisieren.sh (als root).
# Gemeinsamer Server mit dem MARAGA CRM (crm.themaraga-group.de, Port 8100, eigener angehängter Block in derselben
# Caddyfile): geändert wird nur die erste Zeile unseres eigenen Blocks (die sslip-Adresse), der CRM-Block bleibt unberührt.
NAME=invest.themaraga-group.de
DATEI=/etc/caddy/Caddyfile
LOG=/var/log/invest-cockpit-update.log
[ -f "$DATEI" ] || exit 0
grep -q "$NAME" "$DATEI" && exit 0
ERSTE=$(awk 'NF{print; exit}' "$DATEI")
ADR=$(echo "$ERSTE" | awk '{print $1}')
case "$ADR" in *.sslip.io) ;; *) exit 0 ;; esac
IP=$(echo "${ADR%.sslip.io}" | tr '-' '.')
resolvectl flush-caches 2>/dev/null                 # keine alte „gibt es nicht“-Antwort aus dem Zwischenspeicher
DNS=$(getent ahostsv4 "$NAME" | awk '{print $1; exit}')
[ "$DNS" = "$IP" ] || exit 0                       # A-Eintrag noch nicht da (oder zeigt woanders hin): warten
NEU=$(mktemp)
awk -v alt="$ERSTE" -v neu="$ADR, $NAME {" 'BEGIN{d=0} !d && $0==alt {print neu; d=1; next} {print}' "$DATEI" > "$NEU"
if caddy validate --config "$NEU" --adapter caddyfile >/dev/null 2>&1; then
  cp "$DATEI" "$DATEI.vor-adresse"
  install -m 640 -o root -g caddy "$NEU" "$DATEI" && systemctl reload caddy \
    && echo "$(date '+%d.%m.%Y %H:%M') Eigene Adresse eingerichtet: https://$NAME" >> "$LOG"
else
  echo "$(date '+%d.%m.%Y %H:%M') Eigene Adresse: neue Caddyfile ungültig – Tür unverändert" >> "$LOG"
fi
rm -f "$NEU"
