"""Market Profile nach J. Peter Steidlmayer (CBOT) und James Dalton – aus 30-Minuten-Kerzen, für beide Richtungen.

Tagesprofil: jede 30-Minuten-Kerze der regulären Sitzung ist ein Zeitabschnitt (TPO, 13 je Tag). Sie setzt in jede
    Preiszeile, die ihre Spanne berührt, eine Marke. Preiszeilen: festes logarithmisches Raster, jede Zeile 0,2 % breit.
POC: Zeile mit den meisten Marken; bei Gleichstand die zur Mitte der Spanne nächste.
Wertbereich (70 %): vom POC aus werden je zwei Zeilen darüber und darunter verglichen und das Paar mit mehr Marken
    hinzugenommen (Steidlmayer), bis 70 % aller Marken erfasst sind.
Zone (Dalton, überlappender Wert, Wochenprofile): eine abgeschlossene Woche gehört zur Zone, solange ihr Wertbereich den
    gemeinsamen Wertbereich der Zone überlappt. Liegt er ganz darüber oder darunter, ist der Wert gewandert (B), mit
    dieser Woche beginnt die nächste Zone.
Tageswert zum Vortag: ▲ ganz höher · △ überlappend höher · ▬ unverändert (innen/außen) · ▽ überlappend tiefer · ▼ ganz tiefer.

Auslöser je Tag, gemessen an der Zone der abgeschlossenen Wochen davor (kein Blick in die Zukunft):
    A  Schluss jenseits des Rahmens und Tageswert ganz außerhalb des Zonenwerts, Zone mindestens 3 Wochen alt
    F  dasselbe in einer jüngeren Zone, die selbst aus einem Ausbruch in dieselbe Richtung entstand (Fortsetzung)
    U  dasselbe in einer jüngeren Zone, deren Bruch in die Gegenrichtung gescheitert ist (S) – Umkehr nach einer
       gescheiterten Auktion (Dalton: „look below and fail“ / „look above and fail“)
    B  Wochenwert ganz außerhalb (am letzten Tag der Woche)
    R  Rücktest der verlassenen Zone, der hält – ↑: Tief ≤ altes VAH, Schluss > altes VAH, Tages-VAL ≥ alter POC
       (↓ gespiegelt: Hoch ≥ altes VAL, Schluss < altes VAL, Tages-VAH ≤ alter POC)
    S  gescheitert: Schluss zurück im Wertbereich der verlassenen Zone (↑: unter ihrem VAH, ↓: über ihrem VAL)
Zustand am letzten Tag: Balance · an der Schwelle · Ausbruch (Tag n) · bestätigt – jeweils mit Richtung.
"""
import numpy as np
import pandas as pd

STUFE = 0.002            # Preiszeile 0,2 %
WERT = 0.70              # Wertbereich 70 %
LOG_STUFE = np.log1p(STUFE)
ZONE_REIF = 3            # A erst ab einer Zone von 3 Wochen; jüngere Zonen: F (Fortsetzung) – Flaggenregel
SCHWELLE_TAGE = 5        # an der Schwelle: Tageswerte der letzten 5 Tage
SCHWELLE_MIN = 3         # … davon mindestens 3 in eine Richtung (▲/△ bzw. ▼/▽) und keiner ganz dagegen
ZEICHEN = {"hoch": "▲", "ueber": "△", "gleich": "▬", "unter": "▽", "tief": "▼"}


def _zeile(preis):
    return int(np.floor(np.log(preis) / LOG_STUFE))


def _preis(zeile):
    return float(np.exp((zeile + 0.5) * LOG_STUFE))


def _marken(d):
    m = {}
    for lo, hi in zip(d["Low"].to_numpy(float), d["High"].to_numpy(float)):
        for z in range(_zeile(lo), _zeile(hi) + 1):
            m[z] = m.get(z, 0) + 1
    return m


def wertbereich(marken):
    """(VAL, VAH, POC) als Preise aus einem Markenverzeichnis, Verfahren nach Steidlmayer."""
    if not marken:
        return None
    zeilen = sorted(marken)
    lo, hi = zeilen[0], zeilen[-1]
    mitte = (lo + hi) / 2
    poc = max(zeilen, key=lambda z: (marken[z], -abs(z - mitte)))
    gesamt = sum(marken.values())
    oben = unten = poc
    summe = marken[poc]
    while summe < WERT * gesamt and (oben < hi or unten > lo):
        a = sum(marken.get(z, 0) for z in (oben + 1, oben + 2)) if oben < hi else -1
        b = sum(marken.get(z, 0) for z in (unten - 1, unten - 2)) if unten > lo else -1
        if a >= b:
            summe += max(a, 0)
            oben = min(hi, oben + 2)
        else:
            summe += max(b, 0)
            unten = max(lo, unten - 2)
    return _preis(unten) * (1 - STUFE / 2), _preis(oben) * (1 + STUFE / 2), _preis(poc)


def _profil(d, tag):
    m = _marken(d)
    val, vah, poc = wertbereich(m)
    return {"tag": tag, "ende": d.index[-1].normalize(), "hoch": float(d["High"].max()), "tief": float(d["Low"].min()),
            "auf": float(d["Open"].iloc[0]), "schluss": float(d["Close"].iloc[-1]),
            "val": val, "vah": vah, "poc": poc, "marken": m, "abschnitte": len(d)}


def tagesprofile(df30):
    return [_profil(d, pd.Timestamp(t)) for t, d in df30.groupby(df30.index.normalize())]


def wochenprofile(df30, bis=None):
    """Wochen-Composite (alle 30-Minuten-TPO der Woche, Woche endet freitags). Nur abgeschlossene Wochen: die letzte
    zählt, wenn ihr Freitag erreicht ist oder `bis` (letzter Tag der Reihe) danach liegt."""
    bis = pd.Timestamp(bis if bis is not None else df30.index[-1]).normalize()
    aus = []
    for woche, d in df30.groupby(df30.index.to_period("W-FRI")):
        if woche.end_time.normalize() > bis:
            continue
        aus.append(_profil(d, d.index[0].normalize()))
    return aus


def beziehung(p, v):
    """Tageswert p zum Vortag v (Dalton)."""
    if p["val"] > v["vah"]:
        return "hoch"
    if p["vah"] < v["val"]:
        return "tief"
    if p["vah"] > v["vah"] and p["val"] > v["val"]:
        return "ueber"
    if p["vah"] < v["vah"] and p["val"] < v["val"]:
        return "unter"
    return "gleich"


def _zonen_verlauf(wochen):
    """Zonen aus abgeschlossenen Wochen. Gibt (zonen, stand) zurück: stand[k] = Zone nach Woche k (so, wie sie an dem
    Tag bekannt war: Wertbereich, Rahmen, Alter in Wochen, Herkunft = Richtung des Ausbruchs, mit dem sie begann)."""
    zonen, stand, cur = [], [], None
    for k, w in enumerate(wochen):
        if cur is not None and (w["val"] > cur["vah"] or w["vah"] < cur["val"]):
            richtung = "↑" if w["val"] > cur["vah"] else "↓"
            cur["bis"], cur["ausbruch"], cur["richtung"] = k - 1, k, richtung
            zonen.append(cur)
            cur = None
        else:
            richtung = None
        if cur is None:
            cur = {"von": k, "bis": k, "marken": dict(w["marken"]), "hoch": w["hoch"], "tief": w["tief"],
                   "val": w["val"], "vah": w["vah"], "poc": w["poc"], "herkunft": richtung,
                   "ausbruch": None, "richtung": None, "nr": len(zonen)}
        else:
            cur["bis"] = k
            for z, n in w["marken"].items():
                cur["marken"][z] = cur["marken"].get(z, 0) + n
            cur["val"], cur["vah"], cur["poc"] = wertbereich(cur["marken"])
            cur["hoch"], cur["tief"] = max(cur["hoch"], w["hoch"]), min(cur["tief"], w["tief"])
        stand.append({s: cur[s] for s in ("von", "hoch", "tief", "val", "vah", "poc", "herkunft", "nr")}
                     | {"wochen": k - cur["von"] + 1, "neu": richtung})
    if cur is not None:
        zonen.append(cur)
    for z in zonen:
        z.pop("marken", None)
        z["wochen"] = z["bis"] - z["von"] + 1
        z["beginn"], z["ende"] = wochen[z["von"]]["tag"], wochen[z["bis"]]["ende"]
    return zonen, stand


def analyse(df30, tages=None):
    """Alles, was App und Chart brauchen. tages: Tagesreihe der App (Index Datum) – Signale werden auf ihre Tage gelegt."""
    if df30 is None or len(df30) < 13 * 15:
        return None
    tage = tagesprofile(df30)
    wochen = wochenprofile(df30)
    if len(wochen) < 2:
        return None
    zonen, stand = _zonen_verlauf(wochen)
    woche_von = {}
    for k, w in enumerate(wochen):
        for t in pd.date_range(w["tag"], w["ende"]):
            woche_von[t] = k
    ende_woche = {w["ende"]: k for k, w in enumerate(wochen)}
    perioden = {p["tag"]: p["tag"].to_period("W-FRI") for p in tage}
    erste_woche = {}
    for k, w in enumerate(wochen):
        erste_woche[w["tag"].to_period("W-FRI")] = k
    for i, p in enumerate(tage):
        p["bez"] = beziehung(p, tage[i - 1]) if i else None

    signale, aktiv, gescheitert = [], None, None
    gemeldet = set()
    for i, p in enumerate(tage):
        per = perioden[p["tag"]]
        k = erste_woche.get(per)                         # Index dieser Woche (falls abgeschlossen)
        vorher = (k - 1) if k is not None else len(wochen) - 1   # laufende Woche: letzte abgeschlossene davor
        if vorher < 0:
            continue
        ref = stand[vorher]
        c = p["schluss"]
        # Ablauf: eine aktive Bewegung endet, wenn die neue Zone selbst reif ist (neue Balance auf neuer Höhe)
        if aktiv and ref["nr"] != aktiv["zone"]["nr"] and ref["wochen"] >= ZONE_REIF and aktiv.get("bestaetigt"):
            aktiv = None
        # S – gescheitert
        if aktiv and i > aktiv["seit"]:
            z = aktiv["zone"]
            if (aktiv["dir"] == "↑" and c < z["vah"]) or (aktiv["dir"] == "↓" and c > z["val"]):
                signale.append({"i": i, "tag": p["tag"], "art": "S", "dir": aktiv["dir"], "preis": c,
                                "zone": aktiv["zone"]["nr"]})
                gescheitert = {"i": i, "dir": aktiv["dir"], "tag": p["tag"]}
                aktiv = None
        # A / F
        for d, jenseits in (("↑", c > ref["hoch"] and p["val"] > ref["vah"]),
                            ("↓", c < ref["tief"] and p["vah"] < ref["val"])):
            if not jenseits or (ref["nr"], d) in gemeldet or (aktiv and aktiv["dir"] == d):
                continue
            umkehr = bool(gescheitert and gescheitert["dir"] != d and ref["herkunft"] == gescheitert["dir"]
                          and gescheitert["tag"] >= wochen[ref["von"]]["tag"])
            art = "A" if ref["wochen"] >= ZONE_REIF else ("F" if ref["herkunft"] == d else "U" if umkehr else None)
            if art:
                gemeldet.add((ref["nr"], d))
                signale.append({"i": i, "tag": p["tag"], "art": art, "dir": d, "preis": c, "zone": ref["nr"]})
                aktiv = {"dir": d, "zone": ref, "seit": i, "art": art}
        # R – Rücktest, der hält
        if aktiv and i > aktiv["seit"]:
            z = aktiv["zone"]
            halt = ((aktiv["dir"] == "↑" and p["tief"] <= z["vah"] < c and p["val"] >= z["poc"]) or
                    (aktiv["dir"] == "↓" and p["hoch"] >= z["val"] > c and p["vah"] <= z["poc"]))
            if halt and not aktiv.get("rueck"):
                aktiv["rueck"] = True                # je Lauf der erste Rücktest, der hält
                signale.append({"i": i, "tag": p["tag"], "art": "R", "dir": aktiv["dir"], "preis": c,
                                "zone": aktiv["zone"]["nr"]})
        # B – am letzten Tag einer Woche, deren Wert die Zone verlassen hat
        kw = ende_woche.get(p["tag"])
        if kw is not None and stand[kw]["neu"]:
            d = stand[kw]["neu"]
            alt = stand[kw - 1]
            signale.append({"i": i, "tag": p["tag"], "art": "B", "dir": d, "preis": c, "zone": alt["nr"]})
            if not aktiv or aktiv["dir"] != d:
                aktiv = {"dir": d, "zone": alt, "seit": i, "art": "B"}
            aktiv["zone"] = alt                     # jede neue Stufe: Stop an der zuletzt verlassenen Zone (Treppe)
            aktiv["bestaetigt"] = True
            gemeldet.add((alt["nr"], d))

    zustand = _zustand(tage, stand, aktiv, gescheitert, signale)
    return {"tage": tage, "wochen": wochen, "zonen": zonen, "stand": stand, "signale": signale,
            "aktiv": aktiv, "zustand": zustand}


def _zahl(x, s=2):
    return f"{x:,.{s}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _zustand(tage, stand, aktiv, gescheitert, signale):
    n = len(tage) - 1
    p = tage[-1]
    ref = stand[-1]
    folge = [tage[j]["bez"] for j in range(max(1, n - SCHWELLE_TAGE + 1), n + 1)]
    zeichen = " ".join(ZEICHEN[b] for b in folge if b)
    poc_vor = tage[max(0, n - SCHWELLE_TAGE)]["poc"]
    belege = [f"Tageswert {zeichen}", f"POC {_zahl(poc_vor)} → {_zahl(p['poc'])} $"]
    if aktiv:
        d = aktiv["dir"]
        z = aktiv["zone"]
        kante = z["vah"] if d == "↑" else z["val"]
        belege.append(f"verlassene Zone: {'VAH' if d == '↑' else 'VAL'} {_zahl(kante)} $ (Stop bei Schluss "
                      f"{'darunter' if d == '↑' else 'darüber'})")
        if aktiv.get("bestaetigt"):
            return {"wort": f"bestätigt {d}", "dir": d, "ampel": "grün", "belege": belege}
        tag = n - aktiv["seit"] + 1
        name = "Umkehr" if aktiv.get("art") == "U" else "Ausbruch"
        return {"wort": f"{name} {d} (Tag {tag})", "dir": d, "ampel": "grün", "belege": belege}
    lage = (p["schluss"] - ref["val"]) / max(ref["vah"] - ref["val"], 1e-9)
    lage_text = ("über dem Wertbereich" if lage > 1 else "im oberen Drittel des Wertbereichs" if lage >= 2 / 3 else
                 "in der Mitte des Wertbereichs" if lage > 1 / 3 else "im unteren Drittel des Wertbereichs" if lage >= 0
                 else "unter dem Wertbereich")
    belege.append(f"Kurs {lage_text} der Zone ({_zahl(ref['val'])}–{_zahl(ref['vah'])} $)")
    hoch = sum(b in ("hoch", "ueber") for b in folge)
    tief = sum(b in ("tief", "unter") for b in folge)
    if hoch >= SCHWELLE_MIN and "tief" not in folge and p["poc"] > poc_vor and lage >= 2 / 3:
        return {"wort": "an der Schwelle ↑", "dir": "↑", "ampel": "gelb", "belege": belege}
    if tief >= SCHWELLE_MIN and "hoch" not in folge and p["poc"] < poc_vor and lage <= 1 / 3:
        return {"wort": "an der Schwelle ↓", "dir": "↓", "ampel": "gelb", "belege": belege}
    if gescheitert and n - gescheitert["i"] < 10:
        belege.insert(0, f"Ausbruch {gescheitert['dir']} am {gescheitert['tag']:%d.%m.} gescheitert")
    return {"wort": "Balance", "dir": None, "ampel": "grau", "belege": belege}
