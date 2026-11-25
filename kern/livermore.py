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
      vorige Reaktionstief): Aufwärtstrend vorbei · d) gespiegelt: Abwärtstrend vorbei · a) dasselbe in Trendrichtung:
      Pivotal Point bestätigt · e) NE endet kurz (≤ Bestätigung) unter dem AT-Pivotal-Point und
      fällt dann um die Bestätigung: Gefahrensignal, der Aufwärtstrend ist zu Ende · f) gespiegelt.
"""
import numpy as np

SCHWUNG = 2.0             # Livermores ~6 Punkte = 2 × ATR (wie vcp_zone.GROB, die Wendepunkte)
BESTAETIGUNG = 1.0        # Livermores ~3 Punkte = 1 × ATR
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
        je_tag[i] = (spalte, trend)
    if spalte is None:
        return None
    return {"spalte": spalte, "trend": trend, "eintraege": eintraege, "pivotal": pivotal, "ereignisse": ereignisse,
            "letzte": {k: float(v) for k, v in letzte.items()}, "extrem": float(ext), "je_tag": je_tag}


def spanne(nb, n=None):
    """Livermores Spanne am Ende der Zeile n − 1 (Micky 25.11.2026: streng nach Livermore) → {oben, unten, trend,
    spalte} oder None: oben = der letzte Pivotal Point oben (aus Aufwärtstrend oder natürlicher Erholung), unten = der
    letzte Pivotal Point unten (aus Abwärtstrend oder natürlicher Reaktion) – die beiden Linien, die Livermore im
    Notizbuch beobachtet. Der Pivot ist der Pivotal Point oben (Regel 5a, 6d). Ohne Pivotal Point oben: None."""
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


def spalte_text(nb):
    """„📈 Aufwärtstrend“ usw. – die Spalte, in der Livermore heute schreiben würde."""
    if not nb:
        return ""
    return f'{ZEICHEN[nb["spalte"]]} {SPALTEN[nb["spalte"]]}'


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
