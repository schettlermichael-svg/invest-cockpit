"""Geplantes Chance-Risiko-Verhältnis (05.11.2026) – vor dem Kauf, als Zeichen, kein Filter.

Einstieg und Setup-Stopp (A) wie auf der Lagekarte (depot.plan: Pivot bzw. Auslöser; VAH/VAL der Zone oder ∓8 %).
Ziel: der erste FESTE Widerstand (long) bzw. die erste feste Unterstützung (short) aus der Freien Bahn – dünne Marken
(ein altes Hoch ohne Umsatz) zählen nicht. Stopp B: außerhalb des Tagesrauschens, mindestens 1,5 × ATR vom Einstieg
(nur gezeigt, wenn A näher liegt). CRV = Chance ÷ Risiko; grün ab 3 : 1, gelb ab 2 : 1, rot darunter (unsere
Setzung; Minervini will mindestens 2–3 : 1).
Minervini-Abgleich: der Stopp soll höchstens die Hälfte, besser ein Drittel des eigenen Durchschnittsgewinns betragen –
aus den geschlossenen Trades im Depot (depot.bilanz), sobald mindestens MIN_TRADES vorliegen.
"""
B_ATR = 1.5
MIN_TRADES = 5


def _z(x):
    return f"{x:.1f}".replace(".", ",")


def _geld(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _ampel(x):
    return "grün" if x >= 3 else "gelb" if x >= 2 else "rot"


def zeichen(erk, df, atr_wert):
    """Liste (Ampel, Text) für die Lagekarte."""
    import depot
    pl = depot.plan(erk)
    fb = erk.get("bahn")
    if not pl or not fb:
        return []
    seite, e, s_a, _ = pl
    fest = (fb.get(seite) or {}).get("fest")
    if not fest or (fest[0] <= e if seite == "long" else fest[0] >= e):
        return [("grün", f"CRV offen: kein fester {'Widerstand darüber' if seite == 'long' else 'Halt darunter'} – "
                         f"freie Bahn")]
    ziel, art = fest
    chance = abs(ziel - e)
    r_a = abs(e - s_a)
    if r_a <= 0:
        return []
    aus = []
    x = chance / r_a
    aus.append((_ampel(x), f"CRV {_z(x)} : 1 mit Setup-Stopp · Ziel {_geld(ziel)} $ ({art})"))
    if atr_wert and r_a < B_ATR * atr_wert:
        r_b = B_ATR * atr_wert
        y = chance / r_b
        s_b = e - r_b if seite == "long" else e + r_b
        aus.append((_ampel(y), f"CRV {_z(y)} : 1 mit Stopp außerhalb des Rauschens ({_geld(s_b)} $ = 1,5 × ATR)"))
    b = depot.bilanz()
    if b and b["anzahl"] >= MIN_TRADES and b["schnitt_gewinn"]:
        stopp_pct = r_a / e * 100
        anteil = stopp_pct / b["schnitt_gewinn"]
        a_ = "grün" if anteil <= 1 / 3 else "gelb" if anteil <= 0.5 else "rot"
        aus.append((a_, f"Stopp {_z(stopp_pct)} % = {_z(anteil * 100)} % deines Durchschnittsgewinns "
                        f"({_z(b['schnitt_gewinn'])} %) – Minervini: höchstens die Hälfte, besser ein Drittel"))
    return aus
