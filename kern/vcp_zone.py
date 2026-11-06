"""VCP-Scanner, Baustein 1: die Zone, Baustein 2: die Enge am rechten Rand (06.11.2026).

Die Zone ist die ruhige Phase vor dem rechten Rand – die Base im Sinne Minervinis, ohne den Lauf oder Absturz davor.
Alles auf Tageskerzen, Wendepunkte über ein ZigZag nach ATR (grob = 2 × ATR 14).

  Oberkante  = grobes Swing-Hoch, über dem seitdem kein Schlusskurs lag
               (von mehreren solchen das älteste, dessen Zone die Erholungsregel erfüllt)
  Erholung   = nach dem tiefsten Tief kam der Kurs wieder in die obere Hälfte der Zone
               (sonst ist das Hoch der Rand eines Absturzes, nicht einer Base → nächstjüngeres Hoch;
               erfüllt keines die Regel, läuft der Rücksetzer noch: Rahmen ab dem ältesten Hoch, Zone offen)
  Unterkante = tiefstes Tief seit der Oberkante
  Länge      = Oberkante bis heute, 3–65 Wochen (kürzer/länger wird gezeigt, nicht verworfen)
  Tiefe      = Oberkante bis Unterkante in % der Oberkante

Vorgeschichte (gehört nicht zur Zone, entscheidet den Namen):
  Absturz ↓  = vor der Oberkante stand der Kurs höher (höchstes Hoch der 26 Wochen vor dem Anlauf-Tief über der Oberkante)
  Schub ↑    = sonst: Anstieg vom Anlauf-Tief (tiefstes Tief seit dem letzten Hoch über der Oberkante, höchstens 52 Wochen)
Name:
  Flagge         = Fahnenstange ≥ 30 % in höchstens 13 Wochen (1–3 Monate, Kullamägi), Zone 1–8 Wochen und
                   höchstens 25 % tief; Stange = Anstieg vom tiefsten Tief der 13 Wochen vor der Oberkante, ohne
                   höheres Hoch dazwischen (sonst war es ein Absturz, keine Stange)
  Base           = nach einem Schub, sonst
  Konsolidierung = nach einem Absturz
Flagge in der Zone (Kullamägi): liegt in einer Base ein jüngeres ungebrochenes Hoch mit eigener Fahnenstange,
  kommt sie als 'innen' dazu – Minervini sieht die Base, Kullamägi die Flagge

Baustein 2 – die Enge (Minervini, VCP), nur innerhalb der Zone:
  Kontraktion = erste vom Hoch der Zone zum tiefsten Tief danach, jede weitere vom höchsten Hoch nach dem letzten
                Tief zum tiefsten Tief danach (Schicht für Schicht zum rechten Rand); zählt ab 1 × ATR; Tiefe in %
  schrumpfend = grob halbiert: jede höchstens 70 % so tief wie die vorige (Minervinis Faustregel)
  Enge        = die letzte Kontraktion; höchstens 10 % tief; ihr Hoch ist der Pivot
  Volumen     = Ø Volumen vom Pivot bis heute (ohne Tage über dem Pivot, am 50-Tage-Schnitt gemessen) leiser als
                in der ersten Kontraktion – das Volumen schrumpft mit den Kontraktionen
  Tiefs       = steigend als Zeichen, keine Pflicht (Shakeout erlaubt)
  Ampel       = grün: mindestens 2 Kontraktionen, schrumpfend, Enge ≤ 10 %, Volumen leiser · rot: die letzte
                Kontraktion ist tiefer als die vorige · gelb: sonst · grau: keine fertige Zone
"""
import numpy as np
import pandas as pd

ATR_TAGE = 14
GROB = 2.0
FEIN = 1.0
WOCHE = 5
MIN_WOCHEN, MAX_WOCHEN = 3, 65
ERHOLUNG = 0.5                 # Anteil der Zonenhöhe, den der Kurs nach dem Tief zurückgewinnen muss
FLAGGE_SCHUB, FLAGGE_STANGE_W, FLAGGE_ZONE_W, FLAGGE_TIEFE = 0.30, 13, 8, 0.25   # Kullamägi: 30 % in 1–3 Monaten
FLAGGE_MIN_W = 1


def atr(df, n=ATR_TAGE):
    h, l, c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


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


def _vorgeschichte(df, top_i, top):
    h, l = df["High"].to_numpy(), df["Low"].to_numpy()
    start = max(0, top_i - 52 * WOCHE)
    hoeher = np.where(h[start:top_i] > top)[0]
    von = start + (hoeher[-1] + 1 if len(hoeher) else 0)
    if von >= top_i:
        von = max(0, top_i - 1)
    tief_i = von + int(np.argmin(l[von:top_i + 1]))
    tief = l[tief_i]
    vor = max(0, tief_i - 26 * WOCHE)
    if tief_i > vor:
        hoch_i = vor + int(np.argmax(h[vor:tief_i]))
        if h[hoch_i] > top:
            return {"art": "Absturz", "pfeil": "↓", "prozent": (tief / h[hoch_i] - 1) * 100,
                    "wochen": (tief_i - hoch_i) / WOCHE, "von_i": hoch_i, "bis_i": tief_i,
                    "von": h[hoch_i], "bis": tief}
    return {"art": "Schub", "pfeil": "↑", "prozent": (top / tief - 1) * 100, "wochen": (top_i - tief_i) / WOCHE,
            "von_i": tief_i, "bis_i": top_i, "von": tief, "bis": top}


def zone(df):
    """Zone am rechten Rand oder None (dann mit Grund in 'grund')."""
    df = df.dropna(subset=["High", "Low", "Close"])
    if len(df) < 60:
        return {"zone": False, "grund": "zu wenig Kurse"}
    c = df["Close"].to_numpy()
    h, l = df["High"].to_numpy(), df["Low"].to_numpy()
    n = len(df)
    hochs = [p for p in zigzag(df, GROB) if p[2] == "H" and p[0] >= n - MAX_WOCHEN * WOCHE - 1]
    # ungebrochen: seit dem Hoch kein Schluss darüber
    ungebrochen = [p for p in hochs if p[0] < n - 1 and c[p[0] + 1:].max() <= p[1]]
    if not ungebrochen:
        return {"zone": False, "grund": "kein grobes Hoch ohne Schluss darüber in 65 Wochen – Kurs läuft am Hoch"}
    for i, top, _ in sorted(ungebrochen):       # älteste zuerst
        tief_i = i + int(np.argmin(l[i:]))
        boden = l[tief_i]
        hoehe = top - boden
        erholt = h[tief_i:].max() if tief_i < n else boden
        if hoehe <= 0 or erholt >= top - ERHOLUNG * hoehe:
            break
    else:                                       # Rücksetzer läuft: Zone noch nicht fertig, Rahmen trotzdem zeigen
        i, top, _ = sorted(ungebrochen)[0]
        tief_i = i + int(np.argmin(l[i:]))
        return {"zone": False, "grund": "Rücksetzer läuft – seit dem Hoch nicht zurück in der oberen Hälfte, Zone noch offen",
                "offen": True, "start_i": i, "oben": top, "unten": l[tief_i], "tief_i": tief_i,
                "wochen": (n - 1 - i) / WOCHE, "tiefe": (top - l[tief_i]) / top * 100, "abstand": (c[-1] / top - 1) * 100}
    k = _rahmen(df, i, top)
    # Flagge in der Zone (Kullamägi): ein jüngeres ungebrochenes Hoch mit eigener Fahnenstange davor
    for j, top_j, _ in sorted(ungebrochen):
        if j > i:
            f = _rahmen(df, j, top_j)
            if f["name"] == "Flagge":
                k["innen"] = f
                break
    return k


def _stange(df, i, top):
    """Fahnenstange: Anstieg vom tiefsten Tief der 13 Wochen vor der Oberkante, ohne höheres Hoch dazwischen."""
    h, l = df["High"].to_numpy(), df["Low"].to_numpy()
    s0 = max(0, i - FLAGGE_STANGE_W * WOCHE)
    si = s0 + int(np.argmin(l[s0:i + 1]))
    sauber = h[si:i].max() <= top if i > si else False
    return {"prozent": (top / l[si] - 1) * 100, "wochen": (i - si) / WOCHE, "von_i": si, "von": l[si], "sauber": sauber}


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
    if (stange["sauber"] and stange["prozent"] >= FLAGGE_SCHUB * 100 and wochen <= FLAGGE_ZONE_W
            and hoehe / top <= FLAGGE_TIEFE):
        name = "Flagge"
    elif v["art"] == "Absturz":
        name = "Konsolidierung"
    else:
        name = "Base"
    mindest = FLAGGE_MIN_W if name == "Flagge" else MIN_WOCHEN
    laenge = "zu kurz" if wochen < mindest else "zu lang" if wochen > MAX_WOCHEN else "ok"
    return {"zone": True, "name": name, "start_i": i, "start": df.index[i], "oben": top, "unten": boden,
            "tief_i": tief_i, "tief_datum": df.index[tief_i], "wochen": wochen, "laenge": laenge,
            "tiefe": hoehe / top * 100, "abstand": (c[-1] / top - 1) * 100, "vorgeschichte": v, "stange": stange}


SCHRUMPF = 0.70                # jede Kontraktion höchstens 70 % so tief wie die vorige
ENGE_MAX = 10.0                # letzte Kontraktion höchstens 10 % tief


def enge(df, z):
    """Baustein 2: Kontraktionen in der Zone z (aus zone()), Enge, Pivot, Volumen, Ampel.

    Kontraktionen von links nach rechts: die erste vom Hoch der Zone bis zum tiefsten Tief danach; jede weitere vom
    höchsten Hoch nach dem letzten Tief bis zum tiefsten Tief danach. So schält sich die Base Schicht für Schicht zum
    rechten Rand hin ab. Ein Rücksetzer zählt erst ab 1 × ATR (darunter ist es Rauschen, der Kurs steht am Pivot)."""
    if not z.get("zone"):
        return {"ampel": "grau", "text": "keine fertige Zone – keine Enge"}
    h, l, c = df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy()
    v = df["Volume"].to_numpy(float)
    v50 = pd.Series(v).rolling(50, min_periods=20).mean().to_numpy()
    a = atr(df).to_numpy()
    n = len(df)

    def vol(i0, i1):
        s50 = np.nanmean(v50[i0:i1 + 1])
        return v[i0:i1 + 1].mean() / s50 * 100 if s50 else np.nan

    kontr = []
    hi = z["start_i"]
    while hi < n - 1:
        ti = hi + 1 + int(np.argmin(l[hi + 1:]))
        tiefe = (1 - l[ti] / h[hi]) * 100
        if h[hi] - l[ti] < FEIN * a[hi]:          # Rauschen: kein Rücksetzer mehr, der Kurs steht oben
            break
        kontr.append({"hoch_i": hi, "hoch": h[hi], "tief_i": ti, "tief": l[ti], "tiefe": tiefe, "volumen": vol(hi, ti)})
        if ti >= n - 1:
            break
        hi = ti + 1 + int(np.argmax(h[ti + 1:]))
    if not kontr:
        return {"ampel": "gelb", "zahl": 0, "text": "kein Rücksetzer von 1 × ATR seit der Oberkante", "fehlt": ["keine Kontraktion"]}
    tiefen = [k["tiefe"] for k in kontr]
    schrumpft = all(b <= SCHRUMPF * a_ for a_, b in zip(tiefen, tiefen[1:]))
    groesser = len(tiefen) >= 2 and tiefen[-1] > tiefen[-2]
    letzte = kontr[-1]
    pivot_i, pivot = letzte["hoch_i"], letzte["hoch"]
    tage = [i for i in range(pivot_i, n) if c[i] <= pivot]          # Ausbruchstage über dem Pivot zählen nicht mit
    s50 = np.nanmean(v50[tage]) if tage else np.nan
    vol_enge = v[tage].mean() / s50 * 100 if tage and s50 else np.nan
    vol_erste = kontr[0]["volumen"]               # Minervini: das Volumen schrumpft mit den Kontraktionen
    ruhig = len(kontr) >= 2 and vol_enge == vol_enge and vol_erste == vol_erste and vol_enge < vol_erste
    eng = letzte["tiefe"] <= ENGE_MAX
    tiefs = [k["tief"] for k in kontr]
    steigend = len(tiefs) >= 2 and all(b > a_ for a_, b in zip(tiefs, tiefs[1:]))
    if len(kontr) >= 2 and schrumpft and eng and ruhig:
        ampel = "grün"
    elif groesser:
        ampel = "rot"
    else:
        ampel = "gelb"
    fehlt = ([] if len(kontr) >= 2 else ["erst eine Kontraktion"]) + ([] if schrumpft else ["schrumpft nicht"]) \
        + ([] if eng else [f"Enge {letzte['tiefe']:.1f} % (über {ENGE_MAX:.0f} %)".replace(".", ",")]) \
        + ([] if ruhig or len(kontr) < 2 else ["Volumen nicht leiser als in der ersten Kontraktion"])
    folge = " → ".join(f"{t:.0f}" for t in tiefen)
    return {"ampel": ampel, "kontraktionen": kontr, "zahl": len(kontr), "folge": folge, "schrumpft": schrumpft,
            "groesser": groesser, "eng": eng, "enge_tiefe": letzte["tiefe"], "pivot_i": pivot_i, "pivot": pivot,
            "volumen": vol_enge, "volumen_erste": vol_erste, "ruhig": ruhig, "steigende_tiefs": steigend, "fehlt": fehlt,
            "abstand": (c[-1] / pivot - 1) * 100,
            "text": f"{len(kontr)} Kontraktion{'en' if len(kontr) != 1 else ''} {folge} %"
                    + (f" · fehlt: {', '.join(fehlt)}" if fehlt else "")}


def verlauf(df, tage=600):
    """Abgeschlossene Zonen der letzten `tage` Handelstage – dieselbe Regel wie live: eine Zone ist fertig, wenn
    der Kurs über seiner Oberkante schließt (Flagge in der Zone ebenso). Gerechnet wird nur an Tagen mit Schluss über
    den fünf Schlüssen davor – nur dort kann eine Zone (ab 1 Woche) enden."""
    df = df.dropna(subset=["High", "Low", "Close"])
    c = df["Close"].to_numpy()
    n = len(df)
    fertig = []
    for t in range(max(120, n - tage), n):
        if c[t] <= c[t - 5:t].max():
            continue
        k = zone(df.iloc[:t])
        if not k.get("zone"):
            continue
        for b in [k] + ([k["innen"]] if k.get("innen") else []):
            if b["laenge"] == "ok" and c[t] > b["oben"]:
                fertig.append(dict(b, ende_i=t, ende=df.index[t]))
    return fertig


def alles(df):
    """Für den Chart: Zone jetzt, abgeschlossene Zonen, grobes ZigZag – Lage als Datum (passt zu Tag und Woche)."""
    df = df.dropna(subset=["High", "Low", "Close"])
    ix = df.index

    def datiert(b):
        b = dict(b)
        for k_ in ("start_i", "tief_i", "ende_i"):
            if k_ in b:
                b[k_.replace("_i", "_t")] = ix[b[k_]]
        for k_ in ("vorgeschichte", "stange"):
            if k_ in b:
                b[k_] = dict(b[k_], von_t=ix[b[k_]["von_i"]], **({"bis_t": ix[b[k_]["bis_i"]]} if "bis_i" in b[k_] else {}))
        if b.get("innen"):
            b["innen"] = datiert(b["innen"])
        return b

    jetzt = zone(df)
    e = enge(df, jetzt)
    if e.get("kontraktionen"):
        e["kontraktionen"] = [dict(k, hoch_t=ix[k["hoch_i"]], tief_t=ix[k["tief_i"]]) for k in e["kontraktionen"]]
        e["pivot_t"] = ix[e["pivot_i"]]
    return {"jetzt": datiert(jetzt), "enge": e, "verlauf": [datiert(b) for b in verlauf(df)],
            "zigzag": [(ix[i], p) for i, p, _ in zigzag(df, GROB)]}
