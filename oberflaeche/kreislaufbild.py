"""Kreislaufbild je Titel (Micky 13.11.2026): der echte Kursverlauf eines Jahres (Wochenschlüsse), nach Phasen gefärbt –
Basis blaugrau, aufwärts grün, Verteilung ambergrau, abwärts rot, Rückschlag in Phase 2 amber –, ein Punkt „hier steht
er“, dazu die Wochentiefs (gepunktet) und der S&P 500 als Schatten (gestrichelt, gleicher Start), damit Stärke oder
Schwäche gegen den Markt sofort sichtbar ist. Zeichnet sich ein Wechsel ab, verblasst die laufende Phase (hell) ab dem
ersten Zeichen. Darunter die Phase in Worten und die Zeichen der Stärke und Schwäche, die die App gemessen hat.

gross(k, titel, satz_stab=None)  großes Bild für die Titelseite (HTML mit SVG); satz_stab für den künftigen Strategen-Call
mini(k, breite, hoehe)           Mini-Kurve für die Karten auf Rückenwind und Setups (SVG)
punkt_wort(k)                    Phase in einem Wort mit farbigem Punkt für Tabellen, z. B. „● 4 → 1 Abwärts → Basis“
"""
from gestaltung import KARTE, RAND, TEXT, TEXT_2, TEXT_3, t, zahl

RUECKSCHLAG = 21
# Basis blaugrau, aufwärts grün, Verteilung ambergrau, abwärts rot, Rückschlag amber, jung neutral
FARBE = {0: "#6B7280", 1: "#7F93AD", 2: "#1D9E75", 3: "#B09A72", 4: "#D85A30", RUECKSCHLAG: "#E0A33A"}
# Wechsel zeichnet sich ab (Micky 13.11.2026: „Hell = laufende Phase verblasst“): die laufende Phase hell ab dem
# ersten Zeichen – 4 → 1 hellrot, 2 → 3 hellgrün, 1 → 2 und 1 → 4 hell-blaugrau, 3 → 2 und 3 → 4 hell-ambergrau
HELL = {1: "#BCC8D8", 2: "#9FE1CB", 3: "#DCCDAE", 4: "#F0997B", RUECKSCHLAG: "#F1D29A"}
PUNKT = {0: "◌", 1: "🔵", 2: "🟢", 3: "🟤", 4: "🔴"}
from zeichen import PHASE_NAME as NAME   # noqa: E402  ein Name je Phase in der ganzen App
INDEX_FARBE = "#9AA3AF"


def wort(k):
    """„Phase 4 → 1 · Abwärts, Wechsel zur Basis“ in kurz: „4 → 1 Abwärts → Basis“."""
    if not k:
        return ""
    p = k["phase"]
    if p == 0:
        return "jung (noch keine Phase)"
    w = f'{p} {NAME[p]}'
    if k.get("ziel"):
        w = f'{p} → {k["ziel"]} {NAME[p]} → {NAME[k["ziel"]]}'
    if k.get("rueckschlag"):
        w += " · Rückschlag"
    if k.get("einquetschung"):
        w += " · Einquetschung"
    return w


def punkt_wort(k):
    return f'{PUNKT.get(k["phase"], "◌")} {wort(k)}' if k else ""


def _farbe_jetzt(k):
    return FARBE[RUECKSCHLAG] if k.get("rueckschlag") else FARBE.get(k["phase"], FARBE[0])


def _farben(k):
    """Farbe je Woche: Phase; die letzten wechsel_wochen Wochen der laufenden Phase hell, wenn ein Wechsel sich abzeichnet."""
    ph = list(k["phasen"])
    f = [FARBE.get(p, FARBE[0]) for p in ph]
    if k.get("ziel") and k.get("wechsel_wochen"):
        jetzt = ph[-1]
        for i in range(max(0, len(ph) - int(k["wechsel_wochen"]) - 1), len(ph)):
            if ph[i] == jetzt or (jetzt in (2, RUECKSCHLAG) and ph[i] in (2, RUECKSCHLAG)):
                f[i] = HELL.get(ph[i], f[i])
    return f


def _skala(werte, y0, h):
    lo, hi = min(werte), max(werte)
    sp = (hi - lo) or 1.0
    return lo, hi, (lambda v: y0 + h - h * (v - lo) / sp)


def _pfade(kurve, farben, x0, b, y_, dicke):
    n = len(kurve)
    xs = [x0 + b * i / max(n - 1, 1) for i in range(n)]
    ys = [y_(v) for v in kurve]
    teile, start = [], 0
    for i in range(1, n + 1):
        if i == n or farben[i] != farben[start]:
            von = max(start - 1, 0)                         # an die vorige Strecke anschließen, keine Lücke
            pts = " ".join(f"{xs[j]:.1f},{ys[j]:.1f}" for j in range(von, i))
            teile.append(f'<polyline points="{pts}" fill="none" stroke="{farben[start]}" '
                         f'stroke-width="{dicke}" stroke-linejoin="round" stroke-linecap="round"/>')
            start = i
    return teile, xs, ys


def _linie(werte, x0, b, y_, farbe, dicke, strich):
    n = len(werte)
    pts = " ".join(f"{x0 + b * i / max(n - 1, 1):.1f},{y_(v):.1f}" for i, v in enumerate(werte))
    return (f'<polyline points="{pts}" fill="none" stroke="{farbe}" stroke-width="{dicke}" '
            f'stroke-dasharray="{strich}" stroke-linejoin="round" opacity="0.85"/>')


def _index_gleich(k):
    """S&P 500 auf den Startkurs des Titels umgerechnet (gleicher Start) oder None."""
    ik, ku = k.get("index_kurve"), k.get("kurve")
    if not ik or not ku or len(ik) != len(ku) or not ik[0]:
        return None
    f = ku[0] / ik[0]
    return [v * f for v in ik]


def mini(k, breite=120, hoehe=30):
    if not k or not k.get("kurve"):
        return ""
    farben = _farben(k)
    _, _, y_ = _skala(k["kurve"], 3, hoehe - 6)
    teile, xs, ys = _pfade(k["kurve"], farben, 2, breite - 6, y_, 1.6)
    return (f'<svg width="{breite}" height="{hoehe}" viewBox="0 0 {breite} {hoehe}" role="img" '
            f'aria-label="Kreislauf ein Jahr, Phase {t(wort(k))}" style="display:block">' + "".join(teile)
            + f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="2.6" fill="{farben[-1]}"/></svg>')


def _ring(k):
    """Die vier Phasen als Leiste, die heutige hervorgehoben, das Ziel des Wechsels mit Pfeil."""
    zellen = []
    for p in (1, 2, 3, 4):
        an = p == k["phase"]
        ziel = p == k.get("ziel")
        f = _farbe_jetzt(k) if an else FARBE[p]
        rand = f if an or ziel else RAND
        zellen.append(f'<div style="flex:1;border:{"2px solid" if an else "1px dashed" if ziel else "1px solid"} '
                      f'{rand};border-radius:8px;padding:6px 8px;background:{"#1F2833" if an else "transparent"}">'
                      f'<div style="font-size:12px;color:{TEXT_3}">Phase {p}{" · hier" if an else " · nächste?" if ziel else ""}'
                      f'</div><div style="font-size:14px;color:{f if an or ziel else TEXT_2};font-weight:'
                      f'{600 if an else 400}">{NAME[p]}{" · Rückschlag" if an and k.get("rueckschlag") else ""}</div></div>')
    return f'<div style="display:flex;gap:6px;margin:10px 0 4px">{"".join(zellen)}</div>'


def gross(k, titel="", satz_stab=None, breite=640, hoehe=170):
    """Großes Kreislaufbild (HTML). satz_stab: der Satz des Stabs zu diesem Titel, wenn es einen gibt."""
    if not k or not k.get("kurve"):
        return ""
    farben = _farben(k)
    tiefs = k.get("tiefs") if k.get("tiefs") and len(k["tiefs"]) == len(k["kurve"]) else None
    ix = _index_gleich(k)
    lo, hi, y_ = _skala(list(k["kurve"]) + (tiefs or []) + (ix or []), 12, hoehe - 34)
    b = breite - 120
    unten = []
    if ix:
        unten.append(_linie(ix, 8, b, y_, INDEX_FARBE, 1.2, "5 4"))
    if tiefs:
        unten.append(_linie(tiefs, 8, b, y_, TEXT_3, 1, "1 3"))
    teile, xs, ys = _pfade(k["kurve"], farben, 8, b, y_, 2.4)
    x, y = xs[-1], ys[-1]
    svg = (f'<svg viewBox="0 0 {breite} {hoehe}" width="100%" role="img" aria-label="Kreislauf {t(titel)}: '
           f'{t(wort(k))}" style="display:block;max-width:{breite}px">'
           f'<text x="8" y="10" font-size="11" fill="{TEXT_3}">{zahl(hi)} $</text>'
           f'<text x="8" y="{hoehe - 4}" font-size="11" fill="{TEXT_3}">{zahl(lo)} $ · {t(k.get("kurve_von", ""))} – '
           f'{t(k.get("kurve_bis", ""))} (Wochenschlüsse)</text>' + "".join(unten) + "".join(teile)
           + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{farben[-1]}" stroke="{TEXT}" stroke-width="1.5"/>'
           f'<line x1="{x + 7:.1f}" y1="{y:.1f}" x2="{x + 20:.1f}" y2="{y:.1f}" stroke="{TEXT_2}" stroke-width="1"/>'
           f'<text x="{x + 24:.1f}" y="{y + 4:.1f}" font-size="13" fill="{TEXT}">hier steht er</text></svg>')
    if ix:                                        # wer liegt vorn – in Zahlen, nicht nur im Bild
        t_pct = (k["kurve"][-1] / k["kurve"][0] - 1) * 100
        i_pct = (ix[-1] / ix[0] - 1) * 100
        vz = lambda v: ("+" if v > 0 else "") + zahl(v, 0)    # noqa: E731
        vorn = f'Titel {vz(t_pct)} %, S&P 500 {vz(i_pct)} % in 52 Wochen'
    else:
        vorn = ""
    eintraege = [(FARBE[1], "Basis", ""), (FARBE[2], "aufwärts", ""), (FARBE[3], "Verteilung", ""),
                 (FARBE[4], "abwärts", "")]
    if RUECKSCHLAG in k.get("phasen", []):
        eintraege.append((FARBE[RUECKSCHLAG], "Rückschlag", ""))
    if k.get("ziel") and k.get("wechsel_wochen"):
        eintraege.append((farben[-1], "hell: die Phase verblasst, Wechsel zeichnet sich ab", ""))
    if tiefs:
        eintraege.append((TEXT_3, "Wochentiefs", "1 3"))
    if ix:
        eintraege.append((INDEX_FARBE, "S&P 500 (gleicher Start)", "5 4"))
    leg = " ".join(
        f'<span style="color:{TEXT_3};font-size:12px;margin-right:10px;white-space:nowrap">'
        + (f'<svg width="16" height="6" style="vertical-align:middle;margin-right:4px"><line x1="0" y1="3" x2="16" y2="3" '
           f'stroke="{f}" stroke-width="2" stroke-dasharray="{s}"/></svg>' if s else
           f'<span style="display:inline-block;width:14px;height:3px;background:{f};vertical-align:middle;'
           f'margin-right:4px"></span>')
        + f'{n}</span>' for f, n, s in eintraege)
    if vorn:
        leg += f'<div style="color:{TEXT_2};font-size:13px;margin-top:2px">{t(vorn)}</div>'
    zeilen = []
    for name, liste, f in (("Stärke", k.get("staerke") or [], FARBE[2]), ("Schwäche", k.get("schwaeche") or [], FARBE[4])):
        if liste:
            zeilen.append(f'<div style="font-size:14px;color:{TEXT_2};margin-top:4px"><b style="color:{f}">{name}:</b> '
                          + " · ".join(t(s) for s in liste) + "</div>")
    stab = (f'<div style="font-size:15px;color:{TEXT};margin-top:8px;border-left:3px solid {_farbe_jetzt(k)};'
            f'padding-left:8px">{t(satz_stab)}</div>') if satz_stab else ""
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:12px 14px;margin:8px 0">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap">'
            f'<b style="font-size:16px;color:{TEXT}">Kreislauf{(" · " + t(titel)) if titel else ""}</b>'
            f'<span style="font-size:15px;color:{_farbe_jetzt(k)}">{t(wort(k))}</span></div>'
            + svg + f'<div style="margin-top:2px">{leg}</div>' + (_ring(k) if k["phase"] else "")
            + "".join(zeilen) + stab + "</div>")
