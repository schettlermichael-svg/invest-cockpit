"""Datenampel: erkennt Störungen in den Kursdaten, bevor sie als falsches Muster erscheinen.

pruefen(df, index=None, gegenprobe=None) -> {"ampel": …, "zeichen": [(ampel, datum, text), …]}

Geprüft wird das letzte Jahr (252 Handelstage):
  rot   ungültige Kurse (fehlend, null oder negativ, Hoch unter Tief)
  rot   Lücke: mehr als 5 Handelstage des Index fehlen am Stück
  rot   veraltet: der letzte Kurs ist mehr als 2 Handelstage älter als der Index
  gelb  Split-Verdacht: Sprung von einem Tag zum nächsten genau um einen typischen Split-Faktor
        (2, 3, 4, 5, 10, 3:2 – auf 2 % genau), auch bei Eröffnung und Schluss gleichermaßen
  gelb  Volumen null an mindestens 3 Tagen
  gelb  Kerzen ohne Spanne (Hoch = Tief) an mindestens 5 Tagen
  gelb  Gegenprobe: der letzte gemeinsame Schlusskurs weicht von der zweiten Quelle (Massive) um mehr
        als 1 % ab. Verglichen wird nur der jüngste Tag, weil Yahoo ältere Kurse um Dividenden bereinigt.
Schwellen gesetzt, nicht aus dem Buch. Die Störung wird gezeigt, nicht versteckt; ein Kaufsetup
gilt nicht, solange eine rote Störung vorliegt oder eine Störung in die Base fällt.
"""
import numpy as np
import pandas as pd

TAGE = 252
FAKTOREN = (2, 3, 4, 5, 10, 1.5)
GENAU = 0.02


def _split_faktor(q):
    for f in FAKTOREN:
        for z in (f, 1 / f):
            if abs(q / z - 1) <= GENAU:
                return f
    return None


def pruefen(df, index=None, gegenprobe=None):
    d = df.iloc[-TAGE:]
    zeichen = []
    kurse = d[["Open", "High", "Low", "Close"]]
    falsch = kurse.isna().any(axis=1) | (kurse <= 0).any(axis=1) | (d["High"] < d["Low"])
    if falsch.any():
        zeichen.append(("rot", falsch[falsch].index[-1], f"ungültige Kurse an {int(falsch.sum())} Tagen"))

    if index is not None and len(index):
        ix = index.index[(index.index >= d.index[0]) & (index.index <= index.index[-1])]
        fehlt = ~ix.isin(d.index)
        if fehlt.any():
            # längste zusammenhängende Lücke
            gruppen = (~fehlt).cumsum()
            laengen = pd.Series(fehlt.astype(int)).groupby(gruppen).sum()
            if laengen.max() > 5:
                g = laengen.idxmax()
                tag = ix[(gruppen == g) & fehlt][0]
                zeichen.append(("rot", tag, f"Lücke: {int(laengen.max())} Handelstage fehlen ab {tag:%d.%m.%Y}"))
        rueckstand = int((index.index > d.index[-1]).sum())
        if rueckstand > 2:
            zeichen.append(("rot", d.index[-1], f"veraltet: {rueckstand} Handelstage hinter dem Index"))

    c, o = d["Close"].to_numpy(float), d["Open"].to_numpy(float)
    for i in range(1, len(d)):
        q_schluss, q_offen = c[i] / c[i - 1], o[i] / c[i - 1]
        if abs(np.log(q_schluss)) < np.log(1.4):
            continue
        f = _split_faktor(q_offen)
        if f and _split_faktor(q_schluss) == f:
            zeichen.append(("gelb", d.index[i], f"Split-Verdacht: Sprung um Faktor {f:g} am {d.index[i]:%d.%m.%Y}"))

    null = d["Volume"] <= 0
    if null.sum() >= 3:
        zeichen.append(("gelb", null[null].index[-1], f"Volumen null an {int(null.sum())} Tagen"))
    flach = d["High"] == d["Low"]
    if flach.sum() >= 5:
        zeichen.append(("gelb", flach[flach].index[-1], f"{int(flach.sum())} Tage ohne Kursspanne"))

    if gegenprobe is not None and len(gegenprobe):
        gemeinsam = gegenprobe.index.intersection(d.index)
        if len(gemeinsam):
            t = gemeinsam.max()
            a_, b_ = float(d.loc[t, "Close"]), float(gegenprobe.loc[t])
            if b_ > 0 and abs(a_ / b_ - 1) > 0.01:
                de = lambda x: f"{x:.2f}".replace(".", ",")      # noqa: E731
                zeichen.append(("gelb", t, f"Kursquellen weichen ab: Yahoo {de(a_)} gegen Massive {de(b_)} "
                                           f"am {t:%d.%m.%Y}"))

    ampel = "rot" if any(a == "rot" for a, _, _ in zeichen) else "gelb" if zeichen else "grün"
    return {"ampel": ampel, "zeichen": zeichen}
