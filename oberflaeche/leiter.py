"""Die Leiter (Micky 26.11.2026): alle Stellungen aller Ebenen auf einer Preisachse neben dem Bericht – Front und
Unterkante kräftig, Decken rot, Böden grün, die alte Plattform als blasses Band (Rollentausch, nicht gezählt), der
Kurs als Punkt. Lücken über 3 Tages-ATR (ein ganzer Zug, livermore.WEG_ATR) heißen „sauber“. Stellungen weiter als
LEITER_ATR vom Kurs stehen mit Pfeil am Rand."""
from gestaltung import BLAU, GRUEN, ROT, TEXT, TEXT_2, TEXT_3, t, zahl

B, H = 360, 470            # Layout: Breite und Höhe des Bildes
X0, X1 = 8, 150            # Layout: die Sprossen
OBEN, UNTEN = 18, 452      # Layout: Rand der Achse
ETIKETT_ABSTAND = 15               # Layout: Mindestabstand der Beschriftungen
LEITER_ATR = 8             # Layout: so viele Tages-ATR über und unter dem Kurs zeigt die Leiter
NAME = {"front": "Front", "unterkante": "Unterkante", "decke": "Decke", "boden": "Boden"}


def bild(le):
    """SVG der Leiter aus bericht.leiter → HTML oder "" ohne Daten."""
    if not le or not le["sprossen"]:
        return ""
    import livermore
    kurs, a = le["kurs"], le["atr"] or le["kurs"] * 0.02   # Layout: ohne ATR 2 % je Stufe
    preise = [s_["preis"] for s_ in le["sprossen"]] + [x for g in le["alt"] for x in (g["unten"], g["oben"])] + [kurs]
    hi = min(max(preise), kurs + LEITER_ATR * a)
    lo = max(min(preise), kurs - LEITER_ATR * a)
    hi, lo = hi + (hi - lo) * 0.04, lo - (hi - lo) * 0.04  # Layout: Luft am Rand
    Y = lambda p_: OBEN + (hi - min(max(p_, lo), hi)) / (hi - lo) * (UNTEN - OBEN)   # noqa: E731
    s = [f'<svg viewBox="0 0 {B} {H}" style="width:100%;height:auto;display:block" role="img" '
         f'aria-label="Leiter der Stellungen über alle Ebenen">']
    for g in le["alt"]:                                                          # alte Plattform: blasses Band
        farbe = ROT if g["rolle"] == "decke" else GRUEN
        y0, y1 = Y(g["oben"]), Y(g["unten"])
        s.append(f'<rect x="{X0}" y="{y0:.1f}" width="{X1 - X0}" height="{max(3, y1 - y0):.1f}" fill="{farbe}" '  # Layout
                 f'fill-opacity="0.12" stroke="{farbe}" stroke-opacity="0.5" stroke-dasharray="3 3"/>')
    etik = []
    for s_ in sorted(le["sprossen"], key=lambda x: -x["preis"]):
        farbe = ROT if s_["preis"] > kurs else GRUEN
        stark = s_["art"] in ("front", "unterkante")
        y = Y(s_["preis"])
        s.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{farbe}" stroke-width="{2.5 if stark else 1.2}"'  # Layout
                 + ('' if stark else ' stroke-dasharray="5 3"') + '/>')
        rand = "↑ " if s_["preis"] > hi else "↓ " if s_["preis"] < lo else ""
        wort = NAME[s_["art"]] if stark else ("Decke" if s_["preis"] > kurs else "Boden")
        etik.append((y, f'{rand}{zahl(s_["preis"])} {wort} ({", ".join(s_["ebenen"])})'
                     + (f' · {s_["abpraller"]} 🛡' if s_["abpraller"] else ""), TEXT_2 if not stark else TEXT))
    for g in le["alt"]:
        etik.append(((Y(g["oben"]) + Y(g["unten"])) / 2, f'alte Plattform {zahl(g["unten"])}'
                     + (f'–{zahl(g["oben"])}' if g["oben"] != g["unten"] else "") + f' ({", ".join(g["ebenen"])})', TEXT_3))
    yk = Y(kurs)
    s.append(f'<circle cx="{(X0 + X1) / 2:.1f}" cy="{yk:.1f}" r="6" fill="{BLAU}"/>')
    etik.append((yk, f'Kurs {zahl(kurs)}', BLAU))
    stufen = sorted([s_["preis"] for s_ in le["sprossen"]] + [kurs])            # sauber: Lücken über einen ganzen Zug
    for p0, p1 in zip(stufen, stufen[1:]):
        if p1 - p0 > livermore.WEG_ATR * a and Y(p0) - Y(p1) > ETIKETT_ABSTAND * 2:
            s.append(f'<text x="{(X0 + X1) / 2:.1f}" y="{(Y(p0) + Y(p1)) / 2 + 4:.1f}" fill="{TEXT_3}" font-size="12" '  # Layout
                     f'text-anchor="middle">sauber</text>')
    etik.sort(key=lambda x: x[0])                                                # Beschriftungen ohne Überlappung
    platz = []
    for y, _, _ in etik:
        platz.append(max(y + 4, (platz[-1] + ETIKETT_ABSTAND) if platz else OBEN))  # Layout
    ueber = max(0, platz[-1] - (H - 4)) if platz else 0                          # Layout: unten zu voll: alles hochschieben
    for y_, (_, text, farbe) in zip(platz, etik):
        s.append(f'<text x="{X1 + 8}" y="{max(OBEN, y_ - ueber):.1f}" fill="{farbe}" font-size="12">{t(text)}</text>')  # Layout
    s.append("</svg>")
    return "".join(s)
