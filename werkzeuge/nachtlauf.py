"""Nachtlauf (Schritt 8, 04.11.2026): alle Daten aller Titel, jeden Handelsabend, ohne Ausnahme – mit Protokoll.

Start automatisch über launchd (werkzeuge/nachtlauf_einrichten.sh, Mo–Fr 22:45 Uhr) oder von Hand im Ordner InvestCockpit:
    caffeinate -i python3 werkzeuge/nachtlauf.py
Schritte (jeder für sich abgesichert; scheitert einer, laufen die übrigen weiter und das Protokoll meldet ihn):
  1. Massive: Tageskurse aller US-Aktien des letzten Handelstags und Splits (Rudel, Kursverwandte, Themen-Gruppen, RS-Rang)
  2. Rudel, Kursverwandte und Themen-Gruppen neu rechnen
  3. 30-Minuten-Kerzen des neuen Tages über Yahoo (Wertzonen), Ausland inklusive
  4. Tageskurse aller Titel (Revier, Watchlists, Positionen, geöffnete Titel, Gesamtmarkt) und Wechselkurse
  5. Lage: Wirtschaftswetter, Pendel, Marktbreite, Frontkarte, Marktrichtung (Übersicht einmal bauen = alle Quellen frisch)
  6. freitags Revier-Pflege (kern/revier_pflege.py: Zugänge nach den Revier-Regeln, Abgänge nur gemeldet)
     und TradingView-Kennzahlen (Screener-Schnittstelle, ohne Login): Aktienzahl, Rückkäufe, Margen, Zahlentermine
  7. Kartentisch (Erkennung aller Titel, volle Titelseite der Titel in Reihen und Watchlists, Fundamentdaten inklusive)
  8. Massive-Durchgänge für Lücken der 30-Minuten-Kerzen bis spätestens 07:00 Uhr (Erstbefüllung, neue Titel)
Protokoll: daten/nachtlauf/protokoll.json – die Übersicht zeigt daraus die Datenampel im Kopf. Am Ende eine
Mitteilung auf dem Mac mit den Neuigkeiten.
"""
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, os.path.join(HIER, "..", "oberflaeche"))
sys.path.insert(0, HIER)
from dateien import json_schreiben  # noqa: E402

PROTOKOLL = os.path.join(HIER, "..", "daten", "nachtlauf", "protokoll.json")
TISCH_PROTOKOLL = os.path.join(HIER, "..", "daten", "nachtlauf", "tisch_lauf.json")   # Knopf in der Übersicht
TISCH_LOG = os.path.join(HIER, "..", "daten", "nachtlauf", "tisch_lauf.log")
SEITEN_PROTOKOLL = os.path.join(HIER, "..", "daten", "nachtlauf", "seiten_lauf.json")   # Schrank nach Änderungen
SEITEN_LOG = os.path.join(HIER, "..", "daten", "nachtlauf", "seiten_lauf.log")
SCHLUSS = (7, 0)              # Massive-Durchgänge enden morgens, damit der Mac tagsüber frei ist


def _schreiben(p, datei=PROTOKOLL):
    os.makedirs(os.path.dirname(datei), exist_ok=True)
    json_schreiben(datei, p, ensure_ascii=False, indent=1)


def _mitteilung(text):
    try:
        subprocess.run(["osascript", "-e", f'display notification "{text}" with title "Invest Cockpit"'], timeout=10)
    except Exception:  # noqa: BLE001 – ohne Mitteilung läuft alles weiter
        pass


def main(nur_tisch=False):
    """nur_tisch (Knopf „Kartentisch neu rechnen“ in der Übersicht): nur Ränge, Kartentisch und Lage mit den
    vorhandenen Kursen – eigenes Protokoll, die Datenampel des Nachtlaufs bleibt unberührt."""
    import tpo_daten
    import tpo_laden
    tpo_daten._mehr_dateien()
    datei = TISCH_PROTOKOLL if nur_tisch else PROTOKOLL
    p = {"start": datetime.now().strftime("%d.%m.%Y %H:%M"), "ende": None, "schritte": [], "pid": os.getpid()}
    _schreiben(p, datei)

    def schritt(name, f):
        t0 = time.time()
        print(f"{datetime.now():%H:%M} {name} …", flush=True)
        try:
            text = f() or "ok"
            ok = True
        except Exception as e:  # noqa: BLE001
            text, ok = f"{type(e).__name__}: {e}", False
            traceback.print_exc()
        p["schritte"].append({"name": name, "ok": ok, "text": str(text)[:300], "sekunden": round(time.time() - t0)})
        _schreiben(p, datei)
        print(f"    {'✓' if ok else '✗'} {text}", flush=True)
        return ok

    alle = tpo_laden.titel()

    def massive_tage():
        import massive
        tage = massive.letzte_tage(495)
        von, bis = tage[-5][0], tage[-1][0]
        massive.splits_zeitraum(von, bis)
        return f"bis {bis:%d.%m.%Y}"

    def rudel_neu():
        import rudel
        rudel._laden()
        return f"Stand {rudel.stand():%d.%m.%Y}"

    def kerzen_neu():
        mit = [t for t in alle if tpo_daten.lesen(t) is not None or tpo_daten.auslaendisch(t)]
        erg = tpo_daten.fortsetzen(mit)
        return f"{sum(1 for k in erg.values() if k > 0)} von {len(mit)} Titeln ergänzt"

    def tageskurse():
        import daten
        import depot
        n = daten.kurse_viele(alle + [daten.INDEX] + [p_["ticker"] for p_ in depot.laden()["positionen"]])
        for w in {depot.waehrung(t) for t in alle} - {"EUR"}:
            depot.fx(w)
        return f"{n} Titel"

    def lage():
        import uebersicht
        uebersicht.ablegen(uebersicht.seite_uebersicht())   # die App zeigt sie morgens sofort
        return "Übersicht gebaut"

    def tisch():
        import kartentisch
        t_ = kartentisch.rechnen(alle, melden=lambda x: print(x, flush=True))
        p["neu"] = len(t_["neu"])
        p["reihen"] = {k: sum(1 for x in t_["titel"].values() if x.get("reihe") == k) for k in ("m_spitze", "k_breakout", "k_ep", "k_ermuedung", "vcp", "flagge")}
        return f"{len(t_['titel'])} Titel auf dem Tisch, {len(t_['neu'])} Neuigkeiten"

    def raenge():
        import fuehrer_rang
        import rs_rang
        r_, stand_ = rs_rang.raenge()
        f_, _ = fuehrer_rang.raenge()               # vor dem Kartentisch: die Prozesse lesen dann nur die Datei
        return f"RS-Rang {len(r_)}, Führer-Rang {len(f_)} Titel (Stand {stand_})"

    def revier():
        import revier_pflege
        return revier_pflege.pflegen()

    def tradingview():
        import tv_kennzahlen
        return tv_kennzahlen.aktualisieren(alle)

    def rueckenwind_():
        import rueckenwind
        e = rueckenwind.rechnen(netz=True)
        from collections import Counter
        n = Counter(x["stufe"] for x in e["titel"].values())
        return (f"Stand {e['stand']}: Entsteht {n.get('Entsteht', 0)}, Läuft {n.get('Läuft', 0)}, "
                f"Ermüdet {n.get('Ermüdet', 0)}, Abfluss {n.get('Abfluss', 0)}")

    if nur_tisch:
        schritt("RS-Rang, Führer-Rang (Kullamägi)", raenge)
        schritt("Kartentisch", tisch)
        schritt("Lage (Wetter, Pendel, Breite, Front, Marktrichtung)", lage)
        schritt("Rückenwind (RS-Dynamik, Geldfluss, Zahlen)", rueckenwind_)
        p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        _schreiben(p, datei)
        return

    schritt("Massive: Tageskurse und Splits", massive_tage)
    schritt("Rudel, Kursverwandte, Themen-Gruppen", rudel_neu)
    schritt("30-Minuten-Kerzen (Yahoo)", kerzen_neu)
    schritt("Tageskurse und Wechselkurse", tageskurse)
    if datetime.now().weekday() == 4:            # freitags: Revier-Pflege (Zugänge, Abgänge gemeldet)
        schritt("Revier-Pflege", revier)
    schritt("TradingView-Kennzahlen", tradingview)
    schritt("RS-Rang, Führer-Rang (Kullamägi)", raenge)
    schritt("Kartentisch", tisch)
    schritt("Lage (Wetter, Pendel, Breite, Front, Marktrichtung)", lage)   # nach dem Tisch: liest dessen Barometer
    schritt("Rückenwind (RS-Dynamik, Geldfluss, Zahlen)", rueckenwind_)
    p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    _schreiben(p)
    fehler = [s["name"] for s in p["schritte"] if not s["ok"]]
    _mitteilung((f"⚠ gescheitert: {', '.join(fehler)}. " if fehler else "Lage steht. ")
                + f"{(p.get('reihen') or {}).get('m_spitze', 0)} Spitzenkandidaten · {p.get('neu', 0)} Neuigkeiten")

    # Massive-Durchgänge für Lücken (Erstbefüllung, neue Titel) bis morgens
    durchgang = 0
    while datetime.now().hour < 12 and (datetime.now().hour, datetime.now().minute) < SCHLUSS or datetime.now().hour >= 18:
        kal = tpo_daten._kalender()
        offen = [t for t in alle if not tpo_daten.auslaendisch(t) and tpo_daten.luecke(t, kal)]
        if not offen:
            break
        durchgang += 1
        offen.sort(key=tpo_laden._neuester)
        print(f"Durchgang {durchgang}: {len(offen)} Titel mit Lücke", flush=True)
        for t in offen:
            if datetime.now().hour < 12 and (datetime.now().hour, datetime.now().minute) >= SCHLUSS:
                break
            try:
                tpo_daten.schritt(t, kal)
            except Exception as e:  # noqa: BLE001
                print(f"  {t}: {e}", flush=True)
    p["massive_durchgaenge"] = durchgang
    _schreiben(p)


def stand():
    """Für die Übersicht: (Ampel, Text) aus dem Protokoll."""
    try:
        p = json.load(open(PROTOKOLL, encoding="utf-8"))
    except (OSError, ValueError):
        return "grau", "Nachtlauf noch nie gelaufen (werkzeuge/nachtlauf_einrichten.sh)"
    start = datetime.strptime(p["start"], "%d.%m.%Y %H:%M")
    alter = (datetime.now() - start).total_seconds() / 3600
    wochenende = datetime.now().weekday() >= 5 or (datetime.now().weekday() == 0 and datetime.now().hour < 22)
    fehler = [s["name"] for s in p.get("schritte", []) if not s["ok"]]
    if not p.get("ende"):
        return ("gelb" if alter < 12 else "rot"), f"Nachtlauf vom {p['start']} läuft noch oder brach ab"
    if fehler:
        return "rot", f"Nachtlauf {p['start']}: gescheitert – {', '.join(fehler)}"
    if alter > (72 if wochenende else 26):
        return "rot", f"letzter Nachtlauf {p['start']} – Daten veraltet"
    text = f"Nachtlauf {p['start']}–{p['ende'][-5:]} vollständig"
    try:                                         # Teil von Claude (TradingView, Revier, Scalable), 00:37 Uhr
        c = json.load(open(os.path.join(os.path.dirname(PROTOKOLL), "claude_lauf.json"), encoding="utf-8"))
        text += f" · Claude {c.get('zeit', '')}: TradingView {c.get('tradingview', '–')}"
        if str(c.get("tradingview", "")).startswith("Fehler"):
            return "gelb", text
    except (OSError, ValueError):
        pass
    return "grün", text


def _laeuft(datei, stunden):
    """Protokoll ohne Ende, jünger als `stunden` und der Prozess lebt noch → (True, Protokoll)."""
    try:
        p = json.load(open(datei, encoding="utf-8"))
    except (OSError, ValueError):
        return False, None
    if p.get("ende"):
        return False, p
    alter = (datetime.now() - datetime.strptime(p["start"], "%d.%m.%Y %H:%M")).total_seconds() / 3600
    if alter > stunden:
        return False, p
    pid = p.get("pid")
    if pid:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False, p
        except PermissionError:
            pass
    return True, p


def tisch_lauf_stand():
    """Für den Knopf: (laeuft, Text). Läuft gerade der Nachtlauf, wird nicht doppelt gerechnet."""
    nacht, _ = _laeuft(PROTOKOLL, 12)
    if nacht:
        return True, "Der Nachtlauf rechnet gerade – der Kartentisch kommt mit ihm."
    laeuft, p = _laeuft(TISCH_PROTOKOLL, 3)
    if p is None:
        return False, ""
    namen = ["Ränge", "Kartentisch", "Lage"]
    fehler = [s["name"] for s in p.get("schritte", []) if not s["ok"]]
    if laeuft:
        i = min(len(p.get("schritte", [])), 2)
        return True, f"Läuft seit {p['start'][-5:]} Uhr · Schritt {i + 1} von 3: {namen[i]}"
    if not p.get("ende"):
        return False, f"Lauf vom {p['start']} brach ab"
    return False, (f"Zuletzt {p['start']}–{p['ende'][-5:]} " + (f"– gescheitert: {', '.join(fehler)}" if fehler else "✓"))


def tisch_lauf_starten():
    """Startet `nachtlauf.py --tisch` als eigenen Prozess (die App wartet nicht darauf)."""
    if tisch_lauf_stand()[0]:
        return False
    os.makedirs(os.path.dirname(TISCH_LOG), exist_ok=True)
    log = open(TISCH_LOG, "w", encoding="utf-8")
    subprocess.Popen([sys.executable, "-u", os.path.abspath(__file__), "--tisch"], cwd=os.path.join(HIER, ".."),
                     stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return True


def _gross_laeuft():
    return _laeuft(PROTOKOLL, 12)[0] or _laeuft(TISCH_PROTOKOLL, 3)[0]


def seiten(prozesse=None):
    """Schrank neu füllen (06.11.2026): Nach einer Programm- oder Depotänderung gelten die abgelegten Titelseiten
    nicht mehr. Dieser Lauf baut sie für alle Titel des Kartentischs neu (Watchlist zuerst) und schreibt Lagekarte und
    Kacheln in den Tisch zurück – mit den vorhandenen Kursen, ohne neue Reihen. Startet ein Nacht- oder Tischlauf,
    hört er auf (die füllen den Schrank ohnehin)."""
    from concurrent.futures import ProcessPoolExecutor
    import kartentisch
    import titel
    import watchlists
    tisch = kartentisch.laden()
    if not tisch:
        return
    grenze = titel.ablage_grenze()
    wl = set(watchlists.alle())
    liste = sorted((tk for tk in tisch["titel"] if not titel.frisch(tk, grenze)), key=lambda tk: (tk not in wl, tk))
    p = {"start": datetime.now().strftime("%d.%m.%Y %H:%M"), "ende": None, "pid": os.getpid(), "zahl": len(liste),
         "fertig": 0}
    _schreiben(p, SEITEN_PROTOKOLL)
    neu = {}
    ex = ProcessPoolExecutor(prozesse or max(1, (os.cpu_count() or 2) - 1))
    try:
        for tk, karte, kacheln in ex.map(kartentisch._stufe2, liste):
            neu[tk] = (karte, kacheln)
            p["fertig"] += 1
            if p["fertig"] % 10 == 0:
                _schreiben(p, SEITEN_PROTOKOLL)
                if _gross_laeuft():
                    p["abbruch"] = "Nacht- oder Tischlauf gestartet"
                    break
    finally:
        ex.shutdown(cancel_futures=True)
    jetzt = kartentisch.laden()
    if jetzt and jetzt.get("erzeugt") == tisch.get("erzeugt") and not _gross_laeuft():
        for tk, (karte, kacheln) in neu.items():
            if karte is not None and tk in jetzt["titel"]:
                jetzt["titel"][tk].update(karte=karte, kacheln=kacheln)
        pfad = os.path.join(kartentisch.SPEICHER, f'{jetzt["stand"]}.json')
        json.dump(jetzt, open(pfad + ".neu", "w", encoding="utf-8"), ensure_ascii=False)
        os.replace(pfad + ".neu", pfad)
    p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    _schreiben(p, SEITEN_PROTOKOLL)


def seiten_lauf_stand():
    """Text für die Übersicht, solange der Schrank gefüllt wird, sonst ''."""
    laeuft, p = _laeuft(SEITEN_PROTOKOLL, 6)
    return f"Titelseiten nach der Änderung neu abgelegt: {p['fertig']} von {p['zahl']}" if laeuft else ""


def seiten_lauf_starten():
    """Startet `nachtlauf.py --seiten`, wenn Titelseiten veraltet sind und kein anderer Lauf rechnet."""
    import kartentisch
    import titel
    if _gross_laeuft() or _laeuft(SEITEN_PROTOKOLL, 6)[0]:
        return False
    tisch = kartentisch.laden()
    grenze = titel.ablage_grenze()
    if not tisch or all(titel.frisch(tk, grenze) for tk in tisch["titel"]):
        return False
    os.makedirs(os.path.dirname(SEITEN_LOG), exist_ok=True)
    log = open(SEITEN_LOG, "w", encoding="utf-8")
    subprocess.Popen([sys.executable, "-u", os.path.abspath(__file__), "--seiten"], cwd=os.path.join(HIER, ".."),
                     stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return True


if __name__ == "__main__":
    if "--seiten" in sys.argv:
        seiten()
    else:
        main(nur_tisch="--tisch" in sys.argv)
