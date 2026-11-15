"""Erkennung des Invest Cockpit (seit der Generalinventur 15.11.2026 nur noch, was die App wirklich benutzt):

erkenne(df, woche=False, index=None) -> dict
    mp        Market-Profile-Analyse (Wertzonen aus 30-Minuten-Kerzen, marketprofile.py)
    seite     long/short: die laufende Bewegung der Wertzonen (↑/↓), sonst die Phase (Short in Phase 3 und 4, Weinstein)
    zonen     Wertzonen für Chart und Zustand
    werte     start_index, val, vah, poc der Wertzone, die heute gilt (Nach dem Kauf: enger Nachzieh-Stopp)
    hinweise  Warnungen für den Kopf der Titelseite: Übernahme-Verdacht, Klimax-Verdacht, Daten gestört
    daten     Datenampel (datenpruefung)
Dazu klimax() (Klimax-Zeichen, auch für den Zustand), letztes_markttief() (Beginn der Basenzählung), _phase_von().

Bis 15.11.2026 rechnete erkenne() zusätzlich eine eigene Base mit Trendvorlage, Muster, Kaufsetup und Hinweisen
(Tiefenampel, Kaufzone, V-Erholung, Base auf Base, Primärbasis) – eine zweite Base neben dem Scanner (vcp_zone) und eine
zweite Trendvorlage neben system_minervini. Nichts davon wurde mehr benutzt; der Code liegt in
_to_delete/uebergabe_2026-11-12/erkennung_alt_2026-11-15.py. Klimax und Datenampel gelten jetzt für jeden Titel (vorher
nur, wenn die alte Erkennung eine reife Long-Zone fand).
"""
import numpy as np

import datenpruefung
import massive
from phase import phasen
from masse import GD200_TAGE, JAHR_TAGE, WOCHE  # noqa: E402

# ── Klimax und Überdehnung (O'Neil, Verkaufsregeln; Regelkatalog O'Neil „Technische Verkaufssignale“) ──
KLIMAX_GD200 = 0.70        # Kurs mindestens 70 % über dem GD200
KLIMAX_LAUF_TAGE = 90      # Klimax erst nach langem Anstieg: mindestens 18 Wochen seit dem Tief der letzten Base
KLIMAX_SPURT = 0.25        # … und zuletzt mindestens 25 % in höchstens 15 Handelstagen
KLIMAX_FENSTER = 15        # die Zeichen zählen, wenn sie in den letzten 3 Wochen auftreten


KLIMAX_GD200_MIT = 0.50    # die übrigen Zeichen zählen nur, wenn der Kurs schon mindestens 50 % über dem GD200 steht –
                           # sonst wäre jeder kräftige Ausbruch aus einer Base (größte Wochenspanne!) ein „Klimax“


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
KLIMAX_MIN_WOCHEN = 8   # Wochenspanne vergleichen ab 8 Wochen Anstieg
KLIMAX_WOCHEN = 3       # Klimax-Zeichen zählen in den letzten 3 Wochen
BREIT_FAKTOR = 1.5      # breite Woche: Spanne mindestens 1,5-fach des Medians
SCHIENEN_GLEICH = 0.01  # Eisenbahnschienen: Schluss der beiden Wochen höchstens 1 % auseinander
LUECKE_MIN = 1.03       # Erschöpfungslücke: Tief mindestens 3 % über dem Hoch des Vortags
KLEBE_TAGE = 8          # Übernahme-Verdacht: die letzten 8 Tage …
KLEBE_SPANNE = 0.03     # … Gesamtspanne höchstens 3 % …
KLEBE_TAG = 0.008       # … Tagesspanne im Mittel höchstens 0,8 % …
KLEBE_FAKTOR = 3        # … und vorher mindestens dreimal so groß
PHASE_MIN_TAGE = 300         # unter 300 Tagen Daten: keine Phase (junge Aktie)


def klimax(h, l, c, v):
    """Zeichen eines Gipfels nach O'Neil. Liefert die Gründe (leer = kein Verdacht).
    Allein reicht: Kurs mindestens 70 % über dem GD200. Die übrigen Zeichen (Spurt nach langem Anstieg, größte
    Wochenspanne, Eisenbahnschienen, Erschöpfungslücke) zählen erst ab 50 % über dem GD200."""
    n = len(c)
    gruende = []
    if n < GD200_TAGE:
        return gruende
    gd200 = float(np.mean(c[-GD200_TAGE:]))
    ueber = c[-1] / gd200 - 1
    if ueber >= KLIMAX_GD200:
        gruende.append(f"{ueber * 100:.0f} % über dem GD200")
    if ueber < KLIMAX_GD200_MIT:
        return gruende
    # Anstieg seit dem Tief der letzten Base (tiefstes Tief des letzten Jahres vor dem jüngsten Hoch)
    hi = n - 1 - int(np.argmax(h[::-1][:KLIMAX_FENSTER + 1]))
    a = max(0, hi - JAHR_TAGE)
    tief = a + int(np.argmin(l[a:hi + 1]))
    lauf = hi - tief
    if lauf >= KLIMAX_LAUF_TAGE:
        spurt = h[hi] / l[max(tief, hi - KLIMAX_FENSTER):hi + 1].min() - 1
        if spurt >= KLIMAX_SPURT:
            gruende.append(f"Spurt +{spurt * 100:.0f} % in 3 Wochen nach {lauf // WOCHE} Wochen Anstieg")
        # größte Wochenspanne seit Beginn des Anstiegs in den letzten 3 Wochen
        k = (n - tief) // WOCHE
        if k >= KLIMAX_MIN_WOCHEN:
            wh = h[n - WOCHE * k:].reshape(k, WOCHE).max(1); wl = l[n - WOCHE * k:].reshape(k, WOCHE).min(1)
            sp = wh - wl
            if int(np.argmax(sp)) >= k - KLIMAX_WOCHEN and sp.max() > BREIT_FAKTOR * np.median(sp):
                gruende.append("größte Wochenspanne seit Beginn des Anstiegs")
            # Eisenbahnschienen: zwei breite Wochen nebeneinander mit fast gleichem Schluss
            wc = c[n - WOCHE * k:].reshape(k, WOCHE)[:, -1]
            for j in (k - 2, k - KLIMAX_WOCHEN):
                if j >= 1 and min(sp[j], sp[j + 1]) > BREIT_FAKTOR * np.median(sp) and abs(wc[j + 1] / wc[j] - 1) < SCHIENEN_GLEICH:
                    gruende.append("Eisenbahnschienen (zwei breite Wochen, gleicher Schluss)")
                    break
        # Erschöpfungslücke: Kurslücke nach oben ab 3 % in den letzten 3 Wochen
        for i in range(max(1, n - KLIMAX_FENSTER), n):
            if l[i] > h[i - 1] * LUECKE_MIN:
                gruende.append("Erschöpfungslücke")
                break
    return gruende


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
    spanne = h[-KLEBE_TAGE:].max() / l[-KLEBE_TAGE:].min() - 1
    tag = np.mean(h[-KLEBE_TAGE:] / l[-KLEBE_TAGE:] - 1)
    vorher = np.mean(h[-JAHR_TAGE:-KLEBE_TAGE] / l[-JAHR_TAGE:-KLEBE_TAGE] - 1)
    if spanne <= KLEBE_SPANNE and tag <= KLEBE_TAG and vorher >= KLEBE_FAKTOR * tag:
        return (f"Übernahme-Verdacht: Kurs klebt seit 8 Tagen in {spanne * 100:.1f} % Spanne "
                f"(Tagesspanne {tag * 100:.2f} % statt {vorher * 100:.1f} %) – kein Muster bewertet").replace(".", ",")
    return None


_PHASEN = {}


def _phase_von(df):
    """Phase je Tag (Weinstein, wöchentlich gerechnet, auf Tage übertragen); None bei zu kurzer Reihe."""
    n = len(df)
    if n < PHASE_MIN_TAGE or df.attrs.get("jung", n < PHASE_MIN_TAGE):
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


REIF_WOCHEN = 3              # eine Wertzone ist reif ab 3 Wochen (Dalton: Balance braucht Zeit; vorher nur Flagge oder Umkehr)


def _reif(a, st, seite):
    """Reife Wertzone für den engen Nachzieh-Stopp (Nach dem Kauf): ab 3 Wochen; jünger nur als Flagge (entstanden aus
    einem Lauf in Richtung der Seite, der nicht gescheitert ist) oder als Umkehr nach gescheitertem Bruch (Dalton)."""
    d = "↑" if seite == "long" else "↓"
    if st["wochen"] >= REIF_WOCHEN:
        return True
    ak = a.get("aktiv")
    if st["herkunft"] == d:
        t_zone = a["wochen"][st["von"]]["tag"]
        return not any(x["art"] == "S" and x["dir"] == d and x["tag"] >= t_zone for x in a["signale"])
    return bool(ak and ak.get("art") == "U" and ak["dir"] == d and ak["zone"]["nr"] == st["nr"])


def _erkenne_mp(df, woche=False, index=None):
    h, l, c, v = (df[s_].to_numpy(float) for s_ in ("High", "Low", "Close", "Volume"))
    hinweise, werte = [], {}
    a = mp_von(df)
    aus = {"mp": a, "hinweise": hinweise, "werte": werte}
    uebernahme = uebernahme_verdacht(h, l)
    if uebernahme:
        hinweise.append(uebernahme)
    if a is not None and not uebernahme:
        ph = _phase_von(df)
        phase = int(ph[-1]) if ph is not None else None
        ak = a.get("aktiv")
        # Seite: eine laufende Bewegung der Wertzonen (A, F, U, B – nicht gescheitert) bestimmt sie; sonst die Phase
        aus["seite"] = ("long" if ak["dir"] == "↑" else "short") if ak else ("short" if phase in SHORT_PHASEN else "long")
        aus["zonen"] = a["zonen"]
        st = a["stand"][-1]                      # Wertzone der abgeschlossenen Wochen, wie sie heute gilt
        if _reif(a, st, aus["seite"]):
            werte.update(start_index=_tag_index(df, a["wochen"][st["von"]]["tag"]), val=st["val"], vah=st["vah"],
                         poc=st["poc"])
    elif a is None:
        hinweise.append("keine 30-Minuten-Kerzen – Wertzonen fehlen")
    gipfel = klimax(h, l, c, v)
    if gipfel:
        werte["klimax"] = gipfel
        hinweise.append("Klimax-Verdacht (rot): " + "; ".join(gipfel))
    gegen = massive.schlusskurse(df.attrs["ticker"]) if df.attrs.get("ticker") else None
    daten = datenpruefung.pruefen(df, index, gegen)
    aus["daten"] = daten
    if daten["zeichen"]:
        beginn = df.index[werte["start_index"]] if "start_index" in werte else df.index[-1]
        in_zone = any(tag >= beginn for _, tag, _ in daten["zeichen"])
        if daten["ampel"] == "rot" or in_zone:
            hinweise.append("Daten gestört" + (" in der Wertzone" if in_zone else "") + " – Zonen nicht verlässlich")
    return aus


def erkenne(df, woche=False, index=None, _vor_hoch=False):
    """Seite, Wertzonen, Warnungen und Datenampel eines Titels (siehe oben)."""
    return _erkenne_mp(df, woche, index)

