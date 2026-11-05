"""Lageleiste rechnen: heute und an bekannten Zeitpunkten (Prüfung von Pendel und Quadrant).
Aufruf im Ordner InvestCockpit:  python3 werkzeuge/lage_test.py
Der erste Lauf lädt die Marktbreite für rund 500 Aktien ab 2006 (einige Minuten).
Ergebnis: werkzeuge/lage_test.txt"""
import os
import sys
import traceback

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import lage  # noqa: E402

PRUEFTAGE = [("2008-10-24", "Kapitulation / Abwärts", "Quad 4"), ("2009-03-09", "Kapitulation / Boden", "Quad 4"),
             ("2009-06-01", "Frühe Erholung", "–"), ("2013-06-03", "Gesunder Trend", "–"),
             ("2018-01-26", "Überhitzung", "Quad 2"), ("2018-12-24", "Abwärts / Kapitulation", "–"),
             ("2020-03-23", "Kapitulation", "Quad 4"), ("2020-06-08", "Frühe Erholung", "–"),
             ("2021-06-01", "Gesunder Trend / Überhitzung", "Quad 2"), ("2021-12-31", "Topbildung", "–"),
             ("2022-06-16", "Abwärts", "Quad 3"), ("2022-10-12", "Bodenbildung", "Quad 3/4"),
             ("2023-06-30", "Gesunder Trend", "Quad 1"), (None, "heute", "")]
with open(os.path.join(HIER, "lage_test.txt"), "w", encoding="utf-8") as f:
    for tag, buch_p, buch_q in PRUEFTAGE:
        try:
            p = lage.pendel(tag)
            q = lage.quadrant(tag)
            a = lage.marktampel(tag)
            m = p["messwerte"]
            f.write(f"{tag or 'heute':10}  Pendel: {p['zone']:24} {p['pfeil']} (erwartet {buch_p:28}) "
                    f"Quad {q['quad']} {q['name']:11} amtlich {q['amtlich']} (erwartet {buch_q:8}) "
                    f"Ampel {a['ampel']:5} | VIX-Rang {m['vix_rang']:.0f} Kredit-Rang {m['kredit_rang']:.0f} "
                    f"Breite {m['breite']:.0f} ({m['breite_4w']:+.0f}) Levy {m['levy']:.2f} | "
                    f"W {q['wachstum']['steigt']}↑{q['wachstum']['fällt']}↓ I {q['inflation']['steigt']}↑{q['inflation']['fällt']}↓\n")
            print(f"✓ {tag or 'heute'}", flush=True)
        except Exception:
            f.write(f"{tag}  FEHLER\n{traceback.format_exc()}\n")
            print(f"✗ {tag}", flush=True)
    q = lage.quadrant()
    f.write("\nInstrumente heute:\n")
    for achse in ("wachstum", "inflation"):
        for name, (r, d, *_) in q[achse]["instrumente"].items():
            f.write(f"  {achse:9} {name:32} {r:7} {d:+.2f}\n")
print("Fertig: werkzeuge/lage_test.txt")
