"""Lageleiste: Dalio-Quadrant (Makro) und Marks-Pendel (Zyklus).

Alle drei Funktionen nehmen einen Stichtag (Standard: heute) und rechnen nur mit Daten bis zu
diesem Tag – so lassen sie sich an bekannten Zeitpunkten prüfen.
Regeln: Konzept, Abschnitte „Ebene 1“ und „Ebene 2“.
"""
import numpy as np
import pandas as pd

import marktdaten as md

# ── Dalio-Quadrant ──────────────────────────────────────────────────────────
QUADS = {1: "Goldilocks", 2: "Reflation", 3: "Stagflation", 4: "Deflation"}
FUEHRER = {1: "Technologie, zyklischer Konsum, Kommunikation",
           2: "Energie, Grundstoffe, Industrie, Finanzwerte",
           3: "Energie, Versorger, Gold",
           4: "Versorger, Basiskonsum, Gesundheit, Staatsanleihen"}


def _bis(s, bis):
    return s[s.index <= pd.Timestamp(bis)] if bis else s


def _jahresrate(s):
    """Veränderung zum Vorjahr in Prozent (auf Wochenbasis)."""
    w = s.resample("W-FRI").last().dropna()
    return (w / w.shift(52) - 1) * 100


def _richtung(rate, schwelle, umgekehrt=False):
    """Steigt oder fällt die Rate gegenüber vor 13 Wochen?
    Liefert (Richtung 'steigt'|'fällt'|'unklar', Änderung, Wert vor 13 Wochen, Wert heute)."""
    r = rate.dropna()
    if len(r) < 2:
        return "unklar", np.nan, np.nan, np.nan
    alt = r[r.index <= r.index[-1] - pd.Timedelta(weeks=13)]
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
        "Kupfer/Gold": _richtung(_jahresrate(_bis(hg / gc.reindex(hg.index, method="ffill"), bis)), 2),
        "Zyklischer gegen Basiskonsum": _richtung(_jahresrate(_bis(xly / xlp.reindex(xly.index, method="ffill"), bis)), 2),
        "Weekly Economic Index": _richtung(_bis(md.fred("WEI"), bis).resample("W-FRI").last(), 0.25),
        "Erstanträge Arbeitslosenhilfe": _richtung(_jahresrate(_bis(md.fred("ICSA"), bis).rolling(4).mean()), 2, umgekehrt=True),
        "GDPNow": _richtung(_bis(md.fred("GDPNOW"), bis).resample("W-FRI").last().ffill(), 0.25),
    }
    inflation = {
        "Rohstoffkorb (DBC)": _richtung(_jahresrate(_bis(md.yahoo("DBC"), bis)), 2),
        "Öl": _richtung(_jahresrate(_bis(md.yahoo("CL=F"), bis)), 2),
        "Breakeven-Inflation 5 Jahre": _richtung(_bis(md.fred("T5YIE"), bis).resample("W-FRI").last(), 0.05),
    }
    return wachstum, inflation


def _amtlich(bis):
    bip = _bis(md.fred("GDPC1"), bis)
    cpi = _bis(md.fred("CPIAUCSL"), bis)
    bip_rate = (bip / bip.shift(4) - 1) * 100
    cpi_rate = (cpi / cpi.shift(12) - 1) * 100
    w = "steigt" if bip_rate.iloc[-1] > bip_rate.iloc[-2] else "fällt"
    i = "steigt" if cpi_rate.iloc[-1] > cpi_rate.iloc[-4] else "fällt"
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


def _rang(s, wert, jahre=10):
    """Perzentil des Wertes in der eigenen Geschichte der letzten zehn Jahre (0–100)."""
    teil = s[s.index > s.index[-1] - pd.Timedelta(days=365 * jahre)].dropna()
    return float((teil <= wert).mean() * 100) if len(teil) else 50.0


def _messwerte(bis):
    vix = _bis(md.yahoo("^VIX"), bis)
    hyg, ief = md.yahoo("HYG"), md.yahoo("IEF")
    verh = (hyg / ief.reindex(hyg.index, method="ffill")).dropna()
    # Das Verhältnis steigt über die Jahre schon durch die höheren Zinsen der Hochzinsanleihen.
    # Gemessen wird deshalb der Abstand zum eigenen 52-Wochen-Hoch: 0 = ruhig, stark negativ = Stress.
    kredit = _bis(verh / verh.rolling(252, min_periods=60).max() - 1, bis).dropna() * 100
    br = _bis(md.breite(), bis)
    spx = _bis(md.yahoo("^GSPC"), bis)
    return {
        "vix_rang": _rang(vix, vix.iloc[-1]), "vix": float(vix.iloc[-1]),
        "kredit_rang": _rang(kredit, kredit.iloc[-1]),                        # hoch = Gier
        "kredit_4w": float(kredit.iloc[-1] - kredit.iloc[-21]),              # negativ = Aufschlag weitet sich
        "breite": float(br.iloc[-1]), "breite_4w": float(br.iloc[-1] - br.iloc[-21]),
        "breite_max60": float(br.iloc[-60:].max()),
        "breite_min120": float(br.iloc[-120:].min()),
        "levy": float(spx.iloc[-1] / spx.iloc[-130:].mean()),
        "nah_hoch": bool(spx.iloc[-1] >= spx.iloc[-252:].max() * 0.97),
        "ueber_gd200": bool(spx.iloc[-1] > spx.iloc[-200:].mean()),
    }


def _zone(m):
    """Einordnung in die sieben Zonen; Reihenfolge der Prüfung = Vorrang."""
    if m["vix_rang"] >= 90 and m["breite"] <= 20:
        return "Kapitulation"
    if m["vix_rang"] >= 80 and (m["breite_4w"] <= -15 or m["kredit_4w"] <= -2):
        return "Abwärtsbeschleunigung"
    # Frühe Erholung: Breite dreht kräftig nach oben, kurz nach einem Tief der Breite,
    # während VIX oder Kreditstress noch erhöht sind
    if m["breite_4w"] >= 10 and m["breite_min120"] <= 25 and (m["vix_rang"] >= 60 or m["kredit_rang"] <= 40):
        return "Frühe Erholung"
    if not m["ueber_gd200"] and m["breite"] <= 40:
        return "Bodenbildung"
    if m["vix_rang"] <= 15 and m["kredit_rang"] >= 85 and m["levy"] >= 1.10:
        return "Überhitzung"
    if m["nah_hoch"] and m["breite"] <= m["breite_max60"] - 10 and m["kredit_4w"] < 0:
        return "Topbildung"
    if m["ueber_gd200"] and m["breite"] >= 50:
        return "Gesunder Aufwärtstrend"
    return "Bodenbildung" if not m["ueber_gd200"] else "Topbildung"


def pendel(bis=None):
    heute = pd.Timestamp(bis) if bis else pd.Timestamp.today().normalize()
    m = _messwerte(heute)
    zone = _zone(m)
    vorher = _zone(_messwerte(heute - pd.Timedelta(weeks=4)))
    schritt = (ZONEN.index(zone) - ZONEN.index(vorher)) % len(ZONEN)
    pfeil = "→" if schritt == 0 else "↗" if schritt <= 3 else "↘"
    return {"zone": zone, "ampel": ZONEN_AMPEL[zone], "vor_4_wochen": vorher, "pfeil": pfeil, "messwerte": m}
