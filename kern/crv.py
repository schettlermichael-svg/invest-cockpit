"""Geplantes Chance-Risiko-Verhältnis – vor dem Kauf, als Zeichen, kein Filter (grüne Null, 05.11.2026).

Einstieg und Setup-Stopp (A) wie auf der Lagekarte (depot.plan: Pivot bzw. Auslöser; VAH/VAL der Zone oder ∓8 %).
Ziel nach O'Neil: +20 % über dem Einstieg (Short: −20 %) – dort nimmt er Gewinne. Stopp B: außerhalb des Tagesrauschens,
mindestens 1,5 × ATR vom Einstieg (nur gezeigt, wenn A näher liegt). CRV = Chance ÷ Risiko; grün ab 3 : 1, gelb ab 2 : 1,
rot darunter (Minervini will mindestens 2–3 : 1).
Minervini-Abgleich: der Stopp soll höchstens die Hälfte, besser ein Drittel des eigenen Durchschnittsgewinns betragen –
aus den geschlossenen Trades im Depot (depot.bilanz), sobald mindestens MIN_TRADES vorliegen.
"""
B_ATR = 1.5
ZIEL = 0.20             # O'Neil: Gewinne bei +20 bis 25 % sichern
MIN_TRADES = 5


def _z(x):
    return f"{x:.1f}".replace(".", ",")


def _geld(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _ampel(x):
    return "grün" if x >= 3 else "gelb" if x >= 2 else "rot"


def linien(erk, atr_wert):
    """Einstieg, Ziel (+20 %), Stopp A, Stopp B (oder None) und die CRV-Werte – für Lagekarte und Chart; None ohne Plan."""
    import depot
    pl = depot.plan(erk)
    if not pl:
        return None
    seite, e, s_a, _ = pl
    r_a = abs(e - s_a)
    if r_a <= 0:
        return None
    ziel = e * (1 + ZIEL) if seite == "long" else e * (1 - ZIEL)
    r_b = B_ATR * atr_wert if atr_wert and r_a < B_ATR * atr_wert else None
    chance = abs(ziel - e)
    return {"seite": seite, "einstieg": e, "stopp_a": s_a, "risiko_a": r_a,
            "stopp_b": (e - r_b if seite == "long" else e + r_b) if r_b else None, "risiko_b": r_b,
            "ziel": ziel, "crv_a": chance / r_a, "crv_b": chance / r_b if r_b else None}


def zeichen(erk, df, atr_wert):
    """Liste (Ampel, Text) für die Lagekarte."""
    import depot
    li = linien(erk, atr_wert)
    if not li:
        return []
    aus = [(_ampel(li["crv_a"]), f"CRV {_z(li['crv_a'])} : 1 mit Setup-Stopp · Ziel {_geld(li['ziel'])} $ "
                                 f"({'+' if li['seite'] == 'long' else '−'}20 %, O'Neil)")]
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
