"""Der Stab – MARAGA Investment (Konferenzraum, 09.11.2026).

Sechs Strategen (fünf plus Gegenspieler, seit 10.11.2026 nach dem Handwerk ihrer Meister) lesen nach dem Frühlauf die Daten der App und schreiben ihre Lagemeldung. Sie erklären und zeigen auf,
sie filtern nichts und erfinden keine Werte: jede Zahl, die sie nennen, steht in den Daten, die sie bekommen.
  2 Strömungs-Analyst   Rückenwind: Geld in Sektoren, Branchen, Themen, Stufenwechsel, Anführer und Verfolger
  3 Fundamental-Analyst Zahlen der Kandidaten, Termine ≤ 14 Tage, Reaktionen; Nachrichten per Web-Suche (begrenzt)
  4 Chart-Techniker     Setups der Kandidaten: Zone, Enge, Base, Ausbruch, Kaufzone, Fehlausbruch, Ermüdung
  5 Risikomanager       Depot, Stopps, Klumpen, Earnings im Depot, Barometer des Marktes
  1 Stratege            liest die vier Meldungen und schreibt den Tagesbefehl in fester Gliederung: Lage,
                        Volltreffer (dreifacher Rückenwind und Setup am Auslöser), Angriffsziele long, Ziele short, Gefahren
Jeder Hinweis trägt einen oder mehrere Ticker und, wenn er einen vergangenen Tag im Chart meint, das Datum – daraus
werden die Nadeln im Chart der Akte.

Umbau 10.11.2026 (Konferenz vom 10.11.: 3 von 4 Meldungen unlesbar, der Stab blind): festes Meldeformular über ein
Werkzeug der Schnittstelle statt freiem JSON-Text (keine kaputten Anführungszeichen mehr), zweiter Versuch, Rohantwort
im Protokoll; der Stab liest alle Reihen des Kartentischs (long, short), die Watchlist und den dreifachen Rückenwind –
seit 12.11.2026 nur einsatzbereite Setups (AKTEN_MAX, Depot immer); vollständige Akten (alle Kacheln, Pivot, Kaufzone, Stopp 1,5 ATR, Ausbruch,
Rückenwind, Zahlen); heutiges Datum, vergangene Termine aussortiert; Dienstanweisung mit den Setups und der Haltung
des Traders; feste Gefechtsfragen je Stratege; Sperre, wenn der Kartentisch veraltet ist.

Modell: Claude Sonnet 5.5 über die Anthropic-Schnittstelle (2 $ je Million Eingabe-, 10 $ je Million Ausgabe-Token,
Web-Suche 10 $ je 1.000). Kostenbuch je Monat in daten/konferenz/kosten.json; ab dem Deckel (DECKEL_USD) ruft der
Stab nicht mehr an bis zum Monatsende. Schlüssel: einstellungen/anthropic_schluessel.txt (nicht in Git), in der App
auf der Seite Konferenzraum eingetragen.
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

STRATEGEN = {
    1: ("Stratege", "Tagesbefehl"),
    2: ("Strömungs-Analyst", "Wohin fließt das Geld?"),
    3: ("Fundamental-Analyst", "Tragen die Zahlen?"),
    4: ("Chart-Techniker", "Wo steht der Angriff?"),
    5: ("Risikomanager", "Was kann uns treffen?"),
    6: ("Gegenspieler", "Warum kann es scheitern?"),
}

HEUTE = lambda: datetime.now().strftime("%Y-%m-%d")                    # noqa: E731
TISCH_MAX_TAGE = 4                                                     # älterer Kartentisch: Stab tagt nicht

DIENSTANWEISUNG = """Du bist Mitglied im Stab von MARAGA Investment, dem Handelsstab eines Swing-Traders. Du arbeitest im Invest Cockpit, seiner App.

HALTUNG DES TRADERS
- Er handelt long und short, Aktien und Knock-outs, nach einem eigenen System (seit 12.11.2026) mit sieben Setups: Base-Ausbruch (VCP), Flagge, Momentum-Ausbruch, Sprung (EP), Zahlen-Reaktion, Ermüdung (Short), Bärenflagge (Short). Die Regeln stammen von den Meistern (Base-Ausbruch: Minervini; Flagge, Momentum-Ausbruch, Sprung, Ermüdung: Kullamägi; dazu Bonde, Shannon, Morales/Kacher); nenne die Setups bei ihrem Namen, die Meister nur als Quelle einer Regel. O'Neil und Weinstein dienen nur als Zeichen.
- Sein Hauptsetup ist der Ausbruch aus einer Konsolidierungszone, wenn der Kurs danach wieder anzieht (Qullamaggie-Stil). Eine Konsolidierung darf auch eine tiefe Korrektur über 30 % sein. Ausbruchsvolumen über dem 50-Tage-Schnitt reicht ihm.
- Zweites Setup: die Flagge als Trendfortsetzung. Drittes: Short nach Überdehnung (Ermüdung). Dazu der Episodic Pivot.
- Seinen stärksten Vorteil sieht er in relativer Stärke und Geldfluss in Sektor und Branche: Er will Strömungen früher erkennen als die Masse, auch den Abfluss. Stärke in der Schwäche ist das, was ihn am meisten interessiert.
- Er lässt Gewinne laufen und zieht den Stopp nach; keine starren Kursziele.

BEGRIFFE DER APP
- Reihen des Kartentischs (ein Titel steht in genau einer): {reihen}
- Jeder Titel hat genau ein Setup (Feld „reihe“); „auch“ nennt weitere Setups, die er zeigt. „setup_minervini“ und „setup_kullamaegi“ sind die Rohbefunde der Regeln dahinter. „Base-Ausbruch · nur Muster“: Muster da, mehrere Regeln fehlen – kein Angriffsziel.
- Stufen des Rückenwinds: {stufen}
- Felder einer Gruppe (Sektor, Branche, Thema): Erstarkend (noch schwächer als der Markt, holt auf) · Führend (stärker, Stärke nimmt zu) · Schwächelnd (noch stärker, Stärke lässt nach) · Zurückfallend (schwächer, fällt zurück). Nicht verwechseln: „Ermüdet“ ist eine Stufe eines Titels, „Ermüdung nach Überdehnung“ ein Short-Setup. Zufluss × = Volumen an Kauf- gegen Abgabetagen der letzten 4 Wochen (ab 1,10 rein, unter 0,90 raus).
- Geld-Ampel: grün, wenn zwei von drei Gruppen (Sektor, Branche, Thema) vorne liegen und keine schwächelt.
- Dreifacher Rückenwind: Stufe Entsteht oder Läuft UND Geld-Ampel grün UND Zahlen-Ampel grün.
- Volltreffer: dreifacher Rückenwind UND der Titel steht in einer Reihe des Kartentischs (Setup).
- Kaufzone: Pivot bis +5 %. Stopp im Chart: 1,5 ATR unter dem Pivot (Short: 1,5 ATR über der Unterkante).
- Zahlen-Reaktion: der Einstieg („pivot“) ist der AVWAP ab dem Reaktionstag; „zahlen_reaktion“ nennt Tag, Reaktion
  in %, Volumen, Lage des Schlusses (1 = Hoch, 0 = Tief), Tage seitdem und ob Tief/Hoch und AVWAP gehalten wurden.

REGELN
1. Heute ist der {heute}. Termine vor heute sind vergangen.
2. Schreibe auf Deutsch, klar und knapp, ohne Floskeln. Jede Aussage nennt Ticker und Zahl aus den Daten. Allgemeine Sätze ohne Ticker sind nicht erlaubt, außer in der Lage.
3. Verwende nur Zahlen und Fakten aus den Daten, die du bekommst (bei Web-Suche: nur aus den Fundstellen, dann Quelle nennen). Erfinde nichts; fehlt etwas, sage es einmal.
4. Du erklärst und zeigst auf, du filterst nichts weg und gibst keine Kauf- oder Verkaufsbefehle – die Entscheidung trifft der Trader.
5. Ampeln statt Punktzahlen: grün = spricht dafür, gelb = beachten, rot = Warnung.
6. Ein Hinweis nennt im Feld titel jeden Ticker einzeln (Liste). Das Feld datum nur für einen vergangenen Tag im Chart (Ausbruch, Fehlausbruch, Sprung), sonst null.
7. Eine kurze Kriegs- oder Schlachtanalogie ist erlaubt, wenn sie die Lage schneller erklärt.
8. Gib deine Meldung ausschließlich über das Werkzeug ab.
9. Jeder arbeitet nach dem Handwerk seiner Meister (steht im Auftrag bzw. im Feldhandbuch). Bei Widerspruch gilt diese Rangordnung: zuerst die Haltung des Traders oben, dann der Hauptmeister, dann der Ergänzungsmeister. Nenne die Regel, nach der du urteilst, kurz beim Namen (z. B. „VCP: Kontraktionen nehmen ab“).
10. Eine Faktenwache prüft nach der Konferenz jeden Ticker und jede Zahl gegen die Daten und markiert, was sie nicht findet. Rechnest du selbst etwas aus, sage es („gerechnet: …“).
11. Sprichst du den Trader direkt an, dann mit „du“, nie mit „Sie“.
12. Die Daten enthalten „datenstand“: mit welchem Handelstag jeder Teil der App gerechnet hat. Haben die Teile
   verschiedene Tage, ist das eine Gefahr ersten Ranges – nenne sie zuerst, die Lage kann dann nicht stimmen.
13. Jede Akte trägt „feste_ampeln“: Setup, Einstieg, Geld, Zahlen, Termin. Die rechnet der Code nach den Regeln der Meister
   und festen Grenzen – sie sind gesetzt. Du prüfst sie nicht neu und färbst sie nicht um. Deine Ampel bewertet nur deine
   eigene Frage. Weichst du von einer festen Ampel ab, dann nur mit einem Grund, den der Code nicht kennt, und nenne ihn.
14. Im Feld „urteile“ gibst du je Titel, den du geprüft hast, genau ein Urteil: Ampel und Grund in höchstens 12 Wörtern,
   mit Zahl. Daraus entsteht die Konsens-Matrix des Konferenzraums – kurz, klar, ohne Floskeln."""

AUFTRAG = {
    2: "Du bist der Strömungs-Analyst. Beantworte in dieser Reihenfolge, jeweils mit Ticker bzw. Gruppe und Zahl: "
       "1) Welche Sektoren und Branchen haben das Feld gewechselt oder sind neu erstarkend, und fließt dort Geld rein "
       "(Zufluss ×)? 2) Dreifacher Rückenwind: welche Titel, welche sind seit der letzten Konferenz neu, welche haben ihn "
       "verloren (Listen dreifach_neu, dreifach_weg)? 3) Stärke in der Schwäche: wer zeigt ein RS-Hoch vor dem Kurs, welche "
       "Verfolger rücken am schnellsten nach? 4) Abfluss: wo geht Geld raus (Warnung für Halter, Gebiet für Shorts)?",
    3: "Du bist der Fundamental-Analyst. Beantworte, jeweils mit Ticker und Zahl: 1) Bei welchen Kandidaten tragen die "
       "Zahlen den Kurs (Zahlen-Ampel grün, Punkte)? Bei welchen läuft der Kurs ohne Fundament? 2) Welche Termine liegen in "
       "den nächsten 14 Tagen (Datum, in wie vielen Tagen)? 3) Wie reagierte der Kurs auf die letzten Zahlen? "
       "4) Nachrichten aus der Web-Suche zu höchstens fünf Volltreffern oder Spitzenkandidaten (Übernahmen, Prognosen, "
       "Ereignisse) – immer mit Quelle.",
    4: "Du bist der Chart-Techniker. Beantworte, jeweils mit Ticker und Zahl: 1) Wer steht am nächsten am Pivot "
       "(Abstand in %, Kaufzone bis …) – wo steht ein Angriff unmittelbar bevor? 2) Wer ist schon über die Kaufzone "
       "gelaufen? 3) Ausbrüche der letzten Tage: welche hielten, welche wurden zum Fehlausbruch (Tag als datum)? "
       "4) Short: wo zeigt sich Ermüdung nach Überdehnung? 5) Wie gut ist die Enge der besten Setups "
       "(Kontraktionen, Volumen)?",
    5: "Du bist der Risikomanager. Beantworte, jeweils mit Ticker und Zahl: 1) Depot: Stopps, Abstand, Earnings vor dem "
       "Stopp. Ist kein Depot oder Konto eingetragen, sage das einmal und prüfe stattdessen die Kandidaten am Auslöser: "
       "Stopp 1,5 ATR und Abstand in %. 2) Klumpen: stehen mehrere Volltreffer oder Spitzenkandidaten im selben Sektor, "
       "in derselben Branche oder im selben Thema? 3) Marktlage (Barometer, Markt: Indizes und Hochs/Tiefs): was heißt das "
       "für long und für short? 4) Welche Kandidaten am Auslöser haben Zahlen vor dem Stopp?",
}

# Feldhandbuch (10.11.2026): das Handwerk der Meister je Stratege, in der Fassung des Traders. Hauptmeister zuerst,
# Ergänzungsmeister nur für die genannte Frage. Ersetzt keine Regel der App – die Ampeln rechnet die App.
MEISTER = {
    1: "HANDWERK DEINER MEISTER – Feldherr. Hauptmeister: das Abwägen des Feldherrn – Wind, Stellung, Zahlen und Risiko "
       "zu einem Befehl verbinden, Prioritäten setzen, und „unklar“ sagen, wenn die Lage unklar ist. "
       "Ergänzung Jesse Livermore (How to Trade in Stocks, 1940; Reminiscences of a Stock Operator, 1923): Erst der "
       "Gesamtmarkt, dann die Gruppe, dann die Schwesteraktien, dann der einzelne Titel. Den Führern folgen – "
       "gehandelt wird, was sich am stärksten bewegt. Nicht vorwegnehmen: gehandelt wird erst, wenn der Kurs seinen "
       "Pivotal Point bestätigt; er kauft nie in einen Rückgang und shortet nie in eine Erholung. Erst tasten, dann "
       "nachlegen: mit einem Teil beginnen und nur aufstocken, wenn der erste Teil im Gewinn ist; nie einen Verlierer "
       "verbilligen. Das große Geld kommt vom Sitzenbleiben im großen Trend, nicht vom häufigen Handeln. Nicht jeden "
       "Tag handeln – ist die Lage unklar, wird gewartet. Die Zeit ist ein Faktor: Ein richtiger Ausbruch läuft prompt; "
       "bleibt das aus, ist das ein Gefahrenzeichen, und der Plan ändert sich. "
       "Ergänzung Stanley Druckenmiller (Reden und Interviews): Liquidität bewegt die Märkte stärker als die Gewinne "
       "des Augenblicks; der Markt preist die Zukunft ein (er schaut 12 bis 24 Monate voraus), die Gegenwart ist schon "
       "im Kurs. Kräfte bündeln: Stimmen Überzeugung, Strömung und Marktlage überein, das Gewicht auf die besten Ziele "
       "legen – zu kleines Gewicht auf die beste Idee ist der eigentliche Fehler; ist die Lage unklar, klein bleiben. "
       "Kapital erhalten und auf große Treffer warten; die Meinung sofort ändern, wenn die Lage sich dreht. "
       "Liquidität zeigen in den Daten nur Kreditaufschlag und Pendel – mehr nicht behaupten. "
       "Feste Gefechtsfrage (Denken zweiter Stufe): Was preist die Masse schon ein, und was übersieht sie? Das Pendel der "
       "App (Zone der Stimmung aus VIX, Kreditaufschlag, Breite) misst dazu die Temperatur; es dimmt oder verstärkt den "
       "Mut des Befehls, verbietet aber kein Setup.",
    2: "HANDWERK DEINER MEISTER – Hauptmeister William O'Neil: Die meisten großen Gewinner kommen aus den führenden "
       "Gruppen; gesucht sind die Nr. 1 und 2 der stärksten Branche. Stan Weinstein: Markt und Gruppe zählen mit – eine "
       "Gruppe im Aufwärtstrend (Phase 2) trägt, eine im Abwärtstrend (Phase 4) zieht jeden Titel mit; den Wechsel der "
       "Gruppe früh erkennen. Kristjan Kullamägi: Führer sind die stärksten Titel über 1, 3 und 6 Monate; dorthin, wo "
       "der Markt gerade jagt (Themen). Ergänzung John Murphy (Intermarket): Zinsen, Dollar, Rohstoffe und Aktien "
       "hängen zusammen; Geld rotiert im Konjunkturzyklus durch die Sektoren – nutze das, wo die Daten Gruppen und "
       "Felder zeigen, um Zufluss und Abfluss einzuordnen. Die Daten enthalten dafür das Wirtschaftswetter der App (Quad "
       "aus Wachstum und Inflation, mit Kupfer/Gold, Zyklisch gegen Basiskonsum, Öl, Rohstoffkorb, Breakeven-Inflation, "
       "amtlichen Zahlen und den typischen Führern des Quads): passt die Strömung der Gruppen zum Quad oder läuft sie "
       "dagegen? Ergänzung Jesse Livermore (Schwesteraktien): Ein Titel läuft selten allein – laufen die Schwestern "
       "derselben Gruppe mit, ist die Bewegung echt; bleiben sie zurück, ist das ein Warnzeichen. Nenne bei den "
       "stärksten Titeln, ob ihre Gruppe mitzieht.",
    3: "HANDWERK DEINER MEISTER – Hauptmeister William O'Neil (CAN SLIM): starke aktuelle Quartalsgewinne (C), "
       "wachsende Jahresgewinne (A), etwas Neues (N: Produkt, Management, neues Hoch), Führer statt Nachzügler (L), "
       "Unterstützung durch Institutionen (I), Marktrichtung (M). Mark Minervini: Beschleunigung – Gewinn und Umsatz "
       "wachsen von Quartal zu Quartal schneller, die Marge weitet sich, positive Überraschungen und angehobene "
       "Prognosen; die Reaktion des Kurses auf die Zahlen zeigt, ob die großen Käufer zustimmen. Ergänzung Pradeep "
       "Bonde (Stockbee, Urheber des Episodic Pivot; Quelle: sein Blog stockbee.blogspot.com): Ein EP braucht drei "
       "Dinge – Vernachlässigung (der Titel hat Monate oder Jahre wenig getan, wenig Volumen davor), einen Auslöser, der "
       "die Sicht der Wall Street auf das Geschäft ändert (am stärksten: dreistelliges Gewinn- oder Umsatzwachstum, die "
       "erste oder zweite große Überraschung; daneben Prognose, Aufträge, Zulassung, Politik, Managementwechsel), und "
       "eine Kurslücke von etwa 10 % oder mehr mit gewaltigem Volumen. Je vernachlässigter, desto größer der mögliche "
       "Lauf. Ein echter EP fällt nicht auf das Niveau vor der Lücke zurück. Viele laufen erst verzögert: nach Lücke, "
       "kurzem Lauf und Ruhephase folgt Tage bis Monate später der zweite Schub – dann ist ein Einstieg aus der "
       "Konsolidierung besser als das Hinterherlaufen. Ein bekannter, schon gelaufener Titel mit guten Zahlen ist "
       "kein EP im Sinne Bondes. Ergänzung Drift nach den Zahlen (Ball und Brown 1968, Bernard und Thomas 1989): "
       "Reagiert der Kurs klar auf die Zahlen, läuft er oft Wochen in dieselbe Richtung weiter, weil die Fonds ihre "
       "Positionen nicht an einem Tag umbauen – nach oben wie nach unten. Prüfe bei der Reihe Zahlen-Reaktion, ob "
       "die Zahlen die Reaktion tragen (Überraschung, Beschleunigung, Ausblick) oder ob sie nur eine Erleichterung war.",
    4: "HANDWERK DEINER MEISTER – Hauptmeister Mark Minervini: Trendvorlage (Kurs über steigenden Durchschnitten, nahe "
       "am Hoch, weit über dem Tief, starke RS); VCP – die Rücksetzer werden von links nach rechts enger, das Volumen "
       "trocknet aus, der Pivot ist die Stelle des geringsten Widerstands; gekauft wird am Pivot, nicht mehr als 5 % "
       "darüber. Ergänzung Jesse Livermore (Pivotal Points, How to Trade in Stocks): Es gibt Umkehrpunkte (neuer Trend "
       "nach Basis oder Klimax) und Fortsetzungspunkte (Ende einer Ruhepause im Trend; der wichtigste ist das neue Hoch). "
       "Nicht vorwegnehmen – erst der Durchbruch zählt, mit zunehmender Aktivität. Läuft der Kurs nach dem Durchbruch "
       "nicht prompt weiter oder schließt er zurück, ist das sein Gefahrenzeichen. Kristjan Kullamägi: Ausbruch nach einem großen Vorlauf aus einer engen Konsolidierung, die an den "
       "steigenden 10- und 20-Tage-Linien entlangläuft; Flagge als Fortsetzung; Episodic Pivot nach einem Ereignis. "
       "Ergänzung James Dalton (Mind over Markets) und Peter Steidlmayer (Market Profile, CBOT): Der Markt ist "
       "eine Auktion, die den fairen Wert sucht, und wechselt zwischen Balance und Ungleichgewicht. Balance: beide "
       "Seiten sind sich über den Wert einig, der Kurs pendelt in der Zone (bei dir die Konsolidierung), Wert wird "
       "angenommen. Ungleichgewicht: eine Seite drängt aggressiv und sucht neuen Wert (Ausbruch, Trend). Daltons "
       "Grundsatz: Der Preis zeigt die Gelegenheit an, die Zeit regelt sie, das Volumen misst den Erfolg. Ein "
       "Ausbruch ist angenommen, wenn der Kurs Zeit und Volumen außerhalb der alten Zone aufbaut; kehrt er schnell in "
       "die Zone zurück, ist er abgelehnt (gescheiterte Auktion, Fehlausbruch) – oft läuft der Kurs dann zur "
       "Gegenseite der Zone. Auf Tageskerzen übertragen: die Zone des Setups ist die Balance, der Pivot ihre Kante. "
       "Ergänzung Brian Shannon (Maximum Trading Gains with Anchored VWAP; alphatrends.net): Der AVWAP ab einem "
       "bedeutsamen Punkt – großes Hoch oder Tief, Zahlen- oder Nachrichten-Lücke, starke Wende; erst ankern, wenn "
       "der Punkt klar wichtig ist – zeigt den durchschnittlichen Einstand aller, die seitdem gekauft haben. Kurs über "
       "steigendem AVWAP: Käufer haben die Kontrolle; unter fallendem: Verkäufer; flacher AVWAP: Kampf. Ein Bruch "
       "dreht Unterstützung in Widerstand und umgekehrt. Der AVWAP ist eine Zone zum Beobachten, kein mechanisches "
       "Signal; schneidet der Kurs hindurch, nicht hoffen. Laufen AVWAPs von Hoch und Tief zusammen (Shannons "
       "„Pinch“), steht eine Entscheidung bevor. Die Akte enthält je Titel unter „avwap“ drei Anker (Hoch der "
       "letzten 52 Wochen, Tief der letzten 6 Monate, jüngster Ereignistag mit Lücke und Volumen) mit Wert, Abstand und "
       "Richtung sowie „pinch“, bei einer Zahlen-Reaktion zusätzlich den Anker „zahlentag“. Fehlt der Eintrag, sage "
       "nichts zum AVWAP. Zur Reihe Zahlen-Reaktion: Der Einstieg ist der ruhige Rücksetzer an den AVWAP ab dem "
       "Reaktionstag (Bondes „Delayed Reaction“) oder eine enge Flagge darüber; schließt der Kurs unter dem Tief des "
       "Reaktionstags oder unter diesem AVWAP, ist die Reaktion gescheitert (Short spiegelbildlich).",
    5: "HANDWERK DEINER MEISTER – Hauptmeister Mark Minervini: Verluste klein halten; der Stopp steht vor dem Kauf fest; "
       "nie einen Verlierer verbilligen; Verluste deutlich kleiner als Gewinne; das Risiko je Position ist ein kleiner "
       "Teil des Kontos; vor Zahlen nur mit Gewinnpolster oder kleiner; in schwachem Markt weniger und kleinere "
       "Positionen. Ergänzung Jesse Livermore (Gefahrenzeichen): die Ein-Tages-Umkehr – ein neues Hoch mit großem "
       "Volumen, das am selben Tag schwach schließt –, ein Ausbruch ohne prompte Nachfolge, und ein Führer, der bei "
       "hohem Volumen nicht mehr steigt; nie einen Verlierer verbilligen; der Stopp steht vor dem Einstieg. "
       "Ergänzung Gil Morales und Chris Kacher (O'Neil-Schüler; Short-Selling with the O'Neil Disciples, "
       "Trade Like an O'Neil Disciple, virtueofselfishinvesting.com): Short-Ziele sind frühere große Führer nach einem "
       "großen Lauf, aus denen die Institutionen aussteigen. Drei Muster: Kopf-Schulter-Top (rechte Schulter tiefer als "
       "die linke, besonders schwach bei fallender Nackenlinie), Late-Stage Failed Base (LSFB – späte, oft weite und "
       "lose Basis, Ausbruch scheitert; shortbar, wenn der Kurs unter den alten Ausbruchspunkt und die 50-Tage-Linie "
       "fällt) und Punchbowl of Death (Doppeltop nach steilem Lauf). Zeitpunkt: meist 8 bis 12 Wochen nach dem Gipfel, "
       "wenn das Top ausgebildet ist – die LSFB erlaubt den früheren Einstieg; die größten Brüche kommen im zweiten "
       "und dritten Abwärtsschub. Eröffnet wird in die Erholung an die 50- oder 20-Tage-Linie, nicht am Tief. Nur "
       "liquide Titel (mindestens 1 bis 2 Mio. Stück am Tag), enge Stopps (3 bis 5 %), Shorts vor allem in einem "
       "kippenden oder fallenden Markt; Gefahr des Short-Squeeze bei starken Erholungen.",
    6: "HANDWERK – Du bist der Gegenspieler (rotes Team). Lies die Lage absichtlich gegen den Strich, mit denselben "
       "Meistern: Minervini (Kontraktionen nicht eng, Volumen nicht ausgetrocknet, über der Kaufzone), Kullamägi (kein "
       "großer Vorlauf, Linien flach), O'Neil (Gruppe schwach, Zahlen tragen nicht), Dalton (Ausbruch ohne Annahme, "
       "Rückkehr in die Balance), Bonde (Lücke ohne echte Vernachlässigung, Rückfall unter das "
       "Niveau vor der Lücke), Livermore (Schwesteraktien ziehen nicht mit, keine prompte Nachfolge nach dem "
       "Pivotal Point, Ein-Tages-Umkehr), Shannon (Kurs unter dem AVWAP), Morales/Kacher (Topbildung, späte weite Basis, "
       "Squeeze-Gefahr bei Shorts), Marktlage gegen die Seite.",
}

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

AUFTRAG[6] = ("Du bist der Gegenspieler. Suche zu jedem Volltreffer und zu den wichtigsten Angriffszielen long und short "
              "aus den Meldungen den stärksten Grund, warum der Angriff scheitern kann – mit Ticker, Zahl und der Regel "
              "des Meisters. Ein Einwand je Titel, die schwersten zuerst. Ampel rot = schwerer Einwand, gelb = beachten. "
              "Findest du keinen ernsten Einwand, sage das (Ampel grün). Erfinde keine Schwächen.")

HINWEIS = {"type": "object", "properties": {
    "titel": {"type": "array", "items": {"type": "string"}, "description": "Ticker, jeder einzeln; leer, wenn kein Titel"},
    "datum": {"type": ["string", "null"], "description": "YYYY-MM-DD eines vergangenen Tages im Chart, sonst null"},
    "ampel": {"type": "string", "enum": ["grün", "gelb", "rot"]},
    "text": {"type": "string", "description": "1 bis 2 Sätze mit Zahl"}},
    "required": ["titel", "ampel", "text"]}
URTEIL = {"type": "object", "properties": {
    "titel": {"type": "string", "description": "genau ein Ticker"},
    "ampel": {"type": "string", "enum": ["grün", "gelb", "rot"], "description": "nur deine Frage, nicht das Setup"},
    "grund": {"type": "string", "description": "höchstens 12 Wörter, mit Zahl"}},
    "required": ["titel", "ampel", "grund"]}
MELDUNG = {"type": "object", "properties": {
    "meldung": {"type": "string", "description": "3 bis 6 Sätze Lage aus deiner Sicht, mit Tickern und Zahlen"},
    "hinweise": {"type": "array", "items": HINWEIS, "description": "höchstens 12, die wichtigsten zuerst"},
    "urteile": {"type": "array", "items": URTEIL, "description": "dein Urteil je geprüftem Titel (höchstens 20): "
                "Volltreffer, Angriffsziele, Depot zuerst"}},
    "required": ["meldung", "hinweise", "urteile"]}
ZIEL = {"type": "object", "properties": {**HINWEIS["properties"],
    "kurz": {"type": "string", "description": "Kernsatz in höchstens 12 Wörtern, mit Zahl"}},
    "required": ["titel", "ampel", "kurz", "text"]}
HALTUNGEN = ("angreifen", "klein tasten", "abwarten", "verteidigen")
BEFEHL = {"type": "object", "properties": {
    "haltung": {"type": "string", "enum": list(HALTUNGEN), "description": "die Haltung des Tages in einem Wort"},
    "lage_kurz": {"type": "string", "description": "die Lage in höchstens 8 Wörtern"},
    "lage": {"type": "string", "description": "die Lage in drei Sätzen"},
    "volltreffer": {"type": "array", "items": ZIEL, "description": "dreifacher Rückenwind und Setup am Auslöser"},
    "long": {"type": "array", "items": ZIEL, "description": "bis 5 Angriffsziele long, das beste zuerst"},
    "short": {"type": "array", "items": ZIEL, "description": "bis 3 Ziele short, das beste zuerst"},
    "gefahren": {"type": "array", "items": ZIEL, "description": "bis 3 Gefahren"},
    "einwaende": {"type": "array", "description": "Antwort auf die schwersten Einwände des Gegenspielers", "items": {
        "type": "object", "properties": {
            "titel": {"type": "array", "items": {"type": "string"}},
            "ampel": {"type": "string", "enum": ["grün", "gelb", "rot"],
                      "description": "wie schwer der Einwand nach deiner Abwägung bleibt"},
            "einwand": {"type": "string", "description": "der Einwand in einem Satz"},
            "antwort": {"type": "string", "description": "deine Abwägung in 1 bis 2 Sätzen mit Zahl"}},
        "required": ["titel", "ampel", "einwand", "antwort"]}}},
    "required": ["haltung", "lage_kurz", "lage", "volltreffer", "long", "short", "gefahren", "einwaende"]}
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
            if e.code in (429, 500, 529) and versuch < 2:     # überlastet oder Rate-Limit: warten und noch einmal
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
    t_ = (zahlen or {}).get("termin")
    if not t_ and kachel:
        teile = [kachel.get("wert"), kachel.get("text")] if isinstance(kachel, dict) else list(kachel)[1:3]
        for teil in teile:
            m_ = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", str(teil or ""))
            if m_:
                t_ = f"{m_.group(3)}-{m_.group(2)}-{m_.group(1)}"
                break
    d = str(t_)[:10] if t_ and re.match(r"\d{4}-\d{2}-\d{2}", str(t_)) else None
    return d if d and d >= (heute or HEUTE()) else None          # vergangene Termine zählen nicht


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


def avwaps(df, zahlentag=None):
    """Anchored VWAP nach Brian Shannon für die Akte des Stabs (10.11.2026), dieselben Anker wie der Wahlschalter im
    Chart (kern/avwap.py): Hoch der letzten 52 Wochen, Tief der letzten 6 Monate, jüngster Ereignistag. Je Anker:
    Datum, Wert, Abstand des Kurses in %, Richtung (über 5 Tage: steigt, fällt, flach); „pinch“, wenn Hoch- und
    Tief-AVWAP weniger als 3 % auseinander liegen."""
    import avwap
    a = avwap.anker(df)
    if zahlentag:                                        # Reaktionstag der Zahlen-Reaktion (12.11.2026)
        import pandas as pd
        a["zahlentag"] = pd.Timestamp(zahlentag)
    if not a:
        return None
    kurs = float(df["Close"].iloc[-1])
    namen = {"hoch": "hoch_52_wochen", "tief": "tief_6_monate", "ereignis": "ereignistag", "zahlentag": "zahlentag"}
    aus = {}
    for k, tag in a.items():
        av = avwap.reihe(df, tag)
        if len(av) < 6:                                  # Anker erst wenige Tage alt: noch keine Aussage
            aus[namen[k]] = {"ab": f"{tag:%Y-%m-%d}", "hinweis": "Anker erst wenige Tage alt – Kurs steht am "
                             + {"hoch": "Hoch", "tief": "Tief", "ereignis": "Ereignis", "zahlentag": "Reaktionstag"}[k]}
            continue
        w, vor = float(av.iloc[-1]), float(av.iloc[-6])
        r = (w / vor - 1) * 100 if vor else 0
        aus[namen[k]] = {"ab": f"{tag:%Y-%m-%d}", "wert": _zahl(w), "kurs_abstand_pct": _zahl((kurs / w - 1) * 100, 1),
                         "richtung": "steigt" if r > 0.3 else "fällt" if r < -0.3 else "flach"}
    h, t = aus.get("hoch_52_wochen"), aus.get("tief_6_monate")
    if h and t and h.get("wert") and t.get("wert"):
        aus["pinch"] = abs(h["wert"] / t["wert"] - 1) * 100 < avwap.PINCH_PCT
    return aus or None


class Aufklaerung(Exception):
    """Kartentisch fehlt oder ist veraltet – der Stab tagt nicht (keine Kosten für leere Antworten)."""


# ── Feste Ampeln (12.11.2026): Tatsachen färbt der Code nach festen Grenzen, nicht das Modell ──

FESTE_REGELN = (
    ("Setup", "grün = das Setup des Titels erfüllt alle seine Regeln · gelb = in einer Reihe des Kartentischs, aber "
              "nicht voll grün · grau = keine Reihe"),
    ("Einstieg", "Abstand zum Pivot (Short: zur Unterkante, gespiegelt): grün = in der Kaufzone (Pivot bis +5 %) · "
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
    d = c.get("abstand_zum_pivot_pct")
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
        aus["Termin"] = ("rot" if tage <= 7 else "gelb" if tage <= 14 else "grün", f"Zahlen in {tage} Tagen")
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
    """Das Lagebrett: Markt beider Systeme, Pendel, Datenstand – Tatsachen der App, so wie der Stab sie las."""
    m = lb.get("markt") or {}
    pe = lb.get("pendel") or {}
    ds = lb.get("datenstand") or {}
    return {"markt": {k: {"ampel": (m.get(k) or {}).get("ampel"), "wort": (m.get(k) or {}).get("wort")}
                      for k in ("minervini",)},
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
        if x.get("reihe") in ("k_ermuedung", "k_baerenflagge") or (x.get("reihe") == "zahlen" and x.get("zr_seite") == "short"):
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

    def termin_tage(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        return _tage((r.get("zahlen") or {}), (x.get("kacheln") or {}).get("Nächste Zahlen"))

    def klasse(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        voll = tk in drei and bool(x.get("reihe"))
        t_ = termin_tage(tk)
        rs = r.get("rang") or 0
        return (t_ is not None and t_ <= 7, not voll, not x.get("stern"), not geld_mit(tk),   # Watchlist zählt nicht
                rs if short(tk) else -rs)                     # (Micky 12.11.2026: neutral, die Stärke entscheidet)

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
        merkmale = ((["Volltreffer"] if tk in drei and x.get("reihe") else []) + ([("★ Short-Zone" if short(tk) else "★ Kaufzone")] if x.get("stern") else [])
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
                av = avwaps(df, (x.get("zr") or {}).get("tag") if x.get("reihe") == "zahlen" else None)
        except Exception:  # noqa: BLE001
            pass
        abst = x.get("abstand_vz")                      # mit Vorzeichen; „abstand“ ist nur der Betrag (10.11.2026)
        if kurs and abst is not None:
            pivot = kurs / (1 + float(abst) / 100)
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
                "dreifacher_rueckenwind": tk in drei, "volltreffer": tk in drei and bool(x.get("reihe")),
                "seite": _seite(x), "setup_minervini": x.get("m"), "setup_kullamaegi": x.get("k"),
                "luecken": x.get("luecken"), "wertzone": x.get("zustand"),
                "kurs": _zahl(kurs), "pivot": _zahl(pivot), "abstand_zum_pivot_pct": _zahl(abst, 1),
                "kaufzone_bis": _zahl(pivot * 1.05) if pivot else None, "atr": _zahl(a),
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
        import markt_systeme
        b = tisch.get("barometer") or {}
        markt = {"minervini": markt_systeme.minervini(b.get("hochs"), b.get("tiefs"))}   # eine Ampel (Micky 12.11.2026)
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
            {a: c.get(a) for a in ("titel", "reihe", "seite", "volltreffer", "setup_gruen", "setup_minervini", "setup_kullamaegi",
                               "luecken", "wertzone", "kurs", "pivot", "abstand_zum_pivot_pct", "kaufzone_bis", "atr",
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
        text_ = " ".join(str(h.get(f) or "") for f in ("kurz", "text", "einwand", "antwort", "grund"))
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


def lagebuch(vorher, nr, lb):
    """Was aus den Hinweisen der letzten Konferenz geworden ist (10.11.2026): je Titel Hinweis von damals, Kurs damals
    und heute, Reihe und Ausbruch heute. Beobachtung zum Lernen am Gelände, kein Urteil über Setups."""
    if not vorher:
        return None
    if nr == 1:
        b = vorher.get("befehl") or {}
        alte = [h for teil, _ in BEFEHL_TEILE for h in b.get(teil) or []]
    else:
        alte = ((vorher.get("meldungen") or {}).get(str(nr)) or {}).get("hinweise") or []
    kand = {c["titel"]: c for c in lb["kandidaten"]}
    kurse_alt = vorher.get("kurse") or {}
    eintraege = []
    for h in alte:
        for tk in _ticker(h.get("titel"), None)[:3]:
            c = kand.get(tk) or {}
            k_neu = c.get("kurs") or _zahl(_kurs(tk))
            k_alt = kurse_alt.get(tk)
            eintraege.append({"titel": tk, "ampel_damals": h.get("ampel"), "damals": str(h.get("text") or "")[:220],
                              "kurs_damals": k_alt, "kurs_heute": k_neu,
                              "veraenderung_pct": _zahl((k_neu / k_alt - 1) * 100, 1) if k_neu and k_alt else None,
                              "reihe_heute": c.get("reihe"), "abstand_zum_pivot_pct": c.get("abstand_zum_pivot_pct"),
                              "ausbruch_heute": c.get("ausbruch")})
        if len(eintraege) >= 15:
            break
    return {"konferenz_vom": vorher.get("stand"), "eintraege": eintraege} if eintraege else None


LAGEBUCH_TEXT = ("\n\nLagebuch – deine Hinweise der letzten Konferenz und was daraus wurde (Beobachtung, kein Urteil "
                 "über Setups). Sage zu Beginn deiner Meldung in einem Satz, was sich bestätigt hat und was nicht:\n")


def _bekannt(lb):
    aus = {c["titel"] for c in lb["kandidaten"]} | set(lb.get("dreifach") or [])
    try:
        import kartentisch
        import rueckenwind
        aus |= set((rueckenwind.laden() or {}).get("titel") or {}) | set((kartentisch.laden() or {}).get("titel") or {})
    except Exception:  # noqa: BLE001
        pass
    return aus


def konferenz(melden=lambda text: None):
    """Alle Strategen; speichert daten/konferenz/<datum>.json und gibt das Ergebnis zurück. `melden` schreibt jeden
    Schritt ins Protokoll (Knopf-Lauf), damit ein Hänger sichtbar wird. Ist der Kartentisch veraltet, tagt der Stab
    nicht (Aufklaerung). Seit 10.11.2026 (Elite-Stab): Feldhandbuch der Meister je Stratege, Lagebuch, Gegenspieler,
    Antwort des Strategen auf die Einwände, Faktenwache."""
    melden(f"{datetime.now():%H:%M:%S} Lagebild wird gelesen …")
    lb = lagebild()
    voll = [c["titel"] for c in lb["kandidaten"] if c["volltreffer"]]
    melden(f"{datetime.now():%H:%M:%S} Lagebild: {len(lb['kandidaten'])} Kandidaten ({len(voll)} Volltreffer), "
           f"{len(lb['dreifach'])} mit dreifachem Rückenwind, {len(lb['gruppen'])} Gruppen")
    heute = lb["heute"]
    system = dienstanweisung()
    bekannt = _bekannt(lb)
    vorher = _vorige(heute)
    erg = {"stand": heute, "zeit": f"{datetime.now():%d.%m.%Y %H:%M}", "modell": MODELL, "meldungen": {},
           "dreifach": lb["dreifach"], "kurse": {c["titel"]: c["kurs"] for c in lb["kandidaten"] if c.get("kurs")},
           "tafel": tafel(lb), "brett": brett(lb)}
    kurse_ = {c["titel"]: c.get("kurs") for c in lb["kandidaten"]}
    erg["bilanz"] = bilanz(vorher, lambda tk: kurse_.get(tk) or _zahl(_kurs(tk)))

    def melden_lassen(nr, inhalt, quelle):
        name = STRATEGEN[nr][0]
        try:
            m = _formular(system, inhalt, "melden", MELDUNG)
            faktenwache((m.get("hinweise") or []) + (m.get("urteile") or []), quelle, bekannt)
        except Deckel:
            raise
        except Unlesbar as e:
            m = {"meldung": f"Keine Meldung: {e}", "hinweise": [], "fehler": True, "roh": e.roh}
            melden(f"   Rohantwort: {e.roh}")
        except Exception as e:  # noqa: BLE001 – eine Meldung fehlt, die anderen laufen weiter
            m = {"meldung": f"Keine Meldung: {e}", "hinweise": [], "fehler": True}
        wache = sum(1 for h in m.get("hinweise") or [] if h.get("wache"))
        melden(f"{datetime.now():%H:%M:%S} {name}: {'Fehler – ' + m['meldung'] if m.get('fehler') else 'fertig'}"
               + (f" · Faktenwache: {wache} Hinweis(e) markiert" if wache else ""))
        erg["meldungen"][str(nr)] = {"name": name, **m}

    for nr in (2, 3, 4, 5):
        melden(f"{datetime.now():%H:%M:%S} {STRATEGEN[nr][0]} liest …")
        daten_ = json.dumps(_ausschnitt(lb, nr), ensure_ascii=False, default=str)
        vorlauf = ""
        if nr == 3:                                      # erst die Web-Suche als Notizen, dann das Formular
            try:
                ziele = list(dict.fromkeys(voll + [c["titel"] for c in lb["kandidaten"]]))[:5]
                notizen = _anfrage(system, "Suche aktuelle Nachrichten (Übernahmen, Prognosen, Ereignisse) zu diesen "
                                   f"Titeln: {', '.join(ziele)}. Schreibe knappe Notizen je Titel mit Quelle (URL). "
                                   "Nichts erfinden.", 6000, SUCHEN_NACHT)
            except Deckel:
                raise
            except Exception as e:  # noqa: BLE001
                notizen = f"Web-Suche fehlgeschlagen: {e}"
            melden(f"   Web-Suche: {len(notizen or '')} Zeichen Notizen (Ende: {_LETZTER['stop']})")
            vorlauf = "\n\nNotizen aus der Web-Suche:\n" + (notizen or "keine Fundstellen")
        buch = lagebuch(vorher, nr, lb)
        buch_ = LAGEBUCH_TEXT + json.dumps(buch, ensure_ascii=False, default=str) if buch else ""
        melden_lassen(nr, f"{AUFTRAG[nr]}\n\n{MEISTER[nr]}\n\nDaten der App (Stand des Nachtlaufs):\n{daten_}"
                      f"{vorlauf}{buch_}", daten_ + vorlauf + buch_)

    def ohne_roh(m):
        return {k_: v for k_, v in m.items() if k_ not in ("roh", "wache")}

    # Gegenspieler: dieselben Akten (Chart-Ausschnitt) der Titel, die in den Meldungen vorkommen, plus Marktlage
    genannt = set(voll)
    for m in erg["meldungen"].values():
        for h in m.get("hinweise") or []:
            genannt |= set(_ticker(h.get("titel"), bekannt))
    chart = _ausschnitt(lb, 4)
    gegen = {"heute": heute, "barometer": lb["barometer"], "markt": lb["markt"], "pendel": lb.get("pendel"),
             "akten": [c for c in chart["kandidaten"] if c["titel"] in genannt],
             "meldungen": {nr: ohne_roh(m) for nr, m in erg["meldungen"].items()}}
    gegen_ = json.dumps(gegen, ensure_ascii=False, default=str)
    melden(f"{datetime.now():%H:%M:%S} Gegenspieler prüft {len(gegen['akten'])} Akten …")
    melden_lassen(6, f"{AUFTRAG[6]}\n\n{MEISTER[6]}\n\nDaten:\n{gegen_}", gegen_)

    befehl_daten = {"heute": heute, "datenstand": lb.get("datenstand"), "barometer": lb["barometer"], "markt": lb["markt"], "pendel": lb.get("pendel"),
                    "wirtschaftswetter": lb.get("wirtschaftswetter"), "volltreffer": [
        {a: c.get(a) for a in ("titel", "reihe", "seite", "abstand_zum_pivot_pct", "kaufzone_bis", "stopp_1_5_atr",
                               "feste_ampeln")}
        | {"stufe": (c["rueckenwind"] or {}).get("stufe")} for c in lb["kandidaten"] if c["volltreffer"]],
        "meldungen": {nr: ohne_roh(m) for nr, m in erg["meldungen"].items() if nr != "6"},
        "einwaende_gegenspieler": ohne_roh(erg["meldungen"].get("6") or {})}
    buch = lagebuch(vorher, 1, lb)
    befehl_ = json.dumps(befehl_daten, ensure_ascii=False, default=str)
    buch_ = LAGEBUCH_TEXT.replace("deiner Meldung", "der Lage") + json.dumps(buch, ensure_ascii=False, default=str) \
        if buch else ""
    inhalt = ("Du bist der Stratege und führst den Stab. Lies die vier Lagemeldungen und die Einwände des Gegenspielers "
              "und schreibe den Tagesbefehl in fester Gliederung: haltung (ein Wort: angreifen, klein tasten, abwarten "
              "oder verteidigen); lage_kurz (höchstens 8 Wörter, das Erste, was der Trader liest); "
              "lage (drei Sätze: Marktlage, wo die Strömung hingeht, "
              "was das für heute heißt); volltreffer (alle Titel mit dreifachem Rückenwind und Setup am Auslöser – die "
              "Liste steht in den Daten; je Titel Setup, Abstand zum Pivot, Stufe); long (bis 5 Angriffsziele); short "
              "(bis 3 Ziele); gefahren (bis 3); einwaende (die schwersten Einwände des Gegenspielers, bis 5: halte der "
              "Einwand stand oder nicht, und warum – mit Zahl). Wiederhole nicht einfach eine Meldung, sondern wäge ab "
              "und verbinde: Wind, Stellung, Zahlen, Risiko. Benenne Widersprüche zwischen den Strategen ausdrücklich "
              "(z. B. Chart grün, Fundament rot bei einem Ticker). Jeder Hinweis mit Ticker und Zahl. Jedes Ziel und "
              "jede Gefahr trägt einen Kernsatz „kurz“ (höchstens 12 Wörter) – er steht in der Zielliste; der Text "
              "darf länger sein. Die festen Ampeln der Akten sind gesetzt (Regel 13).\n\n"
              f"{MEISTER[1]}\n\n{befehl_}{buch_}")
    melden(f"{datetime.now():%H:%M:%S} Stratege schreibt den Tagesbefehl …")
    try:
        erg["befehl"] = _formular(system, inhalt, "tagesbefehl", BEFEHL, 12000)
        b = erg["befehl"]
        faktenwache([h for teil, _ in BEFEHL_TEILE for h in b.get(teil) or []] + list(b.get("einwaende") or []),
                    befehl_ + gegen_ + buch_ + json.dumps(_ausschnitt(lb, 4), ensure_ascii=False, default=str),
                    bekannt)
    except Deckel:
        raise
    except Exception as e:  # noqa: BLE001
        erg["befehl"] = {"haltung": None, "lage_kurz": "kein Tagesbefehl", "lage": f"Kein Tagesbefehl: {e}", "volltreffer": [], "long": [], "short": [], "gefahren": [],
                         "einwaende": []}
    json_schreiben(_pfad(f"{heute}.json"), erg, ensure_ascii=False)
    melden(f"{datetime.now():%H:%M:%S} fertig · Monat {kosten()['usd']:.2f} $")
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
    """Alle Hinweise einer Konferenz als [(Nr. des Strategen, Hinweis)], Tagesbefehl zuerst (alt und neu)."""
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
    handbuch = "\n\n".join(f"{STRATEGEN[nr][0]}: {MEISTER[nr]}" for nr in (1, 2, 3, 4, 5, 6))
    inhalt = ("Der Trader fragt den Stab. Antworte als Stab (der Stratege führt, die Fachleute ergänzen) in höchstens "
              "18 Sätzen, auf Deutsch, nur mit Fakten aus den Daten oder aus Web-Fundstellen (dann Quelle nennen). "
              "Jeder Fachmann urteilt nach dem Handwerk seiner Meister aus dem Feldhandbuch unten und nennt die Regel "
              "beim Namen. Nennt die Frage nur bestimmte Meister, antworte zuerst mit diesen; danach sagt jeder weitere "
              "Meister, dessen Regel für diesen Titel oder diese Lage zählt, in einem Satz, was er sieht (Abschnitt "
              "„Die übrigen Meister“). Meister ohne Bezug (z. B. Short-Meister bei einem Long-Titel) lässt du weg. "
              "Antworte als Klartext, ohne Werkzeug.\n\nFeldhandbuch des Stabs:\n" + handbuch
              + "\n\nFrage: " + text + "\n\nDaten der App:\n" + json.dumps(kontext, ensure_ascii=False, default=str))
    antwort = _anfrage(dienstanweisung().replace("8. Gib deine Meldung ausschließlich über das Werkzeug ab.", ""),
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
