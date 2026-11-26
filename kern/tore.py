"""Drei Tore vor jedem Trade: Richtung → Ort → Auslöser (Harry Sharp, Interview IQCapital 06.11.2026; übernommen und
auf unser System übertragen von Micky am 26.11.2026). Der Auslöser soll erst feuern, wenn Richtung und Ort passen –
gefiltert wird nichts: ein Tor gegen das Setup zeigt ✗, das Signal bleibt stehen.

  Richtung  Sharps Zwei-Kerzen-Regel eine Stufe höher (wir halten Wochen, er Stunden): die letzte abgeschlossene
            Wochenkerze und die letzte Tageskerze – beide grün aufwärts, beide rot abwärts, sonst gemischt; bei gemischt
            entscheidet die Lage der Woche nach Livermore (seine „Story der Woche“), ist auch sie in der Gefechtspause, die
            Tageskerze (sie wiegt schwerer). Die Treppe ist Livermores Lage je Ebene (kein eigenes Wort).
  Ort       Lage in der Spanne, Weg voraus (sauber/unruhig), Chop, weit gelaufen – livermore.ort, auf denselben
            Stellungen wie die Frontkarte. Long: ✗ bei Chop, weit gelaufen aufwärts oder unruhigem Weg nach oben;
            short gespiegelt.
  Auslöser  unser Setup (½ antasten an der Kante, ½ aufstocken bei 📒): ⏳ wartet, ✓ ausgelöst, ✓📒 aufgestockt.

Sharps Auslöser (Feder, Stopp-Kauf, 50-%-Regel), sein enger Stopp, Linien am Körper und Bruch ohne Puffer sind bewusst
nicht übernommen (Micky 26.11.2026) – dort bleibt Livermore.
"""
import livermore
import tiefe

KERZE = {"grün": "🟢", "rot": "🔴", "doji": "⚪"}


def _farbe(o, c):
    return "grün" if c > o else "rot" if c < o else "doji"


def zwei_kerzen(df, laufend=False):
    """Die letzte abgeschlossene Wochenkerze und Tageskerze → {"woche", "tag"} je grün/rot/doji. Die laufende Woche
    (letzter Kurstag vor Freitag) und bei laufend=True der laufende Tag zählen nicht."""
    d = df.iloc[:-1] if laufend and len(df) > 1 else df
    w = tiefe.woche(d)
    if len(w) > 1 and d.index[-1].weekday() < tiefe.FREITAG:    # Woche noch nicht zu Ende (Mo–Do)
        w = w.iloc[:-1]
    if not len(w) or not len(d):
        return None
    return {"woche": _farbe(float(w["Open"].iloc[-1]), float(w["Close"].iloc[-1])),
            "tag": _farbe(float(d["Open"].iloc[-1]), float(d["Close"].iloc[-1]))}


def richtung(df, laufend=False):
    """Richtung → {"wert": auf/ab/None, "kerzen", "woche_lage", "grund"} oder None."""
    zk = zwei_kerzen(df, laufend)
    if not zk:
        return None
    nbw = livermore.notizbuch(tiefe.woche(df))
    sp_w = nbw["spalte"] if nbw else None
    if zk["woche"] == zk["tag"] == "grün":
        wert, grund = "auf", "beide Kerzen grün"
    elif zk["woche"] == zk["tag"] == "rot":
        wert, grund = "ab", "beide Kerzen rot"
    elif sp_w in ("AT", "AB"):
        wert, grund = ("auf" if sp_w == "AT" else "ab"), f"gemischt, die Woche entscheidet: {livermore.lage(sp_w)[1]}"
    else:
        wert = {"grün": "auf", "rot": "ab"}.get(zk["tag"])
        grund = "gemischt, die Woche ruht, die Tageskerze entscheidet" if wert else "gemischt, ohne Entscheidung"
    return {"wert": wert, "kerzen": zk, "woche_lage": sp_w, "grund": grund}


def tore(df, trade=None, laufend=False):
    """Die drei Tore eines Titels (Tag) → {richtung, ort, ausloeser, r, o, a, kurz}; r/o/a = ✓, ✗ oder leer."""
    df = df.dropna(subset=["High", "Low", "Close"])
    nb = livermore.notizbuch(df)
    ri = richtung(df, laufend)
    seite = (trade or {}).get("richtung")
    ab = ({"oben" if seite > 0 else "unten": trade["pivot"]}       # wartet das Setup, zählt der Weg ab der Kante
          if trade and trade.get("wartet") and trade.get("pivot") else None)
    ot = livermore.ort(df, nb, ab=ab) if nb else None
    r_ = o_ = ""
    if seite and ri and ri["wert"]:
        r_ = "✓" if (ri["wert"] == "auf") == (seite > 0) else "✗"
    if seite and ot:
        vorn = ot["weg"]["oben" if seite > 0 else "unten"]
        gegen = ot["chop"] or ot["weit"] == ("auf" if seite > 0 else "ab") or vorn["unruhig"]
        o_ = "✗" if gegen else "✓"
    if not trade:
        a_ = ""
    elif trade.get("aufgestockt"):
        a_ = "✓📒"
    else:
        a_ = "⏳" if trade.get("wartet") else "✓"
    kurz = " ".join(f"{k}{v}" for k, v in (("R", r_), ("O", o_), ("A", a_)) if v) if trade else ""
    return {"richtung": ri, "ort": ot, "r": r_, "o": o_, "a": a_, "kurz": kurz}


def _pz(x):
    """Prozent mit Vorzeichen in deutscher Schreibweise: +4,4 % · −13,1 %."""
    return f"{'+' if x >= 0 else '−'}{abs(x):.1f} %".replace(".", ",")


def ort_text(ot, seite=None):
    """Ort in Worten: Drittel, Weg voraus, Chop, weit gelaufen (seite = Richtung des Setups, sonst beide Wege)."""
    if not ot:
        return ""
    teile = [ot["drittel"]] if ot["drittel"] else []
    for s_, wort in (("oben", "nach oben"), ("unten", "nach unten")):
        if seite and (s_ == "oben") != (seite > 0):
            continue
        w = ot["weg"][s_]
        wo = f"{'über' if s_ == 'oben' else 'unter'} der Kante" if w["von_kante"] else wort
        if w["sauber"]:
            teile.append(f"{wo} sauber" + (f" bis {_pz(w['bis'])}" if w["bis"] is not None else ""))
        elif w["unruhig"]:
            teile.append(f"{wo} unruhig · {w['n']} Niveaus")
    if ot["chop"]:
        teile.append("⚪ Chop")
    if ot["weit"]:
        teile.append("⚠ weit gelaufen – Rücksetzer abwarten" if ot["weit"] == "auf" else "⚠ weit gefallen – Erholung abwarten")
    return " · ".join(teile)


def zeile(to, trade=None):
    """Die Torzeile in Worten: 🚦 Richtung ✓ aufwärts (Woche 🟢 · Tag 🔴, Grund) · Ort ✓ … · Auslöser ⏳ …"""
    if not to:
        return ""
    ri = to["richtung"]
    teile = []
    if ri:
        wert = {"auf": "aufwärts", "ab": "abwärts"}.get(ri["wert"], "offen")
        teile.append(f'Richtung {to["r"]} {wert} (Woche {KERZE[ri["kerzen"]["woche"]]} · Tag {KERZE[ri["kerzen"]["tag"]]}'
                     f'{"" if ri["grund"].startswith("beide") else " · " + ri["grund"]})')
    ot_ = ort_text(to["ort"], (trade or {}).get("richtung"))
    if ot_:
        teile.append(f'Ort {to["o"]} {ot_}'.replace("  ", " "))
    if trade:
        teile.append(f'Auslöser {to["a"][0]} ' + ("📒 erreicht, aufgestockt" if to["a"] == "✓📒" else
                                               f'Schluss {"über" if trade["richtung"] > 0 else "unter"} '
                                               f'{trade["pivot"]:.2f}'.replace(".", ",") if to["a"] == "⏳" else "ausgelöst"))
    return "🚦 " + " · ".join(teile)
