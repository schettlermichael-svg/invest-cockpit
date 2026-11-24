# Invest Cockpit

Eine App für das ganze SEPA-System: Makro (Dalio-Quadrant), Zyklus (Marks-Pendel), Sektoren und Rotation,
Screening und Mustererkennung nach Minervini, später Risikomanagement. Sie zeigt die Instrumente mit Ampeln
und Deutung – entscheiden tust du.

## Ordner
- `app.py` – Startdatei: `streamlit run app.py --server.port 8510` (im Ordner InvestCockpit)
- `kern/` – Rechenteile ohne Oberfläche
  - `erkennung.py` – Mustererkennung (Flagge, Powerplay, flache Base, 3C, VCP, Tasse mit und ohne Henkel, Doppelboden, ansteigende Base, Base auf Base, Primärbasis)
    Anzeige seit 3.11.2026 einheitlich „Base“ (Kachel, Chart, Lagebeurteilung, Frühere Basen); die Form steht nur als ⓘ-Hinweis. Flagge und Powerplay bleiben benannt (eigenes Setup). Pivot einheitlich = Hoch der letzten Kontraktion am rechten Rand (Minervini, Schalter `EINHEITSPIVOT`); Doppelboden (Mittelspitze, O'Neil) und Cheat behalten ihren Buchpivot. Prüfgalerie unverändert 🟢427 🟡53 🔴24 ⚪84. Namen-Helfer: `gestaltung.basename()` / `form_hinweis()`.
  - `phase.py` – Phasenerkennung 1–4 nach Weinstein/Minervini (Wochenbasis), sechs Übergangskriterien, Stimmungszone je Titel
  - `fundament.py` – Fundament-Ampeln (sieben Prüfpunkte, Code 33, Gewinnqualität)
  - `quellen.py` – Yahoo (bereinigter Gewinn, Schätzungen) und SEC (Umsatz, Nettogewinn), Zwischenspeicher in `daten/fundament/`
  - `lage.py` – Marktampel, Dalio-Quadrant, Marks-Pendel (Lageleiste); `marktdaten.py` – FRED, Yahoo, Marktbreite
  - `sektoren.py` – elf Sektor-ETFs gegen SPY als Rotationsbild (RS-Stärke = RS zum 26-Wochen-Schnitt, geglättet; Schwung = Veränderung in 6 Wochen), Abgleich mit dem Quad, Sektor je Titel
  - `datenpruefung.py` – Datenampel (Lücken, Split-Verdacht, Volumen null, veraltet); in die Mustererkennung eingebaut
  - `zirkel.py` – der Zirkel je Titel, das Setup aus dem Zirkel und seit 23.11.2026 die Markt-Ampel aus dem Zirkel des Index (`marktrichtung.py` und `marktklima.py` nach O'Neil sind entfernt)
  - `rudel.py` – Rudel (Branchen-Breite), Kursverwandte, Themen-Gruppen, Mansfield-RS (Speicher in `daten/rudel/`)
  - `massive.py` – Tageskurse aller US-Aktien von Massive (eine Anfrage je Tag, Speicher in `daten/massive/`)
  - SIC-13 (Mickys Raster) und Fonds-Fußabdruck: am 11.11.2026 entfernt (`_to_delete/sic13_2026-11-11`); TradingView-Kennzahlen je Titel liest `tv_kennzahlen.zeile()` aus `daten/tv/revier.csv`
  - `namen_de.py` – deutsche Namen der Sektoren und Branchen; deutsche Unternehmensbeschreibungen aus `daten/steckbrief_de/beschreibungen.json` (von Claude aus Yahoos englischem Text übertragen, 03.11.2026 für alle 1.884 Titel; neue Titel ergänzt der Nachtlauf)
  - später: `risiko.py`
- `oberflaeche/` – alles Sichtbare als HTML/SVG nach der Designvorlage: `gestaltung.py` (Farben, Bausteine), `chart.py` (Chart), `titel.py` (Titelseite), `uebersicht.py` (Lage am Abend), `frontkarte.py` (Rotationsbild der Sektoren und Themen-Gruppen), `uebergaenge.py` (Tafel „Übergänge“: Quad-Türen, Sektoren und Themen-Gruppen an der Tür, Haken, Breite je Gruppe), `rudelkarte.py` (Rudel und Kursverwandte auf der Titelseite), `stimmung.py` (Stimmungskurve)
- `kern/daten.py` – Kurse und Steckbrief von Yahoo, Speicher in `daten/kurse/`
- `daten/` – Kursspeicher der App, je Titel eine Datei, wird nur ergänzt
- `einstellungen/` – Watchlists, Revier, eigene Einstellungen; optional `sec_kontakt.txt` (Absender für die SEC); `fred_schluessel.txt` (FRED-Schlüssel); `breite.txt` (515 große US-Werte für die Marktbreite), `revier.csv` (Revier: Ticker, Sektor, Branche, Sektor-ETF, Börsenwert, Umsatz), `massive_schluessel.txt` (Massive-Schlüssel)
- `werkzeuge/` – Hilfsprogramme: `nachtlauf.py` (Frühlauf, Kartentisch-Knopf, Schrank), `tpo_laden.py` (30-Minuten-Kerzen), `revier_bauen.py` (Revier neu bauen: NASDAQ-Liste + Umsatz von Massive, eine Aktiengattung je Firma), `branchen_nachtragen.py` (Sektoren von Yahoo nachtragen), `server/` (Einrichtung, Aktualisierung, Sicherung und Timer des Servers). Die früheren Prüfwerkzeuge (vorschau, fundament_test, lage_test, sektoren_test, daten_test, markt_test, historie_laden, rudel_test) gibt es nicht mehr; ihre Ergebnisse stehen in den Abschnitten unten.
- `pruefgalerie/oneil/` – O'Neil: Regelkatalog (nur Notizen), Chartkatalog der 286 Buchcharts, Abgleich mit der App
- `werkzeuge/digitalisierung/` – liest O'Neils Wochencharts aus den Buchfotos in Kurse (`digitalisieren.py`), Stapellauf über den Chartkatalog (`batch.py`), Gegenprobe mit TradingView (`vergleich.py`: Apple, Cisco, Amazon, VeriSign – Abweichung im Median 0,1–0,6 %, Daten wochengenau), Galeriegruppe OD bauen (`galerie_bauen.py`)
- `pruefgalerie/oneil_digital/` – die gelesenen Wochenkurse aller 232 Buchcharts und ihre Güte (A/B/C)
- Minervini (BigCharts-Abbildungen Kap. 5 und 10): `werkzeuge/digitalisierung/bigcharts.py` liest Tages- und Wochencharts (Kopfdatum, Achse linear oder logarithmisch, Monatsgitter, Volumen in Millionen), `minervini_katalog.py` ordnet Tafeln den Bildunterschriften zu, `minervini_batch.py` liest alle Fotos, `md_bauen.py` baut die Galeriegruppe MD; Gegenprobe `tvref.py` mit TradingView (MELI, NFLX, DECK, CRUS, CROX: Hoch/Tief im Median 0,04–1,1 %). Ergebnisse in `pruefgalerie/minervini_digital/`
- `pruefgalerie/` – Abnahmetest der Mustererkennung (eigene, eingefrorene Kurse; siehe dortiges LIESMICH)

## Datenquellen
Grundsatz (03.11.2026): Yahoo und Massive sind gut, aber TradingView bietet riesiges Potenzial. Bei jeder
Datenfrage wird TradingView mitgedacht und alles daraus geholt, was der App nützt. Die TradingView-Anbindung gehört
Claude, nicht der App: Die Daten kommen über den Nachtlauf als Dateien nach `daten/tv/` (Mac an, Claude-App offen).

| Quelle | liefert | wofür |
|---|---|---|
| Massive | Tageskurse aller US-Aktien, eine Datei je Tag | Kursreihen für Stärke und Schwung, Rudel, Themen-Gruppen, Breite |
| Yahoo | Kurse, bereinigter Gewinn, Schätzungen, Steckbrief, ETFs, Rohstoffe | Titelseite, Fundament, Quad-Instrumente |
| FRED | Weekly Economic Index, GDPNow, Erstanträge, Breakeven, BIP, Verbraucherpreise | Quad |
| SEC | Umsatz und Nettogewinn je Quartal, 13F | Fundament, I-Ampel |
| TradingView: Screener (ganzer US-Markt) | GD 50/150/200, 52-Wochen-Hoch/-Tief, Performance 1 W bis 1 J, Branche, Liquidität, relatives Volumen | Breite je Gruppe und Branche, Vorhut in der Tafel „Übergänge“, Revier auf den ganzen Markt, Vorauswahl nach Trendvorlage |
| TradingView: Aktienzahl | umlaufende und frei handelbare Aktien, Rückkaufquote | S-Ampel nach O'Neil (statt Yahoo/SEC) |
| TradingView: Termine | nächster Zahlentermin je Titel, Earnings-Kalender | Kachel „Nächste Zahlen“, Earnings 14 Tage |
| TradingView: Schätzungen | Analystenschätzungen und ihre Änderung | Schätzungsrevisionen je Titel und je Gruppe als Vorbote |
| TradingView: Finanzhistorie | Umsatz, Gewinn, Quartale | Gegenprobe zum Fundament, später Hauptquelle |
| TradingView: Wirtschaftsdaten | ISM Auftragseingang und Preise, Leading Index, Fed-Umfragen, Arbeitsmarkt | schärfere Quad-Achsen, Tafel „Übergänge“ |
| TradingView: Wirtschaftskalender | Termine der amtlichen Zahlen | wann eine Quad-Tür aufgehen kann |
| TradingView: Nachrichten und Dokumente | Meldungen je Titel | Grund hinter einem Ereignis (Zahlen, Übernahme, Ausblick) |
| TradingView: Kerzen | Kurse jedes Titels | Titel außerhalb des Reviers |
| TradingView: Alarme und Watchlists | Preisalarme, Watchlists | Wachposten an Pivot und Stopp, Abgleich der Watchlists – nur mit Freigabe |

Bewusst nicht genommen: die „Ratings“ von TradingView (Punktzahlen) und institutionelle Halter (gibt es dort nicht;
die I-Ampel bleibt bei 13F).

Nach jeder Code-Änderung baut die App die Seiten neu (Codestand im Seitenspeicher), sonst halten sie eine Stunde.

## Prüfen
```
cd "/Users/michaelschettler/Desktop/Just EVERYTHING/Investment/Apps/InvestCockpit/pruefgalerie"
python3 pruefen.py
```

Konzept: https://claude.ai/artifact/B185d4Kju4DAeQSbHDSEni

## Chart-Knöpfe (03.11.2026)
Direkt über dem Chart (app.py `chart_knoepfe`): Tag/Woche, Ausschnitt (`chart.AUSSCHNITT`: Tag 3 M/6 M/1 J/2 J, Woche 1 J/3 J/5 J – Woche über 3 Jahre hinaus aus `daten/lang`, skaliert auf den ersten gemeinsamen Schluss), GD10/GD20 als Wahlschalter (nur Tag), „↻ Kurse aktualisieren“ (Rückruf, wirkt im selben Lauf) und „TradingView ↗“. `titel.seite_titel` liefert drei Teile (oben, Zwischenstand für den Chart, unten); `titel.chartkarte` zeichnet nur den Chart neu, die Seite wird dafür nicht neu gerechnet. GD200/GD40W sandfarben (`chart.SAND`), Volumen mit 50-Tage-Schnitt (Woche 10 Wochen).

## Einzeichnung der Base (03.11.2026)
`chart.py`: fertige Base = Rahmen durchgezogen, Pivot und Kaufzone ab dem Tag, der den Pivot setzt (`_pivot_tag`, mit Punkt); Base im Aufbau (`erk["aufbau"]`, nicht Phase 4 und höchstens 35 % tief) = gestrichelter Rahmen, möglicher Pivot gepunktet ab zwei Kontraktionen (`erkennung.kontraktionen_lage`), keine Kaufzone; frühere Basen = blasser Rahmen, Pivot bis zum Ausbruch, danach gepunktet bis zum ersten Schluss darunter; sonst Hinweis „keine Base (– Abwärtstrend)“. `freie_bahn.alte_pivots`: Pivots früherer Basen ohne Schluss darunter seit dem Ausbruch zählen als Unterstützung („alter Pivot“).

## Eine Base-Regel für live, Historie und Zählung (03.11.2026)
`erkennung._base_zaehlt`: eine Pause bis zum neuen Hoch zählt als Base ab `BASE_MIN_RUECK` = 5 % Rücksetzer, `BASE_MIN_TAGE` = 20 Tage vom linken Rand (Hochs bis 2,5 % darunter) und `BASE_MIN_SEIT_HOCH` = 15 Tage ab dem Hoch – gilt für `basen_historie` (nur noch `werkzeuge/massenlauf.py`; die Basenzählung läuft seit 06.11.2026 über `kern/basen.py`). `vorige_base` (Base auf Base) nutzt `streng=True` (alte Abgrenzung 4 Wochen ab Hoch, 10 %). Prüfgalerie danach unverändert (🟢427 🟡53 🔴24 ⚪84). Im Chart steht ✓/✗ über der Kerze, wenn der Ausbruch auf einen Zahlentag fällt.

## Strömung in der Zone und Balance-Zone (03.11.2026)
`kern/stroemung.py`: Karte „Strömung in der Zone“ unter dem Chart (Base, sonst Base im Aufbau, sonst 60 Tage): Wertwanderung (POC letzte 2 Wochen gegen POC der Zone), steigende Tiefs, Schlusslage (↑/↓/→, Richtung gemessen), Enge und Volumen (◆, Druck ohne Richtung, gemessen), Fußabdruck und RS-Linie (Richtung nicht gemessen). `kern/balance.py` + `werkzeuge/messung_balance.py`: Balance-Zone als Messwerkzeug (Darvas-Beginn, Oberkante steigt mit Spießen, Akzeptanz 2 Schlüsse, innere Zone, Auflösung ab 50 % oder Phase 4), von der App noch nicht benutzt; Ergebnisse in `daten/massenlauf/messung_balance_03112026.json`.

## Umstellung auf die Balance-Zone (03.11.2026, Schalter `erkennung.BALANCE`)
`erkennung.erkenne` liest die Zone, die heute gilt (`balance.am_tag`: laufend oder bis 4 Wochen nach dem Kippen), eingeordnet nach den Regeln der Meister: Base (ab 3 Wochen, 5–50 % Tiefe, über 35 % Zeichen „tief“; auch ansteigende Base und Base direkt über einer Base als Kette), Flagge/Powerplay (Flaggenregel der App). Phase 4 = „Abwärtstrend“, keine Base. Pivot = Hoch der letzten Kontraktion. Kaufsetup wie bisher (Trendvorlage, Phase 2, Tiefe, Korrektur zum Markt, Datenampel) plus „Angebot von oben“ (Tief seit dem 65-Wochen-Hoch über 50 % darunter). Basenzählung: gekippte Base-Zonen ab 4 Wochen, eine neue Stufe erst 20 % über der zuletzt gezählten (IBD/O'Neil); frühere Basen = gekippte Base-Zonen ab 4 Wochen. Alte Formerkennung als `_erkenne_formen` (BALANCE = False) bis zur Abnahme; dann nach `_to_delete/`. Prüfgalerie (`pruefen.py`, BALANCE_MODUS: keine Formnamen mehr): 🟢 484 (vorher 427), 🟡 7, 🔴 13, ⚪ 84; schlechter 5: GN189 (Klimax-Top, Kaufsetup mit Klimax-Warnung – Klimax bleibt Zeichen), GN194 (Top, vorher schon gelb), S89, S91 und S147 (Sichtung 30.10.2026: zwei Flaggen, eine ansteigende Base). Spieß-Regel: bei Zonen ab 4 Wochen hebt nur ein Hoch mehr als 2,5 % über der Oberkante mit Schluss in der unteren Tageshälfte die Oberkante (sonst verschmolzen aufeinanderfolgende Basen, HWM 2025); junge Zonen heben bei jedem höheren Hoch. Ausbrüche ohne Akzeptanz (2 Schlüsse) bleiben in der Zone. Bericht: `pruefgalerie/bericht_balance_03112026.json`.

## Market-Profile-Zonen (4.11.2026)

Die Zonen stammen aus dem Market Profile nach Steidlmayer und Dalton und ersetzen die Balance-Zone (`erkennung.MP = True`).

- **Daten:** `kern/tpo_daten.py` speichert 30-Minuten-Kerzen der regulären Sitzung in `daten/tpo/<Ticker>.csv`.
  - Die Erstbefüllung kommt von Massive: 2 Jahre, eine Anfrage je Titel.
  - Danach setzt Yahoo die Reihen fort.
  - Jeder Tag wird auf den Tagesschluss der App skaliert. Damit gilt dieselbe Bereinigung (Splits, Dividenden) wie im Tageschart.
  - Alle Titel lädt `python werkzeuge/tpo_laden.py`. Das dauert einmalig etwa 6,5 Stunden, am besten über Nacht. Danach genügt `python werkzeuge/tpo_laden.py fortsetzen`.
  - Die Titelseite lädt beim Öffnen selbst nach.
- **Rechnung:** `kern/marketprofile.py`.
  - Zeitabschnitte (TPO) von 30 Minuten auf einem Preisraster mit 0,2 % Zeilenhöhe.
  - POC und Wertbereich 70 % nach Steidlmayer.
  - Zonen aus abgeschlossenen Wochen: Die Wochen gehören zusammen, solange sich ihre Wertbereiche überlappen (Dalton).
  - Tageswerte zum Vortag: ▲ △ ▬ ▽ ▼.
  - Auslöser in beide Richtungen, gemessen an der Zone der Wochen davor:
    - **A:** Schluss jenseits des Rahmens, Tageswert ganz außerhalb, Zone mindestens 3 Wochen alt.
    - **F:** dasselbe bei einer jüngeren Zone nach einem Lauf in dieselbe Richtung.
    - **B:** Wochenwert ganz außerhalb.
    - **R:** Rücktest der verlassenen Zone, der hält.
    - **S:** gescheitert, Schluss zurück im Wertbereich der verlassenen Zone.
  - Zustand: Balance · an der Schwelle · Ausbruch (Tag n) · bestätigt.
- **Seite und Setup:**
  - Phase 1/2 bedeutet long: Pivot = Oberkante des Rahmens, Kaufzone +5 %, Regeln von O'Neil und Minervini.
  - Phase 3/4 bedeutet short: Auslöser = Unterkante, Verkaufszone −5 %, Weinstein (Kurs unter dem fallenden 30-Wochen-Durchschnitt).
  - Eine Zone ab 3 Wochen ist eine Base. Eine jüngere Zone nach einem Lauf ist eine Flagge.
- **Basenzählung und Historie:**
  - Gezählt werden verlassene Zonen ↑ ab 4 Wochen, jede neue Stufe erst 20 % über der vorigen.
  - Die Historie zeigt Zonen ↑ und ↓ ab 3 Wochen. Ausgang nach O'Neil, für short gespiegelt.
- **Titelseite:**
  - Kachel „Zone“ mit Zustand und Belegen.
  - Kachel „Setup long/short“.
  - Chart: Rahmen, Wertbereich, orange POC-Treppe und ↑/↓. Die Auslöser und das ✓/✗ früherer Basen stehen seit 04.11.2026 nicht mehr im Chart, sondern nur in den Karten „Strömung in der Zone“ (Letzte Auslöser) und „Frühere Basen“.
  - Ein Volumenprofil über die letzten 52 Wochen.
  - Karte „Strömung in der Zone“ mit Tageswerten, Tages-POC, Lage, Spannen, Volumen, verlassener Zone und Auslösern.
  - Stopp: Schluss unter dem VAH der Zone, höchstens 8 %.

### Aufgeräumt (04.11.2026)

`kern/balance.py`, `kern/darvas.py`, `werkzeuge/messung_balance.py` und die alte Formerkennung liegen in `_to_delete/balance_04112026/`. Aus `erkennung.py` sind ebenfalls entfernt: Doppelboden, Tasse, ansteigende Base, Flaggenprüfung, Base im Aufbau sowie die Schalter BALANCE und MP. Die Prüfgalerie mit den Buchfällen ist kein Tor mehr. Die Buchcharts haben keine 30-Minuten-Kerzen, deshalb läuft sie mit den Market-Profile-Zonen nicht. Die Regelkataloge in `pruefgalerie/` bleiben als Nachschlagewerk.

### Abendlauf: welche Titel (04.11.2026)

`tpo_daten.lauf_liste()` bestimmt, welche Titel der Abendlauf lädt:

- den Gesamtmarkt (SPY, QQQ, IWM);
- das Revier;
- die Watchlists (`einstellungen/watchlists.json`, kommt mit Schritt 6);
- jeden Titel, dessen Titelseite einmal geöffnet wurde (`daten/tpo/_geoeffnet.json`). Dieser bleibt ohne Ablauf im Lauf.

Entfernt wird ein Titel nur, wenn er gelöscht wurde:

- Er wurde aus der Watchlist genommen. Dafür ruft die Watchlist `tpo_daten.vergessen(ticker)` auf.
- Er ist aus dem Revier gefallen.

Seine Datei verschiebt `tpo_laden.py` vor jedem Lauf nach `_to_delete/tpo/`.

### Strömung in der Zone: Bild und Erklärungen (04.11.2026)

Die Karte zeigt jetzt oben ein Bild: die Tageswerte der letzten 15 Tage als Säulen vor dem Wertbereich der Zone (`oberflaeche/stroemungsbild.py`).

- Säule: der Wertbereich des Tages. Grün heißt höher als am Vortag, rot tiefer, grau gleich.
- Orange: der Tages-POC.
- Punkt: der Schlusskurs.
- Über jeder Säule steht das Zeichen ▲ △ ▬ ▽ ▼.
- Nach einem Ausbruch zeigt eine rote Linie die Stopp-Kante der verlassenen Zone.

Jede Zeile der Karte hat ein ⓘ (`stroemung.HILFE`). Es erklärt, was gemessen wird, wie man die Zeichen liest und was das im Kriegsbild bedeutet. Zusätzlich steht die Lesart in Worten in der Zeile, zum Beispiel „– Käufer rücken vor“.

### Lagekarte (04.11.2026)

`oberflaeche/lagekarte.py` baut einen Titel auf einen Blick. Die Karte gibt es einmal, verwendet wird sie auf der Titelseite (links neben den Kacheln) und später unverändert auf dem Kartentisch und in den Watchlists. Sie zeigt:

- den Kopf mit dem Setup;
- Chips für Zone, RS, Phase und Base;
- die Belegzeile der Zone;
- einen Kleinchart über 6 Monate mit Zonen, POC-Treppe und Pivot;
- sechs Ampelpunkte: Markt, Phase, Zone, Branche, RS, Fundament (Maus darauf zeigt die Zeile der Kachel);
- die Abstandsleiste zum Pivot bzw. Auslöser;
- den Stopp und die nächsten Zahlen.

Alle Werte liest die Karte aus den Kacheln (`gestaltung.MITSCHRIFT`). Sie rechnet nichts Eigenes, deshalb widersprechen sich Karte und Kacheln nie.

### Tabelle „Frühere Basen“ entfernt (04.11.2026)

Die Rechnung bleibt, nur die Tabelle fällt weg. Der Ausgang jeder verlassenen Zone steht jetzt im Hinweis am Zonenrahmen im Chart. Dort stehen Basennummer, Ausbruch, Ausgang nach O'Neil, das höchste Ergebnis, das Volumen und ob es damals ein Setup war. Die Bilanz der drei Jahre steht im ⓘ der Kachel „Base“.

### Kartentisch (04.11.2026)

`oberflaeche/kartentisch.py` rechnet die Übersicht im Abendlauf vor, nach dem Yahoo-Schritt und vor den Massive-Durchgängen.

- **Stufe 1:** alle Titel, nur Erkennung und Zone, mehrere Prozesse, etwa 1 bis 2 Minuten. Jeder Titel wird einer Reihe zugeordnet.
- **Stufe 2:** für die Titel in einer Reihe die volle Titelseite, also dieselben Kacheln und dieselbe Lagekarte.

Das Ergebnis liegt in `daten/kartentisch/<Datum>.json`. Die Übersicht liest nur diese Datei.

**Reihen:**
- ★ Spitzenkandidaten: Setup grün, und die Zone steht an der Schwelle oder im Ausbruch in Richtung des Setups.
- Weitere Kandidaten: Setup grün in Balance, oder genau eine Regel fehlt.
- Frühaufklärung (Radar): Zone an der Schwelle oder frischer Angriff (A, F, U in den letzten 5 Tagen), egal wie viele Regeln der Meister noch gelb sind. Frische Angriffe stehen oben, mit Zeichen und Datum (z. B. U↑ 02.11.).
- Short: dieselben Stufen für die Short-Seite.
- Watchlists folgen mit Schritt 6.

Je Reihe erscheinen 12 Karten, der Rest steht aufklappbar als Zeilen darunter. Gefiltert wird nichts. Sortiert wird zuerst nach ★, dann grün vor gelb, dann nach dem Abstand.

Dazu zeigt der Kartentisch:
- das Führer-Barometer: grüne Setups long und short, neue 52-Wochen-Hochs gegen -Tiefs;
- „Neu seit gestern“: neu in einer Reihe, vorgerückt, Phasenwechsel;
- „Earnings 14 Tage“.

Bedienung (05.11.2026): Unter jeder Karte zwei Knöpfe der App – „☆ Watchlist“ (je Liste ein Haken; im
Watchlist-Abschnitt stattdessen „→ nach … verschieben“ und „✕ herausnehmen“) und „Deep Dive →“ (Titelseite im neuen Tab).
Die ersten 12 Titel je Abschnitt als Karte, die übrigen als Tabelle in derselben Rangfolge (★, frischer Auslöser,
Setup grün, Abstand); Klick auf eine Zeile öffnet die Lagekarte im Pop-up (✕ schließt). Rahmen überall: grün long,
rot short, kräftig = ★, voll = Setup grün, blass = Setup nicht grün, gelb = noch keine Reihe/Richtung offen, dazu der
Grund, was fehlt. Watchlist-Zugehörigkeit gilt sofort (aus den Listen der App, nicht aus dem Abendlauf).
Felder „Ausbruch aus der Konsolidierung“ und „Flagge“ (05.11.2026), ganz oben vor den Spitzenkandidaten, ohne
Doppelung (gehen jeder anderen Reihe vor): die laufende Bewegung des Market Profile hält noch (kein S, keine neue reife
Zone), begann vor höchstens 10 Handelstagen, und das Volumen am Ausbruchstag lag über dem 50-Tage-Schnitt.
Konsolidierung = A oder U (bzw. B aus einer Zone ≥ 3 Wochen), Flagge = F (bzw. B aus junger Zone). Long und short
(Rahmen grün/rot). Über der Karte: Auslöser, Volumenfaktor, Vorlauf (Korrektur vom Hoch bzw. Anstieg vom Tief) –
Zeichen, kein Filter; Phase, Trendvorlage und RS sperren nicht (stehen als Ampeln und „Was fehlt“).
Nur den Kartentisch rechnen: `python3 werkzeuge/tpo_laden.py kartentisch`.

### Markt-Ampel mit Zonen, Auslöser U, Seite nach der Bewegung (04.11.2026)

**Markt-Ampel (O'Neil):** Die Verteilungstage bleiben, wie O'Neil sie zählt. Für „Korrektur“ muss jetzt zusätzlich die Zone von S&P 500 (SPY) oder Nasdaq (QQQ) nach unten gebrochen sein, durch A↓, F↓, U↓ oder B↓. Sonst bleibt die Ampel auf „unter Druck“. So handhabt es auch IBD, solange die Indizes nahe am Hoch stehen. Kachel und Übersicht zeigen die Zone beider Indizes.

**Auslöser U (Umkehr):** Nach einem gescheiterten Bruch (S) verlässt der Kurs die junge Zone in die Gegenrichtung. Das ist die gescheiterte Auktion nach Dalton.

**Seite:** Eine laufende Bewegung (A, F, U, B) bestimmt, ob der Titel long oder short geführt wird. Die Phase entscheidet nur, wenn keine Bewegung läuft. Phase, Trendvorlage und Markt bleiben als Regeln mit Ampel erhalten. Ein Signal gegen die Phase wird angezeigt und nicht verschluckt (Anlass: HWM, 02.11.2026).

**Kachel „Base“ bei einer Umkehr:** Sie zeigt „keine – Umkehr“ mit dem Datum des gescheiterten Bruchs und dem Datum der Umkehr.


## Watchlists (Schritt 6, 04.11.2026)

- Eigene Listen der App in `einstellungen/watchlists.json` ({Name: [Ticker]}), Modul `kern/watchlists.py`. Start: einmaliger
  Import der TradingView-Listen (nur gelesen): „Active Watchlist“ (8) und „Watchlist“ (178 Titel, Abschnitte und die
  Indizes SPX/DAX übersprungen). Jeder Titel nur einmal je Liste; über alle Listen zusammen 178 Titel.
- Titelseite: Knopf „☆ Watchlist“ über dem Chart, je Liste ein Haken und „neue Liste“. Aus der letzten Liste genommen = gelöscht:
  ohne Revier fällt der Titel aus dem Abendlauf, seine 30-Minuten-Datei wandert nach `_to_delete/tpo/`.
- Kartentisch: Reihe „Meine Watchlists“ direkt unter den Spitzenkandidaten, je Liste ein Abschnitt; jeder Titel immer (egal
  welche Ampel) und nur einmal: seine eigentliche Reihe und die Listen stehen als Marke über der Karte, in den übrigen Reihen
  erscheint er nicht noch einmal. Neu seit gestern meldet jeden Reihenwechsel eines Watchlist-Titels (◆ Radar → ★ Spitze,
  auch abwärts). Earnings 14 Tage enthält die Watchlist-Titel. Neu hinzugefügte Titel: Zeile „wird im Abendlauf gerechnet“.
- Börsen außerhalb der USA (RHM.DE, LDO.MI, KOG.OL, AM.PA, SAAB-B.ST, BA.L, TKMS.DE): Sitzung der Heimatbörse in Ortszeit
  (`tpo_daten.SITZUNGEN`), 30-Minuten-Kerzen nur über Yahoo (60 Tage, danach wächst die Reihe täglich), Massive überspringt
  sie; TradingView-Knopf mit Heimatbörse (XETR:RHM). RS-Linie und Marktbezug weiter gegen den S&P 500, Fundament aus SEC fehlt.

## Lagekarte nach Sektoren (Schritt 5, 04.11.2026)

- `kartentisch.lagebild`: Bild unter den Reihen der Übersicht. Zeilen = Sektoren (Feld der Frontkarte: Führend → Erstarkend →
  Ermüdend → Abgehängt, darin nach Stärke, mit Pfeil der letzten 5 Wochen), Spalten = ★ Spitze · Radar · Weitere · Short ·
  ◆ ohne Reihe. Jeder Titel genau einmal; Marken anklickbar (Titelseite), Maus zeigt Zustand und Themen-Gruppe.
- Zeichen: ★ grün = Spitzenkandidat long, ★ rot = Short an der Schwelle/im Ausbruch, Radar mit Auslöser (U↑, A↓ …),
  ◆ = Watchlist, ⚑ = Themen-Gruppe im Feld Führend oder Erstarkend. Je Zelle 8 Marken, Rest über „+n“ aufklappbar.
- Sektor: aus dem Revier, sonst aus dem Steckbrief (Yahoo-Sektor); Titel ohne Sektor in der Zeile „ohne Sektor“.

## Schritt 7 Rest (04.11.2026)

- `kern/short_seite.py`: Short-Seite in „Lage und Plan“ (Phase 3/4 oder Seite short): drei Einstiege mit Kursmarke, Stopp
  und Zustand (liegt vor / bildet sich / nicht da) – Bruch der Gipfelzone (MP-Zone, Weinstein), gescheiterte Erholung am
  fallenden GD150 (Weinstein), Schulter-Kopf-Schulter-Top (O'Neil: Kopf = 12-Monats-Hoch, ≥3 % über den Schultern,
  Schultern ≤8 % auseinander, rechte nicht höher, Nackentiefs ≤5 % auseinander, Bruch zählt 3 Monate; Stichprobe 400
  Titel: 10 Formen). Dazu O'Neils Short-Regeln: früherer Führer (+100 % vor dem Top), 5–7 Monate nach dem Top, Liquidität
  (ab 5 Mio. Stück grün). Ersetzt den alten Absatz „Short-Szenario (Phase 4)“.
- `kern/fruehwarnung.py`: Frühwarnzeichen Phase 3/4 (Weinstein) in „Warnzeichen“, nur Phase 2/3: Bruch unter GD50
  (10 Wochen) mit ≥1,4-fachem Volumen in den letzten 10 Tagen; Schluss unter der Unterkante der Zone.
- `kern/avwap.py` + Karte „AVWAP-Liste“ (neben den Warnzeichen): AVWAP ab Zonenbeginn, Zonentief, größtem Volumen,
  Zonenhoch und 52-Wochen-Hoch, alle zugleich; Ampel über allen / dazwischen / unter allen.
- Fundament-Ampeln: S (Aktienzahl, frei handelbar, Rückkauf/Verwässerung aus TradingView) und I (Anteil der
  Institutionen und Zu-/Abbau der 10 größten Halter, Yahoo/13F) als Zeilen neben den sieben Prüfpunkten, nicht gezählt.

## Risikomanagement (Schritt 9, 04.11.2026)

- `kern/depot.py`, `einstellungen/depot.json`: Konto (€), Risiko je Trade (Voreinstellung 1 %, einstellbar über
  „⚙ Konto und Risiko“ auf der Übersicht), Positionen (Titelseite „＋ Position“: Seite, Stück, Einstieg, Stopp,
  Knock-out-Schwelle und Bezug). Umrechnung mit dem Tageskurs EUR/Titelwährung (Yahoo).
- Stückzahl: Risiko € × Kurs / (Einstieg − Stopp) [× Bezug beim Knock-out]; Einstieg/Stopp wie auf der Lagekarte
  (Pivot bzw. Auslöser; VAH/VAL oder 8 %). Auf jeder Lagekarte und in der Karte „Position und Risiko“ (Titelseite) mit
  Positionswert, Klumpen-Warnung über 25 % und Depot-Hitze danach.
- Depot-Hitze: offenes Risiko (Einstieg bis Stopp, 0 sobald gesichert) aller Positionen, Grenze 6 %; Depotleiste auf der
  Übersicht mit Abstand zum Stopp und dem wichtigsten Zeichen.
- Nach dem Kauf: kein Stopp (rot), Verlustgrenze −8 % (O'Neil), Stopp nachziehen ab 2R und bei neuer Zone (VAL),
  Squat, Tennisball, Reset beobachten, +20 % (Teilgewinn bzw. 8-Wochen-Regel).
- Scalable „Agentic Investing“ (MCP, seit 25.08.2026): nach Freischaltung im Kundenbereich und Verbindung in claude.ai
  schreibt Claude die Positionen über `depot.uebernehmen()`; Stopps und Knock-out-Daten bleiben.

## Nachtlauf (Schritt 8, 04.11.2026)

- `werkzeuge/nachtlauf.py`: Massive-Tageskurse und Splits → Rudel/Kursverwandte/Themen-Gruppen → 30-Minuten-Kerzen
  (Yahoo) → Tageskurse und Wechselkurse → Lage (Übersicht einmal bauen) → Kartentisch → Massive-Durchgänge für Lücken bis
  07:00 Uhr. Jeder Schritt einzeln abgesichert, Protokoll `daten/nachtlauf/protokoll.json`, Datenampel im Kopf der Übersicht
  (grün vollständig, rot gescheitert oder veraltet), Mitteilung auf dem Mac.
- Einrichtung einmalig: `zsh werkzeuge/nachtlauf_einrichten.sh` (launchd Mo–Fr 22:45, pmset weckt 22:40; Log
  `~/Library/Logs/InvestCockpit/nachtlauf.log`). Bei „Operation not permitted“: /bin/zsh in Festplattenvollzugriff.
- `werkzeuge/tpo_laden.py` bleibt für Läufe von Hand (z. B. `kartentisch`).

## Ablösung SEPA-Scanner (Schritt 10, 04.11.2026)

Abhakliste: Universum (Nasdaq 100, S&P 500/400/600) → Revier 1.882 Titel ✓ · Watchlist einfügen (Finviz) → „Ticker
einfügen“ im Watchlist-Fenster ✓, gespeicherte Liste → `werkzeuge/sepa_watchlist_uebernehmen.py` ✓ · Nur-Watchlist-Scan →
Reihe „Meine Watchlists“ ✓ · Top N, RS-Minimum, k, Tag/Woche (Regler) → entfallen bewusst (keine Regler, Reihen statt
Filter) ✓ · SEPA-Score → Ampeln statt Punktzahl ✓ · Marktregime → Markt-Ampel ✓ · VCP-Kontraktionen → Market-Profile-Zonen
✓ · AVWAP und AVWAP-Liste → Karte „AVWAP-Liste“ ✓ · Europa → Watchlist-Titel mit Heimatbörse ✓.
Watchlist-Titel außerhalb des Reviers (US) laufen im Rudel mit (Kursverwandte, Themen-Gruppen, Platz), zählen nicht in
die Rudel-Breite.
Alter Scanner abgeschaltet: Ordner nach Apps/_to_delete/sepa verschoben (04.11.2026). Einstellungsseite und Sperrliste
aus Schritt 6 gestrichen (Begründungen als ⓘ und hier; eine Sperrliste wäre ein Filter).
Schritt 11 (Messung, Backtest der Ebenen) gestrichen: keine Ertragsmessungen als Urteil.
- Claudes früherer Teil (00:37 Uhr: TradingView, Revier) entfällt seit 05.11.2026 – der Server holt beides selbst; Scalable-Positionen folgen, sobald die Schnittstelle verbunden ist.

## Server (ab 05.11.2026)

- Hetzner CX23, Nürnberg, `invest-cockpit`, IP 2.31.188.241, Ubuntu 26.04, Backups an (8,43 €/Monat, Rechnung am 23.).
- `werkzeuge/server/einrichten.sh` (einmalig, `ssh root@2.31.188.241 'bash -s' < werkzeuge/server/einrichten.sh`):
  Zeitzone Berlin, automatische Sicherheitsupdates, Firewall (22/80/443), Benutzer `cockpit`, Ordner
  `/opt/invest-cockpit` mit Python-Umgebung, Dienst `invest-cockpit` (Streamlit, immer an), Zeitplan `nachtlauf.timer`
  (seit 12.11.2026 Frühlauf Di–Sa 6:05 Berlin, `werkzeuge/server/nachtlauf.timer`), Caddy mit https unter `2-31-188-241.sslip.io` und Passwort (Benutzer micky).
- `werkzeuge/server/uebertragen.sh`: Ordner vom Mac auf den Server (rsync, ohne _to_delete) und App neu starten.
- Geplant: Code über privaten GitHub-Speicher `schettlermichael-svg/invest-cockpit`, Server holt Änderungen selbst.
- Seit 05.11.2026 auf dem Server, ohne Claude und ohne Mac: TradingView-Kennzahlen (`kern/tv_kennzahlen.py`, Screener-
  Schnittstelle, Test 1.889 Titel = 100 %) und freitags die Revier-Pflege (`kern/revier_pflege.py`: Zugänge nach den
  Revier-Regeln mit Sektor/Branche von Yahoo, höchstens 40 je Woche, Abgänge nur gemeldet). Neue Titel haben zunächst
  den englischen Yahoo-Steckbrief.
- Code kommt über GitHub (`schettlermichael-svg/invest-cockpit`, privat, nur Code): Der Server schaut alle 5 Minuten nach
  (`invest-update.timer`, `/usr/local/bin/invest-aktualisieren`, Deploy key nur lesend) und startet die App neu.
  `werkzeuge/server/uebertragen.sh` schickt nur noch Code (Daten auf dem Server sind das Original).
- Die geplante Claude-Aufgabe (00:37, Mac) ist gelöscht (05.11.2026). Scalable folgt, sobald der Konnektor verbunden ist.
- Watchlists App → TradingView (ab 05.11.2026, nur diese Richtung, von Micky freigegeben): Der Server legt
  `einstellungen/watchlists.json` alle 10 Minuten auf den GitHub-Zweig `daten` (`invest-watchlist.timer`, Deploy key mit
  Schreibrecht). Eine Claude-Aufgabe in der Cloud (stündlich 8–23 Uhr, Minute 13) vergleicht mit `tv_abgleich.json` und
  trägt nur die Änderungen in die gleichnamigen TradingView-Listen ein (neue Liste wird angelegt, keine Liste gelöscht,
  selbst in TradingView eingetragene Titel bleiben unberührt, Alarme tabu). Änderungen in TradingView fließen nicht zurück.

## ATR-Zeichen (05.11.2026)
`kern/atr.py`: ATR (14 Tage) = übliches Tagesrauschen. Auf jeder Lagekarte (Übersicht, Pop-up, Titelseite) vier
Zeichen, kein Filter: Stopp im Rauschen (Einstieg → Stopp unter 1 × ATR rot, bis 1,5 gelb), zu weit gelaufen (über
2 × ATR jenseits des Pivots rot „nicht nachjagen“), Enge (Spannen der letzten 5 Tage unter 0,6 × ATR grün), Überdehnung
(Abstand vom GD50 ab 4 × ATR gelb, ab 6 rot). Short-Seite: Überdehnung über dem GD50 günstig (grün), darunter „nicht
nachjagen“. Depot-Karte: Stoppabstand vom Kurs in ATR. Kachel „Ausbruch“: Volumen grün über dem 50-Tage-Schnitt, dazu
„Spanne × ATR ↑ Vorstoß mit Kraft“ (über 1) bzw. „→ verhaltener Vorstoß“. Schwellen: unsere Setzung.

## Geplantes CRV (05.11.2026)
`kern/crv.py`, auf jeder Lagekarte (Übersicht, Pop-up, Titelseite), Zeichen, kein Filter. Einstieg und Setup-Stopp wie
`depot.plan`; Ziel = erster FESTER Widerstand bzw. feste Unterstützung (`freie_bahn._fest`: Rand der Balance, in der
der Kurs steht, Rand des nächsten Knotens oder ein Hoch/Tief in einem anderen Knoten – dünne Hochs zählen nicht).
Zwei Werte: mit Setup-Stopp und mit Stopp außerhalb des Rauschens (1,5 × ATR, nur wenn der Setup-Stopp näher liegt).
Grün ab 3 : 1, gelb ab 2 : 1. Minervini-Abgleich: Stopp in % gegen den eigenen Durchschnittsgewinn (höchstens die
Hälfte, besser ein Drittel), sobald 5 geschlossene Trades in der Bilanz stehen (`depot.schliessen(tk, ausstieg)`,
`depot.bilanz()`; Ausstiegskurs beim Schließen der Position eintragen).

## Gelände als Rückgrat (05.11.2026)
`kern/gelaende.py`. Zeit (Market-Profile-Zonen) und Menge (Volumen) zusammen; die Meister (O'Neil, Minervini,
Weinstein) entscheiden, das Gelände zeigt, wo sie kämpfen. Nur Zeichen, kein Filter, keine Messung als Urteil.
- Steckbrief je Zone (30-Minuten-Kerzen): Volumen-POC, Volumen ÷ Median der 12 Monate bis zum Zonenende, Tage mit
  Verkaufs-/Kaufdruck (Schluss ±0,2 % bei höherem Volumen als am Vortag, O'Neil), Lesart Verteilung/Akkumulation
  (Unterschied ≥ 2 und ≥ 1,5 ×).
- Art: Festung (ab 1,2 ×), Wartesaal (bis 0,9 ×), Schlachtfeld (Volumenknoten ohne Zone), Niemandsland.
- Zeichen: Zone, Raum ↑/↓ bis zur nächsten Festung bzw. zum Knoten, Überhang (Festungen bis +25 %), Stellung hinter
  dem Stopp, Rücktest, Wert wandert, Dünne Spitze, Squeeze-Raum (short), Lawinenhang (Wartesaal + Verteilung),
  stille Akkumulation.
- CRV-Ziel (`gelaende.ziel`): nächste Festung (VAL long, VAH short) oder 52-Wochen-Knoten jenseits von Einstieg UND
  Kurs; ohne Gelände wie bisher `freie_bahn._fest`.
- Einbindung: Titelseite (Kachel „Gelände“ statt „Freie Bahn“, Karte „Gelände · Zonen und Volumen“ mit den letzten
  6 Zonen, Short-Seite), Lagekarte (Zeichen vor CRV und ATR), Depot-Karte (Verteilung, Dünne Spitze, Stellung des
  Stopps).
- Chart: Festung türkis kräftig gefüllt (Rahmen 2,4), Wartesaal grau gestrichelt und leer, übrige Zonen blau wie bisher; jede Zone ab 55 px Breite trägt Art und Volumen × Jahresmedian („Festung 1,44ד, „Wartesaal 0,78ד, „Zone 0,98ד); Setup-Titel in einer Kopfleiste über dem Kursbild; kein Text mehr in der Schraffur; eine schraffierte Fläche „freie Bahn ↑
  bis Festung …“ bzw. „Raum ↓ bis …“; rechts unverändert das 52-Wochen-Profil mit POC, VAH, VAL. Die alten
  Freie-Bahn-Bänder und das Knotenband sind entfallen.
- Feine Marken im Chart (05.11.2026): dünne Wendepunkte (Hoch/Tief außerhalb von Festung und Knoten) zwischen Kurs
  und nächster Festung sowie bis zu zwei alte Pivots unter dem Kurs (bis −20 %) als gestrichelte Linien ab ihrem Tag (dünn gelb, alter Pivot weiß, beide in der Legende),
  Etikett am Anfang der Linie (`freie_bahn` liefert dazu `alte_pivots`).
- Kartentisch: Gelände-Zeichen kommen über die Lagekarte aus dem nächtlichen Lauf.
- Nachtrag 05.11.2026 (Abgleich mit dem Konzept, nichts darf fehlen):
  - ◆ Volumen-POC je Zone: Lage von Zeit-POC und ◆ in % der Zonenspanne (Tabelle „Lage Zeit / ◆“); liegt ◆ mindestens 20 %
    neben dem Zeit-POC, wird er im Chart innen am rechten Zonenrand gezeichnet (rot = bestätigt Verteilung, grün = bestätigt
    Akkumulation, weiß = ohne passende Tage).
  - Lesart: aus den Tagen mit Verkaufs-/Kaufdruck; „◆ bestätigt“, wenn die Raute deutlich ist und die Richtung passt
    (Zeit oben, Geschäft unten + Verkaufsdruck = Verteilung; Geschäft oben + Kaufdruck = Akkumulation), sonst „nur Tage“.
  - „Freie Bahn ↑“ und „Lawinengefahr ↓“ (statt „Raum“): schwaches Gelände bis zur nächsten Festung bzw. zum Knoten in % und
    in ATR, mit Ort; steht der Kurs in einer alten Festung, zählt deren Wertbereich als nächste Stellung.
  - Short: „Erholung“ (Hoch der Erholung in Festung = starker Widerstand, in Wartesaal/Niemandsland = schwach);
    „Überdehnung im Gelände“ (ab 4 × ATR über dem GD50: Niemandsland darunter = Raum für einen Bruch, Festung = fängt ab).
  - Kachel „Zone“: Art, Volumen und Lesart der Zone vor den Belegen.
- Etikettenspalte (05.11.2026): rechts neben den Kerzen 180 px nur für Preis-Beschriftungen (Pivot, Kaufzone, Auslöser short,
  Ziel, Stopp A/B mit CRV, dünn, alter Pivot). Die Linien enden dort, die Etiketten stehen in Preisfolge so nah wie möglich
  an ihrer Linie, ohne sich zu überlappen. Ziel-Etikett kurz („Ziel 224,66 $ · Festung“), Einzelheiten in der Karte Gelände.

## Grüne Null – Titelseite (05.11.2026)
Leitfrage für jedes Element: Zeigt es nach O'Neil, Minervini und Weinstein die Richtung? Vier Stationen: ① Lage (darf ich
angreifen?), ② Auswahl (wer führt?), ③ Einstieg (wann?), ④ Führung (wie viel, wann raus?).
- Kopf: Name, Branche, Kurs, Abstand zum 52-Wochen-Hoch, nächster Zahlentermin (gelb innerhalb von 10 Tagen).
- 8 Kacheln: Markt (①), Phase mit Trendvorlage, Relative Stärke, Branche, Fundament mit Reaktion auf die Zahlen (②),
  Setup mit Zustand der Zone und Volumen beim Auslöser, Base-Nummer, Absorption (③).
- Chart: Kerzen, Volumen, GD50/150/200, Zonen (einheitlich blau) mit POC-Treppe, Pivot/Kaufzone bzw. Auslöser short,
  RS-Linie gegen den S&P 500, Verkaufssignal, Zahlentermine (E unter dem Volumen mit gestrichelter Linie nach oben,
  wie bei TradingView), Phasenband; Ziel (+20 %, O'Neil) und Stopps in der
  Etikettenspalte.
- Karten: Strömung in der Zone, Earnings + Fundament-Ampeln, Phase und Trend (sechs Merkmale), Warnzeichen, Lage und
  Plan, Position und Risiko.
- CRV: Ziel = Einstieg +20 % (Short −20 %) nach O'Neil (`kern/crv.py`).
- Widerstand vor dem Ziel (Weinstein, `crv.widerstand`): nächstes altes Hoch der letzten 52 Wochen (ältere sind ausgewaschen),
  das seither nicht überstiegen wurde, oder fallender GD150/GD200 zwischen Einstieg und Ziel (Short: altes Tief bzw. steigender GD);
  gelb gepunktet im Chart, als Zeile auf der Lagekarte (rot unter 10 % Abstand, gelb darüber, grün = freie Bahn).
- Entfernt (nach `_to_delete/gruene_null_titelseite`: gelaende.py, freie_bahn.py, avwap.py): Gelände
  (Festung/Wartesaal, ◆, Lawine, freie Bahn), AVWAP und AVWAP-Liste, Marken „dünn“/„alter
  Pivot“, GD10/GD20-Schalter, SIC-13-Karte, Lagekarte neben den Kacheln, Firmenbeschreibung,
  Stimmungskurve, Rudel und Rotation, Kacheln Zone/Ausbruch/Ereignis/Nächste Zahlen (in Setup, Fundament und Kopf
  aufgegangen). Grund: Sie zeigen nicht die Richtung (Messung 05.11.: Festung/Wartesaal und Strecke ohne Richtung).
- Volumenprofil 52 Wochen wieder im Chart (05.11.2026, auf Wunsch): Spalte ganz rechts mit POC (gepunktete Linie im
  Kursbild), VAH/VAL und Kursmarke; `kern/volumenprofil.py` auf `profil()` verschlankt, `erk["profil"]` in `titel.py`.
- 52-Wochen-Fenster sichtbar (05.11.2026): senkrechte Punktlinie „52 Wochen ab …“ im Chart (gilt für Profil und Widerstände; im 1-Jahres-Ausschnitt am linken Rand, ab 2 J mitten im Bild), Legende und Lagekarte nennen „letzte 52 Wochen“.
- RS-Linie gegen den Sektor-ETF wieder im Chart (05.11.2026, auf Wunsch): gestrichelt neben der RS-Linie gegen den S&P 500,
  mit Pfeil der letzten 10 Tage und Hinweiskasten der vier Bilder (Führer im Markt und Sektor usw.).
- Volumenknoten wieder im Kursbild (05.11.2026, auf Wunsch): `volumenprofil.knoten()` (ab 60 % des größten geglätteten Volumens); blasses Band ab Beginn der 52 Wochen – nächster Knoten darüber rot (Widerstand), darunter grün (Unterstützung), Kurs im Knoten türkis mit „Kurs im Knoten … (Balance)“.
- Strömung in der Zone entfällt (05.11.2026): die Zeichen, aus denen „an der Schwelle“ entsteht (Tageswerte, Tages-POC, Lage im Wertbereich) samt verlassener Zone und letzten Auslösern stehen im Hinweis der Setup-Kachel (`stroemung.druck`); Tagesspannen und Volumen (Druck ohne Richtung) und das Strömungsbild nach `_to_delete`. „Lage und Plan“ heißt „Plan“, ohne Einleitungssatz (wiederholte die Kacheln).
- Kein festes Ziel, kein CRV (05.11.2026, Micky): Gewinne laufen lassen, Stopp nachziehen. `kern/crv.py` → `kern/stopps.py`
  (alt nach `_to_delete`): Stopp A und Stopp B mit Abstand in % vom Einstieg, nächster Widerstand bzw. Halt in
  Laufrichtung (altes Hoch/Tief der letzten 52 Wochen oder fallender/steigender GD150/GD200, ohne Obergrenze),
  Minervini-Abgleich (Stopp gegen den eigenen Durchschnittsgewinn). Chart: Stopp-Linien und gelb gepunkteter Widerstand.
- CRV wieder da, ohne festes Ziel (05.11.2026, Micky): CRV 1 bis zur ersten Hürde (nächstes von: altes Hoch der letzten 52
  Wochen, fallender GD150/GD200, nächster Volumenknoten des 52-Wochen-Profils; Short gespiegelt), ohne Hürde „freie Bahn,
  CRV offen“; CRV 2 mit dem eigenen Durchschnittsgewinn ab 5 geschlossenen Trades (Minervini). Ampel grün ab 3 : 1, gelb ab
  2 : 1. Das CRV ist ein Maß, ob sich der Einsatz lohnt – kein Ausstieg: Gewinne laufen lassen, Stopp nachziehen.
  Chart: „1. Hürde … $“ gelb gepunktet, CRV an den Stopp-Etiketten; Etikettenspalte 200 px.

## Nur noch eine Watchlist, Übersicht schlanker (06.11.2026)

- Es gibt nur noch die **Watchlist** (`kern/watchlists.py`). Andere Listen in `einstellungen/watchlists.json` (die
  „Active Watchlist“ aus dem TradingView-Import) werden beim ersten Laden in die Watchlist übernommen und entfernt; alle 8
  Titel standen schon darin. Der stündliche Abgleich App → TradingView nimmt die Titel deshalb auch aus der
  TradingView-Liste „Active Watchlist“ (die Liste selbst bleibt) – so gewünscht.
- Knöpfe: ein Knopf je Titel, „☆ Auf die Watchlist“ oder „★ Auf der Watchlist“ (Klick nimmt ihn herunter); oben in der
  Übersicht „◆ Watchlist“ zum Einfügen ganzer Listen und Herausnehmen. Keine Listenwahl, kein Verschieben mehr.
- Übersicht ① Lage: die Kacheln „Marktrichtung O'Neil (Zeichen)“, „Marktbreite“ und „Neue Hochs gegen Tiefs“ sind raus.
  Breite und Hochs/Tiefs rechnen weiter in Minervinis Markt und der Moral der Truppe mit.

## VCP-Scanner: Zone und Enge (06.11.2026)

Eigener Scanner in `kern/vcp_zone.py`, Regeln im Kopf der Datei. Kein Buchchart, alles aus Tageskerzen.
- **Baustein 1 · Zone:** ruhige Phase vor dem rechten Rand. Oberkante = grobes Hoch (ZigZag 2 × ATR) ohne Schluss
  darüber, Unterkante = tiefstes Tief seitdem, 3–65 Wochen. Vorgeschichte (Schub ↑ / Absturz ↓) gehört nicht zur Zone
  und gibt den Namen: Base, Flagge (Kullamägi: Stange ≥ 30 % in ≤ 13 Wochen, Zone 1–8 Wochen, ≤ 25 % tief),
  Konsolidierung (nach Absturz); Flagge in der Zone (Minervini sieht die Base, Kullamägi die Flagge). Zone offen,
  solange der Kurs nach dem Hoch nicht zurück in die obere Hälfte kam. Abgeschlossene Zonen (Schluss über der Oberkante)
  werden mit derselben Regel rückwärts gerechnet.
- **Baustein 2 · Enge:** erste Kontraktion = linke Seite (Hoch der Zone bis Tief der Base), danach jede Welle der rechten
  Seite der Reihe nach (ZigZag 2 × ATR, die letzte am Rand ab 1 × ATR), grob halbiert (jede ≤ 70 % der vorigen), Enge =
  letzte Kontraktion ≤ 10 %, Pivot = ihr Hoch, Volumen der Enge leiser als in der ersten Kontraktion. Zone zu kurz → noch
  im Aufbau, kein Pivot, Ampel grau; Base über 33 % tief → Ampel nicht grün (O'Neil). Chart-Prüfer 14.11.2026.
  Ampel grün/gelb/rot, nichts wird gefiltert.
- **Chart (schlank):** Kerzen, GD50/150/200, GD10 · GD20 zuschaltbar, Zonen „Aktuell · Historie“, Vorgeschichte gelb,
  Fahnenstange grün, ZigZag grau, Kontraktionen mit Tiefe, Rahmen der Enge in der Ampelfarbe, Pivot; darunter Volumen
  mit 50er-Schnitt und Volumenband (Ruhe türkis bis 50/75 %, viel Volumen grün/rot nach Richtung, kräftig ab 1,5-fach),
  ganz unten die RS-Linien. Der frühere Chart liegt in `_to_delete/chart_vor_vcp_2026-11-06.py`.
- **Namen:** „Zone“ = Zone des Scanners, „Wertzone“ = Market-Profile-Zone (Kacheln, Systeme, Kartentisch).
- Probelauf über alle Titel: `python3 werkzeuge/zonen_lauf.py`.

## Seite „Rückenwind“ (09.11.2026, Konzept: KONZEPT_RUECKENWIND.md)
Dritte Seite neben Übersicht und Titelseite, getrennt von den Systemen. `kern/rueckenwind.py` (Nachtlauf-Schritt
„Rückenwind“, auch im Tischlauf) rechnet je Revier-Titel RS-Rang heute, vor 4 und vor 8 Wochen (wie rs_rang, aus
Massive), Tempo und Beschleunigung, RS-Linie am Hoch vor dem Kurs; Gruppen (Sektor, Branche, Thema) als gleich-
gewichtete Indizes mit Feld (Stärke × Tempo wie sektoren.reihen), Weg der letzten 4 Wochen und Volumen-Zufluss;
Zahlen-Ampel aus fundament.ampeln (lädt im Nachtlauf die Fundamentdaten der Titel in einer Stufe), nächster Termin und
Reaktion auf die letzten Zahlen; Logbuch der Stufen. Stufen: Entsteht (Rang 50–84, +15 in 4 Wochen, schneller als davor,
oder RS-Hoch vor Kurs), Läuft (ab 85, Tempo ≥ −5), Ermüdet (ab 80, Tempo ≤ −10 oder Beschleunigung ≤ −15 bei Tempo ≤ +5), Abfluss (vor 4 Wochen ab 70, −20).
Probelauf 09.11. (Mac, Stand 04.11., 1.802 Titel, 15 s): Entsteht 229, Läuft 257, Ermüdet 5, Abfluss 155; dreifacher
Rückenwind 23; Tempo-Quantile 10/25/50/75/90 % = −29/−9/+2,5/+13/+25 Rangpunkte.
Zahlen-Ampel aus neun Punkten (fundament.ampeln ohne „Jahresgewinn“, dafür Jahresgewinne 3 Jahre je ab +25 %, ROE ab
17 % aus TradingView, Institutionen), Reaktion auf die letzten Zahlen gedeutet (Episodic Pivot, Lücke mit Volumen,
Abverkauf trotz Überraschung) – Einzelheiten in KONZEPT_RUECKENWIND.md.
Dazu (09.11.): Zeichen „Rückenwind“ auf jeder Kartentisch-Karte und in „Befund“, Volumen-Zufluss je Titel, Steigung der
RS-Linie (4 Wochen und davor), Zufluss-Ring und stabile Gruppen (◇: führt seit 8 Wochen, Rückschlag ≤ 8 %) in der Karte.
Seite (`oberflaeche/rueckenwind_seite.py`): Strömungskarte (Sektor/Branche/Thema), Gruppen nach Geldfluss,
Karten „Dreifacher Rückenwind“, Tabellen je Stufe (Klick → Titelseite), Logbuch.

## Gesamtprüfung 06.11.2026: ein Zonenbegriff, Wertzone nur noch Zeichen „Auktion“
- Kullamägi-Breakout auf der Zone des VCP-Scanners (Konsolidierung 1–3 Wochen nach Schub, gelb bis 8, auch die
  Flagge in einer größeren Zone; Pivot = Oberkante; Ausbruch bis 4 Wochen wie bei Minervini); ★ K = grün und Kurs am Pivot.
- Market Profile entscheidet nirgends mehr mit: Chip „Auktion: …“ auf der Lagekarte, Spalte „Befund“ (Scanner · Auktion)
  in der Liste, Zeile im Lagebild, Nachzieh-Hinweis VAL/VAH nach dem Kauf. Kleinchart zeigt Zone und Pivot des Scanners,
  die Zeile unter den Chips den Befund des Scanners. Kein Plan ohne Setup der Systeme (vorher Wertzonen-Plan).
- Warnzeichen auf der Scanner-Base: Korrektur zum Markt (mehr als 2-fach S&P 500) mit Gruppenvergleich, Frühwarnung
  (Schluss unter dem Tief der Zone bis gestern); „Reset beobachten“ am Pivot der Systeme. Selbstprüfung der alten
  Wertzonen-Base, Absorption und Strömung sind raus (`_to_delete`).
- Kartentisch rechnet auch Titel ohne 30-Minuten-Kerzen (vorher fielen sie heraus).
- Massive: Nachtlauf holt nach US-Schluss (New York ab 16:30) auch den heutigen Tag – RS-Rang, Führer-Rang, Marktbreite
  und Rudel hingen vorher einen Tag hinterher.

## IBD-Basenzählung auf Scanner-Zonen (06.11.2026)
`kern/basen.py` zählt die Basen auf den abgeschlossenen Zonen des VCP-Scanners (statt der Wertzonen; `basenzahl` und
die Historie der Wertzonen auf der Titelseite sind weg – die Titelseite rechnet rund 2,7 s weniger). Regeln wie bisher:
Beginn = später von Phase-2-Beginn und letztem Markttief nach Korrektur ab 15 %; Basen ab 3 Wochen und Flaggen ab 1 Woche
zählen; neue Nummer erst 20 % über der Oberkante der zuletzt gezählten (sonst Base auf Base); die laufende Base
(Minervinis Zone) zählt mit. Kachel „Base“: 🟢 Nr. 1–2, 🟡 Nr. 3, 🔴 ab Nr. 4, dazu Tiefe gegen den S&P 500 und die
Bilanz (gelungen = +20 % vor −8 %). Im Chart unter „Historie“ steht die Nummer am Ausbruchspfeil.

## Ausbruch mit Volumen und Fehlausbruch (06.11.2026)
Am Ausbruchstag ist eine Zone fertig und verschwände – mitsamt Setup und Kaufzone. `vcp_zone.ausbruch()` schaut bis 4
Wochen zurück: Schluss über dem Pivot der Zone vom Vortag (oder der Flagge darin). Zone, Enge, Pivot und Stopp von damals
gelten weiter (Minervini, Reihen VCP und Flagge, Chart) – bis 4 Wochen oder bis sich darüber eine neue fertige Zone
gebildet hat. Bis +5 % über dem Pivot = Kaufzone, auch beim Rücksetzer auf den Pivot; darüber ausgedehnt.
Zeichen, kein Muss: 🟢 Volumen am Ausbruchstag über dem 50-Tage-Schnitt, 🟡 darunter (mit Faktor). Schließt der Kurs
wieder unter dem Pivot: 🔴 Fehlausbruch – Zone und Pivot bleiben, kein Kauf, bis er wieder darüber schließt (dann neuer
Ausbruch mit eigenem Volumen). Steht auf jeder Karte, in der Liste und im Plan.

## Short: Ermüdung nach Überdehnung (06.11.2026, statt Parabolic Short)
Die Flagge des VCP-Scanners, im Ausgang gespiegelt: Die Truppe ist weit vorgestoßen, gräbt sich ein, dann bricht die
Stellung nach hinten weg (`vcp_zone.ermuedung`, im System Kullamägi als `ermuedung`).
- Fahnenstange ab 30 % in höchstens 13 Wochen · Flagge 1–8 Wochen, höchstens 25 % tief (auch als Flagge in einer Base)
- Auslöser: Schluss unter der Unterkante, in den letzten 5 Handelstagen (Zone so, wie sie am Vortag stand)
- Stopp über dem Hoch des Auslösetags (Kullamägi: Stopp am Tageshoch); ist er erreicht, fällt das Setup weg
- Zeichen (kein Muss): Volumen am Bruch über dem 50-Tage-Schnitt
- Ampel: grün = Kurs schließt noch unter der Unterkante, gelb = zurück in der Flagge
- Kartentisch-Reihe „Ermüdung nach Überdehnung · Short“, Lagekarte rot, Barometer zählt die grünen.
- Parabolic Short samt Suche im ganzen US-Markt liegt in `_to_delete/`. Probelauf 06.11.: 40 Treffer unter 1.913 Titeln.

## Schrank: Titelseiten nach Änderungen neu ablegen (06.11.2026)
Nacht- und Tischlauf legen jede Titelseite des Kartentischs fertig ab (`daten/titelseiten`); ein Klick holt sie in
Hundertstelsekunden. Ist das Programm oder das Depot jünger, gilt die Ablage nicht mehr (nie eine Seite mit alten Regeln).
Dann startet die App einmal je Stand `werkzeuge/nachtlauf.py --seiten`: baut die veralteten Seiten im Hintergrund neu
(Watchlist zuerst) und schreibt Lagekarte und Kacheln in den Tisch zurück – mit den vorhandenen Kursen, ohne neue
Reihen. Fortschritt unter dem Knopf „Kartentisch neu rechnen“; startet ein Nacht- oder Tischlauf, hört er auf.
Protokoll `daten/nachtlauf/seiten_lauf.json`.

## Knopf „Kartentisch neu rechnen“ (06.11.2026)

Oben in der Übersicht. Rechnet Ränge (RS, Führer), den Kartentisch mit beiden Systemen und die Lage
neu – mit den Kursen des letzten Nachtlaufs, ohne Download (`werkzeuge/nachtlauf.py --tisch`). Läuft als eigener
Prozess auf dem Server, eigenes Protokoll `daten/nachtlauf/tisch_lauf.json` (Log `tisch_lauf.log`), die Datenampel
bleibt beim Nachtlauf. Gesperrt, solange der Nachtlauf oder ein Tischlauf läuft. Ist er fertig, lädt die Seite neu.
Achtung: Neuer Code aus GitHub startet die App neu und bricht einen laufenden Tischlauf ab.

## Übersicht als Trichter (05.11.2026)
Die Übersicht ist der breite Rand des Trichters, die Titelseite der schmale Hals. Inhalt unverändert, nur geordnet nach
Stationen mit ihrer Frage und einer Sprungleiste unter dem Kopf (`gestaltung.STATIONEN`, `station()`, `sprungleiste()`):
① Lage (Markt-Ampel, Marktbreite, neue Hochs gegen Tiefs, Moral der Truppe, Wirtschaftswetter; Stimmungskurve
aufklappbar) · ② Front (Frontkarte, Übergänge, Lagebild nach Sektoren) · ③ Auswahl (Setups, Ausbruchsfelder,
★ Spitze, Meine Watchlists, Weitere, Frühaufklärung, Short) · ④ Termine (Neu seit gestern, Earnings 14 Tage) ·
⑤ Eigene Truppe (Depotleiste) · Anhang (Instrumente, aufklappbar). Lagekarte mit 7 Ampelpunkten (dazu „Angebot“).

## Zwei Systeme: Minervini und Kullamägi (05.11.2026)
Micky modelliert zwei getrennte Systeme. Jedes hat eigene Regeln für „grün“, Markt, Stopp und Ausstieg. O'Neil und
Weinstein bleiben nur als Zeichen (Verteilungstage, Basennummer, CAN SLIM S/I, Phase); Weinsteins Stufe 2 lebt in
Minervinis Trendvorlage weiter. Short nur noch als Ermüdung nach Überdehnung (seit 06.11.2026, vorher Parabolic Short); die bisherigen Short-Einstiege
(Phase 3/4, gescheiterte Erholung, Nackenlinie, O'Neils frühere Führer) liegen in `_to_delete/zwei_systeme`.
Die Market-Profile-Zonen bleiben das gemeinsame Werkzeug, das Konsolidierung und Base erkennt.

- `kern/system_minervini.py` – grün = Trendvorlage 7 Punkte + RS ab 70 (8. Punkt) + Zahlen wachsen (Gewinn und Umsatz
  nicht rot) + reife Base des VCP-Scanners (Base oder Flagge, fertig, höchstens 50 % tief) + Enge aus Baustein 2 (grün
  oder teilweise). Gelb = eine Regel fehlt. Pivot = Hoch der letzten Kontraktion, Stopp unter ihrem Tief, höchstens 8 %.
  Seit 06.11.2026 kommen Base, Enge, Pivot und Stopp aus dem Scanner statt aus Wertzone und Absorption; ★ Spitze M =
  grün und Kurs −5 % bis +5 % um den Pivot.
- `kern/system_kullamaegi.py` – Breakout (Führer = oberste 2 % nach 1/3/6 Monaten, `kern/fuehrer_rang.py`, plus
  Konsolidierung 1–3 Wochen nach einem Schub), Episodic Pivot (Tagesgewinn ab 10 %, Eröffnung über dem Vortageshoch,
  Volumen ab 3-fach – Micky; 10-fach = ideal; grün mit Nachricht/Zahlen; in den letzten 10 Tagen, Kurs hält das Tief),
  Short: Ermüdung nach Überdehnung (siehe unten).
  Stopp am Tagestief, kein Trade weiter als eine Tagesspanne (ADTR 20 Tage). Ausstieg: Teilgewinn Tag 3–5, Einstand,
  Rest bis Schluss unter 10er/20er. Quelle: Interview mit Jack Schwager (Market Wizards).
- Markt: seit 12.11.2026 eine Ampel nach O'Neil in `kern/marktklima.py` (siehe „Marktklima nach O'Neil“ unten). Kein Filter.
- Titelseite: acht Kacheln – Markt, Trend, Stärke, Fundament, Setup, Enge mit je einer M- und einer K-Ampel
  (`gestaltung.kachel2`), Branche und Base als Zeichen. Karte „Plan“ je System mit Regeln, Marken, Stopp, Ausstieg.
- Lagekarte: Setup je System oben rechts, acht geteilte Punkte (links M, rechts K, `gestaltung.punkt2`).
- Kartentisch-Reihen: ★ Spitze M, Weitere M, Episodic Pivot K, Breakout K, Ermüdung (short), Ausbruchsfelder (nur nach
  oben), Frühaufklärung (nur nach oben). Watchlists nach ★ Spitze M.
- Depot: Feld „System“ je Position (M/K) bestimmt die Zeichen nach dem Kauf; kein festes Gewinnziel mehr.
- Nachtlauf: Schritt „RS-Rang, Führer-Rang“ vor dem Kartentisch; „Lage“ läuft nach dem Kartentisch.
- Gemessen am 05.11.2026 (700 Revier-Titel, Kurse bis 04.11.): Minervini 26 grün / 57 gelb, Kullamägi 21 grün / 41 gelb.


## Frühlauf und Datenstand-Wache (12.11.2026)

- Massive gibt im kostenlosen Plan einen Handelstag erst nach Mitternacht New York frei (6 Uhr Berlin; Massive
  Knowledge Base). Der Abendlauf um 22:45 rechnete deshalb Rückenwind, RS-Rang und Führer-Rang mit dem Vortag,
  Charts, Kartentisch und Akten (Yahoo) aber mit dem neuen Tag. Die Notiz vom 06.11. („ohne Tag Verzug“) galt nicht.
- Seitdem: Frühlauf Di–Sa 6:05 Uhr (`werkzeuge/server/nachtlauf.timer`; `aktualisieren.sh` übernimmt den Zeitplan
  selbst). Massive-Schritt wartet bis 30 Minuten, bis der Tag freigegeben ist. Zweiter Anlauf der Konferenz 30 Minuten
  nach dem ersten, Massive-Durchgänge für Lücken bis 11:30 Uhr, Revier-Pflege samstags.
- Datenstand-Wache (`nachtlauf.datenstand()`): Kurstag von Massive, Yahoo, Rückenwind, RS-Rang und Führer-Rang im
  Protokoll; eine Zeile oben auf jeder Seite (grün = alle gleich, gelb = gleich, aber älter als der letzte Handelstag,
  rot = verschiedene Tage). Der Stab bekommt den Datenstand und nennt Abweichungen zuerst.

## Konferenzraum als Lagekarte (12.11.2026)

Oben steht die Lagekarte, darunter zugeklappt Wortlaut, Akten, Feldhandbuch und Technik.
- **Lagebrett:** Haltung des Stabs (angreifen · klein tasten · abwarten · verteidigen), Markt M/K, Pendel, Datenstand.
- **Angriffsziele:** Rang des Strategen, Setup und Einstieg vom Code, Stopp, Kernsatz (≤ 12 Wörter), Einwand.
- **Konsens-Matrix:** links fünf feste Ampeln des Codes (`stab.FESTE_REGELN`: Setup, Einstieg, Geld, Zahlen, Termin), rechts das Urteil je Stratege (Feld `urteile` der Meldung).
- **Drei Spalten:** am Auslöser (Setup grün, bis 5 % vor dem Einstieg), Gefahren, Bilanz der letzten Ziele (✓/✗).
- **Alle Akten:** warum jeder Titel beim Stab liegt, mit seinen festen Ampeln.

Regel 13 der Dienstanweisung: Die festen Ampeln sind gesetzt, der Stab färbt sie nicht um und urteilt nur über seine eigene Frage. Die Konferenz speichert `tafel`, `brett` und `bilanz`. Bei älteren Konferenzen rechnet die Lagekarte die festen Ampeln mit dem heutigen Stand.

## Drei Seiten (12.11.2026)

- **Rückenwind (Lagezentrum):** ① Lage, ② Strömung mit der Wetterkarte und direkt darunter der Lagekarte nach Sektoren, ③ Eigene Truppe.
- **Setups (Aufklärung und Filter):**
  - ① Auswahl für den Stab: Trichter vom Revier zum Stab und die Akten mit Grund. Gerechnet von `stab.auswahl()`, derselben Funktion, die die Konferenz nutzt.
  - ② Stellung: grüne Setups, die Reihen und die Watchlist, jede Karte mit 🎯 oder dem Grund, warum nicht.
  - ③ Rückenwind je Titel: dreifacher Rückenwind, Titel nach Stufe, Logbuch.
  - ④ Termine.
- **Konferenzraum (Beschlusszentrale):** die Lagekarte des Stabs.

Akten des Stabs: Depot plus einsatzbereite Setups (grün und am Auslöser oder in der Kaufzone), je Reihe 2 Plätze vorab, höchstens 30.

## Zahlen-Reaktion (12.11.2026)

Neue Reihe im Kartentisch, long und short (`kern/zahlen_reaktion.py`). Vorrang: EP → Zahlen-Reaktion → Ermüdung → ★ Spitze M → …
- **Voraussetzung:** Der Kurs reagiert am Reaktionstag mit mindestens 3 % (Short −3 %) auf die Zahlen, in den letzten 20 Handelstagen.
- **Grün, wenn alle vier Regeln erfüllt sind:**
  - Volumen über dem 50-Tage-Schnitt
  - Schluss im oberen (Short: unteren) Drittel
  - Tief (Short: Hoch) und AVWAP des Reaktionstags gehalten
  - Kurs über (Short: unter) GD50
- **Einstieg:** am AVWAP ab dem Reaktionstag. Im Chart heißt der Anker „Zahlentag“ und ist bei diesen Titeln vorgewählt.
- **Stopp in der Akte:** beim Short 1,5 ATR über dem Einstieg (vorher darunter, auch bei der Ermüdung).

## Tägliche Sicherung (12.11.2026)

Jeden Tag um 12:10 (nach dem Frühlauf) sichert der Server die Daten mit Geschichte in den GitHub-Zweig `daten`, Ordner `sicherung/` (`werkzeuge/server/sicherung.sh`, Zeitplan `sicherung.timer`). `aktualisieren.sh` richtet beides selbst ein.
- **Gesichert:** Konferenzen samt Kostenbuch und Fragen, Logbuch des Rückenwinds, Protokoll des Laufs, Depot, Watchlists, Revier.
- **Nie gesichert:** Schlüssel.
- **Nicht gesichert:** Kartentische (rund 12 MB je Tag, werden neu gerechnet) und Kurse.
- **Wiederherstellen:** `sicherung/` aus dem Zweig `daten` holen und unter denselben Pfaden nach `/opt/invest-cockpit` kopieren.

## Verschlankt (12.11.2026)

- **Titelseite:** Die Karten „Plan“ und „Warnzeichen“ sind weg. Was nur dort stand, steht jetzt an anderer Stelle:
  - „Es fehlt: …“ in der Setup-Kachel
  - der Plan je System (Einstieg, Kaufzone, Stopp, Ausstiegsregel des Meisters, Marken zur Trendvorlage, Zahlen-Reaktion) als Zeilen unter dem Chart
  - echte Warnungen (Daten gestört, Klimax, Übernahme, rote Datenampel) als roter Hinweis im Kopf, nur wenn es eine gibt
- **Entfernt:**
  - Weinsteins Frühwarnung (`kern/fruehwarnung.py`), `phase.phase_heute` und die Korrektur der Gruppe
  - die Selbstprüfung mit Basenhistorie (`werkzeuge/massenlauf.py`, `erkennung.basen_historie`/`selbstpruefung`)
  - tote Funktionen (`lage.marktampel`, `sektoren.stark_anteil`)

## Ein eigenes System (12.11.2026)

Statt „Minervini“ und „Kullamägi“ gibt es sieben Setups: Base-Ausbruch (★ in der Kaufzone · weiter weg oder eine Regel fehlt · nur Muster), Flagge, Momentum-Ausbruch, Sprung (EP), Zahlen-Reaktion, Ermüdung (Short) und Bärenflagge (Short).
- **Eine Entscheidung für alle:** `kartentisch.setup_feststellen` bestimmt für Kartentisch und Titelseite dasselbe eine Setup.
  - Vorrang: Sprung → Zahlen-Reaktion → Ermüdung/Bärenflagge → Base-Ausbruch ★ → Flagge → Momentum-Ausbruch → Base-Ausbruch → nur Muster.
  - `auch` nennt die übrigen Setups des Titels.
- **Titelseite:** jede Kachel mit einer Ampel für das Setup des Titels (`gestaltung.SYSTEM` = aus wessen Regeln; `LEHRER` in kartentisch).
  - Markt: nur Indizes und Hochs/Tiefs.
  - Short: Markt und Stärke gespiegelt.
  - Momentum-Setups: Trend nach dem GD50.
  - Zahlen-Reaktion: Enge = hält den AVWAP.
- **Inneres:** Die Schlüssel der Reihen bleiben (m_spitze, k_breakout, …). Neu ist `k_baerenflagge`. „nur Muster“ (`vcp`) geht nicht in die Konferenz.

## Rangfolge der Auswahl für den Stab (12.11.2026)

Von den einsatzbereiten Titeln bekommen die besten 30 eine Akte; das Depot kommt immer dazu, und jede Reihe hat 2 Plätze vorab. Die Rangfolge (`stab.auswahl`, Text in `stab.RANG_TEXT`):

1. Zahlen in höchstens 7 Tagen nach hinten.
2. Volltreffer.
3. ★ in der Kaufzone bzw. Short-Zone.
4. Geld in Richtung des Setups (Short gespiegelt: Abfluss zählt).
5. RS-Rang (Short gespiegelt: der schwächere zuerst).

Die Watchlist gibt keinen Vorteil. Die Auswahl ist neutral, damit kein schwächerer Titel vor einem stärkeren steht, nur weil er auf der Liste ist. Vorher zählte die Watchlist vor Geld und RS, die Kaufzone und der Termin zählten nicht, und bei Shorts wurde Geld nicht gespiegelt.

Darunter steht der eigene Kasten „◆ Deine Watchlist · einsatzbereit“. Er enthält nur deine einsatzbereiten Titel, in derselben Rangfolge, mit 🎯 für „beim Stab“, sonst mit dem Grund. Alle übrigen Watchlist-Titel zeigt ② Stellung.

Die Seite Setups zeigt unter der Tabelle „Knapp draußen“: die ersten 10 einsatzbereiten Titel ohne Platz, in derselben Rangfolge und mit denselben Merkmalen. So sieht man die Grenze auf einen Blick.

Die Termin-Ampel liest das Datum jetzt aus dem Text der Kachel. Vorher stand dort „in n Tagen“ als Wert, und die Ampel blieb grau. Eine alte Meldung des Knopfs „Kartentisch neu rechnen“ verschwindet, sobald ein späterer Nachtlauf gelaufen ist.

## Schnellsuche entfernt (12.11.2026)

Die Schnellsuche „die Besten auf einen Blick“ auf der Seite Setups ist weg. Ihre Anführer waren genau die ersten 25 Zeilen der Liste „Läuft“ in „Titel nach Stufe“, ihre Verfolger deckten sich größtenteils mit „Entsteht“. Ein Setup prüfte sie nicht.

Der Stab bekommt Anführer und Verfolger weiter (`rueckenwind.anfuehrer_verfolger`, je 15 Titel). Die Verfolger kommen jetzt nur noch aus dem Band von „Entsteht“ (Rang 50 bis unter 85). Vorher gab es keine Untergrenze, und eine Erholung von Rang 5 auf Rang 30 stand ganz oben. Der alte Code liegt auf dem Mac in `_to_delete/schnellsuche_entfernt_2026-11-12.py`.

## Marktklima nach O'Neil (12.11.2026)

Die eine Markt-Ampel (Rückenwind ① Lage, Titelseite, Konferenzraum, Stab) bestimmt jetzt O'Neil, das „M“ in CAN SLIM (`kern/marktklima.py`, gerechnet in `kern/marktrichtung.py`):

| Ampel | Zustand | Bedingung |
|---|---|---|
| grün | Bestätigter Aufwärtstrend | nach einem Follow-Through-Day, höchstens 3 Distributionstage in 5 Wochen |
| gelb | Aufwärtstrend unter Druck | 4 Distributionstage in einem Index |
| rot | Korrektur | 5 Distributionstage und Bruch der Wertzone bzw. des Tiefs vor dem Follow-Through-Day |

Darunter steht eine Zeichenzeile ohne Urteil: S&P 500 und Nasdaq gegen GD50 und GD200 sowie neue Hochs gegen Tiefs.

Vorher war genau das die Ampel, also eine eigene Faustregel mit dem falschen Etikett „Minervini“. Davor gab es zusätzlich Kullamägis 10/20-Regel.

`kern/markt_systeme.py` ist entfernt. Die Akten tragen jetzt `regeln_base` und `regeln_momentum` statt `setup_minervini` und `setup_kullamaegi`. Die Dienstanweisung verbietet „Minervini grün“ und „Kullamägi rot“. Die Meister werden nur noch als Quelle einer Regel genannt.

## Einstieg und Stopp aus dem einen Setup (12.11.2026)

`depot.einstieg_setup(su, m, k, zr, kurs)` legt Seite und Einstieg nach dem Setup des Titels fest:

| Setup | Seite | Einstieg |
|---|---|---|
| Sprung (EP) | long | Hoch des Sprungtags |
| Zahlen-Reaktion | Seite der Reaktion | AVWAP ab dem Reaktionstag |
| Ermüdung, Bärenflagge | short | Unterkante |
| Base-Ausbruch | long | Pivot der Base |
| Momentum-Ausbruch | long | Pivot der Konsolidierung |
| Flagge, nur Muster | long | Pivot des Scanners |

Diesen Einstieg nutzen Chart, Plan (`depot.plan`), Lagekarte, Kartentisch-Abstand und Stab. Der Stopp liegt 1,5 ATR darunter, beim Short darüber.

Vorher nahm der Chart immer die alte Kette Sprung → Base → Momentum. Bei HWM (Zahlen-Reaktion long, Kurs 224 $) zeichnete er so den Pivot einer alten Base und einen Stopp von 247,93 $ über dem Kurs. Der Momentum-Ausbruch maß seinen Abstand zum Pivot der Base.

Jede Planzeile unter dem Chart trägt jetzt den Stopp ihres eigenen Einstiegs. Der Chart zeichnet nur das aktive Setup. Ein Short gilt als gebrochen, wenn der Kurs über seinem Stopp steht.

Der AVWAP-Text der Zahlen-Reaktion sagt jetzt „einmal gebrochen, Kurs wieder darüber“ statt „bricht den AVWAP“.

## Tagesbefehl aufs Handy (12.11.2026)

Nach jeder gelungenen Konferenz schickt `nachtlauf._tagesbefehl_melden` die Kurzfassung (`stab.kurzfassung`) über ntfy. Das gilt für den Frühlauf (gleich nach der Konferenz, vor dem Schrank, also gegen 7 Uhr), für den zweiten Anlauf und für den Knopf „Konferenz jetzt einberufen“.

Die Meldung enthält:
- als Titel „Tagesbefehl TT.MM. · Haltung“
- die Lage in Kurzform
- Markt (O'Neil) und Pendel mit Ampel
- einen Hinweis, wenn der Datenstand nicht stimmt
- bis zu 6 Ziele mit Ampel, Richtung und Kernsatz
- bis zu 3 Gefahren

Ein Tipp auf die Meldung öffnet den Konferenzraum (`meldung.APP`, Kopfzeile „Click“). Ohne eingerichtete ntfy-App kommt nichts an, die App läuft trotzdem weiter.

## Wachen im Frühlauf (12.11.2026)

`kern/wachen.py` läuft als eigener Schritt nach dem Schrank und schreibt `daten/nachtlauf/wachen.json`. Die vier Wachen:

1. **Gleichlauf:** Kartentisch, abgelegte Titelseite (nur gültige Seiten) und Tafel des Stabs nennen dasselbe Setup, dieselbe Seite und denselben Einstieg (±0,5 %). Der Stopp liegt beim Long unter, beim Short über dem Einstieg.
2. **Plausibilität:** Die Reihe stimmt mit der Seite der Lagekarte überein. Ein grünes Setup hat eine Reihe. Akten liegen in der Zone ihres Setups. Kein vergangener Zahlentermin zählt noch.
3. **Gegenprobe:** 10 Akten (Zufall mit dem Tag als Startwert) gegen TradingView: Schluss ±0,5 %, GD50 ±1 %, Zahlentermin ±1 Tag.
4. **Stab als Prüfer:** Schreibt ein Stratege „Datenfehler“, „Widerspruch“, „doppelt“ oder Ähnliches, wird das ein Hinweis.

Rot heißt Fehler der App: Der Schritt wird rot, und eine Warnung geht aufs Handy. Gelb sind Hinweise: Die Kopfzeile wird gelb (seit 17.11.2026 ohne Meldung aufs Handy). Die Liste steht unter der Datenstand-Zeile jeder Seite („Wachen vom …“).

Der erste Probelauf auf dem Mac hat die alten Seiten aus dem Schrank sofort erkannt (UNP, BNY, MA: Einstieg im Chart ≠ Kartentisch).

## Eine Quelle je Tatsache (12.11.2026, nach dem unabhängigen Prüf-Agenten)

| Tatsache | eine Quelle | vorher daneben |
|---|---|---|
| Einstieg und Seite | `depot.einstieg_setup`, im Kartentisch als `einstieg` {seite, wert, quelle} gespeichert; `pivot_scanner` für Flagge/VCP | Lagekarte (alte Pivot-Kette), `depot.plan` (eigene Kette), `depot.einstieg_long` (entfernt), Stab (Kurs von heute ÷ alter Abstand) |
| Stopp | Einstieg ∓ 1,5 ATR (`depot.plan`) | Planzeilen mit dem Stopp des Charts |
| Plan unter dem Chart | aktive Zeile aus dem Einstieg des Setups, übrige als „Auch“ | erste Zeile nach `k.haupt` (Sprung + Momentum: falsches Setup), Short-Zeile fehlte bei gelbem Breakout |
| RS-Rang | `rs_rang.rang` liest den Rang aus Rückenwind (gleicher Handelstag), sonst die Revier-Rechnung | zwei Ränge (Stärke-Kachel „RS 68“ neben „RS-Rang 72“) |
| Zahlen nah | `gestaltung.termin_ampel`: bis 7 Tage rot, bis 14 gelb | 7/10/14 an fünf Stellen |
| Termin | `stab.termin_datum`: ein vergangener Rückenwind-Termin fällt auf die Kachel zurück | „unbekannt“ |
| Zahlen der Titel | Frühlauf-Schritt „Zahlen nach den Terminen neu laden“ (`quellen.nach_terminen`) vor Rückenwind und Kartentisch | Kartentisch las alte Zahlen, die Titelseite frische |
| Geld beim Short | Kachel gespiegelt wie die feste Ampel | Kachel zeigte die Long-Sicht |
| Volltreffer | nur mit Long-Setup | auch Ermüdung/Bärenflagge |
| Einstiegs-Ampel | ungerundeter Abstand (`abstand_roh`) | gerundet (−0,04 % → grün) |

Dazu sind Texte angeglichen:
- Flagge: grün ab 5 % unter der Oberkante.
- Ermüdung: Stopp 1,5 ATR, das Setup erlischt über dem Hoch des Auslösetags.
- Zufluss: 50 Handelstage.
- Geld gelb: auch „zwei vorne, eine schwächelt“.
- „Entsteht“: zweiter Weg über das RS-Hoch.
- Stab: Einstieg je Setup, Short-Zone.
- Ausstiegstexte ohne den alten Tagestief-Stopp.

## Neuer Stab, Lehre von Stärke und Schwäche, Kreislaufbild (13.11.2026)

Micky: „Was der Stab da macht, ist schwach.“ Das Konzept steht im Konzeptdokument (Abschnitte „Lehre von Stärke und Schwäche“, „Aufträge der Missionen im Wortlaut“).

**Messungen (`kern/zeichen.py`, Frühlauf im Kartentisch, gespeichert in `daten/kreislauf/<stand>.json`):**
- Dow-Struktur der Schwungpunkte auf Tag (n = 5) und Woche (n = 2). Signale: Schluss unter dem letzten höheren Tief, erstes höheres Tief nach tieferen Hochs und Tiefs (und gespiegelt).
- Einquetschung: steigende Tiefs unter flacher Oberkante, dazu das Spiegelbild.
- Akkumulation und Distribution: 20 Tage, Saldo ±3, Pocket Pivot in 5 Tagen über GD10 und GD50.
- Stärke in der Schwäche, gemessen im Korrekturfenster (Regeln seit dem Abschnitt „Blinde Flecken“ unten).
- Reaktion auf Zahlen: Überraschung gegen Kursreaktion, Lücke gekauft/verkauft, Zahlen verworfen (siehe unten).
- Wanderung der Wertzone: POC 5 gegen 5 Tage, ±3 %, nur in der Seitwärtszone (Schluss in 10 Tagen höchstens ±4 %); aus derselben Market-Profile-Analyse wie Karte und Chart (`erkennung.mp_von`, Rohdaten-Speicher auf 50 Titel begrenzt).
- Kreislauf: die Phase nach Weinstein (phase.py), dazu der Wechsel, der sich abzeichnet („4 → 1“), ein fester Satz und 52 Wochenschlüsse mit Phase je Woche.

**Fehlausbruch neu (`vcp_zone.ausbruch`):**
- Fehlausbruch: Schluss unter dem Tief des Ausbruchstags oder mehr als 3 % unter dem Pivot.
- Rücktest: Schluss knapp unter dem Pivot.
- Beide sind nicht einsatzbereit (Kartentisch: grün und ★ aus) und bleiben unter Beobachtung.
- Ein Schluss über dem Pivot nach einem Fehlausbruch zählt als neuer Ausbruch.

**Kreislaufbild (`oberflaeche/kreislaufbild.py`):**
- Darstellung: echter Wochenverlauf eines Jahres, nach Phasen gefärbt (Farben seit dem Abschnitt „Blinde Flecken“ unten), dazu „hier steht er“, die vier Phasen als Leiste sowie die Zeichen der Stärke und Schwäche.
- Titelseite: das große Bild unter den Kacheln, über dem Chart, mit dem Satz des Stabs (`stab.satz_zu`).
- Konferenzraum: das große Bild in jeder Chance.
- Karten (Setups, dreifacher Rückenwind) und die Tabelle „Diese Titel liest der Stab“: Mini-Kurve mit Phasenwort.
- Tabellen (Stufen): einfarbige Kurve (LineChartColumn) und Phasenwort mit Farbpunkt.

**Stab mit acht Missionen (`kern/stab.py`):**
- Missionen: Lage, Aufklärung (Web-Suche, Depot plus 10 Titel), Jäger, Operationsplaner, Gegenspieler, Truppenführung (nur mit Depot), Kriegsgeschichte, Feldherr.
- Gemeinsame Dienstanweisung mit unserer Lehre und 8 Regeln (Regel 8, 13.11.2026: die Haltung der Lage gilt für den Markt, nicht für den Titel – Stärke in der Schwäche wird nie wegen des Marktes verworfen; der Code nennt jeden solchen Titel im Befehl unter „Stärke in der Schwäche“ und meldet als Wache, wenn der Stab ihn übergeht). Die Meister sind keine Rollen mehr, ihre Regeln stehen als Lehrstellen bei der Mission, die sie braucht.
- Wachen im Code:
  - Ein Auftrag geht nur auf eine Akte mit grünem Setup, Einstieg nicht rot; höchstens 8 Aufträge (Micky 13.11.: an starken Tagen gibt es mehr als 5 gute Chancen).
  - Jede Akte wird eingeordnet (beobachten/verworfen).
  - Eine Chance entsteht nur aus einem Auftrag, den der Gegenspieler nicht gekippt hat.
- Die Wache „Form des Stabs“ im Frühlauf prüft dasselbe noch einmal.
- Handy: zuerst „Hey Micky“, dann die Chancen mit Phase, Anwärter, Leitfrage und Markt; verworfene Titel stehen nicht darin.
- Konferenzen vor dem 13.11. werden weiter angezeigt.
- Entfernter Code liegt in `_to_delete/stab_strategen_entfernt_2026-11-13.py`.
- Offen gelassen von Micky:
  - Breite der Aufklärung (Micky 13.11.): das Depot immer, dazu 10 Titel – 6 Akten und 4 Anwärter in Rangfolge; freie Plätze der einen Gruppe füllt die andere. (Erst 20; die Probekonferenz kostete 2,94 $, davon geschätzt rund 2,50 $ für die Web-Suchen.)
  - Budget: Annahme etwa wie bisher; jede Konferenz misst ihre Kosten (`kosten_usd`).
- Anwärter (Micky 13.11.): Titel ohne Akte mit frühen Zeichen – seit dem Abschnitt „Blinde Flecken“ beide Seiten (20 long, 10 short) und Depotwarnungen.
- Wache Zahlentermine (Micky 13.11.): Weichen Yahoo und TradingView mehr als 1 Tag ab, ist das nur gelb, wenn einer der beiden Termine in den nächsten 14 Tagen liegt; sonst grauer, stiller Hinweis (färbt Kopfzeile und Handy nicht).
- Divergenz (Micky 13.11., HWM): höheres Tief gegen den Index als Zeichen der Stärke in der Schwäche – der Titel fiel mindestens 10 % bis zu seinem Tief, der Index macht mindestens 3 Handelstage später ein um mindestens 0,5 % tieferes Tief, der Titel bleibt dabei 5 % über seinem Tief und liegt seit seinem Tief 10 Punkte vor dem Index (`zeichen.divergenz`). HWM wird damit „4 → 1“. Seit dem Abschnitt „Blinde Flecken“: Mindestfall max(5 %, 3 ATR, Fall des Index), zählt als Struktur und RS.
- Kreislaufbild hell (Micky 13.11.): Zeichnet sich ein Wechsel ab, verblasst die laufende Phase ab dem ersten Zeichen (hell in ihrer eigenen Farbe: 4 → 1 hellrot, 2 → 3 hellgrün, 1 → 2/4 hell-blaugrau, 3 → 2/4 hell-ambergrau) (`kreislaufbild.HELL`, `wechsel_wochen` im Kreislauf); ab dem letzten Schwungtief bzw. dem eigenen Tief seit dem Indexhoch (zur Stärke) oder dem letzten Schwunghoch (zur Schwäche).


## Blinde Flecken entfernt (13.11.2026)

Micky: „Unsere ganze App steckt wahrscheinlich noch voll dieser blinden Flecken. Diese müssen rigoros entfernt werden.“ Grundlage ist die Prüfliste im Konzeptdokument (Abschnitt „Blinde Flecken“); umgesetzt wurden alle A- und B-Punkte außer der Korrektur ab −8 % (Micky: „nur Distributionstage“). Gemessen am Mac über 1.907 Titel (Daten bis 04.11.2026).

**Zeichen (`kern/zeichen.py`):**
- Jedes Zeichen hat Seite, Art (Struktur, Volumen, RS, Ereignis) und Gewicht. Ein Wechsel der Phase zeichnet sich nur ab, wenn ein Zeichen der Struktur und eines aus Volumen oder RS auf derselben Seite stehen und die Seite mindestens Gewicht 4 hat und doppelt so schwer wiegt wie die andere. Der Satz nennt die stärksten Zeichen zuerst.
- Korrekturfenster: Stärke in der Schwäche bleibt 45 Handelstage nach dem Tief des Index stehen („in der Korrektur vom … bis …“) – vorher verschwand sie mit dem Follow-Through-Day.
- Hält: am Indextief (Index mindestens 3 % gefallen) mindestens so weit im Plus wie der Index im Minus und 15 Punkte vor ihm (mit 10 Punkten schlug jeder zweite Titel den S&P 500: der Rückgang war eng von wenigen Riesen getragen, QQQ −10 %, IWM −1 %). Trifft 23 %.
- Führt: 10 Punkte vor dem Index seit dem Indextief und höchstens 15 % unter dem 52-Wochen-Hoch. Nah am Hoch: höchstens halb so weit wie der Index und höchstens 15 %.
- Divergenz: höheres Tief gegen den Index (5 %), Spiegelbild tieferes Hoch gegen den Index.
- Neu: Spring/Upthrust (Spanne der 20 Tage davor höchstens 15 %, Unterschreitung höchstens 1 ATR, mit Volumen zurückgekauft), Tage gegen den Markt (mindestens 4 und 60 % der Indextage mit ±1 %), RS-Linie in der Base (+2 % in 20 Tagen bei fallendem Kurs; höheres RS-Tief bei tieferem Kurstief), 3 Wochen eng, Volumen-Trockenheit, verdeckte Abgabe (Churning).
- Volumen: Kauftag braucht Schluss im oberen, Abgabetag im unteren Drittel; Akkumulation bei Saldo ≥ 3 und doppelt so vielen Kauf- wie Abgabetagen. Pocket Pivot höchstens 4 % über dem GD10 nach einer ruhigen Woche.
- Dow: Schluss 0,5 ATR unter dem letzten höheren Tief bzw. über dem letzten tieferen Hoch.
- Zahlen: Reaktionstag und Schwelle 3 % wie `zahlen_reaktion`; Lücke gekauft/verkauft; Kurs heute unter dem Schluss vor den Zahlen nach positivem Tag 1 = Zahlen verworfen (wie die Kachel).
- Ein Maßstab für das RS-Hoch: 0,99 (`zeichen.RS_HOCH`, auch Chart und Rückenwind).

**Kreislauf:**
- Junge Titel ab 70 Handelstagen bekommen Zeichen, Phase erst ab 300 („jung“).
- Phase 2 kommt nach einem tiefen Fall schon über dem höchsten Wochenschluss der Basis (`phase.py`, vorher erst über dem Hoch der letzten 26 Wochen).
- Rückschlag in Phase 2: Wochenschluss unter GD10W und mindestens 15 % unter dem 52-Wochen-Hoch („2 · Rückschlag“, amber).
- Neue Wechsel 1 → 4 (Schluss unter dem Tief der Basis) und 3 → 2 (Schluss über dem Hoch der Verteilung, RS-Linie über ihrem GD50).
- Die Phase wird überall gleich gelesen: die Woche zählt erst ab ihrem Freitag (`phase.aktuell`). Ein Name je Phase: Basis, Aufwärts, Verteilung, Abwärts (`zeichen.PHASE_NAME`).
- Kreislaufbild: Basis blaugrau, aufwärts grün, Verteilung ambergrau, abwärts rot, Rückschlag amber; Wochentiefs gepunktet, S&P 500 gestrichelt mit gleichem Start, darunter beide Prozente.

**Setups:**
- Base-Ausbruch grün erst ab 2 Kontraktionen (Micky: „ab zwei Kontraktionen“).
- Momentum-Ausbruch grün nur, wenn die Pause den GD20 hält und der Kurs davor 3 Wochen über dem GD50 stand.
- Sprung ohne Zahlen grün ab 5-fach Volumen und Schluss im oberen Drittel.
- Flagge grün nur über steigendem GD50 und mit leiserem Volumen als in der Fahnenstange.
- Echte Bärenflagge (`vcp_zone.baerenflagge`): Fall ab 15 % in höchstens 30 Tagen, leises Driften (3–25 Tage, höchstens die Hälfte zurück, steigende Tiefs), GD50 fällt, Schluss unter dem Tief der letzten 5 Tage. Trifft 2 %.
- Neues Setup Bruch der Spanne (`vcp_zone.spannenbruch`, Reihe `k_bruch`): Basis oder Verteilung ab 6 Wochen und höchstens 40 % breit, Schluss 1 % unter ihrem Tief. Trifft 1 %. Damit acht Setups.
- Ermüdung: jede Flagge nach einer Fahnenstange ab 30 %, die nach unten bricht.

**Markt (`kern/marktrichtung.py`):** Distributionstage verfallen ab +5 % (vorher 10 %); Stautage (höchstens +0,4 % bei höherem Volumen, Schluss in der unteren Hälfte, nahe am Hoch) zählen mit.

**Chart (`oberflaeche/chart.py`):** S&P 500 gestrichelt im Kurschart; Schwungpunkte, Pocket Pivot (PP), Spring (S), Upthrust (U), Divergenz (◆); Abgabetage und verdeckte Abgabe über dem Volumen; RS-Tief vor Kurs.

**Stab:** Jäger mit 20 Anwärtern long und 10 short (zwei long, ein short im Wechsel), dazu jede Depotposition mit frühen Zeichen der Schwäche (muss genannt werden, sonst Wache). Die Rangfolge der Akten kennt den Kreislauf. Zahlen gibt es jetzt für jeden Titel, nicht nur für Titel mit Stufe.

**Freitag (Micky 13.11.2026):** „Ein Zeichen der Stärke ist auch freitags abends keine großen Gewinnmitnahmen nach einem guten wöchentlichen Lauf.“ `zeichen.freitag`: letzte fertige Woche mindestens 2 Wochen-ATR im Plus, der letzte Handelstag schließt im oberen Drittel und nicht schwächer als −0,5 %, die Woche im oberen Viertel ihrer Spanne → Stärke (Art Nachfrage/Volumen). Spiegelbild: nach einer Woche von mindestens −2 Wochen-ATR keine Eindeckung → Schwäche. Gemessen an 1.885 Titeln: je Woche 0,4–0,9 % (Wochen 23.10. und 30.10.).

## Verankerung von AVWAP und Volumenprofil (13.11.2026)

Micky: „Die Verankerung ist extrem wichtig. Für das Volumenprofil und für den AVWAP. Falsch verankert machen diese beiden keinen Sinn und führen zu falschen Annahmen.“ Regel: Anker nur aus Ereignis und Struktur, nie aus dem Kalender (`kern/avwap.py`, eine Quelle für Chart, Lagekarte und Stab).

- Hoch: das Hoch, von dem der laufende Fall ausging – höchstes Hoch der 52 Wochen; liegt es am Rand des Fensters, wird bis 2 Jahre zurück gesucht.
- Tief der Bewegung: das tiefste Tief seit dem Hoch (mindestens 10 Handelstage her); steht der Titel am Hoch, das Tief, von dem der Lauf zum Hoch ausging – ebenfalls nie der Rand eines Fensters.
- Ereignis: der jüngere von Zahlentag (Reaktion ab 3 %, `avwap.zahlentag`) und Lücke ab 4 % mit doppeltem Volumen. Der eigene Anker „Zahlentag“ entfällt.
- Gemessen an 584 Titeln (Daten bis 04.11.): vorher lag das Tief der 6 Monate bei 95 Titeln (16 %) am Fensterrand, nachher bei 5; von 242 Zahlenreaktionen ab 3 % waren vorher 151 kein Anker, nachher alle.
- Volumenprofil (`volumenprofil.verankert`, statt starr 52 Wochen): grau ab dem jüngeren von Beginn der Zone und Ereignis (mindestens 5 Handelstage, sonst ab dem Tief der Bewegung) mit dem akzeptierten Wert; Mauer = nächster Knoten seit dem Hoch über dem Kurs, Stütze = nächster Knoten seit dem Tief unter dem Kurs.
- Chart: Profil als durchscheinende Balken von rechts über den Kerzen (der Chart behält seine Breite), Mauer rot und Stütze grün als Bänder mit Preis und Anker-Datum, Überschrift mit Anker und Zahl der Tage.
- Lagekarte: die Hürde für das CRV kommt aus den Knoten des verankerten Profils.
- Stab: die Akte trägt AVWAP (hoch, tief_der_bewegung, ereignis) und „volumen“ (akzeptierter Wert, Mauer, Stütze) mit denselben Ankern wie der Chart; der Zahlentag gilt jetzt für jede Akte, nicht nur für die Zahlen-Reaktion.

## Konferenzraum abgebaut (13.11.2026)

Micky: „Der Konferenzraum kann weg. Den brauchen wir nicht mehr.“ Die Strategen sammelten Daten, statt zu deuten; der Edge liegt in den Messungen der App. Künftig ein Stratege auf Knopfdruck (Strategen-Call, Konzept im Konzeptdokument).

- Entfernt: die acht Missionen (`kern/stab.py`), die Seite Konferenzraum (`oberflaeche/konferenz_seite.py`), die Konferenz im Frühlauf samt zweitem Anlauf und Knopf, der Tagesbefehl aufs Handy, die Nadeln der Strategen im Chart, der Satz des Stabs im Kreislaufbild, die Wachen „Stab“ und „Form des Stabs“, „Stab fragen“ und `rueckenwind.anfuehrer_verfolger` (nur vom Stab genutzt). Der alte Code liegt auf dem Mac in `_to_delete/stab_konferenzraum_2026-11-13.py` und `_to_delete/konferenz_seite_2026-11-13.py`.
- Geblieben: die Auswahl „Einsatzbereit“ mit Zonen und Rangfolge (`kern/auswahl.py`, Seite Setups ① und Wachen) und die Verbindung zum Modell mit Schlüssel, Probe, Kostenbuch und Monatsdeckel (seit 14.11.2026 100 $ – das API-Guthaben im Max-Abo; vorher 50 $; `kern/modell.py`) für den künftigen Strategen-Call. Schlüssel und Kostenbuch bleiben, wo sie lagen (`einstellungen/anthropic_schluessel.txt`, `daten/konferenz/kosten.json`).
- Seite Setups: ① heißt „Einsatzbereit“ (vorher „Auswahl für den Stab“), die Tabelle „🎯 Einsatzbereit · N Titel auf der Liste“ (vorher „Diese Titel liest der Stab“). Ganz unten „⚙ Verbindungen“: API-Schlüssel, Verbindung prüfen, Kosten des Monats, Kanal fürs Handy mit Testmeldung.
- Handy: seit 17.11.2026 nur noch „Heiße Titel“ und Fehler (gescheiterte Schritte, rote Wachen) – kein „Lage steht“, keine gelben Hinweise.
- Alte Lesezeichen `?seite=Konferenzraum` öffnen die Seite Setups.

## Der Code für Balance und Ungleichgewicht – eine Zustandsmaschine (13.11.2026)

Micky: „Diese 3 Bilder bilden jetzt die Grundlage für unsere ganze App und den Strategen.“ Ein Modul `kern/auktion.py`
gibt Titel, Gruppe und Markt denselben Zustand: Balance · Test am Rand · abgelehnt · angenommen · Ungleichgewicht ·
Ende des Laufs (Farben aus dem Bild: grau, grau, grün, rot, rot, grün; Anlass lila). Jedes Ergebnis trägt den Anlass,
die Belege an ihrem Platz in der Kette, die Kraft, die den Lauf beendet (Gegner antwortet · Antrieb erlischt · Wert
akzeptiert), wo die Gegenseite wartet und ob die Kraft eigen oder geliehen ist. Die alten Wörter (Phase, Market
Profile, Feld, O'Neil, Marktzone) stehen als Unterzeile.

- **Titel:** das jüngste Ereignis der letzten 10 Handelstage am Rand entscheidet (Ausbruch/Fehlausbruch des
  VCP-Scanners, Ausbruch A, Umkehr U und Scheitern S des Market Profile, Spring, Upthrust, Bruch der Spanne, Ausbruch
  aus der Verteilung). Ereignisse des Market Profile innerhalb der Zone des Scanners sind innere Rotation, kein Test am
  Rand. Ohne Ereignis: Kurs in der Zone = Balance bzw. Test am Rand (höchstens 3 % vom Rand oder MP „an der Schwelle“);
  Phase 2/4 außerhalb der Zone = Ungleichgewicht, mit einer der drei Kräfte = Ende des Laufs.
- **Gruppe:** Feld der Rotationskarte plus Breite (Anteil der Mitglieder über dem GD50, heute und vor 4 Wochen) und
  Anführer/Verfolger je Gruppe (`rueckenwind.anfuehrer_verfolger`, zurückgeholt und je Gruppe gerechnet).
- **Markt:** O'Neil (Marktrichtung) mit dem gescheiterten Erholungsversuch als „abgelehnt“
  (`marktrichtung.verlauf` merkt ihn sich jetzt), die Marktzone der Lage als Unterzeile.
- **Lücken gemessen:** Kraft ohne Weg am Rand, Exzess bzw. flache Kante aus den 30-Minuten-Kerzen (Exzess ab 15 % der
  ATR), Volumenlücke bis Mauer/Stütze, Verkaufs- und Kauf-Klimax, anderer Rand nach einer Ablehnung, Größe der Ursache.
- **Zusammengeführt:** „Wert wandert“ ist im Market Profile aufgegangen (Zeichen jetzt „an der Schwelle“); die
  Weinstein-Zeile der Kachel Trend nennt nur noch, seit wann die Phase gilt.
- **Anzeige:** Titelseite – Zustand unter dem Kopf und als Karte mit der Kette über dem Kreislaufbild; Setups – Pille
  vor der Mini-Kurve, Spalte „Zustand“ in den Tabellen; Rückenwind – Zustand des Marktes oben, Zustand jeder Gruppe in
  der Wetterkarte (Belege beim Darüberfahren).
- **Strategen-Call** (`kern/strategen.py`, Knopf unter dem Kreislaufbild): ein Stratege, nur das Material der App mit
  Feldnummern, Kette Zustand → Anlass → wer ist am Rand stärker → angenommen/abgelehnt → Gegenseite → eigen/geliehen.
  Antwort: Schuss long/short/kein, Disbalance, höchstens 3 Belege, Auslöser, widerlegt bei, Gegenzeuge. Der Code prüft
  Felder, Zahlen und Seiten und zeigt jeden Befund. Einmal je Titel und Kurstag (`daten/strategen/`), Kosten im
  Kostenbuch, Deckel 100 $ (seit 14.11.2026, vorher 50 $).

Gemessen über 1.907 Titel (Daten bis 04.11.2026, ein breiter Ausbruchstag – 23 % mit Ausbruch des Scanners in 10
Tagen): angenommen 43 %, Balance 26 %, abgelehnt 20 %, Test am Rand 8 %, Ende des Laufs 2,5 %, Ungleichgewicht 1,2 %.

## Befunde des Chart-Prüfers an LUV (14.11.2026)

- **Phase 3 → 4** erst, wenn die 40-Wochen-Linie wirklich fällt (mehr als 0,5 % in 4 Wochen, Weinstein). Vorher reichten
  −0,1 %; LUV stand in Phase 4 bei flacher Linie und Kurs darüber. Gemessen über 1.892 Titel: 62 Titel ändern die Phase
  heute (meist 4 → 3 und 1 → 3), 1,6 % aller Wochen.
- **Knoten im Volumenprofil** sind jetzt alle Gipfel des Profils (ab 30 % des größten Volumens und mindestens 10 % über
  dem höheren Tal daneben), nicht nur Zonen ab 60 %. LUV: das Angebot bei 47–49 $ (42 %) fehlte als Mauer.
- **Ausbruch aus einer Pause tief in der Zone** (Pivot mehr als 3 % unter der Oberkante, jüngere Zone in der großen) ist
  innere Rotation mit Cheat-Drittel (Minervini), keine Annahme außerhalb der Balance (`auktion.titel`).
- Profil der Balance heißt nicht mehr „verlassen“, solange der neue Wert nicht angenommen ist (Dalton).
- **Gescheiterte Tasse** am Schlusskurs unter der Mitte, nicht am Tagestief (Micky; gemessen: 38 von 1.905 Zonen ändern
  sich, alle zu gültigen Zonen). **Zonenbeginn** bleibt: Schluss entscheidet, ein Docht darüber ist ein abgelehnter
  Vorstoß (Micky).
- **Einquetschung**: flache Kante seit mindestens 3 Wochen, gesucht in 60 und 120 Tagen (gemessen 48 → 27 Titel).

## Anker nach Shannon und Dalton (14.11.2026)

Micky (LUV): „Der AVWAP ist komplett falsch verankert und das Volumenprofil fehlt.“ Das alte Hoch der 52 Wochen hing
bei LUV am 17.02., das Tief am 02.04. – beide aus einem Zyklus, der im April endete. Neu nach den Meistern
(`kern/avwap.py`):
- **Letztes Hoch:** jüngstes Hoch, das der Kurs nicht überschritten hat und das durch den Rückgang danach bestätigt ist
  (Shannon): ab 8 % darunter oder als Schwunghoch der Wochenkerzen (n = 2); steht er über allen, das letzte
  (Ausbruchspunkt). 8-%-Regel: Micky 14.11.2026, sonst kam der Anker bis zu 2 Wochen zu spät.
- **Tief der Bewegung:** das Tief, an dem der laufende Trend begann (Shannon: „the pivot low that launched the trend“;
  Micky 14.11.2026: nur dieses) – das tiefste Tief zwischen dem früheren, höheren Hoch (ohne: 52 Wochen) und dem letzten
  Hoch. Trend gebrochen (Kurs darunter): das tiefste Tief seit dem letzten Hoch, sobald der Kurs 1 ATR darüber steht.
- **Hoch des Rückgangs:** höchstes nicht überschrittenes Wochen-Schwunghoch, nach dem der Kurs nie unter das tiefste
  Tief seit dem letzten Hoch fiel (der Gipfel der Korrektur). Voreinstellung im Chart: nur die Zange (letztes Hoch und Tief), Hoch des Rückgangs und Ereignis per Schalter (Micky 14.11.2026).
- **Ereignis:** jüngster Zahlentag, jüngste Lücke ab 4 % oder Volumenspitze (ab doppeltem 50-Tage-Volumen mit Bewegung
  ab 3 %), höchstens 6 Monate (Shannon: Zahlen, Lücke, große Nachricht; Micky 14.11.2026).
- **Volumenprofil:** ab dem ersten Tag der laufenden Balance nach Dalton (überlappender Wert: von heute in Blöcken zu 5 Tagen
  zurück, ein Block gehört dazu, wenn seine Spanne die mittlere Hälfte der typischen Preise der Balance berührt; bis
  2 Blöcke Rotation zum Rand; Wert wandert seit wenigen Tagen → die Balance davor; `avwap.balance_beginn`, Micky 14.11.2026 – vorher ab der Wertzone des Market Profile, immer montags); bei unter
  2 Wochen ab der Zone, sonst ab dem Tief der Bewegung; im Chart mit dem Wertbereich als Feld über dem Zeitraum der Balance. Mauer aus dem Profil
  ab dem Hoch des Rückgangs, Stütze ab dem Tief der Bewegung.

Gemessen über 1.892 Titel: kein Anker am Rand des Datenfensters, kein Kurs unter dem Tief der Bewegung. Hoch des
Rückgangs bei 48 % (sonst gleich dem letzten Hoch), Tief der Bewegung bei 82 % (sonst steht der Kurs am Tief). Profil
der Balance bei 99 % aus der Wertzone, 91 % davon 10–40 Handelstage lang.

## Zonen nach O'Neil und Minervini geprüft (14.11.2026)

Recherchiert: O'Neil – Tasse 7–65 Wochen, 12–33 % tief (im Bärenmarkt bis 40–50 %), der Henkel liegt in der oberen
Hälfte der Base, höchstens etwa 15 % unter dem Hoch der linken Seite; Doppelboden: das zweite Tief unterschreitet das
erste. Minervini – Pivot im unteren Drittel = Low Cheat, im mittleren = Cheat, im oberen = O'Neils Henkel; nach einer
gescheiterten Tasse bildet sich eine neue Base („rebase“).
- **Gefunden:** Die Zone begann am ältesten ungebrochenen Hoch, auch wenn die Tasse danach gescheitert war (LUV: Base
  ab 17.02., die rechte Seite kam am 26.06. bis 52,88 $, danach −29 % bis in die untere Hälfte – kein Henkel mehr).
- **Neu (`vcp_zone.zone`):** Kam die rechte Seite bis 15 % an die Oberkante heran und fiel der Kurs danach wieder in
  die untere Hälfte, ohne das Tief zu unterschreiten, beginnt die Zone neu am Hoch der rechten Seite. Ist dort noch
  keine Erholung, steht die Zone offen mit dem Grund „Base … gescheitert … neue Base ab …“.
- **Neu (Enge):** Der Pivot nennt sein Drittel: Low Cheat (unteres), Cheat (mittleres), Pivot der Base (oberes).
- Gemessen über 1.905 Titel: 22 % haben eine andere Zone (davon 10 % jetzt „zu kurz“, 5 % offen). Pivot im oberen
  Drittel 62 %, Cheat 5 %, Low Cheat 0,5 %.

## Chart-Prüfer (14.11.2026)

Micky wollte einen „Strategen für Chartmuster“. Entschieden: ein Prüfstand, kein Erkenner – die Erkennung bleibt Code
(nur feste Regeln geben bei denselben Kursen immer dieselbe Zone; ein Modell jede Nacht über 1.900 Charts kostete
rund 35 $ am Tag und urteilte von Lauf zu Lauf anders). `kern/chartpruefer.py` (Lauf: `werkzeuge/pruefer_lauf.py`), Knopf auf der Seite Setups:
- Stichprobe von etwa 150 Titeln, gleichmäßig über Base, Konsolidierung, Flagge, offene Zone, keine Zone und die grünen
  Setups des Kartentischs.
- Je Titel ein Bild (matplotlib: 1 Jahr Tageskerzen mit Zone, Pivot, Kontraktionen, AVWAP-Ankern, Beginn der Balance,
  Wochen-Schwunghochs) und die Zahlen der App; das Modell prüft gegen die recherchierten Regeln von O'Neil, Minervini,
  Kullamägi, Shannon und Dalton und meldet nur Widersprüche (Element, Befund, Regel, was richtig wäre, sicher/strittig).
- Bericht in `daten/chartpruefer/`, auf der Seite nach Element gruppiert. Gemessen etwa 19 Cent je Chart (14.11.2026), gegen den Monatsdeckel
  geprüft. Echte Regelfehler gehen in den Code (gemessen über alle Titel), strittige Fälle entscheidet Micky.
- Server: `werkzeuge/server/pakete.txt` (matplotlib) wird vom Update-Skript installiert, sobald sich die Liste ändert.
- Erweitert (14.11.2026, Micky: „checkt er alle Muster, die für unsere drei Bilder wichtig sind?“ – nein, nur den
  Unterbau): jetzt die ganze Kette. Ins Bild kommen Mauer und Stütze sowie Marken für Ausbruch, Fehlausbruch, die Signale
  A, U, R, S des Market Profile (letzte 60 Tage), Spring, Upthrust, Kraft ohne Weg, Klimax, Exzess bzw. flache Kante.
  In die Zahlen kommen Kreislauf, alle Zeichen, die Short-Formen und der Zustand mit Anlass, Belegen je Platz, Ende,
  Gegenseite, eigen/geliehen. Neue Prüfpunkte: Zustand, Anlass, Test am Rand, abgelehnt/angenommen, Ende des Laufs,
  Gegenseite, eigen/geliehen, Kreislauf, Short-Form. Dazu 20 Gruppen (gleichgewichteter Index der Mitglieder, RS-Linie,
  Breite; Feld, Zufluss, Anführer, Zustand). Etwa 4 Cent je Chart, rund 6 $ je Lauf.
- Echter Chart (14.11.2026, Micky: „warum geht der Prüfer nicht echte Chartbilder durch?“): erstes Bild ist jetzt der
  Chart der Titelseite (Tageskerzen, 1 Jahr, Voreinstellung), als SVG mit cairosvg in ein Bild gewandelt (ohne Browser;
  der Schriftsaum fällt weg, sonst unlesbar). Das eigene Bild bleibt als Hilfsbild für Marken, die der Chart nicht zeigt.
  Server: libcairo2 und cairosvg installiert das Update-Skript. Etwa 5 Cent je Chart.
- Knopf je Titel: „🔎 Chart prüfen lassen“ unter dem Chart der Titelseite; Urteil als Karte darunter, gespeichert je
  Titel und Kurstag in `daten/chartpruefer/titel/`.


## Setup-Prüfer (14.11.2026)

Micky: eigener Prüfer nur für die Setups, der Chart-Prüfer bleibt bei Zone, Zeichen, Zustand und Ankern
(`kern/setuppruefer.py`, Lauf `werkzeuge/setup_lauf.py`, Bericht in `daten/setuppruefer/`). Er prüft den Angriffsbefehl:
grün zu Unrecht, zu streng, Regel falsch gemessen, Wahl des Setups, Einstieg/Pivot, Kaufzone, Stopp, übersehene Setups
und Shorts. Stichprobe: 80 Titel gleichmäßig über die Reihen des Kartentischs (grün und nicht grün getrennt) und 20 ohne
Setup. Material: Urteil der App mit allen Regeln beider Lehrer (`kartentisch._stufe1(tk, regeln=True)`), Plan (Einstieg,
1,5-ATR-Stopp), die Zahlen des Charts und die letzten 10 Tage; Bild: der Chart der Titelseite. Regeln der Meister
(Minervini, O'Neil, Kullamägi, Weinstein) und die Setups der App stehen im Auftrag. Der 1,5-ATR-Stopp ist Mickys
Entscheidung (09.11.2026) – Abweichungen meldet der Prüfer als strittig. Etwa 13 Cent je Titel, ein Lauf etwa 13 $; Chart-
und Setup-Prüfer laufen nie gleichzeitig (Monatsdeckel). Knopf „🎯 Setup prüfen lassen“ unter dem Chart der Titelseite;
Kasten auf der Seite Setups unter dem Chart-Prüfer. Auswertung wie beim Chart-Prüfer (`chartpruefer.auswerten` mit
eigenem Auftrag).

## Mängelliste (14.11.2026)

Micky: Befunde der Prüfer dürfen zwischen zwei Chats nicht verloren gehen (`kern/maengel.py`, `daten/maengel.json`).
Jede Auswertung von Chart- oder Setup-Prüfer kommt von selbst in die Liste (`aus_berichten`, auch alte Berichte mit
Auswertung). Jeder Befund hat einen Stand: offen, behoben (Notiz: Commit und Messung) oder entschieden (Notiz: Mickys
Entscheidung). Auf der Seite Setups unter den Prüfern, Vorgabe: nur offene. Darunter der Verlauf je Prüfer:
Widersprüche je Chart (davon sicher) je Element über alle Läufe – ein behobener Befund muss dort sinken.

## Prüfer gegen die drei Bilder abgeglichen (14.11.2026)

Micky: „Denke an unsere drei Bilder.“ Abgleich Kasten für Kasten:
- **Chart-Prüfer, Titel (Bild 1 und 2):** Auftrag beschreibt jetzt jeden Kasten wie im Bild, mit der Gefechtsordnung
  (Zone führt, Rand = Oberkante, Pivot = Auslöser, Wyckoff bei „abgelehnt“, Kullamägi bei „Ungleichgewicht“, Stopp am
  10er/20er). Ende des Laufs nach dem Bild: Gegner antwortet (Knoten, alter Wert, AVWAP vom alten Hoch, Exzess),
  Antrieb erlischt (Kraft ohne Weg, Klimax, Phasenwechsel, Rückschlag), Wert akzeptiert (Zeit und Volumen) – vorher
  stand Kraft ohne Weg beim Gegner. Neue Elemente: Lauf zum anderen Rand, Ungleichgewicht, Neue Balance/Basenzählung.
- **Chart-Prüfer, Gruppe (Bild 3):** alle 13 Kästen im Auftrag (vorher fehlten Anlass, „Gruppe folgt nicht“, „Geld
  wandert weiter“, Neue Balance); der Quad steht im Material. Neue Elemente: Anlass, Anführer bricht aus, Schwestern
  folgen, Gruppe folgt nicht, Ende des Laufs, Neue Balance.
- **Markt:** wurde gar nicht geprüft – jetzt einmal je Lauf (`pruefen_markt`, O'Neil, Wertzonen, Breite, Regel 8).
- **Setup-Prüfer:** kennt die Gefechtsordnung (jedes Setup als Weg durch den Kreislauf, zwei Einstiege, zwei Stopps,
  Ausstieg am 10er/20er, Spring/Upthrust beschlossen) und sieht den Zustand des Titels im Kreislauf.
- **Lücken in der App selbst** (der Prüfer meldet sie jetzt): die Gruppe nennt keinen Anlass, „Geld wandert weiter“
  wird nicht gemessen, der Markt nennt keinen Anlass.

## Befunde aus Lauf 3 (14.11.2026, 100 Charts) – klare Fehler

- **Hoch des Rückgangs** = das höchste bestätigte, nicht überschrittene Hoch der letzten 2 Jahre (`avwap.anker`).
  Vorher schied jedes Hoch aus, nach dem der Kurs tiefer fiel als seit dem letzten Hoch – lag das letzte Hoch nach dem
  Tief (KBH, BAX, ORA), blieb nur das letzte Hoch selbst. Gemessen: eigener Anker bei 1.434 statt 1.053 von 1.865 Titeln.
- **Enge geschärft** (`vcp_zone.enge`): jede Kontraktion mindestens 3 Handelstage, mehr als 6 Wellen ist kein VCP, grün nur
  mit ausgetrocknetem Volumen (unter dem 50-Tage-Schnitt) und nicht in Phase 4. Gemessen: grün 94 → 44, rot 114 → 81,
  90 % der Zonen haben höchstens 4 statt 5 Kontraktionen.
- **Phase an der 30-Wochen-Linie** ausprobiert und verworfen: 35 % der Titel wechselten die Phase, die Beispiele des Prüfers
  wurden nur teils besser (BAX, KBH), teils schlechter (COKE, LUV – die 8-Wochen-Sperre nach Phase 4). Gehört in die
  Gefechtsordnung (Weinsteins Stufen als Rahmen), nicht als Einzelflick.
- **Ereignis-Anker an jedem jüngsten Zahlentag** (Micky, Shannon; `avwap.zahlentag`): vorher erst ab 3 % Reaktion, sonst
  saß der Anker auf einem älteren Ereignis (EXPO, DRH). Die 3 % gelten weiter für das Setup Zahlen-Reaktion. Gemessen:
  Ereignis-Anker bei 1.342 statt 1.255 von 1.343 Titeln mit Zahlen, 269 ankern anders.
- **Flagge grün nur mit steigenden Tiefs** (Micky, Kullamägi; `kartentisch.flagge_im_trend`): das tiefste Tief der zweiten
  Hälfte der Flagge darf höchstens 0,5 ATR unter dem der ersten liegen (gleiche Tiefs oder ein kurzes Unterschneiden
  halten das Gelände). Sonst steht „Tiefs fallen – die Truppe weicht“ unter „fehlt“. Gemessen: Flaggen im Trend 44 → 26
  von 108 (ohne Spielraum wären es 13 gewesen – auch exakt gleiche Tiefs fielen raus).

## Regelkarte und Wachposten (15.11.2026, Gefechtsordnung Schritt 1)

`kern/regelkarte.py` ist die eine Quelle für die Regeln: jeder Kasten der drei Bilder (Titel 14, Gruppe 12, Markt 9),
die Werkzeuge, die sie messen (Zone, Enge, Anker, Profil, Phase …), alle Setups als Wege durch den Kreislauf und die
Regeln der Meister. Jeder Eintrag nennt Regel, führenden Meister, Messung im Code (Modul.Funktion), Stand (gemessen,
teilweise, fehlt – mit der Lücke und dem Schritt, in dem sie geschlossen wird) und das Prüf-Element.

- Chart-Prüfer (`SYSTEM`, `SYSTEM_GRUPPE`, `SYSTEM_MARKT`, `ELEMENTE…`) und Setup-Prüfer (`SYSTEM`, `ELEMENTE`) bauen
  ihre Anleitung aus der Karte; dort steht nur noch, was der Prüfer tut.
- `regelkarte.wachposten()` prüft Karte gegen Code: Messfunktion fehlt, Prüf-Element fehlt, Anleitung ohne Kasten,
  Zustand der App ohne Kasten, Reihe des Kartentischs nicht auf der Karte → 🚨 Alarm. Bekannte Lücken stehen 🟡/🔴.
- Seite Setups: Kasten „🛡️ Regelkarte · Wachposten“ über den Prüfern; bei Alarm offen und rot.
- Zeichen (15.11.2026, Micky: „du hast diesmal alles berücksichtigt?“): alle 15 Zeichen der Stärke und Schwäche aus
  `zeichen.py` stehen mit Regel, Meister, Messung und Prüf-Element auf der Karte (Dow-Struktur, Spring/Upthrust,
  Einquetschung, Bruch der Phase, Akkumulation/Distribution, Pocket Pivot, 3 Wochen eng/Trockenheit, Freitag ohne
  Gewinnmitnahme, Stärke in der Schwäche, höheres Tief gegen den Index, Tage gegen den Markt, RS-Linie in der Base,
  Reaktion auf die Zahlen, Market Profile an der Schwelle, Trendqualität) samt der Gewichtung. Der Wachposten liest
  `zeichen.py` und meldet Alarm für jede Funktion, die ein Zeichen setzt und nicht auf der Karte steht (getestet: Freitag
  von der Karte genommen → Alarm).
- Neue Regel = erst in die Karte, dann bauen.
- Abgleich mit den alten Anleitungen: jeder Satz übernommen (wörtlich oder in einen Kasten umgeformt); zwei fehlten im
  ersten Entwurf und sind nachgetragen („bringt die Balance an den Rand“, Spring/Upthrust „Ziel der andere Rand“).
  Bewusst aktualisiert: „angenommen“ ohne Volumen-Pflicht, Ereignis-Anker an jedem Zahlentag, Hoch des Rückgangs
  2 Jahre. Die Anleitung des Chart-Prüfers ist etwa 3.700 Zeichen länger (rund 1.000 Token, unter 1 Cent je Chart).

## Befunde aus Lauf 4 (15.11.2026) – behoben

Lauf 4: 100 Charts, 690 Widersprüche (309 sicher), 21,74 $ (die Anleitung ist mit Regelkarte und Zeichen länger).
Gemessen über 1.865 Titel, alter gegen neuen Code (Mac-Daten bis 04.11.):

| Befund | Änderung | vorher → nachher |
|---|---|---|
| Test am Rand ohne 3 % | Schwelle des Market Profile und Exzess nur bis 3 % vom Rand; Exzess vor der Zone fällt weg | Titel mit Beleg „Test am Rand“ 1.195 → 740 |
| Wert gewandert als Ungleichgewicht | innerhalb der Zone = innere Rotation | 785 → 284 |
| Upthrust/Spring nicht aufgehoben | Schluss jenseits des Tageshochs/-tiefs hebt auf (auch Anlass, Waage) | 72 aufgehoben, abgelehnt 365 → 280 |
| Eigen/geliehen | RS in Laufrichtung: eigen ≥ 5 %, geliehen ±1 %, teils eigen, Gegenzeichen | „mit dem Markt“ 494 → 0 |
| Waage | alle Zeichen, Seiten getrennt, Gleichstand kein Beleg | Gleichstand-Belege 152 → 0 |
| AVWAP letztes Hoch | nur fertige Wochen bestätigen; Kurs über allen Hochs = „Ausbruchspunkt“ | 172 Ausbruchspunkte, 194 Anker anders |
| Quad in Buchstaben | Material des Prüfers | – |

- **Flagge** (Micky 15.11.2026, `vcp_zone._stange`, `vcp_zone.tiefs_fallen`): eine Zone heißt nur noch Flagge, wenn
  ihre Tiefs halten (Tief der zweiten Hälfte höchstens 0,5 ATR unter dem der ersten), sonst Base bzw. Konsolidierung;
  die Fahnenstange liegt direkt davor (nach einem Rücksetzer über 25 % in den 13 Wochen beginnt sie erst an dessen
  Tief). Die Prüfung der Tiefs im Kartentisch ist damit in die Zone gewandert. Titel mit Flagge 174 → 123, reife
  Flaggen 108 → 72; 33 Zonen heißen jetzt Base (22) bzw. Konsolidierung (11).

Offen aus Lauf 4: Pivot verbraucht/Drittel,
Volumenprofil der Balance, Basenzählung, Kette (Gefechtsordnung), Phase (Schritt 8), Gruppen und Markt.

## Generalinventur (15.11.2026)

Micky: „Die App auf ein einheitliches Niveau – blinde Flecken dürfen nicht mehr zufällig auffallen.“

- **Inventur im Wachposten** (`regelkarte.inventur`): liest den Code selbst. Jede feste Regel (Konstante mit Zahl auf
  Modulebene, auch über `from … import`) muss einer Messfunktion der Karte gehören, sonst 🚨 „blinder Fleck“; Technik
  (Layout, Kosten, Stichproben, Datenpflege) steht mit Grund in `TECHNIK`. Gleicher Name in zwei Modulen = 🚨 Kopie
  (Ausnahmen mit verschiedenem Begriff in `VERSCHIEDEN`). Stand: 190 feste Regeln, 171 auf der Karte, 19 Technik,
  0 blinde Flecken, 0 Kopien (vorher 80 bzw. 6).
- **Weitere Bereiche** auf der Karte (`BEREICHE`): Wahl des Setups, Seite long/short, Einstieg/Stopp/CRV, Nach dem
  Kauf und Depot, Rückenwind-Stufen, Fundament, Termine, Auswahl, Rotationskarte, Rudel. Ohne Prüfer (🟡): Depot,
  Rückenwind, Fundament, Termine, Auswahl, Rudel.
- **Kopien zusammengelegt**: Stopp 1,5 ATR (depot), Kaufzone 5 % (vcp_zone), Sprung-Schwellen (system_kullamaegi),
  Rückschlag (zeichen), Zufluss (rueckenwind), Kosten je Chart (chartpruefer), Wertbereich 70 % (marketprofile),
  Rand 3 % (vcp_zone). `volumenprofil.JAHR` war tot und ist weg.
- **Eine ATR** (`atr.reihe`): vorher fünf Rechnungen (Wilder-Glättung in vcp_zone, Spanne ohne Lücken in avwap,
  einfaches Mittel in atr, zeichen, auktion). Gemessen: 93 von 1.823 Zonen ändern sich (5 %), Enge kaum.
- **Eine Cheat-Regel** (`vcp_zone.cheat`), benutzt von Ausbruch, Historie, Basenzählung und Zustand: ein Ausbruch aus
  einer jüngeren Pause mit Pivot mehr als 3 % unter der Oberkante der noch laufenden größeren Zone ist ein Cheat.
  Historie: dieselbe Schlacht nur einmal (überlappend, Ausbruch innerhalb von 5 Tagen: die größere bleibt), Cheats
  dünn gestrichelt ohne Nummer. Gemessen: Ausbrüche 745 → 604 (151 waren Cheats in der laufenden Zone), Zonen der
  Historie 16.757 → 14.939, davon 2.865 Cheats. LUV: 21.10.–26.11.25 und 22.09.–27.10.26 Cheat, 10.03./17.04.26 eine Zone.
- **Noch nicht inventarisiert**: Zahlen direkt im Code (386 in den Rechenmodulen, ohne 0/1/2/3/4/5/10/20/50/100) –
  die zweite Stufe.

## Generalinventur Stufe 2 abgeschlossen (15.11.2026)

- **Jede feste Zahl in einer Regel-Funktion hat einen Namen.** 386 Zahlen ohne Namen in 312 Funktionen → 0. Frei bleiben nur
  Rechenzahlen (0, 1, 2, −1, 100), Mindestlängen der Daten, Rundung/Format, die GD-Längen in `rolling(50)`, Phasen 1–4 als
  Kennzahl und kurze Textausschnitte. 26 Vergleiche mit 1 oder 2 waren echte Regeln (2 Kontraktionen, 2R, 1 bzw. 2 × ATR,
  ±2 Punkte RS-Linie …) und haben ebenfalls Namen.
- **Geteilte Maße an einer Stelle:** `kern/masse.py` (Woche, Monat, Jahr = 252 Tage, Quartale, GD50/150/200, ATR 14,
  Volumen-Schnitt 50, Phase 3/4, Datumslänge …). Die IBD-Gewichte des RS-Rangs stehen nur in `rs_rang`. Vorher standen
  24 Namen doppelt; die Erkennung rechnete das Jahr mit 250 statt 252 Tagen.
- **Erkennung entschlackt:** die alte eigene Base mit zweiter Trendvorlage, Muster und Kaufsetup hatte 0 Nutzer und ist
  entfernt (alter Stand in `_to_delete/uebergabe_2026-11-12/erkennung_alt_2026-11-15.py`). Klimax-Verdacht und
  Datenampel gelten jetzt für jeden Titel (gemessen an 468 Titeln: 3 Warnungen neu sichtbar, Seite und Wertzone gleich).
- **Wachposten:** die Inventur liest jede Regel-Funktion und meldet rot jede neue Zahl ohne Namen (Datenquellen
  massive, quellen, daten, marktdaten, tpo_daten ausgenommen). Die Regelkarte zeigt die Zahl in ihrer Inventur-Zeile.
- **Beweis:** Syntaxbaum bis auf Namen gleich in 28 von 28 umbenannten Modulen; Gleichlauf an 468 Titeln: Material des
  Chart-Prüfers und Setup Zeichen für Zeichen gleich.

## Gefechtsordnung Schritt 2: zwei Einstiege (15.11.2026)

- **Eine Cheat-Regel** (`vcp_zone.drittel`): liegt das Hoch der letzten Enge mehr als 3 % unter der Oberkante der Base,
  ist ein Schluss darüber der frühe Einstieg – Low Cheat, Cheat (mittleres oder oberes Drittel). Der Ausbruch ist dann
  der Schluss über der Oberkante. Liegt das Hoch der Enge bis 3 % unter der Oberkante, gibt es einen Einstieg, den Pivot
  am Rand. Dieselbe Regel gilt in Enge, Cheat, Ausbruch, Historie, Chart, Plan und Prüfern.
- **Welcher gilt:** der unterste Einstieg, über den der Kurs noch nicht hinaus ist (nicht ausgelöst oder in seiner
  Kaufzone bis 5 %); darüber der Ausbruch. Der Kartentisch misst den Abstand zu diesem.
- **Plan und Chart:** beide Einstiege mit Kaufzone und Stopp (1,5 ATR bis Schritt 3), der geltende mit „← gilt jetzt“;
  der zweite als gestrichelte Linie im Tages- und Stundenchart. Stückzahl je Einstieg.
- **Laufender Börsentag:** der Plan zeigt aus den 30-Minuten-Kerzen, seit wann der Kurs über dem Auslöser steht und ob
  er hält – vorläufig, es zählt der Schluss.
- **Geltung:** Base long (Base-Ausbruch und VCP). Flagge und schnelle Setups behalten einen Einstieg. Der Spiegel für
  Shorts kommt mit Schritt 4 (Plan 21): die App kennt Shorts heute erst nach dem Bruch.
- **Gemessen an 468 Titeln:** 112 von 262 Zonen mit Pivot haben einen Cheat (68 mittleres Drittel, 25 oberes, 19 Low
  Cheat). 68 Ausbrüche waren Schlüsse über einem Cheat und zählen nicht mehr als Ausbruch, 14 haben einen anderen Tag
  oder Pivot. Einstieg bei 14 Titeln anders, Setup-Reihe bei 7.

## Gefechtsordnung Schritt 3: Struktur-Stopp neben 1,5 ATR (15.11.2026)

- **Eine Quelle:** `depot.struktur_stopp` – der Kurs, an dem der Weg des Setups widerlegt ist:
  Base und VCP unter dem Tief der letzten Kontraktion (je Einstieg); Flagge und Momentum-Ausbruch das Tief des
  Ausbruchstags, bis dahin Einstieg − 1 Tagesspanne (ADR 20 Tage); Sprung (EP) das Tief des Sprungtags; Zahlen-Reaktion
  Tief bzw. Hoch des Reaktionstags; Shorts das Hoch des Auslösetags. Liegt die Struktur durch eine Lücke nicht jenseits
  des Einstiegs, gilt Einstieg ∓ 1 Tagesspanne.
- **Nie gekappt:** weiter als die Grenze des Meisters (Base 8 %, schnelles Setup eine Tagesspanne) = Ampel rot „die
  Meister nehmen den Trade so nicht“. Bis 15.11. kappte die App die Base auf 8 %.
- **Überall beide:** Plan, Chart (Struktur durchgezogen, 1,5 ATR gestrichelt; auch Stundenchart und Short), Lagekarte,
  CRV (Stopp A Struktur, B 1,5 ATR), Stückzahl je Einstieg und je Stopp, Setup-Prüfer, Gleichlauf-Wache (falsche Seite).
- **Gemessen an 143 Setups (468 Titel):** Struktur im Schnitt 7,1 % vom Einstieg; 50 liegen im Tagesrauschen (unter
  1 ATR), 71 enger als 1,5 ATR; 27 weiter als die Grenze des Meisters; 7 mit Lücke. Setups und Einstiege unverändert.
- **Blinder Fleck gefunden:** Kaufzone (1,05) und Marken der Trendvorlage (1,30/0,75) standen in Plan und Chart als
  Kopien – jetzt aus der einen Quelle. Die Inventur sah die Anzeige-Module nicht; rund 40 Regel-Zahlen dort sind Plan 22.

## Gefechtsordnung Schritt 4: Spring/Upthrust und früher Short (15.11.2026)

- **Eine Regel** (`vcp_zone.spring_upthrust`) für Zeichen, Zustand „abgelehnt“ und Setup, an der Zone des Scanners, wie
  sie am Vortag stand: Tief höchstens 1 ATR unter der Unterkante (Upthrust: Hoch über der Oberkante), Schluss zurück in der
  Zone am selben Tag oder in den 2 Tagen danach; ein Fehlausbruch zählt auch. Vorher rechnete das Zeichen mit einer eigenen
  Spanne der letzten 20 Tage.
- **Setups Spring (long) und Upthrust (short):** Einstieg am Rand beim Schluss zurück, Struktur-Stopp am Tief bzw. Hoch des
  Fehlausbruchs, Ziel der andere Rand. Gilt 10 Handelstage, solange der Stopp hält und der andere Rand nicht erreicht ist;
  ★ bis 5 % jenseits des Einstiegs. Volumen und Phase sind Zeichen. Vorrang nach Sprung und Zahlen-Reaktion. Der Chart
  zeigt die Zone, an deren Rand es geschah.
- **Bruch der Spanne vor dem Bruch:** eine Verteilung (Phase 3, mindestens 6 Wochen, höchstens 40 % breit) steht wie der
  Base-Ausbruch schon vor dem Bruch in der Reihe (gelb, im Vorrang hinten). Liegt das Tief der letzten Gegenbewegung mehr
  als 3 % über der Unterkante, ist der Schluss darunter der frühe Short (dann grün); Struktur-Stopp über dem Hoch der
  Gegenbewegung.
- **Eine Liste der Short-Reihen** (`system_kullamaegi.SHORT_REIHEN`, Seite einer Reihe über `lagekarte.richtung`) statt an
  8 Stellen von Hand; die Shorts tragen ihren Einstieg als eigenes Feld.
- **Gemessen an 468 Titeln:** Setup Spring 11, Upthrust 23 (14 grün); Bruch der Spanne vor dem Bruch 65, davon 18 mit
  frühem Short. Zeichen: Spring 47 → 36, Upthrust 41 → 76. 4 Base-Ausbrüche stehen jetzt hinter einem Upthrust (unter „auch“).

## Gefechtsordnung Schritt 5: Stopp am 10er/20er (16.11.2026)

- **Eine Quelle** (`kern/reiten.py`), Kullamägi führt:
  - *Ungleichgewicht* (Zustand): Schluss über dem steigenden 10er bzw. 20er (steigend = höher als vor einer Woche),
    abwärts gespiegelt. Phase und Dow-Struktur stehen als Zeichen daneben (vorher maßen sie das Ungleichgewicht).
  - *Nachgezogener Stopp* (Nach dem Kauf): bis Tag 3 der Anfangsstopp; danach folgt er dem 10er, solange seit Tag 3 kein
    Schluss darunter lag, sonst dem 20er (Wechsel nur von 10 auf 20). Er steigt nur; ein Schluss darunter heißt raus.
  - *Ende-Zeichen*: Mauer höchstens 3 % über dem Kurs, Kraft ohne Weg am oberen Rand, Kauf-Klimax – gemessen wie im
    Zustand – ziehen den Stopp sofort unter das Tief des Tages, an dem das Zeichen kam (Stopp im Markt). Short gespiegelt.
- **Ein System für alle Positionen:** die Trennung M/K in „Nach dem Kauf“ entfällt. Kullamägis Teilgewinn (Tag 3–5) und
  Minervinis Zeichen (Verlustgrenze, Einstand ab 2R, Squat, Tennisball, Reset, Führer) bleiben; sie messen am Stopp, der gilt.
- **Gemessen** (gedachte Position vor 30 Handelstagen, 462 Titel): am 10er 0, am 20er 462 (jeder Titel schloss in den
  27 Tagen mindestens einmal unter dem 10er); raus 215; enger 34 (27 Mauer, 4 Kauf-Klimax, 3 Kraft ohne Weg).
  Zustand: anders bei 82 von 468 – 47 Balance → Ungleichgewicht, 9 Ende des Laufs ↑ → Ungleichgewicht ↓ (Phase 2 im
  Rücksetzer unter dem fallenden 10er).

## Seiten Depot und Performance (16.11.2026)

- **Fünf Seiten in einer Reihe:** Rückenwind · Setups · Titelseite · Depot · Performance (auf schmalem Schirm seitlich
  schieben, kein Umbruch).
- **Depot:** Konto und Risiko (⚙), Depot-Hitze, Verlustbremse, Positionen. Für die gewählte Position: Chart der Position
  (Einstieg blau, Anfangsstopp grau, Stopp jetzt rot – 10er/20er nach Schritt 5 –, Ende-Zeichen gelb, GD10/GD20), „Nach dem
  Kauf“ mit Stückzahl und Knock-out, Knöpfe TradingView → und Deep Dive →, Position ändern oder schließen. Die Depot-Karte
  auf Rückenwind entfällt. Die Setup-Art M/K beim Anlegen einer Position entfällt (ein System).
- **Performance** (`kern/performance.py`, Speicher `einstellungen/performance.json`, nicht in GitHub): Depotwert je
  Freitag und Ein-/Auszahlungen eintragen; die App rechnet die Wochenrendite ohne Einzahlungen, die Ø Wochenrendite
  geometrisch aus den echten Wochen, die Hochrechnung auf ein Jahr (mit Ø und mit der letzten Woche), den Zielpfad nach
  dem Wochenziel, Unterwasser-Phasen (rot ab 10 % wie die Verlustbremse) und die Bilanz der geschlossenen Trades.

## Gefechtsordnung Schritt 8: Phasen als Rahmen (16.11.2026)

- **Phase nach Weinstein** (`kern/phase.py`, `rechnen` → Phase, Zusatz, Basis-Hoch je Woche; Regelstand `phase.REGEL`):
  - *Phase 2* beginnt mit dem Ausbruch: Wochenschluss über dem Hoch der Basis (höchster Wochenschluss seit Beginn der
    Phase 1) und über der 40-Wochen-Linie, die nicht mehr fällt → Wechsel „1 → 2 · Ausbruch“; bestätigt, sobald die
    Linie steigt (über 0,5 % in 4 Wochen). Schluss zurück unter das Basis-Hoch oder die Linie: Ausbruch gescheitert.
    Die frühere 25-%-Regel vom Tief (Minervini) gilt für die Phase nicht mehr, nur noch in der Trendvorlage.
  - *2 · Rücksetzer*: das Phase-2-Bild fehlt, die Linie steigt aber noch (Weinstein: noch Stufe 2). Zwei Stufen:
    *2 · Rückschlag* (ab 15 % unter dem Hoch, unter dem GD10W) geht vor und ist Ende-Zeichen; ein Titel trägt nur eines.
  - *Phase 3* erst, wenn die Linie flach wird; *Phase 4* unverändert; aus Phase 4 immer erst in die Basis (8 Wochen Sperre).
- **Die Stufe gibt dem Kasten den Namen** (`auktion.stufe_name`, im Wort jedes Zustands): Balance in 1 = Basis, 2 =
  Fortsetzung, 3 = Verteilung, 4 = Pause im Fall; Lauf aus 1 = Beginn, in 2 = Fortsetzung, in 3 aufwärts = aus der
  Verteilung, abwärts = Beginn des Falls, in 4 = Fortsetzung des Falls bzw. Gegenbewegung im Fall, in 1 abwärts = Bruch
  der Basis, in 2 abwärts = Gegenbewegung im Anstieg.
- **Gegen die Stufe** (`kartentisch.setup_feststellen`, `GEGEN_STUFE`): Long in Phase 4, Short in Phase 2 – Gegenzeichen,
  höchstens gelb, nie gefiltert.
- **Bruch der Spanne** auch aus einer Balance in Phase 2 (Rücksetzer-Wochen; Phase 3 und Rücksetzer zählen zusammen,
  kürzere Rückkehr ins volle Phase-2-Bild unter 4 Wochen überbrückt) – als Short gegen die Stufe gelb.
- **Kreislaufbild:** Rücksetzer gelbgrün. Der Kartentisch vergleicht Phasen nur bei gleichem Regelstand (kein
  Meldungsschwall „Phase 3 → 2“ am ersten Tag).
- **Gemessen** (462 Titel): Phase 1 / 2 / 3 / 4 = 87 / 102 / 183 / 90 → 39 / 219 / 112 / 92; 102 Titel 3 → 2 (Linie
  steigt noch), 31 Titel 1 → 3; Wechsel „1 → 2 · Ausbruch“ läuft bei 4; Phase 1 über steigender Linie 23 → 3; Phasenwechsel
  in 2 Jahren Median 4 → 3, höchstens 15 → 10. Kartentisch (468): Rückschlag 87, Rücksetzer 12; gegen die Stufe 80
  Setups, davon 22 von grün auf gelb; grün 68 → 47, ★ 40 → 25; Bruch der Spanne 68 → 81 (22 neu, 9 weg – vor dem Bruch,
  die Spanne ist wieder Trend oder breiter als 40 %).

## Plan 9: Pivot, Drittel und Enge (16.11.2026)

- **Minervinis Regel „Enge (VCP)“** verlangt jetzt neben der gelben oder grünen Enge mit mindestens 2 Kontraktionen auch
  höchstens 6 Wellen und ein Volumen der Enge unter dem 50-Tage-Schnitt (`vcp_zone.enge` liefert `trocken` und `wenige`).
  Gemessen (468): Minervini grün 11 → 7 (CBOE 121 %, COKE 114 % und 8 Wellen, CSX 143 %, MEDP), gelb 31 → 27; 4 Titel
  fallen aus „Base-Ausbruch“, weil ihnen nun zwei Regeln fehlen (FTDR, AAPL, MAS, OMC).
- **Schon behoben, nachgemessen:** Drittel aus der Lage in der Zone (Schritt 2), die 1. Kontraktion beginnt am Hoch der
  Zone (329 von 329), ein überschrittener Pivot zählt nicht mehr – es gilt der nächste Einstieg (82 Zonen, Schritt 2).
- **Prüfer irrt:** Zonen unter 5 Wochen mit Pivot (35) sind richtig – Minervini: eine Base ab 3 Wochen (5 Wochen ist
  O'Neils flache Base).

## Plan 10: Volumenprofil der Balance und Basenzählung (16.11.2026)

- **Volumenprofil der Balance** (`avwap.balance_beginn`, `avwap.profil_anker`): die Zone bleibt die Base nach Minervini
  (ab dem Hoch der linken Seite, für alle Setups); das graue Profil folgt Dalton: es beginnt nie vor der Zone, eine Lücke
  ab 2 % (`LUECKE_BALANCE`, rund 3 je Titel und Jahr) beendet die Balance, den langsamen Trend ohne Lücke beendet der Kern
  (Wochen, die ihn nicht berühren). Im Ungleichgewicht („angenommen“, „Ungleichgewicht“, „Ende des Laufs“ –
  `auktion.UNGLEICH`) heißt es „verlassene Balance“. Gemessen (468): Balance 178, Wert wandert 39, verlassene Balance 109,
  seit Zone 42, seit Tief 71, seit Hoch 29; Kartentisch unverändert.
- **Basenzählung** (`basen.py`): Beginn = Beginn der laufenden Phase 2 – neu nach Phase 4 und nach 3 → 2; neu bei 1, wenn
  eine Zone unter das Tief der vorigen Base fällt (IBD; 58-mal); das Markttief setzt nicht mehr zurück
  (`erkennung.letztes_markttief` entfernt). Jede laufende Zone trägt ihre Nummer (auch „noch nicht reif“), in Phase 1 oder
  3 ist sie die 1. Base des neuen Anstiegs, in Phase 4 wird nicht gezählt. Nummer im Kasten („Test am Rand (oben) · Basis
  · 1. Base“), in der Kachel und im Material des Prüfers. Gemessen: 266 × 1., 20 × 2., 2 × 3., 1 × 4.; ohne Nummer 179
  (106 ohne Zone, 68 in Phase 4, 5 zu kurz).

## Plan 15: Kette der Belege (16.11.2026)

- **angenommen → Ungleichgewicht**, sobald der Kurs die Kaufzone verlassen hat (mehr als 5 % über dem Pivot bzw. jenseits
  des Randes, `vcp_zone.KAUFZONE`) und am 10er/20er reitet – nicht erst nach 10 Tagen.
- **angenommen aus dem Market Profile** erst ab 2 Tagen mit dem Tageswert außerhalb der Wertzone (`auktion.MP_TAGE`,
  Dalton); der 1. Tag ist ein Vorstoß (Test am Rand). Der Ausbruch des Scanners über den Pivot bleibt sofort angenommen.
- **Anlass:** Spring = Zwang (gefangene Verkäufer unter dem Rand), Upthrust/Fehlausbruch = Zwang (gefangene Käufer über
  dem Rand), nur solange er gilt; „Verteidiger leer“ nur bei echter Enge (höchstens 10 %, Volumen unter dem Schnitt);
  die Information (Zahlen) nur vor dem Ereignis und in Laufrichtung – sonst Gegenzeichen bzw. Beleg „nach dem Ereignis“.
- **Zahlenreaktion einmal** (`zeichen`): nur die Seite, die der heutige Kurs gegen den Schluss vor den Zahlen zeigt
  (vorher bei 41 Titeln Stärke und Schwäche zugleich).
- Gemessen (468): angenommen 139 → 84, Ungleichgewicht 12 → 34, Ende des Laufs 18 → 30, Test am Rand 53 → 64 (11 Vorstöße),
  abgelehnt 56 → 66; Kartentisch unverändert.

## Plan 16: Gültigkeit der Zone (16.11.2026)

- **Tiefe Zonen (über 33 %)** behalten ihren Pivot (Mickys Konsolidierung darf über 30 % tief sein); die Lücke „über 33 %
  tief, nur im Bärenmarkt üblich (O'Neil)“ steht dabei, Minervini ist dort höchstens gelb (Regel „Reife Base“). Gemessen:
  62 Zonen 33–50 % tief (48 Konsolidierungen nach einem Absturz, 14 Basen).
- **Flache Base nach O'Neil** (`vcp_zone.flache_base`): läuft keine fertige Zone, gilt eine Spanne von mindestens 5 Wochen
  seit ihrem Hoch, höchstens 15 % tief, Kurs höchstens 15 % unter dem 52-Wochen-Hoch, ohne Schluss über der Oberkante und
  nicht nach einem Absturz als Zone (LNTH, UBSI heute). An ihren Rändern entstehen Spring und Upthrust: w_spring 11 → 15,
  w_upthrust 23 → 25.
- **Zonenbeginn hinter einem älteren Hoch** ist eine Regel (Absturz über 50 % oder gescheiterte Tasse) – jetzt im Material
  des Prüfers erklärt.
- Minervini grün 7 → 6, gelb 27 → 26; Kartentisch grün 46 → 49, ★ 25 → 27.

## Kacheln nach dem Regelkatalog (16.11.2026)

- **Eine Quelle:** Jedes Setup im Regelkatalog (`regelkarte.SETUPS`, Feld `kacheln`) sagt, mit welcher Regel die Kacheln
  Trend, Stärke, Fundament und Enge urteilen (`regelkarte.KACHEL_REGELN`, `kachel_regel`). Hat das Setup in einer Kachel
  keine Regel, steht der Wert als Zeichen da (grauer Punkt, „Zeichen, keine Regel des Setups“). Ohne Setup gilt der
  Maßstab des Base-Ausbruchs. Die Meister-Systeme M/K wählen keine Kachel-Regel mehr (`kachel2`, `SYSTEM`, `SYSTEM_JE`,
  `punkt2` und die alten Zwei-System-Wege der Lagekarte entfernt).
- **Je Setup:** Base-Ausbruch: Trendvorlage, RS ab 70, Zahlen wachsen, VCP. Flagge: Kurs über steigendem GD50, Enge der
  Flagge (1–8 Wochen, Volumen leiser als in der Stange, sonst gelb). Momentum-Ausbruch: 3 Wochen über GD50, Führer
  oberste 2 %, Pause 1–3 Wochen. Sprung: Nachricht, hält das Tief des Sprungtags. Zahlen-Reaktion: Kurs über GD50, hält
  Tief und AVWAP. Bärenflagge: GD50 fällt. Alles Übrige (Spring/Upthrust, Ermüdung, Bruch der Spanne, Stärke bei Flagge,
  Sprung und Zahlen-Reaktion) nur Zeichen.
- **Stärke (Plan 24, Micky 16.11.):** der RS-Rang urteilt bei allen Setups außer dem Momentum-Ausbruch (dort Führer,
  oberste 2 %): ab 70 grün, 60–69 gelb; beim Short gespiegelt, der Rang von unten gezählt (`rs_rang.SPIEGEL`): bis 30
  grün, 31–40 gelb. Gemessen: 180 Stärke-Kacheln von Zeichen zu Urteil – 64 grün, 23 gelb, 93 rot; Flagge 26 grün,
  1 gelb, 3 rot (vorher nach Kullamägi 7/8/15); Shorts in noch starken Titeln sind jetzt rot (Bruch der Spanne 54).
- **Wachposten:** meldet rot, wenn ein Setup nicht alle vier Kacheln im Katalog hat oder Katalog und Titelseite
  (`titel.URTEILE`) verschiedene Regeln kennen. Der Setup-Prüfer liest die Kachel-Regeln je Setup im Material.
- Gemessen (462 Titel, Mac-Daten): Trend 146, Stärke 180, Enge 140 Ampeln anders, Fundament, Markt, Setup, Geld und Base
  unverändert; Base-Ausbruch und Titel ohne Setup unverändert. Flagge: Stärke 30 → Zeichen, Enge 10 gelb → grün
  (4–8 Wochen), 8 grün → gelb (Volumen laut). Sprung: Enge 6 → grün (hält das Tief). Die Titelseite zeigt das nach dem
  nächsten Nachtlauf.

## Plan 20: AVWAP letztes höheres Tief (16.11.2026)

- **Zwei Tiefs** (Micky: beide Linien, wie Shannon mehrere Anker übereinander): das **Tief der Bewegung** bleibt das
  Trendstart-Tief (großes Bild, mit dem letzten Hoch die Zange). Neu: das **letzte höhere Tief** (`avwap._hoeheres_tief`,
  Schlüssel `hoeher`) = das Tief des letzten Rückgangs ab 8 % (dieselbe Bestätigung wie beim Hoch), aus dem der Anstieg
  zum letzten Hoch kam – Shannons „most recent and relevant higher low“, unter dem sein Stopp sitzt. Nur nach dem
  Trendstart-Tief und solange der Kurs nicht darunter fiel.
- Chart: grüne Linie, in der Voreinstellung an (Wahlschalter neu: `avwap_anker4`); Prüfer-Material und Regelkarte
  (Prüf-Element „AVWAP letztes höheres Tief“).
- Gemessen (1.865 Titel, Mac-Daten): 328 mit höherem Tief; Kurs im Median 4,5 % über dessen AVWAP (Trendstart-Tief
  20,7 %), Alter im Median 73 Tage. Von 195 Trendstarts älter als ein Jahr haben 87 jetzt die nahe Linie. WST (mit den
  Kursen bis 13.11.): Trendstart 30.01. 223,52 $ (AVWAP 313,46 $), höheres Tief 27.07. 325,06 $ (AVWAP 370,74 $).

## Begriff Flagge (16.11.2026, Plan 25)

- Kullamägi: ein großer Anstieg (30–100 %) **in den letzten 1–3 Monaten**, der **ein paar Tage bis ein paar Wochen
  dauert**. Die 1–3 Monate sagen, wann der Mast war, nicht wie lang er sein darf. Der Katalog las sie als Länge
  („30 % in höchstens 13 Wochen“) – so hieß auch ein Aufwärtstrend mit Pause Flagge (WST: 33 % in 13,0 Wochen).
- Neu (`vcp_zone.FLAGGE_STANGE_W` = 6): Fahnenstange ab 30 % in höchstens 6 Wochen, die Flagge kürzer als ihre Stange
  (klassische Lehre: Bulkowski, Murphy; O'Neils High Tight Flag 100 % in 4–8 Wochen). Meistertexte in Regelkarte,
  Chart- und Setup-Prüfer berichtigt.
- Gemessen (479 Titel): von 123 Flaggen-Zonen hatten 61 eine Stange von 10–13 Wochen. Setup Flagge 30 → 11 (grün 7 → 2);
  die übrigen: 14 ohne Setup, 2 Momentum-Ausbruch, 2 Base-Ausbruch, 1 Bruch der Spanne; Ermüdung 3 → 1. WST ist jetzt
  eine Base (in 6 Wochen nur +22 %).

## AVWAP nach Shannons Werkzeugen (16.11.2026, Plan 26)

- Geprüft gegen Shannon: letztes Hoch (erst nach dem Rückgang), Trendstart-Tief, letztes höheres Tief, Hoch des
  Rückgangs und Zange passen. Neu:
  - **Zahlentag** (`zahlen`) als eigene Linie; **Lücke/Volumen** (`ereignis`) nur noch ohne Zahlen (mehr als 1 Tag
    daneben). Vorher verdrängte die jüngere die ältere – Shannon legt mehrere Ereignisse übereinander.
  - **Börsengang** (`ipo`, `avwap._boersengang`): erster Handelstag, wenn die Kursreihe mehr als 30 Tage nach der des
    Index beginnt. Vorher galt der Rand nie als Anker.
  - **Ausbruch (Handoff)** (`ausbruch`, `avwap._ausbruch`): AVWAP ab dem Tag des laufenden Ausbruchs aus der Zone
    (ohne Fehlausbruch).
- Chart: Voreinstellung letztes Hoch, Trendstart, höheres Tief, Börsengang, Handoff (Wahlschalter `avwap_anker5`;
  Zahlen-Reaktion zusätzlich Zahlentag). Prüfer-Material und Regelkarte mit allen Ankern.
- Gemessen (1.865 Titel): Zahlentag 1.328, Lücke/Volumen 1.626, beide 1.166, Börsengang 90, Handoff 282.

## Urväter: Homma und Wyckoff (17.11.2026, Plan 27)

- Micky prüfte Wyckoff, Weinstein, Livermore, Dow, Keene, Harriman und Homma als Grundgesetz; aufgenommen werden nur
  zwei Lücken.
- **Umkehrkerzen** (Homma, Regeln nach Nison; `zeichen.umkehr`): Hammer, Shooting Star, Engulfing auf- und abwärts,
  Morning und Evening Star – nur nach einem Trend (Vortag gegen 5 Tage davor) und an einer Marke (höchstens 1 ATR von
  52-Wochen-Hoch/-Tief, Rand der Zone oder AVWAP-Linie, `zeichen._marken`). Bestätigt: der nächste Tag schließt
  jenseits des Körpers. Zeichen im Kreislauf (letzte 5 Tage), Kürzel im Chart (blass = nicht bestätigt).
- **Kraft ohne Weg** (Wyckoffs Aufwand ohne Ergebnis; jetzt `zeichen.kraft_ohne_weg`, vorher `auktion.kraft_ohne_weg`
  mit 1,5-fach und 0,7 ATR nur am Zonenrand): Volumen ab 2-fach, Spanne höchstens 70 % des 20-Tage-Schnitts, letzte
  10 Tage, an einer Marke; nach einem Anstieg Schwäche, nach einem Fall Stärke. Kasten der Auktion, Reiten, Zeichen und
  Chart („KW“) nutzen dieselbe Funktion.
- Gemessen (1.865 Titel): 942 Umkehrkerzen an Marken in 10 Tagen (399 bestätigt); Kraft ohne Weg 21 Titel (vorher 42).

## Heiße Titel am Morgen (17.11.2026, Plan 28)

- Nach dem Nachtlauf schickt die App (`auswahl.heisse`, aufgerufen in `werkzeuge/nachtlauf.py`) eine zweite Meldung
  über ntfy: die ersten 5 Long und 5 Short der Liste „Einsatzbereit“ in ihrer Rangfolge (ohne Depot-Plätze), je Zeile
  Ticker, Setup, ★, Einstieg mit Abstand und RS-Rang. Tipp auf die Meldung öffnet die Seite Setups. Ohne
  einsatzbereites Setup steht das in der Meldung.
- Micky 17.11.2026: aufs Handy nur noch diese Meldung und Fehler des Laufs – „Lage steht“ und die gelben Hinweise der
  Wachen entfallen.
- Die geplante Aufgabe „US-Trading-Screener“ (TradingView über Claude) hat Micky gelöscht – es gibt eine Liste, ein
  Regelwerk.

## Zugangsausweis an der Haustür (17.11.2026)

- ntfy fragte bei jedem Tipp auf eine Meldung zweimal nach dem Passwort: Der Browser in ntfy merkt sich die
  Passwortsperre von Caddy nicht, und Streamlit öffnet Seite und Live-Leitung getrennt.
- `werkzeuge/server/ausweis.sh` (einmalig, aus `aktualisieren.sh` und `einrichten.sh`): Nach dem ersten richtigen
  Passwort gibt Caddy dem Gerät einen geheimen Ausweis (Cookie `ic_zugang`, 1 Jahr, nur https, HttpOnly). Mit ihm öffnet
  die Tür ohne Frage; ohne ihn bleibt die Passwortsperre. Nutzer und Passwort bleiben unverändert. Umgebaut wird nur die
  Tür aus `einrichten.sh` (6 Zeilen); vorher prüft `caddy validate`, die alte Datei liegt als `Caddyfile.vor-ausweis`.
- Geprüft mit Caddy 2.8.4: ohne Passwort 401 ohne Ausweis, falsches Passwort 401, richtiges Passwort 200 mit Ausweis,
  Ausweis allein 200, falscher Ausweis 401.

## Inventur Stufe 3 (17.11.2026, Plan 22)

Die Inventur sah bisher nur die Funktionen, die im Regelkatalog stehen. Jetzt prüft sie alle 373 Funktionen aller Module.
Jede Zahl, die etwas entscheidet, hat einen Namen oder führt auf ihre eine Quelle (z. B. `rueckenwind.KURS_NAH` statt
0,97/1,03, `system_minervini.BASE_TIEFE_MAX` im Chart-Prüfer). Reine Gestaltungs- oder Technikzahlen tragen am
Zeilenende `# Layout` bzw. `# Technik` (282 Zeilen); sechs reine Technik-Module (`TECHNIK_MODULE`) sind ausgenommen.
Neu im Katalog: „Kopf und Kacheln der Titelseite“, „Pendel der Übersicht“, „Bänder und Zeichen im Chart“.
Ergebnis: 0 frei, 0 Kopien, 0 ohne Namen. Gegenprobe mit denselben Daten: 462 Titel, 0 Kacheln anders.

## Tiefenanalyse aus der App Titel-Analyse (21.11.2026)

Die Bausteine der App „Titel-Analyse“ stehen jetzt im Cockpit (Rechnung in `kern/tiefe.py`, Seite `oberflaeche/analyse_seite.py`).
Quelle: TitelAnalyse/LIESMICH.md und kern/rechnen.py, bericht.py, chart.py (Stand 20.11.2026). Mickys Entscheidungen:

| Baustein | Regel |
|---|---|
| Balance | Cockpit (Blöcke zu 5 Tagen am Kern, Lücke ab 2 % beendet, bis 65 Wochen) |
| Profil, Wertzone 70 % | Titel-Analyse: Stundenkerzen ab dem Anker, Stufen 0,25 %; Anker = Zahlentag, wenn ≥ 1 ATR und höchstens 10 Kerzen vor der Balance, sonst Cockpit-Anker. Das ist jetzt auch das graue Volumenprofil (`volumenprofil.verankert`) |
| Dünne Zonen, Dochte | unter ⅓ des POC-Volumens ab 2 Stufen; dünne Ränder = Dochte |
| Alte Wertzone | Titel-Analyse: letzte Balance ab 10 Kerzen vor dem Anker |
| Pivot | beide: Rand der Balance (long/short) neben dem Pivot der Enge |
| Quetschung | Titel-Analyse: Drittel seit dem Anker, Hochs höchstens 2 % auseinander; gespiegelt für Short (`zeichen.einquetschung`) |
| Spring/Upthrust, Fehlausbruch | Cockpit |
| AVWAP | Anker des Cockpits; neu die Zangen-Messung (vor 5 Tagen → heute) |
| Stärke in der Schwäche | beide: an den Distributionstagen des S&P 500 besser als der Index, dazu die Cockpit-Regel |
| Geldfluss | Rückenwind bleibt; neu die Rangtabelle der 11 Sektoren und CMF 20 |
| Wertwanderung | beide Treppen (Tages-POCs, Wochen-Wertzone), 6 Klassen (innen ▬, außen ◇ getrennt) |
| Zeichenliste | im ganzen Cockpit (`gestaltung.ZEICHEN_LISTE`): ★ → 💥, 🎯 → 💥 bzw. 🦬/🐻 in der Meldung, ⚡ → 🔥, ⚑ → 🌞, ✓/✗ → 🟢/🔴, ⚠ → 🟡/🔴/🦊 | · seit 23.11.2026: 💥 → 🦬 (Micky: der Bulle statt des Knalls; am unteren Rand der Balance 🐻)
| Einschätzung | Stratege mit Websuche (höchstens 8 Suchen): long, short, abwarten mit Tendenz, kein Schuss; Unternehmen, Quartal, Wettbewerber, Fazit, Quellen; der Code prüft jede Antwort |

Wo: Seite **Analyse** (alle Aussagezeilen, Einschätzung darunter), **Chart** der Titelseite mit Reitern Woche/Tag/Stunde (Tag
vorausgewählt; der Stundenchart der letzten 10 Tage entfällt) und Dalton-Flächen, PbD, POC je Kerze, nackten POCs;
**Kartentisch** mit einer Zeile Zeichen je Titel (PbD-Form und D-Kante, Quetschung, CMF, Abgabetage, Wanderung).

## Freie Bahn ✈️ (22.11.2026)
Livermores Linie des geringsten Widerstands als Zeichen: ✈️ = im Tageschart keine Festung (alte Decke, Boden → Decke)
über dem Kurs, ✈️↓ = keine darunter (`zonen.frei`). Reines Zeichen ohne Schwelle – wie leicht der Kurs läuft, zeigen
Pivot, Volumen-Spur, 🏜️ und Kraft ohne Weg. Festungen und ✈️ blicken zwei Jahre zurück (`zonen.BAHN_JAHRE`; so weit
reichen die Massive-Tage), damit Chart, Liste und Titelseite dieselben Festungen sehen. Liste: Spalte „Bahn“
(`rueckenwind.rechnen` → `frei`, aus `massive.kursmatrix` mit mehreren Spalten in einem Durchgang); Titelseite: im Kopf,
live gerechnet. Stand Mac 04.11.: 133 Titel ✈️, 20 ✈️↓ von 1.868.

## Handbuch „Der Zirkel" (22.11.2026)
Langfassung als Doc (https://claude.ai/artifact/Kb2mfjctjSSbq5AADEA8WU): je Wort Herkunft, Geschichte und Psychologie,
Leben und Sport, die Meister, das Zeichen im Cockpit – Stärke, Schwäche, Momentum, Trend, Balance, Disbalance,
Widerstand, Reibung, Zirkel. Kurzfassung als Tabelle in `oberflaeche/handbuch.py`, auf der Seite Rückenwind
aufklappbar („📖 Handbuch: Der Zirkel“), und im Konzept-Doc.

## Der Zirkel im Chart (22.11.2026)
`zonenchart.bild` zeigt zusätzlich: Wendepunkte (Schwunghochs und -tiefs, `vcp_zone.zigzag` ab 2 ATR – seit 23.11.2026 nicht mehr „Pivotal Points“ genannt, der eine Pivot steht als Raute ◆ auf seinem Wendepunkt; hohl = noch
nicht bestätigt), die Kontraktionen der Enge als „−20 %“ unter ihrem Tief (Woche und Tag, aus `zonen.basis`),
✈️/✈️↓ freie Bahn als Etikett, darunter die Zeichenleiste (🦬 Ausbruch, 🦊 Fehlausbruch, 🏜️ leisestes Volumen seit 50
Kerzen, ⚡ Kraft ohne Weg nach Wyckoff, 🌱/🍂 Keim des Zirkels an der letzten Kerze) und Momentum 🚀 am Ende der
RS-Linie. Je Zeichen ein Hinweistext beim Darüberfahren; Legende ergänzt.

## Zirkel-Lauf statt Kartentisch (22.11.2026, Stufe A)
Nachtlauf-Schritt „Zirkel“ (`kern/zirkel.py`) für Revier und Watchlist: Kreislauf (Phase, Zeichen, Keime), Zonen-Trade
der Tagesebene (dieselbe Regel wie Titelseite und Chart: `zonen.basis`, `lage(…, profil=False)`, `trade`) und 52-Wochen-
Hoch/-Tief. Abgelegt mit dem Kreislauf in `daten/kreislauf/<stand>.json` (`titel`, `feld`, `barometer`). Leser: Markt-Ampel
(Hochs/Tiefs), Gruppen-Listen und Spalte „Trade“ der Liste (`rueckenwind_seite.setups`), Morgenmeldung (`zirkel.heisse`:
bis 5 Long am Pivot/im Ausbruch/im Rücktest aus Garde, Angriff, Vorhut; bis 5 Short am Bruch), Stratege (Trade statt
Setup-Reihe). Entfernt: Kartentisch-Schritt, Wachen, Auswahl „Einsatzbereit“, Chart- und Setup-Prüfer, Mängelliste
(Werkstatt, Entscheidung 21.11.). Schrank als eigener Schritt (`nachtlauf.schrank_liste`, `titel.vorbauen`).
Stufe B (22.11.2026, erledigt): Der Stratege liest dieselbe Fährte wie Titelseite und Chart (`strategen.material(tk,
r, …)` mit Zirkel, Zone/Phase je Ebene, Festungen, ✈️, Trade, Klasse); der Schrank legt die heutige Titelseite ab
(`zonenseite.vorbauen/abgelegt`, `daten/schrank/`). Entfernt: `kartentisch.py`, die alte Titelseite (`titel.seite_titel`
mit Kacheln und Setup-Reihen), `lagekarte`, `rudelkarte`, `kreislaufbild`, `stopps`, `basen`, `datenpruefung`,
`system_minervini`, `system_kullamaegi`, `rs_rang`, `fuehrer_rang` (Nachtlauf-Schritt „RS-Rang, Führer-Rang“ – niemand las
die Dateien mehr), dazu die toten Funktionen (Short-Formen, Setup-Einstiege, alte Kacheln). `titel.py` hält nur noch
TradingView-Link, Rückenwind-Eintrag und Markt-Ampel. Datenstand-Wache: Teil „Zirkel“ (Kurstag des Zirkel-Laufs).

## Setup aus dem Zirkel (22.11.2026)
„Unser Setup ergibt sich aus unserem Zirkel“ (Micky): `zirkel.setup(trade, zirkel)` macht aus dem Zonen-Trade der
Tagesebene ein Setup – nur im Einklang mit der Phase des Zirkels und bestätigt durch Stärke bzw. Schwäche (Stärke =
Widerstand überwinden, Druck aushalten; ein Keim zählt nur gemessen): 1 Basis + Ausbruch/Pivot + 🌱 oder Wechsel 1→2 =
Aufbruch · 2 Aufwärts ohne 🍂 = Fortsetzung · Rücktest in 2 bzw. 1→2 = Rücktest · 3 Verteilung + Bruch mit Volumen + 🍂
oder Wechsel 3→4 = Abbruch · 4 Abwärts + Bruch ohne 🌱 = Fortsetzung abwärts; junge Titel ohne Zirkel: Aufbruch/Rücktest.
Gegen den Zirkel: kein Setup, nicht gezeigt (Titelseite „kein Setup“, der Chart zeichnet die Linien der Zone trotzdem, beschriftet „kein Setup“, nicht in Liste und Meldung).
Mac 04.11., 304 Titel: 174 Zonen-Trades → 42 Setups (19 Aufbruch, 21 Fortsetzung, 2 Abbruch).
Zirkel-Datei je Lauftag (`daten/kreislauf/<Lauftag>.json`, die jüngste gilt), Kurstag darin für die Datenstand-Wache.

## Die ganze App auf dem Zirkel: Führung und Markt-Ampel (23.11.2026)
Micky: „Zirkel ersetzt alles“ (Führung) und „Zirkel ersetzt O'Neil“ (Markt). Damit läuft die Kette Markt → Strömung →
Zirkel → Zone → Setup → Führung ganz über unseren Zirkel.

**Führung nach dem Kauf** (`depot._nach_dem_kauf`, long; short gespiegelt):
- Stopp beim Kauf = der Stopp des Setups. Das Formular „＋ Position“ gibt Seite, Einstieg und Stopp aus dem Setup vor
  (`depot.aus_setup`); die Position merkt sich den Pivot des Setups (short: die Unterkante, `zonen.trade` → `pivot`).
- Ab Tag 3 folgt der Stopp dem 10er bzw. 20er (`reiten.nachgezogen`), Schluss darunter = raus.
- Reibung: Mauer, Kraft ohne Weg und Klimax ziehen ihn unter das Tief jenes Tages.
- Zirkel: 🟢 Phase 2 (bzw. Wechsel 1 → 2) ohne 🍂 – laufen lassen · 🟡 🍂 gemessen in Phase 2 – Stopp eng unter das
  Tagestief · 🔴 Wechsel 2 → 3 läuft oder Phase 3/4 – raus · 🔴 Basis bricht (Phase 1 → 4) – raus · grau ohne Zirkel.
- Pivot: 🔴 Schluss zurück unter dem Pivot – der Widerstand ist nicht überwunden, raus.
- Entfernt: Teilgewinn Tag 3–5, 8-%-Verlustgrenze, Einstand ab 2R, Squat, Tennisball, Reset, „Führer +20 %“.
  Kriegskasse bleibt: 1 % Risiko je Trade, Depot-Hitze, Klumpen, Verlustbremse.
- Der Zirkel-Lauf rechnet die Positionen des Depots mit (`zirkel.liste`: Revier, Watchlist, Depot).

**Markt-Ampel** (`zirkel.markt_ampel`, `zirkel.markt`): der Zirkel von S&P 500 (SPY) und Nasdaq (QQQ) aus ihrem eigenen
Kreislauf, ohne Zeichen relativ zum Markt (`zeichen.zirkel_index`); der S&P 500 bestimmt, der Nasdaq steht daneben.
🟢 Angriff: Phase 2 ohne 🍂, Phase 1 mit 🌱 bzw. Wechsel 1 → 2 · 🟡 Vorsicht: Phase 2 mit 🍂, Phase 1 ohne 🌱, Phase 3
ohne 🍂, Phase 4 mit 🌱 · 🔴 Rückzug: Phase 3 mit 🍂 bzw. Wechsel 3 → 4, Phase 4 ohne 🌱. Darunter Hochs gegen Tiefs;
aufklappbar je Index alle Zeichen, die tragen, und die Keime. Gerechnet im Zirkel-Lauf (`barometer.index`). Das
Korrekturfenster für „Stärke in der Schwäche“ öffnet, wenn die Ampel nicht 🟢 steht (vorher O'Neils Ampel). Die
Druck-Tage des Index (O'Neils Distributionstage) bleiben nur als Messung der Stärke in der Schwäche (`tiefe.abgabetage`).
Entfernt: `marktrichtung.py`, `marktklima.py`, `auktion.markt`, der Kasten „Zustand des Marktes“, `marktdaten.yahoo_ohlc`.
Mac 04.11.: S&P 500 Phase 2 ohne Keim = 🟢 Angriff; Nasdaq Phase 2 · Rücksetzer mit 🍂 (Evening Star, 5 Abgabetage) = 🟡.


## Wendepunkte, Pivot und Base an den Quellen geprüft (23.11.2026)
- **Wendepunkte** (`vcp_zone.zigzag`): ein Extrem zählt, sobald der Kurs 2 ATR dagegen gelaufen ist – Livermores
  Kursbuch (Natural Rally/Reaction ab etwa 6 Punkten) in der Schwankung des Titels; in der Wissenschaft „Directional
  Change“. Die 2 ATR und die 1 ATR der letzten Kontraktion sind unsere Zahlen, ungemessen, so gekennzeichnet.
- **Pivot nach Minervinis Dritteln** (`vcp_zone.drittel`, Micky 23.11.2026): liegt das Hoch der letzten Enge im oberen
  Drittel der Base, ist es der Pivot (O'Neils Henkel – der Kaufpunkt liegt fast immer unter dem Hoch der Base); im
  mittleren Drittel Cheat, im unteren Low Cheat – dann ist die Oberkante der Pivot. Vorher galt die Enge nur bis 3 %
  unter der Oberkante. Mac 04.11., 300 Titel: 150 Basen mit Enge, bei 11 rückt der Pivot an den Henkel (z. B. ABNB
  179,13 statt 193,45).
- **Belegt:** obere Hälfte (O'Neil: Henkel in der oberen Hälfte), 65 Wochen (O'Neil: Tasse 7–65 Wochen); die
  Untergrenze von 3 Wochen für alle Basen ist unsere.
- **Livermores Secondary:** Wendepunkte ohne neues Extrem zeichnet der Chart kleiner und blasser
  (`vcp_zone.secondary`); als Zeichen (`zeichen.secondary`, Wendepunkt höchstens 20 Tage alt): nach einem neuen Hoch
  hält die Reaktion über dem letzten Tief = Stärke, gespiegelt Schwäche. Mac: 42 Stärke, 48 Schwäche in 300 Titeln.

## Branchen auf dem Zirkel (23.11.2026)
Micky: die Lage der Gruppen spricht dieselbe Sprache wie Markt und Titel (Weinstein: erst der Markt, dann die Gruppe,
dann der Titel). `rueckenwind._gruppen_index` baut je Gruppe (Sektor, Branche, Thema, ab 5 Titeln) einen
gleichgewichteten Kerzen-Index aus den Massive-Tagen der Mitglieder (zwei Jahre; Eröffnung, Hoch, Tief je gegen den
Vortagesschluss, Volumen als Summe); `rueckenwind._gruppen_zirkel` rechnet daraus den Kreislauf mit den Zeichen relativ
zum S&P 500 (in mehreren Prozessen) → `g["zirkel"]`. Die Spalte „Lage“ der Wetterkarte zeigt ihn statt des
Auktions-Zustands (`auktion.gruppe` entfernt, ebenso `zustandsbild.pille`), Rotation, Breite und Geld bleiben als
Zeichen. Titelseite: „Branche 2 (Aufwärts)“ in der Zeile Rückenwind. Gegenwind (`zirkel.gegenwind`): steht die Branche
gegen die Richtung eines Setups (long in 3/4, short in 1/2, außer der Wechsel läuft schon in die Richtung), trägt das
Setup „🟡 Branche …“ – Titelseite, Liste, Morgenmeldung; nicht gefiltert. Mac 04.11.: 186 Gruppen, alle mit Zirkel,
Rückenwind-Lauf 57 s.

## Zustandsmaschine nach Auktionsart entfernt (23.11.2026)
Micky: aufräumen – die App urteilt mit dem Zirkel. `kern/auktion.py` (Anlass → Balance → Test am Rand → abgelehnt |
angenommen → Ungleichgewicht → Ende des Laufs, für Titel, Gruppe, Markt) ist entfernt, ebenso die Klimax-Zeichen der
alten Erkennung (`erkennung.klimax`), `reiten.ungleichgewicht` und die Kästen der Regelkarte für den Titel. Die Klimax
für die Reibung nach dem Kauf misst jetzt `reiten.klimax_tag` (unverändert übernommen, ebenso `MAUER_NAH`).
Bleiben bewusst neben dem Zirkel: die Rotation der Gruppen als Strömung (Geld-Ampel, Ordnung der Wetterkarte) und die
Schlachtordnung der Titel (Garde … Rückzug) – Micky 23.11.2026.

## Watchlist und Trade, Abgleich mit TradingView in beide Richtungen (23.11.2026)

- Zwei Listen wie in TradingView: **Watchlist ◆** und **Trade 🎯** (`kern/watchlists.py`: `LISTEN`, `liste(name)`,
  `zeichen(tk)`). `alle()` gibt beide zusammen (Abendlauf, Zirkel, Schrank). Ein Titel auf keiner Liste mehr wird
  vergessen (`tpo_daten.vergessen`), egal ob in der App oder in TradingView herausgenommen (Micky: „auch aus der App“).
- Titelseite: zwei Knöpfe „☆/★ Watchlist“ und „☆/🎯 Trade“. Übersicht: je Liste ein Fenster zum Einfügen und Herausnehmen.
  Rückenwind: Umschalter Alle · Watchlist ◆ · Trade 🎯; die Marken kommen frisch aus der Datei (nicht mehr aus dem Lauf).
- Abgleich: Die Claude-Aufgabe (stündlich 8–23 Uhr, Minute 13) vergleicht App (`watchlists.json`), TradingView und den
  letzten gemeinsamen Stand (`tv_abgleich.json`, Zweig `daten`). Wer etwas geändert hat, ergibt sich aus dem Stand:
  App neu/entfernt → in TradingView eintragen/entfernen; TradingView neu/entfernt → als `von_tv.json` auf den Zweig `daten`.
  Erster Lauf einer Liste ohne Stand: nur zusammenführen, nichts entfernen. Abschnitte (###) und Indizes bleiben unberührt.
- Der Server (`werkzeuge/server/watchlist_ablegen.sh`, alle 10 Minuten) übernimmt `von_tv.json` mit
  `werkzeuge/von_tv_anwenden.py` (als Benutzer cockpit, jeder Stand nur einmal), löscht sie und legt die Listen ab.
  `aktualisieren.sh` hält das Skript auf dem Stand des Speichers. Steht `von_tv.json` noch auf dem Zweig, wartet die
  Aufgabe (sonst hielte sie die noch nicht übernommenen Titel für in der App entfernt). Verzögerung bis etwa 1 Stunde.

## Markt-Kachel in zwei Spalten, Pivot als eigene Linie (23.11.2026)

- Markt-Kachel (① Lage): S&P 500 (führt) und Nasdaq nebeneinander – je Ampel, Phase, 🍂/🌱 Keim und 🪨 was trägt
  (`uebersicht._markt_spalten`), darunter Hochs : Tiefs; die lange Erklärung unter „Instrumente“.
- Chart: der Pivot als gestrichelte weiße Linie vom Zonenbeginn bis zum Rand, rechts „Pivot x“ („= Oberkante“, wenn er
  auf der Kante liegt; Auslöser/Einstieg am Pivot nicht doppelt). Ohne Setup blass „möglicher Pivot“. Raute bleibt.
- ▲▲▲ dreifacher Rückenwind am Long-Setup (23.11.2026): Kurs (Garde/Angriff), Geld-Ampel und Zahlen-Ampel grün
  (`rueckenwind.dreifach`, `zirkel.dreifach`) – in der Setup-Karte der Titelseite, in der Spalte „Setup“ und in der
  Morgenmeldung; dort kommen ▲▲▲-Setups zuerst. Kein Filter.
- Rückenwind-Liste, Spalte „Keim“ (23.11.2026): hinter dem Riss 🍂/🌱 steht 🪨 und die Zahl der Zeichen, die die
  Phase tragen – „🍂 Käufer erschöpft · 🪨 4“ ist eine Welle im Aufwärtslauf, das Kippen steht erst als „→ 3“ in der Phase.
- Eigene Liste „▲▲▲ Dreifacher Rückenwind“ oben auf der Seite Rückenwind (23.11.2026, `rueckenwind_seite.dreifach_block`):
  🎯 Schlagbereit (Long-Setup am Pivot, im Ausbruch, im Rücktest – mit Einstieg, Stopp, Risiko, Gegenwind) · ⏳ Auf der
  Lauer (Base im Aufbau/Rücksetzer – Pivot und Abstand) · 🏃 Enteilt oder ohne Base. Der Zirkel-Lauf legt dafür je Titel
  Pivot und Kurs ins Feld (ab dem nächsten Lauf).
- Titelliste übersichtlich (23.11.2026): je Klasse der Schlachtordnung ein Abschnitt (Garde und Angriff offen), 10 Spalten
  als Zeichen – Titel (◆ 🎯 ▲▲▲) · Phase · Setup · Keim (🍂 · 🪨 n) · RS (🦈, Pfeil, Steigung 4 Wo.) · Momentum (🚀, ↑/↓ je
  1M 3M 6M) · Volumen (Ampel, Faktor, 🏜️) · Geld (Ampel, 🐺) · Zahlen (Ampel, 📅 Termin bis 14 Tage) · Hoch. Erklärung an
  der Spaltenüberschrift (`SPALTEN_HILFE`). Sektor, Branche, Thema, letzte Zahlen und Zahlen im Einzelnen stehen jetzt in
  der Rückenwind-Zeile der Titelseite (`titel_zeile`); Rang und Prozente des Momentums standen dort schon.
- ✈️ freie Bahn wieder als Spalte „Bahn“ in der Titelliste, in der Rückenwind-Zeile der Titelseite und in der ▲▲▲-Liste
  (Micky 23.11.2026: nicht nur im Chart).
- Titelseite (23.11.2026): die Rückenwind-Zeile ist jetzt drei Karten (`rueckenwind_seite.titel_karten`) – ⚔️ Front (Klasse,
  🦈, RS-Linie, Rang, Momentum, Hoch, ✈️), 💰 Nachschub (Volumen, Sektor, Branche mit Zirkel, Thema, 🐺), 📊 Fundament
  (nächste Zahlen, letzte Zahlen, im Einzelnen), je mit eigener Ampel; drei Mal grün = ▲▲▲.
- Update ohne Warten (23.11.2026): `aktualisieren.sh` wartet nicht mehr auf den Schrank-Lauf (`nachtlauf.py --laeuft`
  entfernt) – neuer Code kommt spätestens 5 Minuten nach dem Hochladen; der Schrank füllt sich danach mit dem neuen Code.
- Chart (23.11.2026): die Kontraktionen der Base in der Farbe ihres Urteils – grün höchstens 70 % so tief wie die vorige
  (`vcp_zone.SCHRUMPF`), gelb kaum kleiner, rot tiefer, grau die erste; neben dem Namen der Zone das Urteil der Enge
  („VCP 🟢 schrumpft“, „🔴 keine saubere Enge – letzte Welle tiefer“, „🟡 Enge: …“ mit den ersten Gründen).
- Aufsteigende Base (O'Neil, 23.11.2026, Anlass WWW): `vcp_zone.aufsteigende_base` – auf der rechten Seite mindestens drei
  Rücksetzer nacheinander, je 10–20 % tief (`AUF_TIEFE`, `AUF_ZAHL`), jedes Tief und Hoch über dem vorigen. Dann im Chart
  „🟢 Aufsteigende Base (O'Neil)“ an der Zone und die Wellen grün, wenn ihr Tief über dem vorigen liegt (sonst rot); die
  VCP-Prüfung gilt für alle anderen Basen unverändert. Quelle: O'Neil, How to Make Money in Stocks (IBD).
- Titelliste nach den drei Fragen geordnet (24.11.2026): Titel | Phase | Setup | Keim ‖ ⚔️ Front (Ampel) | RS | Momentum |
  Hoch | Bahn ‖ 💰 Nachschub (Geld-Ampel, 🐺) | Volumen ‖ 📊 Fundament (Zahlen-Ampel, 📅). `front_ampel` eine Regel für
  Liste und Titelseite.
- Chart (24.11.2026): Volumen-Schnitt als weiße Linie (50 Tage, Woche 10 Wochen, Stunde 50 Stunden; `VOL_SCHNITT`), die
  Volumen-Achse reicht bis zum 3-fachen des höchsten Schnitts (`VOL_DECKEL`, Ausreißer abgeschnitten); unter dem Profil sein
  Zeitraum („31.07.25 – 04.11.26 · 319 Handelstage“); Zahlentage als „E“ in der Zeichenleiste (Maus: Reaktion am Tag und
  danach, `_zahlentage` aus dem Zwischenspeicher), rechts „📅 Zahlen 27.01. · in 65 T.“. Titelseite: Knopf ⛶ öffnet den
  Chart in einer Großansicht (96 % der Bildschirmbreite).
- Chart entrümpelt (24.11.2026): Urteil der Enge kurz („🟢 VCP“, „🟡 Enge“, „🔴 Enge“, „🟢 Aufsteigende Base“, Gründe beim
  Darüberfahren, nie über den Rand); unter dem Profil „16.10.26–20.11.26 · 26 T.“, „Volumen · Ø 50“, „📅 18.02. · 86 T.“ –
  alles in der Breite des Profils; die Etiketten rechts bleiben im Kursbereich (nächster freier Platz darüber oder darunter).
- Halt der Phase (24.11.2026, statt der Spalte „Keim“): `zeichen.halt` → 🏰 hält (kein Keim) · 🌊 Welle (Keim wiegt weniger
  als das, was trägt) · ⛈️ Sturm (Keim wiegt mindestens so viel oder der Wechsel zeichnet sich ab), dahinter der stärkste
  Grund in Klartext (`zeichen.KLARTEXT`, `klartext`). Gewichte aus dem Kreislauf (`gewicht_keim`, `gewicht_traegt`; ältere
  Läufe: Zahl der Zeichen). Überall: Spalte „Halt“ der Titelliste und der ▲▲▲-Liste, Zirkel der Titelseite, rechts in der
  Zeichenleiste des Charts, Branchen-Pillen, Morgenmeldung, Markt-Kachel („dagegen:“ / „trägt:“ in Klartext).
  🍂/🌱 bleiben nur an den einzelnen Zeichen der Titelseite.
- Datenstand-Wache (24.11.2026): prüft statt der nicht mehr gepflegten Datei ^GSPC_ohlc die Indizes der Markt-Ampel (SPY,
  QQQ aus dem Kursspeicher) und die Sektor-ETFs von Yahoo – der rote Hinweis „abweichend Marktdaten (Indizes) Fr 20.11.“
  war ein Fehlalarm.
- Kontraktionen grafisch (24.11.2026): statt der Prozentzahlen ein Trichter in der Base (Linie über die Hochs, Linie unter
  die Tiefs der Wellen der rechten Seite, Fläche dazwischen; Farbe = Urteil der Enge, grün auch bei aufsteigender Base) und
  unter der RS-Linie die Leiste „Wellen der Base“: ein Balken je Welle, so hoch wie ihre Tiefe, gefärbt wie bisher die
  Zahlen (grün kleiner, gelb kaum, rot tiefer; aufsteigende Base: grün = Tief über dem vorigen). Die Tiefe steht beim
  Darüberfahren.
- Enge je Kerze (24.11.2026, statt der farbigen Wellenbalken): unter der RS-Linie ein Balken je Kerze in einer Farbe, so
  hoch wie die Spanne Hoch–Tief in % des Schlusses (Achse bis zum 95. Perzentil, `ENGE_DECKEL`) – kleiner = enger, gleich
  hoch = gleichmäßig; auf allen Ebenen; weiße Linie = Schnitt über 10 Kerzen (`ENGE_SCHNITT`). Der Trichter bleibt.
- Korridor der Enge (24.11.2026, statt der Balken unter der RS-Linie) = Bollinger-Bänder 20/2 (`ENGE_SCHNITT`, `ENGE_SD`):
  sonst blass; leuchtet er, ist die Weite (BandWidth) so schmal wie seit ~6 Monaten nicht (`SQUEEZE_RUECK`: 125 Tage, 26 Wochen –
  Bollingers Squeeze, „Feder gespannt“). Der erste Schluss über/unter dem Band danach bekommt ▲/▼ (`SPRUNG_FARBE`, „Feder
  springt“); Bollinger warnt vor der Finte (Head Fake). Vorher ±halbe Spanne über 10 Kerzen – zu eng, drei von vier Schlüssen
  lagen außerhalb.- Bollinger als Schalter (24.11.2026): Korridor, Squeeze und ▲/▼ erscheinen nur, wenn unter „Einblenden“ (vorher „Profil“)
  „Bollinger“ gewählt ist (`LINIEN_WAHL`); Grundstellung aus.
- Großansicht als Vollbild (24.11.2026): der Wähler traf die Box nicht (sie ist eine section) – jetzt `[role="dialog"]`, 98 %
  der Breite, und der Chart wird höchstens so hoch wie der Bildschirm minus `GROSS_RAND`, sodass er ganz hineinpasst.
- Trichter als Schalter (24.11.2026): unter „Einblenden“ wie Bollinger, Grundstellung an (`LINIEN_START`).
- Zickzack (24.11.2026): feine Linie durch alle Wendepunkte (ab 2 × ATR) über den ganzen Chart, eigener Schalter
  „Zickzack“ unter „Einblenden“, Grundstellung aus (`ZICK_BREITE`, `ZICK_DECK`) – zeigt die Wellen selbst, der Trichter bleibt die Hülle der rechten Seite.
- Kanal um den Zickzack (24.11.2026, am Schalter „Zickzack“): Linie durch die letzten zwei bestätigten Schwunghochs und eine
  durch die letzten zwei Schwungtiefs, bis zum rechten Rand – nicht erzwungen parallel (Brooks: parallel, zusammen- oder
  auseinanderlaufend). Am Ende steht die Form: Kanal (Breite ±20 %, `KANAL_TOLERANZ`), Trichter (enger), Megafon (weiter).
