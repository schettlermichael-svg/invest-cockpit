"""Kartentisch (4.11.2026, Zwei Systeme seit 05.11.2026): alle Titel des Abendlaufs einmal durchgerechnet, in Reihen
geordnet, als Lagekarten. Die Reihen ordnen, sie filtern nicht – jeder Titel bleibt über die Titelseite erreichbar.

System Minervini (M):
  ★ Spitze M          Setup grün (alle Regeln), Kurs am Pivot des Scanners (−5 % bis +5 %, seit 06.11.2026)
  Weitere M           Setup grün weiter weg vom Pivot oder genau eine Regel fehlt
System Kullamägi (K):
  Episodic Pivot      Sprung ab 10 % mit Lücke und Volumen ab 3-fach in den letzten 10 Tagen, Kurs hält das Tief
  Breakout            Führer (oberste 1–2 %) mit Konsolidierung 1–3 Wochen (gelb: knapp)
  Ermüdung (Short)    Flagge nach Fahnenstange ab 30 %, Schluss unter der Unterkante in den letzten 5 Tagen
                      (seit 06.11.2026 statt des Parabolic Short)
Beide:
  Watchlist           jeder Titel aus einstellungen/watchlists.json, immer; steht direkt nach ★ Spitze M
VCP-Scanner (für Titel ohne Reihe in den Systemen, seit 06.11.2026 statt der Wertzonen-Felder Ausbruch, Flagge, Radar):
  VCP · Enge grün     Zone mit grüner Enge, Kurs höchstens 5 % vom Pivot
  Flagge · Scanner    Flagge des Scanners (Kullamägi), auch als Flagge in einer Base
Ein Titel steht in genau einer Reihe (Vorrang in der Reihenfolge oben); die Lagekarte zeigt das Setup beider Systeme.

Rechnung in zwei Stufen: 1. alle Titel Erkennung, Wertzone und beide Systeme (mehrere Prozesse) → Reihe; 2. für die Titel
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
REIHEN = [("m_spitze", "★ Spitze · Minervini", "Setup grün (alle Regeln), Kurs am Pivot: höchstens 5 % darunter bis "
                                               "5 % darüber (Kaufzone)"),
          ("m_weitere", "Weitere · Minervini", "Setup grün, Kurs weiter weg vom Pivot – oder genau eine Regel fehlt"),
          ("k_ep", "Episodic Pivot · Kullamägi", "Sprung ab 10 % mit Lücke und Volumen ab 3-fach in den letzten 10 Tagen, "
                                                 "Kurs hält das Tief des Sprungtags; grün mit Nachricht (Zahlen)"),
          ("k_breakout", "Breakout · Kullamägi", "Führer (oberste 1–2 % nach 1/3/6 Monaten) mit Konsolidierung von 1–3 "
                                                 "Wochen; gelb = Führer knapp oder Konsolidierung bis 8 Wochen"),
          ("k_ermuedung", "Ermüdung nach Überdehnung · Short", "Flagge nach einer Fahnenstange ab 30 % in höchstens 13 "
                                                               "Wochen, dann Schluss unter der Unterkante (letzte 5 Tage); "
                                                               "Stopp über dem Hoch des Auslösetags; gelb = zurück in der "
                                                               "Flagge"),
          ("vcp", "VCP · Enge grün", "Zone des VCP-Scanners mit grüner Enge (mindestens 2 schrumpfende Kontraktionen, "
                                     "Enge höchstens 10 %, Volumen leiser als in der ersten), Kurs höchstens 5 % vom Pivot – "
                                     "für Titel, die in keinem System stehen"),
          ("flagge", "Flagge · Scanner", "Flagge des VCP-Scanners: Fahnenstange ab 30 % in höchstens 13 Wochen, Zone 1–8 "
                                         "Wochen, höchstens 25 % tief (Kullamägi), auch als Flagge in einer Base – für "
                                         "Titel, die in keinem System stehen")]
WATCHLISTS_NACH = "m_spitze"


def _fund_gespeichert(tk):
    """Fundament-Ampeln aus dem Zwischenspeicher, ohne Abruf (Stufe 1 rechnet über das ganze Revier)."""
    import fundament
    import quellen
    pfad = os.path.join(quellen.SPEICHER, f"{tk.upper()}.json")
    if not os.path.exists(pfad):
        return None, None
    try:
        fd = quellen._aus_json(json.load(open(pfad, encoding="utf-8")))
        return fundament.ampeln(fd), fd.get("gewinne")
    except Exception:  # noqa: BLE001
        return None, None


def _stufe1(tk):
    """Erkennung, Wertzone und beide Systeme eines Titels aus dem Speicher; Reihe oder None."""
    import absorption
    import daten
    import erkennung
    import rs_rang
    import system_kullamaegi
    import system_minervini
    from chart import reaktionen
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
        erk["kurs"] = float(df["Close"].iloc[-1])
        w = erk.get("werte") or {}
        erk["absorption"] = (absorption.absorption(df, w["start_index"], w["pivot"], w.get("ende_index"))
                             if erk["muster"] and "start_index" in w else None)
        fund, gewinne = _fund_gespeichert(tk)
        try:
            rang = rs_rang.rang(tk)[0]
        except Exception:  # noqa: BLE001
            rang = None
        import vcp_zone
        zs = vcp_zone.zone(df)
        scan = (zs, vcp_zone.enge(df, zs))      # VCP-Scanner einmal: für Minervini und die Scanner-Reihen
        m = system_minervini.pruefen(df, erk, rang, fund, scan)
        gtage = [d for d, _ in reaktionen(df, gewinne)] if gewinne is not None else []
        k = system_kullamaegi.pruefen(df, erk, gtage, ticker=tk)
        z = a["zustand"]
        c, h, l = df["Close"].to_numpy(float), df["High"].to_numpy(float), df["Low"].to_numpy(float)
        ph = erkennung._phase_von(df)
        info = {"tk": tk, "zustand": z["wort"], "zdir": z["dir"], "seite": erk.get("seite"),
                "phase": int(ph[-1]) if ph is not None else None,
                "hoch52": bool(len(h) >= 252 and h[-1] >= h[-252:].max()),
                "tief52": bool(len(l) >= 252 and l[-1] <= l[-252:].min()),
                "m": {"ampel": m["ampel"], "setup": m["setup"], "fehlt": [n for n, ok, _ in m["regeln"] if not ok]},
                "k": {"ampel": k["ampel"], "setup": k["setup"],
                      "ermuedung": (k["ermuedung"] or {}).get("ampel")}}
        bewegt = z["wort"].startswith(("an der Schwelle", "Ausbruch")) and z["dir"] == "↑"
        hk = k.get("haupt") or {}
        if m["pivot"]:
            info["abstand"] = abs((c[-1] / m["pivot"] - 1) * 100)
        elif hk.get("pivot"):
            info["abstand"] = abs((c[-1] / hk["pivot"] - 1) * 100)
        info["gruen"] = m["ampel"] == "grün" or (hk.get("ampel") == "grün")
        info["luecken"] = ([f"M: {x}" for x in info["m"]["fehlt"]] if m["ampel"] != "grün" else [])
        if k.get("ep") and k["ep"]["ampel"] != "rot":
            info.update(reihe="k_ep", stern=k["ep"]["ampel"] == "grün", gruen=k["ep"]["ampel"] == "grün")
        elif k.get("ermuedung"):
            em = k["ermuedung"]
            info.update(reihe="k_ermuedung", stern=em["ampel"] == "grün", gruen=em["ampel"] == "grün",
                        abstand=abs((c[-1] / em["unten"] - 1) * 100),
                        luecken=[] if em["ampel"] == "grün" else ["Short: zurück in der Flagge"])
        elif m["ampel"] == "grün" and m["abstand"] is not None and -PIVOT_NAH <= m["abstand"] <= KAUFZONE_M:
            info.update(reihe="m_spitze", stern=True)
        elif k.get("breakout") and k["breakout"]["ampel"] != "rot":
            b = k["breakout"]
            info.update(reihe="k_breakout", stern=b["ampel"] == "grün" and bewegt, gruen=b["ampel"] == "grün",
                        luecken=[f"K: {n}" for n, ok, _ in b["regeln"][:2] if not ok])
        elif m["ampel"] in ("grün", "gelb"):
            info["reihe"] = "m_weitere"
        if "reihe" not in info:                  # VCP-Scanner (Zone und Enge) für Titel ohne Reihe in den Systemen
            _scannerfeld(info, scan)
        return info
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Tisch steht trotzdem
        return None


PIVOT_NAH = 5.0               # VCP-Reihe: Kurs höchstens 5 % unter bzw. über dem Pivot
KAUFZONE_M = 5.0              # ★ Spitze M: höchstens 5 % unter dem Pivot bis 5 % darüber (Minervinis Kaufzone)


def _scannerfeld(info, scan):
    """VCP · Enge grün (Zone mit grüner Enge, Kurs nah am Pivot) oder Flagge · Scanner (Flagge, auch in einer Base)."""
    from gestaltung import zahl
    z, e = scan
    if not z.get("zone"):
        return
    if e.get("ampel") == "grün" and -PIVOT_NAH <= e["abstand"] <= PIVOT_NAH:
        info.update(reihe="vcp", gruen=True, stern=False, abstand=abs(e["abstand"]),
                    scanner=f'{z["name"]} {zahl(z["wochen"], 1)} Wochen · Enge {e["folge"]} % · Pivot {zahl(e["pivot"])} $ '
                            f'({"+" if e["abstand"] >= 0 else "−"}{zahl(abs(e["abstand"]), 1)} %)')
        return
    f = z if z["name"] == "Flagge" else z.get("innen")
    if f and f["laenge"] == "ok":
        nah = f["abstand"] >= -PIVOT_NAH
        info.update(reihe="flagge", gruen=nah, stern=False, abstand=abs(f["abstand"]),
                    scanner=f'Flagge {zahl(f["wochen"], 1)} Wochen, {zahl(f["tiefe"], 0)} % tief · Stange '
                            f'+{zahl(f["stange"]["prozent"], 0)} % in {zahl(f["stange"]["wochen"], 1)} Wochen · '
                            f'Kurs {zahl(f["abstand"], 1)} % zur Oberkante'
                            + (" · in einer Base" if f is not z else ""))


def _stufe2(tk):
    """Volle Titelseite (ohne Abruf neuer 30-Minuten-Kerzen): Lagekarte und Kacheln."""
    import titel
    try:
        r = titel.seite_titel(tk)
        try:
            titel.ablegen(tk, r)                 # für „Deep Dive“: die Titelseite liegt morgens fertig bereit
        except Exception:  # noqa: BLE001
            pass
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
    stufe1 += [{"tk": tk, "zustand": "keine Wertzone (Daten fehlen noch)", "hoch52": False, "tief52": False,
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
                "barometer": {"m_gruen": sum(1 for x in stufe1 if (x.get("m") or {}).get("ampel") == "grün"),
                              "k_gruen": sum(1 for x in stufe1 if (x.get("k") or {}).get("ampel") == "grün"),
                              "k_ermuedung": sum(1 for x in stufe1 if (x.get("k") or {}).get("ermuedung") == "grün"),
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
        felder = ("reihe", "stern", "gruen", "zdir", "luecken", "scanner")
        _REIHEN_CACHE[schluessel] = {k: {f: x.get(f) for f in felder} for k, x in tisch["titel"].items()}
    return _REIHEN_CACHE[schluessel].get(tk)


RANG = {"m_spitze": 5, "k_ep": 5, "k_ermuedung": 4, "k_breakout": 4, "m_weitere": 3, "vcp": 2, "flagge": 2, None: 0}


ALTE_REIHEN = {"spitze": "★ Spitzenkandidaten (alt)", "weitere": "Weitere Kandidaten (alt)", "short": "Short (alt)",
               "konsolidierung": "Ausbruch aus der Konsolidierung (alt)", "frueh": "Frühaufklärung (alt)",
               "k_parabolic": "Parabolic Short (alt)",
               "flagge_alt": "Flagge (alt)"}


def _neu(vorher, jetzt):
    """Neu seit gestern: neu in einer Reihe, vorgerückt, Phasenwechsel. Reihen älterer Tische (vor den zwei Systemen)
    werden mit ihrem alten Namen genannt."""
    if not vorher:
        return []
    alt, neu = vorher.get("titel", {}), jetzt["titel"]
    aus = []
    name = dict(ALTE_REIHEN, **{k: n for k, n, _ in REIHEN})
    name[None] = "keine Reihe"
    for tk, x in neu.items():
        r_alt = (alt.get(tk) or {}).get("reihe")
        r_neu = x.get("reihe")
        if x.get("listen"):                      # Watchlist-Titel: jeder Wechsel der Reihe, auch abwärts
            if tk in alt and (r_alt != r_neu or (x.get("stern") and not alt[tk].get("stern"))):
                aus.append((tk, f"◆ {name.get(r_alt, r_alt)} → {name.get(r_neu, r_neu)}"))
            continue
        if r_neu is None:
            continue
        if r_alt is None:
            aus.append((tk, f"neu in {name.get(r_neu, r_neu)}"))
        elif RANG.get(r_neu, 0) > RANG.get(r_alt, 0) or (x.get("stern") and not alt[tk].get("stern")):
            aus.append((tk, f"vorgerückt: {name.get(r_alt, r_alt)} → {name.get(r_neu, r_neu)}"))
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


def scanner_text(x):
    """Befund des VCP-Scanners für die Reihen „VCP · Enge grün“ und „Flagge · Scanner“, sonst leer."""
    return (x or {}).get("scanner") or ""


def _grundzeile(x):
    """Ausbruch und Grund als kleine Zeile über der Karte (leer, wenn nichts zu sagen ist)."""
    from gestaltung import TEXT_2, t
    g = " · ".join(z for z in (scanner_text(x), lagekarte.grund(x)) if z)
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
        return {"tk": tk, "farbe": GELB, "blass": False, "Setup": "neu – wird im Abendlauf gerechnet", "Wertzone": "",
                "Abstand %": "", "Was fehlt": ""}
    setup = (x.get("kacheln") or {}).get("Setup", ("grau", "–", ""))
    return {"tk": tk, "farbe": _farbe(x)[:7], "blass": len(_farbe(x)) > 7, "Setup": setup[1],
            "Wertzone": " · ".join(z for z in (x.get("zustand", ""), scanner_text(x)) if z),
            "Abstand %": zahl(x.get("abstand", 0), 1), "Was fehlt": lagekarte.grund(x)}


def _klapp(titel, zeile_, inhalt):
    """Karte zum Aufklappen (Übersicht kürzer): zu sieht man Titel und eine Zeile, aufgeklappt den Inhalt."""
    from gestaltung import KARTE, RAND, TEXT_2, t
    return (f'<details style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 20px">'
            f'<summary style="cursor:pointer;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap">'
            f'<span style="font-size:20px;font-weight:600">{t(titel)} ▾</span>'
            f'<span style="font-size:15px;color:{TEXT_2}">{t(zeile_)}</span></summary>'
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:14px">{inhalt}</div></details>')


def _ordnung(x):
    return (not x.get("stern"), not x.get("gruen"), x.get("abstand", 99))


def _kopf(name, zahl_, text, h=2):
    from gestaltung import TEXT_2, TEXT_3, t
    groesse = 26 if h == 2 else 19
    return (f'<div style="display:flex;align-items:baseline;gap:14px;margin:12px 0 4px"><h{h} style="margin:0;'
            f'font-size:{groesse}px">{t(name)} <span style="color:{TEXT_3};font-weight:500">{zahl_}</span></h{h}>'
            + (f'<span style="font-size:15px;color:{TEXT_2}">{t(text)}</span>' if text else "") + f'</div>')


def _abschnitt(name, text, liste, liste_name=None, fehlen=(), zahl_=None):
    """Ein Abschnitt für app.py: Karten (die ersten SICHTBAR mit Lagekarte) und Tabelle der übrigen. app.py zeigt ihn
    als Ausklappmenü (06.11.2026): zu sieht man Name, Zahl und Regel, aufgeklappt die Karten."""
    zahl_ = len(liste) + len(fehlen) if zahl_ is None else zahl_
    kopf = _kopf(name, zahl_, text)
    sichtbar = [(tk, x) for tk, x in liste[:SICHTBAR] if x.get("karte")]
    rest = liste[SICHTBAR:] + [(tk, x) for tk, x in liste[:SICHTBAR] if not x.get("karte")]
    return {"art": "abschnitt", "kopf": kopf, "name": name, "zahl": zahl_, "text": text, "liste": liste_name,
            "karten": [(tk, x, karte_html(x, _marken(x) if liste_name else "")) for tk, x in sichtbar],
            "zeilen": [zeile(tk, x) for tk, x in rest] + [zeile(tk, None) for tk in fehlen],
            "titel": {tk: x for tk, x in rest}}


def plan(tisch=None):
    """Kartentisch für die Übersicht als Folge von Teilen: {"art": "html", "html": …} oder ein Abschnitt (siehe
    _abschnitt). Watchlist-Zugehörigkeit immer aus den Listen der App (nicht aus dem Stand des Abendlaufs) – ein Titel,
    der eben auf eine Liste kam, steht sofort im Watchlist-Abschnitt und nicht mehr in seiner Reihe."""
    import watchlists
    from gestaltung import KARTE, RAND, TEXT_2, TEXT_3, karte, station, t, zahl
    tisch = tisch if tisch is not None else laden()
    if not tisch:
        return [{"art": "html", "html": karte(f'<p style="margin:0;font-size:15px;color:{TEXT_2}">Der Kartentisch wird '
                                              f'im Abendlauf gerechnet. Noch liegt kein Ergebnis vor.</p>', "Kartentisch")}]
    w = watchlists.laden()
    tisch = dict(tisch, titel={tk: dict(x, listen=[n for n, l in w.items() if tk in l],
                                        # Tisch von vor dem VCP-Scanner: die alte Wertzonen-Flagge trägt keinen
                                        # Scanner-Text und gehört nicht in die Reihe „Flagge · Scanner“
                                        **({"reihe": "flagge_alt"} if x.get("reihe") == "flagge"
                                           and not x.get("scanner") else {}))
                               for tk, x in tisch["titel"].items()})
    b = tisch["barometer"]
    if "m_gruen" in b:
        zahlen_ = f'{b["m_gruen"]} Minervini · {b["k_gruen"]} Kullamägi · {b.get("k_ermuedung", 0)} Ermüdung (short)'
    else:                                         # Tisch von vor den zwei Systemen
        zahlen_ = f'{b.get("long_gruen", 0)} long · {b.get("short_gruen", 0)} short'
    barometer = (
        f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 20px">'
        f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:.06em;text-transform:uppercase">Grüne Setups</div>'
        f'<div style="font-size:24px;font-weight:600">{zahlen_}</div>'
        f'<div style="font-size:14px;color:{TEXT_2}">unter {zahl(b["titel"], 0)} Titeln des Reviers</div></div>')
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
    # ② Front (Ende): Lagebild nach Sektoren · ③ Auswahl · ④ Termine – siehe uebersicht.py
    teile = [{"art": "html", "html": lagebild(tisch)},
             {"art": "html", "html": station("auswahl") + barometer}]

    def watchlist_abschnitte():
        """Watchlist: jeder Titel immer, egal welche Ampel – die Marke zeigt seine Reihe."""
        liste = w[watchlists.STANDARD]
        da = sorted(((tk, tisch["titel"][tk]) for tk in liste if tk in tisch["titel"]),
                    key=lambda p: (-RANG.get(p[1].get("reihe"), 0), _ordnung(p[1])))
        teile.append(_abschnitt("◆ Watchlist", "jeder Titel immer, egal welche Ampel – die Marke zeigt seine Reihe; "
                                "unter jeder Karte der Knopf zum Herunternehmen",
                                da, watchlists.STANDARD, [tk for tk in liste if tk not in tisch["titel"]], len(liste)))

    for key, name, text in REIHEN:
        liste = sorted(((tk, x) for tk, x in tisch["titel"].items() if x.get("reihe") == key and not x["listen"]),
                       key=lambda p: _ordnung(p[1]))
        teile.append(_abschnitt(name, text, liste))
        if key == WATCHLISTS_NACH:             # Watchlist direkt nach ★ Spitze (05.11.2026)
            watchlist_abschnitte()
    teile.append({"art": "html", "html": station("termine")
                  + _klapp("Neu seit gestern", f"{len(neu)} Veränderungen gegenüber dem letzten Lauf", neu_html)
                  + _klapp("Earnings 14 Tage", f"{len(termine)} Termine in Reihen und Watchlist"
                           + (f" · der nächste: {termine[0][1]} {termine[0][2]}" if termine else ""), earn)
                  + f'<div style="font-size:13px;color:{TEXT_3}">Kartentisch gerechnet am {tisch["erzeugt"]} Uhr · '
                    f'„Deep Dive →“ öffnet die Titelseite in einem neuen Tab</div>'})
    return teile


def _marken(x):
    """Eine Marke über der Karte eines Watchlist-Titels: seine eigentliche Reihe (die Liste steht schon in der
    Abschnittsüberschrift)."""
    from gestaltung import TEXT_2, t
    r = {k: n for k, n, _ in REIHEN}.get(x.get("reihe"))
    if scanner_text(x):
        r += f" · {scanner_text(x)}"
    f, d = lagekarte.rahmen(x)
    g = lagekarte.grund(x)
    return (f'<span style="display:flex;flex-direction:column;gap:2px"><span style="border:{d}px solid {f};'
            f'border-radius:6px;padding:2px 8px;font-size:13px;color:{TEXT_2};align-self:flex-start">'
            f'{t(r or g or "noch keine Reihe")}</span>'
            + (f'<span style="font-size:13px;color:{TEXT_2}">{t(g)}</span>' if g and r else "") + '</span>')


# ── Lagekarte nach Sektoren (4.11.2026, neu geordnet 6.11.2026) ──
# Eine Frage: an welchem Frontabschnitt sammeln sich die Angriffe, und wer führt dort? Zeilen = Sektoren, sortiert nach
# der Zahl der Angriffe (dann der Bereitstellung); drei Spalten statt neun: Angriff jetzt (Setup grün in einem der
# Systeme oder des VCP-Scanners, ★), Bereitstellung (übrige Reihen: Setup noch nicht grün, Flagge weiter weg) und ◆ Watchlist
# ohne Reihe. Je Zelle ein Balken mit der Zahl und die drei stärksten Titel; der Rest aufklappbar – nichts wird gefiltert.
SPALTEN = [("jetzt", "Angriff jetzt"), ("bereit", "Bereitstellung"), ("watch", "◆ Watchlist ohne Reihe")]
TOP = 3                       # Marken je Zelle sichtbar, der Rest aufklappbar


def _spalte(x):
    if not x.get("reihe"):
        return "watch"
    return "jetzt" if (x.get("stern") or x.get("gruen")) else "bereit"


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
    from gestaltung import BLAU, GRUEN, RAND, TEXT_2, TEXT_3, karte, t, zahl
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
        zellen.setdefault((_sektor_etf(tk, rv), _spalte(x)), []).append((tk, x))

    def marke(tk, x):
        stern = x.get("stern") or x.get("reihe") in ("m_spitze", "spitze")   # ★: jeder Spitzenkandidat (auch ältere Tische)
        rand, dicke = lagekarte.rahmen(x)                  # long grün, short rot, blass = Setup nicht grün, gelb = offen
        text = ("★ " if stern else "") + tk
        if x.get("reihe") in ("vcp", "flagge"):
            text += " VCP" if x["reihe"] == "vcp" else " F"
        if x.get("listen"):
            text += " ◆"
        g = gruppen.get(tk)
        if g:
            text += " ⚑"
        zeilen = [f"<b>{t(tk)}</b> · {t({k: n for k, n, _ in REIHEN}.get(x.get('reihe'), 'keine Reihe'))}",
                  f"Wertzone: {t(x.get('zustand', '–'))}"]
        if stern:
            zeilen.append("★ Setup grün, Kurs am Pivot")
        if scanner_text(x):
            zeilen.append("Scanner: " + t(scanner_text(x)))
        if lagekarte.grund(x):
            zeilen.append(t(lagekarte.grund(x)))
        if x.get("listen"):
            zeilen.append("◆ auf der Watchlist")
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

    hoechst = {k: max([len(v) for (e, s_), v in zellen.items() if s_ == k] or [1]) for k, _ in SPALTEN}
    farbe_sp = {"jetzt": GRUEN, "bereit": BLAU, "watch": TEXT_3}

    def zelle(liste, spalte):
        liste = sorted(liste, key=lambda p: (-RANG.get(p[1].get("reihe"), 0) if spalte == "watch" else 0, _ordnung(p[1])))
        if not liste:
            return f'<span style="color:{TEXT_3}">–</span>'
        breite = max(6, 100 * len(liste) / hoechst[spalte])
        balken = (f'<div style="display:flex;align-items:center;gap:8px"><div style="flex:1;height:8px;background:{RAND};'
                  f'border-radius:4px"><div style="width:{breite:.0f}%;height:8px;border-radius:4px;'
                  f'background:{farbe_sp[spalte]}"></div></div><b style="font-size:15px;min-width:22px;text-align:right">'
                  f'{len(liste)}</b></div>')
        sicht = "".join(marke(tk, x) for tk, x in liste[:TOP])
        rest = liste[TOP:]
        if rest:
            sicht += (f'<details style="display:inline"><summary style="display:inline;cursor:pointer;color:{BLAU};'
                      f'font-size:13px">+{len(rest)}</summary> ' + " ".join(marke(tk, x) for tk, x in rest) + '</details>')
        return balken + f'<div style="display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-top:6px">{sicht}</div>'

    zahl_von = lambda e, k: len(zellen.get((e, k), []))   # noqa: E731
    etfs = sorted({e for e, _ in zellen}, key=lambda e: (-zahl_von(e, "jetzt"), -zahl_von(e, "bereit"),
                                                         -rot.get(e, {}).get("staerke", 0), e))
    raster = "200px repeat(3, minmax(0, 1fr))"
    kopf = (f'<div style="display:grid;grid-template-columns:{raster};gap:16px;padding:6px 0;font-size:13px;color:{TEXT_3};'
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
        zeilen.append(f'<div style="display:grid;grid-template-columns:{raster};gap:16px;padding:12px 0;'
                      f'border-top:1px solid {RAND};align-items:start"><div style="font-size:14px;line-height:1.5">{links}'
                      f'</div>' + "".join(f'<div>{zelle(zellen.get((e, k), []), k)}</div>' for k, _ in SPALTEN) + '</div>')
    hilfe = (f'<div style="font-size:13px;color:{TEXT_2};margin-top:8px">Oben der Abschnitt mit den meisten Angriffen. '
             f'Angriff jetzt = Setup grün (Minervini, Kullamägi oder VCP-Scanner) · Bereitstellung = in einer '
             f'Reihe, Setup noch nicht grün · Balken = Zahl der Titel, je Spalte am größten Abschnitt gemessen · sichtbar '
             f'die drei stärksten, „+n“ klappt den Rest auf · ★ Spitze · ◆ Watchlist · ⚑ Themen-Gruppe Führend/Erstarkend · '
             f'Maus auf einen Titel zeigt Reihe, Wertzone und was fehlt.</div>')
    return karte(kopf + "".join(zeilen) + hilfe, "Lagekarte nach Sektoren · wo die Angriffe sich sammeln")
