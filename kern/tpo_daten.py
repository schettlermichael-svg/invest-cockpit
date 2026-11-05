"""30-Minuten-Kerzen der regulären Sitzung (9:30–16:00 Uhr New York) für das Market Profile, Speicher daten/tpo/<T>.csv.

Quellen: Massive (früher Polygon.io) liefert im kostenlosen Plan 2 Jahre Minutenaggregate, je Anfrage höchstens 50.000 Minuten
(bei großen Titeln rund 2 Monate), mindestens 12,5 s Abstand (das Modul massive hält ihn ein). Gefüllt wird von heute rückwärts. Danach setzt Yahoo die Reihe fort
(30-Minuten-Kerzen der letzten 60 Tage, viele Titel in einer Anfrage). Ohne Massive-Datei reicht Yahoo 60 Tage zurück.
Gespeichert werden nur abgeschlossene Handelstage (13 Kerzen; verkürzte Tage vor Feiertagen 7).

kerzen(ticker, tages=None) -> 30-Minuten-Kerzen (Index: Uhrzeit New York, ohne Zeitzone), auf die Tageskurse der App
    ausgerichtet: jeder Tag wird mit Tagesschluss (Yahoo, dividendenbereinigt) / Schluss der letzten 30-Minuten-Kerze
    skaliert, damit Zonen, Wertbereiche und POC genau auf dem Tageschart liegen.
lesen(ticker)        -> gespeicherte Kerzen oder None (ohne Abruf)
schritt(ticker)      -> eine Anfrage bei Massive: die jüngste Lücke der letzten 2 Jahre (neueste zuerst)
luecke(ticker)       -> jüngste fehlende Handelstage oder None
fortsetzen(ticker_liste) -> Yahoo, letzte 60 Tage, an die gespeicherten Reihen anhängen
"""
import json
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "tpo")
NY = ZoneInfo("America/New_York")
SPALTEN = ["Open", "High", "Low", "Close", "Volume"]


def _pfad(ticker):
    return os.path.join(SPEICHER, f"{ticker.upper().replace('^', '_')}.csv")


# Titel an Börsen außerhalb der USA (aus den Watchlists, 4.11.2026): eigene Sitzung in Ortszeit, Kerzen nur über Yahoo
# (Massive führt nur US-Titel; Yahoo liefert 60 Tage, danach wächst die Reihe mit jedem Abendlauf)
SITZUNGEN = {".DE": ("Europe/Berlin", 540, 1050), ".F": ("Europe/Berlin", 540, 1050),
             ".MI": ("Europe/Rome", 540, 1050), ".PA": ("Europe/Paris", 540, 1050),
             ".AS": ("Europe/Amsterdam", 540, 1050), ".BR": ("Europe/Brussels", 540, 1050),
             ".MC": ("Europe/Madrid", 540, 1050), ".SW": ("Europe/Zurich", 540, 1040),
             ".ST": ("Europe/Stockholm", 540, 1050), ".CO": ("Europe/Copenhagen", 540, 1020),
             ".HE": ("Europe/Helsinki", 600, 1110), ".OL": ("Europe/Oslo", 540, 980),
             ".L": ("Europe/London", 480, 990)}


def _ort(ticker):
    """(Zeitzone, Beginn, Ende in Minuten) der regulären Sitzung; ohne Börsenendung New York 9:30–16:00."""
    t = (ticker or "").upper()
    for endung, (zone, a, e) in SITZUNGEN.items():
        if t.endswith(endung):
            return ZoneInfo(zone), a, e
    return NY, 570, 960


def auslaendisch(ticker):
    return _ort(ticker)[0] is not NY


def _sitzung(df, ticker=None):
    """Nur reguläre Sitzung (New York 9:30–16:00, sonst die der Heimatbörse); Index ohne Zeitzone (Ortszeit)."""
    zone, a, e = _ort(ticker)
    if df.index.tz is not None:
        df = df.tz_convert(zone).tz_localize(None)
    t = df.index.hour * 60 + df.index.minute
    return df[(t >= a) & (t < e)]


def _abgeschlossen(df, ticker=None):
    """Heutigen Tag verwerfen, solange die Sitzung nicht beendet ist (15 Minuten nach Schluss, Ortszeit)."""
    if df.empty:
        return df
    zone, _, e = _ort(ticker)
    jetzt = datetime.now(zone)
    if df.index[-1].date() == jetzt.date() and jetzt.hour * 60 + jetzt.minute < e + 15:
        return df[df.index.date < jetzt.date()]
    return df


def lesen(ticker):
    p = _pfad(ticker)
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, parse_dates=["Zeit"], index_col="Zeit")
    return df if len(df) else None


def _speichern(ticker, neu):
    os.makedirs(SPEICHER, exist_ok=True)
    alt = lesen(ticker)
    df = neu if alt is None else pd.concat([alt, neu])
    df = df[~df.index.duplicated(keep="last")].sort_index()[SPALTEN]
    df.index.name = "Zeit"
    df.to_csv(_pfad(ticker), float_format="%.4f")
    return df


JAHRE = 2
LEER = os.path.join(SPEICHER, "_leer.json")   # Zeiträume ohne Kerzen je Titel (vor dem Börsengang, Feiertage, Handelsstopp)


def _kalender():
    """Handelstage der letzten JAHRE Jahre bis zum letzten abgeschlossenen Tag: Tage des S&P 500 aus daten/kurse, danach
    Werktage."""
    p = os.path.join(HIER, "..", "daten", "kurse", "_GSPC.csv")
    tage = pd.DatetimeIndex(pd.read_csv(p, usecols=["Datum"], parse_dates=["Datum"])["Datum"]) if os.path.exists(p) \
        else pd.DatetimeIndex([])
    jetzt = datetime.now(NY)
    ende = pd.Timestamp(jetzt.date()) - pd.Timedelta(days=0 if (jetzt.hour, jetzt.minute) >= (16, 15) else 1)
    beginn = ende - pd.DateOffset(years=JAHRE)
    rest = pd.bdate_range(tage.max() + pd.Timedelta(days=1) if len(tage) else beginn, ende)
    alle = tage.union(rest)
    return alle[(alle >= beginn) & (alle <= ende)]


def _leer_laden():
    try:
        return json.load(open(LEER, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _leer_merken(ticker, zeitraeume):
    if not zeitraeume:
        return
    alle = _leer_laden()
    alle.setdefault(ticker.upper(), []).extend([[f"{a:%Y-%m-%d}", f"{b:%Y-%m-%d}"] for a, b in zeitraeume])
    os.makedirs(SPEICHER, exist_ok=True)
    json.dump(alle, open(LEER, "w", encoding="utf-8"))


def luecke(ticker, kalender=None):
    """Jüngste Lücke (erster und letzter fehlender Handelstag) in den letzten JAHRE Jahren, sonst None."""
    kalender = _kalender() if kalender is None else kalender
    df = lesen(ticker)
    da = set(df.index.normalize()) if df is not None else set()
    leer = _leer_laden().get(ticker.upper(), [])

    def gedeckt(t):
        k = f"{t:%Y-%m-%d}"
        return t in da or any(a <= k <= b for a, b in leer)
    i = len(kalender) - 1
    while i >= 0 and gedeckt(kalender[i]):
        i -= 1
    if i < 0:
        return None
    e = i
    while i > 0 and not gedeckt(kalender[i - 1]):
        i -= 1
    return kalender[i], kalender[e]


def schritt(ticker, kalender=None):
    """Eine Anfrage bei Massive: die jüngste Lücke, neueste Kerzen zuerst. Massive liefert je Anfrage höchstens 50.000
    Minuten (Vor- und Nachbörse zählen mit), bei großen Titeln rund 2 Monate; der nächste Schritt setzt dort fort.
    Gibt einen Satz für die Anzeige zurück."""
    if auslaendisch(ticker):                     # Massive führt nur US-Titel: Yahoo (60 Tage, wächst täglich)
        n = fortsetzen([ticker]).get(ticker.upper(), 0)
        return f"{n} neue Kerzen über Yahoo (Börse außerhalb der USA)"
    import massive
    kalender = _kalender() if kalender is None else kalender
    l_ = luecke(ticker, kalender)
    if l_ is None:
        return "vollständig"
    s, e = l_
    sym = ticker.upper().replace("-", ".")
    d = massive._abruf(f"/v2/aggs/ticker/{sym}/range/30/minute/{s:%Y-%m-%d}/{e:%Y-%m-%d}"
                       f"?adjusted=true&sort=desc&limit=50000")
    r = d.get("results") or []
    df = pd.DataFrame(r)
    if len(df):
        df.index = pd.to_datetime(df["t"], unit="ms", utc=True)
        df = _abgeschlossen(_sitzung(df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close",
                                                        "v": "Volume"})[SPALTEN]))
    if not len(df):
        _leer_merken(ticker, [(s, e)])           # z. B. vor dem Börsengang
        return f"keine Kerzen {s:%d.%m.%Y}–{e:%d.%m.%Y}"
    _speichern(ticker, df)
    frueh, spaet = df.index.min().normalize(), df.index.max().normalize()
    tage = set(df.index.normalize())
    # leer sind nur fehlende Tage ZWISCHEN den gelieferten (Feiertag, Handelsstopp). Fehlen die jüngsten Tage, hat Massive
    # sie noch nicht veröffentlicht (kostenloser Plan: erst am Folgetag) – die holt der nächste Lauf
    leer = [(t, t) for t in kalender[(kalender >= frueh) & (kalender <= spaet)] if t not in tage]
    if not d.get("next_url"):                    # Massive hat davor nichts mehr: Rest der Lücke ist leer
        leer += [(s, frueh - pd.Timedelta(days=1))] if frueh > s else []
    _leer_merken(ticker, leer)
    return f"{len(df)} Kerzen {frueh:%d.%m.%Y}–{spaet:%d.%m.%Y}"


def fortsetzen(ticker_liste, tage=60):
    """Fortsetzung über Yahoo für viele Titel in einer Anfrage (je 100 Titel). Gibt {ticker: Anzahl neuer Kerzen} zurück."""
    import yfinance as yf
    _mehr_dateien()
    erg = {}
    liste = [t.upper() for t in ticker_liste]
    for a in range(0, len(liste), 50):
        teil = liste[a:a + 50]
        try:                                     # ohne Parallel-Abruf: Yahoos Zeitzonen-Speicher öffnet sonst je Faden
            roh = yf.download(teil, period=f"{tage}d", interval="30m", auto_adjust=False, progress=False,
                              group_by="ticker", threads=False, prepost=False)   # Dateien, bis macOS abbricht
        except Exception:  # noqa: BLE001 – ein Paket scheitert, die übrigen laufen weiter
            continue
        if roh is None or roh.empty:
            continue
        for t in teil:
            try:
                d = roh[t] if isinstance(roh.columns, pd.MultiIndex) else roh
            except KeyError:
                continue
            d = d[SPALTEN].dropna()
            if d.empty:
                continue
            d = _abgeschlossen(_sitzung(d, t), t)
            alt = lesen(t)
            vorher = 0 if alt is None else len(alt)
            erg[t] = len(_speichern(t, d)) - vorher
    return erg


def heute(ticker):
    """30-Minuten-Kerzen des laufenden Börsentags von Yahoo (bis 15 Minuten verzögert, letzte Kerze unvollständig) –
    nur für den Knopf „Kurse aktualisieren“, wird nicht gespeichert. None außerhalb der Sitzung oder ohne Antwort."""
    import yfinance as yf
    d = yf.download(ticker.upper(), period="1d", interval="30m", auto_adjust=False, progress=False, threads=False,
                    prepost=False)
    if d is None or d.empty:
        return None
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d = _sitzung(d[SPALTEN].dropna(), ticker)
    d = d[d.index.date == datetime.now(_ort(ticker)[0]).date()]
    return d if len(d) else None


def _mehr_dateien():
    """macOS erlaubt einem Programm zunächst nur 256 offene Dateien; für den Abendlauf auf 4.096 anheben."""
    try:
        import resource
        weich, hart = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (min(4096, hart), hart))
    except (ImportError, ValueError, OSError):
        pass


def _veraltet(df, tages):
    """Fehlen abgeschlossene Handelstage der Tagesreihe in den 30-Minuten-Kerzen?"""
    if tages is None or df is None or not len(tages):
        return df is None
    return df.index[-1].normalize() < tages.index[-1].normalize()


def ausrichten(df30, tages):
    """Jeden Tag mit Tagesschluss / letztem 30-Minuten-Schluss skalieren (Dividenden- und Splitbereinigung wie im Tageschart).
    Tage, die in der Tagesreihe fehlen, fallen weg."""
    if tages is None:
        return df30
    tag = df30.index.normalize()
    letzter = df30.groupby(tag)["Close"].last()
    ziel = tages["Close"].copy()
    ziel.index = pd.to_datetime(ziel.index).normalize()
    faktor = (ziel.reindex(letzter.index) / letzter).dropna()
    df = df30[tag.isin(faktor.index)].copy()
    f = faktor.reindex(df.index.normalize()).to_numpy()
    for s in ("Open", "High", "Low", "Close"):
        df[s] = df[s].to_numpy() * f
    return df


def kerzen(ticker, tages=None, abruf=True):
    """30-Minuten-Kerzen für die Rechnung. Fehlen sie, wird befüllt (Massive, sonst Yahoo); fehlen nur die letzten Tage,
    setzt Yahoo fort. abruf=False: nur der Speicher (Massenlauf)."""
    df = lesen(ticker)
    if abruf and (df is None or _veraltet(df, tages)):
        try:                                     # Massive: jüngste Lücke; ohne Massive Yahoo (60 Tage)
            schritt(ticker)
        except Exception:  # noqa: BLE001
            try:
                fortsetzen([ticker])
            except Exception:  # noqa: BLE001
                pass
        df = lesen(ticker)
    if df is None:
        return None
    return ausrichten(df, tages)


# ── Wer im Abendlauf ist (4.11.2026) ──
# Gesamtmarkt, Revier, Watchlists und jeder Titel, dessen Titelseite geöffnet wurde. Entfernt wird nur, was gelöscht
# wurde: aus der Watchlist genommen (vergessen) oder aus dem Revier gefallen. Seine Datei wandert nach _to_delete/tpo/.
FEST = ["SPY", "QQQ", "IWM"]          # Gesamtmarkt (S&P 500 über SPY) für den Marktzustand
GEOEFFNET = os.path.join(SPEICHER, "_geoeffnet.json")
EINSTELLUNGEN = os.path.join(HIER, "..", "einstellungen")


def _geoeffnet():
    try:
        return set(json.load(open(GEOEFFNET, encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def merken(ticker):
    """Titelseite geöffnet: der Titel gehört ab jetzt zum Abendlauf, bis er gelöscht wird."""
    g = _geoeffnet()
    if ticker.upper() not in g:
        g.add(ticker.upper())
        os.makedirs(SPEICHER, exist_ok=True)
        json.dump(sorted(g), open(GEOEFFNET, "w", encoding="utf-8"))


def _watchlists():
    """Titel aller Watchlists (einstellungen/watchlists.json), jeder einmal."""
    import watchlists
    return watchlists.alle()


def lauf_liste():
    rv = pd.read_csv(os.path.join(EINSTELLUNGEN, "revier.csv"))
    liste = list(FEST)
    for t in list(rv["ticker"].astype(str).str.upper()) + _watchlists() + sorted(_geoeffnet()):
        if t not in liste:
            liste.append(t)
    return liste


def _archivieren(ticker):
    ziel = os.path.join(HIER, "..", "_to_delete", "tpo")
    os.makedirs(ziel, exist_ok=True)
    quelle = _pfad(ticker)
    if os.path.exists(quelle):
        os.replace(quelle, os.path.join(ziel, os.path.basename(quelle)))


def vergessen(ticker):
    """Titel gelöscht (z. B. aus der Watchlist genommen): nicht mehr geöffnet-gemerkt; fehlt er auch in Revier und
    Watchlists, wird seine Datei archiviert."""
    g = _geoeffnet()
    if ticker.upper() in g:
        g.discard(ticker.upper())
        json.dump(sorted(g), open(GEOEFFNET, "w", encoding="utf-8"))
    if ticker.upper() not in lauf_liste():
        _archivieren(ticker)


def aufraeumen():
    """Dateien von Titeln, die nicht mehr in der Lauf-Liste stehen, nach _to_delete/tpo/ verschieben. Gibt sie zurück."""
    if not os.path.isdir(SPEICHER):
        return []
    liste = set(lauf_liste())
    weg = [f[:-4] for f in os.listdir(SPEICHER) if f.endswith(".csv") and f[:-4].replace("_", "^") not in liste
           and f[:-4] not in liste]
    for t in weg:
        _archivieren(t)
    return weg
