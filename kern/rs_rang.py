"""RS-Rang im Revier (1–99), gerechnet wie das RS-Rating von IBD: Kursentwicklung der letzten 12 Monate, das jüngste
Quartal doppelt gewichtet (40 % letztes Quartal, je 20 % die drei davor), als Rang unter allen Revier-Titeln.

Quelle: Massive-Tagesdateien (alle Titel des Reviers am selben Tag). Ergebnis je Kursstand einmal gerechnet und in
daten/rs_rang.csv gespeichert.
"""
import os

import pandas as pd

import massive

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "daten", "rs_rang.csv")
REVIER = os.path.join(HIER, "..", "einstellungen", "revier.csv")


def wert(schluss):
    """Gewichtete 12-Monats-Entwicklung je Titel aus einer Matrix von Schlusskursen (Zeilen Tage, Spalten Titel)."""
    q = [schluss.iloc[-1] / schluss.iloc[-1 - 63 * k] - 1 for k in (1, 2, 3, 4)]
    return 0.4 * q[0] + 0.2 * q[1] + 0.2 * q[2] + 0.2 * q[3]


def raenge():
    """Rang 1–99 je Ticker zum letzten Kursstand (aus dem Speicher, sonst neu gerechnet)."""
    if os.path.exists(DATEI):
        alt = pd.read_csv(DATEI, keep_default_na=False)
        stand = alt["stand"].iloc[0] if len(alt) else ""
        tage = sorted(f[:10] for f in os.listdir(massive.SPEICHER) if f[:4].isdigit() and f.endswith(".csv"))
        if tage and stand == tage[-1]:            # neuester gespeicherter Handelstag: Rang ist aktuell
            return dict(zip(alt["ticker"], alt["rang"])), stand
    rv = pd.read_csv(REVIER, keep_default_na=False)
    m = massive.kursmatrix(list(rv["ticker"]), 260, "Close")
    w = wert(m).dropna()
    rang = (w.rank(pct=True) * 98 + 1).round().astype(int)
    stand = str(m.index[-1].date())
    pd.DataFrame({"ticker": rang.index, "rang": rang.values, "stand": stand}).to_csv(DATEI, index=False)
    return rang.to_dict(), stand


_RW = {}


def _rueckenwind_raenge():
    """RS-Ränge aus Rückenwind ({Ticker: Rang}, Stand) – einmal je Datei gelesen."""
    import rueckenwind
    pfad = rueckenwind._pfad("stand.json")
    if not os.path.exists(pfad):
        return {}, None
    m = os.path.getmtime(pfad)
    if _RW.get("m") != m:
        from dateien import json_lesen
        e = json_lesen(pfad) or {}
        _RW.update(m=m, stand=e.get("stand"),
                   r={tk: int(x["rang"]) for tk, x in (e.get("titel") or {}).items() if x.get("rang") is not None})
    return _RW["r"], _RW["stand"]


def rang(ticker):
    """Der eine RS-Rang der App (Prüf-Agent 12.11.2026: vorher zwei – hier nur Revier mit voller Historie, in Rückenwind
    auch Watchlist und junge Titel; die Stärke-Kachel zeigte dann „RS 68“ neben „RS-Rang 72“). Quelle: Rückenwind, wenn
    er auf demselben Handelstag steht; sonst die Revier-Rechnung hier."""
    r, stand = raenge()
    try:
        rw, rw_stand = _rueckenwind_raenge()
        if rw_stand == stand and ticker.upper() in rw:
            return rw[ticker.upper()], stand
    except Exception:  # noqa: BLE001
        pass
    return r.get(ticker.upper()), stand
