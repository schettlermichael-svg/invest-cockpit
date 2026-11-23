"""Risikomanagement (Schritt 9, 04.11.2026): Konto, Risiko je Trade, Positionen, Stückzahl, Depot-Hitze, Nach dem Kauf.

Speicher: einstellungen/depot.json
  {"konto": Euro oder null, "risiko_pct": 1.0, "hitze_max_pct": 6.0, "quelle": "Hand" | "Scalable", "stand": "…",
   "positionen": [{"ticker", "seite": "long"|"short", "stueck", "einstieg", "stopp", "datum", "pivot",
                   "ko": {"schwelle", "bezug"} oder null, "notiz"}]}
Preise in der Währung des Titels (US-Titel in $), Konto und Risiko in Euro; umgerechnet mit dem Tageskurs von Yahoo
(EURUSD=X usw.). Bei Knock-outs bewegt sich das Zertifikat um Basiswert × Bezugsverhältnis.
Kriegskasse: Risiko je Trade = Konto × risiko_pct (Voreinstellung 1 %); Depot-Hitze = Summe des offenen Risikos
(Einstieg bis Stopp, solange der Stopp unter dem Einstieg liegt) höchstens 6 % des Kontos; Verlustbremse.
Führung nach dem Kauf (Micky 23.11.2026): nur noch Zirkel und nachgezogener Stopp (nach_dem_kauf).
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


def aus_setup(ticker):
    """Das Setup des Titels aus dem letzten Zirkel-Lauf ({seite, einstieg, stopp, pivot}) oder {} – Vorgabe für eine
    neue Position: der Stopp beim Kauf ist der Stopp des Setups (Micky 23.11.2026)."""
    import zirkel
    t = zirkel.feld(ticker.upper()).get("trade") or {}
    if not t:
        return {}
    return {"seite": "long" if t["richtung"] > 0 else "short", "einstieg": t["einstieg"], "stopp": t["stopp"],
            "pivot": t.get("pivot")}


def setzen(ticker, **werte):
    """Position anlegen oder ändern (nur übergebene Felder); eine neue Position merkt sich den Pivot ihres Setups."""
    d = laden()
    p = next((p for p in d["positionen"] if p["ticker"] == ticker.upper()), None)
    if p is None:
        su = aus_setup(ticker)
        p = {"ticker": ticker.upper(), "seite": "long", "stueck": 0, "einstieg": None, "stopp": None,
             "datum": time.strftime("%Y-%m-%d"), "ko": None, "notiz": "",
             "pivot": su.get("pivot") if su.get("seite") == werte.get("seite", "long") else None}
        d["positionen"].append(p)
    p.update({k: v for k, v in werte.items() if v is not None})
    speichern(d)


def schliessen(ticker, ausstieg=None):
    """Position schließen; mit Ausstiegskurs wird der Trade in der Bilanz verbucht."""
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
        if tk in alt:
            p = dict(alt[tk])
        else:                                      # neu: Stopp und Pivot aus dem Setup, wenn die Seite passt
            su = aus_setup(tk)
            passt = su.get("seite") == (x.get("seite") or "long")
            p = {"ticker": tk, "seite": "long", "stopp": su.get("stopp") if passt else None,
                 "pivot": su.get("pivot") if passt else None, "datum": time.strftime("%Y-%m-%d"), "ko": None, "notiz": ""}
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
    """Führung nach dem Kauf als Liste (Ampel, Text) – nur noch Zirkel und nachgezogener Stopp (Micky 23.11.2026;
    vorher die Regeln der Meister: Teilgewinn Tag 3–5, 8-%-Grenze, Einstand ab 2R, Squat, Tennisball, Reset, Führer).
    Long beschrieben, short spiegelbildlich:
      Stopp     beim Kauf der Stopp des Setups; ab Tag 3 am 10er bzw. 20er (reiten.nachgezogen), Schluss jenseits = raus.
      Reibung   Mauer, Kraft ohne Weg und Klimax ziehen ihn unter das Tagestief jenes Tages.
      Zirkel    🟢 Phase 2 (bzw. Wechsel 1 → 2) ohne 🍂: die Stärke trägt – laufen lassen (Trägheit).
                🟡 🍂 gemessen in Phase 2: die Stärke schwindet – Stopp eng unter das Tagestief.
                🔴 Wechsel 2 → 3 läuft oder Phase 3/4: die Stärke ist gebrochen – raus.
      Pivot     🔴 Schluss zurück unter dem Pivot des Setups: der Widerstand ist nicht überwunden – raus."""
    import reiten
    import zeichen
    import zirkel
    aus = []
    if df is None or not p.get("einstieg"):
        return aus
    lang = p.get("seite", "long") == "long"
    wo = "unter" if lang else "über"
    e, s = float(p["einstieg"]), p.get("stopp")
    k = float(df["Close"].iloc[-1])
    if not s:
        aus.append(("rot", "kein Stopp gesetzt – jede Position braucht einen Stopp vor dem Kauf: den Stopp des Setups"))
    else:
        ende = reiten.ende_zeichen(df, p.get("seite", "long"))
        nz = reiten.nachgezogen(df, p.get("datum"), e, float(s), p.get("seite", "long"), ende)
        if nz:
            if nz["raus"]:
                aus.append(("rot", f"Schluss {wo} dem nachgezogenen Stopp {nz['stopp']:.2f} ({nz['regel']}) – raus"))
            else:
                aus.append(("grün" if nz["linie"] else "grau",
                            f"Stopp jetzt {nz['stopp']:.2f}: {nz['regel']}, Tag {nz['tag_nr']} nach dem Kauf"))
            if nz["enger"]:
                en = nz["enger"]
                getroffen = (k < en["stopp"]) if lang else (k > en["stopp"])
                aus.append(("rot" if getroffen else "gelb",
                            f"Reibung – {en['art']} am {en['tag']:%d.%m.}: Stopp eng {wo} das {'Tief' if lang else 'Hoch'} "
                            f"jenes Tages {en['stopp']:.2f} (Stopp im Markt)" + (" – erreicht" if getroffen else "")))
    zk = zeichen.zirkel(zeichen.von(p.get("ticker", "")))
    ph = (zk or {}).get("phase") or 0
    keim, ziel = bool((zk or {}).get("keim")), (zk or {}).get("ziel")
    keim_text = "; ".join((zk or {}).get("keim") or [])
    traeg, gegen = (zirkel.P_AUF, zirkel.P_VERTEILUNG) if lang else (zirkel.P_AB, zirkel.P_BASIS)
    vor = zirkel.P_BASIS if lang else zirkel.P_VERTEILUNG          # die Phase vor dem Trend (Wechsel 1 → 2 bzw. 3 → 4)
    tag_eng = float(df["Low"].iloc[-1] if lang else df["High"].iloc[-1])
    if not zk or not ph:
        aus.append(("grau", "noch kein Zirkel (unter einem Jahr Kurse oder nicht im letzten Zirkel-Lauf) – der Stopp führt"))
    elif ph == traeg and ziel == gegen:
        aus.append(("rot", f"Wechsel {traeg} → {gegen} läuft: die {'Stärke' if lang else 'Schwäche'} ist gebrochen – raus"
                           + (f" ({keim_text})" if keim_text else "")))
    elif ph == traeg and keim:
        aus.append(("gelb", f"{'🍂 Keim der Schwäche' if lang else '🌱 Keim der Stärke'} in Phase {ph}: die "
                            f"{'Stärke' if lang else 'Schwäche'} schwindet – Stopp eng {wo} das "
                            f"{'Tagestief' if lang else 'Tageshoch'} {tag_eng:.2f} ({keim_text})"))
    elif ph == vor and ziel == (zirkel.P_AB if lang else zirkel.P_AUF):
        aus.append(("rot", f"Phase {zk['wort']} ({zk['name']}): die {'Basis bricht' if lang else 'Verteilung dreht nach oben'}"
                           f" – raus" + (f" ({'; '.join(zk.get('traegt') or [])})" if zk.get("traegt") else "")))
    elif ph == traeg or (ph == vor and (keim or ziel == traeg)):
        aus.append(("grün", f"Phase {zk['wort']} ({zk['name']}): die {'Stärke' if lang else 'Schwäche'} trägt – "
                            "laufen lassen, der Stopp zieht nach"))
    elif ph == vor:
        aus.append(("gelb", f"Phase {zk['wort']} ({zk['name']}): der {'Aufbruch' if lang else 'Abbruch'} ist nicht "
                            f"bestätigt – {'🌱' if lang else '🍂'} nicht gemessen, kein Wechsel; der Stopp führt"))
    else:
        aus.append(("rot", f"Phase {zk['wort']} ({zk['name']}): der Zirkel steht gegen die Position – raus"))
    piv = p.get("pivot")
    if piv and ((k < piv) if lang else (k > piv)):
        aus.append(("rot", f"Schluss {'zurück unter dem Pivot' if lang else 'zurück über der Unterkante'} {piv:.2f}: "
                           f"der {'Widerstand' if lang else 'Boden'} ist nicht {'überwunden' if lang else 'gebrochen'} – raus"))
    return aus
