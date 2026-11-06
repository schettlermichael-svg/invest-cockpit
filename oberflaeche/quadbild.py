"""Dalio-Quad als Bild (06.11.2026): Wachstum × Inflation als Vierfeld, der Punkt von heute mit seiner Spur der letzten
13 Wochen. Lage des Punkts = Mehrheit der schnellen Instrumente je Achse: rechts, wenn mehr Wachstums-Instrumente steigen
als fallen, oben, wenn mehr Inflations-Instrumente steigen (−1 … +1, Mitte = unentschieden). Gestrichelter Rahmen = das
Feld, das die amtlichen Zahlen (BIP, Verbraucherpreise) noch zeigen.
"""
import pandas as pd

from gestaltung import AMPEL, KARTE, RAND, TEXT, TEXT_2, TEXT_3, t

QUAD_AMPEL = {1: "grün", 2: "grün", 3: "gelb", 4: "rot"}
B, H = 720, 450
MX, MY, RX, RY = B / 2, 214, 300, 165         # Mitte und halbe Breite/Höhe des Vierfelds
FELD = {2: (1, -1), 1: (1, 1), 3: (-1, -1), 4: (-1, 1)}   # (rechts?, unten?) je Quad


def _lage(q):
    w, i = q["wachstum"], q["inflation"]
    return ((w["steigt"] - w["fällt"]) / max(1, w["von"]), (i["steigt"] - i["fällt"]) / max(1, i["von"]))


def verlauf(lage_modul, wochen=13):
    """Quad für heute und die Freitage der letzten `wochen` Wochen (älteste zuerst)."""
    heute = pd.Timestamp.today().normalize()
    tage = [heute - pd.Timedelta(weeks=k) for k in range(wochen, 0, -1)]
    aus = []
    for d in tage:
        try:
            aus.append((d, lage_modul.quadrant(bis=d)))
        except Exception:  # noqa: BLE001 – eine fehlende Woche lässt nur eine Lücke in der Spur
            pass
    return aus


def bild(q, spur, instrumente=""):
    """SVG-Karte: Vierfeld, Spur (graue Punkte, älteste blass), heute großer Punkt, amtliches Feld gestrichelt; rechts
    daneben die Instrumente je Achse (Ampelzeilen), aus denen der Punkt entsteht."""
    from lage import FUEHRER, QUADS

    def xy(x, y):
        return MX + x * RX * 0.62, MY - y * RY * 0.55

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}" width="100%" role="img" '
         f'aria-label="Dalio-Quad" style="display:block;max-width:820px;font-family:IBM Plex Sans,sans-serif">'
         '<style>text{paint-order:stroke;stroke:#161C24;stroke-width:4px;stroke-linejoin:round}</style>']
    A = s.append
    for nr, (rechts, unten) in FELD.items():
        x0 = MX if rechts > 0 else MX - RX
        y0 = MY if unten > 0 else MY - RY
        aktiv = nr == q["quad"]
        farbe = AMPEL[QUAD_AMPEL[nr]]
        A(f'<rect x="{x0 + 2}" y="{y0 + 2}" width="{RX - 4}" height="{RY - 4}" rx="10" fill="{farbe}" '
          f'fill-opacity="{0.20 if aktiv else 0.06}" stroke="{farbe}" stroke-opacity="{0.9 if aktiv else 0.25}" '
          f'stroke-width="{2 if aktiv else 1}"/>')
        if nr == q["amtlich"] and nr != q["quad"]:
            A(f'<rect x="{x0 + 8}" y="{y0 + 8}" width="{RX - 16}" height="{RY - 16}" rx="8" fill="none" '
              f'stroke="{TEXT_2}" stroke-width="1.5" stroke-dasharray="6 5"/>')
        tx = x0 + 16 if rechts < 0 else x0 + RX - 16
        anker = "start" if rechts < 0 else "end"
        ty = y0 + 28 if unten < 0 else y0 + RY - 40
        A(f'<text x="{tx}" y="{ty}" fill="{TEXT if aktiv else TEXT_2}" font-size="17" font-weight="600" '
          f'text-anchor="{anker}">Quad {nr} · {QUADS[nr]}</text>')
        A(f'<text x="{tx}" y="{ty + 20}" fill="{TEXT_3}" font-size="12" text-anchor="{anker}">{t(FUEHRER[nr])}</text>')
        if nr == q["amtlich"] and nr != q["quad"]:
            A(f'<text x="{tx}" y="{ty + 38 if unten < 0 else ty - 24}" fill="{TEXT_2}" font-size="12" '
              f'text-anchor="{anker}">amtliche Zahlen noch hier</text>')
    # Achsen
    A(f'<line x1="{MX - RX}" x2="{MX + RX}" y1="{MY}" y2="{MY}" stroke="{TEXT_3}" stroke-width="1.2"/>'
      f'<line x1="{MX}" x2="{MX}" y1="{MY - RY}" y2="{MY + RY}" stroke="{TEXT_3}" stroke-width="1.2"/>'
      f'<text x="{MX + RX}" y="{MY + RY + 22}" fill="{TEXT_2}" font-size="13" text-anchor="end">Wachstum steigt →</text>'
      f'<text x="{MX - RX}" y="{MY + RY + 22}" fill="{TEXT_2}" font-size="13">← Wachstum fällt</text>'
      f'<text x="{MX + 8}" y="{MY - RY - 10}" fill="{TEXT_2}" font-size="13">↑ Inflation steigt</text>'
      f'<text x="{MX + 8}" y="{MY + RY + 22}" fill="{TEXT_2}" font-size="13">↓ Inflation fällt</text>')
    # Spur: gleiche Lagen leicht versetzt, damit jede Woche sichtbar bleibt
    punkte = [(d, *_lage(x)) for d, x in spur] + [(None, *_lage(q))]
    gesehen, pos = {}, []
    for d, x, y in punkte:
        k = gesehen.get((x, y), 0)
        gesehen[(x, y)] = k + 1
        px, py = xy(x, y)
        pos.append((d, px + (k % 4) * 9 - 13 * (k > 0), py + (k // 4) * 9))
    if len(pos) >= 2:
        A(f'<polyline points="{" ".join(f"{px:.1f},{py:.1f}" for _, px, py in pos)}" fill="none" stroke="{TEXT_2}" '
          f'stroke-width="1.4" stroke-opacity="0.6" stroke-dasharray="3 3"/>')
    n = len(pos)
    for k, (d, px, py) in enumerate(pos[:-1]):
        A(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{TEXT_2}" fill-opacity="{0.25 + 0.6 * k / max(1, n - 2):.2f}">'
          f'<title>{d:%d.%m.%Y}: Quad {spur[k][1]["quad"]} · {spur[k][1]["name"]}</title></circle>')
    _, px, py = pos[-1]
    farbe = AMPEL[QUAD_AMPEL[q["quad"]]]
    A(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="11" fill="{farbe}" stroke="{TEXT}" stroke-width="2.5">'
      f'<title>heute: Quad {q["quad"]} · {q["name"]}</title></circle>'
      f'<text x="{px + 16:.1f}" y="{py + 5:.1f}" fill="{TEXT}" font-size="14" font-weight="700">heute</text>')
    if spur:
        alt = spur[0][1]
        A(f'<text x="{MX - RX}" y="{H - 8}" fill="{TEXT_3}" font-size="12">Spur: wöchentlich seit {spur[0][0]:%d.%m.%Y} '
          f'(Quad {alt["quad"]} · {alt["name"]}), je dunkler, desto jünger · Maus auf einen Punkt zeigt die Woche</text>')
    A("</svg>")
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:20px;display:flex;'
            f'flex-direction:column;gap:8px"><div style="display:flex;justify-content:space-between;align-items:baseline;'
            f'flex-wrap:wrap;gap:8px"><h2 style="margin:0;font-size:20px;font-weight:600">Wirtschaftswetter · Dalio-Quad</h2>'
            f'<span style="font-size:13px;color:{TEXT_3}">Lage = Mehrheit der schnellen Instrumente je Achse '
            f'(Wachstum {q["wachstum"]["steigt"]} ↑ / {q["wachstum"]["fällt"]} ↓ von {q["wachstum"]["von"]}, '
            f'Inflation {q["inflation"]["steigt"]} ↑ / {q["inflation"]["fällt"]} ↓ von {q["inflation"]["von"]})</span></div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start">'
            f'<div style="flex:1 1 520px;min-width:0">{"".join(s)}</div>'
            + (f'<div style="flex:1 1 340px;min-width:0;display:flex;flex-direction:column;gap:4px">'
               f'<div style="font-size:14px;font-weight:600">Die Instrumente</div>{instrumente}</div>' if instrumente else "")
            + '</div></div>')
