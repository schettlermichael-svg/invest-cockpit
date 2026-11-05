"""Abnahme Datenampel: (1) künstlich gestörte Kurse müssen erkannt werden, (2) die eingefrorenen
Kurse der Prüfgalerie dürfen keinen Fehlalarm geben. Aufruf: python3 werkzeuge/daten_test.py"""
import glob
import os
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import datenpruefung  # noqa: E402

GALERIE = os.path.join(HIER, "..", "pruefgalerie", "daten")
lade = lambda p: pd.read_csv(p, parse_dates=["Datum"], index_col="Datum")   # noqa: E731
index = lade(os.path.join(GALERIE, "index_sp500.csv"))
basis = lade(os.path.join(GALERIE, "MF1.csv"))
basis = basis[basis.index <= index.index[-1]]
ix = index[index.index <= basis.index[-1]]

def stoerung(name, df, erwartet):
    erg = datenpruefung.pruefen(df, ix)
    ok = erg["ampel"] == erwartet
    print(f'{"✓" if ok else "✗"} {name:32} erwartet {erwartet:5} ist {erg["ampel"]:5} {[z[2] for z in erg["zeichen"]]}')
    return ok

ergebnis = [stoerung("sauber", basis, "grün")]
d = basis.copy(); d.iloc[:-100, :4] = d.iloc[:-100, :4] / 2          # Split nicht bereinigt
ergebnis.append(stoerung("Split nicht bereinigt", d, "gelb"))
d = basis.drop(basis.index[-80:-70])                                     # 10 Tage fehlen
ergebnis.append(stoerung("Lücke 10 Tage", d, "rot"))
d = basis.copy(); d.iloc[-30:-25, d.columns.get_loc("Volume")] = 0       # Volumen null
ergebnis.append(stoerung("Volumen null 5 Tage", d, "gelb"))
d = basis.iloc[:-5]                                                      # veraltet
ergebnis.append(stoerung("veraltet um 5 Tage", d, "rot"))
d = basis.copy(); d.iloc[-50, d.columns.get_loc("Close")] = float("nan")
ergebnis.append(stoerung("fehlender Schlusskurs", d, "rot"))

print()
fehl = []
for p in sorted(glob.glob(os.path.join(GALERIE, "*.csv"))):
    if "index" in p:
        continue
    df = lade(p)
    i = index[(index.index >= df.index[0]) & (index.index <= df.index[-1])]
    for ende in range(252, len(df), 252):                               # jedes Jahr der Historie
        teil = df.iloc[:ende]
        erg = datenpruefung.pruefen(teil, i[i.index <= teil.index[-1]])
        if erg["ampel"] != "grün":
            fehl.append((os.path.basename(p), teil.index[-1].date(), erg["ampel"], [z[2] for z in erg["zeichen"]]))
print(f"Prüfgalerie: {len(fehl)} Jahresausschnitte mit Zeichen")
for f in fehl[:40]:
    print("  ", f)
print(f"\nStörungen erkannt: {sum(ergebnis)} von {len(ergebnis)}")
