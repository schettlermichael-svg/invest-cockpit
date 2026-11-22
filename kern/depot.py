"""Risikomanagement (Schritt 9, 04.11.2026): Konto, Risiko je Trade, Positionen, Stückzahl, Depot-Hitze, Nach dem Kauf.

Speicher: einstellungen/depot.json
  {"konto": Euro oder null, "risiko_pct": 1.0, "hitze_max_pct": 6.0, "quelle": "Hand" | "Scalable", "stand": "…",
   "positionen": [{"ticker", "seite": "long"|"short", "stueck", "einstieg", "stopp", "datum",
                   "ko": {"schwelle", "bezug"} oder null, "notiz"}]}
Preise in der Währung des Titels (US-Titel in $), Konto und Risiko in Euro; umgerechnet mit dem Tageskurs von Yahoo
(EURUSD=X usw.). Bei Knock-outs bewegt sich das Zertifikat um Basiswert × Bezugsverhältnis.
Regeln: Risiko je Trade = Konto × risiko_pct (Minervini 0,5–2,5 %, Voreinstellung 1 %); Depot-Hitze = Summe des offenen
Risikos (Einstieg bis Stopp, solange der Stopp unter dem Einstieg liegt) höchstens 6 % des Kontos; Verlustgrenze 8 % vom
Einstieg (O'Neil); Stopp auf Einstand ab 2R Gewinn (Minervini); Gewinnziel 20–25 % (O'Neil, außer +20 % in höchstens
3 Wochen: 8 Wochen halten).
Scalable („Agentic Investing“, MCP): sobald verbunden, schreibt Claude die Positionen über uebernehmen() hierher; Stopps
und Knock-out-Daten bleiben erhalten, wenn der Titel schon geführt wird.
"""
import json
import os
import time
from dateien import json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "einstellungen", "depot.json")
LEER = {"konto": None, "risiko_pct": 1.0, "hitze_max_pct": 6.0, "quelle": "Hand", "stand": None, "positionen": []}
WAEHRUNG = {".DE": "EUR", ".F": "EUR", ".MI": "EUR", ".PA": "EUR", ".AS": "EUR", ".BR": "EUR", ".MC": "EUR",
            ".HE": "EUR", ".L": "GBp", ".SW": "CHF", ".ST": "SEK", ".CO": "DKK", ".OL": "NOK"}
VERLUSTGRENZE = 0.08


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
TEILGEWINN_AB_TAG = 3   # Kullamägi: Teilgewinn am Tag 3 …
TEILGEWINN_BIS_TAG = 5  # … bis Tag 5 nach dem Kauf
SQUAT_DRITTEL = 0.33    # Squat: Schluss im unteren Drittel der Tagesspanne
TENNIS_RUECK = 0.97     # Tennisball: Rücksetzer mindestens 3 % unter den Einstieg …
TENNIS_TAGE = 5         # … und in höchstens 5 Tagen auf neues Hoch
RESET_NAH = 0.98        # Reset: Einstieg höchstens 2 % unter dem Pivot
FUEHRER_PLUS = 20       # Führer: +20 % in höchstens 3 Wochen (O'Neil)
NACHZIEHEN_R = 2  # Stopp nachziehen ab 2R Gewinn (Minervini)


def laden():
    try:
        d = json.load(open(DATEI, encoding="utf-8"))
        return {**LEER, **d}
    except (OSError, ValueError):
        return dict(LEER, positionen=[])


def speichern(d):
    d["stand"] = time.strftime("%d.%m.%Y %H:%M")
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    json_schreiben(DATEI, d, ensure_ascii=False, indent=1)


def einstellen(konto=None, risiko_pct=None):
    d = laden()
    if konto is not None:
        d["konto"] = float(konto) if konto else None
        if d["konto"]:
            d["konto_hoch"] = max(d.get("konto_hoch") or 0, d["konto"])
    if risiko_pct is not None:
        d["risiko_pct"] = float(risiko_pct)
    speichern(d)


def position(ticker):
    return next((p for p in laden()["positionen"] if p["ticker"] == ticker.upper()), None)


def setzen(ticker, **werte):
    """Position anlegen oder ändern (nur übergebene Felder)."""
    d = laden()
    p = next((p for p in d["positionen"] if p["ticker"] == ticker.upper()), None)
    if p is None:
        p = {"ticker": ticker.upper(), "seite": "long", "stueck": 0, "einstieg": None, "stopp": None,
             "datum": time.strftime("%Y-%m-%d"), "ko": None, "notiz": ""}
        d["positionen"].append(p)
    p.update({k: v for k, v in werte.items() if v is not None})
    speichern(d)


def schliessen(ticker, ausstieg=None):
    """Position schließen; mit Ausstiegskurs wird der Trade in der Bilanz verbucht (Minervini-Abgleich bei den Stopps)."""
    d = laden()
    p = position(ticker)
    if p and ausstieg and p.get("einstieg"):
        lang = p.get("seite", "long") == "long"
        ergebnis = ((ausstieg / p["einstieg"] - 1) if lang else (1 - ausstieg / p["einstieg"])) * 100
        d.setdefault("geschlossen", []).append({"ticker": p["ticker"], "seite": p.get("seite", "long"),
                                                "einstieg": p["einstieg"], "ausstieg": ausstieg,
                                                "ergebnis_pct": round(ergebnis, 2), "datum": time.strftime("%Y-%m-%d")})
    d["positionen"] = [p for p in d["positionen"] if p["ticker"] != ticker.upper()]
    speichern(d)


def bilanz():
    """Eigene Zahlen aus den geschlossenen Trades: Anzahl, Trefferquote, Durchschnittsgewinn und -verlust in %."""
    g = laden().get("geschlossen") or []
    if not g:
        return None
    gew = [x["ergebnis_pct"] for x in g if x["ergebnis_pct"] > 0]
    ver = [-x["ergebnis_pct"] for x in g if x["ergebnis_pct"] <= 0]
    return {"anzahl": len(g), "treffer_pct": len(gew) / len(g) * 100,
            "schnitt_gewinn": sum(gew) / len(gew) if gew else None,
            "schnitt_verlust": sum(ver) / len(ver) if ver else None}


def uebernehmen(liste, quelle="Scalable"):
    """Positionen aus Scalable [{ticker, stueck, einstieg, seite?, ko?}] übernehmen; vorhandene Stopps, Knock-out-Daten
    und Notizen bleiben, nicht mehr gehaltene Titel fallen weg."""
    d = laden()
    alt = {p["ticker"]: p for p in d["positionen"]}
    neu = []
    for x in liste:
        tk = x["ticker"].upper()
        p = dict(alt.get(tk) or {"ticker": tk, "seite": "long", "stopp": None, "datum": time.strftime("%Y-%m-%d"),
                                 "ko": None, "notiz": ""})
        p.update({k: x[k] for k in ("stueck", "einstieg", "seite", "ko") if x.get(k) is not None})
        neu.append(p)
    d["positionen"], d["quelle"] = neu, quelle
    speichern(d)


# ── Währung ──
def waehrung(ticker):
    t = ticker.upper()
    return next((w for e, w in WAEHRUNG.items() if t.endswith(e)), "USD")


def fx(waehrung_):
    """Einheiten der Titelwährung je Euro (USD: EURUSD); GBp in Pence. None ohne Kurs."""
    if waehrung_ == "EUR":
        return 1.0
    import daten
    basis = "GBP" if waehrung_ == "GBp" else waehrung_
    try:
        k = float(daten.kurse(f"EUR{basis}=X", jahre=1)["Close"].iloc[-1])
    except Exception:  # noqa: BLE001
        return None
    return k * 100 if waehrung_ == "GBp" else k


def zeichen_w(waehrung_):
    return {"USD": "$", "EUR": "€", "GBp": "p", "CHF": "CHF", "SEK": "kr", "DKK": "kr", "NOK": "kr"}.get(waehrung_, "")


# ── Rechnen ──
def risiko_euro(d=None):
    d = d or laden()
    return d["konto"] * d["risiko_pct"] / 100 if d.get("konto") else None




def offenes_risiko(p, k=None):
    """Euro, die bis zum Stopp verloren gingen (gemessen vom Einstieg; 0, sobald der Stopp den Einstieg sichert)."""
    if not p.get("stopp") or not p.get("einstieg") or not p.get("stueck"):
        return None
    k = k or fx(waehrung(p["ticker"]))
    if not k:
        return None
    lang = p.get("seite", "long") == "long"
    weg = (p["einstieg"] - p["stopp"]) if lang else (p["stopp"] - p["einstieg"])
    bezug = (p.get("ko") or {}).get("bezug") or 1
    return max(0.0, weg) * p["stueck"] * bezug / k


VERLUSTBREMSE = 10.0        # Konto 10 % unter seinem Höchststand: Zeichen, Risiko je Trade zu halbieren (Minervini)


def verlustbremse(d=None):
    """(Ampel, Text) oder None – nur ein Zeichen, die Stückzahl ändert sich nicht von selbst."""
    d = d or laden()
    if not d.get("konto") or not d.get("konto_hoch"):
        return None
    ab = (1 - d["konto"] / d["konto_hoch"]) * 100
    if ab < VERLUSTBREMSE:
        return None
    return ("rot", _deutsch(f"Verlustbremse: Konto {ab:.1f} % unter seinem Höchststand – Minervini: Risiko je Trade "
                            f"halbieren, bis die Hälfte des Rückgangs aufgeholt ist (Einstellung oben, nicht automatisch)"))


def hitze(d=None):
    d = d or laden()
    summe = sum(offenes_risiko(p) or 0 for p in d["positionen"])
    pct = summe / d["konto"] * 100 if d.get("konto") else None
    ampel = ("grau" if pct is None else "grün" if pct <= d["hitze_max_pct"] * 2 / 3
             else "gelb" if pct <= d["hitze_max_pct"] else "rot")
    return {"euro": summe, "pct": pct, "ampel": ampel, "max": d["hitze_max_pct"],
            "ohne_stopp": [p["ticker"] for p in d["positionen"] if not p.get("stopp")]}


def _deutsch(text):
    import re
    return re.sub(r"(?<!\.\d)(?<!\.\d\d)(\d)\.(\d+)(?![\d.])", r"\1,\2", text)




















def nach_dem_kauf(p, df):
    return [(a, _deutsch(t)) for a, t in _nach_dem_kauf(p, df)]


def _nach_dem_kauf(p, df):
    """Zeichen nach dem Kauf als Liste (Ampel, Text) – ein System für alle Positionen (Gefechtsordnung Schritt 5,
    Micky 16.11.2026; vorher je System M/K getrennt):
    Stopp: bis Tag 3 der Anfangsstopp, danach folgt er dem 10er bzw. 20er (reiten.nachgezogen), Schluss jenseits heißt
    raus; Mauer, Kraft ohne Weg und Klimax ziehen ihn unter das Tagestief. Daneben Kullamägis Teilgewinn (Tag 3–5) und
    Minervinis Zeichen: Verlustgrenze, Stopp auf Einstand ab 2R, Squat, Tennisball, Reset, Führer. Kein festes
    Gewinnziel (Gewinne laufen lassen, Stopp nachziehen)."""
    import pandas as pd
    import reiten
    aus = []
    if df is None or not p.get("einstieg"):
        return aus
    lang = p.get("seite", "long") == "long"
    e, s = float(p["einstieg"]), p.get("stopp")
    seit = df[df.index >= pd.Timestamp(p.get("datum") or df.index[-1])]
    c = df["Close"].to_numpy(float)
    k = float(c[-1])
    g = ((k / e - 1) if lang else (1 - k / e)) * 100
    r1 = abs(e - s) if s else e * VERLUSTGRENZE
    r_mult = ((k - e) if lang else (e - k)) / r1 if r1 else None
    if not s:
        aus.append(("rot", "kein Stopp gesetzt – jede Position braucht einen Stopp vor dem Kauf (Minervini; Kullamägi: "
                           "am Tagestief des Einstiegstags)"))
    else:
        ende = reiten.ende_zeichen(df, p.get("seite", "long"))
        nz = reiten.nachgezogen(df, p.get("datum"), e, float(s), p.get("seite", "long"), ende)
        if nz and nz.get("stopp"):                 # die Zeichen unten messen am Stopp, der jetzt gilt
            s = nz["stopp"]
        if nz:
            wo = "unter" if lang else "über"
            if nz["raus"]:
                aus.append(("rot", f"Schluss {wo} dem nachgezogenen Stopp {nz['stopp']:.2f} ({nz['regel']}) – raus (Kullamägi)"))
            else:
                aus.append(("grün" if nz["linie"] else "grau",
                            f"Stopp jetzt {nz['stopp']:.2f}: {nz['regel']}" + (f", Tag {nz['tag_nr']} nach dem Kauf")))
            if nz["enger"]:
                en = nz["enger"]
                getroffen = (k < en["stopp"]) if lang else (k > en["stopp"])
                aus.append(("rot" if getroffen else "gelb",
                            f"{en['art']} am {en['tag']:%d.%m.}: Stopp enger {wo} das {'Tief' if lang else 'Hoch'} jenes Tages "
                            f"{en['stopp']:.2f} (Stopp im Markt)" + (" – erreicht" if getroffen else "")))
        tage = len(seit) - 1
        if TEILGEWINN_AB_TAG <= tage <= TEILGEWINN_BIS_TAG and g > 0 and ((s < e) if lang else (s > e)):
            aus.append(("gelb", f"Tag {tage} nach dem Kauf, {g:+.1f} %: Teilgewinn nehmen und den Stopp für den Rest auf "
                                f"Einstand {e:.2f} ziehen (Kullamägi)"))
    if g <= -VERLUSTGRENZE * 100:
        aus.append(("rot", f"Verlustgrenze: {g:.1f} % – höchstens 8 % Verlust, ohne Ausnahme (Minervini, O'Neil)"))
    if s and r_mult is not None and r_mult >= NACHZIEHEN_R and ((s < e) if lang else (s > e)):
        aus.append(("gelb", f"Stopp nachziehen: {r_mult:.1f}R Gewinn – Stopp mindestens auf Einstand {e:.2f} (Minervini)"))
    if len(seit) >= 1 and len(seit) <= 4 and lang:
        t = seit.iloc[0]
        spanne = float(t["High"] - t["Low"]) or 1
        if (float(t["Close"]) - float(t["Low"])) / spanne < SQUAT_DRITTEL:
            aus.append(("gelb", "Squat am Kauftag (Schluss im unteren Drittel) – O'Neil: oft Erholung in 1–3 Tagen; "
                                "der Stopp gilt"))
    if len(seit) >= 3 and lang:
        lo = seit["Low"].to_numpy(float)
        hi = seit["High"].to_numpy(float)
        i = int(lo.argmin())
        if i < len(lo) - 1 and lo[i] < e * TENNIS_RUECK and k > hi[:i + 1].max() and len(lo) - 1 - i <= TENNIS_TAGE:
            aus.append(("grün", "Tennisball: nach dem Rücksetzer schnell auf neues Hoch – Zeichen von Stärke (Minervini)"))
    import zirkel                                      # Pivot des Setups (Zirkel-Lauf, 22.11.2026)
    t_ = zirkel.feld(p.get("ticker", "")).get("trade") or {}
    piv = t_.get("einstieg") if t_.get("richtung", 0) > 0 and t_.get("art") in ("aufbruch", "fortsetzung") else None
    if lang and piv and e >= piv * RESET_NAH and k < piv and (not s or k > s):
        aus.append(("gelb", f"Reset beobachten: Kurs zurück unter dem Pivot {piv:.2f} – hält der Stopp, kann sich eine "
                            "neue Base bilden (Minervini)"))
    if g >= FUEHRER_PLUS and len(seit) <= 15:
        aus.append(("grün", f"+{g:.0f} % in höchstens 3 Wochen – Zeichen eines Führers; laufen lassen, Stopp nachziehen"))
    if not aus:
        aus.append(("grün", f"läuft nach Plan: {g:+.1f} %" + (f", {r_mult:.1f}R" if r_mult is not None else "")))
    return aus
