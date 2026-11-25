"""Zonen, Phasen, Strömung – das schlanke Cockpit (Micky 21./22.11.2026).

Grundsatz: Eine Zone ist das Gerüst im Chart (der Nordstern). Reagieren statt antizipieren: gehandelt wird der
Ausbruch aus der Zone, der Rücktest an die gebrochene Kante und der Bruch der Unterkante – sonst nichts.

Die Zone je Ebene (Micky 22.11.2026, die PbD-Kette nach Vorwald ist entfernt):
  Woche und Tag  Livermores Spanne (vcp_zone.zone, livermore.spanne – Micky 25.11.2026: Livermore ist die Grundlage):
                 Oberkante = letzter Pivotal Point oben = Pivot, Unterkante = letzter Pivotal Point unten; Name immer
                 „Spanne“ (Base, Flagge, Konsolidierung am 25.11.2026 entfernt).
                 Beide Ebenen zeigen dieselbe Spanne – die Woche im großen Bild, der Tag im Detail.
                 Läuft gerade ein Ausbruch (vcp_zone.ausbruch, bis 20 Tage), gilt die Spanne, aus der er kam.
  Stunde         die Balance nach Dalton (tiefe.struktur): höchstes Hoch und tiefstes Tief seit dem Anker – die
                 Feinzeichnung für den Einstieg.
Phase (Zeichenliste): 🟡 Spanne im Aufbau · 🟡 Abwärtstrend läuft (Livermore schreibt rot, Zone noch offen) · 🦬 am Pivot (bis 3 % darunter) ·
  🦬 Ausbruch (Schluss über dem Pivot) · 🪝 Rücktest · 🦊 Fehlausbruch · 🐻 Bruch der Unterkante · ⚪ keine Spanne
  (Kurs läuft am Hoch).
Die drei Trades (Tageszone, Micky 22.11.2026):
  Ausbruch    long: Auslöser = Pivot (Schluss darüber, Volumen über dem 50-Tage-Schnitt); Stopp = ¼ ATR unter
              Livermores Pivotal Point unten (der Unterkante, 25.11.2026), höchstens 8 % (Minervini, MAX_STOPP). Vor dem Ausbruch wartet er am Pivot.
  Rücktest    nach dem Ausbruch zurück an den Pivot (vcp_zone.ausbruch: Schluss knapp darunter, kein Fehlausbruch):
              Einstieg am Pivot, Stopp ¼ ATR darunter.
  Short       Bruch der Unterkante: Schluss unter der Unterkante der Spanne von gestern, mit Volumen über dem
              50-Tage-Schnitt; Stopp ¼ ATR über der gebrochenen Kante (ein laufender Rücksetzer bricht nichts).
Kein festes Ziel (Micky: Gewinne laufen lassen, Stopp nachziehen) – die Ampel zeigt das Risiko: 🟢 bis 8 %, 🔴 darüber.
Profil (Micky 21.11.2026: nur eines, aber aussagekräftig): Zeit und Volumen gespiegelt in einer Silhouette, verankert am
  Beginn der Zone (bzw. am eigenen Anker), aus den feineren Kerzen der Ebene; sein POC ist der POC der Zone.
Festungen (Micky 22.11.2026): alte Decke = Swing-Hoch ohne Schluss darüber, alter Boden = Swing-Tief ohne Schluss
darunter (Wendepunkte ab 2 ATR), überwundene Kanten mit getauschter Rolle; je Richtung die 2 nächsten; zwei Jahre
zurück (so weit reichen die Massive-Tage der Liste – Chart, Liste und Zeichen sehen dieselben Festungen).
Freie Bahn ✈️ (Micky 22.11.2026, Livermores Linie des geringsten Widerstands): über dem Kurs steht im Tageschart keine
Festung mehr – niemand wartet oben auf seinen Einstand (O'Neil: kein Overhead Supply); ✈️↓ gespiegelt für den Short.
Reines Zeichen ohne Schwelle: wie leicht der Kurs läuft, zeigen Pivot, Volumen-Spur, 🏜️ und Kraft ohne Weg.
"""
import numpy as np
import pandas as pd

import tiefe
import vcp_zone
MAX_STOPP = 0.08           # Minervini: höchstens 8 % Risiko je Trade (der Stopp wird nie weiter gesetzt)
from tiefe import STOPP_ATR            # ¼ ATR jenseits der Kante – eine Quelle
from masse import VOL_TAGE             # Volumen über dem 50-Tage-Schnitt (Micky: reicht für den Ausbruch) – eine Quelle

EBENEN = ("Woche", "Tag", "Stunde")
BAHN_JAHRE = 2              # Festungen und ✈️: zwei Jahre zurück
PHASE = {"aufbau": ("🟡", "Spanne im Aufbau"), "ruecksetzer": ("🟡", "Abwärtstrend läuft"), "kante": ("🦬", "am Pivot"),
         "ausbruch": ("🦬", "Ausbruch"), "ruecktest": ("🪝", "Rücktest"), "fehl": ("🦊", "Fehlausbruch"),
         "bruch": ("🐻", "Bruch der Unterkante"), "hoch": ("⚪", "keine Spanne – Kurs läuft am Hoch"),
         "balance": ("🟡", "Balance"), "rand_oben": ("🦬", "am oberen Rand"), "rand_unten": ("🐻", "am unteren Rand")}
RICHTUNG = {"ausbruch": 1, "ruecktest": 1, "fehl": -1, "bruch": -1}
TRADE_NAME = {"ausbruch": "Ausbruch", "ruecktest": "Rücktest", "short": "Bruch der Unterkante"}
TRADE_ZEICHEN = {"ausbruch": "🦬", "ruecktest": "🪝", "short": "🐻"}


SPANNE = {"Woche": pd.Timedelta(days=7), "Tag": pd.Timedelta(days=1), "Stunde": pd.Timedelta(hours=1)}


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
    elif a:
        b = a["zone"]
    else:
        b = jetzt if jetzt.get("start_i") is not None else None
    return {"z": vcp_zone.datiert(df, b) if b else None, "ausbruch": a, "jetzt": jetzt, "df": df, "bruch": bruch, "nb": nb}


def _volumen_hoch(df):
    v = df["Volume"].astype(float)
    schnitt = v.rolling(VOL_TAGE, min_periods=VOL_TAGE // 2).mean().shift()   # Technik: halbe Länge reicht zum Start
    return bool(schnitt.iloc[-1] == schnitt.iloc[-1] and v.iloc[-1] > schnitt.iloc[-1])


def lage(e, ba=None, profil=True):
    """Zone, Phase und Richtung einer Ebene → dict. Woche und Tag aus der Base ba (basis()), die Stunde aus der Balance.
    profil=False (Zirkel-Lauf über alle Titel, nur Tageskurse): ohne Volumenprofil, poc und profil sind None."""
    if not e:
        return None
    df = e["df"]
    kurs = float(df["Close"].iloc[-1])
    if e["name"] == "Stunde" or ba is None:
        st_ = e["struktur"]
        lo, hi, beginn = float(st_["short_pivot"]), float(st_["pivot"]), pd.Timestamp(st_["balance_start"])
        nah = (e["atr"] or 0) * STOPP_ATR
        phase = "rand_oben" if kurs >= hi - nah else "rand_unten" if kurs <= lo + nah else "balance"
        name, pivot, info = "Balance", hi, f"seit {beginn:%d.%m. %H:%M}"
    else:
        z, a = ba["z"], ba["ausbruch"]
        if z is None:                              # Kurs läuft am Hoch: keine Zone, das Profil ab dem Anker der Balance
            z_, w_ = PHASE["hoch"]
            pr = profil_seit(e, e["struktur"]["balance_start"]) if profil else None
            return {"zone": None, "phase": "hoch", "zeichen": z_, "wort": w_, "richtung": 0, "pfeil": "→", "kurs": kurs,
                    "name": "", "info": "", "pivot": None, "poc": float(pr["poc"]) if pr else None, "profil": pr,
                    "beginn": None}
        lo, hi, beginn = float(z["unten"]), float(z["oben"]), pd.Timestamp(z["start_t"])
        pivot = float(a["pivot"]) if a else float(z.get("pivot") or hi)   # Livermores Pivotal Point
        td = ba["df"]
        if a and a["fehl"]:
            phase = "fehl"
        elif a:
            phase = "ruecktest" if a["ruecktest"] else "ausbruch"
        elif ba["bruch"]:
            phase = "bruch"
        elif not ba["jetzt"].get("zone"):
            phase = "ruecksetzer"
        elif float(td["Close"].iloc[-1]) >= pivot * (1 - vcp_zone.RAND_PCT / 100):
            phase = "kante"
        else:
            phase = "aufbau"
        name = z.get("name") or "Abwärtstrend"
        teile = [f'{z["wochen"]:.0f} Wo.', f'{z["tiefe"]:.0f} % tief'.replace(".", ",")]
        if a and not a["fehl"]:
            teile.append(f'Ausbruch vor {a["tage_her"]} T. ' + ("mit Volumen" if a["mit_volumen"] else "ohne Volumen"))
        info = " · ".join(teile)
    pr = profil_seit(e, beginn) if profil else None
    z_, w_ = PHASE[phase]
    r = RICHTUNG.get(phase, 0)
    return {"zone": (lo, hi), "pivot": pivot, "poc": float(pr["poc"]) if pr else None, "profil": pr, "beginn": beginn, "name": name,
            "info": info, "phase": phase, "zeichen": z_, "wort": w_, "richtung": r,
            "pfeil": {1: "↗", -1: "↘", 0: "→"}[r], "kurs": kurs}


def trade(e, la, ba):
    """Der eine Trade der Tagesebene → {art, richtung, einstieg, stopp, pivot, risiko, ampel, wartet, name, zeichen} oder
    None; pivot = die Kante, die der Trade überwinden bzw. brechen muss (long der Pivot, short die Unterkante)."""
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












FESTUNGEN_JE_SEITE = 2     # je Richtung die 2 nächsten Festungen (Micky 21.11.2026)
FESTUNG_ABSTAND = 0.5      # Festungen näher als ½ ATR sind eine Festung (sonst stehen Stunden-Festungen dicht an dicht)




def _swing_kanten(e):
    """Festungen aus Swing-Hochs und Swing-Tiefs der Ebene (Micky 22.11.2026; Wendepunkte ab 2 ATR wie die Base,
    vcp_zone.zigzag, ohne den letzten unbestätigten): ein Swing-Hoch ohne Schluss darüber ist eine alte Decke (O'Neil,
    Minervini: Overhead Supply), ein Swing-Tief ohne Schluss darunter ein alter Boden; per Schluss überwunden und
    seitdem nicht zurück, tauscht die Kante die Rolle (Decke → Boden, Boden → Decke). → [(Preis, Grund)]."""
    df = e["df"]
    if len(df) < vcp_zone.ATR_TAGE + 2:
        return []
    C = df["Close"].to_numpy(float)
    ab = int(df.index.searchsorted(df.index[-1] - pd.DateOffset(years=BAHN_JAHRE)))
    aus = []
    for i, p_, art in vcp_zone.zigzag(df, vcp_zone.GROB)[:-1]:
        if i < ab:
            continue
        nach = C[i + 1:]
        durch = np.flatnonzero(nach > p_) if art == "H" else np.flatnonzero(nach < p_)
        if not len(durch):
            aus.append((float(p_), "alte Decke" if art == "H" else "alter Boden"))
        elif not ((nach[durch[0] + 1:] < p_) if art == "H" else (nach[durch[0] + 1:] > p_)).any():
            aus.append((float(p_), "Decke → Boden" if art == "H" else "Boden → Decke"))
    return aus


def festungen(e, la):
    """Die Festungen (Micky 22.11.2026: nur alte Decke und alter Boden): Kanten aus Swing-Hochs und Swing-Tiefs
    (_swing_kanten) – je Richtung die 2 nächsten zum Kurs; Preise innerhalb ½ ATR werden eine Festung mit allen
    Gründen. → {"oben": [...], "unten": [...]} je {preis, grund, abstand}."""
    if not e or not la:
        return {"oben": [], "unten": []}
    kurs, a = la["kurs"], e["atr"] or 0
    roh = _swing_kanten(e)
    aus = {}
    for seite, auswahl in (("oben", [x for x in roh if x[0] > kurs]), ("unten", [x for x in roh if x[0] < kurs])):
        auswahl.sort(key=lambda x: abs(x[0] - kurs))
        liste = []
        for p_, g_ in auswahl:
            nah = next((f for f in liste if abs(f["preis"] - p_) <= a * FESTUNG_ABSTAND), None)
            if nah:
                if g_ not in nah["grund"]:
                    nah["grund"].append(g_)
                continue
            if len(liste) >= FESTUNGEN_JE_SEITE:
                break
            liste.append({"preis": float(p_), "grund": [g_], "abstand": round((p_ / kurs - 1) * 100, 1)})
        aus[seite] = liste
    return aus


def frei(e):
    """✈️ freie Bahn der Ebene: {"oben": keine Festung über dem Schluss, "unten": keine darunter} oder None (zu kurz)."""
    if not e or len(e["df"]) < vcp_zone.ATR_TAGE + 2:
        return None
    kurs, k = float(e["df"]["Close"].iloc[-1]), _swing_kanten(e)
    return {"oben": not any(p_ > kurs for p_, _ in k), "unten": not any(p_ < kurs for p_, _ in k)}


def fuehrte(ebenen):
    """Alles für Kopfzeile und Chart: die Base (Woche und Tag), Lage je Ebene, Festungen, der Trade."""
    tag = ebenen.get("Tag")
    ba = basis(tag["df"]) if tag else None
    la = {n: lage(ebenen.get(n), None if n == "Stunde" else ba) for n in EBENEN}
    fest = {n: festungen(ebenen.get(n), la[n]) for n in EBENEN}
    return {"lage": la, "trade": trade(tag, la["Tag"], ba), "festungen": fest, "basis": ba, "frei": frei(tag)}
