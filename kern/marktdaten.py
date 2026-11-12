"""Marktdaten für Lageleiste, Pendel und Quadrant – mit Speicher in daten/markt/.

fred(reihe)        amtliche und Hochfrequenz-Reihen der US-Notenbank (FRED, ohne Schlüssel)
yahoo(ticker)      Tagesschlüsse ab 2006 (Rohstoffe, ETFs, VIX, Index)
yahoo_ohlc(ticker) Tageskerzen mit Volumen ab 1985 (S&P 500, Nasdaq – für die Marktrichtung)
breite()           Anteil der Aktien der Breite-Liste (einstellungen/breite.txt, 515 große US-Werte)
                   über ihrem GD200, täglich – fest, weil das Pendel an dieser Liste geeicht ist;
                   neue Tage aus Massive, Ersatz Yahoo
breite_pruefung()  Plausibilitätswächter: Abdeckung, Sprünge, Aktualität, Ersatzquelle
Alles wird höchstens einmal je 12 Stunden neu geholt. Kurse von Yahoo (Prüfung 12.11.2026): eine noch laufende Tageskerze
wird nie gespeichert, und eine Datei ohne den letzten abgeschlossenen Handelstag gilt nicht als frisch – vorher konnte ein
Aufruf während der US-Börse (z. B. 17 Uhr) den halben Tag speichern, und der Frühlauf am Morgen las ihn noch als „frisch“.
"""
import io
import os
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "markt")
BREITE_LISTE = os.path.join(HIER, "..", "einstellungen", "breite.txt")
START = "2006-01-01"


def _frisch(pfad, stunden=12):
    return os.path.exists(pfad) and time.time() - os.path.getmtime(pfad) < stunden * 3600


def _kurs_frisch(pfad):
    """Kursdatei frisch: jünger als 12 Stunden UND mit dem letzten abgeschlossenen Handelstag (oder in der letzten Stunde
    geholt – an US-Feiertagen gibt es den Tag nicht, dann nicht bei jedem Aufruf neu laden)."""
    if not _frisch(pfad):
        return False
    if _frisch(pfad, 1):
        return True
    try:
        import massive
        soll = massive._letzter_schluss()
        while soll.weekday() >= 5:
            soll -= pd.Timedelta(days=1)
        with open(pfad, "rb") as f:                 # letzte Zeile genügt
            f.seek(max(0, os.path.getsize(pfad) - 200))
            letzte = f.read().decode("utf-8", "ignore").strip().splitlines()[-1]
        return pd.Timestamp(letzte.split(",")[0]) >= soll
    except Exception:  # noqa: BLE001
        return True


def _ohne_laufende(ticker, df):
    """Laufende Tageskerze (Börse heute noch offen) weglassen – gespeichert werden nur abgeschlossene Tage."""
    try:
        import daten
        if len(df) and daten._offen(ticker, df.index[-1]):
            return df.iloc[:-1]
    except Exception:  # noqa: BLE001
        pass
    return df


def _pfad(name):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, name.replace("^", "_").replace("=", "_") + ".csv")


SCHLUESSEL = os.path.join(HIER, "..", "einstellungen", "fred_schluessel.txt")


def _curl(url):
    import subprocess
    erg = subprocess.run(["curl", "-sSfL", "--http1.1", "--max-time", "40", "-A",
                          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/130.0 Safari/537.36", url],
                         capture_output=True, text=True)
    if erg.returncode == 0 and erg.stdout.strip():
        return erg.stdout
    raise OSError(f"curl: {erg.stderr.strip() or 'keine Antwort'}")


def _fred_api(reihe, schluessel):
    """Offizielle FRED-Schnittstelle (kostenloser Schlüssel) – wird nicht ausgebremst."""
    import json
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={reihe}"
           f"&api_key={schluessel}&file_type=json")
    daten = json.loads(_curl(url))
    df = pd.DataFrame(daten["observations"])[["date", "value"]]
    df.columns = ["Datum", reihe]
    return df


def fred(reihe):
    """Mit Schlüssel (einstellungen/fred_schluessel.txt) über die offizielle Schnittstelle,
    sonst über den öffentlichen CSV-Abruf, den FRED aber oft abweist."""
    pfad = _pfad("fred_" + reihe)
    if not _frisch(pfad):
        print(f"FRED: lade {reihe} …", flush=True)
        schluessel = open(SCHLUESSEL, encoding="utf-8").read().strip() if os.path.exists(SCHLUESSEL) else ""
        if schluessel:
            df = _fred_api(reihe, schluessel)
        else:
            df = pd.read_csv(io.StringIO(_curl(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={reihe}")))
            df.columns = ["Datum", reihe]
        df[reihe] = pd.to_numeric(df[reihe], errors="coerce")
        df.dropna().to_csv(pfad, index=False)
    s = pd.read_csv(pfad, parse_dates=["Datum"], index_col="Datum")[reihe]
    return s.dropna()


def yahoo(ticker):
    pfad = _pfad(ticker)
    if not _kurs_frisch(pfad):
        import yfinance as yf
        df = yf.download(ticker, start=START, auto_adjust=True, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df is None or df.empty:
            raise OSError(f"Yahoo: keine Kurse für {ticker}")
        df = df[["Close"]].dropna()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "Datum"
        _ohne_laufende(ticker, df).to_csv(pfad)
    return pd.read_csv(pfad, parse_dates=["Datum"], index_col="Datum")["Close"]


def yahoo_ohlc(ticker):
    """Tageskerzen mit Volumen ab 1985 (Datei <ticker>_ohlc.csv) – für Distributionstage und Follow-Through-Day."""
    pfad = _pfad(ticker + "_ohlc")
    if not _kurs_frisch(pfad):
        import yfinance as yf
        df = yf.download(ticker, start="1985-01-01", auto_adjust=False, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df is None or df.empty:
            raise OSError(f"Yahoo: keine Kurse für {ticker}")
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = "Datum"
        _ohne_laufende(ticker, df).to_csv(pfad)
    return pd.read_csv(pfad, parse_dates=["Datum"], index_col="Datum")


def _breite_nachtrag_massive(alt):
    """Neue Handelstage aus den Massive-Tagesdateien anhängen (keine Einzelabrufe). Splits mit
    Wirkung an einem neuen Tag werden in der gespeicherten Historie nachgerechnet, sonst entstünde
    ein falscher Bruch im GD200."""
    import massive
    tage = pd.bdate_range(alt.index[-1] + pd.Timedelta(days=1), pd.Timestamp.today().normalize() - pd.Timedelta(days=1))
    if len(tage) > 40:
        raise OSError(f"{len(tage)} fehlende Tage – zu viel für den Nachtrag")
    schluss = alt.copy()
    for tag in tage:
        df = massive.tag(tag)
        if df.empty:                                       # Feiertag
            continue
        for tk, faktor in massive.splits(tag).items():
            if tk in schluss.columns:
                schluss.loc[schluss.index < tag, tk] *= faktor
        reihe = df.assign(Ticker=df["Ticker"].str.replace(".", "-", regex=False)).drop_duplicates("Ticker")
        schluss.loc[tag] = reihe.set_index("Ticker")["Close"].reindex(schluss.columns)
    return schluss.sort_index()


def _breite_nachtrag_yahoo(alt, titel):
    import yfinance as yf
    neu = yf.download(titel, period="1mo", auto_adjust=True, progress=False, threads=True)["Close"]
    neu.index = pd.to_datetime(neu.index).tz_localize(None)
    return pd.concat([alt[~alt.index.isin(neu.index)], neu]).sort_index()


def breite():
    """Täglicher Anteil (Prozent) der 515 großen US-Werte (einstellungen/breite.txt) über ihrem GD200.
    Historie seit 2006 einmalig von Yahoo; neue Tage aus Massive (Tagesdateien aller US-Aktien),
    bei Ausfall von Massive ersatzweise von Yahoo. Gespeichert wird je Tag auch die Abdeckung
    (wie viele Werte einen Kurs hatten) und die Quelle – für breite_pruefung()."""
    pfad_schluss = _pfad("revier_schluesse")
    pfad = _pfad("breite")
    if _kurs_frisch(pfad):
        return pd.read_csv(pfad, parse_dates=["Datum"], index_col="Datum")["breite"]
    titel = [z.strip() for z in open(BREITE_LISTE, encoding="utf-8") if z.strip() and not z.startswith("#")]
    quelle_pfad = os.path.join(SPEICHER, "breite_quelle.txt")
    if os.path.exists(pfad_schluss):
        alt = pd.read_csv(pfad_schluss, parse_dates=["Datum"], index_col="Datum")
        try:
            schluss = _breite_nachtrag_massive(alt)
            quelle = "Massive"
        except Exception as e:
            print(f"Marktbreite: Massive nicht nutzbar ({e}) – Ersatzquelle Yahoo", flush=True)
            schluss = _breite_nachtrag_yahoo(alt, titel)
            quelle = "Yahoo (Ersatz)"
    else:
        import yfinance as yf
        print(f"Marktbreite: lade einmalig {len(titel)} Aktien ab {START[:4]} – das dauert einige Minuten …", flush=True)
        schluss = yf.download(titel, start=START, auto_adjust=True, progress=False, threads=True)["Close"]
        schluss.index = pd.to_datetime(schluss.index).tz_localize(None)
        quelle = "Yahoo"
    schluss.index.name = "Datum"
    schluss.to_csv(pfad_schluss)
    open(quelle_pfad, "w", encoding="utf-8").write(quelle)
    gd = schluss.rolling(200, min_periods=200).mean()
    gueltig = gd.notna() & schluss.notna()
    anteil = ((schluss > gd) & gueltig).sum(axis=1) / gueltig.sum(axis=1).replace(0, float("nan")) * 100
    tabelle = pd.DataFrame({"breite": anteil, "abdeckung": schluss.notna().sum(axis=1)}).dropna()
    tabelle.to_csv(pfad)
    return tabelle["breite"]


def breite_pruefung():
    """Plausibilitätswächter der Marktbreite: Liste von (Ampel, Text); leer = alles in Ordnung."""
    breite()
    t = pd.read_csv(_pfad("breite"), parse_dates=["Datum"], index_col="Datum")
    zeichen = []
    if "abdeckung" in t and len(t) > 21:
        normal = t["abdeckung"].iloc[-21:-1].median()
        if t["abdeckung"].iloc[-1] < 0.95 * normal:
            zeichen.append(("gelb", f"nur {int(t['abdeckung'].iloc[-1])} statt rund {int(normal)} Werte mit Kurs am "
                                    f"{t.index[-1]:%d.%m.%Y}"))
    if len(t) > 1 and abs(t["breite"].iloc[-1] - t["breite"].iloc[-2]) > 15:
        zeichen.append(("gelb", f"Breite springt an einem Tag um {abs(t['breite'].iloc[-1] - t['breite'].iloc[-2]):.0f} Punkte"))
    spx = yahoo("^GSPC")
    rueckstand = int((spx.index > t.index[-1]).sum())
    if rueckstand > 2:
        zeichen.append(("rot", f"veraltet: {rueckstand} Handelstage hinter dem S&P 500"))
    quelle_pfad = os.path.join(SPEICHER, "breite_quelle.txt")
    if os.path.exists(quelle_pfad) and "Ersatz" in open(quelle_pfad, encoding="utf-8").read():
        zeichen.append(("gelb", "Massive nicht erreichbar – neue Tage ersatzweise von Yahoo"))
    return zeichen
