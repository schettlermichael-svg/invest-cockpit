#!/bin/zsh
# Ordner InvestCockpit vom Mac auf den Server kopieren (Code, Daten, Einstellungen) und die App neu starten.
# Aufruf auf dem Mac im Ordner InvestCockpit:  zsh werkzeuge/server/uebertragen.sh
# Beim ersten Mal alles (1,3 GB, einige Minuten); danach nur Geändertes.
SERVER=root@2.31.188.241
ZIEL=/opt/invest-cockpit
cd "$(dirname "$0")/../.." || exit 1
rsync -az --exclude '__pycache__' --exclude '_to_delete' --exclude 'zugang' --exclude '.venv' --exclude '.DS_Store' \
  ./ "$SERVER:$ZIEL/" || exit 1
ssh $SERVER "chown -R cockpit:cockpit $ZIEL && systemctl restart invest-cockpit && systemctl is-active invest-cockpit" \
  && echo "✓ übertragen, App läuft"
