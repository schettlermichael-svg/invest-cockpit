"""Massive (früher Polygon.io): Tageskurse aller US-Aktien mit einer Anfrage je Handelstag.

tag(datum)          -> DataFrame (Ticker, Open, High, Low, Close, Volume) aller US-Aktien eines Tages,
                       gespeichert in daten/massive/<datum>.csv (ein Tag wird nie zweimal geholt)
letzte_tage(n)      -> Liste der letzten n Handelstage als DataFrames (älteste zuerst)
splits(datum)       -> Aktiensplits eines Tages; splits_zeitraum(von, bis) -> alle Splits eines Zeitraums
kursmatrix(ticker, n) -> Schlusskurse der letzten n gespeicherten Handelstage (Zeilen Tage, Spalten Ticker),
                       über alle Tage vergleichbar gemacht (siehe dort)
Kostenloser Plan: 5 Anfragen pro Minute, Tagesschlüsse, 2 Jahre Historie. Das Modul hält den Abstand
selbst ein (mindestens 12,5 s zwischen zwei Anfragen) und wartet bei einer Sperre (429) eine Minute.
Schlüssel: einstellungen/massive_schluessel.txt
"""
import json
import os
import subprocess
import time
from datetime import date

import pandas as pd

from dateien import json_lesen, json_schreiben

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "massive")
SCHLUESSEL = os.path.join(HIER, "..", "einstellungen", "massive_schluessel.txt")
ABSTAND = 12.5
SPALTEN = ["Ticker", "Open", "High", "Low", "Close", "Volume"]
_letzte_anfrage = [0.0]


def _abruf(pfad):
    schluessel = open(SCHLUESSEL, encoding="utf-8").read().strip()
    for versuch in range(5):
        warten = ABSTAND - (time.time() - _letzte_anfrage[0])
        if warten > 0:
            time.sleep(warten)
        _letzte_anfrage[0] = time.time()
        erg = subprocess.run(["curl", "-sS", "--max-time", "60", "-w", "\n%{http_code}",
                              f"https://api.massive.com{pfad}&apiKey={schluessel}"], capture_output=True, text=True)
        text, _, code = erg.stdout.rpartition("\n")
        if code == "200":
            return json.loads(text)
        if code == "429":
            time.sleep(60)
            continue
        raise OSError(f"Massive antwortet {code or 'nicht'}: {text[:200] or erg.stderr.strip()}")
    raise OSError("Massive sperrt weiter (429)")


def tag(datum):
    """Alle US-Aktien eines Tages; leerer DataFrame an Tagen ohne Handel."""
    datum = pd.Timestamp(datum).strftime("%Y-%m-%d")
    os.makedirs(SPEICHER, exist_ok=True)
    pfad = os.path.join(SPEICHER, f"{datum}.csv")
    if os.path.exists(pfad):
        try:
            return pd.read_csv(pfad)
        except pd.errors.EmptyDataError:                  # gespeicherter Feiertag (leere Datei)
            return pd.DataFrame(columns=SPALTEN)
    daten = _abruf(f"/v2/aggs/grouped/locale/us/market/stocks/{datum}?adjusted=true")
    zeilen = daten.get("results") or []
    df = pd.DataFrame(zeilen)
    if df.empty:
        df = pd.DataFrame(columns=SPALTEN)                # Feiertag: leere Datei mit Spaltenköpfen
    else:
        df = df.rename(columns={"T": "Ticker", "o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
        df = df[SPALTEN]
    # heutiger Tag ohne Ergebnis wird nicht gespeichert (Schlusskurse evtl. noch nicht da)
    if not df.empty or pd.Timestamp(datum) < pd.Timestamp(date.today()) - pd.Timedelta(days=1):
        df.to_csv(pfad, index=False)
    return df


def _letzter_schluss():
    """Jüngster Tag mit Schlusskursen: heute, wenn in New York schon 16:30 Uhr vorbei ist (der Nachtlauf um 22:45 Uhr
    Berlin läuft nach Börsenschluss), sonst gestern. Liefert Massive den Tag noch nicht, überspringt letzte_tage() ihn
    (leerer Tag) und nimmt den Vortag – so wie bisher (06.11.2026: vorher immer erst ab gestern, ein Tag Verzug)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ny = datetime.now(ZoneInfo("America/New_York"))
    if ny.weekday() < 5 and (ny.hour, ny.minute) >= (16, 30):
        return pd.Timestamp(ny.date())
    return pd.Timestamp(ny.date()) - pd.Timedelta(days=1)


def letzte_tage(n, bis=None, melden=None):
    """Die letzten n Handelstage bis einschließlich bis (Standard: der jüngste Tag mit Schlusskursen), älteste zuerst."""
    tag_ = pd.Timestamp(bis) if bis else _letzter_schluss()
    aus = []
    while len(aus) < n:
        if tag_.weekday() < 5:
            df = tag(tag_)
            if not df.empty:
                aus.append((tag_, df))
                if melden:
                    melden(len(aus), n, tag_)
        tag_ -= pd.Timedelta(days=1)
    return list(reversed(aus))


def splits(datum):
    """Aktiensplits mit Wirkung an diesem Tag: {Ticker: Faktor}; Kurse davor × Faktor = vergleichbar."""
    datum = pd.Timestamp(datum).strftime("%Y-%m-%d")
    os.makedirs(SPEICHER, exist_ok=True)
    pfad = os.path.join(SPEICHER, f"splits_{datum}.json")
    liste = json_lesen(pfad)
    if liste is None:
        daten = _abruf(f"/v3/reference/splits?execution_date={datum}&limit=1000")
        liste = daten.get("results") or []
        json_schreiben(pfad, liste)
    return {s["ticker"].replace(".", "-"): s["split_from"] / s["split_to"] for s in liste if s.get("split_to")}


def splits_zeitraum(von, bis):
    """Alle Aktiensplits zwischen von und bis (je einschließlich) in wenigen Anfragen:
    Liste (Datum, Ticker, Faktor); Kurse vor dem Datum × Faktor = vergleichbar. Gespeichert je Zeitraum."""
    von, bis = (pd.Timestamp(x).strftime("%Y-%m-%d") for x in (von, bis))
    os.makedirs(SPEICHER, exist_ok=True)
    pfad = os.path.join(SPEICHER, f"splits_{von}_{bis}.json")
    alle = json_lesen(pfad)
    if alle is None:
        alle, weg = [], (f"/v3/reference/splits?execution_date.gte={von}&execution_date.lte={bis}"
                         f"&limit=1000&order=asc&sort=execution_date")
        while weg:
            daten = _abruf(weg)
            alle += daten.get("results") or []
            naechste = daten.get("next_url") or ""
            weg = naechste.replace("https://api.massive.com", "").replace("https://api.polygon.io", "") or None
            if weg and "?" not in weg:
                weg += "?"
        json_schreiben(pfad, alle)
    return [(pd.Timestamp(s["execution_date"]), s["ticker"].replace(".", "-"), s["split_from"] / s["split_to"])
            for s in alle if s.get("split_to")]


def kursmatrix(ticker, n=260, spalte="Close"):
    """Kurse (oder Volumen) aller gespeicherten Tage als Tabelle, über Splits hinweg vergleichbar.

    Massive liefert jeden Tag bereits um alle Splits BIS ZUM ABRUFTAG bereinigt (adjusted=true). Ein Split
    nach dem Abruf eines Tages fehlt in dessen Datei – nur dieser wird nachgerechnet: Datei von Tag d,
    abgerufen am Datum a (Dateizeit), Split am Tag s mit a < s und d < s  →  Kurs × Faktor, Volumen ÷ Faktor.
    Ein zweites Bereinigen bereits bereinigter Tage (Fehler 01.11.2026: NFLX ×10) ist damit ausgeschlossen."""
    namen = {tk: tk.replace("-", ".") for tk in ticker}
    dateien = sorted(d for d in os.listdir(SPEICHER) if d[:4].isdigit() and d.endswith(".csv"))
    spalten, abruf = {}, {}
    for d in reversed(dateien):                                # von hinten, bis n Handelstage beisammen sind
        if len(spalten) == n:
            break
        df = tag(d[:10])
        if df.empty:
            continue
        t = pd.Timestamp(d[:10])
        spalten[t] = df.drop_duplicates("Ticker").set_index("Ticker")[spalte]
        abruf[t] = pd.Timestamp(os.path.getmtime(os.path.join(SPEICHER, d)), unit="s").normalize()
    m = pd.DataFrame(spalten).T.sort_index().reindex(columns=list(namen.values())).astype(float)
    if len(m):
        for s_tag, tk, faktor in splits_zeitraum(m.index[0], m.index[-1]):   # spätere Splits betreffen noch keinen Tag
            name = tk.replace("-", ".")
            if name not in m.columns:
                continue
            betroffen = [t for t in m.index if t < s_tag and abruf[t] < s_tag]
            if betroffen:
                m.loc[betroffen, name] *= faktor if spalte != "Volume" else 1 / faktor
    m.columns = list(namen.keys())
    return m


def schlusskurse(ticker, tage=5):
    """Gegenprobe ohne Anfrage: die letzten Schlusskurse eines Titels aus den gespeicherten Tagesdateien."""
    if not os.path.isdir(SPEICHER):
        return pd.Series(dtype=float)
    dateien = sorted(d for d in os.listdir(SPEICHER) if d[:4].isdigit() and d.endswith(".csv"))[-tage:]
    name = ticker.upper().replace("-", ".")
    werte = {}
    for d in dateien:
        df = tag(d[:10])                                  # liest nur die gespeicherte Datei
        treffer = df.loc[df["Ticker"] == name, "Close"] if not df.empty else []
        if len(treffer):
            werte[pd.Timestamp(d[:10])] = float(treffer.iloc[0])
    return pd.Series(werte, dtype=float)
