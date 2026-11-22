"""Erkennung des Invest Cockpit (seit der Generalinventur 15.11.2026 nur noch, was die App wirklich benutzt):

erkenne(df, woche=False, index=None) -> dict
    mp        Market-Profile-Analyse (Wertzonen aus 30-Minuten-Kerzen, marketprofile.py)
    seite     long/short: die laufende Bewegung der Wertzonen (↑/↓), sonst die Phase (Short in Phase 3 und 4, Weinstein)
    zonen     Wertzonen für Chart und Zustand
    werte     start_index, val, vah, poc der Wertzone, die heute gilt (Nach dem Kauf: enger Nachzieh-Stopp)
    hinweise  Warnungen für den Kopf der Titelseite: Übernahme-Verdacht, Klimax-Verdacht, Daten gestört
    daten     Datenampel (datenpruefung)
Dazu klimax() (Klimax-Zeichen, auch für den Zustand), _phase_von().

Bis 15.11.2026 rechnete erkenne() zusätzlich eine eigene Base mit Trendvorlage, Muster, Kaufsetup und Hinweisen
(Tiefenampel, Kaufzone, V-Erholung, Base auf Base, Primärbasis) – eine zweite Base neben dem Scanner (vcp_zone) und eine
zweite Trendvorlage neben system_minervini. Nichts davon wurde mehr benutzt; der Code liegt in
_to_delete/uebergabe_2026-11-12/erkennung_alt_2026-11-15.py. Klimax und Datenampel gelten jetzt für jeden Titel (vorher
nur, wenn die alte Erkennung eine reife Long-Zone fand).
"""
import numpy as np

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










# ── Wertzonen (4.11.2026): exakte Wertzonen aus 30-Minuten-TPO (kern/marketprofile.py), beide Richtungen ──
_MP, _ROH = {}, {}


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















