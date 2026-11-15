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
from masse import GD50_TAGE  # noqa: E402

TAGE = 14


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
STOPP_GELB = 1.5     # Stopp im Rauschen: unter 1 ATR rot, bis 1,5 gelb, darüber grün
ENGE_TAGE = 5        # Enge: Spannen der letzten 5 Tage …
ENGE_TAGE_HEUTE = 4  # … (die 4 jüngsten nach dem Bezugstag)
ENGE_GRUEN = 0.6     # … unter 0,6 ATR grün (eng)
ENGE_GELB = 0.9      # … bis 0,9 gelb
UEBERDEHNT_ROT = 6   # Überdehnung: ab 6 ATR vom GD50 rot
UEBERDEHNT_GELB = 4  # … ab 4 gelb
STOPP_ROT = 1       # Stopp unter 1 × ATR vom Einstieg: im Tagesrauschen (rot)
NACH_NAH = 1        # nachjagen: bis 1 × ATR über dem Pivot nah am Einstieg (grün) …
NACH_UNTERWEGS = 2  # … bis 2 × ATR schon unterwegs (gelb), darüber zu weit


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


def nachjagen(kurs, pivot, a, seite="long"):
    """None, solange der Kurs den Pivot noch nicht überschritten hat."""
    if not (a and pivot):
        return None
    x = (kurs - pivot) / a if seite == "long" else (pivot - kurs) / a
    if x < 0:
        return None
    wo = "über dem Pivot" if seite == "long" else "unter dem Auslöser"
    if x <= NACH_NAH:
        return "grün", f"{_z(x)} × ATR {wo} → nah am Einstieg"
    if x <= NACH_UNTERWEGS:
        return "gelb", f"{_z(x)} × ATR {wo} → schon unterwegs"
    return "rot", f"{_z(x)} × ATR {wo} → zu weit gelaufen, nicht nachjagen"


def enge(df):
    tr = _tr(df)
    n = len(tr) - 1
    a = wert(df, n - ENGE_TAGE)
    if not a:
        return None
    x = float(np.mean(tr[n - ENGE_TAGE_HEUTE:])) / a
    if x < ENGE_GRUEN:
        return "grün", f"Spannen der letzten 5 Tage {_z(x)} × ATR → eng, Ruhe vor dem Ausbruch"
    if x <= ENGE_GELB:
        return "gelb", f"Spannen der letzten 5 Tage {_z(x)} × ATR → beruhigt sich"
    return "rot", f"Spannen der letzten 5 Tage {_z(x)} × ATR → unruhig, keine Enge"


def ueberdehnung(df, a=None):
    a = a or wert(df)
    c = df["Close"].to_numpy(float)
    if not a or len(c) < 50:
        return None
    x = (c[-1] - float(np.mean(c[-GD50_TAGE:]))) / a
    lage = "über" if x >= 0 else "unter"
    if abs(x) >= UEBERDEHNT_ROT:
        return "rot", f"{_z(abs(x))} × ATR {lage} dem GD50 → überdehnt", x
    if abs(x) >= UEBERDEHNT_GELB:
        return "gelb", f"{_z(abs(x))} × ATR {lage} dem GD50 → weit gespannt", x
    return "grün", f"{_z(abs(x))} × ATR {lage} dem GD50 → im üblichen Rahmen", x
