"""Volumenprofil nach der Auction Market Theory: wie viel Volumen bei welchem Preis gehandelt wurde.

Aus Tageskerzen genähert: Das Volumen jedes Tages wird gleichmäßig über seine Tagesspanne (Tief bis Hoch) verteilt.
Im Chart über die letzten 52 Wochen (JAHR) als Spalte rechts. Knoten (High Volume Node): zusammenhängende Preiszonen
mit mindestens 60 % des größten geglätteten Volumens – dort hat der Markt den Preis akzeptiert. Wertbereich: die 70 % des Volumens um den meistgehandelten Preis (Point of Control).
"""
import numpy as np

FAECHER = 48
KNOTEN, WERT = 0.60, 0.70   # Knoten: mindestens 60 % des größten (geglätteten) Volumens
JAHR = 252


def profil(df, start, ende=None):
    """Volumen je Preisfach von start bis ende (einschließlich): Fachgrenzen, Volumen, meistgehandelter Preis und
    Wertbereich."""
    t = df.iloc[start:(ende + 1) if ende is not None else None]
    lo, hi = float(t["Low"].min()), float(t["High"].max())
    if not hi > lo:
        return None
    grenzen = np.linspace(lo, hi, FAECHER + 1)
    vol = np.zeros(FAECHER)
    for tl, th, tv in zip(t["Low"].to_numpy(float), t["High"].to_numpy(float), t["Volume"].to_numpy(float)):
        if not tv > 0:
            continue
        if th <= tl:
            vol[min(FAECHER - 1, int((tl - lo) / (hi - lo) * FAECHER))] += tv
            continue
        ueber = np.clip(np.minimum(grenzen[1:], th) - np.maximum(grenzen[:-1], tl), 0, None)
        vol += tv * ueber / (th - tl)
    mitte = (grenzen[:-1] + grenzen[1:]) / 2
    i_poc = int(np.argmax(vol))
    # Wertbereich: vom meistgehandelten Fach aus nach oben und unten erweitern, bis 70 % erreicht sind
    a = b = i_poc
    summe, ziel = vol[i_poc], WERT * vol.sum()
    while summe < ziel and (a > 0 or b < FAECHER - 1):
        unten = vol[a - 1] if a > 0 else -1
        oben = vol[b + 1] if b < FAECHER - 1 else -1
        if oben >= unten:
            b += 1
            summe += vol[b]
        else:
            a -= 1
            summe += vol[a]
    return {"grenzen": grenzen, "volumen": vol, "mitte": mitte, "poc": float(mitte[i_poc]),
            "wert_unten": float(grenzen[a]), "wert_oben": float(grenzen[b + 1])}


def knoten(p):
    """Knoten als Preiszonen [(unten, oben)] aus dem geglätteten Profil."""
    v = np.convolve(p["volumen"], np.ones(3) / 3, mode="same")
    g, maske, aus, i = p["grenzen"], v >= KNOTEN * v.max(), [], 0
    while i < len(maske):
        if maske[i]:
            j = i
            while j + 1 < len(maske) and maske[j + 1]:
                j += 1
            aus.append((float(g[i]), float(g[j + 1])))
            i = j + 1
        else:
            i += 1
    return aus
