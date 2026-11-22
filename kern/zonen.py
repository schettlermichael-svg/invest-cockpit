"""Zonen, Phasen, Strömung – das schlanke Cockpit (Micky 21./22.11.2026).

Grundsatz: Eine Zone ist das Gerüst im Chart (der Nordstern). Reagieren statt antizipieren: gehandelt wird der
Ausbruch aus der Zone, der Rücktest an die gebrochene Kante und der Bruch der Unterkante – sonst nichts.

Die Zone je Ebene (Micky 22.11.2026, die PbD-Kette nach Vorwald ist entfernt):
  Woche und Tag  die Base nach Minervini und O'Neil (vcp_zone.zone): Oberkante = letztes Swing-Hoch ohne Schluss
                 darüber, Unterkante = tiefstes Tief seitdem; Name Base, Flagge (Kullamägi) oder Konsolidierung (nach
                 einem Absturz); Pivot = Hoch der letzten Enge, wenn es am Rand liegt, sonst die Oberkante
                 (vcp_zone.rand). Beide Ebenen zeigen dieselbe Base – die Woche im großen Bild, der Tag im Detail.
                 Läuft gerade ein Ausbruch (vcp_zone.ausbruch, bis 20 Tage), gilt die Base, aus der er kam.
  Stunde         die Balance nach Dalton (tiefe.struktur): höchstes Hoch und tiefstes Tief seit dem Anker – die
                 Feinzeichnung für den Einstieg.
Phase (Zeichenliste): 🟡 Base im Aufbau · 🟡 Rücksetzer läuft (Zone noch offen) · 💥 am Pivot (bis 3 % darunter) ·
  💥 Ausbruch (Schluss über dem Pivot) · 🪝 Rücktest · 🦊 Fehlausbruch · 🐻 Bruch der Unterkante · ⚪ keine Base
  (Kurs läuft am Hoch).
Die drei Trades (Tageszone, Micky 22.11.2026):
  Ausbruch    long: Auslöser = Pivot (Schluss darüber, Volumen über dem 50-Tage-Schnitt); Stopp = Tief der letzten
              Kontraktion, höchstens 8 % (Minervini, system_minervini.MAX_STOPP). Vor dem Ausbruch wartet er am Pivot.
  Rücktest    nach dem Ausbruch zurück an den Pivot (vcp_zone.ausbruch: Schluss knapp darunter, kein Fehlausbruch):
              Einstieg am Pivot, Stopp ¼ ATR darunter.
  Short       Bruch der Unterkante: Schluss unter der Unterkante der fertigen Base von gestern, mit Volumen über dem
              50-Tage-Schnitt; Stopp ¼ ATR über der gebrochenen Kante (ein laufender Rücksetzer bricht nichts).
Kein festes Ziel (Micky: Gewinne laufen lassen, Stopp nachziehen) – die Ampel zeigt das Risiko: 🟢 bis 8 %, 🔴 darüber.
Profil (Micky 21.11.2026: nur eines, aber aussagekräftig): Zeit und Volumen gespiegelt in einer Silhouette, verankert am
  Beginn der Zone (bzw. am eigenen Anker), aus den feineren Kerzen der Ebene; sein POC ist der POC der Zone.
Alte Zonen (für die gebrochenen Kanten): die abgeschlossenen Basen (vcp_zone.verlauf) auf Woche und Tag.
Festungen: gebrochene Kanten alter Basen und AVWAP großer Ereignisse (Shannon), je Richtung die 2 nächsten.
"""
import numpy as np
import pandas as pd

import tiefe
import vcp_zone
from system_minervini import MAX_STOPP  # eine Quelle (Minervini: höchstens 8 % Risiko)
from tiefe import STOPP_ATR            # ¼ ATR jenseits der Kante – eine Quelle
from masse import VOL_TAGE             # Volumen über dem 50-Tage-Schnitt (Micky: reicht für den Ausbruch) – eine Quelle

EBENEN = ("Woche", "Tag", "Stunde")
PHASE = {"aufbau": ("🟡", "Base im Aufbau"), "ruecksetzer": ("🟡", "Rücksetzer läuft"), "kante": ("💥", "am Pivot"),
         "ausbruch": ("💥", "Ausbruch"), "ruecktest": ("🪝", "Rücktest"), "fehl": ("🦊", "Fehlausbruch"),
         "bruch": ("🐻", "Bruch der Unterkante"), "hoch": ("⚪", "keine Base – Kurs läuft am Hoch"),
         "balance": ("🟡", "Balance"), "rand_oben": ("💥", "am oberen Rand"), "rand_unten": ("💥", "am unteren Rand")}
RICHTUNG = {"ausbruch": 1, "ruecktest": 1, "fehl": -1, "bruch": -1}
TRADE_NAME = {"ausbruch": "Ausbruch", "ruecktest": "Rücktest", "short": "Bruch der Unterkante"}
TRADE_ZEICHEN = {"ausbruch": "💥", "ruecktest": "🪝", "short": "🐻"}


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
    """Die Base des Titels aus Tageskerzen für Woche und Tag (vcp_zone): {"z", "enge", "ausbruch", "jetzt", "verlauf"}
    – z datiert (Index → Datum), oder None, wenn der Kurs am Hoch läuft."""
    df = df.dropna(subset=["High", "Low", "Close"])
    jetzt = vcp_zone.zone(df)
    a = vcp_zone.ausbruch(df, jetzt=jetzt)
    gestern = vcp_zone.zone(df.iloc[:-1]) if len(df) > 1 else {}
    bruch = bool(not a and gestern.get("zone") and float(df["Close"].iloc[-1]) < gestern["unten"])
    if bruch:                                    # Bruch der Unterkante einer fertigen Base: die Base von gestern
        b, en = gestern, {}
    elif a:
        b, en = a["zone"], a["enge"]
    else:
        b = jetzt if jetzt.get("start_i") is not None else None
        en = vcp_zone.enge(df, jetzt) if jetzt.get("zone") else {}
    try:
        alt = [vcp_zone.datiert(df, x) for x in vcp_zone.verlauf(df)]
    except Exception:  # noqa: BLE001 – Technik: ohne Historie keine alten Zonen
        alt = []
    return {"z": vcp_zone.datiert(df, b) if b else None, "enge": en or {}, "ausbruch": a, "jetzt": jetzt, "df": df,
            "verlauf": alt, "bruch": bruch}


def _volumen_hoch(df):
    v = df["Volume"].astype(float)
    schnitt = v.rolling(VOL_TAGE, min_periods=VOL_TAGE // 2).mean().shift()   # Technik: halbe Länge reicht zum Start
    return bool(schnitt.iloc[-1] == schnitt.iloc[-1] and v.iloc[-1] > schnitt.iloc[-1])


def lage(e, ba=None):
    """Zone, Phase und Richtung einer Ebene → dict. Woche und Tag aus der Base ba (basis()), die Stunde aus der Balance."""
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
        z, en, a = ba["z"], ba["enge"], ba["ausbruch"]
        if z is None:                              # Kurs läuft am Hoch: keine Zone, das Profil ab dem Anker der Balance
            z_, w_ = PHASE["hoch"]
            pr = profil_seit(e, e["struktur"]["balance_start"])
            return {"zone": None, "phase": "hoch", "zeichen": z_, "wort": w_, "richtung": 0, "pfeil": "→", "kurs": kurs,
                    "name": "", "info": "", "pivot": None, "poc": float(pr["poc"]), "profil": pr, "beginn": None}
        lo, hi, beginn = float(z["unten"]), float(z["oben"]), pd.Timestamp(z["start_t"])
        pivot = float(a["pivot"]) if a else vcp_zone.rand(z, en) if en.get("pivot") else hi
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
        name = z.get("name") or "Rücksetzer"
        teile = [f'{z["wochen"]:.0f} Wo.', f'{z["tiefe"]:.0f} % tief'.replace(".", ",")]
        if en.get("zahl"):
            teile.append(f'{en["zahl"]} Kontr. {en["folge"]} %')
        if a and not a["fehl"]:
            teile.append(f'Ausbruch vor {a["tage_her"]} T. ' + ("mit Volumen" if a["mit_volumen"] else "ohne Volumen"))
        info = " · ".join(teile)
    pr = profil_seit(e, beginn)
    z_, w_ = PHASE[phase]
    r = RICHTUNG.get(phase, 0)
    return {"zone": (lo, hi), "pivot": pivot, "poc": float(pr["poc"]), "profil": pr, "beginn": beginn, "name": name,
            "info": info, "phase": phase, "zeichen": z_, "wort": w_, "richtung": r,
            "pfeil": {1: "↗", -1: "↘", 0: "→"}[r], "kurs": kurs}


def trade(e, la, ba):
    """Der eine Trade der Tagesebene → {art, richtung, einstieg, stopp, risiko, ampel, wartet, name, zeichen} oder None."""
    if not e or not la or la.get("zone") is None or ba is None or ba["z"] is None:
        return None
    a, en, z = ba["ausbruch"], ba["enge"], ba["z"]
    atr = e["atr"] or 0
    kurs, pivot, lo = la["kurs"], la["pivot"], la["zone"][0]
    t = None
    if la["phase"] in ("ausbruch", "kante", "aufbau") and (a or z.get("laenge") == "ok"):
        einst = vcp_zone.einstiege(z, en, cheat=False)
        struktur = einst[-1]["struktur"] if einst else None
        stopp = max(struktur, pivot * (1 - MAX_STOPP)) if struktur is not None else pivot * (1 - MAX_STOPP)
        if la["phase"] != "ausbruch" or a.get("kaufzone"):
            t = {"art": "ausbruch", "richtung": 1, "einstieg": pivot, "stopp": stopp, "wartet": la["phase"] != "ausbruch"}
    elif la["phase"] == "ruecktest":
        t = {"art": "ruecktest", "richtung": 1, "einstieg": pivot, "stopp": pivot - atr * STOPP_ATR, "wartet": False}
    elif la["phase"] == "bruch" and _volumen_hoch(ba["df"]):
        t = {"art": "short", "richtung": -1, "einstieg": kurs, "stopp": lo + atr * STOPP_ATR, "wartet": False}
    if t:
        t["risiko"] = round(abs(t["einstieg"] - t["stopp"]) / t["einstieg"] * 100, 1)
        t["ampel"] = "🟢" if t["risiko"] <= MAX_STOPP * 100 else "🔴"
        t["name"], t["zeichen"] = TRADE_NAME[t["art"]], TRADE_ZEICHEN[t["art"]]
    return t


def historie(e, ba):
    """Abgeschlossene Basen (vcp_zone.verlauf) als alte Zonen der Ebene, älteste zuerst – je mit Kanten und Ende (Tag
    des Ausbruchs); für die gebrochenen Kanten unter den Festungen."""
    if not e or ba is None or e["name"] == "Stunde":
        return []
    return [{"name": b["name"], "tief": float(b["unten"]), "hoch": float(b["oben"]), "start": pd.Timestamp(b["start_t"]),
             "ende": pd.Timestamp(b["ende_t"])} for b in sorted(ba["verlauf"], key=lambda x: x["start_t"])]


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
AVWAP_GROSS = {"zahlen": "AVWAP Zahlen", "hoch": "AVWAP Hoch", "gipfel": "AVWAP Gipfel",
               "tief": "AVWAP Tief"}   # große Ereignisse nach Shannon (Micky 21.11.2026)
FESTUNG_ABSTAND = 0.5      # Festungen näher als ½ ATR sind eine Festung (sonst stehen Stunden-Festungen dicht an dicht)




def _gebrochene_kanten(e, hist):
    """Kanten alter Basen, die der Kurs durchbrochen hat und seitdem nicht per Schluss zurück durchquert: die alte Decke
    wird Boden, der alte Boden Decke (Dalton) → [(Preis, Grund)]."""
    C = e["df"]["Close"]
    aus = []
    for z in hist:
        nach = C[C.index > z["ende"]]
        if not len(nach):
            continue
        raus = nach[(nach > z["hoch"]) | (nach < z["tief"])]
        if not len(raus):
            continue
        oben = float(raus.iloc[0]) > z["hoch"]
        kante = z["hoch"] if oben else z["tief"]
        danach = nach[nach.index > raus.index[0]]
        zurueck = (danach < kante).any() if oben else (danach > kante).any()
        if not zurueck:
            aus.append((kante, "alte Decke" if oben else "alter Boden"))
    return aus


def festungen(e, la, avwaps=(), hist=()):
    """Die Festungen (Micky 21.11.2026; ohne Umkehrpreise seit 22.11.2026 – keine Quelle): gebrochene Kanten alter Basen
    (O'Neil: Overhead Supply, Dalton: alte Wertzone) und AVWAP großer Ereignisse (Shannon) – je Richtung die 2 nächsten zum Kurs; Preise innerhalb ½ ATR werden eine Festung mit allen
    Gründen. avwaps = tiefe.avwap_liste(Tageskurse)[0]. → {"oben": [...], "unten": [...]} je {preis, grund, abstand}."""
    if not e or not la:
        return {"oben": [], "unten": []}
    kurs, a = la["kurs"], e["atr"] or 0
    roh = _gebrochene_kanten(e, hist) + [(x["wert"], AVWAP_GROSS[x["anker"]]) for x in avwaps
                                                      if x["anker"] in AVWAP_GROSS]
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


def fuehrte(ebenen, avwaps=()):
    """Alles für Kopfzeile und Chart: die Base (Woche und Tag), Lage je Ebene, alte Zonen, Festungen, der Trade."""
    tag = ebenen.get("Tag")
    ba = basis(tag["df"]) if tag else None
    la = {n: lage(ebenen.get(n), None if n == "Stunde" else ba) for n in EBENEN}
    alt = {n: historie(ebenen.get(n), ba) for n in EBENEN}
    fest = {n: festungen(ebenen.get(n), la[n], avwaps, alt[n]) for n in EBENEN}
    return {"lage": la, "trade": trade(tag, la["Tag"], ba), "festungen": fest, "alt": alt, "basis": ba}
