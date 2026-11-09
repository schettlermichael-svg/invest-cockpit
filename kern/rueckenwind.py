"""Rückenwind (Konzept: KONZEPT_RUECKENWIND.md, 09.11.2026) – eigene Seite, getrennt von den Setups.

Je Titel des Reviers drei Rückenwinde als Ampeln, dazu Earnings:
  Kurs   RS-Dynamik: Stärke (RS-Rang 1–99 wie IBD, rs_rang.wert), Tempo (Veränderung des Rangs in 4 Wochen),
         Beschleunigung (Tempo gegen das Tempo der 4 Wochen davor); Zeichen: RS-Linie am 52-Wochen-Hoch, der Kurs noch
         nicht (O'Neil/Minervini).
  Geld   Sektor, Branche und Thema der Gruppe (drei Stimmen: grün = zwei vorne, keine im Abfluss): Feld (Stärke × Tempo gegen den S&P 500 wie sektoren.reihen, gleich-
         gewichtete Indizes der Revier-Titel), Weg der letzten 4 Wochen, Volumen-Zufluss (Volumen an steigenden gegen
         fallende Tage, 50 Tage).
  Zahlen Fundament-Ampeln (fundament.ampeln, Minervini/O'Neil) aus dem Zwischenspeicher; Termin der nächsten Zahlen,
         Reaktion auf die letzten.
Stufen (Ampel, keine Punktzahl): Entsteht · Läuft · Ermüdet · Abfluss. Logbuch: Eintritt in eine Stufe mit Datum und
Kurs (Beobachtung, kein Urteil). Alles aus den Massive-Tagesdateien des Nachtlaufs, gespeichert in daten/rueckenwind/.
"""
import json
import os

import pandas as pd

import massive
import rs_rang
import sektoren

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
ERMUEDET = (80, -10)           # Ermüdet: Rang ab 80, Tempo −10 oder schlechter
ABFLUSS = (70, -20)            # Abfluss: vor 4 Wochen ab 70, seitdem 20 Rangpunkte oder mehr verloren
VORNE = ("Führend", "Erstarkend")
STUFEN = ("Entsteht", "Läuft", "Ermüdet", "Abfluss")


def _pfad(name):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, name)


def _rang(C):
    w = rs_rang.wert(C).dropna()
    return (w.rank(pct=True) * 98 + 1).round()


def _stufe(r, t, b, r4):
    if r4 is not None and r4 >= ABFLUSS[0] and t <= ABFLUSS[1]:
        return "Abfluss"
    if r >= ERMUEDET[0] and t <= ERMUEDET[1]:
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
    return {"art": art, "name": name, "anzahl": len(g), "feld": feld, "feld_vor4": vorher, "seit_wochen": seit,
            "staerke": round(float(s.iloc[-1]), 1), "schwung": round(float(w.iloc[-1]), 1),
            "weg": [[round(float(a), 1), round(float(b), 1)] for a, b in zip(s.iloc[-5:], w.iloc[-5:])],
            "zufluss": round(ud, 2) if ud else None}


def _geld_ampel(sek, bra, th=None):
    """Drei Stimmen: Sektor, Branche, Thema (Micky, 09.11.2026). Grün = mindestens zwei vorne (führend oder
    erstarkend) und keine im Abfluss (schwächelnd); gelb = eine vorne; rot = keine. Ohne Thema zählen Sektor und
    Branche – dann müssen beide vorne sein."""
    stimmen = [x for x in (sek, bra, th) if x]
    vorne = sum(1 for x in stimmen if x["feld"] in VORNE)
    abfluss = any(x["feld"] == "Ermüdend" for x in stimmen)
    return "grün" if vorne >= 2 and not abfluss else "gelb" if vorne else "rot"


def _zahlen(tk):
    """Fundament-Ampeln, Termin und Gewinne aus dem Zwischenspeicher (ohne Abruf)."""
    import fundament
    import quellen
    pfad = os.path.join(quellen.SPEICHER, f"{tk.upper()}.json")
    if not os.path.exists(pfad):
        return None
    try:
        fd = quellen._aus_json(json.load(open(pfad, encoding="utf-8")))
        f = fundament.ampeln(fd)
    except Exception:  # noqa: BLE001
        return None
    pk = f["punkte"]
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
        termin = f"{d:%Y-%m-%d}" if pd.notna(d) else None
    gew = fd.get("gewinne")
    letzte = None
    if gew is not None and len(gew):
        letzte = {"tag": str(gew.index[-1])[:10], "nach_schluss": int(gew["nach_schluss"].iloc[-1])}
    return {"ampel": ampel, "punkte": {k: list(v) for k, v in pk.items()}, "zeichen": f["zeichen"],
            "termin": termin, "letzte": letzte}


def _reaktion(tk, letzte, C, V):
    """Kurs und Volumen am Tag nach den letzten Zahlen (bzw. am Meldetag, wenn vor Börsenbeginn gemeldet)."""
    if not letzte or tk not in C.columns:
        return None
    c = C[tk].dropna()
    tag = pd.Timestamp(letzte["tag"])
    nach = c.index[c.index > tag] if letzte["nach_schluss"] else c.index[c.index >= tag]
    if not len(nach) or c.index.get_loc(nach[0]) == 0:
        return None
    i = c.index.get_loc(nach[0])
    v = V[tk].reindex(c.index)
    s50 = v.iloc[max(0, i - 50):i].mean()
    return {"tag": f"{nach[0]:%Y-%m-%d}", "kurs": round(float((c.iloc[i] / c.iloc[i - 1] - 1) * 100), 1),
            "volumen": round(float(v.iloc[i] / s50), 2) if s50 == s50 and s50 else None}


def _themenname(g, rang):
    top = sorted(g["mitglieder"], key=lambda t: -rang.get(t, 0))[:4]
    return ", ".join(top) + " · " + ", ".join(b for b, _ in g.get("branchen", [])[:3])


def rechnen(netz=False):
    """Alles rechnen und speichern; Ergebnis als dict. netz=True (Nachtlauf): Fundamentdaten der Titel in einer Stufe
    holen, wenn älter als 12 Stunden (quellen.laden)."""
    import rudel
    rv = rudel.revier()
    C = massive.kursmatrix(list(rv.index) + [MARKT], TAGE)
    V = massive.kursmatrix(list(rv.index) + [MARKT], TAGE, "Volume")
    titel_ = [t for t in rv.index if t in C.columns and C[t].notna().sum() >= 252 + 2 * WOCHEN4]
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
    for br, mit in rv.groupby("branche").groups.items():
        if br:
            g = _gruppe("Branche", br, list(mit), C, V)
            if g:
                gruppen.append(g)
                bra_von.update({t: g for t in mit})
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
        rs_hoch = bool(len(rs) >= 252 and rs.iloc[-1] >= 0.99 * rs.iloc[-252:].max())
        kurs_hoch = bool(len(c) >= 252 and c.iloc[-1] >= 0.97 * c.iloc[-252:].max())
        stufe = _stufe(r, tempo, besch, a4)
        if stufe is None and rs_hoch and not kurs_hoch and tempo > 0:
            stufe = "Entsteht"                      # RS-Linie am Hoch vor dem Kurs: das stärkste frühe Zeichen
        sek, bra, th = sek_von.get(tk), bra_von.get(tk), thema_von.get(tk)
        x = {"rang": int(r), "rang_vor4": int(a4), "tempo": int(tempo), "beschleunigung": int(besch),
             "rs_hoch_vor_kurs": rs_hoch and not kurs_hoch, "stufe": stufe,
             "kurs_ampel": {"Entsteht": "grün", "Läuft": "grün", "Ermüdet": "gelb", "Abfluss": "rot"}.get(stufe, "grau"),
             "sektor": sek["name"] if sek else rv.loc[tk, "sektor"], "sektor_feld": sek["feld"] if sek else None,
             "branche": bra["name"] if bra else rv.loc[tk, "branche"], "branche_feld": bra["feld"] if bra else None,
             "thema": th["name"] if th else None, "thema_feld": th["feld"] if th else None,
             "geld_ampel": _geld_ampel(sek, bra, th), "kurs": round(float(c.iloc[-1]), 2)}
        if stufe:
            if netz:
                try:
                    import quellen
                    quellen.laden(tk)
                except Exception:  # noqa: BLE001 – dann ohne Zahlen
                    pass
            z = _zahlen(tk)
            if z:
                z["reaktion"] = _reaktion(tk, z.pop("letzte"), C, V)
            x["zahlen"] = z
        titel[tk] = x
    stand = f"{C.index[-1]:%Y-%m-%d}"
    erg = {"stand": stand, "gruppen": gruppen, "titel": titel,
           "schwellen": {"stark": STARK, "mittel": MITTEL, "tempo_hoch": TEMPO_HOCH, "ermuedet": ERMUEDET,
                         "abfluss": ABFLUSS}}
    _logbuch(erg)
    json.dump(erg, open(_pfad("stand.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return erg


def _logbuch(erg):
    """Eintritt in eine Stufe mit Datum und Kurs; Austritt mit Datum. Nur Beobachtung."""
    pfad = _pfad("logbuch.json")
    lb = json.load(open(pfad, encoding="utf-8")) if os.path.exists(pfad) else {}
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
    json.dump(lb, open(pfad, "w", encoding="utf-8"), ensure_ascii=False)


def laden():
    """Gespeicherter Stand (ohne Rechnen) und Logbuch, oder None."""
    pfad = _pfad("stand.json")
    if not os.path.exists(pfad):
        return None
    erg = json.load(open(pfad, encoding="utf-8"))
    lb = _pfad("logbuch.json")
    erg["logbuch"] = json.load(open(lb, encoding="utf-8")) if os.path.exists(lb) else {}
    return erg
