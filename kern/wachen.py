"""Wachen (Micky 12.11.2026: „Wie können wir sichergehen, dass nicht noch solche Fehler in der App schlummern?“).

Läuft im Frühlauf nach Kartentisch und Schrank und prüft jeden Morgen über alle Titel:
  1 Gleichlauf      Kartentisch und abgelegte Titelseite (Chart) nennen dasselbe Setup, dieselbe Seite
                    und denselben Einstieg (±0,5 %); der Stopp liegt beim Long unter, beim Short über dem Einstieg.
                    (Anlass: HWM, Zahlen-Reaktion long, Chart-Stopp 247,93 $ über dem Kurs 224 $.)
  2 Plausibilität   Short-Setups stehen auf der Short-Seite, grüne Setups haben eine Reihe, einsatzbereite Titel liegen
                    in der Zone ihres Setups, kein Zahlentermin der Akten liegt in der Vergangenheit.
  3 Gegenprobe      10 zufällige einsatzbereite Titel gegen TradingView: Schlusskurs (±0,5 %), GD50 (±1 %), Zahlentermin.
Ergebnis: daten/nachtlauf/wachen.json; rot = ein Fehler der App (Warnung aufs Handy, Schritt im Nachtlauf rot),
gelb = beachten (fehlende Gegenprobe). Die Wachen über den Stab entfielen mit dem Konferenzraum (13.11.2026).
"""
import json
import os
import random
import re

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "daten", "nachtlauf", "wachen.json")
TOL_EINSTIEG = 0.5             # % Abweichung zwischen den Stellen
TOL_KURS, TOL_GD50 = 0.5, 1.0  # % gegen TradingView
STICHPROBE = 10
SHORT_REIHEN = ("k_ermuedung", "k_baerenflagge", "k_bruch")


def _pct(a, b):
    return abs(a / b - 1) * 100 if a and b else 0.0


def _seite_aus_reihe(x):
    r = x.get("reihe")
    if r in SHORT_REIHEN or (r == "zahlen" and x.get("zr_seite") == "short"):
        return "short"
    return "long" if r else None


def _abgelegte_marken(tk):
    """Einstieg, Stopp und Seite des Charts aus der abgelegten Titelseite (Schrank) oder None."""
    import gzip
    import pickle
    import titel
    pfad = os.path.join(titel.ABLAGE, f"{tk.upper()}.pkl.gz")
    if not os.path.exists(pfad) or not titel.frisch(tk):      # nur Seiten, die die App so auch zeigt
        return None
    try:
        with gzip.open(pfad, "rb") as f:
            teile = pickle.load(f)
    except Exception:  # noqa: BLE001
        return None
    ch = (teile or {}).get("chart") if isinstance(teile, dict) else None
    if not ch:
        return None
    mk, erk = ch.get("marken") or {}, ch.get("erk") or {}
    sh = mk.get("short") or {}
    if sh.get("einstieg"):
        seite, e, s = "short", sh["einstieg"], sh.get("stopp")
    elif mk.get("einstieg"):
        seite, e, s = "long", mk["einstieg"], mk.get("stopp")
    else:
        seite, e, s = None, None, None
    return {"reihe": (erk.get("setup_info") or {}).get("reihe"), "seite": seite, "einstieg": e, "stopp": s}


def gleichlauf(tisch, akten):
    """Wache 1: Chart und Kartentisch zeigen dasselbe Setup, dieselbe Seite und denselben Einstieg → Liste (Ampel, Text)."""
    import daten
    aus = []
    tt = tisch.get("titel") or {}
    for tk in akten:
        x = tt.get(tk) or {}
        if not x.get("reihe") or x.get("abstand_vz") is None:
            continue
        df = daten.kurse_gespeichert(tk)
        if df is None or not len(df):
            continue
        kurs = float(df["Close"].iloc[-1])
        e_tisch = (float(x["einstieg"]["wert"]) if (x.get("einstieg") or {}).get("wert")   # gespeicherter Einstieg
                   else kurs / (1 + float(x["abstand_vz"]) / 100))
        seite = _seite_aus_reihe(x)
        mk = _abgelegte_marken(tk)
        if mk:
            if mk["reihe"] and mk["reihe"] != x["reihe"]:
                aus.append(("rot", f"{tk}: Setup im Chart {mk['reihe']}, im Kartentisch {x['reihe']}"))
            if mk["seite"] and seite and mk["seite"] != seite:
                aus.append(("rot", f"{tk}: Chart zeichnet {mk['seite']}, das Setup ist {seite}"))
            if mk["einstieg"] and _pct(mk["einstieg"], e_tisch) > TOL_EINSTIEG:
                aus.append(("rot", f"{tk}: Einstieg im Chart {mk['einstieg']:.2f} $, im Kartentisch {e_tisch:.2f} $"))
            if mk["einstieg"] and mk["stopp"]:
                falsch = mk["stopp"] >= mk["einstieg"] if mk["seite"] == "long" else mk["stopp"] <= mk["einstieg"]
                if falsch:
                    aus.append(("rot", f"{tk}: Stopp {mk['stopp']:.2f} $ auf der falschen Seite des Einstiegs "
                                       f"{mk['einstieg']:.2f} $ ({mk['seite']})"))
    return aus


def plausibel(tisch, gruende, heute):
    """Wache 2 → Liste (Ampel, Text)."""
    import lagekarte
    import auswahl as auswahl_
    aus = []
    tt = tisch.get("titel") or {}
    for tk, x in tt.items():
        r = x.get("reihe")
        if x.get("gruen") and not r:
            aus.append(("rot", f"{tk}: Setup grün ohne Reihe"))
        if r and _seite_aus_reihe(x) != lagekarte.richtung(x):
            aus.append(("rot", f"{tk}: Reihe {r} ist {_seite_aus_reihe(x)}, die Lagekarte sagt {lagekarte.richtung(x)}"))
        drin, grund = gruende.get(tk, (False, ""))
        if drin and r and x.get("abstand_vz") is not None and not grund.startswith("Depot"):
            a = float(x["abstand_vz"])
            lo, hi = ((auswahl_.ZONE_SHORT if _seite_aus_reihe(x) == "short" else
                       auswahl_.ZONE_VOLLTREFFER if "Volltreffer" in grund else auswahl_.ZONE_LONG))
            if not lo - 0.05 <= a <= hi + 0.05:
                aus.append(("rot", f"{tk}: einsatzbereit mit {a:+.1f} % außerhalb der Zone {lo:+.0f} bis {hi:+.0f} %"))
        if drin:
            k_ = (x.get("kacheln") or {}).get("Nächste Zahlen")
            if k_:
                teile = list(k_)[1:3] if not isinstance(k_, dict) else [k_.get("wert"), k_.get("text")]
                m_ = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", " ".join(str(t) for t in teile))
                if m_ and "zuletzt" not in " ".join(str(t) for t in teile):
                    d = f"{m_.group(3)}-{m_.group(2)}-{m_.group(1)}"
                    if d < heute and auswahl_.termin_tage(None, k_, heute) is not None:
                        aus.append(("rot", f"{tk}: vergangener Zahlentermin {d} zählt noch"))
    return aus


def gegenprobe(akten, n=STICHPROBE):
    """Wache 3: Stichprobe gegen TradingView → Liste (Ampel, Text)."""
    import daten
    import auswahl as auswahl_
    import tpo_daten
    import tv_kennzahlen
    us = [tk for tk in akten if not tpo_daten.auslaendisch(tk)]
    if not us:
        return []
    probe = random.Random(auswahl_.HEUTE()).sample(us, min(n, len(us)))
    boerse = {}
    for tk in probe:
        z = tv_kennzahlen.zeile(tk)
        if z is not None and isinstance(z.get("exchange"), str):
            boerse[tk] = f"{z['exchange']}:{tk.replace('-', '.')}"
    if not boerse:
        return [("gelb", "Gegenprobe TradingView: keine Börse zu den Titeln bekannt")]
    try:
        roh = tv_kennzahlen._abfrage("america", {"symbols": {"tickers": list(boerse.values())},
                                                 "columns": ["close", "SMA50", "earnings_release_next_date"]})
    except Exception as e:  # noqa: BLE001
        return [("gelb", f"Gegenprobe TradingView nicht erreichbar ({type(e).__name__})")]
    zurueck = {x["s"]: x["d"] for x in roh}
    aus = []
    for tk, sym in boerse.items():
        d = zurueck.get(sym)
        df = daten.kurse_gespeichert(tk)
        if not d or df is None or len(df) < 50:
            continue
        tv_close, tv_sma, tv_er = d
        c = df["Close"]
        unser_close, unser_sma = float(c.iloc[-1]), float(c.iloc[-50:].mean())
        if tv_close and _pct(unser_close, tv_close) > TOL_KURS:
            aus.append(("rot", f"{tk}: Schluss {unser_close:.2f} $, TradingView {tv_close:.2f} $"))
        if tv_sma and _pct(unser_sma, tv_sma) > TOL_GD50:
            aus.append(("rot", f"{tk}: GD50 {unser_sma:.2f} $, TradingView {tv_sma:.2f} $"))
        if isinstance(tv_er, (int, float)) and tv_er == tv_er:
            import pandas as pd
            tv_tag = pd.Timestamp(int(tv_er), unit="s").strftime("%Y-%m-%d")
            try:
                import quellen
                fd = quellen.laden(tk)
                t_ = fd.get("termin")
                unser = f"{pd.Timestamp(t_['datum'].iloc[0]):%Y-%m-%d}" if t_ is not None and len(t_) else None
            except Exception:  # noqa: BLE001
                unser = None
            if unser and unser >= auswahl_.HEUTE() and abs((pd.Timestamp(unser) - pd.Timestamp(tv_tag)).days) > 1:
                # Micky 13.11.2026: gelb nur, wo der Termin zählt – einer der beiden liegt in den nächsten 14 Tagen
                # (die Termin-Ampel wird gelb oder rot); ferne Schätzungen weichen oft ab: stiller Hinweis (grau)
                import gestaltung
                naechster = min(pd.Timestamp(unser), pd.Timestamp(tv_tag))
                tage = (naechster - pd.Timestamp(auswahl_.HEUTE())).days
                amp = "gelb" if tage <= gestaltung.TERMIN_GELB else "grau"
                aus.append((amp, f"{tk}: Zahlentermin {unser}, TradingView {tv_tag}"
                                 + ("" if amp == "gelb" else " (Schätzung, mehr als 14 Tage entfernt – kein Alarm)")))
    return aus


def pruefen():
    """Alle Wachen; schreibt wachen.json und gibt {ampel, zeichen, stand} zurück."""
    import kartentisch
    import rueckenwind
    import rueckenwind_seite
    import auswahl as auswahl_
    import watchlists
    import depot
    heute = auswahl_.HEUTE()
    tisch = kartentisch.laden() or {}
    rw = rueckenwind.laden() or {}
    drei = {tk for tk, _ in rueckenwind_seite.dreifach_liste(rw)} if rw else set()
    pos = [p["ticker"] for p in depot.laden().get("positionen", [])]
    akten, gruende = auswahl_.auswahl(tisch.get("titel") or {}, rw.get("titel") or {}, drei, set(watchlists.alle()), pos)
    zeichen = []
    for name, f in (("Gleichlauf", lambda: gleichlauf(tisch, akten)),
                    ("Plausibilität", lambda: plausibel(tisch, gruende, heute)),
                    ("Gegenprobe", lambda: gegenprobe(akten))):
        try:
            zeichen += [(a, f"{name} · {t}") for a, t in f()]
        except Exception as e:  # noqa: BLE001 – eine Wache, die selbst scheitert, ist ein Befund
            zeichen.append(("rot", f"{name} · Wache gescheitert: {type(e).__name__}: {e}"[:200]))
    ampel = ("rot" if any(a == "rot" for a, _ in zeichen) else "gelb" if any(a == "gelb" for a, _ in zeichen)
             else "grün")                         # grau = stiller Hinweis, färbt nichts
    erg = {"stand": heute, "ampel": ampel, "akten": len(akten), "zeichen": zeichen}
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    with open(DATEI, "w", encoding="utf-8") as f:
        json.dump(erg, f, ensure_ascii=False, indent=1)
    return erg


def laden():
    try:
        return json.load(open(DATEI, encoding="utf-8"))
    except (OSError, ValueError):
        return None
