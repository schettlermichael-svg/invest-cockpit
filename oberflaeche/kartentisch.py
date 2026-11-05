"""Kartentisch (4.11.2026): alle Titel des Abendlaufs einmal durchgerechnet, in Reihen geordnet, als Lagekarten.

Reihen (ordnen, filtern nicht – jeder Titel bleibt über die Titelseite erreichbar):
  ★ Spitzenkandidaten  Setup grün (alle Regeln der Meister) und Zone an der Schwelle oder im Ausbruch in Richtung des
                       Setups – long
  Weitere Kandidaten   Setup grün, Zone in Balance; oder Setup gelb, weil genau eine Regel fehlt – long
  Frühaufklärung       Radar: Zone an der Schwelle oder frischer Angriff (A, F, U in den letzten 5 Tagen), egal wie
                       viele Regeln noch gelb sind (beide Richtungen; frische Angriffe zuerst)
  Short                Short-Setups nach denselben Stufen (★ = an der Schwelle oder im Ausbruch ↓)
  Meine Watchlists     jeder Titel aus einstellungen/watchlists.json, immer, egal ob grün, gelb oder rot; er steht nur
                       hier (nicht doppelt), seine eigentliche Reihe als Marke auf der Karte; je Liste ein Abschnitt,
                       ein Titel in mehreren Listen steht im ersten, die anderen Listen als Marke
Innerhalb einer Reihe nach Abstand zum Pivot bzw. Auslöser, die nächsten zuerst.

Rechnung in zwei Stufen: 1. alle Titel nur Erkennung und Zone (schnell, mehrere Prozesse) → Reihe; 2. für die Titel
in einer Reihe die volle Titelseite (dieselben Kacheln, dieselbe Lagekarte). Ergebnis: daten/kartentisch/<Datum>.json;
die Übersicht liest nur diese Datei.
"""
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)
import lagekarte                                      # noqa: E402
SPEICHER = os.path.join(HIER, "..", "daten", "kartentisch")
REIHEN = [("spitze", "★ Spitzenkandidaten", "Setup grün, die Zone bewegt sich schon in Richtung des Setups"),
          ("weitere", "Weitere Kandidaten", "Setup grün, Zone noch in Balance – oder genau eine Regel fehlt"),
          ("frueh", "Frühaufklärung", "Radar: Zone an der Schwelle oder frischer Angriff (A, F, U in 5 Tagen) – Regeln "
                    "der Meister noch nicht alle grün"),
          ("short", "Short", "Short-Setups (★ = Zone an der Schwelle oder im Ausbruch ↓)")]


def _stufe1(tk):
    """Erkennung und Zone eines Titels aus dem Speicher; Reihe oder None."""
    import daten
    import erkennung
    try:
        df = daten.kurse_gespeichert(tk)
        index = daten.kurse_gespeichert(daten.INDEX)
        if df is None or len(df) < 60:
            return None
        df.attrs.update(ticker=tk, jung=len(df) < 300)
        erk = erkennung.erkenne(df, index=index)
        a = erk.get("mp")
        if not a:
            return None
        z = a["zustand"]
        c, h, l = df["Close"].to_numpy(float), df["High"].to_numpy(float), df["Low"].to_numpy(float)
        ph = erkennung._phase_von(df)
        info = {"tk": tk, "zustand": z["wort"], "zdir": z["dir"], "seite": erk.get("seite"),
                "phase": int(ph[-1]) if ph is not None else None,
                "hoch52": bool(len(h) >= 252 and h[-1] >= h[-252:].max()),
                "tief52": bool(len(l) >= 252 and l[-1] <= l[-252:].min())}
        w = erk.get("werte") or {}
        bewegt = z["wort"].startswith(("an der Schwelle", "Ausbruch"))
        if erk.get("short"):
            sh = erk["short"]
            luecken = [n for n, ok, _ in sh["regeln"] if not ok]
            fehlt = len(luecken)
            info.update(abstand=abs(sh["abstand_pct"]), gruen=sh["setup"], luecken=luecken)
            if sh["setup"] or fehlt == 1:
                info.update(reihe="short", stern=bool(sh["setup"] and bewegt and z["dir"] == "↓"))
        elif erk["muster"] and "pivot" in w:
            ab = (c[-1] / w["pivot"] - 1) * 100
            info.update(abstand=abs(ab), gruen=bool(erk["kaufsetup"]))
            luecken = [g for g in (erk.get("hinweise") or []) if g.startswith(("Angebot von oben", "Daten gestört"))]
            if not erk["kaufsetup"]:
                from titel import _fehlt_zum_kaufsetup, _trendvorlage
                tv = sum(_trendvorlage(df).values())
                luecken += [g for g in _fehlt_zum_kaufsetup(erk, info["phase"], tv) if g not in luecken]
            fehlt = len(luecken)
            info["luecken"] = luecken
            if erk["kaufsetup"] and bewegt and z["dir"] == "↑":
                info.update(reihe="spitze", stern=True)
            elif erk["kaufsetup"] or fehlt == 1:
                info["reihe"] = "weitere"
        else:
            info["luecken"] = ["kein Muster erkannt"]
        # Radar (Frühaufklärung): Zone an der Schwelle oder ein frischer Angriff (A, F, U in den letzten 5 Tagen) –
        # egal wie viele Regeln der Meister noch gelb sind; die fehlenden stehen auf der Karte
        n_ = len(a["tage"]) - 1
        frisch = [x for x in a["signale"] if x["art"] in ("A", "F", "U") and x["i"] >= n_ - 4]
        if "reihe" not in info and (frisch or z["wort"].startswith("an der Schwelle")):
            info.update(reihe="frueh", ausloeser=bool(frisch), abstand=info.get("abstand", 0.0),
                        angriff=(f"{frisch[-1]['art']}{frisch[-1]['dir']} {frisch[-1]['tag']:%d.%m.}" if frisch else None))
        return info
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Tisch steht trotzdem
        return None


def _stufe2(tk):
    """Volle Titelseite (ohne Abruf neuer 30-Minuten-Kerzen): Lagekarte und Kacheln."""
    import titel
    try:
        r = titel.seite_titel(tk)
        return tk, r["lagekarte"], r["kacheln"]
    except Exception:  # noqa: BLE001
        return tk, None, None


def rechnen(ticker_liste, prozesse=None, melden=print):
    beginn = time.time()
    prozesse = prozesse or max(1, (os.cpu_count() or 2) - 1)
    with ProcessPoolExecutor(prozesse) as ex:
        stufe1 = [x for x in ex.map(_stufe1, ticker_liste, chunksize=20) if x]
    melden(f"  Stufe 1: {len(stufe1)} Titel gerechnet in {time.time() - beginn:.0f} s")
    import watchlists
    w = watchlists.laden()
    beobachtet = set(watchlists.alle())
    gerechnet = {x["tk"] for x in stufe1}
    stufe1 += [{"tk": tk, "zustand": "keine Zone (Daten fehlen noch)", "hoch52": False, "tief52": False,
                "phase": None} for tk in watchlists.alle() if tk not in gerechnet]
    for x in stufe1:
        if x["tk"] in beobachtet:
            x["listen"] = [n for n, l in w.items() if x["tk"] in l]
    in_reihe = [x for x in stufe1 if x.get("reihe") or x.get("listen")]
    with ProcessPoolExecutor(prozesse) as ex:
        karten = {tk: (lk, kl) for tk, lk, kl in ex.map(_stufe2, [x["tk"] for x in in_reihe])}
    melden(f"  Stufe 2: {len(in_reihe)} Lagekarten in {time.time() - beginn:.0f} s")
    for x in in_reihe:
        x["karte"], x["kacheln"] = karten.get(x["tk"], (None, None))
    stand = pd.Timestamp.now().strftime("%Y-%m-%d")
    vorher = laden()
    ergebnis = {"stand": stand, "erzeugt": time.strftime("%d.%m.%Y %H:%M"),
                "barometer": {"long_gruen": sum(1 for x in stufe1 if x.get("gruen") and x.get("seite") == "long"
                                                 and x.get("reihe") in ("spitze", "weitere")),
                              "short_gruen": sum(1 for x in stufe1 if x.get("gruen") and x.get("reihe") == "short"),
                              "hochs": sum(x["hoch52"] for x in stufe1), "tiefs": sum(x["tief52"] for x in stufe1),
                              "titel": len(stufe1)},
                "titel": {x["tk"]: {k: v for k, v in x.items() if k != "tk"} for x in in_reihe},
                "phasen": {x["tk"]: x["phase"] for x in stufe1}}
    ergebnis["neu"] = _neu(vorher, ergebnis)
    os.makedirs(SPEICHER, exist_ok=True)
    json.dump(ergebnis, open(os.path.join(SPEICHER, f"{stand}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return ergebnis


def laden():
    """Jüngster gespeicherter Kartentisch oder None."""
    if not os.path.isdir(SPEICHER):
        return None
    dateien = sorted(f for f in os.listdir(SPEICHER) if f.endswith(".json"))
    return json.load(open(os.path.join(SPEICHER, dateien[-1]), encoding="utf-8")) if dateien else None


_REIHEN_CACHE = {}


def eintrag_von(tk):
    """Eintrag eines Titels im jüngsten Kartentisch (für Rahmen und Grund auf der Titelseite); einmal je Tisch gelesen."""
    if not os.path.isdir(SPEICHER):
        return None
    dateien = sorted(f for f in os.listdir(SPEICHER) if f.endswith(".json"))
    if not dateien:
        return None
    pfad = os.path.join(SPEICHER, dateien[-1])
    schluessel = (pfad, os.path.getmtime(pfad))
    if schluessel not in _REIHEN_CACHE:
        _REIHEN_CACHE.clear()
        tisch = json.load(open(pfad, encoding="utf-8"))
        felder = ("reihe", "stern", "gruen", "angriff", "zdir", "luecken")
        _REIHEN_CACHE[schluessel] = {k: {f: x.get(f) for f in felder} for k, x in tisch["titel"].items()}
    return _REIHEN_CACHE[schluessel].get(tk)


RANG = {"spitze": 3, "short": 2, "weitere": 2, "frueh": 1, None: 0}


def _neu(vorher, jetzt):
    """Neu seit gestern: neu in einer Reihe, vorgerückt, Phasenwechsel."""
    if not vorher:
        return []
    alt, neu = vorher.get("titel", {}), jetzt["titel"]
    aus = []
    name = dict((k, n) for k, n, _ in REIHEN)
    name[None] = "keine Reihe"
    for tk, x in neu.items():
        r_alt = (alt.get(tk) or {}).get("reihe")
        if x.get("listen"):                      # Watchlist-Titel: jeder Wechsel der Reihe, auch abwärts
            if tk in alt and (r_alt != x.get("reihe") or (x.get("stern") and not alt[tk].get("stern"))):
                aus.append((tk, f"◆ {name[r_alt]} → {name[x.get('reihe')]}"))
            continue
        if r_alt is None:
            aus.append((tk, f"neu in {dict((k, n) for k, n, _ in REIHEN)[x['reihe']]}"))
        elif RANG[x["reihe"]] > RANG[r_alt] or (x.get("stern") and not alt[tk].get("stern")):
            aus.append((tk, f"vorgerückt: {dict((k, n) for k, n, _ in REIHEN)[r_alt]} → "
                            f"{dict((k, n) for k, n, _ in REIHEN)[x['reihe']]}"))
    pa = vorher.get("phasen", {})
    for tk, p in jetzt["phasen"].items():
        if pa.get(tk) and p and pa[tk] != p:
            aus.append((tk, f"Phase {pa[tk]} → {p}"))
    return aus


# ── Darstellung auf der Übersicht ──
# Die Übersicht zeigt den Kartentisch nicht mehr als einen HTML-Block, sondern Stück für Stück (plan): HTML-Teile,
# dazwischen Abschnitte mit Karten, unter jeder Karte echte Knöpfe der App (Watchlist, Deep Dive) und die übrigen
# Titel als anklickbare Tabelle (Klick → Lagekarte im Pop-up). app.py setzt die Knöpfe.
SICHTBAR = 12                 # je Reihe als Karte; die übrigen als Tabellenzeile darunter – nichts wird gefiltert


def _farbe(x):
    """Rahmenfarbe eines Titels: long grün, short rot (blass, solange das Setup nicht grün ist), offen gelb."""
    return lagekarte.rahmen(x)[0]


def _grundzeile(x):
    """Grund als kleine Zeile über der Karte (leer, wenn nichts fehlt)."""
    from gestaltung import TEXT_2, t
    g = lagekarte.grund(x)
    return f'<span style="font-size:13px;color:{TEXT_2}">{t(g)}</span>' if g else ""


def karte_html(x, kopf=""):
    """Lagekarte in der Rahmenstufe des Titels, darüber eine Zeile (Reihe-Marke im Watchlist-Abschnitt, sonst der
    Grund, was fehlt)."""
    kopf = kopf or _grundzeile(x)
    return (f'<div style="display:flex;flex-direction:column;gap:6px">{kopf}'
            f'{lagekarte.faerben(x["karte"], x)}</div>')


def zeile(tk, x):
    """Eine Tabellenzeile für die übrigen Titel (Reihenfolge wie die Karten)."""
    from gestaltung import GELB, zahl
    if x is None:
        return {"tk": tk, "farbe": GELB, "blass": False, "Setup": "neu – wird im Abendlauf gerechnet", "Zone": "",
                "Abstand %": "", "Was fehlt": ""}
    setup = (x.get("kacheln") or {}).get("Setup", ("grau", "–", ""))
    return {"tk": tk, "farbe": _farbe(x)[:7], "blass": len(_farbe(x)) > 7, "Setup": setup[1],
            "Zone": x.get("zustand", ""), "Abstand %": zahl(x.get("abstand", 0), 1), "Was fehlt": lagekarte.grund(x)}


def _klapp(titel, zeile_, inhalt):
    """Karte zum Aufklappen (Übersicht kürzer): zu sieht man Titel und eine Zeile, aufgeklappt den Inhalt."""
    from gestaltung import KARTE, RAND, TEXT_2, t
    return (f'<details style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 20px">'
            f'<summary style="cursor:pointer;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap">'
            f'<span style="font-size:20px;font-weight:600">{t(titel)} ▾</span>'
            f'<span style="font-size:15px;color:{TEXT_2}">{t(zeile_)}</span></summary>'
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:14px">{inhalt}</div></details>')


def _ordnung(x):
    return (not x.get("stern"), not x.get("ausloeser"), not x.get("gruen"), x.get("abstand", 99))


def _kopf(name, zahl_, text, h=2):
    from gestaltung import TEXT_2, TEXT_3, t
    groesse = 26 if h == 2 else 19
    return (f'<div style="display:flex;align-items:baseline;gap:14px;margin:12px 0 4px"><h{h} style="margin:0;'
            f'font-size:{groesse}px">{t(name)} <span style="color:{TEXT_3};font-weight:500">{zahl_}</span></h{h}>'
            + (f'<span style="font-size:15px;color:{TEXT_2}">{t(text)}</span>' if text else "") + f'</div>')


def _abschnitt(kopf, liste, liste_name=None, fehlen=()):
    """Ein Abschnitt für app.py: Karten (die ersten SICHTBAR mit Lagekarte) und Tabelle der übrigen."""
    sichtbar = [(tk, x) for tk, x in liste[:SICHTBAR] if x.get("karte")]
    rest = liste[SICHTBAR:] + [(tk, x) for tk, x in liste[:SICHTBAR] if not x.get("karte")]
    return {"art": "abschnitt", "kopf": kopf, "liste": liste_name,
            "karten": [(tk, x, karte_html(x, _marken(x) if liste_name else "")) for tk, x in sichtbar],
            "zeilen": [zeile(tk, x) for tk, x in rest] + [zeile(tk, None) for tk in fehlen],
            "titel": {tk: x for tk, x in rest}}


def plan(tisch=None):
    """Kartentisch für die Übersicht als Folge von Teilen: {"art": "html", "html": …} oder ein Abschnitt (siehe
    _abschnitt). Watchlist-Zugehörigkeit immer aus den Listen der App (nicht aus dem Stand des Abendlaufs) – ein Titel,
    der eben auf eine Liste kam, steht sofort im Watchlist-Abschnitt und nicht mehr in seiner Reihe."""
    import watchlists
    from gestaltung import GELB, GRUEN, KARTE, RAND, ROT, TEXT_2, TEXT_3, karte, t, zahl
    tisch = tisch if tisch is not None else laden()
    if not tisch:
        return [{"art": "html", "html": karte(f'<p style="margin:0;font-size:15px;color:{TEXT_2}">Der Kartentisch wird '
                                              f'im Abendlauf gerechnet. Noch liegt kein Ergebnis vor.</p>', "Kartentisch")}]
    w = watchlists.laden()
    tisch = dict(tisch, titel={tk: dict(x, listen=[n for n, l in w.items() if tk in l])
                               for tk, x in tisch["titel"].items()})
    b = tisch["barometer"]
    hl = "grün" if b["hochs"] > 2 * b["tiefs"] else "rot" if b["tiefs"] > 2 * b["hochs"] else "gelb"
    farbe = {"grün": GRUEN, "gelb": GELB, "rot": ROT}[hl]
    barometer = (
        f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px">'
        f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 20px">'
        f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:.06em;text-transform:uppercase">Setups</div>'
        f'<div style="font-size:26px;font-weight:600">{b["long_gruen"]} long · {b["short_gruen"]} short</div>'
        f'<div style="font-size:14px;color:{TEXT_2}">grüne Setups unter {zahl(b["titel"], 0)} Titeln</div></div>'
        f'<div title="Neue 52-Wochen-Hochs gegen neue 52-Wochen-Tiefs (Hoch/Boden-Check): grün = mehr als doppelt so viele '
        f'Hochs, rot = mehr als doppelt so viele Tiefs" style="background:{KARTE};border:1px solid {RAND};border-radius:12px;'
        f'padding:16px 20px"><div style="font-size:13px;color:{TEXT_3};letter-spacing:.06em;text-transform:uppercase">'
        f'Neue Hochs gegen Tiefs</div><div style="font-size:26px;font-weight:600;color:{farbe}">{b["hochs"]} : {b["tiefs"]}'
        f'</div><div style="font-size:14px;color:{TEXT_2}">52-Wochen-Hochs : -Tiefs heute</div></div></div>')
    namen = {k: n for k, n, _ in REIHEN}
    neu = tisch.get("neu") or []
    chip = ('<a href="?seite=Titelseite&t={tk}" target="_blank" rel="noopener" style="border:1px solid {f};'
            'border-radius:8px;padding:4px 10px;font-size:14px;color:inherit;text-decoration:none"><b>{tk}</b> '
            '<span style="color:' + TEXT_2 + '">{text}</span></a>')
    neu_html = ("".join(chip.format(tk=t(tk), f=_farbe(tisch["titel"].get(tk)), text=t(text)) for tk, text in neu[:60])
                or f'<span style="color:{TEXT_2}">nichts Neues gegenüber dem letzten Lauf</span>')
    termine = []
    for tk, x in tisch["titel"].items():
        z = ((x.get("kacheln") or {}).get("Nächste Zahlen") or ("", "", ""))
        tage = 0 if z[1] == "heute" else 1 if z[1] == "morgen" else (int(z[1].split()[1]) if z[1].startswith("in ") else 99)
        if 0 <= tage <= 14:                    # vergangene Termine („in -1 Tagen“ älterer Tische) nicht mitzählen
            termine.append((tage, tk, z[2].split(" ·")[0], "Watchlist" if x["listen"] else namen.get(x.get("reihe"), "")))
    termine.sort()
    earn = ("".join(chip.format(tk=t(tk), f=_farbe(tisch["titel"].get(tk)), text=f"{t(d)} · {t(r)}")
                    for _, tk, d, r in termine)
            or f'<span style="color:{TEXT_2}">keine Zahlen in den nächsten 14 Tagen</span>')
    teile = [{"art": "html", "html": barometer
              + _klapp("Neu seit gestern", f"{len(neu)} Veränderungen gegenüber dem letzten Lauf", neu_html)
              + _klapp("Earnings 14 Tage", f"{len(termine)} Termine in Reihen und Watchlists"
                       + (f" · der nächste: {termine[0][1]} {termine[0][2]}" if termine else ""), earn)}]
    # Meine Watchlists: je Liste ein Abschnitt; jeder Titel einmal (im ersten Abschnitt, in dem er steht)
    teile.append({"art": "html", "html": _kopf("Meine Watchlists", len(watchlists.alle()),
                                                "jeder Titel immer, egal welche Ampel – die Marke zeigt seine Reihe; "
                                                "unter jeder Karte verschieben oder herausnehmen")})
    gezeigt = set()
    for name, liste in w.items():
        eigene = [tk for tk in liste if tk not in gezeigt]
        gezeigt.update(eigene)
        if not eigene:
            continue
        da = sorted(((tk, tisch["titel"][tk]) for tk in eigene if tk in tisch["titel"]),
                    key=lambda p: (-RANG.get(p[1].get("reihe"), 0), _ordnung(p[1])))
        teile.append(_abschnitt(_kopf(name, len(eigene), "", h=3), da, name,
                                [tk for tk in eigene if tk not in tisch["titel"]]))
    for key, name, text in REIHEN:
        liste = sorted(((tk, x) for tk, x in tisch["titel"].items() if x.get("reihe") == key and not x["listen"]),
                       key=lambda p: _ordnung(p[1]))
        teile.append(_abschnitt(_kopf(name, len(liste), text), liste))
    teile.append({"art": "html", "html": lagebild(tisch)
                  + f'<div style="font-size:13px;color:{TEXT_3}">Kartentisch gerechnet am {tisch["erzeugt"]} Uhr · '
                    f'„Deep Dive →“ öffnet die Titelseite in einem neuen Tab</div>'})
    return teile


def _marken(x):
    """Eine Marke über der Karte eines Watchlist-Titels: seine eigentliche Reihe (die Liste steht schon in der
    Abschnittsüberschrift)."""
    from gestaltung import TEXT_2, t
    r = {k: n for k, n, _ in REIHEN}.get(x.get("reihe"))
    if x.get("reihe") == "frueh" and x.get("angriff"):
        r += f" · {x['angriff']}"
    f, d = lagekarte.rahmen(x)
    g = lagekarte.grund(x)
    return (f'<span style="display:flex;flex-direction:column;gap:2px"><span style="border:{d}px solid {f};'
            f'border-radius:6px;padding:2px 8px;font-size:13px;color:{TEXT_2};align-self:flex-start">'
            f'{t(r or g or "noch keine Reihe")}</span>'
            + (f'<span style="font-size:13px;color:{TEXT_2}">{t(g)}</span>' if g and r else "") + '</span>')


# ── Lagekarte nach Sektoren (4.11.2026) ──
# Ein Bild unter den Reihen: Zeilen = Sektoren (Feld der Frontkarte, stärkste zuerst), Spalten = Reihen. Jeder Titel
# genau einmal, in der Spalte seiner Reihe; Watchlist-Titel mit ◆, ohne Reihe in der letzten Spalte. Die Themen-Gruppe
# steht als ⚑ am Ticker, wenn sie im Feld Führend oder Erstarkend ist (O'Neil: Führer kommen im Rudel).
SPALTEN = [("spitze", "★ Spitze"), ("frueh", "Radar"), ("weitere", "Weitere"), ("short", "Short"),
           (None, "◆ ohne Reihe")]
FELD_ORDNUNG = {"Führend": 0, "Erstarkend": 1, "Ermüdend": 2, "Abgehängt": 3}
ZELLE = 8                     # Marken je Zelle sichtbar, der Rest aufklappbar – nichts wird gefiltert


def _sektor_etf(tk, rv):
    import daten
    import sektoren
    if tk in rv.index:
        return rv.at[tk, "etf"]
    sb = daten.steckbrief_gespeichert(tk) or {}
    return sektoren.sektor_von(sb.get("sektor", "")) or "–"


def lagebild(tisch):
    import rudel
    import sektoren
    from frontkarte import FARBE, PFEILE, _pfeil
    from gestaltung import BLAU, GRUEN, RAND, ROT, TEXT_2, TEXT_3, karte, t, zahl
    try:
        rot = sektoren.rotation()
    except Exception:  # noqa: BLE001 – ohne Kurse der Sektor-ETFs nur die Zuordnung
        rot = {}
    rv = pd.read_csv(os.path.join(HIER, "..", "einstellungen", "revier.csv")).drop_duplicates("ticker").set_index("ticker")
    try:
        gruppen = {tk: g for g in rudel.themen() if g.get("feld") in ("Führend", "Erstarkend") for tk in g["mitglieder"]}
    except Exception:  # noqa: BLE001
        gruppen = {}
    zellen = {}
    for tk, x in tisch["titel"].items():
        if not x.get("reihe") and not x.get("listen"):
            continue
        zellen.setdefault((_sektor_etf(tk, rv), x.get("reihe")), []).append((tk, x))

    def marke(tk, x):
        stern = x.get("stern") or x.get("reihe") == "spitze"     # ★ long: jeder Spitzenkandidat (auch ältere Tische)
        rand, dicke = lagekarte.rahmen(x)                  # long grün, short rot, blass = Setup nicht grün, gelb = offen
        text = ("★ " if stern else "") + tk
        if x.get("reihe") == "frueh" and x.get("angriff"):
            text += " " + x["angriff"].split()[0]
        if x.get("listen"):
            text += " ◆"
        g = gruppen.get(tk)
        if g:
            text += " ⚑"
        zeilen = [f"<b>{t(tk)}</b> · {t({k: n for k, n, _ in REIHEN}.get(x.get('reihe'), 'keine Reihe'))}",
                  f"Zone: {t(x.get('zustand', '–'))}"]
        if x.get("reihe") == "frueh" and x.get("angriff"):
            art = x["angriff"][0]
            zeilen.append(f"Auslöser {t(x['angriff'])}: " + {"A": "Ausbruch aus reifer Zone", "F": "Fortsetzung (Flagge)",
                                                             "U": "Umkehr nach gescheitertem Ausbruch"}.get(art, ""))
        if stern:
            zeilen.append("★ Setup grün, Zone bewegt sich in Richtung des Setups")
        if lagekarte.grund(x):
            zeilen.append(t(lagekarte.grund(x)))
        if x.get("listen"):
            zeilen.append("◆ Watchlist: " + t(", ".join(x["listen"])))
        if g:
            zeilen.append(f"⚑ Themen-Gruppe {t(g['feld'])}: " + t(" · ".join(g["mitglieder"][:6]))
                          + (f" +{len(g['mitglieder']) - 6}" if len(g["mitglieder"]) > 6 else ""))
        tip = "<br>".join(zeilen)
        return (f'<span class="hinweis-zone" style="position:relative;display:inline-block">'
                f'<a href="?seite=Titelseite&t={tk}" target="_blank" rel="noopener" style="display:inline-block;border:{dicke}px solid {rand};'
                f'border-radius:6px;padding:2px 7px;font-size:13px;font-family:IBM Plex Mono,monospace;color:inherit;'
                f'text-decoration:none;white-space:nowrap">{t(text)}</a>'
                f'<span class="hinweis-tip" style="left:0;right:auto;width:320px;font-family:IBM Plex Sans,system-ui">'
                f'{tip}</span></span>')

    def zelle(liste):
        liste = sorted(liste, key=lambda p: _ordnung(p[1]))
        if not liste:
            return f'<span style="color:{TEXT_3}">–</span>'
        sicht = "".join(marke(tk, x) for tk, x in liste[:ZELLE])
        rest = liste[ZELLE:]
        if rest:
            sicht += (f'<details style="display:inline"><summary style="display:inline;cursor:pointer;color:{BLAU};'
                      f'font-size:13px">+{len(rest)}</summary> ' + " ".join(marke(tk, x) for tk, x in rest) + '</details>')
        return f'<div style="display:flex;flex-wrap:wrap;gap:5px;align-items:center">{sicht}</div>'

    etfs = sorted({e for e, _ in zellen}, key=lambda e: (FELD_ORDNUNG.get(rot.get(e, {}).get("feld"), 9),
                                                         -rot.get(e, {}).get("staerke", 0), e))
    raster = "190px repeat(5, minmax(0, 1fr))"
    kopf = (f'<div style="display:grid;grid-template-columns:{raster};gap:10px;padding:6px 0;font-size:13px;color:{TEXT_3};'
            f'letter-spacing:.05em;text-transform:uppercase"><span>Sektor · Feld · Stärke</span>'
            + "".join(f'<span>{t(n)} ({sum(len(v) for (e, r), v in zellen.items() if r == k)})</span>'
                      for k, n in SPALTEN) + '</div>')
    zeilen = []
    for e in etfs:
        r = rot.get(e)
        if r:
            pf = _pfeil(r)
            links = (f'<b>{t(r["name"])}</b><br><span style="color:{FARBE[r["feld"]]}">{t(r["feld"])}</span> '
                     f'<span title="{t(PFEILE[pf])}">{pf}</span> <span style="color:{TEXT_2}">{zahl(r["staerke"], 0)}</span>')
        else:
            links = f'<b>{t(sektoren.SEKTOREN.get(e, "ohne Sektor"))}</b>'
        zeilen.append(f'<div style="display:grid;grid-template-columns:{raster};gap:10px;padding:10px 0;'
                      f'border-top:1px solid {RAND};align-items:start"><div style="font-size:14px;line-height:1.5">{links}'
                      f'</div>' + "".join(f'<div>{zelle(zellen.get((e, k), []))}</div>' for k, _ in SPALTEN) + '</div>')
    hilfe = (f'<div style="font-size:13px;color:{TEXT_2};margin-top:8px">Zeilen: Sektoren nach Feld der Frontkarte '
             f'(Führend → Erstarkend → Ermüdend → Abgehängt), darin nach Stärke. Jeder Titel genau einmal, in der Spalte '
             f'seiner Reihe. Rahmen grün = long, rot = short, gelb = noch keine Reihe/Richtung offen (überall in der App) · kräftig mit ★ = Spitzenkandidat long bzw. Short an der Schwelle oder im Ausbruch · voll = Setup grün · blass = Setup noch nicht grün (Maus zeigt, was fehlt) · Radar mit '
             f'Auslöser (z. B. U↑) · ◆ = in deiner Watchlist · ⚑ = Themen-Gruppe Führend oder Erstarkend (Maus zeigt sie). '
             f'Sammeln sich Angriffe in einer Zeile, rückt dort ein Rudel vor.</div>')
    return karte(kopf + "".join(zeilen) + hilfe, "Lagekarte nach Sektoren · wo die Angriffe sich sammeln")
