"""Fundament-Ampeln nach Minervini (Regelkatalog Kap. 7–8): sieben Prüfpunkte, Code 33,
Gewinnqualität. Reine Rechnung ohne Netz – die Daten kommen aus quellen.laden().

Schwellen aus dem Buch; „kräftiger Umsatz ab 15 %“ und „deutliche Überraschung ab 3 %“
sind gesetzt, nicht aus dem Buch (dort nur in Worten) – sie stehen hier als Konstanten.
"""
import numpy as np
import pandas as pd

GRUEN, GELB, ROT, GRAU = "grün", "gelb", "rot", "grau"
UMSATZ_KRAEFTIG = 15.0
UEBERRASCHUNG_DEUTLICH = 3.0
BESCHLEUNIGT_AB = 1.0       # Umsatzrate muss um mindestens 1 Prozentpunkt steigen (sonst Rauschen)


def _wachstum(reihe):
    """Wachstum zum Vorjahresquartal in Prozent (vier Werte zurück); bei Verlust im Vorjahr NaN."""
    v = reihe.to_numpy(float)
    g = np.full(len(v), np.nan)
    for i in range(4, len(v)):
        if v[i - 4] > 0:
            g[i] = (v[i] / v[i - 4] - 1) * 100
    return pd.Series(g, index=reihe.index)


def _p(x, stellen=0, vorzeichen=True):
    """Deutsche Zahl mit echtem Minuszeichen, optional mit Plus."""
    t = f"{abs(x):,.{stellen}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 else "+" if vorzeichen else "") + t


def _steigt(werte, n):
    """Die letzten n Schritte steigen jeweils (braucht n+1 Werte ohne Lücke)."""
    w = [x for x in werte[-(n + 1):]]
    return len(w) == n + 1 and not any(np.isnan(w)) and all(b > a for a, b in zip(w, w[1:]))


def quartalsgewinn(gewinne):
    g = _wachstum(gewinne["eps"]).dropna()
    if len(g) < 2:
        return GRAU, "zu wenige Quartale"
    letzte = g.iloc[-2:]
    text = " / ".join(f"{_p(x)} %" for x in g.iloc[-3:])
    if letzte.min() >= 25:
        return GRUEN, text + (" (stark)" if letzte.min() >= 40 else "")
    if letzte.min() >= 20:
        return GELB, text
    return ROT, text


def beschleunigung(gewinne):
    g = _wachstum(gewinne["eps"])
    s = g.rolling(2).mean().dropna()                      # Zwei-Quartals-Schnitt
    if len(s) < 3:
        return GRAU, "zu wenige Quartale"
    a, b, c = s.iloc[-3], s.iloc[-2], s.iloc[-1]
    text = f"Schnitt {_p(a)} → {_p(b)} → {_p(c)} %"
    if c > b > a:
        return GRUEN, text
    if a > 0 and c < 0.5 * a:
        return ROT, text + " (Rate mehr als halbiert)"
    return GELB, text


def umsatz(sec):
    if sec is None or sec.empty or sec["umsatz"].dropna().shape[0] < 6:
        return GRAU, "keine Umsatzreihe"
    g = _wachstum(sec["umsatz"].dropna()).dropna()
    if len(g) < 2:
        return GRAU, "zu wenige Quartale"
    text = " / ".join(f"{_p(x)} %" for x in g.iloc[-3:])
    if g.iloc[-1] <= 2:
        return ROT, text
    if g.iloc[-1] >= UMSATZ_KRAEFTIG and g.iloc[-1] >= g.iloc[-2] + BESCHLEUNIGT_AB:
        return GRUEN, text + " (beschleunigt)"
    return GELB, text


def _marge(sec):
    d = sec.dropna()
    d = d[d["umsatz"] > 0]
    return (d["nettogewinn"] / d["umsatz"] * 100)


def marge(sec):
    if sec is None or sec.empty:
        return GRAU, "keine Umsatzreihe"
    m = _marge(sec)
    if len(m) < 6:
        return GRAU, "zu wenige Quartale"
    zum_vorjahr = (m - m.shift(4)).dropna()               # gleiches Quartal im Vorjahr (Saison)
    text = f"Nettomarge {_p(m.iloc[-1], 1, False)} % (Vorjahr {_p(m.iloc[-5], 1, False)} %)" if len(m) >= 5 else ""
    if len(zum_vorjahr) < 2:
        return GRAU, text
    if (zum_vorjahr.iloc[-2:] > 0).all():
        return GRUEN, text
    if (zum_vorjahr.iloc[-2:] < 0).all():
        return ROT, text
    return GELB, text


def ueberraschung(gewinne):
    u = gewinne["ueberraschung_pct"].dropna()
    if len(u) < 2:
        return GRAU, "keine Schätzungen"
    text = " / ".join(f"{_p(x, 1)} %" for x in u.iloc[-3:])
    if u.iloc[-1] < 0:
        return ROT, text
    if (u.iloc[-2:] >= UEBERRASCHUNG_DEUTLICH).all():
        return GRUEN, text
    return GELB, text


def schaetzungen(trend):
    if trend is None or trend.empty or "30daysAgo" not in trend:
        return GRAU, "kein Schätzungstrend"
    teile, aend = [], []
    for zeile, name in (("0y", "lfd. Jahr"), ("+1y", "nächstes Jahr")):
        if zeile in trend.index and trend.loc[zeile, "30daysAgo"]:
            d = (trend.loc[zeile, "current"] / trend.loc[zeile, "30daysAgo"] - 1) * 100
            aend.append(d)
            teile.append(f"{name} {_p(d, 1)} %")
    if not aend:
        return GRAU, "kein Schätzungstrend"
    text = ", ".join(teile) + " in 30 Tagen"
    if min(aend) <= -5:
        return ROT, text
    if all(d > 0 for d in aend):
        return GRUEN, text + (" (stark)" if min(aend) >= 5 else "")
    return GELB, text


def jahresgewinn(gewinne):
    """Bereinigter Gewinn der letzten vier Quartale gegen die beiden Vorjahre (wie die Quartale)."""
    eps = gewinne["eps"].dropna()
    if len(eps) < 12:
        return GRAU, "zu wenige Quartale"
    summe = eps.rolling(4).sum().dropna()
    j = [summe.iloc[-9], summe.iloc[-5], summe.iloc[-1]]
    text = " → ".join(f"{_p(x, 2, False)} $" for x in j) + " (je vier Quartale)"
    if j[2] < j[1]:
        return ROT, text + ", fällt"
    neu_hoch = j[2] >= summe.max()
    wachstum = (j[2] / j[1] - 1) * 100 if j[1] > 0 else np.nan
    if neu_hoch and wachstum >= 20:
        return GRUEN, text + f", {_p(wachstum)} %, Mehrjahreshoch"
    return GELB, text


def code33(gewinne, sec):
    """Gewinn, Umsatz und Marge beschleunigen sich drei Quartale in Folge gleichzeitig."""
    if sec is None or sec.empty:
        return False
    g_eps = _wachstum(gewinne["eps"]).to_numpy()
    g_ums = _wachstum(sec["umsatz"].dropna()).to_numpy()
    m = _marge(sec).to_numpy()
    return _steigt(g_eps, 3) and _steigt(g_ums, 3) and _steigt(m, 3)


def gewinnqualitaet(qualitaet):
    """Liegt der GAAP-Gewinn in 2 der letzten 4 Quartale unter der Hälfte des bereinigten?"""
    q = qualitaet.dropna() if qualitaet is not None else pd.DataFrame()
    if q.empty:
        return None
    schwach = int(((q["bereinigt"] > 0) & (q["gaap"] < 0.5 * q["bereinigt"])).tail(4).sum())
    return schwach >= 2


def ampeln(daten):
    gew, sec = daten["gewinne"], daten.get("sec")
    punkte = {
        "Quartalsgewinn zum Vorjahr": quartalsgewinn(gew),
        "Beschleunigung Gewinn": beschleunigung(gew),
        "Umsatz": umsatz(sec),
        "Marge": marge(sec),
        "Überraschung": ueberraschung(gew),
        "Schätzungen (30 Tage)": schaetzungen(daten.get("trend")),
        "Jahresgewinn": jahresgewinn(gew),
    }
    zeichen = []
    if code33(gew, sec):
        zeichen.append("Code 33")
    if gewinnqualitaet(daten.get("qualitaet")):
        zeichen.append("Gewinnqualität prüfen (GAAP unter der Hälfte des bereinigten Gewinns)")
    return {"punkte": punkte, "zeichen": zeichen}


# ── S und I nach CAN SLIM (Schritt 7, 04.11.2026) – Zeichen neben den sieben Prüfpunkten, nicht in deren Zählung ──
def angebot(tv):
    """S – Angebot und Nachfrage (O'Neil): frei handelbare Aktien und Rückkäufe (TradingView, daten/tv/revier.csv).
    grün: Rückkauf (Aktienzahl sinkt); rot: Verwässerung über 2 % (Aktienzahl steigt); sonst gelb."""
    if tv is None:
        return ("grau", "keine Daten (TradingView führt den Titel nicht im Revier)")
    try:
        ges, frei, rk = (float(tv.get(k)) if tv.get(k) == tv.get(k) and tv.get(k) is not None else None
                         for k in ("total_shares_outstanding", "float_shares_outstanding", "share_buyback_ratio_fq"))
    except (TypeError, ValueError):
        return ("grau", "keine Daten")
    teile = []
    if ges:
        teile.append(f"{ges / 1e6:,.0f} Mio. Aktien".replace(",", "."))
    if ges and frei:
        teile.append(f"frei handelbar {frei / ges * 100:.0f} %")
    if rk is None:
        return ("grau" if not teile else "gelb", " · ".join(teile + ["Rückkäufe unbekannt"]))
    teile.append(f"Rückkauf {rk:+.1f} % der Aktien".replace(".", ",") if rk else "Aktienzahl unverändert")
    ampel = "grün" if rk > 0 else "rot" if rk < -2 else "gelb"
    if rk < 0:
        teile[-1] = f"Verwässerung {-rk:.1f} %".replace(".", ",")
    return (ampel, " · ".join(teile) + " (O'Neil: Rückkäufe verknappen das Angebot)")


def institutionen(df):
    """I – institutionelle Förderung (O'Neil): ein Anteil von Fonds, der zunimmt. Yahoo: Anteil der Institutionen und
    mittlere Veränderung der zehn größten Halter im letzten Quartal (13F). grün: 20–90 % und die Großen stocken auf;
    rot: die Großen bauen ab (mittlere Veränderung unter −2 %); über 90 % gelb (überbesetzt)."""
    if df is None or not len(df):
        return ("grau", "keine Daten (kommt mit dem nächsten Laden der Fundamentdaten)")
    z = df.iloc[0]
    anteil = z.get("anteil")
    aend = z.get("aenderung")
    anteil = float(anteil) * 100 if anteil == anteil and anteil is not None else None
    aend = float(aend) * 100 if aend == aend and aend is not None else None
    teile = [f"Institutionen halten {anteil:.0f} %" if anteil is not None else "Anteil unbekannt"]
    if aend is not None:
        teile.append(f"die 10 größten {'stocken auf' if aend > 0 else 'bauen ab'} ({aend:+.1f} % im Quartal)".replace(".", ","))
    if anteil is None:
        ampel = "grau"
    elif aend is not None and aend < -2:
        ampel = "rot"
    elif anteil > 90:
        ampel, teile[0] = "gelb", teile[0] + " – überbesetzt"
    elif 20 <= anteil <= 90 and (aend is None or aend > 0):
        ampel = "grün"
    else:
        ampel = "gelb"
    return (ampel, " · ".join(teile))
