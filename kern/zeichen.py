"""Zeichen der Stärke und Schwäche und der Kreislauf je Titel (Lehre von Stärke und Schwäche, Micky 13.11.2026).

Grundsatz (Auction Market Theory): Ein Titel ist in Balance (Seitwärtszone) oder im Ungleichgewicht (Trend). Er verlässt
die Balance, weil neue Information den Wert verändert oder eine Seite erschöpft ist. Stärke = die Nachfrage überwiegt,
das Angebot weicht; Schwäche = das Spiegelbild. Kreislauf (Weinstein/Wyckoff): 1 Basis → 2 Aufwärts → 3 Verteilung →
4 Abwärts; die Phase je Woche rechnet phase.py, die Wechselzeichen kommen von hier.

Die App misst, der Stab deutet. Jede Messung ist eine feste Regel:
  Dow-Struktur      Schwungpunkte (Hoch/Tief, das je n Kerzen links und rechts überragt; Tag n=5, Woche n=2).
                    Höhere Hochs und höhere Tiefs = aufwärts, tiefere Hochs und Tiefe = abwärts, sonst Balance.
                    Frühestes Zeichen des Wechsels zu Schwäche: Schluss unter dem letzten höheren Tief; zu Stärke:
                    erstes höheres Tief nach tieferen Tiefs, oder Schluss über dem letzten tieferen Hoch.
  Einquetschung     in den letzten 60 Tagen mindestens 2 Schwunghochs innerhalb von ±1,5 % der Oberkante und
                    mindestens 3 steigende Schwungtiefs, die Spanne der letzten 10 Tage enger als die der ersten 10,
                    das Volumen der letzten 10 Tage unter dem 50-Tage-Schnitt (aufsteigendes Dreieck; gespiegelt
                    absteigend). Pivot = Oberkante (Form des Base-Ausbruchs bzw. der Bärenflagge).
  Akkumulation      20 Tage: Kauftage (Schluss über dem Vortag) mit Volumen über dem 50-Tage-Schnitt gegen
                    Abgabetage mit Volumen über dem Schnitt (O'Neil); Schlüsse im oberen/unteren Drittel der Spanne;
                    Pocket Pivot in den letzten 5 Tagen (Kauftag, Volumen über dem größten Abgabetag-Volumen der
                    10 Tage davor – Morales/Kacher). Pocket Pivot nur über GD10 und GD50 mit Schluss in der oberen
                    Hälfte. Saldo ≥ 3 Akkumulation, ≤ −3 Distribution.
  Relativ           siehe relativ(): hält, führt aus der Korrektur, nah am Hoch, RS-Linie – und gespiegelt.
  Reaktion          die letzte Zahlenmeldung (höchstens 60 Handelstage her): Überraschung positiv und der Kurs fällt
                    am Reaktionstag = Schwäche; Überraschung negativ und der Kurs hält (Reaktion ≥ 0) = Stärke.
  Wertzone          Market Profile (30-Minuten-Kerzen, wenn vorhanden): POC der letzten 5 Tage gegen die 5 davor –
                    wandert der akzeptierte Wert um mindestens 3 % nach oben bzw. unten, während der Kurs seitwärts läuft
                    (Schluss in 10 Tagen höchstens ±4 %).
"""
import numpy as np
import pandas as pd

GLEICH_PCT = 1.5          # Einquetschung: Hochs innerhalb ±1,5 %
MIN_RUECKGANG = 3.0       # Index mindestens 3 % unter seinem Hoch (bzw. über seinem Tief)
HAELT_PCT = 5.0           # „hält in der Schwäche“: seit dem Indexhoch mindestens 5 % im Plus …
FUEHRT_PUNKTE = 10.0      # … und mindestens 10 Prozentpunkte besser als der Index (ebenso „führt aus der Korrektur“)
KEIN = "kein"             # Startdatum schon gesucht, der Markt ist nicht schwach (statt None = noch nicht gesucht)
SEITWAERTS_PCT = 4.0         # Seitwärtszone: Schluss in 10 Tagen höchstens ±4 %
WERT_WANDERT_PCT = 3.0       # der akzeptierte Wert (POC) wandert in 5 Tagen um mindestens 3 %
PHASE_NAME = {1: "Basis", 2: "Aufwärts", 3: "Verteilung", 4: "Abwärts"}


def _z(x, fmt):
    """Zahl deutsch: Komma statt Punkt, echtes Minus."""
    return format(x, fmt).replace(".", ",").replace("-", "−")


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
    """→ {struktur: aufwärts/abwärts/balance, signal: Text oder None, richtung: stärke/schwäche/None, letztes_tief,
    letztes_hoch}."""
    if df is None or len(df) < 4 * n + 4:
        return None
    hochs, tiefs = schwungpunkte(df["High"], df["Low"], n)
    if len(hochs) < 2 or len(tiefs) < 2:
        return {"struktur": "balance", "signal": None, "richtung": None}
    (_, h1), (_, h2) = hochs[-2], hochs[-1]
    (_, t1), (_, t2) = tiefs[-2], tiefs[-1]
    kurs = float(df["Close"].iloc[-1])
    if h2 > h1 and t2 > t1:
        struktur = "aufwärts"
    elif h2 < h1 and t2 < t1:
        struktur = "abwärts"
    else:
        struktur = "balance"
    signal = richtung = None
    if struktur == "aufwärts" and kurs < t2:
        signal, richtung = f"Schluss unter dem letzten höheren Tief {_z(t2, '.2f')}", "schwäche"
    elif struktur == "abwärts" and kurs > h2:
        signal, richtung = f"Schluss über dem letzten tieferen Hoch {_z(h2, '.2f')}", "stärke"
    elif (t2 > t1 and len(tiefs) >= 3 and len(hochs) >= 3 and tiefs[-3][1] > t1 and hochs[-3][1] > h1
          and tiefs[-2][0] > hochs[-3][0]):
        signal, richtung = f"erstes höheres Tief {_z(t2, '.2f')} nach tieferen Hochs und Tiefs", "stärke"
    elif (h2 < h1 and len(hochs) >= 3 and len(tiefs) >= 3 and hochs[-3][1] < h1 and tiefs[-3][1] < t1
          and hochs[-2][0] > tiefs[-3][0]):
        signal, richtung = f"erstes tieferes Hoch {_z(h2, '.2f')} nach höheren Hochs und Tiefs", "schwäche"
    return {"struktur": struktur, "signal": signal, "richtung": richtung, "letztes_tief": round(t2, 2),
            "letztes_hoch": round(h2, 2)}


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


# ── Einquetschung ─────────────────────────────────────────────────────────────────────────────────────────────────
def einquetschung(df, fenster=60):
    """Aufsteigendes Dreieck (gespiegelt absteigend) → {art, oberkante|unterkante, beruehrungen, tiefs|hochs} oder None.
    Gezählt ab dem tiefsten Tief (bzw. höchsten Hoch) des Fensters: mindestens 3 steigende Schwungtiefs darin, das
    erste ist dieses Tief; mindestens 2 Schwunghochs an der Oberkante (±1,5 %); der Kurs steht noch unter der Oberkante
    oder höchstens 5 % darüber."""
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
    i0 = int(lo.argmin())                                   # aufsteigend: ab dem tiefsten Tief
    t_ = [(i0, lo[i0])] + [(i, p) for i, p in tiefs if i > i0]
    h_ = [(i, p) for i, p in hochs if i > i0]
    if len(t_) >= 3 and len(h_) >= 2 and all(b_[1] > a_[1] for a_, b_ in zip(t_, t_[1:])):
        top = max(p for _, p in h_)
        an = [p for _, p in h_ if abs(p / top - 1) * 100 <= GLEICH_PCT]
        if len(an) >= 2 and kurs <= top * 1.05:
            return {"art": "aufsteigend", "oberkante": round(top, 2), "beruehrungen": len(an), "tiefs": len(t_)}
    j0 = int(hi.argmax())                                   # absteigend: ab dem höchsten Hoch
    h2 = [(j0, hi[j0])] + [(i, p) for i, p in hochs if i > j0]
    t2 = [(i, p) for i, p in tiefs if i > j0]
    if len(h2) >= 3 and len(t2) >= 2 and all(b_[1] < a_[1] for a_, b_ in zip(h2, h2[1:])):
        boden = min(p for _, p in t2)
        am = [p for _, p in t2 if abs(p / boden - 1) * 100 <= GLEICH_PCT]
        if len(am) >= 2 and kurs >= boden * 0.95:
            return {"art": "absteigend", "unterkante": round(boden, 2), "beruehrungen": len(am), "hochs": len(h2)}
    return None


# ── Akkumulation und Distribution ─────────────────────────────────────────────────────────────────────────────────
def lage_ok(df, i):
    """Schluss in der oberen Hälfte der Tagesspanne."""
    h, l, c = df["High"].iloc[i], df["Low"].iloc[i], df["Close"].iloc[i]
    return h > l and (c - l) / (h - l) >= 0.5


def akkumulation(df, tage=20):
    if df is None or len(df) < 70:
        return None
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    schnitt = v.rolling(50).mean()
    auf = c > c.shift(1)
    ab = c < c.shift(1)
    hoch_vol = v > schnitt
    letzte = slice(-tage, None)
    kauf = int((auf & hoch_vol).iloc[letzte].sum())
    abgabe = int((ab & hoch_vol).iloc[letzte].sum())
    lage = ((c - l) / (h - l).replace(0, np.nan)).iloc[letzte]
    oben, unten = int((lage >= 2 / 3).sum()), int((lage <= 1 / 3).sum())
    pocket = None
    g10, g50 = c.rolling(10).mean(), c.rolling(50).mean()
    for i in range(len(df) - 5, len(df)):
        if auf.iloc[i] and c.iloc[i] > g10.iloc[i] and c.iloc[i] > g50.iloc[i] and lage_ok(df, i):
            vor = df.iloc[i - 10:i]
            ab_vol = vor["Volume"][vor["Close"] < vor["Close"].shift(1).fillna(vor["Close"])]
            if len(ab_vol) and v.iloc[i] > ab_vol.max():
                pocket = f"{df.index[i]:%d.%m.}"
    saldo = kauf - abgabe
    return {"kauftage": kauf, "abgabetage": abgabe, "oben": oben, "unten": unten, "pocket_pivot": pocket,
            "bild": "Akkumulation" if saldo >= 3 else "Distribution" if saldo <= -3 else "ausgeglichen"}


# ── Relativ zum Markt ─────────────────────────────────────────────────────────────────────────────────────────────
def korrekturbeginn(idx):
    """Beginn der Schwäche des Index: das Indexhoch vor O'Neils Korrektur (bzw. „unter Druck“), sonst das letzte Hoch der 60 Tage, wenn der Index
    mindestens 3 % darunter liegt; sonst None."""
    try:
        import marktrichtung
        mr = marktrichtung.richtung(bis=idx.index[-1])
        if mr.get("ampel") != "grün" and mr.get("seit") is not None:
            vor = idx["Close"].loc[:pd.Timestamp(mr["seit"])].iloc[-60:]    # das Hoch vor der Korrektur
            return vor.idxmax()
    except Exception:  # noqa: BLE001
        pass
    c = idx["Close"].iloc[-60:]
    if (1 - c.iloc[-1] / c.max()) * 100 >= MIN_RUECKGANG:
        return c.idxmax()
    return None


def relativ(df, idx, start=None):
    """Stärke in der Schwäche und Schwäche in der Stärke → {staerke: [..], schwaeche: [..], seit, titel_pct, index_pct}.
    Stärke in der Schwäche (O'Neil sieht Korrektur oder Druck, oder der Index liegt mindestens 3 % unter dem Hoch der
    letzten 60 Tage – gemessen ab diesem Hoch):
      hält      der Titel steht seit dem Indexhoch mindestens 5 % im Plus und 10 Punkte vor dem Index;
      führt     seit dem Indextief mindestens 10 Prozentpunkte besser als der Index (O'Neil: die Führer brechen als
                erste aus der Korrektur aus);
      nah       am Tag des Indextiefs näher am eigenen 52-Wochen-Hoch als der Index an seinem;
      RS-Linie  in den letzten 5 Tagen am 52-Wochen-Hoch.
    Schwäche in der Stärke (der Index ist seit seinem Tief mindestens 3 % gestiegen): der Titel seit dem Indextief im
    Minus, RS-Linie am 52-Wochen-Tief."""
    if df is None or idx is None or len(df) < 260:
        return None
    c = df["Close"]
    i_c = idx["Close"].reindex(c.index).ffill()
    rs = (c / i_c).dropna()
    aus = {"staerke": [], "schwaeche": []}
    start = None if start == KEIN else start if start is not None else startdatum(idx)
    if start is not None and (c.index >= start).any():
        s = c.index[c.index >= start][0]
        t_pct = float(c.iloc[-1] / c.loc[s] - 1) * 100
        i_pct = float(i_c.iloc[-1] / i_c.loc[s] - 1) * 100
        aus.update(seit=f"{s:%d.%m.%Y}", titel_pct=round(t_pct, 1), index_pct=round(i_pct, 1))
        if i_pct < 0:                     # korrekturbeginn() liefert nur bei schwachem Markt ein Datum
            if t_pct >= HAELT_PCT and t_pct - i_pct >= FUEHRT_PUNKTE:
                aus["staerke"].append(f"seit dem Indexhoch {s:%d.%m.} {_z(t_pct, '+.1f')} %, der S&P 500 {_z(i_pct, '+.1f')} % "
                                      "(hält in der Schwäche)")
            tief_tag = i_c.loc[s:].idxmin()
            if tief_tag < c.index[-1]:
                t3 = float(c.iloc[-1] / c.loc[tief_tag] - 1) * 100
                i3 = float(i_c.iloc[-1] / i_c.loc[tief_tag] - 1) * 100
                if t3 - i3 >= FUEHRT_PUNKTE:
                    aus["staerke"].append(f"seit dem Indextief {tief_tag:%d.%m.} {_z(t3, '+.1f')} %, der S&P 500 {_z(i3, '+.1f')} % "
                                          "(führt aus der Korrektur)")
            hoch52 = float(df["High"].loc[:tief_tag].iloc[-252:].max())
            i_hoch52 = float(idx["High"].loc[:tief_tag].iloc[-252:].max())
            abst = (1 - float(c.loc[tief_tag]) / hoch52) * 100
            i_abst = (1 - float(i_c.loc[tief_tag]) / i_hoch52) * 100
            if abst < i_abst:
                aus["staerke"].append(f"am Indextief {tief_tag:%d.%m.} {_z(abst, '.0f')} % unter dem eigenen Hoch, "
                                      f"der Index {_z(i_abst, '.0f')} %")
            if float(rs.iloc[-5:].max()) >= float(rs.iloc[-252:].max()) * 0.999:
                aus["staerke"].append("RS-Linie am 52-Wochen-Hoch, während der Index fällt")
    tief = i_c.iloc[-60:].idxmin()
    if (float(i_c.iloc[-1]) / float(i_c.loc[tief]) - 1) * 100 >= MIN_RUECKGANG:
        t2 = float(c.iloc[-1] / c.loc[tief] - 1) * 100
        i2 = float(i_c.iloc[-1] / i_c.loc[tief] - 1) * 100
        if t2 < 0:
            aus["schwaeche"].append(f"seit dem Indextief {tief:%d.%m.} {_z(t2, '+.1f')} %, der S&P 500 {_z(i2, '+.1f')} % "
                                    "(Schwäche in der Stärke)")
        if float(rs.iloc[-5:].min()) <= float(rs.iloc[-252:].min()) * 1.001:
            aus["schwaeche"].append("RS-Linie am 52-Wochen-Tief, während der Index steigt")
    return aus


# ── Reaktion auf Nachrichten (Zahlen) ─────────────────────────────────────────────────────────────────────────────
def reaktion(df, gewinne, max_tage=60):
    """→ (Richtung stärke/schwäche, Text) oder None."""
    try:
        import zahlen_reaktion
        rt = zahlen_reaktion.reaktionstag(df, gewinne)
    except Exception:  # noqa: BLE001
        return None
    if not rt:
        return None
    pos, pct = rt
    if len(df) - 1 - pos > max_tage:
        return None
    tag = df.index[pos]
    ue = None
    for t, z in gewinne.iterrows():
        if abs((pd.Timestamp(t) - tag).days) <= 4:
            ue = z.get("ueberraschung_pct")
    if ue is None or pd.isna(ue):
        return None
    if ue > 0 and pct < 0:
        return "schwäche", f"Zahlen am {tag:%d.%m.} {_z(ue, '+.0f')} % über Erwartung, der Kurs fiel {_z(pct, '+.1f')} % (Käufer erschöpft)"
    if ue < 0 and pct >= 0:
        return "stärke", f"Zahlen am {tag:%d.%m.} {_z(ue, '+.0f')} % unter Erwartung, der Kurs hielt {_z(pct, '+.1f')} % (Nachfrage trägt)"
    if ue > 0 and pct >= 3:
        return "stärke", f"Zahlen am {tag:%d.%m.} {_z(ue, '+.0f')} % über Erwartung, der Kurs stieg {_z(pct, '+.1f')} %"
    if ue < 0 and pct <= -3:
        return "schwäche", f"Zahlen am {tag:%d.%m.} {_z(ue, '+.0f')} % unter Erwartung, der Kurs fiel {_z(pct, '+.1f')} %"
    return None


# ── Wertzone wandert (Market Profile) ─────────────────────────────────────────────────────────────────────────────
def wertzone(tage, df=None):
    """tage: Tagesprofile des Market Profile (erkennung.mp_von(df)["tage"], chronologisch, je Tag mit poc). Nur in der
    Seitwärtszone (Schluss in 10 Tagen höchstens ±4 %): Wandert dort der akzeptierte Wert, kündigt sich das
    Ungleichgewicht an – im Trend sagt das nichts Neues."""
    if not tage or len(tage) < 10:
        return None
    if df is not None and len(df) > 11 and abs(float(df["Close"].iloc[-1] / df["Close"].iloc[-11]) - 1) * 100 > SEITWAERTS_PCT:
        return None
    jetzt = np.mean([x["poc"] for x in tage[-5:]])
    vorher = np.mean([x["poc"] for x in tage[-10:-5]])
    d = (jetzt / vorher - 1) * 100
    if d >= WERT_WANDERT_PCT:
        return "stärke", f"Wert wandert nach oben (POC 5 Tage {_z(d, '+.1f')} %)"
    if d <= -WERT_WANDERT_PCT:
        return "schwäche", f"Wert wandert nach unten (POC 5 Tage {_z(d, '+.1f')} %)"
    return None


# ── Kreislauf ─────────────────────────────────────────────────────────────────────────────────────────────────────
def kreislauf(df, idx=None, gewinne=None, tage30=None, fehlausbruch=None, start=None):
    """Phase, Wechsel und Zeichen eines Titels → dict mit
    phase (1–4), wort („4 → 1“, „2 · Einquetschung“), satz (fester Satz aus den Zeichen), staerke/schwaeche (Listen),
    dow_tag, dow_woche, einquetschung, akkumulation, relativ, trend, kurve (52 Wochenschlüsse), phasen (52 Phasen)."""
    import phase as phase_mod
    if df is None or len(df) < 300:
        return None
    ph = phase_mod.phasen(df)
    w = wochenkerzen(df)
    ph = ph.reindex(w.index).ffill().fillna(1).astype(int)
    # Phase wie erkennung._phase_von (Karte, Weinstein-Zeichen): die laufende Woche zählt erst ab ihrem Freitag
    p = int(ph[ph.index <= df.index[-1]].iloc[-1]) if (ph.index <= df.index[-1]).any() else int(ph.iloc[0])
    ph.iloc[-1] = p
    dt, dw = dow(df, 5), dow(w, 2)
    eq = einquetschung(df)
    ak = akkumulation(df)
    rel = relativ(df, idx, start) if idx is not None else None
    re_ = reaktion(df, gewinne) if gewinne is not None else None
    wz = wertzone(tage30, df)
    st, sw = [], []
    for d_ in (dt, dw):
        if d_ and d_.get("signal"):
            txt = d_["signal"] + (" (Woche)" if d_ is dw else "")
            if d_ is dw and dt and dt.get("signal") == d_["signal"]:
                continue                                          # Tag und Woche sagen dasselbe
            (st if d_["richtung"] == "stärke" else sw).append(txt)
    if eq:
        (st if eq["art"] == "aufsteigend" else sw).append(
            f"Einquetschung: {'steigende Tiefs unter der Oberkante ' + _z(eq['oberkante'], '.2f') if eq['art'] == 'aufsteigend' else 'fallende Hochs über der Unterkante ' + _z(eq['unterkante'], '.2f')} $")
    if ak:
        if ak["bild"] == "Akkumulation":
            st.append(f"Akkumulation: {ak['kauftage']} Kauftage gegen {ak['abgabetage']} Abgabetage mit Volumen (20 Tage)")
        elif ak["bild"] == "Distribution":
            sw.append(f"Distribution: {ak['abgabetage']} Abgabetage gegen {ak['kauftage']} Kauftage mit Volumen (20 Tage)")
        if ak["pocket_pivot"]:
            st.append(f"Pocket Pivot am {ak['pocket_pivot']}")
    if rel:
        st += rel["staerke"]
        sw += rel["schwaeche"]
    for x in (re_, wz):
        if x:
            (st if x[0] == "stärke" else sw).append(x[1])
    if fehlausbruch:
        sw.append(fehlausbruch)
    # Wechsel: frühe Zeichen an der Phasengrenze
    ziel = None
    dow_st = "stärke" in ((dt or {}).get("richtung"), (dw or {}).get("richtung"))
    dow_sw = "schwäche" in ((dt or {}).get("richtung"), (dw or {}).get("richtung"))
    rel_st = bool(rel and rel["staerke"])
    if p == 4 and (dow_st or rel_st) and len(st) >= 2 and len(st) > len(sw):
        ziel = 1                                    # das Angebot weicht: Struktur dreht oder hält gegen den Markt
    elif p == 1 and ((eq and eq["art"] == "aufsteigend") or ((dt or {}).get("struktur") == "aufwärts" and len(st) >= 2
                                                              and len(st) > len(sw))):
        ziel = 2
    elif p == 2 and dow_sw and len(sw) >= 2 and len(sw) > len(st):
        ziel = 3
    elif p == 3 and ((dw or {}).get("struktur") == "abwärts" or dow_sw) and len(sw) >= 2 and len(sw) > len(st):
        ziel = 4
    wort = f"{p} → {ziel}" if ziel else str(p)
    if eq:
        wort += " · Einquetschung"
    tq = trendqualitaet(df)
    satz = f"Phase {p} ({PHASE_NAME[p]})"
    if ziel:
        satz += f", Wechsel zu Phase {ziel} ({PHASE_NAME[ziel]}) zeichnet sich ab"
    if st:
        satz += " · Stärke: " + "; ".join(st[:3])
    if sw:
        satz += " · Schwäche: " + "; ".join(sw[:3])
    kurve = w["Close"].iloc[-52:]
    return {"phase": p, "ziel": ziel, "wort": wort, "satz": satz, "staerke": st, "schwaeche": sw,
            "dow_tag": dt, "dow_woche": dw, "einquetschung": eq, "akkumulation": ak, "relativ": rel, "trend": tq,
            "kurve": [round(float(x), 2) for x in kurve], "phasen": [int(x) for x in ph.iloc[-52:]],
            "kurve_von": f"{kurve.index[0]:%d.%m.%Y}", "kurve_bis": f"{df.index[-1]:%d.%m.%Y}"}


# ── Speicher: der Frühlauf rechnet den Kreislauf aller Titel mit dem Kartentisch (daten/kreislauf/<stand>.json) ───
import os  # noqa: E402

SPEICHER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "daten", "kreislauf")
_START, _GELADEN = {}, {}


def startdatum(idx):
    """korrekturbeginn() einmal je Indextag (die Marktrichtung lädt die Indizes); KEIN, wenn der Markt nicht schwach ist."""
    schl = (len(idx), idx.index[-1])
    if schl not in _START:
        _START.clear()
        _START[schl] = korrekturbeginn(idx)
        if _START[schl] is None:
            _START[schl] = KEIN
    return _START[schl]


def fuer_titel(tk, df, idx, gewinne=None, start=None, mit_wertzone=True, fehlausbruch=None):
    """kreislauf() mit Index-Bezug und – wenn gespeichert – 30-Minuten-Kerzen; None bei zu kurzer Reihe."""
    if df is None or len(df) < 300 or idx is None:
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
        for x in ("dow_tag", "dow_woche"):
            if k.get(x):
                k[x] = {a: b for a, b in k[x].items() if a in ("struktur", "signal", "richtung")}
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
