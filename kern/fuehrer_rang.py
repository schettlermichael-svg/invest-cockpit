"""Führer nach Kullamägi (05.11.2026): Er sucht die ein bis zwei Prozent der Aktien mit den größten Kursanstiegen in den
vergangenen ein, drei und sechs Monaten (Interview mit Jack Schwager). Hier: Perzentil jedes Revier-Titels für die
Entwicklung über 21, 63 und 126 Handelstage. Führer = in mindestens einem Zeitraum unter den obersten 2 %.

Quelle: Massive-Tagesdateien wie beim RS-Rang. Ergebnis je Kursstand einmal gerechnet, daten/fuehrer_rang.csv.
"""
import os

import pandas as pd

import massive

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "daten", "fuehrer_rang.csv")
REVIER = os.path.join(HIER, "..", "einstellungen", "revier.csv")
ZEITRAEUME = {"1 M": 21, "3 M": 63, "6 M": 126}
OBEN = 98.0                  # oberste 2 % (Kullamägi: „ein oder zwei Prozent“)
NAH = 95.0                   # gelb: oberste 5 %


_CACHE = {}


def _zahl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def raenge():
    """{ticker: {"1 M": Perzentil, "3 M": …, "6 M": …}}, stand."""
    if os.path.exists(DATEI):
        zeit = os.path.getmtime(DATEI)
        if _CACHE.get("zeit") == zeit:
            return _CACHE["daten"]
        alt = pd.read_csv(DATEI, keep_default_na=False)
        stand = alt["stand"].iloc[0] if len(alt) else ""
        tage = sorted(f[:10] for f in os.listdir(massive.SPEICHER) if f[:4].isdigit() and f.endswith(".csv"))
        if tage and stand == tage[-1]:
            d = {r["ticker"]: {z: _zahl(r[z]) for z in ZEITRAEUME} for r in alt.to_dict("records")}, stand
            _CACHE.update(zeit=zeit, daten=d)
            return d
    rv = pd.read_csv(REVIER, keep_default_na=False)
    m = massive.kursmatrix(list(rv["ticker"]), max(ZEITRAEUME.values()) + 1, "Close")
    spalten = {}
    for z, n in ZEITRAEUME.items():
        w = (m.iloc[-1] / m.iloc[-1 - n] - 1).dropna()
        spalten[z] = (w.rank(pct=True) * 100).round(1)
    t = pd.DataFrame(spalten).dropna(how="all")
    t.index = [str(x).replace(".", "-") for x in t.index]
    stand = str(m.index[-1].date())
    aus = t.reset_index().rename(columns={"index": "ticker"})
    aus["stand"] = stand
    tmp = f"{DATEI}.{os.getpid()}"               # atomar: parallele Prozesse lesen nie eine halbe Datei
    aus.to_csv(tmp, index=False)
    os.replace(tmp, DATEI)
    return {tk: {z: float(r[z]) for z in ZEITRAEUME} for tk, r in t.iterrows()}, stand


def von(ticker):
    """Perzentile eines Titels oder None."""
    r, _ = raenge()
    return r.get(ticker.upper())


def ampel(p):
    """Führer-Ampel aus den Perzentilen: grün = oberste 2 % in einem Zeitraum, gelb = oberste 5 %, sonst rot."""
    if not p:
        return "grau"
    werte = [v for v in p.values() if v == v]
    if not werte:
        return "grau"
    best = max(werte)
    return "grün" if best >= OBEN else "gelb" if best >= NAH else "rot"


def text(p):
    if not p:
        return "keine Daten"
    def zahl(v):
        return (f"{v:.1f}" if v >= 90 else f"{v:.0f}").replace(".", ",")
    return " · ".join(f"{z} besser als {zahl(v)} %" for z, v in p.items() if v == v)
