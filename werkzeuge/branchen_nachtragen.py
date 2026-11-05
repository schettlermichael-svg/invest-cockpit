"""Sektor und Branche für das Revier von Yahoo nachtragen (dieselbe Einteilung wie auf der Titelseite).

Der NASDAQ-Screener ordnet viele Firmen falsch ein (Tanker als zyklischer Konsum, GE als Technologie,
Alphabet und Meta als Technologie statt Kommunikation). Dieses Werkzeug holt für jeden Titel, dessen
Sektor nicht von Yahoo stammt, den Steckbrief von Yahoo – langsam, damit Yahoo nicht sperrt:
eine Anfrage alle 4 Sekunden; bei einer Sperre 10 Minuten Pause, nach drei Sperren Schluss.
Es kann jederzeit abgebrochen und neu gestartet werden; es macht dort weiter, wo es aufgehört hat.
Jeder Steckbrief bleibt 100 Tage gespeichert (daten/kurse/<Ticker>_steckbrief.json).

Aufruf im Ordner InvestCockpit:  python3 werkzeuge/branchen_nachtragen.py     (alle Titel: etwa 2 Stunden)
"""
import logging
import os
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import daten      # noqa: E402
import sektoren   # noqa: E402

REVIER = os.path.join(HIER, "..", "einstellungen", "revier.csv")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def uebernehmen(r, s):
    r.loc[s.name, ["sektor", "branche", "etf", "quelle"]] = [s["sektor"], s["branche"],
                                                             sektoren.sektor_von(s["sektor"]) or "", "Yahoo"]
    if s.get("name"):
        r.loc[s.name, "name"] = s["name"]                    # Yahoo-Name statt „… Common Stock“


def main():
    r = pd.read_csv(REVIER, keep_default_na=False).set_index("ticker")
    offen = [tk for tk in r.index if r.loc[tk, "quelle"] != "Yahoo"]
    print(f"{len(offen)} von {len(r)} Titeln ohne Yahoo-Sektor", flush=True)
    sperren, fertig = 0, 0
    for i, tk in enumerate(offen, 1):
        sb = daten.steckbrief_gespeichert(tk)
        if not sb:
            while True:
                try:
                    time.sleep(4)
                    sb = daten.steckbrief(tk)
                    sperren = 0
                    break
                except Exception as e:
                    if "429" in str(e) or "Too Many" in str(e) or "Rate" in str(e):
                        sperren += 1
                        if sperren > 3:
                            print("Yahoo sperrt weiter – Schluss für heute. Später einfach neu starten.", flush=True)
                            r.reset_index().to_csv(REVIER, index=False)
                            return
                        print(f"  Yahoo sperrt – 10 Minuten Pause ({sperren}. Mal) …", flush=True)
                        time.sleep(600)
                    else:
                        print(f"  {tk}: kein Steckbrief ({e})", flush=True)
                        sb = None
                        break
        if sb and sb.get("sektor"):
            uebernehmen(r, pd.Series(sb, name=tk))
            fertig += 1
        if i % 50 == 0 or i == len(offen):
            r.reset_index().to_csv(REVIER, index=False)          # Zwischenstand sichern
            print(f"  {i} von {len(offen)} – {fertig} Sektoren übernommen", flush=True)
    rest = int((r["quelle"] != "Yahoo").sum())
    print(f"\nFertig. Noch ohne Yahoo-Sektor: {rest}")
    print(r.groupby("sektor").size().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
