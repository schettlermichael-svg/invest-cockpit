"""Marktklima: die eine Markt-Ampel der App (Micky 12.11.2026: „Minervini war für das Marktklima gar kein Experte“).

Es urteilt O'Neil, das „M“ in CAN SLIM (marktrichtung.py): Distributionstage, Erholungsversuch, Follow-Through-Day.
  grün  Bestätigter Aufwärtstrend   nach einem Follow-Through-Day, höchstens 3 Distributionstage
  gelb  Aufwärtstrend unter Druck   4 Distributionstage in einem Index
  rot   Korrektur                   5 Distributionstage und Bruch der Wertzone bzw. des Tiefs vor dem Follow-Through-Day
(Einzelheiten und die Ergänzung zur Buchregel stehen in marktrichtung.py.)

Darunter als Zeichen, ohne Urteil: S&P 500 und Nasdaq gegen GD50 und GD200 sowie neue 52-Wochen-Hochs gegen Tiefs
(Barometer des Kartentischs). Vorher (bis 12.11.2026) war das die Ampel – eine eigene Faustregel der App, die das
Etikett „Minervini“ trug; davor (05.11.) zusätzlich Kullamägis 10/20-Tage-Regel.
"""
import marktdaten as md
import marktrichtung

INDIZES = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC"}
WORT = {"grün": "Aufwärtstrend bestätigt", "gelb": "Aufwärtstrend unter Druck", "rot": "Korrektur"}
REGEL = ("O'Neil (CAN SLIM, „M“): Bestätigter Aufwärtstrend nach einem Follow-Through-Day mit höchstens 3 "
         "Distributionstagen in 5 Wochen = grün; 4 Distributionstage in einem Index = gelb (unter Druck); 5 "
         "Distributionstage und Bruch der Wertzone oder des Tiefs vor dem Follow-Through-Day = rot (Korrektur). Eine "
         "Korrektur endet mit einem Follow-Through-Day ab Tag 4 des Erholungsversuchs.")


def zeichen(hochs=None, tiefs=None):
    """Zeichenzeile ohne Urteil: Indizes gegen GD50/GD200 und neue Hochs gegen Tiefs."""
    teile = []
    for name, tk in INDIZES.items():
        c = md.yahoo_ohlc(tk)["Close"].to_numpy(float)
        k, g50, g200 = float(c[-1]), float(c[-50:].mean()), float(c[-200:].mean())
        teile.append(f'{name}: {"über" if k > g50 else "unter"} GD50, {"über" if k > g200 else "unter"} GD200')
    if hochs is not None and tiefs is not None:
        teile.append(f"neue Hochs : Tiefs {hochs} : {tiefs}")
    return " · ".join(teile)


def markt(hochs=None, tiefs=None):
    """→ {ampel, wort, seit, text (O'Neil), zeichen (Indizes, Hochs/Tiefs), regel} oder Ausnahme ohne Daten."""
    mr = marktrichtung.richtung()
    try:
        z = zeichen(hochs, tiefs)
    except Exception:  # noqa: BLE001 – die Ampel steht auch ohne Zeichenzeile
        z = ""
    return {"ampel": mr["ampel"], "wort": WORT[mr["ampel"]], "zustand": mr["zustand"],
            "seit": f'{mr["seit"]:%d.%m.%Y}', "text": mr["text"], "zeichen": z, "regel": REGEL}
