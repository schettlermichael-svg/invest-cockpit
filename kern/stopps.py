"""Stopps und CRV vor dem Kauf (grüne Null, 05.11.2026) – Gewinne laufen lassen, Stopp nachziehen; das CRV ist ein Maß,
ob sich der Einsatz lohnt, kein Ausstieg.

Einstieg und Stopp wie auf der Lagekarte (depot.plan): ein Stopp, 1,5 ATR vom Einstieg wie im Chart (10.11.2026;
vorher Stopp A des Systems und Stopp B 1,5 × ATR nebeneinander). Stopp B bleibt nur, wenn erk keine ATR trägt.
Nächster Widerstand über dem Einstieg (Weinstein): das nächste alte Hoch der letzten 52 Wochen, das seither nicht
überstiegen wurde (ältere Hochs sind ausgewaschen), oder ein fallender GD150/GD200 (Short gespiegelt: altes Tief bzw.
steigender Durchschnitt) oder der nächste Volumenknoten des 52-Wochen-Profils (Auction Market Theory: der Preis wandert
von Wert zu Wert) – die erste Hürde, an der der Lauf stocken kann.
CRV 1 = Abstand bis zur ersten Hürde ÷ Stoppabstand (Weinstein/AMT, bewusst vorsichtig); ohne Hürde „freie Bahn“.
CRV 2 = eigener Durchschnittsgewinn ÷ Stoppabstand (Minervini), sobald MIN_TRADES geschlossene Trades vorliegen.
Ampel: grün ab 3 : 1, gelb ab 2 : 1 (Minervini: Stopp höchstens die Hälfte, besser ein Drittel des Gewinns).
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


def _ampel(x):
    return "grün" if x >= 3 else "gelb" if x >= 2 else "rot"


def widerstand(df, seite, e, knoten=()):
    """Erste Hürde jenseits des Einstiegs in Laufrichtung: (Preis, Art) oder None."""
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
    for k0, k1 in knoten or ():                 # Volumenknoten des 52-Wochen-Profils: nächster Wert in Laufrichtung
        if lang and k0 > e * 1.01:
            kand.append((float(k0), f"Volumenknoten {_geld(k0)}–{_geld(k1)} $"))
        if not lang and k1 < e * 0.99:
            kand.append((float(k1), f"Volumenknoten {_geld(k0)}–{_geld(k1)} $"))
    if not kand:
        return None
    return (min if lang else max)(kand, key=lambda t: t[0])


def linien(erk, atr_wert, df=None):
    """Einstieg, Stopp A, Stopp B (oder None), erste Hürde, CRV bis zur Hürde und mit dem eigenen Durchschnittsgewinn – für
    Lagekarte und Chart; None ohne Plan."""
    import depot
    pl = depot.plan(erk)
    if not pl:
        return None
    seite, e, s_a, _ = pl
    r_a = abs(e - s_a)
    if r_a <= 0:
        return None
    r_b = B_ATR * atr_wert if atr_wert and r_a < B_ATR * atr_wert else None
    w = widerstand(df, seite, e, ((erk.get("profil") or {}).get("knoten")))
    erg = {"seite": seite, "einstieg": e, "stopp_a": s_a, "risiko_a": r_a,
           "stopp_b": (e - r_b if seite == "long" else e + r_b) if r_b else None, "risiko_b": r_b, "widerstand": w}
    if w:
        chance = abs(w[0] - e)
        erg["crv_a"], erg["crv_b"] = chance / r_a, (chance / r_b if r_b else None)
    b = depot.bilanz()
    if b and b["anzahl"] >= MIN_TRADES and b["schnitt_gewinn"]:
        erg["schnitt"] = b["schnitt_gewinn"]
        erg["crv_schnitt"] = (e * b["schnitt_gewinn"] / 100) / r_a
    return erg


def zeichen(erk, df, atr_wert):
    """Liste (Ampel, Text) für die Lagekarte."""
    li = linien(erk, atr_wert, df)
    if not li:
        return []
    lang = li["seite"] == "long"
    e = li["einstieg"]
    aus = [("grau", f"Stopp {_geld(li['stopp_a'])} $ ({_z(li['risiko_a'] / e * 100)} % vom Einstieg"
                    + (", 1,5 × ATR" if not li["stopp_b"] else "")
                    + (f") · Stopp B {_geld(li['stopp_b'])} $ ({_z(li['risiko_b'] / e * 100)} %, 1,5 × ATR"
                       if li["stopp_b"] else "") + ") – danach nachziehen")]
    w = li["widerstand"]
    if w:
        aus.append((_ampel(li["crv_a"]),
                    f"CRV bis zur ersten Hürde {_z(li['crv_a'])} : 1"
                    + (f" (mit Stopp B {_z(li['crv_b'])} : 1)" if li.get("crv_b") else "")
                    + f" · Hürde {_geld(w[0])} $ ({w[1]}), {_z(abs(w[0] / e - 1) * 100)} % "
                    f"{'über' if lang else 'unter'} dem Einstieg"))
    else:
        aus.append(("grün", "Keine Hürde in den letzten 52 Wochen – freie Bahn (Weinstein), CRV offen"))
    if li.get("crv_schnitt"):
        aus.append((_ampel(li["crv_schnitt"]),
                    f"CRV mit deinem Durchschnittsgewinn ({_z(li['schnitt'])} %) {_z(li['crv_schnitt'])} : 1 – "
                    f"Minervini: Stopp höchstens die Hälfte, besser ein Drittel des Gewinns"))
    return aus
