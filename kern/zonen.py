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
Gedächtnis: alte Zonen (frühere Balancen ab 10 Kerzen, tiefe.alte_balance) – offen, solange der Kurs seit ihrem Ende
  nie wieder in ihre Wertzone lief (Magnet), sonst erledigt. Muster: liegt die Tageszone innerhalb der Wochenzone, setzt
  sich die Woche fort (innen), sonst darüber bzw. darunter.
"""
import tiefe

FRISCH = 5                 # Ausbruch und Gegentrade gelten bis 5 Schlüsse draußen
GESCHEITERT = tiefe.GESCHEITERT    # 2 Schlüsse draußen (Vorwald) – eine Quelle
ALTE_ZONEN = 3             # höchstens 3 alte Zonen je Ebene
ALT_SUCHE_N = 8            # … gesucht unter den 8 Balancen davor
STOPP_ATR = tiefe.STOPP_ATR        # ¼ ATR jenseits der Kante – eine Quelle
HALB = 2                   # Mitte der Zone
EBENEN = ("Woche", "Tag", "Stunde")
PHASE = {"leer": ("⚪", "ungemessen"), "balance": ("🟡", "Balance"), "kante": ("💥", "an der Kante"),
         "test": ("💥", "erster Schluss draußen"), "aus_auf": ("🦬", "Ausbruch"), "aus_ab": ("🐻", "Ausbruch"),
         "gescheitert": ("🦊", "gescheitert")}
TRADE_NAME = {"pendel": "Pendel", "ausbruch": "Ausbruch", "ruecktest": "Rücktest", "gegen": "Gegentrade"}
TRADE_ZEICHEN = {"pendel": "🟡", "ausbruch": "💥", "ruecktest": "🪝", "gegen": "🦊"}


def _zone(e):
    """(tief, hoch, poc, form) der Ebene: faire Zone nach Vorwald, ohne Impuls der Rand der Balance. POC = Volumen
    seit Beginn der Zone (ihr Bauch); eine Zone, die schmaler als ¼ ATR ist (erst eine Kerze), reicht über die Spanne
    ihrer ersten Kerze (Claude, 21.11.2026)."""
    pb, st_, df = e.get("pbd"), e["struktur"], e["df"]
    if not pb:
        return st_["short_pivot"], st_["pivot"], st_["profil"]["poc"], "D"
    lo, hi = pb["zone_tief"], pb["zone_hoch"]
    i = int(df.index.searchsorted(pb["zone_start"]))
    if e["atr"] and hi - lo < e["atr"] * STOPP_ATR:
        lo, hi = min(lo, float(df["Low"].iloc[i])), max(hi, float(df["High"].iloc[i]))
    teil = df.iloc[i:]
    poc = tiefe.profil(teil["High"], teil["Low"], teil["Volume"], tiefe.stufe(float(df["Close"].iloc[-1])))["poc"]
    return lo, hi, poc, pb["form"]


def lage(e):
    """Zone, Phase und Richtung einer Ebene (tiefe.ebene) → dict oder None."""
    if not e:
        return None
    lo, hi, poc, form = _zone(e)
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
    return {"zone": (float(lo), float(hi)), "poc": float(poc), "form": form, "phase": phase, "zeichen": z,
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
    elif la["phase"] in ("aus_auf", "aus_ab") and n <= FRISCH:
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
    elif la["phase"] == "gescheitert" and n <= FRISCH:
        r = la["richtung"]
        t = {"art": "gegen", "richtung": r, "einstieg": kurs,
             "stopp": (hi + a * STOPP_ATR) if r < 0 else (lo - a * STOPP_ATR), "ziel": pb["impuls_kurs"]}
    if t:
        risiko = abs(t["einstieg"] - t["stopp"])
        t["crv"] = round(abs(t["ziel"] - t["einstieg"]) / risiko, 1) if risiko else None
        t["name"], t["zeichen"] = TRADE_NAME[t["art"]], TRADE_ZEICHEN[t["art"]]
    return t


def alte_zonen(e):
    """Frühere Balancen der Ebene mit Stand: offen = seit ihrem Ende nie wieder in ihrer Wertzone (Magnet), erledigt =
    der Kurs lief wieder hinein. Gezeigt werden die nächste offene darüber und darunter (naechste())."""
    if not e:
        return []
    df = e["df"]
    aus, vor = [], e["struktur"]["anker_i"]
    for _ in range(ALT_SUCHE_N):
        b = tiefe.alte_balance(df, vor)
        if not b:
            break
        nach = df.loc[df.index > b["ende"]]
        offen = not ((nach["Low"] <= b["vah"]) & (nach["High"] >= b["val"])).any()
        aus.append({"val": b["val"], "vah": b["vah"], "poc": b["poc"], "start": b["start"], "ende": b["ende"],
                    "offen": bool(offen)})
        vor = int(df.index.searchsorted(b["start"]))
        if sum(x["offen"] for x in aus) >= ALTE_ZONEN:
            break
    return aus


def historie(e, ab):
    """Alle Balancen der Ebene seit Kerze ab (Zonen der Vergangenheit, Micky 21.11.2026), älteste zuerst, je mit
    Spanne (tief–hoch), Wertzone und Stand (offen = seit ihrem Ende nie wieder in ihrer Wertzone)."""
    if not e:
        return []
    df = e["df"]
    aus, vor = [], e["struktur"]["anker_i"]
    while vor > ab:
        b = tiefe.alte_balance(df, vor)
        if not b or int(df.index.searchsorted(b["ende"])) < ab:
            break
        nach = df.loc[df.index > b["ende"]]
        aus.append({"val": b["val"], "vah": b["vah"], "poc": b["poc"], "tief": b["tief"], "hoch": b["hoch"],
                    "start": b["start"], "ende": b["ende"],
                    "offen": not bool(((nach["Low"] <= b["vah"]) & (nach["High"] >= b["val"])).any())})
        vor = int(df.index.searchsorted(b["start"]))
    return aus[::-1]


def phasenband(df, zonen_, la, zone_start):
    """Phase je Kerze (Micky 21.11.2026): in einer Zone (Kasten der Vergangenheit bzw. die Zone von heute ab ihrem
    Beginn) Balance, sonst gegen die letzte Zone davor: Schluss darüber Ausbruch oben, darunter Ausbruch unten.
    → Liste 'b'/'o'/'u'/None je Kerze von df."""
    c = df["Close"].to_numpy(float)
    kaesten = [(z["start"], z["ende"], z["tief"], z["hoch"]) for z in zonen_]
    if la:
        kaesten.append((zone_start, df.index[-1], la["zone"][0], la["zone"][1]))
    aus, letzte = [], None
    for i, t in enumerate(df.index):
        drin = next((k for k in kaesten if k[0] <= t <= k[1]), None)
        if drin:
            letzte = drin
            aus.append("b" if drin[2] <= c[i] <= drin[3] else "o" if c[i] > drin[3] else "u")
            continue
        aus.append(None if letzte is None else "o" if c[i] > letzte[3] else "u" if c[i] < letzte[2] else "b")
    return aus


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
            "alt": {n: alte_zonen(ebenen.get(n)) for n in EBENEN}}


def einig_zeichen(f):
    """Zeichen der Einigkeit: 🦬 bzw. 🐻 so oft, wie Ebenen mitziehen; ohne Richtung 🟡."""
    if not f["richtung"]:
        return "🟡"
    return ("🦬" if f["richtung"] > 0 else "🐻") * max(1, f["einig"])
