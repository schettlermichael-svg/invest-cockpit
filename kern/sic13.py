"""SIC-13 · Sovereign Investment Compass (Mickys eigenes Raster, Durant-Investment-Protocol):
„Strukturelle Überlegenheit vor der technischen Analyse“.

Für JEDEN Titel dieselben elf Kriterien in fünf Ebenen – nichts wird weggelassen. Zusammengelegt (03.11.2026):
IV + XIII (Innovation und Technologievorsprung) und X + XI (Politischer Rückenwind und Krisen-Gewinner, dazu die
Lage aus Quad und Rotation). Gemessen aus Zahlen: III, I, V, VI, VIII und die Zahlenprobe zu VII und XII.
Eingeschätzt (Text mit Ampel, daten/sic13/einschaetzung.json): II, IV, VII, IX, X, XII – klar als Einschätzung
gekennzeichnet. Ebene 0 ist der Torwächter: nicht erfüllt = K.O. nach SIC-13, aber alle Angaben bleiben sichtbar.
Ampeln, keine Punkte; Schwellen sind begründete Voreinstellungen (im Hinweis jedes Kriteriums genannt).
"""
import json
import os

import numpy as np
import pandas as pd

import fussabdruck
import rs_rang
import rudel
import sektoren

HIER = os.path.dirname(os.path.abspath(__file__))
DATEN = os.path.join(HIER, "..", "daten")
EINSCHAETZUNG = os.path.join(DATEN, "sic13", "einschaetzung.json")
TV = os.path.join(DATEN, "tv", "revier.csv")

EBENEN = [("Ebene 0 · Torwächter", ["III"]),
          ("Ebene 1 · Fundament der Stärke", ["I", "II", "IV"]),
          ("Ebene 2 · Psychologie und Überzeugung", ["V", "VI", "VII"]),
          ("Ebene 3 · Systemmacht", ["VIII", "IX", "X"]),
          ("Ebene 4 · Zukunftspotenzial", ["XII"])]
NAMEN = {"III": "Sektor-Alpha und Relative Stärke", "I": "Risiko-History", "II": "Ressourcen-Macht",
         "IV": "Innovation und Technologievorsprung", "V": "Institutionelles Sentiment", "VI": "Krisen-Resistenz",
         "VII": "Burggraben und Relevanz", "VIII": "Pricing Power", "IX": "Regulierungsrisiko",
         "X": "Politischer Rückenwind und Krisen-Gewinner", "XII": "Skalierungs-Potenzial"}
FRAGE = {
    "III": "Torwächter: RS-Rating über 80 und RS-Ratio über 1,0 oder steigend. RS-Rating = RS-Rang 1–99 der App "
           "(12 Monate, jüngstes Quartal doppelt). RS-Ratio = Titel ÷ S&P 500 gegen ihr 52-Wochen-Mittel (Mansfield).",
    "I": "Hat die Aktie eine Historie massiver Rücksetzer oder unberechenbarer Kursverläufe? Gemessen: größter Rücksetzer "
         "der letzten 10 Jahre und Kurslücken über 10 % in 5 Jahren. Grün bis 45 % Rücksetzer und höchstens 2 Lücken, "
         "rot ab 65 % oder ab 6 Lücken.",
    "II": "Kontrolliert das Unternehmen physische Güter, kritische Infrastruktur, Energie oder seltene Erden? "
          "Unternehmen mit Ressourcenkontrolle sind strukturell schwerer zu verdrängen.",
    "IV": "Ist das Management agil oder bürokratisch, entscheidet es schnell? Nutzt es KI und Automatisierung für einen "
          "uneinholbaren Effizienz- oder Technikvorsprung? (SIC IV und XIII zusammen)",
    "V": "Akkumulieren Fonds und ETFs? Gemessen: Tage mit hohem Volumen nach oben gegen nach unten in den letzten "
         "13 Wochen (der Fußabdruck großer Käufer, O'Neil). Die Meldungen der Fonds (13F) kommen mit der I-Ampel dazu.",
    "VI": "Ist das Geschäftsmodell antifragil, überlebt es Krisen? Gemessen: Kurseinbruch 2020 und 2022 gegen den "
          "S&P 500, Umsatzeinbruch 2020, Verschuldung (Nettoschulden zu EBITDA). Grün ohne Schwachstelle, gelb mit "
          "einer, rot ab zwei. Schwachstelle: Einbruch mehr als 1,5-fach des Markts, Umsatz 2020 mehr als 15 % unter "
          "Vorjahr, Nettoschulden über dem 3-Fachen des EBITDA.",
    "VII": "Hat das Produkt unverzichtbare Relevanz oder Kult-Status? Würden Kunden ohne das Produkt ihren Alltag "
           "einschränken? Dazu die Zahlenprobe (Buffett): Ein echter Burggraben zeigt sich in dauerhaft hoher "
           "Marge – grün ab 15 % operativer Marge und keiner Jahres-Nettomarge unter 8 % in 5 Jahren, rot unter 5 % operativer Marge oder bei einem Verlustjahr. (Die Kapitalrendite liefert TradingView nicht.)",
    "VIII": "Kann das Unternehmen Preise erhöhen, ohne Kunden zu verlieren (Mautstation)? Gemessen: Nettomarge in den "
            "Inflationsjahren 2021–2023 gegen 2018–2019 (SEC). Grün: gehalten oder gestiegen, gelb: bis 4 Punkte "
            "darunter, rot: mehr.",
    "IX": "Wie hoch ist das Risiko von Staatszugriff, Preisregulierung, Kartellverfahren oder Sondersteuern? "
          "Grün = geringes Risiko.",
    "X": "Passt die Aktie zum politischen Pendel, profitiert sie von globaler Instabilität? (SIC X und XI zusammen) "
         "Dazu die Lage: Gehört der Sektor zu den typischen Führern des aktuellen Quads, und in welchem Feld steht er? "
         "Widerspricht die Lage, sinkt die Ampel um eine Stufe.",
    "XII": "Frühe exponentielle Kurve oder gesättigter Markt (TAM mehr als 80 % offen?) – eingeschätzt. Dazu gemessen: "
           "Umsatzwachstum der letzten Quartale. Die Ampel ist die schwächere der beiden.",
}
STUFE = {"grün": 2, "gelb": 1, "rot": 0}
AUS_STUFE = {2: "grün", 1: "gelb", 0: "rot"}
WORT = {"grün": "✅", "gelb": "⚠️", "rot": "❌", "grau": "–"}

_cache = {}


def _neu(pfad, schluessel):
    """True, wenn die Datei seit dem letzten Lesen geändert wurde (dann neu lesen)."""
    m = os.path.getmtime(pfad) if os.path.exists(pfad) else 0
    if _cache.get(schluessel + "_m") != m:
        _cache[schluessel + "_m"] = m
        return True
    return False


def _einschaetzung():
    if _neu(EINSCHAETZUNG, "e") or "e" not in _cache:
        try:
            _cache["e"] = json.load(open(EINSCHAETZUNG, encoding="utf-8"))
        except Exception:
            _cache["e"] = {}
    return _cache["e"]


def _tv(tk):
    if _neu(TV, "tv") or "tv" not in _cache:
        try:
            _cache["tv"] = pd.read_csv(TV, keep_default_na=True).set_index("ticker")
        except Exception:
            _cache["tv"] = pd.DataFrame()
    t = _cache["tv"]
    return t.loc[tk] if tk in t.index else None


def _lang(name):
    p = os.path.join(DATEN, "lang", f"{name}.csv")
    return pd.read_csv(p, index_col=0, parse_dates=True) if os.path.exists(p) else None


def _schlechter(*ampeln):
    a = [x for x in ampeln if x in STUFE]
    return AUS_STUFE[min(STUFE[x] for x in a)] if a else "grau"


def _zahl(x, st=0):
    return f"{x:,.{st}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _wert(tv, spalte):
    if tv is None or spalte not in tv.index:
        return None
    v = tv[spalte]
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(v) else v


def k_III(tk, df, spy):
    rang = rs_rang.rang(tk)[0]
    m = rudel.mansfield(df["Close"], spy) if spy is not None else None
    if rang is None and not m:
        return "grau", "keine Daten", "RS-Rang und RS-Ratio nicht verfügbar"
    ok_rang = rang is not None and rang > 80
    ratio = 1 + m["wert"] / 100 if m else None
    ok_ratio = bool(m and (m["wert"] > 0 or m["richtung"] > 0))
    ampel = "grün" if ok_rang and ok_ratio else "gelb" if ok_rang or ok_ratio else "rot"
    zeile = (f"RS-Rang {rang if rang is not None else '–'} ({'über' if ok_rang else 'nicht über'} 80) · RS-Ratio "
             + (f"{_zahl(1 + (m['wert'] - m['richtung']) / 100, 2)} → {_zahl(ratio, 2)} in 4 Wochen" if m else "–"))
    return ampel, {"grün": "bestanden", "gelb": "halb", "rot": "K.O."}[ampel], zeile


def k_I(tk, df):
    lang = _lang(tk)
    c = pd.concat([lang["Close"], df["Close"]]) if lang is not None else df["Close"]
    c = c[~c.index.duplicated(keep="last")].sort_index()
    o = pd.concat([lang["Open"], df["Open"]]) if lang is not None else df["Open"]
    o = o[~o.index.duplicated(keep="last")].sort_index()
    c10 = c[c.index >= c.index[-1] - pd.Timedelta(days=3653)]
    dd = (c10 / c10.cummax() - 1)
    tief = dd.idxmin()
    max_dd = -float(dd.min()) * 100
    c5 = c[c.index >= c.index[-1] - pd.Timedelta(days=1826)]
    o5 = o.reindex(c5.index)
    luecken = int(((o5 / c5.shift(1) - 1).abs() > 0.10).sum())
    jahre = (c10.index[-1] - c10.index[0]).days / 365.25
    ampel = "grün" if max_dd <= 45 and luecken <= 2 else "rot" if max_dd > 65 or luecken >= 6 else "gelb"
    wort = {"grün": "berechenbar", "gelb": "volatil", "rot": "unberechenbar"}[ampel]
    zeile = (f"größter Rücksetzer {_zahl(max_dd)} % ({tief:%Y}) in {_zahl(jahre)} Jahren · "
             f"{luecken} Kurslücke{'n' if luecken != 1 else ''} über 10 % in 5 Jahren")
    return ampel, wort, zeile


def k_V(df):
    if len(df) < 120:
        return "grau", "–", "zu kurze Historie"
    f = fussabdruck.fussabdruck(df, len(df) - 65)
    if not f:
        return "grau", "–", "nicht berechenbar"
    ampel = f["ampel"]
    wort = {"grün": "Akkumulation", "gelb": "ausgeglichen", "rot": "Distribution"}.get(ampel, "–")
    return ampel, wort, (f"13 Wochen: {f['akk']} Kauf- gegen {f['dist']} Verkaufstage mit hohem Volumen "
                         f"(Fonds-Fußabdruck); 13F-Meldungen folgen mit der I-Ampel")


def _einbruch(c, von, bis):
    s = c[(c.index >= von) & (c.index <= bis)]
    if len(s) < 20:
        return None
    return -float((s / s.cummax() - 1).min()) * 100


def _sec(tk):
    p = os.path.join(DATEN, "sec_lang", f"{tk}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["ende"]).dropna(subset=["ende"]).set_index("ende").sort_index()
    return d[~d.index.duplicated(keep="last")]


def k_VI(tk, df, sektor):
    lang, spx = _lang(tk), _lang("_GSPC")
    c = lang["Close"] if lang is not None else df["Close"]
    teile, schwach = [], 0
    for jahr, von, bis in (("2020", "2020-02-01", "2020-06-30"), ("2022", "2022-01-01", "2022-12-31")):
        t = _einbruch(c, von, bis)
        m = _einbruch(spx["Close"], von, bis) if spx is not None else None
        if t is None:
            teile.append(f"{jahr}: noch nicht börsennotiert")
            continue
        faktor = t / m if m else None
        if faktor and faktor > 1.5:
            schwach += 1
        teile.append(f"{jahr} −{_zahl(t)} % (Markt −{_zahl(m)} %)" if m else f"{jahr} −{_zahl(t)} %")
    sec = _sec(tk)
    if sec is not None and sec["umsatz"].notna().sum() >= 8:
        u = sec["umsatz"].dropna()
        vj = u / u.shift(4) - 1
        q20 = vj[(vj.index >= "2020-03-01") & (vj.index <= "2021-03-31")]
        if len(q20):
            tief = float(q20.min()) * 100
            if tief < -15:
                schwach += 1
            teile.append(f"Umsatz 2020 im schwächsten Quartal {'+' if tief >= 0 else '−'}{_zahl(abs(tief))} % zum Vorjahr")
    tv = _tv(tk)
    nd, eb = _wert(tv, "net_debt_fq"), _wert(tv, "ebitda_ttm")
    if sektor in ("Financial Services", "Real Estate"):
        teile.append("Verschuldung bei Banken, Versicherern und REITs nicht vergleichbar")
    elif nd is not None and eb:
        x = nd / eb
        if x > 3:
            schwach += 1
        teile.append("netto schuldenfrei" if nd <= 0 else f"Nettoschulden {_zahl(x, 1)}-faches EBITDA")
    else:
        teile.append("Verschuldung: TradingView-Daten fehlen")
    ampel = "grün" if schwach == 0 else "gelb" if schwach == 1 else "rot"
    wort = {"grün": "krisenfest", "gelb": "eine Schwachstelle", "rot": "anfällig"}[ampel]
    return ampel, wort, " · ".join(teile)


def k_VIII(tk):
    sec = _sec(tk)
    tv = _tv(tk)
    bm = _wert(tv, "gross_margin_ttm")
    zusatz = f" · Bruttomarge heute {_zahl(bm)} %" if bm is not None else ""
    if sec is not None:
        d = sec.dropna(subset=["umsatz", "nettogewinn"])
        d = d[d["umsatz"] > 0]

        def marge(a, b):
            x = d[(d.index >= a) & (d.index <= b)]
            return float(x["nettogewinn"].sum() / x["umsatz"].sum() * 100) if len(x) >= 3 else None
        vor, inf = marge("2018-01-01", "2019-12-31"), marge("2021-01-01", "2023-12-31")
        if vor is not None and inf is not None:
            delta = inf - vor
            ampel = "grün" if delta >= -1 else "gelb" if delta >= -4 else "rot"
            wort = {"grün": "Mautstation", "gelb": "unter Druck", "rot": "keine Preismacht"}[ampel]
            return ampel, wort, (f"Nettomarge 2021–23 {_zahl(inf, 1)} % gegen {_zahl(vor, 1)} % in 2018–19 "
                                 f"({'+' if delta >= 0 else '−'}{_zahl(abs(delta), 1)} Punkte){zusatz}")
    if bm is not None:
        ampel = "grün" if bm >= 50 else "gelb" if bm >= 25 else "rot"
        return ampel, {"grün": "hohe Marge", "gelb": "mittlere Marge", "rot": "dünne Marge"}[ampel], \
            f"keine Zahlen für die Inflationsjahre (SEC) · Bruttomarge heute {_zahl(bm)} % als Ersatz"
    return "grau", "–", "keine Margendaten (SEC und TradingView)"


def _probe_VII(tk):
    """Zahlenprobe zum Burggraben (Buffett): dauerhaft hohe Marge. Operative Marge heute (TradingView) und die
    schwächste Jahres-Nettomarge der letzten 5 Jahre (SEC, je vier Quartale)."""
    om = _wert(_tv(tk), "operating_margin_ttm")
    sec = _sec(tk)
    tiefst = None
    if sec is not None:
        d = sec.dropna(subset=["umsatz", "nettogewinn"])
        d = d[(d["umsatz"] > 0) & (d.index >= d.index.max() - pd.Timedelta(days=5 * 366))]
        if len(d) >= 12:
            j = d.groupby(d.index.year).filter(lambda x: len(x) == 4).groupby(lambda i: i.year).sum()
            if len(j) >= 3:
                tiefst = float((j["nettogewinn"] / j["umsatz"]).min() * 100)
    if om is None and tiefst is None:
        return None, "Zahlenprobe: keine Margendaten"
    teile = []
    if om is not None:
        teile.append(f"operative Marge {_zahl(om)} %")
    if tiefst is not None:
        teile.append(f"schwächste Nettomarge der letzten Jahre {_zahl(tiefst, 1)} %")
    gut = (om is None or om >= 15) and (tiefst is None or tiefst >= 8)
    schlecht = (om is not None and om < 5) or (tiefst is not None and tiefst < 0)
    return ("grün" if gut else "rot" if schlecht else "gelb"), "Zahlenprobe: " + ", ".join(teile)


def _lage_X(etf, quad, rot):
    if not etf or not quad:
        return None, ""
    typisch = etf in sektoren.QUAD_ETFS.get(quad["quad"], [])
    feld = (rot or {}).get(etf, {}).get("feld")
    vorne = feld in ("Führend", "Erstarkend")
    widerspruch = not typisch and not vorne
    return widerspruch, (f"Lage: Sektor {'typisch' if typisch else 'nicht typisch'} für Quad {quad['quad']}"
                         + (f", Feld {feld}" if feld else ""))


def _umsatz_XII(fund):
    p = (fund or {}).get("punkte", {}).get("Umsatz")
    return (p[0], f"Umsatz {p[1]}") if p else (None, "Umsatzwachstum nicht verfügbar")


def kompass(tk, df, spy, sektor, etf, fund, quad=None, rot=None):
    """Alle elf Kriterien: {Nummer: {ampel, wort, zeile, art}} und das Urteil des Torwächters."""
    e = _einschaetzung().get(tk.upper(), {})

    def ein(k):
        a, txt = (e.get(k) or ["grau", "Einschätzung folgt"])[:2]
        return (a if a in STUFE else "grau"), txt
    erg = {}
    for k, f, art in (("III", lambda: k_III(tk, df, spy), "gemessen"), ("I", lambda: k_I(tk, df), "gemessen"),
                      ("V", lambda: k_V(df), "gemessen"), ("VI", lambda: k_VI(tk, df, sektor), "gemessen"),
                      ("VIII", lambda: k_VIII(tk), "gemessen")):
        try:
            a, w, z = f()
        except Exception as ex:  # noqa: BLE001 – ein fehlender Baustein darf die Seite nicht kippen
            a, w, z = "grau", "–", f"nicht berechenbar ({type(ex).__name__})"
        erg[k] = {"ampel": a, "wort": w, "zeile": z, "art": art}
    for k in ("II", "IV", "IX"):
        a, txt = ein(k)
        erg[k] = {"ampel": a, "wort": WORT[a], "zeile": txt, "art": "Einschätzung"}
    a, txt = ein("VII")
    pa, ptxt = _probe_VII(tk)
    erg["VII"] = {"ampel": _schlechter(a, pa) if a != "grau" else (pa or "grau"), "wort": "",
                  "zeile": f"{txt} · {ptxt}", "art": "Einschätzung + Zahlen"}
    a, txt = ein("X")
    wid, lage_txt = _lage_X(etf, quad, rot)
    if wid and a in STUFE:
        a = AUS_STUFE[max(0, STUFE[a] - 1)]
    erg["X"] = {"ampel": a, "wort": "", "zeile": txt + (f" · {lage_txt}" if lage_txt else ""),
                "art": "Einschätzung + Lage"}
    a, txt = ein("XII")
    ua, utxt = _umsatz_XII(fund)
    erg["XII"] = {"ampel": _schlechter(a, ua) if a != "grau" else (ua or "grau"), "wort": "",
                  "zeile": f"{txt} · {utxt}", "art": "Einschätzung + Zahlen"}
    for k, v in erg.items():
        if not v["wort"]:
            v["wort"] = WORT[v["ampel"]]
    return {"kriterien": erg, "torwaechter": erg["III"]["ampel"]}
