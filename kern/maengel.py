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
    ("chart", "2026-11-14 09:40", "Anker letztes Hoch", "behoben",
     "048ab72: 8-%-Regel (Micky); af0614d: nur fertige Wochen bestätigen, Kurs über allen Hochs = Ausbruchspunkt – "
     "172 Ausbruchspunkte, 194 Anker anders"),
    ("chart", "2026-11-14 09:40", "Anker Tief der Bewegung", "behoben",
     "048ab72: nur das Trendstart-Tief (Micky); Lauf 3: 0,17 je Chart (Lauf 1: 0,26), nur 4 sicher"),
    ("chart", "2026-11-14 09:40", "festen Montagen", "behoben",
     "048ab72: Profil ab überlappenden Tagen (Dalton, Micky); Lauf 3: 4 sicher (Lauf 1: 10)"),
    ("chart", "2026-11-14 09:40", "Ereignis-Anker fehlt", "behoben",
     "048ab72: Lücken und Volumenspitzen (Micky); Ereignis jetzt an jedem jüngsten Zahlentag – Anker bei 1.342 statt 1.255 "
     "von 1.343 Titeln mit Zahlen"),
    ("chart", "2026-11-14 09:40", "Schub der Vorgeschichte", "behoben",
     "e02bc42: Vorgeschichte und Fahnenstange im Material getrennt, mit Zeitraum – Anzeige (Material des Prüfers)"),
    ("chart", "2026-11-14 09:40", "Ausgebrochene Base", "behoben",
     "e02bc42: am Hoch zeigt das Material die zuletzt verlassene Zone mit Pivot und Abstand – Anzeige (Material des Prüfers)"),
    ("chart", "2026-11-14 09:40", "Einquetschung", "behoben",
     "9afb297: flache Kante seit mindestens 3 Wochen, 60 und 120 Tage – 48 → 27 Titel"),
    ("chart", "2026-11-14 09:40", "wenigen Cent", "entschieden",
     "Micky 14.11.: Schlusskurs unter der Mitte, nicht Tagestief (a9a7487, 38 Zonen geändert)"),
    ("chart", "2026-11-14 09:40", "Henkel und Cheat", "offen", "Drittel nur in gültigen Basen – noch prüfen"),
    ("chart", "2026-11-14 09:40", "Übernahmefall", "behoben",
     "d5298fd (12.11.): Kurs steht still (Tagesspanne unter 0,5 %) – nicht grün, Hinweis „Übernahme?“"),
    ("chart", "2026-11-14 18:18", "Hoch des Rückgangs fällt", "behoben",
     "4910faf: höchstes nicht überschrittenes Hoch der letzten 2 Jahre – eigener Anker bei 1.434 statt 1.053 Titeln"),
    ("chart", "2026-11-14 18:18", "Abwärtstrend und Ein-Tages", "behoben",
     "4910faf: Kontraktion ab 3 Tagen, höchstens 6 Wellen, Volumen ausgetrocknet, nicht in Phase 4 – grün 94 → 44"),
    ("chart", "2026-11-14 18:18", "Phase nach Weinstein", "behoben",
     "9bd94f6: Schritt 8 (Micky 16.11.) – Phase 3 erst bei flacher Linie (183 → 112, 102 Titel 3 → 2), Phase 2 mit dem Ausbruch (Phase 1 über steigender Linie 23 → 3), eine Phase je Titel"),
    ("chart", "2026-11-14 18:18", "Ereignis", "behoben",
     "faa61d2: Micky 14.11.: Ereignis-Anker an jedem jüngsten Zahlentag (Shannon), die 3 % gelten nur fürs Setup Zahlen-Reaktion – "
     "269 von 1.343 Titeln mit Zahlen ankern anders"),
    ("chart", "2026-11-14 18:18", "Flagge", "behoben",
     "faa61d2: Micky 14.11.: grün nur mit steigenden Tiefs (Tief der zweiten Hälfte höchstens 0,5 ATR unter dem der ersten) – "
     "Flaggen im Trend 44 → 26 von 108"),
    ("chart", "2026-11-14 18:18", "Abfluss unter 1", "behoben",
     "f4dc05f: Beleg heißt bei einem Wert unter 1 jetzt „Abfluss“ statt „Zufluss“ (auktion.gruppe) – Anzeige"),
    ("chart", "2026-11-14 18:18", "Ausbruch ohne Volumen", "entschieden",
     "Micky (06.11.): Volumen ist Zeichen, keine Pflicht; über dem 50-Tage-Schnitt reicht (O'Neils 1,4-fach zu streng)"),
    # Lauf 4 (15.11.2026 11:37) – klare Fehler behoben, gemessen über 1.865 Titel (Mac-Daten bis 04.11.)
    ("chart", "2026-11-15 11:37", "Test am Rand ohne 3-%-Regel", "behoben",
     "af0614d: Market Profile „an der Schwelle“ und Exzess nur bis 3 % vom Rand als Test am Rand, Exzess vor Beginn der Zone fällt "
     "weg – Titel mit Beleg „Test am Rand“ 1.195 → 740, Zustand Test am Rand 220 → 177"),
    ("chart", "2026-11-15 11:37", "Wert gewandert", "behoben",
     "af0614d: Market Profile Wert gewandert/Fortsetzung innerhalb der Zone = innere Rotation (Balance) – als Ungleichgewicht "
     "785 → 284 Titel (der Rest steht über bzw. unter der Zone)"),
    ("chart", "2026-11-15 11:37", "Upthrust/Spring", "behoben",
     "af0614d: aufgehoben, wenn danach ein Schluss über dem Hoch des Upthrust- bzw. unter dem Tief des Spring-Tags kommt – auch "
     "aus Anlass und Waage – bei 72 Titeln; abgelehnt 365 → 280"),
    ("chart", "2026-11-15 11:37", "Eigen/geliehen", "behoben",
     "af0614d: RS in Laufrichtung: eigen ab 5 %, geliehen ±1 %, teils eigen 1–5 %, gegen die Laufrichtung = Gegenzeichen – "
     "„mit dem Markt“ 494 → 0 (teils eigen 177, Gegenzeichen 232)"),
    ("chart", "2026-11-15 11:37", "Waage", "behoben",
     "af0614d: alle Zeichen gewogen (auch RS und Ereignis), Seiten getrennt aufgeführt, Gleichstand kein Beleg (152 → 0), "
     "aufgehobene Springs/Upthrusts zählen nicht"),
    ("chart", "2026-11-15 11:37", "AVWAP letztes Hoch", "behoben",
     "af0614d: nur fertige Wochen bestätigen ein Schwunghoch; steht der Kurs über allen Hochs, heißt der Anker sichtbar "
     "Ausbruchspunkt (172 Titel) – letztes Hoch bei 194 Titeln anders"),
    ("chart", "2026-11-15 11:37", "Quad-Führer", "behoben", "af0614d: Anzeige im Material des Prüfers (Text statt Buchstaben)"),
    ("chart", "2026-11-15 11:37", "Flagge ohne Fahnenstange", "behoben",
     "47ea8c9: Micky 15.11.: Flagge nur mit haltenden Tiefs (sonst Base/Konsolidierung) und Stange direkt davor (nach einem "
     "Rücksetzer über 25 % beginnt sie an dessen Tief) – Titel mit Flagge 174 → 123, reife 108 → 72"),
    ("chart", "2026-11-15 11:37", "Phase nach Weinstein", "behoben",
     "9bd94f6: Schritt 8 (Micky 16.11.) – Phase 3 erst bei flacher Linie (183 → 112, 102 Titel 3 → 2), Phase 2 mit dem Ausbruch (Phase 1 über steigender Linie 23 → 3), eine Phase je Titel"),
    ("chart", "2026-11-15 11:37", "Kette erkennt Ausbruch", "behoben",
     "e2a2de5: angenommen wird ab 5 % über dem Pivot am 10er/20er Ungleichgewicht (angenommen 139 → 84, Ungleichgewicht 12 → 34, "
     "Ende 18 → 30); Zone springt auf Flagge → Plan 17"),
    # Gesamtplan 15.11.2026: jeder offene Befund ist einem Punkt des Plans zugeordnet („→ Plan N“) – der Wachposten
    # meldet jeden offenen Befund ohne Zuordnung
    ("chart", "2026-11-14 09:40", "Kontraktionen aus Absturz", "behoben",
     "bb6e3d1 und 4910faf: rechte Seite der Reihe nach, Kontraktion ab 3 Tagen, 2 bis 6 Wellen, Volumen ausgetrocknet, "
     "nicht in Phase 4 – grün 94 → 44; Lauf 4: Enge/Kontraktionen 21 Widersprüche"),
    ("chart", "2026-11-14 09:40", "Pivot aus 1–3-Tage-Hoch", "behoben",
     "4910faf: Kontraktion ab 3 Handelstagen, auch die letzte am rechten Rand – Pivot nie aus einem 1–2-Tage-Zucken"),
    ("chart", "2026-11-14 09:40", "Anker Hoch des Rückgangs", "behoben",
     "4910faf: höchstes nicht überschrittenes Hoch der letzten 2 Jahre – eigener Anker bei 1.434 statt 1.053 Titeln"),
    ("chart", "2026-11-14 09:40", "Ereignis-Anker fehlt", "behoben",
     "048ab72: Lücken und Volumenspitzen; faa61d2: jeder jüngste Zahlentag – Anker bei 1.342 statt 1.255 von 1.343 Titeln"),
    ("chart", "2026-11-14 09:40", "Henkel und Cheat", "offen", "→ Plan 9 (Drittel) und Plan 4 (Cheat-Einstieg)"),
    ("chart", "2026-11-14 18:18", "Zustand passt nicht", "behoben",
     "e2a2de5: angenommen aus dem Market Profile erst ab 2 Tagen außerhalb (37 → 21, 11 Vorstöße als Test am Rand); Cheat als "
     "innere Rotation und Exzess als Ende schon seit Lauf 4"),
    ("chart", "2026-11-14 18:18", "Belege aus alter Balance", "offen",
     "→ Plan 14: Lauf 5 prüft nach (Exzess vor der Zone und Test am Rand ohne 3-%-Regel sind seit Lauf 4 behoben)"),
    ("chart", "2026-11-14 18:18", "Letztes Hoch überschritten", "behoben",
     "af0614d: nur fertige Wochen bestätigen, Kurs über allen Hochs = Ausbruchspunkt – 172 Ausbruchspunkte, 194 Anker anders"),
    ("chart", "2026-11-14 18:18", "Phase nach Weinstein", "behoben",
     "9bd94f6: Schritt 8 (Micky 16.11.) – Phase 3 erst bei flacher Linie (183 → 112, 102 Titel 3 → 2), Phase 2 mit dem Ausbruch (Phase 1 über steigender Linie 23 → 3), eine Phase je Titel"),
    ("chart", "2026-11-14 18:18", "Eigen oder geliehen", "behoben",
     "af0614d: RS in Laufrichtung, Gegenzeichen – „mit dem Markt“ 494 → 0"),
    ("chart", "2026-11-14 18:18", "Anlass ohne Richtung", "behoben",
     "e2a2de5: Anlass nur in Laufrichtung und vor dem Ereignis – gegen die Richtung 0 von 468 (vorher 24)"),
    ("chart", "2026-11-14 18:18", "Spring und Upthrust ohne Bruch", "behoben",
     "dd133cd (Schritt 4): eine Regel – Tagesextrem jenseits des Randes, Schluss binnen 3 Tagen zurück; Spring 11, Upthrust 23"),
    ("chart", "2026-11-14 18:18", "Ende des Laufs ohne", "behoben",
     "7f19f61 (Schritt 5): Ende nur aus einem Ungleichgewicht am 10er/20er – Ende ohne Lauf 0 von 468"),
    ("chart", "2026-11-14 18:18", "Profil schließt", "offen", "→ Plan 10 (Volumenprofil der Balance)"),
    ("chart", "2026-11-14 18:18", "Zone zu tief", "behoben",
     "4abf7a9: Micky 16.11.: Pivot bleibt (Konsolidierung über 30 % ist sein Setup), Lücke „über 33 % tief“ und Minervini "
     "höchstens gelb – 62 Zonen 33–50 % tief; über 50 % keine Base seit 14.11."),
    ("chart", "2026-11-14 18:18", "Pivot veraltet", "offen", "→ Plan 9"),
    ("chart", "2026-11-14 18:18", "Chart und Zahlen", "offen", "→ Plan 17 (Bild und Zahlen gleich)"),
    ("chart", "2026-11-14 18:18", "Abstände und Gegenseite", "offen", "→ Plan 18 (Gegenseite und Abstände)"),
    ("chart", "2026-11-14 18:18", "Gruppen: Anführer", "offen", "→ Plan 11 (Gruppe)"),
    ("chart", "2026-11-14 18:18", "Dauer der Balance", "offen", "→ Plan 14: Lauf 5 prüft nach"),
    ("chart", "2026-11-14 18:18", "Ersatzregel der App", "offen", "→ Plan 19 (Prüfer irrt: Material erklären)"),
    ("chart", "2026-11-15 11:37", "Spring als", "behoben",
     "e2a2de5: Spring unter Zwang (vorher 20 unter „Verteidiger leer“), Verteidiger leer nur bei echter Enge (vorher 5 ohne)"),
    ("chart", "2026-11-15 11:37", "Anlass zeitlich", "behoben",
     "e2a2de5: Zahlen nach dem Ereignis als Beleg (vorher 12 als Anlass), Reaktion einmal (vorher 41 doppelt), Zwang nur mit "
     "gültigem Spring/Upthrust"),
    ("chart", "2026-11-15 11:37", "Volumenprofil fasst", "behoben",
     "3e94e01: Profil nie vor der Zone, Lücke ab 2 % beendet die Balance, im Ungleichgewicht „verlassene Balance“ (109 von "
     "468); Kartentisch unverändert (0 von 468)"),
    ("chart", "2026-11-15 11:37", "Pivot verbraucht", "behoben",
     "96f5ace (Schritt 2): Drittel aus der Lage in der Zone, überschrittener Pivot zählt nicht – es gilt der nächste "
     "Einstieg (82 Zonen); 1. Kontraktion ab dem Hoch der Zone bei 329 von 329; Zonen unter 5 Wochen (35): Prüfer irrt, "
     "Minervini ab 3 Wochen; 20e3ed0: ab 7 Wellen Minervini höchstens gelb (13 Zonen)"),
    ("chart", "2026-11-15 11:37", "Anderer Rand", "offen", "→ Plan 18 (Gegenseite und Abstände)"),
    ("chart", "2026-11-15 11:37", "Gruppen: Kästen", "offen", "→ Plan 11 (Gruppe)"),
    ("chart", "2026-11-15 11:37", "Bild und Zahlen", "offen", "→ Plan 17 (Bild und Zahlen gleich)"),
    ("chart", "2026-11-15 11:37", "Ampel grün trotz", "behoben",
     "20e3ed0: Minervini grün nur mit Volumen der Enge unter dem Schnitt – grün 11 → 7 (CBOE, COKE, CSX, MEDP gelb)"),
    ("chart", "2026-11-15 11:37", "Base-Gültigkeit", "behoben",
     "4abf7a9: flache Base nach O'Neil als Zone (2 von 462 heute, Spring/Upthrust an ihren Rändern +6); tiefe Zonen behalten den "
     "Pivot (Micky); Zonenbeginn hinter älterem Hoch ist Regel, im Material erklärt"),
    ("chart", "2026-11-15 11:37", "Basenzählung", "behoben",
     "3e94e01: neu nach Phase 4, 3 → 2 und unter dem Tief der vorigen Base (58), Markttief entfällt; Nummer an jeder Zone "
     "(289 mit Nummer statt 140), in Kasten, Kachel und Material"),
    ("chart", "2026-11-15 11:37", "AVWAP Tief der Bewegung und Ereignis", "offen", "→ Plan 20 (Auslegung: Micky entscheidet)"),
    ("chart", "2026-11-15 11:37", "Gruppen-Anlass", "offen", "→ Plan 11 (Gruppe)"),
    ("chart", "2026-11-15 11:37", "Markt:", "offen", "→ Plan 12 (Markt)"),
]
QUELLEN = {"chart": ("🔎 Chart-Prüfer", "chartpruefer"), "setup": ("🎯 Setup-Prüfer", "setuppruefer"),
           "plan": ("🗺️ Gesamtplan", None)}

# Gesamtplan (Micky 15.11.2026: „es darf nichts mehr vergessen oder übersehen werden“): jeder offene Punkt außerhalb der
# Prüfberichte steht hier – mit Stand und Notiz wie ein Befund. Was nicht in der Mängelliste steht, gibt es nicht.
# (Nr, Titel, Bereich, Stand, Notiz) – behoben nur mit Commit und Messung.
PLAN = [
    (1, "Mängelliste als einzige Liste offener Punkte (Gesamtplan, Stand neben jedem Vorschlag)", "Checkliste", "behoben",
     "5a61824: 20 Punkte des Gesamtplans in der Liste, alle 31 offenen Befunde einem Planpunkt zugeordnet, 6 Befunde "
     "standen fälschlich offen (alte Stempel) und sind jetzt behoben; jede Auswertung zeigt den Stand neben dem Vorschlag"),
    (2, "Wachposten prüft die Mängelliste: Stand, Commit und Messung, behoben muss im nächsten Lauf sinken", "Checkliste",
     "behoben", "5a61824: auf dem Server sofort 2 Einträge „behoben ohne Messung“ gefunden und nachgetragen"),
    (3, "Zweite Stufe der Inventur: die 386 Zahlen ohne Namen bekommen Namen und kommen auf die Karte", "Inventur", "behoben",
     "1a0379d und 847ce4d: 0 Zahlen ohne Namen in 312 Regel-Funktionen (vorher 386), 480 feste Regeln, 460 auf der Karte, 20 Technik, "
     "0 doppelt; der Wachposten meldet jede neue Zahl ohne Namen"),
    (4, "Schritt 2: zwei Einstiege – Cheat (früh am Rand) und Ausbruch", "Gefechtsordnung", "behoben",
     "96f5ace: Base long mit zwei Einstiegen in Plan, Chart, Stückzahl, Kartentisch und Prüfern; 112 von 262 Zonen mit Pivot "
     "haben einen Cheat; 68 von 468 Ausbrüchen waren Cheats und zählen nicht mehr als Ausbruch. Der Short-Spiegel steht in Plan 21"),
    (5, "Schritt 3: Struktur-Stopp neben 1,5 ATR (Base: unter der letzten Kontraktion, höchstens 8 %; schnelles Setup: "
        "Tagestief, höchstens eine Tagesspanne)", "Gefechtsordnung", "behoben",
     "0cba440: beide Stopps in Plan, Chart, Lagekarte, CRV, Stückzahl und Prüfer; 143 Setups gemessen: Struktur im Schnitt "
     "7,1 % vom Einstieg, 27 weiter als die Grenze des Meisters (rot), 50 im Tagesrauschen, 7 mit Lücke"),
    (6, "Schritt 4: Spring und Upthrust als eigene Setups (long und short)", "Gefechtsordnung", "behoben",
     "dd133cd: eine Regel an der Zone des Scanners für Zeichen, Zustand und Setup; 468 Titel: Spring 11, Upthrust 23 "
     "(14 grün) als Setup; Zeichen Spring 47 → 36, Upthrust 41 → 76 (vorher eigene 20-Tage-Spanne)"),
    (7, "Schritt 5: Stopp am 10er/20er, Mauer, Kraft ohne Weg und Klimax ziehen ihn enger", "Gefechtsordnung", "behoben",
     "7f19f61: Nach dem Kauf für alle Positionen; gedachte Position vor 30 Tagen an 462 Titeln: 0 am 10er, 462 am 20er, "
     "215 raus, 34 enger (27 Mauer, 4 Klimax, 3 Kraft ohne Weg); Ungleichgewicht am 10er/20er, Zustand anders bei 82 von 468"),
    (8, "Schritt 8: Phasen nach Weinstein als Rahmen (40 Wochen, Sperre nach Phase 4)", "Gefechtsordnung", "behoben",
     "9bd94f6: 462 Titel Phase 1/2/3/4 = 87/102/183/90 → 39/219/112/92; Stufe im Namen jedes Kastens; gegen die Stufe 80 "
     "Setups (22 grün → gelb); Bruch der Spanne auch aus Phase 2: 68 → 81; Phasenwechsel in 2 Jahren höchstens 15 → 10"),
    (9, "Lauf 4: Pivot verbraucht oder zu früh, Drittel falsch (28); grün trotz nicht ausgetrocknetem Volumen (7)",
        "Befunde", "behoben",
     "20e3ed0: Minervini grün 11 → 7 (Volumen der Enge unter dem Schnitt, höchstens 6 Wellen); Drittel, linke Seite und "
     "verbrauchter Pivot schon mit 96f5ace behoben (nachgemessen an 329 Zonen)"),
    (10, "Lauf 4: Volumenprofil der Balance (52, 4 sicher); Basenzählung (34)", "Befunde", "behoben",
     "3e94e01: Profil nach Dalton an der Zone (Lücke ab 2 %), Basenzählung nach IBD – 289 Zonen mit Nummer, 179 ohne "
     "(106 ohne Zone, 68 in Phase 4)"),
    (11, "Gruppe: Anlass (Quad, Verkäufer leer, Zwang), „Geld wandert weiter“", "Gruppe und Markt", "offen", ""),
    (12, "Markt: Anlass, Marktzone gegen Erholungsversuch", "Gruppe und Markt", "offen", ""),
    (13, "Setup-Prüfer prüft die Rückenwind-Stufen (RS-Rang, Ermüdet, Abfluss) – Micky 15.11.: ja", "Prüfer", "offen", ""),
    (14, "Abnahme: voller Setup-Prüfer-Lauf und Chart-Prüfer Lauf 5 (neues Guthaben)", "Abnahme", "offen", ""),
    (15, "Kette der Belege: Zustand passt zu den Belegen, keine Belege aus alter Balance, Anlass mit Richtung und zur "
         "rechten Zeit, Spring nur mit Bruch der Kante, Ende nur bei laufendem Lauf, Dauer der Balance (Lauf 3/4)",
     "Befunde", "behoben",
     "e2a2de5: 7 von 9 Befunden behoben und gemessen (angenommen 139 → 84, Anlass gegen die Richtung 24 → 0); „Belege aus alter "
     "Balance“ und „Dauer der Balance“ prüft Lauf 5 (Plan 14)"),
    (16, "Gültigkeit der Zone: Tiefe, Vorlauf, keine Zone, Zonenbeginn (Lauf 3/4)", "Befunde", "behoben",
     "4abf7a9: flache Base nach O'Neil, tiefe Zonen mit Pivot und Lücke (62), Minervini grün 7 → 6, Zonenregeln im Material"),
    (17, "Bild und Zahlen gleich: Chart und Material aus derselben Zone, Enge und Base (Lauf 3/4)", "Befunde", "offen", ""),
    (18, "Gegenseite und Abstände: anderer Rand, Abstand zu Mauer und Stütze (Lauf 3/4)", "Befunde", "offen", ""),
    (19, "Prüfer irrt: Ersatzregeln der App im Material erklären (Lauf 3)", "Prüfer", "offen", ""),
    (20, "Auslegung für Micky: AVWAP Tief der Bewegung und Ereignis-Anker „zu alt“ (Lauf 4)", "Entscheidung", "offen", ""),
    (21, "Schritt 2 gespiegelt für Shorts (Micky 15.11.: ja): früh unter dem Tief einer Enge, Bruch an der Unterkante. Die "
         "App kennt Shorts heute erst nach dem Bruch (Bärenflagge, Bruch der Spanne) – sie braucht dafür die Zone von der "
         "Short-Seite vor dem Bruch; gebaut mit Schritt 4 (Spring/Upthrust braucht dieselben beiden Ränder)",
     "Gefechtsordnung", "behoben",
     "dd133cd: Bruch der Spanne steht schon vor dem Bruch (Verteilung Phase 3), früher Short am Tief der letzten "
     "Gegenbewegung; 468 Titel: 65 vor dem Bruch, davon 18 mit frühem Short"),
    (22, "Inventur Stufe 3: Regeln in den Anzeige-Modulen – die Inventur sah nur Funktionen der Karte; in Titelseite, "
         "Lagekarte und Kartentisch stehen noch rund 40 Regel-Zahlen ohne Namen (Kacheln: Base Nr. 1–2 grün, RS ab 70/60, "
         "Trendvorlage 7/5, Reaktion ±3 %, Absturz 15 %, Termin 14 Tage, Abstand 10 %), im Chart 189 Zahlen (meist Layout). "
         "Benennen, Kopien auf die eine Quelle führen, Wachposten auf alle Module ausdehnen (Layout als Technik)",
     "Inventur", "offen", ""),
]
COMMIT = r"\b[0-9a-f]{7}\b"
MESSUNG = r"\d"                           # eine Zahl (Messung) – bei reinen Anzeigen das Wort „Anzeige“


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


def _von_hand(x):
    """Hat Micky den Befund auf der Seite gesetzt? (setzen() stempelt Datum UND Uhrzeit; ältere Stempel ohne Uhrzeit
    stammen von Vorgaben – Gesamtplan 15.11.2026: solche Befunde blieben „offen“, obwohl die Vorgabe längst „behoben“ hieß)"""
    import re
    return bool(re.fullmatch(r"\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}", x.get("geaendert") or ""))


def plan():
    """Die Punkte des Gesamtplans als Befunde (Quelle „plan“) – Stand im Code (PLAN)."""
    return [{"id": f"plan-{nr:02d}", "quelle": "plan", "lauf": "Gesamtplan 15.11.2026", "charts": 0, "titel": f"{nr}. {t}",
             "element": bereich, "art": "Plan", "anzahl": 0, "sicher": 0, "beispiele": [], "deutung": "",
             "vorschlag": "", "stand": stand, "notiz": notiz, "geaendert": "Gesamtplan"}
            for nr, t, bereich, stand, notiz in PLAN]


def alle():
    """Alle offenen und erledigten Punkte: Befunde der Prüfer und der Gesamtplan – die eine Liste."""
    return laden()["befunde"] + plan()


def zu_lauf(quelle, lauf, i):
    """Stand des i-ten Befunds (ab 0) der Auswertung eines Laufs → Befund oder None (für „✅ behoben …“ neben dem
    Vorschlag der Auswertung)."""
    bid = f"{quelle}-{lauf.replace('-', '').replace(' ', '-').replace(':', '')}-{i + 1}"
    return next((x for x in laden()["befunde"] if x["id"] == bid), None)


def pruefen():
    """Wachposten für die Liste selbst → [(ampel, name, text)]: Auswertung nicht übernommen (🚨), behoben ohne Commit
    oder ohne Messung (🚨), offener Befund ohne Punkt im Gesamtplan (🚨), behoben, aber im nächsten Lauf nicht seltener
    (gelb)."""
    import importlib
    import re
    aus = []
    m = laden()
    for q, (_, modname) in QUELLEN.items():
        if not modname:
            continue
        try:
            modul = importlib.import_module(modname)
            for f, b in _berichte(modul):
                if b.get("auswertung") and f"{q}:{f}" not in m["uebernommen"]:
                    aus.append(("rot", f"{q} {b['stand']}", "Auswertung nicht in der Mängelliste – Befunde ohne Stand"))
        except Exception:  # noqa: BLE001
            pass
    for x in alle():
        n = x.get("notiz") or ""
        if x["stand"] == "behoben":
            if not re.search(COMMIT, n):
                aus.append(("rot", x["titel"][:60], "behoben ohne Commit"))
            if not (re.search(MESSUNG, n.split(":", 1)[-1]) or "Anzeige" in n):
                aus.append(("rot", x["titel"][:60], "behoben ohne Messung"))
        if x["stand"] == "offen" and x["quelle"] != "plan" and "Plan" not in n:
            aus.append(("rot", x["titel"][:60], "offener Befund ohne Punkt im Gesamtplan – nicht eingeplant"))
    for q in ("chart", "setup"):                    # behoben muss sinken
        try:
            laeufe, tafel = verlauf(q)
        except Exception:  # noqa: BLE001
            continue
        staende = [s_ for s_, _ in laeufe]
        for x in m["befunde"]:
            if x["quelle"] != q or x["stand"] != "behoben" or x["lauf"] not in staende:
                continue
            k = staende.index(x["lauf"])
            if k + 1 >= len(staende):
                continue
            for e in [e.strip() for e in re.split(r"[/,]", x.get("element", ""))]:
                if e in tafel and tafel[e][k] and tafel[e][k + 1] and tafel[e][k + 1][0] >= tafel[e][k][0]:
                    aus.append(("gelb", x["titel"][:60], f"behoben, aber {e} im nächsten Lauf nicht seltener "
                                                         f"({tafel[e][k][0]:.2f} → {tafel[e][k + 1][0]:.2f} je Chart)"))
    return aus


def aus_berichten():
    """Übernimmt die Befunde jeder Auswertung, die noch nicht in der Liste steht. → Zahl der neuen Befunde.
    Befunde ohne eigenen Stand (offen, ohne Notiz) bekommen die VORGABEN."""
    import importlib
    m = laden()
    neu = 0
    for x in m["befunde"]:                         # Vorgaben gelten, solange niemand den Befund selbst gesetzt hat
        if not _von_hand(x):
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
