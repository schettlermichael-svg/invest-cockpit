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
  - SIC-13 (Mickys Raster) und Fonds-Fußabdruck: am 11.11.2026 entfernt (`_to_delete/sic13_2026-11-11`); TradingView-Kennzahlen je Titel liest `tv_kennzahlen.zeile()` aus `daten/tv/revier.csv`
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
- **Baustein 2 · Enge:** Kontraktionen Schicht für Schicht in der Zone (ab 1 × ATR), grob halbiert (jede ≤ 70 % der
  vorigen), Enge = letzte Kontraktion ≤ 10 %, Pivot = ihr Hoch, Volumen der Enge leiser als in der ersten Kontraktion.
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

Rot heißt Fehler der App: Der Schritt wird rot, und eine Warnung geht aufs Handy. Gelb sind Hinweise: Die Kopfzeile wird gelb, und eine Meldung geht aufs Handy. Die Liste steht unter der Datenstand-Zeile jeder Seite („Wachen vom …“).

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
