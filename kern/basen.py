"""IBD-Basenzählung auf den Zonen des VCP-Scanners (06.11.2026, statt der Wertzonen).

Regeln wie bisher (O'Neil/IBD), nur auf Scanner-Zonen:
  Beginn  = was später liegt: Beginn der aktuellen Phase 2 (Weinstein) oder das letzte Markttief nach einer Korrektur
            ab 15 % (erkennung.letztes_markttief) – nach einer Marktkorrektur fängt jeder Titel wieder bei 1 an
  gezählt = abgeschlossene Scanner-Zonen (Ausbruch über die Oberkante, vcp_zone.verlauf) ab dem Beginn, Basen ab
            3 Wochen und Flaggen ab 1 Woche (Micky); die laufende Zone zählt mit
  Stufe   = eine Zone zählt als neue Base erst, wenn ihre Oberkante mindestens 20 % über der Oberkante der zuletzt
            gezählten liegt – sonst ist es Base auf Base auf derselben Stufe (gleiche Nummer)
  Ampel   = 1. und 2. Base grün (früh), 3. gelb (handelbar), ab der 4. rot (spät) – Zeichen, kein Filter
Ausgang je abgeschlossener Zone (O'Neil): gelungen = Hoch 20 % über dem Pivot (Oberkante), bevor ein Schluss 8 % darunter
lag; gescheitert = der Schluss 8 % darunter kam zuerst; sonst offen. Volumen am Ausbruchstag gegen den 50-Tage-Schnitt.
"""
import numpy as np

import erkennung

STUFE = 0.20                  # neue Base erst 20 % über der Oberkante der zuletzt gezählten
ERFOLG, VERLUST = 0.20, 0.08  # Ausgang nach O'Neil


def beginn(df, index=None):
    """Beginn der Zählung (Datum) oder None (zu kurze Historie)."""
    if len(df) < 300:
        return None
    ph = erkennung.phasen(df)
    vorher = ph[ph.isin([1, 4])]
    b = vorher.index[-1] if len(vorher) else ph.index[0]
    markt = erkennung.letztes_markttief(index, df.index[-1])
    return markt if markt is not None and markt > b else b


def _ausgang(df, i, pivot):
    h, c = df["High"].to_numpy(float), df["Close"].to_numpy(float)
    for j in range(i, len(df)):
        if c[j] <= pivot * (1 - VERLUST):
            return "gescheitert"
        if h[j] >= pivot * (1 + ERFOLG):
            return "gelungen"
    return "offen"


def zaehlen(df, index, verlauf, jetzt=None):
    """verlauf: abgeschlossene Zonen aus vcp_zone.verlauf/alles (mit start_i, ende_i, oben); jetzt: die laufende Base
    (Minervinis Zone) oder None. Ergebnis: {zahl (laufende Base, None ohne), liste (abgeschlossene Zonen mit nummer,
    ausgang, volumen), beginn, bilanz}. Die Zonen in verlauf bekommen ihre Nummer (für den Chart)."""
    df = df.dropna(subset=["High", "Low", "Close"])
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(len(df), np.nan)
    t0 = beginn(df, index)
    gesehen, liste = set(), []
    for b in sorted(verlauf or [], key=lambda b: (b["ende_i"], b["start_i"])):
        if b["start_i"] in gesehen:
            continue
        gesehen.add(b["start_i"])
        liste.append(b)
    zahl, letzter = 0, None
    for b in liste:
        i = b["ende_i"]
        s50 = np.nanmean(v[max(0, i - 50):i]) if i > 0 else np.nan
        b["volumen"] = float(v[i] / s50) if s50 == s50 and s50 else None
        b["ausgang"] = _ausgang(df, i, b["oben"])
        if t0 is None or df.index[b["start_i"]] < t0:
            b["nummer"] = None                   # vor dem Beginn der Zählung
            continue
        if letzter is None or b["oben"] >= letzter * (1 + STUFE):
            zahl, letzter = zahl + 1, b["oben"]
        b["nummer"] = zahl
    lauf = None
    if jetzt and jetzt.get("zone") and t0 is not None and df.index[jetzt["start_i"]] >= t0:
        schon = next((b for b in liste if b["start_i"] == jetzt["start_i"]), None)
        if schon:                                # frisch ausgebrochen: dieselbe Zone wie in der Liste
            lauf = schon["nummer"]
        else:
            lauf = zahl + 1 if letzter is None or jetzt["oben"] >= letzter * (1 + STUFE) else max(zahl, 1)
    zaehl = {a: sum(1 for b in liste if b["ausgang"] == a) for a in ("gelungen", "gescheitert", "offen")}
    return {"zahl": lauf, "liste": liste, "beginn": t0, "bilanz": zaehl}


def markt_rueckgang(index, von, bis=None):
    """Größter Rückgang des Index (Schlusskurse) zwischen zwei Daten in %, oder None."""
    if index is None:
        return None
    s = index["Close"]
    s = s[(s.index >= von) & ((s.index <= bis) if bis is not None else True)].to_numpy(float)
    if len(s) < 2:
        return None
    return float(np.max(1 - s / np.maximum.accumulate(s)) * 100)
