#!/bin/bash
# Holt neuen Code aus GitHub und startet die App neu – aber NICHT, solange ein Knopf-Lauf
# (Kartentisch neu rechnen oder Konferenz) läuft: der Neustart würde ihn abschießen. Dann beim nächsten Mal (5 Min).
# Aufgerufen von /usr/local/bin/invest-aktualisieren (Timer invest-update, alle 5 Minuten).
cd /opt/invest-cockpit || exit 0
git fetch -q origin main 2>/dev/null || exit 0
[ "$(git rev-parse HEAD 2>/dev/null)" = "$(git rev-parse origin/main)" ] && exit 0
if .venv/bin/python werkzeuge/nachtlauf.py --laeuft 2>/dev/null; then
  echo "$(date '+%d.%m.%Y %H:%M') neuer Code wartet – es läuft gerade ein Lauf" >> /var/log/invest-cockpit-update.log
  exit 0
fi
git reset -q --hard origin/main
chown -R cockpit:cockpit /opt/invest-cockpit
systemctl restart invest-cockpit
echo "$(date '+%d.%m.%Y %H:%M') Code aktualisiert auf $(git rev-parse --short HEAD)" >> /var/log/invest-cockpit-update.log
