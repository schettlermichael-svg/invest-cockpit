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

from rueckenwind import KLASSEN, ZUFLUSS, abstand_wort, klasse, laden, richtung  # noqa: E402  eine Quelle (rueckenwind)
FELD_FARBE = {"Führend": GRUEN, "Erstarkend": BLAU, "Ermüdend": GELB, "Abgehängt": ROT}
# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
KOPF_SCHRIFT = 12        # Schriftgröße der Kopfzeile
KOPF_ABSTAND = 8         # Abstand der Kopfzeile
KARTE_RAND = 8           # Rand der Wetterkarte
TERMIN_TAGE_ZEIGEN = 60  # „in n T.“ zeigen bis 60 Tage
THEMA_ZEICHEN = 40       # Layout: Thema höchstens 40 Zeichen


def _fn(f):
    return FELD_TEXT[f].split(" · ")[0] if f in FELD_TEXT else f


FELD_TEXT = {"Führend": "Führend · Geld ist drin", "Erstarkend": "Erstarkend · Geld fließt zu",
             "Ermüdend": "Schwächelnd · Geld fließt ab", "Abgehängt": "Zurückfallend · Geld ist weg"}
PUNKT = {"grün": "🟢", "gelb": "🟡", "rot": "🔴", "grau": "⚪"}




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
        f'Geldfluss in Sektor, Branche und Thema (zwei von drei vorne und keine schwächelnd = grün), Fundament – die Strömung, '
        f'das Setup aus Zirkel und Spanne steht in der Spalte „Setup“. '
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


def setups():
    """Setup jedes Titels aus dem letzten Zirkel-Lauf als Klartext ({Ticker: „🦬 Fortsetzung · an der Front“}): Spanne der
    Tagesebene im Einklang mit dem Zirkel, dieselbe Regel wie Titelseite und Chart (Micky 22.11.2026)."""
    import zirkel
    rw = (laden() or {}).get("titel") or {}
    return {tk: " · ".join(x for x in (zirkel.trade_wort(f), zirkel.dreifach(tk, f["trade"], rw),
                                       zirkel.gegenwind(tk, f["trade"])) if x)
            for tk, f in zirkel.feld().items() if f.get("trade")}


def _mitglieder(erg, art, g, setup, drei):
    """Die Titel einer Gruppe als aufklappbare Liste (10.11.2026): nach RS-Rang, mit Klasse, Tempo, Setup und Link.
    Knapp gehalten (Stil einmal in MITGLIEDER_STIL), damit die Wetterkarte mit allen Titeln schnell lädt."""
    import watchlists
    feld = {"Sektor": "sektor", "Branche": "branche", "Thema": "thema"}[art]
    wl = watchlists.laden()
    liste = sorted(((tk, x) for tk, x in erg["titel"].items() if x.get(feld) == g["name"]), key=lambda p: -p[1]["rang"])
    if not liste:
        return '<div class="mg"><i>keine Titel mit Daten</i></div>'
    zeilen = []
    for tk, x in liste:
        k = klasse(x)
        s_ = setup.get(tk)
        zeilen.append(f'<div><b>{_marke(tk, wl, " ")}{tk}{" ▲▲▲" if tk in drei else ""}</b>'
                      f'<span class="k{k or ""}">{f"{k} · {KLASSEN[k - 1]}" if k else "–"}</span><span>{x["rang"]}</span>'
                      f'<span>{"+" if x["tempo"] >= 0 else ""}{x["tempo"]}</span>'
                      f'<span{"" if s_ else " class=o"}>{t(s_.replace(" · ▲▲▲", "")) if s_ else "kein Setup"}</span>'
                      f'<a href="?seite=Titelseite&t={tk}" target="_blank">Titelseite →</a></div>')
    return ('<div class="mg"><div class="k"><span>Titel</span><span>Klasse</span><span>RS-Rang</span><span>Tempo</span>'
            '<span>Setup</span><span></span></div>' + "".join(zeilen)
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


def _zirkel_pille(z):
    """Die Lage einer Gruppe als Zirkel (Micky 23.11.2026, ersetzt den Auktions-Zustand): Phase mit Keim, beim
    Darüberfahren die Zeichen, die tragen, und der Keim; ohne Zirkel „jung“."""
    if not z:
        return f'<span style="color:{TEXT_3};font-size:12px">ohne Zirkel</span>'
    farbe = {1: TEXT_2, 2: GRUEN, 3: GELB, 4: ROT}.get(z["phase"], TEXT_3)
    titel_ = " &#10;".join(t(f"trägt – {x}") for x in z.get("traegt") or []) + (" &#10;" if z.get("traegt") else "") + \
        " &#10;".join(t(f"Keim – {x}") for x in z.get("keim") or [])
    return (f'<span title="{titel_}" style="display:inline-block;border:1px solid {farbe};color:{farbe};'
            f'border-radius:999px;padding:1px 9px;font-size:12px;white-space:nowrap">{t(zirkel_wort(z))}</span>')


def wetterkarte(erg, art):
    """Wetterkarte der Strömung (10.11.2026, ersetzt die Punktwolke): je Gruppe eine Zeile mit dem Feld der letzten
    fünf Wochen als Kästchen, der Phase des Zirkels heute in Worten und dem Geldfluss. Alle Gruppen, geordnet nach Feld heute –
    Erstarkend zuerst (dort entsteht die Strömung), dann Führend offen, Schwächelnd und Zurückfallend zugeklappt."""
    ordnung = ("Erstarkend", "Führend", "Ermüdend", "Abgehängt")
    gr = [g for g in erg["gruppen"] if g["art"] == art]
    setup, drei = setups(), {tk for tk, _ in dreifach_liste(erg)}
    kopf = (f'<div style="display:grid;grid-template-columns:minmax(140px,260px) repeat(5,30px) 1fr 120px;gap:6px;'
            f'font-size:11px;color:{TEXT_3};padding:0 0 4px">'
            f'<span>{art}</span><span>−4</span><span>−3</span><span>−2</span><span>−1</span><span>heute</span>'
            f'<span>Phase</span><span>Geld</span></div>')
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
            lage = _zirkel_pille(g.get("zirkel")) + " " + t(lage)
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
    import rueckenwind
    return [(tk, x) for tk, x in erg["titel"].items() if rueckenwind.dreifach(x)]


DREI_GRUPPEN = (("🎯", "Schlagbereit", "Long-Setup an der Front, im Ausbruch oder im Rücktest – der Angriffspunkt steht"),
                ("⏳", "Auf der Lauer", "Base im Aufbau oder Rücksetzer – warten, bis der Kurs an die Front kommt"),
                ("🏃", "Enteilt oder ohne Base", "stark, aber gerade kein Angriffspunkt – nicht hinterherlaufen"))


def _drei_gruppe(f):
    """Gruppe eines ▲▲▲-Titels aus seinem Feld im Zirkel-Lauf: 0 schlagbereit, 1 auf der Lauer, 2 enteilt/ohne Base."""
    import zirkel
    t_ = (f or {}).get("trade")
    if t_ and t_["richtung"] > 0 and f.get("phase") in zirkel.HEISS:
        return 0
    return 1 if (f or {}).get("phase") in ("aufbau", "ruecksetzer", "kante") else 2


def dreifach_block(erg):
    """Eigene Liste „▲▲▲ Dreifacher Rückenwind“ (Micky 23.11.2026): alle Titel mit Kurs, Geld und Zahlen grün in drei
    Gruppen – 🎯 schlagbereit (mit Einstieg, Stopp, Risiko), ⏳ auf der Lauer (Front und Abstand), 🏃 enteilt oder ohne
    Base. In der Gruppe nach Klasse und Rang. Nichts gefiltert: jeder ▲▲▲-Titel steht in genau einer Gruppe."""
    import watchlists
    import zeichen
    import zirkel
    import zonen
    feld, kreis, wl = zirkel.feld(), zeichen.laden(), watchlists.laden()
    gruppen_ = [[], [], []]
    for tk, x in dreifach_liste(erg):
        gruppen_[_drei_gruppe(feld.get(tk))].append((tk, x))
    if not any(gruppen_):
        return seite(f'<h3 style="margin:0">▲▲▲ Dreifacher Rückenwind</h3><p style="color:{TEXT_3}">heute kein Titel mit '
                     f'Kurs, Geld und Zahlen grün</p>', oben=8, unten=0)   # Layout
    teile = []
    for (sym, name, erkl), liste_ in zip(DREI_GRUPPEN, gruppen_):
        zeilen = []
        for tk, x in sorted(liste_, key=lambda p: (klasse(p[1]) or len(KLASSEN) + 1, -p[1]["rang"])):
            f = feld.get(tk) or {}
            t_, piv, kurs = f.get("trade"), f.get("pivot"), f.get("kurs")
            if sym == "🎯":
                lage_ = (f'{zirkel.trade_wort(f)} · '
                         + (f'½ antasten {zahl(t_["einstieg"])} · ½ aufstocken bei 📒 {zahl(t_["aufstocken"])}'
                            if t_.get("aufstocken") else f'{"Auslöser" if t_["wartet"] else "Einstieg"} {zahl(t_["einstieg"])}')
                         + f' · Stopp {zahl(t_["stopp"])} · {t_["ampel"]} {zahl(t_["risiko"], 1)} %')
                gw = zirkel.gegenwind(tk, t_)
                lage_ += f" · {gw}" if gw else ""
            else:
                lage_ = zonen.PHASE.get(f.get("phase"), ("", "ohne Zirkel-Lauf"))[1]
                if piv and kurs:
                    lage_ += (f" · Front {zahl(piv)} · noch {zahl((piv / kurs - 1) * 100, 1)} %" if kurs < piv else
                              f" · {zahl((kurs / piv - 1) * 100, 1)} % über der Front {zahl(piv)}")
            b_ = bahn(x.get("frei"))
            lage_ += f" · {b_}" if b_ else ""
            phase, halt_ = _zirkel(tk, kreis)
            k = klasse(x)
            zeilen.append(f'<tr><td><a href="?seite=Titelseite&t={tk}" target="_blank">{tk}</a>{t(_marke(tk, wl))}</td>'
                          f'<td>{_lage(f)}</td><td>{f"{k} · {KLASSEN[k - 1]}" if k else "–"}</td><td>{t(phase)}</td>'
                          f'<td>{t(lage_)}</td><td>{t(halt_)}</td></tr>')
        teile.append(f'<details{" open" if sym != "🏃" else ""}><summary style="cursor:pointer;font-size:16px;'
                     f'font-weight:600;padding:6px 0">{sym} {name} ({len(liste_)}) <span style="font-weight:400;'
                     f'font-size:13px;color:{TEXT_3}">{erkl}</span></summary>'
                     + (f'<table style="width:100%;border-collapse:collapse;font-size:13px;color:{TEXT_2}">'
                        f'<tr style="color:{TEXT_3};text-align:left"><th>Titel</th><th title="Livermores Notizbuch: 🟢 Vormarsch · '
                        f'🟡 Gefechtspause · 🔴 Rückzug">Lage</th><th>Klasse</th><th>Phase</th><th>Stand</th><th>Halt</th></tr>{"".join(zeilen)}</table>' if zeilen else
                        f'<p style="color:{TEXT_3};font-size:13px;margin:0">keiner</p>') + '</details>')
    return seite(f'<h3 style="margin:0">▲▲▲ Dreifacher Rückenwind · {sum(map(len, gruppen_))} Titel</h3>'
                 f'<p style="color:{TEXT_2};font-size:14px;margin:6px 0 8px">Kurs (Garde oder Angriff), Geld (Sektor, '
                 f'Branche, Thema) und Zahlen zugleich grün – die stärkste Truppe. Am stärksten mit einem Setup am '
                 f'Front (🎯).</p>' + "".join(teile), oben=8, unten=0)   # Layout


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


def kraft_ampel(x):
    """⚔️ Kraft: 🟢 Garde oder Angriff, 🟡 Vorhut, 🔴 Ohne Nachschub oder Rückzug, ⚪ ohne Klasse – eine Regel für Liste
    und Titelseite."""
    import rueckenwind
    k = klasse(x)
    return ("grau" if not k else "grün" if k in rueckenwind.ANGRIFF_KLASSEN
            else "gelb" if k in rueckenwind.VORNE_KLASSEN else "rot")


def titel_karten(tk):
    """Rückenwind eines Titels für den Kopf der Titelseite (Micky 23.11.2026: statt einer langen Zeile drei Karten, je
    eine Frage mit eigener Ampel und einer Angabe pro Zeile – drei Mal grün ist ▲▲▲; nichts weggelassen):
    ⚔️ Kraft (Kurs), 💰 Nachschub (Geld), 📊 Fundament (Zahlen). → [(Titel, Ampel, [Zeilen])]; leer ohne Stand."""
    erg = laden() or {}
    x = (erg.get("titel") or {}).get(tk)
    if not x:
        return []
    k, r, ab = klasse(x), _richtung(x), x.get("abstand_hoch")
    wort, z = abstand_wort(ab), x.get("zahlen") or {}
    termin, warn = _termin(x, erg["stand"])
    b_ = bahn(x.get("frei"))
    front = [(f"{k} · {KLASSEN[k - 1]}" if k else "ohne Klasse") + (" · 🦈 RS-Hoch vor Kurs" if x.get("rs_hoch_vor_kurs") else ""),
             f'{PFEIL.get(r, "")} RS-Linie {r or "–"} {_rs_linie(x)}'.strip(),
             f'Rang {x["rang_vor4"]} → {x["rang"]}',
             *(["Momentum " + _momentum(x)] if x.get("momentum") else []),
             (f"{HOCH_PUNKT[wort]} Hoch {wort} −{zahl(ab, 0)} %" if wort else "Hoch –") + (f" · {b_}" if b_ else "")]
    zb = _branche_zirkel(tk)
    nachschub = ["Volumen " + (_zufluss(x.get("zufluss"), x.get("trocken")) or "–"),
                 f'Sektor {x["sektor"]} ({_fn(x["sektor_feld"]) or "–"}{", stabil" if x.get("sektor_stabil") else ""})',
                 f'Branche {x["branche"]} ({_fn(x["branche_feld"]) or "–"}{", stabil" if x.get("branche_stabil") else ""})'
                 + (f" · Zirkel {zirkel_wort(zb)}" if zb else ""),
                 *([f'Thema {(x["thema"] or "").split(" · ")[0][:THEMA_ZEICHEN]}'] if x.get("thema") else []),
                 *(["🐺 Einzelkämpfer – stark, aber die Branche liegt hinten"] if x.get("einzelkaempfer") else [])]
    fundament = [*([f'📅 nächste Zahlen {("🔴 " if warn == "rot" else "🟡 " if warn else "")}{termin}'] if termin else []),
                 *([f"letzte Zahlen {r_}"] if (r_ := _reaktion(x)) else []),
                 *([f"im Einzelnen: {p_}"] if (p_ := _punkte_text(x)) else [])] or ["keine Zahlen gemessen"]
    return [("⚔️ Kraft · Wie stark ist der Kurs?", kraft_ampel(x), front),
            ("💰 Nachschub · Fließt Geld hinein?", x["geld_ampel"], nachschub),
            ("📊 Fundament · Tragen die Zahlen?", z.get("ampel") or "grau", fundament)]


def _branche_zirkel(tk):
    import zirkel
    return zirkel.branche(tk)


def zirkel_wort(z, vor=""):
    """Zirkel einer Gruppe in Worten (Micky 23.11.2026, Branchen auf den Zirkel): „Branche 2 (Aufwärts) 🌊“ – dahinter
    der Halt der Phase (🏰 hält · 🌊 Welle · ⛈️ Sturm, zeichen.halt)."""
    import zeichen
    return f'{vor}{z["wort"]} ({z["name"]}) {zeichen.halt(z)[0]}'.strip()


def bahn(fr, wort=" freie Bahn"):
    """✈️ freie Bahn (Livermore: Linie des geringsten Widerstands) aus zonen.frei: keine Stellung über dem Kurs,
    ✈️↓ keine darunter; sonst leer. In der Liste ohne Wort (wort=""), die Spalte heißt schon „Bahn“."""
    return " ".join(z + wort for z, ja in (("✈️", (fr or {}).get("oben")), ("✈️↓", (fr or {}).get("unten"))) if ja)


def _momentum(x):
    """Momentum nach Kullamägi: Rendite über 1, 3, 6 Monate; 🚀 = unter den besten 2 % des Reviers."""
    m = x.get("momentum") or {}
    return " · ".join(f'{"🚀 " if top else ""}{k} {"+" if r > 0 else ""}{zahl(r, 0)} %' for k, (r, top) in m.items())


def _zirkel(tk, kreis):
    """(Phase, Halt) für die Liste aus dem gespeicherten Kreislauf (zeichen.laden). Halt (Micky 24.11.2026, statt der
    Fachnamen des Keims): 🏰 hält · 🌊 Welle · ⛈️ Sturm mit einem Wort in Klartext (zeichen.halt)."""
    import zeichen
    z = zeichen.zirkel((kreis.get("titel") or {}).get(tk))
    if not z:
        return "–", ""
    phase = (f'{z["phase"]} {z["name"]}' + (f' · {z["wochen"]} Wo.' if z["wochen"] else "")
             + (f' → {z["ziel"]}' if z["ziel"] else "")) if z["phase"] else "jung"
    sym, wort, grund = zeichen.halt(z)
    return phase, (f"{sym} {grund or wort}" if sym else "")


def _link(tk, text):
    """Titel als Verweis auf seine Titelseite (Micky 22.11.2026: Titel anklicken → Titelseite); die App zeigt nach
    TITEL_TEXT nur den Text hinter „&z=“."""
    return f"?seite=Titelseite&t={tk}&z={text}"


TITEL_TEXT = r"&z=(.*)$"


def _marke(tk, w, vorn=""):
    """Die Marken der Listen, frisch aus einstellungen/watchlists.json: ◆ Watchlist, 🎯 Trade."""
    import watchlists
    m = watchlists.zeichen(tk, w)
    return (m + vorn) if vorn and m else (" " + m if m else "")


def _rs(x):
    """RS als Zeichen: 🦈 RS-Hoch vor Kurs, Pfeil der Richtung, Steigung in 4 Wochen – „🦈 ⏫ +6,2 %“."""
    r, a = _richtung(x), x.get("rs_tempo")
    return " ".join(s_ for s_ in ("🦈" if x.get("rs_hoch_vor_kurs") else "", PFEIL.get(r, ""),
                                  f'{"+" if a >= 0 else "−"}{zahl(abs(a), 1)} %' if a is not None else "") if s_) or "–"


def _momentum_zeichen(x):
    """Momentum als Zeichen: je Fenster 1M, 3M, 6M ein Pfeil (↑ im Plus, ↓ im Minus), 🚀 wenn der Titel in einem
    Fenster unter den besten 2 % des Reviers ist (Kullamägi) – „🚀 ↑↑↑“. Die Prozente stehen auf der Titelseite."""
    m = x.get("momentum") or {}
    if not m:
        return "–"
    return ("🚀 " if any(top for _, top in m.values()) else "") + "".join("↑" if r > 0 else "↓" for r, _ in m.values())


def _volumen_zeichen(x):
    """Volumen als Zeichen: Ampel des Zuflusses (grün ab 1,1-fach, rot unter 0,9-fach), 🏜️ trocken zählt grün."""
    z = x.get("zufluss")
    if x.get("trocken"):
        return "🟢 🏜️"
    if not z:
        return "–"
    return ("🟢 " if z >= ZUFLUSS[0] else "🔴 " if z < ZUFLUSS[1] else "🟡 ") + zahl(z, 1) + "×"


TABELLE_HOEHE = 560            # Layout: Höhe der Tabelle je Klasse höchstens
TABELLE_ZEILE = 35             # Layout: Höhe einer Zeile
TABELLE_RAND = 3               # Layout: Rand der Tabelle
ANGRIFF_OFFEN = tuple(f"{i} · {KLASSEN[i - 1]}" for i in (1, 2))   # Garde und Angriff aufgeklappt
BREITE = {"Titel": 120, "Lage": 45, "Phase": 105, "Setup": 130, "Halt": 115, "⚔️ Kraft": 70, "RS": 85,   # Layout:
          "Momentum": 70, "Hoch": 65, "Bahn": 40, "💰 Nachschub": 95, "Volumen": 70, "📊 Fundament": 90}   # px, zusammen 1100
SPALTEN = ("Titel", "Lage", "Phase", "Setup", "Halt", "⚔️ Kraft", "RS", "Momentum", "Hoch", "Bahn", "💰 Nachschub", "Volumen",
           "📊 Fundament")   # nach den drei Fragen der Titelseite geordnet (Micky 24.11.2026)
SPALTEN_HILFE = {"Lage": "Livermores Notizbuch des Titels: 🟢 Vormarsch (Aufwärtstrend) · 🟡 Gefechtspause (Rally oder "
                         "Reaktion) · 🔴 Rückzug (Abwärtstrend) – dieselbe Sprache wie Lagebericht und Markt",
                 "RS": "🦈 RS-Hoch vor Kurs · Pfeil = Richtung der RS-Linie (⏫ schneller, ⬆️ steigt, ↗️ dreht hoch, ↘️ "
                       "dreht runter, ⬇️ fällt) · Steigung in 4 Wochen",
                 "Momentum": "1M · 3M · 6M: ↑ im Plus, ↓ im Minus · 🚀 unter den besten 2 % des Reviers (Kullamägi)",
                 "Volumen": "Zufluss: Volumen der Aufwärtstage gegen Abwärtstage · 🟢 ab 1,1× · 🔴 unter 0,9× · 🏜️ "
                            "trocken (kaum noch Verkäufer, Minervini)",
                 "⚔️ Kraft": "Wie stark ist der Kurs? 🟢 Garde oder Angriff · 🟡 Vorhut · 🔴 Ohne Nachschub oder Rückzug",
                 "💰 Nachschub": "Fließt Geld hinein? Geldfluss in Sektor, Branche, Thema: 🟢 zwei vorne, keine schwächelnd · "
                                "🐺 Einzelkämpfer",
                 "📊 Fundament": "Tragen die Zahlen? Fundament-Ampel · 📅 Zahlen in den nächsten 14 Tagen",
                 "Halt": "Hält die Phase? 🏰 hält · 🌊 Welle: ein Riss, die Phase trägt aber mehr · ⛈️ Sturm: der Riss "
                         "wiegt so schwer wie das, was trägt, oder der Wechsel zeichnet sich ab – dahinter der stärkste "
                         "Grund in Klartext (alle Zeichen auf der Titelseite)",
                 "Hoch": "Abstand zum 52-Wochen-Hoch",
                 "Bahn": "✈️ freie Bahn: keine Stellung über dem Kurs (✈️↓ keine darunter) – Livermores Linie des "
                         "geringsten Widerstands"}


def _lage(f):
    """Ampel der Lage aus Livermores Spalte im Feld (livermore.lage); ohne Notizbuch ⚪."""
    import livermore
    import zirkel
    sp = zirkel.spalte(f or {})
    return livermore.lage(sp)[0] if sp else "⚪"


def liste(erg, nur=None):
    """Alle Titel nach Schlachtordnung (Micky 23.11.2026: übersichtlich – je Klasse ein Abschnitt, nur die Spalten zum
    Entscheiden, alles als Zeichen; Sektor, Branche, Thema, Rang und die Zahlen im Einzelnen auf der Titelseite).
    Nichts gefiltert; ohne Daten grau mit Grund. nur="Watchlist" oder "Trade" zeigt nur die Titel dieser Liste.
    → {Abschnitt: DataFrame} in der Reihenfolge Garde … Rückzug, ohne Klasse, ohne Daten."""
    import watchlists
    import zeichen
    wl = watchlists.laden()
    kreis = zeichen.laden()
    feld_ = kreis.get("feld") or {}
    trades, drei_ = setups(), {t_ for t_, _ in dreifach_liste(erg)}
    abschnitte = {f"{i} · {n}": [] for i, n in enumerate(KLASSEN, 1)}
    abschnitte["ohne Klasse"], abschnitte["ohne Daten"] = [], []
    for tk, x in sorted(erg["titel"].items(), key=lambda p: _ordnung(p[1])):
        if nur and tk not in wl[nur]:
            continue
        z = x.get("zahlen") or {}
        termin, warn = _termin(x, erg["stand"])
        ab = x.get("abstand_hoch")
        wort = abstand_wort(ab)
        k = klasse(x)
        phase, halt_ = _zirkel(tk, kreis)
        drei = " ▲▲▲" if tk in drei_ else ""
        abschnitte[f"{k} · {KLASSEN[k - 1]}" if k else "ohne Klasse"].append({
            "Titel": _link(tk, tk + _marke(tk, wl) + drei + (f' · jung {x["jung"]} M' if x.get("jung") else "")),
            "Lage": _lage(feld_.get(tk)),
            "Phase": phase, "Setup": trades.get(tk, "").replace(" · ▲▲▲", ""), "Halt": halt_,
            "⚔️ Kraft": PUNKT[kraft_ampel(x)], "RS": _rs(x), "Momentum": _momentum_zeichen(x),
            "💰 Nachschub": PUNKT[x["geld_ampel"]] + (" 🐺" if x.get("einzelkaempfer") else ""),
            "Volumen": _volumen_zeichen(x),
            "📊 Fundament": PUNKT[z.get("ampel") or "grau"] + (f' 📅 {termin.split(" (")[0]}' if warn else ""),
            "Hoch": f'{HOCH_PUNKT[wort]} −{zahl(ab, 0)} %' if wort else "–", "Bahn": bahn(x.get("frei"), "")})
    for o in erg.get("ohne_daten") or []:       # nicht rechenbar: grau mit Grund, damit nichts still fehlt
        if nur and o["tk"] not in wl[nur]:
            continue
        abschnitte["ohne Daten"].append({"Titel": _link(o["tk"], o["tk"] + _marke(o["tk"], wl)), "Phase": o["grund"],
                                         "⚔️ Kraft": PUNKT["grau"], "💰 Nachschub": PUNKT["grau"],
                                         "📊 Fundament": PUNKT["grau"]})
    return {n: pd.DataFrame(r, columns=SPALTEN) for n, r in abschnitte.items() if r}

