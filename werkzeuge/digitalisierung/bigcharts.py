"""Digitalisierung von BigCharts-Charts aus Minervinis Buch (Tages- und Wochencharts).
Aufbau: grauer Kopf (Kürzel, Daily/Weekly, Datum des letzten Balkens), Kursfeld mit Achse rechts (linear oder
logarithmisch), Volumenfeld darunter (linear, „Millions“), Monats- bzw. Jahresbeschriftung unter dem Volumen."""
import re
import numpy as np, pandas as pd, cv2, pytesseract
import pandas_market_calendars as mcal
import digitalisieren as d

NYSE = mcal.get_calendar("NYSE")


def zeilen_linien(g, x0, x1, schwelle, anteil):
    r = (g[:, x0:x1] < schwelle).mean(1)
    ys = np.where(r > anteil)[0]
    return [int(np.mean(k)) for k in np.split(ys, np.where(np.diff(ys) > 2)[0] + 1)] if len(ys) else []


def spalten_linien(g, y0, y1, schwelle, anteil):
    r = (g[y0:y1] < schwelle).mean(0)
    xs = np.where(r > anteil)[0]
    return [int(np.mean(k)) for k in np.split(xs, np.where(np.diff(xs) > 2)[0] + 1)] if len(xs) else []


def struktur(c):
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    H, W = g.shape
    rand = lambda ys: [y for y in ys if 12 < y < H - 12]                 # Außenrahmen der Tafel zählt nicht
    dunkel = rand(zeilen_linien(g, int(W * .1), int(W * .8), 120, 0.8))  # Unterkanten von Kurs- und Volumenfeld
    hell = rand(zeilen_linien(g, int(W * .1), int(W * .8), 200, 0.8))
    if len(dunkel) < 2:
        raise ValueError("Kurs- und Volumenfeld nicht gefunden")
    p_unten, v_unten = dunkel[0], dunkel[-1]
    oben = [y for y in hell if 15 < y < p_unten - 20]
    p_oben = oben[0]
    v_oben = [y for y in hell if p_unten + 15 < y < v_unten - 10][0]
    senk = [x for x in spalten_linien(g, p_oben + 3, p_unten - 3, 200, 0.85) if 12 < x < W - 12]   # ohne Außenrahmen
    x0, x1 = senk[0], senk[-1]
    gitter = [x for x in senk if x0 + 4 < x < x1 - 4]
    return dict(g=g, p_oben=p_oben, p_unten=p_unten, v_oben=v_oben, v_unten=v_unten, x0=x0, x1=x1, gitter=gitter)


def kopf(c, s):
    hk = max(s["p_oben"], 32)                     # Kopfzeile (bei manchen Tafeln liegt die erste Gitterlinie höher)
    t = pytesseract.image_to_string(cv2.resize(c[:hk, :], None, fx=3, fy=3), config="--psm 6")
    # Datum rechts im Kopf: eigener Lesedurchgang nur mit Ziffern und Schrägstrich (sicherer als im ganzen Kopf)
    W = c.shape[1]
    r = cv2.resize(c[0:hk, int(W * 0.75):], None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    t2 = pytesseract.image_to_string(r, config="--psm 7 -c tessedit_char_whitelist=0123456789/").strip()
    t = t + "\n" + t2
    tk = re.search(r"([A-Z0-9]{1,5})\s+(Da[il1]+y|[HW]ee[kh]?[l1]y|Month[l1]y)", t)
    t = re.sub(r"(?<=\d)[SO]|[SO](?=\d)", lambda m_: {"S": "5", "O": "0"}[m_.group(0)], t)
    dt = (re.search(r"\b(\d{1,2})/(\d{2})/(\d{2})\b", t) or re.search(r"\b(\d{1,2})[/7|lI](\d{2})[/7|lI](\d{2})\b", t)
          or re.search(r"\b(\d{1,2})(\d{2})/(\d{2})\b", t))
    w = tk.group(2) if tk else ""
    art = "Woche" if re.search(r"[HW]ee", t) else "Monat" if "Month" in t else "Tag"
    ende = None
    if dt:
        m, tag, j = map(int, dt.groups())
        if 1 <= m <= 12 and 1 <= tag <= 31:
            ende = pd.Timestamp(1900 + j if j > 30 else 2000 + j, m, tag)
    return (tk.group(1) if tk else "?"), art, ende


def achse(c, x0, x1, y0, y1):
    """Preisachse: linear oder logarithmisch, je nachdem, was die Beschriftungen besser trifft (robust, RANSAC)."""
    lab = d.ocr_zahlen(c, x0, x1, y0, y1, faktor=3)
    if len(lab) < 4:
        raise ValueError("zu wenige Achsenbeschriftungen")
    p = np.array([v for v, _, _ in lab]); ys = np.array([y for _, y, _ in lab])
    beste = None
    for art, f in (("linear", lambda v: v), ("log", np.log)):
        if art == "log" and (p <= 0).any():
            continue
        fp = f(p)
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                if fp[i] == fp[j]:
                    continue
                m_ = (ys[j] - ys[i]) / (fp[j] - fp[i])
                if m_ >= 0:
                    continue
                res = np.abs(ys - (ys[i] + m_ * (fp - fp[i])))
                drin = res < 2.5
                if beste is None or (drin.sum(), -res[drin].mean()) > (beste[0].sum(), -beste[3]):
                    beste = (drin, art, None, res[drin].mean())
    drin, art, _, _ = beste
    if drin.sum() < 4:
        raise ValueError("Achse nicht eindeutig")
    f = (lambda v: v) if art == "linear" else np.log
    a = np.polyfit(f(p[drin]), ys[drin], 1)
    rest = float(np.abs(ys[drin] - np.polyval(a, f(p[drin]))).max())
    inv = (lambda y: (y - a[1]) / a[0]) if art == "linear" else (lambda y: float(np.exp((y - a[1]) / a[0])))
    return inv, art, rest, int(drin.sum())


def achsen_art(c, s):
    """Beschriftung unter dem Volumen: nur zweistellige Jahreszahlen -> Gitter je Jahr, sonst je Monat."""
    r = c[s["v_unten"] + 2:min(c.shape[0], s["v_unten"] + 32), s["x0"]:s["x1"]]
    t = pytesseract.image_to_string(cv2.resize(r, None, fx=3, fy=3), config="--psm 6")
    tok = re.findall(r"[A-Za-z]+|\d+", t)
    jahre = sum(1 for x in tok if re.fullmatch(r"\d{2}", x))
    monate = sum(1 for x in tok if x.isalpha())
    return "Jahre" if jahre >= 3 and jahre > monate else "Monate"


MONATE = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10,
          "nov": 11, "dec": 12}


def monate_lesen(c, s):
    """Monatsnamen unter dem Volumen mit ihrer Lage: Liste (monat, x)."""
    y0 = s["v_unten"] + 2
    r = c[y0:min(c.shape[0], y0 + 30), :]
    big = cv2.resize(r, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    dd = pytesseract.image_to_data(big, config="--psm 11", output_type=pytesseract.Output.DICT)
    aus = []
    for t, l, w in zip(dd["text"], dd["left"], dd["width"]):
        if re.fullmatch(r"'?\d{2}", t.strip()):          # Jahreszahl an der Januar-Linie („10“ = Januar 2010)
            j = int(t.strip()[-2:])
            aus.append((1, (l + w / 2) / 3, 1900 + j if j > 30 else 2000 + j))
            continue
        k = re.sub(r"[^a-z]", "", t.lower().replace("fl", "a").replace("0", "o"))[:3]
        if k in MONATE:
            aus.append((MONATE[k], (l + w / 2) / 3, None))
    return aus


def ende_aus_monaten(c, s, wx, jahr, art):
    """Ohne Datum im Kopf: Monatsnamen unter den Gitterlinien + Jahr aus der Bildunterschrift. Der letzte
    beschriftete Monat liegt im Jahr der Unterschrift oder kurz davor."""
    mon = monate_lesen(c, s)
    if not mon or jahr is None:
        raise ValueError("kein Datum im Kopf und keine Monatsbeschriftung")
    m_letzt, x_letzt, j_letzt = max(mon, key=lambda v: v[1])
    jahre = [(x_, j_) for _, x_, j_ in mon if j_]
    if j_letzt:
        jahr = j_letzt
    elif jahre:                                   # Monat rechts einer Jahreszahl gehört zu deren Jahr
        links = [j_ for x_, j_ in jahre if x_ < x_letzt]
        if links:
            jahr = max(links)
    # Gitterlinie zum letzten Monatsnamen
    g = min(s["gitter"], key=lambda gx: abs(gx - x_letzt)) if s["gitter"] else x_letzt
    i_g = int(np.argmin(np.abs(np.array(wx) - g)))
    nach = len(wx) - 1 - i_g                      # Balken nach dem ersten Tag dieses Monats
    for j in (jahr, jahr - 1):
        tage = NYSE.valid_days(pd.Timestamp(j, m_letzt, 1), pd.Timestamp(j, m_letzt, 1) + pd.Timedelta(days=200)).tz_localize(None)
        if art == "Woche":
            tage = pd.DatetimeIndex(sorted(set(t - pd.Timedelta(days=t.dayofweek) for t in tage)))
        if len(tage) > nach:
            return tage[nach] if j == jahr or True else None
    raise ValueError("Datum nicht bestimmbar")


def handelstage(bis, n, art):
    """Die letzten n Handelstage (bzw. Wochen, Montag) bis einschließlich `bis`."""
    tage = NYSE.valid_days(bis - pd.Timedelta(days=int(n * (1.6 if art == "Tag" else 8)) + 60), bis).tz_localize(None)
    if art == "Woche":
        tage = pd.DatetimeIndex(sorted(set(t - pd.Timedelta(days=t.dayofweek) for t in tage)))
    return tage


def daten_zuordnen(wx, sp, gitter, ende, art, spanne=None):
    """Datum je Balken. Grundlage: das Datum im Kopf (letzter Balken). Feinabgleich mit den Gitterlinien:
    sie stehen am Monatsanfang (Tageschart) bzw. am Jahres- oder Quartalsanfang (Wochenchart); gesucht ist die
    Verschiebung, bei der die Gitterlinien am gleichmäßigsten vor dem ersten Balken des neuen Abschnitts liegen."""
    n = len(wx)
    alle = handelstage(ende + pd.Timedelta(days=40), n + 60, art)
    i_ende = int(np.searchsorted(alle, ende, side="right")) - 1
    beste = None
    if spanne is None:
        spanne = 5 if art == "Tag" else 1         # Wochen: ein Monat Versatz passt auch ans Gitter – nur ±1
    for k in range(-spanne, spanne + 1):
        e = i_ende + k
        if e - n + 1 < 0 or e >= len(alle):
            continue
        tage = alle[e - n + 1:e + 1]
        for teil in ("M", "Q", "Y"):
            if art == "Tag" and teil != "M":
                continue
            per = tage.to_period(teil)
            neu = np.where(per[1:] != per[:-1])[0] + 1          # Index des ersten Balkens eines neuen Abschnitts
            if len(neu) < 2 or len(gitter) < 2:
                continue
            xs_neu = np.array([wx[i] for i in neu])
            ab = [np.min(np.abs(xs_neu - g)) for g in gitter]
            treffer = sum(a <= 0.7 * sp for a in ab)
            if art == "Tag":
                # BigCharts setzt die Monatslinie zwischen den letzten Tag des Vormonats und den ersten des neuen
                # Monats: im Mittel einen halben Balken vor dem ersten Balken (an CRUS, MELI, NFLX geprüft)
                vz = np.median([(g - xs_neu[np.argmin(np.abs(xs_neu - g))]) / sp for g in gitter])
                wert = (-abs(vz + 0.5) - 0.05 * abs(k), 0, 0)
            else:
                wert = (treffer - abs(len(neu) - len(gitter)) * 0.5, -np.mean(ab), -abs(k))
            if beste is None or wert > beste[0]:
                beste = (wert, k, tage, teil)
    if beste is None:
        return alle[i_ende - n + 1:i_ende + 1], 0, None
    return beste[2], beste[1], beste[3]


def lesen(c, jahr=None):
    s = struktur(c)
    tk, art, ende = kopf(c, s)
    preis, p_art, p_rest, p_n = achse(c, s["x1"] + 2, c.shape[1], s["p_oben"] - 10, s["p_unten"] + 10)
    try:
        vol, _, v_rest, _ = achse(c, s["x1"] + 2, c.shape[1], s["v_oben"] - 10, s["v_unten"] + 10)
        v_echt = True
    except ValueError:                            # Volumenskala nicht lesbar: Balkenhöhe als Maß (nur Verhältnisse)
        vol, v_echt = (lambda y: (s["v_unten"] - y) / 1e2), False
    sm, rm = d.masken(c)
    m = sm | rm
    # Volumenbalken: jede Spalte, die direkt über der Grundlinie Tinte hat (auch winzige Balken)
    band = m[s["v_unten"] - 6:s["v_unten"] - 2, s["x0"] + 2:s["x1"] - 1].sum(0) >= 3
    xs = np.where(band)[0] + s["x0"] + 2
    wx = [int(round(k.mean())) for k in np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)] if len(xs) else []
    # letzter Balken: die rechteste Spalte mit Kursbalken (das Volumen am rechten Rand ist manchmal kaum sichtbar)
    pk = d.senkrecht_profil(m[s["p_oben"] + 2:s["p_unten"] - 2], 3)
    spitzen = pk[s["x0"] + 2:s["x1"] - 1]
    if spitzen.max() > 0:
        rechts = s["x0"] + 2 + int(np.where(spitzen > 0.15 * np.percentile(spitzen[spitzen > 0], 90))[0].max())
        if not wx or rechts > wx[-1]:
            wx = sorted(set(wx + [rechts]))
    if art == "Tag" and len(s["gitter"]) >= 3:
        # Gitterlinien am Monatsanfang: im Mittel 21 Handelstage je Monat. Das gibt den Balkenabstand vor –
        # aus dem Volumen allein verschätzt er sich, wenn Balken fehlen oder verschmelzen
        gap = float(np.median(np.diff(s["gitter"])))
        dv = np.diff(wx); spv = float(np.median(dv[dv > 1])) if (dv > 1).any() else gap / 21
        teiler = min((1.0, 5.0, 21.0), key=lambda t: abs(np.log(gap / t / spv)))   # Gitter je Tag, Woche oder Monat
        spanne = 0 if teiler < 21 else None       # Tages-/Wochengitter passt bei jeder Verschiebung: dann gilt das Kopfdatum
        sp0 = gap / teiler
        a0 = wx[-1] if wx else s["x1"] - 2
        wx = sorted(set(np.arange(a0, s["x0"] + 1, -sp0).astype(int)))
    elif art == "Woche" and len(s["gitter"]) >= 2 and len(wx) >= 5:
        # Wochenchart: Gitter je Monat (≈ 4,35 Wochen), Quartal (13) oder Jahr (52) – der Teiler, der zum
        # Volumenabstand passt
        gap = float(np.median(np.diff(s["gitter"])))
        if achsen_art(c, s) == "Jahre":
            teiler = 52.0
        else:
            dv = np.diff(wx); spv = float(np.median(dv[dv > 2])) if (dv > 2).any() else gap / 13
            teiler = min((4.35, 13.0), key=lambda t: abs(np.log(gap / t / spv)))
        sp0 = gap / teiler
        # Raster vom letzten Balken rückwärts bis zum linken Rand (frühe Volumenbalken sind oft kaum sichtbar)
        wx = sorted(set(np.arange(wx[-1], s["x0"] + 1, -sp0).astype(int)))
    else:
        sp0 = None
    if art != "Tag" or len(s["gitter"]) < 3:
        spanne = None
    profil = d.senkrecht_profil(m[s["p_oben"] + 2:s["v_unten"] - 2], 4)
    wx, sp = d.wochenraster(wx, profil, s["x0"] + 2, s["x1"] - 1, sp_vorgabe=sp0)
    weg = d.textmaske(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"]) | d.kastenmaske(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"]) \
        | d.linienmaske(c, s["x0"] + 2, s["x1"] - 2, s["p_oben"] + 2, s["p_unten"] - 2, sp)
    kb, versatz = d.kursbalken(c, wx, s["p_oben"] + 2, s["p_unten"] - 2, weg)
    vh = d.volumen(c, wx, s["v_unten"] - 1, s["v_oben"] + 1)
    quelle = "Kopf"
    if ende is None:
        ende = ende_aus_monaten(c, s, wx, jahr, art)
        quelle = "Monatsnamen + Jahr der Bildunterschrift"
    tage, k, teil = daten_zuordnen(wx, sp, s["gitter"], ende, art, spanne)
    zeilen = []
    for x, b, v, t in zip(wx, kb, vh, tage):
        if b is None:
            continue
        zeilen.append({"Datum": t, "x": x, "High": preis(b[0]), "Low": preis(b[1]), "Close": preis(b[2]),
                       "Volume": max(0.0, vol(s["v_unten"] - v)) * 1e6})
    df = pd.DataFrame(zeilen)
    if len(df):
        df = d.bereinigen(df, grenze=0.2 if art == "Woche" else 0.12, alle=pd.DatetimeIndex(tage))
    info = dict(ticker=tk, art=art, ende=str(ende.date()), datum_aus=quelle, achse=p_art, achse_rest_px=round(p_rest, 2), achse_n=p_n,
                volumen_skala=v_echt, balken=len(wx), px_je_balken=round(sp, 2), verschiebung=k, gitter=teil, gelesen=int(sum(b is not None for b in kb)))
    return df, info, (s, wx, kb, weg)
