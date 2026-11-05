#!/bin/zsh
# Code vom Mac auf den Server bringen und die App neu starten. Aufruf im Ordner InvestCockpit:
#   zsh werkzeuge/server/uebertragen.sh          nur Code (Standard): Daten, Watchlists, Depot und Konto auf dem
#                                                Server bleiben unberührt – der Server ist das Original
#   zsh werkzeuge/server/uebertragen.sh --alles  einmalig alles (Erstbefüllung 05.11.2026 ist erledigt)
SERVER=root@2.31.188.241
ZIEL=/opt/invest-cockpit
cd "$(dirname "$0")/../.." || exit 1
AUSSER=(--exclude '__pycache__' --exclude '_to_delete' --exclude 'zugang' --exclude '.venv' --exclude '.DS_Store')
if [[ "$1" != "--alles" ]]; then
  AUSSER+=(--exclude 'daten' --exclude 'einstellungen/watchlists.json' --exclude 'einstellungen/depot.json'
           --exclude 'einstellungen/revier.csv')
fi
rsync -az "${AUSSER[@]}" ./ "$SERVER:$ZIEL/" || exit 1
ssh $SERVER "chown -R cockpit:cockpit $ZIEL && systemctl restart invest-cockpit && systemctl is-active invest-cockpit" \
  && echo "✓ übertragen, App läuft"
