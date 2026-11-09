"""Die Watchlist (Schritt 6, 4.11.2026; seit 6.11.2026 nur noch eine Liste): einstellungen/watchlists.json
({"Watchlist": [Ticker, …]}). Ticker in Yahoo-Schreibweise (HWM, BRK-B, RHM.DE), jeder einmal. Ein Titel steht auf der
Watchlist oder nicht. Heruntergenommen gilt er als gelöscht (tpo_daten.vergessen): ohne Revier fällt er aus dem Abendlauf.
Der Server legt die Datei alle 10 Minuten ab, ein stündlicher Abgleich trägt Änderungen in TradingView ein (App → TV).
"""
import json
import os
from dateien import json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "einstellungen", "watchlists.json")
STANDARD = "Watchlist"

# TradingView-Börse → Yahoo-Endung (US-Börsen ohne Endung)
BOERSEN = {"XETR": ".DE", "FWB": ".F", "MIL": ".MI", "EURONEXT": ".PA", "OSL": ".OL", "OMXSTO": ".ST",
           "OMXCOP": ".CO", "OMXHEX": ".HE", "LSE": ".L", "SIX": ".SW", "BME": ".MC"}
US = {"NYSE", "NASDAQ", "AMEX", "NYSEARCA", "BATS", "OTC"}


def von_tv(symbol):
    """'NYSE:HWM' → 'HWM', 'XETR:RHM' → 'RHM.DE', 'OMXSTO:SAAB_B' → 'SAAB-B.ST', 'LSE:BA.' → 'BA.L'.
    Abschnitte (###…) und Indizes (SP:SPX, IG:DAX) → None."""
    if not symbol or symbol.startswith("###") or ":" not in symbol:
        return None
    boerse, name = symbol.split(":", 1)
    name = name.rstrip(".").replace("_", "-")
    if boerse in US:
        return name.replace(".", "-").upper()
    if boerse in BOERSEN:
        return (name + BOERSEN[boerse]).upper()
    return None


def zu_tv(ticker):
    """Umkehrung für den TradingView-Knopf bei Titeln außerhalb der USA, sonst None."""
    t = ticker.upper()
    for boerse, endung in BOERSEN.items():
        if t.endswith(endung):
            name = t[: -len(endung)]
            name = name.replace("-", "_") if boerse.startswith("OMX") else name
            return f"{boerse}:{name}." if boerse == "LSE" and len(name) <= 2 else f"{boerse}:{name}"
    return None


def laden():
    """Die eine Watchlist als {"Watchlist": [Ticker, …]}. Seit 06.11.2026 gibt es nur noch diese Liste: stehen in der
    Datei noch andere Listen (z. B. „Active Watchlist“ aus dem TradingView-Import), werden ihre Titel einmalig in die
    Watchlist übernommen und die Listen entfernt (der Abgleich leert sie dann auch in TradingView)."""
    try:
        w = json.load(open(DATEI, encoding="utf-8"))
    except (OSError, ValueError):
        return {STANDARD: []}
    titel = list(dict.fromkeys(t.upper() for t in w.get(STANDARD, [])))
    titel += [t for t in dict.fromkeys(t.upper() for n, l in w.items() if n != STANDARD for t in l) if t not in titel]
    if set(w) != {STANDARD}:
        speichern({STANDARD: titel})
    return {STANDARD: titel}


def speichern(w):
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    w = {STANDARD: list(dict.fromkeys(t.upper() for t in w.get(STANDARD, [])))}
    json_schreiben(DATEI, w, ensure_ascii=False, indent=1)


def alle():
    """Alle Titel der Watchlist in ihrer Reihenfolge."""
    return laden()[STANDARD]


def drin(ticker):
    return ticker.upper() in alle()


def listen_von(ticker):
    """[„Watchlist“], wenn der Titel darauf steht, sonst [] (Form für den Kartentisch)."""
    return [STANDARD] if drin(ticker) else []


def setzen(ticker, auf):
    """Titel auf die Watchlist (auf=True) oder herunter. Heruntergenommen gilt er als gelöscht: ohne Revier fällt er aus
    dem Abendlauf (tpo_daten.vergessen)."""
    tk, liste = ticker.upper(), alle()
    if auf and tk not in liste:
        speichern({STANDARD: liste + [tk]})
    elif not auf and tk in liste:
        liste.remove(tk)
        speichern({STANDARD: liste})
        import tpo_daten
        tpo_daten.vergessen(tk)


def einfuegen(text):
    """Eingefügte Ticker (Finviz, SEPA-Scanner, TradingView) auf die Watchlist; gibt die Zahl der neuen zurück."""
    liste = alle()
    neu = [t for t in aus_text(text) if t not in liste]
    speichern({STANDARD: liste + neu})
    return len(neu)


def aus_text(text):
    """Ticker aus eingefügtem Text (Finviz, SEPA-Scanner, TradingView-Export): getrennt durch Komma, Leerzeichen oder
    Zeilen; „BÖRSE:TICKER“ wird umgerechnet, Abschnitte und Indizes fallen weg. Doppelte einmal."""
    import re
    roh = [x.strip().upper() for x in re.split(r"[\s,;]+", text or "") if x.strip()]
    aus = []
    for x in roh:
        t = von_tv(x) if ":" in x else (x if re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]{0,11}", x) else None)
        if t and "." in t and not t.endswith(tuple(BOERSEN.values())):
            t = t.replace(".", "-")              # Klassenaktien: BRK.B → BRK-B (Yahoo)
        if t and t not in aus:
            aus.append(t)
    return aus
