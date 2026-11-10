"""Fußabdruck der großen Käufer in der Base (O'Neil: Akkumulation/Distribution; Minervini: Volumen trocknet
aus) und Volumen am Ausbruchstag.

Gemessen wird an Tageskursen:
- Auf-/Ab-Volumen: Volumen der Tage mit höherem Schluss geteilt durch das der Tage mit tieferem Schluss in der
  Base (IBD rechnet dieses Verhältnis über 50 Tage; über 1 = es wird mehr gekauft als verkauft).
- Akkumulations- und Distributionstage: Volumen über dem 1,25-fachen Schnitt der 50 Tage davor, Schluss höher
  bzw. tiefer als am Vortag.
- Trockenfallen: Schnitt der letzten 10 Tage vor dem Ausbruch (oder bis heute; bei kurzen Flaggen ab 5 Tagen)
  gegen den Schnitt der 50 Tage davor.
- Ausbruchsvolumen: erster Tag, an dem der Kurs den Pivot überschreitet (Tageshoch; dort greift die Kauforder),
  Volumen gegen den 50-Tage-Schnitt der Tage davor (O'Neil: mindestens 40–50 % über dem Schnitt). Schließt der
  Tag wieder unter dem Pivot, wird das vermerkt.

Schwellen (unsere Setzung, nicht aus dem Buch, außer dem Ausbruchsvolumen): Fußabdruck grün ab Verhältnis 1,1
und nicht mehr Distributions- als Akkumulationstage, rot unter 0,9 mit mindestens zwei Distributionstagen mehr
als Akkumulationstagen. Trocken ab 0,8-fach. Ausbruch (05.11.2026): grün über dem 50-Tage-Schnitt, sonst rot (Minervini: mehr Volumen als
üblich; O'Neils strengere 40–50 % stehen als Faktor daneben). Dazu als Zeichen die Spanne des Ausbruchstags gegen die
ATR (14 Tage): wie weit der Kurs an diesem Tag gegen das Übliche vorstößt.
"""
import numpy as np

HOHES_VOLUMEN = 1.25
FUSS_GRUEN, FUSS_ROT = 1.1, 0.9
TROCKEN = 0.8
AUSBRUCH_GRUEN = 1.0            # über dem 50-Tage-Schnitt


def atr_spanne(df, i):
    """Echte Spanne (True Range) von Tag i gegen die ATR der 14 Tage davor, z. B. 1,8 = 1,8 × ATR; None ohne Daten."""
    h, l, c = (df[k].to_numpy(float) for k in ("High", "Low", "Close"))
    i = int(i)
    if i < 15:
        return None
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))   # tr[k] gehört zu Tag k+1
    atr = float(np.mean(tr[i - 15:i - 1]))
    return float(tr[i - 1] / atr) if atr > 0 else None



def _schnitt50(v, i):
    """Schnitt der 50 Tage vor Tag i (ohne Tag i)."""
    a = max(0, i - 50)
    return float(np.mean(v[a:i])) if i - a >= 20 else None


def fussabdruck(df, start, ende=None, pivot=None):
    """start/ende: Indizes der Base in df (ende = letzter Tag der Base, sonst der letzte Tag).
    Liefert ein Wörterbuch mit Ampel, Kennzahlen und Text oder None, wenn zu wenig Daten da sind."""
    c, v, h = (df[k].to_numpy(float) for k in ("Close", "Volume", "High"))
    n = len(c)
    ende = n - 1 if ende is None else int(ende)
    start = max(1, int(start))
    if ende - start < 5 or np.nansum(v[start:ende + 1]) <= 0:
        return None
    auf = ab = 0.0
    akk = dist = 0
    for i in range(start, ende + 1):
        s = _schnitt50(v, i)
        if c[i] > c[i - 1]:
            auf += v[i]
            akk += bool(s and v[i] > HOHES_VOLUMEN * s)
        elif c[i] < c[i - 1]:
            ab += v[i]
            dist += bool(s and v[i] > HOHES_VOLUMEN * s)
    verh = auf / ab if ab > 0 else None

    # Ausbruch: erster Tag nach dem Tief der Base, dessen Hoch über dem Pivot liegt
    ausbruch = None
    if pivot:
        tief = start + int(np.argmin(c[start:ende + 1]))
        for i in range(tief + 1, n):
            if h[i] > pivot:
                s = _schnitt50(v, i)
                if s:
                    ausbruch = {"index": i, "faktor": v[i] / s, "schluss_darueber": bool(c[i] > pivot)}
                break
    bis = ausbruch["index"] if ausbruch else n
    k = min(10, bis - start)                     # bei kurzen Flaggen die ganze Flagge, mindestens 5 Tage
    s_end = _schnitt50(v, bis - k)               # Schnitt der 50 Tage vor diesen ruhigen Tagen
    trocken = float(np.mean(v[bis - k:bis])) / s_end if s_end and k >= 5 else None

    if verh is None:
        ampel = "grau"
    elif verh >= FUSS_GRUEN and akk >= dist:
        ampel = "grün"
    elif verh < FUSS_ROT and dist >= akk + 2:     # ein einzelner Distributionstag ist noch kein Muster
        ampel = "rot"
    else:
        ampel = "gelb"
    erg = {"ampel": ampel, "verhaeltnis": verh, "akk": akk, "dist": dist, "trocken": trocken, "ausbruch": None}
    if ausbruch:
        f = ausbruch["faktor"]
        erg["ausbruch"] = {"index": ausbruch["index"], "faktor": f, "schluss_darueber": ausbruch["schluss_darueber"],
                           "ampel": "grün" if f > AUSBRUCH_GRUEN else "rot",
                           "atr": atr_spanne(df, ausbruch["index"])}
    elif pivot:
        s = _schnitt50(v, n)
        erg["noetig"] = AUSBRUCH_GRUEN * s if s else None
    return erg
