"""Nachtlauf, seit 12.11.2026 ein Frühlauf (Schritt 8, 04.11.2026): alle Daten aller Titel, jeden Handelstag, ohne
Ausnahme – mit Protokoll.

Start auf dem Server über den Timer nachtlauf.timer (werkzeuge/server/nachtlauf.timer, Di–Sa 6:05 Uhr Berlin; der
Server übernimmt ihn selbst aus dem Speicher) oder von Hand:  python3 werkzeuge/nachtlauf.py
Warum morgens: Massive gibt im kostenlosen Plan einen Handelstag erst nach Mitternacht New York (6 Uhr Berlin) heraus.
Abends um 22:45 rechneten Rückenwind, RS-Rang und Führer-Rang deshalb mit dem Vortag, Charts und Akten (Yahoo) mit dem
neuen Tag. Morgens haben beide Quellen denselben abgeschlossenen Handelstag; die Datenstand-Wache prüft das.
Schritte (jeder für sich abgesichert; scheitert einer, laufen die übrigen weiter und das Protokoll meldet ihn):
  1. Massive: Tageskurse aller US-Aktien des letzten Handelstags (bis 30 Min warten, bis Massive ihn freigibt), Splits
  2. Rudel, Kursverwandte und Themen-Gruppen neu rechnen
  3. 30-Minuten-Kerzen des neuen Tages über Yahoo (Wertzonen), Ausland inklusive
  4. Tageskurse aller Titel (Revier, Watchlist, Positionen, Gesamtmarkt) und Wechselkurse (Yahoo)
  5. samstags (nach dem Freitag) Revier-Pflege; TradingView-Kennzahlen (Screener-Schnittstelle, ohne Login)
  6. RS-Rang, Führer-Rang, Rückenwind, Kartentisch, Lage (Seite Rückenwind), Konferenz des Stabs, Schrank
  7. Datenstand-Wache: Kurstag jedes Teils ins Protokoll (rot, wenn sie verschiedene Tage haben)
  8. bei Bedarf zweiter Anlauf der Konferenz (30 Min später), danach Massive-Durchgänge für Lücken der
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
TISCH_PROTOKOLL = os.path.join(HIER, "..", "daten", "nachtlauf", "tisch_lauf.json")   # Knopf in der Übersicht
TISCH_LOG = os.path.join(HIER, "..", "daten", "nachtlauf", "tisch_lauf.log")
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

    def tisch():
        import kartentisch
        t_ = kartentisch.rechnen(alle, melden=lambda x: print(x, flush=True))
        p["neu"] = len(t_["neu"])
        p["reihen"] = {k: sum(1 for x in t_["titel"].values() if x.get("reihe") == k) for k in ("m_spitze", "m_weitere", "k_breakout", "k_ep", "zahlen", "k_ermuedung", "k_baerenflagge", "vcp", "flagge")}
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

    def zahlen_nach_terminen():
        """Zahlen neu für alle Titel, deren Termin seit dem letzten Laden vorbei ist – vor Rückenwind und Kartentisch,
        damit beide (und die Titelseite) dieselben Zahlen lesen (12.11.2026)."""
        import quellen
        import watchlists
        neu, fehler = quellen.nach_terminen(sorted(set(alle) | set(watchlists.alle())))
        return f"{neu} Titel nach ihren Zahlen neu geladen" + (f", {fehler} gescheitert" if fehler else "")

    def rueckenwind_():
        import rueckenwind
        e = rueckenwind.rechnen(netz=True)
        from collections import Counter
        n = Counter(x["stufe"] for x in e["titel"].values())
        return (f"Stand {e['stand']}: Entsteht {n.get('Entsteht', 0)}, Läuft {n.get('Läuft', 0)}, "
                f"Ermüdet {n.get('Ermüdet', 0)}, Abfluss {n.get('Abfluss', 0)}")

    def schrank():
        """Titelseiten der Rückenwind-Titel mit Stufe und der Watchlist vorbauen (09.11.2026), damit jeder Klick aus
        Rückenwind sofort öffnet. Die Titel des Kartentischs baut der Schritt Kartentisch schon."""
        from concurrent.futures import ProcessPoolExecutor
        import kartentisch
        import rueckenwind
        import titel
        import watchlists
        e = rueckenwind.laden() or {}
        liste = sorted({tk for tk, x in (e.get("titel") or {}).items() if x.get("stufe")} | set(watchlists.alle()))
        grenze = titel.ablage_grenze()
        liste = [tk for tk in liste if not titel.frisch(tk, grenze)]
        n = 0
        with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 1)) as ex:
            for _, karte, _ in ex.map(kartentisch._stufe2, liste, chunksize=4):
                n += karte is not None
        return f"{n} von {len(liste)} Titelseiten abgelegt"

    def konferenz_():
        import stab
        if not stab.schluessel():
            return "übersprungen – kein API-Schlüssel"
        k = stab.konferenz()
        if stab.gescheitert(k):
            raise RuntimeError(stab.gescheitert(k))
        _tagesbefehl_melden(k)                    # gleich nach der Konferenz aufs Handy, vor dem Schrank (~7 Uhr)
        ko = stab.kosten()
        return f"{stab.ergebnis_zeile(k)} · Monat {stab._zahl_de(ko['usd'])} $ von {stab._zahl_de(stab.DECKEL_USD, 0)} $"

    def wachen_():
        """Wachen (12.11.2026): rot = Fehler der App → Schritt rot und Warnung; gelb = Hinweise (Stab, Gegenprobe)."""
        import wachen
        w = wachen.pruefen()
        rot = [t for a, t in w["zeichen"] if a == "rot"]
        gelb = [t for a, t in w["zeichen"] if a == "gelb"]
        p["wachen"] = {"ampel": w["ampel"], "rot": len(rot), "gelb": len(gelb)}
        if rot:
            _mitteilung(f"⚠ Wachen: {len(rot)} Fehler der App – " + " · ".join(rot[:3]), True)
            raise RuntimeError(f"{len(rot)} Fehler: " + " · ".join(rot[:3]))
        if gelb:
            _mitteilung(f"Wachen: {len(gelb)} Hinweise – " + " · ".join(gelb[:3]))
        return f"{w['akten']} Akten geprüft · " + ("alles im Gleichlauf" if not gelb else f"{len(gelb)} Hinweise")

    if nur_tisch:
        schritt("RS-Rang, Führer-Rang (Kullamägi)", raenge)
        schritt("Rückenwind (RS-Dynamik, Geldfluss, Zahlen)", rueckenwind_)   # vor dem Tisch: Titelseiten lesen ihn
        schritt("Kartentisch", tisch)
        schritt("Lage (Wetter, Pendel, Breite, Front, Marktrichtung)", lage)
        p["datenstand"] = datenstand()
        p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        _schreiben(p, datei)
        return

    schritt("Massive: Tageskurse und Splits", massive_tage)
    schritt("Rudel, Kursverwandte, Themen-Gruppen", rudel_neu)
    schritt("30-Minuten-Kerzen (Yahoo)", kerzen_neu)
    schritt("Tageskurse und Wechselkurse", tageskurse)
    if datetime.now().weekday() == 5:            # samstags früh (nach dem Freitag): Revier-Pflege
        schritt("Revier-Pflege", revier)
    schritt("TradingView-Kennzahlen", tradingview)
    schritt("RS-Rang, Führer-Rang (Kullamägi)", raenge)
    schritt("Zahlen nach den Terminen neu laden", zahlen_nach_terminen)
    schritt("Rückenwind (RS-Dynamik, Geldfluss, Zahlen)", rueckenwind_)   # vor dem Tisch: Titelseiten lesen ihn
    schritt("Kartentisch", tisch)
    schritt("Lage (Wetter, Pendel, Breite, Front, Marktrichtung)", lage)   # nach dem Tisch: liest dessen Barometer
    schritt("Konferenz des Stabs (MARAGA Investment)", konferenz_)
    schritt("Schrank: Titelseiten der Rückenwind-Titel und der Watchlist", schrank)
    schritt("Wachen: Gleichlauf, Plausibilität, Gegenprobe TradingView, Stab", wachen_)
    p["datenstand"] = datenstand()
    p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    _schreiben(p)
    _kopf_neu()
    fehler = [s["name"] for s in p["schritte"] if not s["ok"]]
    _mitteilung((f"⚠ gescheitert: {', '.join(fehler)}. " if fehler else "Lage steht. ")
                + f"{(p.get('reihen') or {}).get('m_spitze', 0)} × Base-Ausbruch ★ · {p.get('neu', 0)} Neuigkeiten")

    # Zweiter Anlauf der Konferenz (10.11.2026; seit dem Frühlauf 12.11.2026 30 Minuten nach dem ersten, vor den
    # Massive-Durchgängen): ist sie gescheitert, noch einmal
    if any(s_["name"].startswith("Konferenz") and not s_["ok"] for s_ in p["schritte"]):
        time.sleep(30 * 60)
        try:
            import stab
            k = stab.konferenz(melden=print)
            ok_ = not stab.gescheitert(k)
        except Exception as e:  # noqa: BLE001
            ok_, k = False, {"befehl": {"lage": str(e), "anrede": str(e)}}
        p["konferenz_zweiter_anlauf"] = "geklappt" if ok_ else "gescheitert"
        if ok_:                                  # Ampel der Übersicht: Schritt gilt dann als erledigt
            for s_ in p["schritte"]:
                if s_["name"].startswith("Konferenz"):
                    s_["ok"], s_["text"] = True, "im zweiten Anlauf geklappt"
        _schreiben(p)
        _kopf_neu()
        if not (ok_ and _tagesbefehl_melden(k)):
            _mitteilung("Konferenz im zweiten Anlauf: " + ("Tagesbefehl liegt bereit." if ok_ else
                        f"wieder gescheitert – {str((k.get('befehl') or {}).get('lage') or (k.get('befehl') or {}).get('anrede') or '')[:120]}"), not ok_)

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
    "Massive-Tageskurse": "Rückenwind, RS-Rang, Führer-Rang, Rudel, Breite",
    "Yahoo-Tageskurse": "Charts, Kartentisch, Akten des Stabs",
    "Marktdaten (Indizes)": "Markt-Ampel, Pendel, Sektor-Rotation, O'Neil-Marktrichtung (Yahoo)",
    "Rückenwind": "Stufen, Geldfluss, dreifacher Rückenwind",
    "RS-Rang": "RS-Rang (IBD-Formel) im Kartentisch",
    "Führer-Rang": "Kullamägi-Führer (oberste 1–2 %)",
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
    try:                                        # Marktdaten der Lage (Prüfung 12.11.2026 – vorher nicht bewacht)
        import marktdaten
        pf = marktdaten._pfad("^GSPC_ohlc")
        aus["Marktdaten (Indizes)"] = (f"{pd.read_csv(pf, parse_dates=['Datum']).Datum.iloc[-1]:%Y-%m-%d}"
                                       if os.path.exists(pf) else None)
    except Exception:  # noqa: BLE001
        aus["Marktdaten (Indizes)"] = None
    try:
        import rueckenwind
        aus["Rückenwind"] = (rueckenwind.laden() or {}).get("stand")
    except Exception:  # noqa: BLE001
        aus["Rückenwind"] = None
    for teil, modul in (("RS-Rang", "rs_rang"), ("Führer-Rang", "fuehrer_rang")):
        try:
            m = __import__(modul)
            d = pd.read_csv(m.DATEI, nrows=1, keep_default_na=False) if os.path.exists(m.DATEI) else None
            aus[teil] = str(d["stand"].iloc[0]) if d is not None and len(d) else None
        except Exception:  # noqa: BLE001
            aus[teil] = None
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
    if (p.get("wachen") or {}).get("gelb"):
        return "gelb", (f"Nachtlauf {p['start']}–{p['ende'][-5:]} vollständig · {ds} · Wachen: "
                        f"{p['wachen']['gelb']} Hinweise")
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
    """Gescheiterte Schritte mit Grund, kurz: „Kartentisch (TypeError: …)“ – damit man nicht im Dunkeln steht."""
    return "; ".join(f"{s['name'].split(' (')[0]} ({s['text'][:110]})" for s in p.get("schritte", []) if not s["ok"])


def tisch_lauf_stand():
    """Für den Knopf: (laeuft, Text). Läuft gerade der Nachtlauf, wird nicht doppelt gerechnet."""
    nacht, pn = _laeuft(PROTOKOLL, 12)
    if nacht:
        return True, "Der Nachtlauf rechnet gerade – der Kartentisch kommt mit ihm."
    laeuft, p = _laeuft(TISCH_PROTOKOLL, 3)
    if p is None:
        return False, ""
    if not laeuft and pn and pn.get("start"):
        # Ein späterer Nachtlauf hat den Kartentisch neu gerechnet: die alte Meldung des Knopfs gilt nicht mehr
        # (12.11.2026: „Zuletzt 06.11. – gescheitert“ stand eine Woche lang da, obwohl jeder Nachtlauf danach lief)
        import pandas as pd
        a_, b_ = (pd.to_datetime(str(x.get("start")), dayfirst=True, errors="coerce") for x in (p, pn))
        if not pd.isna(a_) and not pd.isna(b_) and b_ > a_:
            return False, ""
    namen = ["Ränge", "Rückenwind", "Kartentisch", "Lage"]
    fehler = _gruende(p)
    if laeuft:
        i = min(len(p.get("schritte", [])), 3)
        return True, f"Läuft seit {p['start'][-5:]} Uhr · Schritt {i + 1} von 4: {namen[i]}"
    if not p.get("ende"):
        return False, f"Lauf vom {p['start']} brach ab"
    return False, (f"Zuletzt {p['start']}–{p['ende'][-5:]} " + (f"– gescheitert: {fehler}" if fehler else "✓"))


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
    import uebersicht
    if uebersicht.veraltet():                    # Übersicht nach einer Programmänderung sofort neu ablegen
        try:
            uebersicht.ablegen(uebersicht.seite_uebersicht())
        except Exception:  # noqa: BLE001
            traceback.print_exc()
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
    import uebersicht
    tisch = kartentisch.laden()
    grenze = titel.ablage_grenze()
    if not uebersicht.veraltet() and (not tisch or all(titel.frisch(tk, grenze) for tk in tisch["titel"])):
        return False
    os.makedirs(os.path.dirname(SEITEN_LOG), exist_ok=True)
    log = open(SEITEN_LOG, "w", encoding="utf-8")
    subprocess.Popen([sys.executable, "-u", os.path.abspath(__file__), "--seiten"], cwd=os.path.join(HIER, ".."),
                     stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return True


KONFERENZ_PROTOKOLL = os.path.join(HIER, "..", "daten", "nachtlauf", "konferenz_lauf.json")


def konferenz_laeuft():
    return _laeuft(KONFERENZ_PROTOKOLL, 1)[0]


def konferenz_starten():
    """Knopf „Konferenz jetzt einberufen“: nachtlauf.py --konferenz im Hintergrund."""
    if konferenz_laeuft():
        return False
    os.makedirs(os.path.dirname(KONFERENZ_PROTOKOLL), exist_ok=True)
    log = open(os.path.join(os.path.dirname(KONFERENZ_PROTOKOLL), "konferenz_lauf.log"), "w", encoding="utf-8")
    subprocess.Popen([sys.executable, "-u", os.path.abspath(__file__), "--konferenz"], cwd=os.path.join(HIER, ".."),
                     stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return True


def konferenz_protokoll():
    """Protokoll und die letzten Zeilen der Ausgabe des Knopf-Laufs – für die Anzeige im Konferenzraum."""
    try:
        p = json.load(open(KONFERENZ_PROTOKOLL, encoding="utf-8"))
    except (OSError, ValueError):
        p = None
    try:
        zeilen = open(os.path.join(os.path.dirname(KONFERENZ_PROTOKOLL), "konferenz_lauf.log"),
                      encoding="utf-8", errors="replace").read().splitlines()[-40:]
    except OSError:
        zeilen = []
    return p, zeilen


def _konferenz_lauf():
    p = {"start": datetime.now().strftime("%d.%m.%Y %H:%M"), "ende": None, "pid": os.getpid()}
    _schreiben(p, KONFERENZ_PROTOKOLL)
    try:
        import stab
        k = stab.konferenz(melden=print)
        if stab.gescheitert(k):
            p["fehler"] = stab.gescheitert(k)
    except Exception as e:  # noqa: BLE001
        p["fehler"] = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    p["ende"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    _schreiben(p, KONFERENZ_PROTOKOLL)
    if p.get("fehler") or not _tagesbefehl_melden():
        _mitteilung(f"⚠ Konferenz gescheitert: {p['fehler'][:150]}" if p.get("fehler") else
                    "Konferenz fertig – der Tagesbefehl liegt im Konferenzraum.", bool(p.get("fehler")))


def _tagesbefehl_melden(k=None):
    """Tagesbefehl in Kurzfassung aufs Handy (12.11.2026); ein Tipp öffnet den Konferenzraum."""
    try:
        import stab
        titel, text = stab.kurzfassung(k or stab.letzte())
        _mitteilung(text, titel=titel, seite="Konferenzraum")
        return True
    except Exception:  # noqa: BLE001 – dann bleibt die kurze Meldung
        traceback.print_exc()
        return False


def laeuft_etwas():
    """Läuft ein Knopf-Lauf (Kartentisch oder Konferenz)? Für das Update-Skript des Servers: dann kein Neustart."""
    return _laeuft(TISCH_PROTOKOLL, 6)[0] or konferenz_laeuft()


if __name__ == "__main__":
    if "--laeuft" in sys.argv:                   # Update-Skript: Exit 0 = es läuft etwas, bitte nicht neu starten
        sys.exit(0 if laeuft_etwas() else 1)
    elif "--konferenz" in sys.argv:
        _konferenz_lauf()
    elif "--seiten" in sys.argv:
        seiten()
    else:
        main(nur_tisch="--tisch" in sys.argv)
