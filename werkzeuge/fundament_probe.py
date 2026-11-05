"""Probe: Welche Gewinnzahlen liefert Yahoo (yfinance) für die Fundament-Ampeln?

Aufruf im Ordner InvestCockpit:
    python3 werkzeuge/fundament_probe.py
Schreibt werkzeuge/fundament_probe.txt – Claude liest die Datei und gleicht sie mit TradingView ab.
"""
import os
import sys

import pandas as pd
import yfinance as yf

TITEL = ["NVDA", "HWM", "LLY", "AXON", "CRWD"]
AUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fundament_probe.txt")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

with open(AUS, "w", encoding="utf-8") as f:
    f.write(f"yfinance {yf.__version__}\n")
    for tk in TITEL:
        t = yf.Ticker(tk)
        f.write(f"\n===== {tk} =====\n")
        try:
            ed = t.get_earnings_dates(limit=16)
            f.write("-- get_earnings_dates (bereinigter Gewinn je Aktie, Schätzung, Überraschung)\n")
            f.write(ed.to_string() + "\n")
        except Exception as e:
            f.write(f"-- get_earnings_dates FEHLER: {e}\n")
        try:
            q = t.quarterly_income_stmt
            zeilen = [z for z in ("Diluted EPS", "Basic EPS", "Total Revenue", "Net Income") if z in q.index]
            f.write("-- quarterly_income_stmt (GAAP)\n" + q.loc[zeilen].to_string() + "\n")
        except Exception as e:
            f.write(f"-- quarterly_income_stmt FEHLER: {e}\n")
        try:
            eh = t.earnings_history
            f.write("-- earnings_history\n" + eh.to_string() + "\n")
        except Exception as e:
            f.write(f"-- earnings_history FEHLER: {e}\n")
        print(f"✓ {tk}")
        sys.stdout.flush()
print(f"Fertig: {AUS}")
