"""Der Stab – MARAGA Investment (Konferenzraum, 09.11.2026; neuer Stab mit Missionen seit 13.11.2026).

Micky am 13.11.2026: „was der Stab da macht ist schwach … für das, was sie gerade liefern, brauchen wir sie nicht.“ Seitdem
arbeitet der Stab nicht mehr in Rollen nach Meistern, sondern in acht Missionen, jede mit einer einzigen Frage:
  1 Lage              Wirtschaftswetter, Markt (O'Neil), Leitfrage, Szenario A/B mit messbarem Auslöser
  2 Aufklärung        warum sich die Titel bewegen, über die heute entschieden wird (Web-Suche, Quelle mit Datum)
  3 Jäger             frühe Zeichen bei Titeln ohne Setup, beide Seiten: wer führt, wenn der Markt dreht, und wer
                      fällt als Nächster (bis 10 Anwärter, dazu jede Depotposition mit frühen Zeichen der Schwäche)
  4 Operationsplaner  höchstens 8 Aufträge aus den Akten (0 erlaubt); jede übrige Akte: beobachten oder verworfen
  5 Gegenspieler      greift jeden Auftrag an: hält, schwächt oder kippt
  6 Truppenführung    nur mit Depot: halten, Stopp nachziehen, verkaufen – nach der Phase
  7 Kriegsgeschichte  Ergebnisse früherer Aufträge (rechnet der Code): ein Fehler, eine Lehre
  8 Feldherr          der Tagesbefehl an Micky: Chancen zuerst mit dem Warum in Worten, Leitfrage, Anwärter, Depot
Der Code misst (Kreislauf und Zeichen je Titel aus kern/zeichen.py, Einstieg und Stopp der Setups, Ergebnisse) und
wacht: ein Auftrag nur auf eine Akte, nie bei roter Setup-Ampel, jede Akte eingeordnet, eine Chance nur aus einem
Auftrag, den der Gegenspieler nicht gekippt hat. Jede Meldung kommt über ein festes Formular (Werkzeug der
Schnittstelle), die Faktenwache prüft Ticker und Zahlen gegen die Daten. Konferenzen vor dem 13.11.2026 (sechs
Strategen) werden weiter angezeigt; ihr Code liegt in _to_delete.

Modell und Kosten: MODELL über die Anthropic-Schnittstelle, Kostenbuch je Monat in daten/konferenz/kosten.json; ab dem
Deckel (DECKEL_USD) ruft der Stab nicht mehr an bis zum Monatsende. Schlüssel: einstellungen/anthropic_schluessel.txt
(nicht in Git), in der App auf der Seite Konferenzraum eingetragen.
"""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

from dateien import json_lesen, json_schreiben

HIER = os.path.dirname(os.path.abspath(__file__))
SCHLUESSEL = os.path.join(HIER, "..", "einstellungen", "anthropic_schluessel.txt")
SPEICHER = os.path.join(HIER, "..", "daten", "konferenz")
MODELL = "claude-opus-5-5"                                             # alle Strategen auf Opus (Micky 10.11.2026)
PREIS_EIN, PREIS_AUS, PREIS_SUCHE = 4.0 / 1e6, 20.0 / 1e6, 0.01       # $ je Token bzw. je Suche
DECKEL_USD = 50.0                                                      # Monatsdeckel (Micky 11.11.2026: alle Strategen auf Opus, gemessen ~2,10 $ je Konferenz)
SUCHEN_NACHT = 10                                                      # Web-Suchen je Nacht (Fundamental-Analyst)
SUCHEN_FRAGE = 3
# Akten des Stabs (Micky 12.11.2026: „Klasse statt Masse – nur das Beste vom Besten im Konferenzraum“): immer das
# Depot; dazu nur einsatzbereite Setups – Setup grün und Kurs am Auslöser oder in der Kaufzone (long −5 bis +5 % zum
# Pivot, Short bis 5 % unter der Unterkante); Volltreffer auch bis 10 % über dem Pivot. Rang (Micky 12.11.2026):
# Zahlen in höchstens 7 Tagen nach hinten, dann Volltreffer, ★ in der Kaufzone, Geld in Richtung des Setups (Short
# gespiegelt: Abfluss zählt), RS (Short gespiegelt: schwächer zählt); die Watchlist gibt keinen Vorteil. Jede Reihe bekommt bis zu 2 Plätze vorab, damit Short und EP nie fehlen; höchstens
# AKTEN_MAX. Alles andere zeigt der Kartentisch; Watchlist-Titel ohne Akte stehen mit festen Ampeln in der Tafel.
AKTEN_MAX = 30
RANG_TEXT = ("Zahlen in höchstens 7 Tagen nach hinten, dann Volltreffer, ★ in der Kaufzone, Geld in Richtung des "
             "Setups (Short: Abfluss), RS-Rang (Short: der schwächere zuerst) – die Watchlist gibt keinen Vorteil")
AKTEN_JE_REIHE = 2
ZONE_LONG, ZONE_SHORT, ZONE_VOLLTREFFER = (-5.0, 5.0), (-5.0, 0.0), (-5.0, 10.0)

STRATEGEN = {                                    # Konferenzen vor dem 13.11.2026 (sechs Strategen)
    1: ("Stratege", "Tagesbefehl"),
    2: ("Strömungs-Analyst", "Wohin fließt das Geld?"),
    3: ("Fundamental-Analyst", "Tragen die Zahlen?"),
    4: ("Chart-Techniker", "Wo steht der Angriff?"),
    5: ("Risikomanager", "Was kann uns treffen?"),
    6: ("Gegenspieler", "Warum kann es scheitern?"),
}

HEUTE = lambda: datetime.now().strftime("%Y-%m-%d")                    # noqa: E731
TISCH_MAX_TAGE = 4                                                     # älterer Kartentisch: Stab tagt nicht

DIENSTANWEISUNG = """Du bist Mitglied im Stab von Micky, einem Swing-Trader, der long und short handelt. Du arbeitest im Invest Cockpit, seiner App. Dein Auftrag ist eine einzige Frage. Beantworte sie so, dass Micky danach weiß, was er tun soll.

UNSERE LEHRE – STÄRKE UND SCHWÄCHE
- Ein Titel ist in Balance (Seitwärtszone: Käufer und Verkäufer akzeptieren denselben Wert) oder im Ungleichgewicht (Trend: eine Seite überwiegt). Er verlässt die Balance, weil neue Information den Wert verändert (Ereignis) oder weil eine Seite erschöpft ist (das Angebot trocknet aus, dann reicht wenig Nachfrage).
- Stärke heißt: Die Nachfrage überwiegt, das Angebot weicht. Schwäche ist das Spiegelbild.
- Jeder Titel steht in einer Phase des Kreislaufs (Weinstein, Wyckoff): 1 Basis (Balance nach dem Abwärtstrend, Verkäufer erschöpft – wir suchen Zeichen, dass Stärke entsteht) · Übergang 1 → 2 Ausbruch aus der Balance (Base-Ausbruch, Sprung, Momentum-Ausbruch) · 2 Aufwärts (Fortsetzung nach einer Pause: Flagge, Base auf Base, Zahlen-Reaktion) · 3 Verteilung (Balance oben, Institutionen verkaufen – Zeichen, dass Schwäche entsteht; Ermüdung) · Übergang 3 → 4 und 1 → 4 Bruch nach unten (Bruch der Spanne) · 4 Abwärts (Fortsetzung nach einer schwachen Erholung: Bärenflagge). Das Geld läuft denselben Kreislauf in Sektor und Branche (erstarkend → führend → schwächelnd → zurückfallend), im Titel (Entsteht → Läuft → Ermüdet → Abfluss) und in der Wirtschaft (Wirtschaftswetter).
- Die App misst die Zeichen je Titel (Feld „kreislauf“): Phase und Wechsel („4 → 1“), Dow-Struktur der Schwungpunkte (höhere Hochs und Tiefs = aufwärts; der erste Schluss unter dem letzten höheren Tief ist das früheste Zeichen der Schwäche, das erste höhere Tief nach tieferen Hochs und Tiefs das früheste Zeichen der Stärke), Einquetschung (steigende Tiefs unter einer flachen Oberkante: die Käufer zahlen bei jedem Rücksetzer mehr, das Angebot oben wird aufgebraucht), Akkumulation/Distribution (Kauf- gegen Abgabetage mit Volumen, Pocket Pivot), Stärke in der Schwäche (hält oder steigt, während der Index fällt; RS-Linie am Hoch; am Indextief nahe dem eigenen Hoch) und das Spiegelbild, Reaktion auf Zahlen (gute Nachricht und der Kurs fällt = Schwäche, schlechte Nachricht und der Kurs hält = Stärke), Wanderung der Wertzone, Fehlausbruch (Schluss unter dem Tief des Ausbruchstags oder mehr als 3 % unter dem Pivot; knapp unter dem Pivot ist ein Rücktest).
- Was ein Ungleichgewicht ankündigt: Spannen werden enger, das Volumen trocknet aus, der Kurs drückt an die Oberkante, die Wertzone wandert, die RS-Linie steigt in der Base, ein Ereignis steht an. Was es bestätigt: Ausbruch mit Volumen über dem 50-Tage-Schnitt, der Kurs bleibt 2 bis 3 Tage außerhalb der Zone, der Rücktest hält.

BEGRIFFE DER APP
- Unsere Setups: {reihen}. Jeder Titel hat genau ein Setup (Feld „reihe“); „auch“ nennt weitere. „regeln_base“ und „regeln_momentum“ sind die Rohbefunde der Regeln dahinter.
- Stufen des Rückenwinds: {stufen}
- Geld-Ampel: grün, wenn zwei von drei Gruppen (Sektor, Branche, Thema) vorne liegen und keine schwächelt. Dreifacher Rückenwind: Stufe Entsteht oder Läuft UND Geld grün UND Zahlen grün. Volltreffer: dreifacher Rückenwind UND ein Long-Setup.
- Einstieg („pivot“) je Setup: Base-Ausbruch Pivot der Base · Flagge Oberkante · Momentum-Ausbruch Pivot der Konsolidierung · Sprung Hoch des Sprungtags · Zahlen-Reaktion AVWAP ab dem Reaktionstag · Ermüdung, Bärenflagge und Bruch der Spanne Unterkante. Kaufzone long bis +5 %, Short-Zone bis 5 % unter dem Einstieg. Stopp der App: 1,5 ATR vom Einstieg.
- Den Markt bestimmt eine Ampel nach O'Neil (Feld „markt“). Jede Akte trägt „feste_ampeln“ (Setup, Einstieg, Geld, Zahlen, Termin): Die rechnet der Code, sie sind gesetzt – du färbst sie nicht um.
- „datenstand“: Rechnen die Teile der App mit verschiedenen Handelstagen, ist das eine Gefahr ersten Ranges; nenne sie zuerst.

REGELN
1. Die App misst, du urteilst. Wiederhole keine Zahl ohne Deutung. Sag, was sie bedeutet und was daraus folgt.
2. Jeder Satz muss eine Entscheidung tragen (kaufen, warten, leerverkaufen, verkaufen, verwerfen). Sonst streiche ihn.
3. Chancen zuerst. Erkläre in Worten, warum ein Titel Stärke (oder beim Short Schwäche) zeigt.
4. Erfinde nichts. Was du nicht belegen kannst, kennzeichnest du als unbelegt. Quellen mit Datum. Rechnest du selbst, sage „gerechnet“ – eine Faktenwache prüft jede Zahl gegen die Daten.
5. Rot ist nie ein Auftrag. Weniger und dafür stark ist besser als viel und mittelmäßig.
6. Die Setups heißen bei unseren Namen. Die Meister nennst du nur als Quelle einer Regel – nie „Minervini grün“ oder „Kullamägi rot“.
7. Keine Positionsgrößen. Keine starren Kursziele, Micky lässt Gewinne laufen und zieht den Stopp nach.
8. Die Haltung der Lage gilt für den Markt, nicht für den Titel. Ein Titel mit Stärke in der Schwäche (Feld „staerke_in_der_schwaeche“) wird nie wegen des Marktes verworfen: Nenne ihn mit eigener Haltung – „klein tasten“, wenn sein Setup grün ist und der Ausbruch mit Volumen kommt, sonst „vormerken“ mit dem Auslöser Follow-Through-Day oder Ausbruch. Nenne das Risiko des Marktes als Gegenzeugen (drei von vier Titeln folgen dem Markt).
Heute ist der {heute}; Termine davor sind vergangen. Schreibe Deutsch, klar und knapp, sprich Micky mit „du“ an. Eine kurze Kriegsanalogie ist erlaubt, wenn sie die Lage schneller erklärt. Gib deine Antwort ausschließlich über das Werkzeug ab."""

# Missionen (Micky 13.11.2026: „was der Stab da macht ist schwach“): je Mission eine Frage, ihr Material, ihre
# Lehrstelle. Die Meister sind keine Rollen mehr – ihre Regeln stehen als Lehrstellen bei der Mission, die sie braucht.
MISSIONEN = {
    1: ("Lage", "Angriff oder Abwarten?"),
    2: ("Aufklärung", "Warum bewegt er sich?"),
    3: ("Jäger", "Wo entsteht Stärke – oder Schwäche –, bevor das Setup steht?"),
    4: ("Operationsplaner", "Was tun wir heute konkret?"),
    5: ("Gegenspieler", "Warum scheitert genau dieser Plan?"),
    6: ("Truppenführung", "Was tun wir mit den Positionen?"),
    7: ("Kriegsgeschichte", "Was lief, was nicht?"),
    8: ("Feldherr", "Der Tagesbefehl"),
}
AUFTRAG_MISSION = {
    1: "Beurteile die Lage in drei Schritten. (1) Wirtschaftswetter: In welchem Quad stehen wir, kippt er, und welche "
       "Sektoren trägt das? (2) Markt: Was sagt O'Neil, was sagen Pendel und Breite, wo widersprechen sie sich? (3) "
       "Benenne die eine Frage, die heute über Angriff oder Abwarten entscheidet, und schreibe zwei Szenarien. Jedes hat "
       "einen messbaren Auslöser (Kurs, Volumen, Tag), eine Haltung (angreifen, klein tasten, abwarten, verteidigen) und "
       "den Satz, was Micky dann tut.",
    2: "Finde für jeden Titel heraus, warum er sich bewegt. Suche den Auslöser: Zahlen, Ausblick, Auftrag, Produkt, "
       "Übernahme, Analyst, Branchennachricht, Makro, oder nichts Erkennbares. Entscheide, ob der Auslöser tragfähig ist "
       "(er verändert die Gewinne der nächsten Quartale) oder Rauschen. Achte auf das stärkste Zeichen: Wie reagiert der "
       "Kurs auf die Nachricht? Gute Nachricht und der Kurs steigt und hält = Stärke. Schlechte Nachricht und der Kurs "
       "hält = noch mehr Stärke. Gute Nachricht und der Kurs fällt = Schwäche. Nenne die Quelle mit Datum. Findest du "
       "nichts, schreibe „kein Auslöser gefunden“.",
    3: "Wo entsteht Stärke, bevor das Setup steht – wer führt, wenn der Markt dreht? Und wo entsteht Schwäche – wer "
       "fällt als Nächster? Die Liste enthält Titel ohne einsatzbereites Setup mit frühen Zeichen (Feld „seite“: long = "
       "Stärke, short = Schwäche; Feld „fruehe_zeichen“: Stärke bzw. Schwäche gegen den Markt, Wechsel der Phase, "
       "Spring/Upthrust, Einquetschung, Akkumulation/Distribution, Reaktion auf Zahlen). Titel mit „im_depot“ sind "
       "unsere eigenen Positionen mit frühen Zeichen der Schwäche – nenne jeden davon. Wähle sonst bis zu 10 Titel "
       "(beide Seiten) und ordne sie. Erkläre für jeden in Worten, warum er Stärke bzw. Schwäche zeigt: Wer kauft oder "
       "verkauft hier, und warum gerade jetzt? Nenne die Phase im Kreislauf und das Zeichen, auf das wir warten (z. B. "
       "Ausbruch über die Oberkante mit Volumen, erstes höheres Tief, Bruch der Spanne). Nenne, was die These widerlegt. "
       "Bevorzuge Titel, deren Branche ebenfalls Geld anzieht (Short: Geld abzieht).",
    4: "Was tun wir heute konkret? Bilde höchstens 8 Aufträge aus den Stärksten. Kein Auftrag ist erlaubt, wenn nichts "
       "taugt. Für jeden Auftrag: die These in einem Satz (warum Stärke, warum jetzt), die Phase im Kreislauf, der "
       "Auslöser (Kurs, Volumen, Kerze; beim Einstieg im Stundenchart die Kerze), Einstieg und Stopp der App (weichst du "
       "ab, begründe es), in welchem Szenario der Lage er gilt, und wann er ungültig ist. Ordne dann jede übrige Akte ein: "
       "„beobachten“ mit dem Zeichen, auf das wir warten, oder „verworfen“ mit einem Grund in einer Zeile. Ein Auftrag "
       "geht nur auf eine Akte (einsatzbereites Setup).",
    5: "Greife jeden Auftrag an. Suche den stärksten belegten Grund, warum genau dieser Plan scheitert: falsche Phase, "
       "Auslöser ist Rauschen, Geld fließt aus der Branche, Zahlen stehen an, Struktur bricht. Kein allgemeiner Einwand "
       "(„der Markt ist schwach“), sondern das, was diesen Titel trifft. Urteile: hält, schwächt oder kippt.",
    6: "Für jede Position: halten, Stopp nachziehen (auf welche Linie und warum), teilweise oder ganz verkaufen. "
       "Grundlage ist die Phase. Solange Phase 2 und keine Zeichen der Ermüdung erkennbar sind, laufen lassen. Zeichen des "
       "Wechsels (Klimax, Schluss unter dem letzten höheren Tief, schwere Abgabetage) bedeuten handeln.",
    7: "Was lief, was nicht? Benenne einen Fehler des Stabs mit Namen und Titel und eine Lehre für heute. Kein "
       "Selbstlob, keine Ausreden. Die Ergebnisse hat der Code gerechnet (Auslöser erreicht, Bewegung danach, Stopp "
       "erreicht).",
    8: "Entscheide. Übernimm die Aufträge, die den Gegenspieler überstehen. Ein gekippter Auftrag fällt weg, ein "
       "geschwächter bleibt mit dem Einwand als „Achte auf“. Schreibe den Befehl an Micky: Anrede („Hey Micky, …“), die "
       "stärksten Chancen zuerst mit dem Warum in Worten (z. B. „der Gesamtmarkt schwächelt, aber dieser Titel steigt – "
       "ein Zeichen von Stärke“), dann was zu tun ist, je Chance höchstens eine Zeile „Achte auf“. Danach Leitfrage mit "
       "Szenario A/B, Anwärter, Depot, Lehre aus gestern. Gibt es keine Chance, sage das in der Anrede klar – und was "
       "wir stattdessen beobachten.",
}
LEHRSTELLE = {
    1: "Lehrstellen: O'Neil – drei von vier Titeln folgen dem Markt; eine Korrektur endet erst mit einem "
       "Follow-Through-Day ab dem 4. Tag des Erholungsversuchs, 5 bis 6 Distributionstage in 5 Wochen kippen einen "
       "Aufwärtstrend. Murphy – Zinsen, Dollar, Rohstoffe und Aktien hängen zusammen; das Geld rotiert im "
       "Konjunkturzyklus durch die Sektoren. Druckenmiller – Liquidität bewegt die Märkte; der Markt schaut 12 bis 24 "
       "Monate voraus. Livermore – erst der Markt, dann die Gruppe, dann der Titel; ist die Lage unklar, wird gewartet.",
    2: "Lehrstellen: O'Neil (N in CAN SLIM) – etwas Neues treibt große Gewinner: Produkt, Management, Branchenwandel. "
       "Bonde – ein Episodic Pivot braucht Vernachlässigung, einen Auslöser, der die Sicht der Wall Street auf das "
       "Geschäft ändert, und eine Lücke mit gewaltigem Volumen; ein echter fällt nicht unter das Niveau vor der Lücke. "
       "Drift nach den Zahlen (Ball/Brown, Bernard/Thomas) – eine klare Reaktion läuft oft Wochen in dieselbe Richtung.",
    3: "Lehrstelle: O'Neil – die Führer des nächsten Aufschwungs zeigen sich in der Korrektur. Sie fallen am wenigsten "
       "und brechen nach dem Follow-Through-Day als Erste aus. Livermore – laufen die Schwestern derselben Gruppe mit, "
       "ist die Bewegung echt. Wyckoff – ein Unterschreiten des Tiefs, das sofort zurückgekauft wird (Spring), zeigt "
       "erschöpfte Verkäufer.",
    4: "Lehrstellen: Minervini – gekauft wird am Pivot, nicht mehr als 5 % darüber; die Rücksetzer werden enger, das "
       "Volumen trocknet aus. Livermore – nicht vorwegnehmen, erst der Durchbruch zählt; läuft der Kurs danach nicht "
       "prompt, ist das ein Gefahrenzeichen. Dalton – ein Ausbruch ist angenommen, wenn der Kurs Zeit und Volumen "
       "außerhalb der Zone aufbaut; kehrt er schnell zurück, ist die Auktion gescheitert. Shannon – über steigendem "
       "AVWAP haben die Käufer die Kontrolle. Morales/Kacher (Short) – Short in die Erholung an die 50- oder "
       "20-Tage-Linie, nicht am Tief; Squeeze-Gefahr bei starken Erholungen.",
    5: "Lehrstellen: Minervini – Kontraktionen nicht eng, Volumen nicht ausgetrocknet, über der Kaufzone. O'Neil – "
       "Gruppe schwach, Zahlen tragen nicht. Dalton – Ausbruch ohne Annahme, Rückkehr in die Balance. Bonde – Rückfall "
       "unter das Niveau vor der Lücke. Livermore – Ein-Tages-Umkehr, keine prompte Nachfolge.",
    6: "Lehrstellen: Minervini – Stopp auf Einstand, sobald der Gewinn ein Mehrfaches des Risikos erreicht; in die "
       "Stärke teilweise verkaufen. Livermore – das große Geld kommt vom Sitzenbleiben im großen Trend; nie einen "
       "Verlierer verbilligen. Weinstein – solange Phase 2, laufen lassen; der Bruch der 30-Wochen-Linie beendet sie.",
    7: "Lehrstelle: Livermore – Fehler sind die Lehrmeister; der Spekulant prüft jeden Fehler, damit er ihn nicht "
       "wiederholt.",
    8: "Lehrstellen: Livermore – erst tasten, dann nachlegen; nicht jeden Tag handeln. Druckenmiller – stimmen "
       "Überzeugung, Strömung und Markt überein, die Kraft auf die besten Ziele bündeln; ist die Lage unklar, klein "
       "bleiben.",
}
# Aufklärung (Micky 13.11.2026): Titel, über die heute entschieden wird, plus immer das Depot. Erst 20 (12 Akten,
# 8 Anwärter); nach der Probekonferenz (2,94 $, davon geschätzt rund 2,50 $ für die Web-Suchen) auf 10 gesenkt:
# 6 Akten, 4 Anwärter; freie Plätze einer Gruppe füllt die andere.
AUFKLAERUNG_MAX = 10
AUFKLAERUNG_AKTEN, AUFKLAERUNG_ANWAERTER = 6, 4
ANWAERTER_MAX = 30                     # Micky 13.11.2026: frühe Zeichen, höchstens 30 an den Jäger …
ANWAERTER_LONG, ANWAERTER_SHORT = 20, 10   # … 20 mit frühen Zeichen der Stärke, 10 mit frühen Zeichen der Schwäche
#                                        (Prüf-Agent 13.11.2026: die Short-Seite fehlte); dazu Warnungen für das Depot
AUFTRAEGE_MAX = 8                     # Micky 13.11.2026: an starken Tagen (Follow-Through-Day) mehr als 5 gute Chancen
SUCHEN_AUFKLAERUNG = 10                # je Titel eine Suche; für jede Position im Depot eine mehr

_TXT = lambda d: {"type": "string", "description": d}            # noqa: E731
_HALT = {"type": "string", "enum": ["angreifen", "klein tasten", "abwarten", "verteidigen"]}
SZENARIO = {"type": "object", "properties": {"ausloeser": _TXT("messbar: Kurs, Volumen, Tag"), "haltung": _HALT,
                                             "tun": _TXT("was Micky dann tut, ein Satz")},
            "required": ["ausloeser", "haltung", "tun"]}
F_LAGE = {"type": "object", "properties": {
    "wetter": _TXT("2 Sätze: Quad, kippt er, welche Sektoren trägt das"),
    "markt": _TXT("2 Sätze: O'Neil, Pendel, Breite, wo sie sich widersprechen"),
    "leitfrage": _TXT("die eine Frage, die heute über Angriff oder Abwarten entscheidet"),
    "szenario_a": SZENARIO, "szenario_b": SZENARIO},
    "required": ["wetter", "markt", "leitfrage", "szenario_a", "szenario_b"]}
F_AUFKL = {"type": "object", "properties": {"titel": {"type": "array", "items": {"type": "object", "properties": {
    "titel": _TXT("Ticker"), "ausloeser": _TXT("der Auslöser in einem Satz oder „kein Auslöser gefunden“"),
    "art": {"type": "string", "enum": ["Zahlen", "Ausblick", "Auftrag", "Produkt", "Übernahme", "Analyst", "Branche",
                                       "Makro", "nichts erkennbar"]},
    "tragfaehig": {"type": "string", "enum": ["ja", "nein", "unklar"]},
    "reaktion": {"type": "string", "enum": ["stärke", "schwäche", "neutral"]},
    "quelle": _TXT("Name oder URL der Quelle, leer wenn keine"), "datum": _TXT("Datum der Quelle, leer wenn keine")},
    "required": ["titel", "ausloeser", "art", "tragfaehig", "reaktion"]}}}, "required": ["titel"]}
F_JAEGER = {"type": "object", "properties": {"anwaerter": {"type": "array", "items": {"type": "object", "properties": {
    "rang": {"type": "integer"}, "titel": _TXT("Ticker"), "seite": {"type": "string", "enum": ["long", "short"]},
    "these": _TXT("wer kauft (short: verkauft) hier und warum gerade jetzt"),
    "phase": _TXT("Phase im Kreislauf, z. B. „4 → 1“"), "warten_auf": _TXT("das Zeichen, auf das wir warten"),
    "widerlegt_wenn": _TXT("was die These widerlegt")},
    "required": ["rang", "titel", "seite", "these", "phase", "warten_auf", "widerlegt_wenn"]},
    "description": "bis zu 10 (beide Seiten), der deutlichste zuerst, dazu jeder Titel „im_depot“; leer, wenn keiner"}},
    "required": ["anwaerter"]}
F_PLAN = {"type": "object", "properties": {
    "auftraege": {"type": "array", "description": "höchstens 8, leer erlaubt", "items": {"type": "object", "properties": {
        "titel": _TXT("Ticker einer Akte"), "seite": {"type": "string", "enum": ["long", "short"]},
        "these": _TXT("ein Satz: warum Stärke (Short: Schwäche), warum jetzt"), "phase": _TXT("Phase im Kreislauf"),
        "ausloeser": _TXT("Kurs, Volumen, Kerze"), "einstieg": {"type": ["number", "null"]},
        "stopp": {"type": ["number", "null"]}, "abweichung": _TXT("Grund, wenn Einstieg/Stopp von der App abweichen, sonst leer"),
        "szenario": {"type": "string", "enum": ["A", "B", "beide"]}, "ungueltig_wenn": _TXT("wann der Auftrag ungültig ist")},
        "required": ["titel", "seite", "these", "phase", "ausloeser", "einstieg", "stopp", "szenario", "ungueltig_wenn"]}},
    "beobachten": {"type": "array", "items": {"type": "object", "properties": {
        "titel": _TXT("Ticker"), "warten_auf": _TXT("das Zeichen, auf das wir warten")}, "required": ["titel", "warten_auf"]}},
    "verworfen": {"type": "array", "items": {"type": "object", "properties": {
        "titel": _TXT("Ticker"), "grund": _TXT("ein Grund in einer Zeile")}, "required": ["titel", "grund"]}}},
    "required": ["auftraege", "beobachten", "verworfen"]}
F_GEGEN = {"type": "object", "properties": {"einwaende": {"type": "array", "items": {"type": "object", "properties": {
    "titel": _TXT("Ticker des Auftrags"), "einwand": _TXT("der stärkste Grund, warum genau dieser Plan scheitert"),
    "beleg": _TXT("Zahl oder Tatsache aus den Daten"), "urteil": {"type": "string", "enum": ["hält", "schwächt", "kippt"]}},
    "required": ["titel", "einwand", "beleg", "urteil"]}}}, "required": ["einwaende"]}
F_TRUPPE = {"type": "object", "properties": {"positionen": {"type": "array", "items": {"type": "object", "properties": {
    "titel": _TXT("Ticker"), "anweisung": {"type": "string", "enum": ["halten", "Stopp nachziehen", "teilweise verkaufen",
                                                                      "ganz verkaufen"]},
    "linie": _TXT("die Linie des Stopps, wenn nachgezogen wird, sonst leer"), "grund": _TXT("ein Satz")},
    "required": ["titel", "anweisung", "grund"]}}}, "required": ["positionen"]}
F_GESCHICHTE = {"type": "object", "properties": {"bilanz": _TXT("ein Satz"), "fehler_des_stabs": _TXT("ein Fehler mit Mission und Titel"),
                                                 "lehre": _TXT("eine Lehre für heute")},
                "required": ["bilanz", "fehler_des_stabs", "lehre"]}
F_BEFEHL = {"type": "object", "properties": {
    "anrede": _TXT("„Hey Micky, …“ – ein bis zwei Sätze: die Chancen des Tages oder klar, dass es keine gibt"),
    "haltung": _HALT,
    "chancen": {"type": "array", "description": "die Aufträge, die den Gegenspieler überstehen, die stärkste zuerst",
                "items": {"type": "object", "properties": {
                    "titel": _TXT("Ticker"), "seite": {"type": "string", "enum": ["long", "short"]},
                    "warum": _TXT("warum Stärke (Short: Schwäche) – in Worten, 1 bis 2 Sätze"),
                    "tun": _TXT("was zu tun ist: Auslöser, Einstieg, Stopp"), "achte_auf": _TXT("höchstens eine Zeile"),
                    "phase": _TXT("Phase im Kreislauf in Worten, z. B. „Phase 1 → kurz vor dem Ausbruch“")},
                    "required": ["titel", "seite", "warum", "tun", "achte_auf", "phase"]}},
    "leitfrage": _TXT("die Leitfrage der Lage"),
    "szenarien": {"type": "array", "items": {"type": "object", "properties": {
        "name": {"type": "string", "enum": ["A", "B"]}, **SZENARIO["properties"]},
        "required": ["name", "ausloeser", "haltung", "tun"]}},
    "anwaerter": {"type": "array", "items": {"type": "object", "properties": {
        "titel": _TXT("Ticker"), "warum": _TXT("ein Satz"), "warten_auf": _TXT("das Zeichen")},
        "required": ["titel", "warum", "warten_auf"]}},
    "depot": {"type": "array", "items": {"type": "object", "properties": {
        "titel": _TXT("Ticker"), "anweisung": _TXT("ein Satz")}, "required": ["titel", "anweisung"]}},
    "lehre": _TXT("die Lehre aus gestern, ein Satz")},
    "required": ["anrede", "haltung", "chancen", "leitfrage", "szenarien", "anwaerter", "depot", "lehre"]}


QUELLEN = {
    "Minervini": "Trade Like a Stock Market Wizard; Think & Trade Like a Champion",
    "O'Neil": "How to Make Money in Stocks (CAN SLIM)",
    "Weinstein": "Secrets for Profiting in Bull and Bear Markets",
    "Kullamägi": "qullamaggie.com, seine Streams",
    "Murphy": "Intermarket Analysis",
    "Bonde": "stockbee.blogspot.com (Episodic Pivots, Neglect, Delayed Reaction)",
    "Dalton / Steidlmayer": "Mind over Markets; Steidlmayer on Markets (Market Profile)",
    "Shannon": "Maximum Trading Gains with Anchored VWAP; alphatrends.net/anchored-vwap",
    "Morales / Kacher": "Short-Selling with the O'Neil Disciples; Trade Like an O'Neil Disciple; "
                        "virtueofselfishinvesting.com (Six Essential Rules of Short-Selling)",
    "Livermore": "How to Trade in Stocks (1940: Pivotal Points, Schwesteraktien, Gefahrenzeichen, Zeit); Reminiscences "
                 "of a Stock Operator (Lefèvre, 1923)",
    "Drift nach den Zahlen": "Ball und Brown (1968), Bernard und Thomas (1989): Post-Earnings-Announcement Drift",
    "Druckenmiller": "Reden und Interviews (Liquidität, 18 bis 24 Monate voraus, Bündeln bei Überzeugung)",
}

HALTUNGEN = ("angreifen", "klein tasten", "abwarten", "verteidigen")
BEFEHL_TEILE = (("volltreffer", "Volltreffer · dreifacher Rückenwind und Setup am Auslöser"),
                ("long", "Angriffsziele long"), ("short", "Ziele short"), ("gefahren", "Gefahren"))


def dienstanweisung():
    import kartentisch
    import rueckenwind_seite
    reihen = " · ".join(f"{n}: {r}" for _, n, r in kartentisch.REIHEN)
    stufen = " · ".join(f"{k}: {v}" for k, v in rueckenwind_seite.STUFE_TEXT.items() if k)
    return DIENSTANWEISUNG.format(reihen=reihen, stufen=stufen, heute=HEUTE())


# ── Schlüssel, Kosten ──

def schluessel():
    try:
        return open(SCHLUESSEL, encoding="utf-8").read().strip() or None
    except OSError:
        return None


def schluessel_speichern(wert):
    os.makedirs(os.path.dirname(SCHLUESSEL), exist_ok=True)
    with open(SCHLUESSEL, "w", encoding="utf-8") as f:
        f.write(wert.strip())
    os.chmod(SCHLUESSEL, 0o600)


def _pfad(name):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, name)


def kosten():
    """Kostenbuch des laufenden Monats: {"usd", "aufrufe", "suchen", "ein", "aus"}."""
    return (json_lesen(_pfad("kosten.json"), {}) or {}).get(f"{datetime.now():%Y-%m}",
                                                             {"usd": 0.0, "aufrufe": 0, "suchen": 0, "ein": 0, "aus": 0})


def _buchen(usage):
    buch = json_lesen(_pfad("kosten.json"), {}) or {}
    m = buch.setdefault(f"{datetime.now():%Y-%m}", {"usd": 0.0, "aufrufe": 0, "suchen": 0, "ein": 0, "aus": 0})
    ein = (usage.get("input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0) * 1.25 \
        + (usage.get("cache_read_input_tokens") or 0) * 0.05
    aus = usage.get("output_tokens") or 0
    suchen = ((usage.get("server_tool_use") or {}).get("web_search_requests") or 0)
    usd = ein * PREIS_EIN + aus * PREIS_AUS + suchen * PREIS_SUCHE
    m["usd"] = round(m["usd"] + usd, 4)
    m["aufrufe"] += 1
    m["suchen"] += suchen
    m["ein"] += int(ein)
    m["aus"] += aus
    json_schreiben(_pfad("kosten.json"), buch)
    return usd


class Deckel(Exception):
    pass


def _rufen(system, nachrichten, max_tokens, werkzeuge=None, wahl=None):
    """Ein Aufruf an Claude (mit Fortsetzung bei pause_turn); gibt die Inhaltsblöcke zurück. Bricht vor dem Aufruf ab,
    wenn kein Schlüssel da ist oder der Monatsdeckel erreicht ist."""
    k = schluessel()
    if not k:
        raise RuntimeError("kein API-Schlüssel eingetragen (Seite Konferenzraum)")
    if kosten()["usd"] >= DECKEL_USD:
        raise Deckel(f"Monatsdeckel von {DECKEL_USD:.0f} $ erreicht – der Stab ruht bis zum Monatsende")
    bloecke = []
    for _ in range(4):
        daten = {"model": MODELL, "max_tokens": max_tokens, "system": system, "messages": nachrichten}
        if werkzeuge:
            daten["tools"] = werkzeuge
        if wahl:
            daten["tool_choice"] = wahl
        antwort = _senden(k, daten)
        _buchen(antwort.get("usage") or {})
        bloecke += antwort.get("content", [])
        _LETZTER["stop"] = antwort.get("stop_reason")
        if antwort.get("stop_reason") != "pause_turn":
            break
        nachrichten = nachrichten[:1] + [{"role": "assistant", "content": antwort["content"]}]
    return bloecke


def _anfrage(system, inhalt, max_tokens=3000, suchen=0):
    """Freier Text als Antwort (Probe, Stab fragen, Notizen der Web-Suche)."""
    werkzeuge = [{"type": "web_search_20250305", "name": "web_search", "max_uses": suchen}] if suchen else None
    bloecke = _rufen(system, [{"role": "user", "content": inhalt}], max_tokens, werkzeuge)
    _LETZTER["bloecke"] = [b.get("type") for b in bloecke]               # zur Fehlersuche (Stab fragen, 11.11.)
    return "".join(b.get("text", "") for b in bloecke if b.get("type") == "text").strip()


class Unlesbar(Exception):
    def __init__(self, text, roh):
        super().__init__(text)
        self.roh = roh


_LETZTER = {"stop": None}


def _ordnen(obj, schema):
    """Felder, die das Modell als JSON-Text statt als Liste/Objekt schickt, in Listen/Objekte wandeln (rekursiv)."""
    if not isinstance(obj, dict):
        return obj
    for key, sub in (schema.get("properties") or {}).items():
        v = obj.get(key)
        if isinstance(v, str) and sub.get("type") in ("array", "object"):
            try:
                v = json.loads(v)
            except ValueError:
                continue
        if sub.get("type") == "array" and isinstance(v, list) and (sub.get("items") or {}).get("type") == "object":
            neu = []
            for x in v:
                if isinstance(x, str):
                    try:
                        x = json.loads(x)
                    except ValueError:
                        continue
                if isinstance(x, dict):
                    neu.append(_ordnen(x, sub["items"]))
            v = neu
        if v is not None:
            obj[key] = v
    return obj


def _gueltig(obj, schema):
    """Alle Pflichtfelder da und vom richtigen Typ (Text nicht leer, Liste als Liste)."""
    if not isinstance(obj, dict):
        return False
    for key in schema.get("required", []):
        typ = ((schema.get("properties") or {}).get(key) or {}).get("type")
        v = obj.get(key)
        if v is None or (typ == "string" and not str(v).strip()) or (typ == "array" and not isinstance(v, list)):
            return False
    return True


def _formular(system, inhalt, name, schema, max_tokens=8000):
    """Antwort über ein festes Formular (Werkzeug der Schnittstelle): die Schnittstelle gibt ein fertiges Objekt zurück,
    kein JSON-Text, der an Anführungszeichen zerbrechen kann. Opus 5.5 erlaubt kein erzwungenes Werkzeug
    (tool_choice „tool“/„any“ → Fehler 400, Nachtlauf 11.11.2026) – deshalb „auto“ mit klarer Anweisung; schreibt das
    Modell trotzdem Text, wird ein JSON-Objekt darin gelesen. Jede Meldung wird geprüft (alle Pflichtfelder, Listen als
    Listen); unvollständig – etwa am Token-Limit abgeschnitten (11.11.: leere Meldung des Risikomanagers, Tagesbefehl
    nur mit Lage) – gibt es einen zweiten Versuch mit doppeltem Limit, sonst Unlesbar mit der Rohantwort."""
    werkzeug = [{"name": name, "description": "Meldung an den Stab abgeben – der einzige Weg, die Meldung abzugeben",
                 "input_schema": schema}]
    auftrag = (f"{inhalt}\n\nGib deine Antwort ausschließlich über das Werkzeug „{name}“ ab – genau ein Aufruf, "
               "alle Pflichtfelder ausgefüllt, Listen als echte Listen, kein Text davor oder danach.")
    roh = ""
    for versuch in range(2):
        bloecke = _rufen(system, [{"role": "user", "content": auftrag}], max_tokens, werkzeug, {"type": "auto"})
        kandidaten = [b["input"] for b in bloecke if b.get("type") == "tool_use" and isinstance(b.get("input"), dict)]
        text = "".join(b.get("text", "") for b in bloecke if b.get("type") == "text")
        a, e = text.find("{"), text.rfind("}")
        if a >= 0 and e > a:
            try:
                kandidaten.append(json.loads(text[a:e + 1]))
            except ValueError:
                pass
        for obj in kandidaten:
            obj = _ordnen(obj, schema)
            if _gueltig(obj, schema):
                return obj
        roh = f"stop_reason={_LETZTER['stop']} · " + json.dumps(bloecke, ensure_ascii=False)[:600]
        if _LETZTER["stop"] == "max_tokens":
            max_tokens *= 2
        auftrag = (f"{inhalt}\n\nWICHTIG: Deine letzte Antwort war unvollständig oder kam nicht über das Werkzeug. "
                   f"Rufe jetzt das Werkzeug „{name}“ auf und fülle alle Pflichtfelder aus ({', '.join(schema.get('required', []))}); "
                   "fasse dich kürzer. Kein freier Text.")
    raise Unlesbar("Antwort ohne vollständiges Formular", roh)


def _senden(k, daten):
    roh = json.dumps(daten).encode("utf-8")
    for versuch in range(3):
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=roh, method="POST",
                                     headers={"x-api-key": k, "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503, 504, 529) and versuch < 2:   # überlastet, Rate-Limit oder kurz nicht
                # erreichbar (13.11.2026: 503 „credential validation failed“ mitten in der Konferenz): warten, noch einmal
                time.sleep(20 * (versuch + 1))
                continue
            raise RuntimeError(f"Anthropic antwortet {e.code}: {text}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if versuch < 2:
                time.sleep(10)
                continue
            raise RuntimeError(f"Anthropic nicht erreichbar: {getattr(e, 'reason', e)}") from None
    raise RuntimeError("Anthropic nicht erreichbar")


def probe():
    """Kurzer Test nach dem Eintragen des Schlüssels: Text und Meldeformular. (True, Text) oder (False, Grund). Kostet
    weniger als 1 Cent."""
    try:
        antwort = _anfrage("Antworte nur mit OK.", "Verbindungstest", 5)
    except Exception as e:  # noqa: BLE001
        return False, str(e)
    try:                                         # auch das Formular prüfen – daran scheiterte der Nachtlauf am 11.11.
        f = _formular("Du testest eine Verbindung.", "Melde den Status ok.", "melden",
                      {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}, 200)
    except Exception as e:  # noqa: BLE001
        return False, f"Text geht ({antwort[:10] or 'OK'}), aber das Meldeformular nicht: {e}"
    return True, f"Verbindung steht – {MODELL} antwortet, Meldeformular funktioniert ({f.get('status', 'ok')})"


# ── Lagebild aus den Daten der App ──

def _zahl(x, n=2):
    try:
        return round(float(x), n)
    except (TypeError, ValueError):
        return None


def _termin_ok(text_oder_datum):
    """Vergangene Termine aussortieren (die alte Liste trug Termine aus 2018/2019 und „in -1 Tagen“)."""
    if not text_oder_datum:
        return None
    s_ = str(text_oder_datum)
    if s_.startswith("in -"):
        return None
    try:
        import pandas as pd
        d = pd.to_datetime(s_[:10], errors="coerce")
        if not pd.isna(d) and d.strftime("%Y-%m-%d") < HEUTE():
            return None
    except Exception:  # noqa: BLE001
        pass
    return s_


def termin_datum(zahlen, kachel, heute=None):
    """Nächster Zahlentermin als ISO-Datum oder None: aus den Zahlen des Rückenwinds, sonst aus der Kachel „Nächste
    Zahlen“ (deren Wert lautet „in n Tagen“ vom Tag der Kartentisch-Rechnung – das Datum steht im Text, „Do 13.11.2026“).
    Vergangene Termine zählen nicht (12.11.2026: vorher las die Termin-Ampel aus „in 3 Tagen“ kein Datum → grau)."""
    import re
    heute = heute or HEUTE()
    t_ = (zahlen or {}).get("termin")
    if t_ and str(t_)[:10] < heute:                 # Rückenwind behält auch den gestrigen Termin: dann die Kachel
        t_ = None                                   # (Prüf-Agent 12.11.2026)
    if not t_ and kachel:
        teile = [kachel.get("wert"), kachel.get("text")] if isinstance(kachel, dict) else list(kachel)[1:3]
        for teil in teile:
            m_ = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", str(teil or ""))
            if m_:
                t_ = f"{m_.group(3)}-{m_.group(2)}-{m_.group(1)}"
                break
    d = str(t_)[:10] if t_ and re.match(r"\d{4}-\d{2}-\d{2}", str(t_)) else None
    return d if d and d >= heute else None                       # vergangene Termine zählen nicht


def termin_tage(zahlen, kachel, heute=None):
    """Tage bis zu den nächsten Zahlen (0 = heute) oder None."""
    import pandas as pd
    d = termin_datum(zahlen, kachel, heute)
    return None if d is None else (pd.Timestamp(d) - pd.Timestamp(heute or HEUTE())).days


_tage = termin_tage


def _seite(x):
    """Long oder short aus der Reihe des Setups (10.11.2026) – nicht aus der Weinstein-Phase, die nur Zeichen ist."""
    try:
        import lagekarte
        return lagekarte.richtung(x) or "offen"
    except Exception:  # noqa: BLE001
        return "offen"


def _runden(x, n=2):
    """Zahlen in verschachtelten Daten runden (spart Token, liest sich wie auf dem Bildschirm)."""
    if isinstance(x, float):
        return round(x, n)
    if isinstance(x, dict):
        return {k: _runden(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_runden(v, n) for v in x]
    return x


def avwaps(df, zahltag=None, zone_start=None):
    """Anchored VWAP nach Brian Shannon und das verankerte Volumenprofil für die Akte des Stabs – dieselben Anker wie
    Chart und Lagekarte (kern/avwap.py, 13.11.2026: nie aus dem Kalender): Hoch, von dem der Fall ausging; Tief, von
    dem die Bewegung ausging; Ereignis (Zahlen ab 3 % oder Lücke ab 4 % mit Volumen ×2). Je Anker: Datum, Wert, Abstand
    des Kurses in %, Richtung (über 5 Tage); „pinch“, wenn Hoch- und Tief-AVWAP weniger als 3 % auseinander liegen.
    Dazu „volumen“: akzeptierter Wert seit Zone bzw. Ereignis, Mauer (Knoten seit dem Hoch über dem Kurs) und Stütze
    (Knoten seit dem Tief unter dem Kurs)."""
    import pandas as pd
    import avwap
    import volumenprofil
    a = avwap.anker(df, zahltag)
    if not a:
        return None
    kurs = float(df["Close"].iloc[-1])
    namen = {"hoch": "hoch", "tief": "tief_der_bewegung", "ereignis": "ereignis"}
    aus = {}
    for k, tag in a.items():
        av = avwap.reihe(df, tag)
        if len(av) < 6:                                  # Anker erst wenige Tage alt: noch keine Aussage
            aus[namen[k]] = {"ab": f"{tag:%Y-%m-%d}", "hinweis": "Anker erst wenige Tage alt – Kurs steht am "
                             + {"hoch": "Hoch", "tief": "Tief", "ereignis": "Ereignis"}[k]}
            continue
        w, vor = float(av.iloc[-1]), float(av.iloc[-6])
        r = (w / vor - 1) * 100 if vor else 0
        aus[namen[k]] = {"ab": f"{tag:%Y-%m-%d}", "wert": _zahl(w), "kurs_abstand_pct": _zahl((kurs / w - 1) * 100, 1),
                         "richtung": "steigt" if r > 0.3 else "fällt" if r < -0.3 else "flach"}
    h, t = aus.get("hoch"), aus.get("tief_der_bewegung")
    if h and t and h.get("wert") and t.get("wert"):
        aus["pinch"] = abs(h["wert"] / t["wert"] - 1) * 100 < avwap.PINCH_PCT
    try:
        vv = volumenprofil.verankert(df, zahltag, zone_start)
    except Exception:  # noqa: BLE001
        vv = None
    if vv:
        g = vv.get("grau") or {}
        aus["volumen"] = {
            "akzeptierter_wert": _zahl(g["profil"]["poc"]) if g.get("profil") else None,
            "seit": f"{pd.Timestamp(g['ab']):%Y-%m-%d}" if g.get("ab") is not None else None, "anker": g.get("art"),
            "mauer": {"von": _zahl(vv["mauer"][0]), "bis": _zahl(vv["mauer"][1]),
                      "seit_hoch": f"{pd.Timestamp(vv['mauer'][2]):%Y-%m-%d}"} if vv.get("mauer") else None,
            "stuetze": {"von": _zahl(vv["stuetze"][0]), "bis": _zahl(vv["stuetze"][1]),
                        "seit_tief": f"{pd.Timestamp(vv['stuetze'][2]):%Y-%m-%d}"} if vv.get("stuetze") else None}
    return aus or None


class Aufklaerung(Exception):
    """Kartentisch fehlt oder ist veraltet – der Stab tagt nicht (keine Kosten für leere Antworten)."""


# ── Feste Ampeln (12.11.2026): Tatsachen färbt der Code nach festen Grenzen, nicht das Modell ──

FESTE_REGELN = (
    ("Setup", "grün = das Setup des Titels erfüllt alle seine Regeln · gelb = in einer Reihe des Kartentischs, aber "
              "nicht voll grün · grau = keine Reihe"),
    ("Einstieg", "Abstand zum Einstieg des Setups (Short gespiegelt): grün = in der Kaufzone (Pivot bis +5 %) · "
                 "gelb = am Auslöser (bis 5 % davor) oder 5–10 % darüber · rot = mehr als 10 % darüber (gelaufen) · "
                 "grau = weiter weg oder kein Pivot"),
    ("Geld", "Geld-Ampel des Rückenwinds: grün, wenn zwei von drei Gruppen (Sektor, Branche, Thema) vorne liegen und keine schwächelt; beim "
             "Short gespiegelt (Abfluss = grün)"),
    ("Zahlen", "Zahlen-Ampel (Gewinn und Umsatz); beim Short nur Zeichen (grau)"),
    ("Termin", "nächste Zahlen in höchstens 7 Tagen = rot · in 8–14 Tagen = gelb · später = grün · unbekannt = grau"),
)
_GEGEN = {"grün": "rot", "rot": "grün", "gelb": "gelb"}


def feste_ampeln(c, heute=None):
    """Die festen Ampeln einer Akte: {Name: (Ampel, kurzer Wert)}. Ampel grün/gelb/rot/grau."""
    heute = heute or HEUTE()
    short = c.get("seite") == "short"
    r, z = c.get("rueckenwind") or {}, c.get("zahlen") or {}
    aus = {}
    if c.get("reihe") in (None, "keine Reihe"):
        aus["Setup"] = ("grau", "keine Reihe")
    else:
        aus["Setup"] = ("grün" if c.get("setup_gruen") else "gelb", c.get("reihe"))
    d = c.get("abstand_roh") if c.get("abstand_roh") is not None else c.get("abstand_zum_pivot_pct")   # Ampel ungerundet
    if d is None:
        aus["Einstieg"] = ("grau", "kein Pivot")
    else:
        e = -d if short else d
        amp = ("grün" if 0 <= e <= 5 else "gelb" if -5 <= e < 0 or 5 < e <= 10 else "rot" if e > 10 else "grau")
        wort = {"grün": "Kaufzone" if not short else "Short-Zone", "rot": "gelaufen", "grau": "weit weg"}.get(
            amp, "am Auslöser" if e < 0 else "knapp drüber")
        aus["Einstieg"] = (amp, f"{d:+.1f} % · {wort}".replace(".", ","))
    g = r.get("geld_ampel")
    zu = r.get("zufluss")
    zu_ = f" · Zufluss {zu:.2f}×".replace(".", ",") if isinstance(zu, (int, float)) else ""
    if g in _GEGEN:
        aus["Geld"] = (_GEGEN[g] if short else g, f"Geld {g}{zu_}")
    else:
        aus["Geld"] = ("grau", "kein Rückenwind-Eintrag")
    za = z.get("ampel")
    aus["Zahlen"] = (("grau" if short else za) if za in _GEGEN else "grau",
                     f"Zahlen {za}" + (f" · {z['punkte']} Punkte" if isinstance(z.get("punkte"), (int, float)) else "")
                     if za else "unbekannt")
    tage = termin_tage(z, (c.get("kacheln") or {}).get("Nächste Zahlen"), heute)
    if tage is None or tage < 0:
        aus["Termin"] = ("grau", "unbekannt")
    else:
        import gestaltung
        aus["Termin"] = (gestaltung.termin_ampel(tage), f"Zahlen in {tage} Tagen")
    return aus


def warum(c):
    """Warum der Titel beim Stab liegt – in Worten (für die Tafel aller Akten)."""
    teile = (["Depot"] if c.get("depot") else []) + (["Volltreffer"] if c.get("volltreffer") else []) \
        + ([c["reihe"]] if c.get("reihe") not in (None, "keine Reihe") else []) \
        + (["dreifacher Rückenwind"] if c.get("dreifacher_rueckenwind") and not c.get("volltreffer") else []) \
        + (["Watchlist"] if c.get("watchlist") else [])
    return " · ".join(teile) or "—"


def tafel(lb):
    """Die Akten als Tafel: je Titel Seite, Kurs, Pivot, Stopp, warum beim Stab, feste Ampeln (wird mit der Konferenz
    gespeichert – die Lagekarte zeigt den Stand, mit dem der Stab gearbeitet hat)."""
    stab_ = {c["titel"] for c in lb["kandidaten"]}
    return [{"titel": c["titel"], "seite": c.get("seite"), "beim_stab": c["titel"] in stab_,
             "warum": warum(c) if c["titel"] in stab_ else "Watchlist · ohne Setup (nur feste Ampeln)",
             "depot": c.get("depot"),
             "watchlist": c.get("watchlist"), "volltreffer": c.get("volltreffer"), "kurs": c.get("kurs"),
             "pivot": c.get("pivot"), "abstand": c.get("abstand_zum_pivot_pct"), "kaufzone_bis": c.get("kaufzone_bis"),
             "stopp": c.get("stopp_1_5_atr"), "ampeln": c.get("feste_ampeln") or {k: {"ampel": a, "wert": w} for k, (a, w)
                                                       in feste_ampeln(c, lb.get("heute")).items()}}
            for c in lb["kandidaten"] + (lb.get("beobachtet") or [])]


def brett(lb):
    """Das Lagebrett: Markt (O'Neil), Pendel, Datenstand – Tatsachen der App, so wie der Stab sie las."""
    m = lb.get("markt") or {}
    pe = lb.get("pendel") or {}
    ds = lb.get("datenstand") or {}
    return {"markt": {"ampel": m.get("ampel"), "wort": m.get("wort"), "seit": m.get("seit")},
            "pendel": {"zone": pe.get("zone"), "ampel": pe.get("ampel"), "pfeil": pe.get("pfeil"),
                       "vor_4_wochen": pe.get("vor_4_wochen")},
            "datenstand": {"ampel": ds.get("ampel"), "text": ds.get("urteil")}, "barometer": lb.get("barometer")}


def bilanz(vorher, kurs_heute):
    """Was aus den Zielen der letzten Konferenz wurde: je Ziel (Volltreffer, long, short) Kurs damals → heute und ✓/✗
    (long gestiegen bzw. short gefallen). Beobachtung, kein Urteil über Setups."""
    if not vorher:
        return None
    b = vorher.get("befehl") or {}
    kurse = vorher.get("kurse") or {}
    aus, gesehen = [], set()
    if vorher.get("format") == 2:                      # neuer Stab: die Chancen des Befehls
        for c in b.get("chancen") or []:
            tk = str(c.get("titel") or "").upper()
            alt, neu = kurse.get(tk), kurs_heute(tk)
            pct = _zahl((neu / alt - 1) * 100, 1) if alt and neu else None
            sh = c.get("seite") == "short"
            aus.append({"titel": tk, "seite": c.get("seite") or "long", "pct": pct,
                        "treffer": None if pct is None else (pct < 0 if sh else pct > 0)})
        return {"konferenz_vom": vorher.get("stand"), "ziele": aus}
    for teil in ("volltreffer", "long", "short"):
        for h in b.get(teil) or []:
            for tk in _ticker(h.get("titel"), None)[:1]:
                if tk in gesehen:
                    continue
                gesehen.add(tk)
                alt, neu = kurse.get(tk), kurs_heute(tk)
                pct = _zahl((neu / alt - 1) * 100, 1) if alt and neu else None
                aus.append({"titel": tk, "seite": "short" if teil == "short" else "long", "pct": pct,
                            "treffer": None if pct is None else (pct < 0 if teil == "short" else pct > 0)})
    return {"konferenz_vom": vorher.get("stand"), "ziele": aus}


def auswahl(titel_t, rw_t, drei, wl, pos, mit_rest=False):
    """Welche Titel eine Akte bekommen (eine Funktion für Stab und Seite Setups – was die Seite zeigt, geht in die
    Konferenz). → (Liste in Rangfolge, {Ticker: (beim Stab?, Grund)}) für jeden Titel mit Reihe, auf der Watchlist oder
    im Depot."""
    import kartentisch
    rang = kartentisch.RANG

    def zone(tk):
        x = titel_t.get(tk) or {}
        if x.get("reihe") in ("k_ermuedung", "k_baerenflagge", "k_bruch") or (x.get("reihe") == "zahlen" and x.get("zr_seite") == "short"):
            return ZONE_SHORT
        return ZONE_VOLLTREFFER if tk in drei else ZONE_LONG

    def bereit(tk):
        x = titel_t.get(tk) or {}
        a_ = x.get("abstand_vz")
        if not x.get("reihe") or x.get("reihe") == "vcp" or not x.get("gruen") or a_ is None:
            return False                               # „Base-Ausbruch · nur Muster“ geht nicht in die Konferenz
        lo, hi = zone(tk)
        return lo <= float(a_) <= hi

    def short(tk):
        return zone(tk) == ZONE_SHORT

    def geld_mit(tk):
        """Geld in Richtung des Setups: long grün, Short gespiegelt (Abfluss = rot ist der Rückenwind des Shorts)."""
        g = (rw_t.get(tk) or {}).get("geld_ampel")
        return g == ("rot" if short(tk) else "grün")

    try:
        import zeichen
        kreis_alle = zeichen.laden().get("titel") or {}
    except Exception:  # noqa: BLE001
        kreis_alle = {}

    def kreis_mit(tk):
        """Kreislauf in Richtung des Setups (Prüf-Agent 13.11.2026: die Rangfolge kannte ihn nicht): long Phase 2 oder
        ein Wechsel zu 1/2, Short Phase 3/4 oder ein Wechsel zu 3/4."""
        k = kreis_alle.get(tk) or {}
        p, z = k.get("phase"), k.get("ziel")
        if short(tk):
            return (p in (3, 4) and z not in (1, 2)) or z in (3, 4)
        return (p == 2 and z != 3 and not k.get("rueckschlag")) or z in (1, 2)

    def termin_tage(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        return _tage((r.get("zahlen") or {}), (x.get("kacheln") or {}).get("Nächste Zahlen"))

    def klasse(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        voll = tk in drei and bool(x.get("reihe")) and not short(tk)   # Volltreffer nur long (Prüf-Agent 12.11.2026)
        t_ = termin_tage(tk)
        rs = r.get("rang") or 0
        import gestaltung
        # Rang: Termin nah nach hinten, Volltreffer, ★, Geld in Setup-Richtung, Kreislauf in Setup-Richtung, RS – die
        # Watchlist zählt nicht
        # (Micky 12.11.2026: neutral, die Stärke entscheidet)
        return (t_ is not None and t_ <= gestaltung.TERMIN_ROT, not voll, not x.get("stern"), not geld_mit(tk),
                not kreis_mit(tk), rs if short(tk) else -rs)

    pool = set(titel_t) | set(drei) | set(wl)
    elite = sorted((tk for tk in pool if bereit(tk)), key=klasse)
    alle = list(pos)
    for reihe_ in rang:                                # bis zu 2 Plätze je Reihe vorab
        if reihe_:
            alle += [tk for tk in elite if (titel_t.get(tk) or {}).get("reihe") == reihe_
                     and tk not in alle][:AKTEN_JE_REIHE]
    alle += [tk for tk in elite if tk not in alle]
    alle = alle[:AKTEN_MAX + len(pos)]
    alle = list(pos) + sorted(set(alle) - set(pos), key=klasse)
    drin = set(alle)
    gruende = {}
    for tk in set(titel_t) | set(wl) | set(pos):
        x = titel_t.get(tk) or {}
        if not x.get("reihe") and tk not in pos and tk not in wl:
            continue
        r = rw_t.get(tk) or {}
        merkmale = ((["Volltreffer"] if tk in drei and x.get("reihe") and not short(tk) else []) + ([("★ Short-Zone" if short(tk) else "★ Kaufzone")] if x.get("stern") else [])
                    + ([("Geld fließt ab" if short(tk) else "Geld grün")] if geld_mit(tk) else [])
                    + (["Watchlist"] if tk in wl else []) + ([f'RS {r["rang"]}'] if r.get("rang") else [])
                    + ([f"Zahlen in {termin_tage(tk)} Tagen"] if (termin_tage(tk) is not None and termin_tage(tk) <= 7)
                       else []))
        if tk in drin:
            g = "Depot" if tk in pos else (" · ".join(merkmale) or "einsatzbereit")
        elif not x.get("reihe"):
            g = "kein Setup"
        elif x.get("still"):
            g = "Kurs steht still"
        elif x.get("reihe") == "vcp":
            g = "nur Muster"
        elif not x.get("gruen"):
            g = "Setup gelb"
        elif x.get("abstand_vz") is None:
            g = "kein Pivot"
        else:
            a_ = float(x["abstand_vz"])
            lo, hi = zone(tk)
            if a_ > hi:
                g = f"{'über der Unterkante' if short(tk) else 'gelaufen'} {a_:+.1f} %"
            elif a_ < lo:
                g = f"{'gelaufen' if short(tk) else 'noch weit vor dem Pivot'} {a_:+.1f} %"
            else:
                g = " · ".join(["Platz voll"] + merkmale)
        gruende[tk] = (tk in drin, g.replace(".", ","))
    if mit_rest:                                       # alle Einsatzbereiten in Rangfolge (Seite Setups)
        return alle, gruende, elite
    return alle, gruende


def lagebild():
    """Alles, was der Stab liest, als dict – nur aus gespeicherten Daten des Nachtlaufs (kein Abruf)."""
    import atr as atr_modul
    import daten
    import depot
    import kartentisch
    import pandas as pd
    import rueckenwind
    import rueckenwind_seite
    import watchlists
    rw = rueckenwind.laden() or {}
    tisch = kartentisch.laden() or {}
    heute = HEUTE()
    if not tisch or not tisch.get("stand"):
        raise Aufklaerung("Aufklärung fehlt: kein Kartentisch")
    alter = (pd.Timestamp(heute) - pd.Timestamp(tisch["stand"])).days
    if alter > TISCH_MAX_TAGE:
        raise Aufklaerung(f"Aufklärung fehlt: Kartentisch vom {pd.Timestamp(tisch['stand']):%d.%m.%Y} ist {alter} Tage alt")
    namen = {k: n for k, n, _ in kartentisch.REIHEN} | kartentisch.ALTE_REIHEN
    titel_t = tisch.get("titel") or {}
    rw_t = rw.get("titel") or {}
    drei = {tk for tk, _ in rueckenwind_seite.dreifach_liste(rw)} if rw else set()
    dep = depot.laden()
    pos = [p["ticker"] for p in dep.get("positionen", [])]
    wl = set(watchlists.alle())
    alle, _ = auswahl(titel_t, rw_t, drei, wl, pos)
    alle = list(dict.fromkeys(alle))

    def akte(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        z = r.get("zahlen") or {}
        kurs = pivot = a = av = None
        try:
            df = daten.kurse_gespeichert(tk)
            if df is not None and len(df):
                kurs = float(df["Close"].iloc[-1])
                a = atr_modul.wert(df)
                import avwap as avwap_
                import kartentisch as kt_
                _, gew_ = kt_._fund_gespeichert(tk)
                zone_ = None
                try:
                    import vcp_zone
                    z_ = vcp_zone.zone(df)
                    zone_ = df.index[int(z_["start_i"])] if z_.get("zone") else None
                except Exception:  # noqa: BLE001
                    pass
                av = avwaps(df, avwap_.zahlentag(df, gew_) if gew_ is not None else None, zone_)
        except Exception:  # noqa: BLE001
            pass
        ein = x.get("einstieg") or {}                   # Einstieg des Setups, im Kartentisch festgestellt (Prüf-Agent
        if ein.get("wert"):                             # 12.11.2026: vorher aus dem Kurs von heute und dem Abstand
            pivot = float(ein["wert"])                  # eines älteren Tischs zurückgerechnet)
        elif kurs and x.get("abstand_vz") is not None:  # Tische vor dem 13.11.2026
            pivot = kurs / (1 + float(x["abstand_vz"]) / 100)
        # Abstand wie die Auswahl: vom Tag des Kartentischs (Prüf-Agent: sonst misst die Akte am Kurs von heute und
        # die Auswahl am Tisch-Tag – ein Titel stand dann „einsatzbereit“ und zugleich „gelaufen“); ungerundet für die Ampel
        abst = float(x["abstand_vz"]) if x.get("abstand_vz") is not None else None
        short_ = _seite(x) == "short"                   # Short: Stopp über dem Einstieg (12.11.2026, vorher darunter)
        stopp = (pivot + 1.5 * a if short_ else pivot - 1.5 * a) if pivot and a else None
        kacheln = {}
        for k_, v in (x.get("kacheln") or {}).items():
            amp = v[0] if not isinstance(v[0], list) else {"M": v[0][0], "K": v[0][1] if len(v[0]) > 1 else None}
            wert = v[1] if len(v) > 1 else None
            text = v[2] if len(v) > 2 else None
            if k_ == "Nächste Zahlen":                 # Wert „in n Tagen“ auf heute umrechnen, alte Termine weg
                n_ = termin_tage(None, v)
                if n_ is not None:
                    wert = "heute" if n_ == 0 else "morgen" if n_ == 1 else f"in {n_} Tagen"
                elif not _termin_ok(wert) or str(wert).startswith("in ") or wert in ("heute", "morgen"):
                    wert, text = "unbekannt", None
            kacheln[k_] = {"ampel": amp, "wert": wert, "text": text}
        c = {"titel": tk, "depot": tk in pos, "watchlist": tk in wl, "setup_gruen": bool(x.get("gruen")),
                "reihe": namen.get(x.get("reihe"), x.get("reihe")) if x.get("reihe") else "keine Reihe",
                "auch": x.get("auch") or [],
                "dreifacher_rueckenwind": tk in drei, "volltreffer": tk in drei and bool(x.get("reihe")) and _seite(x) != "short",
                "seite": _seite(x), "regeln_base": x.get("m"), "regeln_momentum": x.get("k"),
                "luecken": x.get("luecken"), "wertzone": x.get("zustand"),
                "kurs": _zahl(kurs), "pivot": _zahl(pivot), "abstand_zum_pivot_pct": _zahl(abst, 1),
                "abstand_roh": abst, "einstieg_quelle": ein.get("quelle"),
                "kurs_tisch_tag": _zahl(pivot * (1 + abst / 100)) if pivot and abst is not None else None,
                "kaufzone_bis": _zahl(pivot * 1.05) if pivot and not short_ else None,
                "shortzone_bis": _zahl(pivot * 0.95) if pivot and short_ else None, "atr": _zahl(a),
                "stopp_1_5_atr": _zahl(stopp), "abstand_kurs_stopp_pct": _zahl((kurs / stopp - 1) * 100, 1)
                if kurs and stopp else None,
                "ausbruch": x.get("ausbruch"), "zahlen_reaktion": x.get("zr"), "avwap": av, "kacheln": kacheln,
                "rueckenwind": {k_: ({"Ermüdend": "Schwächelnd", "Abgehängt": "Zurückfallend"}.get(r.get(k_), r.get(k_))
                                     if k_.endswith("_feld") else r.get(k_))
                                for k_ in ("stufe", "rang", "rang_vor4", "tempo", "beschleunigung",
                                                         "rs_hoch_vor_kurs", "geld_ampel", "sektor", "sektor_feld",
                                                         "branche", "branche_feld", "thema", "thema_feld", "zufluss",
                                                         "jung")} if r else None,
                "zahlen": {"ampel": z.get("ampel"), "punkte": z.get("punkte"), "termin": _termin_ok(z.get("termin")),
                           "reaktion": z.get("reaktion")} if z else None}
        c["feste_ampeln"] = {k_: {"ampel": a_, "wert": w_} for k_, (a_, w_) in feste_ampeln(c, heute).items()}
        c["kreislauf"] = _kreis_kurz(tk)              # Phase und Zeichen der Stärke/Schwäche (13.11.2026)
        c["bewegung"] = _bewegung(tk)
        return c

    fn = {"Ermüdend": "Schwächelnd", "Abgehängt": "Zurückfallend"}       # Namen wie auf dem Bildschirm
    gruppen = [{k: (fn.get(g.get(k), g.get(k)) if k in ("feld", "feld_vor4") else g.get(k))
                for k in ("art", "name", "anzahl", "feld", "feld_vor4", "seit_wochen", "weg", "zufluss",
                          "rueckschlag", "stabil")} for g in rw.get("gruppen", [])]
    wechsel = [{"titel": tk, **e[-1]} for tk, e in (rw.get("logbuch") or {}).items()
               if e and e[-1].get("seit") and e[-1]["seit"] >= (rw.get("stand") or "")[:10]][:60]
    import rueckenwind as rw_kern
    schnell = rw_kern.anfuehrer_verfolger(rw) if rw else {}
    vorher = set((_vorige(heute) or {}).get("dreifach") or [])
    markt = {}
    try:
        import marktklima
        b = tisch.get("barometer") or {}
        markt = marktklima.markt(b.get("hochs"), b.get("tiefs"))     # eine Ampel nach O'Neil (Micky 12.11.2026)
    except Exception:  # noqa: BLE001
        pass
    wetter = pendel = None
    try:                                                 # Wirtschaftswetter und Pendel wie auf der Seite Rückenwind
        import lage                                      # (10.11.2026, für Murphy und die Gefechtsfrage des Strategen)
        q = lage.quadrant()
        wetter = {"quad": q["quad"], "name": q["name"], "amtlich": q["amtlich"], "wechsel_moeglich": q["wechsel_moeglich"],
                  "wachstum": _runden(q["wachstum"]), "inflation": _runden(q["inflation"]), "bip_rate": q["bip_rate"],
                  "cpi_rate": q["cpi_rate"], "typische_fuehrer": q["fuehrer"]}
        pe = lage.pendel()
        pendel = {"zone": pe["zone"], "ampel": pe["ampel"], "vor_4_wochen": pe["vor_4_wochen"], "pfeil": pe["pfeil"],
                  "messwerte": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in pe["messwerte"].items()}}
    except Exception:  # noqa: BLE001 – ohne Wetter tagt der Stab trotzdem
        pass
    try:
        import nachtlauf
        teile = nachtlauf.datenstand()             # live gemessen, nicht aus dem Protokoll (das schreibt erst das Ende)
        amp_, urteil_ = nachtlauf.datenstand_zeile(teile)
        ds = {"teile": teile, "urteil": urteil_, "ampel": amp_}
    except Exception:  # noqa: BLE001
        ds = None
    return {"heute": heute, "datenstand": ds, "stand_rueckenwind": rw.get("stand"), "stand_kartentisch": tisch.get("stand"),
            "barometer": tisch.get("barometer"), "markt": markt,
            "wirtschaftswetter": wetter, "pendel": pendel, "gruppen": gruppen, "stufenwechsel_heute": wechsel,
            "schnellsuche": schnell, "dreifach": sorted(drei), "dreifach_neu": sorted(drei - vorher) if vorher else [],
            "dreifach_weg": sorted(vorher - drei) if vorher else [],
            "kandidaten": [akte(tk) for tk in alle],
            "beobachtet": [akte(tk) for tk in sorted(wl - set(alle))],   # nur feste Ampeln, nicht an den Stab
            "depot": {"konto": dep.get("konto"), "risiko_pct": dep.get("risiko_pct"),
                      "positionen": dep.get("positionen", []),
                      "hinweis": None if dep.get("konto") else "kein Kontostand eingetragen"}}


def _ausschnitt(lb, nr):
    """Was jeder Stratege liest (spart Token, schärft den Blick)."""
    k = lb["kandidaten"]
    if nr == 2:
        return {x: lb.get(x) for x in ("heute", "datenstand", "stand_rueckenwind", "wirtschaftswetter", "gruppen", "stufenwechsel_heute",
                                       "schnellsuche", "dreifach", "dreifach_neu", "dreifach_weg")} | {
            "kandidaten": [{a: c.get(a) for a in ("titel", "reihe", "seite", "dreifacher_rueckenwind", "volltreffer", "rueckenwind",
                                                  "feste_ampeln")}
                           for c in k]}
    if nr == 3:
        return {"heute": lb["heute"], "datenstand": lb.get("datenstand"), "kandidaten": [
            {a: c.get(a) for a in ("titel", "reihe", "seite", "volltreffer", "depot", "zahlen", "zahlen_reaktion",
                                   "feste_ampeln")}
            | {"kacheln": {n: c["kacheln"].get(n) for n in ("Fundament", "Nächste Zahlen") if n in c["kacheln"]}}
            for c in k]}
    if nr == 4:
        return {"heute": lb["heute"], "datenstand": lb.get("datenstand"), "stand_kartentisch": lb["stand_kartentisch"], "kandidaten": [
            {a: c.get(a) for a in ("titel", "reihe", "seite", "volltreffer", "setup_gruen", "regeln_base", "regeln_momentum",
                               "luecken", "wertzone", "kurs", "pivot", "abstand_zum_pivot_pct", "kurs_tisch_tag", "kaufzone_bis", "shortzone_bis", "einstieg_quelle", "atr",
                               "stopp_1_5_atr", "ausbruch", "zahlen_reaktion", "avwap", "kacheln", "feste_ampeln")}
            | {"stufe": (c["rueckenwind"] or {}).get("stufe")} for c in k]}
    return {"heute": lb["heute"], "datenstand": lb.get("datenstand"), "barometer": lb["barometer"], "markt": lb["markt"], "pendel": lb.get("pendel"),
            "wirtschaftswetter": lb.get("wirtschaftswetter"), "depot": lb["depot"],
            "kandidaten": [{a: c.get(a) for a in ("titel", "depot", "reihe", "seite", "volltreffer", "kurs", "pivot",
                                                  "stopp_1_5_atr", "abstand_kurs_stopp_pct", "feste_ampeln")}
                           | {"markt": c["kacheln"].get("Markt"), "naechste_zahlen": c["kacheln"].get("Nächste Zahlen"),
                              "sektor": (c["rueckenwind"] or {}).get("sektor"),
                              "branche": (c["rueckenwind"] or {}).get("branche"),
                              "thema": (c["rueckenwind"] or {}).get("thema"),
                              "termin": (c["zahlen"] or {}).get("termin")} for c in k]}


# ── Konferenz (Nachtlauf) und Fragen ──

def _zahlen_in(text):
    """Zahlen aus einem Text (deutsch oder englisch geschrieben) als float."""
    import re
    aus = []
    text = re.sub(r"\b\d{1,2}\.\d{1,2}\.(\d{2,4})?", " ", str(text or ""))          # Datum (19.11.) ist keine Zahl
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", text)
    for z in re.findall(r"(?<![\w.])[-+−]?\d[\d.,]*", text):
        z = z.replace("−", "-").rstrip(".,")
        if "," in z:
            z = z.replace(".", "").replace(",", ".")
        elif z.count(".") > 1:
            z = z.replace(".", "")
        try:
            aus.append(float(z))
        except ValueError:
            pass
    return aus


def _beleg(quelle):
    """Alle Zahlen einer Quelle (Daten als Text) in Rundungsstufen – Grundlage der Faktenwache."""
    menge = set()
    for z in _zahlen_in(quelle):
        for n in (0, 1, 2):
            menge.add(round(abs(z), n))
    return menge


def faktenwache(hinweise_, quelle, bekannt):
    """Prüft jeden Hinweis (10.11.2026): Ticker, die die App nicht kennt, und Zahlen, die in den Daten nicht vorkommen
    (auch nicht gerundet). Kleine ganze Zahlen (Tage, Anzahl) und Jahreszahlen bleiben außen vor. Ergebnis steht im
    Hinweis unter „wache“; „nicht gefunden“ heißt nicht „falsch“, aber: nachsehen. Satzteile, die der Stratege mit
    „gerechnet“ kennzeichnet, prüft die Wache nicht (Regel 10 der Dienstanweisung; 11.11.2026)."""
    beleg = _beleg(quelle)
    for h in hinweise_:
        feld = h.get("titel") or []
        tks = [str(x).upper().strip() for x in ([feld] if isinstance(feld, str) else feld) if str(x).strip()]
        fremd = [x for x in tks if bekannt and x not in bekannt]
        offen = []
        import re
        text_ = " ".join(str(h.get(f) or "") for f in FELDER_WACHE + ("text",) if isinstance(h.get(f), str))
        text_ += " " + " ".join(str(h[f]) for f in ("einstieg", "stopp") if isinstance(h.get(f), (int, float)))
        teile = [t for t in re.split(r"(?<=[.;:!?])\s+|\s·\s|,\s(?=[a-zäöü])", text_) if "gerechnet" not in t]
        for z in _zahlen_in(" ".join(teile)):           # selbst gerechnet und so gekennzeichnet: kein Fall der Wache
            w = abs(z)
            if (w == int(w) and w <= 31) or 1990 <= w <= 2100:
                continue
            if not any(round(w, n) in beleg for n in (0, 1, 2)):
                offen.append(f"{z:g}".replace(".", ","))
        if fremd or offen:
            h["wache"] = {"ticker": fremd, "zahlen": offen[:6]}
    return hinweise_


def _vorige(heute):
    """Letzte Konferenz vor heute (für Lagebuch und Wechsel beim dreifachen Rückenwind)."""
    if not os.path.isdir(SPEICHER):
        return None
    for f in sorted((f for f in os.listdir(SPEICHER) if f[:4].isdigit() and f.endswith(".json")), reverse=True):
        if f[:10] < heute:
            k = json_lesen(os.path.join(SPEICHER, f))
            if k:
                return k
    return None


def _kurs(tk):
    try:
        import daten
        df = daten.kurse_gespeichert(tk)
        return float(df["Close"].iloc[-1]) if df is not None and len(df) else None
    except Exception:  # noqa: BLE001
        return None


def _bekannt(lb):
    aus = {c["titel"] for c in lb["kandidaten"]} | set(lb.get("dreifach") or [])
    try:
        import kartentisch
        import rueckenwind
        aus |= set((rueckenwind.laden() or {}).get("titel") or {}) | set((kartentisch.laden() or {}).get("titel") or {})
    except Exception:  # noqa: BLE001
        pass
    return aus


def _kreis_kurz(tk):
    """Der Kreislauf eines Titels für den Stab (ohne Kurvenpunkte) – vom Frühlauf gespeichert (zeichen.laden)."""
    try:
        import zeichen
        k = zeichen.von(tk)
    except Exception:  # noqa: BLE001
        k = None
    if not k:
        return None
    rel = k.get("relativ") or {}
    return {"phase": k["phase"], "wechsel_zu": k.get("ziel"), "wort": k["wort"], "satz": k["satz"],
            "staerke": k.get("staerke"), "schwaeche": k.get("schwaeche"),
            "dow_tag": (k.get("dow_tag") or {}).get("struktur"), "dow_woche": (k.get("dow_woche") or {}).get("struktur"),
            "einquetschung": k.get("einquetschung"), "akkumulation": k.get("akkumulation"), "trend": k.get("trend"),
            "seit_korrekturbeginn": {"seit": rel.get("seit"), "titel_pct": rel.get("titel_pct"),
                                     "index_pct": rel.get("index_pct")} if rel.get("seit") else None,
            "staerke_in_der_schwaeche": staerke_in_schwaeche(tk)}


def staerke_in_schwaeche(tk):
    """Die Zeichen der Stärke in der Schwäche eines Titels (zeichen.relativ: hält, führt, nah am Hoch, RS-Hoch,
    höheres Tief gegen den Index) – leer, wenn keine. Regel 8 (Micky 13.11.2026): so ein Titel wird nie wegen des
    Marktes verworfen."""
    try:
        import zeichen
        return list(((zeichen.von(tk) or {}).get("relativ") or {}).get("staerke") or [])
    except Exception:  # noqa: BLE001
        return []


def _kerzen(tk, n=60):
    """Die letzten n Tageskerzen kompakt: [Tag, Eröffnung, Hoch, Tief, Schluss, Volumen in Tausend]."""
    try:
        import daten
        df = daten.kurse_gespeichert(tk)
    except Exception:  # noqa: BLE001
        return None
    if df is None or not len(df):
        return None
    return [[f"{i:%m-%d}", _zahl(r.Open), _zahl(r.High), _zahl(r.Low), _zahl(r.Close), int(r.Volume / 1000)]
            for i, r in df.iloc[-n:].iterrows()]


def _bewegung(tk):
    try:
        import daten
        df = daten.kurse_gespeichert(tk)
        c, v = df["Close"], df["Volume"]
        return {"5_tage_pct": _zahl((c.iloc[-1] / c.iloc[-6] - 1) * 100, 1),
                "20_tage_pct": _zahl((c.iloc[-1] / c.iloc[-21] - 1) * 100, 1),
                "volumen_5_zu_50": _zahl(v.iloc[-5:].mean() / v.iloc[-55:-5].mean(), 2)}
    except Exception:  # noqa: BLE001
        return None


def _nachbarn(tk, rw_t, n=5):
    """Schwestern derselben Branche (Livermore): RS-Rang, Stufe, Phase."""
    br = (rw_t.get(tk) or {}).get("branche")
    if not br:
        return []
    liste = sorted(((t_, x) for t_, x in rw_t.items() if t_ != tk and x.get("branche") == br),
                   key=lambda p: -(p[1].get("rang") or 0))[:n]
    return [{"titel": t_, "rang": x.get("rang"), "stufe": x.get("stufe"),
             "phase": ((_kreis_kurz(t_) or {}).get("wort"))} for t_, x in liste]


def fruehe_zeichen(k, seite="stärke"):
    """Frühe Zeichen eines Titels (Micky 13.11.2026), aus dem Kreislauf des Frühlaufs → [(Gewicht, Text)]: jedes
    gemessene Zeichen der Seite mit seinem Gewicht (Struktur und Stärke gegen den Markt 2, sonst 1) und der Wechsel,
    der sich abzeichnet. seite="schwäche" für die Short-Anwärter. Gewicht nur für die Rangfolge, nirgends angezeigt."""
    aus = [(x.get("gewicht", 1), x["text"]) for x in k.get("zeichen") or [] if x.get("seite") == seite]
    if not k.get("zeichen"):                     # ältere Ablage ohne Zeichenliste
        aus = [(1, s_) for s_ in k.get("staerke" if seite == "stärke" else "schwaeche") or []]
    ziele = (1, 2) if seite == "stärke" else (3, 4)
    if k.get("ziel") in ziele:
        aus.insert(0, (3, f"Wechsel zu Phase {k['ziel']} zeichnet sich ab ({k.get('wort')})"))
    return aus


def anwaerter_liste(lb, n_long=ANWAERTER_LONG, n_short=ANWAERTER_SHORT):
    """Material des Jägers (Micky 13.11.2026): Titel ohne Akte (kein einsatzbereites Setup) mit frühen Zeichen – bis zu
    n_long der Stärke (seite long) und n_short der Schwäche (seite short; Prüf-Agent 13.11.2026: die Short-Seite
    fehlte). Dazu jede Depotposition mit frühen Zeichen der Schwäche (im_depot, auch mit Akte). Rangfolge je Seite:
    Gewicht der Zeichen, dann eigene minus Gegenzeichen, dann RS-Rang (Short: der schwächste zuerst)."""
    import rueckenwind
    try:
        import zeichen
        alle = zeichen.laden().get("titel") or {}
    except Exception:  # noqa: BLE001
        alle = {}
    rw_t = (rueckenwind.laden() or {}).get("titel") or {}
    akten_tk = {c["titel"] for c in lb.get("kandidaten") or []}
    depot_tk = {p["ticker"] for p in ((lb.get("depot") or {}).get("positionen") or [])}
    seiten = {"long": ([], "stärke", "staerke", "schwaeche", n_long), "short": ([], "schwäche", "schwaeche", "staerke",
                                                                               n_short)}
    fz, warn = {}, []
    for tk, k in alle.items():
        rang_ = (rw_t.get(tk) or {}).get("rang") or 0
        if tk in depot_tk:
            f_ = fruehe_zeichen(k, "schwäche")
            if f_:
                fz[(tk, "short")] = [t_ for _, t_ in f_]
                warn.append(tk)
            continue
        if tk in akten_tk:
            continue
        for seite, (zeilen, wort, eigen, gegen, _) in seiten.items():
            f_ = fruehe_zeichen(k, wort)
            if f_:
                fz[(tk, seite)] = [t_ for _, t_ in f_]
                zeilen.append((sum(g for g, _ in f_), len(k.get(eigen) or []) - len(k.get(gegen) or []),
                               rang_ if seite == "long" else -rang_, tk))

    def eintrag(tk, seite, im_depot=False):
        r = rw_t.get(tk) or {}
        z = r.get("zahlen") or {}
        return {"titel": tk, "seite": seite, "im_depot": im_depot, "fruehe_zeichen": fz[(tk, seite)],
                "kreislauf": _kreis_kurz(tk), "bewegung": _bewegung(tk), "kerzen_30": _kerzen(tk, 30),
                "rueckenwind": {a: r.get(a) for a in ("stufe", "rang", "tempo", "rs_hoch_vor_kurs", "geld_ampel",
                                                      "sektor", "sektor_feld", "branche", "branche_feld",
                                                      "zufluss")} if r else None,
                "zahlen": {"ampel": z.get("ampel"), "termin": _termin_ok(z.get("termin")),
                           "reaktion": z.get("reaktion")} if z else None,
                "nachbarn": _nachbarn(tk, rw_t)}
    aus = [eintrag(tk, "short", True) for tk in sorted(warn)]
    reihen = {}
    for seite, (zeilen, _, _, _, n) in seiten.items():
        zeilen.sort(reverse=True)
        reihen[seite] = [eintrag(tk, seite) for _, _, _, tk in zeilen[:n]]
    lo, sh = reihen["long"], reihen["short"]
    while lo or sh:                              # zwei long, ein short – so bekommt auch die Aufklärung beide Seiten
        aus += lo[:2] + sh[:1]
        lo, sh = lo[2:], sh[1:]
    return aus


def geschichte_daten(heute, n=10):
    """Material der Kriegsgeschichte – vom Code gerechnet: je Auftrag bzw. Ziel der letzten n Konferenzen Kurs damals,
    ob der Auslöser (Einstieg) erreicht wurde, die größte Bewegung danach, ob der Stopp fiel, Kurs heute."""
    import daten
    import pandas as pd
    if not os.path.isdir(SPEICHER):
        return []
    aus = []
    for f in sorted((f for f in os.listdir(SPEICHER) if f[:4].isdigit() and f.endswith(".json") and f[:10] < heute),
                    reverse=True)[:n]:
        k = json_lesen(os.path.join(SPEICHER, f)) or {}
        kurse = k.get("kurse") or {}
        ziele = []
        if k.get("format") == 2:
            plan = ((k.get("missionen") or {}).get("4") or {})
            chancen = {c["titel"] for c in (k.get("befehl") or {}).get("chancen") or []}
            for a in plan.get("auftraege") or []:
                ziele.append({"mission": "Operationsplaner" + (" · Chance im Befehl" if a["titel"] in chancen else ""),
                              "titel": a["titel"], "seite": a.get("seite"), "einstieg": a.get("einstieg"),
                              "stopp": a.get("stopp")})
            for a in ((k.get("missionen") or {}).get("3") or {}).get("anwaerter") or []:
                ziele.append({"mission": "Jäger", "titel": a["titel"], "seite": "long"})
        else:
            b = k.get("befehl") or {}
            for teil in ("volltreffer", "long", "short"):
                for h in b.get(teil) or []:
                    for tk in _ticker(h.get("titel"), None)[:1]:
                        ziele.append({"mission": "alter Stab · " + teil, "titel": tk,
                                      "seite": "short" if teil == "short" else "long"})
        for z in ziele:
            try:
                df = daten.kurse_gespeichert(z["titel"])
                nach = df[df.index > pd.Timestamp(k["stand"])]
            except Exception:  # noqa: BLE001
                continue
            alt = kurse.get(z["titel"])
            if nach is None or not len(nach) or not alt:
                continue
            short_ = z.get("seite") == "short"
            hoch, tief, jetzt = float(nach["High"].max()), float(nach["Low"].min()), float(nach["Close"].iloc[-1])
            e, s = z.get("einstieg"), z.get("stopp")
            z.update(konferenz=k["stand"], kurs_damals=alt, kurs_heute=_zahl(jetzt),
                     bewegung_pct=_zahl((jetzt / alt - 1) * 100, 1),
                     bestes_pct=_zahl(((tief / alt - 1) if short_ else (hoch / alt - 1)) * 100, 1),
                     ausloeser_erreicht=(tief <= e if short_ else hoch >= e) if e else None,
                     stopp_erreicht=(hoch >= s if short_ else tief <= s) if s else None)
            aus.append(z)
    return aus


def _truppe_daten(lb):
    import atr as atr_modul
    import daten
    aus = []
    for p in (lb.get("depot") or {}).get("positionen") or []:
        tk = p["ticker"]
        try:
            df = daten.kurse_gespeichert(tk)
            kurs, a = float(df["Close"].iloc[-1]), atr_modul.wert(df)
        except Exception:  # noqa: BLE001
            kurs = a = None
        e = p.get("einstieg")
        short_ = p.get("seite") == "short"
        aus.append({"titel": tk, "seite": p.get("seite"), "einstieg": e, "stopp": p.get("stopp"), "kurs": _zahl(kurs),
                    "gewinn_in_atr": _zahl(((e - kurs) if short_ else (kurs - e)) / a, 1) if e and kurs and a else None,
                    "kreislauf": _kreis_kurz(tk), "kerzen_30": _kerzen(tk, 30)})
    return aus


FELDER_WACHE = ("kurz", "text", "einwand", "antwort", "grund", "these", "warum", "tun", "achte_auf", "ausloeser",
                "beleg", "widerlegt_wenn", "warten_auf", "ungueltig_wenn", "anweisung", "wetter", "markt", "leitfrage",
                "anrede", "lehre", "bilanz", "fehler_des_stabs")


def _wache_auf(obj, quelle, bekannt):
    """Faktenwache über eine Meldung beliebiger Form: jedes Objekt mit Text wird geprüft."""
    sammel = []

    def gehe(x):
        if isinstance(x, dict):
            if any(isinstance(x.get(f), str) for f in FELDER_WACHE):
                sammel.append(x)
            for v in x.values():
                if isinstance(v, (dict, list)):
                    gehe(v)
        elif isinstance(x, list):
            for v in x:
                gehe(v)
    gehe(obj)
    if sammel:
        faktenwache(sammel, quelle, bekannt)


def aufklaerung_ziele(depot_tk, akten_tk, anw_tk):
    """Depot zusätzlich; AUFKLAERUNG_MAX weitere Titel: bis 6 Akten und bis 4 Anwärter in Rangfolge, ein freier Platz der einen
    Gruppe geht an die nächste der anderen."""
    a = [t_ for t_ in dict.fromkeys(akten_tk) if t_ not in depot_tk]
    w = [t_ for t_ in dict.fromkeys(anw_tk) if t_ not in depot_tk and t_ not in a]
    n_a = min(len(a), max(AUFKLAERUNG_AKTEN, AUFKLAERUNG_MAX - len(w)))
    n_w = min(len(w), AUFKLAERUNG_MAX - n_a)
    return list(dict.fromkeys(depot_tk)) + a[:n_a] + w[:n_w]


def konferenz(melden=lambda text: None):
    """Der neue Stab (Micky 13.11.2026): acht Missionen statt sechs Strategen nach Meistern. Reihenfolge: Lage und
    Aufklärung → Jäger und Operationsplaner → Gegenspieler → Truppenführung (nur mit Depot) und Kriegsgeschichte →
    Feldherr. Der Code misst (Kreislauf, Zeichen, Ergebnisse früherer Aufträge), die Missionen urteilen. Wachen im Code:
    ein Auftrag nur auf eine Akte mit nicht roter Setup-Ampel, jede Akte eingeordnet, eine Chance nur aus einem
    Auftrag, den der Gegenspieler nicht gekippt hat. Speichert daten/konferenz/<datum>.json (format 2)."""
    melden(f"{datetime.now():%H:%M:%S} Lagebild wird gelesen …")
    lb = lagebild()
    heute = lb["heute"]
    system = dienstanweisung()
    bekannt = _bekannt(lb)
    vorher = _vorige(heute)
    usd_vorher = kosten()["usd"]
    akten_ = lb["kandidaten"]
    import rueckenwind
    rw_t = (rueckenwind.laden() or {}).get("titel") or {}
    for c in akten_:
        c["kerzen_60"] = _kerzen(c["titel"], 60)
    anw = anwaerter_liste(lb)
    bekannt |= {a["titel"] for a in anw}
    melden(f"{datetime.now():%H:%M:%S} {len(akten_)} Akten, {len(anw)} Anwärter (frühe Zeichen, beide Seiten "
           f"und Depot)")
    kurse_ = {c["titel"]: c.get("kurs") for c in akten_} | {a["titel"]: _zahl(_kurs(a["titel"])) for a in anw}
    erg = {"stand": heute, "zeit": f"{datetime.now():%d.%m.%Y %H:%M}", "modell": MODELL, "format": 2, "missionen": {},
           "dreifach": lb["dreifach"], "kurse": {k_: v for k_, v in kurse_.items() if v}, "tafel": tafel(lb),
           "brett": brett(lb), "wache_code": []}
    erg["bilanz"] = bilanz(vorher, lambda tk: kurse_.get(tk) or _zahl(_kurs(tk)))

    def mission(nr, material, schema, max_tokens=6000, vorlauf=""):
        name, frage_ = MISSIONEN[nr]
        daten_ = json.dumps(material, ensure_ascii=False, default=str)
        inhalt = (f"Mission {nr} · {name}: {frage_}\n\nAUFTRAG\n{AUFTRAG_MISSION[nr]}\n\n{LEHRSTELLE[nr]}\n\n"
                  f"MATERIAL DER APP (Stand des Frühlaufs)\n{daten_}{vorlauf}")
        melden(f"{datetime.now():%H:%M:%S} {name} …")
        k0 = dict(kosten())
        usd0 = k0["usd"]
        for versuch in range(2):                       # eine Mission, die an der Schnittstelle scheitert, noch einmal
            try:
                m = _formular(system, inhalt, "melden", schema, max_tokens)
                _wache_auf(m, daten_ + vorlauf, bekannt)
                break
            except Deckel:
                raise
            except Unlesbar as e:
                m = {"fehler": True, "meldung": f"Keine Meldung: {e}", "roh": e.roh}
                break
            except Exception as e:  # noqa: BLE001 – eine Mission fehlt, die anderen laufen weiter
                m = {"fehler": True, "meldung": f"Keine Meldung: {e}"}
                if versuch == 0:
                    melden(f"   {name}: {e} – zweiter Versuch in 60 s")
                    time.sleep(60)
        k1 = kosten()
        m["kosten_usd"] = round(k1["usd"] - usd0 + (vorkosten.pop(nr, 0.0)), 3)
        m["verbrauch"] = {"aufrufe": k1.get("aufrufe", 0) - k0.get("aufrufe", 0),       # wohin das Geld geht
                          "ein_tokens": k1.get("ein", 0) - k0.get("ein", 0), "aus_tokens": k1.get("aus", 0) - k0.get("aus", 0),
                          "material_zeichen": len(inhalt)}
        melden(f"{datetime.now():%H:%M:%S} {name}: {'Fehler – ' + m['meldung'] if m.get('fehler') else 'fertig'}"
               f" · {_zahl_de(m['kosten_usd'])} $ · {m['verbrauch']['aufrufe']} Aufruf(e), "
               f"{m['verbrauch']['ein_tokens'] // 1000}k ein, {m['verbrauch']['aus_tokens'] // 1000}k aus")
        erg["missionen"][str(nr)] = {"name": name, **m}
        return m

    vorkosten = {}                                     # Kosten vor dem Formular einer Mission (Web-Suche der Aufklärung)

    # 1 Lage
    alt_lage = (((vorher or {}).get("missionen") or {}).get("1") or {}) if (vorher or {}).get("format") == 2 else {}
    lage_ = mission(1, {x: lb.get(x) for x in ("heute", "datenstand", "markt", "barometer", "pendel",
                                               "wirtschaftswetter", "gruppen")}
                    | {"lagebuch_gestern": {a: alt_lage.get(a) for a in ("leitfrage", "szenario_a", "szenario_b")}
                       if alt_lage else None}, F_LAGE, 4000)

    # 2 Aufklärung: das Depot immer, dazu 10 Titel – 6 Akten, 4 Anwärter, freie Plätze füllt die andere Gruppe
    depot_tk = [p["ticker"] for p in (lb["depot"].get("positionen") or [])]
    ziele = aufklaerung_ziele(depot_tk, [c["titel"] for c in akten_], [a["titel"] for a in anw])
    akte_von = {c["titel"]: c for c in akten_}
    anw_von = {a["titel"]: a for a in anw}
    stoff = []
    for tk in ziele:
        c = akte_von.get(tk) or anw_von.get(tk) or {}
        stoff.append({"titel": tk, "bewegung": c.get("bewegung") or _bewegung(tk),
                      "zahlen": c.get("zahlen"), "zahlen_reaktion": c.get("zahlen_reaktion"),
                      "kreislauf": (c.get("kreislauf") or {}).get("wort")})
    aufkl = {"titel": []}
    if ziele:
        usd_s = kosten()["usd"]
        try:
            notizen = _anfrage(system, "Suche zu jedem dieser Titel, warum er sich in den letzten Wochen bewegt hat "
                               "(Zahlen, Ausblick, Aufträge, Produkte, Übernahmen, Analysten, Branche, Makro): "
                               f"{', '.join(ziele)}. Schreibe knappe Notizen je Titel mit Quelle (URL) und Datum. "
                               "Nichts erfinden; findest du nichts, schreibe das.", 8000,
                               SUCHEN_AUFKLAERUNG + len(depot_tk))
        except Deckel:
            raise
        except Exception as e:  # noqa: BLE001
            notizen = f"Web-Suche fehlgeschlagen: {e}"
        vorkosten[2] = kosten()["usd"] - usd_s
        melden(f"   Web-Suche: {len(notizen or '')} Zeichen Notizen · {_zahl_de(vorkosten[2])} $")
        aufkl = mission(2, {"heute": heute, "titel": stoff}, F_AUFKL, 8000,
                        "\n\nNOTIZEN DER WEB-SUCHE (Quellen)\n" + (notizen or "keine Fundstellen"))
    aufkl_von = {a.get("titel"): a for a in aufkl.get("titel") or []}

    # 3 Jäger
    jaeger = {"anwaerter": []}
    if anw:
        jaeger = mission(3, {"heute": heute, "markt": lb.get("markt"), "gruppen": lb.get("gruppen"),
                             "anwaerter": [a | {"aufklaerung": aufkl_von.get(a["titel"])} for a in anw]}, F_JAEGER, 6000)
        erlaubt, ges = {a["titel"] for a in anw}, set()
        liste = []
        for a in jaeger.get("anwaerter") or []:
            a["titel"] = str(a.get("titel", "")).upper().strip()
            if a["titel"] in erlaubt and a["titel"] not in ges:
                ges.add(a["titel"])
                liste.append(a)
            elif a["titel"] not in erlaubt:
                erg["wache_code"].append(f"Jäger: {a['titel']} steht nicht auf der Liste der Anwärter – entfernt")
        if not jaeger.get("fehler"):
            seite_von = {a["titel"]: a["seite"] for a in anw}
            depot_w = [a for a in liste if a["titel"] in {x["titel"] for x in anw if x.get("im_depot")}]
            for a in liste:                            # die Seite gibt der Code vor, nicht das Modell
                a["seite"] = seite_von.get(a["titel"], a.get("seite"))
            jaeger["anwaerter"] = depot_w + [a for a in liste if a not in depot_w][:10]
            for x in anw:
                if x.get("im_depot") and x["titel"] not in {a["titel"] for a in depot_w}:
                    erg["wache_code"].append(f"Jäger: Depotposition {x['titel']} mit frühen Zeichen der Schwäche "
                                             "nicht genannt")
            erg["missionen"]["3"]["anwaerter"] = jaeger["anwaerter"]
    else:
        erg["missionen"]["3"] = {"name": MISSIONEN[3][0], "anwaerter": [],
                                 "hinweis": "Kein Titel ohne Setup zeigt frühe Zeichen der Stärke oder Schwäche."}

    # 4 Operationsplaner
    felder = ("titel", "depot", "reihe", "auch", "seite", "volltreffer", "setup_gruen", "kurs", "pivot",
              "abstand_zum_pivot_pct", "kurs_tisch_tag", "kaufzone_bis", "shortzone_bis", "einstieg_quelle", "atr",
              "stopp_1_5_atr", "ausbruch", "zahlen_reaktion", "avwap", "wertzone", "feste_ampeln", "kreislauf",
              "bewegung", "kerzen_60", "luecken")
    plan = {"auftraege": [], "beobachten": [], "verworfen": []}
    if akten_:
        plan = mission(4, {"heute": heute, "datenstand": lb.get("datenstand"), "markt": lb.get("markt"),
                           "szenarien": {"a": lage_.get("szenario_a"), "b": lage_.get("szenario_b")},
                           "akten": [{a: c.get(a) for a in felder} | {"stufe": (c.get("rueckenwind") or {}).get("stufe"),
                                                                        "geld": (c.get("rueckenwind") or {}).get("geld_ampel"),
                                                                        "aufklaerung": aufkl_von.get(c["titel"])}
                                     for c in akten_],
                           "anwaerter_des_jaegers": [{a: x.get(a) for a in ("titel", "seite", "these", "phase", "warten_auf")}
                                                     for x in jaeger.get("anwaerter") or []]}, F_PLAN, 9000)
    # Wachen im Code (Prüf-Agent 13.11.2026): Auftrag nur auf eine Akte mit grünem Setup, Einstieg nicht rot (gelaufen),
    # Seite wie das Setup, jeder Titel einmal, höchstens AUFTRAEGE_MAX; jede Akte eingeordnet; Titel groß geschrieben
    fest = {c["titel"]: c.get("feste_ampeln") or {} for c in akten_}
    ok, weg, gesehen = [], [], set()
    for a in plan.get("auftraege") or []:
        tk = str(a.get("titel", "")).upper().strip()
        a["titel"] = tk
        f_ = fest.get(tk)
        if tk in gesehen:
            continue
        gesehen.add(tk)
        if f_ is None:
            weg.append({"titel": tk, "grund": "keine Akte (kein einsatzbereites Setup) – vom Code aus den Aufträgen genommen"})
        elif (f_.get("Setup") or {}).get("ampel") != "grün":
            weg.append({"titel": tk, "grund": f"Setup-Ampel {(f_.get('Setup') or {}).get('ampel') or 'grau'} – ein Auftrag "
                                              "braucht ein grünes Setup (Code)"})
        elif (f_.get("Einstieg") or {}).get("ampel") == "rot":
            weg.append({"titel": tk, "grund": f"Einstieg rot ({(f_.get('Einstieg') or {}).get('wert')}) – rot ist nie ein "
                                              "Auftrag (Code)"})
        elif akte_von[tk].get("seite") and a.get("seite") != akte_von[tk]["seite"]:
            weg.append({"titel": tk, "grund": f"Seite {a.get('seite')} gegen das Setup ({akte_von[tk]['seite']}) (Code)"})
        elif len(ok) >= AUFTRAEGE_MAX:
            weg.append({"titel": tk, "grund": f"mehr als {AUFTRAEGE_MAX} Aufträge – fällt weg (Code)"})
        else:
            c = akte_von[tk]
            a["einstieg_app"], a["stopp_app"] = c.get("pivot"), c.get("stopp_1_5_atr")
            ok.append(a)
    for teil in ("beobachten", "verworfen"):
        liste, ges = [], set()
        for x in plan.get(teil) or []:
            x["titel"] = str(x.get("titel", "")).upper().strip()
            if x["titel"] and x["titel"] not in ges and x["titel"] not in gesehen - {w["titel"] for w in weg}:
                ges.add(x["titel"])
                liste.append(x)
        plan[teil] = liste
    if not akten_:
        erg["missionen"]["4"] = {"name": MISSIONEN[4][0], **plan, "hinweis": "keine Akte – kein einsatzbereites Setup"}
    elif not plan.get("fehler"):
        plan["auftraege"] = ok
        schon = {x["titel"] for x in plan["verworfen"]}
        plan["verworfen"] += [w for w in weg if w["titel"] not in schon]
        plan["beobachten"] = [x for x in plan["beobachten"] if x["titel"] not in {w["titel"] for w in weg}]
        erg["wache_code"] += [f"Operationsplaner: {w['titel']} – {w['grund']}" for w in weg]
        eingeordnet = {a["titel"] for a in ok} | {x["titel"] for x in plan["beobachten"] + plan["verworfen"]}
        fehlt = [c["titel"] for c in akten_ if c["titel"] not in eingeordnet]
        if fehlt:
            plan["beobachten"] += [{"titel": tk, "warten_auf": "vom Operationsplaner nicht eingeordnet (Code)"}
                                   for tk in fehlt]
            erg["wache_code"].append(f"Operationsplaner: {len(fehlt)} Akte(n) nicht eingeordnet – {', '.join(fehlt)}")
        erg["missionen"]["4"].update(auftraege=plan["auftraege"], beobachten=plan["beobachten"],
                                     verworfen=plan["verworfen"])

    # 5 Gegenspieler
    gegen = {"einwaende": []}
    if plan.get("auftraege"):
        gegen = mission(5, {"heute": heute, "markt": lb.get("markt"), "auftraege": plan["auftraege"],
                            "akten": [{a: akte_von[x["titel"]].get(a) for a in felder}
                                      | {"rueckenwind": akte_von[x["titel"]].get("rueckenwind"),
                                         "zahlen": akte_von[x["titel"]].get("zahlen"),
                                         "nachbarn": _nachbarn(x["titel"], rw_t),
                                         "aufklaerung": aufkl_von.get(x["titel"])} for x in plan["auftraege"]],
                            "anwaerter_des_jaegers": jaeger.get("anwaerter")}, F_GEGEN, 5000)
    else:
        erg["missionen"]["5"] = {"name": MISSIONEN[5][0], "einwaende": [], "hinweis": "kein Auftrag – nichts anzugreifen"}
    urteil = {str(e.get("titel", "")).upper().strip(): e for e in gegen.get("einwaende") or []}

    # 6 Truppenführung, 7 Kriegsgeschichte
    truppe = {"positionen": []}
    if depot_tk:
        truppe = mission(6, {"heute": heute, "markt": lb.get("markt"), "positionen": _truppe_daten(lb),
                             "aufklaerung": [aufkl_von.get(tk) for tk in depot_tk if aufkl_von.get(tk)]}, F_TRUPPE, 4000)
    gesch_d = geschichte_daten(heute)
    gesch = {}
    if gesch_d:
        gesch = mission(7, {"heute": heute, "ergebnisse": gesch_d}, F_GESCHICHTE, 3000)
    else:
        erg["missionen"]["7"] = {"name": MISSIONEN[7][0], "bilanz": "Noch keine früheren Aufträge mit Kursen danach.",
                                 "fehler_des_stabs": None, "lehre": None}

    # 8 Feldherr
    befehl_ = mission(8, {"heute": heute, "datenstand": lb.get("datenstand"), "lage": lage_,
                          "auftraege": [a | {"einwand": urteil.get(a["titel"]),
                                             "kreislauf": (akte_von[a["titel"]].get("kreislauf") or {}).get("wort")}
                                        for a in plan.get("auftraege") or []],
                          "anwaerter_des_jaegers": jaeger.get("anwaerter"), "depot": truppe.get("positionen"),
                          "kriegsgeschichte": gesch if gesch else erg["missionen"]["7"]}, F_BEFEHL, 8000)
    if befehl_.get("fehler"):
        befehl_ = {"anrede": "Hey Micky, heute gibt es keinen Tagesbefehl – " + befehl_.get("meldung", ""),
                   "haltung": None, "chancen": [], "leitfrage": lage_.get("leitfrage"), "szenarien": [],
                   "anwaerter": [], "depot": [], "lehre": None, "fehler": True}
    # Wache im Code: eine Chance nur aus einem Auftrag, den der Gegenspieler nicht gekippt hat
    auftr = {a["titel"]: a for a in plan.get("auftraege") or []}
    bleiben, ges = [], set()
    for c in befehl_.get("chancen") or []:
        tk = str(c.get("titel", "")).upper().strip()
        c["titel"] = tk
        if tk in ges:
            continue
        ges.add(tk)
        if tk not in auftr:
            erg["wache_code"].append(f"Feldherr: {tk} ist kein Auftrag des Planers – aus den Chancen genommen")
        elif (urteil.get(tk) or {}).get("urteil") == "kippt":
            erg["wache_code"].append(f"Feldherr: {tk} vom Gegenspieler gekippt – aus den Chancen genommen")
        else:
            a = auftr[tk]
            c.update(einstieg=a.get("einstieg"), stopp=a.get("stopp"), einstieg_app=a.get("einstieg_app"),
                     stopp_app=a.get("stopp_app"), einwand=urteil.get(tk))
            bleiben.append(c)
    befehl_["chancen"] = bleiben
    erlaubt = {a["titel"] for a in jaeger.get("anwaerter") or []} | {a["titel"] for a in anw}
    an_, ges = [], set()
    for a in befehl_.get("anwaerter") or []:
        a["titel"] = str(a.get("titel", "")).upper().strip()
        if a["titel"] in erlaubt and a["titel"] not in ges:
            ges.add(a["titel"])
            an_.append(a)
        elif a["titel"] not in erlaubt:
            erg["wache_code"].append(f"Feldherr: Anwärter {a['titel']} kommt nicht vom Jäger – entfernt")
    befehl_["anwaerter"] = an_
    for d_ in befehl_.get("depot") or []:
        d_["titel"] = str(d_.get("titel", "")).upper().strip()
    if "8" in erg["missionen"]:
        erg["missionen"]["8"].update(chancen=bleiben, anwaerter=an_)
    befehl_["anhang"] = {"beobachten": plan.get("beobachten") or [], "verworfen": plan.get("verworfen") or []}
    # Regel 8 (Micky 13.11.2026): Stärke in der Schwäche geht nie verloren – der Code nennt jeden solchen Titel
    # (Akte, Anwärter oder Depot, long) selbst und meldet, wenn der Stab ihn übergeht oder wegen des Marktes verwirft
    genannt = {c["titel"] for c in bleiben} | {a["titel"] for a in an_} | {
        str(x.get("titel", "")).upper() for x in plan.get("beobachten") or []}
    markt_wort = ("markt", "korrektur", "marktklima", "o'neil", "distributionstag", "schwacher index")
    sids = []
    for tk in dict.fromkeys(list(akte_von) + [a["titel"] for a in anw if a.get("seite") == "long"] + list(depot_tk)):
        z_ = staerke_in_schwaeche(tk)
        if not z_:
            continue
        sids.append({"titel": tk, "zeichen": z_[:3], "genannt": tk in genannt})
        weg = next((x for x in plan.get("verworfen") or [] if str(x.get("titel", "")).upper() == tk), None)
        if weg and any(w in str(weg.get("grund", "")).lower() for w in markt_wort):
            erg["wache_code"].append(f"Regel 8: {tk} zeigt Stärke in der Schwäche und wurde wegen des Marktes "
                                     f"verworfen („{weg.get('grund', '')}“)")
        elif tk not in genannt:
            erg["wache_code"].append(f"Regel 8: {tk} zeigt Stärke in der Schwäche, der Stab nennt ihn nicht")
    befehl_["staerke_in_der_schwaeche"] = sids
    erg["befehl"] = befehl_
    try:                                               # Kreislaufbild so, wie es am Tag der Konferenz stand
        import zeichen
        tks = set(auftr) | {a.get("titel") for a in jaeger.get("anwaerter") or []} | set(akte_von) | set(depot_tk)
        erg["kreislauf"] = {tk: zeichen.von(tk) for tk in tks if tk and zeichen.von(tk)}
    except Exception:  # noqa: BLE001
        erg["kreislauf"] = {}
    erg["kosten_usd"] = round(kosten()["usd"] - usd_vorher, 2)
    json_schreiben(_pfad(f"{heute}.json"), erg, ensure_ascii=False)
    melden(f"{datetime.now():%H:%M:%S} fertig · diese Konferenz {_zahl_de(erg['kosten_usd'])} $ · Monat "
           f"{_zahl_de(kosten()['usd'])} $")
    return erg


def letzte():
    """Jüngste gespeicherte Konferenz oder None."""
    if not os.path.isdir(SPEICHER):
        return None
    for f in sorted((f for f in os.listdir(SPEICHER) if f[:4].isdigit() and f.endswith(".json")), reverse=True):
        k = json_lesen(os.path.join(SPEICHER, f))
        if k:
            return k
    return None


def _ticker(feld, bekannt):
    """Ticker aus einem Hinweis: Liste (neues Formular) oder Text der alten Konferenzen („COP / PR“,
    „GESUNDHEIT: THC, BTSG, PACS“) – nur Ticker, die die App kennt."""
    import re
    teile = feld if isinstance(feld, list) else re.split(r"[\s,/;:·]+", str(feld or ""))
    return [x for x in (str(t_).upper().strip() for t_ in teile) if x and x != "NULL" and (not bekannt or x in bekannt)]


def hinweise(k):
    """Alle Hinweise einer Konferenz als [(Nr. des Strategen bzw. der Mission, Hinweis)], Tagesbefehl zuerst."""
    if k.get("format") == 2:
        return _hinweise_neu(k)
    b = k.get("befehl") or {}
    liste = [(1, h) for h in b.get("hinweise") or []] + [(1, h) for teil, _ in BEFEHL_TEILE for h in b.get(teil) or []]
    liste += [(1, {**e, "text": f"Einwand: {e.get('einwand', '')} – Abwägung: {e.get('antwort', '')}"})
              for e in b.get("einwaende") or []]
    return liste + [(int(nr), h) for nr, m in sorted((k.get("meldungen") or {}).items()) for h in m.get("hinweise") or []]


def akten(k):
    """Hinweise je Titel aus einer Konferenz: {Ticker: [(Nr. des Strategen, Hinweis)]} – ein Hinweis zu mehreren
    Titeln steht in der Akte jedes einzelnen."""
    bekannt = set()
    try:
        import kartentisch
        import rueckenwind
        bekannt = set((rueckenwind.laden() or {}).get("titel") or {}) | set((kartentisch.laden() or {}).get("titel") or {})
    except Exception:  # noqa: BLE001
        pass
    aus = {}
    for nr, h in hinweise(k):
        for tk in _ticker(h.get("titel"), bekannt):
            aus.setdefault(tk, []).append((nr, h))
    return aus


def frage(text, tk=None):
    """„Stab fragen“: freie Frage an den Stab, auf Wunsch zu einem Titel. Antwort als Text, gespeichert. Seit
    11.11.2026 mit dem Feldhandbuch der Meister, Marktlage, Pendel und Wirtschaftswetter – auf Elite-Stand wie die
    Konferenz."""
    try:
        lb = lagebild()
    except Aufklaerung:
        lb = {"barometer": None, "kandidaten": []}
    k = letzte() or {}
    kontext = {"heute": HEUTE(), "tagesbefehl": k.get("befehl"),
               "meldungen": {nr: m.get("meldung") for nr, m in (k.get("meldungen") or {}).items()},
               "barometer": lb["barometer"], "markt": lb.get("markt"), "pendel": lb.get("pendel"),
               "wirtschaftswetter": lb.get("wirtschaftswetter")}
    if tk:
        tk = tk.upper().strip()
        kontext["titel"] = next((a for a in lb["kandidaten"] if a["titel"] == tk), None) or _einzelakte(tk)
    handbuch = "\n\n".join(f"{MISSIONEN[nr][0]}: {LEHRSTELLE[nr]}" for nr in MISSIONEN)
    inhalt = ("Micky fragt den Stab. Antworte als Stab in höchstens 18 Sätzen, auf Deutsch, nur mit Fakten aus den "
              "Daten oder aus Web-Fundstellen (dann Quelle mit Datum). Urteile nach unserer Lehre von Stärke und "
              "Schwäche (Dienstanweisung) und nenne die Regel beim Namen; nennt die Frage einen Meister, antworte "
              "zuerst mit seiner Regel. Jeder Satz trägt eine Entscheidung. Antworte als Klartext, ohne Werkzeug."
              "\n\nLehrstellen der Missionen:\n" + handbuch
              + "\n\nFrage: " + text + "\n\nDaten der App:\n" + json.dumps(kontext, ensure_ascii=False, default=str))
    antwort = _anfrage(dienstanweisung().replace(" Gib deine Antwort ausschließlich über das Werkzeug ab.", ""),
                       inhalt, 5000, SUCHEN_FRAGE)            # 5000: mit Web-Suche brauchte Opus mehr Platz (11.11.)
    buch = json_lesen(_pfad("fragen.json"), []) or []
    if _LETZTER.get("stop") == "max_tokens":
        antwort += "\n\n*(Antwort am Platzlimit abgeschnitten)*"
    buch.insert(0, {"zeit": f"{datetime.now():%d.%m.%Y %H:%M}", "titel": tk, "frage": text, "antwort": antwort,
                    "ende": _LETZTER.get("stop"), "bloecke": _LETZTER.get("bloecke")})
    json_schreiben(_pfad("fragen.json"), buch[:50], ensure_ascii=False)
    return antwort


def fragen():
    return json_lesen(_pfad("fragen.json"), []) or []


def _einzelakte(tk):
    """Titel außerhalb der Kandidaten: Rückenwind-Eintrag und Kacheln der abgelegten Titelseite."""
    import rueckenwind
    r = ((rueckenwind.laden() or {}).get("titel") or {}).get(tk)
    kach = None
    try:
        import titel
        ab = titel.abgelegt(tk)
        kach = ab[0].get("kacheln") if ab else None
    except Exception:  # noqa: BLE001
        pass
    return {"titel": tk, "rueckenwind": r, "kacheln": kach}


# ── Lagekarte (12.11.2026): was der Konferenzraum auf einen Blick zeigt ──

_RANG_AMPEL = {"rot": 3, "gelb": 2, "grün": 1}


def _kurzsatz(h, n=90):
    t_ = str(h.get("kurz") or h.get("text") or "").strip()
    if h.get("kurz") or len(t_) <= n:
        return t_
    erster = t_.split(". ")[0]
    return (erster if len(erster) <= n else t_[:n].rsplit(" ", 1)[0] + " …")


def lagekarte(k):
    """Alles für die Lagekarte einer Konferenz: brett, ziele, matrix, warten, gefahren, bilanz, tafel, live (True, wenn
    Tafel und Brett nicht mit der Konferenz gespeichert waren und mit dem heutigen Stand gerechnet wurden)."""
    k = k or {}
    b = k.get("befehl") or {}
    if k.get("format") == 2:                           # neuer Stab (13.11.2026): der Befehl selbst ist die Lagekarte
        return {"neu": True, "k": k, "haltung": b.get("haltung"), "lage_kurz": b.get("anrede"), "brett": k.get("brett") or {},
                "tafel": k.get("tafel") or [], "bilanz": k.get("bilanz"), "live": False}
    tf, br, live = k.get("tafel"), k.get("brett"), False
    if tf is None or br is None:                       # Konferenzen vor dem 13.11.2026: Stand von heute
        try:
            lb = lagebild()
            tf, br, live = tf or tafel(lb), br or brett(lb), True
        except Exception:  # noqa: BLE001
            tf, br = tf or [], br or {}
    akten_ = {x["titel"]: x for x in tf}
    einw = {}
    for e in b.get("einwaende") or []:
        for tk in _ticker(e.get("titel"), None):
            einw.setdefault(tk, e)
    ziele, gesehen = [], set()
    for teil in ("volltreffer", "long", "short"):
        for h in b.get(teil) or []:
            tks = _ticker(h.get("titel"), None)
            if not tks or tks[0] in gesehen:
                continue
            tk = tks[0]
            gesehen.add(tk)
            ziele.append({"titel": tk, "teil": teil, "ampel": h.get("ampel"), "kurz": _kurzsatz(h),
                          "text": h.get("text"), "wache": h.get("wache"), "akte": akten_.get(tk),
                          "einwand": einw.get(tk)})
    zeilen = [z["titel"] for z in ziele] + [x["titel"] for x in tf if x.get("depot") and x["titel"] not in gesehen]
    matrix = {}
    for tk in zeilen:
        reihe = {}
        for nr in (2, 3, 4, 5, 6):
            m = (k.get("meldungen") or {}).get(str(nr)) or {}
            u = next((u for u in m.get("urteile") or [] if str(u.get("titel", "")).upper().strip() == tk), None)
            if u:
                reihe[nr] = {"ampel": u.get("ampel"), "grund": u.get("grund"), "wache": u.get("wache")}
                continue
            treffer = [h for h in m.get("hinweise") or [] if tk in _ticker(h.get("titel"), None)]
            if treffer:                                 # ältere Konferenzen: schwerster Hinweis zum Titel
                h = max(treffer, key=lambda h: _RANG_AMPEL.get(h.get("ampel"), 0))
                reihe[nr] = {"ampel": h.get("ampel"), "grund": _kurzsatz(h), "wache": h.get("wache")}
        matrix[tk] = reihe
    warten = [x for x in tf if x["ampeln"].get("Setup", {}).get("ampel") == "grün"
              and str(x["ampeln"].get("Einstieg", {}).get("wert", "")).endswith("am Auslöser")]
    bil = k.get("bilanz")
    if bil is None and k.get("stand"):
        try:
            bil = bilanz(_vorige(k["stand"]), lambda tk: (k.get("kurse") or {}).get(tk) or _zahl(_kurs(tk)))
        except Exception:  # noqa: BLE001
            bil = None
    return {"haltung": b.get("haltung"), "lage_kurz": b.get("lage_kurz"), "lage": b.get("lage"), "brett": br,
            "ziele": ziele, "matrix": matrix, "zeilen": zeilen, "warten": warten,
            "gefahren": [{"titel": _ticker(h.get("titel"), None), "ampel": h.get("ampel"), "kurz": _kurzsatz(h)}
                         for h in b.get("gefahren") or []],
            "bilanz": bil, "tafel": tf, "live": live}


PUNKT = {"grün": "🟢", "gelb": "🟡", "rot": "🔴"}


def kurzfassung(k):
    """Der Tagesbefehl als Meldung aufs Handy (Micky 12.11.2026: „Tagesbefehl gegen 7 Uhr“) → (Titel, Text).
    Nur Tatsachen der Konferenz: Haltung, Lage, Markt und Pendel vom Lagebrett, Ziele mit Kernsatz, Gefahren."""
    if (k or {}).get("format") == 2:
        return _kurzfassung_neu(k)
    lk = lagekarte(k)
    br = lk.get("brett") or {}
    m = br.get("markt") or {}
    quelle = "O'Neil" if "ampel" in m else "alte Regel"      # Konferenzen vor dem 13.11.2026: eigene Faustregel
    m = m if "ampel" in m else (m.get("minervini") or {})
    pe = br.get("pendel") or {}
    tag = str(k.get("stand") or HEUTE())[:10]
    titel = f"Tagesbefehl {tag[8:10]}.{tag[5:7]}. · {lk.get('haltung') or 'ohne Haltung'}"
    zeilen = []
    if lk.get("lage_kurz"):
        zeilen.append(lk["lage_kurz"])
    teile = ([f"Markt {PUNKT.get(m.get('ampel'), '⚪')} {m.get('wort')} ({quelle})"] if m.get("wort") else []) \
        + ([f"Pendel {PUNKT.get(pe.get('ampel'), '⚪')} {pe.get('zone')}"] if pe.get("zone") else [])
    if teile:
        zeilen.append(" · ".join(teile))
    ds = br.get("datenstand") or {}
    if ds.get("ampel") and ds.get("ampel") != "grün":
        zeilen.append(f"⚠ Datenstand prüfen: {ds.get('text') or ''}".strip())
    pfeil = {"short": "↓"}
    for z in (lk.get("ziele") or [])[:6]:
        zeilen.append(f"{PUNKT.get(z.get('ampel'), '⚪')} {pfeil.get(z.get('teil'), '↑')} {z['titel']}: {z.get('kurz') or ''}".rstrip(": "))
    for g in (lk.get("gefahren") or [])[:3]:
        zeilen.append(f"⚠ {', '.join(g.get('titel') or []) or 'Gefahr'}: {g.get('kurz') or ''}".rstrip(": "))
    if not lk.get("ziele"):
        zeilen.append("Keine Angriffsziele heute.")
    return titel, "\n".join(zeilen)


_URTEIL_AMPEL = {"hält": "grün", "schwächt": "gelb", "kippt": "rot"}
_REAKTION_AMPEL = {"stärke": "grün", "neutral": "gelb", "schwäche": "rot"}


def _hinweise_neu(k):
    """Die Meldungen der Missionen (format 2) als [(Nr., Hinweis)] – für Akten je Titel und Nadeln."""
    mi = k.get("missionen") or {}
    b = k.get("befehl") or {}
    aus = []

    def h(nr, tk, ampel, text):
        aus.append((nr, {"titel": [tk] if isinstance(tk, str) else tk, "ampel": ampel, "text": text,
                         "von": MISSIONEN[nr][0], "datum": None}))
    for c in b.get("chancen") or []:
        h(8, c["titel"], "grün", f"Chance: {c.get('warum', '')} Tun: {c.get('tun', '')} Achte auf: {c.get('achte_auf', '')}")
    for a in b.get("anwaerter") or []:
        h(8, a.get("titel"), "gelb", f"Anwärter: {a.get('warum', '')} Warten auf: {a.get('warten_auf', '')}")
    for a in (mi.get("4") or {}).get("auftraege") or []:
        h(4, a["titel"], "grün", f"Auftrag: {a.get('these', '')} Auslöser: {a.get('ausloeser', '')} · ungültig, wenn "
                                 f"{a.get('ungueltig_wenn', '')}")
    for a in (mi.get("4") or {}).get("beobachten") or []:
        h(4, a.get("titel"), "gelb", f"Beobachten: {a.get('warten_auf', '')}")
    for a in (mi.get("4") or {}).get("verworfen") or []:
        h(4, a.get("titel"), "rot", f"Verworfen: {a.get('grund', '')}")
    for a in (mi.get("3") or {}).get("anwaerter") or []:
        h(3, a.get("titel"), "gelb", f"{a.get('these', '')} Warten auf: {a.get('warten_auf', '')} · widerlegt, wenn "
                                     f"{a.get('widerlegt_wenn', '')}")
    for a in (mi.get("2") or {}).get("titel") or []:
        q = " · ".join(x for x in (a.get("quelle"), a.get("datum")) if x)
        h(2, a.get("titel"), _REAKTION_AMPEL.get(a.get("reaktion"), "gelb"),
          f"Auslöser ({a.get('art')}, tragfähig: {a.get('tragfaehig')}): {a.get('ausloeser', '')}" + (f" · {q}" if q else ""))
    for e in (mi.get("5") or {}).get("einwaende") or []:
        h(5, e.get("titel"), _URTEIL_AMPEL.get(e.get("urteil"), "gelb"),
          f"Einwand ({e.get('urteil')}): {e.get('einwand', '')} Beleg: {e.get('beleg', '')}")
    for p in (mi.get("6") or {}).get("positionen") or []:
        h(6, p.get("titel"), "gelb", f"{p.get('anweisung')}: {p.get('grund', '')}" + (f" · Linie {p['linie']}" if p.get("linie") else ""))
    return aus


_GEMERKT = {}


def _letzte_gemerkt():
    """letzte() einmal je Datei und Änderungszeit (die Titelseiten des Schranks fragen je Titel)."""
    if not os.path.isdir(SPEICHER):
        return None
    namen = sorted((f for f in os.listdir(SPEICHER) if f[:4].isdigit() and f.endswith(".json")), reverse=True)
    if not namen:
        return None
    p = os.path.join(SPEICHER, namen[0])
    schl = (p, os.path.getmtime(p))
    if _GEMERKT.get("schl") != schl:
        _GEMERKT.update(schl=schl, k=letzte())
    return _GEMERKT["k"]


def satz_zu(tk):
    """Der Satz des Stabs zu einem Titel aus der jüngsten Konferenz (für das Kreislaufbild der Titelseite) oder None."""
    k = _letzte_gemerkt() or {}
    if k.get("format") != 2:
        return None
    tk = tk.upper()
    b = k.get("befehl") or {}
    mi = k.get("missionen") or {}
    tag = f'Stab {str(k.get("stand"))[8:10]}.{str(k.get("stand"))[5:7]}.: '
    for c in b.get("chancen") or []:
        if c.get("titel") == tk:
            return tag + f"Chance – {c.get('warum', '')} {c.get('tun', '')}".strip()
    for a in (mi.get("3") or {}).get("anwaerter") or []:
        if str(a.get("titel", "")).upper() == tk:
            return tag + f"Anwärter – {a.get('these', '')} Wir warten auf: {a.get('warten_auf', '')}"
    for a in (mi.get("4") or {}).get("beobachten") or []:
        if str(a.get("titel", "")).upper() == tk:
            return tag + f"beobachten – {a.get('warten_auf', '')}"
    for a in (mi.get("4") or {}).get("verworfen") or []:
        if str(a.get("titel", "")).upper() == tk:
            return tag + f"verworfen – {a.get('grund', '')}"
    return None


def _kurzfassung_neu(k):
    """Tagesbefehl (format 2) aufs Handy: Chancen zuerst, mit Phase in Worten; kein Verworfen."""
    b = k.get("befehl") or {}
    br = k.get("brett") or {}
    m = br.get("markt") or {}
    tag = str(k.get("stand") or HEUTE())[:10]
    titel = f"Tagesbefehl {tag[8:10]}.{tag[5:7]}. · {b.get('haltung') or 'ohne Haltung'}"
    zeilen = [b.get("anrede") or "Hey Micky,"]
    for c in (b.get("chancen") or [])[:AUFTRAEGE_MAX]:
        pf = "↓" if c.get("seite") == "short" else "↑"
        zeilen.append(f"🟢 {pf} {c['titel']} · {c.get('phase') or ''}: {c.get('warum') or ''}".replace(" · :", ":"))
    for a in (b.get("anwaerter") or [])[:3]:
        zeilen.append(f"◇ Anwärter {a.get('titel')}: {a.get('warten_auf') or a.get('warum') or ''}")
    if b.get("leitfrage"):
        zeilen.append(f"❓ {b['leitfrage']}")
    if m.get("wort"):
        zeilen.append(f"Markt {PUNKT.get(m.get('ampel'), '⚪')} {m.get('wort')} (O'Neil)")
    ds = br.get("datenstand") or {}
    if ds.get("ampel") and ds.get("ampel") != "grün":
        zeilen.append(f"⚠ Datenstand prüfen: {ds.get('text') or ''}".strip())
    return titel, "\n".join(zeilen)


def gescheitert(k):
    """Grund, wenn keine Mission (bzw. kein Stratege) gemeldet hat und kein Befehl steht – sonst None."""
    teile = (k.get("missionen") or k.get("meldungen") or {}).values()
    if teile and all(m.get("fehler") for m in teile):
        return next(iter(teile)).get("meldung") or "keine Meldung"
    if k.get("format") == 2 and (k.get("befehl") or {}).get("fehler"):
        return (k.get("befehl") or {}).get("anrede") or "kein Tagesbefehl"
    return None


def ergebnis_zeile(k):
    """Eine Zeile fürs Protokoll des Frühlaufs."""
    if k.get("format") == 2:
        b = k.get("befehl") or {}
        return (f"{len(b.get('chancen') or [])} Chancen · {len(b.get('anwaerter') or [])} Anwärter · Haltung "
                f"{b.get('haltung') or '—'} · {_zahl_de(k.get('kosten_usd') or 0)} $")
    return f"{sum(len(m.get('hinweise') or []) for m in (k.get('meldungen') or {}).values())} Hinweise"


def _zahl_de(x, n=2):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")
