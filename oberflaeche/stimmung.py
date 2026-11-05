"""Stimmungskurve: das Marks-Pendel als Kurve eines Marktzyklus (Gestaltung wie die Designvorlage).

kurve(punkte) zeichnet die sieben Zonen und für jeden Eintrag einen Punkt auf der Kurve:
punkte = [{"zone": "...", "vorher": "..." | None, "name": "Gesamtmarkt", "farbe": "#..."}]
Ein hohler Punkt zeigt, wo das Pendel vor vier Wochen stand; die Linie verbindet beide.
"""
import re

from gestaltung import TEXT, TEXT_2, TEXT_3, t

# x-Mitte jeder Zone auf der Kurve (Frühe Erholung erscheint am Anfang des Zyklus)
ZONEN_X = {"Frühe Erholung": 140, "Gesunder Aufwärtstrend": 310, "Überhitzung": 440, "Topbildung": 550,
           "Abwärtsbeschleunigung": 680, "Kapitulation": 810, "Bodenbildung": 930}
STREIFEN = [(40, 200, "#7DB4FF", 0.06), (240, 140, "#3FB950", 0.08), (380, 120, "#D29922", 0.10),
            (500, 100, "#D29922", 0.06), (600, 160, "#F85149", 0.08), (760, 100, "#F85149", 0.14),
            (860, 140, "#8B97A8", 0.08), (1000, 160, "#7DB4FF", 0.06)]
TITEL = [(140, "Frühe Erholung", "#A9CDFF", "Unglaube · Hoffnung"), (310, "Gesunder Trend", "#56D364", "Optimismus · Überzeugung"),
         (440, "Überhitzung", "#E3B341", "Euphorie"), (550, "Topbildung", "#E3B341", "Sorglosigkeit"),
         (680, "Abwärts", "#FF7B72", "Verleugnung · Panik"), (810, "Kapitulation", "#FF7B72", "Aufgabe"),
         (930, "Bodenbildung", "#A9B4C4", "Wut · Depression"), (1080, "Frühe Erholung", "#A9CDFF", "Unglaube")]
PFAD = ("M40,430 C140,440 180,380 260,330 C340,280 400,120 470,90 C520,70 560,160 600,200 "
        "C660,260 700,380 760,430 C800,465 840,452 880,452 C960,452 1020,420 1080,360 C1110,330 1140,310 1160,300")


def _punkte_der_kurve():
    """Kurve als dichte Punktfolge (Bezier-Abschnitte ausgewertet), um y zu einem x zu finden."""
    zahlen = [float(z) for z in re.findall(r"-?\d+(?:\.\d+)?", PFAD)]
    start, rest = (zahlen[0], zahlen[1]), zahlen[2:]
    aus = []
    for k in range(0, len(rest), 6):
        p1, p2, p3 = (rest[k], rest[k + 1]), (rest[k + 2], rest[k + 3]), (rest[k + 4], rest[k + 5])
        for i in range(41):
            s = i / 40
            x = (1 - s) ** 3 * start[0] + 3 * (1 - s) ** 2 * s * p1[0] + 3 * (1 - s) * s ** 2 * p2[0] + s ** 3 * p3[0]
            y = (1 - s) ** 3 * start[1] + 3 * (1 - s) ** 2 * s * p1[1] + 3 * (1 - s) * s ** 2 * p2[1] + s ** 3 * p3[1]
            aus.append((x, y))
        start = p3
    return aus


KURVE = _punkte_der_kurve()


def _auf_kurve(x):
    return min(KURVE, key=lambda p: abs(p[0] - x))


def kurve(punkte):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 520" width="100%" role="img" '
         f'aria-label="Stimmungskurve" style="display:block;font-family:IBM Plex Sans,sans-serif">']
    for x, b, farbe, deck in STREIFEN:
        s.append(f'<rect x="{x}" y="60" width="{b}" height="420" fill="{farbe}" fill-opacity="{deck}"></rect>')
    for x, name, farbe, gefuehl in TITEL:
        s.append(f'<text x="{x}" y="34" fill="{farbe}" font-size="13" font-weight="600" text-anchor="middle">{t(name)}</text>'
                 f'<text x="{x}" y="52" fill="{TEXT_3}" font-size="12" text-anchor="middle">{t(gefuehl)}</text>')
    s.append(f'<path d="{PFAD}" fill="none" stroke="{TEXT}" stroke-width="3" stroke-linecap="round"></path>')
    s.append(f'<text x="470" y="78" fill="{TEXT_2}" font-size="12" text-anchor="middle">größtes Risiko</text>'
             f'<text x="880" y="482" fill="{TEXT_2}" font-size="12" text-anchor="middle">größte Chance</text>')
    belegt, hinten, vorne = {}, [], []          # hohle Punkte (vor 4 Wochen) unter die heutigen legen
    for p in punkte:
        x, y = _auf_kurve(ZONEN_X[p["zone"]])
        unten = belegt.get(p["zone"], 0)          # zweiter Eintrag in derselben Zone: Schild unter den Punkt
        belegt[p["zone"]] = unten + 1
        farbe = p.get("farbe", "#E3B341")
        if p.get("vorher") and p["vorher"] != p["zone"]:
            vx, vy = _auf_kurve(ZONEN_X[p["vorher"]])
            # steht dort heute ein anderer Eintrag, kommt die Beschriftung unter den hohlen Punkt
            ty = vy + 30 if any(q["zone"] == p["vorher"] for q in punkte) else vy - 18
            hinten.append(f'<line x1="{vx:.0f}" y1="{vy:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="{farbe}" stroke-width="2" '
                     f'stroke-dasharray="5 5"></line>'
                     f'<circle cx="{vx:.0f}" cy="{vy:.0f}" r="9" fill="#0E1217" stroke="{farbe}" stroke-width="2.5"></circle>'
                     f'<text x="{vx:.0f}" y="{ty:.0f}" fill="{TEXT_2}" font-size="12" text-anchor="middle" '
                     f'paint-order="stroke" stroke="#161C24" stroke-width="4">vor 4 Wochen</text>')
        breite = 14 + 8 * len(p["name"])
        oben = y - 48 if not unten else y + 20 + 34 * (unten - 1)
        vorne.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="{farbe}" stroke="#0E1217" stroke-width="3"></circle>'
                 f'<rect x="{x - breite / 2:.0f}" y="{oben:.0f}" width="{breite}" height="28" rx="6" fill="#161C24" '
                 f'stroke="{farbe}"></rect>'
                 f'<text x="{x:.0f}" y="{oben + 19:.0f}" fill="{farbe}" font-size="14" font-weight="600" '
                 f'text-anchor="middle">{t(p["name"])}</text>')
    s += hinten + vorne
    s.append("</svg>")
    return "".join(s)
