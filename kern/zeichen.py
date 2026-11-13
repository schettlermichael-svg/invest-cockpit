"""Zeichen der Stärke und Schwäche und der Kreislauf je Titel (Lehre von Stärke und Schwäche, Micky 13.11.2026).

Grundsatz (Auction Market Theory): Ein Titel ist in Balance (Seitwärtszone) oder im Ungleichgewicht (Trend). Er verlässt
die Balance, weil neue Information den Wert verändert oder eine Seite erschöpft ist. Stärke = die Nachfrage überwiegt,
das Angebot weicht; Schwäche = das Spiegelbild. Wir spüren die Ineffizienzen und Disbalancen auf, die den Kurs aus der
Zone brechen lassen, und erspüren starke und schwache Zeichen – auch versteckte. Kreislauf (Weinstein/Wyckoff):
1 Basis → 2 Aufwärts → 3 Verteilung → 4 Abwärts; die Phase je Woche rechnet phase.py, die Wechselzeichen kommen von hier.

Die App misst, der Stab deutet. Jedes Zeichen ist eine feste Regel und hat eine Art – Struktur (Schwungpunkte, Spring,
Einquetschung, Bruch), Volumen (Kauf- und Abgabetage, Pocket Pivot, Enge, Trockenheit), RS (gegen den Markt, auch die Divergenz)
oder Ereignis (Zahlen, Wertzone). Ein Wechsel der Phase zeichnet sich erst ab, wenn ein Zeichen der Struktur UND eines
aus Volumen oder RS auf derselben Seite stehen und die Seite klar überwiegt (Gewicht mindestens 4 und
doppelt so schwer wie die Gegenseite; Prüf-Agent 13.11.2026: vorher genügte das bloße Zählen).

  Dow-Struktur      Schwungpunkte (Tag n = 5, Woche n = 2); höhere Hochs und Tiefs = aufwärts, tiefere = abwärts.
                    Schwäche: Schluss mindestens 0,5 ATR unter dem letzten höheren Tief. Stärke: Schluss mindestens
                    0,5 ATR über dem letzten tieferen Hoch; erstes höheres Tief nach tieferen Hochs und Tiefs, solange der Kurs darüber
                    steht (gespiegelt: erstes tieferes Hoch, Kurs darunter).
  Spring/Upthrust   in den letzten 10 Tagen: Tief höchstens 1 ATR unter dem Tief der 20 Tage davor (Spanne höchstens
                    15 % breit), Schluss innerhalb von 3 Tagen wieder darüber mit Volumen über dem Schnitt = Spring
                    (Wyckoff; O'Neil „undercut and rally“). Upthrust: Hoch über der Oberkante mit Volumen über dem
                    Schnitt, Schluss im unteren Drittel des Tages und wieder in der Spanne.
  Einquetschung     60 Tage: mindestens 2 Schwunghochs innerhalb ±1,5 % der Oberkante, mindestens 3 steigende Tiefs
                    (ein Spring bricht die Reihe nicht), Spanne und Volumen werden kleiner. Gespiegelt.
  Volumen           20 Tage: Kauftag = Schluss über dem Vortag, Volumen über dem 50-Tage-Schnitt, Schluss im oberen
                    Drittel; Abgabetag = Schluss unter dem Vortag, Volumen über dem Schnitt, Schluss im unteren Drittel; Saldo ≥ 3 und doppelt so
                    viele = Akkumulation, gespiegelt Distribution. Verdeckte Abgabe (Churning): mindestens 3 Tage im Plus mit Volumen, die im
                    unteren Drittel schließen. Pocket Pivot (Morales/Kacher) in den letzten 5 Tagen: Tag im Plus über
                    GD10 und GD50, höchstens 4 % über dem GD10, Volumen über dem größten Abgabetag der 10 Tage davor,
                    die 5 Tage davor zusammen höchstens +3 %. Enge: 3 Wochenschlüsse innerhalb 1,5 %. Trockenheit:
                    der leiseste Tag seit 50 Tagen in den letzten 10, in der unteren Hälfte der Spanne der 60 Tage.
  RS gegen Markt    siehe relativ(), divergenz(), divergenz_short(), tage_gegen_markt(), rs_linie().
  Reaktion          letzte Zahlenmeldung (höchstens 60 Handelstage; Reaktionstag und Schwelle 3 % wie
                    zahlen_reaktion): Überraschung gegen Kursreaktion, Lücke gegen Schluss im Tag, Kurs heute unter dem
                    Schluss vor den Zahlen nach positivem Tag 1 = Zahlen verworfen (wie die Kachel, O'Neil).
  Wertzone          POC der letzten 5 Tage gegen die 5 davor, mindestens ±3 %, nur in der Seitwärtszone.
"""
import os

import numpy as np
import pandas as pd

GLEICH_PCT = 1.5          # Einquetschung: Hochs innerhalb ±1,5 %
MIN_RUECKGANG = 3.0       # Index mindestens 3 % unter seinem Hoch (bzw. über seinem Tief)
HAELT_PUNKTE = 15.0      # „hält“: am Indextief mindestens 15 Punkte vor dem Index (Messung 13.11.: mit 10 Punkten
                          # schlug jeder zweite Titel den S&P 500 – der Rückgang war eng von wenigen Riesen getragen)
FUEHRT_PUNKTE = 10.0      # „führt“, Divergenz: mindestens 10 Prozentpunkte vor (bzw. hinter) dem Index
FUEHRT_NAH_HOCH = 15.0    # „führt“ und „nah“ nur höchstens 15 % unter dem 52-Wochen-Hoch
NACHWIRKUNG_TAGE = 45     # Stärke in der Korrektur bleibt nach dem Tief des Index 45 Handelstage stehen
KEIN = "kein"             # Startdatum schon gesucht, kein Fenster (statt None = noch nicht gesucht)
SEITWAERTS_PCT = 4.0      # Seitwärtszone: Schluss in 10 Tagen höchstens ±4 %
WERT_WANDERT_PCT = 3.0    # der akzeptierte Wert (POC) wandert in 5 Tagen um mindestens 3 %
RS_HOCH = 0.99            # RS-Linie „am Hoch“: höchstens 1 % darunter – ein Maßstab für die ganze App
JUNG_TAGE = 70            # Zeichen ab 70 Handelstagen; Phase erst ab 300 (vorher „jung“)
PHASE_NAME = {0: "jung", 1: "Basis", 2: "Aufwärts", 3: "Verteilung", 4: "Abwärts"}
RUECKSCHLAG = 21          # Phase 2 · Rückschlag (Wochenschluss unter GD10W und ≥ 15 % unter dem 52-Wochen-Hoch)


def _z(x, fmt):
    """Zahl deutsch: Komma statt Punkt, echtes Minus."""
    return format(x, fmt).replace(".", ",").replace("-", "−")


def _tage(n, wort):
    return f"{n} {wort}" + ("" if n == 1 else "e")


def _zeichen(seite, art, text, gewicht=1, tag=None):
    """Ein Zeichen; tag (Datum als Text JJJJ-MM-TT) markiert es im Chart."""
    z = {"seite": seite, "art": art, "text": text, "gewicht": gewicht}
    if tag is not None:
        z["tag"] = f"{pd.Timestamp(tag):%Y-%m-%d}"
    return z


def _atr(df, n=14):
    h, l, c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def lage_ok(df, i):
    """Schluss in der oberen Hälfte der Tagesspanne."""
    h, l, c = df["High"].iloc[i], df["Low"].iloc[i], df["Close"].iloc[i]
    return h > l and (c - l) / (h - l) >= 0.5


# ── Dow-Struktur ──────────────────────────────────────────────────────────────────────────────────────────────────
def schwungpunkte(h, l, n):
    """Schwunghochs und -tiefs: [(Position, Preis)], bestätigt erst n Kerzen danach."""
    h, l = np.asarray(h, float), np.asarray(l, float)
    hochs, tiefs = [], []
    for i in range(n, len(h) - n):
        if h[i] == h[i - n:i + n + 1].max() and h[i] > h[i - n:i].max():
            hochs.append((i, h[i]))
        if l[i] == l[i - n:i + n + 1].min() and l[i] < l[i - n:i].min():
            tiefs.append((i, l[i]))
    return hochs, tiefs


def dow(df, n=5):
    """→ {struktur: aufwärts/abwärts/balance, signal, richtung: stärke/schwäche/None, letztes_tief, letztes_hoch,
    tief_tag, hoch_tag}."""
    if df is None or len(df) < 4 * n + 4:
        return None
    hochs, tiefs = schwungpunkte(df["High"], df["Low"], n)
    if len(hochs) < 2 or len(tiefs) < 2:
        return {"struktur": "balance", "signal": None, "richtung": None}
    (_, h1), (ih2, h2) = hochs[-2], hochs[-1]
    (_, t1), (it2, t2) = tiefs[-2], tiefs[-1]
    kurs = float(df["Close"].iloc[-1])
    a = float(_atr(df).iloc[-1]) if len(df) > 15 else 0.0
    a = a if a == a else 0.0
    if h2 > h1 and t2 > t1:
        struktur = "aufwärts"
    elif h2 < h1 and t2 < t1:
        struktur = "abwärts"
    else:
        struktur = "balance"
    signal = richtung = None
    if struktur == "aufwärts" and kurs < t2 - 0.5 * a:
        signal, richtung = f"Schluss unter dem letzten höheren Tief {_z(t2, '.2f')}", "schwäche"
    elif struktur == "abwärts" and kurs > h2 + 0.5 * a:
        signal, richtung = f"Schluss über dem letzten tieferen Hoch {_z(h2, '.2f')}", "stärke"
    elif (t2 > t1 and kurs > t2 and len(tiefs) >= 3 and len(hochs) >= 3 and tiefs[-3][1] > t1 and hochs[-3][1] > h1):
        signal, richtung = f"erstes höheres Tief {_z(t2, '.2f')} nach tieferen Hochs und Tiefs", "stärke"
    elif (h2 < h1 and kurs < h2 and len(hochs) >= 3 and len(tiefs) >= 3 and hochs[-3][1] < h1 and tiefs[-3][1] < t1):
        signal, richtung = f"erstes tieferes Hoch {_z(h2, '.2f')} nach höheren Hochs und Tiefs", "schwäche"
    return {"struktur": struktur, "signal": signal, "richtung": richtung, "letztes_tief": round(t2, 2),
            "letztes_hoch": round(h2, 2), "tief_tag": df.index[it2], "hoch_tag": df.index[ih2]}


def wochenkerzen(df):
    return df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last",
                                     "Volume": "sum"}).dropna()


def trendqualitaet(df):
    """Steigung des GD50 über 20 Tage und Abstand des Kurses zum GD50, in %."""
    c = df["Close"]
    if len(c) < 70:
        return None
    g = c.rolling(50).mean()
    return {"steigung_gd50": round(float(g.iloc[-1] / g.iloc[-21] - 1) * 100, 1),
            "abstand_gd50": round(float(c.iloc[-1] / g.iloc[-1] - 1) * 100, 1)}


# ── Spring und Upthrust ───────────────────────────────────────────────────────────────────────────────────────────
def spring(df, tage=10, vor=20):
    """Spring (Stärke) bzw. Upthrust (Schwäche) in den letzten `tage` Tagen → Zeichen oder None."""
    if df is None or len(df) < vor + tage + 50:
        return None
    lo, hi, c, v = (df[x].to_numpy(float) for x in ("Low", "High", "Close", "Volume"))
    v50 = df["Volume"].rolling(50).mean().to_numpy(float)
    a = _atr(df).to_numpy(float)
    n = len(df)
    for i in range(n - 1, n - tage - 1, -1):
        unten, oben = lo[i - vor:i].min(), hi[i - vor:i].max()
        if not unten > 0 or oben / unten - 1 > 0.15:
            continue
        if lo[i] < unten and unten - lo[i] <= a[i]:
            for j in range(i, min(i + 4, n)):
                if c[j] > unten and v[j] > v50[j]:
                    return _zeichen("stärke", "struktur", f"Spring am {df.index[i]:%d.%m.}: Tief unter "
                                    f"{_z(unten, '.2f')} $, " + ("am selben Tag" if j == i else f"am {df.index[j]:%d.%m.}") +
                                    " mit Volumen zurückgekauft – "
                                    "die Verkäufer sind erschöpft", 2, df.index[i])
        if (hi[i] > oben and hi[i] - oben <= a[i] and c[i] < oben and hi[i] > lo[i] and v[i] > v50[i]
                and (c[i] - lo[i]) / (hi[i] - lo[i]) <= 1 / 3):
            return _zeichen("schwäche", "struktur", f"Upthrust am {df.index[i]:%d.%m.}: Hoch über {_z(oben, '.2f')} $, "
                            "Schluss im unteren Drittel zurück in der Spanne – die Käufer sind erschöpft", 2, df.index[i])
    return None


# ── Einquetschung ─────────────────────────────────────────────────────────────────────────────────────────────────
def _ohne_spring(t_, d):
    """Tiefs einer Reihe ohne die, die binnen 3 Tagen über das vorige Tief zurückgekauft wurden (Spring)."""
    aus = []
    c = d["Close"].to_numpy(float)
    for i, p in t_:
        vorher = aus[-1][1] if aus else None
        if vorher is not None and p <= vorher and any(c[j] > vorher for j in range(i, min(i + 4, len(c)))):
            continue
        aus.append((i, p))
    return aus


def einquetschung(df, fenster=60):
    """Aufsteigendes Dreieck (gespiegelt absteigend) → {art, oberkante|unterkante, beruehrungen, tiefs|hochs} oder None."""
    if df is None or len(df) < fenster + 50:
        return None
    d = df.iloc[-fenster:]
    spanne = lambda x: float(x["High"].max() / x["Low"].min() - 1)    # noqa: E731
    if not spanne(d.iloc[-10:]) < spanne(d.iloc[:10]):
        return None
    if not float(d["Volume"].iloc[-10:].mean()) < float(df["Volume"].iloc[-60:-10].mean()):
        return None
    hochs, tiefs = schwungpunkte(d["High"], d["Low"], 2)
    kurs = float(d["Close"].iloc[-1])
    lo, hi = d["Low"].to_numpy(float), d["High"].to_numpy(float)
    i0 = int(lo.argmin())
    t_ = _ohne_spring([(i0, lo[i0])] + [(i, p) for i, p in tiefs if i > i0], d)
    h_ = [(i, p) for i, p in hochs if i > i0]
    if len(t_) >= 3 and len(h_) >= 2 and all(b_[1] > a_[1] for a_, b_ in zip(t_, t_[1:])):
        top = max(p for _, p in h_)
        an = [p for _, p in h_ if abs(p / top - 1) * 100 <= GLEICH_PCT]
        if len(an) >= 2 and kurs <= top * 1.05:
            return {"art": "aufsteigend", "oberkante": round(top, 2), "beruehrungen": len(an), "tiefs": len(t_)}
    j0 = int(hi.argmax())
    h2 = [(j0, hi[j0])] + [(i, p) for i, p in hochs if i > j0]
    t2 = [(i, p) for i, p in tiefs if i > j0]
    if len(h2) >= 3 and len(t2) >= 2 and all(b_[1] < a_[1] for a_, b_ in zip(h2, h2[1:])):
        boden = min(p for _, p in t2)
        am = [p for _, p in t2 if abs(p / boden - 1) * 100 <= GLEICH_PCT]
        if len(am) >= 2 and kurs >= boden * 0.95:
            return {"art": "absteigend", "unterkante": round(boden, 2), "beruehrungen": len(am), "hochs": len(h2)}
    return None


# ── Volumen ───────────────────────────────────────────────────────────────────────────────────────────────────────
def akkumulation(df, tage=20):
    if df is None or len(df) < 70:
        return None
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    schnitt = v.rolling(50).mean()
    auf, ab = c > c.shift(1), c < c.shift(1)
    hoch_vol = v > schnitt
    lage = (c - l) / (h - l).replace(0, np.nan)
    letzte = slice(-tage, None)
    kauf = int((auf & hoch_vol & (lage >= 2 / 3)).iloc[letzte].sum())
    abgabe = int((ab & hoch_vol & (lage <= 1 / 3)).iloc[letzte].sum())
    churning = int((auf & hoch_vol & (lage <= 1 / 3)).iloc[letzte].sum())
    pocket = None
    g10, g50 = c.rolling(10).mean(), c.rolling(50).mean()
    for i in range(len(df) - 5, len(df)):
        if (auf.iloc[i] and c.iloc[i] > g10.iloc[i] and c.iloc[i] > g50.iloc[i] and lage.iloc[i] >= 0.5
                and c.iloc[i] <= g10.iloc[i] * 1.04 and c.iloc[i - 1] / c.iloc[i - 6] - 1 <= 0.03):
            vor = df.iloc[i - 10:i]
            ab_vol = vor["Volume"][vor["Close"] < df["Close"].shift(1).iloc[i - 10:i]]
            if len(ab_vol) and v.iloc[i] > ab_vol.max():
                pocket = f"{df.index[i]:%d.%m.}"
    saldo = kauf - abgabe
    return {"kauftage": kauf, "abgabetage": abgabe, "churning": churning, "pocket_pivot": pocket,
            "bild": "Akkumulation" if saldo >= 3 and kauf >= 2 * abgabe else
            "Distribution" if saldo <= -3 and abgabe >= 2 * kauf else "ausgeglichen"}


def tagesmarken(df, tage=260):
    """Für den Chart (13.11.2026): Pocket Pivots, Abgabetage (Distributionstage des Titels) und verdeckte Abgabe der
    letzten `tage` Handelstage, nach denselben Regeln wie akkumulation() → {pocket, abgabe, churning: [Datum]}."""
    aus = {"pocket": [], "abgabe": [], "churning": []}
    if df is None or len(df) < 70:
        return aus
    c, h, l, v = (df[x].to_numpy(float) for x in ("Close", "High", "Low", "Volume"))
    s50 = pd.Series(v).rolling(50).mean().to_numpy()
    g10 = pd.Series(c).rolling(10).mean().to_numpy()
    g50 = pd.Series(c).rolling(50).mean().to_numpy()
    for i in range(max(60, len(df) - tage), len(df)):
        sp = h[i] - l[i]
        lage = (c[i] - l[i]) / sp if sp > 0 else 0.5
        auf, ab, laut = c[i] > c[i - 1], c[i] < c[i - 1], v[i] > s50[i]
        if ab and laut and lage <= 1 / 3:
            aus["abgabe"].append(df.index[i])
        if auf and laut and lage <= 1 / 3:
            aus["churning"].append(df.index[i])
        if (auf and c[i] > g10[i] and c[i] > g50[i] and lage >= 0.5 and c[i] <= g10[i] * 1.04
                and c[i - 1] / c[i - 6] - 1 <= 0.03):
            vor = range(i - 10, i)
            ab_vol = [v[j] for j in vor if c[j] < c[j - 1]]
            if ab_vol and v[i] > max(ab_vol):
                aus["pocket"].append(df.index[i])
    return aus


def enge_trocken(df):
    """3 Wochen eng und Volumen-Trockenheit → Liste von Zeichen (Stärke)."""
    aus = []
    if df is None or len(df) < 70:
        return aus
    w = wochenkerzen(df)["Close"].iloc[-3:]
    if len(w) == 3 and w.max() / w.min() - 1 <= 0.015:
        aus.append(_zeichen("stärke", "volumen", f"3 Wochen eng: Wochenschlüsse innerhalb von "
                            f"{_z((w.max() / w.min() - 1) * 100, '.1f')} % – das Angebot ist aufgebraucht"))
    v, lo, hi, c = df["Volume"], df["Low"], df["High"], df["Close"]
    unten, oben = float(lo.iloc[-60:].min()), float(hi.iloc[-60:].max())
    for i in range(len(df) - 10, len(df)):
        if v.iloc[i] > 0 and v.iloc[i] <= v.iloc[i - 49:i + 1].min() and c.iloc[i] <= unten + (oben - unten) / 2:
            aus.append(_zeichen("stärke", "volumen", f"Volumen trocknet aus: {df.index[i]:%d.%m.} der leiseste Tag "
                                "seit 50 Tagen, in der unteren Hälfte der Spanne – niemand will mehr verkaufen"))
            break
    return aus


# ── Relativ zum Markt ─────────────────────────────────────────────────────────────────────────────────────────────
def korrekturfenster(idx):
    """Fenster der Marktschwäche → (start, ende) oder None; ende ist None, solange sie läuft. Läuft: O'Neil sieht
    Korrektur/Druck (start = Indexhoch der 60 Tage davor), oder der Index liegt ≥ 3 % unter dem Hoch der 60 Tage.
    Vorbei (Prüf-Agent 13.11.2026: die Stärke verschwand mit dem Follow-Through-Day – genau dann brechen die Führer
    aus): die letzte Korrektur von mindestens 3 %, deren Tief höchstens NACHWIRKUNG_TAGE Handelstage zurückliegt."""
    c = idx["Close"]
    try:
        import marktrichtung
        mr = marktrichtung.richtung(bis=idx.index[-1])
        if mr.get("ampel") != "grün" and mr.get("seit") is not None:
            vor = c.loc[:pd.Timestamp(mr["seit"])].iloc[-60:]
            return vor.idxmax(), None
    except Exception:  # noqa: BLE001
        pass
    c60 = c.iloc[-60:]
    if (1 - c60.iloc[-1] / c60.max()) * 100 >= MIN_RUECKGANG:
        return c60.idxmax(), None
    fenster = c.iloc[-(NACHWIRKUNG_TAGE + 60):]
    tief = fenster.iloc[-NACHWIRKUNG_TAGE:].idxmin()
    hoch = fenster.loc[:tief].iloc[-60:].idxmax()
    if hoch < tief < c.index[-1] and (1 - fenster.loc[tief] / fenster.loc[hoch]) * 100 >= MIN_RUECKGANG:
        return hoch, tief
    return None


def korrekturbeginn(idx):
    """Verträglich mit älteren Aufrufen: der Beginn des Fensters oder None."""
    f = korrekturfenster(idx)
    return f[0] if f else None


def divergenz(df, idx, s, ende=None):
    """Höheres Tief gegen den Index → Liste mit einem Zeichen. Der Titel fiel seit dem Indexhoch bis zu seinem Tief um
    mindestens max(5 %, 3 ATR, den Rückgang des Index); dieses Tief liegt mindestens 3 Handelstage vor dem Tief des
    Index, der Index fällt danach mindestens 0,5 % tiefer, der Titel bleibt dabei 5 % über seinem Tief und liegt seit
    seinem Tief mindestens 10 Punkte vor dem Index."""
    bis = ende if ende is not None else df.index[-1]
    lo, c = df["Low"].loc[s:bis], df["Close"]
    i_lo = idx["Low"].reindex(df.index).ffill().loc[s:bis]
    i_c = idx["Close"].reindex(df.index).ffill()
    if len(lo) < 8 or i_lo.isna().all():
        return []
    d1, t2 = lo.idxmin(), i_lo.idxmin()
    pos1, pos2 = df.index.get_loc(d1), df.index.get_loc(t2)
    if pos2 - pos1 < 3:
        return []
    um_t2 = float(df["Low"].iloc[max(pos2 - 1, 0):pos2 + 2].min())
    tief1 = float(lo.loc[d1])
    hoch = float(df["High"].loc[s:d1].max())
    i_hoch = float(idx["High"].reindex(df.index).ffill().loc[s:d1].max())
    i_fall = (1 - float(i_lo.min()) / i_hoch) * 100
    a_ = float(_atr(df).loc[d1])
    a_pct = a_ / tief1 * 100 if a_ == a_ else 0.0
    t_ = float(c.iloc[-1] / c.loc[d1] - 1) * 100
    i_ = float(i_c.iloc[-1] / i_c.loc[d1] - 1) * 100
    if not ((1 - tief1 / hoch) * 100 >= max(5.0, 3 * a_pct, i_fall)
            and float(i_lo.loc[t2]) <= float(i_lo.loc[d1]) * 0.995
            and um_t2 >= tief1 * 1.05 and t_ - i_ >= FUEHRT_PUNKTE):
        return []
    return [_zeichen("stärke", "rs", f"höheres Tief gegen den Index: eigenes Tief am {d1:%d.%m.} bei "
                     f"{_z(tief1, '.2f')} $, am tieferen Indextief {t2:%d.%m.} {_z((um_t2 / tief1 - 1) * 100, '+.1f')} % "
                     f"darüber; seitdem {_z(t_, '+.1f')} %, der S&P 500 {_z(i_, '+.1f')} %", 2, t2) | {"auch_struktur": True}]


def divergenz_short(df, idx):
    """Spiegelbild: tieferes Hoch gegen den Index (Verteilung eines Führers) → Liste mit einem Zeichen. In den letzten
    60 Tagen: der Titel stieg mindestens 10 % bis zu seinem Hoch; der Index macht mindestens 3 Handelstage später ein um
    mindestens 0,5 % höheres Hoch; der Titel bleibt dabei 5 % unter seinem Hoch und liegt seit seinem Hoch mindestens
    10 Punkte hinter dem Index."""
    if df is None or len(df) < 70:
        return []
    hi, c = df["High"].iloc[-60:], df["Close"]
    i_hi = idx["High"].reindex(df.index).ffill().iloc[-60:]
    i_c = idx["Close"].reindex(df.index).ffill()
    if i_hi.isna().all():
        return []
    d1, t2 = hi.idxmax(), i_hi.idxmax()
    pos1, pos2 = df.index.get_loc(d1), df.index.get_loc(t2)
    if pos2 - pos1 < 3:
        return []
    um_t2 = float(df["High"].iloc[max(pos2 - 1, 0):pos2 + 2].max())
    hoch1 = float(hi.loc[d1])
    tief = float(df["Low"].iloc[-60:].loc[:d1].min())
    t_ = float(c.iloc[-1] / c.loc[d1] - 1) * 100
    i_ = float(i_c.iloc[-1] / i_c.loc[d1] - 1) * 100
    if not (hoch1 / tief - 1 >= 0.10 and float(i_hi.loc[t2]) >= float(i_hi.loc[d1]) * 1.005
            and um_t2 <= hoch1 * 0.95 and i_ - t_ >= FUEHRT_PUNKTE):
        return []
    return [_zeichen("schwäche", "rs", f"tieferes Hoch gegen den Index: eigenes Hoch am {d1:%d.%m.} bei "
                     f"{_z(hoch1, '.2f')} $, am höheren Indexhoch {t2:%d.%m.} {_z((um_t2 / hoch1 - 1) * 100, '+.1f')} % "
                     f"darunter; seitdem {_z(t_, '+.1f')} %, der S&P 500 {_z(i_, '+.1f')} %", 2, t2) | {"auch_struktur": True}]


def tage_gegen_markt(df, idx, tage=20):
    """Versteckte Stärke: an mindestens 4 (und 60 %) der Indextage mit −1 % oder weniger im Plus geschlossen (20 Tage); gespiegelt
    Schwäche: an mindestens 3 Indextagen mit +1 % oder mehr im Minus."""
    if df is None or len(df) < tage + 2:
        return []
    c = df["Close"]
    ic = idx["Close"].reindex(df.index).ffill()
    r, ir = (c / c.shift() - 1).iloc[-tage:], (ic / ic.shift() - 1).iloc[-tage:]
    aus = []
    schwach = ir <= -0.01
    if (r[schwach] > 0).sum() >= max(4, 0.6 * schwach.sum()):
        aus.append(_zeichen("stärke", "rs", f"an {int((r[schwach] > 0).sum())} von {int(schwach.sum())} schwachen "
                            "Indextagen (−1 % und mehr, 20 Tage) im Plus geschlossen – versteckte Stärke"))
    stark = ir >= 0.01
    if (r[stark] < 0).sum() >= max(4, 0.6 * stark.sum()):
        aus.append(_zeichen("schwäche", "rs", f"an {int((r[stark] < 0).sum())} von {int(stark.sum())} starken "
                            "Indextagen (+1 % und mehr, 20 Tage) im Minus geschlossen – versteckte Schwäche"))
    return aus


def rs_linie(df, idx):
    """RS-Linie in der Base: steigt in 20 Tagen um mindestens 2 %, während der Kurs nachgibt; höheres Tief der RS-Linie
    bei tieferem Kurstief (60 Tage, Schwungpunkte n = 3). Gespiegelt für die Schwäche."""
    c = df["Close"]
    rs = (c / idx["Close"].reindex(df.index).ffill()).dropna()
    aus = []
    if len(rs) < 70 or len(c) < 70:
        return aus
    d_rs, d_k = float(rs.iloc[-1] / rs.iloc[-21] - 1) * 100, float(c.iloc[-1] / c.iloc[-21] - 1) * 100
    if d_rs >= 2 and d_k <= 0:
        aus.append(_zeichen("stärke", "rs", f"RS-Linie steigt in 20 Tagen {_z(d_rs, '+.1f')} %, während der Kurs "
                            f"{_z(d_k, '+.1f')} % nachgibt"))
    elif d_rs <= -2 and d_k >= 0:
        aus.append(_zeichen("schwäche", "rs", f"RS-Linie fällt in 20 Tagen {_z(d_rs, '+.1f')} %, während der Kurs "
                            f"{_z(d_k, '+.1f')} % steigt"))
    d = df.iloc[-60:]
    hs, ts = schwungpunkte(d["High"], d["Low"], 3)
    r60 = rs.reindex(d.index)
    if len(ts) >= 2:
        (i1, p1), (i2, p2) = ts[-2], ts[-1]
        if p2 < p1 and r60.iloc[i2] > r60.iloc[i1]:
            aus.append(_zeichen("stärke", "rs", f"RS-Linie macht ein höheres Tief, der Kurs ein tieferes "
                                f"({d.index[i1]:%d.%m.} → {d.index[i2]:%d.%m.})"))
    if len(hs) >= 2:
        (i1, p1), (i2, p2) = hs[-2], hs[-1]
        if p2 > p1 and r60.iloc[i2] < r60.iloc[i1]:
            aus.append(_zeichen("schwäche", "rs", f"RS-Linie macht ein tieferes Hoch, der Kurs ein höheres "
                                f"({d.index[i1]:%d.%m.} → {d.index[i2]:%d.%m.})"))
    return aus


def _fenster(start, idx):
    """start: (start, ende), ein Datum (ältere Aufrufe), KEIN oder None (dann selbst suchen) → (start, ende) oder None."""
    f = start if start is not None else startdatum(idx)
    if f is None or (isinstance(f, str) and f == KEIN):
        return None
    if isinstance(f, (tuple, list)):
        return pd.Timestamp(f[0]), (pd.Timestamp(f[1]) if f[1] is not None else None)
    return pd.Timestamp(f), None


def relativ(df, idx, start=None):
    """Stärke in der Schwäche und Schwäche in der Stärke → {staerke: [Text], schwaeche: [Text], zeichen: [Zeichen],
    seit, titel_pct, index_pct, vorbei}.
    Stärke in der Schwäche (Fenster der Korrektur, auch bis 45 Handelstage nach ihrem Tief):
      hält      der Index fiel bis zu seinem Tief mindestens 3 %, der Titel steht an diesem Tag mindestens
                so weit im Plus wie der Index im Minus und mindestens 15 Punkte vor ihm (Beta-Abgleich, Prüf-Agent 13.11.2026);
      führt     seit dem Indextief mindestens 10 Punkte vor dem Index, Kurs höchstens 15 % unter dem 52-Wochen-Hoch;
      nah       am Indextief höchstens halb so weit vom eigenen Hoch wie der Index und höchstens 15 %;
      RS-Linie  in den letzten 5 Tagen des Fensters am 52-Wochen-Hoch (höchstens 1 % darunter);
      Divergenz siehe divergenz().
    Schwäche in der Stärke (Index ≥ 3 % über dem Tief der 60 Tage): Titel seit dem Indextief im Minus; RS-Linie am
    52-Wochen-Tief; tieferes Hoch gegen den Index (divergenz_short)."""
    if df is None or idx is None or len(df) < JUNG_TAGE:
        return None
    c = df["Close"]
    i_c = idx["Close"].reindex(c.index).ffill()
    rs = (c / i_c).dropna()
    z_ = []
    aus = {"staerke": [], "schwaeche": [], "zeichen": z_}
    f = _fenster(start, idx)
    if f is not None and (c.index >= f[0]).any():
        s = c.index[c.index >= f[0]][0]
        ende = f[1]
        bis = c.index[c.index <= ende][-1] if ende is not None and (c.index <= ende).any() else c.index[-1]
        vorbei = ende is not None
        vor = f"in der Korrektur vom {s:%d.%m.} bis {bis:%d.%m.}: " if vorbei else ""
        t_pct = float(c.loc[bis] / c.loc[s] - 1) * 100
        i_pct = float(i_c.loc[bis] / i_c.loc[s] - 1) * 100
        aus.update(seit=f"{s:%d.%m.%Y}", titel_pct=round(t_pct, 1), index_pct=round(i_pct, 1), vorbei=vorbei)
        tief_tag = i_c.loc[s:bis].idxmin()
        i_fall = (1 - float(i_c.loc[tief_tag]) / float(i_c.loc[s])) * 100
        if i_pct < 0 and i_fall >= MIN_RUECKGANG:
            t_tief = float(c.loc[tief_tag] / c.loc[s] - 1) * 100       # gemessen am Tiefpunkt der Schwäche
            if t_tief >= i_fall and t_tief + i_fall >= HAELT_PUNKTE:
                z_.append(_zeichen("stärke", "rs", f"{vor}vom Indexhoch {s:%d.%m.} bis zum Indextief {tief_tag:%d.%m.} "
                                   f"{_z(t_tief, '+.1f')} %, der S&P 500 {_z(-i_fall, '+.1f')} % (hält in der Schwäche)", 2))
            hoch52_jetzt = float(df["High"].iloc[-252:].max())
            if tief_tag < c.index[-1]:
                t3 = float(c.iloc[-1] / c.loc[tief_tag] - 1) * 100
                i3 = float(i_c.iloc[-1] / i_c.loc[tief_tag] - 1) * 100
                if t3 - i3 >= FUEHRT_PUNKTE and (1 - float(c.iloc[-1]) / hoch52_jetzt) * 100 <= FUEHRT_NAH_HOCH:
                    z_.append(_zeichen("stärke", "rs", f"seit dem Indextief {tief_tag:%d.%m.} {_z(t3, '+.1f')} %, "
                                       f"der S&P 500 {_z(i3, '+.1f')} % (führt aus der Korrektur)", 2))
            hoch52 = float(df["High"].loc[:tief_tag].iloc[-252:].max())
            i_hoch52 = float(idx["High"].loc[:tief_tag].iloc[-252:].max())
            abst = (1 - float(c.loc[tief_tag]) / hoch52) * 100
            i_abst = (1 - float(i_c.loc[tief_tag]) / i_hoch52) * 100
            if abst <= 0.5 * i_abst and abst <= FUEHRT_NAH_HOCH:
                z_.append(_zeichen("stärke", "rs", f"{vor}am Indextief {tief_tag:%d.%m.} {_z(abst, '.0f')} % unter dem "
                                   f"eigenen Hoch, der Index {_z(i_abst, '.0f')} %"))
            r_bis = rs.loc[:bis]
            if len(r_bis) > 5 and float(r_bis.iloc[-5:].max()) >= float(r_bis.iloc[-252:].max()) * RS_HOCH:
                z_.append(_zeichen("stärke", "rs", f"{vor}RS-Linie am 52-Wochen-Hoch, während der Index fällt", 2))
            z_ += divergenz(df, idx, s, ende)
    tief = i_c.iloc[-60:].idxmin()
    if (float(i_c.iloc[-1]) / float(i_c.loc[tief]) - 1) * 100 >= MIN_RUECKGANG:
        t2 = float(c.iloc[-1] / c.loc[tief] - 1) * 100
        i2 = float(i_c.iloc[-1] / i_c.loc[tief] - 1) * 100
        if t2 < 0:
            z_.append(_zeichen("schwäche", "rs", f"seit dem Indextief {tief:%d.%m.} {_z(t2, '+.1f')} %, der S&P 500 "
                               f"{_z(i2, '+.1f')} % (Schwäche in der Stärke)", 2))
        if float(rs.iloc[-5:].min()) <= float(rs.iloc[-252:].min()) / RS_HOCH:
            z_.append(_zeichen("schwäche", "rs", "RS-Linie am 52-Wochen-Tief, während der Index steigt", 2))
        z_ += divergenz_short(df, idx)
    aus["staerke"] = [x["text"] for x in z_ if x["seite"] == "stärke"]
    aus["schwaeche"] = [x["text"] for x in z_ if x["seite"] == "schwäche"]
    return aus


# ── Reaktion auf Nachrichten (Zahlen) ─────────────────────────────────────────────────────────────────────────────
def reaktion(df, gewinne, max_tage=60):
    """Reaktion auf die letzte Zahlenmeldung → Liste von Zeichen. Überraschung gegen Reaktion (Schwäche ab −2 % trotz
    guter Zahlen, Stärke ab +1 % mit Schluss in der oberen Hälfte trotz schlechter), Lücke gegen Schluss im Tag
    (Lücke ≥ +3 % und Schluss im unteren Drittel = verkauft; gespiegelt gekauft), Kurs heute (zurück unter
    bzw. über den Schluss vor den Zahlen = Zahlen verworfen bzw. Abverkauf zurückgekauft)."""
    try:
        import zahlen_reaktion
        rt = zahlen_reaktion.reaktionstag(df, gewinne)
    except Exception:  # noqa: BLE001
        return []
    if not rt:
        return []
    pos, pct = rt
    if len(df) - 1 - pos > max_tage or pos < 1:
        return []
    tag = df.index[pos]
    ue = None
    for t, z in gewinne.iterrows():
        if abs((pd.Timestamp(t) - tag).days) <= 4:
            ue = z.get("ueberraschung_pct")
    if ue is not None and pd.isna(ue):
        ue = None
    o, h, l, c = (float(df[x].iloc[pos]) for x in ("Open", "High", "Low", "Close"))
    vor = float(df["Close"].iloc[pos - 1])
    luecke = (o / vor - 1) * 100
    lage = (c - l) / (h - l) if h > l else 0.5
    aus = []
    zahl = f"Zahlen am {tag:%d.%m.}" + (f" {_z(ue, '+.0f')} % {'über' if ue > 0 else 'unter'} Erwartung"
                                         if ue else "")
    if luecke >= 3 and lage <= 1 / 3:
        aus.append(_zeichen("schwäche", "ereignis", f"{zahl}: Lücke {_z(luecke, '+.1f')} % verkauft, Schluss im "
                            "unteren Drittel des Tages", 2))
    elif luecke <= -3 and lage >= 2 / 3:
        aus.append(_zeichen("stärke", "ereignis", f"{zahl}: Lücke {_z(luecke, '+.1f')} % gekauft, Schluss im "
                            "oberen Drittel des Tages", 2))
    if ue is not None:
        if ue > 0 and pct <= -2:
            aus.append(_zeichen("schwäche", "ereignis", f"{zahl}, der Kurs fiel {_z(pct, '+.1f')} % (Käufer erschöpft)", 2))
        elif ue < 0 and pct >= 1 and lage >= 0.5:
            aus.append(_zeichen("stärke", "ereignis", f"{zahl}, der Kurs stieg {_z(pct, '+.1f')} % (Nachfrage trägt)", 2))
        elif ue > 0 and pct >= zahlen_reaktion.REAKTION_PCT:
            aus.append(_zeichen("stärke", "ereignis", f"{zahl}, der Kurs stieg {_z(pct, '+.1f')} %"))
        elif ue < 0 and pct <= -zahlen_reaktion.REAKTION_PCT:
            aus.append(_zeichen("schwäche", "ereignis", f"{zahl}, der Kurs fiel {_z(pct, '+.1f')} %"))
    jetzt = float(df["Close"].iloc[-1])
    if pct > 0 and jetzt < vor:                  # wie die Kachel „Zahlen verworfen“ (O'Neil): eine Ablesung, ein Urteil
        aus.append(_zeichen("schwäche", "ereignis", f"{zahl}: Tag 1 {_z(pct, '+.1f')} %, der Kurs steht jetzt unter dem "
                            f"Schluss vor den Zahlen {_z(vor, '.2f')} $ – Zahlen verworfen", 2))
    elif pct < 0 and jetzt > vor:
        aus.append(_zeichen("stärke", "ereignis", f"{zahl}: Tag 1 {_z(pct, '+.1f')} %, der Kurs steht jetzt über dem "
                            f"Schluss vor den Zahlen {_z(vor, '.2f')} $ – Abverkauf zurückgekauft", 2))
    return aus


# ── Wertzone wandert (Market Profile) ─────────────────────────────────────────────────────────────────────────────
def wertzone(tage, df=None):
    """tage: Tagesprofile des Market Profile (erkennung.mp_von(df)["tage"], chronologisch, je Tag mit poc). Nur in der
    Seitwärtszone (Schluss in 10 Tagen höchstens ±4 %) – im Trend sagt das nichts Neues."""
    if not tage or len(tage) < 10:
        return None
    if df is not None and len(df) > 11 and abs(float(df["Close"].iloc[-1] / df["Close"].iloc[-11]) - 1) * 100 > SEITWAERTS_PCT:
        return None
    jetzt = np.mean([x["poc"] for x in tage[-5:]])
    vorher = np.mean([x["poc"] for x in tage[-10:-5]])
    d = (jetzt / vorher - 1) * 100
    if d >= WERT_WANDERT_PCT:
        return _zeichen("stärke", "ereignis", f"Wert wandert nach oben (POC 5 Tage {_z(d, '+.1f')} %)")
    if d <= -WERT_WANDERT_PCT:
        return _zeichen("schwäche", "ereignis", f"Wert wandert nach unten (POC 5 Tage {_z(d, '+.1f')} %)")
    return None


# ── Kreislauf ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _lauf(ph):
    """Länge der laufenden Phase am Ende (Wochen)."""
    n, letzte = 0, ph[-1]
    for x in reversed(ph):
        if x != letzte:
            break
        n += 1
    return n


def _traegt(liste):
    """Ein Zeichen der Struktur und eines aus Volumen oder RS (Prüf-Agent 13.11.2026). Die Divergenz ist beides: ein
    höheres (tieferes) Tief ist Struktur, gegen den Index gemessen RS – zählt sie mit einem zweiten RS-Zeichen."""
    arten = {x["art"] for x in liste} | {"struktur" for x in liste if x.get("auch_struktur")}
    return "struktur" in arten and bool(arten & {"volumen", "rs"})


def kreislauf(df, idx=None, gewinne=None, tage30=None, fehlausbruch=None, start=None):
    """Phase, Wechsel und Zeichen eines Titels → dict mit phase (0 jung, 1–4), ziel, wort, satz, zeichen (Liste),
    staerke/schwaeche (Texte, stärkste zuerst), dow_tag, dow_woche, einquetschung, akkumulation, relativ, trend,
    kurve, tiefs, index_kurve, phasen (52 Wochen; 21 = Rückschlag in Phase 2), wechsel_wochen, rueckschlag, jung."""
    import phase as phase_mod
    if df is None or len(df) < JUNG_TAGE:
        return None
    w = wochenkerzen(df)
    jung = len(df) < 300
    if jung:
        phl = [0] * len(w)
        p = 0
    else:
        ph = phase_mod.phasen(df).reindex(w.index).ffill().fillna(1).astype(int)
        # wie erkennung._phase_von (Karte, Weinstein-Zeichen): die laufende Woche zählt erst ab ihrem Freitag
        p = phase_mod.aktuell(df, ph)
        phl = [int(x) for x in ph]
        phl[-1] = p
    zs = []
    dt, dw = dow(df, 5), dow(w, 2)
    if dt and dt.get("signal"):
        zs.append(_zeichen(dt["richtung"], "struktur", dt["signal"]))
    if dw and dw.get("signal") and not (dt and dt.get("richtung") == dw["richtung"]):
        zs.append(_zeichen(dw["richtung"], "struktur", dw["signal"] + " (Wochenkerzen)", 2))
    elif dw and dw.get("signal"):
        zs[-1]["gewicht"], zs[-1]["text"] = 2, zs[-1]["text"] + " (auch auf Wochenkerzen)"
    sp = spring(df)
    if sp:
        zs.append(sp)
    eq = einquetschung(df)
    if eq:
        zs.append(_zeichen("stärke", "struktur", f"Einquetschung: steigende Tiefs unter der Oberkante "
                           f"{_z(eq['oberkante'], '.2f')} $", 2) if eq["art"] == "aufsteigend" else
                  _zeichen("schwäche", "struktur", f"Einquetschung: fallende Hochs über der Unterkante "
                           f"{_z(eq['unterkante'], '.2f')} $", 2))
    ak = akkumulation(df)
    if ak:
        if ak["bild"] == "Akkumulation":
            zs.append(_zeichen("stärke", "volumen", f"Akkumulation: {_tage(ak['kauftage'], 'Kauftag')} gegen "
                               f"{_tage(ak['abgabetage'], 'Abgabetag')} mit Volumen (20 Tage)"))
        elif ak["bild"] == "Distribution":
            zs.append(_zeichen("schwäche", "volumen", f"Distribution: {_tage(ak['abgabetage'], 'Abgabetag')} gegen "
                               f"{_tage(ak['kauftage'], 'Kauftag')} mit Volumen (20 Tage)"))
        if ak["churning"] >= 3:
            zs.append(_zeichen("schwäche", "volumen", f"verdeckte Abgabe: {ak['churning']} Tage mit Volumen im Plus, "
                               "aber Schluss im unteren Drittel (Churning, 20 Tage)"))
        if ak["pocket_pivot"]:
            zs.append(_zeichen("stärke", "volumen", f"Pocket Pivot am {ak['pocket_pivot']}"))
    zs += enge_trocken(df)
    rel = None
    if idx is not None:
        rel = relativ(df, idx, start)
        if rel:
            zs += rel["zeichen"]
        zs += tage_gegen_markt(df, idx)
        zs += rs_linie(df, idx)
    if gewinne is not None:
        zs += reaktion(df, gewinne)
    wz = wertzone(tage30, df)
    if wz:
        zs.append(wz)
    if fehlausbruch:
        zs.append(_zeichen("schwäche", "struktur", fehlausbruch, 2))
    # Bruch der Spanne (Phase 1/3 nach unten) und Ausbruch aus der Verteilung (Phase 3 nach oben)
    lauf = 0 if jung else _lauf(phl)
    kurs = float(df["Close"].iloc[-1])
    bruch = ausbruch3 = False
    if p in (1, 3) and lauf >= 4:
        spanne = w[w.index < df.index[-1]].iloc[-lauf:]
        if len(spanne) >= 3:
            unten, oben = float(spanne["Low"].min()), float(spanne["High"].max())
            if kurs < unten * 0.99 and (dt or {}).get("struktur") != "aufwärts":
                bruch = True
                zs.append(_zeichen("schwäche", "struktur", f"Schluss unter dem Tief der {PHASE_NAME[p]} "
                                   f"{_z(unten, '.2f')} $", 2))
            if p == 3 and kurs > oben and idx is not None:
                rs = (df["Close"] / idx["Close"].reindex(df.index).ffill()).dropna()
                if len(rs) > 50 and float(rs.iloc[-1]) > float(rs.iloc[-50:].mean()):
                    ausbruch3 = True
                    zs.append(_zeichen("stärke", "struktur", f"Schluss über dem Hoch der Verteilung "
                                       f"{_z(oben, '.2f')} $, RS-Linie über ihrem GD50", 2))
    st_ = [x for x in zs if x["seite"] == "stärke"]
    sw_ = [x for x in zs if x["seite"] == "schwäche"]
    g_st, g_sw = sum(x["gewicht"] for x in st_), sum(x["gewicht"] for x in sw_)
    stark = _traegt(st_) and g_st >= 4 and g_st >= 2 * g_sw       # klares Übergewicht, nicht bloß eins mehr
    schwach = _traegt(sw_) and g_sw >= 4 and g_sw >= 2 * g_st
    ziel = None
    if p == 4 and stark:
        ziel = 1
    elif p == 1 and bruch and schwach:
        ziel = 4
    elif p == 1 and stark:
        ziel = 2
    elif p == 2 and schwach:
        ziel = 3
    elif p == 3 and ausbruch3 and stark:
        ziel = 2
    elif p == 3 and schwach:
        ziel = 4
    # Rückschlag in Phase 2: Wochenschluss unter GD10W und mindestens 15 % unter dem 52-Wochen-Hoch
    rueckschlag = False
    if not jung:
        wc, wh = w["Close"], w["High"].rolling(52, min_periods=10).max()
        g10 = wc.rolling(10).mean()
        for i in range(len(phl)):
            if phl[i] == 2 and wc.iloc[i] < g10.iloc[i] and wc.iloc[i] <= wh.iloc[i] * 0.85:
                phl[i] = RUECKSCHLAG
        rueckschlag = p == 2 and phl[-1] == RUECKSCHLAG
    wort = PHASE_NAME[0] if jung else (f"{p} → {ziel}" if ziel else str(p))
    if rueckschlag:
        wort += " · Rückschlag"
    if eq:
        wort += " · Einquetschung"
    # seit wann sich der Wechsel abzeichnet (Kurve ab dort hell)
    wechsel_wochen = None
    if ziel:
        tag = None
        if ziel in (1, 2):
            if dt and dt.get("tief_tag") is not None:
                tag = dt["tief_tag"]
            if rel and rel.get("seit"):
                s_ = pd.to_datetime(rel["seit"], format="%d.%m.%Y")
                d_ = df["Low"].loc[s_:].idxmin()
                tag = min(tag, d_) if tag is not None else d_
        elif dt and dt.get("hoch_tag") is not None:
            tag = dt["hoch_tag"]
        if tag is not None:
            wechsel_wochen = max(1, int(np.ceil((df.index[-1] - tag).days / 7)))
    ordnung = {"struktur": 0, "rs": 1, "volumen": 2, "ereignis": 3}
    st_.sort(key=lambda x: (-x["gewicht"], ordnung[x["art"]]))
    sw_.sort(key=lambda x: (-x["gewicht"], ordnung[x["art"]]))
    satz = "jung (unter 300 Handelstagen, noch keine Phase)" if jung else f"Phase {p} ({PHASE_NAME[p]})"
    if rueckschlag:
        satz += ", Rückschlag (Wochenschluss unter dem GD10W, mindestens 15 % unter dem Hoch)"
    if ziel:
        satz += f", Wechsel zu Phase {ziel} ({PHASE_NAME[ziel]}) zeichnet sich ab"
    if st_:
        satz += " · Stärke: " + "; ".join(x["text"] for x in st_[:3])
    if sw_:
        satz += " · Schwäche: " + "; ".join(x["text"] for x in sw_[:3])
    kurve = w["Close"].iloc[-52:]
    i_w = None
    if idx is not None:
        iw = idx["Close"].reindex(w.index, method="ffill").iloc[-52:]
        if iw.notna().all():
            i_w = [round(float(x), 2) for x in iw]
    return {"phase": p, "ziel": ziel, "wort": wort, "satz": satz, "zeichen": st_ + sw_,
            "staerke": [x["text"] for x in st_], "schwaeche": [x["text"] for x in sw_],
            "dow_tag": dt, "dow_woche": dw, "einquetschung": eq, "akkumulation": ak, "relativ": rel,
            "trend": trendqualitaet(df), "jung": jung, "rueckschlag": rueckschlag,
            "kurve": [round(float(x), 2) for x in kurve], "tiefs": [round(float(x), 2) for x in w["Low"].iloc[-52:]],
            "index_kurve": i_w, "phasen": phl[-52:],
            "kurve_von": f"{kurve.index[0]:%d.%m.%Y}", "kurve_bis": f"{df.index[-1]:%d.%m.%Y}",
            "wechsel_wochen": wechsel_wochen}


# ── Speicher: der Frühlauf rechnet den Kreislauf aller Titel mit dem Kartentisch (daten/kreislauf/<stand>.json) ───
SPEICHER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "daten", "kreislauf")
_START, _GELADEN = {}, {}


def startdatum(idx):
    """korrekturfenster() einmal je Indextag (die Marktrichtung lädt die Indizes) → (start, ende) oder KEIN."""
    schl = (len(idx), idx.index[-1])
    if schl not in _START:
        _START.clear()
        _START[schl] = korrekturfenster(idx) or KEIN
    return _START[schl]


def fuer_titel(tk, df, idx, gewinne=None, start=None, mit_wertzone=True, fehlausbruch=None):
    """kreislauf() mit Index-Bezug und – wenn gespeichert – der Market-Profile-Analyse; None bei zu kurzer Reihe."""
    if df is None or len(df) < JUNG_TAGE or idx is None:
        return None
    tage30 = None
    if mit_wertzone:                             # dieselbe Market-Profile-Analyse wie Karte und Chart (zwischengespeichert)
        try:
            import erkennung
            if not df.attrs.get("ticker"):
                df.attrs["ticker"] = tk
            tage30 = (erkennung.mp_von(df) or {}).get("tage")
        except Exception:  # noqa: BLE001
            tage30 = None
    st = start if start is not None else startdatum(idx)      # einmal je Indextag, nicht je Titel
    i_ = idx[idx.index <= df.index[-1]]
    k = kreislauf(df, i_, gewinne, tage30, fehlausbruch, start=st)
    if k:
        k["stand"] = f"{df.index[-1]:%Y-%m-%d}"
        for x in ("dow_tag", "dow_woche"):       # nur Speicherbares (keine Zeitstempel)
            if k.get(x):
                k[x] = {a: b for a, b in k[x].items() if a in ("struktur", "signal", "richtung", "letztes_tief",
                                                              "letztes_hoch")}
        if k.get("relativ"):
            k["relativ"] = {a: b for a, b in k["relativ"].items() if a != "zeichen"}
    return k


def ablegen(stand, alle, behalten=10):
    from dateien import json_schreiben
    os.makedirs(SPEICHER, exist_ok=True)
    for f in sorted(f for f in os.listdir(SPEICHER) if f.endswith(".json"))[:-behalten]:
        try:                                     # nur die jüngsten Tage behalten (Prüf-Agent 13.11.2026)
            os.remove(os.path.join(SPEICHER, f))
        except OSError:
            pass
    json_schreiben(os.path.join(SPEICHER, f"{stand}.json"), {"stand": stand, "titel": alle}, ensure_ascii=False)


def laden():
    """Jüngster gespeicherter Kreislauf {stand, titel: {tk: kreislauf}} oder {} – einmal je Datei gelesen."""
    if not os.path.isdir(SPEICHER):
        return {}
    for f in sorted((f for f in os.listdir(SPEICHER) if f.endswith(".json")), reverse=True):
        p = os.path.join(SPEICHER, f)
        m = os.path.getmtime(p)
        if _GELADEN.get("pfad") == (p, m):
            return _GELADEN["daten"]
        from dateien import json_lesen
        d = json_lesen(p)
        if d:
            _GELADEN.update(pfad=(p, m), daten=d)
            return d
    return {}


def von(tk):
    return (laden().get("titel") or {}).get(tk)
