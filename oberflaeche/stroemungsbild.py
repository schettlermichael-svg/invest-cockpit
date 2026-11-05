"""Bild zur Karte „Strömung in der Zone“ (4.11.2026): die Wertbereiche der letzten 15 Tage als Säulen vor dem
Wertbereich der Zone. Säule = Tageswert (70 % der Handelszeit), Farbe nach dem Vortag (grün höher, rot tiefer, grau
gleich), oranger Strich = Tages-POC, weißer Punkt = Schluss; darüber das Zeichen ▲ △ ▬ ▽ ▼, darunter das Datum.
Hinten: blaue Fläche = Wertbereich der Zone, gestrichelt = Rahmen (Hoch/Tief), orange gestrichelt = POC der Zone;
nach einem Ausbruch rot gestrichelt die Stopp-Kante der verlassenen Zone."""
from gestaltung import BLAU, GRAU, GRUEN, ROT, TEXT, TEXT_2, TEXT_3, zahl

POC = "#FFA657"
FARBE = {"hoch": GRUEN, "ueber": GRUEN, "gleich": GRAU, "unter": ROT, "tief": ROT, None: GRAU}
ZEICHEN = {"hoch": "▲", "ueber": "△", "gleich": "▬", "unter": "▽", "tief": "▼", None: ""}
TAGE = 15


def bild(a, schluss=None):
    tage, st, z = a["tage"][-TAGE:], a["stand"][-1], a["zustand"]
    ak = a.get("aktiv")
    B, H, L, R, O, U = 1100, 250, 70, 190, 34, 34
    werte = [st["hoch"], st["tief"]] + [t["vah"] for t in tage] + [t["val"] for t in tage]
    if ak:
        werte.append(ak["zone"]["vah"] if ak["dir"] == "↑" else ak["zone"]["val"])
    lo, hi = min(werte), max(werte)
    pad = (hi - lo) * 0.06 or hi * 0.01
    lo, hi = lo - pad, hi + pad

    def Y(p):
        return O + (H - O - U) * (1 - (p - lo) / (hi - lo))
    breite = (B - L - R) / len(tage)

    def X(i):
        return L + breite * (i + 0.5)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}" width="100%" role="img" '
         f'aria-label="Tageswerte der letzten {len(tage)} Tage vor dem Wertbereich der Zone" '
         f'style="display:block;font-family:IBM Plex Sans,sans-serif;margin:6px 0 4px">']
    A = s.append
    # Zone: Wertbereich, Rahmen, POC
    A(f'<rect x="{L}" y="{Y(st["vah"]):.1f}" width="{B - L - R}" height="{Y(st["val"]) - Y(st["vah"]):.1f}" '
      f'fill="{BLAU}" fill-opacity="0.13"/>')
    for p, name, farbe, strich in ((st["hoch"], "Rahmen oben", TEXT_3, "5 4"), (st["tief"], "Rahmen unten", TEXT_3, "5 4"),
                                   (st["vah"], "VAH Zone", BLAU, ""), (st["val"], "VAL Zone", BLAU, ""),
                                   (st["poc"], "POC Zone", POC, "3 4")):
        A(f'<line x1="{L}" x2="{B - R}" y1="{Y(p):.1f}" y2="{Y(p):.1f}" stroke="{farbe}" stroke-opacity="0.8" '
          f'stroke-width="1.2"' + (f' stroke-dasharray="{strich}"' if strich else "") + '/>')
    beschr = sorted([(st["hoch"], "Rahmen"), (st["vah"], "VAH"), (st["poc"], "POC"), (st["val"], "VAL"),
                     (st["tief"], "Rahmen")], key=lambda x: -x[0])
    y_frei = -99
    for p, name in beschr:                       # Beschriftungen rechts, ohne Überlappung
        y = max(Y(p) + 4, y_frei + 13)
        y_frei = y
        farbe = POC if name == "POC" else BLAU if name in ("VAH", "VAL") else TEXT_3
        A(f'<text x="{B - R + 8}" y="{y:.1f}" fill="{farbe}" font-size="12">{name} {zahl(p)}</text>')
    if ak:
        kante = ak["zone"]["vah"] if ak["dir"] == "↑" else ak["zone"]["val"]
        A(f'<line x1="{L}" x2="{B - R}" y1="{Y(kante):.1f}" y2="{Y(kante):.1f}" stroke="{ROT}" stroke-width="1.4" '
          f'stroke-dasharray="7 4"/>'
          f'<text x="{L + 4}" y="{Y(kante) - 5:.1f}" fill="{ROT}" font-size="12">Stopp-Kante der verlassenen Zone '
          f'{zahl(kante)}</text>')
    # Tageswerte
    for i, t in enumerate(tage):
        x, w = X(i), breite * 0.42
        f = FARBE[t.get("bez")]
        A(f'<g><title>{t["tag"]:%d.%m.%Y}: Wert {zahl(t["val"])}–{zahl(t["vah"])} $, POC {zahl(t["poc"])} $, Schluss '
          f'{zahl(t["schluss"])} $</title>'
          f'<rect x="{x - w / 2:.1f}" y="{Y(t["vah"]):.1f}" width="{w:.1f}" height="{max(2, Y(t["val"]) - Y(t["vah"])):.1f}" '
          f'fill="{f}" fill-opacity="0.55" stroke="{f}" rx="2"/>'
          f'<line x1="{x - w / 2 - 3:.1f}" x2="{x + w / 2 + 3:.1f}" y1="{Y(t["poc"]):.1f}" y2="{Y(t["poc"]):.1f}" '
          f'stroke="{POC}" stroke-width="2.4"/>'
          f'<circle cx="{x:.1f}" cy="{Y(t["schluss"]):.1f}" r="3" fill="{TEXT}"/></g>')
        A(f'<text x="{x:.1f}" y="{O - 12}" fill="{f}" font-size="15" text-anchor="middle">{ZEICHEN[t.get("bez")]}</text>')
        A(f'<text x="{x:.1f}" y="{H - 10}" fill="{TEXT_3}" font-size="11" text-anchor="middle">{t["tag"]:%d.%m.}</text>')
    A(f'<text x="{B - R + 8}" y="{O - 12}" fill="{TEXT}" font-size="13" font-weight="600">{z["wort"]}</text>')
    A(f'<text x="{4}" y="{O - 12}" fill="{TEXT_2}" font-size="12">Tageswert</text>')
    s.append("</svg>")
    legende = (f'<div style="display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:{TEXT_2};margin-bottom:6px">'
               f'<span><span style="display:inline-block;width:10px;height:10px;background:{GRUEN};opacity:.7;border-radius:2px"></span> '
               f'Säule = Wert des Tages (70 % der Zeit), höher als am Vortag</span>'
               f'<span><span style="display:inline-block;width:10px;height:10px;background:{ROT};opacity:.7;border-radius:2px"></span> tiefer</span>'
               f'<span><span style="display:inline-block;width:10px;height:10px;background:{GRAU};border-radius:2px"></span> gleich</span>'
               f'<span><span style="display:inline-block;width:14px;height:3px;background:{POC}"></span> POC (fairer Preis)</span>'
               f'<span>● Schluss</span>'
               f'<span><span style="display:inline-block;width:14px;height:10px;background:{BLAU};opacity:.25"></span> Wert der Zone, '
               f'gestrichelt Rahmen</span></div>')
    return "".join(s) + legende
