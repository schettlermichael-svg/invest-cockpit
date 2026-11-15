"""Volumenprofil nach der Auction Market Theory: wie viel Volumen bei welchem Preis gehandelt wurde.

Aus Tageskerzen genähert: Das Volumen jedes Tages wird gleichmäßig über seine Tagesspanne (Tief bis Hoch) verteilt.
Seit 13.11.2026 verankert nach Ereignis und Struktur, seit 14.11.2026 nach Dalton (Balance) und Shannon (verankert(), Anker aus avwap.profil_anker) statt starr über 52 Wochen. Knoten (High Volume Node): jeder Gipfel des
geglätteten Profils, der sich klar aus den Tälern (Low Volume Nodes) links und rechts erhebt – dort hat der Markt den
Preis akzeptiert. Seit 14.11.2026 auch Nebengipfel (Chart-Prüfer, LUV: das Angebot bei 47–49,50 $ lag bei 42 % des
größten Volumens und fehlte, solange nur Zonen ab 60 % zählten). Wertbereich: die 70 % des Volumens um den meistgehandelten Preis (Point of Control).
"""
import numpy as np
import pandas as pd

FAECHER = 48
from marketprofile import WERT  # noqa: E402  Wertbereich 70 % des Volumens (Dalton) – eine Quelle
GIPFEL_MIN = 0.30           # Knoten: Gipfel mit mindestens 30 % des größten Volumens …
GIPFEL_UEBER = 0.10         # … der mindestens 10 % (des größten) über dem höheren der beiden Täler daneben liegt


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
GLAETTEN = 3  # Profil über 3 Stufen geglättet, bevor die Gipfel gesucht werden


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
    """Knoten als Preiszonen [(unten, oben)]: jeder Gipfel des geglätteten Profils ab GIPFEL_MIN, der sich mindestens
    GIPFEL_UEBER über das höhere der beiden Täler daneben erhebt; die Zone reicht so weit, wie das Volumen über der
    halben Höhe zwischen Tal und Gipfel bleibt."""
    v = np.convolve(p["volumen"], np.ones(GLAETTEN) / 3, mode="same")
    g, n = p["grenzen"], len(v)
    if not n or v.max() <= 0:
        return []
    v = v / v.max()
    aus = []
    for i in range(n):
        if v[i] < GIPFEL_MIN or (i > 0 and v[i - 1] > v[i]) or (i < n - 1 and v[i + 1] > v[i]):
            continue
        if i > 0 and v[i - 1] == v[i]:                  # Plateau: nur einmal zählen
            continue
        a_ = i
        while a_ > 0 and v[a_ - 1] <= v[a_]:
            a_ -= 1
        b_ = i
        while b_ < n - 1 and v[b_ + 1] <= v[b_]:
            b_ += 1
        tal = max(v[a_] if a_ > 0 else 0.0, v[b_] if b_ < n - 1 else 0.0)
        if v[i] - tal < GIPFEL_UEBER:
            continue
        halb = tal + (v[i] - tal) / 2
        lo, hi = i, i
        while lo > a_ and v[lo - 1] >= halb:
            lo -= 1
        while hi < b_ and v[hi + 1] >= halb:
            hi += 1
        aus.append((float(g[lo]), float(g[hi + 1])))
    return aus


def verankert(df, zahltag=None, zone_start=None):
    """Volumenprofil nach den Ankern aus avwap.profil_anker (Micky 13.11.2026: nie aus dem Kalender) →
    {grau: {profil, ab, art, tage}, mauer: (unten, oben, ab) oder None, stuetze: (unten, oben, ab) oder None,
    knoten: [(unten, oben)] – alle Knoten von grau, Hoch und Tief für die Hürde der Lagekarte} oder None.
    Mauer: der nächste Knoten über dem Kurs im Profil seit dem Hoch des Rückgangs bzw. dem letzten Hoch (das Angebot
    der gefangenen Käufer). Stütze: der nächste Knoten unter dem Kurs seit dem Tief der Bewegung (die Käufer im
    Gewinn). Das graue Profil beginnt mit der laufenden Balance (avwap.balance_beginn, Dalton)."""
    import avwap
    a = avwap.profil_anker(df, zahltag, zone_start)
    if not a:
        return None
    kurs = float(df["Close"].iloc[-1])
    pos = lambda t: int(df.index.searchsorted(pd.Timestamp(t)))      # noqa: E731
    g_tag, g_art = a["grau"]
    pg = profil(df, pos(g_tag))
    aus = {"grau": {"profil": pg, "ab": g_tag, "art": g_art, "tage": int((df.index >= g_tag).sum())} if pg else None,
           "mauer": None, "stuetze": None, "knoten": list(knoten(pg)) if pg else []}
    for schl, tag in (("mauer", a["mauer"]), ("stuetze", a["stuetze"])):
        if tag is None:
            continue
        p = profil(df, pos(tag))
        if not p:
            continue
        kn = knoten(p)
        aus["knoten"] += kn
        kn = [k for k in kn if (k[0] > kurs if schl == "mauer" else k[1] < kurs)]
        if kn:
            k0, k1 = min(kn) if schl == "mauer" else max(kn)
            aus[schl] = (k0, k1, tag)
    aus["knoten"] = sorted(set(aus["knoten"]))
    return aus
