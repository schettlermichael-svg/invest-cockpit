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
# Stand der Befunde, die vor der Mängelliste bearbeitet wurden (14.11.2026) – wird beim Übernehmen gesetzt, solange der
# Befund noch keinen eigenen Stand hat: (Quelle, Lauf, Stück des Titels, Stand, Notiz)
VORGABEN = [
    ("chart", "2026-11-14 09:40", "Absturz oder Abwärtstrend", "behoben",
     "4857c58: über 50 % tief ist keine Base; bb6e3d1: Base über 33 % wird nie grün. Lauf 3: Zone: Unterkante 0,04 je Chart (Lauf 1: 0,30)"),
    ("chart", "2026-11-14 09:40", "Mini-Zonen", "behoben",
     "bb6e3d1: zu kurze Zone = im Aufbau, kein Pivot, Ampel grau. Lauf 3: Zone: Name 0,17 je Chart (Lauf 1: 0,36)"),
    ("chart", "2026-11-14 09:40", "Zonenbeginn verfehlt", "entschieden",
     "Micky 14.11.: Schluss entscheidet – ein Docht über der Oberkante ist ein abgelehnter Vorstoß"),
    ("chart", "2026-11-14 09:40", "Kontraktionen aus Absturz", "offen",
     "bb6e3d1: rechte Seite der Reihe nach – Lauf 3 meldet weiter Abwärtstrend und 1-Tages-Rücksetzer: nachschärfen"),
    ("chart", "2026-11-14 09:40", "Pivot aus 1–3-Tage-Hoch", "offen",
     "bb6e3d1: zu kurze Zone ohne Pivot – Lauf 3 meldet weiter veraltete Pivots"),
    ("chart", "2026-11-14 09:40", "Anker Hoch des Rückgangs", "offen",
     "048ab72: Hoch ab 8 % Rückgang – Lauf 3: Hoch des Rückgangs fällt meist mit letztem Hoch zusammen"),
    ("chart", "2026-11-14 09:40", "Anker letztes Hoch", "offen",
     "048ab72: 8-%-Regel (Micky) – Lauf 3 meldet überschrittene oder unbestätigte Hochs"),
    ("chart", "2026-11-14 09:40", "Anker Tief der Bewegung", "behoben",
     "048ab72: nur das Trendstart-Tief (Micky); Lauf 3: 0,17 je Chart (Lauf 1: 0,26), nur 4 sicher"),
    ("chart", "2026-11-14 09:40", "festen Montagen", "behoben",
     "048ab72: Profil ab überlappenden Tagen (Dalton, Micky); Lauf 3: 4 sicher (Lauf 1: 10)"),
    ("chart", "2026-11-14 09:40", "Ereignis-Anker fehlt", "offen",
     "048ab72: Lücken und Volumenspitzen (Micky) – Lauf 3: Anker nicht am jüngsten Zahlentag"),
    ("chart", "2026-11-14 09:40", "Schub der Vorgeschichte", "behoben",
     "e02bc42: Vorgeschichte und Fahnenstange im Material getrennt, mit Zeitraum"),
    ("chart", "2026-11-14 09:40", "Ausgebrochene Base", "behoben",
     "e02bc42: am Hoch zeigt das Material die zuletzt verlassene Zone mit Pivot und Abstand"),
    ("chart", "2026-11-14 09:40", "Einquetschung", "behoben",
     "a9a7487: flache Kante seit mindestens 3 Wochen, 60 und 120 Tage – 48 → 27 Titel"),
    ("chart", "2026-11-14 09:40", "wenigen Cent", "entschieden",
     "Micky 14.11.: Schlusskurs unter der Mitte, nicht Tagestief (a9a7487, 38 Zonen geändert)"),
    ("chart", "2026-11-14 09:40", "Henkel und Cheat", "offen", "Drittel nur in gültigen Basen – noch prüfen"),
    ("chart", "2026-11-14 09:40", "Übernahmefall", "behoben",
     "Regel seit 12.11.: Kurs steht still (Tagesspanne unter 0,5 %) – nicht grün, Hinweis „Übernahme?“"),
    ("chart", "2026-11-14 18:18", "Ausbruch ohne Volumen", "entschieden",
     "Micky (06.11.): Volumen ist Zeichen, keine Pflicht; über dem 50-Tage-Schnitt reicht (O'Neils 1,4-fach zu streng)"),
]
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
    """Übernimmt die Befunde jeder Auswertung, die noch nicht in der Liste steht. → Zahl der neuen Befunde.
    Befunde ohne eigenen Stand (offen, ohne Notiz) bekommen die VORGABEN."""
    import importlib
    m = laden()
    neu = 0
    for x in m["befunde"]:
        if x["stand"] == "offen" and not x.get("notiz"):
            for vq, vl, stueck, vs, vn in VORGABEN:
                if vq == x["quelle"] and vl == x["lauf"] and stueck in x.get("titel", ""):
                    x.update(stand=vs, notiz=vn, geaendert="14.11.2026")
                    neu += 1
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
                for vq, vl, stueck, vs, vn in VORGABEN:
                    if vq == q and vl == b["stand"] and stueck in x.get("titel", ""):
                        m["befunde"][-1].update(stand=vs, notiz=vn, geaendert="14.11.2026")
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
