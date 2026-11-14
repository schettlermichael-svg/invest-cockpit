"""Mängelliste (Micky 14.11.2026): jeder Befund aus den Auswertungen von Chart- und Setup-Prüfer mit seinem Stand –
offen, behoben (mit Commit bzw. Messung) oder entschieden (mit Mickys Entscheidung). Damit geht zwischen zwei Chats
nichts verloren, und der nächste Prüflauf zeigt, ob ein behobener Befund wirklich verschwunden ist (Verlauf: Widersprüche
je Chart und Element über alle Läufe).

Die Befunde kommen von selbst aus jeder Auswertung (aus_berichten liest alle Berichte mit Auswertung, die noch nicht
übernommen sind). Den Stand setzt man auf der Seite Setups. Gespeichert in daten/maengel.json (Server)."""
import os
from datetime import datetime

from dateien import json_lesen, json_schreiben

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "daten", "maengel.json")
STAENDE = ["offen", "behoben", "entschieden"]
QUELLEN = {"chart": ("🔎 Chart-Prüfer", "chartpruefer"), "setup": ("🎯 Setup-Prüfer", "setuppruefer")}


def laden():
    return json_lesen(DATEI, None) or {"befunde": [], "uebernommen": []}


def _berichte(modul):
    """Alle Berichte eines Prüfers: [(Pfad, Bericht)], älteste zuerst."""
    ordner = modul.ORDNER
    if not os.path.isdir(ordner):
        return []
    aus = []
    for f in sorted(f for f in os.listdir(ordner) if f.startswith("bericht_")):
        b = json_lesen(os.path.join(ordner, f), None)
        if b and b.get("titel"):
            aus.append((f, b))
    return aus


def aus_berichten():
    """Übernimmt die Befunde jeder Auswertung, die noch nicht in der Liste steht. → Zahl der neuen Befunde."""
    import importlib
    m = laden()
    neu = 0
    for q, (_, modname) in QUELLEN.items():
        try:
            modul = importlib.import_module(modname)
        except Exception:  # noqa: BLE001
            continue
        for f, b in _berichte(modul):
            a = b.get("auswertung")
            schluessel = f"{q}:{f}"
            if not a or schluessel in m["uebernommen"]:
                continue
            for i, x in enumerate(a.get("befunde") or []):
                m["befunde"].append({
                    "id": f"{q}-{b['stand'].replace('-', '').replace(' ', '-').replace(':', '')}-{i + 1}",
                    "quelle": q, "lauf": b["stand"], "charts": len(b["titel"]),
                    "titel": x.get("titel", ""), "element": x.get("element", ""), "art": x.get("art", ""),
                    "anzahl": x.get("anzahl", 0), "sicher": x.get("sicher", 0), "beispiele": x.get("beispiele", [])[:5],
                    "deutung": x.get("deutung", ""), "vorschlag": x.get("vorschlag", ""),
                    "stand": "offen", "notiz": "", "geaendert": None})
                neu += 1
            m["uebernommen"].append(schluessel)
    if neu:
        json_schreiben(DATEI, m, ensure_ascii=False)
    return neu


def setzen(bid, stand, notiz):
    """Stand und Notiz eines Befunds setzen (Notiz: Commit und Messung bei „behoben“, Mickys Entscheidung bei
    „entschieden“)."""
    m = laden()
    for x in m["befunde"]:
        if x["id"] == bid:
            x.update(stand=stand, notiz=notiz.strip(), geaendert=f"{datetime.now():%d.%m.%Y %H:%M}")
            json_schreiben(DATEI, m, ensure_ascii=False)
            return True
    return False


def verlauf(q):
    """Widersprüche je Chart und Element über alle Läufe eines Prüfers → (Läufe [(Stand, Charts)],
    {Element: [(je Chart, sicher je Chart) oder None je Lauf]}). Ein behobener Befund muss hier sinken."""
    import importlib
    modul = importlib.import_module(QUELLEN[q][1])
    laeufe, tafel = [], {}
    berichte = _berichte(modul)
    for k, (_, b) in enumerate(berichte):
        n = len(b["titel"])
        laeufe.append((b["stand"], n))
        for r in b["titel"]:
            for w in r.get("widersprueche") or []:
                z = tafel.setdefault(w["element"], [[0, 0] for _ in berichte])
                z[k][0] += 1
                z[k][1] += w.get("gewicht") == "sicher"
    aus = {e: [(a / laeufe[k][1], s / laeufe[k][1]) if laeufe[k][1] else None for k, (a, s) in enumerate(z)]
           for e, z in tafel.items()}
    return laeufe, aus
