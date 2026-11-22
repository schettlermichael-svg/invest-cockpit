"""Kartentisch (4.11.2026; ein eigenes System seit 12.11.2026): alle Titel des Laufs einmal durchgerechnet, in Reihen
geordnet, als Lagekarten. Die Reihen ordnen, sie filtern nicht – jeder Titel bleibt über die Titelseite erreichbar.

Acht Setups (Namen nach dem, was sie sind; die Regeln stammen von den Meistern, siehe REIHEN und setup_feststellen):
  Base-Ausbruch (VCP)  💥 in der Kaufzone · weiter weg oder eine Regel fehlt · nur Muster (Regeln: Minervini)
  Flagge, Momentum-Ausbruch, Sprung (EP), Ermüdung (Short) (Regeln: Kullamägi; EP auch Bonde)
  Zahlen-Reaktion (Drift nach den Zahlen), Bärenflagge (Short), Bruch der Spanne (Short, seit 13.11.2026; Weinstein)
  Watchlist: jeder Titel aus einstellungen/watchlists.json, immer; steht direkt nach dem Base-Ausbruch 💥
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
import phase                                         # noqa: E402
from dateien import json_lesen, json_schreiben  # noqa: E402
SPEICHER = os.path.join(HIER, "..", "daten", "kartentisch")
REIHEN = [("m_spitze", "💥 Base-Ausbruch · in der Kaufzone", "Base reif und eng (VCP), Trendvorlage, RS ab 70, Zahlen "
                                                          "wachsen – alle Regeln erfüllt, Kurs 5 % vor bis 5 % über dem "
                                                          "Pivot"),
          ("m_weitere", "Base-Ausbruch · weiter weg oder eine Regel fehlt", "Base-Ausbruch mit allen Regeln, aber Kurs "
                                                                             "weiter vom Pivot – oder genau eine Regel fehlt"),
          ("vcp", "Base-Ausbruch · nur Muster", "Base mit grüner Enge, Kurs höchstens 5 % vom Pivot, aber mehrere Regeln "
                                                "fehlen (meist Trendvorlage, RS oder Zahlen) – sichtbar, kommt nicht auf die "
                                                "Liste Einsatzbereit"),
          ("flagge", "Flagge", "Fahnenstange ab 30 % in höchstens 13 Wochen, Flagge 1–8 Wochen, höchstens 25 % tief, auch "
                               "in einer Base, Kurs über dem steigenden GD50, Volumen in der Flagge leiser als in der "
                               "Stange, steigende Tiefs (Tief der zweiten Hälfte der Flagge mehr als 0,5 ATR unter dem der ersten = fehlt); grün, sobald der Kurs höchstens 5 % unter der Oberkante steht oder darüber (nach einem "
                               "Ausbruch: in der Kaufzone bis +5 %)"),
          ("k_breakout", "Momentum-Ausbruch", "Führer (oberste 1–2 % nach 1/3/6 Monaten) mit einer Pause von 1–3 Wochen "
                                              "nach einem Schub; gelb = Führer knapp oder Pause bis 8 Wochen"),
          ("k_ep", "Sprung (EP)", "Sprung ab 10 % mit Lücke und Volumen ab 3-fach in den letzten 10 Tagen, Kurs hält das "
                                  "Tief des Sprungtags; grün mit Nachricht (Zahlen)"),
          ("zahlen", "Zahlen-Reaktion · long und short", "Kurs reagiert auf die Zahlen ab 3 % (Short ab −3 %) in den "
                                                       "letzten 20 Handelstagen, Volumen über dem Schnitt, Schluss im "
                                                       "oberen (Short: unteren) Drittel, hält Tief und AVWAP des "
                                                       "Reaktionstags, Kurs über (unter) GD50; Einstieg am AVWAP"),
          ("w_spring", "Spring", "Wyckoff: Tief höchstens 1 ATR unter der Unterkante der Zone (wie sie am Vortag "
                                 "stand), Schluss binnen 3 Tagen zurück in der Zone; gilt 10 Tage, solange das Tief des "
                                 "Fehlausbruchs hält und die Oberkante nicht erreicht ist; Einstieg an der Unterkante, Ziel "
                                 "die Oberkante; 💥 bis 5 % darüber"),
          ("w_upthrust", "Upthrust · Short", "Wyckoff: Hoch höchstens 1 ATR über der Oberkante der Zone, Schluss binnen 3 "
                                             "Tagen zurück in der Zone; gilt 10 Tage, solange das Hoch des Fehlausbruchs "
                                             "hält und die Unterkante nicht erreicht ist; Einstieg an der Oberkante, Ziel die "
                                             "Unterkante; 💥 bis 5 % darunter"),
          ("k_ermuedung", "Ermüdung · Short", "Nach einer Fahnenstange ab 30 % bricht die Flagge nach unten (Schluss "
                                              "unter der Unterkante, letzte 5 Tage) – meist ein Führer; grün bis 5 % "
                                              "darunter; Stopp 1,5 ATR über der Unterkante, das Setup erlischt schon "
                                              "über dem Hoch des Auslösetags"),
          ("k_baerenflagge", "Bärenflagge · Short", "Steiler Fall ab 15 %, dann schwaches, leises Driften nach oben (GD50 "
                                                    "fällt), dann Schluss unter dem Tief der letzten 5 Tage des "
                                                    "Driftens; grün bis 5 % unter der Unterkante"),
          ("k_bruch", "Bruch der Spanne · Short", "Eine Basis, Verteilung oder Balance in Phase 2 von mindestens 6 Wochen "
                                                  "bricht: Schluss mindestens 1 % unter ihrem Tief; grün bis 5 % "
                                                  "darunter")]


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
JAHR = 252            # 52 Wochen in Handelstagen
GD50_STEIG_TAGE = 21  # Flagge im Trend: GD50 steigt (gegen 20 Tage vorher)


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


def _stufe1(tk, start=None, regeln=False):
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
                "hoch52": bool(len(h) >= 252 and h[-1] >= h[-JAHR:].max()),
                "tief52": bool(len(l) >= 252 and l[-1] <= l[-JAHR:].min()),
                "m": {"ampel": m["ampel"], "setup": m["setup"], "fehlt": [n for n, ok, _ in m["regeln"] if not ok]},
                "k": {"ampel": k["ampel"], "setup": k["setup"],
                      **{f_: (k.get(f_) or {}).get("ampel") for f_ in (*SHORTS.values(), "spring")}}}
        import zahlen_reaktion
        zr_ = zahlen_reaktion.pruefen(df, gewinne)
        info.update(setup_feststellen(df, m, k, zr_, scan))
        if regeln:                                  # für den Setup-Prüfer: die Urteile beider Lehrer mit allen Regeln
            info["_regeln"] = {"m": m, "k": k, "zr": zr_}
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
        try:                                        # Tiefenanalyse je Titel (Micky 21.11.2026, aus der Titel-Analyse)
            import avwap
            import tiefe
            zt = avwap.zahlentag(df, gewinne) if gewinne is not None else None
            info["tiefe"] = tiefe.kurz(df, tiefe.dreissig(df), zt, index, tiefe.zone_beginn(df))
        except Exception:  # noqa: BLE001 – ohne Tiefenanalyse steht die Karte trotzdem
            info["tiefe"] = None
        return info
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Tisch steht trotzdem
        return None


NAME = {"m_spitze": "Base-Ausbruch 💥", "m_weitere": "Base-Ausbruch", "vcp": "Base-Ausbruch · nur Muster",
        "flagge": "Flagge", "k_breakout": "Momentum-Ausbruch", "k_ep": "Sprung (EP)", "zahlen": "Zahlen-Reaktion",
        "k_ermuedung": "Ermüdung (Short)", "k_baerenflagge": "Bärenflagge (Short)", "k_bruch": "Bruch der Spanne (Short)",
        "w_spring": "Spring", "w_upthrust": "Upthrust (Short)"}
from system_kullamaegi import SHORTS, short_von   # noqa: E402  Reihe → Feld in k (Ermüdung, Bärenflagge, Bruch)


def setup_feststellen(df, m, k, zr, scan):
    """Das eine Setup eines Titels (Micky 12.11.2026: ein eigenes System, ein Urteil je Titel) – für Kartentisch und
    Titelseite dieselbe Entscheidung. Vorrang: Sprung (EP) → Zahlen-Reaktion → Spring → Upthrust/Ermüdung/Bärenflagge/Bruch der Spanne → Base-Ausbruch 💥
    (Kaufzone) → Flagge → Momentum-Ausbruch → Base-Ausbruch (weiter weg oder eine Regel fehlt) → Base-Ausbruch · nur
    Muster. „auch“ nennt die übrigen Setups, die der Titel zeigt (nichts geht verloren).
    → {reihe, gruen, stern, abstand, abstand_vz, luecken, zr, zr_seite, short_art, still, scanner, ausbruch, auch}"""
    import atr as atr_
    import depot
    import erkennung
    import vcp_zone
    import zeichen
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
    if k.get("spring"):                            # Spring (Wyckoff) nach Sprung und Zahlen-Reaktion (Micky 15.11.2026)
        gefunden.append("w_spring")
    for r_s in SHORTS:                             # Upthrust → Ermüdung → Bärenflagge → Bruch der Spanne
        x_ = short_von(k, r_s)
        if x_ and not (x_.get("vor_bruch") and x_.get("ampel") != "grün"):
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
    vb_ = short_von(k, "k_bruch")                  # Verteilung vor dem Bruch (noch nicht ausgelöst) steht wie der
    if vb_ and vb_.get("vor_bruch") and vb_.get("ampel") != "grün":   # Base-Ausbruch „weiter weg“ hinten an
        gefunden.append("k_bruch")
    r_ = gefunden[0] if gefunden else None
    if r_ == "k_ep":
        info.update(reihe="k_ep", stern=k["ep"]["ampel"] == "grün", gruen=k["ep"]["ampel"] == "grün")
    elif r_ == "zahlen":
        e_ = -zr["abstand"] if zr["seite"] == "short" else zr["abstand"]
        info.update(reihe="zahlen", zr_seite=zr["seite"], gruen=zr["ampel"] == "grün",
                    stern=bool(zr["ampel"] == "grün" and 0 <= e_ <= KAUFZONE_M), abstand=float(abs(zr["abstand"])),
                    abstand_vz=float(zr["abstand"]), luecken=zr["luecken"])
    elif r_ == "w_spring":
        sp_ = k["spring"]
        ab_ = float((c[-1] / sp_["einstieg"] - 1) * 100)
        info.update(reihe="w_spring", gruen=True, stern=bool(0 <= ab_ <= KAUFZONE_M), abstand=abs(ab_), abstand_vz=ab_,
                    luecken=[] if ab_ <= KAUFZONE_M else [f"Spring: schon {ab_:.1f} % über der Unterkante".replace(".", ",")])
    elif r_ in SHORTS:
        em = short_von(k, r_)
        short_art = em["art"]
        ein_s = em.get("einstiege") or []
        e_s = ein_s[vcp_zone.naechster(ein_s, float(c[-1]), seite="short")]["wert"] if len(ein_s) > 1 else em["einstieg"]
        ab_ = float((c[-1] / e_s - 1) * 100)
        # Short-Zone wie die Kaufzone gespiegelt (12.11.2026: DT stand 21,9 %, ALNY 25,2 % unter der Unterkante als
        # 💥 – der Fall war längst gelaufen, der Stopp über dem Auslösetag 40 % entfernt)
        gruen_ = em["ampel"] == "grün" and -KAUFZONE_M <= ab_ <= 0
        info.update(reihe=r_, short_art=short_art, stern=gruen_, gruen=gruen_, abstand=abs(ab_), abstand_vz=ab_,
                    luecken=[] if gruen_ else [f"Short: vor dem Bruch, noch {ab_:.1f} % über dem Auslöser".replace(".", ",")]
                    if em.get("vor_bruch") and em["ampel"] != "grün"
                    else [f"Short: zurück über {'der Oberkante' if r_ == 'w_upthrust' else 'der Unterkante'}"]
                    if em["ampel"] != "grün"
                    else [f"Short: schon {-ab_:.1f} % unter {'der Oberkante' if r_ == 'w_upthrust' else 'der Unterkante'} – gelaufen".replace(".", ",")])
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
                  else None if r_ in ("k_ep", "zahlen", "w_spring", *SHORTS)   # alte Konsolidierung)
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
    elif r_ in ("w_spring", "w_upthrust"):
        su_ = k["spring" if r_ == "w_spring" else "upthrust"]
        info["ausbruch"] = (f"{'▲ Spring' if r_ == 'w_spring' else '▼ Upthrust'} am {su_['tag']:%d.%m.}: "
                            f"{'Tief unter der Unterkante' if r_ == 'w_spring' else 'Hoch über der Oberkante'}, "
                            f"am {su_['zurueck_tag']:%d.%m.} zurück in der Zone – Ziel der andere Rand "
                            f"{su_['ziel']:.2f} $".replace(f"{su_['ziel']:.2f}", f"{su_['ziel']:.2f}".replace(".", ",")))
    elif r_ == "k_ermuedung":
        info["ausbruch"] = "▼ Ermüdung nach Überdehnung: die Flagge nach der Fahnenstange bricht nach unten"
    elif r_ == "k_baerenflagge":
        info["ausbruch"] = "▼ Bärenflagge: steiler Fall, schwaches Driften nach oben, dann Bruch der Unterkante"
    elif r_ == "k_bruch" and short_von(k, r_).get("vor_bruch"):
        info["ausbruch"] = ("▽ Bruch der Spanne: Verteilung, noch nicht gebrochen – Auslöser Unterkante"
                            + (" (früher Short am Tief der letzten Gegenbewegung)" if len(short_von(k, r_).get("einstiege") or []) > 1 else ""))
    elif r_ == "k_bruch":
        r0_ = str(short_von(k, r_)["regeln"][0][0])
        info["ausbruch"] = "▼ Bruch der Spanne: Schluss unter dem Tief der " + (
            "Basis" if "Basis" in r0_ else "Balance in Phase 2" if "Phase 2" in r0_ else "Verteilung")
    if zeichen_br:                           # Zeichen auf jeder Karte: Ausbruch mit/ohne Volumen, Fehlausbruch
        info["ausbruch"] = vcp_zone.ausbruch_text(zeichen_br)
    if zeichen_br and (zeichen_br.get("fehl") or zeichen_br.get("ruecktest")):
        # Fehlausbruch (13.11.2026: Schluss unter dem Tief des Ausbruchstags oder > 3 % unter dem Pivot) und Rücktest
        # sind nicht einsatzbereit, bleiben aber in der Reihe unter Beobachtung
        info.update(gruen=False, stern=False, luecken=(info.get("luecken") or []) + [
            "Fehlausbruch – beobachten" if zeichen_br.get("fehl") else "Rücktest des Pivots – beobachten"])
    # Gegen die Stufe (Gefechtsordnung Schritt 8, Micky 16.11.2026): Long in Phase 4 oder Short in Phase 2 bleibt
    # sichtbar, trägt ein Gegenzeichen und wird höchstens gelb
    ph_ = erkennung._phase_von(df) if seite_ else None
    p_ = int(ph_[-1]) if ph_ is not None else None
    if (seite_, p_) in GEGEN_STUFE:
        info["gegen_stufe"] = (f"Gegenzeichen: {'Long' if seite_ == 'long' else 'Short'}-Setup in Phase {p_} "
                               f"({zeichen.PHASE_NAME[p_]}) – gegen die Stufe")
        info.update(gruen=False, stern=False, luecken=(info.get("luecken") or []) + [info["gegen_stufe"]])
    info["gruen"], info["stern"] = bool(info.get("gruen")), bool(info.get("stern"))
    return info


GEGEN_STUFE = {("long", 4), ("short", 2)}   # Setup gegen die Stufe: Long im Abwärts, Short im Aufwärts (Schritt 8)


STILL_PCT = 0.5               # ATR unter 0,5 % des Kurses: der Kurs steht still (Übernahme), kein handelbares Setup
PIVOT_NAH = 5.0               # VCP-Reihe: Kurs höchstens 5 % unter bzw. über dem Pivot
from vcp_zone import KAUFZONE as KAUFZONE_M  # noqa: E402  💥: höchstens 5 % unter bis 5 % über dem Pivot (Minervini, eine Quelle)


def flagge_im_trend(df, f):
    """Eine Flagge zählt nur im Aufwärtstrend und bei leisem Volumen (Prüf-Agent 13.11.2026: sie wurde auch in Phase 4
    grün): Kurs über dem steigenden GD50 und Volumen in der Flagge leiser als in der Fahnenstange → (ok, Lücken).
    Steigende Tiefs prüft seit 15.11.2026 die Zone selbst (vcp_zone.tiefs_fallen): mit fallenden Tiefs heißt sie nicht
    mehr Flagge."""
    if df is None or len(df) < 70 or not f:
        return True, []
    c, v = df["Close"].to_numpy(float), df["Volume"].to_numpy(float)
    g50 = df["Close"].rolling(50).mean().to_numpy(float)
    luecken = []
    if not (c[-1] > g50[-1] and g50[-1] > g50[-GD50_STEIG_TAGE]):
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
            import vcp_zone
            info.update(reihe="vcp", gruen=not br["fehl"], stern=False, abstand=abs(br["abstand"]), abstand_vz=br["abstand"],
                        pivot_scanner=float(br["pivot"]),
                        einstiege=[x for x in vcp_zone.einstiege(bz, be, cheat=False) if x["wert"] == float(br["pivot"])],
                        scanner=f'{bz["name"]} {zahl(bz["wochen"], 1)} Wochen · Enge {be["folge"]} % · Pivot '
                                f'{zahl(br["pivot"])} $')
            return
        if bz.get("name") == "Flagge":
            ok_, l_ = flagge_im_trend(df, bz)
            info.update(reihe="flagge", gruen=br["kaufzone"] and ok_, stern=False, luecken=l_, abstand=abs(br["abstand"]), abstand_vz=br["abstand"],
                        pivot_scanner=float(br["pivot"]), flagge_zone={"wochen": float(bz["wochen"]), "tiefe": float(bz["tiefe"])},
                        scanner=f'Flagge {zahl(bz["wochen"], 1)} Wochen, {zahl(bz["tiefe"], 0)} % tief · Stange '
                                f'+{zahl(bz["stange"]["prozent"], 0)} % · Pivot {zahl(br["pivot"])} $'
                                + (" · in einer Base" if br["innen"] else ""))
            return
    z, e = scan
    if not z.get("zone"):
        return
    import vcp_zone
    einst = vcp_zone.einstiege(z, e, cheat=z.get("name") == "Base") if e.get("pivot") else []
    i_ = vcp_zone.naechster(einst, float(df["Close"].iloc[-1])) if einst and df is not None else None
    piv = einst[i_]["wert"] if i_ is not None else e.get("pivot")
    ab_ = (float(df["Close"].iloc[-1]) / piv - 1) * 100 if i_ is not None else e.get("abstand")
    if e.get("ampel") == "grün" and ab_ is not None and -PIVOT_NAH <= ab_ <= PIVOT_NAH:
        wort = f'{einst[i_]["wort"]} ' if len(einst) > 1 else ""
        info.update(reihe="vcp", gruen=True, stern=False, abstand=abs(ab_), abstand_vz=ab_,
                    pivot_scanner=float(piv), einstiege=einst,
                    scanner=f'{z["name"]} {zahl(z["wochen"], 1)} Wochen · Enge {e["folge"]} % · {wort or "Pivot "}{zahl(piv)} $ '
                            f'({"+" if ab_ >= 0 else "−"}{zahl(abs(ab_), 1)} %)')
        return
    f = z if z["name"] == "Flagge" else z.get("innen")
    if f and f["laenge"] == "ok":
        nah = f["abstand"] >= -PIVOT_NAH
        ok_, l_ = flagge_im_trend(df, f)
        info.update(reihe="flagge", gruen=nah and ok_, stern=False, luecken=l_, abstand=abs(f["abstand"]), abstand_vz=f["abstand"],
                    pivot_scanner=float(f["oben"]), flagge_zone={"wochen": float(f["wochen"]), "tiefe": float(f["tiefe"])},
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
        stufe1 = [x for x in ex.map(functools.partial(_stufe1, start=start), ticker_liste, chunksize=20) if x]  # Layout
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
                "phasen": {x["tk"]: x["phase"] for x in stufe1}, "phasen_regel": phase.REGEL}
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


RANG = {"m_spitze": 5, "k_ep": 5, "zahlen": 5, "w_spring": 5, "w_upthrust": 5, "k_ermuedung": 4, "k_baerenflagge": 4, "k_bruch": 4, "flagge": 4,
        "k_breakout": 4,
        "m_weitere": 3, "vcp": 1, None: 0}


ALTE_REIHEN = {"spitze": "💥 Spitzenkandidaten (alt)", "weitere": "Weitere Kandidaten (alt)", "short": "Short (alt)",
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
    # neue Phasenregel (Schritt 8: 102 Titel wechselten auf einen Schlag von 3 nach 2): kein Vergleich mit dem alten Stand
    pa = vorher.get("phasen", {}) if vorher.get("phasen_regel") == jetzt.get("phasen_regel") else {}
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


def tiefe_zeichen(x):
    """Zeichen der Tiefenanalyse in einer Zeile (Micky 21.11.2026): PbD-Form und D-Kante, Quetschung, CMF, Stärke in
    der Schwäche an den Abgabetagen, Wertwanderung – jedes Zeichen aus der Zeichenliste."""
    import tiefe
    ti = (x or {}).get("tiefe")
    if not ti:
        return ""
    from gestaltung import zahl
    teile = []
    if ti.get("quetsch"):
        teile.append("🦈 Quetschung" + (" nach unten" if ti["quetsch"] == "absteigend" else ""))
    c = ti.get("cmf")
    if c is not None:
        teile.append(f"{'🟢' if c > tiefe.CMF_GRENZE else '🔴' if c < -tiefe.CMF_GRENZE else '🟡'} CMF "
                     f"{'+' if c > 0 else '−' if c < 0 else ''}{zahl(abs(c), 2)}")
    s_ = ti.get("sis")
    if s_ and s_[1]:
        teile.append(f"{'🦈' if s_[0] * 2 > s_[1] else '🟡' if s_[0] else '🔴'} Abgabetage {s_[0]}/{s_[1]} besser")
    w = ti.get("wander")
    if w:
        r_, n_ = w["treppe"]
        if n_ >= tiefe.TREPPE:
            teile.append(f"{'🦬' if r_ > 0 else '🐻'} Treppe {'↑' if r_ > 0 else '↓'}{n_}")
        if w["ballen"]:
            teile.append("🟡 POCs ballen sich")
        if w["abtasten"]:
            teile.append(f"🪝 Abtasten {w['abtasten']}")
    return " · ".join(teile)






def zeile(tk, x):
    """Eine Tabellenzeile für die übrigen Titel (Reihenfolge wie die Karten)."""
    from gestaltung import GELB, zahl
    if x is None:
        return {"tk": tk, "farbe": GELB, "blass": False, "Setup": "neu – wird im Abendlauf gerechnet", "Befund": "", "Stab": "",
                "Abstand %": "", "Was fehlt": ""}
    setup = (x.get("kacheln") or {}).get("Setup", ("grau", "–", ""))
    st_ = x.get("stab")
    return {"tk": tk, "farbe": _farbe(x)[:7], "blass": len(_farbe(x)) > 7, "Setup": setup[1],  # Layout
            "Stab": ("💥 " if st_[0] else "") + st_[1] if st_ else "",
            "Befund": " · ".join(z for z in (rueckenwind_zeichen(x), scanner_text(x), tiefe_zeichen(x),
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




def _ordnung(x):
    return (not x.get("stern"), not x.get("gruen"), x.get("abstand", 99))  # Layout


def _kopf(name, zahl_, text, h=2):
    from gestaltung import TEXT_2, TEXT_3, t
    groesse = 26 if h == 2 else 19  # Layout
    return (f'<div style="display:flex;align-items:baseline;gap:14px;margin:12px 0 4px"><h{h} style="margin:0;'
            f'font-size:{groesse}px">{t(name)} <span style="color:{TEXT_3};font-weight:500">{zahl_}</span></h{h}>'
            + (f'<span style="font-size:15px;color:{TEXT_2}">{t(text)}</span>' if text else "") + '</div>')












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
# Systeme oder des VCP-Scanners, 💥), Bereitstellung (übrige Reihen: Setup noch nicht grün, Flagge weiter weg) und ◆ Watchlist
# ohne Reihe. Je Zelle ein Balken mit der Zahl und die drei stärksten Titel; der Rest aufklappbar – nichts wird gefiltert.
SPALTEN = [("jetzt", "Angriff jetzt"), ("bereit", "Bereitstellung"), ("watch", "◆ Watchlist ohne Reihe")]
TOP = 3                       # Marken je Zelle sichtbar, der Rest aufklappbar






