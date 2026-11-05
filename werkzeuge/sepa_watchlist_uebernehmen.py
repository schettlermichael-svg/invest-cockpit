"""Einmalig: die gespeicherte Watchlist des alten SEPA-Scanners (~/.sepa_scanner_watchlist.txt) als Liste
„SEPA-Scanner“ in die Watchlists des Cockpits übernehmen (Doppelte einmal).
Aufruf im Ordner InvestCockpit:  python3 werkzeuge/sepa_watchlist_uebernehmen.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kern"))
import watchlists  # noqa: E402

pfad = os.path.expanduser("~/.sepa_scanner_watchlist.txt")
if not os.path.exists(pfad):
    print("Keine gespeicherte Watchlist des SEPA-Scanners gefunden.")
else:
    n = watchlists.einfuegen(open(pfad, encoding="utf-8").read(), "SEPA-Scanner")
    print(f"✓ {n} Titel in die Liste „SEPA-Scanner“ übernommen ({len(watchlists.laden().get('SEPA-Scanner', []))} insgesamt)")
