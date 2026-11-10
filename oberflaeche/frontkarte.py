"""Sektoren-Werkzeuge (früher Frontkarte): Farben und Pfeile der vier Felder für Lagekarte, Quad-Bild und Rudelkarte,
dazu der Abgleich mit dem Quad. Die Vier-Felder-Tafel der Sektoren und die Themen-Gruppen entfielen am 10.11.2026 –
beides zeigt die Wetterkarte der Seite Rückenwind (Ebene Sektor bzw. Thema); Code in _to_delete.

Jeder Sektor steht in seinem Feld, sortiert nach relativer Stärke; darunter steht, seit wie vielen
Wochen er dort ist und aus welchem Feld er kam (Wechsel dieser Woche mit NEU). Der Pfeil zeigt die Bewegung der
letzten 5 Wochen in derselben Geometrie wie die Felder: nach rechts = Stärke nimmt zu, nach oben =
Schwung nimmt zu. Ein frei gezeichnetes Rotationsbild mit Schweifen war bei elf Sektoren unlesbar.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))

import sektoren                                                     # noqa: E402
from gestaltung import KARTE, RAND, ampelzeile, feld_name  # noqa: E402

FARBE = {"Führend": "#56D364", "Ermüdend": "#E3B341", "Abgehängt": "#FF7B72", "Erstarkend": "#7DB4FF"}
AMPEL = {"Führend": "grün", "Erstarkend": "blau", "Ermüdend": "gelb", "Abgehängt": "rot"}
PFEILE = {"↖": "Abwärtsdruck lässt nach", "↑": "Wende kündigt sich an", "↗": "Geld fließt zu",
          "←": "verliert weiter", "·": "kaum Bewegung", "→": "gewinnt weiter",
          "↙": "Geld fließt ab", "↓": "Schwung lässt nach", "↘": "Kraft lässt nach"}
SCHWELLE = 0.5            # Punkte in 5 Wochen, darunter gilt eine Achse als unverändert


def richtung(r):
    """Bewegung der letzten 5 Wochen (Mittel der Wochen 4–6 zurück → heute): (waagrecht, senkrecht) je −1, 0, +1."""
    alt = r["schweif"][-7:-4]
    ds = r["staerke"] - sum(a for a, _ in alt) / len(alt)
    dm = r["schwung"] - sum(b for _, b in alt) / len(alt)
    return (1 if ds > SCHWELLE else -1 if ds < -SCHWELLE else 0), (1 if dm > SCHWELLE else -1 if dm < -SCHWELLE else 0)


def _pfeil(r):
    """Bewegung der letzten 5 Wochen als Pfeil."""
    h, v = richtung(r)
    return {(1, 1): "↗", (1, 0): "→", (1, -1): "↘", (0, 1): "↑", (0, 0): "·",
            (0, -1): "↓", (-1, 1): "↖", (-1, 0): "←", (-1, -1): "↙"}[(h, v)]


def quad_abgleich(quad):
    """Abgleich mit dem Quad (aus der früheren Frontkarte, 10.11.2026 erhalten): führen die Sektoren, die im Quad
    typischerweise führen? Stehen sie hinten, widersprechen sich Markt und Wirtschaftswetter."""
    rot = sektoren.rotation()
    if not rot:
        return ""
    ab = sektoren.abgleich(rot, quad["quad"])
    zeilen = ampelzeile(f'{len(ab["vorne"])} von {len(ab["erwartet"])} typischen Quad-Sektoren vorne', ab["ampel"],
                        f'Nach dem Quad-Modell führen in Quad {quad["quad"]} ({quad["name"]}) typischerweise diese Sektoren. '
                        f'„Vorne“ heißt Führend oder Erstarkend. Stehen sie hinten, widersprechen Markt und Wirtschaftswetter '
                        f'sich – der Geldfluss traut dem Quad noch nicht.')
    for e in ab["erwartet"]:
        if e in rot:
            r = rot[e]
            zeilen += ampelzeile(f'{r["name"]} ({e})', AMPEL[r["feld"]],
                                 f'{feld_name(r["feld"])} {_pfeil(r)} · {"passt zum Quad" if e in ab["vorne"] else "passt nicht zum Quad"}')
    andere = [r["name"] for e, r in rot.items() if r["feld"] == "Führend" and e not in ab["erwartet"]]
    if andere:
        zeilen += ampelzeile("Führend, obwohl nicht typisch für den Quad", "gelb", ", ".join(andere))
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;'
            f'padding:20px;display:flex;flex-direction:column;gap:6px">'
            f'<h2 style="margin:0 0 6px;font-size:20px;font-weight:600">Abgleich mit dem Quad</h2>{zeilen}</div>')
