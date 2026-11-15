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
VORGABE_STEMPEL = "Vorgabe"
VORGABEN = [
    ("chart", "2026-11-14 09:40", "Absturz oder Abwärtstrend", "behoben",
     "4857c58: über 50 % tief ist keine Base; bb6e3d1: Base über 33 % wird nie grün. Lauf 3: Zone: Unterkante 0,04 je Chart (Lauf 1: 0,30)"),
    ("chart", "2026-11-14 09:40", "Mini-Zonen", "behoben",
     "bb6e3d1: zu kurze Zone = im Aufbau, kein Pivot, Ampel grau. Lauf 3: Zone: Name 0,17 je Chart (Lauf 1: 0,36)"),
    ("chart", "2026-11-14 09:40", "Zonenbeginn verfehlt", "entschieden",
     "Micky 14.11.: Schluss entscheidet – ein Docht über der Oberkante ist ein abgelehnter Vorstoß"),
    ("chart", "2026-11-14 09:40", "Kontraktionen aus Absturz", "behoben",
     "bb6e3d1 und 4910faf: rechte Seite der Reihe nach, Kontraktion ab 3 Tagen, höchstens 6 Wellen, Volumen ausgetrocknet, "
     "nicht in Phase 4 – gemessen grün 94 → 44; im nächsten Lauf prüfen"),
    ("chart", "2026-11-14 09:40", "Pivot aus 1–3-Tage-Hoch", "offen",
     "bb6e3d1: zu kurze Zone ohne Pivot – Lauf 3 meldet weiter veraltete Pivots"),
    ("chart", "2026-11-14 09:40", "Anker Hoch des Rückgangs", "behoben",
     "4910faf: höchstes nicht überschrittenes Hoch der letzten 2 Jahre – eigener Anker bei 1.434 statt 1.053 Titeln"),
    ("chart", "2026-11-14 09:40", "Anker letztes Hoch", "offen",
     "048ab72: 8-%-Regel (Micky) – Lauf 3 meldet überschrittene oder unbestätigte Hochs"),
    ("chart", "2026-11-14 09:40", "Anker Tief der Bewegung", "behoben",
     "048ab72: nur das Trendstart-Tief (Micky); Lauf 3: 0,17 je Chart (Lauf 1: 0,26), nur 4 sicher"),
    ("chart", "2026-11-14 09:40", "festen Montagen", "behoben",
     "048ab72: Profil ab überlappenden Tagen (Dalton, Micky); Lauf 3: 4 sicher (Lauf 1: 10)"),
    ("chart", "2026-11-14 09:40", "Ereignis-Anker fehlt", "behoben",
     "048ab72: Lücken und Volumenspitzen (Micky); Ereignis jetzt an jedem jüngsten Zahlentag – Anker bei 1.342 statt 1.255 "
     "von 1.343 Titeln mit Zahlen"),
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
    ("chart", "2026-11-14 18:18", "Hoch des Rückgangs fällt", "behoben",
     "4910faf: höchstes nicht überschrittenes Hoch der letzten 2 Jahre – eigener Anker bei 1.434 statt 1.053 Titeln"),
    ("chart", "2026-11-14 18:18", "Abwärtstrend und Ein-Tages", "behoben",
     "4910faf: Kontraktion ab 3 Tagen, höchstens 6 Wellen, Volumen ausgetrocknet, nicht in Phase 4 – grün 94 → 44"),
    ("chart", "2026-11-14 18:18", "Phase nach Weinstein", "offen",
     "30-Wochen-Linie ausprobiert (35 % der Titel wechseln, Beispiele teils besser, teils schlechter) – Micky 14.11.: "
     "Schritt 8 der Gefechtsordnung (Phasen als Rahmen)"),
    ("chart", "2026-11-14 18:18", "Ereignis", "behoben",
     "Micky 14.11.: Ereignis-Anker an jedem jüngsten Zahlentag (Shannon), die 3 % gelten nur fürs Setup Zahlen-Reaktion – "
     "269 von 1.343 Titeln mit Zahlen ankern anders"),
    ("chart", "2026-11-14 18:18", "Flagge", "behoben",
     "Micky 14.11.: grün nur mit steigenden Tiefs (Tief der zweiten Hälfte höchstens 0,5 ATR unter dem der ersten) – "
     "Flaggen im Trend 44 → 26 von 108"),
    ("chart", "2026-11-14 18:18", "Abfluss unter 1", "behoben",
     "Beleg heißt bei einem Wert unter 1 jetzt „Abfluss“ statt „Zufluss“ (auktion.gruppe)"),
    ("chart", "2026-11-14 18:18", "Ausbruch ohne Volumen", "entschieden",
     "Micky (06.11.): Volumen ist Zeichen, keine Pflicht; über dem 50-Tage-Schnitt reicht (O'Neils 1,4-fach zu streng)"),
    # Lauf 4 (15.11.2026 11:37) – klare Fehler behoben, gemessen über 1.865 Titel (Mac-Daten bis 04.11.)
    ("chart", "2026-11-15 11:37", "Test am Rand ohne 3-%-Regel", "behoben",
     "Market Profile „an der Schwelle“ und Exzess nur bis 3 % vom Rand als Test am Rand, Exzess vor Beginn der Zone fällt "
     "weg – Titel mit Beleg „Test am Rand“ 1.195 → 740, Zustand Test am Rand 220 → 177"),
    ("chart", "2026-11-15 11:37", "Wert gewandert", "behoben",
     "Market Profile Wert gewandert/Fortsetzung innerhalb der Zone = innere Rotation (Balance) – als Ungleichgewicht "
     "785 → 284 Titel (der Rest steht über bzw. unter der Zone)"),
    ("chart", "2026-11-15 11:37", "Upthrust/Spring", "behoben",
     "aufgehoben, wenn danach ein Schluss über dem Hoch des Upthrust- bzw. unter dem Tief des Spring-Tags kommt – auch "
     "aus Anlass und Waage – bei 72 Titeln; abgelehnt 365 → 280"),
    ("chart", "2026-11-15 11:37", "Eigen/geliehen", "behoben",
     "RS in Laufrichtung: eigen ab 5 %, geliehen ±1 %, teils eigen 1–5 %, gegen die Laufrichtung = Gegenzeichen – "
     "„mit dem Markt“ 494 → 0 (teils eigen 177, Gegenzeichen 232)"),
    ("chart", "2026-11-15 11:37", "Waage", "behoben",
     "alle Zeichen gewogen (auch RS und Ereignis), Seiten getrennt aufgeführt, Gleichstand kein Beleg (152 → 0), "
     "aufgehobene Springs/Upthrusts zählen nicht"),
    ("chart", "2026-11-15 11:37", "AVWAP letztes Hoch", "behoben",
     "nur fertige Wochen bestätigen ein Schwunghoch; steht der Kurs über allen Hochs, heißt der Anker sichtbar "
     "Ausbruchspunkt (172 Titel) – letztes Hoch bei 194 Titeln anders"),
    ("chart", "2026-11-15 11:37", "Quad-Führer", "behoben", "Anzeige im Material des Prüfers (Text statt Buchstaben)"),
    ("chart", "2026-11-15 11:37", "Phase nach Weinstein", "offen", "Micky 14.11.: Schritt 8 der Gefechtsordnung"),
    ("chart", "2026-11-15 11:37", "Kette erkennt Ausbruch", "offen", "Gefechtsordnung (Regelkarte, Schritte 2–5)"),
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
    for x in m["befunde"]:                         # Vorgaben gelten, solange niemand den Befund selbst gesetzt hat
        if (x["stand"] == "offen" and not x.get("notiz")) or x.get("geaendert") == VORGABE_STEMPEL:
            for vq, vl, stueck, vs, vn in VORGABEN:
                if (vq == x["quelle"] and vl == x["lauf"] and stueck in x.get("titel", "")
                        and (x["stand"], x.get("notiz")) != (vs, vn)):
                    x.update(stand=vs, notiz=vn, geaendert=VORGABE_STEMPEL)
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
                        m["befunde"][-1].update(stand=vs, notiz=vn, geaendert=VORGABE_STEMPEL)
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
