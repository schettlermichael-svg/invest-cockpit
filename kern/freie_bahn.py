"""Freie Bahn: wie viel Luft hat der Kurs bis zum nächsten Widerstand (Long) bzw. bis zur nächsten Unterstützung
(Short)? Zwei unabhängige Quellen, im Chart beide sichtbar:

1. Wendepunkte – das nächste frühere Hoch über dem Bezug bzw. Tief darunter. Als Hoch oder Tief zählt ein Tag, der
   10 Handelstage vor und nach sich das höchste Hoch bzw. tiefste Tief hat, gesucht in den letzten drei Jahren, und
   der seither nicht durchbrochen wurde (O'Neil: Überhang, „overhead supply").
2. Volumenknoten – Preiszonen, in denen zwischen Anker und heute viel gehandelt wurde (kern/volumenprofil.py,
   Auction Market Theory): dort hat der Markt den Preis akzeptiert.

Liegen Wendepunkt und Knoten innerhalb von 2 % beieinander, ist die Marke „doppelt“; liegt zusätzlich der AVWAP ab dem
52-Wochen-Hoch in dieser Nähe, „dreifach“. Ein Hoch ohne Knoten ist „dünn“ (wenig Umsatz, wird oft überlaufen), ein
Knoten ohne Wendepunkt „verdeckt“. Die Luft gilt bis zur nächsten Marke, gleich welcher Art.

3. Alte Pivots (seit 03.11.2026) – der Pivot einer früheren Base, die ausgebrochen ist und deren Pivot seither kein
   Schluss unterschritten hat: nach O'Neil wird der alte Kaufpunkt zur Unterstützung. Zählt auf der Short-Seite wie ein
   Tief („alter Pivot“).

Bezug: beim Long der Pivot einer Base (dort wird gekauft), sonst der Kurs; beim Short der Kurs.
Ampel (unsere Setzung, nicht aus dem Buch; O'Neil nimmt 20–25 % Gewinn mit): grün ab 20 % Luft, gelb ab 10 %,
rot darunter. Reines Zeichen, kein Einfluss auf das Kaufsetup.
"""
import numpy as np

import volumenprofil

FENSTER = 10            # Handelstage links und rechts eines Wendepunkts (zwei Wochen: Wendepunkt im Wochenchart)
TAGE = 756              # drei Jahre
NAH = 0.01              # Marken innerhalb 1 % des Bezugs zählen nicht (dort steht der Kurs schon)
ZUSAMMEN = 0.02         # Wendepunkt, Knoten und AVWAP innerhalb 2 % gelten als eine Marke
GRUEN, GELB = 20.0, 10.0


def _ampel(luft):
    return "grün" if luft is None or luft >= GRUEN else "gelb" if luft >= GELB else "rot"


def wendepunkte(df):
    h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
    n = len(h)
    a = max(0, n - TAGE)
    hochs, tiefs = [], []
    for i in range(a, n - 1):
        lo, hi = max(a, i - FENSTER), min(n, i + FENSTER + 1)
        # nur Marken, die seither nicht durchbrochen wurden: ein überstiegenes Hoch ist kein Widerstand mehr,
        # ein unterschrittenes Tief keine Unterstützung
        if h[i] >= h[lo:hi].max() and h[i] >= h[i + 1:].max():
            hochs.append((i, float(h[i])))
        if l[i] <= l[lo:hi].min() and l[i] <= l[i + 1:].min():
            tiefs.append((i, float(l[i])))
    return hochs, tiefs


def _avwap_hoch(df):
    a = max(0, len(df) - volumenprofil.JAHR)
    i = a + int(np.argmax(df["High"].to_numpy(float)[a:]))
    t = df.iloc[i:]
    tp = (t["High"] + t["Low"] + t["Close"]) / 3
    return float((tp * t["Volume"]).sum() / t["Volume"].sum()) if t["Volume"].sum() > 0 else None


def nah_zone(x, zone):
    return zone[0] * (1 - ZUSAMMEN) <= x <= zone[1] * (1 + ZUSAMMEN)


def alte_pivots(df, historie):
    """Pivots früherer Basen, die noch tragen: Ausbruch erfolgt, seither kein Schluss unter dem Pivot.
    Liste (Index des Ausbruchs, Pivot)."""
    c = df["Close"].to_numpy(float)
    aus = []
    for b in historie or []:
        a, pv = b.get("ausbruch"), b.get("pivot")
        if a is None or not pv or a >= len(c) - 1:
            continue
        if c[a:].min() >= pv:
            aus.append((int(a), float(pv)))
    return aus


def _seite(bezug, wend, knoten, avwap, oben, pivots=()):
    """Nächste Marke einer Seite aus Wendepunkten und Knoten; dazu bis zu zwei Marken je Art für den Chart.
    pivots: alte Pivots (Index, Preis), schon in wend enthalten – nur für die Benennung."""
    pivot_marken = set(pivots)
    pivots = {i for i, _ in pivots}
    if oben:
        w = sorted([(i, x) for i, x in wend if x > bezug * (1 + NAH)], key=lambda t: t[1])
        k = sorted([z for z in knoten if z[0] > bezug * (1 + NAH)], key=lambda z: z[0])
        k_preis = lambda z: z[0]                                    # noqa: E731 – Angebot beginnt am unteren Rand
    else:
        w = sorted([(i, x) for i, x in wend if x < bezug * (1 - NAH)], key=lambda t: -t[1])
        k = sorted([z for z in knoten if z[1] < bezug * (1 - NAH)], key=lambda z: -z[1])
        k_preis = lambda z: z[1]                                    # noqa: E731 – Nachfrage beginnt am oberen Rand
    kand = [(x, "wend", (i, x)) for i, x in w[:1]] + [(k_preis(z), "knoten", z) for z in k[:1]]
    if not kand:
        return {"bezug": bezug, "marke": None, "index": None, "luft": None, "art": None,
                "wend": w[:2], "knoten": k[:2]}
    preis, quelle, obj = (min if oben else max)(kand, key=lambda t: t[0])
    zone = k[0] if k else None

    def nah(x):
        """x gehört zur Marke: innerhalb 2 % des Preises oder (bei einem Knoten) innerhalb der Zone ± 2 %."""
        if abs(x / preis - 1) <= ZUSAMMEN:
            return True
        return bool("knoten" in teile and zone and zone[0] * (1 - ZUSAMMEN) <= x <= zone[1] * (1 + ZUSAMMEN))
    teile = {quelle}
    if quelle == "wend" and zone and nah_zone(w[0][1], zone):
        teile.add("knoten")
    if quelle == "knoten" and w and nah_zone(w[0][1], zone):
        teile.add("wend")
    if avwap and nah(avwap):
        teile.add("avwap")
    wort = "Hoch" if oben else ("alter Pivot" if w and w[0][0] in pivots and w[0] in pivot_marken else "Tief")
    if len(teile) == 3:
        art = f"dreifach ({wort}, Knoten und AVWAP)"
    elif teile == {"wend", "knoten"}:
        art = f"doppelt ({wort} im Knoten)"
    elif teile == {"wend", "avwap"}:
        art = f"doppelt ({wort} und AVWAP)"
    elif teile == {"knoten", "avwap"}:
        art = "doppelt (Knoten und AVWAP)"
    elif quelle == "wend":
        art = f"nur {wort}, dünn"
    else:
        art = "Knoten, verdeckt"
    luft = (preis / bezug - 1) * 100 if oben else (1 - preis / bezug) * 100
    index = w[0][0] if w and "wend" in teile else None
    return {"bezug": bezug, "marke": preis, "index": index, "luft": luft, "art": art, "wend": w[:2], "knoten": k[:2],
            "zone": zone if "knoten" in teile else None}


def freie_bahn(df, pivot=None, mit_base=False, historie=None):
    """Liefert {'long': {...}, 'short': {...}, 'profil': {...}} – je Seite Bezug, Marke, Art, Luft in %, Ampel und die
    Marken für den Chart; dazu das Volumenprofil mit Anker, Knoten und Lücken."""
    k = float(df["Close"].iloc[-1])
    hochs, tiefs = wendepunkte(df)
    # Anker fest: die letzten 52 Wochen – das Fenster enthält Jahreshoch und Jahrestief und damit das Gelände über
    # und unter dem Kurs, für long und short gleich (4.11.2026; vorher am 52-Wochen-Hoch bzw. -Tief verankert)
    i_anker, art_anker = max(0, len(df) - volumenprofil.JAHR), "52 Wochen"
    p = volumenprofil.profil(df, i_anker)
    z = volumenprofil.zonen(p) if p else {"knoten": [], "luecken": []}
    av = _avwap_hoch(df)
    long = _seite(pivot if pivot else k, hochs, z["knoten"], av, True)
    alt = [(i, x) for i, x in alte_pivots(df, historie) if x < k]
    short = _seite(k, tiefs + alt, z["knoten"], av, False, alt)
    long["ampel"], short["ampel"] = _ampel(long["luft"]), _ampel(short["luft"])
    im_knoten = next((z_ for z_ in z["knoten"] if z_[0] <= k <= z_[1]), None)   # Kurs in der Balance
    return {"long": long, "short": short, "im_knoten": im_knoten,
            "profil": dict(p or {}, anker=i_anker, anker_art=art_anker, **z) if p else None}
