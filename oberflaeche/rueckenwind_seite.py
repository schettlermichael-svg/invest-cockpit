"""Seite „Rückenwind“ (Modul rueckenwind_seite, Rechnung in kern/rueckenwind.py) (Konzept: KONZEPT_RUECKENWIND.md, 09.11.2026) – nur dieses Setup, getrennt von den Systemen.

Bausteine für app.py: kopf (Lage in Zahlen), stroemungskarte (Feld Stärke × Tempo mit dem Weg der letzten 4 Wochen),
gruppen (Tabelle nach Geldfluss), dreifach (Karten: Kurs, Geld und Zahlen grün), stufe (Tabelle je Stufe), logbuch.
Daten: kern/rueckenwind.py (Nachtlauf).
"""
import os
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))

from gestaltung import BLAU, GELB, GRUEN, KARTE, RAND, ROT, TEXT, TEXT_2, TEXT_3, seite, t, zahl  # noqa: E402

FELD_FARBE = {"Führend": GRUEN, "Erstarkend": BLAU, "Ermüdend": GELB, "Abgehängt": ROT}
FELD_TEXT = {"Führend": "Führend · Geld ist drin", "Erstarkend": "Erstarkend · Geld fließt zu",
             "Ermüdend": "Schwächelnd · Geld fließt ab", "Abgehängt": "Zurückfallend · Geld ist weg"}
STUFE_TEXT = {
    "Entsteht": "RS-Rang 50–84, in 4 Wochen um mindestens 15 Punkte gestiegen und schneller als davor – oder die "
                "RS-Linie steht am 52-Wochen-Hoch, der Kurs noch nicht. Der Trend am Anfang.",
    "Läuft": "RS-Rang ab 85, das Tempo hält (höchstens 5 Punkte verloren in 4 Wochen).",
    "Ermüdet": "RS-Rang noch ab 80, aber das Tempo bricht ein (Beschleunigung −15 oder schlechter, kaum noch "
               "Vorrücken: höchstens +5) oder 10 Punkte verloren in 4 Wochen – früheste Warnung, das Geld beginnt abzufließen.",
    "Abfluss": "Vor 4 Wochen ab 70, seitdem 20 Punkte oder mehr verloren – das Geld geht. Warnung für Halter, "
               "Gebiet für Shorts.",
}
PUNKT = {"grün": "🟢", "gelb": "🟡", "rot": "🔴", "grau": "⚪"}
TERMIN_WARNUNG = 14


def _chip(text, farbe):
    return (f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;border:1px solid {farbe};'
            f'color:{farbe};font-size:13px;margin:2px 4px 2px 0">{t(text)}</span>')


def kopf(erg):
    from collections import Counter
    n = Counter(x["stufe"] for x in erg["titel"].values())
    drei = len(dreifach_liste(erg))
    felder = Counter(g["feld"] for g in erg["gruppen"] if g["art"] == "Branche")
    zeile = " · ".join(f"{s} {n.get(s, 0)}" for s in ("Entsteht", "Läuft", "Ermüdet", "Abfluss"))
    return seite(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
        f'<h1 style="margin:0;font-size:30px;color:{TEXT}">Rückenwind</h1>'
        f'<div style="color:{TEXT_2};font-size:14px">Stand {pd.Timestamp(erg["stand"]):%d.%m.%Y} · '
        f'{len(erg["titel"])} Titel</div></div>'
        f'<p style="color:{TEXT_2};font-size:15px;margin:8px 0 14px">Kurs, Geld und Zahlen: RS-Dynamik des Titels, '
        f'Geldfluss in Sektor, Branche und Thema (zwei von drei vorne = grün), Fundament. Nur dieses Setup – getrennt von Minervini und Kullamägi. '
        f'Ampeln, nichts gefiltert.</p>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px">'
        + "".join(f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:12px 16px;'
                  f'min-width:150px"><div style="color:{TEXT_2};font-size:13px">{k}</div>'
                  f'<div style="color:{f};font-size:26px;font-weight:600">{v}</div></div>'
                  for k, v, f in (("Dreifacher Rückenwind", drei, GRUEN), ("Entsteht", n.get("Entsteht", 0), BLAU),
                                  ("Läuft", n.get("Läuft", 0), GRUEN), ("Ermüdet", n.get("Ermüdet", 0), GELB),
                                  ("Abfluss", n.get("Abfluss", 0), ROT)))
        + f'</div><p style="color:{TEXT_3};font-size:13px;margin:10px 0 0">Branchen: '
        + " · ".join(f"{k} {felder.get(k, 0)}" for k in FELD_TEXT) + f' · Titel: {zeile}</p>', oben=12, unten=8)


def stroemungskarte(erg, art):
    """Feld Stärke × Tempo der Gruppen einer Art; Pfeil vom Stand vor 4 Wochen bis heute."""
    gr = [g for g in erg["gruppen"] if g["art"] == art]
    if not gr:
        return seite(f'<p style="color:{TEXT_2}">Keine Gruppen.</p>')
    W, H, P = 1000, 560, 46
    xs = [p[0] for g in gr for p in g["weg"]] + [100]
    ys = [p[1] for g in gr for p in g["weg"]] + [100]
    dx = max(abs(min(xs) - 100), abs(max(xs) - 100), 2) * 1.08
    dy = max(abs(min(ys) - 100), abs(max(ys) - 100), 2) * 1.08

    def X(v):
        return P + (W - 2 * P) * (v - (100 - dx)) / (2 * dx)

    def Y(v):
        return P + (H - 2 * P) * (1 - (v - (100 - dy)) / (2 * dy))

    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;background:{KARTE};border:1px solid {RAND};'
         f'border-radius:12px" role="img" aria-label="Strömungskarte {art}">',
         '<defs><marker id="pf" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" '
         'orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.6"/>'
         '</marker></defs>']
    for x0, y0, x1, y1, feld in ((P, P, X(100), Y(100), "Erstarkend"), (X(100), P, W - P, Y(100), "Führend"),
                                  (P, Y(100), X(100), H - P, "Abgehängt"), (X(100), Y(100), W - P, H - P, "Ermüdend")):
        f = FELD_FARBE[feld]
        s.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{f}" fill-opacity="0.06"/>')
        tx = x0 + 10 if feld in ("Erstarkend", "Abgehängt") else x1 - 10
        anker = "start" if feld in ("Erstarkend", "Abgehängt") else "end"
        ty = y0 + 22 if feld in ("Erstarkend", "Führend") else y1 - 12
        s.append(f'<text x="{tx}" y="{ty}" fill="{f}" font-size="15" text-anchor="{anker}" font-weight="600">'
                 f'{FELD_TEXT[feld]}</text>')
    s.append(f'<line x1="{X(100)}" x2="{X(100)}" y1="{P}" y2="{H - P}" stroke="{RAND}"/>'
             f'<line x1="{P}" x2="{W - P}" y1="{Y(100)}" y2="{Y(100)}" stroke="{RAND}"/>')
    s.append(f'<text x="{W - P}" y="{H - 14}" fill="{TEXT_3}" font-size="12" text-anchor="end">Stärke gegen S&amp;P 500 →'
             f'</text><text x="{P}" y="{P - 14}" fill="{TEXT_3}" font-size="12">↑ Tempo (Stärke nimmt zu)</text>')
    beschriften = art == "Sektor" or len(gr) <= 14
    wichtig = sorted(gr, key=lambda g: -(abs(g["weg"][-1][1] - g["weg"][0][1]) + abs(g["weg"][-1][0] - g["weg"][0][0])))
    marke = {id(g) for g in wichtig[:12]} if not beschriften else {id(g) for g in gr}
    for g in gr:
        f = FELD_FARBE[g["feld"]]
        pts = " ".join(f"{X(a):.1f},{Y(b):.1f}" for a, b in g["weg"])
        s.append(f'<polyline points="{pts}" fill="none" stroke="{f}" stroke-opacity="0.55" stroke-width="1.4" '
                 f'marker-end="url(#pf)"/>')
        a, b = g["weg"][-1]
        s.append(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="{6 if art == "Sektor" else 4}" fill="{f}">'
                 f'<title>{t(g["name"])} · {g["feld"]} seit {g["seit_wochen"]} Wo. · Zufluss '
                 f'{zahl(g["zufluss"], 2) if g["zufluss"] else "–"}</title></circle>')
        if id(g) in marke:
            name = g["name"] if art != "Thema" else g["name"].split(" · ")[0]
            s.append(f'<text x="{X(a) + 8:.1f}" y="{Y(b) - 6:.1f}" fill="{TEXT}" font-size="12">{t(name[:34])}</text>')
    s.append("</svg>")
    return seite("".join(s), oben=4, unten=4)


def gruppen(erg, art):
    """Tabelle der Gruppen einer Art nach Geldfluss: Führend, Erstarkend (frisch zuerst), Schwächelnd, Zurückfallend."""
    reihen = []
    ordnung = {"Führend": 0, "Erstarkend": 1, "Ermüdend": 2, "Abgehängt": 3}
    for g in sorted((g for g in erg["gruppen"] if g["art"] == art),
                    key=lambda g: (ordnung[g["feld"]], g["seit_wochen"] if g["feld"] == "Erstarkend" else -g["staerke"])):
        z = g["zufluss"]
        reihen.append({"Feld": PUNKT[{"Führend": "grün", "Erstarkend": "grün", "Ermüdend": "gelb",
                                      "Abgehängt": "rot"}[g["feld"]]] + " " + FELD_TEXT[g["feld"]].split(" · ")[0],
                       art: g["name"], "seit Wochen": g["seit_wochen"],
                       "vor 4 Wochen": FELD_TEXT[g["feld_vor4"]].split(" · ")[0],
                       "Volumen-Zufluss": (("🟢 " if z >= 1.1 else "🔴 " if z < 0.9 else "🟡 ") + zahl(z, 2) + "-fach")
                       if z else "–", "Titel": g["anzahl"]})
    return pd.DataFrame(reihen)


def dreifach_liste(erg):
    return [(tk, x) for tk, x in erg["titel"].items()
            if x["stufe"] in ("Entsteht", "Läuft") and x["geld_ampel"] == "grün"
            and (x.get("zahlen") or {}).get("ampel") == "grün"]


def _termin(x, stand):
    z = x.get("zahlen") or {}
    d = pd.to_datetime(z.get("termin"), errors="coerce")
    if pd.isna(d):
        return "", False
    tage = (d - pd.Timestamp(stand)).days
    if tage < 0:                                 # Termin vorbei, die neuen Daten kommen mit dem nächsten Laden
        return "", False
    return f'{d:%d.%m.}' + (f" (in {tage} T.)" if 0 <= tage <= 60 else ""), 0 <= tage <= TERMIN_WARNUNG


def _reaktion(x):
    """Reaktion auf die letzten Zahlen mit Deutung (Episodic Pivot, Lücke mit Volumen, Abverkauf trotz Überraschung)."""
    r = (x.get("zahlen") or {}).get("reaktion")
    if not r:
        return ""
    teile = [f'{"+" if r["kurs"] >= 0 else "−"}{zahl(abs(r["kurs"]), 1)} %']
    if r.get("volumen"):
        teile.append(f'Volumen {zahl(r["volumen"], 1)}-fach')
    if r.get("ueberraschung") is not None:
        teile.append(f'Überraschung {"+" if r["ueberraschung"] >= 0 else "−"}{zahl(abs(r["ueberraschung"]), 1)} %')
    return f'{PUNKT[r.get("ampel", "grau")]} {r.get("deutung", "")} {pd.Timestamp(r["tag"]):%d.%m.}: ' + ", ".join(teile)


KURZ = {"Quartalsgewinn zum Vorjahr": "Gewinn", "Beschleunigung Gewinn": "Beschl.", "Umsatz": "Umsatz",
        "Marge": "Marge", "Überraschung": "Überr.", "Schätzungen (30 Tage)": "Schätz.",
        "Jahresgewinne 3 Jahre": "3 Jahre", "Eigenkapitalrendite": "ROE", "Institutionen": "Inst."}


def _punkte_html(x):
    """Die neun Zahlen-Punkte als kleine Ampeln, der Wert beim Überfahren mit der Maus."""
    pk = (x.get("zahlen") or {}).get("punkte") or {}
    if not pk:
        return ""
    return ('<div style="display:flex;flex-wrap:wrap;gap:4px 8px;margin-top:6px">'
            + "".join(f'<span title="{t(n)}: {t(w)}" style="font-size:12px;color:{TEXT_2};white-space:nowrap">'
                      f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:3px;'
                      f'background:{ {"grün": GRUEN, "gelb": GELB, "rot": ROT}.get(a, TEXT_3)}"></span>'
                      f'{KURZ.get(n, n)}</span>' for n, (a, w) in pk.items())
            + "</div>")


def _punkte_text(x):
    pk = (x.get("zahlen") or {}).get("punkte") or {}
    return " ".join(f'{PUNKT.get(a, "⚪")}{KURZ.get(n, n)}' for n, (a, _) in pk.items())


def dreifach(erg):
    """Karten: Kurs, Geld und Zahlen grün (Entsteht oder Läuft)."""
    liste = sorted(dreifach_liste(erg), key=lambda p: (p[1]["stufe"] != "Entsteht", -p[1]["tempo"]))
    if not liste:
        return seite(f'<p style="color:{TEXT_2}">Zurzeit kein Titel mit dreifachem Rückenwind.</p>', oben=4, unten=4)
    karten = []
    for tk, x in liste:
        termin, warn = _termin(x, erg["stand"])
        karten.append(
            f'<a href="?seite=Titelseite&t={tk}" target="_self" style="text-decoration:none">'
            f'<div style="background:{KARTE};border:1px solid {RAND};border-left:4px solid {GRUEN};border-radius:12px;'
            f'padding:12px 14px;min-height:150px">'
            f'<div style="display:flex;justify-content:space-between"><b style="color:{TEXT};font-size:18px">{tk}</b>'
            f'<span style="color:{BLAU if x["stufe"] == "Entsteht" else GRUEN};font-size:13px">{x["stufe"]}</span></div>'
            f'<div style="color:{TEXT_2};font-size:13px;margin:4px 0">RS {x["rang_vor4"]} → <b style="color:{TEXT}">'
            f'{x["rang"]}</b> ({"+" if x["tempo"] >= 0 else ""}{x["tempo"]} in 4 Wo.)'
            + (" · RS-Hoch vor Kurs" if x["rs_hoch_vor_kurs"] else "") + '</div>'
            f'<div style="color:{TEXT_2};font-size:13px">{t(x["sektor"])} · {t(x["branche"])}</div>'
            + (f'<div style="color:{TEXT_3};font-size:12px">Thema: {t(x["thema"][:60])}</div>' if x.get("thema") else "")
            + f'<div style="margin-top:6px;font-size:13px;color:{ROT if warn else TEXT_2}">'
            + (f'Zahlen {termin}' if termin else "Termin unbekannt") + (" ⚠" if warn else "") + '</div>'
            + (f'<div style="font-size:13px;color:{TEXT_2}">{_reaktion(x)}</div>' if _reaktion(x) else "")
            + _punkte_html(x) + '</div></a>')
    return seite('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px">'
                 + "".join(karten) + '</div>', oben=4, unten=4)


def stufe(erg, name):
    """Tabelle einer Stufe: Geld zuerst, dann Zahlen, dann Tempo."""
    rang = {"grün": 0, "gelb": 1, "rot": 2, "grau": 3, None: 3}
    liste = sorted(((tk, x) for tk, x in erg["titel"].items() if x["stufe"] == name),
                   key=lambda p: (rang[p[1]["geld_ampel"]], rang[(p[1].get("zahlen") or {}).get("ampel")],
                                  -p[1]["tempo"]))
    reihen = []
    for tk, x in liste:
        z = x.get("zahlen") or {}
        termin, warn = _termin(x, erg["stand"])
        reihen.append({"Titel": tk, "Kurs": PUNKT[x["kurs_ampel"]], "Geld": PUNKT[x["geld_ampel"]],
                       "Zahlen": PUNKT[z.get("ampel") or "grau"],
                       "RS": f'{x["rang_vor4"]} → {x["rang"]}', "Tempo": x["tempo"], "Beschl.": x["beschleunigung"],
                       "RS-Hoch vor Kurs": "✓" if x["rs_hoch_vor_kurs"] else "",
                       "Sektor": f'{x["sektor"]} ({x["sektor_feld"] or "–"})',
                       "Branche": f'{x["branche"]} ({x["branche_feld"] or "–"})',
                       "Thema": (x["thema"] or "").split(" · ")[0][:40],
                       "Zahlen am": ("⚠ " if warn else "") + termin, "letzte Zahlen": _reaktion(x),
                       "Zahlen im Einzelnen": _punkte_text(x)})
    return pd.DataFrame(reihen), [tk for tk, _ in liste]


def logbuch(erg, tage=28):
    """Offene Einträge (seit wann in der Stufe, Kurs seitdem) und Austritte der letzten Wochen – Beobachtung."""
    lb = erg.get("logbuch") or {}
    grenze = pd.Timestamp(erg["stand"]) - pd.Timedelta(days=tage)
    reihen = []
    for tk, e in lb.items():
        for x in e:
            offen = not x.get("bis")
            if not offen and pd.Timestamp(x["bis"]) < grenze:
                continue
            heute = (erg["titel"].get(tk) or {}).get("kurs")
            ende = heute if offen else x.get("kurs_bis")
            reihen.append({"Titel": tk, "Stufe": x["stufe"], "seit": f'{pd.Timestamp(x["seit"]):%d.%m.%Y}',
                           "bis": "" if offen else f'{pd.Timestamp(x["bis"]):%d.%m.%Y}',
                           "Kurs seit": x["kurs_seit"], "Kurs heute/bis": ende,
                           "Veränderung %": round((ende / x["kurs_seit"] - 1) * 100, 1) if ende and x["kurs_seit"]
                           else None})
    df = pd.DataFrame(reihen)
    if len(df):
        df = df.sort_values(["bis", "seit"], ascending=[True, False])
    return df
