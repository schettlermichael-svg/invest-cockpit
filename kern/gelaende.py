"""Gelände (05.11.2026): Market-Profile-Zonen und Volumen als eine Karte – das Rückgrat um die Regeln der Meister.

Jede Zone des Market Profile (Zeit, aus 30-Minuten-Kerzen) bekommt ihr Volumen dazu:
  Volumen-POC     Volumen jeder 30-Minuten-Kerze gleichmäßig über ihre Spanne verteilt, 40 Preisfächer der Zone
  Volumen         mittleres Tagesvolumen in der Zone ÷ Median des Tagesvolumens der 12 Monate bis zum Ende der Zone
  Druck           Tage mit Verkaufsdruck (Schluss ≥ 0,2 % tiefer, Volumen über Vortag – O'Neils Verteilungstag)
                  gegen Tage mit Kaufdruck (spiegelbildlich)
Daraus (Auction Market Theory, O'Neil, Minervini – Zeichen, keine Filter):
  Art             Festung (Volumen ≥ 1,2 × Median: echte Akzeptanz) · Wartesaal (≤ 0,9: viel Zeit, kaum Handel) · normal
  Lesart          Verteilung (Verkaufstage mindestens 2 mehr und 1,5-mal so viele) · Akkumulation (spiegelbildlich) ·
                  neutral
  Lawinenhang     Wartesaal mit Verteilung – die Stellung ist kaum besetzt und wird geräumt (O'Neil: Verteilungstage)
  stille Akkum.   Wartesaal mit Akkumulation – ruhige Zone, die Nachfrage zeigt sich an steigenden Tagen (Minervini)
Gelände um den Kurs: nächste Festung (bzw. fester Knoten des 52-Wochen-Profils) darüber und darunter, Raum bis dorthin,
Überhang (Festungen über dem Kurs), Stellung hinter dem Stopp, Wanderung des Werts, Rücktest, dünne Spitze.
Ohne 30-Minuten-Kerzen: kein Steckbrief, das Cockpit arbeitet mit den übrigen Ampeln weiter.
Die Schwellen sind unsere Setzung.
"""
import numpy as np
import pandas as pd

FESTUNG, WARTESAAL = 1.2, 0.9
FAECHER = 40
NAH = 0.01
UEBERHANG_BIS = 0.25            # Überhang: Festungen bis 25 % über dem Kurs


def _z(x, s=1):
    return f"{x:,.{s}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def steckbrief(z, k30, df):
    """Volumen-Fährte einer Zone (z: Zone des Market Profile mit beginn/ende/tief/hoch/poc)."""
    a, e = pd.Timestamp(z["beginn"]), pd.Timestamp(z["ende"]) + pd.Timedelta(days=1)
    k = k30[(k30.index >= a) & (k30.index < e)] if k30 is not None else None
    s = {"vpoc": None, "verschub": None}
    if k is not None and len(k) and z["hoch"] > z["tief"]:
        g = np.linspace(z["tief"], z["hoch"], FAECHER + 1)
        v = np.zeros(FAECHER)
        for lo, hi, vol in zip(k["Low"].to_numpy(float), k["High"].to_numpy(float), k["Volume"].to_numpy(float)):
            i0 = min(FAECHER - 1, max(0, int(np.searchsorted(g, lo)) - 1))
            i1 = min(FAECHER - 1, max(i0, int(np.searchsorted(g, hi)) - 1))
            v[i0:i1 + 1] += vol / (i1 - i0 + 1)
        if v.sum() > 0:
            i = int(np.argmax(v))
            s["vpoc"] = float((g[i] + g[i + 1]) / 2)
            s["verschub"] = (s["vpoc"] - z["poc"]) / (z["hoch"] - z["tief"])
    d = df.loc[a:e - pd.Timedelta(days=1)]
    vorher = df["Volume"].loc[:e].iloc[-252:]
    med = float(vorher.median()) if len(vorher) >= 60 else None
    s["volumen"] = float(d["Volume"].mean() / med) if med and len(d) else None
    c, v_ = d["Close"], d["Volume"]
    s["ab"] = int(((c < c.shift(1) * 0.998) & (v_ > v_.shift(1))).sum())
    s["auf"] = int(((c > c.shift(1) * 1.002) & (v_ > v_.shift(1))).sum())
    vol = s["volumen"]
    s["art"] = None if vol is None else "Festung" if vol >= FESTUNG else "Wartesaal" if vol <= WARTESAAL else "normal"
    if s["ab"] - s["auf"] >= 2 and s["ab"] >= 1.5 * s["auf"]:
        s["lesart"] = "Verteilung"
    elif s["auf"] - s["ab"] >= 2 and s["auf"] >= 1.5 * s["ab"]:
        s["lesart"] = "Akkumulation"
    else:
        s["lesart"] = "neutral"
    s["zeichen"] = ("Lawinenhang" if s["art"] == "Wartesaal" and s["lesart"] == "Verteilung" else
                    "stille Akkumulation" if s["art"] == "Wartesaal" and s["lesart"] == "Akkumulation" else None)
    return s


def _knoten(df):
    """Knoten des 52-Wochen-Volumenprofils (Tageskerzen) als [(unten, oben)]."""
    import volumenprofil
    p = volumenprofil.profil(df, max(0, len(df) - volumenprofil.JAHR))
    return (volumenprofil.zonen(p)["knoten"], p) if p else ([], None)


def gelaende(tk, df, erk, stopp=None, seite=None):
    """Gelände eines Titels: Zonen mit Steckbrief, Halt/Widerstand, Raum, Überhang, Stellung hinter dem Stopp und die
    Zeichen als Liste (Ampel, Titel, Text). None ohne Market Profile."""
    mp = (erk or {}).get("mp")
    if not mp or not mp.get("zonen"):
        return None
    try:
        import tpo_daten
        k30 = tpo_daten.lesen(tk)
    except Exception:  # noqa: BLE001
        k30 = None
    zonen = []
    for k, z in enumerate(mp["zonen"]):
        z_ = dict(z)
        if k == len(mp["zonen"]) - 1:
            z_["ende"] = df.index[-1]
        z_.update(steckbrief(z_, k30, df))
        zonen.append(z_)
    kurs = float(df["Close"].iloc[-1])
    knoten, profil = _knoten(df)
    festungen = [z for z in zonen[:-1] if z.get("art") == "Festung"]
    # Halt darunter / Widerstand darüber: Kante der nächsten Festung (VAH unten, VAL oben) oder eines festen Knotens
    unten = [(z["vah"], f'Festung {z["beginn"]:%d.%m.}–{z["ende"]:%d.%m.%y}') for z in festungen if z["vah"] < kurs * (1 - NAH)]
    oben = [(z["val"], f'Festung {z["beginn"]:%d.%m.}–{z["ende"]:%d.%m.%y}') for z in festungen if z["val"] > kurs * (1 + NAH)]
    unten += [(kn[1], "Volumenknoten") for kn in knoten if kn[1] < kurs * (1 - NAH)]
    oben += [(kn[0], "Volumenknoten") for kn in knoten if kn[0] > kurs * (1 + NAH)]
    halt = max(unten, key=lambda x: x[0]) if unten else None
    widerstand = min(oben, key=lambda x: x[0]) if oben else None
    aktuell = zonen[-1]
    g = {"zonen": zonen, "aktuell": aktuell, "halt": halt, "widerstand": widerstand, "kurs": kurs,
         "raum_ab": (1 - halt[0] / kurs) if halt else None, "raum_auf": (widerstand[0] / kurs - 1) if widerstand else None,
         "profil": profil, "knoten": knoten}
    # Überhang: Festungen über dem Kurs bis +25 %
    ueber = [z for z in festungen if z["val"] > kurs and z["val"] <= kurs * (1 + UEBERHANG_BIS)]
    g["ueberhang"] = ueber
    g["zeichen"] = _zeichen(g, df, erk, stopp, seite)
    return g


def stellung(g, preis):
    """Was am Preis steht: Festung, Wartesaal, Volumenknoten oder Niemandsland."""
    for z in reversed(g["zonen"][:-1]):
        if z["tief"] <= preis <= z["hoch"] and z.get("art") in ("Festung", "Wartesaal"):
            return z["art"]
    if any(kn[0] <= preis <= kn[1] for kn in g["knoten"]):
        return "Volumenknoten"
    return "Niemandsland"


def ziel(g, einstieg, seite):
    """Nächste feste Stellung jenseits des Einstiegs UND des Kurses (Festung oder Knoten) – Ziel für das CRV:
    (Preis, Art) oder None. Ist der Kurs schon über den Einstieg hinaus gelaufen, zählt nur, was noch vor ihm liegt."""
    einstieg = max(einstieg, g["kurs"]) if seite == "long" else min(einstieg, g["kurs"])
    kand = []
    for z in g["zonen"][:-1]:
        if z.get("art") != "Festung":
            continue
        x = z["val"] if seite == "long" else z["vah"]
        if (x > einstieg * (1 + NAH)) if seite == "long" else (x < einstieg * (1 - NAH)):
            kand.append((x, f'Festung {z["beginn"]:%d.%m.}–{z["ende"]:%d.%m.%y}'))
    for kn in g["knoten"]:
        x = kn[0] if seite == "long" else kn[1]
        if (x > einstieg * (1 + NAH)) if seite == "long" else (x < einstieg * (1 - NAH)):
            kand.append((x, "Volumenknoten"))
    if not kand:
        return None
    return (min if seite == "long" else max)(kand, key=lambda t: t[0])


def _zeichen(g, df, erk, stopp, seite):
    """Zeichen des Geländes als Liste (Ampel, Titel, Text) – angezeigt und gedeutet, nie gefiltert."""
    aus = []
    z = g["aktuell"]
    kurs = g["kurs"]
    seite = seite or (erk or {}).get("seite") or "long"
    # 1. Die Zone, in der der Kurs steht bzw. aus der er gerade kommt
    if z.get("art"):
        if z.get("zeichen") == "Lawinenhang":
            a = "rot" if seite == "long" else "grün"
            t = "Lawinenhang: Wartesaal mit Verteilung – die Stellung ist kaum besetzt und wird geräumt"
        elif z.get("zeichen") == "stille Akkumulation":
            a = "grün" if seite == "long" else "rot"
            t = "stille Akkumulation: ruhige Zone, die Nachfrage zeigt sich an steigenden Tagen"
        else:
            a = {"Akkumulation": "grün", "Verteilung": "rot"}.get(z["lesart"], "grau")
            if seite == "short" and a in ("grün", "rot"):
                a = "rot" if a == "grün" else "grün"
            t = f'{z["art"]}, {z["lesart"]}'
        aus.append((a, "Zone", f'{t} · Volumen {_z(z["volumen"], 2)} × Jahresmedian · Tage Verkauf/Kauf '
                               f'{z["ab"]}/{z["auf"]}'))
    # 2. Gelände in Laufrichtung: Raum bis zur nächsten Festung
    if seite == "long":
        w = g["widerstand"]
        if w:
            r = g["raum_auf"] * 100
            aus.append(("grün" if r >= 10 else "gelb" if r >= 5 else "rot", "Raum ↑",
                        f'{_z(r)} % bis {w[1]} bei {_z(w[0], 2)} $' + (" – der Ausbruch läuft sich schnell fest" if r < 5
                                                                     else " – freie Bahn" if r >= 10 else "")))
        else:
            aus.append(("grün", "Raum ↑", "keine Festung darüber – freie Bahn"))
    else:
        h = g["halt"]
        if h:
            r = g["raum_ab"] * 100
            aus.append(("grün" if r >= 10 else "gelb" if r >= 5 else "rot", "Raum ↓",
                        f'{_z(r)} % bis {h[1]} bei {_z(h[0], 2)} $' + (" – Niemandsland, die Lawine hat Raum" if r >= 10
                                                                     else " – der Bruch wird bald aufgefangen" if r < 5 else "")))
        else:
            aus.append(("grün", "Raum ↓", "keine Festung darunter – Niemandsland bis weit hinab"))
        # Squeeze: Raum über dem Short-Einstieg
        if g["raum_auf"] is not None and g["raum_auf"] >= 0.08:
            aus.append(("gelb", "Squeeze-Raum ↑", f'{_z(g["raum_auf"] * 100)} % ohne feste Stellung darüber – scheitert '
                                                   f'der Bruch, steigt der Kurs schnell; Stopp knapp setzen'))
    # 3. Überhang (O'Neil: overhead supply)
    if seite == "long":
        u = g["ueberhang"]
        aus.append(("rot" if len(u) >= 2 else "gelb" if u else "grün", "Überhang",
                    f'{len(u)} Festung{"en" if len(u) != 1 else ""} bis +25 % über dem Kurs'
                    + (" – Käufer im Minus verkaufen bei Einstand, zäher Weg" if u else " – leichter Weg")))
    # 4. Stellung hinter dem Stopp
    if stopp:
        st = stellung(g, stopp)
        a = "grün" if st in ("Festung", "Volumenknoten") else "gelb" if st == "Wartesaal" else "rot"
        aus.append((a, "Stellung hinter dem Stopp", f'Stopp {_z(stopp, 2)} $ liegt in {"einer " if st != "Niemandsland" else ""}'
                                                     f'{st}' + (" – geschützt" if a == "grün" else
                                                                " – rauscht durch bis zur nächsten Stellung" if a == "rot" else
                                                                " – schwacher Schutz")))
    # 5. Rücktest der letzten Bewegung
    mp = erk.get("mp") or {}
    sig = [s_ for s_ in mp.get("signale", []) if s_["art"] == "R"]
    if sig and sig[-1]["i"] >= len(mp.get("tage", [])) - 10:
        r_ = sig[-1]
        st = stellung(g, float(r_["preis"]))
        aus.append(("grün" if st in ("Festung", "Volumenknoten") else "gelb", "Rücktest",
                    f'R{r_["dir"]} am {r_["tag"]:%d.%m.} auf {st}' + (" – stärkster Rücktest" if st in ("Festung", "Volumenknoten")
                                                                       else " – wenig Halt")))
    # 6. Wanderung des Werts (POC-Treppe gegen 52-Wochen-POC)
    zs = g["zonen"]
    if len(zs) >= 3 and g["profil"]:
        p3 = [x["poc"] for x in zs[-3:]]
        p52 = g["profil"]["poc"]
        abst = (kurs / p52 - 1) * 100
        if p3[0] < p3[1] < p3[2]:
            aus.append(("grün" if seite == "long" else "gelb", "Wert wandert ↑",
                        f'POC der Zonen steigen; 52-Wochen-POC {_z(p52, 2)} $ liegt {_z(abs(abst))} % '
                        f'{"unter" if abst > 0 else "über"} dem Kurs (Magnet bei einer Wende)'))
        elif p3[0] > p3[1] > p3[2]:
            aus.append(("rot" if seite == "long" else "grün", "Wert wandert ↓",
                        f'POC der Zonen fallen; 52-Wochen-POC {_z(p52, 2)} $ liegt {_z(abs(abst))} % '
                        f'{"unter" if abst > 0 else "über"} dem Kurs'))
    # 7. Dünne Spitze: neues 52-Wochen-Hoch aus einem Wartesaal
    h52 = float(df["High"].iloc[-252:].max())
    if z.get("art") == "Wartesaal" and z["hoch"] >= h52 * 0.99:
        aus.append(("rot" if seite == "long" else "grün", "Dünne Spitze",
                    "Hoch aus einem Wartesaal – der Anstieg wird von den großen Adressen nicht getragen"))
    return aus
