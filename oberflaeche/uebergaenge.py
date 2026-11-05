"""Tafel „Übergänge“: wer an der Tür zum nächsten Feld steht – Quad (Makro), Sektoren und Themen-Gruppen.

Der Kreislauf läuft im Uhrzeigersinn: Abgehängt → Erstarkend → Führend → Ermüdend → Abgehängt.
Der Schwung dreht vor der Stärke: Die Türen Abgehängt → Erstarkend und Führend → Ermüdend melden früh,
die Türen Erstarkend → Führend und Ermüdend → Abgehängt bestätigen. „An der Tür“ heißt: höchstens NAH Punkte
vor der 100-Linie der entscheidenden Achse und die Bewegung der letzten 5 Wochen zeigt auf die Tür.
Ein Haken ist eine Gruppe, die vor der Tür zurück in ihr altes Feld dreht.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

import lage                                                         # noqa: E402
import rudel                                                        # noqa: E402
import sektoren                                                     # noqa: E402
import namen_de                                                     # noqa: E402
from frontkarte import FARBE, GRUND, PFEILE, PFEILFARBE, _pfeil, richtung  # noqa: E402
from gestaltung import KARTE, RAND, TEXT_2, TEXT_3, t, zahl         # noqa: E402

NAH = 3.0                 # Punkte vor der 100-Linie
TUEREN = [("Abgehängt", "Erstarkend", "früh", "Schwung dreht nach oben – Basen beobachten"),
          ("Erstarkend", "Führend", "Bestätigung", "Stärke steigt über den Markt – erste Ausbrüche"),
          ("Führend", "Ermüdend", "früh", "Schwung kippt – Stopps nachziehen, keine späten Basen"),
          ("Ermüdend", "Abgehängt", "Bestätigung", "Stärke fällt unter den Markt – raus, Short prüfen")]
HAKEN = {"Erstarkend": "Abgehängt", "Ermüdend": "Führend"}


def tuer(r):
    """'Tür' mit Zielfeld, 'Haken' mit Rückfeld oder None."""
    s, m, f = r["staerke"], r["schwung"], r["feld"]
    h, v = richtung(r)
    if f == "Abgehängt" and 100 - m <= NAH and v == 1:
        return "Tür", "Erstarkend"
    if f == "Erstarkend":
        if 100 - s <= NAH and h == 1:
            return "Tür", "Führend"
        if m - 100 <= NAH and v == -1:
            return "Haken", "Abgehängt"
    if f == "Führend" and m - 100 <= NAH and v == -1:
        return "Tür", "Ermüdend"
    if f == "Ermüdend":
        if s - 100 <= NAH and h == -1:
            return "Tür", "Abgehängt"
        if 100 - m <= NAH and v == 1:
            return "Haken", "Führend"
    return None


def _chip(text, tip, pf, rand=RAND):
    return (f'<span class="hinweis-zone" style="position:relative;display:inline-flex;gap:6px;align-items:center;'
            f'font-size:12px;font-family:IBM Plex Mono,monospace;border:1px solid {rand};border-radius:6px;'
            f'padding:3px 7px;background:#1C2430">{text}<span style="color:{PFEILFARBE.get(pf, TEXT_2)}">{pf}</span>'
            f'<span class="hinweis-tip" style="left:0;right:auto;font-family:IBM Plex Sans,system-ui;font-size:13px">'
            f'{tip}</span></span>')


def _sektor_chip(etf, r, ziel):
    pf = _pfeil(r)
    tip = (f'{t(r["name"])} ({etf}) · {r["feld"]} → {ziel} · Stärke {zahl(r["staerke"], 1)}, '
           f'Schwung {zahl(r["schwung"], 1)} · {PFEILE[pf]}')
    return _chip(f'{t(r["name"])}', tip, pf, GRUND[ziel] + "90")


def _gruppen_chip(g, ziel):
    pf = _pfeil(g)
    b = rudel.breite(g["mitglieder"])
    kopf = " · ".join(g["mitglieder"][:3]) + (f' +{len(g["mitglieder"]) - 3}' if len(g["mitglieder"]) > 3 else "")
    breite = (f'<span style="color:{TEXT_3}">{b["im_trend"]}/{b["anzahl"]}</span>' if b["anzahl"] else "")
    tip = (f'Themen-Gruppe {g["nr"]} (Branchen der Mitglieder: {t(namen_de.branche(g["name"]))}) · {g["feld"]} → {ziel} · Stärke {zahl(g["staerke"], 1)}, '
           f'Schwung {zahl(g["schwung"], 1)} · {PFEILE[pf]}<br>Breite: {b["im_trend"]} von {b["anzahl"]} im '
           f'Aufwärtstrend (über steigendem GD200), {b["nahe_hoch"]} nahe am 52-Wochen-Hoch<br>'
           + ", ".join(g["mitglieder"][:30]) + (" …" if len(g["mitglieder"]) > 30 else ""))
    return _chip(f'{t(kopf)} {breite}', tip, pf, GRUND[ziel] + "90")


def _zeile(titel, chips):
    inhalt = "".join(chips) or f'<span style="font-size:12px;color:{TEXT_3}">keine</span>'
    return (f'<div style="display:flex;flex-direction:column;gap:6px"><span style="font-size:12px;color:{TEXT_3}">'
            f'{titel}</span><div style="display:flex;flex-wrap:wrap;gap:6px">{inhalt}</div></div>')


def _quad_tuer(q, achse):
    """Tür zum nächsten Quad, wenn eine Achse kippt: wie viele Instrumente schon dagegen stehen."""
    a = q[achse]
    gegen_richtung = "fällt" if a["richtung"] == "steigt" else "steigt"
    w, i = q["wachstum"]["richtung"], q["inflation"]["richtung"]
    if "unklar" in (w, i):
        return ""
    ziel = lage._quad(gegen_richtung if achse == "wachstum" else w, gegen_richtung if achse == "inflation" else i)
    gekippt = [n for n, (r, *_) in a["instrumente"].items() if r == gegen_richtung]
    noetig = a["von"] // 2 + 1
    felder = "".join(
        f'<span title="{t(n)}: {r}" style="flex:1;height:10px;border-radius:3px;'
        f'background:{"#E3B341" if r == gegen_richtung else "#2A3444"}"></span>'
        for n, (r, *_) in a["instrumente"].items())
    name = "Wachstum" if achse == "wachstum" else "Inflation"
    return (f'<div style="background:#1C2430;border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px">'
            f'<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap">'
            f'<span style="font-size:14px;font-weight:600">→ Quad {ziel} · {lage.QUADS[ziel]}</span>'
            f'<span style="font-size:12px;color:{TEXT_3}">wenn {name} kippt</span></div>'
            f'<div style="display:flex;gap:4px">{felder}</div>'
            f'<div style="font-size:12px;color:{TEXT_2}">{len(gekippt)} von {a["von"]} Instrumenten gekippt, '
            f'{noetig} nötig' + (f' · gekippt: {t(", ".join(gekippt))}' if gekippt else "") + '</div>'
            f'<div style="font-size:12px;color:{TEXT_3}">typische Führer dort: {t(lage.FUEHRER[ziel])}</div></div>')


def tafel(q):
    rot = sektoren.rotation()
    try:
        themen = [g for g in rudel.themen() if g.get("feld") and g.get("schweif")]
    except Exception:
        themen = []
    an_tuer = {(a, z): {"sek": [], "grp": []} for a, z, *_ in TUEREN}
    haken = {"sek": [], "grp": []}
    for etf, r in sorted(rot.items(), key=lambda kv: -kv[1]["staerke"]):
        x = tuer(r)
        if x and x[0] == "Tür":
            an_tuer[(r["feld"], x[1])]["sek"].append(_sektor_chip(etf, r, x[1]))
        elif x:
            haken["sek"].append(_sektor_chip(etf, r, x[1]))
    for g in sorted(themen, key=lambda g: -len(g["mitglieder"])):
        x = tuer(g)
        if x and x[0] == "Tür":
            an_tuer[(g["feld"], x[1])]["grp"].append(_gruppen_chip(g, x[1]))
        elif x:
            haken["grp"].append(_gruppen_chip(g, x[1]))

    tueren = ""
    for von, nach, rolle, tun in TUEREN:
        d = an_tuer[(von, nach)]
        tueren += (f'<div style="border:1px solid {GRUND[nach]}60;border-radius:10px;padding:12px;display:flex;'
                   f'flex-direction:column;gap:10px;background:{GRUND[nach]}0D">'
                   f'<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;flex-wrap:wrap">'
                   f'<span style="font-size:15px;font-weight:600"><span style="color:{FARBE[von]}">{von}</span> → '
                   f'<span style="color:{FARBE[nach]}">{nach}</span></span>'
                   f'<span style="font-size:11px;letter-spacing:0.06em;text-transform:uppercase;color:{TEXT_3}">{rolle}</span></div>'
                   f'<div style="font-size:12px;color:{TEXT_2}">{t(tun)}</div>'
                   f'{_zeile("Sektoren", d["sek"])}{_zeile("Themen-Gruppen", d["grp"])}</div>')
    haken_html = ""
    if haken["sek"] or haken["grp"]:
        haken_html = (f'<div style="border:1px dashed {RAND};border-radius:10px;padding:12px;display:flex;'
                      f'flex-direction:column;gap:10px"><div style="font-size:15px;font-weight:600">↩ Haken '
                      f'<span style="font-size:12px;font-weight:400;color:{TEXT_3}">drehen vor der Tür zurück ins '
                      f'alte Feld (Rahmen = Feld, in das sie zurückdrehen)</span></div>'
                      + (_zeile("Sektoren", haken["sek"]) if haken["sek"] else "")
                      + (_zeile("Themen-Gruppen", haken["grp"]) if haken["grp"] else "") + '</div>')
    quad = (f'<div style="display:flex;flex-direction:column;gap:8px">'
            f'<div style="font-size:14px;font-weight:600">Quad {q["quad"]} · {q["name"]} – die nächsten Türen</div>'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px">'
            f'{_quad_tuer(q, "wachstum")}{_quad_tuer(q, "inflation")}</div></div>')
    return (f'<section style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:20px;'
            f'display:flex;flex-direction:column;gap:16px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
            f'<h2 style="margin:0;font-size:20px;font-weight:600">Übergänge · wer an der Tür steht</h2>'
            f'<span style="font-size:13px;color:{TEXT_3}">an der Tür = höchstens {zahl(NAH, 0)} Punkte vor der '
            f'100-Linie und die Bewegung der letzten 5 Wochen zeigt darauf; Zahl bei Gruppen = Mitglieder im '
            f'Aufwärtstrend; Maus zeigt Einzelheiten</span></div>'
            f'{quad}'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px">{tueren}</div>'
            f'{haken_html}</section>')
