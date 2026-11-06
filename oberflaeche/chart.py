"""Der Chart der Titelseite als SVG – VCP-Scanner (06.11.2026): nur, was wir gerade erarbeiten.

Hauptfenster: Kerzen, GD50/150/200 (Woche: GD10W/30W/40W), auf Wunsch GD10 und GD20 (Kullamägi, nur Tageschart), die
Zonen des VCP-Scanners (Baustein 1: Base, Flagge, Konsolidierung mit Vorgeschichte, Fahnenstange und grobem ZigZag) –
„Aktuell“ nur das Setup jetzt, „Historie“ dazu alle abgeschlossenen Zonen mit ↑ am Ausbruch.
Darunter Volumen mit 50er-Schnitt und dem Volumenband (türkis = Ruhe, grün/rot = viel Volumen am Aufwärts-/Abwärtstag), ganz unten die relative Stärke gegen den S&P 500 und gestrichelt gegen den eigenen
Sektor-ETF (beide links bei 100).
Der frühere Chart (Market-Profile-Zonen, POC-Treppe, Pivot, Stopps, Volumenprofil, Phasenband, Zahlentermine) liegt in
_to_delete/chart_vor_vcp_2026-11-06.py.
"""
import numpy as np
import pandas as pd


from gestaltung import BLAU, GELB, GRUEN, LILA, RAND, ROT, TEXT, TEXT_2, TEXT_3, zahl

MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
B, LINKS, RECHTS = 1344, 64, 104
ETIKETT = 120               # Spalte rechts neben den Kerzen für die Pfeile der RS-Linien
SAND = "#D9B26F"             # GD200 / GD40W: Trennlinie des langfristigen Trends, kräftig
TUERKIS = "#2EC4B6"          # Ruhe im Volumenband
GD_KURZ = {10: "#F0883E", 20: "#FF7EB6"}   # GD10 orange, GD20 rosa (Kullamägi)
ZONE_FARBE = {"Base": BLAU, "Flagge": GELB, "Konsolidierung": LILA}
ZONE_ANSICHT = ["Aktuell", "Historie"]   # Knopf über dem Chart: nur das Setup jetzt oder alle Zonen

# Ausschnitte je Zeitebene: Knopf → Zahl der Balken (feste Knöpfe statt Regler)
AUSSCHNITT = {"Tag": {"3 M": 63, "6 M": 126, "1 J": 252, "2 J": 504},
              "Woche": {"1 J": 52, "3 J": 156, "5 J": 260}}
AUSSCHNITT_START = {"Tag": "1 J", "Woche": "3 J"}


def _verlaengert(df):
    """Für den Wochenchart über 3 Jahre hinaus: ältere Tageskurse aus daten/lang (Yahoo, 10 Jahre) vor die geladenen
    Kurse setzen, auf den ersten gemeinsamen Schluss skaliert (fängt Splits seit dem Abzug ab). Ohne Datei unverändert."""
    import os
    tk = (df.attrs.get("ticker") or "").upper().replace("^", "_")
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daten", "lang", f"{tk}.csv")
    if not tk or not os.path.exists(pfad):
        return df
    try:
        lang = pd.read_csv(pfad, parse_dates=["Datum"], index_col="Datum")
        gemeinsam = lang.index[lang.index <= df.index[0]]
        if not len(gemeinsam):
            return df
        faktor = float(df["Close"].iloc[0]) / float(lang.loc[gemeinsam[-1], "Close"])
        alt = lang[lang.index < df.index[0]].copy()
        for sp in ("Open", "High", "Low", "Close"):
            alt[sp] = alt[sp] * faktor
        neu = pd.concat([alt[["Open", "High", "Low", "Close", "Volume"]], df])
        neu.attrs = dict(df.attrs)
        return neu
    except Exception:  # noqa: BLE001 – ohne lesbare Langdatei bleibt der Chart bei 3 Jahren
        return df


def _woche(df):
    return df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min",
                                     "Close": "last", "Volume": "sum"}).dropna()


def reaktionen(df, gewinne):
    """Kursreaktion am ersten Handelstag nach jeder Gewinnmeldung: Liste (Datum, Prozent)."""
    aus = []
    if gewinne is None or gewinne.empty:
        return aus
    for tag, z in gewinne.iterrows():
        pos = int(df.index.searchsorted(tag))
        if z.get("nach_schluss", 0):
            pos += 1 if pos < len(df) and df.index[pos] == tag else 0
        if 0 < pos < len(df):
            aus.append((df.index[pos], (df["Close"].iloc[pos] / df["Close"].iloc[pos - 1] - 1) * 100))
    return aus



def chart(df, ebene="Tag", index=None, ausschnitt=None, sektor=None, sektor_name="", zonen=None,
          zonen_ansicht="Aktuell", gd_kurz=False):
    """Kerzen mit GD, Zonen des VCP-Scanners, Volumen mit 50er-Schnitt, RS-Linien. ausschnitt: Knopf aus AUSSCHNITT."""
    voll = df if ebene == "Tag" else _woche(_verlaengert(df))
    n_zeigen = AUSSCHNITT[ebene].get(ausschnitt or AUSSCHNITT_START[ebene], AUSSCHNITT[ebene][AUSSCHNITT_START[ebene]])
    gd = (50, 150, 200) if ebene == "Tag" else (10, 30, 40)
    linien = {k: voll["Close"].rolling(k).mean() for k in gd}
    kurz = {k: voll["Close"].rolling(k).mean() for k in GD_KURZ} if gd_kurz and ebene == "Tag" else {}
    d = voll.iloc[-n_zeigen:]
    N = len(d)
    o, h, l, c, v = (d[s_].to_numpy(float) for s_ in ("Open", "High", "Low", "Close", "Volume"))
    breite = B - LINKS - RECHTS - ETIKETT
    ENDE = LINKS + breite

    def X(i):
        return LINKS + breite * (i + 0.5) / N

    def pos(tag):
        """Index des Balkens, der den Tag enthält (Woche: Freitag danach)."""
        return min(int(d.index.searchsorted(pd.Timestamp(tag))), N - 1)

    pmax, pmin = h.max() * 1.04, l.min() * 0.97

    def Y(y):
        return 30 + 400 * (1 - (np.log(y) - np.log(pmin)) / (np.log(pmax) - np.log(pmin)))

    belegt = []                                  # gesetzte Beschriftungen (x0, x1, y), damit sich keine überlappen

    def platz(x, y, text, groesse, anker="middle", nach_oben=True):
        b_ = len(text) * groesse * 0.55
        x0 = x - b_ / 2 if anker == "middle" else (x - b_ if anker == "end" else x)
        x1 = x0 + b_
        for _ in range(12):
            if all(x1 < a0 - 4 or x0 > a1 + 4 or abs(y - ay) >= groesse + 2 for a0, a1, ay in belegt):
                break
            y += -(groesse + 2) if nach_oben else groesse + 2
        belegt.append((x0, x1, y))
        return y

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} 760" width="100%" role="img" aria-label="Kurschart" '
         f'style="display:block;font-family:IBM Plex Sans,sans-serif">'
         '<style>text{paint-order:stroke;stroke:#161C24;stroke-width:4px;stroke-linejoin:round}</style>'
         + "<defs>" + "".join(f'<marker id="spitze{n_}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                              f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{f_}"/></marker>'
                              for n_, f_ in (("G", GRUEN), ("Y", GELB))) + "</defs>"]
    A = s.append
    for k in range(5):
        yv = pmin * (pmax / pmin) ** (k / 4)
        A(f'<line x1="{LINKS}" x2="{ENDE}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="{RAND}"/>')
        A(f'<text x="{LINKS - 8}" y="{Y(yv) + 4:.1f}" fill="{TEXT_3}" font-size="12" text-anchor="end">{yv:.0f}</text>')

    spaete = []                                  # Beschriftungen, die über den Kerzen liegen müssen
    if zonen:
        _zonen(zonen, zonen_ansicht, d, pos, X, Y, A, spaete, platz, ENDE, breite / N / 2)

    # Kerzen
    bw = breite / N * 0.6
    for i in range(N):
        f = GRUEN if c[i] >= o[i] else ROT
        A(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{Y(h[i]):.1f}" y2="{Y(l[i]):.1f}" stroke="{f}"/>')
        y1, y2 = sorted([Y(o[i]), Y(c[i])])
        hohl = i == N - 1 and df.attrs.get("laufend") and ebene == "Tag"
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{max(1, y2 - y1):.1f}" '
          + (f'fill="none" stroke="{f}" stroke-width="1.2"/>' if hohl else f'fill="{f}"/>'))

    def linie(reihe, farbe, dicke=1.6):
        r = reihe.reindex(d.index)
        pkt = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(r.to_numpy(float))
                       if not np.isnan(x) and pmin <= x <= pmax)
        if pkt:
            A(f'<polyline points="{pkt}" fill="none" stroke="{farbe}" stroke-width="{dicke}"/>')

    for k, farbe, dicke in zip(gd[::-1], (SAND, LILA, BLAU), (2.4, 1.6, 1.6)):
        linie(linien[k], farbe, dicke)
    for k, reihe in kurz.items():
        linie(reihe, GD_KURZ[k], 1.4)
    for t_ in spaete:
        A(t_)

    # Volumen mit 50er-Schnitt (Woche: 10 Wochen)
    vmax = v.max() or 1
    A(f'<text x="{LINKS}" y="474" fill="{TEXT_3}" font-size="12">VOLUMEN · Linie = Schnitt {"50 Tage" if ebene == "Tag" else "10 Wochen"}</text>')
    for i in range(N):
        hv = 90 * v[i] / vmax
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{570 - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" '
          f'fill="{GRUEN if c[i] >= o[i] else ROT}" fill-opacity="0.75"/>')
    v50 = voll["Volume"].rolling(50 if ebene == "Tag" else 10).mean().reindex(d.index).to_numpy(float)
    pkt = " ".join(f"{X(i):.1f},{570 - 90 * x / vmax:.1f}" for i, x in enumerate(v50) if not np.isnan(x))
    A(f'<polyline points="{pkt}" fill="none" stroke="{TEXT}" stroke-width="1.2"/>')
    # Volumenband je Balken, am Schnitt gemessen: Ruhe türkis (kräftig bis 50 %, blass bis 75 %), viel Volumen in
    # Richtung des Tages (Schluss zum Vortag) grün bzw. rot (blass über dem Schnitt, kräftig ab 1,5-fach), sonst grau
    cv = voll["Close"].shift().reindex(d.index).to_numpy(float)
    for i in range(N):
        if np.isnan(v50[i]) or not v50[i]:
            continue
        q = v[i] / v50[i]
        auf = c[i] >= (cv[i] if not np.isnan(cv[i]) else o[i])
        if q <= 0.5:
            farbe, deck, wort = TUERKIS, 0.95, "Ruhe"
        elif q <= 0.75:
            farbe, deck, wort = TUERKIS, 0.4, "eher ruhig"
        elif q <= 1.0:
            farbe, deck, wort = TEXT_3, 0.25, "normal"
        else:
            farbe, deck = (GRUEN if auf else ROT), (0.95 if q >= 1.5 else 0.4)
            wort = ("deutlich erhöht" if q >= 1.5 else "über dem Schnitt") + (" ↑" if auf else " ↓")
        A(f'<rect x="{X(i) - breite / N / 2:.1f}" y="577" width="{breite / N + 0.3:.1f}" height="9" fill="{farbe}" '
          f'fill-opacity="{deck}"><title>{d.index[i]:%d.%m.%Y}: Volumen {zahl(q * 100, 0)} % vom Schnitt – {wort}'
          f'</title></rect>')
    A(f'<text x="{ENDE + 8:.1f}" y="585" fill="{TEXT_3}" font-size="11">Volumen</text>')

    # RS-Linien gegen den S&P 500 und gestrichelt gegen den Sektor-ETF, beide links bei 100
    if index is not None:
        def relativ(bezug):
            bx = bezug if ebene == "Tag" else bezug.resample("W-FRI").last()
            r = (voll["Close"] / bx.reindex(voll.index, method="ffill")).reindex(d.index).to_numpy(float)
            gueltig = np.flatnonzero(~np.isnan(r))
            return r / r[gueltig[0]] * 100 if len(gueltig) > 5 else None

        rs = relativ(index["Close"])
        rk = relativ(sektor) if sektor is not None else None
        if rs is not None:
            alle = np.concatenate([rs[~np.isnan(rs)], rk[~np.isnan(rk)] if rk is not None else [], [100.0]])
            lo, hi = alle.min(), alle.max()
            rand = (hi - lo) * 0.06 or 1
            lo, hi = lo - rand, hi + rand
            YR = lambda y: 618 + 102 * (1 - (y - lo) / (hi - lo))          # noqa: E731
            kurz_ = 10 if ebene == "Tag" else 3

            def pfeil(r, farbe, name):
                """Dynamik der letzten 10 Tage (3 Wochen) am Linienende: Pfeil und beide Werte (vorher → heute)."""
                g = r[~np.isnan(r)]
                if len(g) <= kurz_:
                    return
                alt, neu = g[-1 - kurz_], g[-1]
                pr = (neu / alt - 1) * 100
                p_ = "↑" if pr >= 3 else "↗" if pr >= 1 else "↓" if pr <= -3 else "↘" if pr <= -1 else "→"
                A(f'<g><title>{name}: {zahl(alt, 0)} → {zahl(neu, 0)} in {kurz_} {"Tagen" if ebene == "Tag" else "Wochen"} '
                  f'({"+" if pr >= 0 else "−"}{zahl(abs(pr), 1)} %); 100 = so stark wie am linken Rand</title>'
                  f'<text x="{ENDE + 8:.1f}" y="{platz(ENDE + 8, YR(neu) + 5, "↗ 000 → 000", 12, "start"):.1f}" '
                  f'fill="{farbe}" font-size="12"><tspan font-size="15" font-weight="700">{p_}</tspan> '
                  f'{zahl(alt, 0)} → {zahl(neu, 0)}</text></g>')

            A(f'<text x="{LINKS}" y="608" fill="{TEXT_3}" font-size="12">RELATIVE STÄRKE SEIT {d.index[0]:%m/%Y} · '
              f'<tspan fill="{BLAU}">— gegen S&amp;P 500</tspan>'
              + (f'  <tspan fill="{LILA}">- - gegen Sektor {sektor_name}</tspan>' if rk is not None else "")
              + f'  · Pfeil = letzte {kurz_} {"Tage" if ebene == "Tag" else "Wochen"}</text>')
            A(f'<line x1="{LINKS}" x2="{ENDE}" y1="{YR(100):.1f}" y2="{YR(100):.1f}" stroke="{TEXT_3}" '
              f'stroke-width="1" stroke-dasharray="2 4"/>'
              f'<text x="{LINKS - 6}" y="{YR(100) + 4:.1f}" fill="{TEXT_3}" font-size="11" text-anchor="end">100</text>')
            if rk is not None:
                A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(rk) if not np.isnan(x))
                  + f'" fill="none" stroke="{LILA}" stroke-width="1.5" stroke-dasharray="5 4"/>')
            A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(rs) if not np.isnan(x))
              + f'" fill="none" stroke="{BLAU}" stroke-width="1.8"/>')
            pfeil(rs, BLAU, "gegen S&amp;P 500")
            if rk is not None:
                pfeil(rk, LILA, f"gegen Sektor {sektor_name}")

    # Zeitachse: Monatsanfänge
    letzter = None
    for i, tag in enumerate(d.index):
        schluessel = (tag.year, tag.month) if ebene == "Tag" else (tag.year, (tag.month - 1) // 3)
        if schluessel != letzter:
            if letzter is not None:
                text = MONATE[tag.month - 1] + (f" {tag.year % 100:02d}" if tag.month <= 3 or ebene == "Woche" else "")
                A(f'<text x="{X(i):.1f}" y="748" fill="{TEXT_3}" font-size="12">{text}</text>')
            letzter = schluessel
    A("</svg>")
    return "".join(s)


def _zonen(ka, ansicht, d, pos, X, Y, A, spaete, platz, ENDE, halb):
    """VCP-Scanner Baustein 1 im Chart: Zone (Base blau, Flagge gelb, Konsolidierung lila), Vorgeschichte als gelber
    Pfeil, Fahnenstange als grüner Pfeil, grobes ZigZag grau. Aktuell = nur das Setup jetzt (ZigZag ab der Vorgeschichte),
    Historie = dazu alle abgeschlossenen Zonen im Ausschnitt mit ↑ am Ausbruch."""
    erster = d.index[0]
    jetzt = ka.get("jetzt") or {}

    def rahmen(b, x1, dick, deck, strich=""):
        if b.get("ende_t") is not None and b["ende_t"] < erster:
            return None
        fa = ZONE_FARBE.get(b.get("name"), TEXT_3)
        x0 = X(pos(b["start_t"])) - halb if b["start_t"] >= erster else X(0) - halb   # links angeschnitten
        A(f'<rect x="{x0:.1f}" y="{Y(b["oben"]):.1f}" width="{max(2, x1 - x0):.1f}" height="{Y(b["unten"]) - Y(b["oben"]):.1f}" '
          f'fill="{fa}" fill-opacity="{deck}" stroke="{fa}" stroke-width="{dick}"' + (f' stroke-dasharray="{strich}"' if strich else "")
          + f'><title>{b.get("name", "Zone offen")} {b["start_t"]:%d.%m.%Y}' + (f'–{b["ende_t"]:%d.%m.%Y}' if b.get("ende_t") else "–heute")
          + f' · {zahl(b["wochen"], 1)} Wochen · Tiefe {zahl(b["tiefe"], 1)} % · Oberkante {zahl(b["oben"])} $ · Unterkante {zahl(b["unten"])} $'
          + '</title></rect>')
        return x0

    def pfeil(t0, p0, t1, p1, farbe, marke, dick=2):
        if t0 < erster:
            return
        A(f'<line x1="{X(pos(t0)):.1f}" y1="{Y(p0):.1f}" x2="{X(pos(t1)):.1f}" y2="{Y(p1):.1f}" stroke="{farbe}" '
          f'stroke-width="{dick}" stroke-opacity="0.9" marker-end="url(#spitze{marke})"/>')

    # ZigZag (grob, 2 × ATR)
    ab = erster
    if ansicht == "Aktuell":
        v_ = jetzt.get("vorgeschichte") or {}
        ab = max(erster, v_.get("von_t") or jetzt.get("start_t") or d.index[max(0, len(d) - 60)])
    zz = [(X(pos(t)), Y(p)) for t, p in ka.get("zigzag") or [] if t >= ab]
    if len(zz) >= 2:
        A(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in zz)}" fill="none" stroke="{TEXT_3}" '
          f'stroke-width="1.2" stroke-opacity="0.8"/>')

    if ansicht == "Historie":
        stangen_ende = []
        for b in ka.get("verlauf") or []:
            x0 = rahmen(b, X(pos(b["ende_t"])), 1.2, 0.07)
            if x0 is None:
                continue
            spaete.append(f'<text x="{X(pos(b["ende_t"])):.1f}" y="{Y(b["oben"]) - 4:.1f}" fill="{GRUEN}" font-size="15" '
                          f'font-weight="700" text-anchor="middle">↑</text>')
            st_ = b.get("stange") or {}
            if b["name"] == "Flagge" and st_ and not any(st_["von_t"] < e for e in stangen_ende):
                pfeil(st_["von_t"], st_["von"], b["start_t"], b["oben"], GRUEN, "G", 1.6)
            if b["name"] == "Flagge":
                stangen_ende.append(b["ende_t"])

    if jetzt.get("zone") or jetzt.get("offen"):
        offen = not jetzt.get("zone")
        x0 = rahmen(jetzt, ENDE, 2 if not offen else 1.4, 0.09 if not offen else 0, "6 4" if offen else "")
        if x0 is not None:
            if offen:
                text_ = f'Zone offen · Rücksetzer {zahl(jetzt["tiefe"], 1)} % · noch keine Erholung'
            else:
                text_ = (f'{jetzt["name"]} · {zahl(jetzt["wochen"], 1)} Wochen · Tiefe {zahl(jetzt["tiefe"], 1)} %'
                         + (" · zu kurz" if jetzt["laenge"] == "zu kurz" else ""))
            fa = ZONE_FARBE.get(jetzt.get("name"), TEXT_2)
            rechts = x0 + len(text_) * 6.6 > ENDE            # schmale Zone am rechten Rand: Text endet am Rand
            xt, anker = (ENDE, "end") if rechts else (x0 + 4, "start")
            spaete.append(f'<text x="{xt:.1f}" y="{platz(xt, Y(jetzt["oben"]) - 8, text_, 12, anker):.1f}" '
                          f'fill="{fa}" font-size="12" font-weight="600" text-anchor="{anker}">{text_}</text>')
            v_ = jetzt.get("vorgeschichte") or {}
            st_ = jetzt.get("stange") or {}
            if jetzt.get("name") == "Flagge" and st_:
                pfeil(st_["von_t"], st_["von"], jetzt["start_t"], jetzt["oben"], GRUEN, "G", 2.2)
            elif v_.get("von_t") is not None:
                pfeil(v_["von_t"], v_["von"], v_["bis_t"], v_["bis"], GELB, "Y", 2)
        innen = jetzt.get("innen")
        if innen and innen["start_t"] >= erster:
            rahmen(innen, ENDE, 1.8, 0.0)
            st_ = innen.get("stange") or {}
            if st_:
                pfeil(st_["von_t"], st_["von"], innen["start_t"], innen["oben"], GRUEN, "G", 2)
            t_ = f'Flagge in der Zone · {zahl(innen["wochen"], 1)} Wochen · Tiefe {zahl(innen["tiefe"], 1)} %'
            xi = X(pos(innen["start_t"]))
            spaete.append(f'<text x="{xi:.1f}" y="{platz(xi, Y(innen["oben"]) - 8, t_, 12, "start"):.1f}" fill="{GELB}" '
                          f'font-size="12" font-weight="600">{t_}</text>')


def legende(ebene="Tag", gd_kurz=False):
    from gestaltung import t
    namen = ("GD50", "GD150", "GD200") if ebene == "Tag" else ("GD10W", "GD30W", "GD40W")
    eintraege = [(BLAU, namen[0]), (LILA, namen[1]), (SAND, namen[2] + " (langfristiger Trend)")]
    if gd_kurz and ebene == "Tag":
        eintraege += [(GD_KURZ[10], "GD10"), (GD_KURZ[20], "GD20")]
    eintraege += [(BLAU, "Base"), (GELB, "Flagge"), (LILA, "Konsolidierung (nach Absturz)"),
                  (GELB, "Pfeil gelb = Vorgeschichte"), (GRUEN, "Pfeil grün = Fahnenstange · ↑ = Ausbruch"),
                  (TEXT_3, "ZigZag (2 × ATR)"),
                  (TUERKIS, "Band unter dem Volumen: Ruhe – kräftig bis 50 % vom Schnitt, blass bis 75 %"),
                  (GRUEN, "Band: viel Volumen am Aufwärtstag (blass über dem Schnitt, kräftig ab 1,5-fach), rot am Abwärtstag")]
    return "".join(f'<span style="display:inline-flex;align-items:center;gap:8px;font-size:14px;color:{TEXT_2}">'
                   f'<span style="width:18px;height:4px;border-radius:2px;background:{f}"></span>{t(n)}</span>'
                   for f, n in eintraege)
