"""Geplantes Chance-Risiko-Verhältnis (05.11.2026) – vor dem Kauf, als Zeichen, kein Filter.

Einstieg und Setup-Stopp (A) wie auf der Lagekarte (depot.plan: Pivot bzw. Auslöser; VAH/VAL der Zone oder ∓8 %).
Ziel: die nächste FESTE Stellung jenseits des Einstiegs aus dem Gelände (VAL einer alten Festung bzw. VAH beim Short,
oder ein Volumenknoten des 52-Wochen-Profils); ohne Gelände der erste feste Widerstand der Freien Bahn. Wartesäle und
dünne Marken zählen nicht. Stopp B: außerhalb des Tagesrauschens, mindestens 1,5 × ATR vom Einstieg
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


def linien(erk, atr_wert):
    """Einstieg, Ziel, Stopp A, Stopp B (oder None) und die CRV-Werte – für Lagekarte und Chart; None ohne Plan.
    ziel None = kein fester Widerstand bzw. Halt (freie Bahn)."""
    import depot
    pl = depot.plan(erk)
    fb = erk.get("bahn")
    if not pl or not (fb or erk.get("gelaende")):
        return None
    seite, e, s_a, _ = pl
    r_a = abs(e - s_a)
    if r_a <= 0:
        return None
    g = erk.get("gelaende")
    if g:                                         # Gelände: nächste Festung (alte Zone mit Volumen) oder fester Knoten
        import gelaende
        fest = gelaende.ziel(g, e, seite)
    else:
        fest = (fb.get(seite) or {}).get("fest")
    if fest and (fest[0] <= e if seite == "long" else fest[0] >= e):
        fest = None
    r_b = B_ATR * atr_wert if atr_wert and r_a < B_ATR * atr_wert else None
    erg = {"seite": seite, "einstieg": e, "stopp_a": s_a, "risiko_a": r_a,
           "stopp_b": (e - r_b if seite == "long" else e + r_b) if r_b else None, "risiko_b": r_b,
           "ziel": fest[0] if fest else None, "art": fest[1] if fest else None}
    if fest:
        chance = abs(fest[0] - e)
        erg["crv_a"] = chance / r_a
        erg["crv_b"] = chance / r_b if r_b else None
    return erg


def zeichen(erk, df, atr_wert):
    """Liste (Ampel, Text) für die Lagekarte."""
    import depot
    li = linien(erk, atr_wert)
    if not li:
        return []
    if li["ziel"] is None:
        return [("grün", f"CRV offen: kein fester {'Widerstand darüber' if li['seite'] == 'long' else 'Halt darunter'} – "
                         f"freie Bahn")]
    aus = [(_ampel(li["crv_a"]), f"CRV {_z(li['crv_a'])} : 1 mit Setup-Stopp · Ziel {_geld(li['ziel'])} $ ({li['art']})")]
    if li["crv_b"]:
        aus.append((_ampel(li["crv_b"]), f"CRV {_z(li['crv_b'])} : 1 mit Stopp außerhalb des Rauschens "
                                         f"({_geld(li['stopp_b'])} $ = 1,5 × ATR)"))
    b = depot.bilanz()
    if b and b["anzahl"] >= MIN_TRADES and b["schnitt_gewinn"]:
        stopp_pct = li["risiko_a"] / li["einstieg"] * 100
        anteil = stopp_pct / b["schnitt_gewinn"]
        a_ = "grün" if anteil <= 1 / 3 else "gelb" if anteil <= 0.5 else "rot"
        aus.append((a_, f"Stopp {_z(stopp_pct)} % = {_z(anteil * 100)} % deines Durchschnittsgewinns "
                        f"({_z(b['schnitt_gewinn'])} %) – Minervini: höchstens die Hälfte, besser ein Drittel"))
    return aus
