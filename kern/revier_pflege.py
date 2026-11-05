"""Revier-Pflege (Nachtlauf, freitags, ab 05.11.2026): Zugänge automatisch, Abgänge nur gemeldet.

Regeln des Reviers (Schritt 3): US-Börse (NYSE, NASDAQ, AMEX), Börsenwert ab 1 Mrd. $, Handelsumsatz ab 20 Mio. $ je Tag
(30-Tage-Schnitt), Kurs ab 10 $. Quelle der Kandidaten: TradingView-Screener (wie tv_kennzahlen); Sektor und Branche
für einen Zugang von Yahoo (daten.steckbrief), damit sie zur Yahoo-Einteilung des Reviers passen.
Abgang = seit 5 Handelstagen keine neuen Kurse (Übernahme, Delisting) – wird gemeldet, nicht entfernt (nichts löschen).
Vorher Sicherung von einstellungen/revier.csv nach _to_delete/revier/.
"""
import os
import shutil
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
REVIER = os.path.join(HIER, "..", "einstellungen", "revier.csv")
SPALTEN = ["name", "exchange", "description", "market_cap_basic", "close", "average_volume_30d_calc", "type"]
HOECHSTENS = 40               # Zugänge je Lauf (Yahoo-Abfragen begrenzen); der Rest kommt nächste Woche


def kandidaten():
    import tv_kennzahlen
    roh = tv_kennzahlen._abfrage("america", {
        "filter": [{"left": "market_cap_basic", "operation": "egreater", "right": 1e9},
                   {"left": "close", "operation": "egreater", "right": 10},
                   {"left": "exchange", "operation": "in_range", "right": ["NYSE", "NASDAQ", "AMEX"]},
                   {"left": "type", "operation": "equal", "right": "stock"}],
        "markets": ["america"], "columns": SPALTEN, "range": [0, 9000]})
    df = pd.DataFrame([dict(zip(SPALTEN, z["d"])) for z in roh])
    df["umsatz"] = df["close"] * df["average_volume_30d_calc"]
    df = df[df["umsatz"] >= 20e6].copy()
    df["ticker"] = df["name"].astype(str).str.replace(".", "-", regex=False).str.upper()
    return df.drop_duplicates("ticker")


def abgaenge(rv):
    import daten
    weg = []
    grenze = pd.Timestamp.now().normalize() - pd.tseries.offsets.BDay(5)
    for tk in rv["ticker"]:
        df = daten.kurse_gespeichert(tk)
        if df is None or df.index[-1] < grenze:
            weg.append(tk)
    return weg


def pflegen():
    import daten
    import sektoren
    rv = pd.read_csv(REVIER)
    kd = kandidaten()
    neu = kd[~kd["ticker"].isin(set(rv["ticker"]))].sort_values("market_cap_basic", ascending=False).head(HOECHSTENS)
    zeilen = []
    for _, z in neu.iterrows():
        try:
            sb = daten.steckbrief(z["ticker"])
            time.sleep(1)
        except Exception:  # noqa: BLE001 – ohne Yahoo-Steckbrief kein Zugang (Sektor unbekannt)
            continue
        zeilen.append({"ticker": z["ticker"], "name": sb.get("name") or z["description"], "sektor": sb.get("sektor", ""),
                       "branche": sb.get("branche", ""), "etf": sektoren.sektor_von(sb.get("sektor", "")) or "",
                       "quelle": "TradingView", "boersenwert_mrd": round(z["market_cap_basic"] / 1e9, 1),
                       "umsatz_mio": round(z["umsatz"] / 1e6, 1), "land": "United States"})
    if zeilen:
        ziel = os.path.join(HIER, "..", "_to_delete", "revier")
        os.makedirs(ziel, exist_ok=True)
        shutil.copy(REVIER, os.path.join(ziel, f"revier_{time.strftime('%Y-%m-%d')}.csv"))
        pd.concat([rv, pd.DataFrame(zeilen)], ignore_index=True).to_csv(REVIER, index=False)
    weg = abgaenge(rv)
    return (f"{len(zeilen)} Zugänge" + (f" ({', '.join(z['ticker'] for z in zeilen[:15])})" if zeilen else "")
            + f" · Abgänge gemeldet: {', '.join(weg) if weg else 'keine'}")
