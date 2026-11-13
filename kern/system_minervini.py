"""System Minervini (SEPA, 05.11.2026): Positionstrader mit Fundament. Er kauft Führer mit guten Zahlen am Pivot einer
reifen, engen Base in Stufe 2. Eines der zwei getrennten Systeme der App (das andere: system_kullamaegi.py).

Regeln für „grün“ (alle erfüllt; gelb = genau eine fehlt oder die Enge ist erst teilweise da; sonst rot):
  1. Trendvorlage: die sieben Punkte zu Kurs und Durchschnitten (Kurs über GD150/200, GD150 über GD200, GD200 steigt
     seit einem Monat, GD50 über GD150/200, Kurs über GD50, mindestens 30 % über dem 52-Wochen-Tief, höchstens 25 % unter
     dem 52-Wochen-Hoch). Sie entspricht Weinsteins Stufe 2.
  2. RS ab 70 – der achte Punkt der Trendvorlage.
  3. Zahlen wachsen: Quartalsgewinn und Umsatz zum Vorjahr nicht rot (Fundament-Ampeln).
  4. Reife Base: Zone des VCP-Scanners (vcp_zone.zone) ist Base oder Flagge, fertig (nicht offen), Länge in Ordnung,
     höchstens 50 % tief. Fällt die große Zone durch (zu tief, Konsolidierung nach einem Absturz), steht darin aber eine
     Flagge mit eigener Fahnenstange, gilt die Flagge als Base (Micky, 06.11.2026) – Enge, Pivot und Stopp dann aus ihr.
  5. Enge (VCP): Baustein 2 des Scanners (vcp_zone.enge) – schrumpfende Kontraktionen, letzte höchstens 10 %, Volumen
     leiser als in der ersten. Erfüllt bei grün oder teilweise (gelb) und mindestens 2 Kontraktionen (Micky 13.11.2026:
     „ab zwei Kontraktionen“ – mit einer ist es noch kein VCP); nicht erfüllt bei rot.
Seit 06.11.2026 kommen Base, Enge, Pivot und Stopp aus dem Scanner (vorher Wertzone und Absorption) – Chart, Scanner und
Minervini zeigen dieselbe Linie.
Ausbruch (06.11.2026): Schloss der Kurs in den letzten 4 Wochen über dem Pivot, gelten Zone, Enge und Pivot vom
Vortag des Ausbruchs weiter (vcp_zone.ausbruch) – sonst verschwände das Setup am Kauftag. Schluss wieder unter dem
Pivot = Fehlausbruch (Zeichen, Zone bleibt). Volumen am Ausbruchstag über dem 50-Tage-Schnitt ist ein Zeichen, keine Regel.
Pivot = Hoch der letzten Kontraktion (ohne Kontraktion: Oberkante der Zone); Kaufzone bis +5 %. Stopp unter dem Tief der
letzten Kontraktion, höchstens 8 % unter dem Pivot. Ausstieg: Stopp auf Einstand, sobald der Gewinn ein Mehrfaches des Risikos erreicht; in die Stärke teilweise
verkaufen, den Rest mit nachgezogenem Stopp laufen lassen.
Der Markt (marktklima.py, O'Neil, seit 12.11.2026) ist eine eigene Ampel und gehört nicht zu „grün“ – kein Filter.
"""
import vcp_zone

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


def pruefen(df, erk, rs_rang, fund, scan=None, ausbruch=False):
    """Ergebnis: ampel, setup (Wort), regeln [(Name, ok, Text)], pivot, stopp, lage, ausstieg, zone, enge, ausbruch.
    scan = (Zone, Enge) aus vcp_zone, ausbruch = vcp_zone.ausbruch(df), wenn schon gerechnet (False = selbst rechnen)."""
    tv = trendvorlage(df)
    c = df["Close"].to_numpy(float)
    br = vcp_zone.ausbruch(df) if ausbruch is False else ausbruch

    def _reif(b):
        return b.get("zone") and b.get("name") in ("Base", "Flagge") and b.get("laenge") == "ok" and b.get("tiefe", 99) <= 50

    def _waehle(z, e):
        """Die große Zone – oder die Flagge darin, wenn die große durchfällt (Micky, 06.11.2026)."""
        innen = z.get("innen") if z.get("zone") else None
        if not _reif(z) and innen and _reif(innen):
            return dict(innen, in_zone=z["name"]), vcp_zone.enge(df, innen)
        return z, e

    if scan is None:
        z_ = vcp_zone.zone(df)
        scan = (z_, vcp_zone.enge(df, z_))
    z, e = _waehle(*scan)
    if br and not br["innen"] and not _reif(br["zone"]):
        # Ausbruch über eine Zone, die für Minervini keine Base ist (z. B. über 50 % tief): gesucht wird der Ausbruch über
        # die Base, mit der er rechnet – sonst sprechen Text und Abstand von zwei Pivots (NIQ, 12.11.2026)
        br = vcp_zone.ausbruch(df, jetzt=scan[0] if scan else None, passt=_reif)
    if br:                                          # Ausbruch (bis 4 Wochen, auch Fehlausbruch): die Zone vom Vortag gilt –
        bz, be = (dict(br["zone"], in_zone=br["eltern"]), br["enge"]) if br["innen"] else _waehle(br["zone"], br["enge"])
        if _reif(bz) or not _reif(z):               # außer sie ist keine Base, die Zone von heute aber schon
            z, e = bz, be
        else:
            br = None
    art = z.get("name") if z.get("zone") else None
    reif = bool(_reif(z))
    eng = e.get("ampel", "grau") if reif else "grau"
    z_ok, z_txt = _zahlen(fund)
    n_kontr = len(e.get("kontraktionen") or []) if reif else 0
    if reif:
        zone_txt = (f"{art} {z['wochen']:.1f} Wochen, {z['tiefe']:.0f} % tief".replace(".", ",")
                    + (f" (in einer {z['in_zone']})" if z.get("in_zone") else ""))
    elif z.get("offen"):
        zone_txt = "Rücksetzer läuft – Zone noch offen"
    elif not z.get("zone"):
        zone_txt = z.get("grund", "keine Zone")
    elif art == "Konsolidierung":
        zone_txt = "Konsolidierung nach einem Absturz, keine Base"
    else:
        zone_txt = f"{art} zu kurz/zu lang" if z.get("laenge") != "ok" else f"{art} über 50 % tief"
    regeln = [("Trendvorlage (7 Punkte)", bool(tv) and all(tv.values()),
               f"{sum(tv.values())} von 7" + ("" if not tv or all(tv.values()) else
                                               " – fehlt: " + ", ".join(n for n, ok in tv.items() if not ok))
               if tv else "zu kurze Historie"),
              ("RS ab 70 (8. Punkt)", rs_rang is not None and rs_rang >= RS_MIN,
               f"RS {rs_rang} von 99" if rs_rang is not None else "kein RS-Rang"),
              ("Zahlen wachsen", z_ok, z_txt),
              ("Reife Base (Scanner)", reif, zone_txt),
              ("Enge (VCP)", eng in ("grün", "gelb") and n_kontr >= 2,
               (("" if eng == "grün" else "teilweise · " if eng == "gelb" else "nicht eng · ") + e.get("text", "")
                + ("" if n_kontr >= 2 or eng not in ("grün", "gelb") else " – erst eine Kontraktion"))
               if reif else "ohne reife Base nicht prüfbar")]
    fehlt = sum(1 for _, ok, _ in regeln if not ok)
    ampel = "grün" if fehlt == 0 else "gelb" if fehlt == 1 else "rot"
    pivot = float(e.get("pivot") or z["oben"]) if reif else None
    stopp, lage = None, ""
    if pivot:
        kontr = e.get("kontraktionen") or []
        unten = min(float(kontr[-1]["tief"]), pivot) if kontr else pivot * (1 - MAX_STOPP)
        stopp = max(unten, pivot * (1 - MAX_STOPP))
        ab = (c[-1] / pivot - 1) * 100
        lage = ("in der Kaufzone" if 0 <= ab <= KAUFZONE else f"{ab:.1f} % über dem Pivot, ausgedehnt" if ab > KAUFZONE
                else f"{-ab:.1f} % unter dem Pivot").replace(".", ",")
        if br:                                     # das Zeichen sagt die Lage schon (Kaufzone/ausgedehnt)
            lage = vcp_zone.ausbruch_text(br)
    setup = f"{art} {z['wochen']:.0f} W." if reif else "keines"
    return {"system": "M", "ampel": ampel, "setup": setup, "regeln": regeln, "fehlt": fehlt,
            "pivot": pivot, "stopp": stopp, "lage": lage, "trendvorlage": tv, "zone": z, "enge": e, "ausbruch": br,
            "abstand": (c[-1] / pivot - 1) * 100 if pivot else None,
            "ausstieg": ("Stopp unter dem Tief der letzten Kontraktion, höchstens 8 % unter dem Pivot. Stopp auf Einstand, "
                         "sobald der Gewinn ein Mehrfaches des Risikos erreicht; in die Stärke teilweise verkaufen, den "
                         "Rest mit nachgezogenem Stopp laufen lassen (Minervini).")}


def kurz(m):
    """Eine Zeile für Karte und Hinweis: was fehlt."""
    fehlt = [n for n, ok, _ in m["regeln"] if not ok]
    return "alle Regeln erfüllt" if not fehlt else "fehlt: " + ", ".join(fehlt)
