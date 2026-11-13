"""Kartentisch (4.11.2026; ein eigenes System seit 12.11.2026): alle Titel des Laufs einmal durchgerechnet, in Reihen
geordnet, als Lagekarten. Die Reihen ordnen, sie filtern nicht – jeder Titel bleibt über die Titelseite erreichbar.

Acht Setups (Namen nach dem, was sie sind; die Regeln stammen von den Meistern, siehe REIHEN und setup_feststellen):
  Base-Ausbruch (VCP)  ★ in der Kaufzone · weiter weg oder eine Regel fehlt · nur Muster (Regeln: Minervini)
  Flagge, Momentum-Ausbruch, Sprung (EP), Ermüdung (Short) (Regeln: Kullamägi; EP auch Bonde)
  Zahlen-Reaktion (Drift nach den Zahlen), Bärenflagge (Short), Bruch der Spanne (Short, seit 13.11.2026; Weinstein)
  Watchlist: jeder Titel aus einstellungen/watchlists.json, immer; steht direkt nach dem Base-Ausbruch ★
Ein Titel steht in genau einer Reihe (Vorrang in setup_feststellen); „auch“ nennt seine übrigen Setups.

Rechnung in zwei Stufen: 1. alle Titel VCP-Scanner, die Regeln und Auktion als Zeichen (mehrere Prozesse) → Reihe; 2.
für die Titel in einer Reihe die volle Titelseite (dieselben Kacheln, dieselbe Lagekarte). Ergebnis:
daten/kartentisch/<Datum>.json; die Übersicht liest nur diese Datei.
"""
import functools
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
from dateien import json_lesen, json_schreiben  # noqa: E402
SPEICHER = os.path.join(HIER, "..", "daten", "kartentisch")
REIHEN = [("m_spitze", "★ Base-Ausbruch · in der Kaufzone", "Base reif und eng (VCP), Trendvorlage, RS ab 70, Zahlen "
                                                          "wachsen – alle Regeln erfüllt, Kurs 5 % vor bis 5 % über dem "
                                                          "Pivot"),
          ("m_weitere", "Base-Ausbruch · weiter weg oder eine Regel fehlt", "Base-Ausbruch mit allen Regeln, aber Kurs "
                                                                             "weiter vom Pivot – oder genau eine Regel fehlt"),
          ("vcp", "Base-Ausbruch · nur Muster", "Base mit grüner Enge, Kurs höchstens 5 % vom Pivot, aber mehrere Regeln "
                                                "fehlen (meist Trendvorlage, RS oder Zahlen) – sichtbar, kommt nicht auf die "
                                                "Liste Einsatzbereit"),
          ("flagge", "Flagge", "Fahnenstange ab 30 % in höchstens 13 Wochen, Flagge 1–8 Wochen, höchstens 25 % tief, auch "
                               "in einer Base, Kurs über dem steigenden GD50, Volumen in der Flagge leiser als in der "
                               "Stange; grün, sobald der Kurs höchstens 5 % unter der Oberkante steht oder darüber (nach einem "
                               "Ausbruch: in der Kaufzone bis +5 %)"),
          ("k_breakout", "Momentum-Ausbruch", "Führer (oberste 1–2 % nach 1/3/6 Monaten) mit einer Pause von 1–3 Wochen "
                                              "nach einem Schub; gelb = Führer knapp oder Pause bis 8 Wochen"),
          ("k_ep", "Sprung (EP)", "Sprung ab 10 % mit Lücke und Volumen ab 3-fach in den letzten 10 Tagen, Kurs hält das "
                                  "Tief des Sprungtags; grün mit Nachricht (Zahlen)"),
          ("zahlen", "Zahlen-Reaktion · long und short", "Kurs reagiert auf die Zahlen ab 3 % (Short ab −3 %) in den "
                                                       "letzten 20 Handelstagen, Volumen über dem Schnitt, Schluss im "
                                                       "oberen (Short: unteren) Drittel, hält Tief und AVWAP des "
                                                       "Reaktionstags, Kurs über (unter) GD50; Einstieg am AVWAP"),
          ("k_ermuedung", "Ermüdung · Short", "Nach einer Fahnenstange ab 30 % bricht die Flagge nach unten (Schluss "
                                              "unter der Unterkante, letzte 5 Tage) – meist ein Führer; grün bis 5 % "
                                              "darunter; Stopp 1,5 ATR über der Unterkante, das Setup erlischt schon "
                                              "über dem Hoch des Auslösetags"),
          ("k_baerenflagge", "Bärenflagge · Short", "Steiler Fall ab 15 %, dann schwaches, leises Driften nach oben (GD50 "
                                                    "fällt), dann Schluss unter dem Tief der letzten 5 Tage des "
                                                    "Driftens; grün bis 5 % unter der Unterkante"),
          ("k_bruch", "Bruch der Spanne · Short", "Eine Basis (Phase 1) oder Verteilung (Phase 3) von mindestens 6 Wochen "
                                                  "bricht: Schluss mindestens 1 % unter ihrem Tief; grün bis 5 % "
                                                  "darunter")]
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


def _stufe1(tk, start=None):
    """VCP-Scanner, beide Systeme und die Auktion (Market Profile, nur Zeichen) eines Titels aus dem Speicher; Reihe
    oder None. Seit 06.11.2026 entscheidet die Wertzone nirgends mehr mit; ein Titel ohne 30-Minuten-Kerzen wird trotzdem
    gerechnet."""
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
        erk["kurs"] = float(df["Close"].iloc[-1])
        fund, gewinne = _fund_gespeichert(tk)
        try:
            rang = rs_rang.rang(tk)[0]
        except Exception:  # noqa: BLE001
            rang = None
        import vcp_zone
        zs = vcp_zone.zone(df)
        scan = (zs, vcp_zone.enge(df, zs))      # VCP-Scanner einmal: für Minervini und die Scanner-Reihen
        br = vcp_zone.ausbruch(df, jetzt=zs)    # Ausbruch (bis 4 Wochen, auch Fehlausbruch): Zone vom Vortag gilt weiter
        m = system_minervini.pruefen(df, erk, rang, fund, scan, br)
        gtage = [d for d, _ in reaktionen(df, gewinne)] if gewinne is not None else []
        k = system_kullamaegi.pruefen(df, erk, gtage, ticker=tk, scan=scan, br=br)
        z = a["zustand"] if a else {"wort": "keine 30-Minuten-Kerzen", "dir": ""}
        h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
        ph = erkennung._phase_von(df)
        info = {"tk": tk, "zustand": z["wort"], "zdir": z["dir"], "seite": erk.get("seite"),
                "phase": int(ph[-1]) if ph is not None else None,
                "hoch52": bool(len(h) >= 252 and h[-1] >= h[-252:].max()),
                "tief52": bool(len(l) >= 252 and l[-1] <= l[-252:].min()),
                "m": {"ampel": m["ampel"], "setup": m["setup"], "fehlt": [n for n, ok, _ in m["regeln"] if not ok]},
                "k": {"ampel": k["ampel"], "setup": k["setup"],
                      **{f_: (k.get(f_) or {}).get("ampel") for f_ in SHORTS.values()}}}
        import zahlen_reaktion
        info.update(setup_feststellen(df, m, k, zahlen_reaktion.pruefen(df, gewinne), scan))
        try:                                        # Kreislauf und Zeichen der Stärke/Schwäche (13.11.2026)
            import zeichen
            fa = info.get("ausbruch") if str(info.get("ausbruch") or "").startswith("🔴 Fehlausbruch") else None
            info["_kreislauf"] = zeichen.fuer_titel(tk, df, index, gewinne, start=start, fehlausbruch=fa)
            if info["_kreislauf"]:                  # Zustand im Code für Balance und Ungleichgewicht (13.11.2026)
                import auktion
                e = auktion.fuer_titel(tk, df, info["_kreislauf"], index, a, br, zs, gewinne)
                info["_kreislauf"]["auktion"] = auktion.speicherbar(e) if e else None
        except Exception:  # noqa: BLE001
            info["_kreislauf"] = None
        if info["_kreislauf"]:
            info["kreislauf"] = {"wort": info["_kreislauf"]["wort"], "phase": info["_kreislauf"]["phase"],
                                 "ziel": info["_kreislauf"]["ziel"]}
        return info
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Tisch steht trotzdem
        return None


NAME = {"m_spitze": "Base-Ausbruch ★", "m_weitere": "Base-Ausbruch", "vcp": "Base-Ausbruch · nur Muster",
        "flagge": "Flagge", "k_breakout": "Momentum-Ausbruch", "k_ep": "Sprung (EP)", "zahlen": "Zahlen-Reaktion",
        "k_ermuedung": "Ermüdung (Short)", "k_baerenflagge": "Bärenflagge (Short)", "k_bruch": "Bruch der Spanne (Short)"}
from system_kullamaegi import SHORTS, short_von   # noqa: E402  Reihe → Feld in k (Ermüdung, Bärenflagge, Bruch)
LEHRER = {"m_spitze": "M", "m_weitere": "M", "vcp": "M", "flagge": "K", "k_breakout": "K", "k_ep": "K", "zahlen": "K",
          "k_ermuedung": "K", "k_baerenflagge": "K", "k_bruch": "K"}      # aus wessen Regeln die Kacheln urteilen (Meister als Lehrer)


def setup_feststellen(df, m, k, zr, scan):
    """Das eine Setup eines Titels (Micky 12.11.2026: ein eigenes System, ein Urteil je Titel) – für Kartentisch und
    Titelseite dieselbe Entscheidung. Vorrang: Sprung (EP) → Zahlen-Reaktion → Ermüdung/Bärenflagge/Bruch der Spanne → Base-Ausbruch ★
    (Kaufzone) → Flagge → Momentum-Ausbruch → Base-Ausbruch (weiter weg oder eine Regel fehlt) → Base-Ausbruch · nur
    Muster. „auch“ nennt die übrigen Setups, die der Titel zeigt (nichts geht verloren).
    → {reihe, gruen, stern, abstand, abstand_vz, luecken, zr, zr_seite, short_art, still, scanner, ausbruch, auch}"""
    import atr as atr_
    import depot
    import vcp_zone
    c = df["Close"].to_numpy(float)
    info = {}
    hk = k.get("haupt") or {}
    info["gruen"] = m["ampel"] == "grün" or (hk.get("ampel") == "grün")
    info["luecken"] = ([f"Base-Ausbruch: {n}" for n, ok, _ in m["regeln"] if not ok] if m["ampel"] != "grün" else [])
    if zr:
        info["zr"] = {k_: zr[k_] for k_ in ("ampel", "seite", "tag", "pct", "volumen", "schluss_lage", "tage_her",
                                            "avwap", "tief", "hoch", "halten", "text")}
    sf = {}
    if scan:
        _scannerfeld(sf, scan, m["ausbruch"], df)     # Flagge oder Muster des Scanners – dieselbe Zone wie Minervini und Chart
    gefunden = []                                  # alle Setups, die der Titel zeigt (für „auch“)
    if k.get("ep") and k["ep"]["ampel"] != "rot":
        gefunden.append("k_ep")
    if zr and zr["ampel"] != "rot" and zr["abstand"] is not None:
        gefunden.append("zahlen")
    for r_s in SHORTS:                             # Ermüdung → Bärenflagge → Bruch der Spanne
        if short_von(k, r_s):
            gefunden.append(r_s)
    if m["ampel"] == "grün" and m["abstand"] is not None and -PIVOT_NAH <= m["abstand"] <= KAUFZONE_M:
        gefunden.append("m_spitze")
    if sf.get("reihe") == "flagge":
        gefunden.append("flagge")
    if k.get("breakout") and k["breakout"]["ampel"] != "rot":
        gefunden.append("k_breakout")
    if m["ampel"] in ("grün", "gelb") and "m_spitze" not in gefunden:
        gefunden.append("m_weitere")
    if sf.get("reihe") == "vcp":
        gefunden.append("vcp")
    r_ = gefunden[0] if gefunden else None
    if r_ == "k_ep":
        info.update(reihe="k_ep", stern=k["ep"]["ampel"] == "grün", gruen=k["ep"]["ampel"] == "grün")
    elif r_ == "zahlen":
        e_ = -zr["abstand"] if zr["seite"] == "short" else zr["abstand"]
        info.update(reihe="zahlen", zr_seite=zr["seite"], gruen=zr["ampel"] == "grün",
                    stern=bool(zr["ampel"] == "grün" and 0 <= e_ <= KAUFZONE_M), abstand=float(abs(zr["abstand"])),
                    abstand_vz=float(zr["abstand"]), luecken=zr["luecken"])
    elif r_ in SHORTS:
        em = short_von(k, r_)
        short_art = em["art"]
        ab_ = float((c[-1] / em["unten"] - 1) * 100)
        # Short-Zone wie die Kaufzone gespiegelt (12.11.2026: DT stand 21,9 %, ALNY 25,2 % unter der Unterkante als
        # ★ – der Fall war längst gelaufen, der Stopp über dem Auslösetag 40 % entfernt)
        gruen_ = em["ampel"] == "grün" and -KAUFZONE_M <= ab_ <= 0
        info.update(reihe=r_, short_art=short_art, stern=gruen_, gruen=gruen_, abstand=abs(ab_), abstand_vz=ab_,
                    luecken=[] if gruen_ else ["Short: zurück über der Unterkante"] if em["ampel"] != "grün"
                    else [f"Short: schon {-ab_:.1f} % unter der Unterkante – gelaufen".replace(".", ",")])
    elif r_ == "m_spitze":
        info.update(reihe="m_spitze", stern=True)
    elif r_ in ("flagge", "vcp"):
        info.update(sf)
    elif r_ == "k_breakout":
        b = k["breakout"]
        am_pivot = b.get("abstand") is not None and -PIVOT_NAH <= b["abstand"] <= KAUFZONE_M and \
            not (b.get("ausbruch") or {}).get("fehl")
        info.update(reihe="k_breakout", stern=b["ampel"] == "grün" and am_pivot, gruen=b["ampel"] == "grün",
                    luecken=[f"Momentum-Ausbruch: {n}" for n, ok, _ in b["regeln"][:3] if not ok])
    elif r_ == "m_weitere":
        info["reihe"] = "m_weitere"
    # Einstieg DES Setups (Prüf-Agent 12.11.2026): einmal hier festgestellt und gespeichert – Chart, Plan, Lagekarte
    # und Auswahl lesen ihn; der Abstand gilt nur zu diesem Einstieg (vorher zuerst zur alten Pivot-Kette).
    seite_, e_, quelle_ = depot.einstieg_setup(info | {"reihe": r_}, m, k, zr, c[-1]) if r_ else (None, None, "")
    if e_:
        info["einstieg"] = {"seite": seite_, "wert": float(e_), "quelle": quelle_}
        info["abstand_vz"] = float((c[-1] / e_ - 1) * 100)
        info["abstand"] = abs(info["abstand_vz"])
    else:
        info.pop("abstand_vz", None)
        info.pop("abstand", None)
    info["auch"] = [NAME[x] for x in gefunden[1:] if NAME.get(x) != NAME.get(r_)]
    kb_ = (k.get("breakout") or {}).get("ausbruch")   # Ausbruchszeichen des Setups (12.11.2026: TREX im EP zeigte eine
    zeichen_br = (m["ausbruch"] if r_ in ("m_spitze", "m_weitere", "vcp", "flagge") else kb_ if r_ == "k_breakout"
                  else None if r_ in ("k_ep", "zahlen", *SHORTS)   # alte Konsolidierung)
                  else m["ausbruch"] if m.get("pivot") else kb_)
    a_ = atr_.wert(df)
    if info.get("reihe") and a_ and a_ / c[-1] * 100 < STILL_PCT:
        # Kurs steht still (12.11.2026: ARX bei 19,85 $ mit 0,06 $ Tagesspanne – Übernahmeangebot, kein Setup;
        # der Stopp lag 0,07 $ unter dem Pivot): bleibt in der Reihe, wird aber nicht grün
        info.update(gruen=False, stern=False, still=True,
                    luecken=(info.get("luecken") or []) + [f"Kurs steht still: Tagesspanne {a_ / c[-1] * 100:.2f} % – "
                                                           f"Übernahme?".replace(".", ",")])
    if r_ == "zahlen":
        info["ausbruch"] = zr["text"]
    elif r_ == "k_ermuedung":
        info["ausbruch"] = "▼ Ermüdung nach Überdehnung: die Flagge nach der Fahnenstange bricht nach unten"
    elif r_ == "k_baerenflagge":
        info["ausbruch"] = "▼ Bärenflagge: steiler Fall, schwaches Driften nach oben, dann Bruch der Unterkante"
    elif r_ == "k_bruch":
        info["ausbruch"] = "▼ Bruch der Spanne: Schluss unter dem Tief der " + (
            "Basis" if "Basis" in str(short_von(k, r_)["regeln"][0][0]) else "Verteilung")
    if zeichen_br:                           # Zeichen auf jeder Karte: Ausbruch mit/ohne Volumen, Fehlausbruch
        info["ausbruch"] = vcp_zone.ausbruch_text(zeichen_br)
    if zeichen_br and (zeichen_br.get("fehl") or zeichen_br.get("ruecktest")):
        # Fehlausbruch (13.11.2026: Schluss unter dem Tief des Ausbruchstags oder > 3 % unter dem Pivot) und Rücktest
        # sind nicht einsatzbereit, bleiben aber in der Reihe unter Beobachtung
        info.update(gruen=False, stern=False, luecken=(info.get("luecken") or []) + [
            "Fehlausbruch – beobachten" if zeichen_br.get("fehl") else "Rücktest des Pivots – beobachten"])
    info["gruen"], info["stern"] = bool(info.get("gruen")), bool(info.get("stern"))
    return info


STILL_PCT = 0.5               # ATR unter 0,5 % des Kurses: der Kurs steht still (Übernahme), kein handelbares Setup
PIVOT_NAH = 5.0               # VCP-Reihe: Kurs höchstens 5 % unter bzw. über dem Pivot
KAUFZONE_M = 5.0              # ★ Spitze M: höchstens 5 % unter dem Pivot bis 5 % darüber (Minervinis Kaufzone)


def flagge_im_trend(df, f):
    """Eine Flagge zählt nur im Aufwärtstrend und bei leisem Volumen (Prüf-Agent 13.11.2026: sie wurde auch in Phase 4
    grün): Kurs über dem steigenden GD50 und Volumen in der Flagge leiser als in der Fahnenstange → (ok, Lücken)."""
    if df is None or len(df) < 70 or not f:
        return True, []
    c, v = df["Close"].to_numpy(float), df["Volume"].to_numpy(float)
    g50 = df["Close"].rolling(50).mean().to_numpy(float)
    luecken = []
    if not (c[-1] > g50[-1] and g50[-1] > g50[-21]):
        luecken.append("Flagge: kein Aufwärtstrend (Kurs unter dem GD50 oder GD50 fällt)")
    i0, s0 = int(f.get("start_i", 0)), int((f.get("stange") or {}).get("von_i", 0))
    if i0 > s0 and i0 < len(v):
        flg, stg = v[i0:].mean(), v[s0:i0 + 1].mean()
        if stg and flg >= stg:
            luecken.append(f"Flagge: Volumen nicht leiser als in der Fahnenstange ({flg / stg:.2f}-fach)".replace(".", ","))
    return not luecken, luecken


def _scannerfeld(info, scan, br=None, df=None):
    """VCP · Enge grün (Zone mit grüner Enge, Kurs nah am Pivot) oder Flagge · Scanner (Flagge, auch in einer Base).
    Nach einem Ausbruch (br, bis 4 Wochen, auch Fehlausbruch) gilt die Zone vom Vortag."""
    from gestaltung import zahl
    if br:
        bz, be = br["zone"], br["enge"]
        if be.get("ampel") == "grün" and abs(br["abstand"]) <= PIVOT_NAH:
            info.update(reihe="vcp", gruen=not br["fehl"], stern=False, abstand=abs(br["abstand"]), abstand_vz=br["abstand"],
                        pivot_scanner=float(br["pivot"]),
                        scanner=f'{bz["name"]} {zahl(bz["wochen"], 1)} Wochen · Enge {be["folge"]} % · Pivot '
                                f'{zahl(br["pivot"])} $')
            return
        if bz.get("name") == "Flagge":
            ok_, l_ = flagge_im_trend(df, bz)
            info.update(reihe="flagge", gruen=br["kaufzone"] and ok_, stern=False, luecken=l_, abstand=abs(br["abstand"]), abstand_vz=br["abstand"],
                        pivot_scanner=float(br["pivot"]),
                        scanner=f'Flagge {zahl(bz["wochen"], 1)} Wochen, {zahl(bz["tiefe"], 0)} % tief · Stange '
                                f'+{zahl(bz["stange"]["prozent"], 0)} % · Pivot {zahl(br["pivot"])} $'
                                + (" · in einer Base" if br["innen"] else ""))
            return
    z, e = scan
    if not z.get("zone"):
        return
    if e.get("ampel") == "grün" and -PIVOT_NAH <= e["abstand"] <= PIVOT_NAH:
        info.update(reihe="vcp", gruen=True, stern=False, abstand=abs(e["abstand"]), abstand_vz=e["abstand"],
                    pivot_scanner=float(e["pivot"]),
                    scanner=f'{z["name"]} {zahl(z["wochen"], 1)} Wochen · Enge {e["folge"]} % · Pivot {zahl(e["pivot"])} $ '
                            f'({"+" if e["abstand"] >= 0 else "−"}{zahl(abs(e["abstand"]), 1)} %)')
        return
    f = z if z["name"] == "Flagge" else z.get("innen")
    if f and f["laenge"] == "ok":
        nah = f["abstand"] >= -PIVOT_NAH
        ok_, l_ = flagge_im_trend(df, f)
        info.update(reihe="flagge", gruen=nah and ok_, stern=False, luecken=l_, abstand=abs(f["abstand"]), abstand_vz=f["abstand"],
                    pivot_scanner=float(f["oben"]),
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
    import daten
    import zeichen
    try:                                            # Beginn der Marktschwäche einmal für alle Titel
        start = zeichen.startdatum(daten.kurse_gespeichert(daten.INDEX))
    except Exception:  # noqa: BLE001
        start = zeichen.KEIN
    with ProcessPoolExecutor(prozesse) as ex:
        stufe1 = [x for x in ex.map(functools.partial(_stufe1, start=start), ticker_liste, chunksize=20) if x]
    melden(f"  Stufe 1: {len(stufe1)} Titel gerechnet in {time.time() - beginn:.0f} s")
    import watchlists
    w = watchlists.laden()
    beobachtet = set(watchlists.alle())
    gerechnet = {x["tk"] for x in stufe1}
    stufe1 += [{"tk": tk, "zustand": "Kurse fehlen noch", "hoch52": False, "tief52": False,
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
    zeichen.ablegen(stand, {x["tk"]: x.pop("_kreislauf") for x in stufe1 if x.get("_kreislauf")})
    for x in stufe1:
        x.pop("_kreislauf", None)
    vorher = laden()
    ergebnis = {"stand": stand, "erzeugt": time.strftime("%d.%m.%Y %H:%M"),
                "barometer": {"m_gruen": sum(1 for x in stufe1 if (x.get("m") or {}).get("ampel") == "grün"),
                              "k_gruen": sum(1 for x in stufe1 if (x.get("k") or {}).get("ampel") == "grün"),
                              "k_ermuedung": sum(1 for x in stufe1 if (x.get("k") or {}).get("ermuedung") == "grün"),
                              "k_short": sum(1 for x in stufe1 if any((x.get("k") or {}).get(f_) == "grün"
                                                                      for f_ in SHORTS.values())),
                              "hochs": sum(x["hoch52"] for x in stufe1), "tiefs": sum(x["tief52"] for x in stufe1),
                              "titel": len(stufe1)},
                "titel": {x["tk"]: {k: v for k, v in x.items() if k != "tk"} for x in in_reihe},
                "phasen": {x["tk"]: x["phase"] for x in stufe1}}
    ergebnis["neu"] = _neu(vorher, ergebnis)
    os.makedirs(SPEICHER, exist_ok=True)
    json_schreiben(os.path.join(SPEICHER, f"{stand}.json"), ergebnis, ensure_ascii=False)
    return ergebnis


def laden():
    """Jüngster gespeicherter Kartentisch oder None."""
    if not os.path.isdir(SPEICHER):
        return None
    for f in sorted((f for f in os.listdir(SPEICHER) if f.endswith(".json")), reverse=True):
        tisch = json_lesen(os.path.join(SPEICHER, f))           # kaputter Tisch: der davor
        if tisch is not None:
            return tisch
    return None


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
        tisch = json_lesen(pfad, {"titel": {}})
        felder = ("reihe", "stern", "gruen", "zdir", "luecken", "scanner", "ausbruch", "short_art", "zr_seite", "zr", "auch",
                  "einstieg")
        _REIHEN_CACHE[schluessel] = {k: {f: x.get(f) for f in felder} for k, x in tisch["titel"].items()}
    return _REIHEN_CACHE[schluessel].get(tk)


RANG = {"m_spitze": 5, "k_ep": 5, "zahlen": 5, "k_ermuedung": 4, "k_baerenflagge": 4, "k_bruch": 4, "flagge": 4,
        "k_breakout": 4,
        "m_weitere": 3, "vcp": 1, None: 0}


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
    """Befund des VCP-Scanners (Reihen „VCP · Enge grün“ und „Flagge · Scanner“) und das Zeichen eines frischen
    Ausbruchs mit oder ohne Volumen (jede Reihe), sonst leer."""
    x = x or {}
    return " · ".join(z for z in (x.get("scanner"), x.get("ausbruch")) if z)


def _grundzeile(x):
    """Ausbruch und Grund als kleine Zeile über der Karte (leer, wenn nichts zu sagen ist)."""
    from gestaltung import TEXT_2, t
    g = " · ".join(z for z in (scanner_text(x), lagekarte.grund(x)) if z)
    return f'<span style="font-size:13px;color:{TEXT_2}">{t(g)}</span>' if g else ""


def stab_marke(x):
    """Marke über jeder Karte (Seite Setups, 12.11.2026): 🎯 auf der Liste „Einsatzbereit“ oder der Grund, warum nicht."""
    from gestaltung import BLAU, TEXT_3, t
    st_ = (x or {}).get("stab")
    if not st_:
        return ""
    drin, grund = st_
    if drin:
        return (f'<span style="font-size:13px;color:{BLAU};font-weight:600">🎯 einsatzbereit'
                f'<span style="font-weight:400"> · {t(grund)}</span></span>')
    return f'<span style="font-size:13px;color:{TEXT_3}">nicht auf der Liste · {t(grund)}</span>'


def rueckenwind_zeichen(x):
    """Zeichen „Rückenwind“ (Seite Rückenwind, 09.11.2026): Kurs · Geld · Zahlen als Ampeln und die Stufe."""
    rw = (x or {}).get("rueckenwind")
    if not rw:
        return ""
    p = {"grün": "🟢", "gelb": "🟡", "rot": "🔴"}
    if lagekarte.richtung(x) == "short":              # Short: Kurs und Geld gespiegelt (Prüf-Agent 12.11.2026)
        import auswahl as auswahl_
        g = lambda a: auswahl_._GEGEN.get(a, a)       # noqa: E731
        return (f'Gegenwind für long = Rückenwind für Short · Kurs {p.get(g(rw["kurs"]), "⚪")} '
                f'Geld {p.get(g(rw["geld"]), "⚪")}' + (f' · {rw["stufe"]}' if rw.get("stufe") else ""))
    return (f'Rückenwind Kurs {p.get(rw["kurs"], "⚪")} Geld {p.get(rw["geld"], "⚪")} Zahlen {p.get(rw["zahlen"], "⚪")}'
            + (f' · {rw["stufe"]}' if rw.get("stufe") else ""))


def karte_html(x, kopf="", tk=None):
    """Lagekarte in der Rahmenstufe des Titels, darüber eine Zeile (Reihe-Marke im Watchlist-Abschnitt, sonst der
    Grund, was fehlt), das Zeichen „Rückenwind“ und der Kreislauf (Mini-Kurve des Jahres und Phase, 13.11.2026)."""
    from gestaltung import TEXT_2, t
    kopf = stab_marke(x) + (kopf or _grundzeile(x))
    rw = rueckenwind_zeichen(x)
    rw = f'<span style="font-size:13px;color:{TEXT_2}">{t(rw)}</span>' if rw else ""
    return (f'<div style="display:flex;flex-direction:column;gap:6px">{kopf}{rw}{kreislauf_zeile(tk)}'
            f'{lagekarte.faerben(x["karte"], x)}</div>')


def kreislauf_zeile(tk):
    """Mini-Kurve des Jahres nach Phasen gefärbt und die Phase in einem Wort; ein Klick öffnet die Titelseite."""
    if not tk:
        return ""
    try:
        import kreislaufbild
        import zeichen
        k = zeichen.von(tk)
    except Exception:  # noqa: BLE001
        return ""
    if not k:
        return ""
    from gestaltung import TEXT_2, t
    import zustandsbild                      # zuerst der Zustand (13.11.2026), die Phase als Unterzeile
    return (f'<a href="?seite=Titelseite&t={t(tk)}" target="_self" style="display:flex;align-items:center;gap:8px;'
            f'flex-wrap:wrap;text-decoration:none">{zustandsbild.pille(k.get("auktion"))}{kreislaufbild.mini(k)}'
            f'<span style="font-size:13px;color:{TEXT_2}">{t(kreislaufbild.punkt_wort(k))}</span></a>')


def zeile(tk, x):
    """Eine Tabellenzeile für die übrigen Titel (Reihenfolge wie die Karten)."""
    from gestaltung import GELB, zahl
    if x is None:
        return {"tk": tk, "farbe": GELB, "blass": False, "Setup": "neu – wird im Abendlauf gerechnet", "Befund": "", "Stab": "",
                "Abstand %": "", "Was fehlt": ""}
    setup = (x.get("kacheln") or {}).get("Setup", ("grau", "–", ""))
    st_ = x.get("stab")
    return {"tk": tk, "farbe": _farbe(x)[:7], "blass": len(_farbe(x)) > 7, "Setup": setup[1],
            "Stab": ("🎯 " if st_[0] else "") + st_[1] if st_ else "",
            "Befund": " · ".join(z for z in (rueckenwind_zeichen(x), scanner_text(x),
                                             "Market Profile: " + x["zustand"] if x.get("zustand") else "") if z),
            "Abstand %": zahl(x["abstand_vz"], 1) if x.get("abstand_vz") is not None else "",   # ohne Einstieg leer
            "Zustand": _zustand_wort(tk), "Phase": _phase_wort(tk), "Was fehlt": lagekarte.grund(x)}


def _zustand_wort(tk):
    try:
        import auktion
        import zeichen
        return auktion.wort((zeichen.von(tk) or {}).get("auktion"))
    except Exception:  # noqa: BLE001
        return ""


def _phase_wort(tk):
    try:
        import kreislaufbild
        import zeichen
        return kreislaufbild.punkt_wort(zeichen.von(tk))
    except Exception:  # noqa: BLE001
        return ""


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
            + (f'<span style="font-size:15px;color:{TEXT_2}">{t(text)}</span>' if text else "") + '</div>')


def _abschnitt(name, text, liste, liste_name=None, fehlen=(), zahl_=None):
    """Ein Abschnitt für app.py: Karten (die ersten SICHTBAR mit Lagekarte) und Tabelle der übrigen. app.py zeigt ihn
    als Ausklappmenü (06.11.2026): zu sieht man Name, Zahl und Regel, aufgeklappt die Karten."""
    zahl_ = len(liste) + len(fehlen) if zahl_ is None else zahl_
    kopf = _kopf(name, zahl_, text)
    sichtbar = [(tk, x) for tk, x in liste[:SICHTBAR] if x.get("karte")]
    rest = liste[SICHTBAR:] + [(tk, x) for tk, x in liste[:SICHTBAR] if not x.get("karte")]
    return {"art": "abschnitt", "kopf": kopf, "name": name, "zahl": zahl_, "text": text, "liste": liste_name,
            "karten": [(tk, x, karte_html(x, _marken(x) if liste_name else "", tk)) for tk, x in sichtbar],
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
    try:                                          # Zeichen „Rückenwind“ aus dem Stand der Seite Rückenwind
        import rueckenwind
        rw = (rueckenwind.laden() or {}).get("titel") or {}
    except Exception:  # noqa: BLE001
        rw = {}

    def _rw(tk):
        r = rw.get(tk)
        return {"rueckenwind": {"kurs": r["kurs_ampel"], "geld": r["geld_ampel"],
                                "zahlen": (r.get("zahlen") or {}).get("ampel"), "stufe": r["stufe"]}} if r else {}

    tisch = dict(tisch, titel={tk: dict(x, **_rw(tk), listen=[n for n, l in w.items() if tk in l],
                                        # Tisch von vor dem VCP-Scanner: die alte Wertzonen-Flagge trägt keinen
                                        # Scanner-Text und gehört nicht in die Reihe „Flagge · Scanner“
                                        **({"reihe": "flagge_alt"} if x.get("reihe") == "flagge"
                                           and not x.get("scanner") else {}))
                               for tk, x in tisch["titel"].items()})
    try:                                          # Auswahl „Einsatzbereit“ (kern/auswahl.py, auch für die Wachen)
        import depot
        import rueckenwind_seite
        import auswahl as auswahl_
        rw_erg = rueckenwind.laden() or {}
        drei = {tk for tk, _ in rueckenwind_seite.dreifach_liste(rw_erg)} if rw_erg else set()
        pos = [p_["ticker"] for p_ in depot.laden().get("positionen", [])]
        wl_ = set(w[watchlists.STANDARD])
        akten, gruende, elite = auswahl_.auswahl(tisch["titel"], rw_erg.get("titel") or {}, drei, wl_, pos, mit_rest=True)
        for tk, g in gruende.items():
            if tk in tisch["titel"]:
                tisch["titel"][tk]["stab"] = g
    except Exception:  # noqa: BLE001 – ohne Auswahl steht der Tisch trotzdem
        akten, gruende, drei, elite, wl_ = [], {}, set(), [], set()
    b = tisch["barometer"]
    if "m_gruen" in b:                            # ein System (12.11.2026): grüne Setups nach Richtung, „nur Muster“ nicht
        gr = [lagekarte.richtung(x) for x in tisch["titel"].values() if x.get("gruen") and x.get("reihe") not in (None, "vcp")]
        zahlen_ = f'{gr.count("long")} long · {gr.count("short")} short'
    else:                                         # Tisch von vor den zwei Systemen
        zahlen_ = f'{b.get("long_gruen", 0)} long · {b.get("short_gruen", 0)} short'
    barometer = (
        f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 20px">'
        f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:.06em;text-transform:uppercase">Grüne Setups · ohne „nur Muster“</div>'
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
    # ③ Stellung: Barometer, Lagekarte nach Sektoren, Reihen · ④ Termine (Seite Rückenwind seit 10.11.2026)
    teile = [{"art": "html", "rolle": "auswahl", "html": station("auswahl") + auswahl_html(tisch, akten, gruende, drei, elite, wl_)},
             {"art": "html", "rolle": "stellung", "html": station("stellung") + barometer},
             {"art": "html", "rolle": "lagekarte", "html": lagebild(tisch)}]

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
    teile.append({"art": "html", "rolle": "termine", "html": station("termine")
                  + _klapp("Neu seit gestern", f"{len(neu)} Veränderungen gegenüber dem letzten Lauf", neu_html)
                  + _klapp("Earnings 14 Tage", f"{len(termine)} Termine in Reihen und Watchlist"
                           + (f" · der nächste: {termine[0][1]} {termine[0][2]}" if termine else ""), earn)
                  + f'<div style="font-size:13px;color:{TEXT_3}">Kartentisch gerechnet am {tisch["erzeugt"]} Uhr · '
                    f'„Deep Dive →“ öffnet die Titelseite in einem neuen Tab</div>'})
    return teile


def auswahl_html(tisch, akten, gruende, drei, elite=(), wl=()):
    """Trichter vom Revier zur Liste „Einsatzbereit“ und ihre Tabelle (Seite Setups, 12.11.2026; bis 13.11.2026 „Diese
    Titel liest der Stab“) – was einsatzbereit ist, und warum."""
    import auswahl as auswahl_
    from gestaltung import AMPEL, BLAU, GRAU, KARTE, RAND, TEXT, TEXT_2, TEXT_3, t, zahl
    tt = tisch["titel"]
    n_revier = (tisch.get("barometer") or {}).get("titel") or len(tt)
    in_reihe = [tk for tk, x in tt.items() if x.get("reihe") and not str(x.get("reihe")).endswith("_alt")]
    gruen = [tk for tk in in_reihe if tt[tk].get("gruen")]
    bereit = [tk for tk in gruen if gruende.get(tk) and (gruende[tk][0] or gruende[tk][1].startswith("Platz voll"))]
    stufen = (("Revier", n_revier), ("in einer Reihe", len(in_reihe)), ("Setup grün", len(gruen)),
              ("einsatzbereit", len(bereit)), ("auf der Liste", len(akten)))
    trichter = "".join(
        f'<div style="flex:1 1 130px;background:{KARTE};border:1px solid {BLAU if i == 4 else RAND};border-radius:10px;'
        f'padding:10px 14px"><div style="font-size:13px;color:{TEXT_3}">{n}</div>'
        f'<div style="font-size:24px;font-weight:600;color:{BLAU if i == 4 else TEXT}">{zahl(z, 0)}</div></div>'
        for i, (n, z) in enumerate(stufen))
    namen = {k: n for k, n, _ in REIHEN}
    zeilen = ""
    for tk in akten:
        x = tt.get(tk) or {}
        a_ = x.get("abstand_vz")
        r = (x.get("rueckenwind") or {})
        g_ = r.get("geld")
        if g_ and lagekarte.richtung(x) == "short":       # Short: Abfluss ist Rückenwind (gespiegelt wie die Matrix)
            g_ = auswahl_._GEGEN.get(g_, g_)
        geld = AMPEL.get(g_, GRAU)
        zeilen += (f'<tr><td style="padding:6px 8px"><a href="?seite=Titelseite&t={t(tk)}" target="_self" style="color:{BLAU};'
                   f'font-weight:600;text-decoration:none">{t(tk)}</a></td>'
                   f'<td style="padding:6px 8px;color:{TEXT_2}">{t(namen.get(x.get("reihe"), "Depot" if not x else "—"))}'
                   + '</td>'
                   f'<td style="padding:4px 8px">{kreislauf_zeile(tk)}</td>'
                   f'<td style="padding:6px 8px">{"—" if a_ is None else zahl(float(a_), 1) + " %"}</td>'
                   f'<td style="padding:6px 8px"><span style="display:inline-block;width:11px;height:11px;border-radius:50%;'
                   f'background:{geld}"></span></td>'
                   f'<td style="padding:6px 8px;color:{TEXT_2}">{t((gruende.get(tk) or (True, "Depot"))[1])}</td></tr>')
    kopf = "".join(f'<th style="text-align:left;padding:6px 8px;font-size:13px;font-weight:500;color:{TEXT_3};'
                   f'border-bottom:1px solid {RAND}">{k}</th>' for k in ("Titel", "Reihe", "Kreislauf", "zum Einstieg",
                                                                         "Geld", "Warum dabei"))
    regel = (f"Einsatzbereit = Setup grün und Kurs am Auslöser oder in der Kaufzone (long {zahl(auswahl_.ZONE_LONG[0], 0)} "
             f"bis +{zahl(auswahl_.ZONE_LONG[1], 0)} % zum Einstieg des Setups, Short bis {zahl(auswahl_.ZONE_SHORT[0], 0)} % unter dem "
             f"Einstieg, Volltreffer bis +{zahl(auswahl_.ZONE_VOLLTREFFER[1], 0)} %) · Depot immer · Rang: {auswahl_.RANG_TEXT} · je Reihe {auswahl_.AKTEN_JE_REIHE} Plätze vorab · höchstens {auswahl_.AKTEN_MAX}")
    return (f'<div style="display:flex;flex-wrap:wrap;gap:10px">{trichter}</div>'
            f'<div style="font-size:13px;color:{TEXT_3}">{t(regel)}</div>'
            f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:14px 16px;overflow-x:auto">'
            f'<div style="font-size:16px;font-weight:600;margin-bottom:6px">🎯 Einsatzbereit · {len(akten)} Titel auf der Liste'
            f'</div><table style="width:100%;border-collapse:collapse;font-size:14px;color:{TEXT}"><thead><tr>{kopf}'
            f'</tr></thead><tbody>{zeilen or "<tr><td>keiner einsatzbereit</td></tr>"}</tbody></table>'
            + _knapp_draussen(tt, gruende, [tk for tk in elite if tk not in akten], namen) + '</div>'
            + _watchlist_kasten(tt, gruende, [tk for tk in elite if tk in wl], set(akten), namen))


def _knapp_draussen(tt, gruende, rest, namen, n=10):
    """Die Grenze sichtbar: die ersten Einsatzbereiten ohne Platz, in derselben Rangfolge (12.11.2026 – so prüft man
    mit einem Blick, ob draußen jemand Besseres steht als drinnen)."""
    from gestaltung import TEXT_2, TEXT_3, t
    if not rest:
        return ""
    teile = " · ".join(f'<b>{t(tk)}</b> {t(namen.get((tt.get(tk) or {}).get("reihe"), ""))} '
                       f'<span style="color:{TEXT_3}">({t((gruende.get(tk) or (False, ""))[1])})</span>'
                       for tk in rest[:n])
    return (f'<div style="margin-top:10px;font-size:13px;color:{TEXT_2}">Knapp draußen – {len(rest)} weitere '
            f'einsatzbereit, die ersten {min(n, len(rest))} in Rangfolge: {teile}</div>')


def _watchlist_kasten(tt, gruende, liste, drin, namen):
    """◆ Deine Watchlist · einsatzbereit (Micky 12.11.2026): die Auswahl ist neutral, die eigene Truppe
    steht hier getrennt – dieselbe Rangfolge, je Titel 🎯 auf der Liste oder der Grund. Die übrigen Watchlist-Titel zeigt
    ② Stellung vollständig."""
    from gestaltung import BLAU, KARTE, RAND, TEXT, TEXT_2, TEXT_3, t, zahl
    zeilen = "".join(
        f'<tr><td style="padding:6px 8px;width:28px">{"🎯" if tk in drin else ""}</td>'
        f'<td style="padding:6px 8px"><a href="?seite=Titelseite&t={t(tk)}" target="_self" style="color:{BLAU};'
        f'font-weight:600;text-decoration:none">{t(tk)}</a></td>'
        f'<td style="padding:6px 8px;color:{TEXT_2}">{t(namen.get((tt.get(tk) or {}).get("reihe"), "—"))}</td>'
        f'<td style="padding:6px 8px">{"—" if (tt.get(tk) or {}).get("abstand_vz") is None else zahl(float(tt[tk]["abstand_vz"]), 1) + " %"}</td>'
        f'<td style="padding:6px 8px;color:{TEXT_2}">{t((gruende.get(tk) or (False, ""))[1])}</td></tr>'
        for tk in liste)
    n_drin = sum(1 for tk in liste if tk in drin)
    return (f'<div style="margin-top:12px;background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:14px 16px;'
            f'overflow-x:auto"><div style="font-size:16px;font-weight:600;margin-bottom:2px">◆ Deine Watchlist · '
            f'einsatzbereit · {len(liste)}, davon {n_drin} auf der Liste</div>'
            f'<div style="font-size:13px;color:{TEXT_3};margin-bottom:6px">Dieselbe Rangfolge wie oben, nur deine Titel · '
            f'🎯 = auf der Liste, sonst der Grund · alle übrigen Watchlist-Titel stehen in ② Stellung</div>'
            f'<table style="width:100%;border-collapse:collapse;font-size:14px;color:{TEXT}"><tbody>'
            f'{zeilen or "<tr><td>zurzeit keiner deiner Titel einsatzbereit</td></tr>"}</tbody></table></div>')


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
    if x.get("reihe") == "vcp":                   # „nur Muster“ (12.11.2026): Bereitstellung, kein Angriff
        return "bereit"
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
    from gestaltung import BLAU, GRUEN, RAND, TEXT_2, TEXT_3, feld_name, karte, t, zahl
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
            text += " M" if x["reihe"] == "vcp" else " F"
        if x.get("reihe") == "zahlen":
            text += " ⚡"
        if x.get("listen"):
            text += " ◆"
        g = gruppen.get(tk)
        if g:
            text += " ⚑"
        zeilen = [f"<b>{t(tk)}</b> · {t({k: n for k, n, _ in REIHEN}.get(x.get('reihe'), 'keine Reihe'))}",
                  f"Auktion: {t(x.get('zustand', '–'))}"]
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
            links = (f'<b>{t(r["name"])}</b><br><span style="color:{FARBE[r["feld"]]}">{t(feld_name(r["feld"]))}</span> '
                     f'<span title="{t(PFEILE[pf])}">{pf}</span> <span style="color:{TEXT_2}">{zahl(r["staerke"], 0)}</span>')
        else:
            links = f'<b>{t(sektoren.SEKTOREN.get(e, "ohne Sektor"))}</b>'
        zeilen.append(f'<div style="display:grid;grid-template-columns:{raster};gap:16px;padding:12px 0;'
                      f'border-top:1px solid {RAND};align-items:start"><div style="font-size:14px;line-height:1.5">{links}'
                      f'</div>' + "".join(f'<div>{zelle(zellen.get((e, k), []), k)}</div>' for k, _ in SPALTEN) + '</div>')
    hilfe = (f'<div style="font-size:13px;color:{TEXT_2};margin-top:8px">Oben der Abschnitt mit den meisten Angriffen. '
             f'Angriff jetzt = Setup grün · Bereitstellung = in einer Reihe, Setup noch nicht grün oder nur Muster '
             f'(„M“) · F = Flagge · ⚡ = Zahlen-Reaktion · Balken = Zahl der Titel, je Spalte am größten Abschnitt gemessen · sichtbar '
             f'die drei stärksten, „+n“ klappt den Rest auf · ★ Kaufzone · ◆ Watchlist · ⚑ Themen-Gruppe Führend/Erstarkend · '
             f'Maus auf einen Titel zeigt Reihe, Befund des Scanners, Auktion und was fehlt.</div>')
    return karte(kopf + "".join(zeilen) + hilfe, "Lagekarte nach Sektoren · wo die Angriffe sich sammeln")
