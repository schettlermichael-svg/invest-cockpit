"""System Minervini (SEPA, 05.11.2026): Positionstrader mit Fundament. Er kauft Führer mit guten Zahlen am Pivot einer
reifen, engen Base in Stufe 2. Eines der zwei getrennten Systeme der App (das andere: system_kullamaegi.py).

Regeln für „grün“ (alle erfüllt; gelb = genau eine fehlt oder die Enge ist erst teilweise da; sonst rot):
  1. Trendvorlage: die sieben Punkte zu Kurs und Durchschnitten (Kurs über GD150/200, GD150 über GD200, GD200 steigt
     seit einem Monat, GD50 über GD150/200, Kurs über GD50, mindestens 30 % über dem 52-Wochen-Tief, höchstens 25 % unter
     dem 52-Wochen-Hoch). Sie entspricht Weinsteins Stufe 2.
  2. RS ab 70 – der achte Punkt der Trendvorlage.
  3. Zahlen wachsen: Quartalsgewinn und Umsatz zum Vorjahr nicht rot (Fundament-Ampeln).
  4. Reife Wertzone (Base oder Flagge nach einem Lauf nach oben) mit Pivot, höchstens 50 % tief.
  5. Enge (VCP): am rechten Rand halten oder steigen die Tiefs, die Spanne zieht sich zusammen, das Volumen trocknet aus
     (Ampel „Angebot aufgenommen“). Erfüllt bei grün oder teilweise (gelb); nicht erfüllt bei rot. Eine Flagge unter drei
     Wochen ist zu kurz zum Messen und sperrt nicht (Hinweis: im Chart prüfen).
Pivot = Oberkante der Wertzone; Kaufzone bis +5 %. Stopp unter dem Tief der letzten Kontraktion, höchstens 8 % unter dem
Pivot. Ausstieg: Stopp auf Einstand, sobald der Gewinn ein Mehrfaches des Risikos erreicht; in die Stärke teilweise
verkaufen, den Rest mit nachgezogenem Stopp laufen lassen.
Der Markt (markt_systeme.minervini) ist eine eigene Ampel und gehört nicht zu „grün“ – kein Filter.
"""
RS_MIN = 70
MAX_STOPP = 0.08
KAUFZONE = 5.0


def trendvorlage(df):
    """Die sieben Punkte der Trendvorlage ohne RS: Kurzname → erfüllt? (leer bei zu kurzer Historie)."""
    c, h, l = (df[s].to_numpy(float) for s in ("Close", "High", "Low"))
    if len(c) < 260:
        return {}
    g50, g150, g200 = c[-50:].mean(), c[-150:].mean(), c[-200:].mean()
    g200_vor = c[-222:-22].mean()
    k = c[-1]
    return {"Kurs über GD150/200": bool(k > g150 and k > g200), "GD150 über GD200": bool(g150 > g200),
            "GD200 steigt": bool(g200 > g200_vor), "GD50 über GD150/200": bool(g50 > g150 and g50 > g200),
            "Kurs über GD50": bool(k > g50), "30 % über Tief": bool(k >= 1.30 * l[-252:].min()),
            "höchstens 25 % unter Hoch": bool(k >= 0.75 * h[-252:].max())}


def _zahlen(fund):
    if not fund:
        return False, "keine Fundamentdaten"
    pk = fund["punkte"]
    g, u = pk.get("Quartalsgewinn zum Vorjahr", ("grau", "")), pk.get("Umsatz", ("grau", ""))
    if g[0] == "grau" and u[0] == "grau":
        return False, "keine Fundamentdaten"
    ok = g[0] != "rot" and u[0] != "rot"
    letzt = lambda x: x[1].split(" / ")[-1].split(" (")[0] if x[0] != "grau" else "–"   # noqa: E731
    return ok, f"Gewinn {letzt(g)}, Umsatz {letzt(u)} zum Vorjahr"


def pruefen(df, erk, rs_rang, fund):
    """Ergebnis: ampel, setup (Wort), regeln [(Name, ok, Text)], pivot, stopp, lage, ausstieg."""
    tv = trendvorlage(df)
    c, l = df["Close"].to_numpy(float), df["Low"].to_numpy(float)
    w = erk.get("werte") or {}
    art = (erk.get("muster") or [None])[0]
    reif = art in ("Base", "Flagge") and erk.get("seite") == "long" and "pivot" in w and w.get("tiefe_pct", 99) <= 50
    a = erk.get("absorption") or {}
    eng = (a.get("ampel", "grau") if a else "leer") if reif else "grau"
    z_ok, z_txt = _zahlen(fund)
    regeln = [("Trendvorlage (7 Punkte)", bool(tv) and all(tv.values()),
               f"{sum(tv.values())} von 7" + ("" if not tv or all(tv.values()) else
                                               " – fehlt: " + ", ".join(n for n, ok in tv.items() if not ok))
               if tv else "zu kurze Historie"),
              ("RS ab 70 (8. Punkt)", rs_rang is not None and rs_rang >= RS_MIN,
               f"RS {rs_rang} von 99" if rs_rang is not None else "kein RS-Rang"),
              ("Zahlen wachsen", z_ok, z_txt),
              ("Reife Wertzone mit Pivot", reif,
               f"{art} {w.get('wochen')} Wochen, {w.get('tiefe_pct', 0):.0f} % tief".replace(".", ",") if reif
               else "keine Base/Flagge nach oben" if art not in ("Base", "Flagge") else "zu tief oder ohne Pivot"),
              ("Enge (VCP)", eng in ("grün", "gelb", "leer"),
               {"grün": "Tiefs halten, Spanne eng, Volumen trocken", "gelb": "teilweise eng (Tiefs/Spanne oder Volumen)",
                "rot": "nicht eng – Tiefs fallen oder Spanne und Volumen weit", "grau": "ohne Wertzone nicht prüfbar",
                "leer": "Wertzone zu kurz zum Messen – Enge im Chart prüfen"}[eng])]
    fehlt = sum(1 for _, ok, _ in regeln if not ok)
    ampel = "grün" if fehlt == 0 else "gelb" if fehlt == 1 else "rot"
    pivot = float(w["pivot"]) if reif else None
    stopp, lage = None, ""
    if pivot:
        tiefs = [l[lo] for _, lo, _ in (w.get("kontraktionen_lage") or []) if lo < len(l)]
        unten = min(tiefs[-1], pivot) if tiefs else pivot * (1 - MAX_STOPP)
        stopp = max(unten, pivot * (1 - MAX_STOPP))
        ab = (c[-1] / pivot - 1) * 100
        lage = ("in der Kaufzone" if 0 <= ab <= KAUFZONE else f"{ab:.1f} % über dem Pivot, ausgedehnt" if ab > KAUFZONE
                else f"{-ab:.1f} % unter dem Pivot").replace(".", ",")
    setup = f"{art} {w.get('wochen')} W." if reif else "keines"
    return {"system": "M", "ampel": ampel, "setup": setup, "regeln": regeln, "fehlt": fehlt,
            "pivot": pivot, "stopp": stopp, "lage": lage, "trendvorlage": tv,
            "ausstieg": ("Stopp unter dem Tief der letzten Kontraktion, höchstens 8 % unter dem Pivot. Stopp auf Einstand, "
                         "sobald der Gewinn ein Mehrfaches des Risikos erreicht; in die Stärke teilweise verkaufen, den "
                         "Rest mit nachgezogenem Stopp laufen lassen (Minervini).")}


def kurz(m):
    """Eine Zeile für Karte und Hinweis: was fehlt."""
    fehlt = [n for n, ok, _ in m["regeln"] if not ok]
    return "alle Regeln erfüllt" if not fehlt else "fehlt: " + ", ".join(fehlt)
