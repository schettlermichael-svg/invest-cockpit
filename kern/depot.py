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
import math
import os
import time
from dateien import json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "einstellungen", "depot.json")
LEER = {"konto": None, "risiko_pct": 1.0, "hitze_max_pct": 6.0, "quelle": "Hand", "stand": None, "positionen": []}
WAEHRUNG = {".DE": "EUR", ".F": "EUR", ".MI": "EUR", ".PA": "EUR", ".AS": "EUR", ".BR": "EUR", ".MC": "EUR",
            ".HE": "EUR", ".L": "GBp", ".SW": "CHF", ".ST": "SEK", ".CO": "DKK", ".OL": "NOK"}
VERLUSTGRENZE = 0.08
KLUMPEN = 25.0               # Positionswert über 25 % des Kontos: Klumpen (Minervini: höchstens 20–25 % je Titel)


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


def stueckzahl(ticker, einstieg, stopp, bezug=None, d=None):
    """Stückzahl (Aktie oder Knock-out mit Bezugsverhältnis) für das Risiko je Trade. dict oder None."""
    d = d or laden()
    r = risiko_euro(d)
    k = fx(waehrung(ticker))
    if not r or not k or not einstieg or not stopp or einstieg == stopp:
        return None
    je = abs(einstieg - stopp) * (bezug or 1)                 # Verlust je Stück in Titelwährung
    n = math.floor(r * k / je)
    wert = n * einstieg / k if not bezug else None
    return {"stueck": n, "risiko": n * je / k, "wert": wert,
            "anteil": (wert / d["konto"] * 100) if wert and d.get("konto") else None, "fx": k}


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


ATR_STOPP = 1.5                                  # ein Stopp für alle Systeme: 1,5 ATR vom Einstieg (Micky, 09.11.2026)


def einstieg_setup(su, m, k, zr=None, kurs=None):
    """Einstieg des EINEN Setups eines Titels (12.11.2026 – vorher nahm der Chart immer die alte Kette Sprung →
    Base-Ausbruch → Momentum-Ausbruch: HWM stand in Zahlen-Reaktion long bei 224 $, der Chart zeichnete den Pivot
    einer alten Base und den Stopp 247,93 $ über dem Kurs). → (Seite, Einstieg, Quelle) oder (None, None, "").
      Sprung (EP)          Hoch des Sprungtags (Pivot des EP)
      Zahlen-Reaktion      AVWAP ab dem Reaktionstag, Seite der Reaktion
      Ermüdung, Bärenflagge, Bruch der Spanne  Unterkante (short)
      Base-Ausbruch        Pivot der Base (sonst Pivot des letzten Ausbruchs)
      Momentum-Ausbruch    Pivot der Konsolidierung
      Flagge, nur Muster   Pivot des Scanners (aus dem Abstand des Kartentischs)"""
    su, m, k, zr = su or {}, m or {}, k or {}, zr or {}
    r = su.get("reihe")
    if r == "k_ep" and (k.get("ep") or {}).get("pivot"):
        return "long", float(k["ep"]["pivot"]), "Sprung (EP)"
    if r == "zahlen" and zr.get("avwap"):
        return zr.get("seite", "long"), float(zr["avwap"]), "AVWAP ab dem Reaktionstag"
    if r in ("k_ermuedung", "k_baerenflagge", "k_bruch"):
        import system_kullamaegi
        em = system_kullamaegi.short_von(k, r) or {}
        if em.get("unten"):
            return "short", float(em["unten"]), "Unterkante"
    if r in ("m_spitze", "m_weitere"):
        e = m.get("pivot") or (m.get("ausbruch") or {}).get("pivot")
        return ("long", float(e), "Pivot der Base") if e else (None, None, "")
    if r == "k_breakout" and (k.get("breakout") or {}).get("pivot"):
        return "long", float(k["breakout"]["pivot"]), "Pivot der Konsolidierung"
    if r in ("flagge", "vcp") and su.get("pivot_scanner"):
        return "long", float(su["pivot_scanner"]), "Pivot des Scanners"
    if r in ("flagge", "vcp") and su.get("abstand_vz") is not None and kurs:   # Tische vor dem 13.11.2026
        return "long", float(kurs) / (1 + float(su["abstand_vz"]) / 100), "Pivot des Scanners"
    return None, None, ""


def plan(erk):
    """Einstieg und Stopp DES Setups wie im Chart: (Seite, Einstieg, Stopp, Stopp-Regel) oder None. Einstieg aus
    einstieg_setup (das eine Setup, kartentisch.setup_feststellen), Stopp 1,5 ATR vom Einstieg (long darunter, short
    darüber). Ohne Setup oder ATR kein Plan. (Bis 12.11.2026 eine eigene Kette Sprung → Ermüdung → Base → Momentum;
    der Prüf-Agent fand sie als zweite Quelle neben dem Setup.)"""
    sy = erk.get("systeme") or {}
    m, k = sy.get("m") or {}, sy.get("k") or {}
    a = erk.get("atr")
    seite, e, _ = einstieg_setup(erk.get("setup_info"), m, k, erk.get("zahlen_reaktion"), erk.get("kurs"))
    if not e or not a:
        return None
    return seite, e, (e + ATR_STOPP * a if seite == "short" else e - ATR_STOPP * a), f"{zahl_kurz(ATR_STOPP)} ATR wie im Chart"


def zahl_kurz(x):
    return f"{x:g}".replace(".", ",")


def nach_dem_kauf(p, df, erk=None):
    return [(a, _deutsch(t)) for a, t in _nach_dem_kauf(p, df, erk)]


def _nach_dem_kauf(p, df, erk=None):
    """Zeichen nach dem Kauf als Liste (Ampel, Text) – je nach System der Position (05.11.2026):
    Minervini (M, Vorgabe): Stopp vor dem Kauf, Verlustgrenze, Stopp auf Einstand ab 2R, Squat, Tennisball, Reset.
    Kullamägi (K): Teilgewinn in den ersten 3–5 Tagen und Stopp auf Einstand, dann Schluss unter dem 10er (schnelle
    Titel) bzw. 20er als Ausstieg für den Rest. Kein festes Gewinnziel (Gewinne laufen lassen, Stopp nachziehen)."""
    import pandas as pd
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
        aus.append(("rot", "kein Stopp gesetzt – jede Position braucht einen Stopp vor dem Kauf (Minervini)"))
    if p.get("system") == "K":
        tage = len(seit) - 1
        g10, g20 = float(c[-10:].mean()), float(c[-20:].mean())
        if 3 <= tage <= 5 and g > 0 and s and ((s < e) if lang else (s > e)):
            aus.append(("gelb", f"Tag {tage} nach dem Kauf, {g:+.1f} %: Teilgewinn nehmen und den Stopp für den Rest auf "
                                f"Einstand {e:.2f} ziehen (Kullamägi)"))
        if tage >= 1 and lang:
            if k < g20:
                aus.append(("rot", f"Schluss unter dem 20-Tage-Durchschnitt ({g20:.2f}) – Rest verkaufen (Kullamägi)"))
            elif k < g10:
                aus.append(("gelb", f"Schluss unter dem 10-Tage-Durchschnitt ({g10:.2f}) – Ausstieg für weit gelaufene "
                                    f"Titel; sonst gilt der 20er ({g20:.2f}) (Kullamägi)"))
            else:
                aus.append(("grün", f"über 10er ({g10:.2f}) und 20er ({g20:.2f}) – laufen lassen (Kullamägi)"))
        if not s:
            aus.append(("rot", "kein Stopp – Kullamägi: Stopp am Tagestief des Einstiegstags"))
        return aus
    if g <= -VERLUSTGRENZE * 100:
        aus.append(("rot", f"Verlustgrenze: {g:.1f} % – höchstens 8 % Verlust, ohne Ausnahme (Minervini, O'Neil)"))
    if s and r_mult is not None and r_mult >= 2 and ((s < e) if lang else (s > e)):
        aus.append(("gelb", f"Stopp nachziehen: {r_mult:.1f}R Gewinn – Stopp mindestens auf Einstand {e:.2f} (Minervini)"))
    w = (erk or {}).get("werte") or {}
    if erk and erk.get("mp") and "start_index" in w and s:
        z_beginn = df.index[w["start_index"]]
        neue_kante = w.get("val") if lang else w.get("vah")
        if z_beginn > pd.Timestamp(p.get("datum") or df.index[0]) and neue_kante and \
                ((neue_kante > s) if lang else (neue_kante < s)):
            aus.append(("gelb", f"Zeichen Auktion: neue Wertzone seit {z_beginn:%d.%m.} – Schluss {'unter VAL' if lang else 'über VAH'} "
                                f"{neue_kante:.2f} wäre ein enger Nachzieh-Stopp (Market Profile)"))
    if len(seit) >= 1 and len(seit) <= 4 and lang:
        t = seit.iloc[0]
        spanne = float(t["High"] - t["Low"]) or 1
        if (float(t["Close"]) - float(t["Low"])) / spanne < 0.33:
            aus.append(("gelb", "Squat am Kauftag (Schluss im unteren Drittel) – O'Neil: oft Erholung in 1–3 Tagen; "
                                "der Stopp gilt"))
    if len(seit) >= 3 and lang:
        lo = seit["Low"].to_numpy(float)
        hi = seit["High"].to_numpy(float)
        i = int(lo.argmin())
        if i < len(lo) - 1 and lo[i] < e * 0.97 and k > hi[:i + 1].max() and len(lo) - 1 - i <= 5:
            aus.append(("grün", "Tennisball: nach dem Rücksetzer schnell auf neues Hoch – Zeichen von Stärke (Minervini)"))
    pl_ = plan(erk) if erk else None                 # Einstieg des Setups (Prüf-Agent 12.11.2026)
    piv = pl_[1] if pl_ and pl_[0] == "long" else None
    if lang and piv and e >= piv * 0.98 and k < piv and (not s or k > s):
        aus.append(("gelb", f"Reset beobachten: Kurs zurück unter dem Pivot {piv:.2f} – hält der Stopp, kann sich eine "
                            "neue Base bilden (Minervini)"))
    if g >= 20 and len(seit) <= 15:
        aus.append(("grün", f"+{g:.0f} % in höchstens 3 Wochen – Zeichen eines Führers; laufen lassen, Stopp nachziehen"))
    if not aus:
        aus.append(("grün", f"läuft nach Plan: {g:+.1f} %" + (f", {r_mult:.1f}R" if r_mult is not None else "")))
    return aus
