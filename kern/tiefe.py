"""Tiefenanalyse eines Titels – aus der App „Titel-Analyse“ ins Cockpit übernommen (Micky 21.11.2026).

Quelle: TitelAnalyse/kern/rechnen.py (Stand 20.11.2026), dort mit Herkunft. Übernommen mit Mickys Entscheidungen vom
21.11.2026 – wo das Cockpit schon eine Regel hatte, gilt, was er gewählt hat:
  Balance            Cockpit (avwap.balance_beginn: Blöcke zu 5 Tagen am Kern, Lücke ab 2 % beendet, bis 65 Wochen)
  Profil             Titel-Analyse: Volumen aus Stundenkerzen ab dem Anker, Stufen ≈ 0,25 % des Kurses, Wertzone 70 %
                     vom POC nach außen (Dalton: jeweils die schwerere Nachbarstufe). Ohne Stundenkerzen Tageskerzen.
  Anker              Titel-Analyse: der Zahlentag, wenn sein Schluss mindestens 1 ATR vom Vortag lag (neue Auktion) und
                     die Balance daraus hervorging (höchstens 10 Handelstage davor); sonst der erste Tag der Balance.
  Dünne Zonen        zusammenhängend unter ⅓ des POC-Volumens, mindestens 2 Stufen; dünne Ränder = Dochte.
  Alte Wertzone      Titel-Analyse: Profil der letzten Balance von mindestens 10 Tagen vor dem Anker.
  Pivot              beide: der Rand der Balance (höchstes Hoch, Tests bis 1 % darunter; short tiefstes Tief) neben dem
                     Pivot der Enge (vcp_zone).
  Quetschung         Titel-Analyse (zeichen.einquetschung rechnet mit quetschung() hier): Tiefs der drei Drittel seit dem
                     Anker steigen, ihre Hochs liegen höchstens 2 % auseinander; gespiegelt für Short (Claude, 21.11.2026:
                     das Cockpit handelt beide Seiten): Hochs fallen, Tiefs höchstens 2 % auseinander.
  Spring/Upthrust,   Cockpit (vcp_zone.spring_upthrust, vcp_zone.ausbruch) – hier nur gelesen.
  Fehlausbruch
  AVWAP              Anker des Cockpits (avwap.anker); dazu Shannons Zange gemessen: Abstand der AVWAP vom letzten Hoch
                     und vom Tief der Bewegung vor 5 Tagen → heute, Kurs über, unter oder zwischen den Linien.
  Stärke in Schwäche beide: an den Druck-Tagen des S&P 500 (O'Neils Distributionstage) der letzten 25
                     Sitzungen besser als der Index – neben zeichen.tage_gegen_markt.
  Geldfluss          Rückenwind bleibt das Urteil; dazu die Rangtabelle der 11 Sektor-ETFs über 1M/3M/6M.
  CMF                Chaikin Money Flow 20 Tage: Geldfluss je Kerze = ((C−L)−(H−C))/(H−L) × Volumen, mit den Treibern.
Die Wertwanderung (POC je Kerze) siehe dort. ATR: die eine ATR der App (atr.reihe).
"""
import numpy as np
import pandas as pd

import atr as atr_modul
from marketprofile import WERT  # noqa: E402  Wertzone 70 % (Dalton) – eine Quelle
from masse import MONAT_TAGE, WOCHE

# ── Struktur nach Dalton ──────────────────────────────────────────────────────────────────────────────────────────
STUFE_PCT = 0.0025           # Preisstufe des Profils ≈ 0,25 % des Kurses, auf glatte Werte gerundet
STUFEN = (0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50)   # Technik: glatte Stufen in $
DUENN = 1 / 3                # dünne Zone: unter ⅓ des POC-Volumens …
DUENN_MIN = 2                # … mindestens 2 Stufen am Stück
ANKER_ATR = 1.0              # Zahlentag als Anker: Schluss mindestens 1 ATR vom Vortag (neue Auktion)
ANKER_VOR = 10               # … höchstens 10 Handelstage vor dem Beginn der Balance
BALANCE_MIN = 5              # ohne erkannte Balance: die letzten 5 Tage
STUNDEN_MIN = 10             # Profil aus Stundenkerzen erst ab 10 Kerzen, sonst Tageskerzen
PIVOT_TEST = 0.01            # Test der Kante: Hoch höchstens 1 % unter dem Pivot (short: Tief 1 % darüber)
QUETSCH_HOCHS = 0.02         # Quetschung: Hochs der drei Drittel höchstens 2 % auseinander
QUETSCH_MIN = 6              # … ab 6 Tagen seit dem Anker (drei Drittel zu je 2 Tagen)
DRITTEL = 3                  # … drei Teilstücke
ALT_MIN = 10                 # alte Balance: mindestens 10 Tage
ALT_SUCHE = 40               # … gesucht bis 40 Tage vor dem Anker
NAH_PCT = 0.08               # alte Wertzone „in Reichweite“: POC höchstens 8 % vom Kurs (🪝)

# ── AVWAP nach Shannon ────────────────────────────────────────────────────────────────────────────────────────────
ZANGE_TAGE = 5               # Zange: Abstand vor 5 Tagen → heute
DECKEL_PCT = 2.0             # Kurs bis 2 % unter einer AVWAP: sie ist der nächste Deckel (🪝)
DOPPEL_PCT = 0.01            # AVWAP vom Zahlentag höchstens 1 % neben POC bzw. Unterkante: doppelte Marke

# ── Relative Stärke und Geldfluss ─────────────────────────────────────────────────────────────────────────────────
PERIODEN = {"1W": WOCHE, "1M": MONAT_TAGE, "3M": 3 * MONAT_TAGE, "6M": 6 * MONAT_TAGE}
CMF_TAGE = 20                # Chaikin Money Flow über 20 Tage
CMF_GRENZE = 0.05            # über +0,05 Zufluss (🟢), unter −0,05 Abfluss (🔴)
CMF_TREIBER = 3              # die 3 stärksten Kerzen je Seite
RANG_SONNE = 3.5             # Sektor im Mittel der Ränge 1M/3M/6M bis 3,5 von 11: Geld fließt hinein (☀️)
RANG_SCHNEE = 8              # … ab 8: Geld fließt ab (❄️)
RANG_SEITE = 3               # „fließt in … / kommt aus …“: die 3 vordersten und hintersten

# ── Feste Maße der Ebenen (die PbD-Kette nach Tom Vorwald ist am 22.11.2026 entfernt) ─────────────────────────────
IMPULS_SCHLUESSE = 3         # Mindestlänge einer Ebene: 2 × 3 Kerzen plus die alte Balance
SCHWANZ_ZEILEN = 2           # Schwanz: mindestens 2 Preiszeilen mit nur einer Zeitmarke
STOPP_ATR = 0.25             # Stopp ¼ ATR hinter der Kante (Rücktest, Bruch der Unterkante; Micky)
ZEIT_VERSATZ = 3             # die feineren Kerzen beginnen höchstens 3 Tage nach dem Beginn des Profils

# ── Wertwanderung (POC je Kerze) ──────────────────────────────────────────────────────────────────────────────────
# Dalton: wo sich Wert bildet, trennt Akzeptanz vom Ausflug. Vergleich jeder Wertzone mit der vorigen in 6 Klassen
# (Micky 21.11.2026). Gesetzt (Claude, Titel-Analyse 20.11.2026): Treppe ab 3 POCs in Folge; Ballen = letzte 5 POCs
# innerhalb 1 ATR; Abtasten = Schluss außerhalb der vorigen Wertzone, eigener POC noch darin; nackte POCs der letzten
# 60 Kerzen (Praxisbegriff, keine Regel nach Dalton).
TREPPE = 3
FREITAG, WOCHENTAGE = 4, 7   # Technik: Wochentag des Freitags (Montag = 0), Tage je Woche
BALLEN_N = 5
NACKT_N = 60
WANDER_KERZEN = 4            # Profil je Kerze erst ab 4 feineren Kerzen


# ── Grundgrößen ───────────────────────────────────────────────────────────────────────────────────────────────────
def stufe(kurs):
    ziel = kurs * STUFE_PCT
    return min(STUFEN, key=lambda w: abs(np.log(w / ziel)))


def pos(df, tag):
    return int(df.index.get_indexer([pd.Timestamp(tag)], method="nearest")[0])


def leistung(c):
    """Veränderung in % über 1W/1M/3M/6M (Schluss zu Schluss) und seit Jahresbeginn."""
    d = {k: (None if len(c) <= n else round(float(c.iloc[-1] / c.iloc[-1 - n] - 1) * 100, 2)) for k, n in PERIODEN.items()}
    vorjahr = c[c.index.year < c.index[-1].year]
    d["YTD"] = round(float(c.iloc[-1] / vorjahr.iloc[-1] - 1) * 100, 2) if len(vorjahr) else None
    return d




def woche(df):
    """Wochenkerzen aus Tageskerzen, je Woche am Freitag beschriftet (wie der Wochenchart)."""
    return df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last",
                                     "Volume": "sum"}).dropna()


def dreissig(df):
    """30-Minuten-Kerzen des Titels aus dem Speicher (tpo_daten, auf die Tageskurse ausgerichtet), ohne Abruf; der
    Ticker steht in df.attrs["ticker"]. None ohne Datei."""
    tk = (df.attrs or {}).get("ticker") if df is not None else None
    if not tk:
        return None
    try:
        import tpo_daten
        return tpo_daten.kerzen(tk, df.iloc[:-1] if df.attrs.get("laufend") else df, abruf=False)
    except Exception:  # noqa: BLE001 – Technik: ohne lesbare Datei keine feineren Kerzen
        return None


def stunde(d30):
    """Stundenkerzen aus den 30-Minuten-Kerzen (9:30, 10:30 … New York)."""
    if d30 is None or not len(d30):
        return None
    return d30.resample("60min", offset="30min").agg({"Open": "first", "High": "max", "Low": "min",
                                                      "Close": "last", "Volume": "sum"}).dropna()


# ── Profil (Dalton) ───────────────────────────────────────────────────────────────────────────────────────────────
def profil(H, L, V, schritt):
    """Volumen je Preisstufe, POC und Wertzone 70 % vom POC nach außen (jeweils die schwerere Nachbarstufe dazu).
    Schlüssel wie volumenprofil.profil (grenzen, volumen, mitte, poc, wert_unten, wert_oben) und kurz (val, vah)."""
    H, L, V = (np.asarray(x, float) for x in (H, L, V))
    lo = np.floor(L.min() / schritt) * schritt
    hi = np.ceil(H.max() / schritt) * schritt
    kanten = np.arange(lo, hi + schritt / 2, schritt)                # Technik: halbe Stufe gegen Rundung
    if len(kanten) < 2:
        kanten = np.array([lo, lo + schritt])
    p = np.zeros(len(kanten) - 1)
    for h, l, v in zip(H, L, V):
        if not v > 0:
            continue
        if h <= l:
            p[min(max(int((h - lo) // schritt), 0), len(p) - 1)] += v
            continue
        ov = np.clip(np.minimum(kanten[1:], h) - np.maximum(kanten[:-1], l), 0, None)
        p += v * ov / (h - l)
    poc = int(p.argmax())
    s, a, b = p[poc], poc, poc
    while s < WERT * p.sum() and (a > 0 or b < len(p) - 1):
        up = p[b + 1] if b + 1 < len(p) else -1
        dn = p[a - 1] if a > 0 else -1
        if up >= dn:
            b += 1
            s += up
        else:
            a -= 1
            s += dn
    mitte = (kanten[:-1] + kanten[1:]) / 2
    return {"grenzen": kanten, "volumen": p, "mitte": mitte, "poc": float(mitte[poc]), "wert_unten": float(kanten[a]),
            "wert_oben": float(kanten[b + 1]), "val": float(kanten[a]), "vah": float(kanten[b + 1]), "schritt": schritt}


def zonen(pr):
    """Dünne Zonen (zusammenhängend unter ⅓ des POC-Volumens, mindestens 2 Stufen) und Dochte (dünne Ränder)."""
    p, k = pr["volumen"], pr["grenzen"]
    duenn = p < p.max() * DUENN
    erg = {"duenn": [], "docht_unten": None, "docht_oben": None}
    i = 0
    while i < len(p):
        if not duenn[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(p) and duenn[j + 1]:
            j += 1
        if j - i + 1 >= DUENN_MIN:
            z = (float(k[i]), float(k[j + 1]))
            if i == 0:
                erg["docht_unten"] = z
            elif j == len(p) - 1:
                erg["docht_oben"] = z
            else:
                erg["duenn"].append(z)
        i = j + 1
    return erg


def _balance(df, bis=None):
    """Beginn der Balance nach der Cockpit-Regel (Micky 21.11.2026) als Position."""
    import avwap
    b = avwap.balance_beginn(df, bis)
    n = len(df) if bis is None else bis + 1
    return b if b is not None else max(0, n - BALANCE_MIN)


def zone_beginn(df):
    """Beginn der Zone des Scanners, an der das Profil nicht vorbei darf (Cockpit-Regel): nach einem Ausbruch (bis 4
    Wochen) die Zone vom Vortag, sonst die Zone jetzt; None ohne fertige Zone. Eine Quelle für Titelseite, Analyse,
    Kartentisch und Quetschung."""
    import vcp_zone
    try:
        a = vcp_zone.ausbruch(df)
        z = vcp_zone.datiert(df, a["zone"] if a else vcp_zone.zone(df))
    except Exception:  # noqa: BLE001 – Technik: zu kurze Reihe
        return None
    return z.get("start_t") if z and z.get("zone") else None


def anker(df, zahltag=None, a_serie=None, zone_start=None):
    """(Anker-Index, Begründung, Beginn der Balance, Art): der Zahlentag, wenn er eine neue Auktion ausgelöst hat
    (Schluss ≥ 1 ATR vom Vortag) und die Balance daraus hervorging (höchstens 10 Handelstage vor ihrem Beginn) –
    Titel-Analyse, Micky 21.11.2026; sonst der Anker des grauen Profils nach der Cockpit-Regel (avwap.profil_anker:
    Beginn der Balance, nie vor der Zone; Wert wandert erst seit wenigen Tagen: die Balance davor)."""
    import avwap
    a_serie = atr_modul.reihe(df) if a_serie is None else a_serie
    start = _balance(df)
    try:
        g_tag, g_art = (avwap.profil_anker(df, zahltag, zone_start) or {}).get("grau") or (df.index[start], "Balance")
    except (ValueError, IndexError, KeyError):   # Technik: zu kurze Reihe der Ebene
        g_tag, g_art = df.index[start], "Balance"
    g_i = min(int(df.index.searchsorted(pd.Timestamp(g_tag))), len(df) - 1)
    if zahltag is not None and pd.Timestamp(zahltag) >= df.index[0]:
        i = pos(df, zahltag)
        a = float(a_serie.iloc[i - 1]) if i > 0 else float("nan")
        if i > 0 and a == a and a > 0:
            bewegung = abs(float(df["Close"].iloc[i]) - float(df["Close"].iloc[i - 1])) / a
            b_ = f"{bewegung:.2f}".replace(".", ",")
            if bewegung >= ANKER_ATR and start - ANKER_VOR <= i:
                return i, (f"Zahlentag {df.index[i]:%d.%m.}: Schluss {b_} ATR vom Vortag – neue Auktion; die Balance seit "
                           f"{df.index[start]:%d.%m.} ging daraus hervor"), start, "Zahlentag"
            grund = (f"Zahlentag {df.index[i]:%d.%m.} bewegte den Kurs nur {b_} ATR" if bewegung < ANKER_ATR else
                     f"Zahlentag {df.index[i]:%d.%m.} liegt mehr als {ANKER_VOR} Kerzen vor der Balance")
        else:
            grund = "Zahlentag ohne ATR davor"
    else:
        grund = "kein Zahlentag bekannt"
    return g_i, f"{grund} – Anker {df.index[g_i]:%d.%m.} ({g_art})", start, g_art


def profil_ab(df, stunden, i0):
    """Profil ab Index i0 aus Stundenkerzen (Micky 21.11.2026), ohne genug Stundenkerzen aus Tageskerzen."""
    schritt = stufe(float(df["Close"].iloc[-1]))
    ab = pd.Timestamp(df.index[i0]).normalize()
    st_ = stunden[stunden.index.normalize() >= ab] if stunden is not None and len(stunden) else None
    if st_ is not None and len(st_) >= STUNDEN_MIN and st_.index[0].normalize() <= ab + pd.Timedelta(days=ZEIT_VERSATZ):
        quelle, teil = "Stundenkerzen", st_
    else:
        quelle, teil = "Tageskerzen (keine Stundenkerzen für den Zeitraum)", df.iloc[i0:]
    pr = profil(teil["High"], teil["Low"], teil["Volume"], schritt)
    pr.update(zonen(pr))
    pr["quelle"], pr["kerzen"], pr["ab"] = quelle, len(teil), df.index[i0]
    return pr


def drittel(df, i0):
    """(Tiefs, Hochs) der drei Drittel seit dem Anker, oder None bei weniger als 6 Kerzen."""
    teil = df.iloc[i0:]
    if len(teil) < QUETSCH_MIN:
        return None
    teile = np.array_split(np.arange(len(teil)), DRITTEL)
    return [float(teil["Low"].iloc[x].min()) for x in teile], [float(teil["High"].iloc[x].max()) for x in teile]


def quetschung(df, i0):
    """Einquetschen seit dem Anker (Titel-Analyse, Micky 21.11.2026): die Tiefs der drei Drittel steigen, ihre Hochs
    liegen höchstens 2 % auseinander (aufsteigend); gespiegelt: Hochs fallen, Tiefs höchstens 2 % auseinander
    (absteigend). → {art, tiefs, hochs, oberkante|unterkante, tage} oder None."""
    d = drittel(df, i0)
    if d is None:
        return None
    tiefs, hochs = d
    teil = df.iloc[i0:]
    if tiefs[0] < tiefs[1] < tiefs[2] and max(hochs) / min(hochs) <= 1 + QUETSCH_HOCHS:
        return {"art": "aufsteigend", "tiefs": tiefs, "hochs": hochs, "oberkante": round(max(hochs), 2),
                "tage": len(teil), "ab": df.index[i0]}
    if hochs[0] > hochs[1] > hochs[2] and max(tiefs) / min(tiefs) <= 1 + QUETSCH_HOCHS:
        return {"art": "absteigend", "tiefs": tiefs, "hochs": hochs, "unterkante": round(min(tiefs), 2),
                "tage": len(teil), "ab": df.index[i0]}
    return None


def struktur(df, stunden, zahltag=None, zone_start=None):
    """Anker, Profil ab Anker, Rand der Balance als Pivot long und short mit Tests, Quetschung seit dem Anker."""
    a_serie = atr_modul.reihe(df)
    i0, grund, ib_roh, art = anker(df, zahltag, a_serie, zone_start)
    ib = max(i0, ib_roh)                         # Pivots ab dem Anker (Titel-Analyse)
    bal = df.iloc[ib:]
    hoch, tief = float(bal["High"].max()), float(bal["Low"].min())
    return {"anker_i": i0, "anker": df.index[i0], "anker_grund": grund, "anker_art": art, "balance_i": ib, "balance_roh": df.index[ib_roh], "balance_start": df.index[ib],
            "profil": profil_ab(df, stunden, i0), "kurs": float(df["Close"].iloc[-1]),
            "atr": float(a_serie.iloc[-1]) if a_serie.iloc[-1] == a_serie.iloc[-1] else None,
            "pivot": hoch, "pivot_tag": bal["High"].idxmax(),
            "tests_oben": [d for d, h in bal["High"].items() if h >= hoch * (1 - PIVOT_TEST)],
            "short_pivot": tief, "short_pivot_tag": bal["Low"].idxmin(),
            "tests_unten": [d for d, l in bal["Low"].items() if l <= tief * (1 + PIVOT_TEST)],
            "quetsch": quetschung(df, i0), "drittel": drittel(df, i0)}


def alte_balance(df, vor_index):
    """Profil der letzten Balance von mindestens 10 Tagen vor dem Anker (Titel-Analyse, Micky 21.11.2026) – der Bezug
    nach einem Ausbruch – oder None. Beginn nach der Cockpit-Regel."""
    for k in range(1, ALT_SUCHE + 1):
        ende = vor_index - k
        if ende < ALT_MIN:
            return None
        b = _balance(df, ende)
        if ende - b + 1 >= ALT_MIN:
            teil = df.iloc[b:ende + 1]
            pr = profil(teil["High"], teil["Low"], teil["Volume"], stufe(float(df["Close"].iloc[-1])))
            pr.update({"start": df.index[b], "ende": df.index[ende], "tief": float(teil["Low"].min()),
                       "hoch": float(teil["High"].max())})
            return pr
    return None


# ── AVWAP: Zange ──────────────────────────────────────────────────────────────────────────────────────────────────
def avwap_liste(df, zahltag=None):
    """Alle AVWAP des Cockpits (avwap.anker) mit Wert und Abstand des Kurses; dazu die Zange."""
    import avwap
    kurs = float(df["Close"].iloc[-1])
    a = avwap.anker(df, zahltag) or {}
    erg = []
    for k, tag in a.items():
        if not isinstance(tag, pd.Timestamp):
            continue
        r = avwap.reihe(df, tag)
        if not len(r):
            continue
        erg.append({"anker": k, "tag": tag, "wert": float(r.iloc[-1]), "linie": r,
                    "abstand": round((kurs / float(r.iloc[-1]) - 1) * 100, 2)})
    lh = next((e for e in erg if e["anker"] == "hoch"), None)
    lt = next((e for e in erg if e["anker"] == "tief"), None)
    zange = None
    if lh and lt and min(len(lh["linie"]), len(lt["linie"])) > 1:
        zurueck = min(ZANGE_TAGE, len(lh["linie"]) - 1, len(lt["linie"]) - 1)
        zange = {"vorher": round(float(lh["linie"].iloc[-1 - zurueck] - lt["linie"].iloc[-1 - zurueck]), 2),
                 "heute": round(lh["wert"] - lt["wert"], 2), "tage": zurueck,
                 "ueber": kurs > max(lh["wert"], lt["wert"]), "unter": kurs < min(lh["wert"], lt["wert"])}
    return erg, zange


# ── Relative Stärke und Geldfluss ─────────────────────────────────────────────────────────────────────────────────
DRUCK_SCHWELLE = -0.2   # Druck-Tag des Index (O'Neils Distributionstag): Schluss mindestens 0,2 % tiefer bei höherem
DRUCK_FENSTER = 25      # Volumen als am Vortag, in den letzten 25 Sitzungen


def abgabetage(index):
    """Druck-Tage des Index in den letzten 25 Sitzungen (O'Neils Distributionstage) – dort zeigt sich, wer Druck
    aushält (Stärke in der Schwäche)."""
    c, v = index["Close"], index["Volume"]
    n = len(c)
    return [c.index[i] for i in range(max(1, n - DRUCK_FENSTER), n)
            if (c.iloc[i] / c.iloc[i - 1] - 1) * 100 <= DRUCK_SCHWELLE and v.iloc[i] > v.iloc[i - 1]]


def staerke_in_schwaeche(df, index):
    """An jedem Distributionstag des Index: Veränderung des Titels gegen die des Index (Titel-Analyse, Micky
    21.11.2026 neben zeichen.tage_gegen_markt) → {tage: [...], besser, n}."""
    if index is None or "Volume" not in index:
        return None
    zeilen = []
    for d in abgabetage(index):
        if d in df.index and d in index.index:
            i, j = df.index.get_loc(d), index.index.get_loc(d)
            if i < 1 or j < 1:
                continue
            zeilen.append({"tag": d, "titel": round(float(df["Close"].iloc[i] / df["Close"].iloc[i - 1] - 1) * 100, 2),
                           "index": round(float(index["Close"].iloc[j] / index["Close"].iloc[j - 1] - 1) * 100, 2)})
    return {"tage": zeilen, "besser": sum(1 for z in zeilen if z["titel"] > z["index"]), "n": len(zeilen)}


def cmf(df, n=CMF_TAGE):
    """Chaikin Money Flow über n Tage mit den Kerzen, die ihn treiben."""
    t = df.iloc[-n:]
    spanne = (t["High"] - t["Low"]).replace(0, np.nan)
    mf = (((t["Close"] - t["Low"]) - (t["High"] - t["Close"])) / spanne).fillna(0) * t["Volume"]
    wert = float(mf.sum() / t["Volume"].sum()) if t["Volume"].sum() else None
    folge = mf.sort_values()
    return {"wert": round(wert, 3) if wert is not None else None,
            "plus": [(d, float(x)) for d, x in folge.iloc[::-1].items() if x > 0][:CMF_TREIBER],
            "minus": [(d, float(x)) for d, x in folge.items() if x < 0][:CMF_TREIBER]}


def sektor_rang(sektoren_df):
    """{ETF: {1M, 3M, 6M, rang_1M, rang_3M, rang_6M}} aus Tageskerzen der 11 Sektor-ETFs."""
    tab = {s: {k: leistung(df["Close"])[k] for k in ("1M", "3M", "6M")} for s, df in sektoren_df.items() if df is not None}
    for k in ("1M", "3M", "6M"):
        for r, s in enumerate(sorted((s for s in tab if tab[s][k] is not None), key=lambda s: -tab[s][k]), 1):
            tab[s][f"rang_{k}"] = r
    return tab


























# ── Wertwanderung ─────────────────────────────────────────────────────────────────────────────────────────────────
def klasse(v0, h0, v1, h1):
    """Wertzone heute (v1–h1) gegen die vorige (v0–h0) in 6 Klassen – die Regel aus marketprofile.klasse."""
    import marketprofile
    return marketprofile.NAME[marketprofile.klasse(v0, h0, v1, h1)]


def wanderung(df, fein, gruppe, atr_wert):
    """POC und Wertzone je Kerze der Ebene aus feineren Kerzen (Tag aus 30 Minuten, Woche aus Stunden): Klassen,
    Treppe, Ballen, Abtasten, nackte POCs. None ohne feinere Kerzen."""
    if fein is None or not len(fein) or atr_wert is None:
        return None
    schritt = stufe(float(df["Close"].iloc[-1]))
    schl = fein.index.normalize() if gruppe == "D" else _freitag(fein.index)      # Woche: Freitag (W-FRI)
    werte = {}
    for t, k in fein.groupby(schl):
        if t in df.index and len(k) >= WANDER_KERZEN:
            pr = profil(k["High"], k["Low"], k["Volume"], schritt)
            werte[t] = (pr["poc"], pr["val"], pr["vah"])
    tage = [t for t in df.index if t in werte]
    if len(tage) < TREPPE:
        return None
    klassen = [(b, klasse(werte[a][1], werte[a][2], werte[b][1], werte[b][2])) for a, b in zip(tage[:-1], tage[1:])]
    pocs = [werte[t][0] for t in tage]
    richt, n = 0, 0
    for a_, b_ in zip(pocs[::-1][1:], pocs[::-1][:-1]):          # von heute rückwärts
        r_ = 1 if b_ > a_ else -1 if b_ < a_ else 0
        if r_ == 0 or (richt and r_ != richt):
            break
        richt, n = r_, n + 1
    letzte = pocs[-BALLEN_N:]
    t_heute, t_vor = tage[-1], tage[-2]
    kurs = float(df["Close"].loc[t_heute])
    _, v0, h0 = werte[t_vor]
    p1 = werte[t_heute][0]
    nackt = []
    for t in tage[-NACKT_N:-1]:
        poc = werte[t][0]
        spaeter = df.loc[df.index > t]
        if not ((spaeter["Low"] <= poc) & (spaeter["High"] >= poc)).any():
            nackt.append((t, poc))
    jetzt = float(df["Close"].iloc[-1])
    return {"werte": werte, "klassen": klassen, "treppe": (richt, n + 1 if n else 0),
            "ballen": len(letzte) == BALLEN_N and max(letzte) - min(letzte) <= atr_wert,
            "ballen_spanne": max(letzte) - min(letzte),
            "abtasten": "oben" if kurs > h0 and p1 <= h0 else "unten" if kurs < v0 and p1 >= v0 else None,
            "nackt": nackt, "nackt_ueber": min((x for x in nackt if x[1] > jetzt), key=lambda x: x[1], default=None),
            "nackt_unter": max((x for x in nackt if x[1] < jetzt), key=lambda x: x[1], default=None),
            "heute": t_heute, "poc_heute": p1, "vah_vor": h0, "val_vor": v0}


# ── Je Zeitebene ──────────────────────────────────────────────────────────────────────────
def _freitag(index):
    """Freitag der Woche je Zeitpunkt – der Schlüssel der Wochenkerzen (W-FRI)."""
    return index.normalize() + pd.to_timedelta((FREITAG - index.dayofweek) % WOCHENTAGE, unit="D")


def ebene_zeit(df, tag, name):
    """Ein Tag (Zahlentag) als Kerze der Ebene: Woche = die Woche, die ihn enthält; Stunde = erste Stunde des Tages."""
    if tag is None or df is None or not len(df):
        return None
    t = pd.Timestamp(tag)
    if name == "Woche":
        t = _freitag(pd.DatetimeIndex([t]))[0]
    i = int(df.index.searchsorted(t))
    return df.index[i] if i < len(df) else None


def ebene(name, df, d30, zahltag=None, tage=None):
    """Bausteine einer Zeitebene mit denselben Regeln (Micky 20.11.2026, Titel-Analyse), gezählt in Kerzen der Ebene:
    Struktur (Anker, Profil, Pivots, Quetschung), alte Wertzone, Wertwanderung (PbD entfernt 22.11.2026). df = Kerzen der Ebene, d30 =
    30-Minuten-Kerzen, tage = Tageskerzen (für die Woche). Woche: Zeitprofil und Schwänze aus Tageskerzen,
    Profil und Wanderung aus Stundenkerzen; Tag: Profil aus Stunden-, Zeitprofil, Schwänze und Wanderung aus
    30-Minuten-Kerzen; Stunde: Profil und Zeitprofil aus 30-Minuten-Kerzen, ohne Schwänze und Wanderung."""
    if df is None or len(df) < 2 * IMPULS_SCHLUESSE + ALT_MIN:
        return None
    h1 = stunde(d30)
    st_ = struktur(df, d30 if name == "Stunde" else h1, ebene_zeit(df, zahltag, name))
    a = st_["atr"]
    return {"name": name, "df": df, "struktur": st_, "atr": a, "alt": alte_balance(df, st_["anker_i"]),
            "fein": d30 if name == "Stunde" else h1,
            "wander": None if name == "Stunde" else wanderung(df, d30 if name == "Tag" else h1, "D" if name == "Tag" else "W", a)}


