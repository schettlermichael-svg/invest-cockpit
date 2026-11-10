"""Rudel, Kursverwandte und Themen-Gruppen (Schritt 4) – aus einem Jahr Tageskursen aller Revier-Titel.

Grundlage: massive.kursmatrix (260 Handelstage, über Splits vergleichbar) und SPY als Markt.
Gleichlauf  = Korrelation der täglichen Renditen NACH Abzug der Marktbewegung (Rendite − Beta × SPY),
              sonst liefen alle Aktien zusammen, nur weil der Markt steigt. Mindestens 120 gemeinsame Tage.
              Tagesrenditen statt Wochen: ein Jahr hat nur 52 Wochen, damit tauchten Zufallspartner auf.
Kursverwandte  die 5 Titel mit dem engsten Gleichlauf: „eng“ ab 0,50, „mittel“ ab 0,35, darunter keine Nennung
               (an den Daten gewählt: bei 0,6 hätte die Hälfte aller Titel keinen einzigen engen Verwandten).
Themen-Gruppen Titel, die untereinander eng laufen, auch über Branchengrenzen: schrittweises Zusammenfassen
               (mittlerer Gleichlauf zweier Gruppen mindestens 0,40), Gruppen ab 5 Titeln.
Rudel          die Yahoo-Branche des Titels (ab 5 Revier-Titeln, sonst der Sektor): wie viele im Aufwärtstrend
               (über steigendem GD200), wie viele nahe am Hoch (höchstens 15 % unter dem 52-Wochen-Hoch),
               Mansfield-RS der Gruppe, eigener Platz nach 3-Monats-Kursentwicklung.
               „Einsamer Wolf“: Titel stark, aber weniger als ein Drittel des Rudels im Trend.
Mansfield-RS   (RS-Linie ÷ ihr Schnitt über 52 Wochen − 1) × 100 (Weinstein); Richtung = Veränderung in 4 Wochen.
               Ampel: grün über 0 und steigend, rot unter 0 und fallend, sonst gelb.
Themen-Gruppen stehen zusätzlich als gleichgewichteter Kursindex im Rotationsbild (Feld wie die Sektoren).
Branchen-Index über knapp zwei Jahre (495 Tage, Grenze des kostenlosen Massive-Plans) für Phase und Stimmungskurve.
Alles wird einmal je neuem Handelstag gerechnet und in daten/rudel/ gespeichert (rund 10 Sekunden).
"""
import os

import numpy as np
import pandas as pd

import massive
import sektoren
from dateien import json_lesen, json_schreiben  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "rudel")
REVIER = os.path.join(HIER, "..", "einstellungen", "revier.csv")
MARKT = "SPY"
TAGE, MIN_TAGE = 260, 120
LANG = 495                       # Branchen-Index für Phase und Stimmungskurve (Phase braucht mehr als 300 Tage)
ENG, MITTEL = 0.50, 0.35
THEMA_SCHWELLE, THEMA_MIN, RUDEL_MIN = 0.40, 5, 5
NAHE_HOCH = 0.85
WOLF_ANTEIL = 1 / 3


def revier():
    return pd.read_csv(REVIER, keep_default_na=False).set_index("ticker")


def _pfad(name):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, name)


def mansfield(kurs, markt):
    """Mansfield-RS heute, Veränderung in 4 Wochen und Ampel; None bei weniger als 200 Tagen."""
    rs = (kurs / markt.reindex(kurs.index).ffill()).dropna()
    m = (rs / rs.rolling(252, min_periods=200).mean() - 1) * 100
    m = m.dropna()
    if len(m) < 21:
        return None
    wert, richtung = float(m.iloc[-1]), float(m.iloc[-1] - m.iloc[-21])
    ampel = "grün" if wert > 0 and richtung > 0 else "rot" if wert < 0 and richtung < 0 else "gelb"
    return {"wert": round(wert, 1), "richtung": round(richtung, 1), "ampel": ampel}


def _zusammenfassen(S, schwelle):
    """Schrittweises Zusammenfassen (mittlerer Gleichlauf), bis kein Paar mehr die Schwelle erreicht."""
    S = S.copy()
    n = len(S)
    np.fill_diagonal(S, -np.inf)
    groesse = np.ones(n)
    mitglieder = [[i] for i in range(n)]
    while True:
        i, j = np.unravel_index(np.argmax(S), S.shape)
        if S[i, j] < schwelle:
            break
        neu = (S[i] * groesse[i] + S[j] * groesse[j]) / (groesse[i] + groesse[j])
        S[i], S[:, i] = neu, neu
        S[i, i] = -np.inf
        S[j], S[:, j] = -np.inf, -np.inf
        groesse[i] += groesse[j]
        mitglieder[i] += mitglieder[j]
        mitglieder[j] = []
    return [g for g in mitglieder if len(g) >= THEMA_MIN]


def _beobachtet(rv):
    """US-Titel der Watchlists außerhalb des Reviers: laufen im Rudel mit (Kursverwandte, Themen-Gruppen, eigener
    Stand), zählen aber nicht in die Rudel-Breite (Konzept Schritt 6)."""
    try:
        import tpo_daten
        import watchlists
        return [t for t in watchlists.alle() if t not in rv.index and not tpo_daten.auslaendisch(t)]
    except Exception:  # noqa: BLE001
        return []


def _rechnen():
    rv = revier()
    C = massive.kursmatrix(list(rv.index) + _beobachtet(rv) + [MARKT], TAGE)
    stand = C.index[-1]
    r = np.log(C).diff().iloc[1:]
    m = r.pop(MARKT)
    r = r.loc[:, r.notna().sum() >= MIN_TAGE]
    beta = r.apply(lambda s: s.cov(m) / m.var())
    rest = r - np.outer(m.to_numpy(), beta.to_numpy())
    K = rest.corr(min_periods=MIN_TAGE)
    tk = list(K.columns)
    A = K.to_numpy(dtype=np.float32)
    np.save(_pfad("gleichlauf.npy"), A)
    # Themen-Gruppen
    gruppen = []
    for g in _zusammenfassen(np.nan_to_num(A, nan=0.0).astype(float), THEMA_SCHWELLE):
        namen = [tk[i] for i in g]
        innen = A[np.ix_(g, g)]
        mittel = float(np.nanmean(innen[~np.eye(len(g), dtype=bool)]))
        br = rv.reindex(namen)["branche"].dropna().value_counts()
        gruppen.append({"mitglieder": namen, "gleichlauf": round(mittel, 2),
                        "branchen": [[b, int(c)] for b, c in br.head(3).items()]})
    gruppen.sort(key=lambda x: -len(x["mitglieder"]))
    for nr, g in enumerate(gruppen, 1):
        g["nr"] = nr
        g["name"] = " · ".join(b for b, _ in g["branchen"][:2])
        kurs = 100 * (1 + C[g["mitglieder"]].pct_change(fill_method=None).iloc[1:].mean(axis=1)).cumprod()
        rot = sektoren.reihen(kurs, C[MARKT])                 # Feld im Rotationsbild wie die Sektoren
        if len(rot) >= sektoren.SCHWEIF:
            g["staerke"], g["schwung"] = round(float(rot["staerke"].iloc[-1]), 1), round(float(rot["schwung"].iloc[-1]), 1)
            g["feld"] = sektoren.feld(g["staerke"], g["schwung"])
            g["schweif"] = [[round(float(a), 2), round(float(b), 2)]
                            for a, b in rot[["staerke", "schwung"]].iloc[-sektoren.SCHWEIF:].to_numpy()]
    # Lage je Titel für die Rudel-Breite
    gd200 = C.rolling(200, min_periods=200).mean()
    trend = (C > gd200) & (gd200 > gd200.shift(20))
    hoch = C.rolling(252, min_periods=200).max()
    lage = pd.DataFrame({"trend": trend.iloc[-1], "nahe_hoch": C.iloc[-1] >= NAHE_HOCH * hoch.iloc[-1],
                         "historie": C.notna().sum()}).drop(index=MARKT)
    lage.to_csv(_pfad("lage.csv"))
    # Branchen-Index (gleichgewichtet) über knapp zwei Jahre, mit Volumen – für Phase und Stimmungskurve
    CL = massive.kursmatrix(list(rv.index), LANG)
    VL = massive.kursmatrix(list(rv.index), LANG, "Volume")
    kurs, vol = {}, {}
    for branche, gruppe in rv.groupby("branche").groups.items():
        if branche and len(gruppe) >= RUDEL_MIN:
            g = [t for t in gruppe if t in CL.columns]
            kurs[branche] = 100 * (1 + CL[g].pct_change(fill_method=None).iloc[1:].mean(axis=1)).cumprod()
            vol[branche] = VL[g].iloc[1:].sum(axis=1, min_count=1)
    pd.DataFrame(kurs).to_csv(_pfad("branchen_kurs.csv"))
    pd.DataFrame(vol).to_csv(_pfad("branchen_volumen.csv"))
    json_schreiben(_pfad("themen.json"), {"stand": f"{stand:%Y-%m-%d}", "ticker": tk, "themen": gruppen},
                   ensure_ascii=False)
    return stand


_cache = {}


def _laden():
    """Gespeicherte Ergebnisse; neu gerechnet, sobald Massive einen neueren Handelstag hat."""
    letzter = max(d[:10] for d in os.listdir(massive.SPEICHER) if d[:4].isdigit() and d.endswith(".csv"))
    pfad = _pfad("themen.json")
    if (json_lesen(pfad) or {}).get("stand", "") < letzter:
        _rechnen()
        _cache.clear()
    if not _cache:
        meta = json_lesen(pfad)
        _cache.update(meta=meta, A=np.load(_pfad("gleichlauf.npy")),
                      idx={t: i for i, t in enumerate(meta["ticker"])},
                      lage=pd.read_csv(_pfad("lage.csv"), index_col=0), rv=revier())
    return _cache


def stand():
    return pd.Timestamp(_laden()["meta"]["stand"])


def kursverwandte(tk, n=5):
    """Die n engsten Kursverwandten: Liste von Dicts (ticker, name, branche, wert, grad). None = zu kurze Historie."""
    c = _laden()
    if tk not in c["idx"]:
        return None
    zeile = c["A"][c["idx"][tk]].astype(float)
    zeile[c["idx"][tk]] = np.nan
    ordnung = np.argsort(np.nan_to_num(zeile, nan=-2))[::-1][:n]
    aus = []
    for i in ordnung:
        w = zeile[i]
        if np.isnan(w) or w < MITTEL:
            break
        t = c["meta"]["ticker"][i]
        z = c["rv"].loc[t] if t in c["rv"].index else {"name": t, "branche": ""}
        aus.append({"ticker": t, "name": z["name"], "branche": z["branche"],
                    "wert": round(float(w), 2), "grad": "eng" if w >= ENG else "mittel"})
    return aus


def themen():
    return _laden()["meta"]["themen"]


def breite(mitglieder):
    """Wie viele Mitglieder im Aufwärtstrend (über steigendem GD200) und nahe am 52-Wochen-Hoch stehen."""
    l = _laden()["lage"].reindex(mitglieder).dropna()
    l = l[l["historie"] >= 200]
    return {"anzahl": len(l), "im_trend": int(l["trend"].astype(bool).sum()),
            "nahe_hoch": int(l["nahe_hoch"].astype(bool).sum())}


def thema_von(tk):
    return next((g for g in themen() if tk in g["mitglieder"]), None)


def rudel(tk):
    """Rudel des Titels: Branche (ab 5 Titeln) sonst Sektor, mit Breite, eigenem Stand und Einsamer Wolf."""
    c = _laden()
    rv, lage = c["rv"], c["lage"]
    if tk in rv.index:
        branche, etf, sektor = rv.loc[tk, "branche"], rv.loc[tk, "etf"], rv.loc[tk, "sektor"]
    else:                                        # Watchlist-Titel außerhalb des Reviers: Rudel nach seiner Branche
        import daten
        sb = daten.steckbrief_gespeichert(tk) or {}
        branche, sektor = sb.get("branche") or "", sb.get("sektor") or ""
        etf = sektoren.sektor_von(sektor)
        if not branche and not etf:
            return None
    mitglieder = rv.index[rv["branche"] == branche] if branche else []
    art, name = "Branche", branche
    if len(mitglieder) < RUDEL_MIN:
        mitglieder, art, name = rv.index[rv["etf"] == etf], "Sektor", sektor
    l = lage.reindex(mitglieder).dropna()
    l = l[l["historie"] >= 200]
    im_trend, nahe = int(l["trend"].astype(bool).sum()), int(l["nahe_hoch"].astype(bool).sum())
    selbst = lage.loc[tk] if tk in lage.index else None
    stark = bool(selbst is not None and selbst["trend"] and selbst["nahe_hoch"])
    anteil = im_trend / len(l) if len(l) else 0
    # eigener Platz im Rudel: Kursentwicklung der letzten 3 Monate (63 Handelstage), 1 = stärkster
    C = kurse()
    g = [m for m in list(l.index) + ([tk] if tk not in l.index else []) if m in C.columns]
    perf = (C[g].iloc[-1] / C[g].iloc[-64] - 1).dropna().sort_values(ascending=False)
    platz = int(list(perf.index).index(tk)) + 1 if tk in perf.index else None
    return {"art": art, "name": name, "anzahl": len(l), "im_trend": im_trend, "nahe_hoch": nahe,
            "selbst_trend": bool(selbst is not None and selbst["trend"]),
            "selbst_nahe_hoch": bool(selbst is not None and selbst["nahe_hoch"]),
            "platz": platz, "platz_von": len(perf),
            "ampel": "grün" if anteil >= 0.6 else "gelb" if anteil >= WOLF_ANTEIL else "rot",
            "einsamer_wolf": stark and anteil < WOLF_ANTEIL, "mitglieder": list(l.index)}


def kurse():
    """Kursmatrix aller Revier-Titel und SPY (einmal je Programmlauf gelesen)."""
    c = _laden()
    if "C" not in c:
        c["C"] = massive.kursmatrix(list(c["rv"].index) + _beobachtet(c["rv"]) + [MARKT], TAGE)
    return c["C"]


def gruppenkurs(mitglieder):
    """Gleichgewichteter Kursindex einer Gruppe (Start 100) aus den Tagesrenditen der Mitglieder."""
    C = kurse()
    r = C[[m for m in mitglieder if m in C.columns]].pct_change(fill_method=None).iloc[1:].mean(axis=1, skipna=True)
    return 100 * (1 + r).cumprod()


def branche_kurse(branche):
    """Tageskerzen eines Branchen-Index (Open = High = Low = Close, Volumen = Summe der Mitglieder) für Phase und
    Stimmungskurve; None, wenn die Branche weniger als 5 Revier-Titel hat."""
    _laden()
    k = pd.read_csv(_pfad("branchen_kurs.csv"), index_col=0, parse_dates=True)
    if branche not in k.columns:
        return None
    v = pd.read_csv(_pfad("branchen_volumen.csv"), index_col=0, parse_dates=True)
    c = k[branche].dropna()
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": v[branche].reindex(c.index)})


def gruppen_mansfield(mitglieder):
    return mansfield(gruppenkurs(mitglieder), kurse()[MARKT])
