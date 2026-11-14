"""VCP-Scanner, Baustein 1: die Zone, Baustein 2: die Enge am rechten Rand (06.11.2026).

Die Zone ist die ruhige Phase vor dem rechten Rand – die Base im Sinne Minervinis, ohne den Lauf oder Absturz davor.
Alles auf Tageskerzen, Wendepunkte über ein ZigZag nach ATR (grob = 2 × ATR 14).

  Oberkante  = grobes Swing-Hoch, über dem seitdem kein Schlusskurs lag
               (von mehreren solchen das älteste, dessen Zone die Erholungsregel erfüllt)
  Erholung   = nach dem tiefsten Tief kam der Kurs wieder in die obere Hälfte der Zone
               (sonst ist das Hoch der Rand eines Absturzes, nicht einer Base → nächstjüngeres Hoch;
               erfüllt keines die Regel, läuft der Rücksetzer noch: Rahmen ab dem ältesten Hoch, Zone offen)
  Henkel     = war die Tasse mindestens 7 Wochen lang (O'Neil), kam die rechte Seite bis 15 % an die Oberkante heran
               (O'Neil: Henkel höchstens 15 % unter dem Hoch der
               linken Seite) und fiel der Kurs danach wieder in die untere Hälfte, ohne das Tief zu
               unterschreiten, ist die Tasse gescheitert (O'Neil: Henkel in der oberen Hälfte) → nächstjüngeres Hoch
               (14.11.2026; ein Unterschreiten des Tiefs ist ein Doppelboden und bleibt eine Base)
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
  Lage        = Drittel der Base, in dem der Pivot liegt (Minervini): unteres = Low Cheat, mittleres = Cheat,
                oberes = Pivot (O'Neils Henkel) – 14.11.2026
  Volumen     = Ø Volumen vom Pivot bis heute (ohne Tage über dem Pivot, am 50-Tage-Schnitt gemessen) leiser als
                in der ersten Kontraktion – das Volumen schrumpft mit den Kontraktionen
  Tiefs       = steigend als Zeichen, keine Pflicht (Shakeout erlaubt)
  Ampel       = grün: mindestens 2 Kontraktionen, schrumpfend, Enge ≤ 10 %, Volumen leiser · rot: die letzte
                Kontraktion ist tiefer als die vorige · gelb: sonst · grau: keine fertige Zone

Ausbruch (06.11.2026): Am Ausbruchstag ist die Zone fertig und verschwindet. Damit Setup und Kaufzone stehen bleiben,
  schaut ausbruch() bis 4 Wochen zurück: Schluss über dem Pivot der Zone vom Vortag (oder der Flagge darin). Zone, Enge
  und Pivot von damals gelten weiter – bis 4 Wochen, oder bis sich darüber eine neue fertige Zone gebildet hat. Bis +5 %
  über dem Pivot = Kaufzone, darüber ausgedehnt. Schluss knapp unter dem Pivot, das Tief des Ausbruchstags hält =
  🟡 Rücktest (keine Kaufzone, beobachten; 13.11.2026). Schluss unter dem Tief des Ausbruchstags oder mehr als 3 % unter
  dem Pivot = 🔴 Fehlausbruch (Zone und Pivot bleiben; neuer Schluss darüber = neuer Ausbruch).
  Zeichen (kein Muss, Micky): Volumen am Ausbruchstag über dem 50-Tage-Schnitt = mit Volumen.

Short – Ermüdung nach Überdehnung (Kullamägi-Stopp, 06.11.2026): die Flagge, im Ausgang gespiegelt. Die Truppe ist weit
vorgestoßen, gräbt sich ein, dann bricht die Stellung nach hinten weg.
  Fahnenstange ≥ 30 % in höchstens 13 Wochen, Zone 1–8 Wochen, höchstens 25 % tief (dieselbe Flagge wie oben, auch als
  Flagge in einer Base) · Auslöser: Schluss unter der Unterkante (in den letzten ERM_TAGE Handelstagen) · Stopp über dem
  Hoch des Auslösetags · Zeichen (kein Muss): Volumen am Bruch über dem 50-Tage-Schnitt
  grün: Kurs schließt noch unter der Unterkante · gelb: zurück in der Flagge, Stopp nicht erreicht · weg: Stopp erreicht

Short – Bärenflagge (echt, Prüf-Agent 13.11.2026; vorher hieß jede gebrochene Flagge im Abwärtstrend so): erst ein
steiler Fall, dann ein schwaches Driften nach oben, dann der Bruch – die Truppe zieht sich zurück, sammelt sich halbherzig
und weicht weiter.
  Fall mindestens 15 % in höchstens 30 Handelstagen · Driften 3–25 Tage, holt höchstens die Hälfte des Falls zurück,
  steigende Tiefs, Volumen leiser als im Fall · GD50 fällt · Auslöser: Schluss unter dem Tief der letzten 5 Tage des
  Driftens (Unterkante) · Stopp und Ampel wie bei der Ermüdung.

Short – Bruch der Spanne (Prüf-Agent 13.11.2026): eine Basis (Phase 1) oder Verteilung (Phase 3) von mindestens 6 Wochen
und höchstens 40 % Breite bricht nach unten – Schluss mindestens 1 % unter ihrem Tief (Unterkante). Die Stellung, die lange gehalten wurde, fällt.
  Stopp und Ampel wie bei der Ermüdung.
"""
import numpy as np
import pandas as pd

ATR_TAGE = 14
GROB = 2.0
FEIN = 1.0
WOCHE = 5
MIN_WOCHEN, MAX_WOCHEN = 3, 65
ERHOLUNG = 0.5                 # Anteil der Zonenhöhe, den der Kurs nach dem Tief zurückgewinnen muss
HENKEL_HAELFTE = 0.5           # O'Neil: nach der rechten Seite nicht wieder in die untere Hälfte (sonst neue Base) …
HENKEL_NAH = 0.15              # … sobald die rechte Seite bis 15 % an das Hoch der linken Seite heran kam (Henkel möglich)
TASSE_MIN_W = 7                # … und nur bei einer Tasse: linke Seite bis rechte Seite mindestens 7 Wochen (O'Neil) –
                               # Chart-Prüfer 14.11.2026: sonst „scheiterten“ Pausen von Tagen und es blieben Zonen von 0,2 Wochen
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
    kand = sorted((p[0], p[1]) for p in ungebrochen)   # älteste zuerst
    gewaehlt, gescheitert, k_ = None, None, 0
    while k_ < len(kand):
        i, top = kand[k_]
        k_ += 1
        tief_i = i + int(np.argmin(l[i:]))
        boden = l[tief_i]
        hoehe = top - boden
        erholt = h[tief_i:].max() if tief_i < n else boden
        if hoehe <= 0:
            gewaehlt = (i, top)
            break
        if erholt >= top - ERHOLUNG * hoehe:
            # O'Neil: der Henkel liegt in der oberen Hälfte der Base. Kam die rechte Seite bis 15 % an das Hoch heran
            # und fiel der Kurs danach wieder in die untere Hälfte, ist die Tasse gescheitert – die Base beginnt neu
            # am Hoch der rechten Seite (Minervini: „rebase following a failed cup-and-handle“; LUV 14.11.2026: Base
            # ab 17.02. statt ab 26.06.)
            r_i = tief_i + 1 + int(np.argmax(h[tief_i + 1:])) if tief_i < n - 1 else n - 1   # nach dem Tief
            if (r_i < n - 1 and (r_i - i) / WOCHE >= TASSE_MIN_W and h[r_i] >= top * (1 - HENKEL_NAH) and
                    l[r_i + 1:].min() < boden + HENKEL_HAELFTE * hoehe):
                gescheitert = (i, r_i)
                if all(x[0] != r_i for x in kand):
                    kand = sorted(kand + [(r_i, float(h[r_i]))])
                continue
            gewaehlt = (i, top)
            break
    if gewaehlt is None:                        # Rücksetzer läuft: Zone noch nicht fertig, Rahmen trotzdem zeigen
        if gescheitert:                         # ab der neuen linken Seite (dem Hoch der gescheiterten rechten Seite)
            i = gescheitert[1]
            top = float(h[i])
            grund = (f"Base ab {df.index[gescheitert[0]]:%d.%m.%Y} gescheitert (nach der rechten Seite zurück in der "
                     f"unteren Hälfte, O'Neil) – neue Base ab {df.index[i]:%d.%m.%Y}, Rücksetzer läuft")
        else:
            i, top = kand[0]
            grund = "Rücksetzer läuft – seit dem Hoch nicht zurück in der oberen Hälfte, Zone noch offen"
        tief_i = i + int(np.argmin(l[i:]))
        return {"zone": False, "grund": grund, "offen": True, "start_i": i, "oben": top, "unten": l[tief_i],
                "tief_i": tief_i, "wochen": (n - 1 - i) / WOCHE, "tiefe": (top - l[tief_i]) / top * 100,
                "abstand": (c[-1] / top - 1) * 100}
    i, top = gewaehlt
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
    hoehe_z = z["oben"] - z["unten"]
    anteil = (pivot - z["unten"]) / hoehe_z if hoehe_z > 0 else 1.0
    lage = ("Low Cheat" if anteil < 1 / 3 else "Cheat" if anteil < 2 / 3 else "Pivot")   # Minervini: Drittel der Base
    return {"ampel": ampel, "kontraktionen": kontr, "zahl": len(kontr), "folge": folge, "schrumpft": schrumpft,
            "lage": lage, "lage_anteil": anteil,
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


AUSBRUCH_TAGE = 20             # Ausbruch gilt bis 4 Wochen, solange kein Schluss unter dem Pivot (Micky, 06.11.2026)
KAUFZONE = 5.0                 # bis 5 % über dem Pivot (Minervini)
FEHL_PCT = 3.0                 # Fehlausbruch: Schluss mehr als 3 % unter dem Pivot (oder unter dem Tief des Ausbruchstags)


def ausbruch(df, tage=AUSBRUCH_TAGE, jetzt=None, passt=None):
    """Ausbruch über den Pivot in den letzten `tage` Handelstagen oder None:
    {tag, tage_her, erster_tag, pivot, zone, enge, volumen, mit_volumen, abstand, kaufzone, fehl, fehl_tag, innen, eltern}.
    Zone und Enge so, wie sie am Vortag des ersten Ausbruchs standen (Indizes passen zu df). Schließt der Kurs danach
    wieder unter dem Pivot, ist es ein Fehlausbruch (fehl) – Zone und Pivot bleiben; ein neuer Schluss darüber ist ein
    neuer Ausbruch (tag, volumen von diesem Tag). Hat sich über dem Ausbruch schon eine neue fertige Zone gebildet
    (jetzt = zone(df), sonst gerechnet), übernimmt sie: None. passt(zone) → bool: nur Zonen, die das System als Base
    gelten lässt (Minervini, 12.11.2026: NIQ brach über eine 61 % tiefe Base aus, gerechnet wurde mit der Flagge darin –
    Text +9,0 %, Abstand +2,9 % zu zwei verschiedenen Pivots)."""
    df = df.dropna(subset=["High", "Low", "Close"])
    n = len(df)
    if n < 80:
        return None
    c = df["Close"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    v50 = pd.Series(v).rolling(50, min_periods=20).mean().shift().to_numpy()
    for t in range(n - tage, n):
        if c[t] <= c[t - 5:t].max():                       # Vorprüfung wie in verlauf(): ohne neues Schlusshoch kein Ausbruch
            continue
        vor = df.iloc[:t]
        z = zone(vor)
        if not z.get("zone"):
            continue
        for b in [z] + ([z["innen"]] if z.get("innen") else []):
            if b.get("laenge") != "ok" or (passt and not passt(b)):
                continue
            e = enge(vor, b)
            pivot = float(e.get("pivot") or b["oben"])
            if c[t] <= pivot:
                continue
            jz = jetzt if jetzt is not None else zone(df)
            if jz.get("zone") and jz.get("laenge") == "ok" and jz["start_i"] > t:
                return None                                # neue fertige Zone über dem Ausbruch
            # Verlauf seit dem Ausbruch (Micky 13.11.2026): Fehlausbruch erst bei Schluss unter dem Tief des
            # Ausbruchstags oder mehr als 3 % unter dem Pivot; knapp unter dem Pivot ist ein Rücktest. Ein Schluss
            # über dem Pivot nach einem Fehlausbruch ist ein neuer Ausbruch (Tag und Volumen von dort).
            letzter, fehl_tag, rueck_tag = t, None, None
            lo = df["Low"].to_numpy(float)
            for u in range(t + 1, n):
                if c[u] > pivot:
                    if fehl_tag is not None:
                        letzter = u
                    fehl_tag = rueck_tag = None
                elif fehl_tag is None and (c[u] < lo[letzter] or c[u] < pivot * (1 - FEHL_PCT / 100)):
                    fehl_tag, rueck_tag = u, None
                elif fehl_tag is None and rueck_tag is None:
                    rueck_tag = u
            vol = v[letzter] / v50[letzter] if v50[letzter] == v50[letzter] and v50[letzter] else None
            ab = (c[-1] / pivot - 1) * 100
            fehl = fehl_tag is not None
            return {"tag": df.index[letzter], "tage_her": n - 1 - letzter, "erster_tag": df.index[t],
                    "vortag_i": t, "pivot": pivot, "zone": b, "enge": e, "volumen": vol,
                    "mit_volumen": bool(vol and vol > 1), "abstand": ab, "kaufzone": not fehl and rueck_tag is None and 0 <= ab <= KAUFZONE,
                    "fehl": fehl, "fehl_tag": df.index[fehl_tag] if fehl else None,
                    "ruecktest": rueck_tag is not None, "rueck_tag": df.index[rueck_tag] if rueck_tag is not None else None,
                    "tief_ausbruchstag": float(lo[letzter]), "innen": b is not z,
                    "eltern": z["name"]}
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
    return f"{'🟢' if a['mit_volumen'] else '🟡'} Ausbruch am {a['tag']:%d.%m.} {vol} · {ab}, {lage}"


ERM_TAGE = 5                   # Bruch höchstens 5 Handelstage her


def ermuedung(df, tage=ERM_TAGE):
    """Short-Setup Ermüdung nach Überdehnung oder None. Zone und Flagge so, wie sie am Vortag des Bruchs standen."""
    df = df.dropna(subset=["High", "Low", "Close"])
    n = len(df)
    if n < 80:
        return None
    c, h, l = df["Close"].to_numpy(float), df["High"].to_numpy(float), df["Low"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    v50 = pd.Series(v).rolling(50, min_periods=20).mean().shift().to_numpy()
    for t in range(n - tage, n):
        if c[t] >= l[t - FLAGGE_MIN_W * WOCHE:t].min():     # Vorprüfung: ohne Schluss unter den Tiefs der Woche kein Bruch
            continue
        z = zone(df.iloc[:t])
        f = z if z.get("name") == "Flagge" else z.get("innen")
        if not f or f["laenge"] != "ok" or c[t] >= f["unten"]:
            continue
        stopp = h[t]
        if t < n - 1 and h[t + 1:].max() > stopp:                # Stopp erreicht: Setup vorbei
            continue
        unter = c[-1] < f["unten"]
        vol = v[t] / v50[t] if v50[t] == v50[t] and v50[t] else None
        st = f["stange"]
        datum = df.index[t]
        regeln = [("Fahnenstange ab 30 % in höchstens 13 Wochen", True,
                   f"+{st['prozent']:.0f} % in {st['wochen']:.0f} Wochen"),
                  ("Flagge 1–8 Wochen, höchstens 25 % tief", True, f"{_de(f['wochen'], '.1f')} Wochen, {f['tiefe']:.0f} %"),
                  ("Schluss unter der Unterkante", True, f"{datum:%d.%m.} · {_de(c[t])} unter {_de(f['unten'])}"),
                  ("Kurs noch unter der Unterkante", unter, f"heute {_de(c[-1])}"),
                  ("Volumen am Bruch über dem Schnitt (Zeichen)", bool(vol and vol > 1),
                   f"{_de(vol, '.1f')}-fach" if vol else "kein Volumen")]
        return {"art": "Ermüdung nach Überdehnung", "ampel": "grün" if unter else "gelb", "regeln": regeln,
                "tag": datum, "tage_her": n - 1 - t, "oben": f["oben"], "unten": f["unten"], "stopp": float(stopp),
                "stange": st["prozent"], "volumen": vol, "start": f["start"]}
    return None


def enge_datiert(df, z):
    """enge() mit Datum zu jedem Index (für den Chart)."""
    df = df.dropna(subset=["High", "Low", "Close"])
    ix = df.index
    e = enge(df, z)
    if e.get("kontraktionen"):
        e["kontraktionen"] = [dict(k, hoch_t=ix[k["hoch_i"]], tief_t=ix[k["tief_i"]]) for k in e["kontraktionen"]]
        e["pivot_t"] = ix[e["pivot_i"]]
    return e


def datiert(df, b):
    """Zone mit Datum zu jedem Index (für den Chart)."""
    ix = df.dropna(subset=["High", "Low", "Close"]).index
    b = dict(b)
    for k_ in ("start_i", "tief_i", "ende_i"):
        if k_ in b:
            b[k_.replace("_i", "_t")] = ix[b[k_]]
    for k_ in ("vorgeschichte", "stange"):
        if k_ in b:
            b[k_] = dict(b[k_], von_t=ix[b[k_]["von_i"]], **({"bis_t": ix[b[k_]["bis_i"]]} if "bis_i" in b[k_] else {}))
    if b.get("innen"):
        b["innen"] = datiert(df, b["innen"])
    return b


def alles(df):
    """Für den Chart: Zone jetzt, abgeschlossene Zonen, grobes ZigZag – Lage als Datum (passt zu Tag und Woche)."""
    df = df.dropna(subset=["High", "Low", "Close"])
    ix = df.index

    def datiert_(b):
        return datiert(df, b)

    jetzt = zone(df)
    e = enge_datiert(df, jetzt)
    return {"jetzt": datiert_(jetzt), "enge": e, "verlauf": [datiert_(b) for b in verlauf(df)],
            "zigzag": [(ix[i], p) for i, p, _ in zigzag(df, GROB)]}


BF_FALL, BF_FALL_TAGE, BF_DRIFT = 0.15, 30, (3, 25)     # Bärenflagge: Fall ab 15 % in höchstens 30 Tagen, Driften 3–25 Tage
SPANNE_WOCHEN = 6                                      # Bruch der Spanne: Phase 1 oder 3 mindestens 6 Wochen …
SPANNE_BREIT = 0.40                                    # … und höchstens 40 % breit (sonst ist es keine Balance)


def _de(x, fmt=".2f"):
    return format(x, fmt).replace(".", ",")


def _short_dict(df, art, t, oben, unten, regeln, start):
    """Gemeinsame Form der Shorts (wie ermuedung): grün unter der Unterkante, gelb zurück darüber, None nach dem Stopp."""
    c, h = df["Close"].to_numpy(float), df["High"].to_numpy(float)
    n = len(df)
    stopp = h[t]
    if t < n - 1 and h[t + 1:].max() > stopp:                # Stopp erreicht: Setup vorbei
        return None
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    v50 = pd.Series(v).rolling(50, min_periods=20).mean().shift().to_numpy()
    vol = v[t] / v50[t] if v50[t] == v50[t] and v50[t] else None
    unter = c[-1] < unten
    regeln = regeln + [("Schluss unter der Unterkante", True, f"{df.index[t]:%d.%m.} · {_de(c[t])} unter {_de(unten)}"),
                       ("Kurs noch unter der Unterkante", unter, f"heute {_de(c[-1])}"),
                       ("Volumen am Bruch über dem Schnitt (Zeichen)", bool(vol and vol > 1),
                        f"{_de(vol, '.1f')}-fach" if vol else "kein Volumen")]
    return {"art": art, "ampel": "grün" if unter else "gelb", "regeln": regeln,
            "tag": df.index[t], "tage_her": n - 1 - t, "oben": float(oben), "unten": float(unten),
            "stopp": float(stopp), "volumen": vol, "start": start}


def baerenflagge(df, tage=ERM_TAGE):
    """Echte Bärenflagge (steiler Fall, schwaches Driften nach oben, Bruch) oder None."""
    df = df.dropna(subset=["High", "Low", "Close"])
    n = len(df)
    if n < 120:
        return None
    c, h, l = df["Close"].to_numpy(float), df["High"].to_numpy(float), df["Low"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    g50 = pd.Series(c).rolling(50).mean().to_numpy()
    for t in range(n - tage, n):
        if not g50[t] < g50[t - 20]:
            continue
        b = t - BF_DRIFT[1] + int(np.argmin(l[t - BF_DRIFT[1]:t - BF_DRIFT[0] + 1]))     # Tief des Falls
        a = b - BF_FALL_TAGE + int(np.argmax(h[b - BF_FALL_TAGE:b]))                       # Hoch vor dem Fall
        fall = h[a] - l[b]
        if fall / h[a] < BF_FALL:
            continue
        unten = l[t - 5:t].min()
        oben = h[b:t].max()
        if not (unten > l[b] and oben - l[b] <= 0.5 * fall and c[t - 1] > l[b]):
            continue
        ruhig = np.nanmean(v[b:t]) < np.nanmean(v[a:b + 1]) if b > a else False
        if not ruhig or c[t] >= unten or c[t - 1] < unten:
            continue
        regeln = [("Steiler Fall ab 15 % in höchstens 30 Tagen", True,
                   f"−{fall / h[a] * 100:.0f} % vom {df.index[a]:%d.%m.} bis {df.index[b]:%d.%m.}"),
                  ("Schwaches Driften nach oben, leiser", True,
                   f"{t - b} Tage, holt {(oben - l[b]) / fall * 100:.0f} % des Falls zurück"),
                  ("GD50 fällt", True, "")]
        return _short_dict(df, "Bärenflagge", t, oben, unten, regeln, df.index[b])
    return None


def spannenbruch(df, tage=ERM_TAGE):
    """Bruch der Spanne: Schluss mindestens 1 % unter dem Tief einer Phase 1 oder 3 von mindestens 6 Wochen, oder None."""
    import phase as phase_mod
    df = df.dropna(subset=["High", "Low", "Close"])
    n = len(df)
    if n < 300:
        return None
    c, l = df["Close"].to_numpy(float), df["Low"].to_numpy(float)
    try:
        ph = phase_mod.phasen(df)
    except Exception:  # noqa: BLE001
        return None
    for t in range(n - tage, n):
        fertig = ph[ph.index < df.index[t]]      # nur Wochen, deren Freitag vor dem Bruchtag liegt
        if not len(fertig) or int(fertig.iloc[-1]) not in (1, 3):
            continue
        p = int(fertig.iloc[-1])
        lauf = 0
        for x in reversed(fertig.to_numpy()):
            if int(x) != p:
                break
            lauf += 1
        if lauf < SPANNE_WOCHEN:
            continue
        von = fertig.index[-lauf] - pd.Timedelta(days=6)
        maske = (df.index > von) & (df.index < df.index[t])
        unten = float(l[maske].min())
        oben = float(df["High"].to_numpy(float)[maske].max())
        if not (c[t] < unten * 0.99 and c[t - 1] >= unten * 0.99) or oben / unten - 1 > SPANNE_BREIT:
            continue
        regeln = [(f"{'Basis' if p == 1 else 'Verteilung'} (Phase {p}) mindestens 6 Wochen, höchstens 40 % breit", True,
                   f"{lauf} Wochen, Spanne {_de(unten)}–{_de(oben)} $ ({oben / unten * 100 - 100:.0f} %)")]
        return _short_dict(df, "Bruch der Spanne", t, oben, unten, regeln, df.index[maske][0])
    return None
