"""Phasenerkennung nach Weinstein/Minervini (Regelkatalog Kap. 5) – auf Wochenbasis.

phasen(df) -> pandas.Series   Phase 1–4 für jede Woche (Freitag), aus Tageskursen
phase_heute(df) -> dict       aktuelle Phase, die sechs Übergangskriterien als Ampeln, Warnzeichen

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
    for i, b in enumerate(roh):
        vorher = roh[i - 1] if i else 0
        z = w.iloc[i]
        serie2 = serie2 + 1 if b == 2 else 0
        if b == 2 and (serie2 >= 2 if phase == 2 else serie2 >= NEUSTART_WOCHEN):
            if phase in (1, 4) and (z.Close < 1.25 * z.tief52 or z.Close <= z.hoch26_vor):
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
        seit4 = seit4 + 1 if phase == 4 else 0
        aus.append(phase)
    return pd.Series(aus, index=w.index, name="phase")


def phase_heute(df):
    w = wochen(df)
    if len(w) < 45:
        return {"phase": None, "kriterien": {}, "warnungen": ["zu kurze Historie"]}
    ph = phasen(df)
    z = w.iloc[-1]
    letzte = w.iloc[-20:]
    hochs = letzte["High"].rolling(5).max().iloc[[-16, -11, -6, -1]].to_numpy()
    tiefs = letzte["Low"].rolling(5).min().iloc[[-16, -11, -6, -1]].to_numpy()
    auf = letzte[letzte["Close"] > letzte["Open"]]
    ab = letzte[letzte["Close"] <= letzte["Open"]]
    vol_schnitt = w["Volume"].iloc[-50:].mean()
    kriterien = {
        "Kurs über GD30W und GD40W": bool(z.Close > z.gd30 and z.Close > z.gd40),
        "GD30W über GD40W": bool(z.gd30 > z.gd40),
        "GD40W steigt": bool(z.steig40 > STEIGT),
        "höhere Hochs und höhere Tiefs": bool(np.all(np.diff(hochs) >= 0) and np.all(np.diff(tiefs) >= 0)),
        "Volumenspitzen an Aufwärtswochen": bool(auf["Volume"].max() > ab["Volume"].max()) if len(auf) and len(ab) else False,
        "mehr Aufwärts- als Abwärtswochen mit hohem Volumen":
            bool((auf["Volume"] > vol_schnitt).sum() > (ab["Volume"] > vol_schnitt).sum()),
    }
    warnungen = []
    # Größter Wochenrückgang seit Beginn von Phase 2, mit hohem Volumen (Phase-3-Zeichen)
    beginn = ph[ph != 2].index[-1] if (ph != 2).any() else ph.index[0]
    seit = w[w.index > beginn]
    if len(seit) >= 8:
        rueck = seit["Close"].pct_change()
        if rueck.iloc[-1] == rueck.min() and rueck.iloc[-1] < -0.05 and z.Volume > 2 * vol_schnitt:
            warnungen.append("größter Wochenrückgang seit Phase-2-Beginn mit hohem Volumen")
    return {"phase": int(ph.iloc[-1]), "kriterien": kriterien, "warnungen": warnungen}


# ── Stimmungszone eines einzelnen Titels (Stimmungskurve auf der Titelseite) ───────────────
# Angstindex und Kreditrisiko gelten nur für den ganzen Markt; für einen Titel ergibt sich die
# Zone aus Phase, Überdehnung und Volumen. Schwellen gesetzt, nicht aus dem Buch:
UEBERDEHNT_GD200 = 0.70     # Kurs mindestens 70 % über dem GD200 …
CLIMAX_ANSTIEG = 0.25       # … oder Climax-Lauf: mindestens 25 % Anstieg in höchstens 15 Handelstagen
KAPITULATION_RUECKGANG = 0.40   # mindestens 40 % unter dem 52-Wochen-Hoch …
KAPITULATION_VOLUMEN = 3.0      # … und in den letzten 10 Tagen ein Abwärtstag mit 3-fachem Volumen


def stimmungszone(df, ph_reihe, bis=None):
    """Zone der Stimmungskurve für einen Titel am Tag bis (Standard: letzter Tag)."""
    d = df[df.index <= pd.Timestamp(bis)] if bis is not None else df
    if len(d) < 220 or ph_reihe is None:
        return None
    p = ph_reihe[ph_reihe.index <= d.index[-1] + pd.Timedelta(days=6)]
    if p.empty:
        return None
    ph = int(p.iloc[-1])
    c, v = d["Close"], d["Volume"]
    k = c.iloc[-1]
    if ph == 1:
        gd50 = c.rolling(50).mean()
        return "Frühe Erholung" if k > gd50.iloc[-1] > gd50.iloc[-11] else "Bodenbildung"
    if ph == 2:
        gd200 = c.iloc[-200:].mean()
        climax = k / c.iloc[-16:-1].min() - 1 >= CLIMAX_ANSTIEG
        return "Überhitzung" if k / gd200 - 1 >= UEBERDEHNT_GD200 or climax else "Gesunder Aufwärtstrend"
    if ph == 3:
        return "Topbildung"
    hoch = d["High"].iloc[-252:].max()
    v50 = v.rolling(50).mean()
    letzte = d.iloc[-10:]
    abwaerts = letzte["Close"] < c.shift(1).iloc[-10:]
    ausverkauf = ((letzte["Volume"] >= KAPITULATION_VOLUMEN * v50.iloc[-10:]) & abwaerts).any()
    return "Kapitulation" if k <= (1 - KAPITULATION_RUECKGANG) * hoch and ausverkauf else "Abwärtsbeschleunigung"
