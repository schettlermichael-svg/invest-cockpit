"""Maße der App: Einheiten und Standardlängen, die mehrere Regeln teilen (Generalinventur 15.11.2026).

Eine Quelle: jede Regel holt sie hier (from masse import …), keine zweite Zahl im Code. Die Regeln selbst (Schwellen,
Grenzen der Meister) stehen bei ihren Modulen.
"""
WOCHE = 5                  # Handelstage je Woche
MONAT_TAGE = 21            # Handelstage je Monat (4 Wochen)
JAHR_TAGE = 252            # Handelstage je Jahr (52 Wochen)
JAHR_WOCHEN = 52           # Wochen je Jahr
QUARTALE_JAHR = 4          # Quartale je Jahr (Vorjahresquartal, Summe der letzten 4 Quartale)
VORJAHR_ZURUECK = 5        # Quartalsreihe: der 5. Wert zurück = Vorjahresquartal
ZWEI_JAHRE_ZURUECK = 9     # Quartalsreihe: der 9. Wert zurück = vor zwei Jahren
GD200_TAGE = 200           # GD200
ATR_N = 14                 # ATR über 14 Tage (die eine ATR: atr.reihe)
VOL_TAGE = 50              # Volumen gegen den Schnitt der 50 Tage
VOL_MIN_TAGE = 20          # Volumen-Schnitt erst ab 20 Tagen Daten
LAGE_MITTE = 0.5           # Lage des Schlusses in der Tagesspanne: Mitte (ohne Spanne gilt die Mitte)
P_ABWAERTS = 4             # Phase 4 (Weinstein: Abwärts)
DATUM = 10                 # Länge eines Datums JJJJ-MM-TT
JAHR_ZIFFERN = 4           # Dateiname beginnt mit dem Jahr (JJJJ)
ZEILENUMBRUCH = 10         # Zeichen 10 = Zeilenumbruch
