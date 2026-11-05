"""Geplantes Chance-Risiko-Verhältnis – vor dem Kauf, als Zeichen, kein Filter (grüne Null, 05.11.2026).

Einstieg und Setup-Stopp (A) wie auf der Lagekarte (depot.plan: Pivot bzw. Auslöser; VAH/VAL der Zone oder ∓8 %).
Ziel nach O'Neil: +20 % über dem Einstieg (Short: −20 %) – dort nimmt er Gewinne. Stopp B: außerhalb des Tagesrauschens,
mindestens 1,5 × ATR vom Einstieg (nur gezeigt, wenn A näher liegt). CRV = Chance ÷ Risiko; grün ab 3 : 1, gelb ab 2 : 1,
rot darunter (Minervini will mindestens 2–3 : 1).
Widerstand vor dem Ziel (Weinstein): das nächste alte Hoch der letzten zwei Jahre, das seither nicht überstiegen wurde,
oder ein fallender GD150/GD200 zwischen Einstieg und Ziel (Short gespiegelt: altes Tief bzw. steigender Durchschnitt).
Weinstein kauft am liebsten dort, wo über dem Ausbruch wenig Widerstand liegt – sonst wird der Weg zäh.
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


FENSTER, JAHRE2 = 10, 504     # Wendepunkt: höchstes Hoch ±10 Tage; Suche über zwei Jahre


def widerstand(df, seite, e, ziel):
    """Nächste Stellung zwischen Einstieg und Ziel: (Preis, Art) oder None."""
    if df is None or len(df) < 60:
        return None
    h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
    n = len(h)
    a = max(0, n - JAHRE2)
    lang = seite == "long"
    lo_, hi_ = (e * 1.01, ziel) if lang else (ziel, e * 0.99)
    kand = []
    for i in range(a, n - 1):
        f0, f1 = max(a, i - FENSTER), min(n, i + FENSTER + 1)
        if lang and h[i] >= h[f0:f1].max() and h[i] >= h[i + 1:].max() and lo_ <= h[i] <= hi_:
            kand.append((float(h[i]), f"altes Hoch {df.index[i]:%d.%m.%y}"))
        if not lang and l[i] <= l[f0:f1].min() and l[i] <= l[i + 1:].min() and lo_ <= l[i] <= hi_:
            kand.append((float(l[i]), f"altes Tief {df.index[i]:%d.%m.%y}"))
    for k in (150, 200):
        if n >= k + 20:
            gd = df["Close"].rolling(k).mean()
            jetzt, vorher = float(gd.iloc[-1]), float(gd.iloc[-21])
            if lo_ <= jetzt <= hi_ and ((lang and jetzt < vorher) or (not lang and jetzt > vorher)):
                kand.append((jetzt, f"GD{k} {'fallend' if lang else 'steigend'}"))
    if not kand:
        return None
    return (min if lang else max)(kand, key=lambda t: t[0])


def linien(erk, atr_wert, df=None):
    """Einstieg, Ziel (+20 %), Stopp A, Stopp B (oder None), Widerstand vor dem Ziel und die CRV-Werte – für Lagekarte
    und Chart; None ohne Plan."""
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
            "ziel": ziel, "crv_a": chance / r_a, "crv_b": chance / r_b if r_b else None,
            "widerstand": widerstand(df, seite, e, ziel)}


def zeichen(erk, df, atr_wert):
    """Liste (Ampel, Text) für die Lagekarte."""
    import depot
    li = linien(erk, atr_wert, df)
    if not li:
        return []
    aus = [(_ampel(li["crv_a"]), f"CRV {_z(li['crv_a'])} : 1 mit Setup-Stopp · Ziel {_geld(li['ziel'])} $ "
                                 f"({'+' if li['seite'] == 'long' else '−'}20 %, O'Neil)")]
    w = li["widerstand"]
    lang = li["seite"] == "long"
    if w:
        abst = abs(w[0] / li["einstieg"] - 1) * 100
        aus.append(("gelb" if abst >= 10 else "rot",
                    f"{'Widerstand' if lang else 'Halt'} vor dem Ziel: {_geld(w[0])} $ ({w[1]}), {_z(abst)} % "
                    f"{'über' if lang else 'unter'} dem Einstieg – Weinstein: der Weg wird zäh"))
    else:
        aus.append(("grün", f"Kein {'Widerstand' if lang else 'Halt'} bis zum Ziel – freie Bahn (Weinstein)"))
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
