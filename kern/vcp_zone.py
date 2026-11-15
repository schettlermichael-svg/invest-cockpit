"""VCP-Scanner, Baustein 1: die Zone, Baustein 2: die Enge am rechten Rand (06.11.2026).

Die Zone ist die ruhige Phase vor dem rechten Rand – die Base im Sinne Minervinis, ohne den Lauf oder Absturz davor.
Alles auf Tageskerzen, Wendepunkte über ein ZigZag nach ATR (grob = 2 × ATR 14).

  Oberkante  = grobes Swing-Hoch, über dem seitdem kein Schlusskurs lag
               (von mehreren solchen das älteste, dessen Zone die Erholungsregel erfüllt)
  Erholung   = nach dem tiefsten Tief kam der Kurs wieder in die obere Hälfte der Zone
               (sonst ist das Hoch der Rand eines Absturzes, nicht einer Base → nächstjüngeres Hoch;
               erfüllt keines die Regel, läuft der Rücksetzer noch: Rahmen ab dem ältesten Hoch, Zone offen)
  Absturz    = ist die Zone eines Hochs über 50 % tief, ist sie keine Base (O'Neil: im schweren Bärenmarkt bis 40–50 %)
               → nächstjüngeres Hoch; der Absturz gehört zur Vorgeschichte (14.11.2026, Chart-Prüfer)
  Henkel     = war die Tasse mindestens 7 Wochen lang (O'Neil), kam die rechte Seite bis 15 % an die Oberkante heran
               (O'Neil: Henkel höchstens 15 % unter dem Hoch der
               linken Seite) und schloss der Kurs danach wieder in der unteren Hälfte (Schlusskurs, Micky 14.11.2026 – ein
               Docht nach unten reicht nicht), ohne das Tief zu
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
  Kontraktion = die erste ist die linke Seite (Hoch der Zone bis zum tiefsten Tief der Base), danach jede Welle der
                rechten Seite der Reihe nach: grobes Schwunghoch bis zum nächsten Schwungtief (2 × ATR); am rechten
                Rand die letzte, enge ab 1 × ATR; Tiefe in % (14.11.2026, Chart-Prüfer: vorher vom höchsten Hoch nach
                dem letzten Tief – Wellen der rechten Seite fielen weg)
  Reife       = Zone kürzer als ihre Mindestdauer (Base 3 Wochen, Flagge 1 Woche) → noch im Aufbau, kein Pivot, Ampel grau
  Tiefe       = Base über 33 % tief (O'Neil: nur im Bärenmarkt) → Ampel nicht grün, steht unter „fehlt“
  Schärfe     = (14.11.2026, Chart-Prüfer Lauf 3) jede Kontraktion mindestens 3 Handelstage; mehr als 6 Wellen ist kein VCP;
                grün nur, wenn das Volumen der Enge unter dem 50-Tage-Schnitt liegt (ausgetrocknet) und nicht in Phase 4
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
from masse import PHASE_VERTEILUNG, VOL_MIN_TAGE, WOCHE  # noqa: E402

ATR_TAGE = 14
GROB = 2.0
FEIN = 1.0
MIN_WOCHEN, MAX_WOCHEN = 3, 65
ERHOLUNG = 0.5                 # Anteil der Zonenhöhe, den der Kurs nach dem Tief zurückgewinnen muss
HENKEL_HAELFTE = 0.5           # O'Neil: nach der rechten Seite nicht wieder in die untere Hälfte (sonst neue Base) …
HENKEL_NAH = 0.15              # … sobald die rechte Seite bis 15 % an das Hoch der linken Seite heran kam (Henkel möglich)
TASSE_MIN_W = 7                # … und nur bei einer Tasse: linke Seite bis rechte Seite mindestens 7 Wochen (O'Neil) –
                               # Chart-Prüfer 14.11.2026: sonst „scheiterten“ Pausen von Tagen und es blieben Zonen von 0,2 Wochen
ABSTURZ_TIEFE = 0.50           # Chart-Prüfer 14.11.2026: Zonen von 51–73 % Tiefe (WIX, CNXC, RH …) fassten den Absturz mit ein
FLAGGE_SCHUB, FLAGGE_STANGE_W, FLAGGE_ZONE_W, FLAGGE_TIEFE = 0.30, 13, 8, 0.25   # Kullamägi: 30 % in 1–3 Monaten
FLAGGE_MIN_W = 1
FLAGGE_TIEF_ATR = 0.5     # Flagge: das Tief der zweiten Hälfte darf bis 0,5 ATR unter dem der ersten liegen (Shakeout)


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
VOR_WOCHEN = 52         # Vorgeschichte: Anstieg in den 52 Wochen vor der Oberkante
VOR_TIEF_WOCHEN = 26    # … Tief der 26 Wochen davor
FLAGGE_MIN_TAGE = 4     # Tiefs der Flagge erst ab 4 Tagen vergleichbar
VERLAUF_TAGE = 600      # Historie: die letzten 600 Handelstage
VERLAUF_START = 120     # … frühestens ab Tag 120 (Zonen brauchen Vorlauf)
NEUES_HOCH_TAGE = 5     # Ausbruch nur an einem Tag mit Schluss über den 5 Schlüssen davor
MIN_DATEN = 80          # Ausbruch/Ermüdung ab 80 Handelstagen Daten
MIN_DATEN_BF = 120      # Bärenflagge ab 120 Handelstagen Daten
BF_GD50_TAGE = 20       # Bärenflagge: GD50 fällt (gegen 20 Tage vorher)
BF_DRIFT_TIEF_TAGE = 5  # Bärenflagge: Tief des Driftens der letzten 5 Tage
BF_RUECKHOL = 0.5       # Bärenflagge: holt höchstens die Hälfte des Falls zurück
MIN_DATEN_PHASE = 300   # Bruch der Spanne ab 300 Handelstagen (Phase braucht sie)
WOCHE_RAND_TAGE = 6     # Beginn der Phase: Wochenbeginn (6 Kalendertage vor dem Wochenschluss)
SPANNE_BRUCH = 0.99     # Bruch der Spanne: Schluss 1 % unter ihrem Tief


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
        if hoehe / top > ABSTURZ_TIEFE:          # O'Neil: über 50 % tief ist keine Base mehr, sondern ein Absturz – er
            continue                             # gehört zur Vorgeschichte, die Zone beginnt am nächstjüngeren Hoch
        if erholt >= top - ERHOLUNG * hoehe:
            # O'Neil: der Henkel liegt in der oberen Hälfte der Base. Kam die rechte Seite bis 15 % an das Hoch heran
            # und fiel der Kurs danach wieder in die untere Hälfte, ist die Tasse gescheitert – die Base beginnt neu
            # am Hoch der rechten Seite (Minervini: „rebase following a failed cup-and-handle“; LUV 14.11.2026: Base
            # ab 17.02. statt ab 26.06.)
            r_i = tief_i + 1 + int(np.argmax(h[tief_i + 1:])) if tief_i < n - 1 else n - 1   # nach dem Tief
            if (r_i < n - 1 and (r_i - i) / WOCHE >= TASSE_MIN_W and h[r_i] >= top * (1 - HENKEL_NAH) and
                    c[r_i + 1:].min() < boden + HENKEL_HAELFTE * hoehe):   # Schluss entscheidet (Micky 14.11.)
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
            flach = [(i_, t_) for i_, t_ in kand if (t_ - l[i_:].min()) / t_ <= ABSTURZ_TIEFE]
            if flach:                           # das jüngste Hoch, dessen Rücksetzer noch eine Base werden kann
                i, top = flach[-1]
                grund = "Rücksetzer läuft – seit dem Hoch nicht zurück in der oberen Hälfte, Zone noch offen"
            else:
                i, top = kand[0]
                grund = (f"Absturz über {ABSTURZ_TIEFE * 100:.0f} % seit {df.index[i]:%d.%m.%Y} – keine Base "
                         "(O'Neil), es hat sich noch keine neue Zone gebildet")
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
    """Fahnenstange: Anstieg vom tiefsten Tief der 13 Wochen vor der Oberkante, ohne höheres Hoch dazwischen – und
    direkt vor der Flagge (Micky 15.11.2026, Chart-Prüfer Lauf 4: die Stange kam aus einem Lauf, der Monate
    zurücklag): gab es in den 13 Wochen einen Rücksetzer tiefer als eine Flagge sein darf (25 %), beginnt die Stange
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
            and hoehe / top <= FLAGGE_TIEFE and not (tf and tf[0])):     # fallende Tiefs: die Truppe weicht – keine Flagge
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
KONTR_MIN_TAGE = 3             # eine Kontraktion dauert mindestens 3 Handelstage (Chart-Prüfer 14.11.2026: 1-Tages-Zucken)
KONTR_MAX = 6                  # Minervini: 2–6 Kontraktionen; mehr Wellen sind Seitwärtsrauschen, kein VCP
BASE_TIEFE_UEBLICH = 33.0          # O'Neil: Tassen 12–33 % tief, tiefer nur im Bärenmarkt (bis 40–50 %); Minervini ähnlich –
                               # tiefer wird gezeigt, die Ampel wird aber nicht grün (Chart-Prüfer 14.11.2026)


def enge(df, z):
    """Baustein 2: Kontraktionen in der Zone z (aus zone()), Enge, Pivot, Volumen, Ampel.

    Kontraktionen (Minervini): linke Seite bis zum Tief der Base, dann jede Welle der rechten Seite (ZigZag 2 × ATR);
    am rechten Rand zählt die letzte, enge Kontraktion schon ab 1 × ATR. Zu kurze Zonen haben noch keinen Pivot."""
    if not z.get("zone"):
        return {"ampel": "grau", "text": "keine fertige Zone – keine Enge"}
    if z.get("laenge") == "zu kurz":            # O'Neil/Minervini: eine Base braucht ihre Mindestdauer, vorher kein Pivot
        mindest = FLAGGE_MIN_W if z.get("name") == "Flagge" else MIN_WOCHEN
        return {"ampel": "grau", "zahl": 0, "fehlt": ["zu kurz"],
                "text": f"{z.get('name', 'Zone')} erst {z['wochen']:.1f} Wochen (mindestens {mindest}) – noch im Aufbau, "
                        "kein Pivot".replace(".", ",")}
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
    pivot_i, pivot = letzte["hoch_i"], letzte["hoch"]
    tage = [i for i in range(pivot_i, n) if c[i] <= pivot]          # Ausbruchstage über dem Pivot zählen nicht mit
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
    if len(kontr) >= 2 and schrumpft and eng and ruhig and flach_genug and wenige and trocken and ph != 4:
        ampel = "grün"
    elif groesser:
        ampel = "rot"
    else:
        ampel = "gelb"
    fehlt = ([] if len(kontr) >= 2 else ["erst eine Kontraktion"]) + ([] if schrumpft else ["schrumpft nicht"]) \
        + ([] if eng else [f"Enge {letzte['tiefe']:.1f} % (über {ENGE_MAX:.0f} %)".replace(".", ",")]) \
        + ([] if ruhig or len(kontr) < 2 else ["Volumen nicht leiser als in der ersten Kontraktion"]) \
        + ([] if flach_genug else [f"Base {z['tiefe']:.0f} % tief (über {BASE_TIEFE_UEBLICH:.0f} %, nur im Bärenmarkt üblich)"]) \
        + ([] if wenige else [f"{len(kontr)} Wellen (Minervini: 2–{KONTR_MAX})"]) \
        + ([] if trocken or vol_enge != vol_enge else [f"Volumen der Enge {vol_enge:.0f} % des Schnitts (nicht ausgetrocknet)"]) \
        + ([] if ph != 4 else ["Phase 4 – im Abwärtstrend kein VCP"])
    folge = " → ".join(f"{t:.0f}" for t in tiefen)
    hoehe_z = z["oben"] - z["unten"]
    anteil = (pivot - z["unten"]) / hoehe_z if hoehe_z > 0 else 1.0
    lage = drittel(z, pivot) or "Pivot am Rand"   # eine Cheat-Regel (Drittel der Base, mehr als RAND_PCT unter der Oberkante)
    return {"ampel": ampel, "kontraktionen": kontr, "zahl": len(kontr), "folge": folge, "schrumpft": schrumpft,
            "lage": lage, "lage_anteil": anteil,
            "groesser": groesser, "eng": eng, "enge_tiefe": letzte["tiefe"], "pivot_i": pivot_i, "pivot": pivot,
            "volumen": vol_enge, "volumen_erste": vol_erste, "ruhig": ruhig, "steigende_tiefs": steigend, "fehlt": fehlt,
            "abstand": (c[-1] / pivot - 1) * 100,
            "text": f"{len(kontr)} Kontraktion{'en' if len(kontr) != 1 else ''} {folge} %"
                    + (f" · fehlt: {', '.join(fehlt)}" if fehlt else "")}


RAND_PCT = 3.0              # Rand einer Zone: bis 3 % von der Oberkante (Test am Rand, Cheat-Grenze) – eine Quelle
DOPPELT_TAGE = 5            # zwei Zonen, die innerhalb von 5 Tagen ausbrechen und sich überlappen: dieselbe Schlacht


def cheat(gross, b, pivot):
    """Die eine Cheat-Regel der App (Gefechtsordnung, Micky 14./15.11.2026): ein Ausbruch über `pivot` aus der Zone b
    ist ein früher Einstieg (Cheat) und kein Ausbruch, wenn b jünger ist als die größere Zone `gross`, die noch läuft,
    und der Pivot mehr als RAND_PCT unter deren Oberkante liegt – der Kurs bricht aus einer Pause in der Balance, nicht
    aus der Balance. → „Low Cheat (unteres Drittel)“ / „Cheat (mittleres Drittel)“ / „Cheat (oberes Drittel)“ oder None.
    Benutzt von: ausbruch (zählt ihn nicht als Ausbruch), verlauf (Historie: Cheat statt eigener Zone), basen (zählt
    ihn nicht), auktion (innere Rotation)."""
    if not (gross and gross.get("zone") and b and gross.get("oben") and gross.get("unten") is not None):
        return None
    if b.get("start_i", -1) <= gross.get("start_i", -1):
        return None
    return drittel(gross, pivot)


def drittel(z, pivot):
    """Lage eines Pivots in der Zone z: mehr als RAND_PCT unter der Oberkante und über der Unterkante ist es ein Cheat
    (Minervini: Drittel der Base) → „Low Cheat (unteres Drittel)“ / „Cheat (mittleres Drittel)“ / „Cheat (oberes
    Drittel)“; am Rand (bis RAND_PCT unter der Oberkante) oder außerhalb None."""
    if not (z and z.get("oben") and z.get("unten") is not None and pivot):
        return None
    if pivot >= z["oben"] * (1 - RAND_PCT / 100) or pivot <= z["unten"]:
        return None
    anteil = (pivot - z["unten"]) / (z["oben"] - z["unten"])
    return ("Low Cheat (unteres Drittel)" if anteil < 1 / 3 else "Cheat (mittleres Drittel)" if anteil < 2 / 3
            else "Cheat (oberes Drittel)")


def rand(z, e):
    """Der Auslöser des Ausbruchs (Entscheidung 6): das Hoch der Enge, wenn es höchstens RAND_PCT unter der Oberkante
    liegt, sonst die Oberkante – dieselbe Regel wie ausbruch()."""
    p = (e or {}).get("pivot")
    return float(z["oben"] if drittel(z, p) else (p or z["oben"]))


def einstiege(z, e, cheat=True):
    """Die Einstiege einer Base (Gefechtsordnung Schritt 2, Micky 14./15.11.2026): liegt das Hoch der letzten Enge mehr
    als RAND_PCT unter der Oberkante, gibt es zwei – früh beim Schluss über der Enge (Cheat) und am Ausbruch über die
    Oberkante; sonst einen am Rand (rand()). cheat=False (Flagge, keine Base): nur der eine am Rand. Struktur-Stopp je
    Einstieg (Schritt 3): Tief der letzten Kontraktion. → [{art, wort, wert, quelle, struktur}], aufsteigend."""
    if not (z and z.get("zone")):
        return []
    p = (e or {}).get("pivot")
    w = drittel(z, p) if cheat else None
    if w:
        aus = [{"art": "cheat", "wort": w, "wert": float(p), "quelle": f"{w}: Schluss über dem Hoch der letzten Enge"},
               {"art": "ausbruch", "wort": "Ausbruch", "wert": float(z["oben"]), "quelle": "Ausbruch über die Oberkante"}]
    else:
        aus = [{"art": "ausbruch", "wort": "Ausbruch", "wert": rand(z, e), "quelle": "Pivot der Base"}]
    kontr = (e or {}).get("kontraktionen") or []
    for x in aus:                                  # Struktur-Stopp (Schritt 3): unter dem Tief der letzten Kontraktion
        x["struktur"] = min(float(kontr[-1]["tief"]), x["wert"]) if kontr else None
    return aus


def naechster(liste, kurs, kaufzone=None):
    """Der Einstieg, der jetzt gilt: der unterste, über dem der Kurs noch nicht hinaus ist – noch nicht ausgelöst oder
    in seiner Kaufzone (bis kaufzone % darüber); über allen der oberste (ausgedehnt). → Stelle in liste oder None."""
    if not liste:
        return None
    kaufzone = KAUFZONE if kaufzone is None else kaufzone
    for i, x in enumerate(liste):
        if kurs <= x["wert"] * (1 + kaufzone / 100):
            return i
    return len(liste) - 1


def _einordnen(fertig, jetzt):
    """Historie nach der Gefechtsordnung: dieselbe Schlacht nur einmal (überlappende Zonen, die innerhalb von
    DOPPELT_TAGE ausbrechen: die größere bleibt), ein Ausbruch innerhalb einer größeren Zone ist ein Cheat
    (b["cheat"] = Drittel) – innerhalb einer später ausbrechenden Zone der Historie oder der laufenden Zone."""
    fertig = sorted(fertig, key=lambda b: (b["ende_i"], b["start_i"]))
    raus = set()
    for i, a in enumerate(fertig):
        for j, b in enumerate(fertig):
            if i == j or i in raus or j in raus:
                continue
            ueberlapp = a["start_i"] <= b["start_i"] <= a["ende_i"] or b["start_i"] <= a["start_i"] <= b["ende_i"]
            if ueberlapp and abs(a["ende_i"] - b["ende_i"]) <= DOPPELT_TAGE:
                klein = j if (b["oben"] - b["unten"]) * (b["ende_i"] - b["start_i"]) <= \
                    (a["oben"] - a["unten"]) * (a["ende_i"] - a["start_i"]) else i
                raus.add(klein)
    aus = [b for k, b in enumerate(fertig) if k not in raus]
    for b in aus:
        groessere = [g for g in aus if g is not b and g["start_i"] < b["start_i"] and g["ende_i"] > b["ende_i"]]
        if jetzt and jetzt.get("zone") and jetzt["start_i"] < b["start_i"]:
            groessere.append(jetzt)
        for g in groessere:
            ch = cheat(dict(g, zone=True), b, b["oben"])
            if ch:
                b["cheat"] = ch
                break
    return aus


def verlauf(df, tage=VERLAUF_TAGE):
    """Abgeschlossene Zonen der letzten `tage` Handelstage – dieselbe Regel wie live: eine Zone ist fertig, wenn
    der Kurs über seiner Oberkante schließt (Flagge in der Zone ebenso). Gerechnet wird nur an Tagen mit Schluss über
    den fünf Schlüssen davor – nur dort kann eine Zone (ab 1 Woche) enden."""
    df = df.dropna(subset=["High", "Low", "Close"])
    c = df["Close"].to_numpy()
    n = len(df)
    fertig = []
    for t in range(max(VERLAUF_START, n - tage), n):
        if c[t] <= c[t - NEUES_HOCH_TAGE:t].max():
            continue
        k = zone(df.iloc[:t])
        if not k.get("zone"):
            continue
        for b in [k] + ([k["innen"]] if k.get("innen") else []):
            if b["laenge"] == "ok" and c[t] > b["oben"]:
                fertig.append(dict(b, ende_i=t, ende=df.index[t]))
    return _einordnen(fertig, zone(df))


AUSBRUCH_TAGE = 20             # Ausbruch gilt bis 4 Wochen, solange kein Schluss unter dem Pivot (Micky, 06.11.2026)
KAUFZONE = 5.0                 # bis 5 % über dem Pivot (Minervini)
FEHL_PCT = 3.0                 # Fehlausbruch: Schluss mehr als 3 % unter dem Pivot (oder unter dem Tief des Ausbruchstags)


def ausbruch(df, tage=AUSBRUCH_TAGE, jetzt=None, passt=None, cheats=False):
    """Ausbruch über den Pivot in den letzten `tage` Handelstagen oder None:
    {tag, tage_her, erster_tag, pivot, zone, enge, volumen, mit_volumen, abstand, kaufzone, fehl, fehl_tag, innen, eltern}.
    Zone und Enge so, wie sie am Vortag des ersten Ausbruchs standen (Indizes passen zu df). Schließt der Kurs danach
    wieder unter dem Pivot, ist es ein Fehlausbruch (fehl) – Zone und Pivot bleiben; ein neuer Schluss darüber ist ein
    neuer Ausbruch (tag, volumen von diesem Tag). Hat sich über dem Ausbruch schon eine neue fertige Zone gebildet
    (jetzt = zone(df), sonst gerechnet), übernimmt sie: None. passt(zone) → bool: nur Zonen, die das System als Base
    gelten lässt (Minervini, 12.11.2026: NIQ brach über eine 61 % tiefe Base aus, gerechnet wurde mit der Flagge darin –
    Text +9,0 %, Abstand +2,9 % zu zwei verschiedenen Pivots).
    Ein Ausbruch aus einer Pause innerhalb der noch laufenden größeren Zone ist ein Cheat (cheat()) und zählt nicht,
    ebenso ein Schluss über einem Hoch der Enge, das mehr als RAND_PCT unter der Oberkante liegt (drittel()) – der
    Ausbruch ist dann der Schluss über der Oberkante; mit cheats=True liefert die Funktion genau diesen Cheat (mit
    „cheat“: Drittel) – für Zustand und frühen Einstieg."""
    df = df.dropna(subset=["High", "Low", "Close"])
    n = len(df)
    if n < MIN_DATEN:
        return None
    c = df["Close"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().shift().to_numpy()
    for t in range(n - tage, n):
        if c[t] <= c[t - NEUES_HOCH_TAGE:t].max():                       # Vorprüfung wie in verlauf(): ohne neues Schlusshoch kein Ausbruch
            continue
        vor = df.iloc[:t]
        z = zone(vor)
        if not z.get("zone"):
            continue
        for b in [z] + ([z["innen"]] if z.get("innen") else []):
            if b.get("laenge") != "ok" or (passt and not passt(b)):
                continue
            e = enge(vor, b)
            # Gefechtsordnung Schritt 2 / Entscheidung 6: der Ausbruch geschieht am Rand – am Hoch der Enge, wenn es höchstens
            # RAND_PCT unter der Oberkante liegt, sonst an der Oberkante; ein Schluss über einem tieferen Hoch der Enge ist
            # der frühe Einstieg (Cheat, Drittel der Zone)
            w_enge = drittel(b, e.get("pivot"))
            pivot = float(e["pivot"]) if (cheats and w_enge) else rand(b, e)
            if c[t] <= pivot:
                continue
            jz = jetzt if jetzt is not None else zone(df)
            if jz.get("zone") and jz.get("laenge") == "ok" and jz["start_i"] > t:
                return None                                # neue fertige Zone über dem Ausbruch
            ch = cheat(jz, b, pivot) if jz.get("start_i", n) < t else None
            if cheats and not ch and w_enge:
                ch = w_enge                                # Schluss über einem Hoch der Enge unter dem Rand
            if bool(ch) != cheats:
                continue                                   # Cheat in der laufenden Zone: kein Ausbruch (bzw. umgekehrt)
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
                    "eltern": z["name"], "cheat": ch}
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
    if n < MIN_DATEN:
        return None
    c, h, l = df["Close"].to_numpy(float), df["High"].to_numpy(float), df["Low"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().shift().to_numpy()
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
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().shift().to_numpy()
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
    if n < MIN_DATEN_BF:
        return None
    c, h, l = df["Close"].to_numpy(float), df["High"].to_numpy(float), df["Low"].to_numpy(float)
    v = df["Volume"].to_numpy(float) if "Volume" in df else np.full(n, np.nan)
    g50 = pd.Series(c).rolling(50).mean().to_numpy()
    for t in range(n - tage, n):
        if not g50[t] < g50[t - BF_GD50_TAGE]:
            continue
        b = t - BF_DRIFT[1] + int(np.argmin(l[t - BF_DRIFT[1]:t - BF_DRIFT[0] + 1]))     # Tief des Falls
        a = b - BF_FALL_TAGE + int(np.argmax(h[b - BF_FALL_TAGE:b]))                       # Hoch vor dem Fall
        fall = h[a] - l[b]
        if fall / h[a] < BF_FALL:
            continue
        unten = l[t - BF_DRIFT_TIEF_TAGE:t].min()
        oben = h[b:t].max()
        if not (unten > l[b] and oben - l[b] <= BF_RUECKHOL * fall and c[t - 1] > l[b]):
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
    if n < MIN_DATEN_PHASE:
        return None
    c, l = df["Close"].to_numpy(float), df["Low"].to_numpy(float)
    try:
        ph = phase_mod.phasen(df)
    except Exception:  # noqa: BLE001
        return None
    for t in range(n - tage, n):
        fertig = ph[ph.index < df.index[t]]      # nur Wochen, deren Freitag vor dem Bruchtag liegt
        if not len(fertig) or int(fertig.iloc[-1]) not in (1, PHASE_VERTEILUNG):
            continue
        p = int(fertig.iloc[-1])
        lauf = 0
        for x in reversed(fertig.to_numpy()):
            if int(x) != p:
                break
            lauf += 1
        if lauf < SPANNE_WOCHEN:
            continue
        von = fertig.index[-lauf] - pd.Timedelta(days=WOCHE_RAND_TAGE)
        maske = (df.index > von) & (df.index < df.index[t])
        unten = float(l[maske].min())
        oben = float(df["High"].to_numpy(float)[maske].max())
        if not (c[t] < unten * SPANNE_BRUCH and c[t - 1] >= unten * SPANNE_BRUCH) or oben / unten - 1 > SPANNE_BREIT:
            continue
        regeln = [(f"{'Basis' if p == 1 else 'Verteilung'} (Phase {p}) mindestens 6 Wochen, höchstens 40 % breit", True,
                   f"{lauf} Wochen, Spanne {_de(unten)}–{_de(oben)} $ ({oben / unten * 100 - 100:.0f} %)")]
        return _short_dict(df, "Bruch der Spanne", t, oben, unten, regeln, df.index[maske][0])
    return None
