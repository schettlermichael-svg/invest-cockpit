#!/bin/bash
# Einmalig: Der Server legt alle 10 Minuten die Watchlists der App (einstellungen/watchlists.json) auf den Zweig „daten“
# des GitHub-Speichers. Von dort trägt die Claude-Aufgabe (stündlich 8–23 Uhr) Änderungen in TradingView ein
# (nur App → TradingView). Voraussetzung: Deploy key des Servers MIT Schreibrecht.
# Aufruf auf dem Mac im Ordner InvestCockpit:  ssh root@2.31.188.241 'bash -s' < werkzeuge/server/watchlist_ablegen_einrichten.sh
set -e
cat > /usr/local/bin/invest-watchlist-ablegen <<'EOF'
#!/bin/bash
D=/opt/invest-daten
QUELLE=/opt/invest-cockpit/einstellungen/watchlists.json
[ -f "$QUELLE" ] || exit 0
if [ ! -d $D/.git ]; then
  git clone -q git@github.com:schettlermichael-svg/invest-cockpit.git $D || exit 0
  cd $D
  if git ls-remote --exit-code -q origin daten >/dev/null; then git checkout -q daten
  else git checkout -q --orphan daten && git rm -rqf . && git clean -qfdx; fi
fi
cd $D
git fetch -q origin daten 2>/dev/null && git reset -q --hard origin/daten
cp "$QUELLE" $D/watchlists.json
git add watchlists.json
git diff --cached --quiet && exit 0
git -c user.name="invest-cockpit-server" -c user.email="server@invest-cockpit" commit -qm "Watchlists $(date '+%d.%m.%Y %H:%M')"
git push -q origin HEAD:daten && echo "$(date '+%d.%m.%Y %H:%M') Watchlists abgelegt" >> /var/log/invest-cockpit-update.log
EOF
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
