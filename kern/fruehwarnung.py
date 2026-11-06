"""Frühwarnzeichen Phase 3 und 4 (Weinstein, Schritt 7, 04.11.2026) – für Long-Halter, Zeichen ohne Einfluss auf die
Phasengrenzen:
  · Bruch unter den 10-Wochen-Durchschnitt (GD50) mit hohem Volumen (mindestens 1,4-faches 50-Tage-Mittel) in den
    letzten 10 Tagen
  · Unterstützung der Gipfelzone gebrochen: Schluss unter dem tiefsten Tief der Zone des VCP-Scanners bis gestern
    (seit 06.11.2026, vorher Wertzone), nachdem der Titel in Phase 2 oder 3 lief
"""
import re

import numpy as np


def deutsch(text):
    """Dezimalpunkt → Komma (Datumsangaben bleiben)."""
    return re.sub(r"(?<!\.\d)(?<!\.\d\d)(\d)\.(\d+)(?![\d.])", r"\1,\2", text)

VOLUMEN_HOCH = 1.4
FENSTER = 10


def _zeichen(df, erk, phase):
    c, v = df["Close"].to_numpy(float), df["Volume"].to_numpy(float)
    n = len(c)
    aus = []
    if n < 120 or phase not in (2, 3):
        return aus
    g = np.convolve(c, np.ones(50) / 50, mode="valid")          # g[j] = GD50 am Tag j+49
    vs = np.convolve(v, np.ones(50) / 50, mode="valid")
    for i in range(n - FENSTER, n):
        j = i - 49
        if j < 1:
            continue
        if c[i] < g[j] and c[i - 1] >= g[j - 1] and v[i] >= VOLUMEN_HOCH * vs[j - 1]:
            aus.append(("rot" if c[-1] < g[-1] else "gelb",
                        f"Frühwarnung (Weinstein): Bruch unter den 10-Wochen-Durchschnitt am {df.index[i]:%d.%m.} mit "
                        f"{v[i] / vs[j - 1]:.1f}-fachem Volumen"
                        + ("" if c[-1] < g[-1] else " – inzwischen zurückerobert")))
            break
    z = erk.get("scanner_zone")
    if z and z.get("start_i") is not None and z["start_i"] < n - 2:
        u = float(df["Low"].to_numpy(float)[z["start_i"]:n - 1].min())
        if c[-1] < u:
            aus.append(("rot", f"Frühwarnung (Weinstein): Unterstützung der Gipfelzone gebrochen – Schluss {c[-1]:.2f} unter "
                               f"der Unterkante der Zone {u:.2f} in Phase {phase}"))
    return aus


def zeichen(*args):
    return [tuple(deutsch(x) if isinstance(x, str) else x for x in z) for z in _zeichen(*args)]
