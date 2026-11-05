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
FLAGGE_MIN, FLAGGE_MAX = 5, 30        # 1–6 Wochen
STANGE_FENSTER = 40                   # Fahnenstange in höchstens 8 Wochen
HOCH_TOLERANZ = 0.025                 # Hochs bis 2,5 % unter dem Höchsten zählen zum linken Rand
FLAGGE_KURZ, FLAGGE_STEIL = 20, 50    # Flagge bis 4 Wochen; bis 6 Wochen nur nach Stange ab 50 %


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


def basenzahl(df, index=None):
    """Zählt die Bases seit Beginn der aktuellen Phase 2 bzw. seit dem letzten Markttief nach
    einer Korrektur ab 15 % – was später liegt (Buch: Basis 1 und 2 entstehen meist aus einer
    Marktkorrektur). Eine Base = verlassene Market-Profile-Zone ↑ ab 4 Wochen. Die laufende Base zählt mit."""
    if len(df) < 300:
        return None
    ph = phasen(df)
    vorher = ph[ph.isin([1, 4])]
    beginn_t = vorher.index[-1] if len(vorher) else ph.index[0]
    markt = letztes_markttief(index, df.index[-1])
    if markt is not None and markt > beginn_t:
        beginn_t = markt
    beginn = min(int(np.searchsorted(df.index, beginn_t)), len(df) - 1)
    # gezählt werden verlassene Market-Profile-Zonen ↑ ab 4 Wochen seit dem Beginn, jede neue Stufe erst 20 % über
    # der zuletzt gezählten (IBD/O'Neil); die laufende Zone zählt mit
    a_ = mp_von(df)
    if a_ is None:
        return None
    t_beginn, letzter, zahl = df.index[beginn], None, 0
    for z in a_["zonen"]:
        if z["richtung"] != "↑" or z["wochen"] < ZAEHL_DAUER // 5 or z["beginn"] < t_beginn:
            continue
        if letzter is None or z["hoch"] >= letzter * (1 + ZAEHL_ANSTIEG):
            zahl, letzter = zahl + 1, z["hoch"]
    return zahl + 1


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
                f"(Tagesspanne {tag * 100:.2f} % statt {vorher * 100:.1f} %) – kein Muster bewertet")
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


ZAEHL_DAUER = 20             # gezählt wird eine Base ab 4 Wochen (O'Neil zählt auf dem Wochenchart)
ZAEHL_ANSTIEG = 0.20         # eine neue Base zählt erst, wenn die Oberkante 20 % über dem Pivot der zuletzt gezählten
                            # liegt (IBD/O'Neil: ohne 20 % Anstieg dazwischen ist es Base auf Base, keine neue Stufe)


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


# ── Market-Profile-Zonen (4.11.2026): exakte Zonen aus 30-Minuten-TPO (kern/marketprofile.py), beide Richtungen ──
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
        return {**leer, "mp": None, "hinweise": ["keine 30-Minuten-Kerzen – Market-Profile-Zonen fehlen"]}
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
    st = a["stand"][-1]                          # Zone der abgeschlossenen Wochen, wie sie heute gilt
    start = _tag_index(df, a["wochen"][st["von"]]["tag"])
    art = "Base" if st["wochen"] >= 3 else ("Flagge" if st["herkunft"] == d else None)
    if art is None and ak and ak.get("art") == "U" and ak["dir"] == d and ak["zone"]["nr"] == st["nr"]:
        art = "Umkehr"                           # junge Zone nach gescheitertem Bruch, verlassen in Gegenrichtung
    t_zone = a["wochen"][st["von"]]["tag"]
    if art == "Flagge" and any(x["art"] == "S" and x["dir"] == d and x["tag"] >= t_zone for x in a["signale"]):
        art = None                               # der Lauf, aus dem die junge Zone entstand, ist gescheitert
    basis = {**leer, "mp": a, "seite": seite, "zonen": a["zonen"]}
    if art is None:
        basis["hinweise"].append(f"Zone erst {st['wochen']} Woche{'n' if st['wochen'] > 1 else ''} alt"
                                 + (f", entstanden aus einem Ausbruch {st['herkunft']}" if st["herkunft"] else "")
                                 + f" – keine reife Zone für {seite}")
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
        # Short nur noch als Parabolic Short (System Kullamägi, 05.11.2026); die Zone nach unten bleibt als Lagebild
        werte["pivot"] = tief                    # Unterkante des Rahmens
        basis["werte"] = werte
        if art == "Umkehr":
            basis["hinweise"].append("Umkehr ↓ nach gescheitertem Bruch nach oben (Dalton)")
        basis["muster"] = []
        return basis
    werte["pivot"] = hoch                        # Pivot long: Oberkante des Rahmens (A: Schluss darüber)
    r = _abschluss(df, woche, index, h, l, c, v, n, art, [], werte, start, dauer, tiefe, tief_idx, hoch, bl, None, None)
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


def _historie_mp(df, index, tage):
    """Frühere Zonen (Market Profile), die mindestens 3 Wochen standen und verlassen wurden – in beide Richtungen.
    Ausbruch = erster Auslöser A/F/B in Richtung des Verlassens; Ausgang nach O'Neil, short gespiegelt:
    gelungen = 20 % jenseits des Auslösers, bevor ein Schluss 8 % dagegen liegt."""
    a = mp_von(df)
    if a is None:
        return []
    h, l, c = (df[s].to_numpy(float) for s in ("High", "Low", "Close"))
    n = len(h)
    grenze = df.index[max(0, n - tage)]
    aus = []
    for z in a["zonen"]:
        if z["richtung"] is None or z["wochen"] < 3 or z["ende"] < grenze:
            continue
        d = z["richtung"]
        beginn, ende = _tag_index(df, z["beginn"]), _tag_index(df, z["ende"])
        bwoche = a["wochen"][z["ausbruch"]]
        sig = next((s for s in a["signale"] if s["dir"] == d and s["art"] in ("A", "F", "B") and
                    s.get("zone") == z["nr"]), None)
        aus_i = _tag_index(df, sig["tag"]) if sig else _tag_index(df, bwoche["ende"])
        pivot = float(z["hoch"] if d == "↑" else z["tief"])
        ausgang, ergebnis = "offen", None
        for j in range(aus_i, n):
            if (d == "↑" and h[j] >= pivot * (1 + HIST_GEWINN)) or (d == "↓" and l[j] <= pivot * (1 - HIST_GEWINN)):
                ausgang, ergebnis = "gelungen", j
                break
            if (d == "↑" and c[j] < pivot * (1 - HIST_VERLUST)) or (d == "↓" and c[j] > pivot * (1 + HIST_VERLUST)):
                ausgang, ergebnis = "gescheitert", j
                break
        teil = df.iloc[:aus_i].copy()
        teil.attrs = {"tk_mp": df.attrs.get("ticker") or df.attrs.get("tk_mp"), "jung": df.attrs.get("jung")}
        try:
            r = erkenne(teil, index=index[index.index <= teil.index[-1]] if index is not None else None)
        except Exception:
            r = {"kaufsetup": False, "werte": {}}
        damals = bool(r.get("kaufsetup")) if d == "↑" else bool((r.get("short") or {}).get("setup"))
        weite = (h[aus_i:].max() / pivot - 1) * 100 if d == "↑" else (1 - l[aus_i:].min() / pivot) * 100
        aus.append({"beginn": beginn, "ende": ende, "ausbruch": aus_i, "pivot": pivot, "innen": {},
                    "muster": ["Base" if d == "↑" else "Zone ↓"], "richtung": d, "wochen": z["wochen"],
                    "val": z["val"], "vah": z["vah"], "poc": z["poc"],
                    "basenzahl": (r.get("werte") or {}).get("basenzahl") if d == "↑" else None,
                    "kaufsetup": damals, "tiefe_pct": round((1 - z["tief"] / z["hoch"]) * 100, 1),
                    "ausgang": ausgang, "ergebnis_index": ergebnis, "max_gewinn_pct": round(weite, 1)})
    return aus


def erkenne(df, woche=False, index=None, _vor_hoch=False):
    """Erkennung über die Balance-Zone: die Zone, die heute gilt (laufend oder höchstens 4 Wochen nach ihrem Kippen),
    eingeordnet nach den Regeln der Meister als Base oder Flagge (Powerplay). Pivot = Hoch der letzten Enge (innere
    Zone, Minervini); Flagge: Hoch der Flagge. Formnamen gibt es nicht mehr."""
    return _erkenne_mp(df, woche, index)

def _abschluss(df, woche, index, h, l, c, v, n, muster, oneil, werte, start, dauer, tiefe, tief_idx, hoch, bl, db,
               hinweis_db):
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
    hinweise = []
    if db is not None and hinweis_db:
        hinweise.append(hinweis_db)
    if muster == "Tasse ohne Henkel":
        hinweise.append("ohne Henkel: etwas höhere Ausfallquote (gelb)")
    markt = korrektur_markt(df, index, werte["start_index"])
    zu_tief_zum_markt = False
    if markt is not None:
        # Fällt der Markt kaum, wird mit 5 % gerechnet: eine Base von 40 % bei ruhigem Markt ist
        # abnorme Schwäche (Buch: Korrektur höchstens das 2- bis 3-Fache des Marktes).
        faktor = tiefe / max(markt, 5.0)
        werte.update({"index_rueckgang_pct": round(markt, 1), "korrektur_x_markt": round(faktor, 1)})
        ampel = "grün" if faktor <= 2 else "gelb" if faktor <= 3 else "rot"
        if muster:
            hinweise.append(f"Korrektur {faktor:.1f}-fach zum Markt ({ampel})")
        zu_tief_zum_markt = faktor > 3
    bz = basenzahl(df, index)
    if bz is not None and muster:
        werte["basenzahl"] = bz
        if bz >= 4:
            hinweise.append(f"späte Base (Nr. {bz})")
        elif bz == 3:
            hinweise.append("Base Nr. 3 (gelb)")
    if muster in ("Flat Base", "Base", "Cup+Handle", "Doppelboden", "Tasse ohne Henkel"):
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
        phase = int(phasen(df).iloc[-1])
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


# ── Basenhistorie: frühere Basen mit Form, Pivot und Ausgang des Ausbruchs ──
# Die Vergangenheit ist Lernstoff: welche Base Nr., welche Form, ist der Ausbruch gelungen oder gescheitert.
HIST_GEWINN = 0.20          # gelungen: Hoch mindestens 20 % über dem Pivot (O'Neils Gewinnziel) …
HIST_VERLUST = 0.08         # … bevor ein Schluss 8 % unter dem Pivot liegt (O'Neils Verlustgrenze) – sonst gescheitert


def basen_historie(df, index=None, tage=520):
    """Abgeschlossene Basen der letzten `tage` Handelstage (ohne die laufende Base am rechten Rand).
    Eine Base = mindestens 4 Wochen vom linken Rand und mindestens 5 % Rücksetzer (_base_zaehlt), beendet durch ein neues Hoch
    (dieselbe Abgrenzung wie die Basenzählung). Je Base: Form und Pivot aus der Erkennung am Tag vor dem neuen Hoch,
    Ausbruchstag (erster Schluss über dem Pivot nach dem Tief der Base) und Ausgang:
    gelungen (+20 % vor −8 %), gescheitert (Schluss 8 % unter dem Pivot zuerst) oder offen."""
    return _historie_mp(df, index, tage)


# ── Selbstprüfung: innere Widersprüche der Erkennung (wie der eingebaute Selbsttest im Flugzeug) ──
# Jede Prüfung beschreibt eine Bedingung, die bei richtiger Erkennung immer gilt. Schlägt eine an, ist das Muster
# unsicher und wird so gezeigt – die Erkennung selbst bleibt unverändert (Zeichen, kein Filter).
def selbstpruefung(df, erk, historie=None):
    h, l, c = (df[s].to_numpy(float) for s in ("High", "Low", "Close"))
    n = len(h)
    befunde = []
    w, muster = erk.get("werte", {}), erk.get("muster", [])
    if muster:
        s_i = w.get("start_index")
        e_i = w.get("ende_index", n - 1)
        if s_i is None or not 0 <= s_i <= e_i < n:
            befunde.append(f"Fenster der Base ungültig (Beginn {s_i}, Ende {e_i})")
        else:
            hb, tb = h[s_i:e_i + 1].max(), l[s_i:e_i + 1].min()
            p = w.get("pivot")
            if p is None or not tb <= p <= hb * 1.001:
                befunde.append(f"Pivot {p:.2f} liegt außerhalb der Base ({tb:.2f}–{hb:.2f})" if p else "kein Pivot")
            tiefe = (1 - tb / hb) * 100
            if abs(tiefe - (w.get("tiefe_pct") or 0)) > 1.0:
                befunde.append(f"Tiefe {w.get('tiefe_pct')} % passt nicht zum Fenster ({tiefe:.1f} %)")
            if e_i - s_i + 1 < FLAGGE_MIN:
                befunde.append(f"Base nur {e_i - s_i + 1} Tage lang")
            for a, b, _ in w.get("kontraktionen_lage", []):
                if not s_i <= a <= b <= e_i:
                    befunde.append("Kontraktion außerhalb der Base")
                    break
            db = w.get("doppelboden")
            if db and not (db["tief1"] < db["mitte"] < db["tief2"]):
                befunde.append("Doppelboden: Reihenfolge Tief – Zwischenhoch – Tief verletzt")
            if db and h[db["mitte"]] <= max(l[db["tief1"]], l[db["tief2"]]):
                befunde.append("Doppelboden: Zwischenhoch nicht über den Tiefs")
            ta = w.get("tasse")
            if ta and not (ta["links"] < ta["boden"] < ta["henkel_hoch"] <= ta["ende"]):
                befunde.append("Tasse: Reihenfolge linker Rand – Boden – Henkel verletzt")
        if len(set(muster)) != len(muster):
            befunde.append("Muster doppelt genannt")
        if "Doppelboden" in muster and not w.get("doppelboden"):
            befunde.append("Doppelboden genannt, aber nicht vermessen")
        if erk.get("kaufsetup") and s_i is not None and c[-1] < l[s_i:].min() * 0.999:
            befunde.append("Kaufsetup, aber Kurs unter dem Tief der Base")
    vorige_ende = -1
    for b in historie or []:
        if not b["beginn"] <= b["ende"] < n:
            befunde.append(f"Frühere Base {df.index[min(b['ende'], n - 1)].date()}: Fenster ungültig")
        elif b["beginn"] <= vorige_ende:
            befunde.append(f"Frühere Base ab {df.index[b['beginn']].date()} überlappt die vorige")
        elif not l[b["beginn"]:b["ende"] + 1].min() * 0.995 <= b["pivot"] <= h[b["beginn"]:b["ende"] + 1].max() * 1.005:
            befunde.append(f"Frühere Base ab {df.index[b['beginn']].date()}: Pivot außerhalb der Base")
        vorige_ende = max(vorige_ende, b["ende"])
    return befunde
