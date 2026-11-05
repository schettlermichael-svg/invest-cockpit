"""Der Chart der Titelseite als SVG – grüne Null (05.11.2026): nur, was nach O'Neil, Minervini und Weinstein die
Richtung zeigt.

Hauptfenster: Kerzen, GD50/150/200 (Woche: GD10W/30W/40W), Zonen des Market Profile mit POC-Treppe, Pivot und Kaufzone
bis +5 % bzw. Auslöser short, Zahlentermine mit Reaktion, rotes Dreieck beim größten Tagesrückgang seit Beginn von
Phase 2, Phasenband; rechts eine eigene Spalte für die Beschriftungen von Pivot, Stopps und nächstem Widerstand, ganz
rechts das Volumenprofil der letzten 52 Wochen.
Darunter Volumen mit 50er-Schnitt und ruhigen Tagen, ganz unten die relative Stärke gegen den S&P 500 und gestrichelt
gegen den eigenen Sektor-ETF (beide links bei 100).
"""
import numpy as np
import pandas as pd


from gestaltung import BLAU, GELB, GRAU, GRUEN, LILA, RAND, ROT, TEXT, TEXT_2, TEXT_3, basename, form_hinweis, zahl

MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
PHASENFARBE = {1: GRAU, 2: GRUEN, 3: GELB, 4: ROT}
B, LINKS, RECHTS = 1344, 64, 104
PROFIL_X, PROFIL_B = 1344 - 96, 70   # Spalte des 52-Wochen-Volumenprofils ganz rechts
TUERKIS = "#2EC4B6"          # Volumenprofil
ETIKETT = 200               # eigene Spalte rechts neben den Kerzen nur für Preis-Beschriftungen (nichts überlappt)
TREPPE = "#FFA657"           # POC-Treppe der Market-Profile-Zonen
SAND = "#D9B26F"             # GD200 / GD40W: Trennlinie des langfristigen Trends, kräftig

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


def chart(df, ebene="Tag", erk=None, phasen=None, index=None, gewinne=None, ausschnitt=None, sektor=None, sektor_name=""):
    """Kurschart der grünen Null (05.11.2026): nur, was nach O'Neil, Minervini und Weinstein die Richtung zeigt –
    Kerzen, Volumen, GD50/150/200, Zonen mit Pivot bzw. Auslöser, RS-Linie gegen den Markt, Verkaufssignal, Zahlen,
    Phasenband; dazu die Stopps und der nächste Widerstand (kein festes Ziel). ausschnitt: Knopf aus AUSSCHNITT (z. B. „6 M“)."""
    werte = (erk or {}).get("werte", {})
    muster = (erk or {}).get("muster", [])
    voll = df if ebene == "Tag" else _woche(_verlaengert(df))
    n_zeigen = AUSSCHNITT[ebene].get(ausschnitt or AUSSCHNITT_START[ebene], AUSSCHNITT[ebene][AUSSCHNITT_START[ebene]])
    gd = (50, 150, 200) if ebene == "Tag" else (10, 30, 40)
    linien = {k: voll["Close"].rolling(k).mean() for k in gd}
    d = voll.iloc[-n_zeigen:]
    N = len(d)
    o, h, l, c, v = (d[s].to_numpy(float) for s in ("Open", "High", "Low", "Close", "Volume"))
    breite = B - LINKS - RECHTS - ETIKETT
    ENDE = LINKS + breite                        # rechtes Ende der Kerzen; dahinter die Etikettenspalte

    def X(i):
        return LINKS + breite * (i + 0.5) / N

    def pos(tag):
        """Index des Balkens, der den Tag enthält (Woche: Freitag danach)."""
        i = int(d.index.searchsorted(pd.Timestamp(tag)))
        return min(i, N - 1)

    pivot = werte.get("pivot") if muster else None

    try:                                         # Stopp A, Stopp B und nächster Widerstand als Linien rechts im Chart
        import atr as atr_modul
        import stopps as stopps_modul
        st_ = stopps_modul.linien(erk or {}, atr_modul.wert(df), df)
    except Exception:  # noqa: BLE001
        st_ = None
    w_st = (st_ or {}).get("widerstand")
    crv_preise = [x for x in ((st_ or {}).get(k) for k in ("stopp_a", "stopp_b")) if x] + \
        ([w_st[0]] if w_st and 0.75 <= w_st[0] / float(c[-1]) <= 1.3 else [])
    oben = [h.max()] + ([pivot * 1.06] if pivot else [])
    unten = [l.min()]
    oben, unten = oben + crv_preise, unten + crv_preise
    pmax, pmin = max(oben) * 1.03, min(unten) * 0.95

    def Y(y):
        return 44 + 376 * (1 - (np.log(y) - np.log(pmin)) / (np.log(pmax) - np.log(pmin)))   # oben 44: Kopfleiste fürs Setup

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

    spalte = []                                  # Etiketten der Preislinien, am Ende von oben nach unten gesetzt

    def etikett(preis, text, farbe, fett=False):
        """Beschriftung einer Preislinie in der Etikettenspalte rechts; gesetzt wird am Schluss in Preisfolge, jedes so
        nah wie möglich an seiner Linie, ohne Überlappung (Reihenfolge bleibt wie die Linien)."""
        spalte.append((float(preis), text, farbe, fett))

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
            letzte_z = k_ == len(zonen_) - 1
            A(f'<rect x="{x0:.1f}" y="{Y(z_["vah"]):.1f}" width="{x1 - x0:.1f}" height="{Y(z_["val"]) - Y(z_["vah"]):.1f}" '
              f'fill="{BLAU}" fill-opacity="0.11"/>'
              f'<rect x="{x0:.1f}" y="{Y(z_["hoch"]):.1f}" width="{x1 - x0:.1f}" height="{Y(z_["tief"]) - Y(z_["hoch"]):.1f}" '
              f'fill="none" stroke="{BLAU}" stroke-opacity="{0.9 if letzte_z else 0.45}" stroke-width="1" rx="3">'
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
        if pivot:
            # Pivot und Kaufzone beginnen an dem Hoch, das den Pivot setzt (letzte Enge; Doppelboden: Mittelspitze;
            # Cheat: Hoch der Pause) – mit Punkt, damit man sieht, woher der Pivot kommt
            ip = pos(df.index[_pivot_tag(df, werte["start_index"], werte.get("ende_index", len(df) - 1), pivot)])
            A(f'<rect x="{X(ip):.1f}" y="{Y(pivot * 1.05):.1f}" width="{ENDE - X(ip):.1f}" '
              f'height="{Y(pivot) - Y(pivot * 1.05):.1f}" fill="{GRUEN}" fill-opacity="0.14"/>')
            A(f'<line x1="{X(ip):.1f}" x2="{ENDE + 4}" y1="{Y(pivot):.1f}" y2="{Y(pivot):.1f}" '
              f'stroke="{TEXT}" stroke-width="1.5" stroke-dasharray="6 4"/>')
            spaete.append(f'<circle cx="{X(ip):.1f}" cy="{Y(pivot):.1f}" r="4" fill="{TEXT}"/>')
            etikett(pivot, f"Pivot {zahl(pivot)} $", TEXT, True)
            etikett(pivot * 1.05, "Kaufzone bis +5 %", GRUEN)
        wo_ = werte.get("wochen") or round(werte.get("dauer_tage", 0) / 5)
        fuss = f'{wo_} {"Woche" if wo_ == 1 else "Wochen"}, Tiefe {zahl(werte.get("tiefe_pct", 0), 0)} %'
        nr = f' · Base Nr. {werte["basenzahl"]}' if werte.get("basenzahl") else ""
        titel_ = f'{basename(muster)}{nr} · {fuss}'
        fh_ = form_hinweis(muster)
        spaete.append(f'<text x="{B - RECHTS:.1f}" y="{platz(B - RECHTS, 26, titel_, 14, "end", False):.1f}" fill="{BLAU}" '
                      f'font-size="14" font-weight="600" text-anchor="end">' + (f'<title>{fh_}</title>' if fh_ else "")
                      + f'{titel_}</text>')

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


    # Volumenprofil in eigener Spalte rechts neben dem Kursbild – die letzten 52 Wochen: wo die Masse der Ware liegt
    # (POC = Magnet, VAH/VAL = Wertbereich 70 % des Volumens); passt zum 52-Wochen-Fenster für Widerstände
    pr_ = (erk or {}).get("profil")
    if pr_:
        vmax_ = float(np.max(pr_["volumen"])) or 1.0
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
        # Knoten (viel Volumen = akzeptierter Preis) als blasse Bänder im Kursbild ab Beginn der 52 Wochen: der nächste
        # darüber rot (Widerstand), der nächste darunter grün (Unterstützung); steht der Kurs in einem Knoten, türkis
        kurs_ = float(c[-1])
        kn_ = pr_.get("knoten") or []
        im_ = next((k for k in kn_ if k[0] <= kurs_ <= k[1]), None)
        ueber_ = min((k for k in kn_ if k[0] > kurs_), key=lambda k: k[0], default=None)
        unter_ = max((k for k in kn_ if k[1] < kurs_), key=lambda k: k[1], default=None)
        for k_, farbe_k, deck_ in ((ueber_, ROT, 0.08), (unter_, GRUEN, 0.08), (im_, TUERKIS, 0.10)):
            if k_ and k_[1] >= pmin and k_[0] <= pmax:
                yo_k, yu_k = Y(min(k_[1], pmax)), Y(max(k_[0], pmin))
                s.insert(1, f'<rect x="{x_anker:.1f}" y="{yo_k:.1f}" width="{ENDE - x_anker:.1f}" height="{yu_k - yo_k:.1f}" '
                            f'fill="{farbe_k}" fill-opacity="{deck_}"><title>Volumenknoten {zahl(k_[0])}–{zahl(k_[1])} $'
                            f'</title></rect>')
        if im_:
            t_im = f"Kurs im Knoten {zahl(im_[0])}–{zahl(im_[1])} $ (Balance)"
            spaete.append(f'<text x="{x_anker + 6:.1f}" y="{platz(x_anker + 6, Y(min(im_[1], pmax)) + 14, t_im, 11, "start", False):.1f}" '
                          f'fill="{TUERKIS}" font-size="11">{t_im}</text>')
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
        if tag_ >= d.index[0]:                    # Beginn des 52-Wochen-Fensters (Profil und Widerstände vor dem Ziel)
            s.insert(1, f'<line x1="{x_anker:.1f}" x2="{x_anker:.1f}" y1="44" y2="420" stroke="{TEXT_3}" stroke-width="1" '
                        f'stroke-dasharray="1 5" stroke-opacity="0.8"/>')
            A(f'<text x="{x_anker + 4:.1f}" y="56" fill="{TEXT_3}" font-size="11">52 Wochen ab {tag_:%d.%m.%y}</text>')
        A(f'<text x="{PROFIL_X}" y="14" fill="{TEXT_3}" font-size="11">Profil {pr_["anker_art"]}</text>'
          f'<text x="{PROFIL_X}" y="28" fill="{TEXT_3}" font-size="11">seit {tag_:%d.%m.%Y}</text>')

    if st_:                                      # Stopps rechts: A rot gestrichelt, B rot; nächster Widerstand gelb gepunktet
        x0_c, x1_c = LINKS + breite * 0.8, ENDE + 4
        lang_ = st_["seite"] == "long"
        e_ = st_["einstieg"]
        linien_ = [(st_["stopp_a"], ROT if lang_ else GRUEN, "6 4", 1.5,
                    f'Stopp A {zahl(st_["stopp_a"])} $ · {zahl(st_["risiko_a"] / e_ * 100, 1)} %'
                    + (f' · CRV {zahl(st_["crv_a"], 1)}' if st_.get("crv_a") else ""))]
        if st_.get("stopp_b"):
            linien_.append((st_["stopp_b"], ROT if lang_ else GRUEN, "", 1.5,
                            f'Stopp B {zahl(st_["stopp_b"])} $ · {zahl(st_["risiko_b"] / e_ * 100, 1)} %'
                            + (f' · CRV {zahl(st_["crv_b"], 1)}' if st_.get("crv_b") else "")))
        if w_st and pmin <= w_st[0] <= pmax:      # erste Hürde (Weinstein/AMT): Maß fürs CRV, kein Ausstieg
            art_w = w_st[1].split(" ")[0] if w_st[1].startswith("Volumenknoten") else w_st[1]
            linien_.append((w_st[0], GELB, "2 3", 1.4, f'1. Hürde {zahl(w_st[0])} $ · {art_w}'))
        for preis_, farbe_, strich_, dicke_, text_ in linien_:
            A(f'<line x1="{x0_c:.1f}" x2="{x1_c:.1f}" y1="{Y(preis_):.1f}" y2="{Y(preis_):.1f}" stroke="{farbe_}" '
              f'stroke-width="{dicke_}"' + (f' stroke-dasharray="{strich_}"' if strich_ else "") + '/>')
            etikett(preis_, text_, farbe_, True)

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

    for k, farbe, dicke in zip(gd[::-1], (SAND, LILA, BLAU), (2.4, 1.6, 1.6)):
        linie(linien[k], farbe, dicke)
    y_frei = 0.0                                 # Etikettenspalte: von oben nach unten, mindestens 13 px Abstand
    for preis_, text_, farbe_, fett_ in sorted(spalte, key=lambda e: -e[0]):
        y_ = max(Y(preis_) + 4, y_frei + 13)
        y_frei = y_
        spaete.append(f'<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{farbe_}" font-size="11"'
                      + (' font-weight="600"' if fett_ else "") + f'>{text_}</text>')
    for t_ in spaete:
        A(t_)

    vs = verkaufssignal(df, phasen)
    # Gewinnmeldungen wie bei TradingView: „E“ unter dem Volumen, feine gestrichelte Linie nach oben durch Volumen und Kurs
    # (unter allem anderen gezeichnet), daneben die Reaktion des ersten Tages
    for tag, r in reaktionen(df, gewinne):
        if tag < d.index[0]:
            continue
        i = pos(tag)
        farbe = GRUEN if r >= 0 else ROT
        s.insert(1, f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="44" y2="572" stroke="{BLAU}" stroke-width="1" '
                    f'stroke-dasharray="2 4" stroke-opacity="0.45"/>')
        A(f'<circle cx="{X(i):.1f}" cy="582" r="8" fill="#161C24" stroke="{BLAU}"/>'
          f'<text x="{X(i):.1f}" y="586" fill="{BLAU}" font-size="11" text-anchor="middle">E</text>'
          f'<title>Zahlen am {tag:%d.%m.%Y}: erster Tag {"+" if r >= 0 else "−"}{zahl(abs(r), 1)} %</title>')
        if vs and vs[0] == tag:                  # derselbe Tag trägt schon das Dreieck mit der Zahl
            continue
        A(f'<text x="{X(i) + 11:.1f}" y="586" fill="{farbe}" font-size="11">{"+" if r >= 0 else "−"}{zahl(abs(r), 1)} %</text>')

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

    # RS-Linien gegen den S&P 500 und gestrichelt gegen den Sektor-ETF, beide links bei 100, gemeinsame Skala (O'Neil: macht
    # die RS-Linie neue Hochs vor dem Kurs, führt der Titel; gegen den Sektor: führt er seine Gruppe oder läuft er nur mit)
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
                y = YR(neu)
                A(f'<g><title>{name}: {zahl(alt, 0)} → {zahl(neu, 0)} in {kurz_} {"Tagen" if ebene == "Tag" else "Wochen"} '
                  f'({"+" if pr >= 0 else "−"}{zahl(abs(pr), 1)} %); 100 = so stark wie am linken Rand</title>'
                  f'<text x="{ENDE + 8:.1f}" y="{platz(ENDE + 8, y + 5, "↗ 000 → 000", 12, "start"):.1f}" '
                  f'fill="{farbe}" font-size="12"><tspan font-size="15" font-weight="700">{p_}</tspan> '
                  f'{zahl(alt, 0)} → {zahl(neu, 0)}</text></g>')

            A(f'<text x="{LINKS}" y="608" fill="{TEXT_3}" font-size="12">RELATIVE STÄRKE SEIT {d.index[0]:%m/%Y} · '
              f'<tspan fill="{BLAU}">— gegen S&amp;P 500</tspan>'
              + (f'  <tspan fill="{LILA}">- - gegen Sektor {sektor_name}</tspan>' if rk is not None else "")
              + f'  · Pfeil = letzte {kurz_} {"Tage" if ebene == "Tag" else "Wochen"}</text>')
            A(f'<line x1="{LINKS}" x2="{ENDE}" y1="{YR(100):.1f}" y2="{YR(100):.1f}" stroke="{TEXT_3}" '
              f'stroke-width="1" stroke-dasharray="2 4"/>'
              f'<text x="{LINKS - 6}" y="{YR(100) + 4:.1f}" fill="{TEXT_3}" font-size="11" text-anchor="end">100</text>'
              f'<text x="{B - RECHTS}" y="608" fill="{TEXT_3}" font-size="11" text-anchor="end">'
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



def legende(erk, ebene="Tag"):
    from gestaltung import t
    namen = ("GD50", "GD150", "GD200") if ebene == "Tag" else ("GD10W", "GD30W", "GD40W")
    eintraege = [(BLAU, namen[0]), (LILA, namen[1]), (SAND, namen[2] + " (langfristiger Trend)")]
    if (erk or {}).get("muster"):
        eintraege += [(TEXT, "Pivot"), (GRUEN, "Kaufzone bis +5 %"), (TEXT_2, "Tiefs-Linie und Enge")]
    if (erk or {}).get("mp"):
        eintraege += [(BLAU, "Zone (Market Profile): Rahmen = Hoch und Tief, Fläche = Wertbereich (70 % der Zeit)"),
                      (TREPPE, "POC-Treppe; ↑/↓ = Wochenwert hat die Zone verlassen")]
    if (erk.get("werte") or {}).get("pivot"):
        eintraege += [(ROT, "rechts: Stopp A = Stopp des Setups, Stopp B = 1,5 × ATR (Abstand vom Einstieg in %); "
                                "CRV = Abstand bis zur 1. Hürde ÷ Stoppabstand – Gewinne laufen lassen, Stopp nachziehen"),
                      (GELB, "1. Hürde (Weinstein, Auction Market Theory): altes Hoch der letzten 52 Wochen, fallender "
                             "GD150/GD200 oder nächster Volumenknoten – die nächste davon; senkrechte Punktlinie = Beginn "
                             "der 52 Wochen")]
    if (erk or {}).get("profil"):
        eintraege += [(TUERKIS, "Volumenprofil 52 Wochen rechts: kräftig = viel Volumen, blass = wenig; POC = "
                                "meistgehandelter Preis (gepunktet im Chart); VAH/VAL = Wertbereich (70 % des Volumens); "
                                "▸ = Kurs"),
                      (TUERKIS, "Volumenknoten als blasses Band: rot = nächster darüber (Widerstand), grün = nächster "
                                "darunter (Unterstützung), türkis = Kurs im Knoten (Balance)")]
    eintraege.append((ROT, "▼ größter Tagesrückgang seit Beginn des Anstiegs (O'Neil-Verkaufsregel)"))
    erklaerung = (f'<span title="Zonen nach dem Market Profile (30-Minuten-Kerzen): Rahmen = Hoch und Tief der Zone, '
                  f'Fläche = Wertbereich (70 % der Zeit), orange Treppe = POC je Zone, ↑/↓ = Wochenwert hat die Zone '
                  f'verlassen; die hellere Zone ist die laufende. Punkt = Hoch, das den Pivot setzt. Auslöser und '
                  f'frühere Ausgänge stehen in „Strömung in der Zone“ und „Frühere Basen“." '
                  f'style="font-size:13px;color:{TEXT_3};cursor:help">ⓘ Lesehilfe</span>')
    return erklaerung + "".join(f'<span style="display:inline-flex;align-items:center;gap:8px;font-size:14px;color:{TEXT_2}">'
                   f'<span style="width:18px;height:4px;border-radius:2px;background:{f}"></span>{t(n)}</span>'
                   for f, n in eintraege)
