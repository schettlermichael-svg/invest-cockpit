"""Übergänge: wer an der Tür zum nächsten Feld steht (für die Rudelkarte). Die Tafel „Übergänge“ auf der Übersicht
entfällt seit 06.11.2026 (in _to_delete/uebergaenge_tafel_2026-11-06.py).

Der Kreislauf läuft im Uhrzeigersinn: Abgehängt → Erstarkend → Führend → Ermüdend → Abgehängt.
Der Schwung dreht vor der Stärke: Die Türen Abgehängt → Erstarkend und Führend → Ermüdend melden früh,
die Türen Erstarkend → Führend und Ermüdend → Abgehängt bestätigen. „An der Tür“ heißt: höchstens NAH Punkte
vor der 100-Linie der entscheidenden Achse und die Bewegung der letzten 5 Wochen zeigt auf die Tür.
Ein Haken ist eine Gruppe, die vor der Tür zurück in ihr altes Feld dreht.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

from frontkarte import richtung                                     # noqa: E402

NAH = 3.0                 # Punkte vor der 100-Linie


def tuer(r):
    """'Tür' mit Zielfeld, 'Haken' mit Rückfeld oder None."""
    s, m, f = r["staerke"], r["schwung"], r["feld"]
    h, v = richtung(r)
    if f == "Abgehängt" and 100 - m <= NAH and v == 1:
        return "Tür", "Erstarkend"
    if f == "Erstarkend":
        if 100 - s <= NAH and h == 1:
            return "Tür", "Führend"
        if m - 100 <= NAH and v == -1:
            return "Haken", "Abgehängt"
    if f == "Führend" and m - 100 <= NAH and v == -1:
        return "Tür", "Ermüdend"
    if f == "Ermüdend":
        if s - 100 <= NAH and h == -1:
            return "Tür", "Abgehängt"
        if 100 - m <= NAH and v == 1:
            return "Haken", "Führend"
    return None
