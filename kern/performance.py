"""Performance des Kontos Woche für Woche (16.11.2026, ersetzt Mickys Excel-Liste „Trading Performance Tracker“).

Speicher: einstellungen/performance.json (nur auf Mac bzw. Server, nicht in GitHub)
  {"start": Startkapital €, "start_datum": "JJJJ-MM-TT", "ziel_woche": Zielrendite je Woche (0,20 = 20 %),
   "wochen": [{"datum": Freitag "JJJJ-MM-TT", "wert": Depotwert €, "einzahlung": Ein- (+) bzw. Auszahlung (−) €}]}

Rechnung:
  Wochenrendite   (Depotwert − Depotwert der Vorwoche − Einzahlung) / Depotwert der Vorwoche – Einzahlungen sind keine
                  Rendite (in der Excel-Liste fehlten sie)
  Ø Wochenrendite geometrisch über alle eingetragenen Wochen (aus den echten Wochen, nicht von Hand)
  Hochrechnung    ein Jahr (52 Wochen) mit der Ø Wochenrendite: (1 + Ø)^52 − 1, und der Depotwert nach 52 Wochen ab
                  dem Start; dasselbe mit der Rendite der letzten Woche
  Zielpfad        Start × (1 + Ziel)^Woche
  Unterwasser     Abstand des Depotwerts (ohne Einzahlungen, als Index) zu seinem bisherigen Hoch; ab 10 % rot wie die
                  Verlustbremse (depot.VERLUSTBREMSE, Minervini)
"""
import os

from dateien import json_lesen, json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "einstellungen", "performance.json")
WOCHEN_JAHR = 52


def laden():
    d = json_lesen(DATEI, None) if os.path.exists(DATEI) else None
    d = d or {}
    d.setdefault("start", None)
    d.setdefault("start_datum", None)
    d.setdefault("ziel_woche", None)
    d.setdefault("wochen", [])
    d["wochen"] = sorted(d["wochen"], key=lambda w: w["datum"])
    return d


def speichern(d):
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    d["wochen"] = sorted(d["wochen"], key=lambda w: w["datum"])
    json_schreiben(DATEI, d, ensure_ascii=False, indent=1)


def woche_setzen(datum, wert, einzahlung=0.0):
    d = laden()
    d["wochen"] = [w for w in d["wochen"] if w["datum"] != datum] + [
        {"datum": datum, "wert": float(wert), "einzahlung": float(einzahlung or 0)}]
    speichern(d)


def woche_loeschen(datum):
    d = laden()
    d["wochen"] = [w for w in d["wochen"] if w["datum"] != datum]
    speichern(d)


def rechnen(d=None):
    """→ {wochen: [{nr, datum, wert, einzahlung, rendite, index, unterwasser, ziel}], schnitt, letzte, jahr_schnitt,
    jahr_letzte, wert_jahr_schnitt, wert_jahr_letzte, ziel_jahr, unterwasser, tiefster} oder None."""
    d = d or laden()
    if not d.get("start"):
        return None
    vor, index, hoch = float(d["start"]), 1.0, 1.0
    zeilen = []
    for nr, w in enumerate(d["wochen"], 1):
        r = (w["wert"] - vor - w.get("einzahlung", 0)) / vor if vor else 0.0
        index *= 1 + r
        hoch = max(hoch, index)
        zeilen.append({"nr": nr, "datum": w["datum"], "wert": w["wert"], "einzahlung": w.get("einzahlung", 0),
                       "rendite": r, "index": index, "unterwasser": (1 - index / hoch) * 100,
                       "ziel": float(d["start"]) * (1 + (d.get("ziel_woche") or 0)) ** nr})
        vor = w["wert"]
    aus = {"wochen": zeilen, "schnitt": None, "letzte": None}
    if zeilen:
        aus["schnitt"] = index ** (1 / len(zeilen)) - 1
        aus["letzte"] = zeilen[-1]["rendite"]
        aus["unterwasser"] = zeilen[-1]["unterwasser"]
        aus["tiefster"] = max(z["unterwasser"] for z in zeilen)
        for name, r in (("schnitt", aus["schnitt"]), ("letzte", aus["letzte"])):
            aus[f"jahr_{name}"] = (1 + r) ** WOCHEN_JAHR - 1
            rest = max(0, WOCHEN_JAHR - len(zeilen))
            aus[f"wert_jahr_{name}"] = zeilen[-1]["wert"] * (1 + r) ** rest   # nach 52 Wochen ab dem Start
    if d.get("ziel_woche") is not None:
        aus["ziel_jahr"] = (1 + d["ziel_woche"]) ** WOCHEN_JAHR - 1
        aus["ziel_wert_jahr"] = float(d["start"]) * (1 + d["ziel_woche"]) ** WOCHEN_JAHR
    return aus
