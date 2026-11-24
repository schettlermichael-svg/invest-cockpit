"""Der Zonenchart (Micky 21.11.2026): wenig, aber aussagekräftig – dasselbe Bild für Woche, Tag und Stunde.

Kursfeld: Kerzen; die Zone von heute (Base nach Minervini/O'Neil, in der Stunde die Balance) als gelber Rahmen mit
Namen, Pivot und POC; in der Stunde die
Base des Tages als feiner Rahmen; Festungen und Schluchten quer über das Gelände; der Trade (Einstieg, Stopp, Ziel); nach Wahl Durchschnitte und
der eigene AVWAP (zwei Anker, Zange). Rechts das eine Profil der Ebene: Zeit und Volumen gespiegelt, ab Beginn des
Impulses. Darunter das Volumen und das Feld der
relativen Stärke gegen den S&P 500 und gestrichelt gegen den Sektor (Punkte RS-Hoch bzw. RS-Tief vor Kurs)."""
import numpy as np
import pandas as pd

from gestaltung import AMPEL, BLAU, GRUEN, LILA, RAND, ROT, TEXT_2, TEXT_3, t as t_esc, zahl

B = 1200                               # Layout: Breite des Bildes
LINKS, RECHTS, PROFIL_W = 56, 190, 110  # Layout: Preisachse, Etiketten, Profil (Zeit links, Volumen rechts)
OBEN, KURS_H = 16, 360                 # Layout: Kursfeld
VOL_H, RS_H = 60, 90                   # Layout: Volumen, relative Stärke
ZEICHEN_H = 22                         # Layout: Zeichenleiste unter dem Volumen
LUECKE = 14                            # Layout: Abstand zwischen den Feldern
ZEIGEN = {"Woche": 104, "Tag": 126, "Stunde": 140}   # Kerzen im Bild (2 Jahre, 6 Monate, 20 Handelstage)
JAHR = {"Woche": 52, "Tag": 252, "Stunde": 252 * 7}  # Kerzen je Jahr (RS-Hoch vor Kurs)
PFEIL_N = 10                           # RS-Pfeil: die letzten 10 Kerzen
PFEIL_LEICHT, PFEIL_STARK = 1, 3       # ↗/↘ ab 1 %, ↑/↓ ab 3 % (wie bisher im Cockpit)
ZONE_FARBE = "#EDA100"                 # Zone wie in Vorwalds Bildern gelb
POC_FARBE = "#1BAF7A"
WOCHE_FARBE = "#7DB4FF"
EINSTIEG_FARBE = "#E6EAF0"
RS_HOCH_FARBE, RS_TIEF_FARBE = "#FFD166", "#FF6B6B"
GD_FARBE = {10: "#F0883E", 20: "#FF7EB6", 50: BLAU, 150: LILA, 200: "#D9B26F"}   # wie bisher im Cockpit
GD_WAHL = (10, 20, 50, 150, 200)
ANKER_FARBE = ("#4DD0E1", "#FF8A65")   # eigener AVWAP: Anker 1 türkis, Anker 2 orange
ZEIT_FARBE = LILA                      # Zeitprofil (Market Profile)
LINIEN_WAHL = {"details": "Profil-Details"}
FESTUNG_FARBE = "#C9D1DC"              # Festungen der Lagekarte
SCHLUCHT_ETIKETTEN = 2                 # Layout: höchstens 2 Schluchten beschriftet (die breitesten)
WERT_FARBE = "#E6EAF0"                 # VAH, VAL
DUENN_FARBE = "#7DB4FF"                # dünne Stellen (LVN)
EINZEL_FARBE = "#FFFFFF"               # Einzeldrucke im Zeitprofil
LVN_ETIKETTEN = 3                      # Layout: höchstens 3 dünne Stellen beschriftet (die breitesten)
STOPP_BAND = 0.25                      # Layout: Festung als Band von ¼ ATR
RAND_SPIEL = 0.04                      # Layout: 4 % Luft über und unter den Kursen
WENDE_FARBE = "#9AA7B8"                # Wendepunkte (Schwunghochs und -tiefs ab 2 ATR)
SCHNITT_FARBE = "#E6EAF0"              # Volumen-Schnitt als weiße Linie
VOL_DECKEL = 3.0                       # Layout: Volumen-Achse bis zum 3-fachen des höchsten Schnitts
VOL_SCHNITT = {"Tag": 50, "Woche": 10, "Stunde": 50}   # Kerzen im Volumen-Schnitt (O'Neil: 50 Tage, 10 Wochen)
EINHEIT = {"Tag": "T.", "Woche": "Wo.", "Stunde": "Std."}       # kurz: unter dem Profil ist nur seine Breite Platz
ZEILE = 14                             # Layout: Abstand der Etiketten rechts
ETIKETT_SUCHE = 60                     # Technik: so viele Plätze sucht ein Etikett, dann ans Ende
URTEIL_BREITE = 8                      # Layout: Breite je Zeichen des Enge-Urteils (12 px)
KERZE_WORT = {"Tag": ("am Tag", "am Tag danach"), "Woche": ("in der Woche", "in der Woche danach")}
PIVOT_FARBE = "#FFFFFF"                # der Pivot: gestrichelt weiß über allem
PIVOT_BLASS = 0.45                     # Layout: Deckkraft des möglichen Pivots ohne Setup
PIVOT_GLEICH = 0.001                   # Technik: der Wendepunkt des Pivots – Hoch bis 0,1 % am Pivot
TRICHTER_DECK = 0.10                   # Layout: Füllung des Trichters
ENGE_FARBE = "#5DCAA5"                 # Korridor der Enge
KORRIDOR_DECK = 0.12                   # Layout: Füllung des Korridors
ENGE_SCHNITT = 10                      # Korridor über 10 Kerzen (wie der GD10: kurz genug für die Enge)
NAME_BREITE = 10                       # Layout: Breite je Buchstabe des Zonennamens (16 px fett)


def _pfeil(r):
    g = r[~np.isnan(r)]
    if len(g) <= PFEIL_N:
        return ""
    alt, neu = g[-1 - PFEIL_N], g[-1]
    p = (neu / alt - 1) * 100
    z = "↑" if p >= PFEIL_STARK else "↗" if p >= PFEIL_LEICHT else "↓" if p <= -PFEIL_STARK else "↘" if p <= -PFEIL_LEICHT else "→"
    return f"{z} {alt:.0f} → {neu:.0f}"


def nummer(df, tag):
    """Balkennummer von rechts (1 = letzte Kerze) zu einem Zeitpunkt der Ebene."""
    return len(df) - int(df.index.searchsorted(pd.Timestamp(tag)))


def zeitpunkt(df, nr):
    """Zeitpunkt der Kerze mit Balkennummer nr (von rechts), oder None außerhalb."""
    return df.index[len(df) - int(nr)] if 1 <= int(nr) <= len(df) else None


def _zahlentage(tk):
    """Vergangene Zahlentage (gemeldete Gewinne) und der nächste Termin aus dem Zwischenspeicher der Fundamentaldaten,
    ohne Abruf → ([Zeitpunkte], nächster Termin oder None)."""
    import json
    import os
    import quellen
    pfad = os.path.join(quellen.SPEICHER, f"{tk.upper()}.json")
    try:
        aus = quellen._aus_json(json.load(open(pfad, encoding="utf-8")))
    except (OSError, ValueError):
        return [], None
    g = aus.get("gewinne")
    tage = []
    if g is not None and len(g):
        idx = pd.to_datetime(g.index, errors="coerce", utc=True).tz_convert(None).normalize()
        heute = pd.Timestamp.today().normalize()
        tage = sorted({t_ for t_, eps in zip(idx, g.get("eps", pd.Series(index=g.index, dtype=float)))
                       if t_ is not pd.NaT and t_ <= heute and eps == eps})
    t = aus.get("termin")
    naechster = None
    if t is not None and len(t) and "datum" in t:
        n_ = pd.to_datetime(t["datum"].iloc[0], errors="coerce")
        naechster = None if pd.isna(n_) else pd.Timestamp(n_).tz_localize(None).normalize() if pd.Timestamp(n_).tzinfo \
            else pd.Timestamp(n_).normalize()
    return tage, naechster


def bild(e, la, t=None, laufend=False, woche=None, rs=None, gd=(), anker=(), linien_=(), profil=None, fest=None,
         ba=None, tk=None):
    """SVG einer Ebene. e = tiefe.ebene, la = zonen.lage, t = zonen.trade (nur Tag),
    woche = (Lage der Wochenzone, Beginn) für den Tageschart, rs = {"index": Kurse, "sektor": Kurse oder None},
    gd = gewählte Durchschnitte (Kerzen der Ebene), anker = bis zu zwei Zeitpunkte für den eigenen AVWAP (Micky
    21.11.2026: selbst verankert; beide gesetzt = Zange), linien_ = gewählte POC-Linien (LINIEN_WAHL), profil = Profil
    am eigenen Anker (zonen.profil_seit) statt des Profils ab Beginn der Zone, fest = zonen.festungen der Ebene; woche =
    (Lage, Beginn, Name) der höheren Ebene als Rahmen (nur in der Stunde: die Base des Tages). Aufgeräumt 22.11.2026:
    ohne PbD, Phasenband, Szenarien, Gedächtnis, Treppe, Wanderung, Korridor und alte Zonen-Kästen.
    Der Zirkel im Chart (Micky 22.11.2026): Wendepunkte (Schwunghochs und -tiefs ab 2 ATR, vcp_zone.zigzag – dieselbe
    Rechnung wie Zone, Enge und Festungen) als Punkte; der eine Pivot als gestrichelte weiße Linie (blass ohne Setup) und als Raute auf seinem Wendepunkt (Micky 23.11.2026),
    die Kontraktionen der Enge (ba = zonen.basis, Woche und Tag) als Zahlen, ✈️ freie Bahn als Etikett, darunter die
    Zeichenleiste (🦬 Ausbruch, 🦊 Fehlausbruch, 🏜️ leisester Tag seit 50 Kerzen, ⚡ Kraft ohne Weg, am Ende der Halt der
    Phase) und Momentum 🚀 am Ende der RS-Linie (tk = Ticker für Zirkel und Momentum)."""
    import avwap
    import rueckenwind
    import tiefe
    import zeichen
    import zonen
    if not e or not la:
        return f'<p style="color:{TEXT_2}">ungemessen – zu wenige Kerzen</p>'
    df = e["df"]
    n0 = max(0, len(df) - ZEIGEN[e["name"]])
    if la.get("beginn") is not None:               # die ganze Zone im Bild
        n0 = min(n0, int(df.index.searchsorted(la["beginn"])))
    d = df.iloc[n0:]
    N = len(d)
    o, h, l, c, v = (d[k].to_numpy(float) for k in ("Open", "High", "Low", "Close", "Volume"))
    lo, hi = la["zone"] or (None, None)
    werte = [h.max(), l.min()] + ([lo, hi] if la["zone"] else []) + ([t["einstieg"], t["stopp"]] if t else [])
    spanne_bild = float(h.max() - l.min())
    burgen = [(x, seite_) for seite_ in ("oben", "unten") for x in (fest or {}).get(seite_, [])
              if l.min() - spanne_bild <= x["preis"] <= h.max() + spanne_bild]          # Layout: höchstens eine Bildhöhe weit
    werte += [x["preis"] for x, _ in burgen]
    if woche:
        werte += list(woche[0]["zone"])
    linien = {g: df["Close"].rolling(g).mean().reindex(d.index) for g in gd}
    eigene = [avwap.reihe(df, a_).reindex(d.index) if a_ is not None else None for a_ in anker]
    for r_ in list(linien.values()) + [x for x in eigene if x is not None]:
        werte += [float(x) for x in r_.dropna() if l.min() * 0.7 <= x <= h.max() * 1.3]   # Layout: wie LINIEN_SPIEL
    pmin, pmax = min(werte), max(werte)
    rand = (pmax - pmin) * RAND_SPIEL or 1
    pmin, pmax = pmin - rand, pmax + rand
    ende = B - RECHTS - PROFIL_W
    breite = ende - LINKS
    NZ = N
    X = lambda i: LINKS + breite * (i + 0.5) / NZ                                  # noqa: E731  # Layout
    Y = lambda y: OBEN + KURS_H * (1 - (y - pmin) / (pmax - pmin))                 # noqa: E731
    pos = lambda t_: min(max(int(d.index.searchsorted(pd.Timestamp(t_))), 0), N - 1)   # noqa: E731
    halb = breite / NZ / 2
    y_vol = OBEN + KURS_H + LUECKE
    y_zei = y_vol + VOL_H + 4                                                       # Layout: Zeichenleiste
    y_rs = y_zei + ZEICHEN_H + LUECKE + 14                                          # Layout: Platz für die Überschrift
    H = y_rs + RS_H + 24                                                            # Layout: Zeitachse
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B} {H}" width="100%" role="img" '
         f'aria-label="Zonenchart {e["name"]}" style="display:block;font-family:IBM Plex Sans,sans-serif">'
         '<style>text{paint-order:stroke;stroke:#161C24;stroke-width:4px;stroke-linejoin:round}</style>'
         '<defs><marker id="spitze" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
         'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke"/></marker></defs>']
    A = s.append
    for k in range(5):                                                              # Layout: 5 Preislinien
        y_ = pmin + (pmax - pmin) * k / 4                                           # Layout
        A(f'<line x1="{LINKS}" x2="{ende}" y1="{Y(y_):.1f}" y2="{Y(y_):.1f}" stroke="{RAND}"/>'
          f'<text x="{LINKS - 6}" y="{Y(y_) + 4:.1f}" fill="{TEXT_3}" font-size="11" text-anchor="end">{y_:.0f}</text>')  # Layout
    etiketten = []                                                                  # (y, Text, Farbe) rechts
    pr = profil or la["profil"]                                                     # das eine Profil (auch für das Gelände)
    det_g = zonen.profil_details(pr)
    for a_, b_ in det_g["duenn"]:                                                   # Schluchten quer über das Gelände
        if b_ >= pmin and a_ <= pmax:
            A(f'<rect x="{LINKS}" y="{Y(min(b_, pmax)):.1f}" width="{ende - LINKS}" height="{max(1, Y(max(a_, pmin)) - Y(min(b_, pmax))):.1f}" '
              f'fill="{DUENN_FARBE}" fill-opacity="0.07"/>')                         # Layout
    for a_, b_ in sorted(det_g["duenn"], key=lambda x: x[0] - x[1])[:SCHLUCHT_ETIKETTEN]:
        if b_ >= pmin and a_ <= pmax:
            etiketten.append((Y((a_ + b_) / 2), f"Schlucht {zahl(a_, 0)}–{zahl(b_, 0)}", DUENN_FARBE))
    halb_b = max(1.5, KURS_H * (e["atr"] or 0) * STOPP_BAND / max(pmax - pmin, 1e-9))  # Layout: Festung ¼ ATR breit
    for x, seite_ in burgen:                                                        # Festungen quer über das Gelände
        A(f'<rect x="{LINKS}" y="{Y(x["preis"]) - halb_b / 2:.1f}" width="{ende - LINKS}" height="{halb_b:.1f}" '
          f'fill="{FESTUNG_FARBE}" fill-opacity="0.10"/>'
          f'<line x1="{LINKS}" x2="{ende}" y1="{Y(x["preis"]):.1f}" y2="{Y(x["preis"]):.1f}" stroke="{FESTUNG_FARBE}" '
          f'stroke-width="2" stroke-opacity="0.85"><title>Festung {zahl(x["preis"])}: {" · ".join(x["grund"])}</title></line>')  # Layout
        etiketten.append((Y(x["preis"]), f'{"▲" if seite_ == "oben" else "▼"} {zahl(x["preis"], 0)} {x["grund"][0]}'
                                         f'{"+" if len(x["grund"]) > 1 else ""} {x["abstand"]:+.1f} %'.replace(".", ","), FESTUNG_FARBE))
    if woche:                                                                       # die Front der höheren Ebene
        wl, wh = woche[0]["zone"]
        x0 = X(pos(woche[1])) - halb if woche[1] >= d.index[0] else LINKS
        A(f'<rect x="{x0:.1f}" y="{Y(wh):.1f}" width="{ende - x0:.1f}" height="{max(2, Y(wl) - Y(wh)):.1f}" fill="none" '
          f'stroke="{WOCHE_FARBE}" stroke-width="1.2" stroke-opacity="0.7"/>'                                    # Layout
          f'<text x="{x0 + 4:.1f}" y="{Y(wl) + 13:.1f}" fill="{WOCHE_FARBE}" font-size="11">{"Wochenzone" if woche[2] == "Woche" else "Tageszone"} {woche[0]["name"]}</text>')  # Layout: unter dem Rahmen
    if la["zone"]:                                                                  # die Zone von heute
        zs = pd.Timestamp(la["beginn"])
        xz = X(pos(zs)) - halb if zs >= d.index[0] else LINKS
        A(f'<rect x="{xz:.1f}" y="{Y(hi):.1f}" width="{ende - xz:.1f}" height="{max(2, Y(lo) - Y(hi)):.1f}" fill="{ZONE_FARBE}" '
          f'fill-opacity="0.10" stroke="{ZONE_FARBE}" stroke-width="1.8" stroke-dasharray="6 3"/>'  # Layout
          f'<text x="{xz + 6:.1f}" y="{Y(hi) - 6:.1f}" fill="{ZONE_FARBE}" font-size="16" font-weight="700">{la["name"]}</text>')  # Layout
        A(f'<line x1="{xz:.1f}" x2="{ende}" y1="{Y(la["poc"]):.1f}" y2="{Y(la["poc"]):.1f}" stroke="{POC_FARBE}" '
          f'stroke-width="1.4" stroke-dasharray="2 3"/>')                           # Layout
    piv = la.get("pivot") if la.get("zone") else None
    oben_ = piv is not None and abs(piv - hi) <= piv * PIVOT_GLEICH                   # Pivot auf der Oberkante
    am_pivot = bool(t and piv is not None and abs(t["einstieg"] - piv) <= piv * PIVOT_GLEICH)   # Auslöser = Pivot
    if la["zone"]:
        etiketten += ([] if oben_ else [(Y(hi), f"Zone oben {zahl(hi)}", ZONE_FARBE)]) + \
                     [(Y(lo), f"Zone unten {zahl(lo)}", ZONE_FARBE), (Y(la["poc"]), f"POC {zahl(la['poc'])}", POC_FARBE)]
    if piv is not None and pmin <= piv <= pmax:          # der Pivot als eigene Linie (Micky 23.11.2026): gestrichelt weiß;
        moeglich = bool(t and t.get("kein_setup"))       # ohne Setup blass als „möglicher Pivot“
        A(f'<line x1="{xz:.1f}" x2="{ende}" y1="{Y(piv):.1f}" y2="{Y(piv):.1f}" stroke="{PIVOT_FARBE}" '
          f'stroke-width="{1.4 if moeglich else 2.4}" stroke-dasharray="8 4" stroke-opacity="{PIVOT_BLASS if moeglich else 1}">'   # Layout
          f'<title>{"möglicher " if moeglich else ""}Pivot {zahl(piv)} – die Kante, an der die Waage kippt</title></line>')  # Layout
        etiketten.append((Y(piv), ("möglicher Pivot" if moeglich else "Pivot") + f" {zahl(piv)}"   # Layout: kurz, passt
                          + (" = Oberkante" if oben_ and not moeglich else ""),                    # an den Rand
                          TEXT_3 if moeglich else PIVOT_FARBE))
    def kurve(r_, farbe, dicke=1.6, strich=""):  # Layout
        pkt = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(r_.to_numpy(float)) if not np.isnan(x) and pmin <= x <= pmax)
        if pkt:
            A(f'<polyline points="{pkt}" fill="none" stroke="{farbe}" stroke-width="{dicke}"{strich}/>')
    for g, r_ in linien.items():                                                    # gewählte Durchschnitte
        kurve(r_, GD_FARBE[g], 1.4)                                                 # Layout
        w_ = r_.dropna()
        if len(w_) and pmin <= w_.iloc[-1] <= pmax:
            etiketten.append((Y(float(w_.iloc[-1])), f"GD{g} {zahl(float(w_.iloc[-1]))}", GD_FARBE[g]))
    if len(eigene) == 2 and all(x is not None for x in eigene):                     # Zange schattiert
        a_, b_ = eigene[0].to_numpy(float), eigene[1].to_numpy(float)
        pkt = [(X(i), Y(p), Y(q)) for i, (p, q) in enumerate(zip(a_, b_)) if not (np.isnan(p) or np.isnan(q))]
        if len(pkt) >= 2:
            A('<polygon points="' + " ".join(f"{x:.1f},{p:.1f}" for x, p, _ in pkt) + " "
              + " ".join(f"{x:.1f},{q:.1f}" for x, _, q in reversed(pkt)) + f'" fill="{ANKER_FARBE[0]}" fill-opacity="0.08"/>')  # Layout
    for k, r_ in enumerate(eigene):                                                 # eigener AVWAP
        if r_ is None:
            continue
        kurve(r_, ANKER_FARBE[k], 1.9)                                              # Layout
        w_ = r_.dropna()
        if len(w_):
            etiketten.append((Y(float(w_.iloc[-1])), f"AVWAP {k + 1} {zahl(float(w_.iloc[-1]))}", ANKER_FARBE[k]))
    mitte = df["Close"].rolling(ENGE_SCHNITT).mean()                               # Korridor der Enge (Micky 24.11.
    halbe = (df["High"] - df["Low"]).rolling(ENGE_SCHNITT).mean() / 2             # 2026): Schnitt des Schlusses ± die
    ko = (mitte + halbe).reindex(d.index).to_numpy(float)                          # halbe Spanne der letzten 10 Kerzen –
    ku = (mitte - halbe).reindex(d.index).to_numpy(float)                          # wird das Band schmaler, zieht sich
    ok_ = [i for i in range(N) if not (np.isnan(ko[i]) or np.isnan(ku[i]))]        # der Kurs zusammen
    if len(ok_) >= 2:
        oben_ = [f"{X(i):.1f},{Y(min(max(ko[i], pmin), pmax)):.1f}" for i in ok_]
        unten_ = [f"{X(i):.1f},{Y(min(max(ku[i], pmin), pmax)):.1f}" for i in ok_[::-1]]
        A(f'<polygon points="{" ".join(oben_ + unten_)}" fill="{ENGE_FARBE}" fill-opacity="{KORRIDOR_DECK}" '
          f'stroke="none"><title>Korridor der Enge: Schnitt der letzten {ENGE_SCHNITT} Schlusskurse ± die halbe '
          f'Spanne (Hoch bis Tief) – wird er schmaler, wird der Kurs enger</title></polygon>')
        for pk in (oben_, unten_):
            A(f'<polyline points="{" ".join(pk)}" fill="none" stroke="{ENGE_FARBE}" stroke-width="0.8" '
              f'stroke-opacity="0.7"/>')                                            # Layout
    bw = max(1.0, breite / NZ * 0.6)                                                # Layout: Kerzenbreite
    n_ges = len(df)
    for i in range(N):
        f = GRUEN if c[i] >= o[i] else ROT
        nr = n_ges - n0 - i                                                         # Balkennummer von rechts
        A(f'<g><title>Balken {nr} · {d.index[i]:%d.%m.%Y{" %H:%M" if e["name"] == "Stunde" else ""}} · E {zahl(o[i])} · '
          f'H {zahl(h[i])} · T {zahl(l[i])} · S {zahl(c[i])}</title>'
          f'<rect x="{X(i) - halb:.1f}" y="{OBEN}" width="{2 * halb:.1f}" height="{KURS_H}" fill="#000" fill-opacity="0"/>'
          f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{Y(h[i]):.1f}" y2="{Y(l[i]):.1f}" stroke="{f}"/>')
        y1, y2 = sorted([Y(o[i]), Y(c[i])])
        hohl = laufend and i == N - 1
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{max(1, y2 - y1):.1f}" '
          + (f'fill="none" stroke="{f}"/></g>' if hohl else f'fill="{f}"/></g>'))
    import vcp_zone
    zz = vcp_zone.zigzag(df, vcp_zone.GROB) if len(df) > vcp_zone.ATR_TAGE + 1 else []
    sek = vcp_zone.secondary(zz)                                                    # Livermores Secondary: ohne neues Extrem
    for k_, (i_, p_, art) in enumerate(zz):                                         # Wendepunkte (Schwunghochs und -tiefs)
        j = i_ - n0
        if 0 <= j < N:
            y_ = Y(p_) - 6 if art == "H" else Y(p_) + 6                             # Layout: über dem Hoch, unter dem Tief
            letzt = k_ == len(zz) - 1
            s_ = k_ in sek
            A(f'<circle cx="{X(j):.1f}" cy="{y_:.1f}" r="{2 if s_ else 3}" '                  # Layout: Secondary kleiner
              f'fill="{"none" if letzt else WENDE_FARBE}" '
              f'stroke="{WENDE_FARBE}" fill-opacity="{0.55 if s_ else 1}">'          # Layout: Secondary kleiner und blasser
              f'<title>Wendepunkt {"Hoch" if art == "H" else "Tief"} {zahl(p_)}'
              + (f' · Secondary (Livermore): {"kein neues Hoch" if art == "H" else "kein neues Tief"}' if s_ else "")
              + f'{" (noch nicht bestätigt)" if letzt else ""}</title></circle>')    # Layout
    if la.get("pivot") is not None and la.get("beginn") is not None:                # der eine Pivot: sein Wendepunkt
        seit_z = (d.index >= pd.Timestamp(la["beginn"])) & (np.abs(h - la["pivot"]) <= la["pivot"] * PIVOT_GLEICH)
        if seit_z.any():
            j = int(np.nonzero(seit_z)[0][-1])
            y_ = Y(la["pivot"]) - 7                                                 # Layout: über dem Hoch
            A(f'<path d="M{X(j):.1f},{y_ - 6:.1f} L{X(j) + 6:.1f},{y_:.1f} L{X(j):.1f},{y_ + 6:.1f} '  # Layout: Raute
              f'L{X(j) - 6:.1f},{y_:.1f} Z" '                                       # Layout
              f'fill="{ZONE_FARBE}" stroke="#000" stroke-width="0.6"><title>Pivot {zahl(la["pivot"])} · '
              f'{d.index[j]:%d.%m.%Y} – die Kante, an der die Waage kippt</title></path>')
    if ba and e["name"] != "Stunde":                                                # Enge: die Kontraktionen der Base
        bdf, en_ = ba["df"], ba.get("enge") or {}
        auf, punkte_o, punkte_u = en_.get("aufsteigend"), [], []
        for k_ in (en_.get("kontraktionen") or [])[1:]:   # Trichter (Micky 24.11.2026): über die Hochs und unter die
            # Tiefs der Wellen der rechten Seite – die erste Welle ist der Fall der linken Seite (die Tiefe der Base)
            for i_, w_, liste_ in ((k_["hoch_i"], k_["hoch"], punkte_o), (k_["tief_i"], k_["tief"], punkte_u)):
                if bdf.index[i_] >= d.index[0]:                                     # Linie unter die Tiefs
                    liste_.append((X(pos(bdf.index[i_])), Y(w_)))
        if len(punkte_o) >= 2 and len(punkte_u) >= 2:
            f_t = AMPEL.get("grün" if auf else en_.get("ampel"), TEXT_3)
            flaeche = " ".join(f"{x_:.1f},{y_:.1f}" for x_, y_ in punkte_o + punkte_u[::-1])
            A(f'<polygon points="{flaeche}" fill="{f_t}" fill-opacity="{TRICHTER_DECK}" stroke="none"/>')
            for pk in (punkte_o, punkte_u):
                A(f'<polyline points="{" ".join(f"{x_:.1f},{y_:.1f}" for x_, y_ in pk)}" fill="none" stroke="{f_t}" '
                  f'stroke-width="1.6" stroke-opacity="0.9"><title>Trichter der Base: Wellen '   # Layout
                  f'{t_esc(en_.get("folge") or "")} % – schließt er sich, trocknen die Verkäufer aus (Minervini)'
                  f'</title></polyline>')
        if en_.get("kontraktionen") and la.get("zone") and la.get("beginn") is not None:   # Urteil an der Zone
            amp = "grün" if auf else en_.get("ampel")
            urteil = ("🟢 Aufsteigende Base" if auf else "🟢 VCP" if amp == "grün" else "🔴 Enge" if amp == "rot"
                      else "🟡 Enge")                                               # kurz; die Gründe beim Darüberfahren
            grund = ("O'Neil: drei Rücksetzer von 10–20 %, Tiefs und Hochs steigen" if auf
                     else "schrumpft: jede Welle höchstens 70 % so tief wie die vorige" if amp == "grün"
                     else "letzte Welle tiefer als die vorige" if amp == "rot"
                     else ", ".join(en_.get("fehlt") or ["noch nicht reif"]))
            zs = pd.Timestamp(la["beginn"])
            xz_ = X(pos(zs)) - halb if zs >= d.index[0] else LINKS
            x_u = min(xz_ + 6 + len(la["name"]) * NAME_BREITE, ende - len(urteil) * URTEIL_BREITE)   # nie über den Rand  (Layout)
            A(f'<text x="{x_u:.1f}" y="{Y(hi) - 6:.1f}" fill="{AMPEL.get(amp, TEXT_3)}" font-size="12">'      # Layout
              f'{t_esc(urteil)}<title>{t_esc(grund)} · Wellen {t_esc(en_.get("folge") or "")} % · VCP (Minervini): '
              f'jede Welle höchstens 70 % so tief wie die vorige, die letzte eng, das Volumen trocknet aus · '
              f'Aufsteigende Base (O\'Neil): drei Rücksetzer von 10–20 %, Tiefs und Hochs steigen</title></text>')
    if fest is not None and e["name"] != "Stunde":                                  # ✈️ freie Bahn (Livermore)
        if not fest.get("oben"):
            etiketten.append((OBEN + 4, "✈️ freie Bahn", GRUEN))   # Layout: ganz oben
        if not fest.get("unten"):
            etiketten.append((OBEN + KURS_H - 4, "✈️↓ freie Bahn", ROT))   # Layout: ganz unten
    if t:                                                                           # der Trade: Auslöser bzw. Einstieg, Stopp
        gegen = " · kein Setup" if t.get("kein_setup") else ""                         # Zone gegen den Zirkel: Linien bleiben
        x_t = X(max(0, N - 12))                                                     # Layout: die letzten 12 Kerzen
        for wert, farbe, name in ((t["einstieg"], EINSTIEG_FARBE, "Auslöser" if t["wartet"] else "Einstieg"),
                                  (t["stopp"], ROT, "Stopp")):
            if name != "Stopp" and am_pivot:                                        # steht schon an der Pivot-Linie
                continue
            A(f'<line x1="{x_t:.1f}" x2="{ende}" y1="{Y(wert):.1f}" y2="{Y(wert):.1f}" stroke="{farbe}" stroke-width="2"/>')
            etiketten.append((Y(wert), f"{name} {zahl(wert)}" + (f' · {t["ampel"]} Risiko {zahl(t["risiko"], 1)} %'
                                                                 if name == "Stopp" else gegen), farbe))
    mitte_x = ende + PROFIL_W / 2
    halb_w = PROFIL_W / 2 - 4                                                       # Layout
    vmax_p, zmax_p = float(max(pr["volumen"])) or 1.0, float(max(pr["zeit"])) or 1.0
    det = zonen.profil_details(pr) if "details" in linien_ else None
    for a_, b_, w_, z_, k_ in zip(pr["grenzen"][:-1], pr["grenzen"][1:], pr["volumen"], pr["zeit"], pr["kauf"]):
        if b_ < pmin or a_ > pmax:
            continue
        y1, y2 = Y(min(b_, pmax)), Y(max(a_, pmin))
        hh = max(1, y2 - y1 - 0.6)  # Layout
        poc_, tpoc_ = a_ <= pr["poc"] <= b_, a_ <= pr["tpoc"] <= b_
        bz = max(1, halb_w * z_ / zmax_p)
        A(f'<rect x="{mitte_x - 1 - bz:.1f}" y="{y1 + 0.3:.1f}" width="{bz:.1f}" height="{hh:.1f}" fill="{ZEIT_FARBE}" '  # Layout
          f'fill-opacity="{0.9 if tpoc_ else 0.4}"/>')                              # Layout
        deck_v = 0.95 if poc_ else (0.75 if det["val"] <= (a_ + b_) / 2 <= det["vah"] else 0.3) if det else 0.6  # Layout
        bv = max(1, halb_w * w_ / vmax_p)
        bk = bv * (k_ / w_ if w_ > 0 else 0)                                        # Truppen: Käufer grün, Verkäufer rot
        A(f'<rect x="{mitte_x + 1:.1f}" y="{y1 + 0.3:.1f}" width="{bk:.1f}" height="{hh:.1f}" fill="{GRUEN}" fill-opacity="{deck_v}"/>'  # Layout
          f'<rect x="{mitte_x + 1 + bk:.1f}" y="{y1 + 0.3:.1f}" width="{max(0, bv - bk):.1f}" height="{hh:.1f}" fill="{ROT}" fill-opacity="{deck_v}"/>')  # Layout
        if poc_:
            A(f'<rect x="{mitte_x + 1:.1f}" y="{y1 + 0.3:.1f}" width="{bv:.1f}" height="{hh:.1f}" fill="none" stroke="{POC_FARBE}" stroke-width="1.2"/>')  # Layout
        if det and z_ == 1 and any(e0 <= (a_ + b_) / 2 <= e1 for e0, e1 in det["einzel"]):   # Einzeldruck
            A(f'<rect x="{mitte_x - 1 - bz:.1f}" y="{y1 + 0.3:.1f}" width="{bz:.1f}" height="{hh:.1f}" fill="{EINZEL_FARBE}"/>')  # Layout
    A(f'<text x="{mitte_x:.1f}" y="{OBEN - 4}" fill="{TEXT_3 if profil is None else ANKER_FARBE[0]}" font-size="10" '  # Layout
      f'text-anchor="middle">Zeit ◂ ▸ Käufer | Verkäufer (geschätzt) seit {pd.Timestamp(pr["ab"]):%d.%m.}{" (eigener Anker)" if profil else ""}</text>')                                    # Layout
    ab_ = pd.Timestamp(pr["ab"])                                                     # Zeitraum unter dem Profil
    n_pr = int((df.index >= ab_).sum())                                             # (Micky 24.11.2026)
    A(f'<text x="{mitte_x:.1f}" y="{OBEN + KURS_H + 12}" fill="{TEXT_3}" font-size="10" text-anchor="middle">'   # Layout
      f'{ab_:%d.%m.%y}–{df.index[-1]:%d.%m.%y} · {n_pr} {EINHEIT[e["name"]]}<title>Zeitraum des Profils: '
      f'{n_pr} Kerzen</title></text>')
    if det:                                                                         # Profil-Details
        for wert, name in ((det["vah"], "VAH"), (det["val"], "VAL")):
            if pmin <= wert <= pmax:
                A(f'<line x1="{ende - 140}" x2="{ende + PROFIL_W}" y1="{Y(wert):.1f}" y2="{Y(wert):.1f}" stroke="{WERT_FARBE}" '  # Layout
                  f'stroke-width="1.1" stroke-dasharray="5 3" stroke-opacity="0.8"/>')  # Layout: 140 px in den Chart
                etiketten.append((Y(wert), f"{name} {zahl(wert)}", WERT_FARBE))
        for wert in det["knoten"]:
            if pmin <= wert <= pmax:
                A(f'<text x="{ende + PROFIL_W - 2}" y="{Y(wert) + 4:.1f}" fill="{POC_FARBE}" font-size="11" text-anchor="end">◀</text>')  # Layout
                etiketten.append((Y(wert), f"Knoten {zahl(wert)}", POC_FARBE))
        for a_, b_ in det["duenn"]:
            if b_ >= pmin and a_ <= pmax:
                A(f'<rect x="{ende + 2}" y="{Y(min(b_, pmax)):.1f}" width="{PROFIL_W - 4}" height="{max(1, Y(max(a_, pmin)) - Y(min(b_, pmax))):.1f}" '  # Layout
                  f'fill="{DUENN_FARBE}" fill-opacity="0.16"/>')                     # Layout
        for a_, b_ in sorted(det["duenn"], key=lambda x: x[0] - x[1])[:LVN_ETIKETTEN]:
            if b_ >= pmin and a_ <= pmax:
                etiketten.append((Y((a_ + b_) / 2), f"dünn {zahl(a_, 0)}–{zahl(b_, 0)}", DUENN_FARBE))
    if profil is not None:                                                          # eigener Anker: sein POC
        etiketten.append((Y(pr["poc"]), f"Profil-POC {zahl(pr['poc'])}", POC_FARBE))
        A(f'<line x1="{LINKS}" x2="{ende}" y1="{Y(pr["poc"]):.1f}" y2="{Y(pr["poc"]):.1f}" stroke="{POC_FARBE}" '
          f'stroke-width="1" stroke-dasharray="1 4" stroke-opacity="0.8"/>')        # Layout
    if abs(pr["tpoc"] - pr["poc"]) > tiefe.stufe(la["kurs"]) * 1.5:                # Layout: mehr als eine Stufe auseinander
        etiketten.append((Y(pr["tpoc"]), f"Zeit-POC {zahl(pr['tpoc'])}", ZEIT_FARBE))
    belegt = []
    for y0, text, farbe in sorted(etiketten):                                       # rechts, ohne Überlappung: der
        y_, k_ = y0, 0                                                              # nächste freie Platz, abwechselnd
        while any(abs(y_ - b_) < ZEILE for b_ in belegt) or not OBEN - 4 <= y_ <= OBEN + KURS_H + 4:   # darunter und  (Layout)
            k_ += 1                                                                 # darüber, im Kursbereich (Micky
            y_ = y0 + ZEILE * ((k_ + 1) // 2) * (1 if k_ % 2 else -1)              # 24.11.: nicht ins Volumen)
            if k_ > ETIKETT_SUCHE:
                y_ = y0 + ZEILE * len(belegt)
                break
        belegt.append(y_)
        A(f'<text x="{ende + PROFIL_W + 6}" y="{y_ + 4:.1f}" fill="{farbe}" font-size="12">{text}</text>')  # Layout
    vs_ = df["Volume"].astype(float).rolling(VOL_SCHNITT[e["name"]]).mean().reindex(d.index).to_numpy()
    vmax = min(v.max(), VOL_DECKEL * np.nanmax(vs_)) if np.isfinite(np.nanmax(vs_)) else v.max()
    vmax = vmax or 1                                # ein Ausreißer drückt sonst alle Balken flach – darüber abgeschnitten
    schnitt = pd.Series(v).rolling(min(50, N)).mean().to_numpy()                    # Layout: 50 Kerzen Schnitt
    for i in range(N):
        hv = min(VOL_H, VOL_H * v[i] / vmax)
        hoch = not np.isnan(schnitt[i]) and v[i] > schnitt[i]
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y_vol + VOL_H - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" '
          f'fill="{GRUEN if c[i] >= o[i] else ROT}" fill-opacity="{0.85 if hoch else 0.35}"/>')  # Layout
    vs = vs_                                                                        # Schnitt als
    pkt_v = " ".join(f"{X(i):.1f},{y_vol + VOL_H - min(VOL_H, VOL_H * vs[i] / vmax):.1f}"   # weiße Linie (Micky 24.11.)
                     for i in range(N) if not np.isnan(vs[i]))
    if pkt_v:
        A(f'<polyline points="{pkt_v}" fill="none" stroke="{SCHNITT_FARBE}" stroke-width="1.3">'   # Layout
          f'<title>Volumen-Schnitt {VOL_SCHNITT[e["name"]]} Kerzen</title></polyline>')
    A(f'<text x="{ende + 2}" y="{y_vol + 12}" fill="{TEXT_3}" font-size="10">Volumen · Ø {VOL_SCHNITT[e["name"]]}'   # Layout
      f'<title>weiße Linie = Schnitt der letzten {VOL_SCHNITT[e["name"]]} Kerzen</title></text>')   # Layout
    leiste = {}                                                                     # Zeichenleiste: Kerze → [(Zeichen, Text)]
    vv = df["Volume"].astype(float).to_numpy()
    for i in range(N):                                                              # 🏜️ leisester Tag seit 50 Kerzen
        g = n0 + i
        if g >= zeichen.TROCKEN_VERGLEICH and 0 < vv[g] <= vv[g - zeichen.TROCKEN_VERGLEICH:g + 1].min():
            leiste.setdefault(i, []).append(("🏜️", "leisestes Volumen seit 50 Kerzen – kaum noch Verkäufer (Minervini)"))
    for x in zeichen.kraft_ohne_weg(df, tage=len(df), oben=hi, unten=lo, alle=True) or []:   # ⚡ Kraft ohne Weg
        if x["tag"] >= d.index[0]:
            leiste.setdefault(pos(x["tag"]), []).append(
                ("⚡", f'Kraft ohne Weg an {x["marke"]}: {zahl(x["volumen"], 1)}-faches Volumen, enge Spanne '
                       f'({"Verkäufer schlucken die Nachfrage" if x["rand"] == "oben" else "Käufer schlucken das Angebot"}, Wyckoff)'))
    a_b = (ba or {}).get("ausbruch") if e["name"] != "Stunde" else None
    if a_b:                                                                         # 🦬 Ausbruch, 🦊 Fehlausbruch
        for tag_, z_, text in ((a_b["tag"], "🦬", "Ausbruch über den Pivot"
                                + (" mit Volumen" if a_b["mit_volumen"] else " ohne Volumen")),
                               (a_b.get("fehl_tag"), "🦊", "Fehlausbruch: Schluss zurück unter dem Pivot")):
            if tag_ is not None and (z_ == "🦬" or a_b["fehl"]) and pd.Timestamp(tag_) >= d.index[0]:
                leiste.setdefault(pos(tag_), []).append((z_, text))
    if tk and e["name"] != "Stunde":                                                # Halt der Phase: jetzt
        zk = zeichen.zirkel((zeichen.laden().get("titel") or {}).get(tk))
        sym, wort, grund = zeichen.halt(zk)                                         # Halt der Phase (24.11.2026)
        if sym:
            leiste.setdefault(N - 1, []).append((sym, f"Phase {wort}" + (f" – {grund}" if grund else "")
                                                 + "".join(f" · Keim: {x}" for x in (zk or {}).get("keim", [])[:3])))
    tage_, naechster = _zahlentage(tk) if tk and e["name"] != "Stunde" else ([], None)
    cf = df["Close"].to_numpy(float)
    for tag_ in tage_:                                                              # Ⓔ Zahlentage (Micky 24.11.2026)
        if tag_ < d.index[0] or tag_ > d.index[-1]:
            continue
        g = int(df.index.searchsorted(tag_))
        if g >= len(df):
            continue
        r1 = (cf[g] / cf[g - 1] - 1) * 100 if g > 0 else None
        r2 = (cf[g + 1] / cf[g] - 1) * 100 if g + 1 < len(df) else None
        reakt = " · ".join(f"{w} {r:+.1f} %".replace(".", ",") for w, r in zip(KERZE_WORT[e["name"]], (r1, r2))
                           if r is not None)
        j = g - n0
        A(f'<text x="{X(j) + (10 if j in leiste else 0):.1f}" y="{y_zei + 15}" fill="{TEXT_2}" font-size="12" '   # Layout
          f'font-weight="700" text-anchor="middle">E<title>Zahlen am {tag_:%d.%m.%Y} – Kurs {reakt}</title></text>')  # Layout
    if naechster is not None:                                                      # 📅 der nächste Termin rechts
        tage_bis = (naechster - pd.Timestamp.today().normalize()).days
        A(f'<text x="{ende + 2}" y="{y_vol + 26}" fill="{TEXT_2}" font-size="10">📅 {naechster:%d.%m.}'   # Layout
          + (f" · {tage_bis} T." if tage_bis >= 0 else "") + f'<title>nächste Zahlen am {naechster:%d.%m.%Y}'
          + (f", in {tage_bis} Tagen" if tage_bis >= 0 else "") + '</title></text>')   # Layout
    for i, liste_ in leiste.items():
        A(f'<text x="{X(i):.1f}" y="{y_zei + 15}" font-size="13" text-anchor="middle">{"".join(dict.fromkeys(z for z, _ in liste_))}'  # Layout
          f'<title>{" · ".join(x for _, x in liste_)}</title></text>')              # Layout
    A(f'<text x="{ende + 16}" y="{y_zei + 15}" fill="{TEXT_3}" font-size="10">Zeichen</text>')   # Layout: neben dem Zeichen der letzten Kerze
    if rs and rs.get("index") is not None:                                          # relative Stärke
        def relativ(bezug):
            bx = bezug.reindex(df.index, method="ffill")
            rv = df["Close"] / bx
            r = rv.reindex(d.index).to_numpy(float)
            g = np.flatnonzero(~np.isnan(r))
            return (r / r[g[0]] * 100, rv) if len(g) > PFEIL_N else (None, None)
        r_i, rv = relativ(rs["index"])
        r_s, _ = relativ(rs["sektor"]) if rs.get("sektor") is not None else (None, None)
        if r_i is not None:
            alle = np.concatenate([r_i[~np.isnan(r_i)], r_s[~np.isnan(r_s)] if r_s is not None else [], [100.0]])
            a0, a1 = alle.min(), alle.max()
            sp = (a1 - a0) * 0.08 or 1                                              # Layout
            a0, a1 = a0 - sp, a1 + sp
            YR = lambda y: y_rs + RS_H * (1 - (y - a0) / (a1 - a0))                 # noqa: E731
            A(f'<text x="{LINKS}" y="{y_rs - 6}" fill="{TEXT_3}" font-size="11">Relative Stärke · '  # Layout
              f'<tspan fill="{BLAU}">— gegen S&amp;P 500 {_pfeil(r_i)}</tspan>'
              + (f'  <tspan fill="{LILA}">- - gegen Sektor {_pfeil(r_s)}</tspan>' if r_s is not None else "")
              + f'  · <tspan fill="{RS_HOCH_FARBE}">● RS-Hoch vor Kurs</tspan> · <tspan fill="{RS_TIEF_FARBE}">● RS-Tief vor Kurs</tspan></text>')
            A(f'<line x1="{LINKS}" x2="{ende}" y1="{YR(100):.1f}" y2="{YR(100):.1f}" stroke="{TEXT_3}" stroke-dasharray="2 4"/>')
            for r_, farbe, strich in ((r_s, LILA, ' stroke-dasharray="5 4"'), (r_i, BLAU, "")):
                if r_ is not None:
                    A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(r_) if not np.isnan(x))
                      + f'" fill="none" stroke="{farbe}" stroke-width="1.6"{strich}/>')  # Layout
            mom = ((rueckenwind.laden() or {}).get("titel") or {}).get(tk, {}).get("momentum") if tk else None
            if mom:                                                                 # Momentum 🚀 (Kullamägi)
                text = " · ".join(f'{"🚀 " if top else ""}{k} {"+" if round(r) > 0 else ""}{zahl(round(r) or 0, 0)} %' for k, (r, top) in mom.items())
                g_ = np.flatnonzero(~np.isnan(r_i))
                A(f'<text x="{ende + 6}" y="{YR(r_i[g_[-1]]) + 4:.1f}" fill="{TEXT_2}" font-size="12">Momentum {text}'  # Layout
                  f'<title>Rendite über 1, 3, 6 Monate; 🚀 = unter den besten 2 % des Reviers (Kullamägi)</title></text>')   # Layout
            jahr = JAHR[e["name"]]
            cl = df["Close"]
            hoch_ = (rv >= zeichen.RS_HOCH * rv.rolling(jahr, min_periods=jahr).max()) & \
                    (cl < rueckenwind.KURS_NAH * cl.rolling(jahr, min_periods=jahr).max())
            tief_ = (rv <= rv.rolling(jahr, min_periods=jahr).min() / zeichen.RS_HOCH) & \
                    (cl > (2 - rueckenwind.KURS_NAH) * cl.rolling(jahr, min_periods=jahr).min())
            for reihe, farbe in ((hoch_, RS_HOCH_FARBE), (tief_, RS_TIEF_FARBE)):
                fl = reihe.reindex(d.index).fillna(False).to_numpy(bool)
                for i in np.flatnonzero(fl):
                    if not np.isnan(r_i[i]):
                        A(f'<circle cx="{X(i):.1f}" cy="{YR(r_i[i]):.1f}" r="3" fill="{farbe}"/>')  # Layout
    letzter = None
    for i, tag in enumerate(d.index):                                               # Zeitachse
        schl = {"Woche": (tag.year, (tag.month - 1) // 3), "Tag": (tag.year, tag.month)}.get(e["name"], tag.normalize())  # Layout
        if schl != letzter and letzter is not None and (e["name"] != "Stunde" or tag.dayofweek == 0):
            text = f"{tag:%d.%m.}" if e["name"] == "Stunde" else f"{tag:%m/%y}"
            A(f'<text x="{X(i):.1f}" y="{H - 6}" fill="{TEXT_3}" font-size="11">{text}</text>')  # Layout
        letzter = schl
    A("</svg>")
    return "".join(s)


def legende():
    """Erklärung der Farben unter dem Chart (aufklappbar)."""
    from gestaltung import t
    teile = [(ZONE_FARBE, "Zone von heute: Base, Flagge oder Konsolidierung (Minervini, O'Neil), in der Stunde die Balance · POC grün gepunktet"),
             (FESTUNG_FARBE, "Festung ▲▼: alte Decke = Swing-Hoch ohne Schluss darüber, alter Boden = Swing-Tief ohne Schluss "
              "darunter (Wendepunkte ab 2 ATR); überwunden tauschen sie die Rolle (Decke → Boden) – je Richtung die 2 nächsten"),
             (DUENN_FARBE, "Schlucht: dünne Stelle des Profils quer über das Gelände – dort fällt der Kurs durch"),
             (GRUEN, "Profil rechts: Zeit (lila) ◂ ▸ Käufer grün | Verkäufer rot – geschätzt aus steigenden und fallenden Kerzen"),
             (WERT_FARBE, "Profil-Details: VAH/VAL = Wertzone (70 % des Volumens, kräftig) · ◀ Knoten (dicke Stellen) · "
              "blauer Streifen = dünne Stelle · weiß im Zeitprofil = Einzeldruck (nur eine Kerze)"),
             (WOCHE_FARBE, "Rahmen in der Stunde: die Base des Tages"),
             (ANKER_FARBE[0], "eigener AVWAP 1 · AVWAP 2 orange · dazwischen die Zange"),
             (WENDE_FARBE, "● Wendepunkte: Schwunghochs und -tiefs ab 2 ATR (Livermores 6 Punkte in ATR) – hohl = noch "
              "nicht bestätigt, klein und blass = Secondary (kein neues Extrem); aus ihnen entstehen Zone, Enge und "
              "Festungen"),
             (PIVOT_FARBE, "- - Pivot (◆ auf seinem Wendepunkt): die Kante, an der die Waage kippt – das Hoch der letzten "
              "Enge im oberen Drittel, sonst die Oberkante (in der Stunde das Hoch der Balance); blass = möglicher Pivot "
              "ohne Setup"),
             (GRUEN, "Trichter: Linie über die Hochs und unter die Tiefs der Wellen in der Base – schließt er sich, "
              "trocknen die Verkäufer aus (Minervinis VCP); grün = sauber (oder aufsteigende Base nach O'Neil), gelb = "
              "noch nicht reif, rot = die letzte Welle tiefer"),
             (ENGE_FARBE, "Korridor der Enge: Band um den Kurs aus dem Schnitt der letzten 10 Schlusskurse ± der halben "
              "Spanne (Hoch bis Tief) – wird es schmaler, zieht sich der Kurs zusammen (Minervini: die Volatilität "
              "schrumpft); gleich breit = gleichmäßig, aufgehend = unruhig"),
             (GRUEN, "✈️ freie Bahn: keine Festung über dem Kurs (✈️↓ darunter) – Livermores Linie des geringsten Widerstands"),
             (TEXT_2, "Zeichenleiste: 🦬 Ausbruch · 🦊 Fehlausbruch · 🏜️ leisestes Volumen seit 50 Kerzen · ⚡ Kraft ohne Weg · "
              "Halt der Phase rechts, jetzt (🏰 hält · 🌊 Welle · ⛈️ Sturm) · E Zahlentag (Maus darauf: Reaktion des Kurses), rechts 📅 der "
              "nächste Termin · Momentum 🚀 am Ende der RS-Linie"),
             (SCHNITT_FARBE, "Weiße Linie im Volumen: Schnitt der letzten 50 Tage (Woche: 10 Wochen) – Balken darüber "
              "kräftig, darunter blass · unter dem Profil sein Zeitraum"),
             (TEXT_3, "Über jeder Kerze: Balkennummer (von rechts) für den eigenen AVWAP")]
    return (f'<details><summary style="cursor:pointer;color:{TEXT_2};font-size:14px">Legende</summary>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:8px;font-size:13px;color:{TEXT_2}">'
            + "".join(f'<span><span style="display:inline-block;width:14px;height:4px;background:{f};vertical-align:middle;'
                      f'margin-right:6px"></span>{t(x)}</span>' for f, x in teile) + '</div></details>')
