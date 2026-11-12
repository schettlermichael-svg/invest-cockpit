#!/bin/bash
# Einrichtung des Servers (einmalig). Aufruf auf dem Mac im Ordner InvestCockpit:
#   ssh root@2.31.188.241 'bash -s' < werkzeuge/server/einrichten.sh
# Richtet ein: Zeitzone Berlin, automatische Sicherheitsupdates, Firewall, Python-Umgebung, Benutzer „cockpit“,
# die App als Dienst (immer an), den Nachtlauf (Mo–Fr 22:45) und die Haustür (https mit Passwort über Caddy).
# Am Ende stehen Adresse, Benutzername und Passwort da – einmal notieren (z. B. in der App „Passwörter“).
set -e
export DEBIAN_FRONTEND=noninteractive
IP=$(hostname -I | awk '{print $1}')
ADRESSE="${IP//./-}.sslip.io"
ZIEL=/opt/invest-cockpit

echo "1/7 System aktualisieren …"
timedatectl set-timezone Europe/Berlin
apt-get update -qq && apt-get upgrade -y -qq
apt-get install -y -qq python3-venv python3-pip unattended-upgrades ufw rsync git curl caddy >/dev/null
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "2/7 Firewall: nur SSH und Web …"
ufw allow 22/tcp >/dev/null; ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null

echo "3/7 Benutzer und Ordner …"
id cockpit >/dev/null 2>&1 || useradd --system --create-home --shell /bin/bash cockpit
mkdir -p $ZIEL && chown -R cockpit:cockpit $ZIEL

echo "4/7 Python-Umgebung (dauert ein paar Minuten) …"
sudo -u cockpit python3 -m venv $ZIEL/.venv
sudo -u cockpit $ZIEL/.venv/bin/pip install -q --upgrade pip
sudo -u cockpit $ZIEL/.venv/bin/pip install -q streamlit yfinance pandas numpy

echo "5/7 App als Dienst …"
cat > /etc/systemd/system/invest-cockpit.service <<EOF
[Unit]
Description=Invest Cockpit (Streamlit)
After=network-online.target
[Service]
User=cockpit
WorkingDirectory=$ZIEL
ExecStart=$ZIEL/.venv/bin/streamlit run app.py --server.port 8510 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF

echo "6/7 Nachtlauf Mo–Fr 22:45 …"
cat > /etc/systemd/system/nachtlauf.service <<EOF
[Unit]
Description=Invest Cockpit Nachtlauf
[Service]
Type=oneshot
User=cockpit
WorkingDirectory=$ZIEL
ExecStart=$ZIEL/.venv/bin/python -u werkzeuge/nachtlauf.py
EOF
cat > /etc/systemd/system/nachtlauf.timer <<EOF
[Unit]
Description=Frühlauf Di–Sa 6:05 (Berlin) – wie werkzeuge/server/nachtlauf.timer (seit 12.11.2026)
[Timer]
OnCalendar=Tue..Sat 06:05 Europe/Berlin
Persistent=true
[Install]
WantedBy=timers.target
EOF

echo "7/7 Haustür (https mit Passwort) …"
PASSWORT=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 16)
HASH=$(caddy hash-password --plaintext "$PASSWORT")
cat > /etc/caddy/Caddyfile <<EOF
$ADRESSE {
    basicauth {
        micky $HASH
    }
    reverse_proxy 127.0.0.1:8510
}
EOF
systemctl daemon-reload
systemctl enable -q invest-cockpit nachtlauf.timer
systemctl restart caddy
systemctl start nachtlauf.timer

echo
echo "✓ Server eingerichtet."
echo "  Adresse:  https://$ADRESSE"
echo "  Benutzer: micky"
echo "  Passwort: $PASSWORT"
echo "  (Die App startet, sobald die Daten übertragen sind: werkzeuge/server/uebertragen.sh)"
