"""Stopps vor dem Kauf (grüne Null, 05.11.2026) – kein festes Ziel, kein CRV: Gewinne laufen lassen, Stopp nachziehen.

Einstieg und Setup-Stopp (A) wie auf der Lagekarte (depot.plan: Pivot bzw. Auslöser; VAH/VAL der Zone oder ∓8 %).
Stopp B: außerhalb des Tagesrauschens, mindestens 1,5 × ATR vom Einstieg (nur gezeigt, wenn A näher liegt).
Nächster Widerstand über dem Einstieg (Weinstein): das nächste alte Hoch der letzten 52 Wochen, das seither nicht
überstiegen wurde (ältere Hochs sind ausgewaschen), oder ein fallender GD150/GD200 (Short gespiegelt: altes Tief bzw.
steigender Durchschnitt) – dort kann der Lauf zuerst stocken; kein Ziel.
Minervini-Abgleich: der Stopp soll höchstens die Hälfte, besser ein Drittel des eigenen Durchschnittsgewinns betragen –
aus den geschlossenen Trades im Depot (depot.bilanz), sobald mindestens MIN_TRADES vorliegen.
"""
B_ATR = 1.5
MIN_TRADES = 5
FENSTER, JAHR = 10, 252       # Wendepunkt: höchstes Hoch ±10 Tage; Suche über 52 Wochen


def _z(x):
    return f"{x:.1f}".replace(".", ",")


def _geld(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def widerstand(df, seite, e):
    """Nächste Stellung jenseits des Einstiegs in Laufrichtung: (Preis, Art) oder None."""
    if df is None or len(df) < 60:
        return None
    h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
    n = len(h)
    a = max(0, n - JAHR)
    lang = seite == "long"
    kand = []
    for i in range(a, n - 1):
        f0, f1 = max(a, i - FENSTER), min(n, i + FENSTER + 1)
        if lang and h[i] >= h[f0:f1].max() and h[i] >= h[i + 1:].max() and h[i] > e * 1.01:
            kand.append((float(h[i]), f"altes Hoch {df.index[i]:%d.%m.%y}"))
        if not lang and l[i] <= l[f0:f1].min() and l[i] <= l[i + 1:].min() and l[i] < e * 0.99:
            kand.append((float(l[i]), f"altes Tief {df.index[i]:%d.%m.%y}"))
    for k in (150, 200):
        if n >= k + 20:
            gd = df["Close"].rolling(k).mean()
            jetzt, vorher = float(gd.iloc[-1]), float(gd.iloc[-21])
            if (lang and jetzt > e * 1.01 and jetzt < vorher) or (not lang and jetzt < e * 0.99 and jetzt > vorher):
                kand.append((jetzt, f"GD{k} {'fallend' if lang else 'steigend'}"))
    if not kand:
        return None
    return (min if lang else max)(kand, key=lambda t: t[0])


def linien(erk, atr_wert, df=None):
    """Einstieg, Stopp A, Stopp B (oder None), nächster Widerstand – für Lagekarte und Chart; None ohne Plan."""
    import depot
    pl = depot.plan(erk)
    if not pl:
        return None
    seite, e, s_a, _ = pl
    r_a = abs(e - s_a)
    if r_a <= 0:
        return None
    r_b = B_ATR * atr_wert if atr_wert and r_a < B_ATR * atr_wert else None
    return {"seite": seite, "einstieg": e, "stopp_a": s_a, "risiko_a": r_a,
            "stopp_b": (e - r_b if seite == "long" else e + r_b) if r_b else None, "risiko_b": r_b,
            "widerstand": widerstand(df, seite, e)}


def zeichen(erk, df, atr_wert):
    """Liste (Ampel, Text) für die Lagekarte."""
    import depot
    li = linien(erk, atr_wert, df)
    if not li:
        return []
    lang = li["seite"] == "long"
    e = li["einstieg"]
    aus = [("grau", f"Stopp A {_geld(li['stopp_a'])} $ ({_z(li['risiko_a'] / e * 100)} % vom Einstieg)"
                    + (f" · Stopp B {_geld(li['stopp_b'])} $ ({_z(li['risiko_b'] / e * 100)} %, 1,5 × ATR)"
                       if li["stopp_b"] else "") + " – danach nachziehen")]
    w = li["widerstand"]
    if w:
        abst = abs(w[0] / e - 1) * 100
        aus.append(("rot" if abst < 10 else "gelb",
                    f"Nächster {'Widerstand' if lang else 'Halt'} (letzte 52 Wochen): {_geld(w[0])} $ ({w[1]}), "
                    f"{_z(abst)} % {'über' if lang else 'unter'} dem Einstieg – Weinstein: dort kann der Lauf stocken"))
    else:
        aus.append(("grün", f"Kein {'Widerstand' if lang else 'Halt'} in den letzten 52 Wochen – freie Bahn (Weinstein)"))
    b = depot.bilanz()
    if b and b["anzahl"] >= MIN_TRADES and b["schnitt_gewinn"]:
        stopp_pct = li["risiko_a"] / e * 100
        anteil = stopp_pct / b["schnitt_gewinn"]
        a_ = "grün" if anteil <= 1 / 3 else "gelb" if anteil <= 0.5 else "rot"
        aus.append((a_, f"Stopp {_z(stopp_pct)} % = {_z(anteil * 100)} % deines Durchschnittsgewinns "
                        f"({_z(b['schnitt_gewinn'])} %) – Minervini: höchstens die Hälfte, besser ein Drittel"))
    return aus
