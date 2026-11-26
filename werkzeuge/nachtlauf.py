"""Nachtlauf, seit 12.11.2026 ein Frühlauf (Schritt 8, 04.11.2026): alle Daten aller Titel, jeden Handelstag, ohne
Ausnahme – mit Protokoll.

Start auf dem Server über den Timer nachtlauf.timer (werkzeuge/server/nachtlauf.timer, Di–Sa 6:05 Uhr Berlin; der
Server übernimmt ihn selbst aus dem Speicher) oder von Hand:  python3 werkzeuge/nachtlauf.py
Warum morgens: Massive gibt im kostenlosen Plan einen Handelstag erst nach Mitternacht New York (6 Uhr Berlin) heraus.
Abends um 22:45 rechneten Rückenwind und die Ränge deshalb mit dem Vortag, Charts und Akten (Yahoo) mit dem
neuen Tag. Morgens haben beide Quellen denselben abgeschlossenen Handelstag; die Datenstand-Wache prüft das.
Schritte (jeder für sich abgesichert; scheitert einer, laufen die übrigen weiter und das Protokoll meldet ihn):
  1. Massive: Tageskurse aller US-Aktien des letzten Handelstags (bis 30 Min warten, bis Massive ihn freigibt), Splits
  2. Rudel, Kursverwandte und Themen-Gruppen neu rechnen
  3. 30-Minuten-Kerzen des neuen Tages über Yahoo (Wertzonen), Ausland inklusive
  4. Tageskurse aller Titel (Revier, Watchlist, Positionen, Gesamtmarkt) und Wechselkurse (Yahoo)
  5. samstags (nach dem Freitag) Revier-Pflege; TradingView-Kennzahlen (Screener-Schnittstelle, ohne Login)
  6. Rückenwind, Zirkel (Kreislauf, Setup, Hochs/Tiefs je Titel; löst am 22.11.2026 den
     Kartentisch ab), Lage (Seite Rückenwind), Schrank; danach die Morgenmeldung (Schlachtordnung, Setups)
  7. Datenstand-Wache: Kurstag jedes Teils ins Protokoll (rot, wenn sie verschiedene Tage haben)
  8. Massive-Durchgänge für Lücken der
     30-Minuten-Kerzen bis 11:30 Uhr (Erstbefüllung, neue Titel)
Protokoll: daten/nachtlauf/protokoll.json – die Seiten zeigen daraus Statuszeile und Datenstand.
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
SEITEN_PROTOKOLL = os.path.join(HIER, "..", "daten", "nachtlauf", "seiten_lauf.json")   # Schrank nach Änderungen
SEITEN_LOG = os.path.join(HIER, "..", "daten", "nachtlauf", "seiten_lauf.log")
SCHLUSS = (11, 30)            # Massive-Durchgänge für Lücken enden vormittags (Frühlauf ab 6:05, seit 12.11.2026)


def _schreiben(p, datei=PROTOKOLL):
    os.makedirs(os.path.dirname(datei), exist_ok=True)
    json_schreiben(datei, p, ensure_ascii=False, indent=1)


def _mitteilung(text, wichtig=False, titel="Invest Cockpit", seite=None):
    """Meldung aufs Handy (ntfy, kern/meldung.py) und – auf dem Mac – als Mitteilung am Bildschirm."""
    try:
        import meldung
        meldung.senden(text, titel, wichtig, seite)
    except Exception:  # noqa: BLE001
        pass
    if sys.platform == "darwin":
        try:
            subprocess.run(["osascript", "-e", f'display notification "{text[:200]}" with title "{titel}"'], timeout=10)
        except Exception:  # noqa: BLE001 – ohne Mitteilung läuft alles weiter
            pass


def main():
    import tpo_daten
    import tpo_laden
    tpo_daten._mehr_dateien()
    datei = PROTOKOLL
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
        print(f"    {'🟢' if ok else '🔴'} {text}", flush=True)
        return ok

    alle = tpo_laden.titel()

    def massive_tage():
        import massive
        soll = massive._letzter_schluss()          # Frühlauf: der gestrige Handelstag (in New York nach Mitternacht)
        for versuch in range(7):                   # Massive gibt ihn kurz nach Mitternacht New York frei: bis 30 Min warten
            massive.tag(soll)
            if os.path.exists(os.path.join(massive.SPEICHER, f"{soll:%Y-%m-%d}.csv")):
                break                              # gespeichert (auch ein Feiertag wird als leerer Tag gespeichert)
            print(f"    Massive hat den {soll:%d.%m.} noch nicht – Versuch {versuch + 1}, warte 5 Minuten", flush=True)
            time.sleep(300)
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

    def zirkel_():
        import zirkel
        z_ = zirkel.rechnen(zirkel.liste(alle), melden=lambda x: print(x, flush=True))
        b_ = z_["barometer"]
        sp, he = b_.get("fuehrer") or {}, b_.get("heer") or {}
        ampel = (f"Lage {zirkel.MARKT_WORT[zirkel.lage_ampel(sp, he)]}: Spitze {sp.get('auf')}↑ {sp.get('ab')}↓ · "
                 f"Heer {he.get('auf')}↑ {he.get('ab')}↓")
        return f"{z_['titel']} Titel, {z_['trades']} mit Setup · {b_['hochs']} Hochs, {b_['tiefs']} Tiefs · {ampel}"

    def revier():
        import revier_pflege
        return revier_pflege.pflegen()

    def tradingview():
        import tv_kennzahlen
        return tv_kennzahlen.aktualisieren(alle)

    def zahlen_nach_terminen():
        """Zahlen neu für alle Titel, deren Termin seit dem letzten Laden vorbei ist – vor Rückenwind und Zirkel,
        damit beide (und die Titelseite) dieselben Zahlen lesen (12.11.2026)."""
        import quellen
        import watchlists
        neu, fehler = quellen.nach_terminen(sorted(set(alle) | set(watchlists.alle())))
        return f"{neu} Titel nach ihren Zahlen neu geladen" + (f", {fehler} gescheitert" if fehler else "")

    def rueckenwind_():
        import rueckenwind
        e = rueckenwind.rechnen(netz=True)
        from collections import Counter
        n = Counter(x.get("klasse") for x in e["titel"].values())
        return f"Stand {e['stand']}: " + ", ".join(f"{k} {n.get(i, 0)}" for i, k in enumerate(rueckenwind.KLASSEN, 1))

    def schrank():
        """Titelseiten der Rückenwind-Titel in Garde, Angriff und Vorhut und der Watchlist vorbauen (09.11.2026), damit
        jeder Klick aus Rückenwind sofort öffnet."""
        from concurrent.futures import ProcessPoolExecutor
        import zonenseite
        liste = schrank_liste()
        n = 0
        with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 1)) as ex:
            for ok in ex.map(zonenseite.vorbauen, liste, chunksize=4):
                n += ok
        return f"{n} von {len(liste)} Titelseiten abgelegt"

    schritt("Massive: Tageskurse und Splits", massive_tage)
    schritt("Rudel, Kursverwandte, Themen-Gruppen", rudel_neu)
    schritt("30-Minuten-Kerzen (Yahoo)", kerzen_neu)
    schritt("Tageskurse und Wechselkurse", tageskurse)
    if datetime.now().weekday() == 5:            # samstags früh (nach dem Freitag): Revier-Pflege
        schritt("Revier-Pflege", revier)
    schritt("TradingView-Kennzahlen", tradingview)
    schritt("Zahlen nach den Terminen neu laden", zahlen_nach_terminen)
    schritt("Rückenwind (RS-Dynamik, Geldfluss, Zahlen)", rueckenwind_)   # vor dem Zirkel: die Meldung liest beide
    schritt("Zirkel (Kreislauf, Setup, Hochs/Tiefs, Markt-Ampel)", zirkel_)
    schritt("Lage (Markt-Ampel, Wetter, Pendel, Breite)", lage)   # nach dem Zirkel: liest Markt-Ampel, Hochs und Tiefs
    schritt("Schrank: Titelseiten der Rückenwind-Titel und der Watchlist", schrank)
    p["datenstand"] = datenstand()
    p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    _schreiben(p)
    _kopf_neu()
    fehler = [s["name"] for s in p["schritte"] if not s["ok"]]
    if fehler:                                    # Micky 17.11.2026: kein „Lage steht“ mehr – aufs Handy nur die heißen
        _mitteilung(f"🔴 gescheitert: {', '.join(fehler)}", True)   # Titel und Fehler des Laufs
    try:                                          # Morgenmeldung: Setups nach Schlachtordnung (22.11.2026)
        import zirkel
        text_, n_ = zirkel.heisse()
        _mitteilung(text_, titel=f"Setups: {n_}", seite="Rückenwind")
    except Exception as e:  # noqa: BLE001 – ohne Liste läuft der Lauf weiter
        print(f"Heiße Titel: {e}", flush=True)

    # Massive-Durchgänge für Lücken (Erstbefüllung, neue Titel) bis zum Vormittag (SCHLUSS)
    durchgang = 0
    while (datetime.now().hour, datetime.now().minute) < SCHLUSS:
        kal = tpo_daten._kalender()
        offen = [t for t in alle if not tpo_daten.auslaendisch(t) and tpo_daten.luecke(t, kal)]
        if not offen:
            break
        durchgang += 1
        offen.sort(key=tpo_laden._neuester)
        print(f"Durchgang {durchgang}: {len(offen)} Titel mit Lücke", flush=True)
        for t in offen:
            if (datetime.now().hour, datetime.now().minute) >= SCHLUSS:
                break
            try:
                tpo_daten.schritt(t, kal)
            except Exception as e:  # noqa: BLE001
                print(f"  {t}: {e}", flush=True)
    p["massive_durchgaenge"] = durchgang
    _schreiben(p)



QUELLEN_DATENSTAND = {                       # Teil der App → woher sein Kurstag kommt (Datenstand-Wache, 12.11.2026)
    "Massive-Tageskurse": "Rückenwind (RS-Rang, Klassen, Momentum, ✈️), Rudel, Breite",
    "Yahoo-Tageskurse": "Charts, Zirkel, Setups, Morgenmeldung",
    "Indizes (SPY, QQQ)": "Markt-Ampel (Zirkel der Indizes)",
    "Marktdaten (Sektor-ETFs)": "Pendel, Sektor-Rotation, Wirtschaftswetter (Yahoo)",
    "Rückenwind": "Schlachtordnung, Geldfluss, dreifacher Rückenwind",
    "Zirkel": "Kreislauf, Setups, Hochs/Tiefs der Markt-Ampel",
}


def datenstand():
    """Datenstand-Wache (12.11.2026): mit welchem Kurstag jeder Teil gerechnet hat, {Teil: 'YYYY-MM-DD' oder None}.
    Alle Teile müssen denselben abgeschlossenen Handelstag haben – sonst meldet die Statuszeile es rot."""
    import pandas as pd
    aus = {}
    try:
        import massive
        tage = sorted(f[:10] for f in os.listdir(massive.SPEICHER) if f[:4].isdigit() and f.endswith(".csv")
                      and os.path.getsize(os.path.join(massive.SPEICHER, f)) > 200)     # leere Tage (Feiertag) nicht
        aus["Massive-Tageskurse"] = tage[-1] if tage else None
    except Exception:  # noqa: BLE001
        aus["Massive-Tageskurse"] = None
    try:
        import daten
        i = daten.kurse_gespeichert(daten.INDEX)
        aus["Yahoo-Tageskurse"] = f"{i.index[-1]:%Y-%m-%d}" if i is not None and len(i) else None
    except Exception:  # noqa: BLE001
        aus["Yahoo-Tageskurse"] = None
    try:                                        # Indizes der Markt-Ampel (24.11.2026: der Zirkel liest SPY und QQQ aus dem
        import daten                            # Kursspeicher – die frühere Datei ^GSPC_ohlc wird nicht mehr gepflegt)
        import zirkel
        tage_i = [daten.kurse_gespeichert(tk).index[-1] for tk in zirkel.INDIZES.values()]
        aus["Indizes (SPY, QQQ)"] = f"{min(tage_i):%Y-%m-%d}"
    except Exception:  # noqa: BLE001
        aus["Indizes (SPY, QQQ)"] = None
    try:                                        # Sektor-ETFs von Yahoo (Pendel, Rotation, Wirtschaftswetter)
        import marktdaten
        import sektoren
        pf = marktdaten._pfad(sektoren.MARKT)
        aus["Marktdaten (Sektor-ETFs)"] = (f"{pd.read_csv(pf, parse_dates=['Datum']).Datum.iloc[-1]:%Y-%m-%d}"
                                           if os.path.exists(pf) else None)
    except Exception:  # noqa: BLE001
        aus["Marktdaten (Sektor-ETFs)"] = None
    try:
        import rueckenwind
        aus["Rückenwind"] = (rueckenwind.laden() or {}).get("stand")
    except Exception:  # noqa: BLE001
        aus["Rückenwind"] = None
    try:                                        # Zirkel-Lauf (Kreislauf, Setups) aus den Yahoo-Tageskursen
        import zeichen
        aus["Zirkel"] = (zeichen.laden() or {}).get("kurstag")
    except Exception:  # noqa: BLE001
        aus["Zirkel"] = None
    return aus


def datenstand_zeile(ds=None):
    """(Ampel, Text) für jede Seite: „Kurse vom Mi 11.11.“ oder rot, wenn die Teile verschiedene Tage haben."""
    import pandas as pd
    if ds is None:
        try:
            ds = json.load(open(PROTOKOLL, encoding="utf-8")).get("datenstand")
        except (OSError, ValueError):
            ds = None
    if not ds:
        return "grau", "Datenstand unbekannt (noch kein Lauf mit Datenstand-Wache)"
    tage = {v for v in ds.values() if v}
    fehlt = [k for k, v in ds.items() if not v]
    tag_ = lambda t: f"{['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][pd.Timestamp(t).weekday()]} {pd.Timestamp(t):%d.%m.}"  # noqa: E731
    if len(tage) == 1 and not fehlt:
        t = next(iter(tage))
        try:                                       # einheitlich, aber alt? Erwartet: der letzte abgeschlossene Handelstag
            import massive
            soll = massive._letzter_schluss()
            while soll.weekday() >= 5:
                soll -= pd.Timedelta(days=1)
            if pd.Timestamp(t) < soll:
                return "gelb", (f"Kurse vom {tag_(t)} – alle Teile gleich, aber der letzte Handelstag wäre der "
                                f"{tag_(soll)} (Feiertag in den USA oder Lauf ausgefallen?)")
        except Exception:  # noqa: BLE001
            pass
        return "grün", f"Kurse vom {tag_(t)} – alle Teile auf demselben Handelstag"
    neu = max(tage) if tage else None
    alt = [f"{k} {tag_(v)}" for k, v in ds.items() if v and v != neu] + [f"{k} fehlt" for k in fehlt]
    return "rot", (f"Datenstand uneinheitlich: neuester Tag {tag_(neu)}, abweichend " + ", ".join(alt)
                   if neu else "Datenstand fehlt: " + ", ".join(alt))


def _kopf_neu():
    """Die abgelegte Seite Rückenwind noch einmal bauen, wenn das Protokoll fertig ist (12.11.2026): Sie wird im Schritt
    „Lage“ mitten im Lauf gebaut und zeigte deshalb bis zur nächsten Programmänderung „Nachtlauf läuft noch oder brach
    ab“."""
    try:
        import uebersicht
        uebersicht.ablegen(uebersicht.seite_uebersicht())
    except Exception as e:  # noqa: BLE001 – die alte Ablage bleibt, die App baut sonst selbst
        print(f"Seite Rückenwind nach Laufende nicht neu abgelegt: {e}", flush=True)


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
        return "rot", f"Nachtlauf {p['start']}: gescheitert – {_gruende(p)}"
    if alter > (72 if wochenende else 26):
        return "rot", f"letzter Nachtlauf {p['start']} – Daten veraltet"
    # Der frühere Teil von Claude um 00:37 (claude_lauf.json) entfällt: TradingView und Revier holt seit 05.11.2026
    # der Server selbst; die alte Datei zeigte sonst einen veralteten Stand an (12.11.2026).
    ampel, ds = datenstand_zeile(p.get("datenstand"))
    if ampel in ("rot", "gelb"):
        return ampel, f"Nachtlauf {p['start']}–{p['ende'][-5:]} · {ds}"
    return "grün", f"Nachtlauf {p['start']}–{p['ende'][-5:]} vollständig · {ds}"


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
        try:                                     # beendet, aber vom Elternprozess nicht abgeholt (Zombie) = läuft nicht
            with open(f"/proc/{pid}/status", encoding="utf-8") as f:
                if any(z.startswith("State:") and "Z" in z.split()[1] for z in f):
                    return False, p
        except OSError:
            pass
    return True, p


def _gruende(p):
    """Gescheiterte Schritte mit Grund, kurz: „Zirkel (TypeError: …)“ – damit man nicht im Dunkeln steht."""
    return "; ".join(f"{s['name'].split(' (')[0]} ({s['text'][:110]})" for s in p.get("schritte", []) if not s["ok"])






def _gross_laeuft():
    return _laeuft(PROTOKOLL, 12)[0]


def schrank_liste():
    """Die Titel des Schranks: Rückenwind in Garde, Angriff und Vorhut und die Watchlist, Watchlist zuerst, nur die
    nicht frisch abgelegten."""
    import rueckenwind
    import watchlists
    import zonenseite
    wl = set(watchlists.alle())
    e = rueckenwind.laden() or {}
    vorne = {tk for tk, x in (e.get("titel") or {}).items() if x.get("klasse") in rueckenwind.VORNE_KLASSEN}
    grenze = zonenseite.ablage_grenze()
    return sorted((tk for tk in vorne | wl if not zonenseite.frisch(tk, grenze)), key=lambda tk: (tk not in wl, tk))


def seiten(prozesse=None):
    """Schrank neu füllen (06.11.2026), beim ersten Start ohne Zirkel-Lauf vorher den Zirkel: Nach einer Programm- oder Depotänderung gelten die abgelegten Titelseiten
    nicht mehr. Dieser Lauf baut sie neu (Watchlist zuerst) – mit den vorhandenen Kursen. Startet ein Nachtlauf, hört
    er auf (der füllt den Schrank ohnehin)."""
    from concurrent.futures import ProcessPoolExecutor
    import uebersicht
    import zonenseite
    if uebersicht.veraltet():                    # Übersicht nach einer Programmänderung sofort neu ablegen
        try:
            uebersicht.ablegen(uebersicht.seite_uebersicht())
        except Exception:  # noqa: BLE001
            traceback.print_exc()
    p = {"start": datetime.now().strftime("%d.%m.%Y %H:%M"), "ende": None, "pid": os.getpid(), "zahl": 0, "fertig": 0}
    _schreiben(p, SEITEN_PROTOKOLL)
    import zirkel
    if not zirkel.feld() or not zirkel.barometer().get("index"):   # noch kein Zirkel-Lauf bzw. ohne Markt-Ampel (23.11.)
        import tpo_laden
        zirkel.rechnen(zirkel.liste(tpo_laden.titel()), prozesse=prozesse)
        uebersicht.ablegen(uebersicht.seite_uebersicht())   # Markt-Ampel mit Hochs und Tiefs
    liste = schrank_liste()
    p["zahl"] = len(liste)
    ex = ProcessPoolExecutor(prozesse or max(1, (os.cpu_count() or 2) - 1))
    try:
        for _ in ex.map(zonenseite.vorbauen, liste):
            p["fertig"] += 1
            if p["fertig"] % 10 == 0:
                _schreiben(p, SEITEN_PROTOKOLL)
                if _gross_laeuft():
                    p["abbruch"] = "Nachtlauf gestartet"
                    break
    finally:
        ex.shutdown(cancel_futures=True)
    p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    _schreiben(p, SEITEN_PROTOKOLL)


def seiten_lauf_starten():
    """Startet `nachtlauf.py --seiten`, wenn Titelseiten veraltet sind und kein anderer Lauf rechnet."""
    if _gross_laeuft() or _laeuft(SEITEN_PROTOKOLL, 6)[0]:
        return False
    import uebersicht
    import zirkel
    if not uebersicht.veraltet() and zirkel.feld() and not schrank_liste():
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
        main()
