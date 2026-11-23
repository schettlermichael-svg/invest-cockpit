#!/bin/bash
# Einmalig: Der Server legt alle 10 Minuten die Listen der App (einstellungen/watchlists.json) auf den Zweig „daten“
# des GitHub-Speichers und übernimmt vorher Änderungen aus TradingView (von_tv.json). Die Claude-Aufgabe (stündlich
# 8–23 Uhr) gleicht in beide Richtungen ab (seit 23.11.2026). Voraussetzung: Deploy key des Servers MIT Schreibrecht.
# Das Skript selbst (watchlist_ablegen.sh) hält aktualisieren.sh danach von allein auf dem Stand des Speichers.
# Aufruf auf dem Mac im Ordner InvestCockpit:  ssh root@2.31.188.241 'bash -s' < werkzeuge/server/watchlist_ablegen_einrichten.sh
set -e
install -m 755 "$(dirname "$0")/watchlist_ablegen.sh" /usr/local/bin/invest-watchlist-ablegen 2>/dev/null \
  || install -m 755 /opt/invest-cockpit/werkzeuge/server/watchlist_ablegen.sh /usr/local/bin/invest-watchlist-ablegen
chmod +x /usr/local/bin/invest-watchlist-ablegen
cat > /etc/systemd/system/invest-watchlist.service <<EOF
[Unit]
Description=Invest Cockpit: Watchlists nach GitHub (Zweig daten)
[Service]
Type=oneshot
Environment=HOME=/root
Environment="GIT_SSH_COMMAND=ssh -i /root/.ssh/github_invest -o StrictHostKeyChecking=accept-new"
ExecStart=/usr/local/bin/invest-watchlist-ablegen
EOF
cat > /etc/systemd/system/invest-watchlist.timer <<EOF
[Unit]
Description=Invest Cockpit: Watchlists alle 10 Minuten ablegen
[Timer]
OnBootSec=3min
OnUnitActiveSec=10min
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable -q --now invest-watchlist.timer
systemctl start invest-watchlist.service || true
echo "✓ Server legt die Watchlists alle 10 Minuten auf den Zweig „daten“."
tail -1 /var/log/invest-cockpit-update.log
