"""Angebot absorbiert: misst, ob in einer Base das Angebot verschwindet – ohne Wellen zu zählen.

Minervini verbindet O'Neil (Base, Pivot) und Weinstein (Phase 2): Im Aufwärtstrend zieht sich der Kurs unter einem
Widerstand zusammen, die Tiefs steigen, das Volumen trocknet aus. Ob das als 2, 3 oder 4 Kontraktionen gezählt
wird, ist zweitrangig. Vier Zeilen, je als Ampel:

1. Trend: Kurs über dem GD200 und GD200 nicht fallend (Weinstein Phase 2 / Minervinis Trendvorlage im Kern);
   bei zu kurzer Historie der Anstieg vor der Base (O'Neil: mindestens 30 %).
Gemessen wird bis zum Tag vor dem Ausbruch (erster Tag mit Hoch über dem Pivot).
2. Höhere Tiefs, engere Spanne: die Tiefs der letzten drei 10-Tage-Abschnitte (vom rechten Rand her, keine
   Wellen) steigen und die Spanne der letzten 10 Tage ist höchstens ein Drittel der Spanne der ganzen Base, beide als Hoch über Tief (Keil, Dreieck);
   oder die Tiefs halten und die Spanne ist höchstens 5 % (flache Base). Gelb: Tiefs halten oder Spanne bis zur
   Hälfte.
3. Volumen trocken: Schnitt der letzten 10 Tage gegen die 50 Tage davor; grün bis 0,8-fach, gelb bis 1,0-fach.
4. Enge nah am Pivot: Schluss höchstens 10 % unter dem Pivot (gelb bis 15 %); darunter ist es Zappeln am Boden.

Gesamt: grün, wenn Tiefs/Enge und Volumen grün sind; rot, wenn beide rot sind oder Trend bzw. Pivot-Nähe rot ist
(Pflicht); sonst gelb. Gemessen an 3.941 früheren Basen des Reviers trennten nur diese beiden Zeilen
(beide grün 56,5 % gelungen, beide rot 39,8 %, Schnitt 46 %).
Schwellen sind unsere Setzung (Drittel und 0,8-fach angelehnt an Minervinis Beschreibung der Enge und des
Austrocknens). Zeichen, kein Filter.
"""
import numpy as np

ENGE_TAGE = 10
ENG_ABSOLUT = 5.0         # Spanne der Enge in %, die immer als eng gilt (Minervini: zuletzt wenige Prozent)


def _ampel(gut, mittel):
    return "grün" if gut else "gelb" if mittel else "rot"


def trend(c, woche=False):
    g, m = (40, 4) if woche else (200, 22)
    if len(c) < g + m:
        return None
    ma = np.convolve(c, np.ones(g) / g, mode="valid")
    return bool(c[-1] > ma[-1] and ma[-1] >= ma[-1 - m] * 0.99)


def absorption(df, start, pivot, ende=None, woche=False):
    h, l, c, v = (df[k].to_numpy(float) for k in ("High", "Low", "Close", "Volume"))
    n = len(c)
    ende = n - 1 if ende is None else int(ende)
    start = int(start)
    k_ = 3 if woche else ENGE_TAGE              # Wochenchart: 3 Wochen Enge, Schnitt über 10 Wochen
    s_ = 10 if woche else 50
    if ende - start + 1 < (5 if woche else 15) or not pivot:
        return None
    # Gemessen wird die Base bis zum Tag vor dem Ausbruch: der Ausbruch selbst bringt Volumen und Spanne
    tief_i = start + int(np.argmin(l[start:ende + 1]))
    for i in range(tief_i + 1, ende + 1):
        if h[i] > pivot:
            ende = i - 1
            break
    if ende - start + 1 < (5 if woche else 15):
        return None
    zeilen = {}

    t = trend(c[:ende + 1], woche)
    if t is None:
        # Zu kurze Historie für den GD200: dann der Vorlauf nach O'Neil (mindestens 30 % Anstieg vor der Base)
        vor = l[max(0, start - (24 if woche else 120)):start + 1]
        if len(vor) >= (4 if woche else 20):
            vl = (h[start:ende + 1].max() / vor.min() - 1) * 100
            zeilen["trend"] = (_ampel(vl >= 30, vl >= 20), f"Anstieg vor der Base {vl:.0f} % (kein GD200, zu kurze Historie)")
        else:
            zeilen["trend"] = ("grau", "zu kurze Historie")
    else:
        zeilen["trend"] = (_ampel(t, False), "Kurs über steigendem GD200" if t else
                           "kein Aufwärtstrend (Kurs unter oder GD200 fallend)")

    # Höhere Tiefs am rechten Rand: Tiefs von drei aufeinanderfolgenden Abschnitten (10 Tage bzw. 3 Wochen), vom Ende her gezählt
    stuecke = [(max(start, ende + 1 - k_ * (k + 1)), ende + 1 - k_ * k) for k in (2, 1, 0)]
    tiefs = [(a_ + int(np.argmin(l[a_:b_])), float(l[a_:b_].min())) for a_, b_ in stuecke if b_ > a_]
    werte = [x for _, x in tiefs]
    # Tiefs halten (keins fällt um mehr als 1 %) bzw. steigen (zusätzlich das letzte über dem ersten)
    halten = len(werte) == 3 and werte[1] >= werte[0] * 0.99 and werte[2] >= werte[1] * 0.99
    steigend = halten and werte[2] > werte[0] * 1.01
    tiefe = (h[start:ende + 1].max() / l[start:ende + 1].min() - 1) * 100
    a = max(start, ende + 1 - k_)
    eng = (h[a:ende + 1].max() / l[a:ende + 1].min() - 1) * 100
    verh = eng / tiefe if tiefe > 0 else 1.0
    # Keil/Dreieck: Tiefs steigen und die Spanne schrumpft auf ein Drittel der Tiefe; flache Base: Tiefs halten und
    # die Spanne ist ohnehin eng (höchstens 5 %)
    gruen = (steigend and verh <= 1 / 3) or (halten and eng <= ENG_ABSOLUT)
    zeilen["absorption"] = (_ampel(gruen, halten or verh <= 0.5),
                            f'Tiefs der letzten drei Abschnitte {"steigen" if steigend else "halten" if halten else "fallen"}; '
                            f'Spanne der letzten {ende + 1 - a} {"Wochen" if woche else "Tage"} {eng:.1f} % gegen {tiefe:.1f} % Spanne der ganzen Base '
                            f'({verh:.2f}-fach; Spanne = Hoch über Tief, die Tiefe vom Hoch aus ist '
                            f'{(1 - l[start:ende + 1].min() / h[start:ende + 1].max()) * 100:.1f} %)')

    s = float(np.mean(v[max(0, a - s_):a])) if a >= (4 if woche else 20) else None
    trocken = float(np.mean(v[a:ende + 1])) / s if s else None
    zeilen["volumen"] = ("grau", "zu kurze Historie") if trocken is None else (
        _ampel(trocken <= 0.8, trocken <= 1.0), f"Volumen der letzten {ende + 1 - a} {'Wochen' if woche else 'Tage'} {trocken:.2f}-fach des Schnitts")

    abst = (1 - c[ende] / pivot) * 100
    zeilen["pivot"] = (_ampel(-5 <= abst <= 10, abst <= 15),
                       f"Schluss {abst:.1f} % unter dem Pivot" if abst >= 0 else f"Schluss {-abst:.1f} % über dem Pivot")

    # Gesamt: getragen von den beiden Zeilen, die an 3.941 früheren Basen trennten (Tiefs/Enge und Volumen);
    # Trend und Pivot-Nähe sind Pflicht (rot dort macht die Ampel rot), trennen aber nicht zusätzlich
    ab_, vo_ = zeilen["absorption"][0], zeilen["volumen"][0]
    pflicht_rot = zeilen["trend"][0] == "rot" or zeilen["pivot"][0] == "rot"
    if pflicht_rot or (ab_ == "rot" and vo_ == "rot"):
        gesamt = "rot"
    elif ab_ == "grün" and vo_ == "grün":
        gesamt = "grün"
    else:
        gesamt = "gelb"
    return {"ampel": gesamt, "zeilen": zeilen, "tiefs": tiefs, "ende": ende,
            "enge": (a, ende, float(h[a:ende + 1].max()), float(l[a:ende + 1].min()), eng), "trocken": trocken,
            "eng": eng, "verhaeltnis": verh, "halten": halten, "steigend": steigend}
