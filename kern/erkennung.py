"""Mustererkennung des Invest Cockpit (Regeln: Minervini, Kap. 5–11; Regelkatalog).

erkenne(df, woche=False, index=None) -> dict
    muster     Liste der erkannten Muster (höchstens ein Hauptmuster plus "Primärbasis")
    kaufsetup  True, wenn ein Muster vorliegt UND die Trendvorlage erfüllt ist
    hinweise   Zeichen zum Muster (Tiefenampel, Kaufzone, Volumen …) – nie ein Filter
    werte      die gemessenen Zahlen (Dauer, Tiefe, Vorlauf, Kontraktionen, Pivot)

df: Tageskurse mit Open, High, Low, Close, Volume; letzte Zeile = letzter abgeschlossener Tag.
    df.attrs["jung"] = True/False sagt, ob die Reihe am Börsengang beginnt. Fehlt die Angabe,
    gilt eine Reihe unter 300 Tagen als jung (die App lädt immer die volle Historie).
index: Tageskurse des Vergleichsindex (S&P 500) für „Korrektur zum Markt“; ohne Index entfällt das Zeichen.
Alle Grenzen in Prozent, damit Splits und Dividenden keine Rolle spielen.
"""
import numpy as np

import datenpruefung
import massive
from phase import phasen

# Grenzen aus dem Regelkatalog (Wochen × 5 Handelstage)
BASE_MIN, BASE_MAX = 15, 325          # 3–65 Wochen
STANGE_FENSTER = 40                   # Fahnenstange in höchstens 8 Wochen
HOCH_TOLERANZ = 0.025                 # Hochs bis 2,5 % unter dem Höchsten zählen zum linken Rand


def gd(werte, n):
    return float(np.mean(werte[-n:])) if len(werte) >= n else float("nan")


def trendvorlage(c, h, l):
    """Sieben Kriterien der Trendvorlage ohne RS-Rating (das kommt aus dem Revier)."""
    if len(c) < 260:
        return False
    g50, g150, g200 = gd(c, 50), gd(c, 150), gd(c, 200)
    g200_vor = float(np.mean(c[-222:-22]))
    k = c[-1]
    return bool(k > g150 and k > g200 and g150 > g200 and g200 > g200_vor
                and g50 > g150 and k > g50
                and k >= 1.30 * l[-252:].min() and k >= 0.75 * h[-252:].max())


def kontraktionen_lage(h, l, mindest=2.0):
    """Kontraktionen mit Lage: Liste (index_hoch, index_tief, tiefe_pct), siehe kontraktionen()."""
    aus, i, n = [], 0, len(h)
    while i < n - 2:
        hi = i + int(np.argmax(h[i:]))
        if hi >= n - 1:
            break
        lo = hi + int(np.argmin(l[hi:]))
        t = (1 - l[lo] / h[hi]) * 100
        if t < mindest:
            break
        aus.append((hi, lo, round(float(t), 1)))
        i = lo + 1
    return aus


def kontraktionen(h, l, mindest=2.0):
    """Kontraktionen der Base nach Minervini, in Prozent: die erste vom Hoch der Base bis zu
    ihrem Tief; jede weitere vom höchsten Hoch nach dem vorigen Tief bis zum Tief danach.
    Endet, wenn ein Rücksetzer unter `mindest` Prozent bleibt."""
    return [t for _, _, t in kontraktionen_lage(h, l, mindest)]


# ── O'Neil-Formen (Regelkatalog O'Neil 8.2, 8.4, 8.7, 8.8) ──


# ── Klimax und Überdehnung (O'Neil, Verkaufsregeln; Regelkatalog O'Neil „Technische Verkaufssignale“) ──
KLIMAX_GD200 = 0.70        # Kurs mindestens 70 % über dem GD200
KLIMAX_LAUF_TAGE = 90      # Klimax erst nach langem Anstieg: mindestens 18 Wochen seit dem Tief der letzten Base
KLIMAX_SPURT = 0.25        # … und zuletzt mindestens 25 % in höchstens 15 Handelstagen
KLIMAX_FENSTER = 15        # die Zeichen zählen, wenn sie in den letzten 3 Wochen auftreten


KLIMAX_GD200_MIT = 0.50    # die übrigen Zeichen zählen nur, wenn der Kurs schon mindestens 50 % über dem GD200 steht –
                           # sonst wäre jeder kräftige Ausbruch aus einer Base (größte Wochenspanne!) ein „Klimax“


def klimax(h, l, c, v):
    """Zeichen eines Gipfels nach O'Neil. Liefert die Gründe (leer = kein Verdacht).
    Allein reicht: Kurs mindestens 70 % über dem GD200. Die übrigen Zeichen (Spurt nach langem Anstieg, größte
    Wochenspanne, Eisenbahnschienen, Erschöpfungslücke) zählen erst ab 50 % über dem GD200."""
    n = len(c)
    gruende = []
    if n < 200:
        return gruende
    gd200 = float(np.mean(c[-200:]))
    ueber = c[-1] / gd200 - 1
    if ueber >= KLIMAX_GD200:
        gruende.append(f"{ueber * 100:.0f} % über dem GD200")
    if ueber < KLIMAX_GD200_MIT:
        return gruende
    # Anstieg seit dem Tief der letzten Base (tiefstes Tief des letzten Jahres vor dem jüngsten Hoch)
    hi = n - 1 - int(np.argmax(h[::-1][:KLIMAX_FENSTER + 1]))
    a = max(0, hi - 250)
    tief = a + int(np.argmin(l[a:hi + 1]))
    lauf = hi - tief
    if lauf >= KLIMAX_LAUF_TAGE:
        spurt = h[hi] / l[max(tief, hi - KLIMAX_FENSTER):hi + 1].min() - 1
        if spurt >= KLIMAX_SPURT:
            gruende.append(f"Spurt +{spurt * 100:.0f} % in 3 Wochen nach {lauf // 5} Wochen Anstieg")
        # größte Wochenspanne seit Beginn des Anstiegs in den letzten 3 Wochen
        k = (n - tief) // 5
        if k >= 8:
            wh = h[n - 5 * k:].reshape(k, 5).max(1); wl = l[n - 5 * k:].reshape(k, 5).min(1)
            sp = wh - wl
            if int(np.argmax(sp)) >= k - 3 and sp.max() > 1.5 * np.median(sp):
                gruende.append("größte Wochenspanne seit Beginn des Anstiegs")
            # Eisenbahnschienen: zwei breite Wochen nebeneinander mit fast gleichem Schluss
            wc = c[n - 5 * k:].reshape(k, 5)[:, -1]
            for j in (k - 2, k - 3):
                if j >= 1 and min(sp[j], sp[j + 1]) > 1.5 * np.median(sp) and abs(wc[j + 1] / wc[j] - 1) < 0.01:
                    gruende.append("Eisenbahnschienen (zwei breite Wochen, gleicher Schluss)")
                    break
        # Erschöpfungslücke: Kurslücke nach oben ab 3 % in den letzten 3 Wochen
        for i in range(max(1, n - KLIMAX_FENSTER), n):
            if l[i] > h[i - 1] * 1.03:
                gruende.append("Erschöpfungslücke")
                break
    return gruende


def vorige_base(h, l, bis):
    """Letzte abgeschlossene Base vor `bis`: Hoch, dem mindestens 4 Wochen (vom linken Rand) und 5 % Rücksetzer
    folgten und das danach überboten wurde. Liefert (hoch_index, hoch) oder None."""
    hoch_i, letzte = 0, None
    tief = l[0]
    for i in range(1, bis + 1):
        if h[i] > h[hoch_i]:
            if _base_zaehlt(h, hoch_i, i, tief, streng=True):
                letzte = (hoch_i, float(h[hoch_i]))
            hoch_i, tief = i, l[i]
        else:
            tief = min(tief, l[i])
    return letzte


BASE_MIN_TAGE = 20          # eine Base zählt ab 4 Wochen vom linken Rand bis zum neuen Hoch …
BASE_MIN_RUECK = 0.05       # … und mindestens 5 % Rücksetzer – dieselben Grenzen wie die flache Base der Erkennung
                            # (3.11.2026: vorher 10 % und 4 Wochen ab dem Hoch; dadurch fehlten flache Basen, die
                            # die Erkennung live meldete, in Zählung und früheren Basen – Fall HWM Jan./Feb. 2026)


BASE_MIN_SEIT_HOCH = 15     # … und mindestens 3 Wochen ab dem Hoch selbst (sonst zählt jedes Zögern am Hoch)


def _base_zaehlt(h, hoch_i, i, tief, streng=False):
    """Pause vom Hoch hoch_i bis zum neuen Hoch am Tag i zählt als Base: Rücksetzer mindestens BASE_MIN_RUECK und
    mindestens BASE_MIN_TAGE vom linken Rand (erste Hochs bis 2,5 % unter dem Hoch, wie in der Erkennung).
    streng=True: alte Abgrenzung (4 Wochen ab dem Hoch, 10 % Rücksetzer) – für „Base auf Base“: die vorige Base ist
    dort die letzte richtige Base, nicht eine flache Pause dazwischen (Galeriefälle S133, S142, S143)."""
    if streng:
        return i - hoch_i >= BASE_MIN_TAGE and tief <= h[hoch_i] * 0.90
    if tief > h[hoch_i] * (1 - BASE_MIN_RUECK) or i - hoch_i < BASE_MIN_SEIT_HOCH:
        return False
    j = hoch_i
    while j > 0 and hoch_i - j < BASE_MIN_TAGE and h[j - 1] >= h[hoch_i] * (1 - HOCH_TOLERANZ):
        j -= 1
    return i - j >= BASE_MIN_TAGE
MARKT_KORREKTUR = 0.15      # Markt fällt mindestens 15 %: danach beginnt die Zählung neu


def letztes_markttief(index, bis):
    """Datum des Tiefs der letzten abgeschlossenen oder laufenden Marktkorrektur ab 15 %."""
    if index is None:
        return None
    teil = index[index.index < bis]["Close"]
    if teil.empty:
        return None
    werte, tage = teil.to_numpy(float), teil.index
    letzte, spitze, tief, tief_i, in_korr = None, werte[0], werte[0], 0, False
    for i, x in enumerate(werte):
        if x > spitze:
            if in_korr:
                letzte, in_korr = tage[tief_i], False
            spitze, tief, tief_i = x, x, i
        elif x < tief:
            tief, tief_i = x, i
            if x <= spitze * (1 - MARKT_KORREKTUR):
                in_korr = True
    return tage[tief_i] if in_korr else letzte


def uebernahme_verdacht(h, l):
    """Kurs klebt: 8 Tage Gesamtspanne ≤ 3 % und Tagesspanne im Mittel ≤ 0,8 %, nachdem sie in den 60 Tagen davor
    mindestens dreimal so groß war (Mittel des Jahres davor). So handelt eine Aktie nach einem Übernahmeangebot (Kurs am Angebotspreis) –
    das ist keine Base, sondern ein fester Preis. Liefert den Hinweistext oder None."""
    if len(h) < 70:
        return None
    spanne = h[-8:].max() / l[-8:].min() - 1
    tag = np.mean(h[-8:] / l[-8:] - 1)
    vorher = np.mean(h[-250:-8] / l[-250:-8] - 1)
    if spanne <= 0.03 and tag <= 0.008 and vorher >= 3 * tag:
        return (f"Übernahme-Verdacht: Kurs klebt seit 8 Tagen in {spanne * 100:.1f} % Spanne "
                f"(Tagesspanne {tag * 100:.2f} % statt {vorher * 100:.1f} %) – kein Muster bewertet").replace(".", ",")
    return None


def korrektur_markt(df, index, start):
    """Tiefe der Base geteilt durch den Rückgang des Index im selben Zeitraum (None bei < 5 %)."""
    if index is None:
        return None
    ab = df.index[start]
    teil = index[(index.index >= ab) & (index.index <= df.index[-1])]
    if len(teil) < 5:
        return None
    hi, lo = teil["High"].to_numpy(float), teil["Low"].to_numpy(float)
    rueckgang = float(np.max(1 - lo / np.maximum.accumulate(hi)) * 100)
    return rueckgang


_PHASEN = {}


def _phase_von(df):
    """Phase je Tag (Weinstein, wöchentlich gerechnet, auf Tage übertragen); None bei zu kurzer Reihe."""
    n = len(df)
    if n < 300 or df.attrs.get("jung", n < 300):
        return None
    schluessel = (n, df.index[-1], float(df["Close"].iloc[-1]), float(df["Close"].iloc[0]), df.attrs.get("ticker"))
    if schluessel not in _PHASEN:
        if len(_PHASEN) > 2000:
            _PHASEN.clear()
        _PHASEN[schluessel] = phasen(df).reindex(df.index, method="ffill").fillna(1).to_numpy()
    return _PHASEN[schluessel]


# ── Wertzonen (4.11.2026): exakte Wertzonen aus 30-Minuten-TPO (kern/marketprofile.py), beide Richtungen ──
_MP, _ROH = {}, {}
SHORT_PHASEN = (3, 4)        # Weinstein: geshortet wird beim Bruch aus Phase 3 und in Phase 4; sonst Seite long


def mp_von(df):
    """Market-Profile-Analyse der Reihe (gekappt am letzten Tag von df, kein Blick in die Zukunft); None ohne Kerzen."""
    tk = df.attrs.get("ticker") or df.attrs.get("tk_mp")
    if not tk or not len(df):
        return None
    schluessel = (tk, len(df), df.index[-1], float(df["Close"].iloc[-1]))
    if schluessel not in _MP:
        import marketprofile
        import tpo_daten
        if len(_MP) > 500:
            _MP.clear()
        if tk not in _ROH:
            if len(_ROH) > 50:                   # Massenlauf (Kartentisch, Kreislauf): Speicher begrenzen
                _ROH.clear()
            _ROH[tk] = tpo_daten.lesen(tk)
        roh = _ROH[tk]
        a = None
        if roh is not None:
            teil = roh[roh.index.normalize() <= df.index[-1]]
            if len(teil):
                a = marketprofile.analyse(tpo_daten.ausrichten(teil, df), df)
        if a is not None and df.attrs.get("laufend") and roh.index[-1].normalize() == df.index[-1]:
            # mit der unvollständigen Kerze von heute: alles am rechten Rand ist vorläufig bis Börsenschluss
            a["vorlaeufig"] = df.attrs.get("stand", "")
            w = a["zustand"]["wort"]
            a["zustand"]["wort"] = (w[:-1] + ", vorläufig)") if w.endswith(")") else w + " (vorläufig)"
        _MP[schluessel] = a
    return _MP[schluessel]


def mp_vergessen(tk):
    """Nach neuen 30-Minuten-Kerzen (Titelseite) die gespeicherte Reihe neu lesen."""
    _ROH.pop(tk, None)


def mp_heute(tk, kerzen):
    """Laufender Börsentag (Knopf „Kurse aktualisieren“): die 30-Minuten-Kerzen von heute an die gespeicherte Reihe
    hängen. Das Ergebnis gilt als vorläufig bis Börsenschluss."""
    import tpo_daten
    roh = tpo_daten.lesen(tk)
    if kerzen is None or roh is None:
        return
    import pandas as pd
    _ROH[tk] = pd.concat([roh[roh.index.normalize() < kerzen.index[0].normalize()], kerzen])


def _tag_index(df, tag):
    return min(int(df.index.searchsorted(tag)), len(df) - 1)


def _erkenne_mp(df, woche=False, index=None):
    h, l, c, v = (df[s].to_numpy(float) for s in ("High", "Low", "Close", "Volume"))
    n = len(c)
    leer = {"muster": [], "kaufsetup": False, "hinweise": [], "werte": {}}
    a = mp_von(df)
    if a is None:
        return {**leer, "mp": None, "hinweise": ["keine 30-Minuten-Kerzen – Wertzonen fehlen"]}
    uebernahme = uebernahme_verdacht(h, l)
    if uebernahme:
        return {**leer, "mp": a, "hinweise": [uebernahme]}
    ph = _phase_von(df)
    phase = int(ph[-1]) if ph is not None else None
    ak = a.get("aktiv")
    # Seite: eine laufende Bewegung (A, F, U, B – nicht gescheitert) bestimmt sie; sonst die Phase nach Weinstein.
    # Phase, Trendvorlage und Markt bleiben Regeln mit Ampel – ein Signal gegen die Phase wird gezeigt, nicht verschluckt
    seite = ("long" if ak["dir"] == "↑" else "short") if ak else ("short" if phase in SHORT_PHASEN else "long")
    d = "↑" if seite == "long" else "↓"
    st = a["stand"][-1]                          # Wertzone der abgeschlossenen Wochen, wie sie heute gilt
    start = _tag_index(df, a["wochen"][st["von"]]["tag"])
    art = "Base" if st["wochen"] >= 3 else ("Flagge" if st["herkunft"] == d else None)
    if art is None and ak and ak.get("art") == "U" and ak["dir"] == d and ak["zone"]["nr"] == st["nr"]:
        art = "Umkehr"                           # junge Wertzone nach gescheitertem Bruch, verlassen in Gegenrichtung
    t_zone = a["wochen"][st["von"]]["tag"]
    if art == "Flagge" and any(x["art"] == "S" and x["dir"] == d and x["tag"] >= t_zone for x in a["signale"]):
        art = None                               # der Lauf, aus dem die junge Wertzone entstand, ist gescheitert
    basis = {**leer, "mp": a, "seite": seite, "zonen": a["zonen"]}
    if art is None:
        basis["hinweise"].append(f"Wertzone erst {st['wochen']} Woche{'n' if st['wochen'] > 1 else ''} alt"
                                 + (f", entstanden aus einem Ausbruch {st['herkunft']}" if st["herkunft"] else "")
                                 + f" – keine reife Wertzone für {seite}")
        return basis
    dauer = n - start
    hoch, tief = float(st["hoch"]), float(st["tief"])
    tiefe = (1 - tief / hoch) * 100
    bh, bl = h[start:], l[start:]
    tief_idx = int(np.argmin(bl))
    vor = max(0, start - STANGE_FENSTER)
    werte = {"start_index": start, "ende_index": n - 1, "dauer_tage": int(dauer), "wochen": int(st["wochen"]),
             "tiefe_pct": round(tiefe, 1), "zone_oberkante": hoch, "zone_unterkante": tief, "zone_kippen": None,
             "val": st["val"], "vah": st["vah"], "poc": st["poc"],
             "vorlauf_pct": round((hoch / l[vor:start + 1].min() - 1) * 100, 1) if start > 0 else 0.0,
             "stange_pct": round((h[vor:start + 1].max() / l[vor:start + 1].min() - 1) * 100, 1) if start > 0 else 0.0,
             "kontraktionen": kontraktionen(bh, bl),
             "kontraktionen_lage": [(start + x, start + y, t) for x, y, t in kontraktionen_lage(bh, bl)]}
    if seite == "short":
        # Short nur als Ermüdung nach Überdehnung (vcp_zone.ermuedung, 06.11.2026); die Wertzone nach unten bleibt als Lagebild
        werte["pivot"] = tief                    # Unterkante des Rahmens
        basis["werte"] = werte
        if art == "Umkehr":
            basis["hinweise"].append("Umkehr ↓ nach gescheitertem Bruch nach oben (Dalton)")
        basis["muster"] = []
        return basis
    werte["pivot"] = hoch                        # Pivot long: Oberkante des Rahmens (A: Schluss darüber)
    r = _abschluss(df, woche, index, h, l, c, v, n, art, [], werte, start, dauer, tiefe, tief_idx, hoch, bl)
    r.update({"mp": a, "seite": seite, "zonen": a["zonen"]})
    if art == "Umkehr":
        r["hinweise"].append("Umkehr ↑ nach gescheitertem Bruch nach unten (Dalton) – gegen die Phase, Regeln der "
                             "Meister prüfen")
    a65 = max(0, n - BASE_MAX)
    i65 = a65 + int(np.argmax(h[a65:]))
    oben = (1 - l[i65:].min() / h[i65]) * 100
    if oben > 50 and i65 < start:
        r["kaufsetup"] = False
        r["hinweise"].append(f"Angebot von oben: seit dem Hoch der letzten 65 Wochen ({h[i65]:.2f}) bis {oben:.0f} % gefallen")
    if tiefe > 35 and art == "Base":
        r["hinweise"].append("tief (über 35 %: nur nach einem Bärenmarkt, O'Neil)")
    return r


def erkenne(df, woche=False, index=None, _vor_hoch=False):
    """Erkennung über die Balance-Zone: die Wertzone, die heute gilt (laufend oder höchstens 4 Wochen nach ihrem Kippen),
    eingeordnet nach den Regeln der Meister als Base oder Flagge (Powerplay). Pivot = Hoch der letzten Enge (innere
    Wertzone, Minervini); Flagge: Hoch der Flagge. Formnamen gibt es nicht mehr."""
    return _erkenne_mp(df, woche, index)

def _abschluss(df, woche, index, h, l, c, v, n, muster, oneil, werte, start, dauer, tiefe, tief_idx, hoch, bl):
    """Gemeinsamer Abschluss: Base auf Base, Primärbasis, Zeichen, Basenzahl, Phase, Klimax, Kaufsetup, Datenampel."""
    vor = vorige_base(h, l, start) if start > BASE_MIN_TAGE else None
    if vor is not None and dauer >= 15 and bl.min() >= vor[1] * 0.95 and hoch <= vor[1] * 1.35:
        oneil.append("Base auf Base")              # zweite Base direkt über der ersten, Rücksetzer stoppt am alten Pivot
        werte["vorige_base_pivot"] = vor[1]

    gefunden = [muster] if muster else []
    gefunden += [o for o in oneil if o not in gefunden]
    gefunden = list(dict.fromkeys(gefunden))      # jede Form nur einmal nennen
    jung = df.attrs.get("jung", n < 300) and n < 300
    if muster and jung and dauer >= BASE_MIN and tiefe <= 35:
        gefunden.append("Primärbasis")            # junger Börsengang, erste Base

    # ── Zeichen zum Muster (deuten, filtern nie) ──
    hinweise = []                               # (Reste der alten Formerkennung – Tasse, Doppelboden – am 14.11.2026 entfernt)
    markt = korrektur_markt(df, index, werte["start_index"])
    zu_tief_zum_markt = False
    if markt is not None:
        # Fällt der Markt kaum, wird mit 5 % gerechnet: eine Base von 40 % bei ruhigem Markt ist
        # abnorme Schwäche (Buch: Korrektur höchstens das 2- bis 3-Fache des Marktes).
        faktor = tiefe / max(markt, 5.0)
        werte.update({"index_rueckgang_pct": round(markt, 1), "korrektur_x_markt": round(faktor, 1)})
        ampel = "grün" if faktor <= 2 else "gelb" if faktor <= 3 else "rot"
        if muster:
            hinweise.append(f"Korrektur {faktor:.1f}-fach so tief wie der Markt".replace(".", ",") + f" ({ampel})")
        zu_tief_zum_markt = faktor > 3
    if muster == "Base":
        hinweise.append("Tiefe " + ("grün" if tiefe <= 35 else "gelb" if tiefe <= 50 else "rot"))
    if dauer - tief_idx <= 5 and tiefe >= 15 and c[-1] >= hoch * 0.85:
        # V-Erholung: vom Tief in wenigen Tagen zurück nach oben (steht der Kurs noch am Tief, ist es keine Erholung)
        hinweise.append("keine Zeit zum Verdauen (V-Erholung)")
    vol50 = gd(v, 50)
    if n >= 50 and v[-5:].mean() < vol50 and v[-10:].min() <= 0.5 * vol50:
        hinweise.append("Volumen trocknet aus")
    abstand = (c[-1] / werte["pivot"] - 1) * 100
    if 0 <= abstand <= 5:
        hinweise.append("in der Kaufzone")
    elif abstand > 5:
        hinweise.append("ausgedehnt")

    # Junger Börsengang: statt Trendvorlage reicht Kurs über dem GD50 (bzw. über dem Schnitt seit Börsengang)
    trend = trendvorlage(c, h, l) or (jung and "Primärbasis" in gefunden
                                      and c[-1] > gd(c, min(50, n)))
    # Rote Tiefe (über 50 %) und eine Korrektur über dem 3-Fachen des Marktes bleiben sichtbar, ist aber kein Kaufsetup – auch nicht für eine
    # kurze Flagge, die sich darin bildet (Minervini: Base zu tief, Angebot von oben).
    # Nur in Phase 2 teilhaben (Minervini); junge Börsengänge haben noch keinen GD40W
    phase = None
    if not jung and n >= 300:
        import phase as phase_mod
        phase = phase_mod.aktuell(df)
        werte["phase"] = phase
        if phase != 2:
            hinweise.append(f"Phase {phase}")
    gipfel = klimax(h, l, c, v)
    if gipfel:
        werte["klimax"] = gipfel
        # nur Zeichen, kein Filter: an der Galerie gemessen hätte ein Aufheben des Kaufsetups 23 Kaufpunkte aus
        # O'Neils und Minervinis Büchern gelöscht (Powerplays und 1999er Führer stehen oft 100 % über dem GD200)
        hinweise.append("Klimax-Verdacht (rot): " + "; ".join(gipfel))
    kaufsetup = bool(muster and trend and tiefe <= 50
                     and not zu_tief_zum_markt and phase in (None, 2))
    # Datenampel: eine Störung wird gezeigt; ein Kaufsetup gilt nicht bei roter Störung
    # oder wenn eine Störung in die Base fällt (dann ist das Muster womöglich ein Datenfehler)
    gegen = massive.schlusskurse(df.attrs["ticker"]) if df.attrs.get("ticker") else None
    daten = datenpruefung.pruefen(df, index, gegen)
    if daten["zeichen"]:
        beginn = df.index[werte["start_index"]] if "start_index" in werte else df.index[-1]
        in_base = any(tag >= beginn for _, tag, _ in daten["zeichen"])
        if daten["ampel"] == "rot" or in_base:
            kaufsetup = False
            hinweise.append("Daten gestört" + (" in der Base" if in_base else "") + " – Muster nicht verlässlich")
    return {"muster": gefunden, "kaufsetup": kaufsetup, "hinweise": hinweise, "werte": werte, "daten": daten}
