"""Kartentisch (4.11.2026, Zwei Systeme seit 05.11.2026): alle Titel des Abendlaufs einmal durchgerechnet, in Reihen
geordnet, als Lagekarten. Die Reihen ordnen, sie filtern nicht – jeder Titel bleibt über die Titelseite erreichbar.

System Minervini (M):
  ★ Spitze M          Setup grün (alle Regeln) und die Wertzone steht an der Schwelle oder bricht nach oben aus
  Weitere M           Setup grün in Balance oder genau eine Regel fehlt
System Kullamägi (K):
  Episodic Pivot      Sprung ab 10 % mit Lücke und Volumen ab 3-fach in den letzten 10 Tagen, Kurs hält das Tief
  Breakout            Führer (oberste 1–2 %) mit Konsolidierung 1–3 Wochen (gelb: knapp)
  Parabolic Short     Serie steigender Tage im Revier (300 % kleine, 50 % große Werte) – dazu die Liste aus dem
                      ganzen US-Markt (parabolic.py)
Beide:
  Watchlist           jeder Titel aus einstellungen/watchlists.json, immer; steht direkt nach ★ Spitze M
  Ausbruchsfelder     frischer Ausbruch (A/U) bzw. Flagge (F) der Wertzone nach oben, mit Volumen, für Titel ohne Reihe
  Frühaufklärung      Radar: Wertzone an der Schwelle oder frischer Angriff nach oben
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
REIHEN = [("m_spitze", "★ Spitze · Minervini", "Setup grün (alle Regeln), die Wertzone steht an der Schwelle oder bricht "
                                               "nach oben aus"),
          ("m_weitere", "Weitere · Minervini", "Setup grün in Balance – oder genau eine Regel fehlt"),
          ("k_ep", "Episodic Pivot · Kullamägi", "Sprung ab 10 % mit Lücke und Volumen ab 3-fach in den letzten 10 Tagen, "
                                                 "Kurs hält das Tief des Sprungtags; grün mit Nachricht (Zahlen)"),
          ("k_breakout", "Breakout · Kullamägi", "Führer (oberste 1–2 % nach 1/3/6 Monaten) mit Konsolidierung von 1–3 "
                                                 "Wochen; gelb = Führer knapp oder Konsolidierung bis 8 Wochen"),
          ("k_parabolic", "Parabolic Short · Kullamägi", "Serie steigender Tage im Revier: ab 300 % (kleine Werte) bzw. "
                                                         "50 % (große Werte, Schwelle aus seinem Blog); grün an Tag 3–5"),
          ("konsolidierung", "Ausbruch aus der Konsolidierung",
           "frischer Ausbruch nach oben (A oder U, letzte 10 Handelstage, Volumen über dem 50-Tage-Schnitt) aus einer Wertzone "
           "von mindestens 3 Wochen, der noch hält – für Titel, die in keinem System stehen"),
          ("flagge", "Flagge", "frische Fortsetzung nach oben (F, letzte 10 Handelstage, Volumen über dem 50-Tage-Schnitt) "
                               "aus einer jungen Wertzone unter 3 Wochen – für Titel, die in keinem System stehen"),
          ("frueh", "Frühaufklärung", "Radar: Wertzone an der Schwelle oder frischer Angriff nach oben (A, F, U in 5 Tagen)")]
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
    import titel
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
        m = system_minervini.pruefen(df, erk, rang, fund)
        gtage = [d for d, _ in reaktionen(df, gewinne)] if gewinne is not None else []
        k = system_kullamaegi.pruefen(df, erk, gtage, titel.boersenwert(tk), tk)
        z = a["zustand"]
        c, h, l = df["Close"].to_numpy(float), df["High"].to_numpy(float), df["Low"].to_numpy(float)
        ph = erkennung._phase_von(df)
        info = {"tk": tk, "zustand": z["wort"], "zdir": z["dir"], "seite": erk.get("seite"),
                "phase": int(ph[-1]) if ph is not None else None,
                "hoch52": bool(len(h) >= 252 and h[-1] >= h[-252:].max()),
                "tief52": bool(len(l) >= 252 and l[-1] <= l[-252:].min()),
                "m": {"ampel": m["ampel"], "setup": m["setup"], "fehlt": [n for n, ok, _ in m["regeln"] if not ok]},
                "k": {"ampel": k["ampel"], "setup": k["setup"],
                      "parabolic": (k["parabolic"] or {}).get("ampel")}}
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
        elif k.get("parabolic"):
            ps = k["parabolic"]
            info.update(reihe="k_parabolic", stern=ps["ampel"] == "grün", gruen=ps["ampel"] == "grün",
                        abstand=0.0, luecken=[] if ps["ampel"] == "grün" else [f"K: Tag {ps['tag']} (erst Tag 3–5)"])
        elif m["ampel"] == "grün" and bewegt:
            info.update(reihe="m_spitze", stern=True)
        elif k.get("breakout") and k["breakout"]["ampel"] != "rot":
            b = k["breakout"]
            info.update(reihe="k_breakout", stern=b["ampel"] == "grün" and bewegt, gruen=b["ampel"] == "grün",
                        luecken=[f"K: {n}" for n, ok, _ in b["regeln"][:2] if not ok])
        elif m["ampel"] in ("grün", "gelb"):
            info["reihe"] = "m_weitere"
        # Radar (Frühaufklärung): Wertzone an der Schwelle oder ein frischer Angriff nach oben (A, F, U in 5 Tagen)
        n_ = len(a["tage"]) - 1
        frisch = [x for x in a["signale"] if x["art"] in ("A", "F", "U") and x["dir"] == "↑" and x["i"] >= n_ - 4]
        if "reihe" not in info:
            _ausbruchsfeld(info, a, df)
        if "reihe" not in info and (frisch or (z["wort"].startswith("an der Schwelle") and z["dir"] == "↑")):
            info.update(reihe="frueh", ausloeser=bool(frisch), abstand=info.get("abstand", 0.0),
                        angriff=(f"{frisch[-1]['art']}{frisch[-1]['dir']} {frisch[-1]['tag']:%d.%m.}" if frisch else None))
        return info
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Tisch steht trotzdem
        return None


FRISCH_TAGE = 10              # Ausbruchsfelder: Auslöser höchstens 10 Handelstage alt (und er hält noch)


def _ausbruchsfeld(info, a, df):
    """Ausbruch aus der Konsolidierung (A, U; B aus reifer Wertzone) bzw. Flagge (F; B aus junger Wertzone): die laufende
    Bewegung des Market Profile hält noch (kein S, keine neue reife Wertzone) und begann vor höchstens FRISCH_TAGE
    Handelstagen, mit Volumen am Ausbruchstag über dem 50-Tage-Schnitt. Geht vor jeder anderen Reihe (keine Doppelung). Vorlauf = Korrektur vom Hoch (long) bzw. Anstieg
    vom Tief (short) bis zum Ausbruch – nur ein Zeichen, kein Filter."""
    from marketprofile import ZONE_REIF
    akt = a.get("aktiv")
    if not akt or akt.get("art") not in ("A", "U", "F", "B"):
        return
    n_ = len(a["tage"]) - 1
    if n_ - akt["seit"] > FRISCH_TAGE - 1:
        return
    reif = akt["art"] in ("A", "U") or (akt["art"] == "B" and (akt["zone"].get("wochen") or 0) >= ZONE_REIF)
    d = akt["dir"]
    if d != "↑":                                 # Short nur noch als Parabolic Short (Kullamägi, 05.11.2026)
        return
    tag = a["tage"][akt["seit"]]["tag"]
    h = df.loc[:tag].iloc[-250:]
    vol = h["Volume"]
    faktor = float(vol.iloc[-1] / vol.iloc[-51:-1].mean()) if len(vol) > 20 else None
    if not faktor or faktor <= 1:                # Ausbruch ohne erhöhtes Volumen (nicht über dem 50-Tage-Schnitt)
        return
    import fussabdruck
    spanne = fussabdruck.atr_spanne(h, len(h) - 1)
    if d == "↑":
        hoch_i = h["High"].idxmax()
        vorlauf = (h.loc[hoch_i:, "Low"].min() / h["High"].max() - 1) * 100
    else:
        tief_i = h["Low"].idxmin()
        vorlauf = (h.loc[tief_i:, "High"].max() / h["Low"].min() - 1) * 100
    info.update(reihe="konsolidierung" if reif else "flagge", bdir=d, ausloeser=True,
                stern=False, vorlauf=round(float(vorlauf), 1),
                ausbruch=f"{akt['art']}{d} {tag:%d.%m.}", tage_seit=n_ - akt["seit"], vol_faktor=round(faktor, 1),
                atr_spanne=round(spanne, 1) if spanne else None,
                abstand=info.get("abstand", 0.0))


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
                              "k_parabolic": sum(1 for x in stufe1 if (x.get("k") or {}).get("parabolic") == "grün"),
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
        felder = ("reihe", "stern", "gruen", "angriff", "zdir", "luecken", "bdir", "ausbruch", "vorlauf")
        _REIHEN_CACHE[schluessel] = {k: {f: x.get(f) for f in felder} for k, x in tisch["titel"].items()}
    return _REIHEN_CACHE[schluessel].get(tk)


RANG = {"m_spitze": 5, "k_ep": 5, "k_parabolic": 4, "k_breakout": 4, "m_weitere": 3, "konsolidierung": 2, "flagge": 2,
        "frueh": 1, None: 0}


ALTE_REIHEN = {"spitze": "★ Spitzenkandidaten (alt)", "weitere": "Weitere Kandidaten (alt)", "short": "Short (alt)"}


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


def ausbruch_text(x):
    """„U↑ 02.11. · Korrektur −41 % davor“ für die Ausbruchsfelder, sonst leer."""
    import fussabdruck
    from gestaltung import zahl
    if (x or {}).get("reihe") not in ("konsolidierung", "flagge") or not x.get("ausbruch"):
        return ""
    v = x.get("vorlauf")
    art = "Korrektur" if x.get("bdir") == "↑" else "Anstieg"
    return (x["ausbruch"] + (f" · Volumen {zahl(x['vol_faktor'], 1)}-fach" if x.get("vol_faktor") else "")
            + (" · " + fussabdruck.spanne_text(x["atr_spanne"]) if x.get("atr_spanne") else "")
            + (f" · {art} {zahl(v, 0)} % davor" if v is not None else ""))


def _grundzeile(x):
    """Ausbruch und Grund als kleine Zeile über der Karte (leer, wenn nichts zu sagen ist)."""
    from gestaltung import TEXT_2, t
    g = " · ".join(z for z in (ausbruch_text(x), lagekarte.grund(x)) if z)
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
            "Wertzone": " · ".join(z for z in (x.get("zustand", ""), ausbruch_text(x)) if z),
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
    from gestaltung import KARTE, RAND, TEXT_2, TEXT_3, karte, station, t, zahl
    tisch = tisch if tisch is not None else laden()
    if not tisch:
        return [{"art": "html", "html": karte(f'<p style="margin:0;font-size:15px;color:{TEXT_2}">Der Kartentisch wird '
                                              f'im Abendlauf gerechnet. Noch liegt kein Ergebnis vor.</p>', "Kartentisch")}]
    w = watchlists.laden()
    tisch = dict(tisch, titel={tk: dict(x, listen=[n for n, l in w.items() if tk in l])
                               for tk, x in tisch["titel"].items()})
    b = tisch["barometer"]
    if "m_gruen" in b:
        zahlen_ = f'{b["m_gruen"]} Minervini · {b["k_gruen"]} Kullamägi · {b["k_parabolic"]} Parabolic Short'
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
        teile.append(_abschnitt(_kopf("◆ Watchlist", len(liste), "jeder Titel immer, egal welche Ampel – die Marke zeigt "
                                      "seine Reihe; unter jeder Karte der Knopf zum Herunternehmen"),
                                da, watchlists.STANDARD, [tk for tk in liste if tk not in tisch["titel"]]))

    for key, name, text in REIHEN:
        liste = sorted(((tk, x) for tk, x in tisch["titel"].items() if x.get("reihe") == key and not x["listen"]),
                       key=lambda p: _ordnung(p[1]))
        teile.append(_abschnitt(_kopf(name, len(liste), text), liste))
        if key == WATCHLISTS_NACH:             # Watchlist direkt nach ★ Spitze (05.11.2026)
            watchlist_abschnitte()
        if key == "k_parabolic":               # dazu der ganze US-Markt (Small Caps außerhalb des Reviers)
            teile.append({"art": "html", "html": parabolic_markt()})
    teile.append({"art": "html", "html": station("termine")
                  + _klapp("Neu seit gestern", f"{len(neu)} Veränderungen gegenüber dem letzten Lauf", neu_html)
                  + _klapp("Earnings 14 Tage", f"{len(termine)} Termine in Reihen und Watchlist"
                           + (f" · der nächste: {termine[0][1]} {termine[0][2]}" if termine else ""), earn)
                  + f'<div style="font-size:13px;color:{TEXT_3}">Kartentisch gerechnet am {tisch["erzeugt"]} Uhr · '
                    f'„Deep Dive →“ öffnet die Titelseite in einem neuen Tab</div>'})
    return teile


def parabolic_markt():
    """Parabolic-Short-Kandidaten aus dem ganzen US-Markt (Nachtlauf, parabolic.py) als Marken mit TradingView-Link."""
    import parabolic
    from gestaltung import AMPEL, KARTE, TEXT_2, t, zahl
    d = parabolic.laden()
    if not d:
        inhalt = f'<span style="color:{TEXT_2}">kommt mit dem nächsten Nachtlauf</span>'
        zeile_ = "noch keine Suche"
    else:
        tr = d["treffer"]
        zeile_ = (f'{len(tr)} Kandidaten · Stand {d["stand"]} · ab 300 % in Folge, Umsatz ab 5 Mio. $; '
                  f'grün = Tag 3–5 (Kullamägi: nie am ersten Tag, selten am zweiten)')
        inhalt = "".join(
            f'<a href="https://www.tradingview.com/chart/?symbol={t(x["ticker"])}" target="_blank" rel="noopener" '
            f'style="border:1px solid {AMPEL[x["ampel"]]};border-radius:8px;padding:4px 10px;font-size:14px;'
            f'color:inherit;text-decoration:none;background:{KARTE}"><b>{t(x["ticker"])}</b> '
            f'<span style="color:{TEXT_2}">Tag {x["tag"]} · +{zahl(x["gewinn"], 0)} % · {zahl(x["kurs"])} $ · '
            f'{zahl(x["umsatz_mio"], 0)} Mio. $</span></a>' for x in tr) or \
            f'<span style="color:{TEXT_2}">zurzeit keine Serie ab 300 %</span>'
    return _klapp("Parabolic Short im ganzen US-Markt", zeile_, inhalt)


def _marken(x):
    """Eine Marke über der Karte eines Watchlist-Titels: seine eigentliche Reihe (die Liste steht schon in der
    Abschnittsüberschrift)."""
    from gestaltung import TEXT_2, t
    r = {k: n for k, n, _ in REIHEN}.get(x.get("reihe"))
    if x.get("reihe") == "frueh" and x.get("angriff"):
        r += f" · {x['angriff']}"
    if ausbruch_text(x):
        r += f" · {ausbruch_text(x)}"
    f, d = lagekarte.rahmen(x)
    g = lagekarte.grund(x)
    return (f'<span style="display:flex;flex-direction:column;gap:2px"><span style="border:{d}px solid {f};'
            f'border-radius:6px;padding:2px 8px;font-size:13px;color:{TEXT_2};align-self:flex-start">'
            f'{t(r or g or "noch keine Reihe")}</span>'
            + (f'<span style="font-size:13px;color:{TEXT_2}">{t(g)}</span>' if g and r else "") + '</span>')


# ── Lagekarte nach Sektoren (4.11.2026, neu geordnet 6.11.2026) ──
# Eine Frage: an welchem Frontabschnitt sammeln sich die Angriffe, und wer führt dort? Zeilen = Sektoren, sortiert nach
# der Zahl der Angriffe (dann der Bereitstellung); drei Spalten statt neun: Angriff jetzt (Setup grün in einem der
# Systeme, ★ oder frischer Ausbruch), Bereitstellung (übrige Reihen: Setup noch nicht grün, Flagge, Radar) und ◆ Watchlist
# ohne Reihe. Je Zelle ein Balken mit der Zahl und die drei stärksten Titel; der Rest aufklappbar – nichts wird gefiltert.
SPALTEN = [("jetzt", "Angriff jetzt"), ("bereit", "Bereitstellung"), ("watch", "◆ Watchlist ohne Reihe")]
TOP = 3                       # Marken je Zelle sichtbar, der Rest aufklappbar


def _spalte(x):
    if not x.get("reihe"):
        return "watch"
    return "jetzt" if (x.get("stern") or x.get("gruen") or x.get("reihe") == "konsolidierung") else "bereit"


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
        if x.get("reihe") == "frueh" and x.get("angriff"):
            text += " " + x["angriff"].split()[0]
        if x.get("ausbruch"):
            text += " " + x["ausbruch"].split()[0]
        if x.get("listen"):
            text += " ◆"
        g = gruppen.get(tk)
        if g:
            text += " ⚑"
        zeilen = [f"<b>{t(tk)}</b> · {t({k: n for k, n, _ in REIHEN}.get(x.get('reihe'), 'keine Reihe'))}",
                  f"Wertzone: {t(x.get('zustand', '–'))}"]
        if x.get("reihe") == "frueh" and x.get("angriff"):
            art = x["angriff"][0]
            zeilen.append(f"Auslöser {t(x['angriff'])}: " + {"A": "Ausbruch aus reifer Wertzone", "F": "Fortsetzung (Flagge)",
                                                             "U": "Umkehr nach gescheitertem Ausbruch"}.get(art, ""))
        if stern:
            zeilen.append("★ Setup grün, Wertzone bewegt sich in Richtung des Setups")
        if ausbruch_text(x):
            zeilen.append("Ausbruch " + t(ausbruch_text(x)))
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
             f'Angriff jetzt = Setup grün (Minervini oder Kullamägi) oder frischer Ausbruch · Bereitstellung = in einer '
             f'Reihe, Setup noch nicht grün · Balken = Zahl der Titel, je Spalte am größten Abschnitt gemessen · sichtbar '
             f'die drei stärksten, „+n“ klappt den Rest auf · ★ Spitze · ◆ Watchlist · ⚑ Themen-Gruppe Führend/Erstarkend · '
             f'Maus auf einen Titel zeigt Reihe, Wertzone und was fehlt.</div>')
    return karte(kopf + "".join(zeilen) + hilfe, "Lagekarte nach Sektoren · wo die Angriffe sich sammeln")
