"""Titelseite als eigenständige HTML-Datei schreiben (gleiche Seite wie in der App).
Aufruf im Ordner InvestCockpit:  python3 werkzeuge/vorschau.py HWM [Woche]
Ergebnis: vorschau/<TICKER>.html – im Browser öffnen oder in die Designvorlage übernehmen."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "oberflaeche"))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import titel  # noqa: E402

tk = sys.argv[1] if len(sys.argv) > 1 else "HWM"
ebene = sys.argv[2] if len(sys.argv) > 2 else "Tag"
html = titel.seite_titel(tk, ebene)
ziel = os.path.join(HIER, "..", "vorschau")
os.makedirs(ziel, exist_ok=True)
pfad = os.path.join(ziel, f"{tk.upper()}{'' if ebene == 'Tag' else '_woche'}.html")
with open(pfad, "w", encoding="utf-8") as f:
    f.write("<!doctype html><html lang='de'><head><meta charset='utf-8'><title>Invest Cockpit – "
            f"{tk.upper()}</title></head><body style='margin:0;background:#0E1217'>{html}</body></html>")
print(f"Fertig: {os.path.abspath(pfad)}")
