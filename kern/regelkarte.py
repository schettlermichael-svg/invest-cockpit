"""Regelkarte (Gefechtsordnung, Schritt 1 – Micky 14./15.11.2026): die eine Dienstvorschrift für Code und Prüfer.

Bisher standen die Regeln dreimal da: im Code, in der Anleitung des Chart-Prüfers und in der des Setup-Prüfers. So
fehlten am 14.11. Kästen der drei Bilder in den Prüfern, ohne dass es auffiel. Jetzt gilt:

  Kasten     jeder Kasten der drei Bilder (Titel: Kreislauf und Code Balance/Ungleichgewicht, Gruppe: Geldfluss,
             Markt) – mit Regel nach der Gefechtsordnung, führendem Meister, Zeichen-Meistern, der Messung im Code
             (Modul.Funktion), dem Stand der Messung (gemessen, teilweise, fehlt – mit der Lücke) und dem Element, unter
             dem der Prüfer ihn prüft
  Zeichen    jedes Zeichen der Stärke und Schwäche aus zeichen.py mit Regel, Meister, Messung und Prüf-Element (der
             Wachposten liest zeichen.py und meldet jede Funktion, die ein Zeichen setzt und nicht auf der Karte steht)
  Werkzeug   was die Kästen misst (Zone, Enge, Pivot, Anker, Profil, Phase …) – mit der Regel der App, die der Prüfer
             kennen muss
  Setup      jedes Setup als Weg durch den Kreislauf (Gefechtsordnung): Weg, Lehrer, Regel, Einstieg, Stopp, widerlegt,
             eigene Abweichung mit Grund, Messung, Stand
  Meister    die recherchierten Regeln der Meister (14.11.2026, Quellen im Konzeptdokument), getrennt nach dem, was der
             Chart-Prüfer und was der Setup-Prüfer braucht

Die Anleitungen beider Prüfer entstehen aus dieser Karte (block_titel, block_gruppe, block_markt, block_setups), die
Formularfelder der Prüfer ebenso (elemente). Der Wachposten (wachposten) meldet rot, wenn ein Kasten keine Messung im
Code hat, eine Messfunktion fehlt, ein Kasten keinem Prüf-Element zugeordnet ist, ein Zustand der App keinen Kasten
hat oder ein Setup des Kartentischs nicht auf der Karte steht; gelb, wenn eine Messung erst teilweise steht. Neue
Regel = erst hier eintragen, dann bauen.
"""
import importlib

# ── Kästen ──────────────────────────────────────────────────────────────────────────────────────────────────────
# zustand: der Zustand der App (auktion.ZUSTAENDE bzw. gruppe/markt), zu dem der Kasten gehört (None = Anlass/Zeichen)
# stand: "gemessen" | "teilweise" | "fehlt"; luecke: was fehlt (und wann es kommt)

KAESTEN = {
    "titel": [
        dict(name="Anlass: neue Information", zustand=None,
             regel="Bringt die Balance an den Rand: der Wert ändert sich (Zahlen, Lücke, Nachricht) – ein Ereignis, das den "
                   "Wert neu bewertet. Anlass nur vor dem Ereignis am Rand und in Laufrichtung, sonst Gegenzeichen bzw. "
                   "Beleg danach; die Zahlenreaktion zählt einmal, nach dem heutigen Kurs gegen den Schluss vor den Zahlen "
                   "(Plan 15, Micky 16.11.2026).",
             fuehrt="Kullamägi/Bonde (Episodic Pivot)", zeichen="O'Neil (das „N“: neues Produkt, neue Zahlen), Mickys Zahlen-Reaktion",
             messung=["auktion.titel", "avwap.zahlentag", "zahlen_reaktion.reaktionstag"], stand="gemessen",
             pruefer=["Anlass"]),
        dict(name="Anlass: Verteidiger leer", zustand=None,
             regel="Angebot aufgebraucht: Enge, Volumen trocknet aus, Einquetschung – nur bei echter Enge (letzte "
                   "Kontraktion höchstens 10 %, Volumen der Enge unter dem Schnitt; Plan 15).",
             fuehrt="Minervini (VCP, Volumen trocknet aus)", zeichen="Wyckoff",
             messung=["zeichen.enge_trocken", "zeichen.einquetschung", "vcp_zone.enge"], stand="gemessen",
             pruefer=["Anlass", "Einquetschung"]),
        dict(name="Anlass: Zwang", zustand=None,
             regel="Stopps, Gefangene; geht im Spring/Upthrust auf (Micky 14.11.2026, kein eigenes Zeichen): Spring = "
                   "gefangene Verkäufer unter dem Rand, Upthrust oder Fehlausbruch = gefangene Käufer über dem Rand – nur "
                   "solange er gilt (Plan 15).",
             fuehrt="Wyckoff (Shakeout, Spring)", zeichen="Dalton",
             messung=["zeichen.spring", "vcp_zone.ausbruch"], stand="gemessen", pruefer=["Anlass"]),
        dict(name="Balance", zustand="Balance",
             regel="Die Ursache wird aufgebaut. Die Zone des Scanners führt (Rand, Pivot, Stopp); Daltons überlappender "
                   "Wert bestätigt nur. Weinsteins Stufe (1 Basis, 2 Fortsetzung, 3 Verteilung) steht als Rahmen daneben.",
             fuehrt="Minervini und O'Neil (Base)", zeichen="Weinstein (Stufe 1 und 3), Wyckoff (Ursache), Dalton (überlappender Wert, bestätigt)",
             messung=["vcp_zone.zone", "auktion.ursache", "avwap.balance_beginn"], stand="gemessen",
             pruefer=["Zustand"]),
        dict(name="Test am Rand", zustand="Test am Rand",
             regel="Wer ist stärker am Rand? Der Rand ist die Oberkante (bzw. Unterkante) der Zone; der Pivot ist der "
                   "Auslöser – liegt er darunter, ist es der frühe Einstieg (Cheat), an der Oberkante der Ausbruch. "
                   "Kurs höchstens 3 % vom Rand.",
             fuehrt="Minervini und O'Neil (Pivot)", zeichen="Wyckoff (Spring, Upthrust), Dalton (Test der Kante), Shannon (Zange)",
             messung=["auktion.titel", "zeichen.kraft_ohne_weg", "auktion.exzess"], stand="gemessen",
             pruefer=["Test am Rand: Zeichen"]),
        dict(name="abgelehnt", zustand="abgelehnt",
             regel="Zurück in den Wert – Wyckoff führt: Kurs bricht über den Rand und schließt zurück in der Zone "
                   "(Spring unten, Upthrust oben; Fehlausbruch = Schluss zurück in der Zone).",
             fuehrt="Wyckoff (Spring, Upthrust)", zeichen="Dalton (zurück in den Wert)",
             messung=["vcp_zone.ausbruch", "zeichen.spring", "marketprofile.analyse"], stand="gemessen",
             pruefer=["abgelehnt/angenommen"]),
        dict(name="Lauf zum anderen Rand", zustand="abgelehnt",
             regel="Nach „abgelehnt“: Gefangene treiben den Kurs zum anderen Rand der Zone.",
             fuehrt="Wyckoff", zeichen="Dalton",
             messung=["auktion.titel"], stand="teilweise",
             luecke="die App nennt den anderen Rand als Ziel; das Setup Spring/Upthrust fehlt (Schritt 4)",
             pruefer=["Lauf zum anderen Rand"]),
        dict(name="angenommen", zustand="angenommen",
             regel="Der Wert folgt dem Kurs: Ausbruch über den Pivot (Volumen ist Zeichen, keine Pflicht); Dalton "
                   "bestätigt, wenn der Wert folgt – aus dem Market Profile erst ab 2 Tagen mit dem Wert außerhalb (der 1. Tag ist "
                   "ein Vorstoß, Test am Rand). Höchstens 10 Tage – mehr als 5 % über dem Pivot (Kaufzone verlassen) und "
                   "am 10er/20er wird es Ungleichgewicht (Plan 15, Micky 16.11.2026).",
             fuehrt="O'Neil und Minervini (Ausbruch über den Pivot)",
             zeichen="Kullamägi (Ausbruch am Tag), Shannon (Kurs über dem AVWAP vom Hoch), Dalton (Wert folgt, bestätigt)",
             messung=["vcp_zone.ausbruch", "marketprofile.analyse"], stand="gemessen",
             pruefer=["abgelehnt/angenommen"]),
        dict(name="Ungleichgewicht", zustand="Ungleichgewicht",
             regel="Schnell durch dünnes Volumen – Kullamägi führt: Schluss über dem steigenden 10er bzw. 20er (steigend "
                   "= höher als vor einer Woche), abwärts gespiegelt; Phase und Dow-Struktur sind Zeichen.",
             fuehrt="Kullamägi (10er/20er)", zeichen="Weinstein (Stufe 2), Dalton (dünnes Volumen)",
             messung=["auktion.titel", "reiten.ungleichgewicht", "phase.aktuell"], stand="gemessen",
             pruefer=["Ungleichgewicht"]),
        dict(name="Ende: Gegner antwortet", zustand="Ende des Laufs",
             regel="Knoten im Volumenprofil (Mauer), alter Wert, AVWAP vom alten Hoch, Exzess, Kraft ohne Weg am Rand.",
             fuehrt="Dalton und Shannon", zeichen="Wyckoff (Kraft ohne Weg)",
             messung=["volumenprofil.knoten", "zeichen.kraft_ohne_weg", "auktion.exzess"], stand="teilweise",
             luecke="der AVWAP vom alten Hoch zählt noch nicht als Gegner",
             pruefer=["Ende des Laufs"]),
        dict(name="Ende: Antrieb erlischt", zustand="Ende des Laufs",
             regel="Kraft ohne Weg, Klimax, Wechsel der Phase, Rückschlag.",
             fuehrt="Wyckoff (Kraft ohne Weg, Klimax)", zeichen="Weinstein (Stufe 3)",
             messung=["auktion.klimax_tag", "erkennung.klimax", "phase.aktuell"], stand="gemessen",
             pruefer=["Ende des Laufs"]),
        dict(name="Ende: Wert akzeptiert", zustand="Ende des Laufs",
             regel="Zeit und Volumen: eine neue Wertzone auf der neuen Höhe.",
             fuehrt="Dalton", zeichen="",
             messung=["marketprofile.analyse"], stand="gemessen", pruefer=["Ende des Laufs"]),
        dict(name="Ende: Stopp folgt dem 10er/20er", zustand="Ende des Laufs",
             regel="Der Stopp folgt dem 10er (schnelle Titel) bzw. 20er, Schluss darunter heißt raus; Mauer, Kraft ohne "
                   "Weg und Klimax ziehen ihn sofort enger (unter das Tagestief).",
             fuehrt="Kullamägi", zeichen="Dalton, Wyckoff",
             messung=[], stand="fehlt", luecke="kommt mit Schritt 5 (nachgezogener Stopp in „Nach dem Kauf“)",
             pruefer=["Ende des Laufs"]),
        dict(name="Neue Balance", zustand="Balance",
             regel="Der Kreislauf beginnt neu, mit Gedächtnis (O'Neil: Basenzählung, späte Basen sind gefährlicher).",
             fuehrt="O'Neil (Basenzählung)", zeichen="",
             messung=[], stand="gemessen", pruefer=["Neue Balance/Basenzählung"]),
    ],
    "gruppe": [
        dict(name="Anlass: neue Information", zustand=None,
             regel="Zins, Rohstoffe, Quad im Wirtschaftswetter – warum das Geld wandert.",
             fuehrt="Quad (Wirtschaftswetter)", zeichen="",
             messung=["lage.quadrant"], stand="fehlt",
             luecke="der Quad steht im Material des Prüfers, der Zustand der Gruppe nennt keinen Anlass",
             pruefer=["Anlass"]),
        dict(name="Anlass: Verkäufer leer", zustand=None,
             regel="Der Ausverkauf der Gruppe ist durch.", fuehrt="O'Neil/Weinstein", zeichen="",
             messung=[], stand="fehlt", luecke="die App erkennt das Ende des Ausverkaufs einer Gruppe nicht",
             pruefer=["Anlass"]),
        dict(name="Anlass: Zwang", zustand=None,
             regel="Umschichtung, Abfluss.", fuehrt="O'Neil/Weinstein (Geldfluss)", zeichen="",
             messung=["auktion.gruppe"], stand="teilweise",
             luecke="Abfluss steht als Beleg (Geldfluss unter 1), nicht als Anlass", pruefer=["Anlass", "Geldfluss"]),
        dict(name="Balance", zustand="Balance",
             regel="Die RS der Gruppe läuft seitwärts (RS-Stärke und Schwung nahe 100).",
             fuehrt="O'Neil, Weinstein (Gruppen-RS seitwärts)", zeichen="",
             messung=["auktion.gruppe", "sektoren.feld"], stand="gemessen", pruefer=["Zustand der Gruppe", "Feld (Rotation)"]),
        dict(name="Anführer bricht aus", zustand="Test am Rand",
             regel="Folgen die Schwestern? (App: Feld Erstarkend, Anführer genannt)",
             fuehrt="O'Neil (das „L“: der Führer)", zeichen="Kullamägi (Führer-Rang: die Speerspitze als Zeichen)",
             messung=["auktion.gruppe"], stand="gemessen", pruefer=["Anführer bricht aus"]),
        dict(name="Gruppe folgt nicht", zustand="abgelehnt",
             regel="Das Geld rotiert zurück → Fehlausbruch der Gruppe, zurück in die Mitte (App: Erstarkend kippt zurück "
                   "nach Abgehängt = abgelehnt).",
             fuehrt="O'Neil/Weinstein", zeichen="", messung=["auktion.gruppe"], stand="gemessen",
             pruefer=["Gruppe folgt nicht/Fehlausbruch"]),
        dict(name="Schwestern folgen", zustand="angenommen",
             regel="Die Breite wächst, Zufluss (App: angenommen = Breite +10 Punkte in 4 Wochen und Zufluss ab 1,1).",
             fuehrt="O'Neil und Weinstein (erst die Gruppe, dann der Titel; Breite, Zufluss)", zeichen="",
             messung=["auktion.gruppe", "rudel.breite"], stand="gemessen", pruefer=["Schwestern folgen/Breite", "Geldfluss"]),
        dict(name="Gruppe führt", zustand="Ungleichgewicht",
             regel="Das Geld fließt stetig (App: Feld Führend = Ungleichgewicht).",
             fuehrt="O'Neil/Weinstein", zeichen="", messung=["auktion.gruppe", "sektoren.feld"], stand="gemessen",
             pruefer=["Zustand der Gruppe", "Feld (Rotation)"]),
        dict(name="Ende: Geld wandert weiter", zustand="Ende des Laufs",
             regel="Die nächste Gruppe lockt.", fuehrt="Weinstein", zeichen="",
             messung=[], stand="fehlt", luecke="die App sieht nicht, wohin das Geld als Nächstes fließt",
             pruefer=["Ende des Laufs"]),
        dict(name="Ende: Breite wird schmal", zustand="Ende des Laufs",
             regel="Der Anführer läuft allein (Breite fällt um 10 Punkte in 4 Wochen).", fuehrt="Weinstein", zeichen="",
             messung=["auktion.gruppe"], stand="gemessen", pruefer=["Ende des Laufs", "Schwestern folgen/Breite"]),
        dict(name="Ende: RS flacht ab", zustand="Ende des Laufs",
             regel="Zurück zur Mitte (App: Feld Ermüdend).", fuehrt="Weinstein", zeichen="",
             messung=["auktion.gruppe", "sektoren.feld"], stand="gemessen", pruefer=["Ende des Laufs"]),
        dict(name="Neue Balance", zustand="Balance",
             regel="Die Rotation geht weiter.", fuehrt="O'Neil/Weinstein", zeichen="",
             messung=["sektoren.rotation"], stand="gemessen", pruefer=["Neue Balance"]),
    ],
    "markt": [
        dict(name="Anlass", zustand=None,
             regel="Was den Markt an den Rand bringt (Zins, Wirtschaftswetter, Ereignis).", fuehrt="O'Neil", zeichen="Quad",
             messung=[], stand="fehlt", luecke="der Zustand des Marktes nennt keinen Anlass", pruefer=["Anlass"]),
        dict(name="Balance", zustand="Balance",
             regel="Wertzonen von S&P 500 und Nasdaq.", fuehrt="Dalton (Wertzonen)", zeichen="O'Neil",
             messung=["auktion.markt", "marktrichtung.zonen_bruch"], stand="gemessen", pruefer=["Balance (Wertzonen)"]),
        dict(name="Test am Rand", zustand="Test am Rand",
             regel="Erholungsversuch in der Korrektur.", fuehrt="O'Neil (Erholungsversuch)", zeichen="",
             messung=["auktion.markt", "marktrichtung.verlauf"], stand="gemessen", pruefer=["Test am Rand (Erholungsversuch)"]),
        dict(name="angenommen", zustand="angenommen",
             regel="Follow-Through-Day ab Tag 4 des Erholungsversuchs mit deutlichem Plus bei höherem Volumen.",
             fuehrt="O'Neil (Follow-Through-Day)", zeichen="", messung=["marktrichtung.verlauf"], stand="gemessen",
             pruefer=["Follow-Through-Day/angenommen"]),
        dict(name="abgelehnt", zustand="abgelehnt",
             regel="Erholungsversuch gescheitert: Schluss unter dem Tief des Versuchs.", fuehrt="O'Neil", zeichen="",
             messung=["marktrichtung.verlauf"], stand="gemessen", pruefer=["abgelehnt"]),
        dict(name="Ungleichgewicht", zustand="Ungleichgewicht",
             regel="Bestätigter Aufwärtstrend bzw. Korrektur ohne Erholungsversuch.", fuehrt="O'Neil", zeichen="",
             messung=["auktion.markt"], stand="gemessen", pruefer=["Zustand des Marktes"]),
        dict(name="Folgen die Schwestern", zustand=None,
             regel="Die Breite (Anteil der Titel über dem GD50) – trägt die Truppe den Markt?", fuehrt="Breite", zeichen="",
             messung=["lage.pendel"], stand="gemessen", pruefer=["Folgen die Schwestern (Breite)"]),
        dict(name="Ende: Gegner antwortet", zustand="Ende des Laufs",
             regel="Distributionstage (fallender Schluss bei höherem Volumen als am Vortag, 5–6 in 4–5 Wochen = unter "
                   "Druck), Abgabe am Rand.",
             fuehrt="O'Neil (Distributionstage)", zeichen="", messung=["marktrichtung.verlauf"], stand="gemessen",
             pruefer=["Distributionstage", "Ende des Laufs"]),
        dict(name="Ende: Antrieb erlischt", zustand="Ende des Laufs",
             regel="Überhitzung, Topbildung, Kapitulation (Marktzonen).", fuehrt="O'Neil", zeichen="",
             messung=["lage.pendel"], stand="gemessen", pruefer=["Ende des Laufs"]),
    ],
}

# Regeln, die für ein ganzes Bild gelten (stehen in der Anleitung, sind kein Kasten)

# ── Werkzeuge ───────────────────────────────────────────────────────────────────────────────────────────────────
WERKZEUGE = {
    "titel": [
        dict(name="Zone", regel="Zone der App: beginnt am ältesten Hoch ohne Schlusskurs darüber (ein Hoch darüber ohne "
                                "Schluss darüber bricht sie nicht – ein abgelehnter Vorstoß; so entschieden, nicht als "
                                "Widerspruch melden). Eine Tasse ab 7 Wochen gilt als gescheitert, wenn der Kurs nach der "
                                "rechten Seite in der unteren Hälfte schließt (Schlusskurs, nicht Tagestief). Über 50 % tief "
                                "ist keine Base; eine zu kurze Zone ist noch im Aufbau (kein Pivot). Flagge = Fahnenstange ab 30 % "
                                "direkt davor, 1–8 Wochen, höchstens 25 % tief, die Tiefs halten (sonst Base bzw. "
                                "Konsolidierung).",
             messung=["vcp_zone.zone"], stand="gemessen",
             pruefer=["Zone: Beginn", "Zone: Unterkante/Tiefe", "Zone: Name", "Zone: keine/offen"]),
        dict(name="Enge und Pivot", regel="Kontraktionen: die linke Seite bis zum Tief der Base, dann jede Welle der "
                                          "rechten Seite (jede mindestens 3 Handelstage, höchstens 6 Wellen); Pivot = Hoch "
                                          "der letzten Kontraktion; grün nur mit ausgetrocknetem Volumen und nicht in "
                                          "Phase 4. Liegt der Pivot mehr als 3 % unter der Oberkante, ist er ein Cheat (Drittel der "
                                          "Base: Low Cheat unten, Cheat Mitte, Cheat oben); bis 3 % unter der Oberkante ist er "
                                          "der Pivot am Rand.",
             messung=["vcp_zone.enge", "vcp_zone.drittel"], stand="gemessen",
             pruefer=["Pivot", "Drittel des Pivots", "Enge/Kontraktionen"]),
        dict(name="Cheat (eine Regel)", regel="Ein Ausbruch aus einer Pause, die jünger ist als die noch laufende größere "
                                               "Zone, mit Pivot mehr als 3 % unter deren Oberkante, ist ein früher "
                                               "Einstieg (Low Cheat, Cheat) und kein Ausbruch – ebenso ein Schluss über dem "
                                               "Hoch der letzten Enge, das mehr als 3 % unter der Oberkante liegt; der Ausbruch "
                                               "ist dann der Schluss über der Oberkante. Ein Cheat zählt nicht als "
                                               "Ausbruch, nicht als eigene Base und steht im Zustand als innere Rotation. "
                                               "In der Historie zeigt die App dieselbe Schlacht nur einmal (überlappende "
                                               "Zonen, die innerhalb von 5 Tagen ausbrechen: die größere).",
             messung=["vcp_zone.cheat", "vcp_zone.drittel", "vcp_zone.ausbruch", "vcp_zone.verlauf", "auktion.titel"],
             stand="gemessen", pruefer=["Zone: Name", "abgelehnt/angenommen", "Neue Balance/Basenzählung"]),
        dict(name="ATR (eine Rechnung)", regel="Die ATR ist das Mittel der True Range der letzten 14 Tage (Lücken zum Vortag "
                                                "eingeschlossen) – eine Rechnung für Stopp, Zonen, Anker, Zeichen und Zustand.",
             messung=["atr.reihe", "atr.wert"], stand="gemessen", pruefer=["Sonstiges"]),
        dict(name="Ausbruchsvolumen", regel="Ausbruchsvolumen ist bei der App ein Zeichen, keine Pflicht – über dem "
                                            "50-Tage-Schnitt reicht (Entscheidung des Nutzers, O'Neils 1,4-fach ist ihm zu "
                                            "streng); ein Ausbruch mit wenig Volumen ist kein Widerspruch, höchstens ein "
                                            "schwaches Zeichen.",
             messung=["vcp_zone.ausbruch"], stand="gemessen", pruefer=["abgelehnt/angenommen"]),
        dict(name="Gegenseite", regel="Mauer (Knoten über dem Kurs) und Stütze (Knoten darunter) aus dem Volumenprofil: "
                                      "jeder Gipfel ab 30 % des größten und 10 % über dem höheren Tal daneben.",
             messung=["volumenprofil.knoten"], stand="gemessen", pruefer=["Gegenseite (Mauer/Stütze)"]),
        dict(name="Eigen oder geliehen", regel="RS-Linie in 20 Tagen, in Laufrichtung gemessen: eigen ab 5 %; geliehen "
                                               "höchstens ±1 % (der Markt trägt); teils eigen 1–5 %; über 1 % gegen die "
                                               "Laufrichtung = Gegenzeichen. Stärke in der Schwäche macht eigen, solange "
                                               "die RS nicht gegen die Laufrichtung läuft.",
             messung=["auktion.kraft"], stand="gemessen", pruefer=["Eigen oder geliehen"]),
        dict(name="Phase", regel="Weinsteins Stufen an der 40-Wochen-Linie (Schritt 8, Micky 16.11.2026): Phase 2 beginnt mit "
                                 "dem Wochenschluss über dem Hoch der Basis und über der Linie, die nicht mehr fällt "
                                 "(„1 → 2 · Ausbruch“), bestätigt, sobald die Linie steigt; fehlt das Phase-2-Bild, solange "
                                 "die Linie steigt: „2 · Rücksetzer“ (ab 15 % unter dem Hoch und unter dem GD10W "
                                 "„2 · Rückschlag“, Ende-Zeichen); Phase 3 erst, wenn die Linie flach wird; Phase 4 "
                                 "unter der fallenden Linie; aus Phase 4 immer erst in die Basis (frühestens nach 8 Wochen).",
             messung=["phase.rechnen", "phase.aktuell", "zeichen.kreislauf"], stand="gemessen",
             pruefer=["Kreislauf/Phase"]),
        dict(name="Stufe als Rahmen", regel="Die Stufe gibt jedem Kasten den Namen: Balance in Stufe 1 = Basis, 2 = "
                                            "Fortsetzung, 3 = Verteilung, 4 = Pause im Fall; Lauf aus Stufe 1 = Beginn, "
                                            "in Stufe 2 = Fortsetzung. Ein Setup gegen die Stufe (Long in Phase 4, Short in "
                                            "Phase 2) trägt ein Gegenzeichen und wird höchstens gelb – nie gefiltert.",
             messung=["auktion.stufe_name"], stand="gemessen",
             pruefer=["Kreislauf/Phase"]),
        dict(name="AVWAP letztes Hoch", regel="Letztes Hoch = jüngstes Hoch, das der Kurs nicht überschritten hat und "
                                              "das bestätigt ist (Rückgang ab 8 % danach oder Wochen-Schwunghoch mit 2 "
                                              "fertige Wochen davor und danach tiefer). Steht der Kurs über allen bestätigten Hochs, "
                                              "ankert die App am jüngsten Wochen-Schwunghoch und nennt es Ausbruchspunkt.",
             messung=["avwap.anker"], stand="gemessen", pruefer=["AVWAP letztes Hoch"]),
        dict(name="AVWAP Hoch des Rückgangs", regel="Hoch des Rückgangs = der Gipfel der ganzen Korrektur: das höchste "
                                                    "bestätigte Hoch der letzten 2 Jahre, das der Kurs nicht überschritten "
                                                    "hat (fehlt, wenn er dasselbe ist wie das letzte Hoch).",
             messung=["avwap.anker"], stand="gemessen", pruefer=["AVWAP Hoch des Rückgangs"]),
        dict(name="AVWAP Tief der Bewegung", regel="Tief der Bewegung = das Tief, an dem der Trend zum letzten Hoch begann "
                                                   "(tiefstes Tief zwischen dem früheren, höheren Hoch und dem letzten "
                                                   "Hoch; ist es gebrochen, das tiefste Tief seit dem letzten Hoch, sobald "
                                                   "der Kurs 1 ATR darüber steht).",
             messung=["avwap.anker"], stand="gemessen", pruefer=["AVWAP Tief der Bewegung"]),
        dict(name="AVWAP letztes höheres Tief", regel="Letztes höheres Tief = das Tief des letzten Rückgangs ab 8 % "
                                                       "(dieselbe Bestätigung wie beim Hoch), aus dem der Anstieg zum "
                                                       "letzten Hoch kam – Shannons Stopp-Anker; nur nach dem "
                                                       "Trendstart-Tief und solange der Kurs nicht darunter fiel (Plan 20, "
                                                       "Micky 16.11.2026: beide Tiefs).",
             messung=["avwap.anker", "avwap._hoeheres_tief"], stand="gemessen", pruefer=["AVWAP letztes höheres Tief"]),
        dict(name="AVWAP Zahlentag", regel="Zahlentag = der letzte Zahlentag (jeder, gleich wie stark die Reaktion), "
                                           "höchstens 6 Monate zurück – eigene Linie (Shannon: mehrere Ereignisse "
                                           "übereinander; Micky 16.11.2026).",
             messung=["avwap.anker", "avwap.zahlentag"], stand="gemessen", pruefer=["AVWAP Zahlentag"]),
        dict(name="AVWAP Lücke/Volumen", regel="Lücke/Volumen = die jüngste Lücke ab 4 % oder Volumenspitze ab doppeltem "
                                               "Schnitt mit Bewegung ab 3 % (6 Monate), die nicht auf den Zahlentag fällt.",
             messung=["avwap.anker"], stand="gemessen", pruefer=["AVWAP Lücke/Volumen"]),
        dict(name="AVWAP Börsengang", regel="Börsengang = der erste Handelstag einer jungen Aktie (ihre Kursreihe beginnt "
                                            "mehr als 30 Tage nach der des Index) – Shannons wichtigster Anker bei "
                                            "Neuemissionen (Micky 16.11.2026).",
             messung=["avwap.anker", "avwap._boersengang"], stand="gemessen", pruefer=["AVWAP Börsengang"]),
        dict(name="AVWAP Ausbruch (Handoff)", regel="Ausbruch = der Tag des laufenden Ausbruchs aus der Zone (ohne "
                                                    "Fehlausbruch) – Shannons Handoff: nach dem Ausbruch die neue Stütze "
                                                    "(Micky 16.11.2026).",
             messung=["avwap.anker", "avwap._ausbruch"], stand="gemessen", pruefer=["AVWAP Ausbruch (Handoff)"]),
        dict(name="Volumenprofil", regel="Volumenprofil der Balance ab dem ersten Tag, ab dem sich die Tagesspannen "
                                         "überlappen (Dalton).",
             messung=["avwap.profil_anker", "volumenprofil.verankert"], stand="gemessen",
             pruefer=["Volumenprofil (Balance)"]),
    ],
    "gruppe": [
        dict(name="Geldfluss", regel="Zufluss = Volumen steigender ÷ fallender Tage (50 Tage); unter 1 heißt Abfluss.",
             messung=["auktion.gruppe"], stand="gemessen", pruefer=["Geldfluss"]),
    ],
    "markt": [],
}

# ── Zeichen (Stärke und Schwäche – gewogen, wer am Rand stärker ist; zeichen.py) ────────────────────────────────────
# Jede Funktion in zeichen.py, die ein Zeichen setzt, muss hier (oder bei einem Kasten/Werkzeug) als Messung stehen –
# der Wachposten liest zeichen.py und schlägt Alarm, wenn ein Zeichen fehlt (Micky 15.11.2026).
ZEICHEN = [
    dict(name="Dow-Struktur", art="Struktur", meister="Dow",
         regel="Schwungpunkte (Tag n = 5, Woche n = 2); höhere Hochs und Tiefs = aufwärts, tiefere = abwärts. Schwäche: "
               "Schluss mindestens 0,5 ATR unter dem letzten höheren Tief. Stärke: Schluss mindestens 0,5 ATR über dem "
               "letzten tieferen Hoch; erstes höheres Tief nach tieferen Hochs und Tiefs, solange der Kurs darüber steht "
               "(gespiegelt: erstes tieferes Hoch, Kurs darunter).",
         messung=["zeichen.dow", "zeichen.kreislauf"], pruefer=["Test am Rand: Zeichen", "Kreislauf/Phase"]),
    dict(name="Spring/Upthrust", art="Struktur", meister="Wyckoff; O'Neil („undercut and rally“)",
         regel="An der Zone des Scanners, wie sie am Vortag stand (dieselbe Regel wie das Setup): Tief höchstens 1 ATR "
               "unter der Unterkante und ein Schluss zurück in der Zone am selben Tag oder in den 2 Tagen danach = Spring; "
               "Hoch höchstens 1 ATR über der Oberkante und Schluss zurück = Upthrust; ein Fehlausbruch zählt auch. Zeichen "
               "in den letzten 10 Tagen; Volumen am Schluss zurück steht dabei (Zeichen, keine Bedingung).",
         messung=["zeichen.spring", "vcp_zone.spring_upthrust"], pruefer=["Test am Rand: Zeichen", "abgelehnt/angenommen"]),
    dict(name="Einquetschung", art="Struktur", meister="Micky (Titel-Analyse, 21.11.2026)",
         regel="Seit dem Anker des Profils (Zahlentag, der die Balance auslöste, sonst ihr Beginn) steigen die Tiefs der "
               "drei Drittel, ihre Hochs liegen höchstens 2 % auseinander. Gespiegelt: fallende Hochs über Tiefs, die "
               "höchstens 2 % auseinanderliegen.",
         messung=["zeichen.einquetschung", "tiefe.quetschung", "tiefe.anker", "zeichen.kreislauf"], pruefer=["Einquetschung"]),
    dict(name="Bruch der Phase", art="Struktur", meister="Weinstein",
         regel="Schluss unter dem Tief der Basis bzw. über dem Hoch der Verteilung.",
         messung=["zeichen.kreislauf"], pruefer=["Kreislauf/Phase", "abgelehnt/angenommen"]),
    dict(name="Akkumulation und Distribution", art="Volumen", meister="O'Neil",
         regel="20 Tage: Kauftag = Schluss über dem Vortag, Volumen über dem 50-Tage-Schnitt, Schluss im oberen Drittel; "
               "Abgabetag = Schluss unter dem Vortag, Volumen über dem Schnitt, Schluss im unteren Drittel; Saldo ≥ 3 und "
               "doppelt so viele = Akkumulation, gespiegelt Distribution. Verdeckte Abgabe (Churning): mindestens 3 Tage "
               "im Plus mit Volumen, die im unteren Drittel schließen.",
         messung=["zeichen.akkumulation", "zeichen.tagesmarken"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="Pocket Pivot", art="Volumen", meister="Morales/Kacher",
         regel="In den letzten 5 Tagen: Tag im Plus über GD10 und GD50, höchstens 4 % über dem GD10, Volumen über dem "
               "größten Abgabetag der 10 Tage davor, die 5 Tage davor zusammen höchstens +3 %.",
         messung=["zeichen.akkumulation", "zeichen.tagesmarken"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="Umkehrkerzen", art="Struktur", meister="Homma (Regeln nach Nison)",
         regel="Nur an einer Marke (höchstens 1 ATR von 52-Wochen-Hoch/-Tief, Rand der Zone oder AVWAP-Linie) und nach "
               "einem Trend, den sie umkehren kann (Vortag gegen 5 Tage davor): Hammer (unterer Schatten mindestens "
               "2-mal der Körper, oberer höchstens 10 % der Spanne) und Shooting Star (gespiegelt), Engulfing (der Körper "
               "umschließt den des Vortags in Gegenfarbe), Morning/Evening Star (langer Körper, Stern höchstens 35 % "
               "davon mit Abstand, Schluss über bzw. unter der Mitte des ersten Körpers). Bestätigt: der nächste Tag "
               "schließt jenseits des Körpers (Micky 17.11.2026).",
         messung=["zeichen.umkehr", "zeichen.kreislauf"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="Kraft ohne Weg", art="Volumen", meister="Wyckoff (Aufwand ohne Ergebnis)",
         regel="Volumen ab 2-fach des 50-Tage-Schnitts bei einer Spanne von höchstens 70 % der Spanne der 20 Tage "
               "davor, in den letzten 10 Tagen an einer Marke (wie die Umkehrkerzen): Absorption – nach einem Anstieg "
               "Schwäche (Verkäufer schlucken die Nachfrage), nach einem Fall Stärke (Micky 17.11.2026; vorher 1,5-fach, "
               "Spanne unter 0,7 ATR, nur am Rand der Zone). Eine Regel für Kasten, Zeichen und Chart.",
         messung=["zeichen.kraft_ohne_weg", "zeichen.kreislauf"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="3 Wochen eng, Volumen trocknet aus", art="Volumen", meister="O'Neil (3 Wochen eng), Minervini",
         regel="Enge: 3 Wochenschlüsse innerhalb 1,5 %. Trockenheit: der leiseste Tag seit 50 Tagen in den letzten 10, in "
               "der unteren Hälfte der Spanne der 60 Tage.",
         messung=["zeichen.enge_trocken"], pruefer=["Anlass", "Test am Rand: Zeichen"]),
    dict(name="Freitag ohne Gewinnmitnahme", art="Volumen", meister="Micky (13.11.2026)",
         regel="Nach einer Woche von mindestens 2 Wochen-ATR keine Gewinnmitnahme: der letzte Handelstag der Woche "
               "schließt im oberen Drittel seiner Spanne und nicht schwächer als −0,5 %, die Woche im oberen Viertel – die "
               "Käufer trauen dem Lauf. Gespiegelt keine Eindeckung nach einer schwachen Woche.",
         messung=["zeichen.freitag"], pruefer=["Test am Rand: Zeichen", "Ungleichgewicht"]),
    dict(name="Stärke in der Schwäche", art="RS", meister="Micky, Minervini, O'Neil",
         regel="Im Fenster der Korrektur (bis 45 Handelstage nach ihrem Tief): hält = der Index fiel mindestens 3 %, der "
               "Titel steht am Indextief mindestens so weit im Plus wie der Index im Minus und mindestens 15 Punkte vor "
               "ihm; führt = seit dem Indextief mindestens 10 Punkte vor dem Index, Kurs höchstens 15 % unter dem "
               "52-Wochen-Hoch; nah = am Indextief höchstens halb so weit vom eigenen Hoch wie der Index und höchstens "
               "15 %; RS-Linie am 52-Wochen-Hoch, während der Index fällt. Gespiegelt Schwäche in der Stärke (Index ≥ 3 % "
               "über dem Tief der 60 Tage): Titel seit dem Indextief im Minus, RS-Linie am 52-Wochen-Tief.",
         messung=["zeichen.relativ"], pruefer=["Test am Rand: Zeichen", "Eigen oder geliehen"]),
    dict(name="Höheres Tief gegen den Index", art="RS", meister="O'Neil, Minervini (Divergenz)",
         regel="Der Titel fiel seit dem Indexhoch bis zu seinem Tief um mindestens max(5 %, 3 ATR, den Rückgang des "
               "Index); dieses Tief liegt mindestens 3 Handelstage vor dem Tief des Index, der Index fällt danach "
               "mindestens 0,5 % tiefer, der Titel bleibt 5 % über seinem Tief und liegt seit seinem Tief mindestens 10 "
               "Punkte vor dem Index. Gespiegelt (Verteilung eines Führers): tieferes Hoch gegen den Index nach einem "
               "Anstieg ab 10 % in 60 Tagen.",
         messung=["zeichen.divergenz", "zeichen.divergenz_short"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="Tage gegen den Markt", art="RS", meister="O'Neil (versteckte Stärke)",
         regel="An mindestens 4 (und 60 %) der Indextage mit −1 % oder weniger im Plus geschlossen (20 Tage); gespiegelt "
               "Schwäche: an mindestens 3 Indextagen mit +1 % oder mehr im Minus.",
         messung=["zeichen.tage_gegen_markt"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="RS-Linie in der Base", art="RS", meister="O'Neil, Minervini",
         regel="Die RS-Linie steigt in 20 Tagen um mindestens 2 %, während der Kurs nachgibt; höheres Tief der RS-Linie bei "
               "tieferem Kurstief (60 Tage). Gespiegelt für die Schwäche.",
         messung=["zeichen.rs_linie"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="Reaktion auf die Zahlen", art="Ereignis", meister="O'Neil, Micky",
         regel="Letzte Zahlenmeldung (höchstens 60 Handelstage): Überraschung gegen Reaktion (Schwäche ab −2 % trotz guter "
               "Zahlen, Stärke ab +1 % mit Schluss in der oberen Hälfte trotz schlechter), Lücke gegen Schluss im Tag "
               "(Lücke ≥ +3 % und Schluss im unteren Drittel = verkauft; gespiegelt gekauft), Kurs heute zurück unter bzw. "
               "über dem Schluss vor den Zahlen = Zahlen verworfen bzw. Abverkauf zurückgekauft.",
         messung=["zeichen.reaktion"], pruefer=["Anlass"]),
    dict(name="Market Profile an der Schwelle", art="Ereignis", meister="Dalton",
         regel="Tageswerte der letzten 5 Tage überwiegend höher bzw. tiefer, POC steigt bzw. fällt, Kurs im oberen bzw. "
               "unteren Drittel der Wertzone.",
         messung=["zeichen.wertzone"], pruefer=["Test am Rand: Zeichen"]),
    dict(name="Trendqualität", art="Struktur", meister="Minervini (Trendvorlage)",
         regel="Steigung des GD50 über 20 Tage und Abstand des Kurses zum GD50, in % – als Zahl neben der Phase.",
         messung=["zeichen.trendqualitaet"], pruefer=["Kreislauf/Phase"]),
]

# ── Setups als Wege durch den Kreislauf ─────────────────────────────────────────────────────────────────────────

# Kacheln der Titelseite je Setup (Micky 16.11.2026: „die Setups werden nach unseren Kriterien gemessen, nicht nach den
# Meistern“): jede Kachel urteilt mit der Regel, die der Katalog dem Setup gibt; None = das Setup hat dort keine Regel,
# die Kachel zeigt den Wert als Zeichen (grauer Punkt). Ohne Setup gilt der Maßstab des Base-Ausbruchs. Stärke: der
# RS-Rang gilt für alle Setups außer dem Momentum-Ausbruch (Führer) – Micky 16.11.2026, Plan 24.




# Für alle Setups (Gefechtsordnung, Micky 14.11.2026)

# ── Weitere Bereiche der App (Generalinventur 15.11.2026) ────────────────────────────────────────────────────────
# Regeln außerhalb der drei Bilder und der Setups: Rückenwind, Depot und Risiko, Fundament, Stopps, Kartentisch,
# Erkennung, Rudel. pruefer leer = noch kein Prüfer sieht den Bereich (gelb, Micky entscheidet).
BEREICHE = [
    dict(name="Nach dem Kauf und Depot", quelle="Kullamägi (10er/20er, Teilgewinn), Micky 14./16.11.2026 (Schritt 5), "
                                                "O'Neil (8 %), Minervini (Einstand ab 2R, Klumpen, Verlustbremse)",
         regel="Ein System für alle Positionen: bis Tag 3 gilt der Anfangsstopp, danach folgt der Stopp dem 10er (solange "
               "seit Tag 3 kein Schluss darunter lag) bzw. dem 20er, er steigt nur, Schluss darunter heißt raus; Mauer "
               "(höchstens 3 % über dem Kurs), Kraft ohne Weg am oberen Rand und Kauf-Klimax ziehen ihn sofort unter das "
               "Tief jenes Tages (Stopp im Markt); short gespiegelt. Teilgewinn Tag 3–5 (Kullamägi). "
               "Verlustgrenze 8 % vom Einstieg ohne Ausnahme; ab 2R Gewinn Stopp mindestens auf Einstand; Positionswert "
               "über 25 % des Kontos = Klumpen; Konto 10 % unter seinem Höchststand = Zeichen, das Risiko je Trade zu "
               "halbieren; Depot-Hitze höchstens 6 % des Kontos.",
         messung=["depot._nach_dem_kauf", "atr.stopp", "reiten.nachgezogen", "reiten.ende_zeichen", "depot.verlustbremse",
                  "depotleiste.titelkarte", "depotleiste.positionsmarken"], pruefer=[],
         luecke="kein Prüfer – die Regeln sind fest, gemessen wird am eigenen Depot"),
    dict(name="Performance", quelle="Micky 16.11.2026 (Excel-Liste „Trading Performance Tracker“), Minervini (Verlustbremse)",
         regel="Wochenrendite = (Depotwert − Vorwoche − Einzahlung) / Vorwoche; Ø Wochenrendite geometrisch aus den echten "
               "Wochen; Hochrechnung auf ein Jahr (52 Wochen) mit der Ø und mit der letzten Woche; Zielpfad Start × (1 + "
               "Wochenziel)^Woche; Unterwasser = Abstand zum bisherigen Hoch, ab 10 % rot wie die Verlustbremse.",
         messung=["performance.rechnen"], pruefer=[],
         luecke="kein Prüfer – gerechnet wird am eigenen Konto"),
    dict(name="Rückenwind: Schlachtordnung der Titel", quelle="O'Neil/IBD (RS-Rang), Micky 09.11.2026 (Stufen)",
         regel="RS-Rang 1–99 wie IBD (letztes Quartal 40 %, die drei davor je 20 %). Läuft: Rang ab 85 und Tempo nicht "
               "schlechter als −5 in 4 Wochen; Entsteht: Rang 50 bis unter 85, mindestens +15 in 4 Wochen und "
               "positive Beschleunigung; Ermüdet: Rang ab 80 und Tempo −10 oder schlechter – oder Beschleunigung −15 "
               "und Tempo höchstens +5; Abfluss: vor 4 Wochen ab 70, seitdem 20 Punkte verloren. Zufluss ab 1,1, "
               "Abfluss unter 0,9 (Volumen steigender ÷ fallender Tage, 50 Tage); Gruppe stabil: führt seit 8 Wochen, "
               "Rückschlag höchstens 8 %; Kurs am Hoch: höchstens 3 % darunter. Qualität: Eigenkapitalrendite ab 17 %, "
               "Jahresgewinn ab 25 %; Reaktion auf Zahlen: Lücke mit 1,5-fachem Volumen, Abverkauf ab −3 %.",
         messung=["rueckenwind.rechnen", "rueckenwind_seite.wetterkarte", "rueckenwind_seite.gruppen",
                  "rueckenwind_seite._zufluss"], pruefer=[],
         luecke="kein Prüfer sieht die Rückenwind-Seite (der Gruppen-Prüfer sieht nur Geldfluss und Feld der Gruppen)"),
    dict(name="Fundament (Zahlen)", quelle="Minervini (Regelkatalog Kap. 7–8), O'Neil",
         regel="Gewinn je Quartal und Beschleunigung, Umsatz kräftig ab 15 % (Rate muss um mindestens 1 Punkt steigen), "
               "Überraschung deutlich ab 3 %, Marge, Gewinnqualität – als Ampeln.",
         messung=["fundament.umsatz", "fundament.ueberraschung", "fundament.beschleunigung", "fundament.quartalsgewinn", "fundament.ampeln", "fundament.institutionen"],
         pruefer=[], luecke="kein Prüfer – die Zahlen kommen aus den Quellen, gerechnet wird nur"),
    dict(name="Termine der Zahlen", quelle="Micky (Zahlen nicht im Trade überraschen lassen)",
         regel="Nächste Zahlen in höchstens 7 Tagen rot, 8–14 Tage gelb, später grün.",
         messung=["gestaltung.termin_ampel"], pruefer=[],
         luecke="kein Prüfer – eine Kalenderregel"),
    dict(name="Pendel der Übersicht", quelle="Marks (Pendel), Levy (Überdehnung)",
         regel="Kreditrisiko und Angstindex (gespiegelt): Rang ab 60 von 100 grün, ab 30 gelb. Marktbreite: ab 60 % über "
               "GD200 grün, ab 40 % gelb. Überdehnung (Levy): S&P 500 ab 10 % über dem 26-Wochen-Schnitt gelb, darunter "
               "bis zum Schnitt grün, unter dem Schnitt rot.",
         messung=["uebersicht._pendel_instrumente"], pruefer=[], luecke="kein Prüfer – die Seite Übersicht"),
    dict(name="Bänder und Zeichen im Chart", quelle="O'Neil (Volumen), Dow (Schwungpunkte), Micky",
         regel="Volumenband: Ruhe bis 50 % des 50-Tage-Schnitts (kräftig), bis 75 % blass, deutlich ab 150 %. RS-Pfeil: "
               "Änderung der letzten 10 Tage (Wochenchart 3 Wochen), ↗/↘ ab 1 Punkt, ↑/↓ ab 3 Punkten. Dow-Schwungpunkte "
               "mit 5 Tagen links und rechts. RS-Hoch vor dem Kurs: RS-Linie am Jahreshoch, Kurs mehr als 3 % darunter "
               "(wie Rückenwind). Lagekarte: Rahmen einer Flagge nur, wenn ihre Oberkante bis 0,5 % am Pivot liegt.",
         messung=["chart.chart", "chart._signale"], pruefer=[],
         luecke="kein Prüfer – Zeichnung"),
    dict(name="Tiefenanalyse: Struktur nach Dalton", quelle="Dalton (Mind Over Markets), Titel-Analyse, Micky 21.11.2026",
         regel="Anker: der Zahlentag, wenn sein Schluss mindestens 1 ATR vom Vortag lag und die Balance daraus hervorging "
               "(höchstens 10 Kerzen vor ihrem Beginn), sonst der Beginn der Balance (Regel des Cockpits). Profil ab dem "
               "Anker aus Stundenkerzen in Stufen von 0,25 % (ohne Stundenkerzen Tageskerzen), Wertzone 70 % vom POC nach "
               "außen; dünne Zone unter ⅓ des POC-Volumens ab 2 Stufen, dünne Ränder = Dochte. Alte Wertzone: letzte "
               "Balance ab 10 Kerzen vor dem Anker. Pivot long/short: Rand der Balance (Tests bis 1 %) neben dem Pivot der "
               "Enge. Dasselbe Profil ist das graue Volumenprofil des Cockpits.",
         messung=["tiefe.struktur", "tiefe.anker", "tiefe.profil_ab", "tiefe.zonen", "tiefe.alte_balance",
                  "volumenprofil.verankert", "analyse_seite.struktur_zeilen"], pruefer=[],
         luecke="kein Prüfer – neu aus der Titel-Analyse"),
    dict(name="Tiefenanalyse: Wertwanderung", quelle="Dalton (überlappender Wert), Titel-Analyse",
         regel="POC und Wertzone je Kerze aus feineren Kerzen (Tag aus 30 Minuten, Woche aus Stunden), 6 Klassen zur "
               "vorigen; Treppe ab 3 POCs in Folge, Ballen = letzte 5 POCs innerhalb 1 ATR, Abtasten = Schluss außerhalb "
               "der vorigen Wertzone mit eigenem POC darin, nackte POCs der letzten 60 Kerzen.",
         messung=["tiefe.wanderung", "tiefe.klasse", "marketprofile.klasse", "analyse_seite.wander_zeilen"], pruefer=[],
         luecke="kein Prüfer – neu aus der Titel-Analyse"),
    dict(name="Tiefenanalyse: Zange, Stärke in der Schwäche, CMF, Sektor-Rang", quelle="Shannon, O'Neil, Chaikin, Titel-Analyse",
         regel="Zange: Abstand der AVWAP vom letzten Hoch und vom Tief der Bewegung vor 5 Tagen → heute; Kurs bis 2 % unter "
               "einer AVWAP = nächster Deckel. Stärke in der Schwäche: besser als der S&P 500 an seinen Distributionstagen der "
               "letzten 25 Sitzungen, an der Mehrheit 🦈. CMF 20 Tage, über +0,05 Zufluss, unter −0,05 Abfluss. Sektor-Rang "
               "der 11 Sektor-ETFs über 1M/3M/6M, im Mittel bis 3,5 🌞, ab 8 ❄️.",
         messung=["tiefe.avwap_liste", "tiefe.staerke_in_schwaeche", "tiefe.cmf", "tiefe.sektor_rang", "tiefe.leistung",
                  "analyse_seite.avwap_zeilen", "analyse_seite.rs_zeilen", "analyse_seite.geld_zeilen",
                  "analyse_seite.seite_analyse", "analyse_seite.material"], pruefer=[],
         luecke="kein Prüfer – neu aus der Titel-Analyse"),
    dict(name="Einschätzung: Stratege mit Recherche", quelle="Titel-Analyse (Punkte 1, 2, 9, 11), Micky 21.11.2026",
         regel="Long, short, abwarten (mit Auslöser und Tendenz) oder kein Schuss; höchstens 3 Belege mit Feldnummer, "
               "Auslöser, Widerlegung, Gegenzeuge; im Netz nur Unternehmen, letztes Quartal und 3–5 Wettbewerber, höchstens "
               "8 Suchen. Der Code prüft: Felder und Zahlen im Material, Kursmarken (bis 40 % um den Kurs) auf 0,5 % genau "
               "im Material, Zeichen am Zeilenanfang, Long-Auslöser über der Widerlegung (Short umgekehrt), Quellen nur "
               "aus der Websuche.",
         messung=["strategen.pruefen", "strategen.rufen", "strategen.material"], pruefer=[],
         luecke="kein Prüfer – der Code prüft jede Antwort"),
    dict(name="Zonen, Phasen und das eine Profil (schlankes Cockpit)", quelle="Minervini, O'Neil, Kullamägi, Dalton, Micky 22.11.2026",
         regel="Woche und Tag: die Base nach Minervini/O'Neil (vcp_zone.zone – Oberkante = letztes Swing-Hoch ohne Schluss "
               "darüber, Unterkante = tiefstes Tief seitdem; Base, Flagge, Konsolidierung; Pivot = Hoch der Enge am Rand, "
               "sonst die Oberkante), während eines Ausbruchs (bis 20 Tage) die Base, aus der er kam. Stunde: die Balance "
               "nach Dalton (tiefe.struktur). Trades: Ausbruch long (Auslöser Pivot, Stopp Tief der letzten Kontraktion, "
               "höchstens 8 %), Rücktest (Einstieg am Pivot, Stopp ¼ ATR darunter), Bruch der Unterkante short (mit Volumen "
               "über dem 50-Tage-Schnitt, Stopp ¼ ATR über der Kante); kein festes Ziel, Risiko-Ampel bis 8 %. Ein Profil je "
               "Ebene ab Beginn der Zone. PbD-Kette nach Vorwald am 22.11.2026 entfernt.",
         messung=["zonen.basis", "zonen.lage", "zonen.trade", "zonen.fuehrte", "zonen.profil_details",
                  "zonenchart.bild"], pruefer=[],
         luecke="kein Prüfer"),
    dict(name="Zirkel: Stärke, Schwäche, Momentum, Balance und Disbalance", quelle="Weinstein, Wyckoff, Dalton, Kullamägi, Micky 22.11.2026",
         regel="Vier Phasen je Woche (Basis, Aufwärts, Verteilung, Abwärts); jede trägt den Keim des Gegenteils: in Basis "
               "und Abwärts keimt die Stärke, in Aufwärts und Verteilung die Schwäche. Titelseite: Leiste und Zeichen "
               "„trägt“ / „Keim“; Liste: Phase, Keim (🌱/🍂). Momentum nach Kullamägi: Rendite über 22, 67, 126 Tage, die "
               "besten 2 % des Reviers je Fenster = 🚀.",
         messung=["zeichen.zirkel", "zeichen.kurz", "rueckenwind.rechnen"], pruefer=[],
         luecke="kein Prüfer"),
    dict(name="Festungen", quelle="O'Neil, Minervini (Overhead Supply), Micky 22.11.2026",
         regel="Alte Decke = Swing-Hoch (Wendepunkt ab 2 ATR, vcp_zone.zigzag) ohne Schluss darüber, alter Boden = Swing-"
               "Tief ohne Schluss darunter; per Schluss überwunden und seitdem nicht zurück, tauscht die Kante die Rolle. "
               "Je Richtung die 2 nächsten, näher als ½ ATR verschmolzen; zwei Jahre zurück. Umkehrpreise und AVWAP am "
               "22.11.2026 entfernt.",
         messung=["zonen.festungen"], pruefer=[],
         luecke="kein Prüfer"),
    dict(name="Freie Bahn ✈️", quelle="Livermore (Linie des geringsten Widerstands), O'Neil (Overhead Supply), Micky 22.11.2026",
         regel="✈️ = im Tageschart keine Festung über dem Kurs (zwei Jahre zurück), ✈️↓ = keine darunter. Reines Zeichen "
               "ohne Schwelle; wie leicht der Kurs läuft, zeigen Pivot, Volumen-Spur, 🏜️ und Kraft ohne Weg. Liste "
               "(Spalte Bahn), Rückenwind-Zeile und Kopf der Titelseite.",
         messung=["zonen.frei", "rueckenwind.rechnen", "rueckenwind_seite.bahn"], pruefer=[],
         luecke="kein Prüfer"),
    dict(name="Morgenmeldung: Setups", quelle="Micky 17.11.2026, umgestellt 22.11.2026 (Schlachtordnung, Zirkel)",
         regel="Nach dem Nachtlauf eine Meldung aufs Handy: bis 5 Long (Aufbruch, Fortsetzung oder Rücktest am Pivot, im "
               "Ausbruch oder Rücktest, aus Garde, Angriff oder Vorhut; Klasse vor Rang) und bis 5 Short (Abbruch, "
               "Fortsetzung abwärts; Rückzug zuerst), je Titel Klasse, Setup, Einstieg, Stopp mit Risiko-Ampel, ✈️ und "
               "Keim des Zirkels; ohne Setup sagt die Meldung das.",
         messung=["zirkel.heisse", "zirkel.trade_wort"], pruefer=[], luecke="kein Prüfer – eine Auswahl"),
    dict(name="Setup aus dem Zirkel", quelle="Micky 22.11.2026 (unser Setup ergibt sich aus unserem Zirkel)",
         regel="Setup = Phase des Zirkels (Woche) + Zone (Tag), bestätigt durch Stärke bzw. Schwäche (Stärke = Widerstand "
               "überwinden, Druck aushalten; ein Keim zählt nur gemessen): 1 Basis + Ausbruch/Pivot + 🌱 oder Wechsel 1→2 = "
               "Aufbruch · 2 Aufwärts + Ausbruch/Pivot ohne 🍂 = Fortsetzung · Rücktest in 2 bzw. 1→2 = Rücktest · 3 "
               "Verteilung + Bruch mit Volumen + 🍂 oder Wechsel 3→4 = Abbruch · 4 Abwärts + Bruch ohne 🌱 = Fortsetzung "
               "abwärts; junge Titel ohne Zirkel: Aufbruch/Rücktest. Gegen den Zirkel kein Setup, nicht gezeigt.",
         messung=["zirkel.setup", "zonen.trade"], pruefer=[], luecke="kein Prüfer"),
    dict(name="Zirkel-Lauf", quelle="Micky 22.11.2026 (löst den Kartentisch ab)",
         regel="Jede Nacht für Revier und Watchlist aus den Tageskursen: Kreislauf (Phase, Zeichen, Keime), Setup aus Zone der "
               "Tagesebene im Einklang mit dem Zirkel (Setup), 52-Wochen-Hoch bzw. -Tief für O'Neils Markt-Ampel "
               "(Hochs gegen Tiefs). Gruppen-Listen und Spalte „Setup“ der Liste lesen daraus.",
         messung=["zirkel.rechnen", "zirkel.feld", "zirkel.barometer", "rueckenwind_seite.setups"], pruefer=[],
         luecke="kein Prüfer"),
    dict(name="Rotationskarte (Pfeile)", quelle="Rotation der Sektoren (Feld × Schwung)",
         regel="Pfeil = Bewegung der letzten 5 Wochen; unter 0,5 Punkten gilt eine Achse als unverändert.",
         messung=["frontkarte.richtung"], pruefer=["Feld (Rotation)"]),
    dict(name="Rudel und Kursverwandte", quelle="eigene Messung (Gleichlauf nach Abzug des Marktes)",
         regel="Kursverwandte: die 5 Titel mit dem engsten Gleichlauf – eng ab 0,50, mittel ab 0,35; Themen-Gruppen ab "
               "0,40 und 5 Titeln.",
         messung=["rudel._rechnen", "rudel.rudel"], pruefer=[],
         luecke="kein Prüfer – Zeichen am Rand, kein Urteil"),
]

# ── Meister (recherchiert 14.11.2026) ───────────────────────────────────────────────────────────────────────────


# ── Anleitungen für die Prüfer ──────────────────────────────────────────────────────────────────────────────────










# ── Inventur: jede feste Regel im Code gehört einem Eintrag der Karte (Generalinventur, Micky 15.11.2026) ──────────
# Eine feste Regel = eine Konstante auf Modulebene mit einer Zahl (Schwelle, Fenster, Faktor). Sie gilt als auf der
# Karte, wenn eine Messfunktion der Karte sie benutzt – direkt oder über Funktionen, die sie aufruft. Was keiner gehört,
# ist ein blinder Fleck (🚨). Technik (Layout, Kosten, Datenpflege) steht mit Grund auf der Ausnahmeliste.
TECHNIK = {
    "chart.ETIKETT": "Layout", "zonenchart.GD_WAHL": "Anzeige (Auswahl der Durchschnitte)",
    "zonenseite.ANKER_PLAETZE": "Speicher der eigenen Anker", "zonenseite.PROFIL_PLATZ": "Speicher der eigenen Anker", "chart.LINKS": "Layout", "chart.RECHTS": "Layout", "chart.LINIEN_SPIEL": "Layout (Skala)",
    "modell.DECKEL_USD": "Monatsdeckel der Prüfer", "modell.CACHE_SCHREIBEN": "Preis Prompt-Caching",
    "modell.CACHE_LESEN": "Preis Prompt-Caching", "quellen.GUELTIG_STUNDEN": "Datenpflege",
    "revier_pflege.HOECHSTENS": "Datenpflege", "revier_pflege.REVIER_WERT": "Datenpflege (Grenze des Reviers)",
    "revier_pflege.REVIER_KURS": "Datenpflege (Grenze des Reviers)",
    "revier_pflege.REVIER_UMSATZ": "Datenpflege (Grenze des Reviers)", "tpo_daten.JAHRE": "Datenpflege", "tv_kennzahlen.MINDEST": "Datenpflege",
    "datenpruefung.TAGE": "Datenprüfung", "datenpruefung.FAKTOREN": "Datenprüfung (Split-Faktoren)",
    "datenpruefung.GENAU": "Datenprüfung",
    "zeichen.ABLAGE_BEHALTEN": "Datenpflege", "fundament.MIO": "Anzeige (Millionen)",
    **{f"performance_seite.{n_}": "Layout" for n_ in ("B", "H", "UW", "KURVE_LINKS", "KURVE_RECHTS", "TSD_AB", "TAUSEND")},
}
VERSCHIEDEN = {"FENSTER", "JAHR", "MITTEL", "STICHPROBE", "STUFE", "TAGE",
               "LINKS", "RECHTS", "OBEN", "LUECKE"}   # Layout-Ränder je Bild bzw. verschiedene Begriffe (avwap.LUECKE = Kurslücke)   # gleicher Name, verschiedene Begriffe


def _quellen():
    import os
    hier = os.path.dirname(os.path.abspath(__file__))
    aus = {}
    for d in ("", os.path.join("..", "oberflaeche")):
        ordner = os.path.normpath(os.path.join(hier, d))
        for f in sorted(os.listdir(ordner)):
            if f.endswith(".py"):
                aus[f[:-3]] = os.path.join(ordner, f)
    return aus


def inventur():
    """→ {konstanten: {(modul, NAME): Wert}, abgedeckt: set, frei: [modul.NAME], kopien: [(NAME, [modul…])]}."""
    import ast
    konst, fdefs, alias = {}, {}, {}
    for m, pfad in _quellen().items():
        baum = ast.parse(open(pfad, encoding="utf-8").read())
        for n in baum.body:
            if isinstance(n, ast.ImportFrom) and n.module:     # from modul import NAME (as X): dieselbe Regel
                for a_ in n.names:
                    alias[(m, a_.asname or a_.name)] = (n.module, a_.name)
            if isinstance(n, ast.Assign):
                for tg in n.targets:
                    for nm in ([tg] if isinstance(tg, ast.Name) else getattr(tg, "elts", [])):
                        if isinstance(nm, ast.Name) and nm.id.isupper() and len(nm.id) > 2:
                            try:
                                v = ast.literal_eval(n.value)
                            except Exception:  # noqa: BLE001
                                continue
                            if isinstance(v, bool):
                                continue
                            if isinstance(v, (int, float)) or (isinstance(v, tuple) and v
                                                               and all(isinstance(e, (int, float)) for e in v)):
                                konst[(m, nm.id)] = v
            elif isinstance(n, ast.FunctionDef):
                fdefs[(m, n.name)] = n

    def nachbarn(f):
        aus_k, aus_f = set(), set()
        m = f[0]
        for n in ast.walk(fdefs[f]):
            if isinstance(n, ast.Name):
                if (m, n.id) in konst:
                    aus_k.add((m, n.id))
                if alias.get((m, n.id)) in konst:
                    aus_k.add(alias[(m, n.id)])
                if alias.get((m, n.id)) in fdefs:
                    aus_f.add(alias[(m, n.id)])
                if (m, n.id) in fdefs:
                    aus_f.add((m, n.id))
            elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
                if (n.value.id, n.attr) in konst:
                    aus_k.add((n.value.id, n.attr))
                if (n.value.id, n.attr) in fdefs:
                    aus_f.add((n.value.id, n.attr))
        return aus_k, aus_f

    start = {tuple(m.rsplit(".", 1)) for m in alle_messungen()}
    stapel, gesehen, abgedeckt = [f for f in start if f in fdefs], set(), set()
    while stapel:
        f = stapel.pop()
        if f in gesehen:
            continue
        gesehen.add(f)
        k_, f_ = nachbarn(f)
        abgedeckt |= k_
        stapel += list(f_)
    frei = sorted(f"{m}.{k}" for (m, k) in konst if (m, k) not in abgedeckt and f"{m}.{k}" not in TECHNIK)
    # Stufe 3 (Plan 22, 17.11.2026): Zahlen ohne Namen in allen Funktionen aller Module, nicht nur in denen der Karte –
    # Layout und Technik stehen mit der Marke „# Layout“ bzw. „# Technik“ in der Zeile
    ohne = [(m, f[1], z, wert, text) for f in sorted(fdefs) if (m := f[0]) not in TECHNIK_MODULE
            for z, wert, text in _zahlen_ohne_namen(fdefs[f], _quellen()[m])]
    namen = {}
    for (m, k), v in konst.items():
        namen.setdefault(k, []).append((m, v))
    kopien = [(k, sorted(m for m, _ in v)) for k, v in sorted(namen.items())
              if len({m for m, _ in v}) > 1 and k not in VERSCHIEDEN]
    return {"konstanten": konst, "abgedeckt": abgedeckt, "frei": frei, "kopien": kopien, "ohne_namen": ohne,
            "funktionen": len(gesehen)}


# Zahlen ohne Namen: jede feste Zahl in einer Regel-Funktion ist eine benannte Konstante. Frei bleiben Rechenzahlen
# (0, 1, 2, −1, 100), Mindestlängen der Daten (len(df) < 30), Rundung und Format, die Namen der GD (rolling(50)),
# Phasen 1–4 als Kennzahl, Stellen in einer benannten Konstante (ERMUEDET[3]) und kurze Ausschnitte für Texte (liste[:3]).
RECHENZAHLEN = {0, 1, 2, -1, 100}
GD_LAENGEN = {10, 20, 30, 40, 50, 150, 200}
PHASE_NAMEN = {"p", "ph", "phase", "ziel", "p_", "pa", "pn", "phl", "phasen", "alt", "neu"}
TECHNIK_MODULE = {"massive": "Datenquelle", "quellen": "Datenquelle", "daten": "Datenquelle", "marktdaten": "Datenquelle",
                  "tpo_daten": "Datenquelle", "tv_kennzahlen": "Datenquelle", "modell": "Schnittstelle (Anthropic)",
                  "strategen": "Schnittstelle (Anthropic)", "meldung": "Versand (ntfy)",
                  "regelkarte": "Prüfwerkzeug"}      # Abrufe, Wartezeiten, Börsenzeiten, Schnittstellen – keine Regel
MARKE_FREI = ("Layout", "Technik")   # Zeile mit „# Layout“ bzw. „# Technik“: Pixel, Schrift, Fenster der Anzeige, Abruf


def _zahlen_ohne_namen(funktion, pfad):
    """Zahlen ohne Namen in einer Funktion → [(Zeile, Wert, Code)]."""
    import ast
    zeilen = _zeilen(pfad)
    for n in ast.walk(funktion):
        for c in ast.iter_child_nodes(n):
            c._eltern = n
    aus = []
    for n in ast.walk(funktion):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) \
                and n.value not in RECHENZAHLEN and not _frei(n, ast) and not _markiert(zeilen[n.lineno - 1]):
            aus.append((n.lineno, n.value, zeilen[n.lineno - 1].strip()[:100]))
    return aus


def _markiert(zeile):
    """Zeile mit der Marke „# Layout“ oder „# Technik“ (im Kommentar): keine Regel."""
    i = zeile.find("#")
    return i >= 0 and any(w in zeile[i:] for w in MARKE_FREI)


def _zeilen(pfad, _cache={}):  # noqa: B006
    if pfad not in _cache:
        _cache[pfad] = open(pfad, encoding="utf-8").read().split("\n")
    return _cache[pfad]


def _frei(n, ast):
    p, v = getattr(n, "_eltern", None), n.value

    def namen(x):
        return {y.id for y in ast.walk(x) if isinstance(y, ast.Name)} | {y.attr for y in ast.walk(x) if isinstance(y, ast.Attribute)}
    q = p
    for _ in range(4):                       # Mindestlänge der Daten: len(df) < 4 * n + 4
        if isinstance(q, ast.Compare) and any(isinstance(x, ast.Call) and getattr(x.func, "id", None) == "len"
                                              for x in [q.left] + q.comparators):
            return True
        if not isinstance(q, (ast.BinOp, ast.UnaryOp, ast.Compare)):
            break
        q = getattr(q, "_eltern", None)
    if isinstance(p, ast.Call) and getattr(p.func, "id", None) == "round" and n is not p.args[0]:
        return True
    if isinstance(p, ast.FormattedValue):
        return True
    if v in (7, 3) and isinstance(p, ast.BinOp) and isinstance(p.op, ast.Div):
        return True
    if isinstance(p, ast.Call) and isinstance(p.func, ast.Attribute) and p.func.attr == "rolling" and v in GD_LAENGEN:
        return True
    if v in (1, 2, 3, 4):
        q = p
        if isinstance(q, ast.Tuple):
            q = getattr(q, "_eltern", None)
        if isinstance(q, ast.Compare) and (namen(q) & PHASE_NAMEN):
            return True
        if isinstance(q, ast.Assign) and any(isinstance(t, ast.Name) and t.id in PHASE_NAMEN for t in q.targets):
            return True
        if isinstance(q, ast.Dict):
            return True
    if isinstance(p, ast.Subscript) and p.slice is n and isinstance(p.value, ast.Name) and p.value.id.isupper():
        return True
    if isinstance(p, ast.Slice) and isinstance(getattr(p, "_eltern", None), ast.Subscript) and p.lower is None and v in (3, 5):
        return True
    return False


def alle_messungen():
    aus = set()
    for b in list(KAESTEN.values()) + list(WERKZEUGE.values()):
        for x in b:
            aus.update(x["messung"])
    for x in ZEICHEN + BEREICHE:
        aus.update(x["messung"])
    return aus


# ── Wachposten ──────────────────────────────────────────────────────────────────────────────────────────────────
def _gibt_es(ziel):
    mod, fn = ziel.rsplit(".", 1)
    try:
        return callable(getattr(importlib.import_module(mod), fn, None))
    except Exception:  # noqa: BLE001
        return False


def wachposten():
    """Prüft die Karte gegen den Code → Liste von {ampel, art, bild, name, text, alarm}. rot = nicht gemessen bzw.
    nicht gebaut, gelb = erst teilweise; alarm = Karte und Code passen nicht zusammen (Messfunktion fehlt, Prüfer weicht
    ab, Zustand ohne Kasten, Reihe des Kartentischs fehlt) – das ist der Fall „vergessen“ und muss sofort behoben werden.
    Grün steht nur in der Zusammenfassung (zaehlen)."""
    aus = []

    def melde(ampel, art, bild, name, text, alarm=True):
        """alarm = Karte und Code passen nicht zusammen (sofort beheben); sonst eine bekannte, geplante Lücke."""
        aus.append({"ampel": ampel, "art": art, "bild": bild, "name": name, "text": text, "alarm": alarm})

    for bild in ("titel", "gruppe", "markt"):
        for art, liste in (("Kasten", KAESTEN[bild]), ("Werkzeug", WERKZEUGE[bild])):
            for x in liste:
                for m in x["messung"]:
                    if not _gibt_es(m):
                        melde("rot", art, bild, x["name"], f"Messfunktion {m} fehlt im Code")
                if x["stand"] == "fehlt":
                    melde("rot", art, bild, x["name"], "nicht gemessen" + (f" – {x['luecke']}" if x.get("luecke") else ""),
                          alarm=False)
                elif x["stand"] == "teilweise":
                    melde("gelb", art, bild, x["name"], "erst teilweise" + (f" – {x['luecke']}" if x.get("luecke") else ""),
                          alarm=False)
                elif not x["messung"]:
                    melde("rot", art, bild, x["name"], "als gemessen eingetragen, aber ohne Messfunktion")
                if not x.get("pruefer"):
                    melde("rot", art, bild, x["name"], "kein Prüf-Element – der Prüfer sieht den Kasten nicht")
    for z in ZEICHEN:
        for m in z["messung"]:
            if not _gibt_es(m):
                melde("rot", "Zeichen", "titel", z["name"], f"Messfunktion {m} fehlt im Code")
        if not z.get("pruefer"):
            melde("rot", "Zeichen", "titel", z["name"], "kein Prüf-Element – der Prüfer sieht das Zeichen nicht")
    # Jede Funktion in zeichen.py, die ein Zeichen setzt, steht auf der Karte (sonst wurde ein Zeichen vergessen)
    try:
        import ast
        import inspect
        import zeichen as zmod
        baum = ast.parse(inspect.getsource(zmod))
        auf_karte = {m for x in ZEICHEN + [y for b in KAESTEN.values() for y in b] + [y for b in WERKZEUGE.values() for y in b]
                     for m in x["messung"]}
        for f in baum.body:
            if isinstance(f, ast.FunctionDef) and f.name != "_zeichen" and any(
                    isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_zeichen" for n in ast.walk(f)):
                if f"zeichen.{f.name}" not in auf_karte:
                    melde("rot", "Zeichen", "titel", f.name, f"zeichen.{f.name} setzt Zeichen, steht aber nicht auf der Karte")
    except Exception as e:  # noqa: BLE001
        melde("rot", "Zeichen", "titel", "zeichen.py", f"nicht lesbar: {e}")
    for b in BEREICHE:
        for m in b["messung"]:
            if not _gibt_es(m):
                melde("rot", "Bereich", "bereich", b["name"], f"Messfunktion {m} fehlt im Code")
        if not b.get("pruefer"):
            melde("gelb", "Bereich", "bereich", b["name"], "kein Prüfer sieht diesen Bereich" +
                  (f" – {b['luecke']}" if b.get("luecke") else ""), alarm=False)
    # Inventur: jede feste Regel des Codes gehört der Karte, keine Regel steht doppelt
    try:
        inv = inventur()
        for k in inv["frei"]:
            melde("rot", "Regel", "inventur", k, f"feste Regel {k} = {inv['konstanten'][tuple(k.split('.'))]} gehört "
                                                 "keinem Eintrag der Karte – blinder Fleck")
        for k, ms in inv["kopien"]:
            melde("rot", "Regel", "inventur", k, f"{k} steht doppelt im Code ({', '.join(ms)}) – eine Quelle, sonst "
                                                 "laufen die Kopien auseinander")
        for m, f, z, wert, text in inv["ohne_namen"]:
            melde("rot", "Regel", "inventur", f"{m}.{f}", f"Zahl {wert} ohne Namen (Zeile {z}: {text}) – jede feste Regel "
                                                         "braucht einen Namen und einen Eintrag der Karte")
    except Exception as e:  # noqa: BLE001
        melde("rot", "Regel", "inventur", "Code", f"Inventur nicht lesbar: {e}")
    return aus


def zaehlen(meldungen=None):
    """{bild: (gesamt, rot, gelb)} für die Zusammenfassung des Wachpostens."""
    m = wachposten() if meldungen is None else meldungen
    aus = {}
    for bild in ("titel", "gruppe", "markt"):
        namen = [x["name"] for x in KAESTEN[bild] + WERKZEUGE[bild] + (ZEICHEN if bild == "titel" else [])]
        rot = {x["name"] for x in m if x["bild"] == bild and x["ampel"] == "rot"}
        gelb = {x["name"] for x in m if x["bild"] == bild and x["ampel"] == "gelb"} - rot
        aus[bild] = (len(namen), len(rot), len(gelb))
    return aus
