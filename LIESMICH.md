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
  - `marktrichtung.py` – Marktrichtung nach O'Neil: Distributionstage, Erholungsversuch, Follow-Through-Day (S&P 500 und Nasdaq, Gegenprobe des Volumens mit Massive)
  - `rudel.py` – Rudel (Branchen-Breite), Kursverwandte, Themen-Gruppen, Mansfield-RS (Speicher in `daten/rudel/`)
  - `massive.py` – Tageskurse aller US-Aktien von Massive (eine Anfrage je Tag, Speicher in `daten/massive/`)
  - `sic13.py` – SIC-13 · Sovereign Investment Compass (Mickys Raster): elf Kriterien in fünf Ebenen für jeden Titel, gemessen (RS, Risiko-History, Fonds-Fußabdruck, Krisen-Resistenz, Pricing Power, Zahlenproben) und eingeschätzt (`daten/sic13/einschaetzung.json`, von Claude für alle 1.884 Titel, 03.11.2026); TradingView-Kennzahlen aus `daten/tv/revier.csv`
  - `namen_de.py` – deutsche Namen der Sektoren und Branchen; deutsche Unternehmensbeschreibungen aus `daten/steckbrief_de/beschreibungen.json` (von Claude aus Yahoos englischem Text übertragen, 03.11.2026 für alle 1.884 Titel; neue Titel ergänzt der Nachtlauf)
  - später: `risiko.py`
- `oberflaeche/` – alles Sichtbare als HTML/SVG nach der Designvorlage: `gestaltung.py` (Farben, Bausteine), `chart.py` (Chart), `titel.py` (Titelseite), `uebersicht.py` (Lage am Abend), `frontkarte.py` (Rotationsbild der Sektoren und Themen-Gruppen), `uebergaenge.py` (Tafel „Übergänge“: Quad-Türen, Sektoren und Themen-Gruppen an der Tür, Haken, Breite je Gruppe), `rudelkarte.py` (Rudel und Kursverwandte auf der Titelseite), `stimmung.py` (Stimmungskurve)
- `kern/daten.py` – Kurse und Steckbrief von Yahoo, Speicher in `daten/kurse/`
- `daten/` – Kursspeicher der App, je Titel eine Datei, wird nur ergänzt
- `einstellungen/` – Watchlists, Revier, eigene Einstellungen; optional `sec_kontakt.txt` (Absender für die SEC); `fred_schluessel.txt` (FRED-Schlüssel); `breite.txt` (515 große US-Werte für die Marktbreite), `revier.csv` (Revier: Ticker, Sektor, Branche, Sektor-ETF, Börsenwert, Umsatz), `massive_schluessel.txt` (Massive-Schlüssel)
- `werkzeuge/` – Hilfsprogramme: `vorschau.py HWM` (Titelseite als HTML-Datei in `vorschau/`), `fundament_test.py` (Ampeln für einzelne Titel), `lage_test.py` (Pendel und Quadrant an Prüftagen), `sektoren_test.py` (bekannte Rotationen 2008–2023), `daten_test.py` (Datenampel), `revier_bauen.py` (Revier neu bauen: NASDAQ-Liste + Umsatz von Massive, eine Aktiengattung je Firma), `branchen_nachtragen.py` (Sektoren von Yahoo nachtragen), `markt_test.py` (Marktrichtung an den Tops und Böden aus O'Neils Buch), `historie_laden.py` (ein Jahr Tageskurse aller US-Aktien von Massive, einmalig), `rudel_test.py` (Abnahme Schritt 4)
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
`erkennung._base_zaehlt`: eine Pause bis zum neuen Hoch zählt als Base ab `BASE_MIN_RUECK` = 5 % Rücksetzer, `BASE_MIN_TAGE` = 20 Tage vom linken Rand (Hochs bis 2,5 % darunter) und `BASE_MIN_SEIT_HOCH` = 15 Tage ab dem Hoch – gilt für `basenzahl`, `basen_historie` und damit Chart und Tabelle „Frühere Basen“. `vorige_base` (Base auf Base) nutzt `streng=True` (alte Abgrenzung 4 Wochen ab Hoch, 10 %). Prüfgalerie danach unverändert (🟢427 🟡53 🔴24 ⚪84). Im Chart steht ✓/✗ über der Kerze, wenn der Ausbruch auf einen Zahlentag fällt.

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

Ein Klick auf eine Karte öffnet die Titelseite. Nur den Kartentisch rechnen: `python3 werkzeuge/tpo_laden.py kartentisch`.

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
- Claudes Teil (geplante Aufgabe Di–Sa 00:37 Uhr, braucht Mac an und Claude-App): TradingView-Kennzahlen nach
  `daten/tv/revier.csv`, samstags Revier-Pflege (Zugänge mit Steckbrief und SIC-13, Abgänge nur gemeldet), Scalable-Positionen
  über `depot.uebernehmen()` sobald verbunden; Ergebnis in `daten/nachtlauf/claude_lauf.json`, steht mit in der Datenampel.

## Server (ab 05.11.2026)

- Hetzner CX23, Nürnberg, `invest-cockpit`, IP 2.31.188.241, Ubuntu 26.04, Backups an (8,43 €/Monat, Rechnung am 23.).
- `werkzeuge/server/einrichten.sh` (einmalig, `ssh root@2.31.188.241 'bash -s' < werkzeuge/server/einrichten.sh`):
  Zeitzone Berlin, automatische Sicherheitsupdates, Firewall (22/80/443), Benutzer `cockpit`, Ordner
  `/opt/invest-cockpit` mit Python-Umgebung, Dienst `invest-cockpit` (Streamlit, immer an), Zeitplan `nachtlauf.timer`
  (Mo–Fr 22:45 Berlin), Caddy mit https unter `2-31-188-241.sslip.io` und Passwort (Benutzer micky).
- `werkzeuge/server/uebertragen.sh`: Ordner vom Mac auf den Server (rsync, ohne _to_delete) und App neu starten.
- Geplant: Code über privaten GitHub-Speicher `schettlermichael-svg/invest-cockpit`, Server holt Änderungen selbst.
