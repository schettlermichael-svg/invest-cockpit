"""Watchlists (Schritt 6, 4.11.2026): eigene Listen der App in einstellungen/watchlists.json ({Name: [Ticker, …]}).

Ticker in Yahoo-Schreibweise (HWM, BRK-B, RHM.DE). Ein Titel steht in einer Liste höchstens einmal; in mehreren Listen
darf er stehen – Abendlauf, Daten und Kartentisch führen ihn trotzdem nur einmal. Wird ein Titel aus seiner letzten
Liste genommen, gilt er als gelöscht (tpo_daten.vergessen): ohne Revier fällt er aus dem Abendlauf.
Start: einmaliger Import der TradingView-Watchlists (nur lesen; in TradingView wird nichts geändert).
"""
import json
import os

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
    try:
        w = json.load(open(DATEI, encoding="utf-8"))
        return {n: list(dict.fromkeys(t.upper() for t in l)) for n, l in w.items()}
    except (OSError, ValueError):
        return {}


def speichern(w):
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    w = {n: list(dict.fromkeys(t.upper() for t in l)) for n, l in w.items()}
    json.dump(w, open(DATEI, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def alle():
    """Alle Titel aller Listen, jeder einmal, in Listenreihenfolge."""
    return list(dict.fromkeys(t for l in laden().values() for t in l))


def listen_von(ticker):
    return [n for n, l in laden().items() if ticker.upper() in l]


def setzen(ticker, name, drin):
    """Titel in Liste `name` aufnehmen (drin=True) oder herausnehmen. Neue Liste entsteht beim ersten Titel.
    Aus der letzten Liste genommen: gilt als gelöscht."""
    tk, w = ticker.upper(), laden()
    if drin:
        w.setdefault(name, [])
        if tk not in w[name]:
            w[name].append(tk)
        speichern(w)
        return
    if name in w and tk in w[name]:
        w[name].remove(tk)
        speichern(w)
    if not listen_von(tk):
        import tpo_daten
        tpo_daten.vergessen(tk)


def importieren(tv_listen):
    """TradingView-Listen [{name, symbols}] zusammenführen; bestehende Listen bleiben, Doppelte fallen weg.
    Gibt (übernommen, übersprungen) zurück."""
    w, ueber, weg = laden(), 0, []
    for l in tv_listen:
        tks = [von_tv(s) for s in l.get("symbols", [])]
        weg += [s for s, t in zip(l.get("symbols", []), tks) if t is None and not s.startswith("###")]
        tks = [t for t in tks if t]
        if not tks:
            continue
        ziel = w.setdefault(l["name"], [])
        for t in tks:
            if t not in ziel:
                ziel.append(t)
                ueber += 1
    speichern(w)
    return ueber, weg


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


def einfuegen(text, name=STANDARD):
    """Eingefügte Ticker in die Liste `name`; gibt die Zahl der neuen zurück."""
    w = laden()
    ziel = w.setdefault(name, [])
    neu = [t for t in aus_text(text) if t not in ziel]
    ziel.extend(neu)
    speichern(w)
    return len(neu)


def liste_loeschen(name):
    """Ganze Liste entfernen. Titel, die in keiner anderen Liste stehen, gelten als gelöscht (tpo_daten.vergessen:
    ohne Revier fallen sie aus dem Abendlauf). Gibt die Zahl der so gelöschten Titel zurück."""
    w = laden()
    titel = w.pop(name, [])
    speichern(w)
    import tpo_daten
    weg = [t for t in titel if not listen_von(t)]
    for t in weg:
        tpo_daten.vergessen(t)
    return len(weg)
