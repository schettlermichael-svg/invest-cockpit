"""Anchored VWAP nach Brian Shannon (10.11.2026): bedeutsame Anker, die sich aus den Kursen eindeutig ergeben – eine
Quelle für den Chart der Titelseite (Wahlschalter) und die Akte des Stabs.

  hoch      Hoch der letzten 52 Wochen
  tief      Tief der letzten 6 Monate
  ereignis  jüngster Ereignistag der letzten 6 Monate: Kurslücke ab 4 % mit mindestens doppeltem 50-Tage-Volumen
            (meist Zahlen oder eine Nachricht)
  zone      Beginn der aktuellen Zone (Anker des VCP-Scanners; kommt aus den Chartmarken, nicht von hier)

Hoch und Tief zusammen sind Shannons Zange („Pinch“): laufen beide Linien eng zusammen, steht eine Entscheidung an."""
import numpy as np
import pandas as pd

NAMEN = {"hoch": "Hoch 52 Wochen", "tief": "Tief 6 Monate", "ereignis": "Ereignistag", "zone": "Beginn der Zone"}
LUECKE, VOLUMEN_FACH = 0.04, 2.0
PINCH_PCT = 3.0


def anker(df):
    """{"hoch"|"tief"|"ereignis": Tag} aus Tageskerzen (fehlt ein Anker, fehlt der Schlüssel)."""
    if df is None or len(df) < 30 or not {"High", "Low", "Close", "Volume"} <= set(df.columns):
        return {}
    d = df.iloc[-252:]
    aus = {"hoch": d["High"].idxmax(), "tief": d["Low"].iloc[-126:].idxmin()}
    if "Open" in d.columns:
        vol50 = df["Volume"].rolling(50).mean().shift(1).reindex(d.index)
        luecke = (d["Open"] / d["Close"].shift(1) - 1).abs()
        tage = d.index[(luecke >= LUECKE) & (d["Volume"] >= VOLUMEN_FACH * vol50)]
        tage = [t for t in tage if t >= d.index[-126]]
        if tage:
            aus["ereignis"] = tage[-1]
    return aus


def reihe(df, ab):
    """AVWAP ab dem Tag `ab` (typischer Preis × Volumen, aufsummiert) als Reihe; leer, wenn zu wenig Kerzen."""
    t_ = df[df.index >= pd.Timestamp(ab)]
    if len(t_) < 2:
        return pd.Series(dtype=float)
    tp = (t_["High"] + t_["Low"] + t_["Close"]) / 3
    return ((tp * t_["Volume"]).cumsum() / t_["Volume"].cumsum().replace(0, np.nan)).dropna()
