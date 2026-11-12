"""Seite „Rückenwind“ (Modul rueckenwind_seite, Rechnung in kern/rueckenwind.py) (Konzept: KONZEPT_RUECKENWIND.md, 09.11.2026) – nur dieses Setup, getrennt von den Systemen.

Bausteine für app.py: kopf (Lage in Zahlen), wetterkarte (Feld je Gruppe in den letzten 5 Wochen, seit 10.11.2026),
gruppen (Tabelle nach Geldfluss), dreifach (Karten: Kurs, Geld und Zahlen grün), stufe (Tabelle je Stufe), logbuch.
Daten: kern/rueckenwind.py (Nachtlauf).
"""
import os
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))

from gestaltung import BLAU, GELB, GRUEN, KARTE, RAND, ROT, TEXT, TEXT_2, TEXT_3, seite, t, zahl  # noqa: E402

ZUFLUSS = (1.1, 0.9)
FELD_FARBE = {"Führend": GRUEN, "Erstarkend": BLAU, "Ermüdend": GELB, "Abgehängt": ROT}
def _fn(f):
    return FELD_TEXT[f].split(" · ")[0] if f in FELD_TEXT else f


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
    None: "Gerechnet, aber zurzeit in keiner Stufe – zur Vollständigkeit, nichts weggelassen. Unten grau die Titel, "
          "die sich nicht rechnen lassen (mit Grund). „jung n M“ = weniger als 14 Monate an der Börse: RS-Rang aus den "
          "vorhandenen Quartalen, RS-Hoch seit dem Börsengang.",
}
PUNKT = {"grün": "🟢", "gelb": "🟡", "rot": "🔴", "grau": "⚪"}
TERMIN_WARNUNG = 14


def _chip(text, farbe):
    return (f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;border:1px solid {farbe};'
            f'color:{farbe};font-size:13px;margin:2px 4px 2px 0">{t(text)}</span>')


def kopf(erg, titel=True):
    """Kopf des Rückenwinds: Stand, Zähler je Stufe, dreifacher Rückenwind. titel=False: ohne eigene Überschrift
    (Seite Rückenwind mit Übersicht seit 10.11.2026 – die Überschrift steht dort ganz oben)."""
    from collections import Counter
    n = Counter(x["stufe"] for x in erg["titel"].values())
    drei = len(dreifach_liste(erg))
    felder = Counter(g["feld"] for g in erg["gruppen"] if g["art"] == "Branche")
    zeile = " · ".join(f"{s} {n.get(s, 0)}" for s in ("Entsteht", "Läuft", "Ermüdet", "Abfluss"))
    return seite(
        '<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
        + (f'<h1 style="margin:0;font-size:30px;color:{TEXT}">Rückenwind</h1>' if titel else '<span></span>')
        + f'<div style="color:{TEXT_2};font-size:14px">Stand {pd.Timestamp(erg["stand"]):%d.%m.%Y} · '
        f'{len(erg["titel"])} Titel gerechnet'
        + (f' · {len(erg.get("ohne_daten") or [])} ohne Daten' if erg.get("ohne_daten") else "")
        + '</div></div>'
        f'<p style="color:{TEXT_2};font-size:15px;margin:8px 0 14px">Kurs, Geld und Zahlen: RS-Dynamik des Titels, '
        f'Geldfluss in Sektor, Branche und Thema (zwei von drei vorne = grün), Fundament – eigenes Setup der Strömung, '
        f'getrennt von den sieben Setups der Stellung (Seite Setups, ②). '
        f'Ampeln, nichts gefiltert.</p>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px">'
        + "".join(f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:12px 16px;'
                  f'min-width:150px"><div style="color:{TEXT_2};font-size:13px">{k}</div>'
                  f'<div style="color:{f};font-size:26px;font-weight:600">{v}</div></div>'
                  for k, v, f in (("Dreifacher Rückenwind", drei, GRUEN), ("Entsteht", n.get("Entsteht", 0), BLAU),
                                  ("Läuft", n.get("Läuft", 0), GRUEN), ("Ermüdet", n.get("Ermüdet", 0), GELB),
                                  ("Abfluss", n.get("Abfluss", 0), ROT)))
        + f'</div><p style="color:{TEXT_3};font-size:13px;margin:10px 0 0">Branchen: '
        + " · ".join(f"{FELD_TEXT[k].split(' · ')[0]} {felder.get(k, 0)}" for k in FELD_TEXT) + f' · Titel: {zeile}</p>', oben=12, unten=8)


def _name(g):
    """Deutscher Name der Gruppe; Themen tragen die Namen ihrer Mitglieder – dort der erste Teil."""
    if g["art"] == "Branche":
        try:
            import namen_de
            return namen_de.branche(g["name"]) or g["name"]
        except Exception:  # noqa: BLE001
            return g["name"]
    return g["name"].split(" · ")[0] if g["art"] == "Thema" else g["name"]


def _wochenfeld(punkt):
    import sektoren
    return sektoren.feld(punkt[0], punkt[1])


_SETUPS = {}


def setups():
    """Reihe jedes Titels im jüngsten Kartentisch als Klartext ({Ticker: „VCP · Enge grün“}); einmal je Tisch gelesen."""
    import kartentisch
    try:
        neu = max((f for f in os.listdir(kartentisch.SPEICHER) if f.endswith(".json")), default=None)
        stempel = (neu, os.path.getmtime(os.path.join(kartentisch.SPEICHER, neu))) if neu else None
    except OSError:
        return {}
    if _SETUPS.get("stempel") != stempel:
        namen = {k: n for k, n, _ in kartentisch.REIHEN} | kartentisch.ALTE_REIHEN
        tisch = kartentisch.laden() or {}
        _SETUPS.update(stempel=stempel, werte={tk: namen.get(x.get("reihe"), x.get("reihe"))
                                               for tk, x in (tisch.get("titel") or {}).items() if x.get("reihe")})
    return _SETUPS["werte"]


def _mitglieder(erg, art, g, setup, drei):
    """Die Titel einer Gruppe als aufklappbare Liste (10.11.2026): nach RS-Rang, mit Stufe, Tempo, Setup und Link.
    Knapp gehalten (Stil einmal in MITGLIEDER_STIL), damit die Wetterkarte mit allen Titeln schnell lädt."""
    feld = {"Sektor": "sektor", "Branche": "branche", "Thema": "thema"}[art]
    liste = sorted(((tk, x) for tk, x in erg["titel"].items() if x.get(feld) == g["name"]), key=lambda p: -p[1]["rang"])
    if not liste:
        return '<div class="mg"><i>keine Titel mit Daten</i></div>'
    zeilen = []
    for tk, x in liste:
        stufe = x.get("stufe")
        s_ = setup.get(tk)
        zeilen.append(f'<div><b>{"◆ " if x.get("watchlist") else ""}{tk}{" ▲▲▲" if tk in drei else ""}</b>'
                      f'<span class="s{STUFEN_KURZ.get(stufe, "")}">{stufe or "–"}</span><span>{x["rang"]}</span>'
                      f'<span>{"+" if x["tempo"] >= 0 else ""}{x["tempo"]}</span>'
                      f'<span{"" if s_ else " class=o"}>{t(s_) if s_ else "kein Setup"}</span>'
                      f'<a href="?seite=Titelseite&t={tk}" target="_blank">Titelseite →</a></div>')
    return ('<div class="mg"><div class="k"><span>Titel</span><span>Stufe</span><span>RS-Rang</span><span>Tempo</span>'
            '<span>Setup (Kartentisch)</span><span></span></div>' + "".join(zeilen)
            + '<p>nach RS-Rang · Tempo = RS-Rang heute gegen vor 4 Wochen · ◆ Watchlist · ▲▲▲ dreifacher Rückenwind</p></div>')


STUFEN_KURZ = {"Entsteht": "e", "Läuft": "l", "Ermüdet": "m", "Abfluss": "a"}
MITGLIEDER_STIL = (
    f"<style>.mg{{margin:4px 0 12px 12px;padding:8px 12px;border-left:2px solid {RAND};font-size:13px}}"
    f".mg>div{{display:grid;grid-template-columns:110px 90px 70px 80px 1fr 90px;gap:8px;align-items:center;"
    f"padding:3px 0;border-bottom:1px dotted {RAND};color:{TEXT_2}}}"
    f".mg>div.k{{font-size:11px;color:{TEXT_3};border:0}}.mg b{{color:{TEXT}}}.mg a{{color:{BLAU};text-decoration:none}}"
    f".mg .se{{color:{BLAU}}}.mg .sl{{color:{GRUEN}}}.mg .sm{{color:{GELB}}}.mg .sa{{color:{ROT}}}.mg .o,.mg i{{color:{TEXT_3}}}"
    f".mg p{{color:{TEXT_3};font-size:12px;margin:6px 0 0}}.wk summary{{list-style:none}}"
    f".wk summary::-webkit-details-marker{{display:none}}</style>")


def wetterkarte(erg, art):
    """Wetterkarte der Strömung (10.11.2026, ersetzt die Punktwolke): je Gruppe eine Zeile mit dem Feld der letzten
    fünf Wochen als Kästchen, der Lage heute in Worten und dem Geldfluss. Alle Gruppen, geordnet nach Feld heute –
    Erstarkend zuerst (dort entsteht die Strömung), dann Führend offen, Schwächelnd und Zurückfallend zugeklappt."""
    ordnung = ("Erstarkend", "Führend", "Ermüdend", "Abgehängt")
    gr = [g for g in erg["gruppen"] if g["art"] == art]
    setup, drei = setups(), {tk for tk, _ in dreifach_liste(erg)}
    kopf = (f'<div style="display:grid;grid-template-columns:minmax(140px,260px) repeat(5,30px) 1fr 120px;gap:6px;'
            f'font-size:11px;color:{TEXT_3};padding:0 0 4px">'
            f'<span>{art}</span><span>−4</span><span>−3</span><span>−2</span><span>−1</span><span>heute</span>'
            f'<span>Lage</span><span>Geld</span></div>')
    teile = []
    for feld in ordnung:
        liste = sorted((g for g in gr if g["feld"] == feld),
                       key=lambda g: (g["seit_wochen"], -g["schwung"]) if feld == "Erstarkend" else (-g["staerke"],))
        zeilen = []
        for g in liste:
            kaestchen = "".join(f'<span title="{FELD_TEXT[_wochenfeld(p)].split(" · ")[0]}" style="height:20px;'
                                f'border-radius:4px;background:{FELD_FARBE[_wochenfeld(p)]}"></span>' for p in g["weg"])
            seit = g["seit_wochen"]
            wort = FELD_TEXT[feld].split(" · ")[0].lower()
            lage = ("neu " + wort if seit == 1 else f"seit {seit} Wochen {wort}")
            if g.get("stabil"):
                lage += " · ◇ stabil"
            z = g.get("zufluss")
            if z:
                fz, wz = ((GRUEN, "rein") if z >= ZUFLUSS[0] else (ROT, "raus") if z < ZUFLUSS[1] else (TEXT_2, "gleich"))
                geld = (f'<span style="border:1px solid {fz};color:{fz};border-radius:6px;padding:1px 8px;'
                        f'font-size:13px;text-align:center">{wz} {zahl(z, 2)}×</span>')
            else:
                geld = f'<span style="color:{TEXT_3}">–</span>'
            info = (f'{_name(g)} · {g["anzahl"]} Titel · Stärke {zahl(g["staerke"], 1)} · Tempo {zahl(g["schwung"], 1)} · '
                    f'Rückschlag 8 Wochen {zahl(g.get("rueckschlag"), 1)} %'
                    + (f' · Mitglieder: {g["name"]}' if art == "Thema" else ""))
            zeilen.append(f'<details><summary title="{t(info)}" style="display:grid;cursor:pointer;'
                          f'grid-template-columns:minmax(140px,260px) repeat(5,30px) 1fr 120px;gap:6px;'
                          f'align-items:center;padding:5px 0;border-bottom:1px solid {RAND};font-size:15px">'
                          f'<span style="color:{TEXT};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                          f'{t(_name(g))} <span style="color:{BLAU};font-size:12px;border:1px solid {RAND};'
                          f'border-radius:6px;padding:0 5px">{g["anzahl"]} ▾</span></span>'
                          f'{kaestchen}<span style="color:{TEXT_2};font-size:14px">{lage}</span>{geld}</summary>'
                          f'{_mitglieder(erg, art, g, setup, drei)}</details>')
        if not zeilen:
            continue
        titel_ = (f'<span style="color:{FELD_FARBE[feld]};font-weight:600;font-size:16px">{FELD_TEXT[feld]}</span>'
                  f'<span style="color:{TEXT_3};font-size:13px"> · {len(zeilen)}</span>')
        offen = " open" if feld in ("Erstarkend", "Führend") else ""
        teile.append(f'<details{offen} style="margin:10px 0"><summary style="cursor:pointer;padding:4px 0">{titel_}'
                     f'</summary><div style="margin-top:6px">{kopf}{"".join(zeilen)}</div></details>')
    legende_ = " · ".join(f'<span style="color:{FELD_FARBE[f]}">■</span> {FELD_TEXT[f].split(" · ")[0]}' for f in ordnung)
    return seite(MITGLIEDER_STIL + f'<div class="wk" style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:14px 18px">'
                 + "".join(teile)
                 + f'<div style="color:{TEXT_3};font-size:13px;margin-top:8px">{legende_} · je Kästchen eine Woche · '
                   f'Geld = Volumen an Kauf- gegen Abgabetagen der letzten 4 Wochen · Zahl hinter dem Namen = Titel im Revier, '
                   f'Klick auf die Zeile zeigt sie · Zahlen beim Darüberfahren</div>'
                 + "</div>", oben=8, unten=8)


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
                       "stabil": "◇ stabil" if g.get("stabil") else "",
                       "Rückschlag 8 Wo. %": g.get("rueckschlag"),
                       "vor 4 Wochen": FELD_TEXT[g["feld_vor4"]].split(" · ")[0],
                       "Volumen-Zufluss": (("🟢 " if z >= ZUFLUSS[0] else "🔴 " if z < ZUFLUSS[1] else "🟡 ")
                                           + zahl(z, 2) + "-fach")
                       if z else "–", "Titel": g["anzahl"]})
    return pd.DataFrame(reihen)


def _rs_linie(x):
    """Steigung der RS-Linie in 4 Wochen und davor, z. B. „+6,2 % (davor +1,1 %)“."""
    a, b = x.get("rs_tempo"), x.get("rs_vortempo")
    if a is None:
        return ""
    f = lambda v: f'{"+" if v >= 0 else "−"}{zahl(abs(v), 1)} %'   # noqa: E731
    return f(a) + (f" (davor {f(b)})" if b is not None else "")


def _zufluss(z):
    if not z:
        return ""
    return ("🟢 " if z >= ZUFLUSS[0] else "🔴 " if z < ZUFLUSS[1] else "🟡 ") + zahl(z, 2) + "-fach"


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
            f'<div style="color:{TEXT_2};font-size:13px">RS-Linie {_rs_linie(x)} · Volumen {_zufluss(x.get("zufluss"))}</div>'
            f'<div style="color:{TEXT_2};font-size:13px">{t(x["sektor"])}{" ◇" if x.get("sektor_stabil") else ""} · '
            f'{t(x["branche"])}{" ◇" if x.get("branche_stabil") else ""}</div>'
            + (f'<div style="color:{TEXT_3};font-size:12px">Thema: {t(x["thema"][:60])}</div>' if x.get("thema") else "")
            + f'<div style="margin-top:6px;font-size:13px;color:{ROT if warn else TEXT_2}">'
            + (f'Zahlen {termin}' if termin else "Termin unbekannt") + (" ⚠" if warn else "") + '</div>'
            + (f'<div style="font-size:13px;color:{TEXT_2}">{_reaktion(x)}</div>' if _reaktion(x) else "")
            + _punkte_html(x) + '</div></a>')
    return seite('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px">'
                 + "".join(karten) + '</div>', oben=4, unten=4)


def _zeile(tk, x, stand):
    """Eine Tabellenzeile eines Titels (Stufen, Anführer, Verfolger)."""
    z = x.get("zahlen") or {}
    termin, warn = _termin(x, stand)
    return {"Titel": tk + (" ◆" if x.get("watchlist") else "") + (f' · jung {x["jung"]} M' if x.get("jung") else ""),
            "Kurs": PUNKT[x["kurs_ampel"]], "Geld": PUNKT[x["geld_ampel"]],
            "Zahlen": PUNKT[z.get("ampel") or "grau"],
            "RS": f'{x["rang_vor4"]} → {x["rang"]}', "Tempo": x["tempo"], "Beschl.": x["beschleunigung"],
            "RS-Hoch vor Kurs": "✓" if x["rs_hoch_vor_kurs"] else "",
            "RS-Linie 4 Wo.": _rs_linie(x), "Volumen-Zufluss": _zufluss(x.get("zufluss")),
            "Sektor": f'{x["sektor"]} ({_fn(x["sektor_feld"]) or "–"}{", stabil" if x.get("sektor_stabil") else ""})',
            "Branche": f'{x["branche"]} ({_fn(x["branche_feld"]) or "–"}{", stabil" if x.get("branche_stabil") else ""})',
            "Thema": (x["thema"] or "").split(" · ")[0][:40],
            "Zahlen am": ("⚠ " if warn else "") + termin, "letzte Zahlen": _reaktion(x),
            "Zahlen im Einzelnen": _punkte_text(x)}


def stufe(erg, name):
    """Tabelle einer Stufe: Geld zuerst, dann Zahlen, dann Tempo."""
    rang = {"grün": 0, "gelb": 1, "rot": 2, "grau": 3, None: 3}
    liste = sorted(((tk, x) for tk, x in erg["titel"].items() if x["stufe"] == name),
                   key=lambda p: (rang[p[1]["geld_ampel"]], rang[(p[1].get("zahlen") or {}).get("ampel")],
                                  -p[1]["tempo"]))
    reihen = [_zeile(tk, x, erg["stand"]) for tk, x in liste]
    tks = [tk for tk, _ in liste]
    if name is None:                            # nicht rechenbar: grau mit Grund, damit nichts still fehlt
        for o in erg.get("ohne_daten") or []:
            reihen.append({"Titel": o["tk"] + (" ◆" if o.get("watchlist") else ""), "Kurs": PUNKT["grau"],
                           "Geld": PUNKT["grau"], "Zahlen": PUNKT["grau"], "Zahlen im Einzelnen": o["grund"]})
            tks.append(o["tk"])
    return pd.DataFrame(reihen), tks


SPITZE = 25
SCHNELL_TEXT = {
    "Anführer": "Die 25 Titel mit dem höchsten RS-Rang, deren Tempo hält (Stufe Läuft) – bei gleichem Rang der "
                "stärkere Volumen-Zufluss zuerst. Die Vorhut, die schon an der Front steht.",
    "Verfolger": "Die 25 Titel, die in 4 Wochen am meisten Rang gewonnen haben und dabei schneller werden "
                 "(Beschleunigung positiv), noch unter Rang 85. Die Einheiten, die gerade am schnellsten nachrücken.",
}


def schnell(erg, art):
    """Schnellsuche (09.11.2026): Anführer = Top 25 nach RS-Rang in Stufe Läuft; Verfolger = Top 25 nach Tempo mit
    positiver Beschleunigung unter Rang 85. Nur eine Sicht – die Listen nach Stufe bleiben vollständig."""
    t = erg["titel"].items()
    if art == "Anführer":
        liste = sorted(((tk, x) for tk, x in t if x["stufe"] == "Läuft"),
                       key=lambda p: (-p[1]["rang"], -(p[1].get("zufluss") or 0)))[:SPITZE]
    else:
        liste = sorted(((tk, x) for tk, x in t if x["rang"] < 85 and x["beschleunigung"] > 0),
                       key=lambda p: (-p[1]["tempo"], -p[1]["beschleunigung"]))[:SPITZE]
    return pd.DataFrame([_zeile(tk, x, erg["stand"]) for tk, x in liste]), [tk for tk, _ in liste]


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
