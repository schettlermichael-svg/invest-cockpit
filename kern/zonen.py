"""Zonen, Phasen, Strömung – das schlanke Cockpit (Micky 21.11.2026).

Grundsatz: Eine Zone ist das Gerüst im Chart (der Nordstern). Der Markt pendelt in ihr (Balance) oder bricht aus ihr
aus (Disbalance). Drei Ebenen: die Woche zeigt die Strömung, der Tag die Zone, die Stunde den Einstieg. Gehandelt
werden nur vier Zonen-Trades; die Wahrscheinlichkeit zeigt die Einigkeit der Ebenen (Zeichen, keine Zahl).

Die Zone je Ebene ist die faire Zone nach Tom Vorwald (tiefe.pbd: Impuls, Zone aus Kerzenkörpern, Schlusskurszählung);
ohne Impuls der Rand der Balance (tiefe.struktur). POC = meistgehandelter Preis seit Impulsbeginn bzw. seit dem Anker.

Phase je Ebene (Zeichenliste):
  ⚪ ungemessen · 🟡 Balance (Kurs in der Zone, nicht an der Kante) · 💥 an der Kante (Test) bzw. erster Schluss
  draußen · 🦬/🐻 Ausbruch (2 Schlüsse draußen in Richtung des Impulses) · 🦊 gescheitert (2 Schlüsse draußen auf der
  Gegenseite: die Form ist gescheitert, Vorwald).
Richtung je Ebene: ↗ aufwärts, ↘ abwärts, → offen – der Impuls, nach einem Scheitern umgekehrt; in Balance ohne
  Ausbruch offen, außer die Form zeigt (P aufwärts, b abwärts).

Die vier Zonen-Trades (Tageszone; Micky 21.11.2026: nur diese):
  Pendel      Kurs an der Kante der Zone, Schluss darin → Einstieg an der Kante, Stopp eine Stufe hinter dem
              abgelehnten Docht (mindestens ¼ ATR, tiefe._d_trade), Ziel die Gegenkante.
  Ausbruch    2 bis 5 Schlüsse außerhalb in Richtung des Impulses → Einstieg am Schluss, Stopp in der Mitte der Zone,
              Ziel die Höhe der Zone nach außen abgetragen.
  Rücktest    nach dem Ausbruch (2 Schlüsse draußen) läuft die Kerze bis an die gebrochene Kante zurück (Kantenabstand),
              der Schluss bleibt draußen → Einstieg an der Kante, Stopp ¼ ATR jenseits der Kante, Ziel das Extrem seit
              dem Ausbruch.
  Gegentrade  Form gescheitert (2 bis 5 Schlüsse auf der Gegenseite) → Einstieg am Schluss, Stopp ¼ ATR jenseits der
              anderen Kante, Ziel der Impulsbeginn (Vorwald).
Gesetzt (Claude, 21.11.2026, zur Bestätigung): „frisch“ = höchstens 5 Schlüsse draußen, danach läuft der Trend ohne
neuen Einstieg; Ausbruchsziel = Zonenhöhe (Messregel der Balance).
Einigkeit: Richtung der Woche, Richtung des Trades und Richtung der Stunde – je Ebene, die mitzieht, ein Zeichen mehr
  (3 von 3 = 🦬🦬🦬). Ohne Trade die Einigkeit der Richtungen.
Zonen der Vergangenheit (Micky 21.11.2026: eine Regel für Woche, Tag und Stunde, die PbD-Kette, kette()):
  Impuls → Zone → Ausbruch oder Scheitern → nächster Impuls. Maßgeblich ist ein Impuls wie in tiefe.pbd (ein späterer
  löst ihn nur ab, wenn er per Schluss aus der Zone herausläuft). Die Zone beginnt am Impulsende und endet mit dem
  letzten Schluss darin vor dem 2. Schluss draußen, sonst am Beginn des nächsten Impulses. Kasten = Kerzenkörper (faire
  Zone, tiefe._zone), Dochte blass. Zwischen Ausbruch und nächstem Impuls und vor dem ersten Impuls: D-Zonen – 3 Kerzen,
  deren Körper zusammen keine 2 ATR überspannen (kein Impuls), danach wie die faire Zone fortgeschrieben, Ende wieder
  beim 2. Schluss draußen. Mindestlänge 3 Kerzen nach einem Impuls, 5 für eine D-Zone (ZONE_MIN, D_MIN, Claude
  21.11.2026, ungemessen). Alle Maße in ATR der Ebene.
  Offen, solange der Kurs seit ihrem Ende nie wieder in ihre Wertzone lief (Magnet), sonst erledigt; ihr POC ist nackt,
  solange kein Docht ihn seitdem berührt hat.
Profil (Micky 21.11.2026: nur eines, aber aussagekräftig): Zeit und Volumen gespiegelt in einer Silhouette, verankert
  am Beginn des Impulses der Zone von heute (Stiel = Impuls, Bauch = Zone: das Profil zeigt den Buchstaben), ohne
  Impuls am Beginn der Balance; aus den feineren Kerzen der Ebene. Sein POC ist der POC der Zone. Muster: liegt die Tageszone innerhalb der Wochenzone, setzt
  sich die Woche fort (innen), sonst darüber bzw. darunter.
"""
import pandas as pd

import tiefe

FRISCH_SCHLUESSE = 5                 # Ausbruch und Gegentrade gelten bis 5 Schlüsse draußen
ZONE_MIN = 3               # eine Zone nach einem Impuls braucht mindestens 3 Kerzen (Claude 21.11.2026, ungemessen)
D_MIN = 5                  # eine D-Zone ohne Impuls davor mindestens 5 (eine Rotation, wie avwap.BALANCE_BLOCK; ungemessen)
D_ATR = tiefe.IMPULS_ATR   # D-Zone: 3 Körper überspannen zusammen weniger als ein Impuls (2 ATR) – eine Quelle
GESCHEITERT = tiefe.GESCHEITERT    # 2 Schlüsse draußen (Vorwald) – eine Quelle
STOPP_ATR = tiefe.STOPP_ATR        # ¼ ATR jenseits der Kante – eine Quelle
HALB = 2                   # Mitte der Zone
EBENEN = ("Woche", "Tag", "Stunde")
PHASE = {"leer": ("⚪", "ungemessen"), "balance": ("🟡", "Balance"), "kante": ("💥", "an der Kante"),
         "test": ("💥", "erster Schluss draußen"), "aus_auf": ("🦬", "Ausbruch"), "aus_ab": ("🐻", "Ausbruch"),
         "gescheitert": ("🦊", "gescheitert")}
TRADE_NAME = {"pendel": "Pendel", "ausbruch": "Ausbruch", "ruecktest": "Rücktest", "gegen": "Gegentrade"}
TRADE_ZEICHEN = {"pendel": "🟡", "ausbruch": "💥", "ruecktest": "🪝", "gegen": "🦊"}


def _zone(e):
    """(tief, hoch, Profil, form, Beginn) der Ebene: faire Zone nach Vorwald, ohne Impuls der Rand der Balance. Das
    Profil hängt am Beginn des Impulses (profil_impuls). Eine Zone, die schmaler als ¼ ATR ist (erst eine Kerze), reicht
    über die Spanne ihrer ersten Kerze (Claude, 21.11.2026)."""
    pb, st_, df = e.get("pbd"), e["struktur"], e["df"]
    if pb:
        lo, hi, form, beginn = pb["zone_tief"], pb["zone_hoch"], pb["form"], pb["zone_start"]
    else:
        lo, hi, form, beginn = st_["short_pivot"], st_["pivot"], "D", st_["balance_start"]
    i = min(int(df.index.searchsorted(beginn)), len(df) - 1)
    if pb and e["atr"] and hi - lo < e["atr"] * STOPP_ATR:
        lo, hi = min(lo, float(df["Low"].iloc[i])), max(hi, float(df["High"].iloc[i]))
    return lo, hi, profil_impuls(e), form, df.index[i]


SPANNE = {"Woche": pd.Timedelta(days=7), "Tag": pd.Timedelta(days=1), "Stunde": pd.Timedelta(hours=1)}


def _von_bis(e, t):
    """Zeitraum der Kerze t der Ebene in feineren Kerzen: die Woche trägt den Freitag als Namen (W-FRI)."""
    t = pd.Timestamp(t)
    if e["name"] == "Woche":
        return t - pd.Timedelta(days=6), t + pd.Timedelta(days=1)  # Technik: Montag bis Freitag
    return t, t + SPANNE[e["name"]]


def _doppel(teil, schritt):
    """Volumen- und Zeitprofil (Market Profile: eine Marke je Kerze und berührter Stufe) auf denselben Stufen."""
    pr = tiefe.profil(teil["High"], teil["Low"], teil["Volume"], schritt)
    zp = tiefe.profil(teil["High"], teil["Low"], [1.0] * len(teil), schritt)
    pr["zeit"], pr["tpoc"] = zp["volumen"], zp["poc"]
    return pr


def profil_impuls(e):
    """Das eine Profil der Ebene: ab Beginn des Impulses der Zone von heute (ohne Impuls ab Beginn der Balance), aus den
    feineren Kerzen, sonst aus denen der Ebene → tiefe.profil plus zeit, tpoc, ab, quelle."""
    df, pb, fein = e["df"], e.get("pbd"), e.get("fein")
    ab_ = pd.Timestamp(pb["impuls_tag"] if pb else e["struktur"]["balance_start"])
    ab = _von_bis(e, ab_)[0]
    schritt = tiefe.stufe(float(df["Close"].iloc[-1]))
    f_ = fein[fein.index >= ab] if fein is not None and len(fein) else None
    if f_ is not None and len(f_) >= tiefe.STUNDEN_MIN and f_.index[0] <= ab + pd.Timedelta(days=tiefe.ZEIT_VERSATZ):
        teil, quelle = f_, "fein"
    else:
        teil, quelle = df[df.index >= ab_], "Ebene"
    pr = _doppel(teil, schritt)
    pr["ab"], pr["quelle"] = ab_, quelle
    return pr


def wanderung(e, beginn):
    """POC-Wanderung in der Zone von heute: POC des Volumens seit Beginn der Zone bis zu jeder Kerze (Serie), aus den
    feineren Kerzen, sonst aus denen der Ebene."""
    df, fein = e["df"], e.get("fein")
    schritt = tiefe.stufe(float(df["Close"].iloc[-1]))
    von = _von_bis(e, beginn)[0]
    tage = df.index[df.index >= pd.Timestamp(beginn)]
    f_ = fein[fein.index >= von] if fein is not None and len(fein) else None
    if f_ is None or not len(f_) or f_.index[0] > von + pd.Timedelta(days=tiefe.ZEIT_VERSATZ):
        f_ = None
    werte = {}
    for t in tage:
        bis = f_[f_.index < _von_bis(e, t)[1]] if f_ is not None else df[(df.index >= pd.Timestamp(beginn)) & (df.index <= t)]
        if len(bis):
            werte[t] = tiefe.profil(bis["High"], bis["Low"], bis["Volume"], schritt)["poc"]
    return pd.Series(werte, dtype=float)


def lage(e):
    """Zone, Phase und Richtung einer Ebene (tiefe.ebene) → dict oder None."""
    if not e:
        return None
    lo, hi, pr, form, beginn = _zone(e)
    poc = pr["poc"]
    pb, df = e.get("pbd"), e["df"]
    kurs = float(df["Close"].iloc[-1])
    phase, richt = "balance", 0
    if pb:
        auf = pb["aufwaerts"]
        richt = 1 if auf else -1
        if pb["gescheitert"]:
            phase, richt = "gescheitert", -richt
        elif pb["seite"] and pb["zaehl"] >= GESCHEITERT:
            phase = "aus_auf" if pb["seite"] == "oben" else "aus_ab"
        elif pb["seite"]:
            phase = "test"
        elif pb["kante"]:
            phase = "kante"
        if phase in ("balance", "kante") and form == "D":
            richt = 0
    elif kurs >= hi or kurs <= lo:
        phase = "kante"
    z, wort = PHASE[phase]
    return {"zone": (float(lo), float(hi)), "poc": float(poc), "profil": pr, "beginn": beginn, "form": form,
            "phase": phase, "zeichen": z,
            "wort": wort, "richtung": richt, "pfeil": {1: "↗", -1: "↘", 0: "→"}[richt], "kurs": kurs,
            "zaehl": pb["zaehl"] if pb else 0, "seite": pb["seite"] if pb else None, "kante": pb["kante"] if pb else None}


def trade(e, la):
    """Der eine Zonen-Trade der Tagesebene jetzt → {art, richtung (1/−1), einstieg, stopp, ziel, crv} oder None."""
    pb = e.get("pbd") if e else None
    if not pb or not la:
        return None
    df, a = e["df"], e["atr"]
    lo, hi = la["zone"]
    kurs = la["kurs"]
    n = pb["zaehl"]
    t = None
    if la["phase"] in ("balance", "kante") and pb["kante"] and not pb["seite"]:
        tr = pb["d_long"] if pb["kante"] == "unten" else pb["d_short"]
        t = {"art": "pendel", "richtung": 1 if pb["kante"] == "unten" else -1, "einstieg": tr["einstieg"],
             "stopp": tr["stopp"], "ziel": tr["ziel"]}
    elif la["phase"] in ("aus_auf", "aus_ab") and n <= FRISCH_SCHLUESSE:
        r = 1 if la["phase"] == "aus_auf" else -1
        kante = hi if r > 0 else lo
        nah = pb["kantenabstand"]
        rueck = (float(df["Low"].iloc[-1]) <= kante + nah) if r > 0 else (float(df["High"].iloc[-1]) >= kante - nah)
        seit = df.iloc[len(df) - n:]
        if rueck:
            t = {"art": "ruecktest", "richtung": r, "einstieg": kante, "stopp": kante - r * a * STOPP_ATR,
                 "ziel": float(seit["High"].max() if r > 0 else seit["Low"].min())}
        else:
            t = {"art": "ausbruch", "richtung": r, "einstieg": kurs, "stopp": (lo + hi) / HALB,
                 "ziel": kante + r * (hi - lo)}
    elif la["phase"] == "gescheitert" and n <= FRISCH_SCHLUESSE:
        r = la["richtung"]
        t = {"art": "gegen", "richtung": r, "einstieg": kurs,
             "stopp": (hi + a * STOPP_ATR) if r < 0 else (lo - a * STOPP_ATR), "ziel": pb["impuls_kurs"]}
    if t:
        risiko = abs(t["einstieg"] - t["stopp"])
        t["crv"] = round(abs(t["ziel"] - t["einstieg"]) / risiko, 1) if risiko else None
        t["name"], t["zeichen"] = TRADE_NAME[t["art"]], TRADE_ZEICHEN[t["art"]]
    return t


def _d_zonen(O, C, a, b, atr_wert, aus, band):
    """D-Zonen zwischen den Kerzen a und b (einschließlich): 3 Kerzen, deren Körper zusammen keine 2 ATR überspannen,
    danach fortgeschrieben wie die faire Zone; Ende beim 2. Schluss draußen. Kerzen ohne Zone tragen weiter, was sie
    vorher trugen (Ausbruch, Scheitern oder nichts)."""
    k = a
    while k + ZONE_MIN - 1 <= b:
        koerper = [x for j in range(k, k + ZONE_MIN) for x in (O[j], C[j])]
        if max(koerper) - min(koerper) >= D_ATR * atr_wert:
            k += 1
            continue
        zt, zh, letzte, zaehl = min(koerper), max(koerper), k + ZONE_MIN - 1, 0
        j = letzte + 1
        while j <= b:
            if zt <= C[j] <= zh:
                zt, zh, letzte, zaehl = min(zt, O[j], C[j]), max(zh, O[j], C[j]), j, 0
            else:
                zaehl += 1
                if zaehl >= GESCHEITERT:
                    break
            j += 1
        aus.append({"art": "D", "s": k, "e": letzte, "tief": zt, "hoch": zh, "auf": None,
                    "aus": "oben" if j <= b and C[j] > zh else "unten" if j <= b else None})
        for x in range(k, letzte + 1):
            band[x] = "b"
        k = letzte + 1


def kette(df, atr_wert):
    """Die PbD-Kette der Ebene (Regel im Kopf dieser Datei) → (Zonen, Band). Zone = {art P/b/D, s, e (Positionen),
    tief, hoch (Körper), auf, aus (oben/unten/None)}; Band je Kerze: i+/i- Impuls, b Zone, a+/a- Ausbruch, f Scheitern."""
    n = len(df)
    band, aus = [None] * n, []
    if atr_wert is None or not atr_wert > 0 or n < 2 * ZONE_MIN:
        return aus, band
    O, C, L, H = (df[k].to_numpy(float) for k in ("Open", "Close", "Low", "High"))
    start_kurs = lambda i, auf: float(L[i] if auf else H[i])                       # noqa: E731
    gilt, akt = [], None                                                            # maßgebliche Impulse wie tiefe.pbd
    for imp in tiefe.impulse(df, atr_wert, suche=n):
        if imp[1] > n - 2:
            continue
        if akt is not None:
            if imp[0] <= akt[1]:
                continue
            zt, zh = tiefe._zone(O, C, start_kurs(akt[0], akt[2]), akt[1], akt[2], imp[0])[:2]
            if not (C[imp[1]] > zh or C[imp[1]] < zt):
                continue
        akt = imp
        gilt.append(imp)
    _d_zonen(O, C, 0, (gilt[0][0] - 1) if gilt else n - 1, atr_wert, aus, band)
    for k, (s_, e_, auf, _) in enumerate(gilt):
        for j in range(s_, e_ + 1):
            band[j] = "i+" if auf else "i-"
        bis = gilt[k + 1][0] - 1 if k + 1 < len(gilt) else n - 1
        ende, aus_seite = bis, None
        for j in range(e_ + 1, bis + 1):
            zaehl, seite = tiefe._zone(O, C, start_kurs(s_, auf), e_, auf, j)[4:6]  # Technik: Felder von tiefe._zone
            if seite and zaehl >= GESCHEITERT:
                ende, aus_seite = j - zaehl, seite
                break
        zt, zh = tiefe._zone(O, C, start_kurs(s_, auf), e_, auf, ende)[:2]
        aus.append({"art": "P" if auf else "b", "s": e_, "e": ende, "tief": zt, "hoch": zh, "auf": auf, "aus": aus_seite})
        for j in range(e_ + 1, ende + 1):
            band[j] = "b"
        if aus_seite:
            mit = (aus_seite == "oben") == bool(auf)
            for j in range(ende + 1, bis + 1):
                band[j] = ("a+" if aus_seite == "oben" else "a-") if mit else "f"
            _d_zonen(O, C, ende + 1, bis, atr_wert, aus, band)
    aus.sort(key=lambda z: z["s"])
    return aus, band


def historie(e, ab):
    """Zonen der Vergangenheit der Ebene seit Kerze ab nach der PbD-Kette, älteste zuerst, ohne die Zone von heute –
    je mit Körper (tief–hoch), Dochten, Volumenprofil (POC, Wertzone), offen und nackt."""
    if not e:
        return []
    df, fein = e["df"], e.get("fein")
    zonen_, _ = _kette(e)
    pb = e.get("pbd")
    heute = pd.Timestamp(pb["zone_start"]) if pb else pd.Timestamp(e["struktur"]["balance_start"])
    schritt = tiefe.stufe(float(df["Close"].iloc[-1]))
    L, H = df["Low"].to_numpy(float), df["High"].to_numpy(float)
    erg = []
    for z in zonen_:
        if z["e"] < ab or z["e"] - z["s"] + 1 < (D_MIN if z["art"] == "D" else ZONE_MIN) or df.index[z["s"]] >= heute:
            continue
        von, bis = _von_bis(e, df.index[z["s"]])[0], _von_bis(e, df.index[z["e"]])[1]
        f_ = fein[(fein.index >= von) & (fein.index < bis)] if fein is not None and len(fein) else None
        teil = f_ if f_ is not None and len(f_) >= tiefe.STUNDEN_MIN else df.iloc[z["s"]:z["e"] + 1]
        pr = tiefe.profil(teil["High"], teil["Low"], teil["Volume"], schritt)
        nach = slice(z["e"] + 1, len(df))
        beruehrt = (L[nach] <= pr["poc"]) & (H[nach] >= pr["poc"])
        erg.append({"form": z["art"], "tief": float(z["tief"]), "hoch": float(z["hoch"]),
                    "docht_tief": float(L[z["s"]:z["e"] + 1].min()), "docht_hoch": float(H[z["s"]:z["e"] + 1].max()),
                    "poc": float(pr["poc"]), "val": float(pr["val"]), "vah": float(pr["vah"]),
                    "start": df.index[z["s"]], "ende": df.index[z["e"]], "aus": z["aus"],
                    "offen": not bool(((L[nach] <= pr["vah"]) & (H[nach] >= pr["val"])).any()),
                    "nackt": not bool(beruehrt.any()),
                    "beruehrt": df.index[z["e"] + 1 + int(beruehrt.argmax())] if beruehrt.any() else None})
    return erg


def _kette(e):
    """kette() der Ebene, einmal gerechnet."""
    if "_kette" not in e:
        e["_kette"] = kette(e["df"], e["atr"])
    return e["_kette"]


def band(e):
    """Phase je Kerze der Ebene nach der PbD-Kette (Liste wie kette)."""
    return _kette(e)[1]


def naechste(alt, kurs):
    """Die nächste offene alte Zone über und unter dem Kurs (die Magnete) – höchstens zwei, damit das Bild schmal
    bleibt (Micky 21.11.2026: wenig, aber aussagekräftig)."""
    offen = [z for z in alt if z["offen"]]
    ueber = min((z for z in offen if z["val"] > kurs), key=lambda z: z["val"], default=None)
    unter = max((z for z in offen if z["vah"] < kurs), key=lambda z: z["vah"], default=None)
    return [z for z in (ueber, unter) if z]


def fuehrte(ebenen):
    """Alles für Kopfzeile und Chart: Lage je Ebene, der Trade des Tages, Einigkeit, Muster, alte Zonen."""
    la = {n: lage(ebenen.get(n)) for n in EBENEN}
    t = trade(ebenen.get("Tag"), la["Tag"])
    bezug = t["richtung"] if t else (la["Tag"] or {}).get("richtung", 0)
    einig = sum(1 for n in EBENEN if la[n] and bezug and la[n]["richtung"] == bezug) if bezug else 0
    if t and la["Tag"] and la["Tag"]["richtung"] != bezug:
        einig += 1                                   # der Trade selbst zählt für den Tag (Pendel gegen die Form)
    muster = None
    if la["Tag"] and la["Woche"]:
        (lo, hi), (wl, wh) = la["Tag"]["zone"], la["Woche"]["zone"]
        muster = "innen" if wl <= lo and hi <= wh else "darüber" if lo > wh else "darunter" if hi < wl else "überlappend"
    return {"lage": la, "trade": t, "einig": min(einig, len(EBENEN)), "richtung": bezug, "muster": muster,
            "alt": {n: historie(ebenen.get(n), 0) for n in EBENEN}}


def einig_zeichen(f):
    """Zeichen der Einigkeit: 🦬 bzw. 🐻 so oft, wie Ebenen mitziehen; ohne Richtung 🟡."""
    if not f["richtung"]:
        return "🟡"
    return ("🦬" if f["richtung"] > 0 else "🐻") * max(1, f["einig"])
