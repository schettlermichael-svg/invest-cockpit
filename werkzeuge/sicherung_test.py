"""Abnahme der gegenseitigen Absicherung (ohne Netz, mit künstlichen Daten):
1. Gegenprobe Yahoo gegen Massive in der Datenampel
2. Split-Korrektur beim Nachtrag der Marktbreite aus Massive
3. Plausibilitätswächter der Marktbreite (Abdeckung, Sprung, veraltet, Ersatzquelle)
Aufruf: python3 werkzeuge/sicherung_test.py"""
import os
import sys
import tempfile

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import datenpruefung  # noqa: E402
import marktdaten     # noqa: E402
import massive        # noqa: E402

ok = []
def pruef(name, bedingung, info=""):
    ok.append(bool(bedingung))
    print(f'{"✓" if bedingung else "✗"} {name} {info}')

tage = pd.bdate_range("2025-01-01", periods=300)
kurs = pd.Series(np.linspace(100, 150, 300), index=tage)
df = pd.DataFrame({"Open": kurs, "High": kurs * 1.01, "Low": kurs * 0.99, "Close": kurs, "Volume": 1e6})

# 1. Gegenprobe
gleich = kurs.iloc[-5:].copy()
pruef("Gegenprobe gleich → grün", datenpruefung.pruefen(df, gegenprobe=gleich)["ampel"] == "grün")
falsch = gleich.copy(); falsch.iloc[-1] *= 1.03
erg = datenpruefung.pruefen(df, gegenprobe=falsch)
pruef("Gegenprobe 3 % daneben → gelb", erg["ampel"] == "gelb", [z[2] for z in erg["zeichen"]])
alt_div = gleich.copy(); alt_div.iloc[:-1] *= 1.02          # ältere Tage um Dividende verschieden
pruef("ältere Tage verschieden (Dividende) → grün", datenpruefung.pruefen(df, gegenprobe=alt_div)["ampel"] == "grün")

# 2. Split-Korrektur beim Nachtrag
alt = pd.DataFrame({"AAA": np.full(250, 100.0), "BBB": np.full(250, 50.0)},
                   index=pd.bdate_range(end=pd.Timestamp.today().normalize() - pd.Timedelta(days=8), periods=250))
neu_tage = pd.bdate_range(alt.index[-1] + pd.Timedelta(days=1), pd.Timestamp.today().normalize() - pd.Timedelta(days=1))
split_tag = neu_tage[0]
massive.tag = lambda t: pd.DataFrame({"Ticker": ["AAA", "BBB"],
                                      "Close": [50.0 if pd.Timestamp(t) >= split_tag else 100.0, 50.0]})
massive.splits = lambda t: {"AAA": 0.5} if pd.Timestamp(t) == split_tag else {}
s = marktdaten._breite_nachtrag_massive(alt)
pruef("Split 2:1 nachgerechnet (Historie halbiert, kein Bruch)",
      abs(s["AAA"].iloc[0] - 50) < 1e-9 and abs(s["AAA"].iloc[-1] - 50) < 1e-9, f'({s["AAA"].iloc[0]} → {s["AAA"].iloc[-1]})')

# 3. Plausibilitätswächter
mit = tempfile.mkdtemp()
marktdaten.SPEICHER = mit
idx = pd.bdate_range(end=pd.Timestamp.today().normalize() - pd.Timedelta(days=1), periods=40)
tab = pd.DataFrame({"breite": [55.0] * 39 + [80.0], "abdeckung": [510] * 39 + [400]}, index=idx)
tab.index.name = "Datum"
tab.to_csv(marktdaten._pfad("breite"))
pd.DataFrame({"Close": 1.0}, index=pd.Index(idx, name="Datum")).to_csv(marktdaten._pfad("^GSPC"))
open(os.path.join(mit, "breite_quelle.txt"), "w").write("Yahoo (Ersatz)")
z = marktdaten.breite_pruefung()
texte = " | ".join(t for _, t in z)
pruef("Abdeckung eingebrochen erkannt", "statt rund" in texte)
pruef("Sprung erkannt", "springt" in texte)
pruef("Ersatzquelle gemeldet", "ersatzweise" in texte)
tab.iloc[:-5].to_csv(marktdaten._pfad("breite"))
z = marktdaten.breite_pruefung()
pruef("veraltet erkannt", any("veraltet" in t for _, t in z), [t for _, t in z if "veraltet" in t])
print(f"\n{sum(ok)} von {len(ok)} bestanden")
