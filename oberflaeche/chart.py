"""Der Chart der Titelseite als SVG (Aufbau: Konzept, Abschnitt Titelseite).

Hauptfenster: Kerzen, GD50/150/200 (Woche: GD10W/30W/40W), Anchored VWAP, Base-Rahmen mit
Dauer und Tiefe, Pivot, Kaufzone bis +5 %, Gewinnmeldungen mit Reaktion, rotes
Dreieck beim größten Tagesrückgang seit Beginn von Phase 2, Phasenband.
Darunter Volumen mit 50er-Schnitt und ruhigen Tagen, ganz unten die relative Stärke gegen den
S&P 500 und gestrichelt gegen den eigenen Sektor-ETF: beide links bei 100, gemeinsame Skala,
Linie bei 100 = so stark wie der Index.
"""
import numpy as np
import pandas as pd


from gestaltung import BLAU, GELB, GRAU, GRUEN, LILA, ORANGE, RAND, ROT, TEXT, TEXT_2, TEXT_3, basename, form_hinweis, zahl

MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
PHASENFARBE = {1: GRAU, 2: GRUEN, 3: GELB, 4: ROT}
B, LINKS, RECHTS = 1344, 64, 104
PROFIL_X, PROFIL_B = 1344 - 96, 70
TREPPE = "#FFA657"           # POC-Treppe der Market-Profile-Zonen (heller als der AVWAP)
TUERKIS = "#2EC4B6"          # Spalte des Volumenprofils rechts neben dem Kursbild
SAND = "#D9B26F"             # GD200 / GD40W: Trennlinie des langfristigen Trends, kräftig
KURZ_FARBE = {10: "#E6EAF0", 20: "#F778BA"}   # GD10 / GD20 (Wahlschalter, nur Tageschart), dünn

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


def _pivot_tag(df, von, bis, pivot):
    """Index des Tages im Fenster von..bis, dessen Hoch dem Pivot am nächsten liegt (der Tag, der den Pivot setzt)."""
    h = df["High"].to_numpy(float)
    von, bis = max(0, int(von)), min(len(h) - 1, int(bis))
    return von + int(np.argmin(np.abs(h[von:bis + 1] - pivot)))


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


def verkaufssignal(df, phasen):
    """Größter Tagesrückgang seit Beginn des letzten Phase-2-Abschnitts – als Signal nur, wenn
    er mit Volumen über dem 1,5-Fachen des 50-Tage-Schnitts kam. (Datum, Prozent) oder None."""
    if phasen is None or not (phasen == 2).any():
        return None
    wechsel = phasen[(phasen == 2) & (phasen.shift(1) != 2)]
    teil = df[df.index >= wechsel.index[-1] - pd.Timedelta(days=6)]
    r = teil["Close"].pct_change() * 100
    if r.min() > -4:
        return None
    tag = r.idxmin()
    vol50 = df["Volume"].rolling(50).mean()
    return (tag, float(r.min())) if teil.loc[tag, "Volume"] > 1.5 * vol50.loc[tag] else None




def _ausgang_text(b, df):
    """Hinweis am Zonenrahmen: Ausbruch, Ausgang nach O'Neil, höchstens, Volumen, Kaufsetup damals."""
    if not b:
        return ""
    vol = f", Volumen {zahl(b['vol_ausbruch'], 1)}-fach" if b.get("vol_ausbruch") else ""
    nr = f"Base Nr. {b['basenzahl']} · " if b.get("basenzahl") else ""
    return (f"&#10;{nr}Ausbruch {b.get('richtung', '↑')} {df.index[b['ausbruch']]:%d.%m.%Y}: {b['ausgang']}, höchstens "
            f"{'+' if b['max_gewinn_pct'] >= 0 else '−'}{zahl(abs(b['max_gewinn_pct']), 0)} %{vol} · damals "
            f"{'Setup' if b.get('kaufsetup') else 'kein Setup'}")


def chart(df, ebene="Tag", erk=None, phasen=None, index=None, gewinne=None, sektor=None, sektor_name="", ausschnitt=None,
          kurz=()):
    """ausschnitt: Knopf aus AUSSCHNITT (z. B. „6 M“); kurz: zusätzliche kurze Durchschnitte (10, 20), nur im Tageschart."""
    werte = (erk or {}).get("werte", {})
    muster = (erk or {}).get("muster", [])
    voll = df if ebene == "Tag" else _woche(_verlaengert(df))
    n_zeigen = AUSSCHNITT[ebene].get(ausschnitt or AUSSCHNITT_START[ebene], AUSSCHNITT[ebene][AUSSCHNITT_START[ebene]])
    gd = (50, 150, 200) if ebene == "Tag" else (10, 30, 40)
    kurz = tuple(k for k in kurz if k in (10, 20)) if ebene == "Tag" else ()
    linien = {k: voll["Close"].rolling(k).mean() for k in gd + kurz}
    d = voll.iloc[-n_zeigen:]
    N = len(d)
    o, h, l, c, v = (d[s].to_numpy(float) for s in ("Open", "High", "Low", "Close", "Volume"))
    breite = B - LINKS - RECHTS

    def X(i):
        return LINKS + breite * (i + 0.5) / N

    def pos(tag):
        """Index des Balkens, der den Tag enthält (Woche: Freitag danach)."""
        i = int(d.index.searchsorted(pd.Timestamp(tag)))
        return min(i, N - 1)

    # Anchored VWAP ab Beginn der Base (ohne Muster: ab dem Hoch, an dem die Base beginnt)
    av = None
    if "start_index" in werte:
        anker = df.index[werte["start_index"]]
        tp = (df["High"] + df["Low"] + df["Close"]) / 3
        ab = df.index >= anker
        av_tag = (tp[ab] * df["Volume"][ab]).cumsum() / df["Volume"][ab].cumsum()
        av = av_tag if ebene == "Tag" else av_tag.resample("W-FRI").last().dropna()
    pivot = werte.get("pivot") if muster else None

    bahn = (erk or {}).get("bahn") or {}
    marke_l, marke_s = (bahn.get("long") or {}).get("marke"), (bahn.get("short") or {}).get("marke")
    zone_l, zone_s = (bahn.get("long") or {}).get("zone"), (bahn.get("short") or {}).get("zone")
    try:                                         # geplantes CRV: Ziel, Stopp A, Stopp B als Linien rechts im Chart
        import atr as atr_modul
        import crv as crv_modul
        crv_ = crv_modul.linien(erk or {}, atr_modul.wert(df))
    except Exception:  # noqa: BLE001
        crv_ = None
    crv_preise = [x for x in ((crv_ or {}).get(k) for k in ("ziel", "stopp_a", "stopp_b")) if x]
    oben = [h.max()] + ([pivot * 1.06] if pivot else []) + ([marke_l] if marke_l else []) + ([zone_l[1]] if zone_l else [])
    unten = [l.min()] + ([marke_s] if marke_s else []) + ([zone_s[0]] if zone_s else [])
    oben, unten = oben + crv_preise, unten + crv_preise
    pmax, pmin = max(oben) * 1.03, min(unten) * 0.95

    def Y(y):
        return 20 + 400 * (1 - (np.log(y) - np.log(pmin)) / (np.log(pmax) - np.log(pmin)))

    belegt = []                                  # schon gesetzte Beschriftungen (x0, x1, y), damit sich keine überlappen

    def platz(x, y, text, groesse, anker="middle", nach_oben=True):
        """Freie Zeile für eine Beschriftung: rückt in Schritten einer Zeilenhöhe weg, bis sie keine andere trifft."""
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
         '<style>text{paint-order:stroke;stroke:#161C24;stroke-width:4px;stroke-linejoin:round}</style>']
    A = s.append
    for k in range(5):
        yv = pmin * (pmax / pmin) ** (k / 4)
        A(f'<line x1="{LINKS}" x2="{B - RECHTS}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="{RAND}"/>')
        A(f'<text x="{LINKS - 8}" y="{Y(yv) + 4:.1f}" fill="{TEXT_3}" font-size="12" text-anchor="end">{yv:.0f}</text>')

    spaete = []                                  # Beschriftungen, die über den Kerzen liegen müssen
    mp_ = (erk or {}).get("mp")
    if mp_:
        # Market-Profile-Zonen: Rahmen (Hoch/Tief), Wertbereich 70 % (Fläche), POC; orange Treppe verbindet die POCs,
        # Pfeil ↑/↓ an jeder Stufe (Wochenwert hat die Zone verlassen)
        halb = breite / N / 2
        treppe, vor_ = [], None
        zonen_ = mp_["zonen"]
        # Ausgang je verlassener Zone (aus der Basenhistorie) für den Hinweis am Rahmen
        ausgaenge = {df.index[b["beginn"]].normalize(): b for b in (erk or {}).get("historie") or []}
        for k_, z_ in enumerate(zonen_):
            ende_t = z_["ende"] if k_ < len(zonen_) - 1 else d.index[-1]
            if ende_t < d.index[0]:
                vor_ = z_
                continue
            j0 = pos(z_["beginn"]) if z_["beginn"] >= d.index[0] else 0
            j1 = N - 1 if k_ == len(zonen_) - 1 else pos(z_["ende"])
            x0, x1 = X(j0) - halb, X(j1) + halb
            A(f'<rect x="{x0:.1f}" y="{Y(z_["vah"]):.1f}" width="{x1 - x0:.1f}" height="{Y(z_["val"]) - Y(z_["vah"]):.1f}" '
              f'fill="{BLAU}" fill-opacity="0.11"/>'
              f'<rect x="{x0:.1f}" y="{Y(z_["hoch"]):.1f}" width="{x1 - x0:.1f}" height="{Y(z_["tief"]) - Y(z_["hoch"]):.1f}" '
              f'fill="none" stroke="{BLAU}" stroke-opacity="{0.75 if k_ == len(zonen_) - 1 else 0.35}" stroke-width="1" rx="3">'
              f'<title>Zone {z_["beginn"]:%d.%m.%Y}–{z_["ende"]:%d.%m.%Y}, {z_["wochen"]} Wochen · Rahmen '
              f'{zahl(z_["tief"])}–{zahl(z_["hoch"])} $ · Wert {zahl(z_["val"])}–{zahl(z_["vah"])} $ · POC {zahl(z_["poc"])} $'
              f'{_ausgang_text(ausgaenge.get(df.index[min(int(df.index.searchsorted(z_["beginn"])), len(df) - 1)].normalize()), df)}'
              f'</title></rect>')
            if vor_ is not None and treppe:
                treppe.append((x0, Y(vor_["poc"])))
            treppe += [(x0, Y(z_["poc"])), (x1, Y(z_["poc"]))]
            if vor_ is not None and vor_.get("richtung") and vor_["ende"] >= d.index[0]:
                hoch_ = vor_["richtung"] == "↑"
                ya_ = (Y(vor_["poc"]) + Y(z_["poc"])) / 2
                A(f'<text x="{x0 - 3:.1f}" y="{ya_ + 6:.1f}" fill="{GRUEN if hoch_ else ROT}" font-size="18" '
                  f'font-weight="700" text-anchor="end">{vor_["richtung"]}</text>')
            vor_ = z_
        if len(treppe) >= 2:
            spaete.insert(0, f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in treppe)}" fill="none" '
                             f'stroke="{TREPPE}" stroke-width="2.6" stroke-linejoin="miter"/>')
    else:
        A(f'<text x="{B - RECHTS - 4:.1f}" y="40" fill="{TEXT_3}" font-size="13" text-anchor="end">keine Zonen – '
          f'30-Minuten-Kerzen fehlen (werkzeuge/tpo_laden.py)</text>')
    # Base, Pivot, Kaufzone
    if muster and "start_index" in werte:
        i0 = pos(df.index[werte["start_index"]])
        # Ende der Base: bei einer Form, die vor dem Ausbruch endete, nicht der rechte Rand
        i1 = pos(df.index[werte["ende_index"]]) if "ende_index" in werte else N - 1
        hoch_b = h[i0:i1 + 1].max()
        if pivot:
            # Pivot und Kaufzone beginnen an dem Hoch, das den Pivot setzt (letzte Enge; Doppelboden: Mittelspitze;
            # Cheat: Hoch der Pause) – mit Punkt, damit man sieht, woher der Pivot kommt
            ip = pos(df.index[_pivot_tag(df, werte["start_index"], werte.get("ende_index", len(df) - 1), pivot)])
            A(f'<rect x="{X(ip):.1f}" y="{Y(pivot * 1.05):.1f}" width="{B - RECHTS - X(ip):.1f}" '
              f'height="{Y(pivot) - Y(pivot * 1.05):.1f}" fill="{GRUEN}" fill-opacity="0.14"/>')
            A(f'<line x1="{X(ip):.1f}" x2="{B - RECHTS}" y1="{Y(pivot):.1f}" y2="{Y(pivot):.1f}" '
              f'stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="6 4"/>')
            spaete.append(f'<circle cx="{X(ip):.1f}" cy="{Y(pivot):.1f}" r="4" fill="{TEXT}"/>')
            # Beschriftung links vom Punkt, damit Linie, Zone und Zahl zusammen gelesen werden
            spaete.append(f'<text x="{X(ip) - 8:.1f}" y="{platz(X(ip) - 8, Y(pivot) - 6, f"Pivot {zahl(pivot)}", 13, "end"):.1f}" '
                          f'fill="{TEXT}" font-size="13" text-anchor="end">Pivot {zahl(pivot)}</text>')
            spaete.append(f'<text x="{X(ip) - 8:.1f}" y="{platz(X(ip) - 8, Y(pivot * 1.05) + 4, "Kaufzone +5 %", 13, "end"):.1f}" '
                          f'fill="{GRUEN}" font-size="13" text-anchor="end">Kaufzone +5 %</text>')
        fuss = f'{werte.get("wochen") or round(werte.get("dauer_tage", 0) / 5)} Wochen, Tiefe {zahl(werte.get("tiefe_pct", 0), 0)} %'
        nr = f' Nr. {werte["basenzahl"]}' if werte.get("basenzahl") else ""
        oben_y = min(Y(hoch_b), Y(pivot * 1.05) if pivot else Y(hoch_b)) - 12
        titel_ = f'{basename(muster)}{nr} · {fuss}'
        fh_ = form_hinweis(muster)
        A(f'<text x="{X(N - 1) + 4:.1f}" y="{platz(X(N - 1) + 4, oben_y, titel_, 14, "end"):.1f}" fill="{BLAU}" font-size="14" '
          f'font-weight="600" text-anchor="end">' + (f'<title>{fh_}</title>' if fh_ else "") + f'{titel_}</text>')

    kurz_ = (erk or {}).get("short")
    if kurz_ and "pivot" in werte:
        # Short: Auslöser = Unterkante des Rahmens, Verkaufszone bis −5 % (gespiegelt zur Kaufzone)
        sp_ = werte["pivot"]
        ip_ = pos(df.index[werte["start_index"]]) if df.index[werte["start_index"]] >= d.index[0] else 0
        A(f'<rect x="{X(ip_):.1f}" y="{Y(sp_):.1f}" width="{B - RECHTS - X(ip_):.1f}" '
          f'height="{Y(sp_ * 0.95) - Y(sp_):.1f}" fill="{ROT}" fill-opacity="0.12"/>'
          f'<line x1="{X(ip_):.1f}" x2="{B - RECHTS}" y1="{Y(sp_):.1f}" y2="{Y(sp_):.1f}" stroke="{TEXT}" '
          f'stroke-width="1.5" stroke-dasharray="6 4"/>')
        spaete.append(f'<text x="{X(ip_) - 8:.1f}" y="{platz(X(ip_) - 8, Y(sp_) - 6, f"Auslöser short {zahl(sp_)}", 13, "end"):.1f}" '
                      f'fill="{TEXT}" font-size="13" text-anchor="end">Auslöser short {zahl(sp_)}</text>')
        titel_s = f'Short · {kurz_["art"] if kurz_["art"] != "Base" else "Zone"} {werte.get("wochen")} Wochen, Tiefe {zahl(werte.get("tiefe_pct", 0), 0)} %'
        A(f'<text x="{X(N - 1) + 4:.1f}" y="{platz(X(N - 1) + 4, Y(werte["zone_oberkante"]) - 12, titel_s, 14, "end"):.1f}" '
          f'fill="{ROT}" font-size="14" font-weight="600" text-anchor="end">{titel_s}</text>')

    # Angebot absorbiert: Linie durch die Tiefs der letzten drei Abschnitte und Kasten über der Enge (nur Tageschart)
    ab_ = (erk or {}).get("absorption")
    if ab_ and muster and ebene == "Tag":
        pk_ = [(X(pos(df.index[i_])), Y(x_)) for i_, x_ in ab_["tiefs"] if df.index[i_] >= d.index[0]]
        if len(pk_) >= 2:
            A(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pk_)}" fill="none" stroke="{TEXT_2}" '
              f'stroke-width="1.5" stroke-dasharray="5 3"/>')
        a0_, a1_, eh_, el_, eng_ = ab_["enge"]
        if df.index[a0_] >= d.index[0]:
            xa_, xb_ = X(pos(df.index[a0_])) - 3, X(pos(df.index[a1_])) + 3
            A(f'<rect x="{xa_:.1f}" y="{Y(eh_):.1f}" width="{xb_ - xa_:.1f}" height="{Y(el_) - Y(eh_):.1f}" '
              f'fill="{TEXT_2}" fill-opacity="0.10" stroke="{TEXT_2}" stroke-opacity="0.5" stroke-width="1"/>')
            A(f'<text x="{(xa_ + xb_) / 2:.1f}" y="{platz((xa_ + xb_) / 2, Y(el_) + 30, f"Enge {zahl(eng_, 1)} %", 11, nach_oben=False):.1f}" '
              f'fill="{TEXT_2}" font-size="11" text-anchor="middle">Enge {zahl(eng_, 1)} %</text>')

    pr_a = bahn.get("profil")
    x_knoten = (X(pos(df.index[pr_a["anker"]])) if pr_a and df.index[pr_a["anker"]] >= d.index[0] else LINKS)
    # Freie Bahn: je Seite die nächste Marke – Volumenknoten als blasses Band, früheres Hoch/Tief als Linie;
    # eine Beschriftung je Seite mit der Art der Marke (doppelt, dreifach, dünn, verdeckt)
    for seite_, farbe_ in (("long", ROT), ("short", GRUEN)):
        m_ = bahn.get(seite_) or {}
        if not m_.get("marke"):
            continue
        k_ = (m_.get("knoten") or [None])[0]
        if k_:
            A(f'<rect x="{x_knoten:.1f}" y="{Y(k_[1]):.1f}" width="{B - RECHTS - x_knoten:.1f}" height="{Y(k_[0]) - Y(k_[1]):.1f}" '
              f'fill="{farbe_}" fill-opacity="0.07"/>')
        w_ = (m_.get("wend") or [None])[0]
        if w_ and df.index[w_[0]] >= d.index[0] - pd.Timedelta(days=1100):
            x0_ = X(pos(df.index[w_[0]])) if df.index[w_[0]] >= d.index[0] else LINKS
            A(f'<line x1="{x0_:.1f}" x2="{B - RECHTS}" y1="{Y(w_[1]):.1f}" y2="{Y(w_[1]):.1f}" stroke="{farbe_}" '
              f'stroke-opacity="0.55" stroke-width="1.5" stroke-dasharray="6 4"/>')
        y_ = Y(m_["marke"])
        art_ = (m_.get("art") or "").split(" (")[0]
        text_ = (f'Widerstand {zahl(m_["marke"])} $ {art_} (+{zahl(m_["luft"], 1)} % über dem {"Pivot" if pivot else "Kurs"})'
                 if seite_ == "long" else f'Unterstützung {zahl(m_["marke"])} $ {art_} (−{zahl(m_["luft"], 1)} % unter dem Kurs)')
        spaete.append(f'<text x="{B - RECHTS - 4:.1f}" y="{platz(B - RECHTS - 4, y_ + (-6 if seite_ == "long" else 15), text_, 11, "end", seite_ == "long"):.1f}" '
                      f'fill="{farbe_}" font-size="11" text-anchor="end">{text_}</text>')

    ik_ = bahn.get("im_knoten")
    if ik_:
        A(f'<rect x="{x_knoten:.1f}" y="{Y(ik_[1]):.1f}" width="{B - RECHTS - x_knoten:.1f}" height="{Y(ik_[0]) - Y(ik_[1]):.1f}" '
          f'fill="{TUERKIS}" fill-opacity="0.08"/>')
        spaete.append(f'<text x="{x_knoten + 6:.1f}" y="{platz(x_knoten + 6, Y(ik_[1]) + 14, "Kurs im Knoten 000–000 $ (Balance)", 11, "start", False):.1f}" '
                      f'fill="{TUERKIS}" font-size="11">Kurs im Knoten {zahl(ik_[0])}–{zahl(ik_[1])} $ (Balance)</text>')

    # Volumenprofil in eigener Spalte rechts neben dem Kursbild (verankert am 52-Wochen-Hoch bzw. am Tief)
    pr_ = bahn.get("profil")
    if pr_:
        vmax_ = float(np.max(pr_["volumen"])) or 1.0
        kn_ = pr_.get("knoten") or []
        for g0_, g1_, v_ in zip(pr_["grenzen"][:-1], pr_["grenzen"][1:], pr_["volumen"]):
            if g1_ < pmin or g0_ > pmax:
                continue
            yo_, yu_ = Y(min(g1_, pmax)), Y(max(g0_, pmin))
            # Türkis, Deckkraft nach Stärke: kräftig bei viel Volumen (Knoten), schwach bei wenig (Lücken)
            A(f'<rect x="{PROFIL_X}" y="{yo_ + 0.5:.1f}" width="{PROFIL_B * v_ / vmax_:.1f}" height="{max(0.5, yu_ - yo_ - 1):.1f}" '
              f'fill="{TUERKIS}" fill-opacity="{0.12 + 0.83 * (v_ / vmax_) ** 1.5:.2f}"/>')
        y_poc = Y(pr_["poc"])
        # POC als Linie vom Anker bis zur Profilspalte (der faire Preis seit dem Anker, wirkt wie ein Magnet)
        x_anker = X(pos(df.index[pr_["anker"]])) if df.index[pr_["anker"]] >= d.index[0] else LINKS
        A(f'<line x1="{x_anker:.1f}" x2="{PROFIL_X + PROFIL_B + 4}" y1="{y_poc:.1f}" y2="{y_poc:.1f}" stroke="{TUERKIS}" '
          f'stroke-width="1.2" stroke-dasharray="2 4" stroke-opacity="0.9"/>')
        spaete.append(f'<text x="{x_anker + 4:.1f}" y="{platz(x_anker + 4, y_poc - 5, "POC 000,00 $", 11, "start"):.1f}" '
                      f'fill="{TUERKIS}" font-size="11">POC {zahl(pr_["poc"])} $</text>')
        A(f'<text x="{PROFIL_X + PROFIL_B + 6}" y="{y_poc + 4:.1f}" fill="{TUERKIS}" font-size="11">POC</text>')
        # Wertbereich (70 % des Volumens): Klammer am rechten Rand der Spalte
        for wert_, name_ in ((pr_["wert_oben"], "VAH"), (pr_["wert_unten"], "VAL")):
            if pmin <= wert_ <= pmax:
                A(f'<line x1="{PROFIL_X + PROFIL_B - 6}" x2="{PROFIL_X + PROFIL_B + 4}" y1="{Y(wert_):.1f}" '
                  f'y2="{Y(wert_):.1f}" stroke="{TEXT_2}" stroke-width="1.5"/>'
                  f'<text x="{PROFIL_X + PROFIL_B + 6}" y="{Y(wert_) + 4:.1f}" fill="{TEXT_2}" font-size="11">{name_}</text>')
        A(f'<line x1="{PROFIL_X + PROFIL_B - 1}" x2="{PROFIL_X + PROFIL_B - 1}" y1="{Y(min(pr_["wert_oben"], pmax)):.1f}" '
          f'y2="{Y(max(pr_["wert_unten"], pmin)):.1f}" stroke="{TEXT_2}" stroke-opacity="0.6"/>')
        # Kursmarke: wo der Kurs im Profil steht
        y_k = Y(float(c[-1]))
        A(f'<polygon points="{PROFIL_X - 2},{y_k:.1f} {PROFIL_X - 10},{y_k - 5:.1f} {PROFIL_X - 10},{y_k + 5:.1f}" '
          f'fill="{TEXT}"/>')
        tag_ = df.index[pr_["anker"]]
        A(f'<text x="{PROFIL_X}" y="14" fill="{TEXT_3}" font-size="11">Profil {pr_["anker_art"]}</text>'
          f'<text x="{PROFIL_X}" y="28" fill="{TEXT_3}" font-size="11">seit {tag_:%d.%m.%Y}</text>')

    if crv_:                                     # CRV-Linien im rechten Fünftel: Ziel grün, Stopp A rot gestrichelt, Stopp B rot
        x0_c, x1_c = LINKS + breite * 0.8, B - RECHTS
        lang_ = crv_["seite"] == "long"
        linien_ = []
        if crv_.get("ziel"):
            linien_.append((crv_["ziel"], GRUEN if lang_ else ROT, "", 2,
                            f'Ziel {zahl(crv_["ziel"])} $ ({crv_["art"]})'))
        linien_.append((crv_["stopp_a"], ROT if lang_ else GRUEN, "6 4", 1.5,
                        f'Stopp A {zahl(crv_["stopp_a"])} $' + (f' · CRV {zahl(crv_["crv_a"], 1)} : 1' if crv_.get("crv_a") else "")))
        if crv_.get("stopp_b"):
            linien_.append((crv_["stopp_b"], ROT if lang_ else GRUEN, "", 1.5,
                            f'Stopp B {zahl(crv_["stopp_b"])} $ (1,5 × ATR)'
                            + (f' · CRV {zahl(crv_["crv_b"], 1)} : 1' if crv_.get("crv_b") else "")))
        for preis_, farbe_, strich_, dicke_, text_ in linien_:
            A(f'<line x1="{x0_c:.1f}" x2="{x1_c:.1f}" y1="{Y(preis_):.1f}" y2="{Y(preis_):.1f}" stroke="{farbe_}" '
              f'stroke-width="{dicke_}"' + (f' stroke-dasharray="{strich_}"' if strich_ else "") + '/>')
            spaete.append(f'<text x="{x1_c - 4:.1f}" y="{platz(x1_c - 4, Y(preis_) - 5, text_, 11, "end"):.1f}" '
                          f'fill="{farbe_}" font-size="11" text-anchor="end">{text_}</text>')

    if pivot and bahn.get("long") and not marke_l:
        text_ = "über dem Pivot kein Widerstand (kein früheres Hoch und kein Volumenknoten)"
        A(f'<text x="{B - RECHTS - 4:.1f}" y="{platz(B - RECHTS - 4, Y(pivot) - 6, text_, 11, "end"):.1f}" '
          f'fill="{TEXT_2}" font-size="11" text-anchor="end">{text_}</text>')

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
        pkt = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(r.to_numpy(float)) if not np.isnan(x))
        if pkt:
            A(f'<polyline points="{pkt}" fill="none" stroke="{farbe}" stroke-width="{dicke}"/>')

    for k in kurz[::-1]:
        linie(linien[k], KURZ_FARBE[k], 1.1)
    for k, farbe, dicke in zip(gd[::-1], (SAND, LILA, BLAU), (2.4, 1.6, 1.6)):
        linie(linien[k], farbe, dicke)
    if av is not None:
        linie(av, ORANGE, 2)
    for t_ in spaete:
        A(t_)

    vs = verkaufssignal(df, phasen)
    # Gewinnmeldungen
    for tag, r in reaktionen(df, gewinne):
        if tag < d.index[0]:
            continue
        i = pos(tag)
        y = min(Y(l[i]) + 20, 410)
        farbe = GRUEN if r >= 0 else ROT
        A(f'<circle cx="{X(i):.1f}" cy="{y:.1f}" r="11" fill="#161C24" stroke="{BLAU}"/>'
          f'<text x="{X(i):.1f}" y="{y + 4:.1f}" fill="{BLAU}" font-size="12" text-anchor="middle">E</text>')
        if vs and vs[0] == tag:                  # derselbe Tag trägt schon das Dreieck mit der Zahl
            continue
        xe_ = min(X(i), B - RECHTS - 24)
        A(f'<text x="{xe_:.1f}" y="{platz(xe_, y - 16, "+00,0 %", 12):.1f}" fill="{farbe}" font-size="12" text-anchor="middle">'
          f'{"+" if r >= 0 else "−"}{zahl(abs(r), 1)} %</text>')

    # Verkaufssignal
    if vs and vs[0] >= d.index[0]:
        i = pos(vs[0])
        y = Y(h[i]) - 10
        A(f'<polygon points="{X(i) - 8:.1f},{y - 12:.1f} {X(i) + 8:.1f},{y - 12:.1f} {X(i):.1f},{y:.1f}" fill="{ROT}"/>'
          f'<text x="{X(i):.1f}" y="{platz(X(i), y - 18, "−00,0 %", 12):.1f}" fill="{ROT}" font-size="12" text-anchor="middle">'
          f'{zahl(vs[1], 1)} %</text>')

    # Phasenband
    if phasen is not None and len(phasen):
        ph = phasen.reindex(d.index, method="ffill").fillna(1).astype(int).to_numpy()
        stuecke, start = [], 0
        for i in range(1, N + 1):
            if i == N or ph[i] != ph[start]:
                stuecke.append((start, i))
                start = i
        for a, b in stuecke:
            A(f'<rect x="{X(a) - breite / N / 2:.1f}" y="428" width="{breite * (b - a) / N:.1f}" '
              f'height="10" fill="{PHASENFARBE[ph[a]]}"/>')
            mitte = (X(a) + X(b - 1)) / 2
            if (b - a) / N > 0.06:
                A(f'<text x="{mitte:.1f}" y="452" fill="{TEXT_2}" font-size="12" '
                  f'text-anchor="middle">Phase {ph[a]}</text>')

    # Volumen
    vmax = v.max()
    A(f'<text x="{LINKS}" y="474" fill="{TEXT_3}" font-size="12">VOLUMEN</text>')
    for i in range(N):
        hv = 90 * v[i] / vmax
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{570 - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" '
          f'fill="{GRUEN if c[i] >= o[i] else ROT}" fill-opacity="0.75"/>')
    v50 = voll["Volume"].rolling(50 if ebene == "Tag" else 10).mean().reindex(d.index).to_numpy(float)
    pkt = " ".join(f"{X(i):.1f},{570 - 90 * x / vmax:.1f}" for i, x in enumerate(v50) if not np.isnan(x))
    A(f'<polyline points="{pkt}" fill="none" stroke="{TEXT}" stroke-width="1.2"/>')
    if ebene == "Tag":
        for i in range(max(0, N - 15), N):
            if not np.isnan(v50[i]) and v[i] <= 0.5 * v50[i]:
                A(f'<circle cx="{X(i):.1f}" cy="{570 - 90 * v[i] / vmax - 8:.1f}" r="4" fill="{GELB}"/>')

    # RS-Linien gegen S&P 500 und Sektor: beide links bei 100, gemeinsame Skala
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
            YR = lambda y: 604 + 116 * (1 - (y - lo) / (hi - lo))          # noqa: E731
            vier = 63 if ebene == "Tag" else 13

            kurz_ = 10 if ebene == "Tag" else 3

            def pfeil(r, farbe, name):
                """Dynamik der letzten 10 Tage (3 Wochen) am Linienende: Pfeil und beide Werte (vorher → heute)."""
                g = r[~np.isnan(r)]
                if len(g) <= kurz_:
                    return
                alt, neu = g[-1 - kurz_], g[-1]
                pr = (neu / alt - 1) * 100
                p_ = "↑" if pr >= 3 else "↗" if pr >= 1 else "↓" if pr <= -3 else "↘" if pr <= -1 else "→"
                y = YR(neu)
                A(f'<g><title>{name}: {zahl(alt, 0)} → {zahl(neu, 0)} in {kurz_} {"Tagen" if ebene == "Tag" else "Wochen"} '
                  f'({"+" if pr >= 0 else "−"}{zahl(abs(pr), 1)} %); 100 = so stark wie am linken Rand</title>'
                  f'<text x="{B - RECHTS + 6}" y="{platz(B - RECHTS + 6, y + 5, "↗ 000 → 000", 12, "start"):.1f}" '
                  f'fill="{farbe}" font-size="12"><tspan font-size="15" font-weight="700">{p_}</tspan> '
                  f'{zahl(alt, 0)} → {zahl(neu, 0)}</text></g>')

            A(f'<text x="{LINKS}" y="594" fill="{TEXT_3}" font-size="12">RELATIVE STÄRKE SEIT {d.index[0]:%m/%Y} · '
              f'<tspan fill="{BLAU}">— gegen S&amp;P 500</tspan>'
              + (f'  <tspan fill="{LILA}">- - gegen Sektor {sektor_name}</tspan>' if rk is not None else "")
              + f'  · Pfeil = letzte {kurz_} {"Tage" if ebene == "Tag" else "Wochen"}</text>')
            A(f'<line x1="{LINKS}" x2="{B - RECHTS}" y1="{YR(100):.1f}" y2="{YR(100):.1f}" stroke="{TEXT_3}" '
              f'stroke-width="1" stroke-dasharray="2 4"/>'
              f'<text x="{LINKS - 6}" y="{YR(100) + 4:.1f}" fill="{TEXT_3}" font-size="11" text-anchor="end">100</text>'
              f'<text x="{B - RECHTS}" y="594" fill="{TEXT_3}" font-size="11" text-anchor="end">'
              f'100 = so stark wie der Index</text>')
            if rk is not None:
                A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(rk)
                                                   if not np.isnan(x))
                  + f'" fill="none" stroke="{LILA}" stroke-width="1.5" stroke-dasharray="5 4"/>')
            A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(rs) if not np.isnan(x))
              + f'" fill="none" stroke="{BLAU}" stroke-width="1.8"/>')
            pfeil(rs, BLAU, "gegen S&amp;P 500")
            if rk is not None:
                pfeil(rk, LILA, f"gegen Sektor {sektor_name}")
            # RS-Linie auf neuem Hoch, während der Kurs es noch nicht ist
            letzte = 20 if ebene == "Tag" else 4
            if np.nanmax(rs[-letzte:]) >= np.nanmax(rs) and c[-letzte:].max() < h.max():
                k = N - letzte + int(np.nanargmax(rs[-letzte:]))
                A(f'<circle cx="{X(k):.1f}" cy="{YR(rs[k]):.1f}" r="6" fill="none" stroke="{GRUEN}" stroke-width="2"/>'
                  f'<text x="{X(k) - 10:.1f}" y="{YR(rs[k]) - 10:.1f}" fill="{GRUEN}" font-size="12" '
                  f'text-anchor="end">neues RS-Hoch vor dem Kurs</text>')

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



def legende(erk, ebene="Tag", kurz=()):
    from gestaltung import t
    namen = ("GD50", "GD150", "GD200") if ebene == "Tag" else ("GD10W", "GD30W", "GD40W")
    eintraege = [(BLAU, namen[0]), (LILA, namen[1]), (SAND, namen[2] + " (langfristiger Trend)")]
    if ebene == "Tag":
        eintraege = [(KURZ_FARBE[k], f"GD{k}") for k in (10, 20) if k in kurz] + eintraege
    muster = (erk or {}).get("muster")
    eintraege.append((ORANGE, "AVWAP ab Beginn der Base" if muster else "AVWAP ab dem Hoch"))
    if muster:
        eintraege += [(TEXT, "Pivot"), (GRUEN, "Kaufzone bis +5 %"), (TEXT_2, "Tiefs-Linie und Enge")]
    bahn = (erk or {}).get("bahn") or {}
    if (bahn.get("long") or {}).get("marke"):
        eintraege.append((ROT, "Widerstand: Linie = früheres Hoch, Band = Volumenknoten"))
    if (bahn.get("short") or {}).get("marke"):
        eintraege.append((GRUEN, "Unterstützung: Linie = früheres Tief, Band = Volumenknoten"))
    if (erk.get("werte") or {}).get("pivot") and bahn:
        eintraege.append((GRUEN, "rechts: Ziel = erster fester Widerstand (CRV), Stopp A = Stopp des Setups, "
                                 "Stopp B = 1,5 × ATR außerhalb des Rauschens"))
    if bahn.get("profil"):
        eintraege.append((TUERKIS, "Volumenprofil rechts: kräftig = viel Volumen (Knoten), blass = wenig (Lücke); POC = meistgehandelter Preis (gepunktet im Chart); VAH/VAL = Wertbereich (70 % des Volumens); ▸ = Kurs"))
    if (erk or {}).get("mp"):
        eintraege += [(BLAU, "Zone (Market Profile): Rahmen = Hoch und Tief, Fläche = Wertbereich (70 % der Zeit)"),
                      (TREPPE, "POC-Treppe; ↑/↓ = Wochenwert hat die Zone verlassen")]
        if (erk or {}).get("short"):
            eintraege += [(TEXT, "Auslöser short"), (ROT, "Verkaufszone bis −5 %")]
    eintraege.append((ROT, "▼ größter Tagesrückgang seit Beginn des Anstiegs (O'Neil-Verkaufsregel)"))
    erklaerung = (f'<span title="Zonen nach dem Market Profile (30-Minuten-Kerzen): Rahmen = Hoch und Tief der Zone, '
                  f'Fläche = Wertbereich (70 % der Zeit), orange Treppe = POC je Zone, ↑/↓ = Wochenwert hat die Zone '
                  f'verlassen; die hellere Zone ist die laufende. Punkt = Hoch, das den Pivot setzt. Auslöser und '
                  f'frühere Ausgänge stehen in „Strömung in der Zone“ und „Frühere Basen“." '
                  f'style="font-size:13px;color:{TEXT_3};cursor:help">ⓘ Lesehilfe</span>')
    return erklaerung + "".join(f'<span style="display:inline-flex;align-items:center;gap:8px;font-size:14px;color:{TEXT_2}">'
                   f'<span style="width:18px;height:4px;border-radius:2px;background:{f}"></span>{t(n)}</span>'
                   for f, n in eintraege)
