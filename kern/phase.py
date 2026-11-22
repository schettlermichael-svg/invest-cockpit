"""Phasenerkennung nach Weinstein (Stufen) – auf Wochenbasis, an der 40-Wochen-Linie (GD40W).

phasen(df) -> pandas.Series        Phase 1–4 für jede Woche (Freitag), aus Tageskursen
rechnen(df) -> (phase, zusatz, basis)  dazu der Zusatz je Woche („Rücksetzer“ in Phase 2, „Ausbruch“ während des Wechsels
                                       1 → 2, sonst „“) und das Hoch der Basis, solange der Ausbruch läuft

Schritt 8 der Gefechtsordnung (Micky 16.11.2026, Weinstein: Stufe 3 beginnt erst, wenn die Linie nach dem Anstieg flach
wird; Stufe 2 beginnt mit dem Ausbruch über das Hoch der Basis):
Phase 2: aus Phase 1 mit dem Ausbruch – Wochenschluss über dem Hoch der Basis (höchster Wochenschluss seit Beginn
         der Phase 1) und über dem GD40W, der nicht mehr fällt. Aus Phase 4 führt der Weg immer über die Basis (Phase 1).
         Ab da steht der Wechsel „1 → 2 · Ausbruch“; Phase 2 ist bestätigt, sobald der GD40W steigt (über 0,5 % in
         4 Wochen). Schließt eine Woche vorher wieder unter dem Basis-Hoch oder dem GD40W, ist der Ausbruch gescheitert.
         Aus Phase 3 zurück in Phase 2 erst nach vier Wochen Phase-2-Bild (Kurs über GD30W und GD40W, GD30W über GD40W,
         GD40W steigt).
Phase 2 · Rücksetzer: das Phase-2-Bild fehlt (Kurs unter GD30W/GD40W oder die Schwankung explodiert), aber der GD40W
         steigt noch – für Weinstein noch Stufe 2.
Phase 3: nach Phase 2, sobald der GD40W nicht mehr steigt (höchstens 0,5 % in 4 Wochen) und das Phase-2-Bild fehlt.
Phase 4: Kurs unter GD40W, GD40W fällt, GD30W unter GD40W, Kurs mehr als 5 % unter dem Stand von vor 13 Wochen (Treppe
         abwärts), zwei Wochen in Folge; pendelt der Kurs dagegen um einen nur leicht fallenden GD40W (mindestens zwei
         Kreuzungen in 26 Wochen, Gefälle unter 3 %), ist es kein Abwärtsbild. Aus Phase 3 auch, wenn der Kurs zwei Wochen
         unter dem fallenden GD40W schließt.
Phase 1: nach Phase 4 frühestens nach 8 Wochen, sobald das Abwärtsbild zwei Wochen fehlt und der GD40W nicht mehr fällt.
"""
import numpy as np
import pandas as pd
from masse import P_ABWAERTS  # noqa: E402

RUECKSETZER = 22      # Phase 2 · Rücksetzer als Wochencode (Kreislaufbild, Bruch der Spanne)
STEIGT = 0.005        # GD40W über 4 Wochen um mehr als 0,5 % gestiegen
FAELLT = -0.005
NEUSTART_WOCHEN = 4   # aus Phase 3 zurück in Phase 2 erst nach 4 Wochen Phase-2-Bild


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
STEIG_WOCHEN = 4         # Steigung der 40-Wochen-Linie über 4 Wochen
HALBJAHR_W = 26          # 26 Wochen (Kreuzungen, Hoch davor)
QUARTAL_W = 13           # Treppe abwärts: tiefer als vor 13 Wochen
MIN_WOCHEN_HOCH = 10     # Hoch der 26 Wochen ab 10 Wochen Daten
SEITWAERTS_STEIG = 0.03  # seitwärts: mindestens 2 Kreuzungen in 26 Wochen und die Linie fällt höchstens 3 %
TREPPE_ROC = 0.05        # Treppe abwärts: 13 Wochen mindestens 5 % tiefer
SPANNE_GLAETTEN = 0.9    # geglättete Wochenspanne: 90 % alt …
SPANNE_NEU = 0.1         # … 10 % neu
SPANNE_SPRUNG = 1.8      # Wochenspanne 1,8-fach der geglätteten: Ausbruchswoche
SPERRE_WOCHEN = 8        # nach Phase 4 frühestens nach 8 Wochen zurück in Phase 1
SEITWAERTS_KREUZ = 2   # seitwärts: mindestens 2 Kreuzungen der 30-Wochen-Linie in 26 Wochen


def wochen(df):
    w = df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min",
                                  "Close": "last", "Volume": "sum"}).dropna()
    w["gd10"] = w["Close"].rolling(10).mean()
    w["gd30"] = w["Close"].rolling(30).mean()
    w["gd40"] = w["Close"].rolling(40).mean()
    w["steig40"] = w["gd40"] / w["gd40"].shift(STEIG_WOCHEN) - 1
    w["spanne"] = (w["High"] / w["Low"] - 1).rolling(10).mean()
    ueber = (w["Close"] > w["gd40"]).astype(int)
    w["kreuz26"] = ueber.diff().abs().rolling(HALBJAHR_W).sum()
    w["roc13"] = w["Close"] / w["Close"].shift(QUARTAL_W) - 1
    w["hoch26_vor"] = w["Close"].shift(1).rolling(HALBJAHR_W, min_periods=MIN_WOCHEN_HOCH).max()
    return w


def ist_seitwaerts(z):
    """Kurs pendelt um einen flachen oder nur leicht fallenden GD40W."""
    return z.kreuz26 >= SEITWAERTS_KREUZ and z.steig40 > -SEITWAERTS_STEIG


def bild(z):
    """Rohes Bild einer Woche: 2, 4 oder 0 (unklar)."""
    if np.isnan(z.gd40) or np.isnan(z.steig40):
        return 0
    if z.Close > z.gd30 and z.Close > z.gd40 and z.gd30 > z.gd40 and z.steig40 > STEIGT:
        return 2
    seitwaerts = ist_seitwaerts(z)
    if (z.Close < z.gd40 and z.steig40 < FAELLT and z.gd30 < z.gd40 and z.roc13 < -TREPPE_ROC
            and not seitwaerts):
        return P_ABWAERTS                                            # Treppe abwärts: tiefer als vor 13 Wochen
    return 0


def rechnen(df):
    """Phase, Zusatz und Basis-Hoch des laufenden Ausbruchs je Woche (siehe Kopf) → (phase, zusatz, basis) als Series."""
    w = wochen(df)
    roh = [bild(z) for z in w.itertuples()]
    phase, aus, zus, bas, spanne2, serie2, seit4 = 1, [], [], [], None, 0, 0
    basis_hoch = None             # höchster Wochenschluss seit Beginn der Phase 1
    ausbruch = None               # Basis-Hoch, über das der Kurs ausgebrochen ist (Wechsel 1 → 2 läuft)
    for i, b in enumerate(roh):
        vorher = roh[i - 1] if i else 0
        z = w.iloc[i]
        serie2 = serie2 + 1 if b == 2 else 0
        zusatz, bestaetigt = "", False
        if phase == 1 and not np.isnan(z.gd40) and not np.isnan(z.steig40):
            hoch = basis_hoch if basis_hoch is not None else z.hoch26_vor
            if ausbruch is not None and (z.Close <= ausbruch or z.Close <= z.gd40):
                ausbruch = None                             # zurück in die Basis: Ausbruch gescheitert
            if ausbruch is None and not np.isnan(hoch) and z.Close > hoch and z.Close > z.gd40 and z.steig40 >= FAELLT:
                ausbruch = hoch
            if ausbruch is not None and z.steig40 > STEIGT:
                phase, ausbruch, spanne2, bestaetigt = 2, None, z.spanne, True     # bestätigt: die Linie steigt
            elif ausbruch is not None:
                zusatz = "Ausbruch"
        if bestaetigt:
            pass
        elif b == 2 and (phase == 2 or (phase == 3 and serie2 >= NEUSTART_WOCHEN)):
            phase = 2
            spanne2 = z.spanne if spanne2 is None else SPANNE_GLAETTEN * spanne2 + SPANNE_NEU * z.spanne
            if spanne2 and z.spanne > SPANNE_SPRUNG * spanne2 and z.Close < z.gd10:
                zusatz = "Rücksetzer"                       # Schwankung explodiert, Kurs bricht ein – Linie steigt noch
        elif b == P_ABWAERTS and vorher == P_ABWAERTS and phase != P_ABWAERTS:
            phase, spanne2, ausbruch, zusatz = P_ABWAERTS, None, None, ""
        elif phase == 2 and b != 2:
            if z.steig40 > STEIGT:
                zusatz = "Rücksetzer"                       # Phase-2-Bild fehlt, die Linie steigt noch (Weinstein: Stufe 2)
            else:
                phase = 3                                   # die Linie ist flach geworden: Verteilung
        elif (phase == 3 and z.Close < z.gd40 and w.iloc[i - 1].Close < w.iloc[i - 1].gd40
              and z.steig40 < FAELLT and not ist_seitwaerts(z)):
            phase = 4                                       # zwei Wochen unter fallendem GD40W (Weinstein: die Linie
            #                                                 fällt – flach ist sie bei weniger als 0,5 % in 4 Wochen;
            #                                                 Chart-Prüfer 14.11.2026, LUV: −0,1 % galt als fallend)
        if phase == 4 and seit4 >= SPERRE_WOCHEN and b != P_ABWAERTS and vorher != P_ABWAERTS and z.steig40 >= FAELLT:
            phase = 1                                       # Abwärtsbild weg, GD40W fällt nicht mehr
            basis_hoch = None
        if phase == 1:
            basis_hoch = z.Close if basis_hoch is None else max(basis_hoch, z.Close)
        seit4 = seit4 + 1 if phase == 4 else 0
        aus.append(phase)
        zus.append(zusatz)
        bas.append(ausbruch if zusatz == "Ausbruch" else np.nan)
    return (pd.Series(aus, index=w.index, name="phase"), pd.Series(zus, index=w.index, name="zusatz"),
            pd.Series(bas, index=w.index, name="basis"))


def phasen(df):
    return rechnen(df)[0]


def aktuell(df, ph=None):
    """Die Phase heute, für die ganze App gleich gelesen (Prüf-Agent 13.11.2026: Karte, Titelseite und Kreislauf lasen
    sie verschieden): die Woche zählt erst ab ihrem Freitag – die laufende Woche noch nicht. ph: phasen(df), falls schon
    gerechnet."""
    ph = phasen(df) if ph is None else ph
    fertig = ph[ph.index <= df.index[-1]]
    return int(fertig.iloc[-1]) if len(fertig) else int(ph.iloc[0])
