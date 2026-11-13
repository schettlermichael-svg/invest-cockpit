"""Anchored VWAP nach Brian Shannon (10.11.2026) und die Anker des Volumenprofils – eine Quelle für Chart, Lagekarte
und Stab. Grundsatz (Micky 13.11.2026: „Die Verankerung ist extrem wichtig – falsch verankert führen beide zu falschen
Annahmen“): Anker nur aus Ereignis und Struktur, nie aus dem Kalender. Gemessen an 584 Titeln am 13.11.: das alte
„Tief der 6 Monate“ lag bei 16 % am Rand des Fensters (dort begann keine Bewegung), 62 % der Zahlenreaktionen ab 3 %
waren kein Anker.

  hoch      das Hoch, von dem der laufende Fall ausging: höchstes Hoch der 52 Wochen – liegt es am Rand des Fensters,
            wird weiter zurück gesucht (bis 2 Jahre), bis es ein echtes Hoch ist
  tief      das Tief, von dem die laufende Bewegung ausging: das tiefste Tief seit dem Hoch, wenn es mindestens
            10 Handelstage zurückliegt; sonst (der Titel steht am Hoch) das Tief, von dem der Lauf zum Hoch ausging –
            ebenfalls ein echtes Tief, nicht der Rand des Fensters
  ereignis  die Neubewertung: der jüngere von Zahlentag (Reaktion ab 3 %, zahlen_reaktion) und Ereignistag (Lücke ab 4 %
            mit mindestens doppeltem 50-Tage-Volumen), höchstens 6 Monate zurück
Hoch und Tief zusammen sind Shannons Zange („Pinch“): laufen beide Linien eng zusammen, steht eine Entscheidung an.
Volumenprofil (profil_anker): grau ab dem jüngeren von Beginn der Zone und Ereignis (mindestens 5 Handelstage, sonst ab
dem Tief), dazu die Mauer (Knoten seit dem Hoch über dem Kurs) und die Stütze (Knoten seit dem Tief unter dem Kurs)."""
import numpy as np
import pandas as pd

LUECKE, VOLUMEN_FACH = 0.04, 2.0
PINCH_PCT = 3.0
RAND = 5                      # ein Extrem in den ersten 5 Tagen des Fensters ist kein Anker, sondern der Rand
TIEF_MIN_TAGE = 10            # Tief seit dem Hoch zählt als Beginn der Bewegung ab 10 Handelstagen Abstand
PROFIL_MIN_TAGE = 5


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


def anker(df, zahltag=None):
    """{"hoch"|"tief"|"ereignis": Tag} aus Tageskerzen (fehlt ein Anker, fehlt der Schlüssel). zahltag: Reaktionstag
    der Zahlen (zahlentag()), wenn bekannt."""
    if df is None or len(df) < 30 or not {"High", "Low", "Close", "Volume"} <= set(df.columns):
        return {}
    h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
    n = len(df)
    i_h = _echt(h, "max", 252)
    aus = {"hoch": df.index[i_h]}
    i_t = i_h + int(np.argmin(l[i_h:]))
    if n - 1 - i_h < TIEF_MIN_TAGE or i_t == n - 1:   # am Hoch (oder das Tief ist heute): Beginn des Laufs zum Hoch
        i_t = _echt(l, "min", 126, bis=i_h + 1)
    aus["tief"] = df.index[i_t]
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


def profil_anker(df, zahltag=None, zone_start=None):
    """Anker des Volumenprofils → {"grau": (Tag, Art), "hoch": Tag, "tief": Tag}. Grau = der jüngere von Beginn der Zone
    und Ereignis; weniger als 5 Handelstage alt → ab dem Tief der Bewegung."""
    a = anker(df, zahltag)
    if not a:
        return {}
    kand = []
    if zone_start is not None:
        kand.append((pd.Timestamp(zone_start), "Zone"))
    if a.get("ereignis") is not None:
        kand.append((a["ereignis"], "Ereignis"))
    grau = max(kand) if kand else (a["tief"], "Tief")
    if (df.index > grau[0]).sum() < PROFIL_MIN_TAGE:
        grau = (a["tief"], "Tief")
    return {"grau": grau, "hoch": a["hoch"], "tief": a["tief"]}


def reihe(df, ab):
    """AVWAP ab dem Tag `ab` (typischer Preis × Volumen, aufsummiert) als Reihe; leer, wenn zu wenig Kerzen."""
    t_ = df[df.index >= pd.Timestamp(ab)]
    if len(t_) < 2:
        return pd.Series(dtype=float)
    tp = (t_["High"] + t_["Low"] + t_["Close"]) / 3
    return ((tp * t_["Volume"]).cumsum() / t_["Volume"].cumsum().replace(0, np.nan)).dropna()
