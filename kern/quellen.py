"""Datenquellen für die Fundament-Ampeln, mit Zwischenspeicher in daten/fundament/.

Yahoo (yfinance): bereinigter Gewinn je Aktie mit Schätzung und Überraschung (20+ Quartale),
                  GAAP-Gewinn je Aktie der letzten 4–5 Quartale, Schätzungstrend.
SEC EDGAR:        Umsatz und Nettogewinn je Quartal aus den Pflichtberichten (10-Q/10-K).
                  Das vierte Quartal steht nur im Jahresbericht und wird als Jahr minus
                  Quartal 1–3 gerechnet. Gewinn je Aktie wird von der SEC NICHT genommen,
                  weil die Berichte nicht nachträglich um Aktiensplits bereinigt sind.
Die SEC verlangt eine Absenderangabe: einstellungen/sec_kontakt.txt (eine Zeile, z. B.
„Vorname Nachname mail@adresse.de“); fehlt die Datei, gilt ein Platzhalter.
"""
import json
import os
import time
import urllib.request

import pandas as pd

from dateien import json_lesen, json_schreiben

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "fundament")
KONTAKT = os.path.join(HIER, "..", "einstellungen", "sec_kontakt.txt")
GUELTIG_STUNDEN = 12
UMSATZ_KONZEPTE = ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                   "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax")


def _absender():
    if os.path.exists(KONTAKT):
        zeile = open(KONTAKT, encoding="utf-8").read().strip()
        if zeile:
            return zeile
    return "InvestCockpit privat investcockpit@example.com"


def _sec(url):
    anfrage = urllib.request.Request(url, headers={"User-Agent": _absender()})
    with urllib.request.urlopen(anfrage, timeout=30) as r:
        return json.loads(r.read().decode())


def _sec_reihe(fakten, konzepte, einheit="USD"):
    """Quartalsreihe aus einem oder mehreren XBRL-Konzepten; Q4 = Jahr minus Q1–Q3."""
    zeilen = []
    for k in konzepte:
        try:
            zeilen += fakten["facts"]["us-gaap"][k]["units"][einheit]
        except KeyError:
            continue
    if not zeilen:
        return pd.Series(dtype=float)
    df = pd.DataFrame(zeilen)
    if "start" not in df:
        return pd.Series(dtype=float)
    df["start"], df["end"] = pd.to_datetime(df["start"]), pd.to_datetime(df["end"])
    df["tage"] = (df["end"] - df["start"]).dt.days
    df = df.sort_values("filed")
    quartal = df[(df.tage > 80) & (df.tage < 100)].drop_duplicates("end", keep="last")
    q = quartal.set_index("end")["val"].astype(float)
    jahr = df[(df.tage > 350) & (df.tage < 380)].drop_duplicates("end", keep="last")
    for _, j in jahr.iterrows():
        if j["end"] in q.index:
            continue
        drei = q[(q.index > j["start"]) & (q.index < j["end"])]
        if len(drei) == 3:
            q.loc[j["end"]] = float(j["val"]) - float(drei.sum())
    return q.sort_index()


def sec_quartale(ticker):
    """DataFrame je Quartalsende: umsatz, nettogewinn (USD)."""
    liste = _sec("https://www.sec.gov/files/company_tickers.json")
    cik = {v["ticker"]: v["cik_str"] for v in liste.values()}.get(ticker.upper())
    if cik is None:
        return pd.DataFrame()
    fakten = _sec(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    return pd.DataFrame({"umsatz": _sec_reihe(fakten, UMSATZ_KONZEPTE),
                         "nettogewinn": _sec_reihe(fakten, ("NetIncomeLoss",))}).dropna(how="all")


def yahoo(ticker):
    import yfinance as yf
    t = yf.Ticker(ticker)
    alle = t.get_earnings_dates(limit=28)
    jetzt = pd.Timestamp.now(tz=alle.index.tz) - pd.Timedelta(days=1) if len(alle) else None
    kuenftig = alle[alle["Reported EPS"].isna() & (alle.index >= jetzt)].sort_index() if len(alle) else alle
    # nur künftige Termine (12.11.2026: Zeilen ohne gemeldeten Gewinn aus 2005/2017 standen vorne – IDT, GKOS)
    termin = pd.DataFrame({"datum": [kuenftig.index[0].tz_localize(None).isoformat()] if len(kuenftig) else [None],
                           "schaetzung": [float(kuenftig["EPS Estimate"].iloc[0])] if len(kuenftig) else [None]})
    ed = alle.dropna(subset=["Reported EPS"]).sort_index()
    nach_schluss = (ed.index.hour >= 12).astype(int)      # Meldung nach Börsenschluss: Reaktion am Folgetag
    ed.index = ed.index.tz_localize(None).normalize()
    gewinne = pd.DataFrame({"eps": ed["Reported EPS"], "schaetzung": ed["EPS Estimate"],
                            "ueberraschung_pct": ed["Surprise(%)"], "nach_schluss": nach_schluss},
                           index=ed.index)
    eh = t.earnings_history
    q = t.quarterly_income_stmt
    gaap = q.loc["Diluted EPS"].dropna() if "Diluted EPS" in q.index else pd.Series(dtype=float)
    qualitaet = pd.DataFrame({"bereinigt": eh["epsActual"]}).join(gaap.rename("gaap"), how="left")
    trend = t.eps_trend
    aus = {"gewinne": gewinne, "qualitaet": qualitaet, "trend": trend, "termin": termin}
    try:                                         # I nach CAN SLIM: Anteil der Institutionen, Zu- und Abgänge der größten
        info = t.info or {}
        ih = t.institutional_holders
        aenderung = (float(ih["pctChange"].astype(float).mean()) if ih is not None and "pctChange" in ih
                     and len(ih) else None)
        aus["institutionen"] = pd.DataFrame({"anteil": [info.get("heldPercentInstitutions")],
                                             "aenderung": [aenderung], "halter": [len(ih) if ih is not None else None]})
    except Exception:  # noqa: BLE001
        pass
    return aus


def _als_json(daten):
    aus = {}
    for k, v in daten.items():
        if isinstance(v, (pd.DataFrame, pd.Series)):
            aus[k] = v.to_json(date_format="iso", orient="split")
    return aus


def _aus_json(roh):
    from io import StringIO
    aus = {}
    for k in ("gewinne", "qualitaet", "trend", "sec", "termin", "institutionen"):
        if k in roh:
            aus[k] = pd.read_json(StringIO(roh[k]), orient="split")
    t = aus.get("termin")                              # gespeicherte Termine aus der Vergangenheit gelten nicht (12.11.)
    if t is not None and len(t) and "datum" in t:
        d = pd.to_datetime(t["datum"], errors="coerce")
        if d.notna().all() and (d < pd.Timestamp.today().normalize() - pd.Timedelta(days=1)).all():
            aus["termin"] = t.iloc[0:0]
    return aus


def laden(ticker, neu=False):
    """Alle Fundamentdaten eines Titels; aus dem Zwischenspeicher, wenn jünger als 12 Stunden."""
    os.makedirs(SPEICHER, exist_ok=True)
    pfad = os.path.join(SPEICHER, f"{ticker.upper()}.json")
    if not neu and os.path.exists(pfad) and time.time() - os.path.getmtime(pfad) < GUELTIG_STUNDEN * 3600:
        roh = json_lesen(pfad)
        if roh is not None:
            return _aus_json(roh)
    daten = yahoo(ticker)
    try:
        daten["sec"] = sec_quartale(ticker)
    except Exception:
        daten["sec"] = pd.DataFrame()
    json_schreiben(pfad, _als_json(daten))
    return daten


def nach_terminen(titel, heute=None):
    """Zahlen neu laden für Titel, deren gespeicherter Termin seit dem letzten Laden vorbei ist (Prüf-Agent 12.11.2026:
    Kartentisch las alte Zahlen und fand die Zahlen-Reaktion nicht, die Titelseite – frisch geladen – fand sie).
    → (neu geladen, gescheitert)."""
    import datetime as _dt
    heute = heute or _dt.date.today().isoformat()
    neu, fehler = 0, 0
    for tk in titel:
        pfad = os.path.join(SPEICHER, f"{tk.upper()}.json")
        if not os.path.exists(pfad):
            continue
        try:
            fd = _aus_json(json_lesen(pfad))
            t = fd.get("termin")
            tag = f"{pd.Timestamp(t['datum'].iloc[0]):%Y-%m-%d}" if t is not None and len(t) and t["datum"].iloc[0] else None
        except Exception:  # noqa: BLE001
            continue
        geladen = _dt.date.fromtimestamp(os.path.getmtime(pfad)).isoformat()
        if tag and geladen <= tag <= heute:        # Termin lag nach dem letzten Laden und ist jetzt vorbei
            try:
                laden(tk, neu=True)
                neu += 1
            except Exception:  # noqa: BLE001
                fehler += 1
    return neu, fehler
