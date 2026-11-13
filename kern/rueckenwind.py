"""Rückenwind (Konzept: KONZEPT_RUECKENWIND.md, 09.11.2026) – eigene Seite, getrennt von den Setups.

Je Titel des Reviers drei Rückenwinde als Ampeln, dazu Earnings:
  Kurs   RS-Dynamik: Stärke (RS-Rang 1–99 wie IBD, rs_rang.wert), Tempo (Veränderung des Rangs in 4 Wochen),
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
Stufen (Ampel, keine Punktzahl): Entsteht · Läuft · Ermüdet · Abfluss. Logbuch: Eintritt in eine Stufe mit Datum und
Kurs (Beobachtung, kein Urteil). Alles aus den Massive-Tagesdateien des Nachtlaufs, gespeichert in daten/rueckenwind/.
"""
import json
import os

import numpy as np
import pandas as pd

import massive
import sektoren
from dateien import json_lesen, json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "rueckenwind")
MARKT = "SPY"
TAGE = 320                     # 12 Monate RS-Rang + 8 Wochen zurück
WOCHEN4 = 20                   # Handelstage in 4 Wochen
VOL_TAGE = 50
# Schwellen der Stufen (Probelauf 09.11.2026, siehe LIESMICH)
STARK = 85                     # Läuft: Rang ab 85
MITTEL = (50, 85)              # Entsteht: Rang 50 bis unter 85 …
TEMPO_HOCH = 15                # … mit mindestens +15 Rangpunkten in 4 Wochen und positiver Beschleunigung
TEMPO_HAELT = -5               # Läuft: Tempo nicht schlechter als −5
ERMUEDET = (80, -10, -15, 5)   # Ermüdet: Rang ab 80, Tempo −10 oder schlechter – oder das Tempo bricht ein
                               # (Beschleunigung −15 oder schlechter) und der Titel rückt kaum noch vor (Tempo höchstens
                               # +5); Micky 09.11.2026, früheste Warnung
ABFLUSS = (70, -20)            # Abfluss: vor 4 Wochen ab 70, seitdem 20 Rangpunkte oder mehr verloren
VORNE = ("Führend", "Erstarkend")
STABIL_WOCHEN, STABIL_RUECKSCHLAG = 8, 8.0   # stabil: führt seit 8 Wochen und größter Rückschlag (8 Wochen) ≤ 8 %
ZUFLUSS = (1.1, 0.9)           # Volumen an steigenden ÷ fallenden Tagen: ab 1,1 Zufluss, unter 0,9 Abfluss
STUFEN = ("Entsteht", "Läuft", "Ermüdet", "Abfluss")
from zeichen import RS_HOCH as RS_MASS   # noqa: E402  RS-Linie am Hoch: ein Maßstab für App, Chart und Zeichen (0,99)
KURS_NAH = 0.97                         # Kurs „am Hoch“: höchstens 3 % darunter (wie der Chart)


def _pfad(name):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, name)


QUARTAL = 63
JUNG_MIN = QUARTAL + 2 * 20      # junge Titel ab einem Quartal plus 8 Wochen Rückblick (Micky, 09.11.2026)


def _wert(C):
    """RS-Wert nach IBD (letztes Quartal 40 %, die drei davor je 20 %) – bei jungen Titeln nur aus den Quartalen, die
    sie haben, Gewichte darauf verteilt. Bei voller Historie genau rs_rang.wert."""
    letzt = C.iloc[-1]
    summe, gewicht = 0 * letzt.fillna(0), 0 * letzt.fillna(0)
    for k, w in ((1, 0.4), (2, 0.2), (3, 0.2), (4, 0.2)):
        if len(C) <= QUARTAL * k:
            break
        q = letzt / C.iloc[-1 - QUARTAL * k] - 1
        da = q.notna()
        summe, gewicht = summe + (w * q).where(da, 0), gewicht + w * da
    return (summe / gewicht.where(gewicht > 0)).where(letzt.notna())


def _rang(C):
    w = _wert(C).dropna()
    return (w.rank(pct=True) * 98 + 1).round()


def _zusatz(rv):
    """Titel außerhalb des Reviers, die trotzdem mitgerechnet werden: Watchlist und jeder auf der Titelseite geöffnete
    Titel (ohne SPY/QQQ/IWM). Sektor und Branche aus dem Steckbrief; sie zählen nicht in die Gruppen (wie im Rudel),
    bekommen aber deren Geldfluss. Ergebnis: ({Ticker: {sektor, branche, etf, herkunft}}, Menge der Watchlist-Titel)."""
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
    return aus, wl


def _stufe(r, t, b, r4):
    if r4 is not None and r4 >= ABFLUSS[0] and t <= ABFLUSS[1]:
        return "Abfluss"
    if r >= ERMUEDET[0] and (t <= ERMUEDET[1] or (b <= ERMUEDET[2] and t <= ERMUEDET[3])):
        return "Ermüdet"
    if r >= STARK and t >= TEMPO_HAELT:
        return "Läuft"
    if MITTEL[0] <= r < MITTEL[1] and t >= TEMPO_HOCH and b > 0:
        return "Entsteht"
    return None


def _ud(kurs, vol):
    """Volumen an steigenden gegen fallende Tage (50 Tage) – über 1 = Zufluss."""
    r = kurs.pct_change(fill_method=None).iloc[-VOL_TAGE:]
    v = vol.reindex(r.index)
    auf, ab = v[r > 0].sum(), v[r < 0].sum()
    return float(auf / ab) if ab else None


def _gruppe(art, name, mitglieder, C, V):
    g = [m for m in mitglieder if m in C.columns]
    if len(g) < 5:
        return None
    kurs = 100 * (1 + C[g].pct_change(fill_method=None).iloc[1:].mean(axis=1, skipna=True)).cumprod()
    vol = V[g].iloc[1:].sum(axis=1, min_count=1)
    rot = sektoren.reihen(kurs, C[MARKT])
    if len(rot) < 6:
        return None
    s, w = rot["staerke"], rot["schwung"]
    feld = sektoren.feld(s.iloc[-1], w.iloc[-1])
    vorher = sektoren.feld(s.iloc[-5], w.iloc[-5])
    seit = 1
    while seit < len(s) and sektoren.feld(s.iloc[-1 - seit], w.iloc[-1 - seit]) == feld:
        seit += 1
    ud = _ud(kurs, vol)
    # Breite in der Gruppe (Auktion, 13.11.2026): Anteil der Mitglieder über dem GD50, heute und vor 4 Wochen
    x = C[g]
    g50 = x.rolling(50, min_periods=40).mean()
    def _br(i):
        ok = g50.iloc[i].notna() & x.iloc[i].notna()
        return round(float((x.iloc[i][ok] > g50.iloc[i][ok]).mean() * 100), 0) if ok.sum() >= 5 else None
    breite, breite_vor4 = _br(-1), _br(-1 - WOCHEN4)
    k8 = kurs.iloc[-2 * WOCHEN4:]
    rueck = float((1 - k8 / k8.cummax()).max() * 100)
    return {"art": art, "name": name, "anzahl": len(g), "feld": feld, "feld_vor4": vorher, "seit_wochen": seit,
            "rueckschlag": round(rueck, 1),
            "stabil": feld == "Führend" and seit >= STABIL_WOCHEN and rueck <= STABIL_RUECKSCHLAG,
            "staerke": round(float(s.iloc[-1]), 1), "schwung": round(float(w.iloc[-1]), 1),
            "weg": [[round(float(a), 1), round(float(b), 1)] for a, b in zip(s.iloc[-5:], w.iloc[-5:])],
            "zufluss": round(ud, 2) if ud else None, "breite": breite, "breite_vor4": breite_vor4,
            "mitglieder": g}


def _geld_ampel(sek, bra, th=None):
    """Drei Stimmen: Sektor, Branche, Thema (Micky, 09.11.2026). Grün = mindestens zwei vorne (führend oder
    erstarkend) und keine schwächelnd (Feld „Ermüdend“, das Geld fließt ab); gelb = eine vorne; rot = keine. Ohne Thema zählen Sektor und
    Branche – dann müssen beide vorne sein."""
    stimmen = [x for x in (sek, bra, th) if x]
    vorne = sum(1 for x in stimmen if x["feld"] in VORNE)
    abfluss = any(x["feld"] == "Ermüdend" for x in stimmen)
    return "grün" if vorne >= 2 and not abfluss else "gelb" if vorne else "rot"


ROE_MIN = 17.0                 # Eigenkapitalrendite ab 17 % (O'Neil)
JAHR_MIN = 25.0                # Jahresgewinne: drei Jahre je ab +25 %
EP_SPRUNG, EP_VOLUMEN = 10.0, 3.0   # Episodic Pivot wie im System Kullamägi
LUECKE_VOLUMEN = 1.5           # Lücke nach oben mit Volumen
ABVERKAUF = -3.0               # Abverkauf nach den Zahlen ab −3 %


def _jahre(gewinne):
    """Jahresgewinne der letzten drei Jahre (je vier Quartale bereinigter Gewinn) – grün: jedes Jahr ab +25 %;
    rot: ein Jahr fällt; sonst gelb."""
    from fundament import _p
    eps = gewinne["eps"].dropna()
    if len(eps) < 16:
        return ["grau", "zu wenige Quartale für drei Jahre"]
    summe = eps.rolling(4).sum().dropna()
    j = [summe.iloc[-13], summe.iloc[-9], summe.iloc[-5], summe.iloc[-1]]
    # Basis unter 5 Cent je Aktie (CRDO 13.11.2026: Rundungsrest 1e-17 → +4,6 Trillionen %) ergibt keine Rate
    w = [((b / a - 1) * 100) if a >= 0.05 else None for a, b in zip(j, j[1:])]
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
    elif q == "grün" and "grün" in (bes, ums) and rot <= 1:
        ampel = "grün"
    elif q == "rot" and ums == "rot" or rot >= 4:
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
        letzte = {"tag": str(gew.index[-1])[:10], "nach_schluss": int(gew["nach_schluss"].iloc[-1]),
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
    s50 = v.iloc[max(0, i - 50):i].mean()
    vol = float(v.iloc[i] / s50) if s50 == s50 and s50 else None
    kurs = float((c.iloc[i] / c.iloc[i - 1] - 1) * 100)
    eroeff = O[tk].get(d)
    luecke = (float(eroeff / c.iloc[i - 1] - 1) * 100) if eroeff == eroeff and eroeff else None
    ueber = letzte.get("ueberraschung")
    if kurs >= EP_SPRUNG and (vol or 0) >= EP_VOLUMEN and eroeff and eroeff > H[tk].get(d0, np.inf):
        art = ("grün", "Episodic Pivot")
    elif luecke is not None and luecke >= 2 and kurs > 0 and (vol or 0) >= LUECKE_VOLUMEN:
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
    top = sorted(g["mitglieder"], key=lambda t: -rang.get(t, 0))[:4]
    return ", ".join(top) + " · " + ", ".join(b for b, _ in g.get("branchen", [])[:3])


def rechnen(netz=False):
    """Alles rechnen und speichern; Ergebnis als dict. netz=True (Nachtlauf): Fundamentdaten der Titel in einer Stufe
    holen, wenn älter als 12 Stunden (quellen.laden)."""
    import rudel
    rv = rudel.revier()
    zusatz, wl = _zusatz(rv)                    # Watchlist und geöffnete Titel außerhalb des Reviers (09.11.2026)
    alle = list(rv.index) + list(zusatz)
    C = massive.kursmatrix(alle + [MARKT], TAGE)
    V = massive.kursmatrix(alle + [MARKT], TAGE, "Volume")
    O = massive.kursmatrix(alle, 100, "Open")     # letzte Zahlen höchstens ein Quartal her
    H = massive.kursmatrix(alle, 100, "High")
    tv = _tv()
    titel_, ohne_daten = [], []
    for t in alle:
        n_ = int(C[t].notna().sum()) if t in C.columns else 0
        if n_ >= JUNG_MIN + 1:
            titel_.append(t)
        else:                                   # nicht still weglassen: auf der Seite in „Ohne Stufe“ mit Grund
            ohne_daten.append({"tk": t, "watchlist": t in wl,
                               "grund": (f"zu jung ({n_} Handelstage, nötig {JUNG_MIN + 1})" if n_
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
        rs_hoch = bool(len(rs) >= JUNG_MIN and rs.iloc[-1] >= RS_MASS * rs.iloc[-252:].max())   # jung: seit Börsengang
        # Tempo der RS-Linie selbst: Steigung in 4 Wochen und in den 4 Wochen davor (%)
        rs_tempo = float((rs.iloc[-1] / rs.iloc[-1 - WOCHEN4] - 1) * 100) if len(rs) > 2 * WOCHEN4 else None
        rs_vortempo = (float((rs.iloc[-1 - WOCHEN4] / rs.iloc[-1 - 2 * WOCHEN4] - 1) * 100)
                       if len(rs) > 2 * WOCHEN4 else None)
        zufluss = _ud(c, V[tk].reindex(c.index))      # Volumen-Zufluss des Titels selbst (Akkumulation)
        kurs_hoch = bool(len(c) >= JUNG_MIN and c.iloc[-1] >= KURS_NAH * c.iloc[-252:].max())
        stufe = _stufe(r, tempo, besch, a4)
        if stufe is None and rs_hoch and not kurs_hoch and tempo > 0:
            stufe = "Entsteht"                      # RS-Linie am Hoch vor dem Kurs: das stärkste frühe Zeichen
        sek, bra, th = sek_von.get(tk), bra_von.get(tk), thema_von.get(tk)
        x = {"rang": int(r), "rang_vor4": int(a4), "tempo": int(tempo), "beschleunigung": int(besch),
             "rs_hoch_vor_kurs": rs_hoch and not kurs_hoch, "stufe": stufe,
             "rs_tempo": round(rs_tempo, 1) if rs_tempo is not None else None,
             "rs_vortempo": round(rs_vortempo, 1) if rs_vortempo is not None else None,
             "zufluss": round(zufluss, 2) if zufluss else None,
             "sektor_stabil": bool(sek and sek["stabil"]), "branche_stabil": bool(bra and bra["stabil"]),
             "kurs_ampel": {"Entsteht": "grün", "Läuft": "grün", "Ermüdet": "gelb", "Abfluss": "rot"}.get(stufe, "grau"),
             "sektor": sek["name"] if sek else (zusatz[tk]["sektor"] if tk in zusatz else rv.loc[tk, "sektor"]),
             "sektor_feld": sek["feld"] if sek else None,
             "branche": bra["name"] if bra else (zusatz[tk]["branche"] if tk in zusatz else rv.loc[tk, "branche"]),
             "branche_feld": bra["feld"] if bra else None,
             "watchlist": tk in wl, "jung": round(len(c) / 21) if len(c) < 252 + 2 * WOCHEN4 else None, "herkunft": zusatz[tk]["herkunft"] if tk in zusatz else "Revier",
             "thema": th["name"] if th else None, "thema_feld": th["feld"] if th else None,
             "geld_ampel": _geld_ampel(sek, bra, th), "kurs": round(float(c.iloc[-1]), 2)}
        if stufe and netz:                       # neue Zahlen holen nur für Titel mit Stufe …
            try:
                import quellen
                quellen.laden(tk)
            except Exception:  # noqa: BLE001 – dann ohne Zahlen
                pass
        z = _zahlen(tk, tv)                      # … gelesen für alle (Prüf-Agent 13.11.2026: Short-Titel ohne Stufe
        if z:                                    # standen ohne Zahlen da)
            z["reaktion"] = _reaktion(tk, z.pop("letzte"), (C, O, H, V))
        x["zahlen"] = z
        titel[tk] = x
    for g in gruppen:                            # Anführer und Verfolger je Gruppe: folgen die Schwestern?
        anfuehrer_verfolger(g, titel)
    stand = f"{C.index[-1]:%Y-%m-%d}"
    erg = {"stand": stand, "gruppen": gruppen, "titel": titel, "ohne_daten": ohne_daten,
           "schwellen": {"stark": STARK, "mittel": MITTEL, "tempo_hoch": TEMPO_HOCH, "ermuedet": ERMUEDET,
                         "abfluss": ABFLUSS}}
    _logbuch(erg)
    json_schreiben(_pfad("stand.json"), erg, ensure_ascii=False)
    return erg


def anfuehrer_verfolger(g, titel, n=3):
    """Anführer = höchster RS-Rang in Stufe Läuft (bei Gleichstand mehr Zufluss); Verfolger = Stufe Entsteht, größtes
    Tempo zuerst. Je Gruppe (13.11.2026; bis 13.11.2026 über alle Titel für den Stab). Zählt auch, wie viele der
    Mitglieder vorne sind (Entsteht oder Läuft)."""
    m = [(tk, titel[tk]) for tk in g.get("mitglieder", []) if tk in titel]
    anf = sorted(((tk, x) for tk, x in m if x.get("stufe") == "Läuft"),
                 key=lambda p: (-p[1]["rang"], -(p[1].get("zufluss") or 0)))
    ver = sorted(((tk, x) for tk, x in m if x.get("stufe") == "Entsteht"), key=lambda p: -p[1]["tempo"])
    g["anfuehrer"] = [tk for tk, _ in anf[:n]]
    g["verfolger"] = [tk for tk, _ in ver[:n]]
    g["vorne"] = [len(anf) + len(ver), len(m)]
    return g


def _logbuch(erg):
    """Eintritt in eine Stufe mit Datum und Kurs; Austritt mit Datum. Nur Beobachtung."""
    pfad = _pfad("logbuch.json")
    lb = json_lesen(pfad, {})
    for tk, x in erg["titel"].items():
        e = lb.get(tk, [])
        jetzt = x["stufe"]
        offen = e[-1] if e and not e[-1].get("bis") else None
        if offen and offen["stufe"] == jetzt:
            continue
        if offen:
            offen["bis"] = erg["stand"]
            offen["kurs_bis"] = x["kurs"]
        if jetzt:
            e.append({"stufe": jetzt, "seit": erg["stand"], "kurs_seit": x["kurs"]})
        if e:
            lb[tk] = e[-12:]
    json_schreiben(pfad, lb, ensure_ascii=False)


def laden():
    """Gespeicherter Stand (ohne Rechnen) und Logbuch, oder None."""
    pfad = _pfad("stand.json")
    erg = json_lesen(pfad)
    if erg is None:
        return None
    erg["logbuch"] = json_lesen(_pfad("logbuch.json"), {})
    return erg


