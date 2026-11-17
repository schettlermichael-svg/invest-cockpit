#!/bin/bash
# Zugangsausweis an der Haustür (Micky 17.11.2026: ntfy fragte bei jedem Tipp zweimal nach dem Passwort – der kleine
# Browser von ntfy merkt sich die Passwortsperre nicht, Streamlit öffnet Seite und Live-Leitung). Nach dem ersten
# richtigen Passwort gibt Caddy dem Gerät einen geheimen Ausweis (Cookie ic_zugang, 1 Jahr, nur über https, für Skripte
# unlesbar); mit ihm öffnet die Tür ohne Frage. Passwort und Nutzer bleiben, wie sie sind (aus der alten Caddyfile).
# Nur einmal: steht der Ausweis schon in der Caddyfile, tut das Skript nichts. Vor dem Umschalten prüft Caddy die neue
# Einstellung; ist sie fehlerhaft, bleibt die alte Tür. Aufgerufen von aktualisieren.sh und einrichten.sh (als root).
DATEI=/etc/caddy/Caddyfile
[ -f "$DATEI" ] || exit 0
grep -q "ic_zugang" "$DATEI" && exit 0
ADR=$(awk 'NF{print $1; exit}' "$DATEI")
NUTZER_HASH=$(awk '/basicauth/{f=1;next} f&&/}/{f=0} f&&NF{print $1" "$2; exit}' "$DATEI")
# nur die Tür aus einrichten.sh (6 Zeilen: Adresse, basicauth, Nutzer, zwei Klammern, reverse_proxy) – jede andere,
# von Hand geänderte Caddyfile bleibt unberührt, damit nichts verloren geht
ZEILEN=$(grep -c . "$DATEI")
if [ -z "$ADR" ] || [ -z "$NUTZER_HASH" ] || [ "$ZEILEN" != "6" ] || ! grep -q "reverse_proxy 127.0.0.1:8510" "$DATEI"; then
  echo "$(date '+%d.%m.%Y %H:%M') Ausweis: Caddyfile nicht wie erwartet – Tür unverändert" >> /var/log/invest-cockpit-update.log
  exit 0
fi
AUSWEIS=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 40)
NEU=$(mktemp)
cat > "$NEU" <<EOF
$ADR {
    @ausweis header Cookie *ic_zugang=$AUSWEIS*
    handle @ausweis {
        reverse_proxy 127.0.0.1:8510
    }
    handle {
        route {
            basicauth {
                $NUTZER_HASH
            }
            header Set-Cookie "ic_zugang=$AUSWEIS; Max-Age=31536000; Path=/; Secure; HttpOnly; SameSite=Lax"
            reverse_proxy 127.0.0.1:8510
        }
    }
}
EOF
if caddy validate --config "$NEU" --adapter caddyfile >/dev/null 2>&1; then
  cp "$DATEI" "$DATEI.vor-ausweis"
  install -m 640 -o root -g caddy "$NEU" "$DATEI" && systemctl reload caddy \
    && echo "$(date '+%d.%m.%Y %H:%M') Ausweis an der Haustür eingerichtet (1 Jahr)" >> /var/log/invest-cockpit-update.log
else
  echo "$(date '+%d.%m.%Y %H:%M') Ausweis: neue Caddyfile ungültig – Tür unverändert" >> /var/log/invest-cockpit-update.log
fi
rm -f "$NEU"
