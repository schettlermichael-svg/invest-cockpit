#!/bin/bash
# Holt neuen Code aus GitHub und startet die App neu (spätestens 5 Minuten nach dem Hochladen).
# Aufgerufen von /usr/local/bin/invest-aktualisieren (Timer invest-update, alle 5 Minuten).
cd /opt/invest-cockpit || exit 0
# Zeitplan des Laufs aus dem Speicher übernehmen (12.11.2026: Frühlauf Di–Sa 6:05), sobald er sich unterscheidet
if [ -f werkzeuge/server/nachtlauf.timer ] && ! cmp -s werkzeuge/server/nachtlauf.timer /etc/systemd/system/nachtlauf.timer; then
  cp werkzeuge/server/nachtlauf.timer /etc/systemd/system/nachtlauf.timer
  systemctl daemon-reload && systemctl restart nachtlauf.timer
  echo "$(date '+%d.%m.%Y %H:%M') Zeitplan des Laufs übernommen: $(grep OnCalendar werkzeuge/server/nachtlauf.timer)" >> /var/log/invest-cockpit-update.log
fi
# Tägliche Sicherung (12.11.2026): Dienst und Zeitplan aus dem Speicher übernehmen, sobald sie sich unterscheiden
for u in sicherung.service sicherung.timer; do
  if [ -f werkzeuge/server/$u ] && ! cmp -s werkzeuge/server/$u /etc/systemd/system/$u; then
    cp werkzeuge/server/$u /etc/systemd/system/$u && NEU_SICHERUNG=1
  fi
done
if [ -n "$NEU_SICHERUNG" ]; then
  systemctl daemon-reload && systemctl enable -q --now sicherung.timer
  echo "$(date '+%d.%m.%Y %H:%M') Sicherung eingerichtet: $(grep OnCalendar werkzeuge/server/sicherung.timer)" >> /var/log/invest-cockpit-update.log
fi
# Zusätzliche Python-Pakete (14.11.2026: matplotlib und cairosvg für die Bilder des Chart-Prüfers), sobald die Liste sich ändert
if [ -f werkzeuge/server/pakete.txt ] && ! cmp -s werkzeuge/server/pakete.txt .venv/pakete.txt; then
  # cairosvg braucht die Systembibliothek Cairo (Chart der Titelseite als Bild für den Chart-Prüfer)
  dpkg -s libcairo2 >/dev/null 2>&1 || apt-get install -y -qq libcairo2 >/dev/null 2>&1
  .venv/bin/pip install -q -r werkzeuge/server/pakete.txt && cp werkzeuge/server/pakete.txt .venv/pakete.txt \
    && chown -R cockpit:cockpit .venv
  echo "$(date '+%d.%m.%Y %H:%M') Pakete installiert: $(tr '\n' ' ' < werkzeuge/server/pakete.txt)" >> /var/log/invest-cockpit-update.log
fi
# Watchlist-Abgleich (23.11.2026: in beide Richtungen): das Skript aus dem Speicher übernehmen, sobald es sich unterscheidet
if [ -f werkzeuge/server/watchlist_ablegen.sh ] && [ -f /etc/systemd/system/invest-watchlist.timer ] \
   && ! cmp -s werkzeuge/server/watchlist_ablegen.sh /usr/local/bin/invest-watchlist-ablegen; then
  install -m 755 werkzeuge/server/watchlist_ablegen.sh /usr/local/bin/invest-watchlist-ablegen
  echo "$(date '+%d.%m.%Y %H:%M') Watchlist-Abgleich übernommen (beide Richtungen)" >> /var/log/invest-cockpit-update.log
fi
# Zugangsausweis an der Haustür (17.11.2026), einmalig
[ -f werkzeuge/server/ausweis.sh ] && bash werkzeuge/server/ausweis.sh
git fetch -q origin main 2>/dev/null || exit 0
[ "$(git rev-parse HEAD 2>/dev/null)" = "$(git rev-parse origin/main)" ] && exit 0
# Kein Warten mehr auf den Schrank-Lauf (Micky 23.11.2026): er baut mit altem Code Seiten, die nach dem Update ohnehin
# veraltet sind; der Neustart beendet ihn, die App füllt den Schrank mit dem neuen Code neu. Der Nachtlauf hat einen
# eigenen Dienst und läuft weiter.
git reset -q --hard origin/main
chown -R cockpit:cockpit /opt/invest-cockpit
systemctl restart invest-cockpit
echo "$(date '+%d.%m.%Y %H:%M') Code aktualisiert auf $(git rev-parse --short HEAD)" >> /var/log/invest-cockpit-update.log
