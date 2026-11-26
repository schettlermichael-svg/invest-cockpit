"""Rückenwind (Konzept: KONZEPT_RUECKENWIND.md, 09.11.2026) – eigene Seite, getrennt von den Setups.

Je Titel des Reviers drei Rückenwinde als Ampeln, dazu Earnings:
  Kurs   RS-Dynamik: Stärke (RS-Rang 1–99 wie IBD, der IBD-Formel), Tempo (Veränderung des Rangs in 4 Wochen),
         Beschleunigung (Tempo gegen das Tempo der 4 Wochen davor); Zeichen: RS-Linie am 52-Wochen-Hoch, der Kurs noch
         nicht (O'Neil/Minervini).
  Zeichen dazu: Steigung der RS-Linie in 4 Wochen (und davor), Volumen-Zufluss des Titels selbst (Volumen an
         steigenden ÷ fallenden Tagen, 50 Tage: ab 1,1 Zufluss, unter 0,9 Abfluss).
  Geld   Sektor, Branche und Thema der Gruppe (drei Stimmen: grün = zwei vorne, keine im Abfluss); „stabil“ = führt
         seit mindestens 8 Wochen und größter Rückschlag des Gruppenindex in 8 Wochen höchstens 8 %: Feld (Stärke × Tempo gegen den S&P 500 wie sektoren.reihen, gleich-
         gewichtete Indizes der Revier-Titel), Weg der letzten 4 Wochen, Volumen-Zufluss (Volumen an steigenden gegen
         fallende Tage, 50 Tage).
  Zahlen Fundament-Ampeln (fundament.ampeln, Minervini/O'Neil) aus dem Zwischenspeicher; Termin der nächsten Zahlen,
         Reaktion auf die letzten.
Schlachtordnung statt Stufen (Micky 21./22.11.2026): Klasse 1–5 aus Front (RS-Linie) und Truppen (Volumen-Zufluss,
austrocknendes Volumen), in der Klasse RS-Hoch vor Kurs, Geld der Branche, Zahlen, Rang als Kraft; dazu Abstand zum 52-Wochen-Hoch (nah · mittel · fern) und das Zeichen Einzelkämpfer (stark, Branche hinten).
Alles aus den Massive-Tagesdateien des Nachtlaufs, gespeichert in daten/rueckenwind/.
"""
import json
import os

import numpy as np
import pandas as pd

import livermore
import massive
import sektoren
from dateien import json_lesen, json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "rueckenwind")
MARKT = "SPY"
TAGE = 320                     # 12 Monate RS-Rang + 8 Wochen zurück
WOCHEN4 = 20                   # Handelstage in 4 Wochen
STARK = 85                     # Anführer einer Gruppe: Rang ab 85 (IBD: Ø 87 vor den großen Läufen)
VORNE = ("Führend", "Erstarkend")
STABIL_WOCHEN, STABIL_RUECKSCHLAG = 8, 8.0   # stabil: führt seit 8 Wochen und größter Rückschlag (8 Wochen) ≤ 8 %
ZUFLUSS = (1.1, 0.9)           # Volumen an steigenden ÷ fallenden Tagen: ab 1,1 Zufluss, unter 0,9 Abfluss
from zeichen import TROCKEN_TAGE, TROCKEN_VERGLEICH  # noqa: E402  Volumen trocken: eine Quelle (zeichen)
from zeichen import RS_HOCH as RS_MASS   # noqa: E402  RS-Linie am Hoch: ein Maßstab für App, Chart und Zeichen (0,99)
QUARTAL = 63           # RS-Rang wie das RS-Rating von IBD: ein Quartal in Handelstagen,
Q3, Q4 = 3, 4          # das dritte und vierte Quartal zurück,
GEWICHT_LETZTES = 0.4  # das letzte Quartal zählt 40 % …
GEWICHT_FRUEHER = 0.2  # … die drei davor je 20 %;
RANG_SPANNE = 98       # Rang 1 bis 99
from masse import DATUM, JAHR_TAGE, MONAT_TAGE, QUARTALE_JAHR, VOL_TAGE, VORJAHR_ZURUECK, ZWEI_JAHRE_ZURUECK  # noqa: E402
KURS_NAH = 0.97                         # Kurs „am Hoch“: höchstens 3 % darunter (wie der Chart)
HOCH_MITTEL = 25.0                      # Abstand zum 52-Wochen-Hoch: bis 25 % „mittel“ (Minervini), darüber „fern“


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
GD50_MIN_TAGE = 40       # GD50 der Mitglieder ab 40 Tagen Daten
GRUPPE_MIN = 5           # eine Gruppe ab 5 Titeln (wie das Rudel)
VOR_4_WOCHEN_W = 5       # Wochenreihe: der 5. Wert zurück = vor 4 Wochen
BREITE_MIN_TITEL = 5     # Breite der Gruppe ab 5 Mitgliedern mit Daten
SCHWEIF_WOCHEN = 5       # Weg im Rotationsbild: die letzten 5 Wochen
DREI_JAHRE_ZURUECK = 13  # vor drei Jahren: der 13. Quartalswert zurück
EPS_MIN_BASIS = 0.05     # Jahresrate erst ab 5 Cent Gewinn je Aktie im Basisjahr (sonst keine Rate)
ROT_PUNKTE = 4           # Fundament rot ab 4 roten Prüfpunkten
THEMA_TITEL = 4          # Themenname: die 4 stärksten Titel
ANFUEHRER_ZAHL = 3       # Anführer einer Gruppe: die 3 stärksten
VORNE_GRUEN = 2  # Geldfluss grün: mindestens 2 Gruppen vorne und kein Abfluss
ROT_ERLAUBT = 1  # Fundament grün: höchstens 1 roter Prüfpunkt
LUECKE_PCT = 2   # Lücke nach oben ab 2 % mit Volumen


def _pfad(name):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, name)


JUNG_MIN = QUARTAL + 2 * 20      # junge Titel ab einem Quartal plus 8 Wochen Rückblick (Micky, 09.11.2026)


def _wert(C):
    """RS-Wert nach IBD (letztes Quartal 40 %, die drei davor je 20 %) – bei jungen Titeln nur aus den Quartalen, die
    sie haben, Gewichte darauf verteilt. Bei voller Historie genau der IBD-Formel."""
    letzt = C.iloc[-1]
    summe, gewicht = 0 * letzt.fillna(0), 0 * letzt.fillna(0)
    for k, w in ((1, GEWICHT_LETZTES), (2, GEWICHT_FRUEHER), (Q3, GEWICHT_FRUEHER), (Q4, GEWICHT_FRUEHER)):
        if len(C) <= QUARTAL * k:
            break
        q = letzt / C.iloc[-1 - QUARTAL * k] - 1
        da = q.notna()
        summe, gewicht = summe + (w * q).where(da, 0), gewicht + w * da
    return (summe / gewicht.where(gewicht > 0)).where(letzt.notna())


def _rang(C):
    w = _wert(C).dropna()
    return (w.rank(pct=True) * RANG_SPANNE + 1).round()


def _zusatz(rv):
    """Titel außerhalb des Reviers, die trotzdem mitgerechnet werden: Watchlist und jeder auf der Titelseite geöffnete
    Titel (ohne SPY/QQQ/IWM). Sektor und Branche aus dem Steckbrief; sie zählen nicht in die Gruppen (wie im Rudel),
    bekommen aber deren Geldfluss. Ergebnis: {Ticker: {sektor, branche, etf, herkunft}}; die Marken der Listen setzt die Seite frisch (watchlists.zeichen)."""
    import daten
    import tpo_daten
    import watchlists
    try:
        wl = set(watchlists.alle())
    except Exception:  # noqa: BLE001
        wl = set()
    try:
        offen = tpo_daten._geoeffnet()
    except Exception:  # noqa: BLE001
        offen = set()
    aus = {}
    for t in sorted((wl | offen) - set(rv.index) - set(tpo_daten.FEST)):
        sb = daten.steckbrief_gespeichert(t) or {}
        aus[t] = {"sektor": sb.get("sektor", ""), "branche": sb.get("branche", ""),
                  "etf": sektoren.sektor_von(sb.get("sektor", "")) or "",
                  "herkunft": "Watchlist" if t in wl else "geöffnet"}
    return aus


def richtung(jetzt, davor):
    """Richtung der RS-Linie aus ihrer Steigung in 4 Wochen (jetzt) und den 4 Wochen davor → steigt schneller, dreht
    nach oben, steigt, dreht nach unten, fällt oder None (Micky 21.11.2026)."""
    if jetzt is None:
        return None
    if jetzt > 0:
        if davor is not None and davor <= 0:
            return "dreht nach oben"
        return "steigt schneller" if davor is not None and jetzt > davor else "steigt"
    return "dreht nach unten" if davor is not None and davor > 0 else "fällt"


MOMENTUM_FENSTER = {"1M": 22, "3M": 67, "6M": 126}   # Kullamägi: Scanner über 1, 3 und 6 Monate (Handelstage)
MOMENTUM_SPITZE = 0.98         # Kullamägi: die besten 1–2 % des Reviers in einem Fenster = 🚀
KLASSEN = ("Garde", "Angriff", "Vorhut", "Ohne Nachschub", "Rückzug")   # Schlachtordnung (Micky 21.11.2026)
ANGRIFF_KLASSEN = (1, 2)       # Garde und Angriff: Front und Truppen vorn
VORNE_KLASSEN = (1, 2, 3)      # dazu die Vorhut: die Linie steigt, der Nachschub ist offen
STEIGT = ("steigt schneller", "steigt", "dreht nach oben")


def dreifach(x):
    """Dreifacher Rückenwind ▲▲▲: Kurs (Garde oder Angriff), Geld (Geld-Ampel grün) und Zahlen (Ampel grün) zugleich."""
    return bool(x) and klasse(x) in ANGRIFF_KLASSEN and x.get("geld_ampel") == "grün" \
        and (x.get("zahlen") or {}).get("ampel") == "grün"


def klasse(x):
    """Klasse 1–5 aus Front (RS-Linie) und Truppen (Volumen-Zufluss oder austrocknendes Volumen), keine Punkte: 1 Garde
    = RS-Hoch vor Kurs mit Zufluss · 2 Angriff = Linie steigt mit Zufluss · 3 Vorhut = steigt, Volumen gemischt · 4 Ohne Nachschub = steigt,
    Abfluss · 5 Rückzug = Linie dreht nach unten oder fällt. None = ohne RS-Linie (zu wenig Daten)."""
    r = x.get("richtung") or richtung(x.get("rs_tempo"), x.get("rs_vortempo"))
    hoch = x.get("rs_hoch_vor_kurs")
    if r is None and not hoch:
        return None
    if not hoch and r not in STEIGT:
        return 5                          # Technik: Klassennummer (Rückzug)
    z = x.get("zufluss")
    if x.get("trocken") or (z is not None and z >= ZUFLUSS[0]):   # trocken zählt wie Zufluss (Micky 22.11.2026)
        return 1 if hoch else 2
    return 4 if z is not None and z < ZUFLUSS[1] else 3   # Technik: Klassennummern (Ohne Nachschub, Vorhut)


def _trocken(vol):
    """Volumen trocknet aus (Minervini, letzte Kontraktion): in den letzten TROCKEN_TAGE Tagen der leiseste Tag seit
    50 Tagen. Anders als das Zeichen auf der Titelseite (O'Neil: untere Hälfte der Spanne) ohne Lage in der Spanne –
    Minervini sucht das Austrocknen nahe am Hoch; rechnen() wertet es nur bis HOCH_MITTEL unter dem Hoch (Micky
    22.11.2026: positives Zeichen, nicht rot)."""
    v = vol.dropna()
    v = v[v > 0]
    if len(v) <= TROCKEN_VERGLEICH + TROCKEN_TAGE:
        return False
    return any(v.iloc[i] <= v.iloc[i - TROCKEN_VERGLEICH:i + 1].min() for i in range(len(v) - TROCKEN_TAGE, len(v)))


def abstand_wort(abstand):
    """Abstand zum 52-Wochen-Hoch in % → nah (bis 3 %, wie der Chart), mittel (bis 25 %, Minervini), fern."""
    if abstand is None:
        return None
    return "nah" if abstand <= (1 - KURS_NAH) * 100 else "mittel" if abstand <= HOCH_MITTEL else "fern"


def _ud(kurs, vol):
    """Volumen an steigenden gegen fallende Tage (50 Tage) – über 1 = Zufluss."""
    r = kurs.pct_change(fill_method=None).iloc[-VOL_TAGE:]
    v = vol.reindex(r.index)
    auf, ab = v[r > 0].sum(), v[r < 0].sum()
    return float(auf / ab) if ab else None


def _gruppe(art, name, mitglieder, C, V):
    g = [m for m in mitglieder if m in C.columns]
    if len(g) < GRUPPE_MIN:
        return None
    kurs = 100 * (1 + C[g].pct_change(fill_method=None).iloc[1:].mean(axis=1, skipna=True)).cumprod()
    vol = V[g].iloc[1:].sum(axis=1, min_count=1)
    rot = sektoren.reihen(kurs, C[MARKT])
    if len(rot) < 6:
        return None
    s, w = rot["staerke"], rot["schwung"]
    feld = sektoren.feld(s.iloc[-1], w.iloc[-1])
    vorher = sektoren.feld(s.iloc[-VOR_4_WOCHEN_W], w.iloc[-VOR_4_WOCHEN_W])
    seit = 1
    while seit < len(s) and sektoren.feld(s.iloc[-1 - seit], w.iloc[-1 - seit]) == feld:
        seit += 1
    ud = _ud(kurs, vol)
    # Breite in der Gruppe (Auktion, 13.11.2026): Anteil der Mitglieder über dem GD50, heute und vor 4 Wochen
    x = C[g]
    g50 = x.rolling(50, min_periods=GD50_MIN_TAGE).mean()
    def _br(i):
        ok = g50.iloc[i].notna() & x.iloc[i].notna()
        return round(float((x.iloc[i][ok] > g50.iloc[i][ok]).mean() * 100), 0) if ok.sum() >= BREITE_MIN_TITEL else None
    breite, breite_vor4 = _br(-1), _br(-1 - WOCHEN4)
    k8 = kurs.iloc[-2 * WOCHEN4:]
    rueck = float((1 - k8 / k8.cummax()).max() * 100)
    return {"art": art, "name": name, "anzahl": len(g), "feld": feld, "feld_vor4": vorher, "seit_wochen": seit,
            "rueckschlag": round(rueck, 1),
            "stabil": feld == "Führend" and seit >= STABIL_WOCHEN and rueck <= STABIL_RUECKSCHLAG,
            "staerke": round(float(s.iloc[-1]), 1), "schwung": round(float(w.iloc[-1]), 1),
            "weg": [[round(float(a), 1), round(float(b), 1)] for a, b in zip(s.iloc[-SCHWEIF_WOCHEN:], w.iloc[-SCHWEIF_WOCHEN:])],
            "zufluss": round(ud, 2) if ud else None, "breite": breite, "breite_vor4": breite_vor4,
            "mitglieder": g}


def _gruppen_index(mitglieder, B):
    """Gleichgewichteter Tageskerzen-Index einer Gruppe aus den Massive-Tagen der Mitglieder (zwei Jahre): Schluss =
    Index des Vortags × mittlere Rendite; Eröffnung, Hoch und Tief ebenso, jeweils gegen den Schluss des Vortags;
    Volumen = Summe. → DataFrame oder None."""
    g = [m for m in mitglieder if m in B["Close"].columns]
    if len(g) < GRUPPE_MIN:
        return None
    c = B["Close"][g]
    vor = c.shift()
    r = (c / vor).mean(axis=1, skipna=True).iloc[1:]
    kurs = 100 * r.cumprod()
    basis = kurs.shift().fillna(100)
    df = pd.DataFrame({k: basis * (B[k][g] / vor).mean(axis=1, skipna=True).iloc[1:] for k in ("Open", "High", "Low")})
    df["Close"], df["Volume"] = kurs, B["Volume"][g].iloc[1:].sum(axis=1, min_count=1)
    df["High"] = df[["High", "Close", "Open"]].max(axis=1)
    df["Low"] = df[["Low", "Close", "Open"]].min(axis=1)
    return df.dropna(subset=["High", "Low", "Close"])


ZIRKEL_FELDER = ("phase", "name", "ziel", "wort", "keim", "traegt", "wochen", "gewicht_keim", "gewicht_traegt")


def _ein_zirkel(arg):
    """Zirkel einer Gruppe aus ihrem Index (für den Prozess-Pool) → dict oder None."""
    name, df, idx, start = arg
    import zeichen
    if df is None:
        return None
    try:
        z = zeichen.zirkel(zeichen.fuer_titel(name, df, idx, start=start, mit_wertzone=False))
    except Exception:  # noqa: BLE001 – eine Gruppe ohne Zirkel steht trotzdem in der Liste
        return None
    return {x: z.get(x) for x in ZIRKEL_FELDER} if z else None


def _gruppen_zirkel(gruppen, B, ampel=None):
    """Der Zirkel jeder Gruppe (Micky 23.11.2026: Branchen auf den Zirkel – Weinstein: erst die Gruppe, dann der
    Titel): Kreislauf ihres Index mit den Zeichen relativ zum S&P 500 (zeichen.fuer_titel) → g["zirkel"]; in
    mehreren Prozessen wie der Zirkel-Lauf der Titel."""
    from concurrent.futures import ProcessPoolExecutor
    import daten
    import zeichen
    idx = daten.kurse_gespeichert(daten.INDEX)
    if idx is None:
        return
    start = zeichen.startdatum(idx, ampel)          # ampel = das Lagebild von heute (zirkel.lagebild_vorab)
    arg = [(g["name"], _gruppen_index(g["mitglieder"], B), idx, start) for g in gruppen]
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 1)) as ex:
        for g, z in zip(gruppen, ex.map(_ein_zirkel, arg)):
            g["zirkel"] = z


def _geld_ampel(sek, bra, th=None):
    """Drei Stimmen: Sektor, Branche, Thema (Micky, 09.11.2026). Grün = mindestens zwei vorne (führend oder
    erstarkend) und keine schwächelnd (Feld „Ermüdend“, das Geld fließt ab); gelb = eine vorne; rot = keine. Ohne Thema zählen Sektor und
    Branche – dann müssen beide vorne sein."""
    stimmen = [x for x in (sek, bra, th) if x]
    vorne = sum(1 for x in stimmen if x["feld"] in VORNE)
    abfluss = any(x["feld"] == "Ermüdend" for x in stimmen)
    return "grün" if vorne >= VORNE_GRUEN and not abfluss else "gelb" if vorne else "rot"


ROE_MIN = 17.0                 # Eigenkapitalrendite ab 17 % (O'Neil)
JAHR_MIN = 25.0                # Jahresgewinne: drei Jahre je ab +25 %
EP_SPRUNG = 10.0           # Episodic Pivot (Kullamägi): Kurssprung ab 10 % …
EP_VOLUMEN = 3.0           # … mit mindestens 3-fachem Volumen (Micky 05.11.2026: grün ab 3-fach)
LUECKE_VOLUMEN = 1.5           # Lücke nach oben mit Volumen
ABVERKAUF = -3.0               # Abverkauf nach den Zahlen ab −3 %


def _jahre(gewinne):
    """Jahresgewinne der letzten drei Jahre (je vier Quartale bereinigter Gewinn) – grün: jedes Jahr ab +25 %;
    rot: ein Jahr fällt; sonst gelb."""
    from fundament import _p
    eps = gewinne["eps"].dropna()
    if len(eps) < 16:
        return ["grau", "zu wenige Quartale für drei Jahre"]
    summe = eps.rolling(QUARTALE_JAHR).sum().dropna()
    j = [summe.iloc[-DREI_JAHRE_ZURUECK], summe.iloc[-ZWEI_JAHRE_ZURUECK], summe.iloc[-VORJAHR_ZURUECK], summe.iloc[-1]]
    # Basis unter 5 Cent je Aktie (CRDO 13.11.2026: Rundungsrest 1e-17 → +4,6 Trillionen %) ergibt keine Rate
    w = [((b / a - 1) * 100) if a >= EPS_MIN_BASIS else None for a, b in zip(j, j[1:])]
    text = " / ".join("–" if x is None else f"{_p(x)} %" for x in w) + " (drei Jahre, je vier Quartale)"
    if any(b < a for a, b in zip(j, j[1:])):
        return ["rot", text]
    if all(x is not None and x >= JAHR_MIN for x in w):
        return ["grün", text]
    return ["gelb", text]


def _roe(tv):
    """Eigenkapitalrendite des letzten Geschäftsjahres (TradingView, return_on_equity_fy)."""
    try:
        x = float(tv.get("return_on_equity_fy"))
    except (TypeError, ValueError, AttributeError):
        return ["grau", "keine Daten"]
    if x != x:
        return ["grau", "keine Daten"]
    t_ = f"{x:.0f} %".replace(".", ",")
    return ["grün", t_] if x >= ROE_MIN else ["rot", t_] if x < 0 else ["gelb", t_ + " (unter 17 %)"]


def _tv():
    """TradingView-Kennzahlen des Nachtlaufs je Ticker (für ROE)."""
    import tv_kennzahlen
    if not os.path.exists(tv_kennzahlen.DATEI):
        return {}
    return pd.read_csv(tv_kennzahlen.DATEI).drop_duplicates("ticker").set_index("ticker").to_dict("index")


def _zahlen(tk, tv):
    """Fundament-Punkte (Minervini/O'Neil), Termin und letzte Zahlen aus dem Zwischenspeicher (ohne Abruf).
    Punkte: Quartalsgewinn, Beschleunigung, Umsatz (ab 15 %, beschleunigend), Marge, Überraschung, Schätzungen,
    Jahresgewinne (drei Jahre je ab 25 %), Eigenkapitalrendite (ab 17 %), Institutionen."""
    import fundament
    import quellen
    pfad = os.path.join(quellen.SPEICHER, f"{tk.upper()}.json")
    try:
        fd = quellen._aus_json(json.load(open(pfad, encoding="utf-8")))
        f = fundament.ampeln(fd)
    except Exception:  # noqa: BLE001 – ohne Yahoo/SEC: ROE und Termin von TradingView, Ampel grau
        d = pd.to_datetime((tv.get(tk) or {}).get("earnings_release_next_date"), errors="coerce")
        return {"ampel": "grau", "punkte": {"Eigenkapitalrendite": _roe(tv.get(tk))}, "zeichen": [],
                "termin": f"{d:%Y-%m-%d}" if pd.notna(d) else None, "letzte": None}
    pk = {k: list(v) for k, v in f["punkte"].items() if k != "Jahresgewinn"}
    pk["Jahresgewinne 3 Jahre"] = _jahre(fd["gewinne"])
    pk["Eigenkapitalrendite"] = _roe(tv.get(tk))
    pk["Institutionen"] = list(fundament.institutionen(fd.get("institutionen")))
    rot = sum(1 for a, _ in pk.values() if a == "rot")
    q, bes, ums = (pk.get(k, ("grau", ""))[0] for k in ("Quartalsgewinn zum Vorjahr", "Beschleunigung Gewinn", "Umsatz"))
    if q == "grau" and ums == "grau":
        ampel = "grau"
    elif q == "grün" and "grün" in (bes, ums) and rot <= ROT_ERLAUBT:
        ampel = "grün"
    elif q == "rot" and ums == "rot" or rot >= ROT_PUNKTE:
        ampel = "rot"
    else:
        ampel = "gelb"
    termin = None
    t = fd.get("termin")
    if t is not None and len(t):
        d = pd.to_datetime(t["datum"].iloc[0], errors="coerce")
        heute = pd.Timestamp.today().normalize()
        termin = f"{d:%Y-%m-%d}" if pd.notna(d) and d >= heute - pd.Timedelta(days=1) else None   # alte Termine verwerfen
    if termin is None:                           # sonst der nächste Termin laut TradingView
        d = pd.to_datetime((tv.get(tk) or {}).get("earnings_release_next_date"), errors="coerce")
        termin = f"{d:%Y-%m-%d}" if pd.notna(d) else None
    gew = fd.get("gewinne")
    letzte = None
    if gew is not None and len(gew):
        u = gew["ueberraschung_pct"].iloc[-1]
        letzte = {"tag": str(gew.index[-1])[:DATUM], "nach_schluss": int(gew["nach_schluss"].iloc[-1]),
                  "ueberraschung": float(u) if u == u else None}
    return {"ampel": ampel, "punkte": pk, "zeichen": f["zeichen"], "termin": termin, "letzte": letzte}


def _reaktion(tk, letzte, M):
    """Reaktion auf die letzten Zahlen (Tag danach bzw. Meldetag vor Börsenbeginn), gedeutet:
    🟢 Episodic Pivot (≥ +10 %, Lücke über das Vortageshoch, Volumen ≥ 3-fach) · 🟢 Lücke nach oben mit Volumen
    (Eröffnung ≥ 2 % über dem Vortagesschluss, Schluss im Plus, Volumen ≥ 1,5-fach) · 🔴 Abverkauf trotz Überraschung
    (Überraschung positiv, Kurs ≤ −3 %) · 🔴 Abverkauf (≤ −3 %) · sonst 🟡 kaum Reaktion."""
    C, O, H, V = M
    if not letzte or tk not in C.columns:
        return None
    c = C[tk].dropna()
    tag = pd.Timestamp(letzte["tag"])
    nach = c.index[c.index > tag] if letzte["nach_schluss"] else c.index[c.index >= tag]
    if not len(nach) or c.index.get_loc(nach[0]) == 0:
        return None
    i = c.index.get_loc(nach[0])
    d, d0 = c.index[i], c.index[i - 1]
    v = V[tk].reindex(c.index)
    s50 = v.iloc[max(0, i - VOL_TAGE):i].mean()
    vol = float(v.iloc[i] / s50) if s50 == s50 and s50 else None
    kurs = float((c.iloc[i] / c.iloc[i - 1] - 1) * 100)
    eroeff = O[tk].get(d)
    luecke = (float(eroeff / c.iloc[i - 1] - 1) * 100) if eroeff == eroeff and eroeff else None
    ueber = letzte.get("ueberraschung")
    if kurs >= EP_SPRUNG and (vol or 0) >= EP_VOLUMEN and eroeff and eroeff > H[tk].get(d0, np.inf):
        art = ("grün", "Episodic Pivot")
    elif luecke is not None and luecke >= LUECKE_PCT and kurs > 0 and (vol or 0) >= LUECKE_VOLUMEN:
        art = ("grün", "Lücke nach oben mit Volumen")
    elif kurs <= ABVERKAUF and ueber is not None and ueber > 0:
        art = ("rot", "Abverkauf trotz Überraschung")
    elif kurs <= ABVERKAUF:
        art = ("rot", "Abverkauf nach den Zahlen")
    else:
        art = ("gelb", "kaum Reaktion")
    return {"tag": f"{d:%Y-%m-%d}", "kurs": round(kurs, 1), "volumen": round(vol, 2) if vol else None,
            "luecke": round(luecke, 1) if luecke is not None else None, "ueberraschung": ueber,
            "ampel": art[0], "deutung": art[1]}


def _themenname(g, rang):
    top = sorted(g["mitglieder"], key=lambda t: -rang.get(t, 0))[:THEMA_TITEL]
    return ", ".join(top) + " · " + ", ".join(b for b, _ in g.get("branchen", [])[:3])


def rechnen(netz=False):
    """Alles rechnen und speichern; Ergebnis als dict. netz=True (Nachtlauf): Fundamentdaten der Titel in einer Stufe
    holen, wenn älter als 12 Stunden (quellen.laden)."""
    import rudel
    rv = rudel.revier()
    zusatz = _zusatz(rv)                    # Watchlist und geöffnete Titel außerhalb des Reviers (09.11.2026)
    alle = list(rv.index) + list(zusatz)
    C = massive.kursmatrix(alle + [MARKT], TAGE)
    V = massive.kursmatrix(alle + [MARKT], TAGE, "Volume")
    O = massive.kursmatrix(alle, 100, "Open")     # letzte Zahlen höchstens ein Quartal her
    H = massive.kursmatrix(alle, 100, "High")
    B = massive.kursmatrix(alle, livermore.STELLUNG_JAHRE * JAHR_TAGE, ["Open", "High", "Low", "Close", "Volume"])   # Zirkel der Gruppen
    tv = _tv()
    titel_, ohne_daten = [], []
    for t in alle:
        n_ = int(C[t].notna().sum()) if t in C.columns else 0
        if n_ >= JUNG_MIN + 1:
            titel_.append(t)
        else:                                   # nicht still weglassen: auf der Seite in „Ohne Stufe“ mit Grund
            ohne_daten.append({"tk": t, "grund": (f"zu jung ({n_} Handelstage, nötig {JUNG_MIN + 1})" if n_
                                         else "keine Kurse bei Massive (Börse außerhalb der USA oder Fonds)")})
    X = C[titel_]
    r0, r4, r8 = _rang(X), _rang(X.iloc[:-WOCHEN4]), _rang(X.iloc[:-2 * WOCHEN4])
    # Gruppen: Sektoren (über die Revier-Titel je Sektor-ETF), Branchen, Themen
    gruppen, sek_von, bra_von, thema_von = [], {}, {}, {}
    for etf, mit in rv.groupby("etf").groups.items():
        if etf:
            g = _gruppe("Sektor", sektoren.SEKTOREN.get(etf, etf), list(mit), C, V)
            if g:
                gruppen.append(g)
                sek_von.update({t: g for t in mit})
                sek_von.update({t: g for t, z in zusatz.items() if z["etf"] == etf})
    for br, mit in rv.groupby("branche").groups.items():
        if br:
            g = _gruppe("Branche", br, list(mit), C, V)
            if g:
                gruppen.append(g)
                bra_von.update({t: g for t in mit})
                bra_von.update({t: g for t, z in zusatz.items() if z["branche"] == br})
    for th in rudel.themen():
        g = _gruppe("Thema", _themenname(th, r0), th["mitglieder"], C, V)
        if g:
            g["nr"] = th.get("nr")
            gruppen.append(g)
            thema_von.update({t: g for t in th["mitglieder"]})
    # Momentum (Kullamägi, 22.11.2026): Rendite über 1, 3, 6 Monate; die besten 2 % des Reviers je Fenster = 🚀
    mom = {k: C.iloc[-1] / C.iloc[-1 - n] - 1 for k, n in MOMENTUM_FENSTER.items()}
    spitze = {k: float(r_.reindex(rv.index).quantile(MOMENTUM_SPITZE)) for k, r_ in mom.items()}
    # Titel
    titel = {}
    spy = C[MARKT]
    for tk in r0.index:
        r, a4, a8 = float(r0[tk]), r4.get(tk), r8.get(tk)
        if a4 is None or a8 is None or a4 != a4 or a8 != a8:
            continue
        tempo, vortempo = r - a4, a4 - a8
        besch = tempo - vortempo
        c = C[tk].dropna()
        rs = (c / spy.reindex(c.index)).dropna()
        rs_hoch = bool(len(rs) >= JUNG_MIN and rs.iloc[-1] >= RS_MASS * rs.iloc[-JAHR_TAGE:].max())   # jung: seit Börsengang
        # Tempo der RS-Linie selbst: Steigung in 4 Wochen und in den 4 Wochen davor (%)
        rs_tempo = float((rs.iloc[-1] / rs.iloc[-1 - WOCHEN4] - 1) * 100) if len(rs) > 2 * WOCHEN4 else None
        rs_vortempo = (float((rs.iloc[-1 - WOCHEN4] / rs.iloc[-1 - 2 * WOCHEN4] - 1) * 100)
                       if len(rs) > 2 * WOCHEN4 else None)
        vol = V[tk].reindex(c.index)
        zufluss = _ud(c, vol)                         # Volumen-Zufluss des Titels selbst (Akkumulation)
        kurs_hoch = bool(len(c) >= JUNG_MIN and c.iloc[-1] >= KURS_NAH * c.iloc[-JAHR_TAGE:].max())
        abstand = float((1 - c.iloc[-1] / c.iloc[-JAHR_TAGE:].max()) * 100)
        trocken = abstand <= HOCH_MITTEL and _trocken(vol)   # nur in der Konsolidierung nahe am Hoch (Minervini: ≤ 25 %)
        sek, bra, th = sek_von.get(tk), bra_von.get(tk), thema_von.get(tk)
        x = {"rang": int(r), "rang_vor4": int(a4), "tempo": int(tempo), "beschleunigung": int(besch),
             "rs_hoch_vor_kurs": rs_hoch and not kurs_hoch,
             "abstand_hoch": round(abstand, 1),
             "momentum": {k: [round(float(mom[k][tk]) * 100, 1), bool(mom[k][tk] >= spitze[k])]
                          for k in MOMENTUM_FENSTER if tk in mom[k] and mom[k][tk] == mom[k][tk]},
             "rs_tempo": round(rs_tempo, 1) if rs_tempo is not None else None,
             "rs_vortempo": round(rs_vortempo, 1) if rs_vortempo is not None else None,
             "zufluss": round(zufluss, 2) if zufluss else None, "trocken": trocken,
             "sektor_stabil": bool(sek and sek["stabil"]), "branche_stabil": bool(bra and bra["stabil"]),
             "sektor": sek["name"] if sek else (zusatz[tk]["sektor"] if tk in zusatz else rv.loc[tk, "sektor"]),
             "sektor_feld": sek["feld"] if sek else None,
             "branche": bra["name"] if bra else (zusatz[tk]["branche"] if tk in zusatz else rv.loc[tk, "branche"]),
             "branche_feld": bra["feld"] if bra else None,
             "jung": round(len(c) / MONAT_TAGE) if len(c) < 252 + 2 * WOCHEN4 else None, "herkunft": zusatz[tk]["herkunft"] if tk in zusatz else "Revier",
             "thema": th["name"] if th else None, "thema_feld": th["feld"] if th else None,
             "geld_ampel": _geld_ampel(sek, bra, th), "kurs": round(float(c.iloc[-1]), 2)}
        x["richtung"] = richtung(x["rs_tempo"], x["rs_vortempo"])
        x["klasse"] = klasse(x)                  # Schlachtordnung statt Stufe (Micky 22.11.2026)
        if x["klasse"] in VORNE_KLASSEN and netz:   # neue Zahlen holen nur für Garde, Angriff und Vorhut …
            try:
                import quellen
                quellen.laden(tk)
            except Exception:  # noqa: BLE001 – dann ohne Zahlen
                pass
        z = _zahlen(tk, tv)                      # … gelesen für alle (Prüf-Agent 13.11.2026: Short-Titel standen
        if z:                                    # sonst ohne Zahlen da)
            z["reaktion"] = _reaktion(tk, z.pop("letzte"), (C, O, H, V))
        x["zahlen"] = z
        # Einzelkämpfer (Micky 21.11.2026): stark (Garde oder Angriff), die Branche hinten
        x["einzelkaempfer"] = bool(x["klasse"] in ANGRIFF_KLASSEN
                                   and bra and bra["feld"] not in VORNE)
        titel[tk] = x
    for g in gruppen:                            # Anführer und Verfolger je Gruppe: folgen die Schwestern?
        anfuehrer_verfolger(g, titel)
    import tpo_daten                             # das Lagebild von heute (Spitze aus den Klassen dieses Laufs) zuerst,
    import zirkel                                # dann der Zirkel der Gruppen – dasselbe Fenster wie bei den Titeln
    lb = zirkel.lagebild_vorab(zirkel.liste(tpo_daten.lauf_liste()), rw=titel)     # (Audit 26.11.2026)
    _gruppen_zirkel(gruppen, B, lb["ampel"])
    stand = f"{C.index[-1]:%Y-%m-%d}"
    erg = {"stand": stand, "gruppen": gruppen, "titel": titel, "ohne_daten": ohne_daten}
    json_schreiben(_pfad("stand.json"), erg, ensure_ascii=False)
    return erg


def anfuehrer_verfolger(g, titel, n=ANFUEHRER_ZAHL):
    """Je Gruppe (22.11.2026 auf die Schlachtordnung umgestellt): Anführer = Garde oder Angriff mit Rang ab STARK,
    höchster Rang zuerst (bei Gleichstand mehr Zufluss); Verfolger = Garde oder Angriff mit Rang darunter, größtes
    Tempo zuerst. „vorne“ zählt Garde und Angriff gegen alle Mitglieder."""
    m = [(tk, titel[tk]) for tk in g.get("mitglieder", []) if tk in titel]
    vorn = [(tk, x) for tk, x in m if x.get("klasse") in ANGRIFF_KLASSEN]
    anf = sorted(((tk, x) for tk, x in vorn if x["rang"] >= STARK),
                 key=lambda p: (-p[1]["rang"], -(p[1].get("zufluss") or 0)))
    ver = sorted(((tk, x) for tk, x in vorn if x["rang"] < STARK), key=lambda p: -p[1]["tempo"])
    g["anfuehrer"] = [tk for tk, _ in anf[:n]]
    g["verfolger"] = [tk for tk, _ in ver[:n]]
    g["vorne"] = [len(vorn), len(m)]
    return g


def laden():
    """Gespeicherter Stand (ohne Rechnen) oder None."""
    return json_lesen(_pfad("stand.json"))


