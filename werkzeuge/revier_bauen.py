"""Baut das Revier: die US-Aktien, die die App durchsucht (Konzept, Schritt 3).

Regeln: Börsenwert ab 1 Mrd. $, Kurs ab 10 $, gehandelter Wert im Schnitt der letzten 50 Tage
ab 20 Mio. $ je Tag; nur Stammaktien und ADRs (keine Vorzugsaktien, Optionsscheine, Units).
Quellen: Liste aller US-Aktien vom NASDAQ-Screener (Börsenwert, Kurs, Sektor, Branche), Umsatz der
letzten 50 Handelstage von Massive (eine Anfrage je Tag für alle Aktien, siehe kern/massive.py). Sektor und Branche nimmt das Skript von Yahoo, wo der Steckbrief schon
gespeichert ist (wie auf der Titelseite), sonst vom NASDAQ-Screener.
Yahoo wird dafür nicht mehr gefragt: 2.000 Einzelabrufe führten zu Sperren (Fehler 429).
Ergebnis: einstellungen/revier.csv (Ticker, Name, Sektor, Branche, Sektor-ETF, Börsenwert, Umsatz).

Aufruf im Ordner InvestCockpit:  python3 werkzeuge/revier_bauen.py      (beim ersten Mal etwa 11 Minuten, danach Sekunden: die Tage bleiben gespeichert)
"""
import json
import os
import re
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import daten        # noqa: E402
import marktdaten   # noqa: E402
import massive      # noqa: E402
import sektoren     # noqa: E402

ZIEL = os.path.join(HIER, "..", "einstellungen", "revier.csv")
BOERSENWERT, KURS, UMSATZ = 1e9, 10.0, 20e6
# Sektoren des NASDAQ-Screeners → Sektor-ETF („Miscellaneous“ bleibt ohne Zuordnung)
NASDAQ_ETF = {"Technology": "XLK", "Telecommunications": "XLC", "Health Care": "XLV", "Finance": "XLF",
              "Real Estate": "XLRE", "Consumer Discretionary": "XLY", "Consumer Staples": "XLP",
              "Industrials": "XLI", "Basic Materials": "XLB", "Energy": "XLE", "Utilities": "XLU"}
AUSSCHLUSS = re.compile(r"preferred|warrant|\bunits?\b|\bright\b|\brights\b|notes due|debenture|depositary shares.*series",
                        re.IGNORECASE)


GATTUNG = r"\b(Class [A-Z]|Series [A-Z])\b|Common Stock|Capital Stock|Common Shares|Ordinary Shares"


def nur_eine_gattung(revier):
    """Eine Firma mit mehreren Aktiengattungen (GOOGL/GOOG, BRK-B/BRK-A, FOXA/FOX …) nur einmal führen –
    die meistgehandelte Gattung bleibt. Sonst zählt die Firma in Sektor-Breite und Rudel doppelt."""
    firma = (revier["name"].str.replace(GATTUNG, "", regex=True)
             .str.replace(r"\s+", " ", regex=True).str.strip().str.lower())
    doppelt = revier[firma.duplicated(keep="first")]          # nach Umsatz sortiert: die erste bleibt
    if len(doppelt):
        print(f"    zweite Aktiengattung entfernt: {', '.join(doppelt['ticker'])}", flush=True)
    return revier[~firma.duplicated(keep="first")]


def zahl(text):
    try:
        return float(str(text).replace("$", "").replace(",", ""))
    except ValueError:
        return float("nan")


def main():
    start = time.time()
    print("1/4 Liste aller US-Aktien vom NASDAQ-Screener …", flush=True)
    roh = json.loads(marktdaten._curl("https://api.nasdaq.com/api/screener/stocks?tableonly=true&download=true"))
    liste = pd.DataFrame(roh["data"]["rows"])
    liste["kurs"] = liste["lastsale"].map(zahl)
    liste["wert"] = liste["marketCap"].map(zahl)
    liste["ticker"] = liste["symbol"].str.strip().str.replace("/", "-", regex=False)
    gut = liste[(liste["wert"] >= BOERSENWERT) & (liste["kurs"] >= KURS)
                & liste["ticker"].str.fullmatch(r"[A-Z]{1,5}(-[A-Z])?")
                & ~liste["name"].fillna("").str.contains(AUSSCHLUSS)]
    print(f"    {len(liste)} Titel gesamt, {len(gut)} mit Börsenwert ab 1 Mrd. und Kurs ab 10 $", flush=True)

    print("2/4 Umsatz der letzten 50 Handelstage von Massive (1 Anfrage je Tag, 5 pro Minute) …", flush=True)
    tage = massive.letzte_tage(50, melden=lambda k, n, t: print(f"    {k} von {n} ({t:%d.%m.%Y})", flush=True))
    alle = pd.concat([df.assign(Datum=t) for t, df in tage])
    alle["Ticker"] = alle["Ticker"].str.replace(".", "-", regex=False)   # BRK.B → BRK-B wie bei NASDAQ/Yahoo
    alle["wert"] = alle["Close"] * alle["Volume"]
    zaehl = alle.groupby("Ticker")["wert"].agg(["mean", "count"])
    umsatz = zaehl.loc[zaehl["count"] >= 40, "mean"]          # mindestens 40 der 50 Tage gehandelt
    gut = gut.assign(umsatz=gut["ticker"].map(umsatz))
    fehlen = gut["umsatz"].isna().sum()
    if fehlen:
        print(f"    für {fehlen} Titel keine 40 Handelstage bei Massive (nicht aufgenommen)", flush=True)
    gut = gut[gut["umsatz"] >= UMSATZ]
    print(f"    {len(gut)} mit mindestens 20 Mio. $ Umsatz je Tag", flush=True)

    print("3/4 Sektor und Branche …", flush=True)
    sb = {tk: daten.steckbrief_gespeichert(tk) for tk in gut["ticker"]}
    print(f"    {sum(1 for v in sb.values() if v)} von Yahoo (gespeichert), übrige vom NASDAQ-Screener", flush=True)

    print("4/4 Schreiben …", flush=True)
    zeilen = []
    ohne = []
    for _, r in gut.iterrows():
        s = sb.get(r["ticker"])
        if s and s.get("sektor"):
            sektor, branche, etf, quelle = s["sektor"], s.get("branche") or "", sektoren.sektor_von(s["sektor"]), "Yahoo"
        else:
            sektor, branche, quelle = r.get("sector") or "", r.get("industry") or "", "NASDAQ"
            etf = NASDAQ_ETF.get(sektor)
        if not sektor or not etf:            # kein Sektor beim NASDAQ-Screener: bleibt drin, Sektor folgt
            ohne.append(r["ticker"])         # mit werkzeuge/branchen_nachtragen.py
            sektor, branche, etf, quelle = "", "", "", "offen"
        zeilen.append({"ticker": r["ticker"], "name": (s or {}).get("name") or r["name"], "sektor": sektor,
                       "branche": branche, "etf": etf, "quelle": quelle,
                       "boersenwert_mrd": round(r["wert"] / 1e9, 1), "umsatz_mio": round(r["umsatz"] / 1e6, 0),
                       "land": r.get("country") or ""})
    revier = pd.DataFrame(zeilen).sort_values("umsatz_mio", ascending=False)
    revier = nur_eine_gattung(revier)
    revier.to_csv(ZIEL, index=False)
    print(f"\nRevier: {len(revier)} Aktien → einstellungen/revier.csv  ({time.time() - start:.0f} s)")
    print(f"ohne Sektor beim NASDAQ-Screener (aufgenommen, Sektor folgt): {len(ohne)}  {' '.join(ohne[:30])}")
    print("\nnach Sektor:")
    print(revier.groupby("sektor").size().sort_values(ascending=False).to_string())
    print(f"\nBranchen: {revier['branche'].nunique()}")


if __name__ == "__main__":
    main()
