"""Phasenerkennung nach Weinstein/Minervini (Regelkatalog Kap. 5) – auf Wochenbasis.

phasen(df) -> pandas.Series   Phase 1–4 für jede Woche (Freitag), aus Tageskursen

Phase 2: Kurs über GD30W und GD40W, GD30W über GD40W, GD40W steigt.
Phase 4: Kurs unter GD40W, GD40W fällt, GD30W unter GD40W, Kurs mehr als 5 % unter dem Stand
         von vor 13 Wochen (Treppe abwärts). Pendelt der Kurs dagegen um einen nur leicht fallenden
         GD40W (mindestens zwei Kreuzungen in 26 Wochen, Gefälle unter 3 % je Monat), ist es Phase 1.
Phase 3: nach Phase 2, sobald der Kurs unter den GD40W fällt, das Phase-2-Bild zwei Wochen fehlt
         oder die Schwankung deutlich über dem Phase-2-Niveau liegt.
Phase 4: auch aus Phase 3 heraus, wenn der Kurs zwei Wochen unter dem fallenden GD40W schließt.
Phase 1: nach Phase 4, sobald das Bild zwei Wochen nicht mehr Phase 4 ist
         und der GD40W nicht mehr fällt.
Eine Phase gilt erst, wenn ihr Bild zwei Wochen in Folge vorliegt (gegen Flackern); zurück in
Phase 2 aus jeder anderen Phase erst nach vier Wochen Phase-2-Bild.
Aus Phase 1 heraus gilt Phase 2 erst, wenn der Kurs mindestens 25 % über dem 52-Wochen-Tief steht
(Minervini: vorher stets eine Rallye von 25–30 % vom Tief) und über dem höchsten Wochenschluss
der letzten 26 Wochen schließt (Ausbruch aus der Spanne der Bodenphase, erstes höheres Hoch).
"""
import numpy as np
import pandas as pd

STEIGT = 0.005        # GD40W über 4 Wochen um mehr als 0,5 % gestiegen
FAELLT = -0.005
NEUSTART_WOCHEN = 4   # aus Phase 1, 3 oder 4 zurück in Phase 2 erst nach 4 Wochen Phase-2-Bild


def wochen(df):
    w = df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min",
                                  "Close": "last", "Volume": "sum"}).dropna()
    w["gd10"] = w["Close"].rolling(10).mean()
    w["gd30"] = w["Close"].rolling(30).mean()
    w["gd40"] = w["Close"].rolling(40).mean()
    w["steig40"] = w["gd40"] / w["gd40"].shift(4) - 1
    w["spanne"] = (w["High"] / w["Low"] - 1).rolling(10).mean()
    ueber = (w["Close"] > w["gd40"]).astype(int)
    w["kreuz26"] = ueber.diff().abs().rolling(26).sum()
    w["roc13"] = w["Close"] / w["Close"].shift(13) - 1
    w["hoch26_vor"] = w["Close"].shift(1).rolling(26, min_periods=10).max()
    w["tief52"] = w["Low"].rolling(52, min_periods=20).min()
    return w


def ist_seitwaerts(z):
    """Kurs pendelt um einen flachen oder nur leicht fallenden GD40W."""
    return z.kreuz26 >= 2 and z.steig40 > -0.03


def bild(z):
    """Rohes Bild einer Woche: 2, 4 oder 0 (unklar)."""
    if np.isnan(z.gd40) or np.isnan(z.steig40):
        return 0
    if z.Close > z.gd30 and z.Close > z.gd40 and z.gd30 > z.gd40 and z.steig40 > STEIGT:
        return 2
    seitwaerts = ist_seitwaerts(z)
    if (z.Close < z.gd40 and z.steig40 < FAELLT and z.gd30 < z.gd40 and z.roc13 < -0.05
            and not seitwaerts):
        return 4                                            # Treppe abwärts: tiefer als vor 13 Wochen
    return 0


def phasen(df):
    w = wochen(df)
    roh = [bild(z) for z in w.itertuples()]
    phase, aus, spanne2, serie2, seit4 = 1, [], None, 0, 0
    basis_hoch = None             # höchster Wochenschluss seit Beginn der Phase 1 (Prüf-Agent 13.11.2026: nach einem tiefen
    #                               Fall kam Phase 2 erst über dem Hoch der letzten 26 Wochen – viel zu spät)
    for i, b in enumerate(roh):
        vorher = roh[i - 1] if i else 0
        z = w.iloc[i]
        serie2 = serie2 + 1 if b == 2 else 0
        if b == 2 and (serie2 >= 2 if phase == 2 else serie2 >= NEUSTART_WOCHEN):
            ueber = z.Close <= (basis_hoch if phase == 1 and basis_hoch is not None else z.hoch26_vor)
            if phase in (1, 4) and (z.Close < 1.25 * z.tief52 or ueber):
                aus.append(phase)                           # noch keine Rallye vom Tief bzw. kein
                continue                                    # Ausbruch über die Spanne der Bodenphase
            phase = 2
            spanne2 = z.spanne if spanne2 is None else 0.9 * spanne2 + 0.1 * z.spanne
            if spanne2 and z.spanne > 1.8 * spanne2 and z.Close < z.gd10:
                phase = 3                                   # Schwankung explodiert, Kurs bricht ein
        elif b == 4 and vorher == 4:
            phase = 4
            spanne2 = None
        elif phase == 2 and b != 2 and (z.Close < z.gd40 or vorher != 2):
            phase = 3                                       # unter GD40W oder Phase-2-Bild verloren
        elif (phase == 3 and z.Close < z.gd40 and w.iloc[i - 1].Close < w.iloc[i - 1].gd40
              and z.steig40 < 0 and not ist_seitwaerts(z)):
            phase = 4                                       # zwei Wochen unter fallendem GD40W
        elif phase == 4 and seit4 >= 8 and b != 4 and vorher != 4 and z.steig40 >= FAELLT:
            phase = 1                                       # Abwärtsbild weg, GD40W fällt nicht mehr
            basis_hoch = None
        if phase == 1:
            basis_hoch = z.Close if basis_hoch is None else max(basis_hoch, z.Close)
        seit4 = seit4 + 1 if phase == 4 else 0
        aus.append(phase)
    return pd.Series(aus, index=w.index, name="phase")


def aktuell(df, ph=None):
    """Die Phase heute, für die ganze App gleich gelesen (Prüf-Agent 13.11.2026: Karte, Titelseite und Kreislauf lasen
    sie verschieden): die Woche zählt erst ab ihrem Freitag – die laufende Woche noch nicht. ph: phasen(df), falls schon
    gerechnet."""
    ph = phasen(df) if ph is None else ph
    fertig = ph[ph.index <= df.index[-1]]
    return int(fertig.iloc[-1]) if len(fertig) else int(ph.iloc[0])
