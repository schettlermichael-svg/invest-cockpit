"""Abnahme Schritt 2: bekannte Rotationen. Aufruf: python3 werkzeuge/sektoren_test.py

Gemessen wird, in wie vielen Wochen eines Jahres der Sektor stärker als der Markt war.
Grün: bekannter Führer mindestens 70 %, bekannter Verlierer höchstens 40 %.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kern"))
import sektoren  # noqa: E402

FAELLE = [("XLE", 2022, True, "Energie führt im Rohstoff- und Inflationsjahr"),
          ("XLK", 2022, False, "Technologie hinten im Zinsanstieg"),
          ("XLK", 2023, True, "Technologie führt (KI)"),
          ("XLE", 2023, False, "Energie hinten nach dem Ölpreishoch"),
          ("XLK", 2020, True, "Technologie führt im Corona-Jahr"),
          ("XLE", 2020, False, "Energie bricht ein"),
          ("XLP", 2008, True, "Basiskonsum hält im Crash"),
          ("XLF", 2008, False, "Finanzwerte in der Finanzkrise")]
ok = 0
for etf, jahr, fuehrer, text in FAELLE:
    a = sektoren.stark_anteil(etf, jahr)
    gut = a >= 70 if fuehrer else a <= 40
    ok += gut
    print(f'{"✓" if gut else "✗"} {jahr} {sektoren.SEKTOREN[etf]:12} {a:4.0f} % der Wochen stärker als der Markt – {text}')
print(f"{ok} von {len(FAELLE)} bestanden")
