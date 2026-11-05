"""Fundament-Ampeln für einige Titel berechnen und ausgeben (lädt Yahoo + SEC).
Aufruf im Ordner InvestCockpit:  python3 werkzeuge/fundament_test.py [TICKER ...]
Schreibt werkzeuge/fundament_test.txt."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import fundament
import quellen

titel = sys.argv[1:] or ["NVDA", "HWM", "LLY", "AXON", "CRWD"]
with open(os.path.join(HIER, "fundament_test.txt"), "w", encoding="utf-8") as f:
    for tk in titel:
        try:
            d = quellen.laden(tk, neu=True)
            erg = fundament.ampeln(d)
            f.write(f"\n===== {tk} =====\n")
            for name, (ampel, text) in erg["punkte"].items():
                f.write(f"{ampel:5} {name}: {text}\n")
            f.write("Zeichen: " + (", ".join(erg["zeichen"]) or "–") + "\n")
            sec = d["sec"]
            f.write("SEC-Quartale (letzte 9):\n" + (sec.tail(9).to_string() if not sec.empty else "leer") + "\n")
            print(f"✓ {tk}", flush=True)
        except Exception as e:
            f.write(f"\n===== {tk} FEHLER: {e}\n")
            print(f"✗ {tk}: {e}", flush=True)
print("Fertig: werkzeuge/fundament_test.txt")
