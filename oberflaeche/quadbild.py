"""Dalio-Quad als Bild (06.11.2026), Bild und Instrumente in einer Sprache:

Jedes Instrument ist eine Stimme. Wachstumsstimmen schieben den Punkt nach rechts (→, Wachstum steigt) oder links (←),
Inflationsstimmen nach oben (↑) oder unten (↓); · = unentschieden (Änderung unter der Schwelle). Die Mehrheit je Achse
bestimmt das Feld. An den Achsen steht die Stimmleiste, neben dem Bild die Stimmen einzeln mit beiden Werten (vorher →
heute), im Feld der Abstand zum Kippen (wie viele Stimmen noch fehlen, bis eine Achse dreht – dieselbe Regel wie in den
Übergängen), unter dem Bild die Folgerung: Rückenwind für welche Sektoren, und stehen sie an der Front vorne?
Gestrichelter Rahmen = das Feld, das die amtlichen Zahlen (BIP, Verbraucherpreise) noch zeigen.
"""
import pandas as pd

from gestaltung import AMPEL, KARTE, RAND, TEXT, TEXT_2, TEXT_3, t, zahl

QUAD_AMPEL = {1: "grün", 2: "grün", 3: "gelb", 4: "rot"}
B, H = 720, 450
MX, MY, RX, RY = B / 2, 214, 300, 165         # Mitte und halbe Breite/Höhe des Vierfelds
FELD = {2: (1, -1), 1: (1, 1), 3: (-1, -1), 4: (-1, 1)}   # (rechts?, unten?) je Quad
WERT = ("Weekly Economic Index", "GDPNow", "Breakeven-Inflation 5 Jahre")   # Stand in %, sonst Veränderung zum Vorjahr
PFEIL = {"wachstum": {"steigt": "→", "fällt": "←", "unklar": "·"},
         "inflation": {"steigt": "↑", "fällt": "↓", "unklar": "·"}}
STIMMFARBE = {"steigt": "#E6EAF0", "fällt": "#E6EAF0", "unklar": "#5A6475"}


def _lage(q):
    w, i = q["wachstum"], q["inflation"]
    return ((w["steigt"] - w["fällt"]) / max(1, w["von"]), (i["steigt"] - i["fällt"]) / max(1, i["von"]))


def verlauf(lage_modul, wochen=13):
    """Quad für die Freitage der letzten `wochen` Wochen (älteste zuerst)."""
    heute = pd.Timestamp.today().normalize()
    aus = []
    for k in range(wochen, 0, -1):
        d = heute - pd.Timedelta(weeks=k)
        try:
            aus.append((d, lage_modul.quadrant(bis=d)))
        except Exception:  # noqa: BLE001 – eine fehlende Woche lässt nur eine Lücke in der Spur
            pass
    return aus


def _leiste(q, achse):
    """Stimmleiste einer Achse, z. B. „→→→←·“ (erst die Mehrheit, dann die Gegenstimmen, dann unentschieden)."""
    r = [x[0] for x in q[achse]["instrumente"].values()]
    return "".join(PFEIL[achse][k] * r.count(k) for k in ("steigt", "fällt", "unklar"))


def _kippen(q, achse):
    """(Ziel-Quad, Stimmen, die noch kippen müssen) – Mehrheit der Gegenrichtung wie in den Übergängen."""
    from lage import _quad
    a = q[achse]
    w, i = q["wachstum"]["richtung"], q["inflation"]["richtung"]
    if "unklar" in (w, i) or a["richtung"] == "unklar":
        return None
    gegen = "fällt" if a["richtung"] == "steigt" else "steigt"
    ziel = _quad(gegen if achse == "wachstum" else w, gegen if achse == "inflation" else i)
    schon = sum(1 for r, *_ in a["instrumente"].values() if r == gegen)
    return ziel, max(1, a["von"] // 2 + 1 - schon)


def _stimmen(q):
    """Liste neben dem Bild: je Achse die Stimmen mit Pfeil und beiden Werten."""
    def block(achse, name, wohin):
        a = q[achse]
        mehr = a["richtung"]
        kopf = (f'<div style="display:flex;justify-content:space-between;gap:8px;margin-top:6px">'
                f'<b style="font-size:15px">{name} {PFEIL[achse].get(mehr, "·")} {wohin.get(mehr, "unentschieden")}</b>'
                f'<span style="font-size:13px;color:{TEXT_3}">{a["steigt"]} {PFEIL[achse]["steigt"]} · {a["fällt"]} '
                f'{PFEIL[achse]["fällt"]} · {a["von"] - a["steigt"] - a["fällt"]} · von {a["von"]}</span></div>')
        zeilen = ""
        for n, (r, _d, alt, neu) in a["instrumente"].items():
            art = "Stand" if n in WERT else "zum Vorjahr"
            werte = (f'{zahl(alt, 1)} % → {zahl(neu, 1)} % ({art})' if alt == alt else "keine Daten")
            extra = " · weniger Anträge = mehr Wachstum" if "Erstanträge" in n else ""
            zeilen += (f'<div style="display:grid;grid-template-columns:26px 1fr;gap:6px;align-items:baseline;'
                       f'padding:5px 0;border-top:1px solid {RAND}">'
                       f'<span style="font-size:20px;font-weight:700;color:{STIMMFARBE[r]};text-align:center">'
                       f'{PFEIL[achse][r]}</span><span style="font-size:14px">{t(n)}<br><span style="font-size:13px;'
                       f'color:{TEXT_2}">{werte}{extra}</span></span></div>')
        return kopf + zeilen

    return (block("wachstum", "Wachstum", {"steigt": "rechts", "fällt": "links"})
            + block("inflation", "Inflation", {"steigt": "oben", "fällt": "unten"})
            + f'<div style="font-size:13px;color:{TEXT_3};margin-top:8px;border-top:1px solid {RAND};padding-top:6px">'
              f'Amtlich zur Bestätigung: BIP {zahl(q["bip_rate"], 1)} % zum Vorjahr, Verbraucherpreise '
              f'{zahl(q["cpi_rate"], 1)} % → Quad {q["amtlich"]} (gestrichelt im Bild)</div>')


def _folgerung(q):
    """Ein Satz: Rückenwind für welche Sektoren – und stehen sie an der Front (Frontkarte) vorne?"""
    from lage import FUEHRER
    satz = f'<b>Quad {q["quad"]} · {q["name"]}:</b> Rückenwind für {t(FUEHRER[q["quad"]])}.'
    try:
        import sektoren
        ab = sektoren.abgleich(sektoren.rotation(), q["quad"])
        n, v = len(ab["erwartet"]), len(ab["vorne"])
        urteil = ("Geldfluss und Wetter passen zusammen" if ab["ampel"] == "grün" else
                  "der Geldfluss folgt dem Wetter erst teilweise" if ab["ampel"] == "gelb" else
                  "der Geldfluss traut dem Wetter nicht")
        satz += (f' An der Front stehen davon {v} von {n} vorne (Führend oder Erstarkend) – {urteil}.')
        farbe = AMPEL[ab["ampel"]]
    except Exception:  # noqa: BLE001 – ohne Sektordaten nur der erste Satz
        farbe = AMPEL[QUAD_AMPEL[q["quad"]]]
    if q["wechsel_moeglich"]:
        satz += f' Die amtlichen Zahlen zeigen noch Quad {q["amtlich"]} – Wechsel möglich, noch nicht bestätigt.'
    return (f'<div style="display:flex;gap:10px;align-items:flex-start;font-size:15px;line-height:1.5;'
            f'border-top:1px solid {RAND};padding-top:10px"><span style="width:14px;height:14px;border-radius:50%;'
            f'background:{farbe};flex-shrink:0;margin-top:4px"></span><span>{satz}</span></div>')


def bild(q, spur):
    """Karte: Vierfeld mit Stimmleisten an den Achsen, Spur, heute, Abstand zum Kippen; daneben die Stimmen; darunter
    die Folgerung."""
    from lage import QUADS

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
        if nr == q["amtlich"] and nr != q["quad"]:
            A(f'<text x="{tx}" y="{ty + 20 if unten < 0 else ty - 24}" fill="{TEXT_2}" font-size="12" '
              f'text-anchor="{anker}">amtliche Zahlen noch hier</text>')
    # Achsen mit Stimmleisten
    lw, li = _leiste(q, "wachstum"), _leiste(q, "inflation")
    A(f'<line x1="{MX - RX}" x2="{MX + RX}" y1="{MY}" y2="{MY}" stroke="{TEXT_3}" stroke-width="1.2"/>'
      f'<line x1="{MX}" x2="{MX}" y1="{MY - RY}" y2="{MY + RY}" stroke="{TEXT_3}" stroke-width="1.2"/>'
      f'<text x="{MX + RX}" y="{MY + RY + 24}" fill="{TEXT}" font-size="14" text-anchor="end">Wachstum steigt → · '
      f'Stimmen <tspan font-size="17" font-weight="700" letter-spacing="2">{lw}</tspan></text>'
      f'<text x="{MX - RX}" y="{MY + RY + 24}" fill="{TEXT_2}" font-size="14">← Wachstum fällt</text>'
      f'<text x="{MX + 8}" y="{MY - RY - 10}" fill="{TEXT}" font-size="14">↑ Inflation steigt · Stimmen '
      f'<tspan font-size="17" font-weight="700" letter-spacing="2">{li}</tspan></text>'
      f'<text x="{MX + 8}" y="{MY + RY + 44}" fill="{TEXT_2}" font-size="14">↓ Inflation fällt</text>')
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
    # Abstand zum Kippen: je Achse ein Hinweis im aktiven Feld, zur Grenze hin
    rechts, unten = FELD[q["quad"]]
    x0 = MX if rechts > 0 else MX - RX
    y0 = MY if unten > 0 else MY - RY
    for achse, name, zeile in (("wachstum", "Wachstums", 0), ("inflation", "Inflations", 1)):
        k_ = _kippen(q, achse)
        if not k_:
            continue
        ziel, fehlt = k_
        pf = ("←" if rechts > 0 else "→") if achse == "wachstum" else ("↓" if unten < 0 else "↑")
        text_ = f'{pf} Quad {ziel}, wenn noch {fehlt} {name}stimme{"n" if fehlt != 1 else ""} kippen'
        tx = x0 + RX / 2
        ty = (y0 + RY - 30 if unten < 0 else y0 + 30) + zeile * 18
        A(f'<text x="{tx:.1f}" y="{ty:.1f}" fill="{TEXT_2}" font-size="12" text-anchor="middle"><title>Quad {ziel} · '
          f'{QUADS[ziel]}: die Achse dreht, wenn die Mehrheit ihrer Stimmen die Richtung wechselt</title>{text_}</text>')
    if spur:
        alt = spur[0][1]
        A(f'<text x="{MX - RX}" y="{H - 2}" fill="{TEXT_3}" font-size="12">Spur: wöchentlich seit {spur[0][0]:%d.%m.%Y} '
          f'(Quad {alt["quad"]} · {alt["name"]}), je dunkler, desto jünger · Maus auf einen Punkt zeigt die Woche</text>')
    A("</svg>")
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:20px;display:flex;'
            f'flex-direction:column;gap:10px"><h2 style="margin:0;font-size:20px;font-weight:600">'
            f'Wirtschaftswetter · Dalio-Quad</h2>'
            f'<div style="font-size:14px;color:{TEXT_2}">Jedes Instrument ist eine Stimme: → / ← schiebt den Punkt nach '
            f'rechts oder links (Wachstum), ↑ / ↓ nach oben oder unten (Inflation), · = unentschieden. Die Mehrheit je '
            f'Achse bestimmt das Feld.</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start">'
            f'<div style="flex:1 1 520px;min-width:0">{"".join(s)}</div>'
            f'<div style="flex:1 1 340px;min-width:0;display:flex;flex-direction:column">{_stimmen(q)}</div></div>'
            + _folgerung(q) + '</div>')
