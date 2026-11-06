"""Markt je System (05.11.2026, „Zwei Systeme“): Die App modelliert zwei getrennte Systeme – Minervini und Kullamägi –,
jedes mit seiner eigenen Marktregel. O'Neils Marktrichtung (marktrichtung.py) bleibt als Zeichen sichtbar.

Kullamägi (Interview mit Jack Schwager, „Market Wizards“-Reihe): Steigen der 10- und der 20-Tage-Durchschnitt des Index,
ist der Markt im Aufwärtstrend; kreuzt der 10er den 20er nach unten, ist das ein Warnsignal. Breakout und Episodic Pivot
nur im Aufwärtstrend; der Short (Ermüdung nach Überdehnung) ist unabhängig vom Markt. Er schätzt: hält ihn in rund 80 % der Fälle aus
schlechten Märkten heraus und in gute hinein.
  grün  10er über 20er, beide steigend (über dem Wert von vor STEIGEND_TAGE Handelstagen)
  gelb  10er über 20er, aber nicht beide steigend
  rot   10er unter 20er
  Gesamt: grün nur, wenn S&P 500 und Nasdaq grün sind; rot, wenn beide rot sind; sonst gelb.

Minervini nennt keine feste Formel für den Markt; er folgt den Führern (funktionieren ihre Ausbrüche, mehr neue Hochs
als Tiefs) und dem Stand der Indizes. Umsetzung hier (Vorschlag, aus seinen Büchern abgeleitet, keine Buchregel):
  grün  S&P 500 und Nasdaq über GD50 und GD200, neue 52-Wochen-Hochs mehr als Tiefs
  rot   ein Index unter GD200 oder mehr als doppelt so viele Tiefs wie Hochs
  gelb  sonst
"""
import marktdaten as md

STEIGEND_TAGE = 3            # „steigend“: Durchschnitt heute über dem Wert von vor 3 Handelstagen (glättet Tagesrauschen)
INDIZES = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC"}


def _gd(c, n, zurueck=0):
    ende = len(c) - zurueck
    return float(c[ende - n:ende].mean())


def zehn_zwanzig(c):
    """Kullamägis Regel für eine Schlusskursreihe (numpy): Ampel und Werte."""
    g10, g20 = _gd(c, 10), _gd(c, 20)
    g10v, g20v = _gd(c, 10, STEIGEND_TAGE), _gd(c, 20, STEIGEND_TAGE)
    s10, s20 = g10 > g10v, g20 > g20v
    ampel = "rot" if g10 < g20 else "grün" if (s10 and s20) else "gelb"
    return {"ampel": ampel, "g10": g10, "g20": g20, "s10": s10, "s20": s20}


def _wort(x):
    lage = "10er über 20er" if x["g10"] >= x["g20"] else "10er unter 20er"
    return f'{lage}, 10er {"steigt" if x["s10"] else "fällt"}, 20er {"steigt" if x["s20"] else "fällt"}'


def kullamaegi():
    je = {}
    for name, tk in INDIZES.items():
        c = md.yahoo_ohlc(tk)["Close"].to_numpy(float)
        je[name] = zehn_zwanzig(c)
    farben = [x["ampel"] for x in je.values()]
    ampel = "grün" if all(f == "grün" for f in farben) else "rot" if all(f == "rot" for f in farben) else "gelb"
    wort = {"grün": "Aufwärtstrend", "gelb": "Warnung", "rot": "Abwärtstrend"}[ampel]
    return {"ampel": ampel, "wort": wort, "je": je,
            "text": " · ".join(f"{n}: {_wort(x)}" for n, x in je.items()),
            "regel": "Kullamägi: 10- und 20-Tage-Durchschnitt des Index steigen = Aufwärtstrend; 10er kreuzt den 20er "
                     "nach unten = Warnsignal. Breakout und Episodic Pivot nur im Aufwärtstrend; der Short (Ermüdung nach Überdehnung) ist "
                     "unabhängig vom Markt."}


def minervini(hochs=None, tiefs=None):
    je, unter200, alle_ueber = {}, False, True
    for name, tk in INDIZES.items():
        c = md.yahoo_ohlc(tk)["Close"].to_numpy(float)
        g50, g200 = _gd(c, 50), _gd(c, 200)
        k = float(c[-1])
        je[name] = {"kurs": k, "g50": g50, "g200": g200}
        unter200 |= k < g200
        alle_ueber &= k > g50 and k > g200
    breit = hochs is not None and tiefs is not None
    if unter200 or (breit and tiefs > 2 * hochs):
        ampel = "rot"
    elif alle_ueber and (not breit or hochs > tiefs):
        ampel = "grün"
    else:
        ampel = "gelb"
    teile = [f'{n}: {"über" if x["kurs"] > x["g50"] else "unter"} GD50, {"über" if x["kurs"] > x["g200"] else "unter"} GD200'
             for n, x in je.items()]
    if breit:
        teile.append(f"neue Hochs : Tiefs {hochs} : {tiefs}")
    wort = {"grün": "Rückenwind", "gelb": "gemischt", "rot": "Gegenwind"}[ampel]
    return {"ampel": ampel, "wort": wort, "je": je, "text": " · ".join(teile),
            "regel": "Minervini folgt den Führern und dem Stand der Indizes; eine feste Formel nennt er nicht. Hier: "
                     "grün = S&P 500 und Nasdaq über GD50 und GD200 und mehr neue Hochs als Tiefs; rot = ein Index unter "
                     "GD200 oder mehr als doppelt so viele Tiefs wie Hochs (Umsetzung der App, keine Buchregel)."}
