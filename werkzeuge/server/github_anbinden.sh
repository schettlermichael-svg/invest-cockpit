#!/bin/bash
# Einmalig: Server mit GitHub verbinden, damit er neuen Code selbst holt. Aufruf auf dem Mac im Ordner InvestCockpit:
#   ssh root@2.31.188.241 'bash -s' < werkzeuge/server/github_anbinden.sh
# Am Ende steht ein Schlüssel (ssh-ed25519 …). Den in GitHub unter invest-cockpit → Settings → Deploy keys →
# „Add deploy key“ einfügen (Titel „Server“, Haken „Allow write access“ NICHT setzen).
set -e
ZIEL=/opt/invest-cockpit
mkdir -p /root/.ssh && chmod 700 /root/.ssh
[ -f /root/.ssh/github_invest ] || ssh-keygen -q -t ed25519 -N "" -f /root/.ssh/github_invest -C "invest-cockpit-server"
grep -q "Host github.com" /root/.ssh/config 2>/dev/null || cat >> /root/.ssh/config <<EOF
Host github.com
  IdentityFile /root/.ssh/github_invest
  StrictHostKeyChecking accept-new
EOF
git config --global --add safe.directory $ZIEL
cd $ZIEL
[ -d .git ] || git init -q -b main
git remote get-url origin >/dev/null 2>&1 || git remote add origin git@github.com:schettlermichael-svg/invest-cockpit.git
cat > /usr/local/bin/invest-aktualisieren <<'EOF'
#!/bin/bash
cd /opt/invest-cockpit || exit 0
git fetch -q origin main 2>/dev/null || exit 0
if [ "$(git rev-parse HEAD 2>/dev/null)" != "$(git rev-parse origin/main)" ]; then
  git reset -q --hard origin/main
  chown -R cockpit:cockpit /opt/invest-cockpit
  systemctl restart invest-cockpit
  echo "$(date '+%d.%m.%Y %H:%M') Code aktualisiert auf $(git rev-parse --short HEAD)" >> /var/log/invest-cockpit-update.log
fi
EOF
chmod +x /usr/local/bin/invest-aktualisieren
cat > /etc/systemd/system/invest-update.service <<EOF
[Unit]
Description=Invest Cockpit: neuen Code aus GitHub holen
[Service]
Type=oneshot
ExecStart=/usr/local/bin/invest-aktualisieren
EOF
cat > /etc/systemd/system/invest-update.timer <<EOF
[Unit]
Description=Invest Cockpit: alle 5 Minuten nach neuem Code schauen
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable -q --now invest-update.timer
echo
echo "✓ Server holt ab jetzt alle 5 Minuten neuen Code aus GitHub."
echo "  Diesen Schlüssel in GitHub als Deploy key eintragen (ohne Schreibrecht):"
echo
cat /root/.ssh/github_invest.pub
