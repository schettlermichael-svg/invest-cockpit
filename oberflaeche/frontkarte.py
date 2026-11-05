"""Frontkarte „wohin das Geld fließt“: die elf Sektoren als Vier-Felder-Tafel (Rotationsbild ohne
Gewirr) und daneben der Abgleich mit dem Quad.

Jeder Sektor steht in seinem Feld, sortiert nach relativer Stärke; darunter steht, seit wie vielen
Wochen er dort ist und aus welchem Feld er kam (Wechsel dieser Woche mit NEU). Der Pfeil zeigt die Bewegung der
letzten 5 Wochen in derselben Geometrie wie die Felder: nach rechts = Stärke nimmt zu, nach oben =
Schwung nimmt zu. Ein frei gezeichnetes Rotationsbild mit Schweifen war bei elf Sektoren unlesbar.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))

import rudel                                                        # noqa: E402
import sektoren                                                     # noqa: E402
import namen_de                                                     # noqa: E402
from gestaltung import KARTE, RAND, TEXT_2, TEXT_3, ampelzeile, t, zahl  # noqa: E402

FARBE = {"Führend": "#56D364", "Ermüdend": "#E3B341", "Abgehängt": "#FF7B72", "Erstarkend": "#7DB4FF"}
GRUND = {"Führend": "#3FB950", "Ermüdend": "#D29922", "Abgehängt": "#F85149", "Erstarkend": "#4C9AFF"}
BEDEUTUNG = {"Erstarkend": "noch schwächer als der Markt, holt aber auf",
             "Führend": "stärker als der Markt, Stärke nimmt zu",
             "Abgehängt": "schwächer als der Markt, fällt weiter zurück",
             "Ermüdend": "noch stärker als der Markt, Stärke lässt nach"}
AMPEL = {"Führend": "grün", "Erstarkend": "blau", "Ermüdend": "gelb", "Abgehängt": "rot"}
PFEILE = {"↖": "Abwärtsdruck lässt nach", "↑": "Wende kündigt sich an", "↗": "Geld fließt zu",
          "←": "verliert weiter", "·": "kaum Bewegung", "→": "gewinnt weiter",
          "↙": "Geld fließt ab", "↓": "Schwung lässt nach", "↘": "Kraft lässt nach"}
PFEILFARBE = {"↗": "#56D364", "↙": "#FF7B72"}
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


def _herkunft(r):
    """Woher der Sektor kommt: seit wie vielen Wochen im Feld, welches Feld davor."""
    w, davor = r["seit_wochen"], r["davor"]
    if davor is None:
        text = f"seit über {w} Wochen hier"
    else:
        text = ("diese Woche gewechselt" if w == 1 else f"seit {w} Wochen") + f", kommt aus {davor}"
    neu = w == 1 and davor is not None
    marke = (f'<span style="font-size:10px;font-weight:600;letter-spacing:0.06em;border:1px solid {TEXT_3};'
             f'border-radius:4px;padding:0 4px;margin-right:6px;color:{TEXT_2}">NEU</span>' if neu else "")
    return f'<span style="flex-basis:100%;font-size:12px;color:{TEXT_3}">{marke}{t(text)}</span>'


def _eintrag(etf, r, quad_etfs, quad_nr):
    quad = etf in quad_etfs
    marken = ""
    if quad:
        marken += (f'<span style="font-size:11px;border-radius:5px;padding:2px 6px;border:1px solid #5A4A1A;'
                   f'color:#E3B341" title="Nach dem Quad-Modell führt dieser Sektor in Quad {quad_nr} typischerweise – '
                   f'ob er es tut, zeigt das Feld">typisch für Quad {quad_nr}</span>')
    return (f'<div style="display:grid;grid-template-columns:14px 1fr auto auto;gap:10px;align-items:center;'
            f'background:#1C2430;border-radius:8px;padding:8px 10px">'
            f'<span style="width:12px;height:12px;border-radius:50%;background:{FARBE[r["feld"]]}"></span>'
            f'<span style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:15px">'
            f'<b style="font-weight:600">{t(r["name"])}</b><span style="color:{TEXT_3};font-size:13px">{etf}</span>'
            f'{marken}{_herkunft(r)}</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:13px;color:{TEXT_2}">{zahl(r["staerke"], 1)}</span>'
            f'<span class="hinweis-zone" style="position:relative;font-size:20px;color:{FARBE[r["feld"]]};'
            f'width:20px;text-align:center">{_pfeil(r)}<span class="hinweis-tip" style="width:220px;text-align:left">'
            f'{t(PFEILE[_pfeil(r)])} (letzte 5 Wochen)</span></span></div>')


def tafel(rot, quad_etfs, quad_nr):
    def feld(name):
        drin = sorted(((e, r) for e, r in rot.items() if r["feld"] == name), key=lambda kv: -kv[1]["staerke"])
        inhalt = "".join(_eintrag(e, r, quad_etfs, quad_nr) for e, r in drin) or \
            f'<div style="font-size:14px;color:{TEXT_3}">kein Sektor</div>'
        return (f'<div style="background:{GRUND[name]}12;border:1px solid {GRUND[name]}40;border-radius:10px;'
                f'padding:14px;display:flex;flex-direction:column;gap:8px;min-height:120px">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap">'
                f'<span style="font-size:16px;font-weight:600;color:{FARBE[name]}">{name}</span>'
                f'<span style="font-size:12px;color:{TEXT_3}">{BEDEUTUNG[name]}</span></div>{inhalt}</div>')
    return (f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">'
            f'{feld("Erstarkend")}{feld("Führend")}{feld("Abgehängt")}{feld("Ermüdend")}</div>')


def themen_tafel():
    """Themen-Gruppen (Schritt 4) in denselben vier Feldern: je Gruppe ein Kürzel aus ihren größten Titeln,
    Maus darauf zeigt Branchen, Gleichlauf und Mitglieder."""
    try:
        themen = [g for g in rudel.themen() if g.get("feld")]
    except Exception:
        return ""
    if not themen:
        return ""

    def chip(g):
        kopf = " · ".join(g["mitglieder"][:3]) + (f' +{len(g["mitglieder"]) - 3}' if len(g["mitglieder"]) > 3 else "")
        pf = _pfeil(g)
        tip = (f'Themen-Gruppe {g["nr"]} (Branchen der Mitglieder: {t(namen_de.branche(g["name"]))}) · {len(g["mitglieder"])} Titel, Gleichlauf {zahl(g["gleichlauf"], 2)} · '
               f'Stärke {zahl(g["staerke"], 0)}, Schwung {zahl(g["schwung"], 0)} · {PFEILE[pf]}<br>'
               + ", ".join(g["mitglieder"][:30]) + (" …" if len(g["mitglieder"]) > 30 else ""))
        return (f'<span class="hinweis-zone" style="position:relative;display:inline-flex;gap:6px;align-items:center;'
                f'font-size:12px;font-family:IBM Plex Mono,monospace;border:1px solid {RAND};border-radius:6px;'
                f'padding:3px 7px;background:#1C2430">{t(kopf)}<span style="color:{PFEILFARBE.get(pf, TEXT_2)}">{pf}</span>'
                f'<span class="hinweis-tip" style="left:0;right:auto;font-family:IBM Plex Sans,system-ui;font-size:13px">'
                f'{tip}</span></span>')

    def feld(name):
        drin = sorted((g for g in themen if g["feld"] == name), key=lambda g: -len(g["mitglieder"]))
        inhalt = "".join(chip(g) for g in drin) or f'<span style="font-size:13px;color:{TEXT_3}">keine</span>'
        return (f'<div style="border:1px solid {GRUND[name]}40;border-radius:10px;padding:10px;display:flex;'
                f'flex-direction:column;gap:8px"><span style="font-size:13px;font-weight:600;color:{FARBE[name]}">'
                f'{name} ({len(drin)})</span><div style="display:flex;flex-wrap:wrap;gap:6px">{inhalt}</div></div>')
    return (f'<div style="display:flex;flex-direction:column;gap:8px;padding-top:6px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
            f'<span style="font-size:16px;font-weight:600">Themen-Gruppen</span>'
            f'<span style="font-size:13px;color:{TEXT_3}">{len(themen)} Gruppen aus dem Revier, die eng zusammenlaufen – '
            f'auch über Branchen hinweg; Maus auf eine Gruppe zeigt ihre Titel</span></div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">'
            f'{feld("Erstarkend")}{feld("Führend")}{feld("Abgehängt")}{feld("Ermüdend")}</div></div>')


def kompass():
    """Lesehilfe für die Pfeile: 3 × 3 Felder in derselben Geometrie wie die Tafel."""
    zellen = "".join(
        f'<div style="background:#1C2430;border-radius:8px;padding:8px 6px;display:flex;flex-direction:column;'
        f'align-items:center;gap:2px;text-align:center"><span style="font-size:22px;line-height:1;'
        f'color:{PFEILFARBE.get(p, TEXT_2)}">{p}</span><span style="font-size:12px;color:{TEXT_2};line-height:1.3">'
        f'{t(PFEILE[p])}</span></div>' for p in ("↖", "↑", "↗", "←", "·", "→", "↙", "↓", "↘"))
    achse = f'font-size:11px;color:{TEXT_3};text-align:center'
    return (f'<div style="flex:0 1 380px;display:flex;flex-direction:column;gap:6px">'
            f'<div style="font-size:14px;font-weight:600">Pfeile lesen</div>'
            f'<div style="{achse}">mehr Schwung ↑</div>'
            f'<div style="display:grid;grid-template-columns:auto 1fr auto;gap:6px;align-items:center">'
            f'<div style="{achse};writing-mode:vertical-rl;transform:rotate(180deg)">← schwächer</div>'
            f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px">{zellen}</div>'
            f'<div style="{achse};writing-mode:vertical-rl">stärker →</div></div>'
            f'<div style="{achse}">weniger Schwung ↓</div></div>')


def frontkarte(quad):
    rot = sektoren.rotation()
    if not rot:
        return ""
    stand = next(iter(rot.values()))["stand"]
    ab = sektoren.abgleich(rot, quad["quad"])
    links = (f'<div style="flex:999 1 640px;min-width:0;background:{KARTE};border:1px solid {RAND};border-radius:12px;'
             f'padding:20px;display:flex;flex-direction:column;gap:12px">'
             f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
             f'<h2 style="margin:0;font-size:20px;font-weight:600">Frontkarte · wohin das Geld fließt</h2>'
             f'<span style="font-size:13px;color:{TEXT_3}">Sektoren gegen den S&amp;P 500, Woche bis {stand:%d.%m.%Y}</span></div>'
             f'{tafel(rot, ab["erwartet"], quad["quad"])}'
             f'<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start;padding-top:6px">'
             f'<div style="flex:1 1 260px;font-size:13px;color:{TEXT_2};line-height:1.7">'
             f'<b style="color:#E6EAF0">Feld</b> = wo der Sektor steht.<br>'
             f'<b style="color:#E6EAF0">Pfeil</b> = wohin er sich in den letzten 5 Wochen bewegt hat '
             f'(Maus auf den Pfeil zeigt die Bedeutung).<br>'
             f'<b style="color:#E6EAF0">Zahl</b> = relative Stärke; 100 = so stark wie der Markt im Schnitt des '
             f'letzten halben Jahres.<br>'
             f'<b style="color:#E6EAF0">Typischer Lauf</b> im Uhrzeigersinn: Erstarkend → Führend → Ermüdend → '
             f'Abgehängt → Erstarkend.</div>{kompass()}</div>{themen_tafel()}</div>')

    zeilen = ampelzeile(f'{len(ab["vorne"])} von {len(ab["erwartet"])} typischen Quad-Sektoren vorne', ab["ampel"],
                        f'Nach dem Quad-Modell führen in Quad {quad["quad"]} ({quad["name"]}) typischerweise diese Sektoren. '
                        f'„Vorne“ heißt Führend oder Erstarkend. Stehen sie hinten, widersprechen Markt und Wirtschaftswetter '
                        f'sich – der Geldfluss traut dem Quad noch nicht.')
    for e in ab["erwartet"]:
        if e in rot:
            r = rot[e]
            zeilen += ampelzeile(f'{r["name"]} ({e})', AMPEL[r["feld"]],
                                 f'{r["feld"]} {_pfeil(r)} · {"passt zum Quad" if e in ab["vorne"] else "passt nicht zum Quad"}')
    andere = [r["name"] for e, r in rot.items() if r["feld"] == "Führend" and e not in ab["erwartet"]]
    if andere:
        zeilen += ampelzeile("Führend, obwohl nicht typisch für den Quad", "gelb", ", ".join(andere))
    rechts = (f'<div style="flex:1 1 360px;min-width:0;display:flex;flex-direction:column;gap:16px">'
              f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;'
              f'padding:20px;display:flex;flex-direction:column;gap:6px">'
              f'<h2 style="margin:0 0 6px;font-size:20px;font-weight:600">Abgleich mit dem Quad</h2>{zeilen}</div></div>')
    return f'<section style="display:flex;flex-wrap:wrap;gap:16px">{links}{rechts}</section>'
