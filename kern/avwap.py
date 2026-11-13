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

  hoch      letztes Hoch: das jüngste Schwunghoch der Wochenkerzen (n = 2 – erst zwei Wochen später bestätigt, also
            durch den Rückgang danach), das der Kurs seitdem nicht überschritten hat. Steht der Kurs über allen, das
            letzte Schwunghoch (der Ausbruchspunkt). Ohne Schwunghoch: das höchste Hoch (bis 2 Jahre, nicht am Rand).
  tief      Tief der Bewegung: das tiefste Tief seit diesem Hoch – im Aufwärtstrend das jüngste höhere Tief. Steht der
            Kurs noch nicht mindestens 1 ATR darüber (oder ist das Tief von heute), hat keine Bewegung begonnen: kein Anker.
  gipfel    Hoch des Rückgangs: das höchste nicht überschrittene Schwunghoch der Wochenkerzen, nach dem der Kurs nie
            unter das tiefste Tief seit dem letzten Hoch fiel – der Gipfel, von dem die ganze Korrektur ausging. Nur, wenn es nicht das
            letzte Hoch ist.
  ereignis  die Neubewertung: der jüngere von Zahlentag (Reaktion ab 3 %, zahlen_reaktion) und Ereignistag (Lücke ab 4 %
            mit mindestens doppeltem 50-Tage-Volumen), höchstens 6 Monate zurück.
Letztes Hoch und Tief zusammen sind Shannons Zange („Pinch“).
Volumenprofil (profil_anker): grau ab dem Beginn der laufenden Wertzone des Market Profile (Daltons überlappender
Wert); ist sie jünger als 2 Wochen, ab dem Beginn der vorigen. Ohne 30-Minuten-Kerzen ab dem Beginn der Zone des
Scanners, sonst ab dem Tief der Bewegung. Mauer: Knoten über dem Kurs im Profil ab dem Gipfel (sonst ab dem letzten
Hoch); Stütze: Knoten unter dem Kurs im Profil ab dem Tief der Bewegung.
Bis 14.11.2026: Hoch = höchstes Hoch der 52 Wochen, grau = der jüngere von Zone und Ereignis."""
import numpy as np
import pandas as pd

LUECKE, VOLUMEN_FACH = 0.04, 2.0
RAND = 5                      # ein Extrem in den ersten 5 Tagen des Fensters ist kein Anker, sondern der Rand
TIEF_ATR = 1.0                # Tief der Bewegung: der Kurs steht mindestens 1 ATR darüber – sonst hat keine Bewegung begonnen
PROFIL_MIN_TAGE = 10          # Profil mindestens 2 Wochen
WOCHEN_N = 2                  # Schwunghoch der Wochenkerzen: höher als je 2 Wochen davor und danach
WERT_MIN_WOCHEN = 2           # laufende Wertzone jünger als 2 Wochen: ab der vorigen


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
    """Reaktionstag der jüngsten Zahlen ab 3 % (zahlen_reaktion.REAKTION_PCT) als Datum oder None."""
    try:
        import zahlen_reaktion
        rt = zahlen_reaktion.reaktionstag(df, gewinne)
    except Exception:  # noqa: BLE001
        return None
    if rt and abs(rt[1]) >= zahlen_reaktion.REAKTION_PCT:
        return df.index[rt[0]]
    return None


def _wochen_hochs(df):
    """Schwunghochs der Wochenkerzen (n = 2) als [(Tag des Hochs in der Woche, Preis)]."""
    import zeichen
    w = zeichen.wochenkerzen(df)
    w = w[w.index <= df.index[-1] + pd.Timedelta(days=6)]
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
    wh = _wochen_hochs(df)
    offen = [(d, p) for d, p in wh if not (h[h.index > d] > p).any()]     # seitdem nicht überschritten
    if offen:
        hoch = offen[-1][0]
    elif wh:
        hoch = wh[-1][0]                                                   # Kurs über allen: der Ausbruchspunkt
    else:
        hoch = df.index[_echt(h.to_numpy(float), "max", 252)]
    aus = {"hoch": hoch}
    seit = l[l.index >= hoch]
    tief = seit.idxmin()
    boden = float(l[tief])
    atr = float((df["High"] - df["Low"]).iloc[-14:].mean())
    if tief != df.index[-1] and float(df["Close"].iloc[-1]) >= boden + TIEF_ATR * atr:    # die Bewegung hat begonnen
        aus["tief"] = tief
    kand = [(p, d) for d, p in offen if d <= hoch and not (l[l.index > d] < boden).any()]
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
        tage = list(d.index[(luecke >= LUECKE) & (d["Volume"] >= VOLUMEN_FACH * vol50)])
    if zahltag is not None and pd.Timestamp(zahltag) >= grenze:
        tage.append(pd.Timestamp(zahltag))
    if tage:
        aus["ereignis"] = max(tage)
    return aus


def wert_beginn(mp):
    """Beginn der laufenden Balance nach Dalton aus der Market-Profile-Analyse (erkennung.mp_von): erster Tag der
    laufenden Wertzone, bei weniger als 2 Wochen der vorigen. None ohne Analyse."""
    st = (mp or {}).get("stand") or []
    wochen = (mp or {}).get("wochen") or []
    if not st or not wochen:
        return None
    s = st[-1]
    von = s["von"]
    if s.get("wochen", 0) < WERT_MIN_WOCHEN:
        vor = [x for x in st if x["von"] < von]
        if vor:
            von = vor[-1]["von"]
    return pd.Timestamp(wochen[von]["tag"])


def profil_anker(df, zahltag=None, zone_start=None, wert_start=None):
    """Anker des Volumenprofils → {"grau": (Tag, Art), "mauer": Tag, "stuetze": Tag} (siehe oben)."""
    a = anker(df, zahltag)
    if not a:
        return {}
    if wert_start is not None:
        grau = (pd.Timestamp(wert_start), "Wertzone")
    elif zone_start is not None:
        grau = (pd.Timestamp(zone_start), "Zone")
    else:
        grau = (a.get("tief", a["hoch"]), "Tief" if "tief" in a else "Hoch")
    if (df.index >= grau[0]).sum() < PROFIL_MIN_TAGE:
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
