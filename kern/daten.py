"""Kursdaten der App (Yahoo über yfinance) mit Speicher in daten/kurse/.

kurse(ticker)  -> Tageskurse (Open, High, Low, Close, Volume), mindestens 3 Jahre
steckbrief(ticker) -> Name, Sektor, Branche (einmal geladen, dann aus dem Speicher)
Die Kurse werden einmal je Tag neu geholt; ein unvollständiger heutiger Balken vor 22:30 Uhr
deutscher Zeit wird verworfen, damit die Rechnung nur mit abgeschlossenen Tagen arbeitet.
"""
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from dateien import json_lesen, json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "kurse")
INDEX = "^GSPC"


def _frisch(pfad, stunden):
    return os.path.exists(pfad) and time.time() - os.path.getmtime(pfad) < stunden * 3600


def _offen(ticker, letzter_tag):
    """Ist die letzte Tageskerze noch unvollständig? Ja, solange ihre Börse heute nicht seit 15 Minuten geschlossen
    hat (New York 16:15 Ortszeit = 22:15 Berlin; Börsen außerhalb der USA nach tpo_daten.SITZUNGEN). Vorher galt fest
    22:30 Berlin – ein Lauf um 22:20 verwarf so den fertigen Handelstag (04.11.2026)."""
    import tpo_daten
    zone, _, ende = tpo_daten._ort(ticker)
    jetzt = datetime.now(zone)
    return letzter_tag.date() == jetzt.date() and jetzt.hour * 60 + jetzt.minute < ende + 15


def kurse(ticker, jahre=3, laufend=False):
    """Tageskurse. laufend=True (Knopf „Kurse aktualisieren“): sofort neu laden und die unvollständige Kerze des
    laufenden Börsentags behalten; gespeichert werden weiter nur abgeschlossene Tage. Yahoo liefert während der Börse
    mit bis zu 15 Minuten Verzögerung."""
    os.makedirs(SPEICHER, exist_ok=True)
    name = ticker.upper().replace("^", "_")
    pfad = os.path.join(SPEICHER, f"{name}.csv")
    if _frisch(pfad, 12) and not laufend:
        return pd.read_csv(pfad, parse_dates=["Datum"], index_col="Datum")
    import yfinance as yf
    df = yf.download(ticker, period=f"{jahre}y", auto_adjust=True, progress=False, threads=False)
    if df is None or df.empty:
        raise ValueError(f"Keine Kurse für {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "Datum"
    offen = _offen(ticker, df.index[-1])
    jetzt = datetime.now(ZoneInfo("Europe/Berlin"))
    (df.iloc[:-1] if offen else df).to_csv(pfad)            # gespeichert werden nur abgeschlossene Tage
    if offen and not laufend:
        return df.iloc[:-1]
    if offen:
        df.attrs["laufend"] = True
        df.attrs["stand"] = jetzt.strftime("%H:%M")
    return df


def kurse_viele(ticker_liste, jahre=3, paket=50):
    """Tageskurse vieler Titel in Paketen (Abendlauf), gespeichert wie kurse(); nur abgeschlossene Tage. Gibt die Zahl
    der aktualisierten Titel zurück."""
    import yfinance as yf
    os.makedirs(SPEICHER, exist_ok=True)
    n = 0
    liste = [t.upper() for t in ticker_liste]
    for a in range(0, len(liste), paket):
        teil = liste[a:a + paket]
        try:
            roh = yf.download(teil, period=f"{jahre}y", auto_adjust=True, progress=False, threads=False,
                              group_by="ticker")
        except Exception:  # noqa: BLE001 – ein Paket scheitert, die übrigen laufen weiter
            continue
        if roh is None or roh.empty:
            continue
        for t_ in teil:
            try:
                df = roh[t_] if isinstance(roh.columns, pd.MultiIndex) else roh
            except KeyError:
                continue
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            if df.empty:
                continue
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df.index.name = "Datum"
            if _offen(t_, df.index[-1]):
                df = df.iloc[:-1]
            df.to_csv(os.path.join(SPEICHER, f"{t_.replace('^', '_')}.csv"))
            n += 1
    return n


def kurse_gespeichert(ticker):
    """Tageskurse nur aus dem Speicher (ohne Abruf), sonst None."""
    pfad = os.path.join(SPEICHER, f"{ticker.upper().replace('^', '_')}.csv")
    return pd.read_csv(pfad, parse_dates=["Datum"], index_col="Datum") if os.path.exists(pfad) else None


def steckbrief_gespeichert(ticker):
    """Steckbrief nur aus dem Speicher (ohne Abruf), sonst None."""
    pfad = os.path.join(SPEICHER, f"{ticker.upper()}_steckbrief.json")
    return json_lesen(pfad)


def steckbrief(ticker):
    os.makedirs(SPEICHER, exist_ok=True)
    pfad = os.path.join(SPEICHER, f"{ticker.upper()}_steckbrief.json")
    if _frisch(pfad, 24 * 100) and json_lesen(pfad) is not None:   # Sektor ändert sich selten; rollierend nachgeprüft
        return json_lesen(pfad)
    import yfinance as yf
    info = yf.Ticker(ticker).info
    if not info or len(info) < 5:                       # leere Antwort (z. B. gedrosselt): nicht speichern
        raise ValueError(f"Kein Steckbrief für {ticker} (leere Antwort von Yahoo)")
    s = {"name": info.get("longName") or info.get("shortName") or ticker.upper(),
         "sektor": info.get("sector") or "", "branche": info.get("industry") or "",
         "beschreibung": (info.get("longBusinessSummary") or "")[:400]}
    json_schreiben(pfad, s, ensure_ascii=False)
    return s
