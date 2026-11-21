"""Der Zonenchart (Micky 21.11.2026): wenig, aber aussagekräftig – dasselbe Bild für Woche, Tag und Stunde.

Kursfeld: Kerzen; die Zone von heute als gelber Rahmen mit P, b oder D und ihr POC; die Zonen der Vergangenheit als
Kästen (erledigt blass, offen kräftiger mit 🪝 und bis zum rechten Rand verlängert – der Magnet); im Tageschart die
Wochenzone als feiner Rahmen; der Trade (Einstieg, Stopp, Ziel); rechts das Volumenprofil seit dem Anker als Silhouette.
Darunter das Phasenband (gelb Balance, grün Ausbruch oben, rot unten), das Volumen und das Feld der relativen Stärke
gegen den S&P 500 und gestrichelt gegen den Sektor (beide links bei 100, Punkte RS-Hoch bzw. RS-Tief vor Kurs).
Kein Durchschnitt, kein AVWAP-Fächer, keine Kürzel im Bild."""
import numpy as np
import pandas as pd

from gestaltung import BLAU, GELB, GRUEN, LILA, RAND, ROT, TEXT_2, TEXT_3, zahl

B = 1200                               # Layout: Breite des Bildes
LINKS, RECHTS, PROFIL_W = 56, 150, 70  # Layout: Preisachse, Etiketten, Volumenprofil
OBEN, KURS_H = 16, 360                 # Layout: Kursfeld
BAND_H, VOL_H, RS_H = 8, 60, 90        # Layout: Phasenband, Volumen, relative Stärke
LUECKE = 14                            # Layout: Abstand zwischen den Feldern
ZEIGEN = {"Woche": 104, "Tag": 126, "Stunde": 140}   # Kerzen im Bild (2 Jahre, 6 Monate, 20 Handelstage)
JAHR = {"Woche": 52, "Tag": 252, "Stunde": 252 * 7}  # Kerzen je Jahr (RS-Hoch vor Kurs)
PFEIL_N = 10                           # RS-Pfeil: die letzten 10 Kerzen
PFEIL_LEICHT, PFEIL_STARK = 1, 3       # ↗/↘ ab 1 %, ↑/↓ ab 3 % (wie bisher im Cockpit)
ZONE_FARBE = "#EDA100"                 # Zone wie in Vorwalds Bildern gelb
POC_FARBE = "#1BAF7A"
ALT_FARBE = "#8B97A8"
WOCHE_FARBE = "#7DB4FF"
EINSTIEG_FARBE = "#E6EAF0"
RS_HOCH_FARBE, RS_TIEF_FARBE = "#FFD166", "#FF6B6B"
BAND = {"b": GELB, "o": GRUEN, "u": ROT}
RAND_SPIEL = 0.04                      # Layout: 4 % Luft über und unter den Kursen


def _pfeil(r):
    g = r[~np.isnan(r)]
    if len(g) <= PFEIL_N:
        return ""
    alt, neu = g[-1 - PFEIL_N], g[-1]
    p = (neu / alt - 1) * 100
    z = "↑" if p >= PFEIL_STARK else "↗" if p >= PFEIL_LEICHT else "↓" if p <= -PFEIL_STARK else "↘" if p <= -PFEIL_LEICHT else "→"
    return f"{z} {alt:.0f} → {neu:.0f}"


def bild(e, la, hist, t=None, laufend=False, woche=None, rs=None):
    """SVG einer Ebene. e = tiefe.ebene, la = zonen.lage, hist = zonen.historie, t = zonen.trade (nur Tag),
    woche = (Lage der Wochenzone, Beginn) für den Tageschart, rs = {"index": Kurse, "sektor": Kurse oder None}."""
    import rueckenwind
    import zeichen
    import zonen
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
    kaesten = [z for z in hist if z["ende"] >= d.index[0]]
    magnete = zonen.naechste(hist, la["kurs"])
    werte = [h.max(), l.min(), lo, hi] + ([t["stopp"], t["ziel"]] if t else [])
    werte += [x for z in magnete for x in (z["val"], z["vah"])]
    if woche:
        werte += list(woche[0]["zone"])
    pmin, pmax = min(werte), max(werte)
    rand = (pmax - pmin) * RAND_SPIEL or 1
    pmin, pmax = pmin - rand, pmax + rand
    ende = B - RECHTS - PROFIL_W
    breite = ende - LINKS
    X = lambda i: LINKS + breite * (i + 0.5) / N                                   # noqa: E731
    Y = lambda y: OBEN + KURS_H * (1 - (y - pmin) / (pmax - pmin))                 # noqa: E731
    pos = lambda t_: min(max(int(d.index.searchsorted(pd.Timestamp(t_))), 0), N - 1)   # noqa: E731
    halb = breite / N / 2
    y_band = OBEN + KURS_H + LUECKE
    y_vol = y_band + BAND_H + LUECKE
    y_rs = y_vol + VOL_H + LUECKE + 14                                              # Layout: Platz für die Überschrift
    H = y_rs + RS_H + 24                                                            # Layout: Zeitachse
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}" width="100%" role="img" '
         f'aria-label="Zonenchart {e["name"]}" style="display:block;font-family:IBM Plex Sans,sans-serif">'
         '<style>text{paint-order:stroke;stroke:#161C24;stroke-width:4px;stroke-linejoin:round}</style>']
    A = s.append
    for k in range(5):                                                              # Layout: 5 Preislinien
        y_ = pmin + (pmax - pmin) * k / 4                                           # Layout
        A(f'<line x1="{LINKS}" x2="{ende}" y1="{Y(y_):.1f}" y2="{Y(y_):.1f}" stroke="{RAND}"/>'
          f'<text x="{LINKS - 6}" y="{Y(y_) + 4:.1f}" fill="{TEXT_3}" font-size="11" text-anchor="end">{y_:.0f}</text>')  # Layout
    etiketten = []                                                                  # (y, Text, Farbe) rechts
    for z in kaesten:                                                               # Zonen der Vergangenheit
        x0 = X(pos(z["start"])) - halb if z["start"] >= d.index[0] else LINKS
        x1 = X(pos(z["ende"])) + halb
        deck = 0.16 if z["offen"] else 0.07                                         # Layout
        A(f'<rect x="{x0:.1f}" y="{Y(z["hoch"]):.1f}" width="{max(2, x1 - x0):.1f}" height="{max(1, Y(z["tief"]) - Y(z["hoch"])):.1f}" '
          f'fill="{ALT_FARBE}" fill-opacity="{deck}" stroke="{ALT_FARBE}" stroke-opacity="{deck * 3:.2f}">'  # Layout
          f'<title>Zone {z["start"]:%d.%m.%y}–{z["ende"]:%d.%m.%y}: {zahl(z["tief"])}–{zahl(z["hoch"])} · '
          f'{"offen – seitdem nie wieder angelaufen" if z["offen"] else "erledigt"}</title></rect>')
    for z in magnete:                                                               # offene Zonen: Magnet bis rechts
        x0 = X(pos(z["ende"])) + halb if z["ende"] >= d.index[0] else LINKS
        A(f'<rect x="{x0:.1f}" y="{Y(z["vah"]):.1f}" width="{max(2, ende - x0):.1f}" height="{max(1, Y(z["val"]) - Y(z["vah"])):.1f}" '
          f'fill="{ALT_FARBE}" fill-opacity="0.10" stroke="{ALT_FARBE}" stroke-dasharray="3 3" stroke-opacity="0.5"/>')  # Layout
        etiketten.append((Y((z["val"] + z["vah"]) / 2), f'🪝 offen {zahl(z["val"], 0)}–{zahl(z["vah"], 0)}', ALT_FARBE))
    if woche:                                                                       # die höhere Ebene im Tageschart
        wl, wh = woche[0]["zone"]
        x0 = X(pos(woche[1])) - halb if woche[1] >= d.index[0] else LINKS
        A(f'<rect x="{x0:.1f}" y="{Y(wh):.1f}" width="{ende - x0:.1f}" height="{max(2, Y(wl) - Y(wh)):.1f}" fill="none" '
          f'stroke="{WOCHE_FARBE}" stroke-width="1.2" stroke-opacity="0.7"/>'                                    # Layout
          f'<text x="{x0 + 4:.1f}" y="{Y(wl) + 13:.1f}" fill="{WOCHE_FARBE}" font-size="11">Wochenzone {woche[0]["form"]}</text>')  # Layout: unter dem Rahmen
    zs = pd.Timestamp(pb["zone_start"]) if pb else pd.Timestamp(e["struktur"]["balance_start"])
    xz = X(pos(zs)) - halb if zs >= d.index[0] else LINKS
    A(f'<rect x="{xz:.1f}" y="{Y(hi):.1f}" width="{ende - xz:.1f}" height="{max(2, Y(lo) - Y(hi)):.1f}" fill="{ZONE_FARBE}" '
      f'fill-opacity="0.10" stroke="{ZONE_FARBE}" stroke-width="1.8" stroke-dasharray="6 3"/>'  # Layout
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
    pr = e["struktur"]["profil"]                                                    # Volumenprofil seit dem Anker
    vmax_p = float(max(pr["volumen"])) or 1.0
    for a_, b_, w_ in zip(pr["grenzen"][:-1], pr["grenzen"][1:], pr["volumen"]):
        if b_ < pmin or a_ > pmax:
            continue
        y1, y2 = Y(min(b_, pmax)), Y(max(a_, pmin))
        poc_ = a_ <= pr["poc"] <= b_
        A(f'<rect x="{ende + 2}" y="{y1 + 0.3:.1f}" width="{max(1, (PROFIL_W - 6) * w_ / vmax_p):.1f}" '
          f'height="{max(1, y2 - y1 - 0.6):.1f}" fill="{POC_FARBE if poc_ else ALT_FARBE}" fill-opacity="{0.9 if poc_ else 0.45}"/>')  # Layout
    A(f'<text x="{ende + 2}" y="{OBEN - 4}" fill="{TEXT_3}" font-size="10">Volumen seit {pd.Timestamp(pr["ab"]):%d.%m.}</text>')  # Layout
    belegt = []
    for y_, text, farbe in sorted(etiketten):                                       # rechts, ohne Überlappung
        while any(abs(y_ - b_) < 14 for b_ in belegt):                              # Layout: 14 px je Zeile
            y_ += 14                                                                # Layout
        belegt.append(y_)
        A(f'<text x="{ende + PROFIL_W + 6}" y="{y_ + 4:.1f}" fill="{farbe}" font-size="12">{text}</text>')  # Layout
    band = zonen.phasenband(d, kaesten, la, zs)                                     # Phasenband
    for i, p_ in enumerate(band):
        if p_:
            A(f'<rect x="{X(i) - halb:.1f}" y="{y_band}" width="{2 * halb + 0.3:.1f}" height="{BAND_H}" fill="{BAND[p_]}" '
              f'fill-opacity="0.85"/>')                                             # Layout
    A(f'<text x="{ende + 2}" y="{y_band + BAND_H}" fill="{TEXT_3}" font-size="10">Phase</text>')  # Layout
    vmax = v.max() or 1
    schnitt = pd.Series(v).rolling(min(50, N)).mean().to_numpy()                    # Layout: 50 Kerzen Schnitt
    for i in range(N):
        hv = VOL_H * v[i] / vmax
        hoch = not np.isnan(schnitt[i]) and v[i] > schnitt[i]
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y_vol + VOL_H - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" '
          f'fill="{GRUEN if c[i] >= o[i] else ROT}" fill-opacity="{0.85 if hoch else 0.35}"/>')  # Layout
    A(f'<text x="{ende + 2}" y="{y_vol + 12}" fill="{TEXT_3}" font-size="10">Volumen</text>')   # Layout
    if rs and rs.get("index") is not None:                                          # relative Stärke
        def relativ(bezug):
            bx = bezug.reindex(df.index, method="ffill")
            rv = df["Close"] / bx
            r = rv.reindex(d.index).to_numpy(float)
            g = np.flatnonzero(~np.isnan(r))
            return (r / r[g[0]] * 100, rv) if len(g) > PFEIL_N else (None, None)
        r_i, rv = relativ(rs["index"])
        r_s, _ = relativ(rs["sektor"]) if rs.get("sektor") is not None else (None, None)
        if r_i is not None:
            alle = np.concatenate([r_i[~np.isnan(r_i)], r_s[~np.isnan(r_s)] if r_s is not None else [], [100.0]])
            a0, a1 = alle.min(), alle.max()
            sp = (a1 - a0) * 0.08 or 1                                              # Layout
            a0, a1 = a0 - sp, a1 + sp
            YR = lambda y: y_rs + RS_H * (1 - (y - a0) / (a1 - a0))                 # noqa: E731
            A(f'<text x="{LINKS}" y="{y_rs - 6}" fill="{TEXT_3}" font-size="11">Relative Stärke · '
              f'<tspan fill="{BLAU}">— gegen S&amp;P 500 {_pfeil(r_i)}</tspan>'
              + (f'  <tspan fill="{LILA}">- - gegen Sektor {_pfeil(r_s)}</tspan>' if r_s is not None else "")
              + f'  · <tspan fill="{RS_HOCH_FARBE}">● RS-Hoch vor Kurs</tspan> · <tspan fill="{RS_TIEF_FARBE}">● RS-Tief vor Kurs</tspan></text>')
            A(f'<line x1="{LINKS}" x2="{ende}" y1="{YR(100):.1f}" y2="{YR(100):.1f}" stroke="{TEXT_3}" stroke-dasharray="2 4"/>')
            for r_, farbe, strich in ((r_s, LILA, ' stroke-dasharray="5 4"'), (r_i, BLAU, "")):
                if r_ is not None:
                    A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(r_) if not np.isnan(x))
                      + f'" fill="none" stroke="{farbe}" stroke-width="1.6"{strich}/>')  # Layout
            jahr = JAHR[e["name"]]
            cl = df["Close"]
            hoch_ = (rv >= zeichen.RS_HOCH * rv.rolling(jahr, min_periods=jahr).max()) & \
                    (cl < rueckenwind.KURS_NAH * cl.rolling(jahr, min_periods=jahr).max())
            tief_ = (rv <= rv.rolling(jahr, min_periods=jahr).min() / zeichen.RS_HOCH) & \
                    (cl > (2 - rueckenwind.KURS_NAH) * cl.rolling(jahr, min_periods=jahr).min())
            for reihe, farbe in ((hoch_, RS_HOCH_FARBE), (tief_, RS_TIEF_FARBE)):
                fl = reihe.reindex(d.index).fillna(False).to_numpy(bool)
                for i in np.flatnonzero(fl):
                    if not np.isnan(r_i[i]):
                        A(f'<circle cx="{X(i):.1f}" cy="{YR(r_i[i]):.1f}" r="3" fill="{farbe}"/>')  # Layout
    letzter = None
    for i, tag in enumerate(d.index):                                               # Zeitachse
        schl = {"Woche": (tag.year, (tag.month - 1) // 3), "Tag": (tag.year, tag.month)}.get(e["name"], tag.normalize())
        if schl != letzter and letzter is not None and (e["name"] != "Stunde" or tag.dayofweek == 0):
            text = f"{tag:%d.%m.}" if e["name"] == "Stunde" else f"{tag:%m/%y}"
            A(f'<text x="{X(i):.1f}" y="{H - 6}" fill="{TEXT_3}" font-size="11">{text}</text>')  # Layout
        letzter = schl
    A("</svg>")
    return "".join(s)
