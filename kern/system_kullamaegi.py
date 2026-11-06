"""System Kullamägi (05.11.2026): Momentum mit kurzem Atem, drei Setups – Breakout, Episodic Pivot
und als Short die Ermüdung nach Überdehnung (seit 06.11.2026 statt des Parabolic Short). Grundlage: sein Interview mit
Jack Schwager („Market Wizards“-Reihe). Eines der zwei getrennten Systeme
der App (das andere: system_minervini.py).

Breakout (Momentum Burst nach Pradeep Bonde): rein technisch. Ein Führer im Aufwärtstrend geht nach einem Schub in eine
  Seitwärtsphase über, vorzugsweise bei reduziertem Volumen, und bricht aus. Führer = die obersten 1–2 % nach der
  Kursentwicklung über 1, 3 oder 6 Monate (fuehrer_rang). Konsolidierung meist 1–3 Wochen. Haltedauer 3–5 Tage für den
  Hauptteil. Erfolgsquote deutlich unter 50 %.
  grün: Führer (oberste 2 %) + Wertzone 1–3 Wochen nach einem Lauf nach oben (oder Kurs über GD50)
Episodic Pivot: eine Nachricht, die den Markt zur völligen Neubewertung zwingt, eine große Kurslücke nach oben und eine
  Volumenexplosion – alle drei Pflicht. Ideal ein vernachlässigter Titel, der lange seitwärts lief (kein Titel, der kurz
  vorher schon stark stieg); ein Ausbruch aus einer Konsolidierung ist ihm lieber, aber keine Pflicht. Sein Scan: Titel,
  die bei hohem Volumen mindestens 10 % gestiegen sind.
  grün (in den letzten EP_TAGE Handelstagen, der Kurs hält das Tief des Sprungtags): Tagesgewinn ≥ 10 %, Eröffnung über
  dem Vortageshoch (echte Lücke), Volumen ≥ 3-fach des 50-Tage-Schnitts (Micky, 05.11.2026; 10-fach = ideal, Zeichen).
  Nachricht: Zahlen am Sprungtag werden erkannt, sonst „Nachricht prüfen“ (gelb).
Ermüdung nach Überdehnung (Short, 06.11.2026, vcp_zone.ermuedung): die Flagge des Scanners, im Ausgang gespiegelt –
  Fahnenstange ≥ 30 % in höchstens 13 Wochen, Flagge 1–8 Wochen, höchstens 25 % tief, dann Schluss unter der Unterkante.
  Stopp über dem Hoch des Auslösetags. Zeichen: Volumen am Bruch über dem Schnitt.
Stopp (alle): Tagestief beim Long, Tageshoch beim Short. Liegt er weiter weg als die durchschnittliche tägliche True Range
  (ADTR), kein Trade. Risiko 0,5 % des Kontos, höchstens 1 %.
Ausstieg: Teilgewinn in den ersten 3–5 Tagen, Stopp für den Rest auf Einstand, dann Schluss unter dem 10- oder
  20-Tage-Durchschnitt (je nachdem, wie weit der Titel schon gestiegen ist).
Markt (markt_systeme.kullamaegi): Breakout und EP nur im Aufwärtstrend – eigene Ampel, gehört nicht zu „grün“, kein Filter.
"""
import numpy as np

import fuehrer_rang
import vcp_zone

EP_TAGE = 10
EP_SPRUNG = 10.0
EP_VOLUMEN = 3.0
EP_VOLUMEN_IDEAL = 10.0
EP_VORLAUF_MAX = 20.0        # vernachlässigt: in den 3 Monaten vor dem Sprung höchstens +20 % (Zeichen, keine Pflicht)
KONS_GRUEN = (1, 3)          # Wochen
KONS_GELB = 8
ADTR_TAGE = 20


def adtr(df, n=ADTR_TAGE):
    h, l, c = (df[s].to_numpy(float) for s in ("High", "Low", "Close"))
    if len(c) < n + 1:
        return None
    tr = np.maximum(h[1:], c[:-1]) - np.minimum(l[1:], c[:-1])
    return float(tr[-n:].mean())


def breakout(df, erk, fr):
    a = erk.get("mp")
    st = a["stand"][-1] if a and a.get("stand") else None
    c = df["Close"].to_numpy(float)
    f_ampel = fuehrer_rang.ampel(fr)
    regeln = [("Führer (oberste 1–2 % nach 1/3/6 Monaten)", f_ampel == "grün", fuehrer_rang.text(fr))]
    if st is None:
        regeln.append(("Konsolidierung 1–3 Wochen", False, "keine Wertzone"))
        return {"art": "Breakout", "ampel": "rot" if f_ampel != "grün" else "gelb", "regeln": regeln, "pivot": None}
    wochen = int(st["wochen"])
    trend = st.get("herkunft") == "↑" or (len(c) >= 50 and c[-1] > c[-50:].mean())
    kons = KONS_GRUEN[0] <= wochen <= KONS_GRUEN[1] and trend
    regeln.append(("Konsolidierung 1–3 Wochen nach einem Schub", kons,
                   f"Wertzone {wochen} Woche{'n' if wochen != 1 else ''}"
                   + ("" if trend else ", kein Schub davor und Kurs unter GD50")))
    v = df["Volume"].to_numpy(float)
    zd = max(5, wochen * 5)                      # Handelstage der Wertzone
    ruhig = v[-zd:].mean() / v[-zd - 50:-zd].mean() if len(v) > zd + 50 and v[-zd - 50:-zd].mean() else None
    if ruhig is not None:
        regeln.append(("Volumen in der Konsolidierung reduziert (vorzugsweise)", ruhig < 1.0,
                       f"{ruhig:.1f}-fach".replace(".", ",")))
    if f_ampel == "grün" and kons:
        ampel = "grün"
    elif (f_ampel == "gelb" and kons) or (f_ampel == "grün" and wochen <= KONS_GELB):
        ampel = "gelb"                           # Führer knapp (oberste 5 %) oder Konsolidierung bis 8 Wochen
    else:
        ampel = "rot"
    pivot = float(st["hoch"])
    ab = (c[-1] / pivot - 1) * 100
    return {"art": "Breakout", "ampel": ampel, "regeln": regeln, "pivot": pivot, "wochen": wochen,
            "lage": (f"{ab:.1f} % über der Oberkante" if ab >= 0 else f"{-ab:.1f} % unter der Oberkante").replace(".", ",")}


def episodic_pivot(df, gewinn_tage=()):
    """Jüngster Sprungtag der letzten EP_TAGE Handelstage, der die Zutaten erfüllt, oder None."""
    o, h, l, c, v = (df[s].to_numpy(float) for s in ("Open", "High", "Low", "Close", "Volume"))
    n = len(c)
    if n < 120:
        return None
    zahlen = {t.normalize() for t in gewinn_tage}
    for i in range(n - 1, max(60, n - EP_TAGE) - 1, -1):
        sprung = (c[i] / c[i - 1] - 1) * 100
        luecke = o[i] > h[i - 1]
        s50 = v[i - 50:i].mean()
        vol = v[i] / s50 if s50 else 0
        if sprung < EP_SPRUNG or vol < EP_VOLUMEN or not luecke:
            continue
        tag = df.index[i]
        nachricht = any(abs((tag.normalize() - z).days) <= 1 for z in zahlen)
        vorlauf = (c[i - 1] / c[max(0, i - 64)] - 1) * 100
        haelt = l[i:].min() >= l[i] * 0.999 if i < n - 1 else True
        regeln = [("Große Lücke (Tagesgewinn ab 10 %, Eröffnung über dem Vortageshoch)", True,
                   f"{tag:%d.%m.}: " + f"+{sprung:.1f} %, Eröffnung {(o[i] / c[i - 1] - 1) * 100:+.1f} %".replace(".", ",")),
                  ("Volumenexplosion (ab 3-fach)", True,
                   f"{vol:.1f}-fach".replace(".", ",") + (" – ideal" if vol >= EP_VOLUMEN_IDEAL else "")),
                  ("Nachricht", nachricht, "Zahlen am Sprungtag" if nachricht else "Nachricht prüfen (keine Zahlen)"),
                  ("Vernachlässigt (davor kein starker Anstieg)", vorlauf <= EP_VORLAUF_MAX,
                   f"3 Monate davor {vorlauf:+.0f} %"),
                  ("Kurs hält das Tief des Sprungtags", haelt, f"Tief {l[i]:.2f} $".replace(".", ","))]
        if not haelt:
            ampel = "rot"
        elif nachricht:
            ampel = "grün"
        else:
            ampel = "gelb"
        return {"art": "Episodic Pivot", "ampel": ampel, "regeln": regeln, "tag": tag, "tage_her": n - 1 - i,
                "pivot": float(h[i]), "stopp": float(l[i]), "volumen": vol, "ideal": vol >= EP_VOLUMEN_IDEAL}
    return None


def pruefen(df, erk, gewinn_tage=(), ticker=""):
    fr = fuehrer_rang.von(ticker) if ticker else None
    b = breakout(df, erk, fr)
    ep = episodic_pivot(df, gewinn_tage)
    em = vcp_zone.ermuedung(df)
    setups = [x for x in (ep, b) if x]
    rang = {"grün": 0, "gelb": 1, "rot": 2}
    haupt = min(setups, key=lambda x: (rang[x["ampel"]], x["art"] != "Episodic Pivot")) if setups else None
    a = adtr(df)
    k = float(df["Close"].iloc[-1])
    return {"system": "K", "ampel": haupt["ampel"] if haupt else "rot", "haupt": haupt, "breakout": b, "ep": ep,
            "ermuedung": em, "fuehrer": fr, "fuehrer_ampel": fuehrer_rang.ampel(fr), "adtr": a,
            "adtr_pct": a / k * 100 if a else None,
            "setup": haupt["art"] if haupt and haupt["ampel"] != "rot" else "keines",
            "ausstieg": ("Stopp am Tagestief des Einstiegstags (kein Trade, wenn weiter weg als eine Tagesspanne"
                         + (f", heute {a:.2f} $ = {a / k * 100:.1f} %".replace(".", ",") if a else "")
                         + "). Teilgewinn in den ersten 3–5 Tagen, Stopp auf Einstand, den Rest bis zum Schluss unter dem "
                           "10- oder 20-Tage-Durchschnitt halten (Kullamägi).")}


def gd10_20(df):
    c = df["Close"].to_numpy(float)
    return (float(c[-10:].mean()), float(c[-20:].mean())) if len(c) >= 20 else (None, None)
