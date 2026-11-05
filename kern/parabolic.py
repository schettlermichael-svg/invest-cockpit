"""Parabolic Short im ganzen US-Markt (05.11.2026): Kullamägis A+-Fälle sind fast immer Small Caps außerhalb unseres
Reviers. Der Nachtlauf sucht deshalb in allen Massive-Tagesdateien (rund 12.000 Titel) nach Serien steigender Schlüsse
bis heute mit zusammen mindestens 300 % (Kullamägi: drei oder vier Tage in Folge, mindestens 300 %).
Ab Tag 2 gelistet (gelb), Tag 3–5 grün (er geht nie am ersten Tag short, selten am zweiten).
Mindestumsatz des letzten Tages 5 Mio. $ (Setzung der App: Kullamägi betont, dass diese Titel im Hype sehr liquide werden).
Ergebnis: daten/parabolic.json.
"""
import json
import os

import pandas as pd

import massive

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "daten", "parabolic.json")
SCHWELLE = 300.0
MIN_UMSATZ = 5e6
TAGE = 8


def suchen():
    letzte = sorted(d for d in os.listdir(massive.SPEICHER) if d[:4].isdigit() and d.endswith(".csv"))[-1]
    alle = list(massive.tag(letzte[:10])["Ticker"].dropna().astype(str).unique())
    c = massive.kursmatrix(alle, TAGE, "Close")
    v = massive.kursmatrix(alle, TAGE, "Volume")
    h = massive.kursmatrix(alle, TAGE, "High")
    treffer = []
    for tk in c.columns:
        s = c[tk].dropna().to_numpy(float)
        if len(s) < 3:
            continue
        n = 0
        while n + 1 < len(s) and s[-1 - n] > s[-2 - n]:
            n += 1
        if n < 2:
            continue
        gewinn = (s[-1] / s[-1 - n] - 1) * 100
        umsatz = float(s[-1] * (v[tk].iloc[-1] or 0))
        if gewinn < SCHWELLE or umsatz < MIN_UMSATZ:
            continue
        treffer.append({"ticker": tk.replace(".", "-"), "tag": n, "gewinn": round(gewinn), "kurs": float(s[-1]),
                        "hoch": float(h[tk].iloc[-1]), "umsatz_mio": round(umsatz / 1e6, 1),
                        "ampel": "grün" if 3 <= n <= 5 else "gelb"})
    treffer.sort(key=lambda x: (x["ampel"] != "grün", -x["gewinn"]))
    aus = {"stand": str(pd.Timestamp(letzte[:10]).date()), "treffer": treffer}
    json.dump(aus, open(DATEI + ".neu", "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(DATEI + ".neu", DATEI)
    return aus


def laden():
    if not os.path.exists(DATEI):
        return None
    return json.load(open(DATEI, encoding="utf-8"))
