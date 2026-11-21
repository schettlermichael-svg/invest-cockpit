"""Der Zonenchart (Micky 21.11.2026): wenig, aber aussagekräftig – Kerzen, die eine Zone als Gerüst (Rahmen mit
P, b oder D), ihr POC, die offenen alten Zonen blass (Magnete), der Trade (Einstieg, Stopp, Ziel) und das Volumen.
Dasselbe Bild für Woche, Tag und Stunde. Kein Durchschnitt, kein AVWAP-Fächer, keine Kürzel im Bild."""
import numpy as np
import pandas as pd

from gestaltung import GRUEN, RAND, ROT, TEXT_2, TEXT_3, zahl

B, H = 1200, 520                       # Layout: Breite und Höhe des Bildes
LINKS, RECHTS = 56, 150                # Layout: Rand für Preisachse und Etiketten
OBEN, KURS_H, VOL_H = 16, 360, 70      # Layout: Kursfeld und Volumenfeld
LUECKE = 24                            # Layout: Abstand Kursfeld → Volumen
ZEIGEN = {"Woche": 104, "Tag": 126, "Stunde": 140}   # Kerzen im Bild (2 Jahre, 6 Monate, 20 Handelstage)
ZONE_FARBE = "#EDA100"                 # Zone wie in Vorwalds Bildern gelb
POC_FARBE = "#1BAF7A"
ALT_FARBE = "#8B97A8"
EINSTIEG_FARBE = "#E6EAF0"
RAND_SPIEL = 0.04                      # Layout: 4 % Luft über und unter den Kursen


def bild(e, la, alt, t=None, laufend=False):
    """SVG einer Ebene. e = tiefe.ebene, la = zonen.lage, alt = zonen.alte_zonen, t = zonen.trade (nur Tag)."""
    if not e or not la:
        return f'<p style="color:{TEXT_2}">ungemessen – zu wenige Kerzen</p>'
    df = e["df"]
    n0 = max(0, len(df) - ZEIGEN[e["name"]])
    pb = e.get("pbd")
    if pb:                                         # die ganze Formation im Bild (Impulsbeginn)
        n0 = min(n0, int(df.index.searchsorted(pb["impuls_tag"])))
    d = df.iloc[n0:]
    N = len(d)
    o, h, l, c, v = (d[k].to_numpy(float) for k in ("Open", "High", "Low", "Close", "Volume"))
    lo, hi = la["zone"]
    import zonen
    offen = zonen.naechste(alt, la["kurs"])
    werte = [h.max(), l.min(), lo, hi] + ([t["stopp"], t["ziel"]] if t else [])
    werte += [x for z in offen for x in (z["val"], z["vah"])]
    pmin, pmax = min(werte), max(werte)
    rand = (pmax - pmin) * RAND_SPIEL or 1
    pmin, pmax = pmin - rand, pmax + rand
    ende = B - RECHTS
    breite = ende - LINKS
    X = lambda i: LINKS + breite * (i + 0.5) / N                                   # noqa: E731
    Y = lambda y: OBEN + KURS_H * (1 - (y - pmin) / (pmax - pmin))                 # noqa: E731
    pos = lambda t_: min(max(int(d.index.searchsorted(pd.Timestamp(t_))), 0), N - 1)   # noqa: E731
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}" width="100%" role="img" '
         f'aria-label="Zonenchart {e["name"]}" style="display:block;font-family:IBM Plex Sans,sans-serif">'
         '<style>text{paint-order:stroke;stroke:#161C24;stroke-width:4px;stroke-linejoin:round}</style>']
    A = s.append
    for k in range(5):                                                              # Layout: 5 Preislinien
        y_ = pmin + (pmax - pmin) * k / 4                                           # Layout
        A(f'<line x1="{LINKS}" x2="{ende}" y1="{Y(y_):.1f}" y2="{Y(y_):.1f}" stroke="{RAND}"/>'
          f'<text x="{LINKS - 6}" y="{Y(y_) + 4:.1f}" fill="{TEXT_3}" font-size="11" text-anchor="end">{y_:.0f}</text>')  # Layout
    etiketten = []                                                                  # (y, Text, Farbe) rechts
    for z in offen:                                                                 # Gedächtnis: offene alte Zonen
        x0 = X(pos(z["start"])) if z["start"] >= d.index[0] else LINKS
        A(f'<rect x="{x0:.1f}" y="{Y(z["vah"]):.1f}" width="{ende - x0:.1f}" height="{max(1, Y(z["val"]) - Y(z["vah"])):.1f}" '
          f'fill="{ALT_FARBE}" fill-opacity="0.13"><title>alte Zone {zahl(z["val"])}–{zahl(z["vah"])} '  # Layout
          f'({z["start"]:%d.%m.%y}–{z["ende"]:%d.%m.%y}) – offen: seitdem nie wieder angelaufen</title></rect>')
        etiketten.append((Y((z["val"] + z["vah"]) / 2), f'🪝 alte Zone {zahl(z["val"], 0)}–{zahl(z["vah"], 0)}', ALT_FARBE))
    zs = pd.Timestamp(pb["zone_start"]) if pb else pd.Timestamp(e["struktur"]["balance_start"])
    xz = X(pos(zs)) - breite / N / 2 if zs >= d.index[0] else LINKS                 # Layout
    A(f'<rect x="{xz:.1f}" y="{Y(hi):.1f}" width="{ende - xz:.1f}" height="{max(2, Y(lo) - Y(hi)):.1f}" fill="{ZONE_FARBE}" '
      f'fill-opacity="0.08" stroke="{ZONE_FARBE}" stroke-width="1.6" stroke-dasharray="6 3"/>'  # Layout
      f'<text x="{xz + 6:.1f}" y="{Y(hi) - 6:.1f}" fill="{ZONE_FARBE}" font-size="20" font-weight="700">{la["form"]}</text>')  # Layout
    A(f'<line x1="{xz:.1f}" x2="{ende}" y1="{Y(la["poc"]):.1f}" y2="{Y(la["poc"]):.1f}" stroke="{POC_FARBE}" '
      f'stroke-width="1.4" stroke-dasharray="2 3"/>')                               # Layout
    etiketten += [(Y(hi), f"Zone oben {zahl(hi)}", ZONE_FARBE), (Y(lo), f"Zone unten {zahl(lo)}", ZONE_FARBE),
                  (Y(la["poc"]), f"POC {zahl(la['poc'])}", POC_FARBE)]
    bw = max(1.0, breite / N * 0.6)                                                 # Layout: Kerzenbreite
    for i in range(N):
        f = GRUEN if c[i] >= o[i] else ROT
        A(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{Y(h[i]):.1f}" y2="{Y(l[i]):.1f}" stroke="{f}"/>')
        y1, y2 = sorted([Y(o[i]), Y(c[i])])
        hohl = laufend and i == N - 1
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{max(1, y2 - y1):.1f}" '
          + (f'fill="none" stroke="{f}"/>' if hohl else f'fill="{f}"/>'))
    if t:                                                                           # der Trade: Einstieg, Stopp, Ziel
        x_t = X(max(0, N - 12))                                                     # Layout: die letzten 12 Kerzen
        for wert, farbe, name in ((t["einstieg"], EINSTIEG_FARBE, "Einstieg"), (t["stopp"], ROT, "Stopp"),
                                  (t["ziel"], GRUEN, "Ziel")):
            A(f'<line x1="{x_t:.1f}" x2="{ende}" y1="{Y(wert):.1f}" y2="{Y(wert):.1f}" stroke="{farbe}" stroke-width="2"/>')
            etiketten.append((Y(wert), f"{name} {zahl(wert)}", farbe))
    belegt = []
    for y_, text, farbe in sorted(etiketten):                                       # rechts, ohne Überlappung
        while any(abs(y_ - b_) < 14 for b_ in belegt):                              # Layout: 14 px je Zeile
            y_ += 14                                                                # Layout
        belegt.append(y_)
        A(f'<text x="{ende + 8}" y="{y_ + 4:.1f}" fill="{farbe}" font-size="12">{text}</text>')  # Layout
    y0 = OBEN + KURS_H + LUECKE
    vmax = v.max() or 1
    schnitt = pd.Series(v).rolling(min(50, N)).mean().to_numpy()                    # Layout: 50 Kerzen Schnitt
    for i in range(N):
        hv = VOL_H * v[i] / vmax
        hoch = not np.isnan(schnitt[i]) and v[i] > schnitt[i]
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y0 + VOL_H - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" '
          f'fill="{GRUEN if c[i] >= o[i] else ROT}" fill-opacity="{0.85 if hoch else 0.35}"/>')  # Layout
    letzter = None
    for i, tag in enumerate(d.index):                                               # Zeitachse
        schl = (tag.year, tag.month) if e["name"] != "Stunde" else tag.normalize()
        if e["name"] == "Woche":
            schl = (tag.year, (tag.month - 1) // 3)                                 # Layout: Quartale
        if schl != letzter and letzter is not None and (e["name"] != "Stunde" or tag.dayofweek == 0):
            text = f"{tag:%d.%m.}" if e["name"] == "Stunde" else f"{tag:%m/%y}"
            A(f'<text x="{X(i):.1f}" y="{H - 6}" fill="{TEXT_3}" font-size="11">{text}</text>')  # Layout
        letzter = schl
    A(f'<text x="{ende + 8}" y="{y0 + 12}" fill="{TEXT_3}" font-size="11">Volumen</text>')   # Layout
    A("</svg>")
    return "".join(s)
