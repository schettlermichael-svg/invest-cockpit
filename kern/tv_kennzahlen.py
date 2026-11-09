"""TradingView-Kennzahlen direkt vom Server (Nachtlauf, ab 05.11.2026): TradingViews öffentliche Screener-Schnittstelle
(scanner.tradingview.com, ohne Login; nicht offiziell dokumentiert). Schreibt daten/tv/revier.csv in derselben Form wie
bisher (eine Zeile je Revier- und Watchlist-Titel). Ersetzt die Datei nur, wenn mindestens 95 % der US-Titel Werte haben;
sonst bleibt der letzte Stand und der Nachtlauf meldet es. Titel außerhalb der USA (RHM.DE …) fragt sie bei ihrer
Heimatbörse ab (watchlists.zu_tv)."""
import json
import os
import urllib.request

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "daten", "tv", "revier.csv")
SPALTEN = ["name", "exchange", "description", "market_cap_basic", "gross_margin_ttm", "gross_margin_fy",
           "operating_margin_ttm", "net_margin_ttm", "net_margin_fy", "return_on_invested_capital_fy",
           "return_on_equity_fy", "debt_to_equity_fq", "net_debt_fq", "current_ratio_fq", "ebitda_ttm",
           "total_shares_outstanding", "float_shares_outstanding", "share_buyback_ratio_fq",
           "earnings_release_next_date", "beta_1_year"]
# ROE und ROIC als Geschäftsjahr (fy): die ttm-Spalten liefert TradingView leer (geprüft 09.11.2026)
MINDEST = 0.95


def _abfrage(markt, koerper):
    req = urllib.request.Request(f"https://scanner.tradingview.com/{markt}/scan", data=json.dumps(koerper).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("data") or []


def _zeilen(daten):
    aus = []
    for z in daten:
        d = dict(zip(SPALTEN, z["d"]))
        er = d.get("earnings_release_next_date")
        if isinstance(er, (int, float)) and er == er:
            d["earnings_release_next_date"] = pd.Timestamp(int(er), unit="s").strftime("%Y-%m-%d")
        aus.append(d)
    return aus


def holen(titel):
    """titel: Ticker in Yahoo-Schreibweise. Gibt (DataFrame, Abdeckung der US-Titel) zurück."""
    import tpo_daten
    import watchlists
    us = [t for t in titel if not tpo_daten.auslaendisch(t)]
    roh = _abfrage("america", {"filter": [{"left": "market_cap_basic", "operation": "greater", "right": 2e8}],
                               "markets": ["america"], "columns": SPALTEN, "range": [0, 9000]})
    df = pd.DataFrame(_zeilen(roh))
    df["ticker"] = df["name"].astype(str).str.replace(".", "-", regex=False).str.upper()
    df = df.sort_values("market_cap_basic", ascending=False).drop_duplicates("ticker")
    df = df[df["ticker"].isin(set(us))]
    ausland = [watchlists.zu_tv(t) for t in titel if tpo_daten.auslaendisch(t) and watchlists.zu_tv(t)]
    if ausland:
        try:
            r = _abfrage("global", {"symbols": {"tickers": ausland}, "columns": SPALTEN})
            for sym, z in zip([x["s"] for x in r], _zeilen(r)):
                yahoo = watchlists.von_tv(sym)
                if yahoo:
                    df = pd.concat([df, pd.DataFrame([{**z, "ticker": yahoo}])], ignore_index=True)
        except Exception:  # noqa: BLE001 – Ausland ist Zugabe, US entscheidet
            pass
    return df[["ticker"] + SPALTEN], (len(df[df["ticker"].isin(set(us))]) / len(us) if us else 0)


def aktualisieren(titel):
    """Holt und speichert; Text für das Protokoll. Löst einen Fehler aus, wenn die Abdeckung zu klein ist."""
    df, anteil = holen(titel)
    if anteil < MINDEST:
        raise RuntimeError(f"nur {anteil:.0%} der Titel von TradingView – letzter Stand bleibt")
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    df.to_csv(DATEI + ".neu", index=False)
    os.replace(DATEI + ".neu", DATEI)
    return f"{len(df)} Titel ({anteil:.0%})"
