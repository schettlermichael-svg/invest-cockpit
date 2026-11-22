"""Seite „Rückenwind“ (Modul rueckenwind_seite, Rechnung in kern/rueckenwind.py) (Konzept: KONZEPT_RUECKENWIND.md, 09.11.2026) – nur dieses Setup, getrennt von den Systemen.

Bausteine für app.py: kopf (Lage in Zahlen), wetterkarte (Feld je Gruppe in den letzten 5 Wochen, seit 10.11.2026),
gruppen (Tabelle nach Geldfluss), liste (alle Titel in der Rangfolge des Rückenwinds, 21.11.2026).
Daten: kern/rueckenwind.py (Nachtlauf).
"""
import os
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))

from gestaltung import BLAU, GELB, GRUEN, KARTE, RAND, ROT, TEXT, TEXT_2, TEXT_3, seite, t, zahl  # noqa: E402

from rueckenwind import ANGRIFF_KLASSEN, KLASSEN, ZUFLUSS, abstand_wort, klasse, laden, richtung  # noqa: E402  eine Quelle (rueckenwind)
FELD_FARBE = {"Führend": GRUEN, "Erstarkend": BLAU, "Ermüdend": GELB, "Abgehängt": ROT}
# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
KOPF_SCHRIFT = 12        # Schriftgröße der Kopfzeile
KOPF_ABSTAND = 8         # Abstand der Kopfzeile
KARTE_RAND = 8           # Rand der Wetterkarte
TERMIN_TAGE_ZEIGEN = 60  # „in n T.“ zeigen bis 60 Tage
THEMA_ZEICHEN = 40       # Thema in der Tabelle: höchstens 40 Zeichen


def _fn(f):
    return FELD_TEXT[f].split(" · ")[0] if f in FELD_TEXT else f


FELD_TEXT = {"Führend": "Führend · Geld ist drin", "Erstarkend": "Erstarkend · Geld fließt zu",
             "Ermüdend": "Schwächelnd · Geld fließt ab", "Abgehängt": "Zurückfallend · Geld ist weg"}
PUNKT = {"grün": "🟢", "gelb": "🟡", "rot": "🔴", "grau": "⚪"}


def _chip(text, farbe):
    return (f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;border:1px solid {farbe};'
            f'color:{farbe};font-size:13px;margin:2px 4px 2px 0">{t(text)}</span>')


def kopf(erg, titel=True):
    """Kopf des Rückenwinds: Stand, Zähler je Klasse der Schlachtordnung, dreifacher Rückenwind. titel=False: ohne eigene Überschrift
    (Seite Rückenwind mit Übersicht seit 10.11.2026 – die Überschrift steht dort ganz oben)."""
    from collections import Counter
    n = Counter(klasse(x) for x in erg["titel"].values())
    drei = len(dreifach_liste(erg))
    felder = Counter(g["feld"] for g in erg["gruppen"] if g["art"] == "Branche")
    return seite(
        '<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
        + (f'<h1 style="margin:0;font-size:30px;color:{TEXT}">Rückenwind</h1>' if titel else '<span></span>')
        + f'<div style="color:{TEXT_2};font-size:14px">Stand {pd.Timestamp(erg["stand"]):%d.%m.%Y} · '
        f'{len(erg["titel"])} Titel gerechnet'
        + (f' · {len(erg.get("ohne_daten") or [])} ohne Daten' if erg.get("ohne_daten") else "")
        + '</div></div>'
        f'<p style="color:{TEXT_2};font-size:15px;margin:8px 0 14px">Kurs, Geld und Zahlen: RS-Dynamik des Titels, '
        f'Geldfluss in Sektor, Branche und Thema (zwei von drei vorne und keine schwächelnd = grün), Fundament – eigenes Setup der Strömung, '
        f'getrennt von den Setups des Kartentischs. '
        f'Ampeln, nichts gefiltert.</p>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px">'
        + "".join(f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:12px 16px;'
                  f'min-width:150px"><div style="color:{TEXT_2};font-size:13px">{k}</div>'
                  f'<div style="color:{f};font-size:26px;font-weight:600">{v}</div></div>'
                  for k, v, f in (("Dreifacher Rückenwind", drei, GRUEN),
                                  *((f"{i} · {name}", n.get(i, 0), KLASSEN_FARBE[i - 1])
                                    for i, name in enumerate(KLASSEN, 1))))
        + f'</div><p style="color:{TEXT_3};font-size:13px;margin:10px 0 0">Branchen: '
        + " · ".join(f"{FELD_TEXT[k].split(' · ')[0]} {felder.get(k, 0)}" for k in FELD_TEXT) + '</p>', oben=KOPF_SCHRIFT, unten=KOPF_ABSTAND)


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
    """Die Titel einer Gruppe als aufklappbare Liste (10.11.2026): nach RS-Rang, mit Klasse, Tempo, Setup und Link.
    Knapp gehalten (Stil einmal in MITGLIEDER_STIL), damit die Wetterkarte mit allen Titeln schnell lädt."""
    feld = {"Sektor": "sektor", "Branche": "branche", "Thema": "thema"}[art]
    liste = sorted(((tk, x) for tk, x in erg["titel"].items() if x.get(feld) == g["name"]), key=lambda p: -p[1]["rang"])
    if not liste:
        return '<div class="mg"><i>keine Titel mit Daten</i></div>'
    zeilen = []
    for tk, x in liste:
        k = klasse(x)
        s_ = setup.get(tk)
        zeilen.append(f'<div><b>{"◆ " if x.get("watchlist") else ""}{tk}{" ▲▲▲" if tk in drei else ""}</b>'
                      f'<span class="k{k or ""}">{f"{k} · {KLASSEN[k - 1]}" if k else "–"}</span><span>{x["rang"]}</span>'
                      f'<span>{"+" if x["tempo"] >= 0 else ""}{x["tempo"]}</span>'
                      f'<span{"" if s_ else " class=o"}>{t(s_) if s_ else "kein Setup"}</span>'
                      f'<a href="?seite=Titelseite&t={tk}" target="_blank">Titelseite →</a></div>')
    return ('<div class="mg"><div class="k"><span>Titel</span><span>Klasse</span><span>RS-Rang</span><span>Tempo</span>'
            '<span>Setup (Kartentisch)</span><span></span></div>' + "".join(zeilen)
            + '<p>nach RS-Rang · Tempo = RS-Rang heute gegen vor 4 Wochen · ◆ Watchlist · ▲▲▲ dreifacher Rückenwind</p></div>')


KLASSEN_FARBE = (GRUEN, GRUEN, GELB, ROT, ROT)   # Garde, Angriff grün · Vorhut gelb · Ohne Nachschub, Rückzug rot
MITGLIEDER_STIL = (
    f"<style>.mg{{margin:4px 0 12px 12px;padding:8px 12px;border-left:2px solid {RAND};font-size:13px}}"
    f".mg>div{{display:grid;grid-template-columns:110px 140px 70px 80px 1fr 90px;gap:8px;align-items:center;"
    f"padding:3px 0;border-bottom:1px dotted {RAND};color:{TEXT_2}}}"
    f".mg>div.k{{font-size:11px;color:{TEXT_3};border:0}}.mg b{{color:{TEXT}}}.mg a{{color:{BLAU};text-decoration:none}}"
    + "".join(f".mg .k{i}{{color:{f}}}" for i, f in enumerate(KLASSEN_FARBE, 1)) + f".mg .o,.mg i{{color:{TEXT_3}}}"
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
            if g.get("breite") is not None:          # folgen die Schwestern (13.11.2026)
                lage += f' · Breite {zahl(g["breite_vor4"], 0) if g.get("breite_vor4") is not None else "–"} → ' \
                        f'{zahl(g["breite"], 0)} %'
            if g.get("vorne"):
                lage += f' · vorne {g["vorne"][0]} von {g["vorne"][1]}'
            import auktion
            import zustandsbild
            lage = zustandsbild.pille(auktion.gruppe(g), klein=True, mit_belegen=True) + " " + t(lage)
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
                   f'Geld = Volumen an Kauf- gegen Abgabetagen der letzten 50 Handelstage (Up/Down-Volumen nach O’Neil) · Zahl hinter dem Namen = Titel im Revier, '
                   f'Klick auf die Zeile zeigt sie · Zahlen beim Darüberfahren</div>'
                 + "</div>", oben=KARTE_RAND, unten=KARTE_RAND)


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


def _zufluss(z, trocken=False):
    """Volumen-Zufluss als Ampel; austrocknendes Volumen ist grün (Minervini: kaum noch Verkäufer, Micky 22.11.2026)."""
    if trocken:
        return "🟢 🏜️ trocken" + (f" · {zahl(z, 2)}-fach" if z else "")
    if not z:
        return ""
    return ("🟢 " if z >= ZUFLUSS[0] else "🔴 " if z < ZUFLUSS[1] else "🟡 ") + zahl(z, 2) + "-fach"


def dreifach_liste(erg):
    return [(tk, x) for tk, x in erg["titel"].items()
            if klasse(x) in ANGRIFF_KLASSEN and x["geld_ampel"] == "grün"
            and (x.get("zahlen") or {}).get("ampel") == "grün"]


def _termin(x, stand):
    z = x.get("zahlen") or {}
    d = pd.to_datetime(z.get("termin"), errors="coerce")
    if pd.isna(d):
        return "", False
    tage = (d - pd.Timestamp(stand)).days
    if tage < 0:                                 # Termin vorbei, die neuen Daten kommen mit dem nächsten Laden
        return "", False
    import gestaltung
    amp = gestaltung.termin_ampel(tage)             # eine Regel für die App: bis 7 Tage rot, bis 14 gelb
    return f'{d:%d.%m.}' + (f" (in {tage} T.)" if 0 <= tage <= TERMIN_TAGE_ZEIGEN else ""), (amp if amp in ("rot", "gelb") else False)


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


def _punkte_text(x):
    pk = (x.get("zahlen") or {}).get("punkte") or {}
    return " ".join(f'{PUNKT.get(a, "⚪")}{KURZ.get(n, n)}' for n, (a, _) in pk.items())


PFEIL = {"steigt schneller": "⏫", "dreht nach oben": "↗️", "steigt": "⬆️", "dreht nach unten": "↘️", "fällt": "⬇️"}
HOCH_PUNKT = {"nah": "🟢", "mittel": "🟡", "fern": "🔴"}


def _richtung(x):
    """Gespeichert seit 21.11.2026; ältere Stände rechnen sie aus der Steigung nach."""
    return x.get("richtung") or richtung(x.get("rs_tempo"), x.get("rs_vortempo"))


AMPEL_ORDNUNG = {"grün": 0, "gelb": 1, "rot": 2}


def _ordnung(x):
    """Schlachtordnung (Micky 21.11.2026): Klasse aus Front und Truppen; in der Klasse 🦈 zuerst, dann das Geld der
    Branche (Einzelkämpfer hinter Titeln mit gleicher Ampel), dann die Zahlen, dann der Rang als Kraft."""
    k = klasse(x)
    return (k or len(KLASSEN) + 1, not x.get("rs_hoch_vor_kurs"), AMPEL_ORDNUNG.get(x.get("geld_ampel"), len(AMPEL_ORDNUNG)),
            bool(x.get("einzelkaempfer")), AMPEL_ORDNUNG.get((x.get("zahlen") or {}).get("ampel"), len(AMPEL_ORDNUNG)),
            -x["rang"])


def titel_zeile(tk):
    """Rückenwind eines Titels für den Kopf der Titelseite (Micky 22.11.2026): dieselben Zeichen wie in der Liste,
    als Liste von Teilen; leer ohne Stand des Nachtlaufs."""
    erg = laden() or {}
    x = (erg.get("titel") or {}).get(tk)
    if not x:
        return []
    k, r, ab = klasse(x), _richtung(x), x.get("abstand_hoch")
    wort, z = abstand_wort(ab), x.get("zahlen") or {}
    termin, warn = _termin(x, erg["stand"])
    return [f"{k} · {KLASSEN[k - 1]}" if k else "ohne Klasse",
            *(["🦈 RS-Hoch vor Kurs"] if x.get("rs_hoch_vor_kurs") else []),
            f'RS-Linie {PFEIL.get(r, "")} {r or "–"} {_rs_linie(x)}'.strip(),
            f'Rang {x["rang_vor4"]} → {x["rang"]}',
            "Volumen " + (_zufluss(x.get("zufluss"), x.get("trocken")) or "–"),
            *([f"Hoch {HOCH_PUNKT[wort]} {wort} −{zahl(ab, 0)} %"] if wort else []),
            "Geld " + PUNKT[x["geld_ampel"]] + (" 🐺 Einzelkämpfer" if x.get("einzelkaempfer") else ""),
            *(["Momentum " + _momentum(x)] if x.get("momentum") else []),
            "Zahlen " + PUNKT[z.get("ampel") or "grau"]
            + (f' · am {("🔴 " if warn == "rot" else "🟡 " if warn else "")}{termin}' if termin else "")]


def bahn(fr, wort=" freie Bahn"):
    """✈️ freie Bahn (Livermore: Linie des geringsten Widerstands) aus zonen.frei: keine Festung über dem Kurs,
    ✈️↓ keine darunter; sonst leer. In der Liste ohne Wort (wort=""), die Spalte heißt schon „Bahn“."""
    return " ".join(z + wort for z, ja in (("✈️", (fr or {}).get("oben")), ("✈️↓", (fr or {}).get("unten"))) if ja)


def _momentum(x):
    """Momentum nach Kullamägi: Rendite über 1, 3, 6 Monate; 🚀 = unter den besten 2 % des Reviers."""
    m = x.get("momentum") or {}
    return " · ".join(f'{"🚀 " if top else ""}{k} {"+" if r > 0 else ""}{zahl(r, 0)} %' for k, (r, top) in m.items())


def _zirkel(tk, kreis):
    """(Phase, Keim) für die Liste aus dem gespeicherten Kreislauf (zeichen.laden)."""
    import zeichen
    z = zeichen.zirkel((kreis.get("titel") or {}).get(tk))
    if not z:
        return "–", ""
    phase = (f'{z["phase"]} {z["name"]}' + (f' · {z["wochen"]} Wo.' if z["wochen"] else "")
             + (f' → {z["ziel"]}' if z["ziel"] else "")) if z["phase"] else "jung"
    if not z["keim"]:
        return phase, ""
    zeichen_ = "🌱" if zeichen.KEIM_SEITE.get(z["phase"]) == "stärke" else "🍂"
    return phase, f'{zeichen_} ' + ", ".join(dict.fromkeys(zeichen.kurz(t) for t in z["keim"][:3]))


def _link(tk, text):
    """Titel als Verweis auf seine Titelseite (Micky 22.11.2026: Titel anklicken → Titelseite); die App zeigt nach
    TITEL_TEXT nur den Text hinter „&z=“."""
    return f"?seite=Titelseite&t={tk}&z={text}"


TITEL_TEXT = r"&z=(.*)$"


def liste(erg, nur_watchlist=False):
    """Alle Titel in der Rangfolge des Rückenwinds, nichts gefiltert; ohne Daten grau am Ende mit Grund. Umschalter
    (Micky 21.11.2026): nur_watchlist zeigt nur die Titel der Watchlist (◆). → DataFrame."""
    import zeichen
    reihen, kreis = [], zeichen.laden()
    for tk, x in sorted(erg["titel"].items(), key=lambda p: _ordnung(p[1])):
        if nur_watchlist and not x.get("watchlist"):
            continue
        z = x.get("zahlen") or {}
        termin, warn = _termin(x, erg["stand"])
        ab = x.get("abstand_hoch")
        wort = abstand_wort(ab)
        r = _richtung(x)
        k = klasse(x)
        phase, keim = _zirkel(tk, kreis)
        reihen.append({
            "Klasse": f"{k} · {KLASSEN[k - 1]}" if k else "–",
            "Titel": _link(tk, tk + (" ◆" if x.get("watchlist") else "") + (f' · jung {x["jung"]} M' if x.get("jung") else "")),
            "Phase": phase, "Keim": keim,
            "RS-Hoch vor Kurs": "🦈" if x["rs_hoch_vor_kurs"] else "",
            "RS-Linie": f'{PFEIL.get(r, "")} {r or "–"}', "Steigung 4 Wo.": _rs_linie(x),
            "Momentum": _momentum(x), "Rang (Kraft)": f'{x["rang_vor4"]} → {x["rang"]}',
            "Volumen": _zufluss(x.get("zufluss"), x.get("trocken")),
            "Hoch": f'{HOCH_PUNKT[wort]} {wort} −{zahl(ab, 0)} %' if wort else "–",
            "Bahn": bahn(x.get("frei"), ""),
            "Geld": PUNKT[x["geld_ampel"]] + (" 🐺 Einzelkämpfer" if x.get("einzelkaempfer") else ""),
            "Sektor": f'{x["sektor"]} ({_fn(x["sektor_feld"]) or "–"}{", stabil" if x.get("sektor_stabil") else ""})',
            "Branche": f'{x["branche"]} ({_fn(x["branche_feld"]) or "–"}{", stabil" if x.get("branche_stabil") else ""})',
            "Thema": (x["thema"] or "").split(" · ")[0][:THEMA_ZEICHEN],
            "Zahlen": PUNKT[z.get("ampel") or "grau"], "letzte Zahlen": _reaktion(x),
            "Zahlen am": ("🔴 " if warn == "rot" else "🟡 " if warn else "") + termin,
            "Zahlen im Einzelnen": _punkte_text(x)})
    for o in erg.get("ohne_daten") or []:       # nicht rechenbar: grau mit Grund, damit nichts still fehlt
        if nur_watchlist and not o.get("watchlist"):
            continue
        reihen.append({"Klasse": "–", "Titel": _link(o["tk"], o["tk"] + (" ◆" if o.get("watchlist") else "")), "Geld": PUNKT["grau"],
                       "Zahlen": PUNKT["grau"], "Zahlen im Einzelnen": o["grund"]})
    return pd.DataFrame(reihen)
