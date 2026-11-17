"""IBD-Basenzählung auf den Zonen des VCP-Scanners (06.11.2026, statt der Wertzonen).

Regeln (O'Neil/IBD), auf Scanner-Zonen:
  Beginn  = Beginn der laufenden Phase 2 (Weinstein): nach Phase 4 und auch nach einer Verteilung (3 → 2) fängt die
            Zählung neu an (Plan 10, Micky 16.11.2026; das Markttief setzt nicht mehr zurück)
  neu     = fällt eine Zone unter das Tief der vorigen Base, beginnt die Zählung wieder bei 1 (IBD-Faustregel; ohne
            Phase 4 dazwischen in 622 von 966 Fällen, 16.11.2026); eine laufende Zone in Phase 1 oder 3 (oder vor dem
            Wechsel zu Phase 2 begonnen) ist die 1. Base des neuen Anstiegs; in Phase 4 wird nicht gezählt
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
from masse import P_ABWAERTS, PHASE_VERTEILUNG, VOL_TAGE  # noqa: E402

BASE_FRUEH, BASE_HANDELBAR = 2, 3   # O'Neil: Basen 1–2 früh (grün), die 3. noch handelbar (gelb), ab der 4. spät
STUFE = 0.20                  # neue Base erst 20 % über der Oberkante der zuletzt gezählten
ERFOLG, VERLUST = 0.20, 0.08  # Ausgang nach O'Neil


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────


def beginn(df):
    """Beginn der Zählung (Datum): der Freitag nach der letzten Woche in Phase 1, 3 oder 4, oder None (zu kurze
    Historie)."""
    if len(df) < 300:
        return None
    ph = erkennung.phasen(df)
    vorher = ph[ph.isin([1, PHASE_VERTEILUNG, P_ABWAERTS])]
    return vorher.index[-1] if len(vorher) else ph.index[0]


def _ausgang(df, i, pivot):
    h, c = df["High"].to_numpy(float), df["Close"].to_numpy(float)
    for j in range(i, len(df)):
        if c[j] <= pivot * (1 - VERLUST):
            return "gescheitert"
        if h[j] >= pivot * (1 + ERFOLG):
            return "gelungen"
    return "offen"


def zaehlen(df, verlauf, jetzt=None, reif=True):
    """verlauf: abgeschlossene Zonen aus vcp_zone.verlauf/alles (mit start_i, ende_i, oben); jetzt: die laufende Zone
    oder None, reif: ist sie eine reife Base (Minervini)? Ergebnis: {zahl (laufende Zone, None ohne), reif, neu (Grund,
    wenn die laufende Zone neu bei 1 beginnt), grund (warum keine Zahl), liste (abgeschlossene Zonen mit nummer, ausgang, volumen), beginn,
    bilanz}. Die Zonen in verlauf bekommen ihre Nummer (für den Chart)."""
    df = df.dropna(subset=["High", "Low", "Close"])
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(len(df), np.nan)
    tiefs = df["Low"].to_numpy(float)
    t0 = beginn(df)
    gesehen, liste = set(), []
    for b in sorted(verlauf or [], key=lambda b: (b["ende_i"], b["start_i"])):
        if b["start_i"] in gesehen:
            continue
        gesehen.add(b["start_i"])
        liste.append(b)
    zahl, letzter, tief_vor = 0, None, None
    for b in liste:
        i = b["ende_i"]
        s50 = np.nanmean(v[max(0, i - VOL_TAGE):i]) if i > 0 else np.nan
        b["volumen"] = float(v[i] / s50) if s50 == s50 and s50 else None
        b["ausgang"] = _ausgang(df, i, b["oben"])
        if b.get("cheat"):                       # Ausbruch aus einer Pause in einer größeren Zone: keine eigene Base
            b["nummer"] = None                   # (die eine Cheat-Regel, vcp_zone.cheat)
            continue
        if t0 is None or df.index[b["start_i"]] < t0:
            b["nummer"] = None                   # vor dem Beginn der Zählung
            continue
        tief_b = float(tiefs[b["start_i"]:b["ende_i"] + 1].min())
        if tief_vor is not None and tief_b < tief_vor:   # unter dem Tief der vorigen Base: neu bei 1 (IBD)
            zahl, letzter = 0, None
            b["neu"] = "unter dem Tief der vorigen Base"
        if letzter is None or b["oben"] >= letzter * (1 + STUFE):
            zahl, letzter = zahl + 1, b["oben"]
        b["nummer"], tief_vor = zahl, tief_b
    lauf, neu = None, None
    if jetzt and jetzt.get("zone") and t0 is not None and df.index[jetzt["start_i"]] >= t0:
        schon = next((b for b in liste if b["start_i"] == jetzt["start_i"]), None)
        if schon:                                # frisch ausgebrochen: dieselbe Zone wie in der Liste
            lauf, neu = schon["nummer"], schon.get("neu")
        elif tief_vor is not None and jetzt.get("unten") is not None and jetzt["unten"] < tief_vor:
            lauf, neu = 1, "unter dem Tief der vorigen Base"
        else:
            lauf = zahl + 1 if letzter is None or jetzt["oben"] >= letzter * (1 + STUFE) else max(zahl, 1)
    grund = None if lauf else "keine laufende Zone" if not (jetzt and jetzt.get("zone")) else None
    if not lauf and jetzt and jetzt.get("zone") and t0 is not None:
        # Plan 10 (Micky 16.11.2026): eine Zone in Phase 1 oder 3 – oder eine, die vor dem Wechsel zu Phase 2 begann – ist
        # die Base, aus der der neue Anstieg startet: 1. Base; in Phase 4 wird nicht gezählt
        p_ = int(erkennung._phase_von(df)[-1])
        if p_ == P_ABWAERTS:
            grund = "keine Zählung in Phase 4"
        else:
            lauf, neu = 1, f"Base vor dem neuen Anstieg (Phase {p_})" if p_ != 2 else "Base aus der Zeit vor Phase 2"
    zaehl = {a: sum(1 for b in liste if b["ausgang"] == a and not b.get("cheat"))
             for a in ("gelungen", "gescheitert", "offen")}
    return {"zahl": lauf, "reif": bool(reif), "neu": neu, "grund": grund, "liste": liste, "beginn": t0, "bilanz": zaehl}


def markt_rueckgang(index, von, bis=None):
    """Größter Rückgang des Index (Schlusskurse) zwischen zwei Daten in %, oder None."""
    if index is None:
        return None
    s = index["Close"]
    s = s[(s.index >= von) & ((s.index <= bis) if bis is not None else True)].to_numpy(float)
    if len(s) < 2:
        return None
    return float(np.max(1 - s / np.maximum.accumulate(s)) * 100)
