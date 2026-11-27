"""Spannen, Phasen, Strömung – das schlanke Cockpit (Micky 21./22.11.2026).

Grundsatz: Eine Spanne ist das Gerüst im Chart (der Nordstern). Reagieren statt antizipieren: gehandelt wird der
Ausbruch aus der Spanne, der Rücktest an die gebrochene Kante und der Bruch der Unterkante – sonst nichts.

Die Spanne je Ebene (Micky 27.11.2026, Einheitlichkeit): Livermores Spanne auf allen vier Ebenen aus ihren eigenen
  Kerzen (vcp_zone.zone, livermore.spanne): Oberkante = letzter Pivotal Point oben = Front, Unterkante = letzter
  Pivotal Point unten; beide stehen, bis ein Schluss 1 ATR jenseits liegt (Regel 1, livermore.steht) – dieselbe Front
  und Unterkante wie im Lagebericht. Läuft gerade ein Ausbruch (vcp_zone.ausbruch, 4 Wochen in Zeit), gilt die Spanne,
  aus der er kam; ist ihre Front gefallen, heißt sie alte Spanne mit alter Front (die Linie des Rücktests). Unter
  NOTIZBUCH_MIN Kerzen: zu wenig Kerzen (kein zweites Messgerät).
Phase (Zeichenliste): 🟡 Spanne im Aufbau · 🦬 an der Front (in der Kipp-Zone, bis 1 ATR darunter) ·
  🦬 Ausbruch (Schluss über der Front) · 🪝 Rücktest · 🦊 Fehlausbruch · 🐻 Bruch der Unterkante · 🔴 Unterkante gefallen
  · ⚪ keine Spanne (Kurs läuft am Hoch).
Die drei Trades (Spanne des Tages, Micky 22.11.2026):
  Ausbruch    long: Auslöser = Front (Schluss darüber, Volumen über dem 50-Tage-Schnitt); Stopp = ¼ ATR unter
              Livermores Pivotal Point unten (der Unterkante, 25.11.2026), höchstens 8 % (Minervini, MAX_STOPP). Vor dem Ausbruch wartet er an der Front.
  Rücktest    nach dem Ausbruch zurück an die Front (vcp_zone.ausbruch: Schluss knapp darunter, kein Fehlausbruch):
              Einstieg an der Front, Stopp ¼ ATR darunter.
  Short       Bruch der Unterkante: Schluss unter der Unterkante der Spanne von gestern, mit Volumen über dem
              50-Tage-Schnitt; Stopp ¼ ATR über der gebrochenen Kante (ein laufender Rücksetzer bricht nichts).
Kein festes Ziel (Micky: Gewinne laufen lassen, Stopp nachziehen) – die Ampel zeigt das Risiko: 🟢 bis 8 %, 🔴 darüber.
Profil (Micky 21.11.2026: nur eines, aber aussagekräftig): Zeit und Volumen gespiegelt in einer Silhouette, verankert am
  Beginn der Spanne (bzw. am eigenen Anker), aus den feineren Kerzen der Ebene; sein POC ist der POC der Spanne.
Stellungen (Micky 25./26.11.2026, nur Livermore, eine Rechnung: livermore.offene → front, stellungen, frei): jeder
Pivotal Point der letzten 2 Jahre, den kein Schluss 1 ATR jenseits durchbrochen hat; über dem Kurs eine Decke, darunter
ein Boden, in Richtung des Setups das Ziel; je Richtung die 2 nächsten.
Freie Bahn ✈️ (Micky 22.11.2026, Livermores Linie des geringsten Widerstands): über dem Kurs steht keine Stellung mehr
(auch nicht die Front); ✈️↓ gespiegelt für den Short.
Reines Zeichen ohne Schwelle: wie leicht der Kurs läuft, zeigen Front, Volumen-Spur, 🏜️ und Kraft ohne Weg.
"""
import numpy as np
import pandas as pd

import tiefe
import vcp_zone
MAX_STOPP = 0.08           # Minervini: höchstens 8 % Risiko je Trade (der Stopp wird nie weiter gesetzt)
from tiefe import STOPP_ATR            # ¼ ATR jenseits der Kante – eine Quelle
from masse import NOTIZBUCH_MIN, VOL_TAGE   # Volumen über dem 50-Tage-Schnitt (Micky: reicht für den Ausbruch) – eine Quelle
from livermore import BESTAETIGUNG     # Kipp-Zone: 1 ATR um die Kante – eine Quelle

EBENEN = ("Woche", "Tag", "4 Stunden", "Stunde")   # wie Mickys Favoriten in TradingView (1W, 1T, 4h, 1h)
PHASE = {"aufbau": ("🟡", "Spanne im Aufbau"), "kante": ("🦬", "an der Front"),
         "ausbruch": ("🦬", "Ausbruch"), "ruecktest": ("🪝", "Rücktest"), "fehl": ("🦊", "Fehlausbruch"),
         "bruch": ("🐻", "Bruch der Unterkante"), "gefallen": ("🔴", "Unterkante gefallen – keine Spanne"),
         "hoch": ("⚪", "keine Spanne – Kurs läuft am Hoch")}
RICHTUNG = {"ausbruch": 1, "ruecktest": 1, "fehl": -1, "bruch": -1, "gefallen": -1}
TRADE_NAME = {"ausbruch": "Ausbruch", "ruecktest": "Rücktest", "short": "Bruch der Unterkante"}
TRADE_ZEICHEN = {"ausbruch": "🦬", "ruecktest": "🪝", "short": "🐻"}


SPANNE = {"Woche": pd.Timedelta(days=7), "Tag": pd.Timedelta(days=1), "4 Stunden": pd.Timedelta(hours=4),
          "Stunde": pd.Timedelta(hours=1)}


def _von_bis(e, t):
    """Zeitraum der Kerze t der Ebene in feineren Kerzen: die Woche trägt den Freitag als Namen (W-FRI)."""
    t = pd.Timestamp(t)
    if e["name"] == "Woche":
        return t - pd.Timedelta(days=6), t + pd.Timedelta(days=1)  # Technik: Montag bis Freitag
    return t, t + SPANNE[e["name"]]


def _doppel(teil, schritt):
    """Volumen- und Zeitprofil (Market Profile: eine Marke je Kerze und berührter Stufe) auf denselben Stufen, dazu die
    Truppen (Micky 21.11.2026, Näherung ohne Orderdaten): das Volumen steigender Kerzen zählt zu den Käufern."""
    pr = tiefe.profil(teil["High"], teil["Low"], teil["Volume"], schritt)
    zp = tiefe.profil(teil["High"], teil["Low"], [1.0] * len(teil), schritt)
    auf = (teil["Close"] >= teil["Open"]).to_numpy()
    kp = tiefe.profil(teil["High"], teil["Low"], teil["Volume"].where(auf, 0.0), schritt)
    pr["zeit"], pr["tpoc"], pr["kauf"] = zp["volumen"], zp["poc"], kp["volumen"]
    return pr


def profil_seit(e, ab_):
    """Zeit- und Volumenprofil ab Kerze ab_ der Ebene bis heute (auch am eigenen Anker, Micky 21.11.2026), aus den
    feineren Kerzen, sonst aus denen der Ebene → tiefe.profil plus zeit, tpoc, ab, quelle."""
    df, fein = e["df"], e.get("fein")
    ab_ = pd.Timestamp(ab_)
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


def basis(df):
    """Die Base des Titels aus Tageskerzen für Woche und Tag (vcp_zone, Livermores Spanne): {"z", "ausbruch", "jetzt",
    "bruch", "nb", "df"}
    – z datiert (Index → Datum), oder None, wenn der Kurs am Hoch läuft."""
    import livermore
    df = df.dropna(subset=["High", "Low", "Close"])
    nb = livermore.notizbuch(df)
    jetzt = vcp_zone.zone(df, nb)
    a = vcp_zone.ausbruch(df, jetzt=jetzt, nb=nb)
    gestern = vcp_zone.zone(df.iloc[:-1], nb) if len(df) > 1 else {}
    bruch = bool(not a and gestern.get("zone") and float(df["Close"].iloc[-1]) < gestern["unten"])
    if bruch:                                    # Bruch der Unterkante: die Spanne von gestern
        b = gestern
    elif a:                                      # Ausbruch: steht seine Front noch (Kipp-Zone), gilt die Spanne von heute –
        b = jetzt if jetzt.get("zone") else a["zone"]   # dieselbe wie im Lagebericht; sonst die alte Spanne (27.11.)
    else:
        b = jetzt if jetzt.get("start_i") is not None else None
    return {"z": vcp_zone.datiert(df, b) if b else None, "ausbruch": a, "jetzt": jetzt, "df": df, "bruch": bruch, "nb": nb}


def _volumen_hoch(df):
    v = df["Volume"].astype(float)
    schnitt = v.rolling(VOL_TAGE, min_periods=VOL_TAGE // 2).mean().shift()   # Technik: halbe Länge reicht zum Start
    return bool(schnitt.iloc[-1] == schnitt.iloc[-1] and v.iloc[-1] > schnitt.iloc[-1])


KERZE = {"Tag": "T.", "Woche": "Wo.", "4 Stunden": "4h", "Stunde": "Std."}   # Einheit der Kerzen je Ebene


def lage(e, ba=None, profil=True):
    """Spanne, Phase und Richtung einer Ebene → dict, aus ihrer Spanne ba (basis() auf den Kerzen der Ebene, 26.11.2026);
    None ohne Notizbuch (zu wenig Kerzen – kein zweites Messgerät, Micky 27.11.2026).
    profil=False (Zirkel-Lauf über alle Titel, nur Tageskurse): ohne Volumenprofil, poc und profil sind None."""
    if not e or ba is None:
        return None
    df = e["df"]
    kurs = float(df["Close"].iloc[-1])
    z, a = ba["z"], ba["ausbruch"]
    if z is None:                              # keine Spanne: Front gefallen (Kurs läuft am Hoch) oder Unterkante
        gef = "gefallen" if (ba.get("jetzt") or {}).get("gefallen") == "unten" else "hoch"   # gefallen (27.11.)
        z_, w_ = PHASE[gef]                    # das Profil ab dem Start der Bewegung: dem letzten Pivotal Point
        art_ = "tief" if gef == "hoch" else "hoch"                              # der Gegenseite (Micky 26.11.)
        pp_ = next((p_ for p_ in reversed((ba.get("nb") or {}).get("pivotal") or []) if p_["art"] == art_), None)
        ab_ = pp_["tag"] if pp_ is not None else e["struktur"]["balance_start"]
        pr = profil_seit(e, ab_) if profil else None
        r_ = RICHTUNG.get(gef, 0)
        return {"zone": None, "phase": gef, "zeichen": z_, "wort": w_, "richtung": r_, "pfeil": {1: "↗", -1: "↘", 0: "→"}[r_],
                "kurs": kurs, "name": "", "info": "", "pivot": None, "poc": float(pr["poc"]) if pr else None,
                "profil": pr, "beginn": None, "spalte": (ba.get("nb") or {}).get("spalte"),
                "kante": (ba.get("jetzt") or {}).get("kante")}
    lo, hi, beginn = float(z["unten"]), float(z["oben"]), pd.Timestamp(z["start_t"])
    alt = not (ba.get("jetzt") or {}).get("zone")     # Kante gefallen (Ausbruch, Bruch): die alte Spanne (27.11.)
    pivot = float(a["pivot"]) if a else float(z.get("pivot") or hi)   # Livermores Pivotal Point
    td = ba["df"]
    if a and a["fehl"]:
        phase = "fehl"
    elif a:
        phase = "ruecktest" if a["ruecktest"] else "ausbruch"
    elif ba["bruch"]:
        phase = "bruch"
    elif float(td["Close"].iloc[-1]) >= pivot - BESTAETIGUNG * float(vcp_zone.atr(td).iloc[-1] or 0):
        phase = "kante"                                # an der Front = in der Kipp-Zone, bis 1 ATR darunter (27.11.)
    else:
        phase = "aufbau"
    name = "alte Spanne" if alt else (z.get("name") or "Spanne")
    dauer = (f'seit {beginn:%d.%m. %H:%M}' if e["name"] in tiefe.INTRADAY          # Dauer in Kalenderwochen, gleich
             else f'{max(0, (df.index[-1] - beginn).days) / 7:.0f} Wo.')                # auf jeder Ebene (26.11.)
    teile = [dauer, f'{z["tiefe"]:.0f} % tief'.replace(".", ",")]
    if a and not a["fehl"]:
        ein_ = KERZE.get(e["name"], "T.")
        teile.append(f'Ausbruch vor {a["tage_her"]} {ein_} ' + ("mit Volumen" if a["mit_volumen"] else "ohne Volumen"))
        teile.append(vcp_zone.wucht(a, ein_))                                   # Masse mal Geschwindigkeit (26.11.)
    info = " · ".join(teile)
    pr = profil_seit(e, beginn) if profil else None
    z_, w_ = PHASE[phase]
    r = RICHTUNG.get(phase, 0)
    return {"zone": (lo, hi), "pivot": pivot, "alt": alt, "poc": float(pr["poc"]) if pr else None, "profil": pr, "beginn": beginn, "name": name,
            "info": info, "phase": phase, "zeichen": z_, "wort": w_, "richtung": r,
            "pfeil": {1: "↗", -1: "↘", 0: "→"}[r], "kurs": kurs, "spalte": ((ba or {}).get("nb") or {}).get("spalte")}


def trade(e, la, ba):
    """Der eine Trade der Tagesebene → {art, richtung, einstieg, stopp, pivot, risiko, ampel, wartet, name, zeichen} oder
    None; pivot = die Kante, die der Trade überwinden bzw. brechen muss (long die Front, short die Unterkante)."""
    if not e or not la or la.get("zone") is None or ba is None or ba["z"] is None:
        return None
    a = ba["ausbruch"]
    atr = e["atr"] or 0
    kurs, pivot, lo = la["kurs"], la["pivot"], la["zone"][0]
    t = None
    if la["phase"] in ("ausbruch", "kante", "aufbau"):
        struktur = min(lo, pivot) - atr * STOPP_ATR     # Struktur-Stopp: ¼ ATR unter Livermores Pivotal Point unten
        stopp = max(struktur, pivot * (1 - MAX_STOPP))  # … höchstens 8 % (Minervini)
        if la["phase"] != "ausbruch" or a.get("kaufzone"):
            t = {"art": "ausbruch", "richtung": 1, "einstieg": pivot, "stopp": stopp, "wartet": la["phase"] != "ausbruch"}
    elif la["phase"] == "ruecktest":
        t = {"art": "ruecktest", "richtung": 1, "einstieg": pivot, "stopp": pivot - atr * STOPP_ATR, "wartet": False}
    elif la["phase"] == "bruch" and _volumen_hoch(ba["df"]):
        t = {"art": "short", "richtung": -1, "einstieg": kurs, "stopp": lo + atr * STOPP_ATR, "wartet": False}
    if t:
        t["pivot"] = pivot if t["richtung"] > 0 else lo
        t["risiko"] = round(abs(t["einstieg"] - t["stopp"]) / t["einstieg"] * 100, 1)
        t["ampel"] = "🟢" if t["risiko"] <= MAX_STOPP * 100 else "🔴"
        t["name"], t["zeichen"] = TRADE_NAME[t["art"]], TRADE_ZEICHEN[t["art"]]
        t["zone_trend"] = ba["z"].get("trend") or "AT"     # Livermores Trend der Spanne: Fortsetzung oder Umkehr
        if t["art"] in ("ausbruch", "short") and atr:      # Antasten und Aufstocken (Micky 26.11.2026, Livermore: erst
            import livermore                               # eine Probe, nur im Gewinn nachlegen, nie verbilligen):
            t["aufstocken"] = (pivot + livermore.BESTAETIGUNG * atr if t["richtung"] > 0     # ½ beim Schluss jenseits
                               else lo - livermore.BESTAETIGUNG * atr)                       # der Kante, ½ bei 📒
            if t["richtung"] > 0:                            # 📒 = ein Hoch 1 ATR über der Front (vcp_zone.ausbruch)
                t["aufgestockt"] = bool(a and a.get("bestaetigt"))
            else:                                            # short gespiegelt: ein Tief 1 ATR unter der Unterkante seit
                td = ba["df"]                                # dem Bruch (die Kerzen seit dem letzten Schluss über ihr)
                ueber = np.nonzero(td["Close"].to_numpy(float) >= lo)[0]
                seit = td["Low"].iloc[(int(ueber[-1]) + 1) if len(ueber) else 0:]
                t["aufgestockt"] = bool(len(seit) and float(seit.min()) <= t["aufstocken"])
    return t


KNOTEN_ANTEIL = 0.5        # Knoten (HVN): Gipfel mit mindestens ½ des POC-Volumens (Claude 21.11.2026, ungemessen)
KNOTEN_MAX = 3             # höchstens die 3 dicksten Knoten
KNOTEN_GLAETTEN = 3        # Gipfel auf dem über 3 Stufen geglätteten Profil (gegen Zacken)


def profil_details(pr):
    """Profil-Details nach Dalton (Micky 21.11.2026): Wertzone (VAL–VAH, 70 %), Knoten (HVN: Gipfel ab ½ POC-Volumen,
    voneinander durch eine dünne Stufe unter ⅓ getrennt), dünne Stellen (LVN, tiefe.zonen) und Einzeldrucke im
    Zeitprofil (nur eine Kerze, mindestens 2 Stufen am Stück, tiefe.SCHWANZ_ZEILEN)."""
    p, k, m = np.asarray(pr["volumen"], float), pr["grenzen"], pr["mitte"]
    top = p.max() or 1.0
    glatt = np.convolve(p, np.ones(KNOTEN_GLAETTEN) / KNOTEN_GLAETTEN, mode="same")
    gipfel = [i for i in range(len(p)) if p[i] >= KNOTEN_ANTEIL * top
              and glatt[i] >= glatt[max(0, i - 1)] and glatt[i] >= glatt[min(len(p) - 1, i + 1)]]
    knoten = []
    for i in sorted(gipfel, key=lambda i: -p[i]):
        if all((p[min(i, j):max(i, j) + 1] < tiefe.DUENN * top).any() for j in knoten):
            knoten.append(i)
        if len(knoten) >= KNOTEN_MAX:
            break
    einzel, z, i = [], np.asarray(pr["zeit"], float), 0
    while i < len(z):
        if z[i] != 1:
            i += 1
            continue
        j = i
        while j + 1 < len(z) and z[j + 1] == 1:
            j += 1
        if j - i + 1 >= tiefe.SCHWANZ_ZEILEN:
            einzel.append((float(k[i]), float(k[j + 1])))
        i = j + 1
    return {"val": float(pr["wert_unten"]), "vah": float(pr["wert_oben"]), "knoten": sorted(float(m[i]) for i in knoten),
            "duenn": tiefe.zonen(pr)["duenn"], "einzel": einzel}












STELLUNGEN_JE_SEITE = 2    # je Richtung die 2 nächsten Stellungen (Micky 21.11.2026)




def stellungen(e):
    """Die Stellungen der Ebene (livermore.stellungen, dieselbe Liste wie die Frontkarte) – je Richtung die 2 nächsten
    zum Kurs. → {"oben": [...], "unten": [...]} je {preis, grund, abstand, gewicht}."""
    import livermore
    if not e:
        return {"oben": [], "unten": []}
    df = e["df"].dropna(subset=["High", "Low", "Close"])
    if len(df) < vcp_zone.ATR_TAGE + 2:
        return {"oben": [], "unten": []}
    return livermore.stellungen(df, je_seite=STELLUNGEN_JE_SEITE)


def frei(e):
    """✈️ freie Bahn der Ebene (livermore.frei) oder None (zu kurz)."""
    import livermore
    if not e or len(e["df"]) < vcp_zone.ATR_TAGE + 2:
        return None
    return livermore.frei(e["df"].dropna(subset=["High", "Low", "Close"]))


def fuehrte(ebenen):
    """Alles für Kopfzeile und Chart: Livermores Spanne je Ebene (sein Notizbuch auf den Kerzen jeder Ebene – eine
    Sprache auf allen Ebenen), Lage je Ebene, Stellungen, der Trade (Tag), die Einigkeit der Ebenen."""
    tag = ebenen.get("Tag")
    ba_e = {}
    for n in EBENEN:
        e_ = ebenen.get(n)
        try:
            ba_e[n] = basis(e_["df"]) if e_ and len(e_["df"]) >= NOTIZBUCH_MIN else None
        except Exception:  # noqa: BLE001 – Technik: ohne Notizbuch zu wenig Kerzen (kein zweites Messgerät)
            ba_e[n] = None
    ba = ba_e.get("Tag")
    la = {n: lage(ebenen.get(n), ba_e.get(n)) for n in EBENEN}
    fest = {n: stellungen(ebenen.get(n)) for n in EBENEN}
    return {"lage": la, "trade": trade(tag, la["Tag"], ba), "stellungen": fest, "basis": ba, "frei": frei(tag),
            "einigkeit": einigkeit(la)}


def einigkeit(la):
    """Einigkeit der Ebenen (Micky 26.11.2026): Livermores Spalte auf Woche, Tag und Stunde → {ebenen: {Name: (Ampel,
    Wort)}, alle: "auf" | "ab" | None}. Vormarsch auf allen drei = "auf", Rückzug auf allen drei = "ab"."""
    import livermore
    sp = {n: (la.get(n) or {}).get("spalte") for n in EBENEN}
    if not any(sp.values()):
        return None
    werte = set(sp.values())
    return {"ebenen": {n: livermore.lage(s_) for n, s_ in sp.items() if s_},
            "alle": "auf" if werte == {"AT"} else "ab" if werte == {"AB"} else None}
