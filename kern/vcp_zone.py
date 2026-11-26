"""Die Spanne am rechten Rand und der Ausbruch – streng nach Livermores Notizbuch (Micky 25.11.2026).

Livermore ist die Grundlage für Base und Front (livermore.spanne): die Spanne zwischen dem letzten Pivotal Point oben
und dem letzten Pivotal Point unten – die beiden Linien, die er im Notizbuch beobachtet. O'Neils und Minervinis Pivot
stammt von Livermores Pivotal Point (Fortsetzungs-Pivotal-Point). Entfernt am 25.11.2026: alle Formregeln der alten Spanne
(Dauer, Tiefe, obere Hälfte, Tasse, flache Base), Minervinis Drittel und Cheats, die Kontraktionen (Wellen, Enge,
VCP-Urteil, aufsteigende Base) und die Reife-Leiste. Livermore filtert mit Bestätigung, Volumen und Key Price.
Schwünge über 2 × ATR 14 (seine ~6 Punkte in der Schwankung des Titels, ungemessen) – dieselben Wendepunkte wie im Chart.

  Oberkante  = der letzte Pivotal Point oben = die Front (Regel 5a, 6d)
  Unterkante = der letzte Pivotal Point unten (ohne ihn das tiefste Tief seit der Oberkante)
  keine Spanne = ein Schluss über der Oberkante (Kurs läuft am Hoch) · offen = Livermore schreibt heute in die Spalte
               Abwärtstrend (noch keine Spanne)
  Länge, Tiefe = Zeichen, keine Schwellen

Name: immer „Spanne“ (Micky 25.11.2026) – Base, Flagge, Konsolidierung, Vorgeschichte und Fahnenstange sind entfernt.

Ausbruch (06.11.2026): Am Ausbruchstag ist die Spanne fertig und verschwindet. Damit Setup und Kaufzone stehen bleiben,
  schaut ausbruch() bis 4 Wochen zurück: Schluss über der Front der Spanne vom Vortag. Spanne und Front von damals gelten
  weiter – bis 4 Wochen, bis sich darüber eine neue Spanne gebildet hat oder Livermore einen neuen Pivotal Point oben
  einträgt. Bis +5 % über der Front =
  Kaufzone, darüber ausgedehnt. Schluss knapp unter der Front, aber weniger als 1 ATR = 🟡 Rücktest (keine Kaufzone,
  beobachten). Schluss 1 ATR unter der Front (Livermores Bestätigung gespiegelt, Micky 25.11.2026; vorher 13.11.2026:
  Tief des Ausbruchstags bzw. 3 %) =
  🔴 Fehlausbruch (Spanne und Front bleiben; neuer Schluss darüber = neuer Ausbruch). Livermores Bestätigung: ein Hoch
  1 ATR über der Front (Zeichen).
  Zeichen (kein Muss, Micky): Volumen am Ausbruchstag über dem 50-Tage-Schnitt = mit Volumen.
"""
import numpy as np
import pandas as pd
from masse import VOL_MIN_TAGE, WOCHE  # noqa: E402

ATR_TAGE = 14
GROB = 2.0
NEUES_HOCH_TAGE = 5     # Ausbruch nur an einem Tag mit Schluss über den 5 Schlüssen davor
MIN_DATEN = 80          # Ausbruch und Spring/Upthrust ab 80 Handelstagen Daten


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


def zone(df, nb=None):
    """Spanne am rechten Rand streng nach Livermores Notizbuch (Micky 25.11.2026; livermore.spanne) oder {"zone": False,
    "grund": …}: Oberkante = der letzte Pivotal Point oben, Unterkante = der letzte Pivotal Point unten (ohne ihn das
    tiefste Tief seit der Oberkante), Front = die Oberkante. Liegt ein Schluss über der Oberkante, läuft der Kurs am
    Hoch (keine Spanne); schreibt Livermore heute in die Spalte Abwärtstrend, ist die Spanne offen (noch keine Spanne). Name
    immer „Spanne“ (Micky 25.11.2026: rein Livermore – keine Namen nach Vorgeschichte mehr).
    nb = livermore.notizbuch über ein df, das mit diesem beginnt (auch länger: es zählt nur, was bis heute im Buch stand)."""
    import livermore
    df = df.dropna(subset=["High", "Low", "Close"])
    if len(df) < 60:
        return {"zone": False, "grund": "zu wenig Kurse"}
    c = df["Close"].to_numpy()
    n = len(df)
    sp = livermore.spanne(nb if nb is not None else livermore.notizbuch(df), n)
    if not sp:
        return {"zone": False, "grund": "noch kein Pivotal Point oben im Notizbuch – Kurs läuft am Hoch"}
    i, top = sp["oben"]["i"], float(sp["oben"]["preis"])
    if i < n - 1 and c[i + 1:].max() > top:
        return {"zone": False, "grund": "Schluss über dem letzten Pivotal Point oben – Kurs läuft am Hoch, keine Spanne"}
    l = df["Low"].to_numpy()
    if sp["unten"] is not None:                  # die Unterkante ist Livermores Pivotal Point unten
        j, boden = sp["unten"]["i"], float(sp["unten"]["preis"])
    else:
        j = i + int(np.argmin(l[i:]))
        boden = float(l[j])
    s0 = min(i, j)
    k = {"zone": True, "name": "Spanne", "start_i": s0, "start": df.index[s0], "oben": top, "unten": boden, "tief_i": j,
         "tief_datum": df.index[j], "wochen": (n - 1 - s0) / WOCHE, "tiefe": (top - boden) / top * 100,
         "abstand": (c[-1] / top - 1) * 100, "pivot": top, "pivot_i": i, "spalte": sp["spalte"], "trend": sp["trend"],
         "oben_aus": sp["oben"]["aus"]}
    if sp["spalte"] == "AB":                     # Livermore schreibt rot in den Abwärtstrend: noch keine Spanne
        return {"zone": False, "offen": True, "grund": "Abwärtstrend (Livermore schreibt in rot) – noch keine Spanne",
                **{x: k[x] for x in ("start_i", "start", "oben", "unten", "tief_i", "tief_datum", "wochen", "tiefe",
                                     "abstand", "pivot", "pivot_i", "spalte", "trend", "oben_aus")}}
    return k


RAND_PCT = 3.0              # an der Front: bis 3 % darunter (Test am Rand) – eine Quelle
AUSBRUCH_TAGE = 20             # Ausbruch gilt bis 4 Wochen, solange kein Schluss unter der Front (Micky, 06.11.2026)
KAUFZONE = 5.0                 # bis 5 % über der Front (Minervini)


def ausbruch(df, tage=AUSBRUCH_TAGE, jetzt=None, nb=None):
    """Ausbruch über die Front (Livermores Pivotal Point, zone()) in den letzten `tage` Handelstagen oder None:
    {tag, tage_her, erster_tag, pivot, zone, volumen, mit_volumen, abstand, kaufzone, fehl, fehl_tag, ruecktest,
    rueck_tag, bestaetigt, bestaetigt_tag, bestaetigung, gescheitert: [(Tag des Fehlausbruchs, Hoch des gescheiterten
    Vorstoßes)]}. Die Spanne so, wie sie am Vortag des ersten Ausbruchs stand (Indizes passen zu df). Schließt der
    Kurs danach wieder unter der Front, ist es ein Fehlausbruch (fehl) – Spanne und Front bleiben; ein neuer Schluss
    darüber ist ein neuer Ausbruch (tag, volumen von diesem Tag). Hat sich über dem Ausbruch schon eine neue Spanne
    gebildet (jetzt = zone(df), sonst gerechnet), übernimmt sie: None; hat Livermore seit dem Ausbruch einen neuen Pivotal
    Point oben eingetragen, gilt die neue Front (ein Ausbruch darüber wird gesucht). Livermores Bestätigung (Regel 5a, seine ~3 Punkte):
    ein Hoch mindestens 1 ATR über der Front seit dem Ausbruchstag – ein Zeichen, keine Pflicht.
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
        jz = jetzt if jetzt is not None else zone(df, nb)
        if jz.get("zone") and jz["start_i"] > t:
            return None                                    # neue Spanne über dem Ausbruch
        if jz.get("pivot_i") not in (None, b["pivot_i"]):
            continue                                       # seitdem ein neuer Pivotal Point oben im Buch: er gilt
        # Verlauf seit dem Ausbruch (Micky 25.11.2026, Livermore – vorher 13.11.2026 Tief des Ausbruchstags bzw. 3 %):
        # Fehlausbruch bei Schluss 1 ATR (ATR am Ausbruchstag) unter der Front – Livermores Bestätigung gespiegelt;
        # knapp unter der Front ist ein Rücktest. Ein Schluss über der Front nach einem Fehlausbruch ist ein neuer
        # Ausbruch (Tag und Volumen von dort).
        letzter, fehl_tag, rueck_tag = t, None, None
        hh = df["High"].to_numpy(float)
        a_ = atr(df).to_numpy(float)
        gescheitert = []                               # frühere Fehlausbrüche (Micky 24.11.2026): Tag und Hoch
        for u in range(t + 1, n):                      # des gescheiterten Vorstoßes – dort sitzen die Gefangenen
            if c[u] > pivot:
                if fehl_tag is not None:
                    gescheitert.append((df.index[fehl_tag], float(hh[letzter:fehl_tag + 1].max())))
                    letzter = u
                fehl_tag = rueck_tag = None
            elif fehl_tag is None and c[u] < pivot - livermore.BESTAETIGUNG * a_[letzter]:
                fehl_tag, rueck_tag = u, None
            elif fehl_tag is None and rueck_tag is None:
                rueck_tag = u
        vol = v[letzter] / v50[letzter] if v50[letzter] == v50[letzter] and v50[letzter] else None
        ab = (c[-1] / pivot - 1) * 100
        fehl = fehl_tag is not None
        bestaetigung = pivot + livermore.BESTAETIGUNG * float(a_[letzter])   # Livermores ~3 Punkte
        fehl_grenze = pivot - livermore.BESTAETIGUNG * float(a_[letzter])
        ueber = np.flatnonzero(hh[letzter:] >= bestaetigung)
        return {"tag": df.index[letzter], "tage_her": n - 1 - letzter, "erster_tag": df.index[t],
                "vortag_i": t, "pivot": pivot, "zone": b, "volumen": vol,
                "mit_volumen": bool(vol and vol > 1), "abstand": ab, "kaufzone": not fehl and rueck_tag is None and 0 <= ab <= KAUFZONE,
                "fehl": fehl, "fehl_tag": df.index[fehl_tag] if fehl else None,
                "ruecktest": rueck_tag is not None, "rueck_tag": df.index[rueck_tag] if rueck_tag is not None else None,
                "fehl_grenze": fehl_grenze, "bestaetigung": bestaetigung,
                "bestaetigt": bool(len(ueber)), "bestaetigt_tag": df.index[letzter + ueber[0]] if len(ueber) else None,
                "tage_bis_bestaetigt": int(ueber[0]) if len(ueber) else None,
                "gescheitert": gescheitert + (
                    [(df.index[fehl_tag], float(hh[letzter:fehl_tag + 1].max()))] if fehl else [])}
    return None


def wucht(a, einheit="T."):
    """Wucht am Ausbruch (Micky 26.11.2026: Momentum = Masse mal Geschwindigkeit) – eine Ablesung, kein Urteil, ohne
    Schwelle: Masse = Volumen am Ausbruchstag gegen den 50-Tage-Schnitt, Geschwindigkeit = Handelstage bis zu
    Livermores Bestätigung 📒 (0 = am Ausbruchstag selbst), in Kerzen der Ebene (einheit). → Text oder "" (kein Ausbruch, Fehlausbruch)."""
    if not a or a["fehl"]:
        return ""
    k = lambda x: f"{x:.1f}".replace(".", ",")        # noqa: E731
    masse = f"Masse {k(a['volumen'])}-fach" if a.get("volumen") else "Masse unbekannt"
    tb = a.get("tage_bis_bestaetigt")
    tempo = ("📒 am selben Tag" if tb == 0 else f"📒 nach {tb} {einheit}" if tb is not None
             else f"📒 steht aus (seit {a['tage_her']} {einheit})")
    return f"💥 Wucht: {masse} · {tempo}"


def ausbruch_text(a):
    """Zeichen für Karte und Plan, z. B. „🟢 Ausbruch am 04.11. mit Volumen 1,35-fach · +2,1 % zur Front, in der
    Kaufzone“ oder „🔴 Fehlausbruch: …“."""
    if not a:
        return ""
    k = lambda x: f"{x:.1f}".replace(".", ",")        # noqa: E731
    v = lambda x: f"{x:.2f}".replace(".", ",")       # noqa: E731 – zwei Stellen, damit 1,03 nicht als 1,0 erscheint
    ab = ("±0,0" if round(abs(a["abstand"]), 1) == 0 else f"{'+' if a['abstand'] >= 0 else '−'}{k(abs(a['abstand']))}") \
        + " % zur Front"
    if a["fehl"]:
        return (f"🔴 Fehlausbruch: Ausbruch am {a['tag']:%d.%m.}, am {a['fehl_tag']:%d.%m.} Schluss 1 ATR unter dem "
                f"Front (unter {v(a['fehl_grenze'])} $, Livermore) · {ab} – kein Kauf, bleibt unter Beobachtung, bis der "
                f"Kurs wieder über der Front schließt")
    if a.get("ruecktest"):
        return (f"🟡 Rücktest: Ausbruch am {a['tag']:%d.%m.}, seit {a['rueck_tag']:%d.%m.} knapp unter der Front · {ab} – "
                f"schließt er nicht 1 ATR darunter (unter {v(a['fehl_grenze'])} $), ist der Ausbruch nicht gescheitert")
    vol = (f"mit Volumen {v(a['volumen'])}-fach" if a["mit_volumen"] else
           f"ohne Volumen ({v(a['volumen'])}-fach)" if a["volumen"] else "Volumen unbekannt")
    lage = "in der Kaufzone" if a["kaufzone"] else "ausgedehnt"
    best = (f"bestätigt am {a['bestaetigt_tag']:%d.%m.} (Livermore: 1 ATR über der Front)" if a.get("bestaetigt")
            else f"noch nicht bestätigt (Livermore: über {v(a['bestaetigung'])} $)")
    return (f"{'🟢' if a['mit_volumen'] and a.get('bestaetigt') else '🟡'} Ausbruch am {a['tag']:%d.%m.} {vol} · {best} · "
            f"{ab}, {lage} · {wucht(a)}")




SU_TAGE = 10                 # Spring/Upthrust gilt bis 10 Handelstage nach dem Schluss zurück (Micky 15.11.2026)
SU_ZURUECK = 3               # … Schluss zurück in der Spanne am Tag selbst oder in den 2 Tagen danach
SU_TIEFE_ATR = 1.0           # … das Tagesextrem höchstens 1 ATR jenseits des Randes (Wyckoff: flacher Spring)


def spring_upthrust(df, tage=SU_TAGE):
    """Spring (long) bzw. Upthrust (short) an der Spanne des Scanners – die eine Regel für Zeichen, Zustand und Setup
    (Gefechtsordnung Schritt 4, Micky 14./15.11.2026; Wyckoff). Die Spanne gilt, wie sie am Vortag stand: das Tief des Tages
    liegt unter ihrer Unterkante (Upthrust: das Hoch über der Oberkante), höchstens 1 ATR, und ein Schluss am selben Tag
    oder in den 2 Tagen danach liegt wieder in der Spanne (ein Fehlausbruch – Schluss jenseits, dann zurück – zählt auch).
    Einstieg beim Schluss zurück in der Spanne (Auslöser: der Rand), Stopp am Tief bzw. Hoch des Fehlausbruchs, Ziel der
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
                       f"Hoch über der Front {o:.2f}".replace(".", ","), True,
                       f"{df.index[i]:%d.%m.} · {tiefe / a[i]:.1f} ATR jenseits".replace(".", ",")),
                      ("Schluss zurück in der Spanne binnen 3 Tagen", True, f"{df.index[j]:%d.%m.} · {c[j]:.2f}".replace(".", ",")),
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
    """Spanne mit Datum zu jedem Index (für den Chart)."""
    ix = df.dropna(subset=["High", "Low", "Close"]).index
    b = dict(b)
    for k_ in ("start_i", "tief_i", "pivot_i"):
        if k_ in b:
            b[k_.replace("_i", "_t")] = ix[b[k_]]
    return b
