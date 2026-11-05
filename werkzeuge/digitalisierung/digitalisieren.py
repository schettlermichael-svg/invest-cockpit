"""Wochencharts aus O'Neils Buch digitalisieren: Bild -> Wochenkerzen (Hoch, Tief, Schluss, Volumen).

Ablauf je Bild: drehen (Zeit nach rechts), Rahmen finden, Preisachse per Texterkennung lesen (logarithmisch,
Ausgleichsgerade, Restfehler in Pixeln wird ausgewiesen), Datumsleiste lesen, Wochen aus den Volumenbalken,
je Woche den senkrechten Kursbalken und den Schlussstrich rechts davon.
"""
import re
import sys

import cv2
import numpy as np
import pandas as pd
import pytesseract

MONATE = {"jan": 1, "feb": 2, "mar": 3, "mär": 3, "apr": 4, "may": 5, "mai": 5, "jun": 6, "jul": 7, "aug": 8,
          "sep": 9, "oct": 10, "okt": 10, "nov": 11, "dec": 12, "dez": 12}


def masken(img):
    a = img.astype(int)
    B, G, R = a[..., 0], a[..., 1], a[..., 2]
    schwarz = (R < 110) & (G < 110) & (B < 110)
    rotm = (R > 140) & (G < 110) & (B < 120) & (R - G > 70)
    return schwarz, rotm


def rahmen(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    d = (g < 90)
    H, W = d.shape
    zeilen = d.sum(1)
    lang = [y for y in range(H) if zeilen[y] > 0.5 * W]
    # zusammenhängende Gruppen
    grp = []
    for y in lang:
        if grp and y - grp[-1][-1] <= 3:
            grp[-1].append(y)
        else:
            grp.append([y])
    linien = [int(np.mean(g)) for g in grp]
    spalten = d.sum(0)
    senk = [x for x in range(W) if spalten[x] > 0.35 * H]
    gx = []
    for x in senk:
        if gx and x - gx[-1][-1] <= 3:
            gx[-1].append(x)
        else:
            gx.append([x])
    slinien = [int(np.mean(g)) for g in gx]
    return linien, slinien


def ocr_zahlen(img, x0, x1, y0, y1, faktor=2):
    crop = img[y0:y1, x0:x1]
    big = cv2.resize(crop, None, fx=faktor, fy=faktor, interpolation=cv2.INTER_CUBIC)
    d = pytesseract.image_to_data(big, config="--psm 6", output_type=pytesseract.Output.DICT)
    aus = []
    for t, l, y, w, h in zip(d["text"], d["left"], d["top"], d["width"], d["height"]):
        t = t.strip().replace(",", "").replace("$", "")
        if re.fullmatch(r"\d+(\.\d+)?", t) and float(t) > 0:
            aus.append((float(t), y0 + (y + h / 2) / faktor, x0 + (l + w / 2) / faktor))
    return aus


def preisachse(img, x0, x1, y0, y1):
    """Logarithmische Preisachse aus den Beschriftungen. Robust gegen Lesefehler (z. B. „15“ als „45“):
    aus allen Paaren die Gerade mit den meisten passenden Beschriftungen (Abweichung unter 3 Pixel), dann
    Ausgleichsgerade nur über diese."""
    lab = ocr_zahlen(img, x0, x1, y0, y1, faktor=3)
    if len(lab) < 4:
        raise ValueError("zu wenige Preisbeschriftungen gelesen")
    lp = np.log([p for p, _, _ in lab])
    ys = np.array([y for _, y, _ in lab])
    beste = None
    for i in range(len(lab)):
        for j in range(i + 1, len(lab)):
            if lp[i] == lp[j] or ys[i] == ys[j]:
                continue
            m_ = (ys[j] - ys[i]) / (lp[j] - lp[i])
            if m_ >= 0:
                continue
            res = np.abs(ys - (ys[i] + m_ * (lp - lp[i])))
            drin = res < 3
            if beste is None or drin.sum() > beste.sum():
                beste = drin
    if beste is None or beste.sum() < 4:
        raise ValueError("Preisachse nicht eindeutig lesbar")
    a = np.polyfit(lp[beste], ys[beste], 1)
    r = ys[beste] - np.polyval(a, lp[beste])
    links = min(x for (_, _, x), ok in zip(lab, beste) if ok)
    return a, float(np.max(np.abs(r))), int(beste.sum()), links


def _datum_lesen(img, y0, y1, x0, x1, faktor, psm, binaer):
    crop = img[y0 + 2:min(y1 + 8, img.shape[0]), x0 + 2:x1]     # Schrift reicht manchmal bis an die Unterkante
    hg = [int(v) for v in np.median(crop.reshape(-1, 3), 0)]
    crop = cv2.copyMakeBorder(crop, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=hg)  # Rand in Papierfarbe hilft der Texterkennung
    big = cv2.resize(crop, None, fx=faktor, fy=faktor, interpolation=cv2.INTER_CUBIC)
    if binaer:
        g = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
        big = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    d = pytesseract.image_to_data(big, config=f"--psm {psm}", output_type=pytesseract.Output.DICT)
    woerter = [(t.strip(), x0 + 2 + l / faktor - 10) for t, l in zip(d["text"], d["left"]) if t.strip()]
    punkte = []
    for i, (t, l) in enumerate(woerter):
        m = re.search(r"([A-Za-zäÄ]{3})", t)
        if not m or m.group(1).lower() not in MONATE:
            continue
        # Jahr im selben oder in den nächsten Wörtern; zerrissene Jahre („199 8“) zusammensetzen
        rest = "".join(re.sub(r"\D", "", w) for w, _ in woerter[i:i + 3])
        j = re.match(r"(18|19|20)\d\d", rest)
        if j:
            # O'Neil-Wochencharts: Quartalskästen tragen den LETZTEN Monat (Kasten „Jun 2003“ = Apr–Jun);
            # die linke Kante ist also der Anfang des Monats zwei Monate davor (an Apple 2004 gegen TradingView geprüft)
            beginn = pd.Timestamp(year=int(j.group(0)), month=MONATE[m.group(1).lower()], day=1) - pd.DateOffset(months=2)
            beginn += pd.Timedelta(days=(7 - beginn.weekday()) % 7)        # erste volle Woche (Montag)
            punkte.append((beginn, l))
    return punkte


def datumsachse(img, y0, y1, x0, x1):
    """Datumsleiste lesen; kleine Schrift: mehrere Vergrößerungen und Lesarten, die ergiebigste zählt."""
    beste = []
    for faktor, psm, binaer in ((3, 6, False), (4, 6, True), (5, 11, True), (4, 11, False)):
        p = _datum_lesen(img, y0, y1, x0, x1, faktor, psm, binaer)
        if len(p) > len(beste):
            beste = p
        if len(beste) >= 6:
            break
    if len(beste) < 3:
        raise ValueError("zu wenige Datumsbeschriftungen gelesen")
    return beste


def wochen_aus_volumen(m, y_unten, y_oben, x0, x1):
    hoehe = y_unten - y_oben
    band = m[y_unten - int(0.15 * hoehe):y_unten - 2, x0:x1].sum(0)
    # durchgehende Senkrechte, die auch über das Feld hinausläuft: Trennlinie, kein Volumen
    # (ein Rekordvolumen füllt das Feld ebenfalls, endet aber an dessen Oberkante)
    voll = (m[y_oben + 2:y_unten - 2, x0:x1].mean(0) > 0.95) & (m[y_oben - 8:y_oben - 3, x0:x1].mean(0) > 0.6) \
        & (m[y_unten + 3:y_unten + 8, x0:x1].mean(0) > 0.6)
    xs = np.where((band >= 0.6 * (int(0.15 * hoehe) - 2)) & ~voll)[0] + x0
    if not len(xs):
        return []
    gr = np.split(xs, np.where(np.diff(xs) > 1)[0] + 1)
    return [int(round(g.mean())) for g in gr]


def senkrecht_profil(m, mindest=6):
    """Je Spalte: Pixel in senkrechten Läufen ab `mindest` px (Balken), flache Linien und Kurven zählen kaum."""
    m = m.astype(np.int8)
    h, w = m.shape
    lauf = np.zeros_like(m, dtype=np.int32)
    for y in range(h):                                  # Lauflänge nach unten zählen
        lauf[y] = (lauf[y - 1] + 1) * m[y] if y else m[y]
    # Lauflänge auf ganze Läufe übertragen: von unten zurück das Maximum weiterreichen
    voll = lauf.copy()
    for y in range(h - 2, -1, -1):
        voll[y] = np.where(m[y] & m[y + 1], voll[y + 1], voll[y])
    p = ((voll >= mindest) * m).sum(0).astype(float)
    return np.convolve(p, [0.5, 1, 0.5], mode="same")


def wochenraster(wx, profil=None, x_min=None, x_max=None, sp_vorgabe=None):
    """Wochen liegen in festem Abstand. Abstand und Lage aus dem Spaltenprofil (senkrechte Balken in Kurs- und
    Volumenfeld): der Abstand, bei dem die Rasterpunkte am dichtesten auf Balken fallen; ein halber Abstand
    trifft jede zweite Lücke und verliert deshalb. Bereich = von der ersten bis zur letzten gefundenen Woche."""
    if len(wx) < 5 or profil is None:
        return wx, float(np.median(np.diff(wx))) if len(wx) > 1 else 10.0
    x_a, x_e = wx[0], wx[-1]
    xs = np.arange(len(profil))
    beste = None
    d0 = np.diff(wx)
    sp0 = float(np.median(d0[d0 > 3])) if (d0 > 3).any() else 10.0
    if sp_vorgabe:
        sp0 = sp_vorgabe
    raster = []
    for k in ((1,) if sp_vorgabe else (1, 2, 3)):
        if sp0 / k >= (1.5 if sp_vorgabe else 5):
            raster += list(np.arange(sp0 / k * 0.93, sp0 / k * 1.07, 0.02 if sp_vorgabe else 0.05))
    for sp in raster:
        for ph in np.arange(0, sp, 0.5):
            pos = np.arange(x_a - sp + ph, x_e + 1, sp)
            pos = pos[(pos >= x_a - 2) & (pos <= x_e + 2)]
            if len(pos) < 4:
                continue
            wert = np.interp(pos, xs, profil).mean()
            if beste is None or wert > beste[0]:
                beste = (wert, sp, ph)
    _, sp, ph = beste

    def pos_aus(x_a, x_e, sp, ph):
        p_ = np.arange(x_a - sp + ph, x_e + 1, sp)
        return p_[(p_ >= x_a - 2) & (p_ <= x_e + 2)]
    # doppelter Abstand prüfen: trifft er fast genauso gut, war der kleine nur ein halber
    pos = list(pos_aus(x_a, x_e, sp, ph))
    # über das Volumen hinaus verlängern, solange im Kursfeld Balken stehen (dünne Volumenbalken am Rand)
    xs_p = np.arange(len(profil))
    schwelle = 0.3 * float(np.median(np.interp(pos, xs_p, profil)))
    if x_max is not None:
        while pos[-1] + sp < x_max and np.interp(pos[-1] + sp, xs_p, profil) > schwelle:
            pos.append(pos[-1] + sp)
    return [int(round(p)) for p in pos], float(sp)


def laeufe(col, luecke=2):
    idx = np.where(col)[0]
    if len(idx) == 0:
        return []
    gr = np.split(idx, np.where(np.diff(idx) > luecke)[0] + 1)
    return [(g[0], g[-1]) for g in gr]


def textmaske(img, x0, x1, y0, y1):
    """Wörter (Beschriftungen, Pfeiltexte) und Kästen im Preisfeld finden, damit sie nicht als Kursbalken gelten."""
    crop = img[y0:y1, x0:x1]
    big = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    d = pytesseract.image_to_data(big, config="--psm 11", output_type=pytesseract.Output.DICT)
    weg = np.zeros(img.shape[:2], bool)
    for t, l, y, w, h, c in zip(d["text"], d["left"], d["top"], d["width"], d["height"], d["conf"]):
        t = t.strip()
        buchst = re.sub(r"[^A-Za-zÄÖÜäöüß]", "", t)
        sicher = float(c) > 60 or (len(buchst) >= 5 and float(c) > 35)     # lange Wörter auch bei mäßiger Lesesicherheit
        if len(buchst) >= 3 and re.search(r"[aeiouäöüAEIOU]", buchst) and len(buchst) >= 0.7 * len(t) and sicher:
            xa, ya = x0 + l // 2 - 2, y0 + y // 2 - 2
            weg[ya:ya + h // 2 + 4, xa:xa + w // 2 + 4] = True
    # Kästen: lange waagrechte schwarze Linien im Preisfeld (Titelkasten) samt Inhalt
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dunkel = g < 90
    for y in range(y0 + 2, y1 - 2):
        reihe = dunkel[y, x0:x1]
        lf = np.where(np.diff(np.concatenate([[0], reihe.astype(int), [0]])))[0].reshape(-1, 2)
        for a_, b_ in lf:
            if b_ - a_ > 250:
                weg[y - 1:y + 2, x0 + a_:x0 + b_] = True
    return weg


def kastenmaske(img, x0, x1, y0, y1):
    """Geschlossene Kästen (Titel) im Preisfeld: Konturen großer Rechtecke, ganz ausblenden."""
    x0, y0 = x0 + 4, y0 + 4          # Rahmen weglassen: ein Kasten in der Ecke teilt sich die Kanten mit ihm
    g = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(g, 90, 255, cv2.THRESH_BINARY_INV)
    kont, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    weg = np.zeros(img.shape[:2], bool)
    for k in kont:
        x, y, w, h = cv2.boundingRect(k)
        if 200 < w < 0.5 * (x1 - x0) and 60 < h < 0.5 * (y1 - y0) and len(cv2.approxPolyDP(k, 5, True)) <= 6:
            weg[y0 + y - 3:y0 + y + h + 3, x0 + x - 3:x0 + x + w + 3] = True
    # Kasten in der linken oberen Ecke (teilt Kanten mit dem Rahmen): dicke waagrechte Kante, die am linken Rahmen
    # beginnt -> alles darüber bis zum Rahmen ausblenden
    gg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) < 90
    for y in range(y0, y0 + int(0.4 * (y1 - y0))):
        reihe = gg[y - 1:y + 2, x0:x1].all(0)               # mindestens 3 px dick
        lf = laeufe(reihe, 1)
        for a_, b_ in lf:
            if a_ <= 8 and b_ - a_ >= 150 and b_ - a_ < 0.6 * (x1 - x0):
                weg[y0 - 4:y + 4, x0 - 4:x0 + b_ + 4] = True
    return weg


def linienmaske(img, x0, x1, y0, y1, sp):
    """Gerade, schräge oder waagrechte Linien (Trendlinien, Kanäle, Pfeile) über mehrere Wochen: ausblenden.
    Senkrechte bleiben (das sind die Kursbalken); ein Balken, den eine Linie kreuzt, verliert nur 1–3 px."""
    s, r = masken(img[y0:y1, x0:x1])
    m = ((s | r) * 255).astype(np.uint8)
    weg = np.zeros(img.shape[:2], bool)
    ls = cv2.HoughLinesP(m, 1, np.pi / 360, threshold=int(3 * sp), minLineLength=int(4 * sp), maxLineGap=3)
    if ls is None:
        return weg
    tmp = np.zeros(m.shape, np.uint8)
    for xa, ya, xb, yb in ls.reshape(-1, 4):
        winkel = abs(np.degrees(np.arctan2(yb - ya, xb - xa)))
        winkel = min(winkel, 180 - winkel)
        if winkel < 60:                         # flacher als 60°: keine Balkenkante
            cv2.line(tmp, (xa, ya), (xb, yb), 1, 3)
    # Pixel in langen senkrechten Läufen gehören zu Balken und bleiben stehen
    mm = (s | r).astype(np.int8)
    lauf = np.zeros(mm.shape, np.int32)
    for y in range(mm.shape[0]):
        lauf[y] = (lauf[y - 1] + 1) * mm[y] if y else mm[y]
    voll = lauf.copy()
    for y in range(mm.shape[0] - 2, -1, -1):
        voll[y] = np.where(mm[y] & mm[y + 1], voll[y + 1], voll[y])
    weg[y0:y1, x0:x1] = tmp.astype(bool) & ~(voll >= 8)
    return weg


def kursbalken(img, wx, y0, y1, weg=None):
    s, r = masken(img)
    m = s | r
    if weg is not None:
        m = m & ~weg
    # Versatz zwischen Volumen- und Kursbalken schätzen
    beste, versatz = -1, 0
    halb = int(np.median(np.diff(wx)) // 2) + 1 if len(wx) > 2 else 5
    for o in range(-halb, halb + 1):
        dichte = sum(int((m[y0:y1, x + o - 1:x + o + 2].sum(1) >= 2).sum()) for x in wx)   # senkrechte Balken
        if dichte > beste:
            beste, versatz = dichte, o
    sp = float(np.median(np.diff(wx))) if len(wx) > 2 else 10.0
    W = m.shape[1]

    def lauf_rechts(y, x):          # zusammenhängende Tinte ab x nach rechts
        n = 0
        while x + n < W and m[y, x + n]:
            n += 1
        return n

    def lauf_links(y, x):
        n = 0
        while x - n >= 0 and m[y, x - n]:
            n += 1
        return n

    kandidaten = []
    for x in wx:
        x = x + versatz
        # dünne Balken (1–2 px): die dichteste Spalte im Umkreis ±2 nehmen
        dichte = [int(m[y0:y1, x + d].sum()) for d in range(-2, 3)]
        x = x + int(np.argmax(dichte)) - 2
        kern = m[y0:y1, x - 1:x + 2].sum(1) >= 1
        kand = [(a + y0, b + y0) for a, b in laeufe(kern) if b - a >= 2]
        liste = []
        lang = max(8, 0.6 * sp)
        for a, b in kand:
            # Breite je Zeile: Balken sind schmal, nur die Striche ragen heraus. Eine flache Linie
            # (Durchschnitt, Zeichnung) ist in fast jeder Zeile breit -> kein Kursbalken
            breiten = []
            ende_r = []
            for yy in range(a, b + 1):
                spalte = x - 1 + int(np.argmax(m[yy, x - 1:x + 2])) if m[yy, x - 1:x + 2].any() else x
                r = lauf_rechts(yy, spalte); l = lauf_links(yy, spalte)
                breiten.append(r + l - 1); ende_r.append(r)
            breiten = np.array(breiten); ende_r = np.array(ende_r)
            if np.median(breiten) > max(5, 0.45 * sp):
                # breit: entweder eine Linie (läuft links UND rechts aus der Woche hinaus) oder ein flacher Balken
                # (enge Woche, im Druck nur ein kurzer dicker Strich) – der bleibt innerhalb seiner Woche
                hw = max(4, int(round(0.6 * sp)))
                ya_, ye_ = max(a - 2, 0), min(b + 3, m.shape[0])
                sub = m[ya_:ye_, max(x - hw, 0):x + hw + 1].astype(np.uint8)
                _, lab = cv2.connectedComponents(sub, connectivity=8)
                ids = set(lab[:, min(hw, sub.shape[1] - 1)][lab[:, min(hw, sub.shape[1] - 1)] > 0])
                k = np.isin(lab, list(ids))
                if k[:, 0].any() and k[:, -1].any():
                    # durchlaufendes Band: dünn = Linie (weg); dick und waagrecht = mehrere enge Wochen nebeneinander
                    if b - a + 1 >= 3 and b - a < 0.5 * sp + 2:
                        liste.append((a, b, (a + b) // 2, False))
                    continue
            # kurzer Lauf: gehört er zu einer schrägen Linie, die über die halbe Wochenbreite nach beiden Seiten läuft?
            # Schräglage: ein Kursbalken steht senkrecht, eine Linie oder Kurve wandert seitlich.
            # Mitte des Tintenstücks je Zeile; Median oberes gegen unteres Drittel (Striche stören den Median nicht)
            mitte = []
            schmal = np.median(breiten) + 1
            for k_, yy in enumerate(range(a, b + 1)):
                if breiten[k_] > schmal:            # Zeilen mit Strich (eigener oder vom Nachbarn) auslassen
                    continue
                spalte = x - 1 + int(np.argmax(m[yy, x - 1:x + 2])) if m[yy, x - 1:x + 2].any() else x
                mitte.append(spalte + (lauf_rechts(yy, spalte) - lauf_links(yy, spalte)) / 2)
            n3 = max(1, len(mitte) // 3)
            linie = len(mitte) >= 6 and abs(np.median(mitte[:n3]) - np.median(mitte[-n3:])) >= 2
            # Schlussstrich: ragt 3 px+ nach rechts, endet aber vor dem Nachbarn (keine durchlaufende Linie)
            w = np.where((ende_r >= 4) & (ende_r < lang))[0]
            t = a + int(np.median(w)) if len(w) else None
            liste.append((a, b, t, linie))
        kandidaten.append(liste)
    # Pfad mit kleinsten Sprüngen: Kosten = Abstand zum letzten Schluss, Strafe ohne Schlussstrich;
    # eine Woche darf fehlen (verdeckt), dann gilt der letzte Schluss weiter (Strafe LUECKE)
    # Kurslücken kommen vor (Ausbrüche!): ein Sprung kostet höchstens SPRUNG_MAX; kurze Läufe sind oft Linienreste
    LUECKE, OHNE_STRICH, SPRUNG_MAX, KURZ, LINIE = 60, 40, 50, 30, 80
    zust = []          # je Woche: Liste (kosten, ref, vorgaenger, kandidat oder None)
    for i, liste in enumerate(kandidaten):
        z = []
        optionen = list(liste) + [None]
        for k in optionen:
            if i == 0:
                if k is None:
                    z.append((LUECKE, None, -1, None))
                else:
                    a, b, t, li = k
                    z.append(((0 if t is not None else OHNE_STRICH) + (KURZ if b - a < 5 else 0) + (LINIE if li else 0), t if t is not None else (a + b) / 2, -1, k))
                continue
            best = (1e18, None, -1, k)
            for j, (c0, ref0, _, _) in enumerate(zust[-1]):
                if k is None:
                    c = c0 + LUECKE
                    ref = ref0
                else:
                    a, b, t, li = k
                    sprung = 0 if ref0 is None or a <= ref0 <= b else min(abs(a - ref0), abs(b - ref0))
                    c = c0 + min(sprung, SPRUNG_MAX) + 0.3 * max(0, sprung - SPRUNG_MAX) + (0 if t is not None else OHNE_STRICH) + (KURZ if b - a < 5 else 0) + (LINIE if li else 0)
                    ref = t if t is not None else (a + b) / 2
                if c < best[0]:
                    best = (c, ref, j, k)
            z.append(best)
        zust.append(z)
    aus = [None] * len(kandidaten)
    j = int(np.argmin([c for c, *_ in zust[-1]]))
    for i in range(len(zust) - 1, -1, -1):
        c, ref, vor, k = zust[i][j]
        if k is not None:
            a, b, t, _ = k
            aus[i] = (a, b, t if t is not None else (a + b) // 2)
        j = vor
    return aus, versatz


def volumen(img, wx, y_unten, y_oben):
    s, r = masken(img)
    m = s | r
    aus = []
    for x in wx:
        col = m[y_oben:y_unten, x - 1:x + 2].sum(1) >= 2
        lf = laeufe(col, 3)
        aus.append(y_unten - (y_oben + lf[-1][0]) if lf else 0)   # Höhe des untersten Laufs (vom Boden)
    return np.array(aus, float)


def tafeln(img):
    """Charts einer Seite: große Rahmen (eine Seite kann zwei Charts nebeneinander tragen)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(g, 90, 255, cv2.THRESH_BINARY_INV)
    kont, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H, W = g.shape
    boxen = sorted(cv2.boundingRect(k) for k in kont)
    boxen = [b for b in boxen if b[2] > 0.25 * W and b[3] > 0.2 * H]
    return [(x, y, w, h) for x, y, w, h in boxen]


def digitalisieren(pfad):
    """Alle Charts einer Seite: Liste von (DataFrame, Info, Bild, Hilfsdaten)."""
    seite = cv2.rotate(cv2.imread(pfad), cv2.ROTATE_90_CLOCKWISE)
    t = tafeln(seite)
    # Rechtecke innerhalb eines größeren (Teilfelder eines Charts) sind keine eigenen Charts
    t = [a for a in t if not any(b != a and b[0] <= a[0] and b[1] <= a[1] and b[0] + b[2] >= a[0] + a[2]
                                 and b[1] + b[3] >= a[1] + a[3] for b in t)]
    aus, fehler = [], []
    for x, y, w, h in t:
        try:
            aus.append(chart_lesen(seite[max(0, y - 4):y + h + 4, max(0, x - 4):x + w + 4].copy()))
        except (ValueError, IndexError) as e:
            fehler.append(e)
    if not aus and fehler:
        raise fehler[0]
    return aus


def bereinigen(df, fenster=3, grenze=0.2, max_luecke=3, alle=None):
    """Ausreißer (Balken passt weder zu den Wochen davor noch danach – meist Beschriftung oder Linie) entfernen,
    kurze Lücken (bis max_luecke Wochen) in Log-Preisen überbrücken und als geschätzt kennzeichnen."""
    if len(df) < 2 * fenster + 2:
        df["geschaetzt"] = False
        return df
    df = df.copy()
    for _ in range(3):
        mitte = (np.log(df.High) + np.log(df.Low)) / 2
        links = mitte.shift(1).rolling(fenster, min_periods=1).median()
        rechts = mitte[::-1].shift(1).rolling(fenster, min_periods=1).median()[::-1]
        ab_l = (mitte - links).abs().fillna(0)
        ab_r = (mitte - rechts).abs().fillna(0)
        rand_l, rand_r = links.isna(), rechts.isna()
        # berührt der Balken den Nachbarbalken (±2 %), ist er echt – auch bei Kurslücken danach (Börsengang, Ausbruch)
        h, l = df.High, df.Low
        beruehrt = ((l <= h.shift(1) * 1.02) & (h >= l.shift(1) * 0.98)) | ((l <= h.shift(-1) * 1.02) & (h >= l.shift(-1) * 0.98))
        schlecht = ((ab_l > grenze) | rand_l) & ((ab_r > grenze) | rand_r) & ~(rand_l & rand_r) & ~beruehrt
        if not schlecht.any():
            break
        df = df[~schlecht].reset_index(drop=True)
    df["Datum"] = pd.to_datetime(df["Datum"])
    if alle is None:                              # Wochenchart: Montag für Montag
        alle = pd.date_range(df.Datum.iloc[0], df.Datum.iloc[-1], freq="7D")
    else:                                         # Tageschart: die Handelstage des Charts
        alle = alle[(alle >= df.Datum.iloc[0]) & (alle <= df.Datum.iloc[-1])]
    d2 = df.set_index("Datum").reindex(alle)
    d2["geschaetzt"] = d2["High"].isna()
    for c in ("High", "Low", "Close"):
        d2[c] = np.exp(np.log(d2[c]).interpolate(limit=max_luecke, limit_area="inside"))
    d2 = d2.dropna(subset=["High"])
    d2.index.name = "Datum"
    return d2.reset_index()


def chart_lesen(img):
    linien, slinien = rahmen(img)
    links, rechts = slinien[0], slinien[-1]
    # Preisfeld = größter Abstand zweier waagrechter Linien; darunter Volumen, darunter Datumsleiste
    abst = [(linien[i + 1] - linien[i], i) for i in range(len(linien) - 1)]
    _, i = max(abst)
    p_oben, p_unten = linien[i], linien[i + 1]
    rest = linien[i + 1:]
    v_unten = rest[1] if len(rest) > 1 else rest[0]
    # Datumsleiste: der erste Streifen unter dem Volumen, der hoch genug für Schrift ist (Doppellinien überspringen)
    d_oben, d_unten = v_unten, v_unten + 30
    unter = [y for y in rest if y >= v_unten]
    for y_a, y_b in zip(unter, unter[1:]):
        if y_b - y_a >= 15:
            d_oben, d_unten = y_a, y_b
            break
    breite = rechts - links
    a, fehler, n_lab, lab_links = preisachse(img, rechts - int(min(300, 0.25 * breite)), rechts - 2, p_oben, p_unten)
    grenze = int(lab_links - 0.03 * breite)                  # rechts davon stehen nur Beschriftungen
    s, r = masken(img)
    wx = wochen_aus_volumen(s | r, v_unten, p_unten, links + 3, grenze)
    wx = [x for x in wx if x > links + 6]                     # Rahmenlinie ist keine Woche
    sm, rm_ = masken(img)
    mm = sm | rm_
    profil = senkrecht_profil(mm[p_oben + 3:v_unten - 3])
    if len(wx) < 5:
        # kein Volumen gedruckt: Wochen aus den Kursbalken selbst (Spitzen im Spaltenprofil)
        pk = senkrecht_profil(mm[p_oben + 3:p_unten - 3])
        sw = 0.25 * pk[links + 6:grenze].max()
        wx = [x for x in range(links + 7, grenze - 1) if pk[x] >= sw and pk[x] >= pk[x - 1] and pk[x] > pk[x + 1]]
    wx, schritt = wochenraster(wx, profil, links + 6, grenze)
    daten = datumsachse(img, d_oben, d_unten, links, rechts)
    # Datum der Wochen: Woche i = Anker + 7·i; Anker aus den Kastenkanten (Median, robust gegen Lesefehler)
    idx = np.arange(len(wx))
    anker = [t - pd.Timedelta(days=7 * round((x - wx[0]) / schritt)) for t, x in daten]   # auch links vor der ersten Woche
    anker = pd.Series(anker).mode().iloc[0] if len(anker) else pd.Timestamp("2000-01-03")
    anker = (anker - pd.Timedelta(days=anker.dayofweek)).normalize()                      # Wochen beginnen montags
    weg = textmaske(img, links, grenze, p_oben, p_unten) | kastenmaske(img, links, rechts, p_oben, p_unten) \
        | linienmaske(img, links + 3, grenze, p_oben + 3, p_unten - 3, schritt)
    kb, versatz = kursbalken(img, wx, p_oben + 3, p_unten - 3, weg)
    vol = volumen(img, wx, v_unten - 2, p_unten + 2)
    preis = lambda y: float(np.exp((y - a[1]) / a[0]))
    zeilen = []
    for i, (x, b, v) in enumerate(zip(wx, kb, vol)):
        if b is None:
            continue
        tag = (anker + pd.Timedelta(days=7 * i)).normalize()
        zeilen.append({"x": x, "Datum": tag, "High": preis(b[0]), "Low": preis(b[1]), "Close": preis(b[2]), "Vol_px": v})
    df = pd.DataFrame(zeilen)
    # Handelszeitraum = erste bis letzte Woche mit echtem Volumenbalken (vor dem Börsengang gibt es keine Kurse;
    # ein voller Balken über die ganze Feldhöhe ist eine Trennlinie)
    if len(df):
        h_v = (v_unten - 2) - (p_unten + 2)
        echt = df["Vol_px"] > 0
        if echt.any():
            i_a, i_e = echt.idxmax(), echt[::-1].idxmax()
            df = df.loc[i_a:i_e].reset_index(drop=True)
    roh = len(df)
    if len(df):
        df = bereinigen(df)
    info = {"preis_restfehler_px": round(fehler, 2), "preislabels": n_lab, "wochen": len(wx), "datumslabels": len(daten),
            "px_je_woche": round(schritt, 2), "versatz": versatz,
            "start": f"{anker:%Y-%m-%d}", "gelesen": roh,
            "geschaetzt": int(df["geschaetzt"].sum()) if len(df) else 0}
    return df, info, img, (a, wx, kb, p_oben, p_unten, weg)


if __name__ == "__main__":
    for df, info, *_ in digitalisieren(sys.argv[1]):
        print(info)
        print(df.head(5).to_string())
