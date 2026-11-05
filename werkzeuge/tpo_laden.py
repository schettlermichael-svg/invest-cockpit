"""30-Minuten-Kerzen für alle Titel des Reviers laden (Market Profile), von heute rückwärts bis 2 Jahre.

Aufruf im Ordner InvestCockpit:
    python3 werkzeuge/tpo_laden.py              Abendlauf: neuer Tag über Yahoo (Minuten), dann Massive in Durchgängen für
                                                Lücken und neue Titel (abbrechen und neu starten jederzeit)
    python3 werkzeuge/tpo_laden.py fortsetzen   nur der neue Tag über Yahoo
    python3 werkzeuge/tpo_laden.py kartentisch  nur Tageskurse und Kartentisch für die Übersicht

Massive liefert je Anfrage höchstens 50.000 Minuten – bei großen Titeln rund 2 Monate. Ein Durchgang macht eine Anfrage je
Titel und füllt jeweils die jüngste Lücke; nach dem ersten Durchgang hat jeder Titel die letzten Wochen (genug für Zone,
Zustand und Setup), jeder weitere Durchgang reicht weiter zurück. Der kostenlose Plan erlaubt 5 Anfragen je Minute: ein
Durchgang über rund 1.900 Titel dauert etwa 6,5 Stunden; Titel, die schon vollständig sind, fallen heraus.
"""
import os
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import tpo_daten  # noqa: E402

def titel():
    """Gesamtmarkt, Revier, Watchlists und auf der Titelseite geöffnete Titel (tpo_daten.lauf_liste). Vorher wandern
    Dateien gelöschter Titel nach _to_delete/tpo/."""
    weg = tpo_daten.aufraeumen()
    if weg:
        print(f"nicht mehr im Lauf (gelöscht), archiviert: {', '.join(weg)}", flush=True)
    return tpo_daten.lauf_liste()


def _neuester(t):
    df = tpo_daten.lesen(t)
    return df.index[-1] if df is not None else pd.Timestamp(0)


def main():
    tpo_daten._mehr_dateien()
    alle = titel()
    if len(sys.argv) > 1 and sys.argv[1] == "kartentisch":   # nur Tageskurse und Kartentisch (z. B. tagsüber)
        sys.path.insert(0, os.path.join(HIER, "..", "oberflaeche"))
        import daten  # noqa: E402
        import kartentisch  # noqa: E402
        print(f"Tageskurse für {len(alle)} Titel …", flush=True)
        print(f"  {daten.kurse_viele(alle + [daten.INDEX])} Titel aktualisiert", flush=True)
        tisch = kartentisch.rechnen(alle)
        print(f"fertig: {len(tisch['titel'])} Titel in Reihen, {len(tisch['neu'])} Neuigkeiten")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "fortsetzen":
        mit = [t for t in alle if tpo_daten.lesen(t) is not None or tpo_daten.auslaendisch(t)]
        print(f"Fortsetzung über Yahoo für {len(mit)} Titel …", flush=True)
        erg = tpo_daten.fortsetzen(mit)
        print(f"fertig: {sum(1 for k in erg.values() if k > 0)} Titel um neue Kerzen ergänzt")
        return
    # Zuerst der neue Tag für alle Titel mit Kerzen über Yahoo (viele Titel je Anfrage, wenige Minuten); Massive nur
    # noch für Lücken und neue Titel – sonst kostete der neue Tag jeden Abend eine Anfrage je Titel (6,5 Stunden)
    mit = [t for t in alle if tpo_daten.lesen(t) is not None or tpo_daten.auslaendisch(t)]   # Ausland nur Yahoo
    if mit:
        print(f"Neuer Tag über Yahoo für {len(mit)} Titel …", flush=True)
        try:
            erg = tpo_daten.fortsetzen(mit)
            print(f"  {sum(1 for k in erg.values() if k > 0)} Titel ergänzt", flush=True)
        except Exception as e:                   # ohne Yahoo holt Massive den Tag in den Durchgängen
            print(f"  Yahoo nicht erreichbar ({e}) – Massive übernimmt", flush=True)
    # Tageskurse aller Titel (Pakete zu 50) und dann der Kartentisch für die Übersicht – vor den langen Massive-Durchgängen,
    # damit die Übersicht morgens steht, auch wenn die Erstbefüllung noch Stunden läuft
    sys.path.insert(0, os.path.join(HIER, "..", "oberflaeche"))
    import daten  # noqa: E402
    import kartentisch  # noqa: E402
    print(f"Tageskurse für {len(alle)} Titel …", flush=True)
    try:
        print(f"  {daten.kurse_viele(alle + [daten.INDEX])} Titel aktualisiert", flush=True)
        print("Kartentisch rechnen …", flush=True)
        tisch = kartentisch.rechnen(alle)
        print(f"  fertig: {len(tisch['titel'])} Titel in Reihen, {len(tisch['neu'])} Neuigkeiten", flush=True)
    except Exception as e:                       # der Kartentisch darf die Erstbefüllung nicht aufhalten
        print(f"  Kartentisch nicht gerechnet: {e}", flush=True)
    durchgang = 0
    while True:
        kal = tpo_daten._kalender()
        offen = [t for t in alle if not tpo_daten.auslaendisch(t) and tpo_daten.luecke(t, kal)]   # Ausland: Yahoo
        if not offen:
            print("fertig: alle Titel vollständig (2 Jahre)")
            return
        durchgang += 1
        offen.sort(key=_neuester)                # Titel ohne neueste Kerzen zuerst
        print(f"Durchgang {durchgang}: {len(offen)} Titel mit Lücke, etwa {len(offen) * 12.5 / 3600:.1f} Stunden",
              flush=True)
        beginn = time.time()
        for i, t in enumerate(offen, 1):
            try:
                text = tpo_daten.schritt(t, kal)
                df = tpo_daten.lesen(t)
                if df is not None:
                    text += f" · gespeichert ab {df.index[0]:%d.%m.%Y}"
            except Exception as e:               # einzelner Titel scheitert: weiter mit dem nächsten
                text = f"Fehler: {e}"
            rest = (time.time() - beginn) / i * (len(offen) - i) / 60
            print(f"[{durchgang}·{i}/{len(offen)}] {t}: {text} · noch etwa {rest:.0f} Min.", flush=True)


if __name__ == "__main__":
    main()
