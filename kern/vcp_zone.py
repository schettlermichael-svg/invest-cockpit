"""VCP-Scanner, Baustein 1: die Zone, Baustein 2: die Enge am rechten Rand (06.11.2026).

Seit 25.11.2026 (Micky: „konsequent wäre die Umstellung auf Livermore“) ist Livermores Notizbuch die Grundlage für
Base und Pivot (livermore.spanne); Minervinis Wellen sind die Reife-Zeichen dieser Spanne. O'Neils und Minervinis Pivot
stammt von Livermores Pivotal Point (Fortsetzungs-Pivotal-Point). Die Formregeln der alten Zone (Mindestdauer 3 Wochen,
höchstens 65 Wochen und 50 % tief, Erholung in die obere Hälfte, gescheiterte Tasse, flache Base, Minervinis Drittel und
Cheats) sind damit entfernt – Livermore filtert mit Bestätigung, Volumen und Key Price.
Wendepunkte über ein ZigZag nach ATR (grob = 2 × ATR 14) – dieselben Schwünge wie im Notizbuch (Livermores ~6 Punkte in
der Schwankung des Titels); die 2 und die 1 ATR sind unsere Zahlen, ungemessen.

  Oberkante  = Kopf der Spanne: im Aufwärtstrend der älteste Pivotal Point oben seit Beginn dieses Aufwärtstrends ohne
               Schluss darüber (die Hochs danach liegen tiefer – alle Wellen der Base bleiben in einer Spanne), im
               Abwärtstrend der letzte Pivotal Point oben (meist das Hoch der natürlichen Erholung)
  Unterkante = tiefstes Tief seit der Oberkante
  Pivot      = der jüngste Pivotal Point oben seit der Oberkante (Livermore Regel 5a), ohne Erholung seitdem die
               Oberkante selbst
  keine Zone = ein Schluss über der Oberkante (Kurs läuft am Hoch) · offen = Livermore schreibt heute in die Spalte
               Abwärtstrend (noch keine Base)
  Länge      = Oberkante bis heute in Wochen · Tiefe = Oberkante bis Unterkante in % (Zeichen, keine Schwellen)

Vorgeschichte (gehört nicht zur Zone, entscheidet den Namen):
  Absturz ↓  = vor der Oberkante stand der Kurs höher (höchstes Hoch der 26 Wochen vor dem Anlauf-Tief über der Oberkante)
  Schub ↑    = sonst: Anstieg vom Anlauf-Tief (tiefstes Tief seit dem letzten Hoch über der Oberkante, höchstens 52 Wochen)
Name:
  Flagge         = Fahnenstange ≥ 30 % in höchstens 13 Wochen (1–3 Monate, Kullamägi), Zone 1–8 Wochen und
                   höchstens 25 % tief; Stange = Anstieg vom tiefsten Tief der 13 Wochen vor der Oberkante, ohne
                   höheres Hoch dazwischen (sonst war es ein Absturz, keine Stange)
  Base           = nach einem Schub, sonst
  Konsolidierung = nach einem Absturz

Baustein 2 – die Enge (Minervini, VCP), nur innerhalb der Zone:
  Kontraktion = die erste ist die linke Seite (Hoch der Zone bis zum tiefsten Tief der Base), danach jede Welle der
                rechten Seite der Reihe nach: grobes Schwunghoch bis zum nächsten Schwungtief (2 × ATR); am rechten
                Rand die letzte, enge ab 1 × ATR; Tiefe in % (14.11.2026, Chart-Prüfer: vorher vom höchsten Hoch nach
                dem letzten Tief – Wellen der rechten Seite fielen weg)
  Tiefe       = Base über 33 % tief (O'Neil: nur im Bärenmarkt) → Ampel nicht grün, steht unter „fehlt“
  Schärfe     = (14.11.2026, Chart-Prüfer Lauf 3) jede Kontraktion mindestens 3 Handelstage; mehr als 6 Wellen ist kein VCP;
                grün nur, wenn das Volumen der Enge unter dem 50-Tage-Schnitt liegt (ausgetrocknet) und nicht in Phase 4
  schrumpfend = grob halbiert: jede höchstens 70 % so tief wie die vorige (Minervinis Faustregel)
  Enge        = die letzte Kontraktion; höchstens 10 % tief (der Pivot ist Livermores Pivotal Point, nicht ihr Hoch)
  Volumen     = Ø Volumen vom Hoch der Enge bis heute (ohne Tage über dem Pivot, am 50-Tage-Schnitt gemessen) leiser als
                in der ersten Kontraktion – das Volumen schrumpft mit den Kontraktionen
  Tiefs       = steigend als Zeichen, keine Pflicht (Shakeout erlaubt)
  Ampel       = grün: mindestens 2 Kontraktionen, schrumpfend, Enge ≤ 10 %, Volumen leiser · rot: die letzte
                Kontraktion ist tiefer als die vorige · gelb: sonst · grau: keine fertige Zone

Ausbruch (06.11.2026): Am Ausbruchstag ist die Zone fertig und verschwindet. Damit Setup und Kaufzone stehen bleiben,
  schaut ausbruch() bis 4 Wochen zurück: Schluss über dem Pivot der Zone vom Vortag. Zone, Enge und Pivot von damals
  gelten weiter – bis 4 Wochen, oder bis sich darüber eine neue Spanne gebildet hat. Bis +5 % über dem Pivot =
  Kaufzone, darüber ausgedehnt. Schluss knapp unter dem Pivot, das Tief des Ausbruchstags hält = 🟡 Rücktest (keine
  Kaufzone, beobachten; 13.11.2026). Schluss unter dem Tief des Ausbruchstags oder mehr als 3 % unter dem Pivot =
  🔴 Fehlausbruch (Zone und Pivot bleiben; neuer Schluss darüber = neuer Ausbruch). Livermores Bestätigung: ein Hoch
  1 ATR über dem Pivot (Zeichen).
  Zeichen (kein Muss, Micky): Volumen am Ausbruchstag über dem 50-Tage-Schnitt = mit Volumen.
"""
import numpy as np
import pandas as pd
from masse import VOL_MIN_TAGE, WOCHE  # noqa: E402

ATR_TAGE = 14
GROB = 2.0
FEIN = 1.0
FLAGGE_SCHUB, FLAGGE_STANGE_W, FLAGGE_ZONE_W, FLAGGE_TIEFE = 0.30, 6, 8, 0.25
# Kullamägi: ein großer Anstieg (30–100 %) in den letzten 1–3 Monaten, der „ein paar Tage bis ein paar Wochen“ dauert –
# der Mast höchstens 6 Wochen (Micky 16.11.2026; vorher 13 Wochen: die 3 Monate sagen, wann der Mast war, nicht wie lang
# er dauern darf – WST stieg 13 Wochen stufenweise und hieß Flagge); die Flagge kürzer als ihr Mast (klassische Lehre)
FLAGGE_TIEF_ATR = 0.5     # Flagge: das Tief der zweiten Hälfte darf bis 0,5 ATR unter dem der ersten liegen (Shakeout)


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
VOR_WOCHEN = 52         # Vorgeschichte: Anstieg in den 52 Wochen vor der Oberkante
VOR_TIEF_WOCHEN = 26    # … Tief der 26 Wochen davor
FLAGGE_MIN_TAGE = 4     # Tiefs der Flagge erst ab 4 Tagen vergleichbar
NEUES_HOCH_TAGE = 5     # Ausbruch nur an einem Tag mit Schluss über den 5 Schlüssen davor
MIN_DATEN = 80          # Ausbruch/Ermüdung ab 80 Handelstagen Daten


def atr(df, n=ATR_TAGE):
    """Die eine ATR der App (atr.reihe)."""
    import atr as atr_
    return atr_.reihe(df, n)


def zigzag(df, faktor):
    """Wendepunkte [(i, preis, 'H'|'T')] nach ATR: ein Extrem gilt, sobald der Kurs faktor × ATR (am Extrem)
    dagegen gelaufen ist. Der letzte, noch unbestätigte Extrempunkt wird angehängt."""
    h, l = df["High"].to_numpy(), df["Low"].to_numpy()
    a = atr(df).to_numpy()
    punkte = []
    richtung = 0
    ext_i = 0
    for i in range(1, len(df)):
        if richtung == 0:                    # Start: erste Bewegung von faktor × ATR entscheidet
            hi = int(np.argmax(h[:i + 1]))
            lo = int(np.argmin(l[:i + 1]))
            if h[i] - l[lo] >= faktor * a[lo] and lo < i:
                punkte.append((lo, l[lo], "T"))
                richtung, ext_i = 1, i
            elif h[hi] - l[i] >= faktor * a[hi] and hi < i:
                punkte.append((hi, h[hi], "H"))
                richtung, ext_i = -1, i
            continue
        if richtung == 1:
            if h[i] >= h[ext_i]:
                ext_i = i
            elif h[ext_i] - l[i] >= faktor * a[ext_i]:
                punkte.append((ext_i, h[ext_i], "H"))
                richtung, ext_i = -1, i
        else:
            if l[i] <= l[ext_i]:
                ext_i = i
            elif h[i] - l[ext_i] >= faktor * a[ext_i]:
                punkte.append((ext_i, l[ext_i], "T"))
                richtung, ext_i = 1, i
    if richtung:
        punkte.append((ext_i, h[ext_i] if richtung == 1 else l[ext_i], "H" if richtung == 1 else "T"))
    return punkte


def secondary(punkte):
    """Livermores Secondary (How to Trade in Stocks, 1940): Wendepunkte ohne neues Extrem – ein Hoch unter dem vorigen
    Hoch (Secondary Rally), ein Tief über dem vorigen Tief (Secondary Reaction). → Menge der Indizes in punkte."""
    aus, letzt = set(), {}
    for k, (_, p_, art) in enumerate(punkte):
        if art in letzt and ((p_ < letzt[art]) if art == "H" else (p_ > letzt[art])):
            aus.add(k)
        letzt[art] = p_
    return aus


def _vorgeschichte(df, top_i, top):
    h, l = df["High"].to_numpy(), df["Low"].to_numpy()
    start = max(0, top_i - VOR_WOCHEN * WOCHE)
    hoeher = np.where(h[start:top_i] > top)[0]
    von = start + (hoeher[-1] + 1 if len(hoeher) else 0)
    if von >= top_i:
        von = max(0, top_i - 1)
    tief_i = von + int(np.argmin(l[von:top_i + 1]))
    tief = l[tief_i]
    vor = max(0, tief_i - VOR_TIEF_WOCHEN * WOCHE)
    if tief_i > vor:
        hoch_i = vor + int(np.argmax(h[vor:tief_i]))
        if h[hoch_i] > top:
            return {"art": "Absturz", "pfeil": "↓", "prozent": (tief / h[hoch_i] - 1) * 100,
                    "wochen": (tief_i - hoch_i) / WOCHE, "von_i": hoch_i, "bis_i": tief_i,
                    "von": h[hoch_i], "bis": tief}
    return {"art": "Schub", "pfeil": "↑", "prozent": (top / tief - 1) * 100, "wochen": (top_i - tief_i) / WOCHE,
            "von_i": tief_i, "bis_i": top_i, "von": tief, "bis": top}


def zone(df, nb=None):
    """Zone am rechten Rand nach Livermores Notizbuch (Micky 25.11.2026: Livermore ist die Grundlage für Base und
    Pivot; livermore.spanne) oder {"zone": False, "grund": …}. Oberkante = der Kopf der Spanne (im Aufwärtstrend der
    älteste Pivotal Point oben dieses Trends ohne Schluss darüber, im Abwärtstrend der letzte), Unterkante = tiefstes Tief
    seitdem, Pivot = der jüngste Pivotal Point oben seit dem Kopf. Liegt ein Schluss über dem Kopf, läuft der Kurs am
    Hoch (keine Spanne); schreibt Livermore heute in die Spalte Abwärtstrend, ist die Zone offen (noch keine Base).
    nb = livermore.notizbuch über ein df, das mit diesem beginnt (auch länger: es zählt nur, was bis heute im Buch stand)."""
    import livermore
    df = df.dropna(subset=["High", "Low", "Close"])
    if len(df) < 60:
        return {"zone": False, "grund": "zu wenig Kurse"}
    c = df["Close"].to_numpy()
    n = len(df)
    sp = livermore.spanne(nb if nb is not None else livermore.notizbuch(df), n, c)
    if not sp:
        return {"zone": False, "grund": "noch kein Pivotal Point oben im Notizbuch – Kurs läuft am Hoch"}
    i, top = sp["kopf"]["i"], float(sp["kopf"]["preis"])
    if i < n - 1 and c[i + 1:].max() > top:
        return {"zone": False, "grund": "Schluss über dem letzten Pivotal Point oben – Kurs läuft am Hoch, keine Spanne"}
    k = _rahmen(df, i, top)
    k.update(pivot=float(sp["pivot"]["preis"]), pivot_i=sp["pivot"]["i"], spalte=sp["spalte"], trend=sp["trend"],
             kopf_aus=sp["kopf"]["aus"])
    if sp["spalte"] == "AB":                     # Livermore schreibt rot in den Abwärtstrend: noch keine Base
        return {"zone": False, "offen": True, "grund": "Abwärtstrend (Livermore schreibt in rot) – noch keine Base",
                **{x: k[x] for x in ("start_i", "start", "oben", "unten", "tief_i", "tief_datum", "wochen", "tiefe",
                                     "abstand", "pivot", "pivot_i", "spalte", "trend", "kopf_aus")}}
    return k


def _stange(df, i, top):
    """Fahnenstange: Anstieg vom tiefsten Tief der 6 Wochen vor der Oberkante (FLAGGE_STANGE_W), ohne höheres Hoch dazwischen – und
    direkt vor der Flagge (Micky 15.11.2026, Chart-Prüfer Lauf 4: die Stange kam aus einem Lauf, der Monate
    zurücklag): gab es in diesen Wochen einen Rücksetzer tiefer als eine Flagge sein darf (25 %), beginnt die Stange
    erst an dessen Tief."""
    h, l = df["High"].to_numpy(), df["Low"].to_numpy()
    s0 = max(0, i - FLAGGE_STANGE_W * WOCHE)
    hm, tief_ab = h[s0], s0
    for j in range(s0, i + 1):
        hm = max(hm, h[j])
        if l[j] <= hm * (1 - FLAGGE_TIEFE):
            tief_ab, hm = j, h[j]                    # tiefer Rücksetzer: die Stange beginnt frühestens hier
    si = tief_ab + int(np.argmin(l[tief_ab:i + 1]))
    sauber = h[si:i].max() <= top if i > si else False
    return {"prozent": (top / l[si] - 1) * 100, "wochen": (i - si) / WOCHE, "von_i": si, "von": l[si], "sauber": sauber}


def tiefs_fallen(df, i, bis=None):
    """Fallen die Tiefs einer Flagge ab Index i (bis heute bzw. bis `bis`)? Das tiefste Tief der zweiten Hälfte liegt
    mehr als FLAGGE_TIEF_ATR unter dem der ersten (Kullamägi: steigende Tiefs; Micky 14./15.11.2026) → (fallen,
    tief1, tief2) oder None bei weniger als 4 Tagen."""
    l = df["Low"].to_numpy(float)
    e = (len(df) - 1) if bis is None else bis
    if e - i + 1 < FLAGGE_MIN_TAGE:
        return None
    m = i + (e - i + 1) // 2
    t1, t2 = l[i:m].min(), l[m:e + 1].min()
    return t2 < t1 - FLAGGE_TIEF_ATR * float(atr(df).iloc[e]), t1, t2


def _rahmen(df, i, top):
    """Zone ab der Oberkante (Index i) bis heute mit Vorgeschichte, Stange und Namen."""
    c, l = df["Close"].to_numpy(), df["Low"].to_numpy()
    n = len(df)
    tief_i = i + int(np.argmin(l[i:]))
    boden = l[tief_i]
    hoehe = top - boden
    wochen = (n - 1 - i) / WOCHE
    v = _vorgeschichte(df, i, top)
    stange = _stange(df, i, top)
    tf = tiefs_fallen(df, i)
    if (stange["sauber"] and stange["prozent"] >= FLAGGE_SCHUB * 100 and wochen <= FLAGGE_ZONE_W
            and wochen < stange["wochen"]                                  # Atempause kürzer als der Angriff
            and hoehe / top <= FLAGGE_TIEFE and not (tf and tf[0])):     # fallende Tiefs: die Truppe weicht – keine Flagge
        name = "Flagge"
    elif v["art"] == "Absturz":
        name = "Konsolidierung"
    else:
        name = "Base"
    return {"zone": True, "name": name, "start_i": i, "start": df.index[i], "oben": top, "unten": boden,
            "tief_i": tief_i, "tief_datum": df.index[tief_i], "wochen": wochen,
            "tiefe": hoehe / top * 100, "abstand": (c[-1] / top - 1) * 100, "vorgeschichte": v, "stange": stange}


SCHRUMPF = 0.70                # jede Kontraktion höchstens 70 % so tief wie die vorige
ENGE_MAX = 10.0                # letzte Kontraktion höchstens 10 % tief
KONTR_MIN_TAGE = 3             # eine Kontraktion dauert mindestens 3 Handelstage (Chart-Prüfer 14.11.2026: 1-Tages-Zucken)
AUF_TIEFE = (10.0, 20.0)       # O'Neil, aufsteigende Base: jeder Rücksetzer 10–20 % tief …
AUF_ZAHL = 3                   # … drei davon nacheinander, jedes Tief und jedes Hoch über dem vorigen
KONTR_MAX = 6                  # Minervini: 2–6 Kontraktionen; mehr Wellen sind Seitwärtsrauschen, kein VCP
BASE_TIEFE_UEBLICH = 33.0          # O'Neil: Tassen 12–33 % tief, tiefer nur im Bärenmarkt (bis 40–50 %); Minervini ähnlich –
                               # tiefer wird gezeigt, die Ampel wird aber nicht grün (Chart-Prüfer 14.11.2026)


def aufsteigende_base(kontr):
    """O'Neils aufsteigende Base (Micky 23.11.2026, WWW): auf der rechten Seite mindestens drei Rücksetzer nacheinander,
    je 10–20 % tief, jedes Tief und jedes Hoch über dem vorigen – die Schwankung wird nicht kleiner, sie wandert nach
    oben (meist in einem schwachen Markt: Stärke in der Schwäche). Die linke Seite (erste Kontraktion) zählt nicht."""
    lauf = 0
    for a_, b in zip([None] + kontr[1:], kontr[1:]):
        passt = AUF_TIEFE[0] <= b["tiefe"] <= AUF_TIEFE[1]
        lauf = (lauf + 1 if a_ is not None and lauf and b["tief"] > a_["tief"] and b["hoch"] > a_["hoch"] else 1) if passt else 0
        if lauf >= AUF_ZAHL:
            return True
    return False


def enge(df, z):
    """Baustein 2: Kontraktionen in der Zone z (aus zone()), Enge, Pivot, Volumen, Ampel.

    Kontraktionen (Minervini): linke Seite bis zum Tief der Base, dann jede Welle der rechten Seite (ZigZag 2 × ATR);
    am rechten Rand zählt die letzte, enge Kontraktion schon ab 1 × ATR. Der Pivot kommt aus der Zone (Livermore)."""
    if not z.get("zone"):
        return {"ampel": "grau", "text": "keine fertige Zone – keine Enge"}
    h, l, c = df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy()
    v = df["Volume"].to_numpy(float)
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().to_numpy()
    a = atr(df).to_numpy()
    n = len(df)

    def vol(i0, i1):
        s50 = np.nanmean(v50[i0:i1 + 1])
        return v[i0:i1 + 1].mean() / s50 * 100 if s50 else np.nan

    def kontraktion(hi, ti):
        return {"hoch_i": hi, "hoch": h[hi], "tief_i": ti, "tief": l[ti], "tiefe": (1 - l[ti] / h[hi]) * 100,
                "volumen": vol(hi, ti)}

    # Minervini: die erste Kontraktion ist die linke Seite – vom Hoch der Zone bis zum tiefsten Tief der Base. Danach
    # zählt jede Welle der rechten Seite der Reihe nach: grobes Schwunghoch bis zum nächsten Schwungtief (ZigZag 2 × ATR).
    # Chart-Prüfer 14.11.2026: vorher lief jede weitere Kontraktion vom höchsten Hoch nach dem letzten Tief – Wellen der
    # rechten Seite dazwischen fielen weg, und am Ende stand oft nur ein Zucken von 1–2 Tagen.
    start, boden_i = z["start_i"], z["tief_i"]
    kontr = [kontraktion(start, boden_i)] if boden_i > start else []
    pkt = [p for p in zigzag(df, GROB) if p[0] > boden_i]
    for p, q in zip(pkt, pkt[1:]):
        if p[2] == "H" and q[2] == "T" and q[0] - p[0] >= KONTR_MIN_TAGE:   # Zucken von 1–2 Tagen zählt nicht
            kontr.append(kontraktion(p[0], q[0]))
    if not pkt and boden_i < n - 1:
        pkt = [(boden_i + 1 + int(np.argmax(h[boden_i + 1:])), None, "H")]
    if pkt and pkt[-1][2] == "H" and pkt[-1][0] < n - 1:  # rechter Rand: die letzte, enge Kontraktion ist oft kleiner als
        hi = pkt[-1][0]                           # 2 × ATR – sie zählt ab 1 × ATR (darunter ist es Rauschen)
        ti = hi + 1 + int(np.argmin(l[hi + 1:]))
        if h[hi] - l[ti] >= FEIN * a[hi] and ti - hi >= KONTR_MIN_TAGE:
            kontr.append(kontraktion(hi, ti))
    if not kontr:
        return {"ampel": "gelb", "zahl": 0, "text": "kein Rücksetzer von 1 × ATR seit der Oberkante", "fehlt": ["keine Kontraktion"]}
    tiefen = [k["tiefe"] for k in kontr]
    schrumpft = all(b <= SCHRUMPF * a_ for a_, b in zip(tiefen, tiefen[1:]))
    groesser = len(tiefen) >= 2 and tiefen[-1] > tiefen[-2]
    letzte = kontr[-1]
    pivot_i, pivot = z["pivot_i"], float(z["pivot"])                 # Livermores Pivotal Point (zone), nicht die Welle
    tage = [i for i in range(letzte["hoch_i"], n) if c[i] <= pivot]  # Volumen der Enge; Tage über dem Pivot zählen nicht
    s50 = np.nanmean(v50[tage]) if tage else np.nan
    vol_enge = v[tage].mean() / s50 * 100 if tage and s50 else np.nan
    vol_erste = kontr[0]["volumen"]               # Minervini: das Volumen schrumpft mit den Kontraktionen
    ruhig = len(kontr) >= 2 and vol_enge == vol_enge and vol_erste == vol_erste and vol_enge < vol_erste
    eng = letzte["tiefe"] <= ENGE_MAX
    flach_genug = z.get("tiefe", 0) <= BASE_TIEFE_UEBLICH
    wenige = len(kontr) <= KONTR_MAX
    trocken = vol_enge == vol_enge and vol_enge < 100          # Minervini: das Volumen trocknet unter den Schnitt aus
    try:
        import phase
        ph = phase.aktuell(df)
    except Exception:  # noqa: BLE001
        ph = None
    tiefs = [k["tief"] for k in kontr]
    steigend = len(tiefs) >= 2 and all(b > a_ for a_, b in zip(tiefs, tiefs[1:]))
    aufsteigend = aufsteigende_base(kontr)
    if len(kontr) >= 2 and schrumpft and eng and ruhig and flach_genug and wenige and trocken and ph != 4:
        ampel = "grün"
    elif groesser:
        ampel = "rot"
    else:
        ampel = "gelb"
    fehlt = ([] if len(kontr) >= 2 else ["erst eine Kontraktion"]) + ([] if schrumpft else ["schrumpft nicht"]) \
        + ([] if eng else [f"Enge {letzte['tiefe']:.1f} % (über {ENGE_MAX:.0f} %)".replace(".", ",")]) \
        + ([] if ruhig or len(kontr) < 2 else ["Volumen nicht leiser als in der ersten Kontraktion"]) \
        + ([] if flach_genug else [f"{z.get('name', 'Zone')} {z['tiefe']:.0f} % tief (über {BASE_TIEFE_UEBLICH:.0f} %, nur im Bärenmarkt üblich, O'Neil)"]) \
        + ([] if wenige else [f"{len(kontr)} Wellen (Minervini: 2–{KONTR_MAX})"]) \
        + ([] if trocken or vol_enge != vol_enge else [f"Volumen der Enge {vol_enge:.0f} % des Schnitts (nicht ausgetrocknet)"]) \
        + ([] if ph != 4 else ["Phase 4 – im Abwärtstrend kein VCP"])
    folge = " → ".join(f"{t:.0f}" for t in tiefen)
    return {"ampel": ampel, "kontraktionen": kontr, "zahl": len(kontr), "folge": folge, "schrumpft": schrumpft,
            "groesser": groesser, "eng": eng, "enge_tiefe": letzte["tiefe"], "pivot_i": pivot_i, "pivot": pivot,
            "trocken": bool(trocken), "wenige": wenige,
            "volumen": vol_enge, "volumen_erste": vol_erste, "ruhig": ruhig, "steigende_tiefs": steigend, "aufsteigend": aufsteigend,
            "fehlt": fehlt,
            "abstand": (c[-1] / pivot - 1) * 100,
            "text": f"{len(kontr)} Kontraktion{'en' if len(kontr) != 1 else ''} {folge} %"
                    + (f" · fehlt: {', '.join(fehlt)}" if fehlt else "")}


RAND_PCT = 3.0              # am Pivot: bis 3 % darunter (Test am Rand) – eine Quelle
AUSBRUCH_TAGE = 20             # Ausbruch gilt bis 4 Wochen, solange kein Schluss unter dem Pivot (Micky, 06.11.2026)
KAUFZONE = 5.0                 # bis 5 % über dem Pivot (Minervini)
FEHL_PCT = 3.0                 # Fehlausbruch: Schluss mehr als 3 % unter dem Pivot (oder unter dem Tief des Ausbruchstags)


def ausbruch(df, tage=AUSBRUCH_TAGE, jetzt=None, nb=None):
    """Ausbruch über den Pivot (Livermores Pivotal Point, zone()) in den letzten `tage` Handelstagen oder None:
    {tag, tage_her, erster_tag, pivot, zone, enge, volumen, mit_volumen, abstand, kaufzone, fehl, fehl_tag, ruecktest,
    rueck_tag, bestaetigt, bestaetigt_tag, bestaetigung, gescheitert: [(Tag des Fehlausbruchs, Hoch des gescheiterten
    Vorstoßes)]}. Zone und Enge so, wie sie am Vortag des ersten Ausbruchs standen (Indizes passen zu df). Schließt der
    Kurs danach wieder unter dem Pivot, ist es ein Fehlausbruch (fehl) – Zone und Pivot bleiben; ein neuer Schluss
    darüber ist ein neuer Ausbruch (tag, volumen von diesem Tag). Hat sich über dem Ausbruch schon eine neue Spanne
    gebildet (jetzt = zone(df), sonst gerechnet), übernimmt sie: None; hat Livermore seit dem Ausbruch einen neuen Pivotal
    Point oben eingetragen, gilt der neue Pivot (ein Ausbruch darüber wird gesucht). Livermores Bestätigung (Regel 5a, seine ~3 Punkte):
    ein Hoch mindestens 1 ATR über dem Pivot seit dem Ausbruchstag – ein Zeichen, keine Pflicht.
    nb = livermore.notizbuch(df), sonst gerechnet."""
    import livermore
    df = df.dropna(subset=["High", "Low", "Close"])
    n = len(df)
    if n < MIN_DATEN:
        return None
    nb = nb if nb is not None else livermore.notizbuch(df)
    c = df["Close"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().shift().to_numpy()
    for t in range(n - tage, n):
        if c[t] <= c[t - NEUES_HOCH_TAGE:t].max():                       # Vorprüfung: ohne neues Schlusshoch kein Ausbruch
            continue
        vor = df.iloc[:t]
        b = zone(vor, nb)
        if not b.get("zone"):
            continue
        pivot = float(b["pivot"])
        if c[t] <= pivot:
            continue
        e = enge(vor, b)
        jz = jetzt if jetzt is not None else zone(df, nb)
        if jz.get("zone") and jz["start_i"] > t:
            return None                                    # neue Spanne über dem Ausbruch
        if jz.get("pivot_i") is not None and jz["pivot_i"] >= t:
            continue                                       # seit dem Ausbruch ein neuer Pivotal Point oben: er gilt
        # Verlauf seit dem Ausbruch (Micky 13.11.2026): Fehlausbruch erst bei Schluss unter dem Tief des
        # Ausbruchstags oder mehr als 3 % unter dem Pivot; knapp unter dem Pivot ist ein Rücktest. Ein Schluss
        # über dem Pivot nach einem Fehlausbruch ist ein neuer Ausbruch (Tag und Volumen von dort).
        letzter, fehl_tag, rueck_tag = t, None, None
        lo, hh = df["Low"].to_numpy(float), df["High"].to_numpy(float)
        gescheitert = []                               # frühere Fehlausbrüche (Micky 24.11.2026): Tag und Hoch
        for u in range(t + 1, n):                      # des gescheiterten Vorstoßes – dort sitzen die Gefangenen
            if c[u] > pivot:
                if fehl_tag is not None:
                    gescheitert.append((df.index[fehl_tag], float(hh[letzter:fehl_tag + 1].max())))
                    letzter = u
                fehl_tag = rueck_tag = None
            elif fehl_tag is None and (c[u] < lo[letzter] or c[u] < pivot * (1 - FEHL_PCT / 100)):
                fehl_tag, rueck_tag = u, None
            elif fehl_tag is None and rueck_tag is None:
                rueck_tag = u
        vol = v[letzter] / v50[letzter] if v50[letzter] == v50[letzter] and v50[letzter] else None
        ab = (c[-1] / pivot - 1) * 100
        fehl = fehl_tag is not None
        bestaetigung = pivot + livermore.BESTAETIGUNG * float(atr(df).iloc[letzter])   # Livermores ~3 Punkte
        ueber = np.flatnonzero(hh[letzter:] >= bestaetigung)
        return {"tag": df.index[letzter], "tage_her": n - 1 - letzter, "erster_tag": df.index[t],
                "vortag_i": t, "pivot": pivot, "zone": b, "enge": e, "volumen": vol,
                "mit_volumen": bool(vol and vol > 1), "abstand": ab, "kaufzone": not fehl and rueck_tag is None and 0 <= ab <= KAUFZONE,
                "fehl": fehl, "fehl_tag": df.index[fehl_tag] if fehl else None,
                "ruecktest": rueck_tag is not None, "rueck_tag": df.index[rueck_tag] if rueck_tag is not None else None,
                "tief_ausbruchstag": float(lo[letzter]), "bestaetigung": bestaetigung,
                "bestaetigt": bool(len(ueber)), "bestaetigt_tag": df.index[letzter + ueber[0]] if len(ueber) else None,
                "gescheitert": gescheitert + (
                    [(df.index[fehl_tag], float(hh[letzter:fehl_tag + 1].max()))] if fehl else [])}
    return None


def ausbruch_text(a):
    """Zeichen für Karte und Plan, z. B. „🟢 Ausbruch am 04.11. mit Volumen 1,35-fach · +2,1 % zum Pivot, in der
    Kaufzone“ oder „🔴 Fehlausbruch: …“."""
    if not a:
        return ""
    k = lambda x: f"{x:.1f}".replace(".", ",")        # noqa: E731
    v = lambda x: f"{x:.2f}".replace(".", ",")       # noqa: E731 – zwei Stellen, damit 1,03 nicht als 1,0 erscheint
    ab = ("±0,0" if round(abs(a["abstand"]), 1) == 0 else f"{'+' if a['abstand'] >= 0 else '−'}{k(abs(a['abstand']))}") \
        + " % zum Pivot"
    if a["fehl"]:
        return (f"🔴 Fehlausbruch: Ausbruch am {a['tag']:%d.%m.}, am {a['fehl_tag']:%d.%m.} unter dem Tief des "
                f"Ausbruchstags bzw. mehr als 3 % unter dem Pivot · {ab} – kein Kauf, bleibt unter Beobachtung, bis der "
                f"Kurs wieder über dem Pivot schließt")
    if a.get("ruecktest"):
        return (f"🟡 Rücktest: Ausbruch am {a['tag']:%d.%m.}, seit {a['rueck_tag']:%d.%m.} knapp unter dem Pivot · {ab} – "
                f"hält das Tief des Ausbruchstags {v(a['tief_ausbruchstag'])} $, ist der Ausbruch nicht gescheitert")
    vol = (f"mit Volumen {v(a['volumen'])}-fach" if a["mit_volumen"] else
           f"ohne Volumen ({v(a['volumen'])}-fach)" if a["volumen"] else "Volumen unbekannt")
    lage = "in der Kaufzone" if a["kaufzone"] else "ausgedehnt"
    best = (f"bestätigt am {a['bestaetigt_tag']:%d.%m.} (Livermore: 1 ATR über dem Pivot)" if a.get("bestaetigt")
            else f"noch nicht bestätigt (Livermore: über {v(a['bestaetigung'])} $)")
    return (f"{'🟢' if a['mit_volumen'] and a.get('bestaetigt') else '🟡'} Ausbruch am {a['tag']:%d.%m.} {vol} · {best} · "
            f"{ab}, {lage}")




SU_TAGE = 10                 # Spring/Upthrust gilt bis 10 Handelstage nach dem Schluss zurück (Micky 15.11.2026)
SU_ZURUECK = 3               # … Schluss zurück in der Zone am Tag selbst oder in den 2 Tagen danach
SU_TIEFE_ATR = 1.0           # … das Tagesextrem höchstens 1 ATR jenseits des Randes (Wyckoff: flacher Spring)


def spring_upthrust(df, tage=SU_TAGE):
    """Spring (long) bzw. Upthrust (short) an der Zone des Scanners – die eine Regel für Zeichen, Zustand und Setup
    (Gefechtsordnung Schritt 4, Micky 14./15.11.2026; Wyckoff). Die Zone gilt, wie sie am Vortag stand: das Tief des Tages
    liegt unter ihrer Unterkante (Upthrust: das Hoch über der Oberkante), höchstens 1 ATR, und ein Schluss am selben Tag
    oder in den 2 Tagen danach liegt wieder in der Zone (ein Fehlausbruch – Schluss jenseits, dann zurück – zählt auch).
    Einstieg beim Schluss zurück in der Zone (Auslöser: der Rand), Stopp am Tief bzw. Hoch des Fehlausbruchs, Ziel der
    andere Rand. Gilt bis `tage` Handelstage nach dem Schluss zurück, solange der Stopp hält und der andere Rand nicht
    erreicht ist (sonst gelb: Zeichen, aber kein Setup mehr). Volumen und Phase sind Zeichen.
    → {art, seite, tag, zurueck_tag, tage_her, einstieg, stopp, ziel, zone, volumen, ampel, regeln, gueltig} oder None."""
    df = df.dropna(subset=["High", "Low", "Close"])
    n = len(df)
    if n < MIN_DATEN:
        return None
    import livermore
    nb = livermore.notizbuch(df)
    lo, hi, c = (df[x].to_numpy(float) for x in ("Low", "High", "Close"))
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().shift().to_numpy()
    a = atr(df).to_numpy(float)
    for i in range(n - 1, max(NEUES_HOCH_TAGE, n - tage - SU_ZURUECK) - 1, -1):     # jüngstes Ereignis zuerst
        neu_tief, neu_hoch = lo[i] < lo[i - NEUES_HOCH_TAGE:i].min(), hi[i] > hi[i - NEUES_HOCH_TAGE:i].max()
        if not (neu_tief or neu_hoch):                       # Vorprüfung: ohne neues Tief bzw. Hoch kein Bruch des Randes
            continue
        z = zone(df.iloc[:i], nb)
        if not z.get("zone"):
            continue
        o, u = float(z["oben"]), float(z["unten"])
        for art, jenseits, tiefe in (("Spring", lo[i] < u, u - lo[i]), ("Upthrust", hi[i] > o, hi[i] - o)):
            if not jenseits or not (a[i] == a[i]) or tiefe > SU_TIEFE_ATR * a[i]:
                continue
            lang = art == "Spring"
            j = next((j for j in range(i, min(i + SU_ZURUECK, n)) if (u < c[j] < o)), None)
            if j is None:
                continue
            stopp = float(lo[i:j + 1].min() if lang else hi[i:j + 1].max())
            einstieg, ziel = (u, o) if lang else (o, u)
            nach_lo, nach_hi = lo[j + 1:], hi[j + 1:]
            gerissen = bool(len(nach_lo) and (nach_lo.min() < stopp if lang else nach_hi.max() > stopp))
            erreicht = bool(len(nach_lo) and (nach_hi.max() >= ziel if lang else nach_lo.min() <= ziel))
            her = n - 1 - j
            gueltig = her <= tage and not gerissen and not erreicht
            vol = v[j] / v50[j] if v50[j] == v50[j] and v50[j] else None
            regeln = [(f"Tief unter der Unterkante {u:.2f}".replace(".", ",") if lang else
                       f"Hoch über der Oberkante {o:.2f}".replace(".", ","), True,
                       f"{df.index[i]:%d.%m.} · {tiefe / a[i]:.1f} ATR jenseits".replace(".", ",")),
                      ("Schluss zurück in der Zone binnen 3 Tagen", True, f"{df.index[j]:%d.%m.} · {c[j]:.2f}".replace(".", ",")),
                      ("Stopp hält", not gerissen, f"{'Tief' if lang else 'Hoch'} des Fehlausbruchs {stopp:.2f}".replace(".", ",")),
                      ("Anderer Rand noch nicht erreicht", not erreicht, f"Ziel {ziel:.2f}".replace(".", ",")),
                      (f"seit dem Schluss zurück höchstens {tage} Tage", her <= tage, f"{her} Tage"),
                      ("Volumen am Schluss zurück über dem Schnitt (Zeichen)", bool(vol and vol > 1),
                       f"{vol:.1f}-fach".replace(".", ",") if vol else "kein Volumen")]
            return {"art": art, "seite": "long" if lang else "short", "tag": df.index[i], "zurueck_tag": df.index[j],
                    "tage_her": her, "einstieg": einstieg, "stopp": stopp, "ziel": ziel, "zone": z, "volumen": vol,
                    "oben": o, "unten": u, "start": z.get("start"),
                    "ampel": "grün" if gueltig else "gelb", "gueltig": gueltig, "regeln": regeln,
                    "tiefe_atr": float(tiefe / a[i])}
    return None






def datiert(df, b):
    """Zone mit Datum zu jedem Index (für den Chart)."""
    ix = df.dropna(subset=["High", "Low", "Close"]).index
    b = dict(b)
    for k_ in ("start_i", "tief_i", "pivot_i"):
        if k_ in b:
            b[k_.replace("_i", "_t")] = ix[b[k_]]
    for k_ in ("vorgeschichte", "stange"):
        if k_ in b:
            b[k_] = dict(b[k_], von_t=ix[b[k_]["von_i"]], **({"bis_t": ix[b[k_]["bis_i"]]} if "bis_i" in b[k_] else {}))
    return b
