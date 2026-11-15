"""Anchored VWAP nach Brian Shannon und die Anker des Volumenprofils nach James Dalton – eine Quelle für Chart,
Lagekarte und Zustand. Grundsatz (Micky 13.11.2026: „Die Verankerung ist extrem wichtig – falsch verankert führen beide
zu falschen Annahmen“): Anker nur aus Ereignis und Struktur, nie aus dem Kalender.

Neu am 14.11.2026 nach den Meistern (LUV: das alte „Hoch der 52 Wochen“ hing am 17.02., das Tief am 02.04. – beide aus
einem Zyklus, der im April endete; die Linien lagen flach und sagten nichts über den laufenden Schub):
  Shannon: Ein Hoch wird erst zum Anker, wenn der Rückgang danach zeigt, dass es wichtig war („Nobody knew it was the
  high at that point … after it broke down … that's when we set that anchor“). Anker: das Pivot-Hoch bzw. -Tief, das
  einen Trend gestartet hat, das jüngste große Hoch, der Tag der Zahlen; mehrere übereinander. Stopp unter dem
  jüngsten relevanten höheren Tief.
  Dalton: Der Markt geht von Balance zu Balance; die Balance erkennt man an überlappendem Wert, das Profil fasst sie
  zusammen.

  hoch      letztes Hoch: das jüngste Hoch, das der Kurs seitdem nicht überschritten hat und das bestätigt ist – durch
            einen Rückgang von mindestens 8 % danach (Micky 14.11.2026, sonst kam der Anker bis zu 2 Wochen zu spät)
            oder als Schwunghoch der Wochenkerzen (n = 2). Steht der Kurs über allen, das letzte Schwunghoch (der
            Ausbruchspunkt). Ohne Schwunghoch: das höchste Hoch (bis 2 Jahre, nicht am Rand).
  tief      Tief der Bewegung = das Tief, an dem der Trend begann, der zum letzten Hoch führte (Shannon: „the pivot low
            that launched the trend“; Micky 14.11.2026: nur dieses, kein Rücksetzer-Tief): das tiefste Tief zwischen dem
            früheren, höheren Hoch (dem Gipfel davor; ohne ihn 52 Wochen zurück, liegt das Tief am Rand des Fensters, bis 2 Jahre) und dem letzten Hoch. Fiel der
            Kurs seitdem darunter, ist der Trend gebrochen: dann das tiefste Tief seit dem letzten Hoch, wenn der Kurs
            mindestens 1 ATR darüber steht und es nicht von heute ist (sonst hat keine Bewegung begonnen).
  gipfel    Hoch des Rückgangs: das höchste bestätigte Hoch der letzten 2 Jahre, das der Kurs seitdem nicht
            überschritten hat – der Gipfel, von dem die ganze Korrektur ausging (14.11.2026, vorher schied es aus, wenn der
            Kurs danach tiefer fiel als seit dem letzten Hoch). Nur, wenn es nicht das letzte Hoch ist.
  ereignis  die Neubewertung (Shannon: Zahlen, Lücke, große Nachricht): der jüngste von Zahlentag (jeder, gleich wie stark
            die Reaktion – 14.11.2026, vorher ab 3 %), Lücke ab 4 % und Volumenspitze (mindestens doppeltes 50-Tage-Volumen bei einer Bewegung
            ab 3 % – ein Tag mit viel Volumen und ohne Bewegung, etwa eine Indexanpassung, ist kein Ereignis), höchstens
            6 Monate zurück (Micky 14.11.2026; vorher nur Lücken mit doppeltem Volumen).
Letztes Hoch und Tief zusammen sind Shannons Zange („Pinch“).
Volumenprofil (profil_anker): grau ab dem Beginn der laufenden Balance nach Dalton – dem ersten Tag, ab dem sich die
Tagesspannen überlappen (balance_beginn; Micky 14.11.2026, vorher ab der Wertzone des Market Profile, also immer an einem
Montag, mit Trendtagen und Lücken im Profil). Ist die laufende Balance kürzer als 2 Wochen (der Wert wandert seit
wenigen Tagen), ab dem Beginn der Balance davor; gibt es keine, ab der Zone des Scanners, sonst ab dem Tief der
Bewegung. Mauer: Knoten über dem Kurs im Profil ab dem Gipfel (sonst ab dem letzten
Hoch); Stütze: Knoten unter dem Kurs im Profil ab dem Tief der Bewegung.
Bis 14.11.2026: Hoch = höchstes Hoch der 52 Wochen, grau = der jüngere von Zone und Ereignis."""
import numpy as np
import pandas as pd

LUECKE, VOLUMEN_FACH = 0.04, 2.0
RAND = 5                      # ein Extrem in den ersten 5 Tagen des Fensters ist kein Anker, sondern der Rand
TIEF_ATR = 1.0                # Tief der Bewegung: der Kurs steht mindestens 1 ATR darüber – sonst hat keine Bewegung begonnen
PROFIL_MIN_TAGE = 10          # Profil mindestens 2 Wochen
WOCHEN_N = 2                  # Schwunghoch der Wochenkerzen: höher als je 2 Wochen davor und danach
TREND_FENSTER = 252           # ohne früheres, höheres Hoch: Start des Trends höchstens 52 Wochen vor dem letzten Hoch
WOCHE_TAGE = 5                # ein Hoch der 8-%-Regel ist zugleich das höchste der Woche davor (Gipfel, keine Stufe)
HOCH_RUECKGANG = 0.08         # ein Hoch ist bestätigt, sobald der Kurs 8 % darunter fiel (Micky 14.11.2026)
SPITZE_BEWEGUNG = 0.03        # Volumenspitze zählt als Ereignis erst mit einer Bewegung ab 3 % (Schluss zu Schluss)
BALANCE_BLOCK = 5             # Balance: in Blöcken zu 5 Tagen zurück (eine Rotation dauert oft eine Woche)
BALANCE_FEHL = 2              # höchstens 2 Blöcke in Folge ohne Überlappung (Rotation zum Rand), dann Ende
BALANCE_MAX = 65 * 5          # höchstens 65 Wochen zurück


def _echt(reihe, art, fenster, bis=None):
    """Position des echten Extrems (art "max"/"min") in den letzten `fenster` Tagen vor `bis` – liegt es am Rand, wird
    das Fenster bis auf 2 Jahre verlängert."""
    n = len(reihe) if bis is None else bis
    for f in (fenster, fenster + 126, fenster + 252, 504):
        lo = max(0, n - f)
        seg = reihe[lo:n]
        if not len(seg):
            return None
        i = lo + int(np.argmax(seg) if art == "max" else np.argmin(seg))
        if i - lo >= RAND or lo == 0:
            return i
    return i


def zahlentag(df, gewinne):
    """Reaktionstag der jüngsten Zahlen als Datum oder None – jeder Zahlentag, gleich wie stark die Reaktion (Shannon,
    Micky 14.11.2026, Chart-Prüfer Lauf 3: vorher erst ab 3 %, sonst saß der Anker auf einem älteren Ereignis; die
    Schwelle von 3 % gilt weiter für das Setup Zahlen-Reaktion)."""
    try:
        import zahlen_reaktion
        rt = zahlen_reaktion.reaktionstag(df, gewinne)
    except Exception:  # noqa: BLE001
        return None
    if rt:
        return df.index[rt[0]]
    return None


def _wochen_hochs(df):
    """Schwunghochs der Wochenkerzen (n = 2) als [(Tag des Hochs in der Woche, Preis)]."""
    import zeichen
    w = zeichen.wochenkerzen(df)
    # nur fertige Wochen bestätigen ein Schwunghoch (Chart-Prüfer Lauf 4: frische Hochs ohne 2 fertige Wochen danach)
    w = w[w.index <= df.index[-1]]
    hochs, _ = zeichen.schwungpunkte(w["High"].to_numpy(float), w["Low"].to_numpy(float), WOCHEN_N)
    aus = []
    for i, p in hochs:
        ende = w.index[i]
        teil = df[(df.index > ende - pd.Timedelta(days=7)) & (df.index <= ende)]
        if len(teil):
            aus.append((teil["High"].idxmax(), float(p)))
    return aus


def anker(df, zahltag=None):
    """{"hoch"|"tief"|"gipfel"|"ereignis": Tag} aus Tageskerzen (fehlt ein Anker, fehlt der Schlüssel). zahltag:
    Reaktionstag der Zahlen (zahlentag()), wenn bekannt."""
    if df is None or len(df) < 30 or not {"High", "Low", "Close", "Volume"} <= set(df.columns):
        return {}
    h, l = df["High"], df["Low"]
    n = len(df)
    hv, lv = h.to_numpy(float), l.to_numpy(float)
    wh = _wochen_hochs(df)
    offen = {d: p for d, p in wh if not (h[h.index > d] > p).any()}     # seitdem nicht überschritten
    suf_max = np.maximum.accumulate(hv[::-1])[::-1]
    suf_min = np.minimum.accumulate(lv[::-1])[::-1]
    for i in range(max(0, n - 504), n - 1):                            # bestätigt durch 8 % Rückgang danach
        if (hv[i] >= suf_max[i] and hv[i] >= hv[max(0, i - WOCHE_TAGE):i + 1].max()     # ein echter Gipfel, keine
                and suf_min[i + 1] <= hv[i] * (1 - HOCH_RUECKGANG)):                     # Stufe im Fall

            offen.setdefault(df.index[i], float(hv[i]))
    offen = sorted(offen.items())
    if offen:
        hoch = offen[-1][0]
    elif wh:
        hoch = wh[-1][0]                                                   # Kurs über allen: der Ausbruchspunkt
    else:
        hoch = df.index[_echt(hv, "max", 252)]
    aus = {"hoch": hoch}
    if not offen:                    # sichtbar machen (Chart-Prüfer Lauf 4): kein Hoch steht mehr über dem Kurs
        aus["ausbruchspunkt"] = True
    t_ = _trendstart(df, hoch)
    if t_ is not None:
        aus["tief"] = t_
    # Hoch des Rückgangs = der Gipfel, von dem die ganze Korrektur ausging: das höchste bestätigte Hoch, das der Kurs
    # seitdem nicht überschritten hat (Chart-Prüfer 14.11.2026, KBH/BAX/ORA: vorher schied jedes Hoch aus, nach dem der
    # Kurs tiefer fiel als seit dem letzten Hoch – lag das letzte Hoch nach dem Tief, blieb nur das letzte Hoch selbst)
    kand = [(p, d) for d, p in offen if d >= df.index[max(0, n - 504)]]
    if kand:
        g = max(kand)[1]
        if g != hoch:
            aus["gipfel"] = g
    grenze = df.index[max(0, n - 126)]
    tage = []
    if "Open" in df.columns:
        d = df.iloc[-126:]
        vol50 = df["Volume"].rolling(50).mean().shift(1).reindex(d.index)
        luecke = (d["Open"] / df["Close"].shift(1).reindex(d.index) - 1).abs()
        bewegung = (d["Close"] / df["Close"].shift(1).reindex(d.index) - 1).abs()
        tage = list(d.index[(luecke >= LUECKE) | ((d["Volume"] >= VOLUMEN_FACH * vol50) & (bewegung >= SPITZE_BEWEGUNG))])
    if zahltag is not None and pd.Timestamp(zahltag) >= grenze:
        tage.append(pd.Timestamp(zahltag))
    if tage:
        aus["ereignis"] = max(tage)
    return aus


def _trendstart(df, hoch):
    """Tag des Tiefs, an dem der Trend begann, der zum letzten Hoch führte (Shannon), oder None – siehe oben (tief)."""
    h, l = df["High"], df["Low"]
    hp = float(h[hoch])
    vorher = h[(h.index < hoch) & (h > hp)]                    # das frühere, höhere Hoch (der Gipfel davor)
    if len(vorher):
        lauf = l[(l.index >= vorher.index[-1]) & (l.index <= hoch)]
        start = lauf.idxmin() if len(lauf) else None
    else:                                                      # ohne: 52 Wochen, liegt das Tief am Rand, weiter zurück
        i = _echt(l.to_numpy(float), "min", TREND_FENSTER, bis=df.index.get_loc(hoch) + 1)
        start = df.index[i] if i is not None else None
    if start is not None and not (l[l.index > start] < float(l[start])).any():
        return start                                           # der Trend steht noch über seinem Start
    seit = l[l.index >= hoch]                                  # Trend gebrochen: die neue Bewegung seit dem Hoch
    tag = seit.idxmin()
    import atr as atr_
    atr = atr_.wert(df) or float((h - l).iloc[-14:].mean())      # die eine ATR der App
    if tag != df.index[-1] and float(df["Close"].iloc[-1]) >= float(seit.min()) + TIEF_ATR * atr:
        return tag
    return None


def balance_beginn(df, bis=None):
    """Erster Tag der Balance nach Dalton (überlappender Wert), die am Tag `bis` (Position, Vorgabe: heute) läuft, als
    Position oder None. Von `bis` in Blöcken zu 5 Tagen zurück: ein Block gehört dazu, wenn seine Spanne den Kern der
    Balance berührt (mittlere Hälfte der typischen Preise der Tage, die schon dazugehören). Höchstens BALANCE_FEHL Blöcke
    in Folge ohne Berührung (eine Rotation zum Rand und zurück), dann endet die Balance – davor lag ein Trend oder eine
    Lücke. Der Beginn ist der erste Tag des ältesten Blocks, der den Kern berührt."""
    n = len(df) if bis is None else bis + 1
    if n < 2 * BALANCE_BLOCK:
        return None
    hv, lv = df["High"].to_numpy(float)[:n], df["Low"].to_numpy(float)[:n]
    tp = (hv + lv + df["Close"].to_numpy(float)[:n]) / 3
    drin = list(range(n - BALANCE_BLOCK, n))
    fehl, e = 0, n - BALANCE_BLOCK
    while e - BALANCE_BLOCK >= max(0, n - BALANCE_MAX):
        blk = list(range(e - BALANCE_BLOCK, e))
        k0, k1 = np.percentile(tp[drin], [25, 75])
        if lv[blk].min() <= k1 and hv[blk].max() >= k0:
            drin += blk
            fehl = 0
        else:
            fehl += 1
            if fehl > BALANCE_FEHL:
                break
        e -= BALANCE_BLOCK
    k0, k1 = np.percentile(tp[drin], [25, 75])
    i = min(drin)
    while i < n - 1 and not (lv[i] <= k1 and hv[i] >= k0):     # der erste Tag, der den Wert berührt
        i += 1
    return i


def profil_anker(df, zahltag=None, zone_start=None):
    """Anker des Volumenprofils → {"grau": (Tag, Art), "mauer": Tag, "stuetze": Tag} (siehe oben)."""
    a = anker(df, zahltag)
    if not a:
        return {}
    lang = lambda t: t is not None and (df.index >= pd.Timestamp(t)).sum() >= PROFIL_MIN_TAGE   # noqa: E731
    n = len(df)
    bb = balance_beginn(df)
    vor = balance_beginn(df, bb - 1) if bb is not None and n - bb < PROFIL_MIN_TAGE and bb > 0 else None
    if bb is not None and n - bb >= PROFIL_MIN_TAGE:
        grau = (df.index[bb], "Balance")
    elif vor is not None and bb - vor >= PROFIL_MIN_TAGE:   # Wert wandert seit wenigen Tagen: die Balance davor (Dalton:
        #                                                   verlassen erst, wenn der neue Wert angenommen ist)
        grau = (df.index[vor], "Balance, Wert wandert")
    elif lang(zone_start):
        grau = (pd.Timestamp(zone_start), "Zone")
    else:
        grau = (a.get("tief", a["hoch"]), "Tief" if "tief" in a else "Hoch")
    return {"grau": grau, "mauer": a.get("gipfel", a["hoch"]), "stuetze": a.get("tief"),
            "hoch": a["hoch"], "tief": a.get("tief")}


def reihe(df, ab):
    """AVWAP ab dem Tag `ab` (typischer Preis × Volumen, aufsummiert) als Reihe; leer, wenn zu wenig Kerzen."""
    t_ = df[df.index >= pd.Timestamp(ab)]
    if len(t_) < 2:
        return pd.Series(dtype=float)
    tp = (t_["High"] + t_["Low"] + t_["Close"]) / 3
    return ((tp * t_["Volume"]).cumsum() / t_["Volume"].cumsum().replace(0, np.nan)).dropna()
