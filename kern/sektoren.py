"""Sektoren und Rotation (Konzept: Frontkarte, RRG-Näherung).

Elf Sektor-ETFs gegen den S&P 500 (SPY), Wochenschlüsse:
  RS        = ETF / SPY
  RS-Stärke = 100 · RS / Schnitt der RS über 26 Wochen, über 4 Wochen geglättet
              (über 100 = stärker als der Markt im letzten halben Jahr)
  Schwung   = 100 + Veränderung der RS-Stärke in 6 Wochen   (über 100 = Stärke nimmt zu)
Gewählt nach der Abnahme (werkzeuge/sektoren_test.py): mit 10 statt 26 Wochen trennt die Stärke
Führer und Abgehängte schlechter (Energie 2022 nur 77 % der Wochen stark statt 98 %), ohne Glättung
wechselt jeder Sektor rund 16-mal im Jahr das Feld statt rund 8-mal.
Felder: Führend (stark, Schwung +), Ermüdend (stark, Schwung −), Abgehängt (schwach, Schwung −),
Erstarkend (schwach, Schwung +). Schweif = die letzten 10 Wochen.
Die echten RRG-Werte von de Kempenaer sind nicht offengelegt; das hier ist eine Näherung.
"""
import pandas as pd

import marktdaten

MARKT = "SPY"
SEKTOREN = {"XLK": "Technologie", "XLC": "Kommunikation", "XLY": "Zyklischer Konsum",
            "XLF": "Finanzen", "XLI": "Industrie", "XLB": "Grundstoffe", "XLE": "Energie",
            "XLV": "Gesundheit", "XLP": "Basiskonsum", "XLU": "Versorger", "XLRE": "Immobilien"}
# Yahoo-Sektornamen → ETF
YAHOO = {"Technology": "XLK", "Communication Services": "XLC", "Consumer Cyclical": "XLY",
         "Financial Services": "XLF", "Industrials": "XLI", "Basic Materials": "XLB", "Energy": "XLE",
         "Healthcare": "XLV", "Consumer Defensive": "XLP", "Utilities": "XLU", "Real Estate": "XLRE"}
# typische Führer je Quad (Konzept, Abschnitt Quadrant) als ETFs
QUAD_ETFS = {1: ["XLK", "XLY", "XLC"], 2: ["XLE", "XLB", "XLI", "XLF"],
             3: ["XLE", "XLU"], 4: ["XLU", "XLP", "XLV"]}
FELDER = {"Führend": "grün", "Ermüdend": "gelb", "Abgehängt": "rot", "Erstarkend": "blau"}
VERLAUF = 26                                   # so weit zurück wird „seit … Wochen“ gezählt
SCHWEIF = 11                                   # heute und die 10 Wochen davor


def feld(staerke, schwung):
    if staerke >= 100:
        return "Führend" if schwung >= 100 else "Ermüdend"
    return "Erstarkend" if schwung >= 100 else "Abgehängt"


def reihen(etf, markt=None):
    """Wöchentliche RS-Stärke und Schwung eines ETFs (oder einer Kursreihe) gegen den Markt."""
    markt = marktdaten.yahoo(MARKT) if markt is None else markt
    kurs = marktdaten.yahoo(etf) if isinstance(etf, str) else etf
    rs = (kurs / markt.reindex(kurs.index, method="ffill")).resample("W-FRI").last().dropna()
    staerke = (100 * rs / rs.rolling(26).mean()).ewm(span=4).mean()
    schwung = 100 + staerke.diff(6)
    return pd.DataFrame({"staerke": staerke, "schwung": schwung}).dropna()


def rotation(bis=None):
    """Je Sektor: Feld heute, Feld vor einer Woche, seit wie vielen Wochen im Feld und das Feld davor,
    Schweif der letzten 10 Wochen."""
    markt = marktdaten.yahoo(MARKT)
    aus = {}
    for etf, name in SEKTOREN.items():
        r = reihen(etf, markt)
        if bis is not None:
            r = r[r.index <= pd.Timestamp(bis)]
        if len(r) < SCHWEIF + 1:
            continue
        s = r.iloc[-SCHWEIF:]
        heute, vorher = s.iloc[-1], s.iloc[-2]
        verlauf = [feld(a, b) for a, b in zip(r["staerke"].iloc[-VERLAUF:], r["schwung"].iloc[-VERLAUF:])]
        seit = next((i for i, f in enumerate(reversed(verlauf)) if f != verlauf[-1]), len(verlauf))
        davor = verlauf[-seit - 1] if seit < len(verlauf) else None
        aus[etf] = {"name": name, "stand": s.index[-1],
                    "staerke": float(heute["staerke"]), "schwung": float(heute["schwung"]),
                    "feld": feld(heute["staerke"], heute["schwung"]),
                    "feld_vorher": feld(vorher["staerke"], vorher["schwung"]),
                    "seit_wochen": seit, "davor": davor,
                    "schweif": list(zip(s["staerke"].round(2), s["schwung"].round(2)))}
    return aus


def stark_anteil(etf, jahr):
    """Anteil der Wochen eines Jahres, in denen der Sektor stärker als der Markt war (Prozent)."""
    r = reihen(etf)["staerke"][str(jahr)]
    return float((r > 100).mean() * 100)


def abgleich(rot, quad):
    """Stehen die typischen Führer des Quads tatsächlich im Feld Führend/Erstarkend?"""
    erwartet = QUAD_ETFS[quad]
    vorne = [e for e in erwartet if e in rot and rot[e]["feld"] in ("Führend", "Erstarkend")]
    ampel = "grün" if len(vorne) * 2 > len(erwartet) else "gelb" if vorne else "rot"
    return {"ampel": ampel, "vorne": vorne, "erwartet": erwartet}


def sektor_von(yahoo_sektor):
    return YAHOO.get(yahoo_sektor)
