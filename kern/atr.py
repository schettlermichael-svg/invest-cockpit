"""ATR-Zeichen (05.11.2026). Die ATR (Average True Range, 14 Tage) ist das normale Tagesrauschen eines Titels: wie weit
er sich an einem gewöhnlichen Tag bewegt, Lücken zum Vortag eingeschlossen. Sie misst jede Entfernung am Temperament
des Titels statt in festen Prozent. Alles hier sind Zeichen, keine Filter.

  Stopp im Rauschen   Abstand Einstieg → Stopp in ATR.   unter 1 rot (im Tagesrauschen), bis 1,5 gelb, darüber grün
  Zu weit gelaufen    Kurs jenseits der Front in ATR.   bis 1 grün, bis 2 gelb, darüber rot (nicht nachjagen)
  Enge                Spannen der letzten 5 Tage gegen die ATR davor.   unter 0,6 grün (eng), bis 0,9 gelb, darüber rot
  Überdehnung         Abstand vom GD50 in ATR.   ab 4 gelb, ab 6 rot (überdehnt – für Long eine Warnung, für Short
                      der Boden, auf dem ein Bruch gedeiht)
Die Schwellen sind unsere Setzung, nicht aus den Büchern.
"""
import numpy as np

TAGE = 14


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
STOPP_GELB = 1.5     # Stopp im Rauschen: unter 1 ATR rot, bis 1,5 gelb, darüber grün
STOPP_ROT = 1       # Stopp unter 1 × ATR vom Einstieg: im Tagesrauschen (rot)


def _tr(df):
    h, l, c = (df[k].to_numpy(float) for k in ("High", "Low", "Close"))
    tr = np.empty(len(c))
    tr[0] = h[0] - l[0]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return tr


def reihe(df, n=TAGE):
    """ATR als Reihe (pandas Series, Index wie df): Mittel der True Range der letzten n Tage – die eine ATR der App
    (Generalinventur 15.11.2026: vorher fünf Rechnungen – Wilder-Glättung in vcp_zone, Spanne ohne Lücken in avwap,
    einfaches Mittel hier, in zeichen und auktion; Stopp, Zonen und Anker maßen dasselbe Rauschen verschieden)."""
    import pandas as pd
    return pd.Series(_tr(df), index=df.index).rolling(n).mean()


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
    if x < STOPP_ROT:
        return "rot", f"Stopp {_z(x)} × ATR vom Einstieg → im Tagesrauschen, wird leicht ausgelöst"
    if x < STOPP_GELB:
        return "gelb", f"Stopp {_z(x)} × ATR vom Einstieg → knapp über dem Tagesrauschen"
    return "grün", f"Stopp {_z(x)} × ATR vom Einstieg → außerhalb des Tagesrauschens"






