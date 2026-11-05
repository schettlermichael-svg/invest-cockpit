"""ATR-Zeichen (05.11.2026). Die ATR (Average True Range, 14 Tage) ist das normale Tagesrauschen eines Titels: wie weit
er sich an einem gewöhnlichen Tag bewegt, Lücken zum Vortag eingeschlossen. Sie misst jede Entfernung am Temperament
des Titels statt in festen Prozent. Alles hier sind Zeichen, keine Filter.

  Stopp im Rauschen   Abstand Einstieg → Stopp in ATR.   unter 1 rot (im Tagesrauschen), bis 1,5 gelb, darüber grün
  Zu weit gelaufen    Kurs jenseits des Pivots in ATR.   bis 1 grün, bis 2 gelb, darüber rot (nicht nachjagen)
  Enge                Spannen der letzten 5 Tage gegen die ATR davor.   unter 0,6 grün (eng), bis 0,9 gelb, darüber rot
  Überdehnung         Abstand vom GD50 in ATR.   ab 4 gelb, ab 6 rot (überdehnt – für Long eine Warnung, für Short
                      der Boden, auf dem ein Bruch gedeiht)
Die Schwellen sind unsere Setzung, nicht aus den Büchern.
"""
import numpy as np

TAGE = 14


def _tr(df):
    h, l, c = (df[k].to_numpy(float) for k in ("High", "Low", "Close"))
    tr = np.empty(len(c))
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return tr


def wert(df, bis=None):
    """ATR der 14 Tage bis einschließlich Index bis (Standard: letzter Tag)."""
    tr = _tr(df)
    bis = len(tr) - 1 if bis is None else bis
    if bis < TAGE:
        return None
    a = float(np.nanmean(tr[bis - TAGE + 1:bis + 1]))
    return a if a > 0 else None


def _z(x):
    return f"{x:.1f}".replace(".", ",")


def stopp(einstieg, stopp_, a):
    if not (a and einstieg and stopp_):
        return None
    x = abs(einstieg - stopp_) / a
    if x < 1:
        return "rot", f"Stopp {_z(x)} × ATR vom Einstieg → im Tagesrauschen, wird leicht ausgelöst"
    if x < 1.5:
        return "gelb", f"Stopp {_z(x)} × ATR vom Einstieg → knapp über dem Tagesrauschen"
    return "grün", f"Stopp {_z(x)} × ATR vom Einstieg → außerhalb des Tagesrauschens"


def nachjagen(kurs, pivot, a, seite="long"):
    """None, solange der Kurs den Pivot noch nicht überschritten hat."""
    if not (a and pivot):
        return None
    x = (kurs - pivot) / a if seite == "long" else (pivot - kurs) / a
    if x < 0:
        return None
    wo = "über dem Pivot" if seite == "long" else "unter dem Auslöser"
    if x <= 1:
        return "grün", f"{_z(x)} × ATR {wo} → nah am Einstieg"
    if x <= 2:
        return "gelb", f"{_z(x)} × ATR {wo} → schon unterwegs"
    return "rot", f"{_z(x)} × ATR {wo} → zu weit gelaufen, nicht nachjagen"


def enge(df):
    tr = _tr(df)
    n = len(tr) - 1
    a = wert(df, n - 5)
    if not a:
        return None
    x = float(np.mean(tr[n - 4:])) / a
    if x < 0.6:
        return "grün", f"Spannen der letzten 5 Tage {_z(x)} × ATR → eng, Ruhe vor dem Ausbruch"
    if x <= 0.9:
        return "gelb", f"Spannen der letzten 5 Tage {_z(x)} × ATR → beruhigt sich"
    return "rot", f"Spannen der letzten 5 Tage {_z(x)} × ATR → unruhig, keine Enge"


def ueberdehnung(df, a=None):
    a = a or wert(df)
    c = df["Close"].to_numpy(float)
    if not a or len(c) < 50:
        return None
    x = (c[-1] - float(np.mean(c[-50:]))) / a
    lage = "über" if x >= 0 else "unter"
    if abs(x) >= 6:
        return "rot", f"{_z(abs(x))} × ATR {lage} dem GD50 → überdehnt", x
    if abs(x) >= 4:
        return "gelb", f"{_z(abs(x))} × ATR {lage} dem GD50 → weit gespannt", x
    return "grün", f"{_z(abs(x))} × ATR {lage} dem GD50 → im üblichen Rahmen", x
