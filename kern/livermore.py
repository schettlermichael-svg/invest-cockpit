"""Livermores Notizbuch (Market Key) je Titel – Micky 25.11.2026: „Der Zirkel deutet, Livermore liefert das System.“

Quelle: Jesse L. Livermore, How to Trade in Stocks (1940), Kapitel VIII „The Livermore Market Key“ und IX
„Explanatory Rules“ (Regeln 1–10). Jeder Tag wird in eine von sechs Spalten eingetragen:

  SE Sekundäre Erholung · NE Natürliche Erholung · AT Aufwärtstrend (schwarze Tinte)
  AB Abwärtstrend (rote Tinte) · NR Natürliche Reaktion · SR Sekundäre Reaktion   (die vier übrigen in Bleistift)

Schwellen (Micky 25.11.2026): Livermores ~6 Punkte für einen Schwung = SCHWUNG × ATR (dieselben 2 ATR wie die
Wendepunkte im Chart, vcp_zone.GROB), seine ~3 Punkte zur Bestätigung = BESTAETIGUNG × ATR. Hochs zählen mit dem
Tageshoch, Tiefs mit dem Tagestief – so sind seine Pivotal Points dieselben Punkte wie die grauen Wendepunkte.

Regeln (verkürzt, Nummern wie im Buch):
  4   Pivot-Linien beim Spaltenwechsel nach einem Schwung: rot unter dem letzten Kurs im AT (→ NR) und unter dem letzten
      Kurs der NR (→ NE/AT); schwarz unter dem letzten Kurs im AB (→ NE) und unter dem letzten Kurs der NE (→ NR/AB).
  5   Aus NE ≥ Bestätigung über dem letzten schwarz unterstrichenen NE-Kurs → AT; aus NR ≥ Bestätigung unter dem letzten
      rot unterstrichenen NR-Kurs → AB.
  6   Wechsel nach einem Schwung; NE über dem letzten AT-Kurs → AT, NR unter dem letzten AB-Kurs → AB; eine Erholung
      aus der NR, die die letzte NE nicht übertrifft → SE (bis sie es tut), gespiegelt SR.
  7/8 Der letzte Trendkurs wird Pivotal Point beim Wechsel in NE/NR, ebenso das Extrem der NE/NR beim Wechsel zurück.
  10  b) nach einem Aufwärtstrend fällt die NR um die Bestätigung unter den letzten rot unterstrichenen NR-Kurs (das
      vorige Reaktionstief dieses Laufs – ein Punkt, den der Abwärtstrend schon unterschritten hat, ist verbraucht und
      zählt nicht mehr; gespiegelt oben): Aufwärtstrend vorbei · d) gespiegelt: Abwärtstrend vorbei · a) dasselbe in Trendrichtung:
      Pivotal Point bestätigt · e) NE endet kurz (≤ Bestätigung) unter dem AT-Pivotal-Point und
      fällt dann um die Bestätigung: Gefahrensignal, der Aufwärtstrend ist zu Ende · f) gespiegelt.
"""
import numpy as np
import pandas as pd

SCHWUNG = 2.0             # Livermores ~6 Punkte = 2 × ATR (wie vcp_zone.GROB, die Wendepunkte)
BESTAETIGUNG = 1.0        # Livermores ~3 Punkte = 1 × ATR
STELLUNG_JAHRE = 2        # Stellungen: stehende Pivotal Points der letzten 2 Jahre (so weit reichen die Massive-Tage der
                          # Liste – Titelseite, Chart, Liste und Zeichen sehen dieselben Stellungen)
STELLUNG_ATR = 0.5        # Pivotal Points innerhalb ½ ATR sind eine Stellung (Gewicht = wie viele dort stehen)
# Ort nach Harry Sharp, auf Livermores Stellungen gerechnet (Micky 26.11.2026, ungemessen, gesetzte Voreinstellungen):
ABPRALL_ATR = 0.25        # Abpraller: ein Docht kommt bis ¼ ATR an die Stellung, der Schluss bleibt auf seiner Seite
WEG_ATR = 3.0             # Weg voraus: die nächsten 3 ATR (Schwung 2 ATR + Bestätigung 1 ATR = ein ganzer Zug)
UNRUHIG_AB = 2            # ab 2 Stellungen auf dem Weg voraus: unruhig (Sharps Zwischenniveaus, Fallen)
CHOP_AB = 3               # Chop: Gefechtspause und ab 3 Stellungen zwischen Front und Unterkante (Micky 26.11.2026)
WEIT_SCHWUENGE = 3        # weit gelaufen: ≥ 3 Schwünge (3 × 2 ATR) seit dem letzten Pivotal Point der Gegenseite
DRITTEL = ("unteres Drittel", "Mitte", "oberes Drittel")
SPALTEN = {"SE": "Sekundäre Erholung", "NE": "Natürliche Erholung", "AT": "Aufwärtstrend",
           "AB": "Abwärtstrend", "NR": "Natürliche Reaktion", "SR": "Sekundäre Reaktion"}
REIHE = ("SE", "NE", "AT", "AB", "NR", "SR")                  # Reihenfolge der Spalten im Buch
TINTE = {"AT": "schwarz", "AB": "rot"}                        # die übrigen Spalten in Bleistift
ZEICHEN = {"AT": "📈", "AB": "📉", "NE": "↗", "NR": "↘", "SE": "⤴", "SR": "⤵"}
EREIGNIS = {"auf_vorbei": "Aufwärtstrend vorbei (Regel 10b)", "ab_vorbei": "Abwärtstrend vorbei (Regel 10d)",
            "gefahr_auf": "Gefahrensignal: die Erholung stockte unter dem Pivotal Point (Regel 10e)",
            "gefahr_ab": "Gefahrensignal: die Reaktion stockte über dem Pivotal Point (Regel 10f)",
            "bestaetigt_auf": "Pivotal Point nach oben bestätigt (Regel 10a)",
            "bestaetigt_ab": "Pivotal Point nach unten bestätigt (Regel 10a)"}


_SPEICHER = {}             # Technik: dasselbe Notizbuch wird je Seite mehrfach gebraucht (Zone, Chart, Zeichen, Tabelle)
SPEICHER_MAX = 400         # Technik: höchstens so viele Notizbücher im Speicher


def notizbuch(df, atr=None):
    """Livermores Notizbuch über die Tageskerzen → {spalte, trend, eintraege: [(Tag, Spalte, Preis)], pivotal:
    [{tag, preis, farbe, aus, art, i, gesetzt_i}], ereignisse: [(Tag, Schlüssel, Preis)], letzte: {Spalte: Preis},
    je_tag: [(Spalte, Trend)] je Zeile} oder None. Das Notizbuch schaut nie voraus: die Einträge bis Zeile t sind
    dieselben wie im Notizbuch über df.iloc[:t + 1] (gesetzt_i = Zeile, an der ein Pivotal Point eingetragen wurde)."""
    import vcp_zone
    if df is None or len(df) <= vcp_zone.ATR_TAGE + 2:
        return None
    if atr is None:
        schl = (len(df), df.index[0], df.index[-1], float(df["High"].iloc[-1]), float(df["Low"].iloc[-1]),
                float(df["High"].sum()))
        if schl not in _SPEICHER:
            if len(_SPEICHER) > SPEICHER_MAX:
                _SPEICHER.clear()
            _SPEICHER[schl] = _notizbuch(df, None)
        return _SPEICHER[schl]
    return _notizbuch(df, atr)


def _notizbuch(df, atr):
    import vcp_zone
    h, lo = df["High"].to_numpy(float), df["Low"].to_numpy(float)
    a = (atr if atr is not None else vcp_zone.atr(df)).to_numpy(float)
    idx = df.index
    eintraege, pivotal, ereignisse = [], [], []
    letzte = {}                     # letzter (extremer) Kurs je Spalte, wenn sie verlassen wurde
    pp = {}                         # letzter Pivotal Point je Herkunft: AT, NR (rot) · AB, NE (schwarz)
    spalte, ext, ext_i = None, None, None
    trend = None                    # die letzte Trendspalte (AT oder AB) – entscheidet zwischen 10a und 10b/d
    gefahr_gemeldet = set()

    def eintragen(i, sp, preis):
        eintraege.append((idx[i], sp, float(preis)))

    def linie(i_ext, aus, i_jetzt):
        farbe = "rot" if aus in ("AT", "NR") else "schwarz"
        pp[aus] = float(ext)
        pivotal.append({"tag": idx[i_ext], "preis": float(ext), "farbe": farbe, "aus": aus, "i": i_ext,
                        "gesetzt_i": i_jetzt, "art": "hoch" if aus in ("AT", "NE") else "tief"})

    def ereignis(i, k, preis):
        ereignisse.append((idx[i], k, float(preis)))

    start = vcp_zone.ATR_TAGE
    je_tag = [(None, None)] * len(df)            # (Spalte, Trend) am Ende jedes Tages – für die Spanne an früheren Tagen
    for i in range(start, len(df)):
        c = BESTAETIGUNG * a[i]
        s = SCHWUNG * (a[ext_i] if ext_i is not None else a[i])       # wie die Wendepunkte: ATR am Extrem
        if not s == s:                                              # ATR noch nicht gerechnet
            continue
        if spalte is None:                                          # Start: der erste Schwung entscheidet
            hi_i = start + int(np.argmax(h[start:i + 1]))
            lo_i = start + int(np.argmin(lo[start:i + 1]))
            if h[i] - lo[lo_i] >= SCHWUNG * a[lo_i] and lo_i < i:
                spalte = trend = "AT"
                ext, ext_i = h[i], i
                eintragen(i, "AT", h[i])
            elif h[hi_i] - lo[i] >= SCHWUNG * a[hi_i] and hi_i < i:
                spalte = trend = "AB"
                ext, ext_i = lo[i], i
                eintragen(i, "AB", lo[i])
            je_tag[i] = (spalte, trend)
            continue

        if spalte == "AT":
            if h[i] > ext:
                ext, ext_i = h[i], i
                eintragen(i, "AT", h[i])
            elif ext - lo[i] >= s:                                  # Regel 6a, 4a: rote Linie unter dem letzten AT-Kurs
                letzte["AT"] = ext
                linie(ext_i, "AT", i)
                spalte, ext, ext_i = "NR", lo[i], i
                eintragen(i, "NR", lo[i])
        elif spalte == "AB":
            if lo[i] < ext:
                ext, ext_i = lo[i], i
                eintragen(i, "AB", lo[i])
            elif h[i] - ext >= s:                                   # Regel 6c, 4c: schwarze Linie unter dem letzten AB-Kurs
                letzte["AB"] = ext
                linie(ext_i, "AB", i)
                spalte, ext, ext_i = "NE", h[i], i
                eintragen(i, "NE", h[i])
        elif spalte in ("NR", "SR"):
            if lo[i] < ext:
                ext, ext_i = lo[i], i
                if spalte == "SR" and "NR" in letzte and lo[i] < letzte["NR"]:
                    spalte = "NR"                                   # Regel 6h: unter der letzten NR → zurück in NR
                if spalte == "NR":
                    if ("AB" in letzte and lo[i] < letzte["AB"]) or ("NR" in pp and lo[i] <= pp["NR"] - c):
                        ereignis(i, "auf_vorbei" if trend == "AT" else "bestaetigt_ab", lo[i])   # Regel 10b / 10a
                        spalte = trend = "AB"                       # Regel 5b, 6e: rote Tinte im Abwärtstrend
                eintragen(i, spalte, lo[i])
            elif h[i] - ext >= s:                                   # Erholung um einen Schwung
                if spalte == "NR":
                    letzte["NR"] = ext
                    linie(ext_i, "NR", i)                              # Regel 4b: rote Linie unter dem letzten NR-Kurs
                else:
                    letzte["SR"] = ext
                neu = "SE" if ("NE" in letzte and h[i] <= letzte["NE"]) else "NE"   # Regel 6g
                if neu == "NE" and "AT" in letzte and h[i] > letzte["AT"]:
                    neu = trend = "AT"                              # Regel 6d: über dem letzten AT-Kurs
                spalte, ext, ext_i = neu, h[i], i
                eintragen(i, neu, h[i])
        elif spalte in ("NE", "SE"):
            if h[i] > ext:
                ext, ext_i = h[i], i
                if spalte == "SE" and "NE" in letzte and h[i] > letzte["NE"]:
                    spalte = "NE"                                   # Regel 6g: über der letzten NE → zurück in NE
                if spalte == "NE":
                    if ("AT" in letzte and h[i] > letzte["AT"]) or ("NE" in pp and h[i] >= pp["NE"] + c):
                        ereignis(i, "ab_vorbei" if trend == "AB" else "bestaetigt_auf", h[i])   # Regel 10d / 10a
                        spalte = trend = "AT"                       # Regel 5a, 6f: schwarze Tinte im Aufwärtstrend
                eintragen(i, spalte, h[i])
            else:
                if (spalte == "NE" and "AT" in pp and ext < pp["AT"] and pp["AT"] - ext <= c
                        and ext - lo[i] >= c and ("10e", ext_i) not in gefahr_gemeldet):
                    ereignis(i, "gefahr_auf", lo[i])                # Regel 10e: stockt kurz unter dem Pivotal Point
                    gefahr_gemeldet.add(("10e", ext_i))
                if ext - lo[i] >= s:                                # Reaktion um einen Schwung
                    if spalte == "NE":
                        letzte["NE"] = ext
                        linie(ext_i, "NE", i)                          # Regel 4d: schwarze Linie unter dem letzten NE-Kurs
                    else:
                        letzte["SE"] = ext
                    neu = "SR" if ("NR" in letzte and lo[i] >= letzte["NR"]) else "NR"   # Regel 6h
                    if neu == "NR" and "AB" in letzte and lo[i] < letzte["AB"]:
                        neu = trend = "AB"                          # Regel 6b
                    spalte, ext, ext_i = neu, lo[i], i
                    eintragen(i, neu, lo[i])
        if spalte == "NR" and "AB" in pp and ext > pp["AB"] and ext - pp["AB"] <= c \
                and h[i] - ext >= c and ("10f", ext_i) not in gefahr_gemeldet:
            ereignis(i, "gefahr_ab", h[i])                          # Regel 10f: stockt kurz über dem Pivotal Point
            gefahr_gemeldet.add(("10f", ext_i))
        if spalte == "AT":                                          # verbraucht (Micky 25.11.2026, TTWO): hat der
            for k_ in ("NE", "AT"):                                 # Aufwärtstrend einen Pivotal Point oben überschritten,
                if k_ in pp and ext > pp[k_]:                       # gilt er nicht mehr – Regel 10 misst am Punkt dieses
                    del pp[k_]                                      # Laufs; gespiegelt im Abwärtstrend unten
        elif spalte == "AB":
            for k_ in ("NR", "AB"):
                if k_ in pp and ext < pp[k_]:
                    del pp[k_]
        je_tag[i] = (spalte, trend)
    if spalte is None:
        return None
    return {"spalte": spalte, "trend": trend, "eintraege": eintraege, "pivotal": pivotal, "ereignisse": ereignisse,
            "letzte": {k: float(v) for k, v in letzte.items()}, "extrem": float(ext), "je_tag": je_tag}


def spanne(nb, n=None):
    """Livermores Spanne am Ende der Zeile n − 1 (Micky 25.11.2026: streng nach Livermore) → {oben, unten, trend,
    spalte} oder None: oben = der letzte Pivotal Point oben (aus Aufwärtstrend oder natürlicher Erholung), unten = der
    letzte Pivotal Point unten (aus Abwärtstrend oder natürlicher Reaktion) – die beiden Linien, die Livermore im
    Notizbuch beobachtet. Die Front ist der Pivotal Point oben (Regel 5a, 6d). Ohne Pivotal Point oben: None."""
    if not nb:
        return None
    n = len(nb["je_tag"]) if n is None else n
    if n < 1 or n > len(nb["je_tag"]):
        return None
    spalte, trend = nb["je_tag"][n - 1]
    if trend not in ("AT", "AB"):
        return None
    pps = [p_ for p_ in nb["pivotal"] if p_["gesetzt_i"] <= n - 1]
    oben = next((p_ for p_ in reversed(pps) if p_["art"] == "hoch"), None)
    unten = next((p_ for p_ in reversed(pps) if p_["art"] == "tief"), None)
    if oben is None:
        return None
    return {"oben": oben, "unten": unten, "trend": trend, "spalte": spalte}


def offene(df, nb=None):
    """Livermores Pivotal Points, die noch stehen (Micky 25.11.2026): durchbrochen ist ein Punkt erst, wenn ein
    Schluss BESTAETIGUNG × ATR (Livermores ~3 Punkte, Regel 10) jenseits liegt – oben darüber, unten darunter; ein
    Schluss knapp jenseits oder ein Ausflug im Tagesverlauf zählt nicht. Nur die letzten STELLUNG_JAHRE Jahre.
    → [Pivotal Point] in der Reihenfolge des Notizbuchs – die eine Quelle aller Stellungen der App (Micky 26.11.2026:
    ein Heer, eine Sprache, eine Rechnung)."""
    import vcp_zone
    nb = nb or notizbuch(df)
    if not nb:
        return []
    c = df["Close"].to_numpy(float)
    a = vcp_zone.atr(df).to_numpy(float)
    ab = df.index[-1] - pd.DateOffset(years=STELLUNG_JAHRE)
    aus = []
    for p_ in nb["pivotal"]:
        if pd.Timestamp(p_["tag"]) < ab:
            continue
        c_, a_ = c[p_["i"] + 1:], a[p_["i"] + 1:]
        weg = c_ > p_["preis"] + BESTAETIGUNG * a_ if p_["art"] == "hoch" else c_ < p_["preis"] - BESTAETIGUNG * a_
        if not weg.any():
            aus.append(p_)
    return aus


def gefallene(df, nb=None):
    """Alte Plattform (Micky 26.11.2026, Rollentausch): durchbrochene Pivotal Points der letzten STELLUNG_JAHRE Jahre,
    die jetzt auf der anderen Seite des Kurses stehen – ein gebrochener Boden über dem Kurs wird zur Decke, eine
    gebrochene Decke unter dem Kurs zum Boden. Punkte innerhalb BESTAETIGUNG × ATR (gemessen vom untersten) bilden eine
    Plattform. Leiter und
    Bericht zeigen sie; im Weg voraus (ort) zählt sie wie eine Stellung (Micky 26.11.2026), bei Chop und Gewicht nicht.
    → [{unten, oben, rolle: "decke"/"boden", n}] nach Abstand zum Kurs."""
    import vcp_zone
    nb = nb or notizbuch(df)
    if not nb:
        return []
    kurs = float(df["Close"].iloc[-1])
    a = float(vcp_zone.atr(df).iloc[-1] or 0)
    ab = df.index[-1] - pd.DateOffset(years=STELLUNG_JAHRE)
    k_offen = {(p_["i"], p_["art"]) for p_ in offene(df, nb)}
    weg = [p_ for p_ in nb["pivotal"] if pd.Timestamp(p_["tag"]) >= ab and (p_["i"], p_["art"]) not in k_offen
           and ((p_["art"] == "tief" and p_["preis"] > kurs) or (p_["art"] == "hoch" and p_["preis"] < kurs))]
    aus = []
    for p_ in sorted(weg, key=lambda x: x["preis"]):
        rolle = "decke" if p_["preis"] > kurs else "boden"
        g = next((g for g in aus if g["rolle"] == rolle and p_["preis"] - g["unten"] <= BESTAETIGUNG * a), None)
        if g:
            g["oben"], g["n"] = float(p_["preis"]), g["n"] + 1
            continue
        aus.append({"unten": float(p_["preis"]), "oben": float(p_["preis"]), "rolle": rolle, "n": 1})
    return sorted(aus, key=lambda g: min(abs(g["unten"] - kurs), abs(g["oben"] - kurs)))


def front(df, nb=None):
    """Die Frontkarte (Micky 26.11.2026): Livermores stehende Pivotal Points nach Rang → {offen: [alle stehenden],
    stark: {(i, art)}, oben, unten (die Front = Spanne, sofern sie steht), ziel (nächste stehende Stellung über dem
    Kurs außer der Front), boden (nächste darunter), kurs} oder None ohne Notizbuch."""
    nb = nb or notizbuch(df)
    if not nb:
        return None
    offen = offene(df, nb)
    sp = spanne(nb) or {}
    kurs = float(df["Close"].iloc[-1])
    schl = lambda p_: (p_["i"], p_["art"])                                      # noqa: E731
    k_offen = {schl(p_) for p_ in offen}
    oben = sp.get("oben") if sp.get("oben") and schl(sp["oben"]) in k_offen else None
    unten = sp.get("unten") if sp.get("unten") and schl(sp["unten"]) in k_offen else None
    f_ = {schl(p_) for p_ in (oben, unten) if p_}
    rest = [p_ for p_ in offen if schl(p_) not in f_]
    ziel = min((p_ for p_ in rest if p_["preis"] > kurs), key=lambda p_: p_["preis"], default=None)
    boden = max((p_ for p_ in rest if p_["preis"] < kurs), key=lambda p_: p_["preis"], default=None)
    return {"offen": offen, "stark": f_ | {schl(p_) for p_ in (ziel, boden) if p_}, "oben": oben, "unten": unten,
            "ziel": ziel, "boden": boden, "kurs": kurs}


def stellungen(df, nb=None, je_seite=None):
    """Die Stellungen über und unter dem Kurs aus derselben Liste wie die Frontkarte (offene): stehende Pivotal Points
    innerhalb ½ ATR (STELLUNG_ATR) sind eine Stellung; über dem Kurs heißt sie Decke, darunter Boden; die Front (Spanne
    oben) und die Unterkante zählen mit. → {"oben": [...], "unten": [...]} nach Abstand zum Kurs, je {preis, grund,
    abstand, gewicht}; je_seite = höchstens so viele je Richtung."""
    import vcp_zone
    nb = nb or notizbuch(df)
    if not nb:
        return {"oben": [], "unten": []}
    kurs = float(df["Close"].iloc[-1])
    a = float(vcp_zone.atr(df).iloc[-1] or 0)
    aus = {}
    for seite, auswahl in (("oben", [p_ for p_ in offene(df, nb) if p_["preis"] > kurs]),
                           ("unten", [p_ for p_ in offene(df, nb) if p_["preis"] < kurs])):
        liste = []
        for p_ in sorted(auswahl, key=lambda x: abs(x["preis"] - kurs)):
            grund = f'{"Decke" if seite == "oben" else "Boden"} ═ {p_["tag"]:%d.%m.%y}'
            nah = next((f for f in liste if abs(f["preis"] - p_["preis"]) <= a * STELLUNG_ATR), None)
            if nah:
                nah["grund"].append(grund)
                nah["gewicht"] += 1
                continue
            if je_seite and len(liste) >= je_seite:
                continue
            liste.append({"preis": float(p_["preis"]), "grund": [grund], "gewicht": 1,
                          "abstand": round((p_["preis"] / kurs - 1) * 100, 1)})
        aus[seite] = liste
    return aus


def frei(df, nb=None):
    """✈️ freie Bahn (Livermores Linie des geringsten Widerstands): {"oben": keine Stellung über dem Kurs (auch nicht
    die Front), "unten": keine darunter} – aus derselben Liste wie Frontkarte und Stellungen."""
    kurs = float(df["Close"].iloc[-1])
    o = offene(df, nb)
    return {"oben": not any(p_["preis"] > kurs for p_ in o), "unten": not any(p_["preis"] < kurs for p_ in o)}


def abpraller(df, preis, ab_i, seite):
    """Wie oft ein Docht an der Stellung abprallte (Sharp: viele Dochte machen ein Niveau stärker): Kerzen nach ab_i,
    deren Hoch (Decke, seite "oben") bis ABPRALL_ATR × ATR an den Preis kam und deren Schluss darunter blieb –
    gespiegelt am Boden."""
    import vcp_zone
    d = df.iloc[ab_i + 1:]
    if not len(d):
        return 0
    a = vcp_zone.atr(df).iloc[ab_i + 1:].to_numpy(float)
    if seite == "oben":
        return int(((d["High"].to_numpy(float) >= preis - ABPRALL_ATR * a) & (d["Close"].to_numpy(float) < preis)).sum())
    return int(((d["Low"].to_numpy(float) <= preis + ABPRALL_ATR * a) & (d["Close"].to_numpy(float) > preis)).sum())


def gruppen(df, nb=None):
    """Alle Stellungen (stehende Pivotal Points innerhalb ½ ATR zusammen) → [{preis, gewicht, i, abpraller}] nach Preis
    – die eine Liste für Gewicht, Weg voraus, Chop und die Etiketten des Charts."""
    import vcp_zone
    a = float(vcp_zone.atr(df).iloc[-1] or 0)
    kurs = float(df["Close"].iloc[-1])
    aus = []
    for p_ in sorted(offene(df, nb), key=lambda x: x["preis"]):
        nah = next((g for g in aus if abs(g["preis"] - p_["preis"]) <= a * STELLUNG_ATR), None)
        if nah:
            nah["gewicht"] += 1
            nah["i"] = min(nah["i"], p_["i"])
            continue
        aus.append({"preis": float(p_["preis"]), "gewicht": 1, "i": p_["i"]})
    for g in aus:
        g["abpraller"] = abpraller(df, g["preis"], g["i"], "oben" if g["preis"] > kurs else "unten")
    return aus


def ort(df, nb=None, fr=None, ab=None):
    """Ort nach Sharp auf Livermores Karte: Lage in der Spanne (Drittel), Weg voraus je Richtung (Stellungen und alte
    Plattformen in den nächsten WEG_ATR × ATR: 0 = sauber, ab UNRUHIG_AB = unruhig), Chop (Gefechtspause und ab CHOP_AB Stellungen zwischen
    Front und Unterkante), weit gelaufen (oberes Drittel bzw. über der Front und ≥ WEIT_SCHWUENGE Schwünge seit dem
    letzten Pivotal Point unten; gespiegelt). ab = {"oben"/"unten": Preis}, von wo der Weg voraus zählt (beim Setup,
    das noch wartet, die Kante – die Front ist dann der Auslöser, kein Hindernis), sonst der Kurs. → dict oder None."""
    import vcp_zone
    nb = nb or notizbuch(df)
    if not nb:
        return None
    fr = fr or front(df, nb)
    kurs = float(df["Close"].iloc[-1])
    a = float(vcp_zone.atr(df).iloc[-1] or 0)
    gr = gruppen(df, nb)
    o_, u_ = (fr["oben"] or {}).get("preis"), (fr["unten"] or {}).get("preis")
    drittel = None
    if o_ and u_ and o_ > u_:
        x = (kurs - u_) / (o_ - u_)
        drittel = ("über der Front" if x > 1 else "unter der Unterkante" if x < 0
                   else DRITTEL[min(len(DRITTEL) - 1, int(x * len(DRITTEL)))])
    weg = {}
    alt = gefallene(df, nb)                       # die alte Plattform steht im Weg wie eine Stellung (Micky 26.11.2026)
    for seite, sg in (("oben", 1), ("unten", -1)):
        ref = (ab or {}).get(seite) or kurs
        rand = a * STELLUNG_ATR if ref != kurs else 0                   # die Kante selbst zählt nicht mit
        hindernis = gr + [{"preis": g_["unten"] if sg > 0 else g_["oben"]} for g_ in alt
                          if g_["rolle"] == ("decke" if sg > 0 else "boden")]   # vorderer Rand der Plattform
        voraus = [g for g in hindernis if rand < sg * (g["preis"] - ref) <= WEG_ATR * a]
        naechste = min((g for g in hindernis if sg * (g["preis"] - ref) > rand), key=lambda g: abs(g["preis"] - ref),
                       default=None)
        weg[seite] = {"n": len(voraus), "sauber": not voraus, "unruhig": len(voraus) >= UNRUHIG_AB, "ab": ref,
                      "von_kante": ref != kurs,
                      "bis": round((naechste["preis"] / kurs - 1) * 100, 1) if naechste else None}
    chop = False
    if o_ and u_ and nb["spalte"] not in ("AT", "AB"):
        innen = [g for g in gr if u_ + a * STELLUNG_ATR < g["preis"] < o_ - a * STELLUNG_ATR]
        chop = len(innen) >= CHOP_AB
    weit = None
    tiefs = [p_ for p_ in nb["pivotal"] if p_["art"] == "tief"]
    hochs = [p_ for p_ in nb["pivotal"] if p_["art"] == "hoch"]
    if a and tiefs and drittel in ("oberes Drittel", "über der Front") and kurs - tiefs[-1]["preis"] >= WEIT_SCHWUENGE * SCHWUNG * a:
        weit = "auf"
    if a and hochs and drittel in (DRITTEL[0], "unter der Unterkante") and hochs[-1]["preis"] - kurs >= WEIT_SCHWUENGE * SCHWUNG * a:
        weit = "ab"
    return {"drittel": drittel, "weg": weg, "chop": chop, "weit": weit, "gruppen": gr}


LAGE = {"AT": ("🟢", "Vormarsch"), "AB": ("🔴", "Rückzug")}   # eine Sprache für Titel und Markt (Micky 26.11.2026);
GEFECHTSPAUSE = ("🟡", "Gefechtspause")                         # die vier Bleistift-Spalten sind die Gefechtspause


def lage(spalte):
    """(Ampel, Wort) zur Spalte: Aufwärtstrend = 🟢 Vormarsch, Abwärtstrend = 🔴 Rückzug, sonst 🟡 Gefechtspause."""
    return LAGE.get(spalte, GEFECHTSPAUSE)


def spalte_text(nb):
    """„🟢 Vormarsch · 📈 Aufwärtstrend“ usw. – die Lage in unserer Sprache und die Spalte, in der Livermore heute
    schreiben würde."""
    if not nb:
        return ""
    a_, w_ = lage(nb["spalte"])
    return f'{a_} {w_} · {ZEICHEN[nb["spalte"]]} {SPALTEN[nb["spalte"]]}'


KEY_JAHRE = 2              # Key Price: beide Titel über die letzten 2 Jahre auf 100 gesetzt und zusammengezählt


def schwester(tk):
    """Livermores Schwesteraktie (Micky 25.11.2026): der stärkste andere Titel derselben Branche nach RS-Rang aus dem
    letzten Rückenwind-Lauf → (Ticker, Branche) oder (None, None)."""
    import rueckenwind
    erg = rueckenwind.laden() or {}
    titel = erg.get("titel") or {}
    br = (titel.get(tk) or {}).get("branche")
    if not br:
        return None, None
    andere = [(x.get("rang") or 0, t) for t, x in titel.items() if t != tk and x.get("branche") == br]
    return (max(andere)[1], br) if andere else (None, br)


def key_price(tk, df):
    """Livermores Key Price: der Titel und seine Schwesteraktie zusammen (Kapitel VIII: ein Trendwechsel gilt erst,
    wenn der Key Price ihn bestätigt). Weil Livermore zwei ähnlich teure Aktien nahm, setzt die App beide über die
    letzten KEY_JAHRE Jahre auf 100 und zählt sie zusammen (unsere Anpassung); das Notizbuch läuft darüber mit denselben
    Schwellen (die ATR der Summe verdoppelt sich von selbst – Livermores 12 statt 6 Punkte).
    → {schwester, branche, nb} oder None."""
    import daten
    import pandas as pd
    sw, br = schwester(tk)
    if not sw or df is None:
        return None
    df2 = daten.kurse_gespeichert(sw)
    if df2 is None or len(df2) < 60:
        return None
    ab = df.index[-1] - pd.DateOffset(years=KEY_JAHRE)
    a_, b_ = df[df.index >= ab], df2[df2.index >= ab]
    gemein = a_.index.intersection(b_.index)
    if len(gemein) < 60:
        return None
    a_, b_ = a_.loc[gemein], b_.loc[gemein]
    fa, fb = 100 / float(a_["Close"].iloc[0]), 100 / float(b_["Close"].iloc[0])
    summe = a_[["Open", "High", "Low", "Close"]] * fa + b_[["Open", "High", "Low", "Close"]] * fb
    summe["Volume"] = a_["Volume"] + b_["Volume"]
    return {"schwester": sw, "branche": br, "nb": notizbuch(summe)}
