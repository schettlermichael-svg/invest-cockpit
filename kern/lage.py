"""Lageleiste: Dalio-Quadrant (Makro) und Marks-Pendel (Zyklus).

Alle drei Funktionen nehmen einen Stichtag (Standard: heute) und rechnen nur mit Daten bis zu
diesem Tag – so lassen sie sich an bekannten Zeitpunkten prüfen.
Regeln: Konzept, Abschnitte „Ebene 1“ und „Ebene 2“.
"""
import numpy as np
import pandas as pd

import marktdaten as md
from masse import GD200_TAGE, JAHR_TAGE, JAHR_WOCHEN, QUARTALE_JAHR  # noqa: E402

# ── Dalio-Quadrant ──────────────────────────────────────────────────────────
QUADS = {1: "Goldilocks", 2: "Reflation", 3: "Stagflation", 4: "Deflation"}
FUEHRER = {1: "Technologie, zyklischer Konsum, Kommunikation",
           2: "Energie, Grundstoffe, Industrie, Finanzwerte",
           3: "Energie, Versorger, Gold",
           4: "Versorger, Basiskonsum, Gesundheit, Staatsanleihen"}


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
QUARTAL_WOCHEN = 13         # Richtung: gegenüber vor 13 Wochen
MONATE_JAHR = 12            # Inflation zum Vorjahr: 12 Monate zurück
RANG_JAHRE = 10             # Rang in der eigenen Geschichte der letzten 10 Jahre
JAHR_KALENDERTAGE = 365     # Kalendertage je Jahr
RANG_MITTE = 50.0           # ohne Geschichte: Rang in der Mitte
DREI_MONATE = 60            # 60 Handelstage (Mindestdaten Kredit; Hoch der Breite)
VIER_WOCHEN = 21            # 4 Wochen in Handelstagen
SECHS_MONATE = 120          # Tief der Breite in 120 Handelstagen
LEVY_TAGE = 130             # Levy-Stärke: Kurs zum Schnitt von 130 Tagen (26 Wochen)
NAH_HOCH = 0.97             # S&P 500 nah am Hoch: höchstens 3 % darunter
PENDEL_WOCHEN = 4           # Pendel: Zone heute gegen vor 4 Wochen
PENDEL_SCHRITT = 3          # bis 3 Zonen weiter im Kreis = vorwärts (↗)
SCHWELLE_PUNKTE = 0.25      # Weekly Economic Index und GDPNow: Richtung erst ab 0,25 Punkten Änderung in 13 Wochen
ICSA_WOCHEN = 4             # Erstanträge: Schnitt über 4 Wochen
SCHWELLE_BREAKEVEN = 0.05   # Breakeven-Inflation: Richtung ab 0,05 Punkten
CPI_ZURUECK = 4             # Inflation steigt/fällt: heute gegen den 4. Monatswert zurück (vor 3 Monaten)
KAPITULATION_VIX = 90       # Kapitulation: VIX-Rang ab 90 …
KAPITULATION_BREITE = 20    # … und Breite höchstens 20 %
BESCHLEUNIGUNG_VIX = 80     # Abwärtsbeschleunigung: VIX-Rang ab 80 …
BESCHLEUNIGUNG_BREITE = 15  # … und Breite in 4 Wochen mindestens 15 Punkte gefallen (oder Kredit −2)
ERHOLUNG_BREITE_PLUS = 10   # Frühe Erholung: Breite in 4 Wochen mindestens +10 Punkte …
ERHOLUNG_BREITE_TIEF = 25   # … nach einem Tief der Breite bis 25 % …
ERHOLUNG_VIX = 60           # … bei VIX-Rang ab 60 …
ERHOLUNG_KREDIT = 40        # … oder Kredit-Rang höchstens 40
BODEN_BREITE = 40           # Bodenbildung: unter dem GD200 und Breite höchstens 40 %
HITZE_VIX = 15              # Überhitzung: VIX-Rang höchstens 15 …
HITZE_KREDIT = 85           # … Kredit-Rang ab 85 …
HITZE_LEVY = 1.10           # … und Levy-Stärke ab 1,10
TOP_BREITE_RUECK = 10       # Topbildung: nah am Hoch, Breite mindestens 10 Punkte unter ihrem Hoch, Kredit weitet sich
GESUND_BREITE = 50          # Gesunder Aufwärtstrend: über dem GD200 und Breite ab 50 %
BESCHLEUNIGUNG_KREDIT = 2  # … oder Kreditabstand in 4 Wochen mindestens 2 Punkte weiter
SCHWELLE_RATE = 2          # Jahresraten: Richtung erst ab 2 Prozentpunkten Änderung in 13 Wochen


def _bis(s, bis):
    return s[s.index <= pd.Timestamp(bis)] if bis else s


def _jahresrate(s):
    """Veränderung zum Vorjahr in Prozent (auf Wochenbasis)."""
    w = s.resample("W-FRI").last().dropna()
    return (w / w.shift(JAHR_WOCHEN) - 1) * 100


def _richtung(rate, schwelle, umgekehrt=False):
    """Steigt oder fällt die Rate gegenüber vor 13 Wochen?
    Liefert (Richtung 'steigt'|'fällt'|'unklar', Änderung, Wert vor 13 Wochen, Wert heute)."""
    r = rate.dropna()
    if len(r) < 2:
        return "unklar", np.nan, np.nan, np.nan
    alt = r[r.index <= r.index[-1] - pd.Timedelta(weeks=QUARTAL_WOCHEN)]
    if alt.empty:
        return "unklar", np.nan, np.nan, np.nan
    d = r.iloc[-1] - alt.iloc[-1]
    if umgekehrt:
        d = -d
    return ("steigt" if d > schwelle else "fällt" if d < -schwelle else "unklar"), float(d), \
        float(alt.iloc[-1]), float(r.iloc[-1])


def _instrumente(bis):
    hg, gc = md.yahoo("HG=F"), md.yahoo("GC=F")
    xly, xlp = md.yahoo("XLY"), md.yahoo("XLP")
    wachstum = {
        "Kupfer/Gold": _richtung(_jahresrate(_bis(hg / gc.reindex(hg.index, method="ffill"), bis)), SCHWELLE_RATE),
        "Zyklischer gegen Basiskonsum": _richtung(_jahresrate(_bis(xly / xlp.reindex(xly.index, method="ffill"), bis)), SCHWELLE_RATE),
        "Weekly Economic Index": _richtung(_bis(md.fred("WEI"), bis).resample("W-FRI").last(), SCHWELLE_PUNKTE),
        "Erstanträge Arbeitslosenhilfe": _richtung(_jahresrate(_bis(md.fred("ICSA"), bis).rolling(ICSA_WOCHEN).mean()), SCHWELLE_RATE, umgekehrt=True),
        "GDPNow": _richtung(_bis(md.fred("GDPNOW"), bis).resample("W-FRI").last().ffill(), SCHWELLE_PUNKTE),
    }
    inflation = {
        "Rohstoffkorb (DBC)": _richtung(_jahresrate(_bis(md.yahoo("DBC"), bis)), SCHWELLE_RATE),
        "Öl": _richtung(_jahresrate(_bis(md.yahoo("CL=F"), bis)), SCHWELLE_RATE),
        "Breakeven-Inflation 5 Jahre": _richtung(_bis(md.fred("T5YIE"), bis).resample("W-FRI").last(), SCHWELLE_BREAKEVEN),
    }
    return wachstum, inflation


def _amtlich(bis):
    bip = _bis(md.fred("GDPC1"), bis)
    cpi = _bis(md.fred("CPIAUCSL"), bis)
    bip_rate = (bip / bip.shift(QUARTALE_JAHR) - 1) * 100
    cpi_rate = (cpi / cpi.shift(MONATE_JAHR) - 1) * 100
    w = "steigt" if bip_rate.iloc[-1] > bip_rate.iloc[-2] else "fällt"
    i = "steigt" if cpi_rate.iloc[-1] > cpi_rate.iloc[-CPI_ZURUECK] else "fällt"
    return w, i, float(bip_rate.iloc[-1]), float(cpi_rate.iloc[-1])


def _quad(w, i):
    return {("steigt", "fällt"): 1, ("steigt", "steigt"): 2, ("fällt", "steigt"): 3, ("fällt", "fällt"): 4}[(w, i)]


def _mehrheit(instr, ersatz):
    auf = sum(1 for r, *_ in instr.values() if r == "steigt")
    ab = sum(1 for r, *_ in instr.values() if r == "fällt")
    return ("steigt" if auf > ab else "fällt" if ab > auf else ersatz), auf, ab


def quadrant(bis=None):
    wachstum, inflation = _instrumente(bis)
    aw, ai, bip, cpi = _amtlich(bis)
    w, w_auf, w_ab = _mehrheit(wachstum, aw)
    i, i_auf, i_ab = _mehrheit(inflation, ai)
    schnell, amtlich = _quad(w, i), _quad(aw, ai)
    return {
        "quad": schnell, "name": QUADS[schnell], "amtlich": amtlich,
        "wechsel_moeglich": schnell != amtlich,
        "wachstum": {"richtung": w, "steigt": w_auf, "fällt": w_ab, "von": len(wachstum), "instrumente": wachstum},
        "inflation": {"richtung": i, "steigt": i_auf, "fällt": i_ab, "von": len(inflation), "instrumente": inflation},
        "bip_rate": round(bip, 1), "cpi_rate": round(cpi, 1), "fuehrer": FUEHRER[schnell],
    }


# ── Marks-Pendel ────────────────────────────────────────────────────────────
ZONEN = ["Frühe Erholung", "Gesunder Aufwärtstrend", "Überhitzung", "Topbildung",
         "Abwärtsbeschleunigung", "Kapitulation", "Bodenbildung"]
ZONEN_AMPEL = {"Frühe Erholung": "grün", "Gesunder Aufwärtstrend": "grün", "Überhitzung": "gelb",
               "Topbildung": "gelb", "Abwärtsbeschleunigung": "rot", "Kapitulation": "rot", "Bodenbildung": "gelb"}


def _rang(s, wert, jahre=RANG_JAHRE):
    """Perzentil des Wertes in der eigenen Geschichte der letzten zehn Jahre (0–100)."""
    teil = s[s.index > s.index[-1] - pd.Timedelta(days=JAHR_KALENDERTAGE * jahre)].dropna()
    return float((teil <= wert).mean() * 100) if len(teil) else RANG_MITTE


def _messwerte(bis):
    vix = _bis(md.yahoo("^VIX"), bis)
    hyg, ief = md.yahoo("HYG"), md.yahoo("IEF")
    verh = (hyg / ief.reindex(hyg.index, method="ffill")).dropna()
    # Das Verhältnis steigt über die Jahre schon durch die höheren Zinsen der Hochzinsanleihen.
    # Gemessen wird deshalb der Abstand zum eigenen 52-Wochen-Hoch: 0 = ruhig, stark negativ = Stress.
    kredit = _bis(verh / verh.rolling(JAHR_TAGE, min_periods=DREI_MONATE).max() - 1, bis).dropna() * 100
    br = _bis(md.breite(), bis)
    spx = _bis(md.yahoo("^GSPC"), bis)
    return {
        "vix_rang": _rang(vix, vix.iloc[-1]), "vix": float(vix.iloc[-1]),
        "kredit_rang": _rang(kredit, kredit.iloc[-1]),                        # hoch = Gier
        "kredit_4w": float(kredit.iloc[-1] - kredit.iloc[-VIER_WOCHEN]),              # negativ = Aufschlag weitet sich
        "breite": float(br.iloc[-1]), "breite_4w": float(br.iloc[-1] - br.iloc[-VIER_WOCHEN]),
        "breite_max60": float(br.iloc[-DREI_MONATE:].max()),
        "breite_min120": float(br.iloc[-SECHS_MONATE:].min()),
        "levy": float(spx.iloc[-1] / spx.iloc[-LEVY_TAGE:].mean()),
        "nah_hoch": bool(spx.iloc[-1] >= spx.iloc[-JAHR_TAGE:].max() * NAH_HOCH),
        "ueber_gd200": bool(spx.iloc[-1] > spx.iloc[-GD200_TAGE:].mean()),
    }


def _zone(m):
    """Einordnung in die sieben Zonen; Reihenfolge der Prüfung = Vorrang."""
    if m["vix_rang"] >= KAPITULATION_VIX and m["breite"] <= KAPITULATION_BREITE:
        return "Kapitulation"
    if m["vix_rang"] >= BESCHLEUNIGUNG_VIX and (m["breite_4w"] <= -BESCHLEUNIGUNG_BREITE or m["kredit_4w"] <= -BESCHLEUNIGUNG_KREDIT):
        return "Abwärtsbeschleunigung"
    # Frühe Erholung: Breite dreht kräftig nach oben, kurz nach einem Tief der Breite,
    # während VIX oder Kreditstress noch erhöht sind
    if m["breite_4w"] >= ERHOLUNG_BREITE_PLUS and m["breite_min120"] <= ERHOLUNG_BREITE_TIEF and (m["vix_rang"] >= ERHOLUNG_VIX or m["kredit_rang"] <= ERHOLUNG_KREDIT):
        return "Frühe Erholung"
    if not m["ueber_gd200"] and m["breite"] <= BODEN_BREITE:
        return "Bodenbildung"
    if m["vix_rang"] <= HITZE_VIX and m["kredit_rang"] >= HITZE_KREDIT and m["levy"] >= HITZE_LEVY:
        return "Überhitzung"
    if m["nah_hoch"] and m["breite"] <= m["breite_max60"] - TOP_BREITE_RUECK and m["kredit_4w"] < 0:
        return "Topbildung"
    if m["ueber_gd200"] and m["breite"] >= GESUND_BREITE:
        return "Gesunder Aufwärtstrend"
    return "Bodenbildung" if not m["ueber_gd200"] else "Topbildung"


def pendel(bis=None):
    heute = pd.Timestamp(bis) if bis else pd.Timestamp.today().normalize()
    m = _messwerte(heute)
    zone = _zone(m)
    vorher = _zone(_messwerte(heute - pd.Timedelta(weeks=PENDEL_WOCHEN)))
    schritt = (ZONEN.index(zone) - ZONEN.index(vorher)) % len(ZONEN)
    pfeil = "→" if schritt == 0 else "↗" if schritt <= PENDEL_SCHRITT else "↘"
    return {"zone": zone, "ampel": ZONEN_AMPEL[zone], "vor_4_wochen": vorher, "pfeil": pfeil, "messwerte": m}
