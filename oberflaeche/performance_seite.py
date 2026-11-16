"""Seite Performance (16.11.2026): Kurve des Kontos gegen den Zielpfad, Hochrechnung auf ein Jahr, Unterwasser-Phasen
und die Bilanz der geschlossenen Trades. Rechnung in kern/performance.py, Eingaben in app.py (Formulare)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kern"))
import depot  # noqa: E402
import performance  # noqa: E402
from fundament import MIO  # noqa: E402  eine Million – eine Quelle (fundament)
from gestaltung import BLAU, GELB, GRUEN, RAND, ROT, TEXT, TEXT_2, TEXT_3, ampelzeile, karte, seite, t, zahl  # noqa: E402

B = 1100                    # Breite der Kurve (Pixel)
H = 330                     # Höhe der Kurve
UW = 90                     # Höhe der Unterwasser-Leiste
KURVE_LINKS = 96            # Rand links (Achse: bis „999,9 Tsd. €“ – 16.11.2026: Zahlen links abgeschnitten)
TSD_AB = 1e4                # Achse: ab 10.000 in Tsd.
TAUSEND = 1e3               # Achse: Teiler für Tsd.
KURVE_RECHTS = 150          # Rand rechts (Beschriftungen)


def _achse(v):
    """Wert an der Achse kurz: 652 €, 12,3 Tsd. €, 33,8 Mio. €."""
    if v >= MIO:
        return f"{zahl(v / MIO, 1)} Mio. €"
    if v >= TSD_AB:
        return f"{zahl(v / TAUSEND, 1)} Tsd. €"
    return f"{zahl(v, 0)} €"


def _pct(r, stellen=1):
    return f'{"+" if r >= 0 else "−"}{zahl(abs(r) * 100, stellen)} %'


def _kachel(name, wert, unter="", farbe=TEXT):
    return (f'<div style="background:#1C2430;border:1px solid {RAND};border-radius:10px;padding:12px 16px;min-width:190px">'
            f'<div style="color:{TEXT_2};font-size:13px">{t(name)}</div>'
            f'<div style="font-size:24px;font-weight:600;color:{farbe}">{t(wert)}</div>'
            f'<div style="color:{TEXT_3};font-size:13px">{t(unter)}</div></div>')


def kurve(d, p):
    """SVG: reale Kurve (Depotwert), Zielpfad (gestrichelt) und Prognose mit der Ø Wochenrendite bis Woche 52; darunter
    die Unterwasser-Leiste (Abstand zum bisherigen Hoch)."""
    start = float(d["start"])
    w = p["wochen"]
    n_real = len(w)
    real = [start] + [z["wert"] for z in w]
    ziel = [start * (1 + (d.get("ziel_woche") or 0)) ** i for i in range(performance.WOCHEN_JAHR + 1)] \
        if d.get("ziel_woche") is not None else []
    prog = ([real[-1] * (1 + p["schnitt"]) ** (i - n_real) for i in range(n_real, performance.WOCHEN_JAHR + 1)]
            if p.get("schnitt") is not None and n_real < performance.WOCHEN_JAHR else [])
    werte = [x for x in real + ziel + prog if x and x > 0]
    lo, hi = min(werte) * 0.9, max(werte) * 1.1
    import math
    breite = B - KURVE_LINKS - KURVE_RECHTS

    def X(i):
        return KURVE_LINKS + breite * i / performance.WOCHEN_JAHR

    def Y(v):
        return 20 + (H - 40) * (1 - (math.log(v) - math.log(lo)) / (math.log(hi) - math.log(lo)))

    s = [f'<svg viewBox="0 0 {B} {H + UW + 40}" width="100%" xmlns="http://www.w3.org/2000/svg" '
         f'style="font-family:IBM Plex Sans,sans-serif">']
    for k in range(5):
        v = lo * (hi / lo) ** (k / 4)
        s.append(f'<line x1="{KURVE_LINKS}" x2="{B - KURVE_RECHTS}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{RAND}"/>'
                 f'<text x="{KURVE_LINKS - 8}" y="{Y(v) + 4:.1f}" fill="{TEXT_3}" font-size="12" text-anchor="end">'
                 f'{_achse(v)}</text>')
    for i in range(0, performance.WOCHEN_JAHR + 1, 4):
        s.append(f'<text x="{X(i):.1f}" y="{H + UW + 32}" fill="{TEXT_3}" font-size="12" text-anchor="middle">W {i}</text>')

    def linie(punkte, farbe, strich="", dicke=2.5):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in punkte if v and v > 0)
        return (f'<polyline points="{pts}" fill="none" stroke="{farbe}" stroke-width="{dicke}"'
                + (f' stroke-dasharray="{strich}"' if strich else "") + "/>")
    if ziel:
        s.append(linie(list(enumerate(ziel)), TEXT_3, "6 5", 1.8))
        s.append(f'<text x="{B - KURVE_RECHTS + 6}" y="{Y(ziel[-1]) + 4:.1f}" fill="{TEXT_3}" font-size="12">Ziel '
                 f'{zahl(ziel[-1], 0)} €</text>')
    if prog:
        s.append(linie([(n_real + j, v) for j, v in enumerate(prog)], BLAU, "3 4", 1.8))
        s.append(f'<text x="{B - KURVE_RECHTS + 6}" y="{Y(prog[-1]) + 18:.1f}" fill="{BLAU}" font-size="12">mit Ø '
                 f'{zahl(prog[-1], 0)} €</text>')
    s.append(linie(list(enumerate(real)), ROT if real[-1] < start else GRUEN))
    for i, v in enumerate(real):
        s.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" fill="{TEXT}"><title>Woche {i}: {zahl(v, 0)} €'
                 f'</title></circle>')
    # Unterwasser: Abstand zum bisherigen Hoch, rot ab der Verlustbremse
    oben = H + 10
    s.append(f'<text x="{KURVE_LINKS - 8}" y="{oben + 12}" fill="{TEXT_3}" font-size="12" text-anchor="end">0 %</text>'
             f'<line x1="{KURVE_LINKS}" x2="{B - KURVE_RECHTS}" y1="{oben}" y2="{oben}" stroke="{RAND}"/>'
             f'<text x="{B - KURVE_RECHTS + 6}" y="{oben + 14}" fill="{TEXT_2}" font-size="12">Unterwasser</text>')
    tief = max([z["unterwasser"] for z in w] + [depot.VERLUSTBREMSE * 2])
    for z in w:
        hoehe = (UW - 10) * z["unterwasser"] / tief
        if hoehe > 0:
            farbe = ROT if z["unterwasser"] >= depot.VERLUSTBREMSE else GELB
            s.append(f'<rect x="{X(z["nr"]) - 6:.1f}" y="{oben}" width="12" height="{hoehe:.1f}" fill="{farbe}" '
                     f'fill-opacity="0.8"><title>Woche {z["nr"]}: {zahl(z["unterwasser"], 1)} % unter dem Hoch</title></rect>')
    s.append("</svg>")
    return "".join(s)


def seite_performance():
    """HTML der Seite (ohne die Eingaben)."""
    d = performance.laden()
    p = performance.rechnen(d)
    if not p:
        return seite(karte(f'<div style="color:{TEXT_2};font-size:15px">Noch kein Startkapital eingetragen – unten '
                           f'„⚙ Start und Ziel“.</div>', "Performance"))
    kacheln = []
    if p["wochen"]:
        letzte = p["wochen"][-1]
        kacheln.append(_kachel("Depotwert", f'{zahl(letzte["wert"], 0)} €',
                               f'Woche {letzte["nr"]} · Start {zahl(d["start"], 0)} €'))
        kacheln.append(_kachel("Ø Wochenrendite (real)", _pct(p["schnitt"]),
                               f'letzte Woche {_pct(p["letzte"])}', GRUEN if p["schnitt"] >= 0 else ROT))
        n_ = len(p["wochen"])                    # worauf die Hochrechnung steht (Micky 16.11.2026: „aus N Wochen“)
        aus_ = f'aus {n_} Woche{"" if n_ == 1 else "n"}'
        kacheln.append(_kachel("Hochgerechnet auf ein Jahr", _pct(p["jahr_schnitt"], 0),
                               f'mit Ø {aus_}: {zahl(p["wert_jahr_schnitt"], 0)} € nach 52 Wochen',
                               GRUEN if p["jahr_schnitt"] >= 0 else ROT))
        if n_ > 1:                               # mit einer Woche zeigt sie dasselbe wie der Ø
            kacheln.append(_kachel("… mit der letzten Woche", _pct(p["jahr_letzte"], 0),
                                   f'{zahl(p["wert_jahr_letzte"], 0)} € nach 52 Wochen'))
    if p.get("ziel_jahr") is not None:
        kacheln.append(_kachel("Ziel", f'{_pct(d["ziel_woche"])} je Woche',
                               f'= {_pct(p["ziel_jahr"], 0)} im Jahr · {zahl(p["ziel_wert_jahr"], 0)} €'))
    kopf = f'<div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:12px">{"".join(kacheln)}</div>'
    zeichen = ""
    if p["wochen"]:
        uw = p["unterwasser"]
        zeichen += ampelzeile(f'Unterwasser: {zahl(uw, 1)} % unter dem bisherigen Hoch (tiefster Stand {zahl(p["tiefster"], 1)} %)',
                              "grün" if uw == 0 else "rot" if uw >= depot.VERLUSTBREMSE else "gelb",
                              f"ab {zahl(depot.VERLUSTBREMSE, 0)} % rot: Minervini halbiert dann das Risiko je Trade")
        if p.get("ziel_jahr") is not None:
            z_ = p["wochen"][-1]["ziel"]
            ab = (p["wochen"][-1]["wert"] / z_ - 1) * 100
            zeichen += ampelzeile(f'Gegen den Zielpfad: {"+" if ab >= 0 else "−"}{zahl(abs(ab), 1)} % '
                                  f'(Ziel Woche {p["wochen"][-1]["nr"]}: {zahl(z_, 0)} €)', "grau",
                                  "Weit über dem Zielpfad: Teilgewinne sichern, Stopps eng; darunter: das System prüfen, "
                                  "nicht die Größe erhöhen")
    tabelle = "".join(
        f'<tr><td>W {z["nr"]}</td><td>{z["datum"][8:10]}.{z["datum"][5:7]}.{z["datum"][:4]}</td>'
        f'<td style="text-align:right">{zahl(z["wert"], 0)} €</td>'
        f'<td style="text-align:right">{zahl(z["einzahlung"], 0) + " €" if z["einzahlung"] else "–"}</td>'
        f'<td style="text-align:right;color:{GRUEN if z["rendite"] >= 0 else ROT}">{_pct(z["rendite"], 2)}</td>'
        f'<td style="text-align:right">{zahl(z["ziel"], 0)} €</td>'
        f'<td style="text-align:right">{zahl(z["unterwasser"], 1)} %</td></tr>' for z in reversed(p["wochen"]))
    tab = (f'<table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:10px;color:{TEXT}">'
           f'<tr style="color:{TEXT_2};text-align:left"><th>Woche</th><th>Freitag</th><th style="text-align:right">Depotwert</th>'
           f'<th style="text-align:right">Ein-/Auszahlung</th><th style="text-align:right">Rendite</th>'
           f'<th style="text-align:right">Zielpfad</th><th style="text-align:right">Unterwasser</th></tr>{tabelle}</table>'
           if tabelle else f'<div style="color:{TEXT_2}">Noch keine Woche eingetragen.</div>')
    b = depot.bilanz()
    bil = (ampelzeile(f'{b["anzahl"]} geschlossene Trades · Trefferquote {zahl(b["treffer_pct"], 0)} %', "grau",
                      f'Ø Gewinn {zahl(b["schnitt_gewinn"], 1) + " %" if b["schnitt_gewinn"] is not None else "–"} · '
                      f'Ø Verlust {zahl(b["schnitt_verlust"], 1) + " %" if b["schnitt_verlust"] is not None else "–"}'
                      + (f' · Verhältnis {zahl(b["schnitt_gewinn"] / b["schnitt_verlust"], 1)} : 1'
                         if b["schnitt_gewinn"] and b["schnitt_verlust"] else ""))
           if b else f'<div style="color:{TEXT_2}">Noch keine geschlossenen Trades (Depot → Position schließen mit Ausstiegskurs).</div>')
    return seite(karte(kopf + kurve(d, p) + zeichen, "Performance · reale Kurve gegen Zielpfad")
                 + karte(tab, "Woche für Woche") + karte(bil, "Bilanz der geschlossenen Trades"))
