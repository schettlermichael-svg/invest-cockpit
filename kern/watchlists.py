"""Die Listen (Schritt 6, 4.11.2026): einstellungen/watchlists.json ({"Watchlist": [Ticker, …], "Trade": [Ticker, …]}).
Ticker in Yahoo-Schreibweise (HWM, BRK-B, RHM.DE), jeder einmal je Liste. Seit 06.11.2026 die eine Watchlist, seit
23.11.2026 daneben die Liste „Trade“ (die Titel, die Micky handeln will), wie in TradingView. Ein Titel, der auf keiner
Liste mehr steht, gilt als gelöscht (tpo_daten.vergessen): ohne Revier fällt er aus dem Abendlauf.
Abgleich mit TradingView in beide Richtungen (23.11.2026): Der Server legt die Datei alle 10 Minuten auf den Zweig
„daten“; die stündliche Claude-Aufgabe vergleicht App, TradingView und den letzten gemeinsamen Stand, trägt Änderungen
der App in TradingView ein und legt Änderungen aus TradingView als von_tv.json ab, die der Server mit anwenden() übernimmt.
"""
import json
import os
from dateien import json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "einstellungen", "watchlists.json")
STANDARD = "Watchlist"
TRADE = "Trade"
LISTEN = (STANDARD, TRADE)
ZEICHEN = {STANDARD: "◆", TRADE: "🎯"}

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


def _eins(liste):
    return list(dict.fromkeys(t.upper() for t in liste))


def laden():
    """Beide Listen als {"Watchlist": [Ticker, …], "Trade": [Ticker, …]}. Stehen in der Datei noch andere Listen (z. B.
    „Active Watchlist“ aus dem ersten TradingView-Import), werden ihre Titel einmalig in die Watchlist übernommen und die
    Listen entfernt."""
    try:
        w = json.load(open(DATEI, encoding="utf-8"))
    except (OSError, ValueError):
        return {n: [] for n in LISTEN}
    titel = _eins(w.get(STANDARD, []))
    titel += [t for t in _eins(t for n, l in w.items() if n not in LISTEN for t in l) if t not in titel]
    aus = {STANDARD: titel, TRADE: _eins(w.get(TRADE, []))}
    if set(w) - set(LISTEN):
        speichern(aus)
    return aus


def speichern(w):
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    json_schreiben(DATEI, {n: _eins(w.get(n, [])) for n in LISTEN}, ensure_ascii=False, indent=1)


def liste(name=STANDARD):
    """Die Titel einer Liste in ihrer Reihenfolge."""
    return laden()[name]


def alle():
    """Alle Titel beider Listen, jeder einmal (Watchlist zuerst) – sie werden im Abendlauf mitgerechnet."""
    w = laden()
    return _eins(w[STANDARD] + w[TRADE])


def drin(ticker, name=STANDARD):
    return ticker.upper() in liste(name)


def zeichen(ticker, w=None):
    """Die Marken eines Titels: „◆“ (Watchlist), „🎯“ (Trade), beide oder leer."""
    w = w or laden()
    return " ".join(ZEICHEN[n] for n in LISTEN if ticker.upper() in w[n])


def setzen(ticker, auf, name=STANDARD):
    """Titel auf eine Liste (auf=True) oder herunter. Steht er danach auf keiner Liste mehr, gilt er als gelöscht: ohne
    Revier fällt er aus dem Abendlauf (tpo_daten.vergessen)."""
    tk, w = ticker.upper(), laden()
    if auf and tk not in w[name]:
        w[name].append(tk)
        speichern(w)
    elif not auf and tk in w[name]:
        w[name].remove(tk)
        speichern(w)
        if not any(tk in w[n] for n in LISTEN):
            import tpo_daten
            tpo_daten.vergessen(tk)


def einfuegen(text, name=STANDARD):
    """Eingefügte Ticker (Finviz, SEPA-Scanner, TradingView) auf eine Liste; gibt die Zahl der neuen zurück."""
    w = laden()
    neu = [t for t in aus_text(text) if t not in w[name]]
    w[name] += neu
    speichern(w)
    return len(neu)


def anwenden(aenderung):
    """Änderungen aus TradingView übernehmen (vom Server aufgerufen, werkzeuge/von_tv_anwenden.py):
    {"listen": {"Watchlist": {"neu": [...], "weg": [...]}, "Trade": {...}}}. Entfernte Titel gehen über setzen() – wer auf
    keiner Liste mehr steht, wird vergessen wie beim Herunternehmen in der App. → Zeilen für das Protokoll."""
    zeilen = []
    for name, d in (aenderung.get("listen") or {}).items():
        if name not in LISTEN:
            continue
        neu = [t for t in _eins(d.get("neu") or []) if not drin(t, name)]
        for t in neu:
            setzen(t, True, name)
        weg = [t for t in _eins(d.get("weg") or []) if drin(t, name)]
        for t in weg:
            setzen(t, False, name)
        if neu or weg:
            zeilen.append(f"{name}: +{', '.join(neu) or '–'} / −{', '.join(weg) or '–'}")
    return zeilen


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
