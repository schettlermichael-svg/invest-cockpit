#!/bin/bash
# Alle 10 Minuten (invest-watchlist.timer, als root): erst Änderungen aus TradingView übernehmen (von_tv.json auf dem
# Zweig „daten“, abgelegt von der stündlichen Claude-Aufgabe), dann die Listen der App (einstellungen/watchlists.json)
# auf den Zweig „daten“ legen. Wird von aktualisieren.sh nach /usr/local/bin/invest-watchlist-ablegen übernommen.
D=/opt/invest-daten
APP=/opt/invest-cockpit
QUELLE=$APP/einstellungen/watchlists.json
LOG=/var/log/invest-cockpit-update.log
[ -f "$QUELLE" ] || exit 0
if [ ! -d $D/.git ]; then
  git clone -q git@github.com:schettlermichael-svg/invest-cockpit.git $D || exit 0
  cd $D
  if git ls-remote --exit-code -q origin daten >/dev/null; then git checkout -q daten
  else git checkout -q --orphan daten && git rm -rqf . && git clean -qfdx; fi
fi
cd $D
git fetch -q origin daten 2>/dev/null && git reset -q --hard origin/daten
TEXT="Watchlists $(date '+%d.%m.%Y %H:%M')"
if [ -f $D/von_tv.json ]; then
  ERG=$(runuser -u cockpit -- $APP/.venv/bin/python $APP/werkzeuge/von_tv_anwenden.py $D/von_tv.json) || exit 0
  [ -n "$ERG" ] && echo "$(date '+%d.%m.%Y %H:%M') $ERG" >> $LOG
  git rm -q von_tv.json
  TEXT="$TEXT (aus TradingView übernommen)"
fi
cp "$QUELLE" $D/watchlists.json
git add watchlists.json
git diff --cached --quiet && exit 0
git -c user.name="invest-cockpit-server" -c user.email="server@invest-cockpit" commit -qm "$TEXT"
git push -q origin HEAD:daten && echo "$(date '+%d.%m.%Y %H:%M') Watchlists abgelegt" >> $LOG
