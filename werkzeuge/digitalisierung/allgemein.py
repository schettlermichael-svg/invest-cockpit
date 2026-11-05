"""Digitalisierung von Tagescharts anderer Anbieter aus Minervinis Buch (StockCharts und die Charts ohne Kopfdatum
mit Achse rechts und Volumen „Clipped at RMS“). Gemeinsamer Weg für beide:
  Grundlinie des Volumens = die Zeile, an der die meisten Volumenbalken enden;
  Datumsachse = Tageszahlen (Montage) und Monatsnamen unter der Grundlinie, Jahr aus „Jan 2007“ bzw. Kopfdatum bzw.
  Bildunterschrift; jede gelesene Tageszahl wird ein Datum, daraus Handelstag-Index -> x (robuste Gerade);
  daraus die x-Lage jedes Handelstags = Balkenraster (das Volumen allein verschätzt sich bei fehlenden Balken);
  Preisachse rechts (linear oder log, RANSAC wie bei BigCharts), Kursbalken wie im O'Neil-Digitalisierer."""
import re
import numpy as np, pandas as pd, cv2, pytesseract
import digitalisieren as d
import bigcharts as b

MONATE = b.MONATE


def worte(c, f=3, psm=11, cfg=""):
    big = cv2.resize(c, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    dd = pytesseract.image_to_data(big, config=f"--psm {psm} {cfg}", output_type=pytesseract.Output.DICT)
    return [dict(t=t.strip(), x=(l + w / 2) / f, l=l / f, r=(l + w) / f, y=(tp + h / 2) / f, h=h / f, cf=float(cf))
            for t, l, tp, w, h, cf in zip(dd["text"], dd["left"], dd["top"], dd["width"], dd["height"], dd["conf"])
            if t.strip()]


def grundlinie(g, y_von, x0, x1):
    """Zeile, an der die meisten Balken nach unten enden (dunkel darüber, hell darunter)."""
    dunkel = g[:, x0:x1] < 170
    ende = np.zeros_like(dunkel)
    ende[4:-3] = dunkel[4:-3] & dunkel[:-7] & ~dunkel[7:]      # Balken (auch 4 Zeilen darüber dunkel), darunter hell
    z = ende.sum(1).astype(float)
    z[:y_von] = 0
    return int(np.argmax(z)), z


def preis_rechts(c, y0, y1):
    """Linke Kante der Preisbeschriftung rechts (= rechter Rand des Kursfelds)."""
    W = c.shape[1]
    x_von = int(W * 0.8)
    ws = [w for f, psm in ((3, 11), (2, 11), (3, 6)) for w in worte(c[y0:y1, x_von:], f=f, psm=psm)
          if re.fullmatch(r"\d+(?:[.,]\d+)?", w["t"].replace(",", "").lstrip("-—"))]
    if len(ws) < 3:
        raise ValueError("Preisachse rechts nicht gefunden")
    return x_von + float(np.median([w["l"] for w in ws]))


def monat_name(t):
    """Monatskürzel auch bei Lesefehlern (Aua, Sen, 0ct): bestes Kürzel mit mindestens 2 von 3 Buchstaben."""
    t = t.lower().replace("0", "o")[:3]
    if len(t) < 3:
        return None
    best = max(MONATE, key=lambda m: sum(a == b_ for a, b_ in zip(m, t)))
    return best if sum(a == b_ for a, b_ in zip(best, t)) >= 2 and best[0] == t[0] else None


def _band_worte(band, f, cfg=""):
    g = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    _, bw = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bw = cv2.copyMakeBorder(bw, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255)
    dd = pytesseract.image_to_data(bw, config=f"--psm 11 {cfg}", output_type=pytesseract.Output.DICT)
    return [dict(t=t.strip(), x=(l - 12 + w / 2) / f, l=(l - 12) / f, r=(l - 12 + w) / f)
            for t, l, w in zip(dd["text"], dd["left"], dd["width"]) if t.strip()]


def zahlen_einzeln(band, x0):
    """Tageszahlen einzeln lesen: die Zeile an Spaltenlücken in Gruppen zerlegen (zwischen zwei Zahlen ist mehr
    Platz als zwischen ihren Ziffern) und jede Gruppe für sich mit Ziffern-Erkennung lesen."""
    g = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
    tinte = (g < 150).sum(0) > 0
    aus, start, leer = [], None, 0
    gruppen = []
    for i, t in enumerate(list(tinte) + [False] * 4):
        if t:
            if start is None:
                start = i
            leer, ende = 0, i
        elif start is not None:
            leer += 1
            if leer >= 4:
                gruppen.append((start, ende + 1))
                start = None
    gruppen = [(a, b_) for a, b_ in gruppen if 2 <= b_ - a <= 22]
    if not gruppen:
        return aus
    # Gruppen mit breiten Lücken neu zusammensetzen und als eine Zeile lesen (Tesseract liest Zeilen besser als
    # einzelne Zahlen); jedes gelesene Wort wird über seine Lage der Gruppe zugeordnet
    hg = g.shape[0]
    teile, lage, pos = [], [], 0
    for a, b_ in gruppen:
        st = g[:, max(0, a - 1):b_ + 1]
        teile += [st, np.full((hg, 10), 235, np.uint8)]
        lage.append((pos, pos + st.shape[1], (a + b_) / 2))
        pos += st.shape[1] + 10
    zeile = np.hstack(teile)
    f = 5
    big = cv2.resize(zeile, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    big = np.where(big < 150, 0, 255).astype(np.uint8)          # harte Schwelle liest diese kleine Schrift am besten
    big = cv2.copyMakeBorder(big, 25, 25, 25, 25, cv2.BORDER_CONSTANT, value=255)
    werte = [None] * len(lage)
    dd = pytesseract.image_to_data(big, config="--psm 6", output_type=pytesseract.Output.DICT)
    for t, l, w in zip(dd["text"], dd["left"], dd["width"]):
        t = t.strip().replace("§", "5").rstrip(".,:")
        if not t.isdigit() or len(t) > 2 or not 1 <= int(t) <= 31:
            continue
        mitte = ((l - 25) + w / 2) / f
        k = [i for i, (p0, p1, _) in enumerate(lage) if p0 - 2 <= mitte <= p1 + 2]
        if len(k) == 1:
            werte[k[0]] = int(t)
    # jede Gruppe ist eine Marke (Lage sicher), der Wert nur, wenn gelesen
    return [(w_, x0 + l_[2]) for w_, l_ in zip(werte, lage)]


def schriftzeilen(c, y0, y1, x0, x1):
    """Textzeilen im Streifen unter dem Volumen: (oben, unten) je Zeile mit Tinte, mindestens 5 Pixel hoch."""
    g = cv2.cvtColor(c[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    zeile = (g < 140).sum(1) > 3
    aus, start = [], None
    for i, z in enumerate(list(zeile) + [False]):
        if z and start is None:
            start = i
        elif not z and start is not None:
            if i - start >= 16:                  # zwei Zeilen berühren sich: an der dünnsten Stelle trennen
                tinte = (g[start:i] < 140).sum(1)
                m = start + 5 + int(np.argmin(tinte[5:-5]))
                aus += [(y0 + start, y0 + m), (y0 + m + 1, y0 + i)]
            elif i - start >= 5:
                aus.append((y0 + start, y0 + i))
            start = None
    return aus


def tageszahlen(c, y0, y1, x0, x1):
    """Beschriftung der Zeitachse: Liste (art, wert, x). art: 'tag' (1–31), 'monat' (1–12), 'jahr'.
    Jede Schriftzeile wird für sich gelesen (Tageszahlen nur mit Ziffern), das ist deutlich sicherer."""
    aus = []
    for k, (a, b_) in enumerate(schriftzeilen(c, y0, y1, x0, x1)[:3]):
        band = c[a:b_ + 1, x0:x1]
        for wert, xx in zahlen_einzeln(band, x0):
            aus.append(("tag", wert if wert is not None else -1, xx, k))
        for w in _band_worte(band, 3):
            for teil in re.findall(r"[A-Za-z0-9]+", w["t"]):
                if re.fullmatch(r"\d{4}", teil) and 1950 < int(teil) < 2030:
                    aus.append(("jahr", int(teil), x0 + w["x"], k))
                elif re.fullmatch(r"'?\d{2}", teil) and len(w["t"]) <= 3 and k > 0:
                    pass
                elif not teil.isdigit() and monat_name(teil):
                    # „Jun5“: Monat steht links, die Tageszahl gehört zur Marke
                    aus.append(("monat", MONATE[monat_name(teil)], x0 + (w["l"] + 8 if teil != w["t"] else w["x"]), k))
    # Tageszahlen nur aus der Zeile mit den meisten Tageszahlen (sonst landen Teile der Monatszeile darin)
    tz = [m for m in aus if m[0] == "tag" and m[1] > 0]
    if tz:
        zeile = max(set(m[3] for m in tz), key=lambda z: sum(m[3] == z for m in tz))
        # Gruppen ohne gelesenen Wert gibt es auch in der Monatszeile: nur die der Tageszeile behalten
        aus = [m for m in aus if m[0] != "tag" or m[3] == zeile]
    return aus


def zeitachse(marken, x_min, x_max, jahre, ende_kopf=None):
    """Datum je Balken aus der Zeitachse. Gesucht werden das Datum der rechtesten Tagesmarke und der Balkenabstand,
    bei denen die meisten gelesenen Tageszahlen, Monatsnamen und Jahreszahlen stimmen – Lesefehler einzelner Marken
    stören so nicht. Kandidaten: alle Handelstage in den Jahren der Bildunterschrift (±1)."""
    tg = sorted([m for m in marken if m[0] == "tag"], key=lambda m: m[2])
    if len(tg) < 5:
        raise ValueError("zu wenige Tagesmarken")
    xs = np.array([m[2] for m in tg]); ws = np.array([m[1] for m in tg])
    woche = float(np.median(np.diff(xs)))
    mon = [m for m in marken if m[0] == "monat"]; jr = [m for m in marken if m[0] == "jahr"]
    j0, j1 = min(jahre) - 1, max(jahre) + 1
    ergebnisse = []
    for name, kal in (("Handelstage", b.NYSE.valid_days(pd.Timestamp(j0 - 1, 1, 1), pd.Timestamp(j1 + 1, 12, 31)).tz_localize(None)),
                      ("Werktage", pd.bdate_range(pd.Timestamp(j0 - 1, 1, 1), pd.Timestamp(j1 + 1, 12, 31)))):
        try:
            ergebnisse.append(_zeitachse_kal(kal, xs, ws, woche, mon, jr, j0, j1, x_min, x_max, ende_kopf) + (name,))
        except ValueError:
            pass
    if not ergebnisse:
        raise ValueError("Zeitachse nicht eindeutig")
    # Kalender mit der besseren Übereinstimmung (manche Anbieter lassen Feiertage als leere Stelle stehen)
    wert, tage, wx, sp, n_ok, kopf, kal_name = max(ergebnisse, key=lambda e: (e[0], e[4]))
    return tage, wx, sp, n_ok, len(tg), kal_name, kopf


def _zeitachse_kal(kal, xs, ws, woche, mon, jr, j0, j1, x_min, x_max, ende_kopf):
    k_tag, k_mon, k_jahr = kal.day.to_numpy(), kal.month.to_numpy(), kal.year.to_numpy()
    woche_nr = (kal - pd.to_timedelta(kal.dayofweek, unit="D")).to_numpy()
    wstart = np.r_[True, woche_nr[1:] != woche_nr[:-1]]          # erster Handelstag (bzw. Werktag) der Woche
    x_r = xs[-1]
    n = len(kal)
    beste = None

    def treffer_von(i):
        """je Marke: Index des passenden Handelstags (Toleranz ±1 Tag, Beschriftung sitzt nicht genau mittig), sonst -1"""
        hit = np.full(len(i), -1)
        for d_ in (0, -1, 1):
            j = np.clip(i + d_, 0, n - 1)
            neu_ = (hit < 0) & (k_tag[j] == ws)
            hit[neu_] = j[neu_]
        return hit

    for sp in woche / 5 * np.linspace(0.94, 1.06, 49):
        ab = np.round((x_r - xs) / sp).astype(int)                     # Handelstage vor der rechtesten Marke
        abm = np.array([int(round((x_r - m[2]) / sp)) for m in mon], int)
        abj = np.array([int(round((x_r - m[2]) / sp)) for m in jr], int)
        for r in np.where((k_jahr >= j0) & (k_jahr <= j1))[0]:
            i = r - ab
            if i.min() < 1:
                continue
            hit = treffer_von(i)
            treffer = int((hit >= 0).sum())
            if treffer < 2:
                continue
            wert = treffer + int((hit == i).sum()) + 0.5 * int(wstart[i].sum())   # Marken stehen am Wochenanfang
            for mm, a_ in zip(mon, abm):                                # Monatsname steht unter den ersten Tagen
                ii = r - a_
                fenster = range(max(0, ii - 4), min(n, ii + 5))
                if any(k_mon[q] == mm[1] and k_tag[q] <= 10 for q in fenster):
                    wert += 6
            for mm, a_ in zip(jr, abj):
                ii = r - a_
                if any(k_jahr[q] == mm[1] for q in range(max(0, ii - 4), min(n, ii + 8))):
                    wert += 10
            if beste is None or wert > beste[0]:
                beste = (wert, treffer, sp, r, hit)
    if beste is None:
        raise ValueError("Zeitachse nicht eindeutig")
    wert, treffer, sp, r, hit = beste
    # Feinabgleich: Gerade Handelstag-Index -> x durch die stimmenden Marken, zweimal nachgeschärft
    ok = hit >= 0
    for _ in range(2):
        a = np.polyfit(hit[ok].astype(float), xs[ok], 1)
        i = np.round((xs - a[1]) / a[0]).astype(int)
        hit = treffer_von(np.clip(i, 1, n - 2))
        ok = hit >= 0
    a = np.polyfit(hit[ok].astype(float), xs[ok], 1)
    i_end = np.clip(np.round((xs - a[1]) / a[0]).astype(int), 0, n - 1)
    guete = int((k_tag[i_end] == ws).sum()) + int(wstart[i_end].sum())   # Gegenprobe: genaue Tage + Wochenanfänge
    x_alle = np.polyval(a, np.arange(n))
    drin = (x_alle >= x_min) & (x_alle <= x_max)
    tage, wx = kal[drin], x_alle[drin]
    if ende_kopf is not None and len(tage):
        # Kopfdatum (StockCharts) = Datum des letzten Balkens: nur als Gegenprobe, Abweichung wird gemeldet
        mo, tg_, jj = ende_kopf
        try:
            kopf = pd.Timestamp(jj or tage[-1].year, mo, tg_)
        except ValueError:
            kopf = None
        if kopf is not None and kopf > tage[-1] + pd.Timedelta(days=200):
            kopf = kopf - pd.DateOffset(years=1)
        ende_kopf = kopf
    return guete, tage, wx, float(a[0]), int(ok.sum()), ende_kopf


def volumen(c, wx, y_unten, y_oben):
    """Volumenbalken: von der Grundlinie nach oben, solange Tinte (Lücken bis 2 Pixel). Ohne Tinte an der
    Grundlinie: kleinster Wert (0,5 Pixel) statt 0 – ein Handelstag hat Volumen, der Balken ist nur zu klein."""
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    aus = []
    for x in wx:
        col = g[y_oben:y_unten + 1, max(0, x - 1):x + 2].min(1) < 185      # auch graue (abgeschnittene) Balken
        y, luecke, oben = len(col) - 1, 0, None
        while y >= 0:
            if col[y]:
                oben, luecke = y, 0
            else:
                luecke += 1
                if luecke > 2:
                    break
            y -= 1
        aus.append(float(len(col) - 1 - oben) + 1 if oben is not None else 0.5)
    return np.array(aus)


def rechteckmaske(c, x0, x1, y0, y1):
    """Eingefügte Kästen (EPS-Kästen, Legenden, Beschriftungen mit Rahmen) im Kursfeld: Inneres und Rand maskieren."""
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    H, W = g.shape
    m = np.zeros((H, W), bool)
    for th in (120, 170):
        bw = (g < th).astype(np.uint8) * 255
        kont, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for k in kont:
            x, y, w, h = cv2.boundingRect(k)
            if not (35 <= w <= 0.45 * (x1 - x0) and 22 <= h <= 0.5 * (y1 - y0)):
                continue
            ap = cv2.approxPolyDP(k, 0.03 * cv2.arcLength(k, True), True)
            if len(ap) == 4 and cv2.contourArea(k) > 0.8 * w * h:
                m[max(0, y - 2):y + h + 3, max(0, x - 2):x + w + 3] = True
    return m


def legendenmaske(c, x0, x1, y0, y1):
    """Legende oben links (StockCharts: „QSII (Daily) 1.63“, „MA(50) 0.98“ …): jede Textzeile dort maskieren."""
    H, W = c.shape[:2]
    m = np.zeros((H, W), bool)
    yb = y0 + int((y1 - y0) * 0.25)
    # Die Schrift ist zu klein für sichere Erkennung: die Legende hat bei StockCharts feste Lage (vier Zeilen oben links)
    m[y0:y0 + 62, x0:x0 + int(0.22 * W)] = True
    return m


def dezimal_faktor(c, x0, y0, y1):
    """Dezimalpunkte der Preisachse gehen beim Lesen oft verloren („2.9“ -> „29“). Zweiter Lesedurchgang mit
    harter Schwelle: steht dort eine Zahl mit Punkt, deren Zehnfaches als Beschriftung gelesen wurde, gilt Faktor 0,1."""
    st = cv2.cvtColor(c[y0:y1, x0:], cv2.COLOR_BGR2GRAY)
    ganz = set()
    punkt = set()
    for f in (2, 3):
        big = cv2.resize(st, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
        for th in (None, 160):
            im = big if th is None else np.where(big < th, 0, 255).astype(np.uint8)
            for t in pytesseract.image_to_string(im, config="--psm 6 -c tessedit_char_whitelist=0123456789.").split():
                if re.fullmatch(r"\d+\.\d", t):
                    punkt.add(round(float(t) * 10))
                elif re.fullmatch(r"\d{2,3}", t):
                    ganz.add(int(t))
    treffer = len(punkt & ganz)
    return 0.1 if treffer >= 2 else 1.0


def struktur(c):
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    H, W = g.shape
    hell = [y for y in b.zeilen_linien(g, int(W * .1), int(W * .8), 200, 0.7) if 12 < y < H - 12]
    # Volumenfeld oben: das Wort „Volume“ links
    vw = [w for f in (2, 3) for w in worte(c[:, :int(W * 0.35)], f=f, psm=11)
          if re.search(r"^vol|olum|clipp", w["t"].lower()) and w["y"] > H * 0.4]
    if vw:
        y_vol = min(vw, key=lambda w: w["y"])["y"]
    else:
        # Ersatz: die dünne helle Trennlinie zwischen Kurs- und Volumenfeld
        r = (g[:, int(W * .1):int(W * .8)] < 215).mean(1)
        kand = [y for y in range(int(H * .45), int(H * .85)) if r[y] > 0.65 and r[y - 3] < r[y] - 0.3 and r[y + 3] < r[y] - 0.3]
        if not kand:
            raise ValueError("Volumenfeld nicht gefunden")
        y_vol = max(kand, key=lambda y: r[y]) + 8
    trenn = [y for y in hell if y_vol - 25 < y < y_vol]
    p_unten = (max(trenn) - 3) if trenn else int(y_vol - 12)
    v_oben = int(y_vol + 8)
    oben = [y for y in hell if 15 < y < p_unten - 100]
    p_oben = (oben[0] + 3) if oben else 8
    x1 = int(preis_rechts(c, p_oben, p_unten)) - 4
    x0 = 8
    v_unten, _ = grundlinie(g, v_oben + 20, x0, x1)
    return dict(g=g, p_oben=p_oben, p_unten=p_unten, v_oben=v_oben, v_unten=v_unten, x0=x0, x1=x1)


def kopfdatum(c, s):
    """StockCharts: „21-Sep-1995“ oben links."""
    if s["p_oben"] < 25:
        return None
    t = pytesseract.image_to_string(cv2.resize(c[:s["p_oben"], :int(c.shape[1] * 0.4)], None, fx=3, fy=3), config="--psm 6")
    m = re.search(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", t)
    if m and m.group(2).lower() in MONATE:
        # Jahr nur, wenn plausibel (Lesefehler „1905“); sonst ergänzt die Zeitachse das Jahr
        j = int(m.group(3))
        return (MONATE[m.group(2).lower()], int(m.group(1)), j if 1960 < j < 2030 else None)
    return None


def _masken_hell(schwelle):
    """Dünne Balken sind kantengeglättet und grau statt schwarz: Schwarz-Schwelle anheben."""
    def masken(img):
        a_ = img.astype(int)
        B, G, R = a_[..., 0], a_[..., 1], a_[..., 2]
        schwarz = (R < schwelle) & (G < schwelle) & (B < schwelle) & (np.abs(R - G) < 40) & (np.abs(G - B) < 40)
        rotm = (R > 140) & (G < 110) & (B < 120) & (R - G > 70)
        return schwarz, rotm
    return masken


def lesen(c, jahr=None, schwelle=130):
    alt = d.masken
    d.masken = _masken_hell(schwelle)
    try:
        return _lesen(c, jahr)
    finally:
        d.masken = alt


def textmaske_gross(c, x0, x1, y0, y1):
    """Fette Anmerkungen im Kursfeld („Starke Nachfrage“, „Shakeout“): Wörter mit sicherer Lesung, großzügig maskiert."""
    m = np.zeros(c.shape[:2], bool)
    for f in (1, 2):
        for w in worte(c[y0:y1, x0:x1], f=f, psm=11):
            bu = re.sub(r"[^A-Za-zÄÖÜäöüß]", "", w["t"])
            if len(bu) >= 4 and len(bu) >= 0.8 * len(w["t"]) and re.search(r"[aeiouäöü]", bu.lower()) and w["cf"] > 60 and w["h"] >= 9:
                ya, yb = int(y0 + w["y"] - w["h"] / 2 - 3), int(y0 + w["y"] + w["h"] / 2 + 3)
                m[max(0, ya):yb, int(x0 + w["l"] - 3):int(x0 + w["r"] + 3)] = True
    return m


def fettmaske(c, x0, x1, y0, y1, sp=5.0):
    """Fette Schrift und Pfeile: Striche, die mindestens 3 Pixel breit UND hoch sind. Kursbalken sind 1–2 Pixel
    breit und verschwinden beim Öffnen mit einem 3x3-Kern; übrig bleibt Fettschrift. Großzügig vergrößert."""
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
    dunkel = np.zeros(g.shape, np.uint8)
    dunkel[y0:y1, x0:x1] = (g[y0:y1, x0:x1] < 110).astype(np.uint8)
    k = 3 if sp < 6 else 5                       # weite Balkenabstände = dickere Balken: größerer Kern
    fett = cv2.morphologyEx(dunkel, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fett)
    m = np.zeros(g.shape, np.uint8)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] >= 12:
            m[lab == k] = 1
    return cv2.dilate(m, np.ones((7, 7), np.uint8)).astype(bool)


def _lesen(c, jahr=None):
    s = struktur(c)
    ende_kopf = kopfdatum(c, s)
    H = c.shape[0]
    marken = tageszahlen(c, s["v_unten"] + 1, min(H - 2, s["v_unten"] + 40), 0, s["x1"] + 8)
    jahre = jahr if isinstance(jahr, (list, tuple)) else [jahr if jahr else (ende_kopf[2] if ende_kopf and ende_kopf[2] else 2000)]
    tage, wx, sp, n_ok, n_marken, kal_name, kopf = zeitachse(marken, s["x0"] + 2, s["x1"], jahre, ende_kopf)
    wx = [int(round(x)) for x in wx]
    preis0, p_art, p_rest, p_n = b.achse(c, s["x1"] + 2, c.shape[1], s["p_oben"] - 6, s["p_unten"] + 6)
    faktor = dezimal_faktor(c, s["x1"] - 5, s["p_oben"], s["p_unten"])
    preis = lambda y: preis0(y) * faktor
    weg = d.textmaske(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"]) | d.kastenmaske(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"]) \
        | d.linienmaske(c, s["x0"] + 2, s["x1"] - 2, s["p_oben"] + 2, s["p_unten"] - 2, sp) \
        | rechteckmaske(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"]) | textmaske_gross(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"]) | fettmaske(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"], sp) | (legendenmaske(c, s["x0"], s["x1"], s["p_oben"], s["p_unten"]) if ende_kopf else False)
    kb, versatz = d.kursbalken(c, wx, s["p_oben"] + 2, s["p_unten"] - 2, weg)
    vh = volumen(c, wx, s["v_unten"] - 1, s["v_oben"] + 1)
    zeilen = []
    handel = set(b.NYSE.valid_days(tage[0], tage[-1]).tz_localize(None)) if len(tage) else set()
    for x, bb, v, t in zip(wx, kb, vh, tage):
        if bb is None or t not in handel:          # Feiertag als leere Stelle im Werktagsraster
            continue
        zeilen.append({"Datum": t, "x": x, "High": preis(bb[0]), "Low": preis(bb[1]), "Close": preis(bb[2]),
                       "Volume": max(0.0, v) * 1e4})
    df = pd.DataFrame(zeilen)
    if len(df):
        df = d.bereinigen(df, grenze=0.12, alle=pd.DatetimeIndex(sorted(t for t in tage if t in handel)))
        df["Volume"] = df["Volume"].interpolate(limit_direction="both")      # überbrückte Tage: Volumen der Nachbarn
    ende = df["Datum"].iloc[-1] if len(df) else None
    info = dict(ticker="?", art="Tag", ende=str(ende.date()) if ende is not None else "", kopfdatum=str(kopf.date()) if kopf is not None else "",
                datum_aus="Zeitachse", achse=p_art, dezimal=faktor, achse_rest_px=round(p_rest, 2), achse_n=p_n, volumen_skala=False,
                kalender=kal_name, balken=len(wx), px_je_balken=round(sp, 2), marken=n_marken, marken_passend=n_ok,
                gelesen=int(sum(bb is not None for bb in kb)))
    return df, info, (s, wx, kb, weg)
