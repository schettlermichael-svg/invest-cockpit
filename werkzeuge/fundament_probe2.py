"""Probe 2: Umsatz- und Gewinnhistorie über 8+ Quartale (SEC EDGAR) und Schätzungstrend (Yahoo).

Aufruf im Ordner InvestCockpit:
    python3 werkzeuge/fundament_probe2.py
Schreibt werkzeuge/fundament_probe2.txt.
"""
import json
import os
import urllib.request

import pandas as pd
import yfinance as yf

TITEL = ["NVDA", "HWM", "AXON"]
AUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fundament_probe2.txt")
# Die SEC verlangt einen Absender im User-Agent (Name + Kontakt). Ohne echte Adresse kann sie sperren.
KOPF = {"User-Agent": "InvestCockpit privat investcockpit@example.com"}
pd.set_option("display.width", 200)


def holen(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=KOPF), timeout=30) as r:
        return json.loads(r.read().decode())


def quartale(fakten, konzept, einheit):
    """Nur echte Quartalswerte (Zeitraum ca. 3 Monate), je Periodenende der zuletzt gemeldete."""
    try:
        werte = fakten["facts"]["us-gaap"][konzept]["units"][einheit]
    except KeyError:
        return None
    df = pd.DataFrame(werte)
    if "start" not in df:
        return None
    tage = (pd.to_datetime(df["end"]) - pd.to_datetime(df["start"])).dt.days
    df = df[(tage > 80) & (tage < 100)].sort_values("filed").drop_duplicates("end", keep="last")
    return df.set_index("end")["val"].sort_index().tail(12)


with open(AUS, "w", encoding="utf-8") as f:
    try:
        liste = holen("https://www.sec.gov/files/company_tickers.json")
        cik = {v["ticker"]: v["cik_str"] for v in liste.values()}
        f.write("SEC: Tickerliste geladen\n")
    except Exception as e:
        cik = {}
        f.write(f"SEC FEHLER Tickerliste: {e}\n")
    for tk in TITEL:
        f.write(f"\n===== {tk} =====\n")
        if tk in cik:
            try:
                fakten = holen(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik[tk]:010d}.json")
                for konzept, einheit in [("RevenueFromContractWithCustomerExcludingAssessedTax", "USD"),
                                         ("Revenues", "USD"), ("NetIncomeLoss", "USD"),
                                         ("EarningsPerShareDiluted", "USD/shares")]:
                    q = quartale(fakten, konzept, einheit)
                    f.write(f"-- SEC {konzept}: {'fehlt' if q is None or q.empty else ''}\n")
                    if q is not None and not q.empty:
                        f.write(q.to_string() + "\n")
            except Exception as e:
                f.write(f"-- SEC FEHLER: {e}\n")
        t = yf.Ticker(tk)
        for name in ("eps_trend", "eps_revisions", "earnings_estimate", "revenue_estimate"):
            try:
                f.write(f"-- Yahoo {name}\n{getattr(t, name).to_string()}\n")
            except Exception as e:
                f.write(f"-- Yahoo {name} FEHLER: {e}\n")
        try:
            a = t.income_stmt
            z = [x for x in ("Diluted EPS", "Total Revenue", "Net Income") if x in a.index]
            f.write("-- Yahoo Jahreszahlen\n" + a.loc[z].to_string() + "\n")
        except Exception as e:
            f.write(f"-- Yahoo Jahreszahlen FEHLER: {e}\n")
        print(f"✓ {tk}", flush=True)
print(f"Fertig: {AUS}")
