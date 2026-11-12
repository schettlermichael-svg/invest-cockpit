#!/bin/bash
# Tägliche Sicherung (Micky 12.11.2026): die Daten mit Geschichte nach GitHub, Zweig „daten“, Ordner sicherung/.
# Gesichert: Konferenzen (mit Lagebuch, Bilanz, Kostenbuch, Fragen), Logbuch des Rückenwinds, Protokoll des Laufs,
# Depot, Watchlists, Revier. NIE gesichert: Schlüssel (einstellungen/*schluessel*). Nicht gesichert: Kartentische
# (rund 12 MB je Tag, der Frühlauf rechnet sie neu) und Kurse.
# Wiederherstellen: Ordner sicherung/ aus dem Zweig „daten“ holen und nach /opt/invest-cockpit zurückkopieren
# (daten/… und einstellungen/… liegen dort unter denselben Pfaden). Läuft als root über sicherung.timer;
# aktualisieren.sh übernimmt Skript und Zeitplan aus dem Speicher.
APP=/opt/invest-cockpit
D=/opt/invest-daten
export GIT_SSH_COMMAND="ssh -i /root/.ssh/github_invest -o StrictHostKeyChecking=accept-new"
if [ ! -d $D/.git ]; then
  git clone -q git@github.com:schettlermichael-svg/invest-cockpit.git $D || exit 1
  cd $D && { git checkout -q daten 2>/dev/null || { git checkout -q --orphan daten && git rm -rqf . && git clean -qfdx; }; }
fi
cd $D || exit 1
git fetch -q origin daten 2>/dev/null && git reset -q --hard origin/daten
mkdir -p sicherung/daten/konferenz sicherung/daten/rueckenwind sicherung/daten/nachtlauf sicherung/einstellungen
cp -f $APP/daten/konferenz/*.json sicherung/daten/konferenz/ 2>/dev/null
cp -f $APP/daten/rueckenwind/logbuch.json sicherung/daten/rueckenwind/ 2>/dev/null
cp -f $APP/daten/nachtlauf/protokoll.json sicherung/daten/nachtlauf/ 2>/dev/null
for f in depot.json watchlists.json revier.csv; do cp -f $APP/einstellungen/$f sicherung/einstellungen/ 2>/dev/null; done
rm -f sicherung/einstellungen/*schluessel*            # Sicherheitsnetz: Schlüssel gehören nie nach GitHub
git add -A sicherung
git diff --cached --quiet && exit 0
git -c user.name="invest-cockpit-server" -c user.email="server@invest-cockpit" commit -qm "Sicherung $(date '+%d.%m.%Y %H:%M')"
git push -q origin HEAD:daten && echo "$(date '+%d.%m.%Y %H:%M') Sicherung nach GitHub (Zweig daten)" >> /var/log/invest-cockpit-update.log
