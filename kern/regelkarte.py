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
                   "Wert neu bewertet.",
             fuehrt="Kullamägi/Bonde (Episodic Pivot)", zeichen="O'Neil (das „N“: neues Produkt, neue Zahlen), Mickys Zahlen-Reaktion",
             messung=["auktion.titel", "avwap.zahlentag", "zahlen_reaktion.reaktionstag"], stand="gemessen",
             pruefer=["Anlass"]),
        dict(name="Anlass: Verteidiger leer", zustand=None,
             regel="Angebot aufgebraucht: Enge, Volumen trocknet aus, Einquetschung.",
             fuehrt="Minervini (VCP, Volumen trocknet aus)", zeichen="Wyckoff",
             messung=["zeichen.enge_trocken", "zeichen.einquetschung", "vcp_zone.enge"], stand="gemessen",
             pruefer=["Anlass", "Einquetschung"]),
        dict(name="Anlass: Zwang", zustand=None,
             regel="Stopps, Gefangene; geht im Spring/Upthrust auf (Micky 14.11.2026, kein eigenes Zeichen).",
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
             messung=["auktion.titel", "auktion.kraft_ohne_weg", "auktion.exzess"], stand="gemessen",
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
                   "bestätigt, wenn der Wert folgt.",
             fuehrt="O'Neil und Minervini (Ausbruch über den Pivot)",
             zeichen="Kullamägi (Ausbruch am Tag), Shannon (Kurs über dem AVWAP vom Hoch), Dalton (Wert folgt, bestätigt)",
             messung=["vcp_zone.ausbruch", "marketprofile.analyse"], stand="gemessen",
             pruefer=["abgelehnt/angenommen"]),
        dict(name="Ungleichgewicht", zustand="Ungleichgewicht",
             regel="Schnell durch dünnes Volumen – Kullamägi führt: der Kurs reitet am 10er bzw. 20er.",
             fuehrt="Kullamägi (10er/20er)", zeichen="Weinstein (Stufe 2), Dalton (dünnes Volumen)",
             messung=["auktion.titel", "phase.aktuell"], stand="teilweise",
             luecke="heute an Phase 2/4 bzw. der Dow-Struktur gemessen; der 10er/20er kommt mit Schritt 5",
             pruefer=["Ungleichgewicht"]),
        dict(name="Ende: Gegner antwortet", zustand="Ende des Laufs",
             regel="Knoten im Volumenprofil (Mauer), alter Wert, AVWAP vom alten Hoch, Exzess, Kraft ohne Weg am Rand.",
             fuehrt="Dalton und Shannon", zeichen="Wyckoff (Kraft ohne Weg)",
             messung=["volumenprofil.knoten", "auktion.kraft_ohne_weg", "auktion.exzess"], stand="teilweise",
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
             messung=["basen.zaehlen"], stand="gemessen", pruefer=["Neue Balance/Basenzählung"]),
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
             messung=["auktion.gruppe", "fuehrer_rang.von"], stand="gemessen", pruefer=["Anführer bricht aus"]),
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
GRUNDSATZ = {
    "titel": "Zustände der App: Balance, Test am Rand, abgelehnt, angenommen, Ungleichgewicht, Ende des Laufs. Ende des "
             "Laufs hat drei Kräfte: Gegner antwortet, Antrieb erlischt, Wert akzeptiert. Weinsteins Stufen sind der "
             "Rahmen: der Kreislauf läuft in jeder Stufe neu ab.",
    "gruppe": "Meister: O'Neil und Weinstein führen – die führenden Aktien kommen aus führenden Gruppen, eine Gruppe ist "
              "stark, wenn die ganze Truppe vorrückt (Gruppen-RS, Breite, Zufluss); Kullamägis Führer-Rang (die stärksten "
              "2 %) benennt die Anführer nur als Zeichen. Felder der Rotationskarte: RS-Stärke und Schwung je um 100 "
              "(über 100 = besser als der Markt bzw. steigend).",
    "markt": "Regel der App (Micky, Regel 8): die Haltung des Marktes gilt für den Markt, nicht für den Titel – kein "
             "Titel wird wegen des Marktes verworfen.",
}

# ── Werkzeuge ───────────────────────────────────────────────────────────────────────────────────────────────────
WERKZEUGE = {
    "titel": [
        dict(name="Zone", regel="Zone der App: beginnt am ältesten Hoch ohne Schlusskurs darüber (ein Hoch darüber ohne "
                                "Schluss darüber bricht sie nicht – ein abgelehnter Vorstoß; so entschieden, nicht als "
                                "Widerspruch melden). Eine Tasse ab 7 Wochen gilt als gescheitert, wenn der Kurs nach der "
                                "rechten Seite in der unteren Hälfte schließt (Schlusskurs, nicht Tagestief). Über 50 % tief "
                                "ist keine Base; eine zu kurze Zone ist noch im Aufbau (kein Pivot).",
             messung=["vcp_zone.zone"], stand="gemessen",
             pruefer=["Zone: Beginn", "Zone: Unterkante/Tiefe", "Zone: Name", "Zone: keine/offen"]),
        dict(name="Enge und Pivot", regel="Kontraktionen: die linke Seite bis zum Tief der Base, dann jede Welle der "
                                          "rechten Seite (jede mindestens 3 Handelstage, höchstens 6 Wellen); Pivot = Hoch "
                                          "der letzten Kontraktion; grün nur mit ausgetrocknetem Volumen und nicht in "
                                          "Phase 4. Drittel der Base: Low Cheat unten, Cheat Mitte, Pivot oben.",
             messung=["vcp_zone.enge"], stand="gemessen",
             pruefer=["Pivot", "Drittel des Pivots", "Enge/Kontraktionen"]),
        dict(name="Ausbruchsvolumen", regel="Ausbruchsvolumen ist bei der App ein Zeichen, keine Pflicht – über dem "
                                            "50-Tage-Schnitt reicht (Entscheidung des Nutzers, O'Neils 1,4-fach ist ihm zu "
                                            "streng); ein Ausbruch mit wenig Volumen ist kein Widerspruch, höchstens ein "
                                            "schwaches Zeichen.",
             messung=["vcp_zone.ausbruch"], stand="gemessen", pruefer=["abgelehnt/angenommen"]),
        dict(name="Gegenseite", regel="Mauer (Knoten über dem Kurs) und Stütze (Knoten darunter) aus dem Volumenprofil: "
                                      "jeder Gipfel ab 30 % des größten und 10 % über dem höheren Tal daneben.",
             messung=["volumenprofil.knoten"], stand="gemessen", pruefer=["Gegenseite (Mauer/Stütze)"]),
        dict(name="Eigen oder geliehen", regel="Eigen: RS-Linie in 20 Tagen mindestens 5 % in Laufrichtung; geliehen: "
                                               "höchstens 1 % (der Markt trägt).",
             messung=["auktion.kraft"], stand="gemessen", pruefer=["Eigen oder geliehen"]),
        dict(name="Phase", regel="Weinsteins Stufen an der 40-Wochen-Linie (Wechsel 3 → 4 erst, wenn die Linie fällt); "
                                 "Rahmen für jeden Kasten.",
             messung=["phase.aktuell", "zeichen.kreislauf"], stand="teilweise",
             luecke="Neubau als Rahmen in Schritt 8 (30 oder 40 Wochen, Sperre nach Phase 4)",
             pruefer=["Kreislauf/Phase"]),
        dict(name="Short-Form", regel="Ermüdung, Bärenflagge, Bruch der Spanne (siehe Setups).",
             messung=["vcp_zone.ermuedung", "vcp_zone.baerenflagge", "vcp_zone.spannenbruch"], stand="gemessen",
             pruefer=["Short-Form"]),
        dict(name="AVWAP letztes Hoch", regel="Letztes Hoch = jüngstes Hoch, das der Kurs nicht überschritten hat und "
                                              "das bestätigt ist (Rückgang ab 8 % danach oder Wochen-Schwunghoch mit 2 "
                                              "Wochen davor und danach tiefer).",
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
        dict(name="AVWAP Ereignis", regel="Ereignis = der jüngste Zahlentag (jeder, gleich wie stark die Reaktion), die "
                                          "jüngste Lücke ab 4 % oder Volumenspitze ab doppeltem Schnitt mit Bewegung ab "
                                          "3 % (6 Monate).",
             messung=["avwap.anker", "avwap.zahlentag"], stand="gemessen", pruefer=["AVWAP Ereignis"]),
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
         regel="In den letzten 10 Tagen: Tief höchstens 1 ATR unter dem Tief der 20 Tage davor (Spanne höchstens 15 % "
               "breit), Schluss innerhalb von 3 Tagen wieder darüber mit Volumen über dem Schnitt = Spring. Upthrust: "
               "Hoch über der Oberkante mit Volumen über dem Schnitt, Schluss im unteren Drittel des Tages und wieder in "
               "der Spanne.",
         messung=["zeichen.spring"], pruefer=["Test am Rand: Zeichen", "abgelehnt/angenommen"]),
    dict(name="Einquetschung", art="Struktur", meister="Micky (aufsteigendes Dreieck)",
         regel="Steigende Tiefs gegen eine flache Oberkante: in 60, sonst 120 Tagen mindestens 2 Schwunghochs innerhalb "
               "±1,5 % der Oberkante, die flache Kante seit mindestens 3 Wochen, mindestens 3 steigende Tiefs (ein Spring "
               "bricht die Reihe nicht), Spanne und Volumen werden kleiner. Gespiegelt.",
         messung=["zeichen.einquetschung", "zeichen.kreislauf"], pruefer=["Einquetschung"]),
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
ZEICHEN_GEWICHT = ("Die Zeichen werden gewogen: Struktur, Volumen, RS und Ereignis. Wer am Rand stärker ist, zeigt das "
                   "Gewicht beider Seiten. Ein Wechsel der Phase zeichnet sich erst ab, wenn ein Zeichen der Struktur UND "
                   "eines aus Volumen oder RS auf derselben Seite stehen und die Seite klar überwiegt (Gewicht mindestens 4 "
                   "und doppelt so schwer wie die Gegenseite).")

# ── Setups als Wege durch den Kreislauf ─────────────────────────────────────────────────────────────────────────
SETUPS = [
    dict(name="Base-Ausbruch", reihen=["m_spitze", "m_weitere", "vcp"], lehrer="Minervini",
         weg="Balance → Test am Rand → angenommen",
         regel="Trendvorlage (Kurs über GD150/200, GD150 über GD200, GD200 steigt seit einem Monat, GD50 über GD150/200, "
               "Kurs über GD50, mindestens 30 % über dem 52-Wochen-Tief, höchstens 25 % unter dem Hoch), RS ab 70, Zahlen "
               "wachsen, reife Base (fertig, Länge ok, höchstens 50 % tief), Enge (mindestens 2 Kontraktionen, jede "
               "höchstens 70 % der vorigen, letzte höchstens 10 %, Volumen leiser). ★ = grün und Kurs bis 5 % unter bzw. "
               "über dem Pivot. Pivot = Hoch der letzten Kontraktion. Nach einem Ausbruch gilt das Setup 4 Wochen weiter. "
               "Nur Muster: die Zone hat eine grüne Enge, aber die Systemregeln (Trendvorlage, Zahlen) fehlen.",
         einstieg="Zwei Einstiege: früh am Rand (Low Cheat, Cheat – der Pivot liegt unter der Oberkante der Zone) und am "
                  "Ausbruch über den Pivot.",
         stopp="unter der letzten Kontraktion, höchstens 8 %", widerlegt="„abgelehnt“ (Schluss zurück in der Zone)",
         abweichung="Base bis 50 % tief zählt als reif, grün nur bis 33 % (Micky: tiefe Korrekturen sind Konsolidierung)",
         messung=["system_minervini.pruefen", "vcp_zone.enge"], stand="teilweise",
         luecke="früher Einstieg am Rand (Schritt 2) und Struktur-Stopp (Schritt 3) fehlen im Plan"),
    dict(name="Flagge", reihen=["flagge"], lehrer="Kullamägi", weg="eine kleine Balance mitten im Ungleichgewicht → angenommen",
         regel="Fahnenstange ab 30 % in höchstens 13 Wochen, Flagge 1–8 Wochen, höchstens 25 % tief, im Aufwärtstrend "
               "(Kurs über steigendem GD50), Volumen in der Flagge leiser als in der Stange, steigende Tiefs (das Tief der "
               "zweiten Hälfte höchstens 0,5 ATR unter dem der ersten); Pivot = Oberkante.",
         einstieg="Ausbruch über die Oberkante", stopp="Tagestief, höchstens eine Tagesspanne",
         widerlegt="Schluss zurück in der Flagge", abweichung="",
         messung=["vcp_zone.zone", "kartentisch.flagge_im_trend"], stand="teilweise",
         luecke="Struktur-Stopp (Schritt 3) fehlt im Plan"),
    dict(name="Momentum-Ausbruch", reihen=["k_breakout"], lehrer="Kullamägi",
         weg="eine kleine Balance mitten im Ungleichgewicht → angenommen",
         regel="Führer (oberste 2 % nach 1, 3 oder 6 Monaten), Pause 1–3 Wochen nach einem Schub, hält den GD20, Kurs "
               "davor 3 Wochen über dem GD50; Pivot = Oberkante der Pause.",
         einstieg="Ausbruch über die Oberkante der Pause", stopp="Tagestief, höchstens eine Tagesspanne",
         widerlegt="Schluss zurück in der Pause", abweichung="",
         messung=["system_kullamaegi.breakout"], stand="teilweise", luecke="Struktur-Stopp (Schritt 3) fehlt im Plan"),
    dict(name="Sprung (EP)", reihen=["k_ep"], lehrer="Kullamägi", weg="Anlass „neue Information“ → direkt angenommen",
         regel="Tagesgewinn ab 10 %, Eröffnung über dem Vortageshoch, Volumen ab 3-fach (10-fach ideal), in den letzten "
               "10 Tagen, Kurs hält das Tief des Sprungtags; Nachricht: Zahlen am Sprungtag, sonst ab 5-fach Volumen und "
               "Schluss im oberen Drittel.",
         einstieg="Hoch des Sprungtags", stopp="unter dem Tief des Sprungtags", widerlegt="Schluss unter dem Tief des Sprungtags",
         abweichung="", messung=["system_kullamaegi.episodic_pivot"], stand="gemessen"),
    dict(name="Zahlen-Reaktion", reihen=["zahlen"], lehrer="Micky (Drift nach den Zahlen, Shannons Anker am Ereignistag)",
         weg="Anlass „neue Information“ → direkt angenommen",
         regel="Reaktion ab 3 % in den letzten 20 Tagen, Volumen über dem Schnitt, Schluss im oberen Drittel (short: "
               "unteren), seitdem kein Schluss unter dem Tief und dem AVWAP ab dem Reaktionstag, Kurs über dem GD50 (short "
               "gespiegelt).",
         einstieg="AVWAP ab dem Reaktionstag, Zone bis 5 % darüber", stopp="unter dem Tief des Reaktionstags",
         widerlegt="Schluss unter dem Tief bzw. dem AVWAP ab dem Reaktionstag", abweichung="",
         messung=["zahlen_reaktion.pruefen"], stand="gemessen"),
    dict(name="Ermüdung (Short)", reihen=["k_ermuedung"], lehrer="Kullamägi", weg="gespiegelt: Ende des Laufs → abgelehnt",
         regel="Flagge nach Stange ab 30 % bricht nach unten (Schluss unter der Unterkante, letzte 5 Tage).",
         einstieg="Unterkante; grün nur bis 5 % darunter", stopp="über dem Hoch des Auslösetags",
         widerlegt="Schluss zurück in der Flagge", abweichung="", messung=["vcp_zone.ermuedung"], stand="gemessen"),
    dict(name="Bärenflagge (Short)", reihen=["k_baerenflagge"], lehrer="Kullamägi",
         weg="gespiegelt: kleine Balance im Ungleichgewicht abwärts → angenommen abwärts",
         regel="Fall ab 15 % in höchstens 30 Tagen, Driften 3–25 Tage mit steigenden Tiefs, holt höchstens die Hälfte "
               "zurück, GD50 fällt, Bruch unter das Tief des Driftens.",
         einstieg="Unterkante; grün nur bis 5 % darunter", stopp="über dem Hoch des Auslösetags",
         widerlegt="Schluss zurück im Driften", abweichung="", messung=["vcp_zone.baerenflagge"], stand="gemessen"),
    dict(name="Bruch der Spanne (Short)", reihen=["k_bruch"], lehrer="Weinstein", weg="gespiegelt: Balance → angenommen abwärts",
         regel="Basis oder Verteilung ab 6 Wochen, höchstens 40 % breit, Schluss 1 % unter ihrem Tief.",
         einstieg="Unterkante; grün nur bis 5 % darunter", stopp="über dem Hoch des Auslösetags",
         widerlegt="Schluss zurück in der Spanne", abweichung="", messung=["vcp_zone.spannenbruch"], stand="gemessen"),
    dict(name="Spring / Upthrust", reihen=[], lehrer="Wyckoff", weg="abgelehnt → Lauf zum anderen Rand",
         regel="Kurs bricht über den Rand und schließt zurück in der Zone (Spring unten = long, Upthrust oben = short); "
               "Ziel der andere Rand.",
         einstieg="beim Schluss zurück in der Zone", stopp="unter dem Tief bzw. über dem Hoch des Fehlausbruchs",
         widerlegt="neuer Schluss jenseits des Randes", abweichung="", messung=[], stand="fehlt",
         luecke="beschlossen (Micky 14.11.2026), Bau in Schritt 4 – siehst du einen, melde ihn als „Übersehen“"),
]

# Für alle Setups (Gefechtsordnung, Micky 14.11.2026)
SETUP_GRUNDSATZ = [
    "Stopp: die App zeigt beide – den Struktur-Stopp (Base: unter der letzten Kontraktion, höchstens 8 %; schnelles "
    "Setup: Tagestief, höchstens eine Tagesspanne) und 1,5 ATR; der Nutzer wählt je Trade. Heute steht im Plan noch "
    "einheitlich 1,5 ATR vom Einstieg (Entscheidung des Nutzers vom 09.11.2026; der Struktur-Stopp kommt mit Schritt 3) – "
    "weicht er von der Regel des Meisters ab, melde es als strittig, mit dem Stopp des Meisters. Prüfe, ob der "
    "Struktur-Stopp dort sitzt, wo der Weg widerlegt ist.",
    "Ausstieg: der Stopp folgt dem 10er (schnelle Titel) bzw. 20er; Mauer, Kraft ohne Weg und Klimax ziehen ihn enger.",
    "Daltons Annahme (der Wert folgt dem Kurs) ist ein Zeichen zum Halten oder Nachkaufen, keine Bedingung.",
    "Ausbruchsvolumen ist ein Zeichen, keine Pflicht – über dem 50-Tage-Schnitt reicht (Entscheidung des Nutzers, "
    "O'Neils 1,4-fach ist ihm zu streng); wenig Volumen ist kein Widerspruch, höchstens ein schwaches Zeichen.",
    "Überall: Fehlausbruch oder Rücktest → nicht grün; Kurs steht still (Tagesspanne unter 0,5 %) → nicht grün.",
    "Markt (Regel 8): die Haltung des Marktes gilt für den Markt, nicht für den Titel – ein Setup wird nie wegen des "
    "Marktes verworfen; Stärke in der Schwäche ist ein Vorteil.",
    "Gruppe: die ganze Truppe misst (Gruppen-RS, Breite, Zufluss); prüfe, ob das Setup Rückenwind der Gruppe hat, und "
    "melde es als Zeichen, nicht als Fehler.",
]
VORRANG = ("Sprung (EP) → Zahlen-Reaktion → Ermüdung/Bärenflagge/Bruch der Spanne → Base-Ausbruch ★ (Kaufzone) → "
           "Flagge → Momentum-Ausbruch → Base-Ausbruch → nur Muster; „auch“ nennt die übrigen")

# ── Meister (recherchiert 14.11.2026) ───────────────────────────────────────────────────────────────────────────
MEISTER = [
    ("O'Neil",
     "Tasse 7–65 Wochen, 12–33 % tief (im Bärenmarkt bis 40–50 %). Der Henkel liegt in der oberen Hälfte der Base, "
     "höchstens etwa 12–15 % tief, sein Hoch höchstens 15 % unter dem Hoch der linken Seite. Pivot = Hoch des Henkels, "
     "ohne Henkel das Hoch der linken Seite. Doppelboden: das zweite Tief unterschreitet das erste, Pivot = die Spitze in "
     "der Mitte des W. Flache Base ab 5 Wochen, höchstens etwa 15 % tief. Ausbruch mit Volumen über dem Schnitt; "
     "Fehlausbruch: zurück unter den Pivot. Distributionstage: fallender Schluss bei höherem Volumen als am Vortag.",
     "Kauf am Pivot mit Volumen deutlich über dem Schnitt, nicht mehr als 5 % darüber; Verlust höchstens 7–8 %."),
    ("Minervini",
     "VCP: 2–6 Kontraktionen, jede grob halb so tief wie die vorige, das Volumen trocknet aus; Pivot = Hoch der letzten "
     "Kontraktion. Low Cheat im unteren Drittel, Cheat im mittleren, Henkel im oberen Drittel. Nach einer gescheiterten "
     "Tasse bildet sich eine neue Base.",
     "VCP mit mindestens 2 Kontraktionen, jede kleiner, Volumen trocknet aus; Kauf beim Ausbruch über den Pivot mit "
     "steigendem Volumen, bis 5 % darüber; Stopp unter dem Tief der letzten Kontraktion, höchstens etwa 8 % (absolut "
     "10 %). Kauf nur in Stufe 2."),
    ("Kullamägi",
     "Flagge: Fahnenstange ab 30 % in 1–3 Monaten, danach 1–8 Wochen enges Seitwärts mit steigenden Tiefs. Episodic "
     "Pivot: Lücke mit sehr hohem Volumen auf eine Nachricht.",
     "Breakout nach einem Lauf von 30–100 % in 1–3 Monaten, geordnete Pause mit höheren Tiefs, enger werdend, am "
     "10er/20er, 2 Wochen bis 2 Monate; Einstieg über dem Hoch der Eröffnungsspanne oder Ausbruch im Tageschart, nicht "
     "vorweggenommen; Stopp am Tagestief, nie weiter als eine durchschnittliche Tagesspanne. EP: Lücke ab 10 % bei "
     "riesigem Volumen auf eine Nachricht, Einstieg Hoch der Eröffnungsspanne, Stopp am Tagestief. Short: Stopp am "
     "Tageshoch."),
    ("Weinstein",
     "Phasen: 1 Basis seitwärts um die flache 30-Wochen-Linie, 2 Aufwärts über der steigenden Linie, 3 Verteilung "
     "seitwärts, die Linie flacht ab, 4 Abwärts unter der fallenden Linie.",
     "Short nur in Stufe 4 bzw. beim Bruch aus Stufe 3 (Kurs unter der fallenden 30-Wochen-Linie)."),
    ("Wyckoff",
     "Spring = Tief kurz unter der Unterkante der Spanne, schnell zurückgekauft; Upthrust = Hoch kurz über der "
     "Oberkante, Schluss zurück in der Spanne. Kraft ohne Weg: viel Volumen, wenig Kursweg.", ""),
    ("Morales/Kacher",
     "Pocket Pivot: Volumen des Anstiegstags über dem höchsten Volumen der Abwärtstage der letzten 10 Tage.", ""),
    ("Einquetschung", "Steigende Tiefs gegen eine flache Oberkante (aufsteigendes Dreieck).", ""),
    ("Shannon",
     "AVWAP: Ein Hoch wird erst durch den Rückgang danach zum Anker. Anker sind das Pivot-Tief, das einen Trend "
     "startete, das jüngste große Hoch, der Tag der Zahlen bzw. eine Kurslücke; mehrere übereinander.", ""),
    ("Dalton",
     "Der Markt geht von Balance zu Balance; Balance = überlappender Wert; das Profil fasst die laufende Balance. Exzess "
     "= scharfe Ablehnung am Extrem (Auktion dort beendet); flache Kante (schwaches Hoch/Tief) = Auktion unfertig.", ""),
]


# ── Anleitungen für die Prüfer ──────────────────────────────────────────────────────────────────────────────────
def _kasten_zeile(k):
    m = k["fuehrt"] + (f"; Zeichen: {k['zeichen']}" if k.get("zeichen") else "")
    s = "" if k["stand"] == "gemessen" else f" [App: {'noch nicht gemessen' if k['stand'] == 'fehlt' else 'erst teilweise gemessen'}" \
                                            f"{' – ' + k['luecke'] if k.get('luecke') else ''}]"
    return f"- {k['name']}: {k['regel']} (führt: {m}){s}"


def block_kaesten(bild):
    """Die Kästen eines Bildes als Abschnitt der Anleitung – genau so in der App gezeichnet und gemessen."""
    zeilen = [_kasten_zeile(k) for k in KAESTEN[bild]]
    w = [f"- {x['name']}: {x['regel']}" + ("" if x["stand"] == "gemessen" else
                                           f" [App: erst teilweise – {x.get('luecke', '')}]") for x in WERKZEUGE[bild]]
    teil = ["Die Kästen (Regelkarte der App – jeder Kasten genau einmal; fehlt ein Kasten, den die Zahlen oder das Bild "
            "zeigen, melde ihn):"] + zeilen + [GRUNDSATZ[bild]]
    if w:
        teil += ["", "Wie die App misst (damit du die Absicht kennst; prüfe trotzdem gegen die Meister):"] + w
    if bild == "titel":
        teil += ["", "Die Zeichen der App (Stärke und Schwäche, je mit Spiegelbild):"] \
            + [f"- {z['name']} ({z['art']}, {z['meister']}): {z['regel']}" for z in ZEICHEN] + [ZEICHEN_GEWICHT]
    return "\n".join(teil)


def block_meister(wofuer="chart"):
    """Die Regeln der Meister: „chart“ für den Chart-Prüfer, „setup“ für den Setup-Prüfer."""
    return "\n".join(f"- {n}: {c if wofuer == 'chart' else st}" for n, c, st in MEISTER if (c if wofuer == "chart" else st))


def block_setups():
    """Die Setups der App mit Regel und Weg durch den Kreislauf – für den Setup-Prüfer."""
    teil = [f"Die Setups der App (ein eigenes System, die Meister sind Lehrer; Vorrang bei mehreren: {VORRANG}):"]
    for s in SETUPS:
        stand = "" if s["stand"] == "gemessen" else \
            f" [App: {'noch nicht gebaut' if s['stand'] == 'fehlt' else 'erst teilweise'} – {s.get('luecke', '')}]"
        teil.append(f"- {s['name']} (Lehrer {s['lehrer']}): {s['regel']} Weg: {s['weg']}. Einstieg: {s['einstieg']}. "
                    f"Stopp des Weges: {s['stopp']}. Widerlegt: {s['widerlegt']}."
                    + (f" Eigene Abweichung: {s['abweichung']}." if s.get("abweichung") else "") + stand)
    teil += ["", "Die Gefechtsordnung der App (Micky 14.11.2026) – jedes Setup ist ein Weg durch den Kreislauf "
                 "Balance → Test am Rand → abgelehnt/angenommen → Ungleichgewicht → Ende des Laufs → neue Balance:"]
    teil += [f"- {g}" for g in SETUP_GRUNDSATZ]
    return "\n".join(teil)


def elemente(bild):
    """Formularfelder des Prüfers: jedes Prüf-Element der Karte genau einmal, in Kartenreihenfolge, dazu „Sonstiges“."""
    if bild == "setup":
        return ["Urteil: grün zu Unrecht", "Urteil: zu streng (Regeln erfüllt, nicht grün)", "Regel falsch gemessen",
                "Wahl des Setups", "Einstieg/Pivot", "Kaufzone/Abstand", "Stopp", "Übersehen (kein Setup, aber eins da)",
                "Short", "Sonstiges"]
    aus = []
    erst = {"titel": ["Zustand", "Anlass"], "gruppe": ["Zustand der Gruppe", "Anlass"], "markt": ["Zustand des Marktes", "Anlass"]}[bild]
    for e in erst + [p for x in KAESTEN[bild] + WERKZEUGE[bild] + (ZEICHEN if bild == "titel" else [])
                     for p in x["pruefer"]]:
        if e not in aus:
            aus.append(e)
    return aus + ["Sonstiges"]


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
    # Jeder Zustand der App hat einen Kasten
    try:
        import auktion
        for z in auktion.ZUSTAENDE:
            if not any(k.get("zustand") == z for k in KAESTEN["titel"]):
                melde("rot", "Zustand", "titel", z, "Zustand der App ohne Kasten auf der Regelkarte")
    except Exception as e:  # noqa: BLE001
        melde("rot", "Zustand", "titel", "auktion", f"nicht lesbar: {e}")
    # Die Prüfer arbeiten mit genau den Elementen der Karte
    for mod_name, bilder in (("chartpruefer", (("ELEMENTE", "titel"), ("ELEMENTE_GRUPPE", "gruppe"),
                                               ("ELEMENTE_MARKT", "markt"))), ("setuppruefer", (("ELEMENTE", "setup"),))):
        try:
            mod = importlib.import_module(mod_name)
            for feld, bild in bilder:
                if list(getattr(mod, feld)) != elemente(bild):
                    melde("rot", "Prüfer", bild, mod_name, f"{feld} weicht von der Regelkarte ab")
        except Exception as e:  # noqa: BLE001
            melde("rot", "Prüfer", "-", mod_name, f"nicht lesbar: {e}")
        try:
            mod = importlib.import_module(mod_name)
            for name in ("SYSTEM", "SYSTEM_GRUPPE", "SYSTEM_MARKT") if mod_name == "chartpruefer" else ("SYSTEM",):
                bild = {"SYSTEM": "titel", "SYSTEM_GRUPPE": "gruppe", "SYSTEM_MARKT": "markt"}[name] \
                    if mod_name == "chartpruefer" else "setup"
                text = getattr(mod, name)
                namen = [s["name"] for s in SETUPS] if bild == "setup" else [k["name"] for k in KAESTEN[bild]] \
                    + ([z["name"] for z in ZEICHEN] if bild == "titel" else [])
                for n in namen:
                    if f"- {n}" not in text:
                        melde("rot", "Prüfer", bild, n, f"fehlt in der Anleitung {mod_name}.{name}")
        except Exception as e:  # noqa: BLE001
            melde("rot", "Prüfer", "-", mod_name, f"Anleitung nicht lesbar: {e}")
    # Setups: jede Reihe des Kartentischs steht auf der Karte, jede Karte hat ihre Messung
    try:
        import kartentisch
        auf_karte = {r for s in SETUPS for r in s["reihen"]}
        for r, name, _ in kartentisch.REIHEN:
            if r not in auf_karte:
                melde("rot", "Setup", "setup", name, f"Reihe {r} des Kartentischs steht nicht auf der Regelkarte")
        for r in auf_karte - {r for r, _, _ in kartentisch.REIHEN}:
            melde("rot", "Setup", "setup", r, "auf der Regelkarte, aber keine Reihe des Kartentischs")
    except Exception as e:  # noqa: BLE001
        melde("rot", "Setup", "setup", "kartentisch", f"nicht lesbar: {e}")
    for s in SETUPS:
        for m in s["messung"]:
            if not _gibt_es(m):
                melde("rot", "Setup", "setup", s["name"], f"Messfunktion {m} fehlt im Code")
        if s["stand"] == "fehlt":
            melde("rot", "Setup", "setup", s["name"], "nicht gebaut" + (f" – {s['luecke']}" if s.get("luecke") else ""),
                  alarm=False)
        elif s["stand"] == "teilweise":
            melde("gelb", "Setup", "setup", s["name"], "erst teilweise" + (f" – {s['luecke']}" if s.get("luecke") else ""),
                  alarm=False)
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
    rot = {x["name"] for x in m if x["bild"] == "setup" and x["ampel"] == "rot"}
    gelb = {x["name"] for x in m if x["bild"] == "setup" and x["ampel"] == "gelb"} - rot
    aus["setup"] = (len(SETUPS), len(rot), len(gelb))
    return aus
