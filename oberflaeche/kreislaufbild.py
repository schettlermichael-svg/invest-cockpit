"""Kreislaufbild je Titel (Micky 13.11.2026): der echte Kursverlauf eines Jahres (Wochenschlüsse), nach Phasen gefärbt –
aufwärts grün, Balance grau (Basis und Verteilung), abwärts rot –, ein Punkt „hier steht er“, darunter die Phase in
Worten, der Wechsel, der sich abzeichnet, und die Zeichen der Stärke und Schwäche, die die App gemessen hat.

gross(k, titel, satz_stab=None)  großes Bild für Titelseite, Akte und Chance im Tagesbefehl (HTML mit SVG)
mini(k, breite, hoehe)           Mini-Kurve für die Karten auf Rückenwind und Setups (SVG)
punkt_wort(k)                    Phase in einem Wort mit farbigem Punkt für Tabellen, z. B. „● 4 → 1 Abwärts → Basis“
"""
from gestaltung import KARTE, RAND, TEXT, TEXT_2, TEXT_3, t

FARBE = {1: "#8A94A6", 2: "#1D9E75", 3: "#8A94A6", 4: "#D85A30"}      # Balance grau, aufwärts grün, abwärts rot
PUNKT = {1: "⚪", 2: "🟢", 3: "⚪", 4: "🔴"}
NAME = {1: "Basis", 2: "Aufwärts", 3: "Verteilung", 4: "Abwärts"}


def wort(k):
    """„Phase 4 → 1 · Abwärts, Wechsel zur Basis“ in kurz: „4 → 1 Abwärts → Basis“."""
    if not k:
        return ""
    w = f'{k["phase"]} {NAME[k["phase"]]}'
    if k.get("ziel"):
        w = f'{k["phase"]} → {k["ziel"]} {NAME[k["phase"]]} → {NAME[k["ziel"]]}'
    if k.get("einquetschung"):
        w += " · Einquetschung"
    return w


def punkt_wort(k):
    return f'{PUNKT[k["phase"]]} {wort(k)}' if k else ""


def _pfade(kurve, phasen, x0, y0, b, h, dicke):
    lo, hi = min(kurve), max(kurve)
    sp = (hi - lo) or 1.0
    n = len(kurve)
    xs = [x0 + b * i / max(n - 1, 1) for i in range(n)]
    ys = [y0 + h - h * (v - lo) / sp for v in kurve]
    teile, start = [], 0
    for i in range(1, n + 1):
        if i == n or phasen[i] != phasen[start]:
            von = max(start - 1, 0)                         # an die vorige Strecke anschließen, keine Lücke
            pts = " ".join(f"{xs[j]:.1f},{ys[j]:.1f}" for j in range(von, i))
            teile.append(f'<polyline points="{pts}" fill="none" stroke="{FARBE[phasen[start]]}" '
                         f'stroke-width="{dicke}" stroke-linejoin="round" stroke-linecap="round"/>')
            start = i
    return teile, xs, ys


def mini(k, breite=120, hoehe=30):
    if not k or not k.get("kurve"):
        return ""
    teile, xs, ys = _pfade(k["kurve"], k["phasen"], 2, 3, breite - 6, hoehe - 6, 1.6)
    return (f'<svg width="{breite}" height="{hoehe}" viewBox="0 0 {breite} {hoehe}" role="img" '
            f'aria-label="Kreislauf ein Jahr, Phase {t(wort(k))}" style="display:block">' + "".join(teile)
            + f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="2.6" fill="{FARBE[k["phase"]]}"/></svg>')


def _ring(k):
    """Die vier Phasen als Leiste, die heutige hervorgehoben, das Ziel des Wechsels mit Pfeil."""
    zellen = []
    for p in (1, 2, 3, 4):
        an = p == k["phase"]
        ziel = p == k.get("ziel")
        rand = FARBE[p] if an or ziel else RAND
        zellen.append(f'<div style="flex:1;border:{"2px solid" if an else "1px dashed" if ziel else "1px solid"} '
                      f'{rand};border-radius:8px;padding:6px 8px;background:{"#1F2833" if an else "transparent"}">'
                      f'<div style="font-size:12px;color:{TEXT_3}">Phase {p}{" · hier" if an else " · nächste?" if ziel else ""}'
                      f'</div><div style="font-size:14px;color:{FARBE[p] if an or ziel else TEXT_2};font-weight:'
                      f'{600 if an else 400}">{NAME[p]}</div></div>')
    return f'<div style="display:flex;gap:6px;margin:10px 0 4px">{"".join(zellen)}</div>'


def gross(k, titel="", satz_stab=None, breite=640, hoehe=170):
    """Großes Kreislaufbild (HTML). satz_stab: der Satz des Stabs zu diesem Titel, wenn es einen gibt."""
    if not k or not k.get("kurve"):
        return ""
    teile, xs, ys = _pfade(k["kurve"], k["phasen"], 8, 12, breite - 120, hoehe - 34, 2.4)
    x, y = xs[-1], ys[-1]
    lo, hi = min(k["kurve"]), max(k["kurve"])
    svg = (f'<svg viewBox="0 0 {breite} {hoehe}" width="100%" role="img" aria-label="Kreislauf {t(titel)}: '
           f'{t(wort(k))}" style="display:block;max-width:{breite}px">'
           f'<text x="8" y="10" font-size="11" fill="{TEXT_3}">{hi:.2f} $</text>'
           f'<text x="8" y="{hoehe - 4}" font-size="11" fill="{TEXT_3}">{lo:.2f} $ · {t(k.get("kurve_von", ""))} – '
           f'{t(k.get("kurve_bis", ""))} (Wochenschlüsse)</text>' + "".join(teile)
           + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{FARBE[k["phase"]]}" stroke="{TEXT}" stroke-width="1.5"/>'
           f'<line x1="{x + 7:.1f}" y1="{y:.1f}" x2="{x + 20:.1f}" y2="{y:.1f}" stroke="{TEXT_2}" stroke-width="1"/>'
           f'<text x="{x + 24:.1f}" y="{y + 4:.1f}" font-size="13" fill="{TEXT}">hier steht er</text></svg>')
    leg = " ".join(f'<span style="color:{TEXT_3};font-size:12px;margin-right:10px">'
                   f'<span style="display:inline-block;width:14px;height:3px;background:{f};vertical-align:middle;'
                   f'margin-right:4px"></span>{n}</span>'
                   for f, n in ((FARBE[2], "aufwärts"), (FARBE[1], "Balance"), (FARBE[4], "abwärts")))
    zeilen = []
    for name, liste, f in (("Stärke", k.get("staerke") or [], FARBE[2]), ("Schwäche", k.get("schwaeche") or [], FARBE[4])):
        if liste:
            zeilen.append(f'<div style="font-size:14px;color:{TEXT_2};margin-top:4px"><b style="color:{f}">{name}:</b> '
                          + " · ".join(t(s) for s in liste) + "</div>")
    stab = (f'<div style="font-size:15px;color:{TEXT};margin-top:8px;border-left:3px solid {FARBE[k["phase"]]};'
            f'padding-left:8px">{t(satz_stab)}</div>') if satz_stab else ""
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:12px 14px;margin:8px 0">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap">'
            f'<b style="font-size:16px;color:{TEXT}">Kreislauf{(" · " + t(titel)) if titel else ""}</b>'
            f'<span style="font-size:15px;color:{FARBE[k["phase"]]}">{t(wort(k))}</span></div>'
            + svg + f'<div style="margin-top:2px">{leg}</div>' + _ring(k) + "".join(zeilen) + stab + "</div>")
