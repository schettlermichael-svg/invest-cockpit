"""Der Zonenchart (Micky 21.11.2026): wenig, aber aussagekräftig – dasselbe Bild für Woche, Tag und Stunde.

Kursfeld: Kerzen; die Spanne von heute (Livermores Spanne seit 25.11.2026, in der Stunde die Balance) als gelber Rahmen mit
Namen, Front und POC; in der Stunde die
Base des Tages als feiner Rahmen; Schluchten quer über das Gelände; Livermores stehende Pivotal Points als Linie bis zum Rand (Front und nächste Stellung kräftig)
(Stellungen seit 25.11.2026 nicht mehr als Band, nur als Ziel des Schlachtplans und ✈️); der Trade (Einstieg, Stopp, Ziel); nach Wahl Durchschnitte und
der eigene AVWAP (zwei Anker, Zange). Rechts das eine Profil der Ebene: Zeit und Volumen gespiegelt, ab Beginn des
Impulses. Darunter das Volumen und das Feld der
relativen Stärke gegen den S&P 500 und gestrichelt gegen den Sektor (Punkte RS-Hoch bzw. RS-Tief vor Kurs)."""
import numpy as np
import pandas as pd

from gestaltung import AMPEL, BLAU, GELB, GRUEN, LILA, RAND, ROT, TEXT_2, TEXT_3, t as t_esc, zahl

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
ZONE_FARBE = "#EDA100"                 # Spanne wie in Vorwalds Bildern gelb
POC_FARBE = "#1BAF7A"
WOCHE_FARBE = "#7DB4FF"
EINSTIEG_FARBE = "#E6EAF0"
RS_HOCH_FARBE, RS_TIEF_FARBE = "#FFD166", "#FF6B6B"
GD_FARBE = {10: "#F0883E", 20: "#FF7EB6", 50: BLAU, 150: LILA, 200: "#D9B26F"}   # wie bisher im Cockpit
GD_WAHL = (10, 20, 50, 150, 200)
ANKER_FARBE = ("#4DD0E1", "#FF8A65")   # eigener AVWAP: Anker 1 türkis, Anker 2 orange
ZEIT_FARBE = LILA                      # Zeitprofil (Market Profile)
LINIEN_WAHL = {"details": "Profil-Details", "marketprofile": "Market Profile", "livermore": "Livermore"}   # Schalter (Micky
LINIEN_START = ["livermore"]                                                  # 24./25.11.2026); Livermore an
SCHLUCHT_ETIKETTEN = 2                 # Layout: höchstens 2 Schluchten beschriftet (die breitesten)
WERT_FARBE = "#E6EAF0"                 # VAH, VAL
DUENN_FARBE = "#7DB4FF"                # dünne Stellen (LVN)
EINZEL_FARBE = "#FFFFFF"               # Einzeldrucke im Zeitprofil
LVN_ETIKETTEN = 3                      # Layout: höchstens 3 dünne Stellen beschriftet (die breitesten)
RAND_SPIEL = 0.04                      # Layout: 4 % Luft über und unter den Kursen
WENDE_FARBE = "#9AA7B8"                # Wendepunkte (Schwunghochs und -tiefs ab 2 ATR)
SCHNITT_FARBE = "#E6EAF0"              # Volumen-Schnitt als weiße Linie
VOL_DECKEL = 3.0                       # Layout: Volumen-Achse bis zum 3-fachen des höchsten Schnitts
VOL_SCHNITT = {"Tag": 50, "Woche": 10, "Stunde": 50}   # Kerzen im Volumen-Schnitt (O'Neil: 50 Tage, 10 Wochen)
EINHEIT = {"Tag": "T.", "Woche": "Wo.", "Stunde": "Std."}       # kurz: unter dem Profil ist nur seine Breite Platz
ZEILE = 14                             # Layout: Abstand der Etiketten rechts
KERZE_WORT = {"Tag": ("am Tag", "am Tag danach"), "Woche": ("in der Woche", "in der Woche danach")}
PIVOT_FARBE = "#FFFFFF"                # die Front: gestrichelt weiß über allem
PIVOT_GLEICH = 0.001                   # Technik: der Wendepunkt der Front – Hoch bis 0,1 % an der Front
PLAN_DECK = 0.13                       # Layout: Flächen des Schlachtplans
MARKE_RAND = 50                        # Layout: Marken so nah am rechten Rand enden an der Kerze
PP_BLASS_DECK = 0.3                    # Layout: weiter entfernte offene Pivotal Points blass (Micky 25.11.2026)
PP_BLASS_DICKE = 1.0                   # Layout
KIPP_DECK = 0.10                       # Layout: Kipp-Zone um die Front (Micky 26.11.2026), je 1 ATR, quer über das Bild
PP_DICKE = 2.0                         # Layout: Strichstärke (Micky 25.11.2026: deutlicher, eine Linie)
PP_HELL = "#E6EAF0"                    # Layout: Pivotal Points aus Abwärtstrend und Erholung


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
         ba=None, tk=None, position=None):
    """SVG einer Ebene. e = tiefe.ebene, la = zonen.lage, t = zonen.trade (nur Tag),
    woche = (Lage der Spanne der Woche, Beginn) für den Tageschart, rs = {"index": Kurse, "sektor": Kurse oder None},
    gd = gewählte Durchschnitte (Kerzen der Ebene), anker = bis zu zwei Zeitpunkte für den eigenen AVWAP (Micky
    21.11.2026: selbst verankert; beide gesetzt = Zange), linien_ = gewählte Einblendungen (LINIEN_WAHL: Profil-Details, Market Profile, Livermore), profil = Profil
    am eigenen Anker (zonen.profil_seit) statt des Profils ab Beginn der Spanne, fest = zonen.stellungen der Ebene; woche =
    (Lage, Beginn, Name) der höheren Ebene als Rahmen (nur in der Stunde: die Base des Tages). Aufgeräumt 22.11.2026:
    ohne PbD, Phasenband, Szenarien, Gedächtnis, Treppe, Wanderung, Korridor und alte Spannen-Kästen.
    Der Zirkel im Chart (Micky 22.11.2026): Wendepunkte (Schwunghochs und -tiefs ab 2 ATR, vcp_zone.zigzag – dieselbe
    Rechnung wie Notizbuch und Stellungen) als Punkte; die eine Front als gestrichelte weiße Linie (blass ohne Setup) und als Raute auf seinem Wendepunkt (Micky 23.11.2026),
    Fehlausbruch, Rücktest und Decke der Gefangenen (ba = zonen.basis), ✈️ freie Bahn als Etikett, darunter die
    Zeichenleiste (🦬 Ausbruch, 📒 Livermores Bestätigung, 🦊 Fehlausbruch, 🏜️ leisester Tag seit 50 Kerzen, ⚡ Kraft ohne Weg, am Ende der Halt der
    Phase) und Momentum 🚀 am Ende der RS-Linie (tk = Ticker für Zirkel und Momentum). position = die gehaltene
    Position (depotleiste.positionsmarken): Einstieg ab dem Kauftag, Anfangsstopp, Stopp jetzt, enge Linie (Depot-Seite,
    Micky 26.11.2026: derselbe Chart wie die Titelseite, mit der Frontkarte)."""
    import avwap
    import rueckenwind
    import tiefe
    import zeichen
    import zonen
    if not e or not la:
        return f'<p style="color:{TEXT_2}">ungemessen – zu wenige Kerzen</p>'
    df = e["df"]
    n0 = max(0, len(df) - ZEIGEN[e["name"]])
    if la.get("beginn") is not None:               # die ganze Spanne im Bild
        n0 = min(n0, int(df.index.searchsorted(la["beginn"])))
    d = df.iloc[n0:]
    N = len(d)
    o, h, l, c, v = (d[k].to_numpy(float) for k in ("Open", "High", "Low", "Close", "Volume"))
    lo, hi = la["zone"] or (None, None)
    werte = [h.max(), l.min()] + ([lo, hi] if la["zone"] else []) + ([t["einstieg"], t["stopp"]] if t else []) \
        + [x for x in ((position or {}).get(k_) for k_ in ("einstieg", "anfang", "stopp", "enger")) if x]
    pp_offen, pp_stark, front_k = [], set(), set()                                  # Livermores Pivotal Points, die noch
    if "livermore" in linien_:                                                      # stehen (Micky 25.11.2026): kräftig
        import livermore                                                            # die Front (Spanne oben und unten)
        fr_ = livermore.front(df) or {}                                             # und je die nächste Stellung über
        pp_offen, pp_stark = fr_.get("offen", []), fr_.get("stark", set())          # und unter dem Kurs, die übrigen
        front_k = {(q_["i"], q_["art"]) for q_ in (fr_.get("oben"), fr_.get("unten")) if q_}   # Front zuerst beschriftet
        kurs_ = float(df["Close"].iloc[-1])                                         # blass; gefallene (Schluss 1 ATR
        schl = lambda p_: (p_["i"], p_["art"])                                      # noqa: E731  jenseits) gar nicht
        spanne_bild = float(h.max() - l.min())
        werte += [p_["preis"] for p_ in pp_offen if schl(p_) in pp_stark          # Layout: höchstens eine Bildhöhe weit
                  and l.min() - spanne_bild <= p_["preis"] <= h.max() + spanne_bild]
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
    if woche:                                                                       # die Front der höheren Ebene
        wl, wh = woche[0]["zone"]
        x0 = X(pos(woche[1])) - halb if woche[1] >= d.index[0] else LINKS
        A(f'<rect x="{x0:.1f}" y="{Y(wh):.1f}" width="{ende - x0:.1f}" height="{max(2, Y(wl) - Y(wh)):.1f}" fill="none" '
          f'stroke="{WOCHE_FARBE}" stroke-width="1.2" stroke-opacity="0.7"/>'                                    # Layout
          f'<text x="{x0 + 4:.1f}" y="{Y(wl) + 13:.1f}" fill="{WOCHE_FARBE}" font-size="11">{"Spanne der Woche" if woche[2] == "Woche" else "Spanne des Tages"} {woche[0]["name"]}</text>')  # Layout: unter dem Rahmen
    if la["zone"]:                                                                  # die Spanne von heute
        zs = pd.Timestamp(la["beginn"])
        xz = X(pos(zs)) - halb if zs >= d.index[0] else LINKS
        A(f'<rect x="{xz:.1f}" y="{Y(hi):.1f}" width="{ende - xz:.1f}" height="{max(2, Y(lo) - Y(hi)):.1f}" fill="{ZONE_FARBE}" '
          f'fill-opacity="0.10" stroke="{ZONE_FARBE}" stroke-width="1.8" stroke-dasharray="6 3"/>'  # Layout
          f'<text x="{xz + 6:.1f}" y="{Y(hi) - 6:.1f}" fill="{ZONE_FARBE}" font-size="16" font-weight="700">{la["name"]}</text>')  # Layout
        A(f'<line x1="{xz:.1f}" x2="{ende}" y1="{Y(la["poc"]):.1f}" y2="{Y(la["poc"]):.1f}" stroke="{POC_FARBE}" '
          f'stroke-width="1.4" stroke-dasharray="2 3"/>')                           # Layout
    piv = la.get("pivot") if la.get("zone") else None
    oben_ = piv is not None and abs(piv - hi) <= piv * PIVOT_GLEICH                   # Front auf der Oberkante
    am_pivot = bool(t and piv is not None and abs(t["einstieg"] - piv) <= piv * PIVOT_GLEICH)   # Auslöser = Front
    a_kipp = float(e.get("atr") or 0)
    import livermore                                                                # Gewicht einer Stellung (26.11.):

    def gewicht(preis):                                                             # stehende Pivotal Points innerhalb
        n_ = sum(abs(q_["preis"] - preis) <= livermore.STELLUNG_ATR * a_kipp for q_ in pp_offen)   # ½ ATR
        return f' · {n_} {"Decken" if preis > float(df["Close"].iloc[-1]) else "Böden"}' if n_ > 1 else ""
    if la["zone"]:                                    # Wörterbuch (Micky 26.11.2026): Front, Unterkante, Decke, Boden
        etiketten += ([] if oben_ else [(Y(hi), f"Spanne oben {zahl(hi)}", ZONE_FARBE)]) + \
                     [(Y(lo), f"Unterkante {zahl(lo)}{gewicht(lo)}", ZONE_FARBE), (Y(la["poc"]), f"POC {zahl(la['poc'])}", POC_FARBE)]
    short_ = bool(la.get("zone")) and ((t and t["richtung"] < 0) or la.get("phase") == "bruch"   # die Kante, an der
                                       or float(df["Close"].iloc[-1]) < lo)       # der Kurs steht (Audit 26.11.2026)
    kante = lo if short_ else piv                     # Kipp-Zone (Micky 26.11.2026, Frontkarte): long um die Front,
    if kante is not None and a_kipp > 0:              # short gespiegelt um die Unterkante; je 1 ATR (Livermores
                                                      # Bestätigung), oben grün, unten rot
        b_ = livermore.BESTAETIGUNG * a_kipp
        if short_:
            baender = ((kante, kante + b_, GRUEN, "🦊 Fehlausbruch", f"ein Schluss über {zahl(kante + b_)} (1 ATR über der Unterkante)", kante + b_),
                       (kante - b_, kante, ROT, "📒 Rückzug bestätigt", f"ein Tief unter {zahl(kante - b_)} (1 ATR unter der Unterkante)", kante - b_))
        else:
            baender = ((kante, kante + b_, GRUEN, "📒 Angriff bestätigt", f"ein Hoch über {zahl(kante + b_)} (1 ATR über der Front)", kante + b_),
                       (kante - b_, kante, ROT, "🦊 Fehlausbruch", f"ein Schluss unter {zahl(kante - b_)} (1 ATR unter der Front)", kante - b_))
        for y_a, y_b, farbe, text, wie, wert_ in baender:
            if y_b < pmin or y_a > pmax:
                continue
            A(f'<rect x="{LINKS}" y="{Y(min(y_b, pmax)):.1f}" width="{ende - LINKS}" '
              f'height="{max(1, Y(max(y_a, pmin)) - Y(min(y_b, pmax))):.1f}" fill="{farbe}" fill-opacity="{KIPP_DECK}">'
              f'<title>Kipp-Zone: {text} – {wie}</title></rect>')
            if pmin <= wert_ <= pmax:
                etiketten.append((Y(wert_), f"{text[:2]} {zahl(wert_)}", farbe))
    if position and position.get("einstieg"):            # die gehaltene Position (Depot-Seite)
        kt = pd.Timestamp(position["tag"]) if position.get("tag") else None
        xk = X(pos(kt)) if kt is not None and kt >= d.index[0] else LINKS
        for wert, farbe, strich, dicke, vor in ((position["einstieg"], BLAU, "6 4", 1.6, "Einstieg"),   # Layout
                                                (position.get("anfang"), TEXT_3, "4 4", 1.2, "Anfangsstopp"),   # Layout
                                                (position.get("stopp"), ROT, "", 2.2, "Stopp jetzt"),   # Layout
                                                (position.get("enger"), GELB, "", 2.0, f'enger: {position.get("enger_art", "")}')):
            if not wert or (vor == "Anfangsstopp" and wert == position.get("stopp")) or not pmin <= wert <= pmax:
                continue
            text = f'{vor} {zahl(wert)}'                                            # Etikett kurz, die Linie im Titel
            titel_ = text + (f' · {position.get("linie") or "Anfang"}' if vor == "Stopp jetzt" else "")
            A(f'<line x1="{xk:.1f}" x2="{ende}" y1="{Y(wert):.1f}" y2="{Y(wert):.1f}" stroke="{farbe}" stroke-width="{dicke}"'
              + (f' stroke-dasharray="{strich}"' if strich else "") + f'><title>{t_esc(titel_)}</title></line>')
            etiketten.append((Y(wert), text, farbe))
        if kt is not None and kt >= d.index[0]:
            A(f'<line x1="{xk:.1f}" x2="{xk:.1f}" y1="{OBEN}" y2="{OBEN + KURS_H}" stroke="{BLAU}" stroke-opacity="0.5" '
              f'stroke-dasharray="2 4"><title>Kauf am {kt:%d.%m.%Y}</title></line>')   # Layout
    if piv is not None and pmin <= piv <= pmax:          # die Front als eigene Linie (Micky 23.11.2026): gestrichelt weiß
        A(f'<line x1="{xz:.1f}" x2="{ende}" y1="{Y(piv):.1f}" y2="{Y(piv):.1f}" stroke="{PIVOT_FARBE}" '
          f'stroke-width="2.4" stroke-dasharray="8 4">'   # Layout
          f'<title>Front {zahl(piv)} – die Kante, an der die Waage kippt</title></line>')  # Layout
        etiketten.append((Y(piv), f"Front {zahl(piv)}{gewicht(piv)}", PIVOT_FARBE))
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
    beschriftet = [x for x in (piv, lo) if x is not None]                           # Front und Unterkante tragen schon ein
    for p_ in sorted(pp_offen, key=lambda q_: (q_["i"], q_["art"]) not in front_k):  # Livermores Pivotal Points als
        if not pmin <= p_["preis"] <= pmax:                                         # Linie ab ihrem Tag bis zum rechten
            continue                                                                # Rand (im Notizbuch doppelt
        stark = (p_["i"], p_["art"]) in pp_stark                                    # unterstrichen, Regel 8)
        x1_ = X(pos(p_["tag"])) if p_["tag"] >= d.index[0] else LINKS
        f_p = ROT if p_["farbe"] == "rot" else PP_HELL
        A(f'<line x1="{x1_:.1f}" x2="{ende}" y1="{Y(p_["preis"]):.1f}" y2="{Y(p_["preis"]):.1f}" stroke="{f_p}" '
          f'stroke-width="{PP_DICKE if stark else PP_BLASS_DICKE}" stroke-opacity="{1 if stark else PP_BLASS_DECK}">'
          f'<title>Livermores Pivotal Point {zahl(p_["preis"])} ({p_["tag"]:%d.%m.%y}) – {p_["farbe"]} unterstrichen, '
          f'aus {livermore.SPALTEN[p_["aus"]]} · steht noch{"" if stark else " (weiter entfernt)"}</title></line>')
        if stark and not any(abs(x_ - p_["preis"]) <= livermore.STELLUNG_ATR * a_kipp for x_ in beschriftet):
            beschriftet.append(p_["preis"])                                         # eine Stellung, ein Etikett
            wort_ = ("Front" if (p_["i"], p_["art"]) in front_k and p_["art"] == "hoch" else "Unterkante"
                     if (p_["i"], p_["art"]) in front_k else "Decke" if p_["preis"] > kurs_ else "Boden")
            etiketten.append((Y(p_["preis"]), f'{wort_} {zahl(p_["preis"])}{gewicht(p_["preis"])}', f_p))
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
    if la.get("pivot") is not None and la.get("beginn") is not None:                # die eine Front: sein Wendepunkt
        seit_z = (d.index >= pd.Timestamp(la["beginn"])) & (np.abs(h - la["pivot"]) <= la["pivot"] * PIVOT_GLEICH)
        if seit_z.any():
            j = int(np.nonzero(seit_z)[0][-1])
            y_ = Y(la["pivot"]) - 7                                                 # Layout: über dem Hoch
            A(f'<path d="M{X(j):.1f},{y_ - 6:.1f} L{X(j) + 6:.1f},{y_:.1f} L{X(j):.1f},{y_ + 6:.1f} '  # Layout: Raute
              f'L{X(j) - 6:.1f},{y_:.1f} Z" '                                       # Layout
              f'fill="{ZONE_FARBE}" stroke="#000" stroke-width="0.6"><title>Front (Livermores Pivotal Point) {zahl(la["pivot"])} · '
              f'{d.index[j]:%d.%m.%Y} – die Kante, an der die Waage kippt</title></path>')
    if ba and e["name"] != "Stunde":                                                # Fehlausbruch und Rücktest
        aus_ = ba.get("ausbruch") or {}                                              # Fehlausbruch (Livermore, 25.11.:
        marken = [(t_, "✗ Fehlausbruch", ROT) for t_, _ in aus_.get("gescheitert") or []]   # Schluss 1 ATR unter dem
        if aus_.get("ruecktest") and aus_.get("rueck_tag") is not None:            # Front; knapp darunter =
            marken.append((aus_["rueck_tag"], "⚠ Rücktest", AMPEL["gelb"]))                  # Rücktest)
        for t_, wort_, f_m in marken:
            if t_ < d.index[0]:
                continue
            j_ = pos(t_)
            y_m = min(Y(max(l[j_], pmin)) + 26, OBEN + KURS_H - 4)                  # Layout: unter der Kerze
            anker_ = "end" if X(j_) > ende - MARKE_RAND else "middle"                # Layout: nicht ins Profil
            A(f'<text x="{X(j_):.1f}" y="{y_m:.1f}" fill="{f_m}" font-size="11" text-anchor="{anker_}">{wort_}'
              f'<title>{t_esc(vcp_zone.ausbruch_text(aus_))}</title></text>')
        if aus_.get("gescheitert"):                                                 # Decke der Gefangenen: das Hoch
            t_g, h_g = aus_["gescheitert"][-1]                                      # des gescheiterten Vorstoßes – wer
            if pmin <= h_g <= pmax:                                                 # dort kaufte, will bei Einstand raus
                x_g = X(max(0, pos(t_g) - 8)) if t_g >= d.index[0] else X(0)        # Layout
                A(f'<line x1="{x_g:.1f}" x2="{ende}" y1="{Y(h_g):.1f}" y2="{Y(h_g):.1f}" stroke="{ROT}" '
                  f'stroke-width="1.2" stroke-dasharray="6 4"><title>Decke der Gefangenen: Hoch des Fehlausbruchs '
                  f'{zahl(h_g)} – wer dort kaufte, sitzt im Verlust und verkauft gern bei Einstand</title></line>')
                etiketten.append((Y(h_g), f"Decke der Gefangenen {zahl(h_g)}", ROT))
    if fest is not None and e["name"] != "Stunde":                                  # ✈️ freie Bahn (Livermore)
        if not fest.get("oben"):
            etiketten.append((OBEN + 4, "✈️ freie Bahn", GRUEN))   # Layout: ganz oben
        if not fest.get("unten"):
            etiketten.append((OBEN + KURS_H - 4, "✈️↓ freie Bahn", ROT))   # Layout: ganz unten
    if t:                                                                           # Schlachtplan (Micky 24.11.2026):
        x_t = X(max(0, N - 12))                                                     # Layout: die letzten 12 Kerzen
        ein_, stopp_ = t["einstieg"], t["stopp"]                                     # zu jedem Setup
        lang_ = t["richtung"] > 0                                                   # Ziel = die nächste Stellung in
        if lang_:                                                                   # Richtung des Setups (Wörterbuch)
            ziele = [f_["preis"] for f_ in ((fest or {}).get("oben") or []) if f_["preis"] > ein_]
            ziele += [h_ for _, h_ in ((ba or {}).get("ausbruch") or {}).get("gescheitert") or [] if h_ > ein_]   # + Gefangene
            ziel_ = min(ziele) if ziele else None
        else:
            ziele = [f_["preis"] for f_ in ((fest or {}).get("unten") or []) if f_["preis"] < ein_]
            ziel_ = max(ziele) if ziele else None
        rand_ = pmax if lang_ else pmin
        y_e, y_z, y_s = Y(min(max(ein_, pmin), pmax)), Y(min(max(ziel_, pmin), pmax) if ziel_ else rand_), Y(min(max(stopp_, pmin), pmax))
        chance = (f"bis zum Ziel {zahl(ziel_)} ({'+' if lang_ else '−'}{zahl(abs(ziel_ / ein_ - 1) * 100, 1)} %)" if ziel_
                  else "keine Stellung in Richtung des Setups – freie Bahn")
        A(f'<rect x="{x_t:.1f}" y="{min(y_z, y_e):.1f}" width="{ende - x_t:.1f}" height="{abs(y_e - y_z):.1f}" fill="{GRUEN}" '
          f'fill-opacity="{PLAN_DECK}"><title>Chance: vom Einstieg {zahl(ein_)} {chance}</title></rect>')
        A(f'<rect x="{x_t:.1f}" y="{min(y_e, y_s):.1f}" width="{ende - x_t:.1f}" height="{abs(y_s - y_e):.1f}" fill="{ROT}" '
          f'fill-opacity="{PLAN_DECK}"><title>Risiko: vom Einstieg {zahl(ein_)} bis zum Stopp {zahl(stopp_)} '
          f'(−{zahl(t["risiko"], 1)} %)</title></rect>')
    if t:                                                                           # der Trade: Auslöser bzw. Einstieg, Stopp
        gegen = " · ✗ Zirkel" if t.get("zirkel") == "✗" else ""                       # der Zirkel steht dagegen (25.11.)
        x_t = X(max(0, N - 12))                                                     # Layout: die letzten 12 Kerzen
        for wert, farbe, name in ((t["einstieg"], EINSTIEG_FARBE, "Auslöser" if t["wartet"] else "Einstieg"),
                                  (t["stopp"], ROT, "Stopp")):
            if name != "Stopp" and am_pivot:                                        # steht schon an die Front-Linie
                continue
            A(f'<line x1="{x_t:.1f}" x2="{ende}" y1="{Y(wert):.1f}" y2="{Y(wert):.1f}" stroke="{farbe}" stroke-width="2"/>')
            etiketten.append((Y(wert), f"{name} {zahl(wert)}" + (f' · {t["ampel"]} Risiko {zahl(t["risiko"], 1)} %'
                                                                 if name == "Stopp" else gegen), farbe))
    mp_an = "marketprofile" in linien_                                              # Market Profile (Zeit) nur per Schalter
    mitte_x = ende + PROFIL_W / 2 if mp_an else ende + 1                            # (Micky 26.11.2026), sonst das
    halb_w = PROFIL_W / 2 - 4 if mp_an else PROFIL_W - 6                            # Volumen über die ganze Breite (Layout)
    vmax_p, zmax_p = float(max(pr["volumen"])) or 1.0, float(max(pr["zeit"])) or 1.0
    det = zonen.profil_details(pr) if "details" in linien_ else None
    for a_, b_, w_, z_, k_ in zip(pr["grenzen"][:-1], pr["grenzen"][1:], pr["volumen"], pr["zeit"], pr["kauf"]):
        if b_ < pmin or a_ > pmax:
            continue
        y1, y2 = Y(min(b_, pmax)), Y(max(a_, pmin))
        hh = max(1, y2 - y1 - 0.6)  # Layout
        poc_, tpoc_ = a_ <= pr["poc"] <= b_, a_ <= pr["tpoc"] <= b_
        bz = max(1, halb_w * z_ / zmax_p)
        if mp_an:
            A(f'<rect x="{mitte_x - 1 - bz:.1f}" y="{y1 + 0.3:.1f}" width="{bz:.1f}" height="{hh:.1f}" fill="{ZEIT_FARBE}" '  # Layout
              f'fill-opacity="{0.9 if tpoc_ else 0.4}"/>')                          # Layout
        deck_v = 0.95 if poc_ else (0.75 if det["val"] <= (a_ + b_) / 2 <= det["vah"] else 0.3) if det else 0.6  # Layout
        bv = max(1, halb_w * w_ / vmax_p)
        bk = bv * (k_ / w_ if w_ > 0 else 0)                                        # Truppen: Käufer grün, Verkäufer rot
        A(f'<rect x="{mitte_x + 1:.1f}" y="{y1 + 0.3:.1f}" width="{bk:.1f}" height="{hh:.1f}" fill="{GRUEN}" fill-opacity="{deck_v}"/>'  # Layout
          f'<rect x="{mitte_x + 1 + bk:.1f}" y="{y1 + 0.3:.1f}" width="{max(0, bv - bk):.1f}" height="{hh:.1f}" fill="{ROT}" fill-opacity="{deck_v}"/>')  # Layout
        if poc_:
            A(f'<rect x="{mitte_x + 1:.1f}" y="{y1 + 0.3:.1f}" width="{bv:.1f}" height="{hh:.1f}" fill="none" stroke="{POC_FARBE}" stroke-width="1.2"/>')  # Layout
        if mp_an and det and z_ == 1 and any(e0 <= (a_ + b_) / 2 <= e1 for e0, e1 in det["einzel"]):   # Einzeldruck
            A(f'<rect x="{mitte_x - 1 - bz:.1f}" y="{y1 + 0.3:.1f}" width="{bz:.1f}" height="{hh:.1f}" fill="{EINZEL_FARBE}"/>')  # Layout
    A(f'<text x="{ende + PROFIL_W / 2:.1f}" y="{OBEN - 4}" fill="{TEXT_3 if profil is None else ANKER_FARBE[0]}" font-size="10" '  # Layout
      f'text-anchor="middle">{"Zeit ◂ ▸ " if mp_an else ""}Käufer | Verkäufer (geschätzt) seit {pd.Timestamp(pr["ab"]):%d.%m.}{" (eigener Anker)" if profil else ""}</text>')                                    # Layout
    ab_ = pd.Timestamp(pr["ab"])                                                     # Zeitraum unter dem Profil
    n_pr = int((df.index >= ab_).sum())                                             # (Micky 24.11.2026)
    A(f'<text x="{ende + PROFIL_W / 2:.1f}" y="{OBEN + KURS_H + 12}" fill="{TEXT_3}" font-size="10" text-anchor="middle">'   # Layout
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
    if mp_an and abs(pr["tpoc"] - pr["poc"]) > tiefe.stufe(la["kurs"]) * 1.5:                # Layout: mehr als eine Stufe auseinander
        etiketten.append((Y(pr["tpoc"]), f"Zeit-POC {zahl(pr['tpoc'])}", ZEIT_FARBE))
    reihe = sorted(etiketten, key=lambda x: x[0])                                   # rechts, ohne Überlappung und in
    platz = []                                                                      # der Reihenfolge der Preise (Micky
    for y0, _, _ in reihe:                                                          # 25.11.2026: ein Etikett springt
        platz.append(max(y0, OBEN - 4, platz[-1] + ZEILE if platz else float("-inf")))   # Layout: nicht weit weg – von oben
    grenze = OBEN + KURS_H + 4                                                      # Layout: nach unten stapeln, dann von
    for k_ in range(len(platz) - 1, -1, -1):                                        # unten nach oben in den
        platz[k_] = min(platz[k_], grenze)                                          # Kursbereich schieben (nicht
        grenze = platz[k_] - ZEILE                                                  # ins Volumen)
    for y_, (_, text, farbe) in zip(platz, reihe):
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
        for tag_, z_, text in ((a_b["tag"], "🦬", "Ausbruch über die Front"
                                + (" mit Volumen" if a_b["mit_volumen"] else " ohne Volumen")),
                               (a_b.get("fehl_tag"), "🦊", "Fehlausbruch: Schluss zurück unter der Front"),
                               (a_b.get("bestaetigt_tag"), "📒", "Livermore: Ausbruch bestätigt – Hoch 1 ATR über der Front")):
            if tag_ is not None and (z_ != "🦊" or a_b["fehl"]) and pd.Timestamp(tag_) >= d.index[0]:
                leiste.setdefault(pos(tag_), []).append((z_, text))
    if tk and e["name"] != "Stunde":                                                # Halt der Jahreszeit: jetzt
        zk = zeichen.zirkel((zeichen.laden().get("titel") or {}).get(tk))
        sym, wort, grund = zeichen.halt(zk)                                         # Halt der Phase (24.11.2026)
        if sym:
            leiste.setdefault(N - 1, []).append((sym, f"Jahreszeit {wort}" + (f" – {grund}" if grund else "")
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
    teile = [(ZONE_FARBE, "Spanne von heute: zwischen Front (letzter Pivotal Point oben) und Unterkante (letzter "
                          "Pivotal Point unten); in der Stunde ohne Notizbuch die Balance · POC grün gepunktet"),
             (DUENN_FARBE, "Schlucht: dünne Stelle des Profils quer über das Gelände – dort fällt der Kurs durch"),
             (GRUEN, "Profil rechts: Käufer grün | Verkäufer rot – geschätzt aus steigenden und fallenden Kerzen; mit dem Schalter „Market Profile“ links davon die Zeit (lila, Zeit-POC, Einzeldrucke)"),
             (WERT_FARBE, "Profil-Details: VAH/VAL = Wertzone (70 % des Volumens, kräftig) · ◀ Knoten (dicke Stellen) · "
              "blauer Streifen = dünne Stelle · weiß im Zeitprofil = Einzeldruck (nur eine Kerze)"),
             (WOCHE_FARBE, "Rahmen in der Stunde: die Spanne des Tages"),
             (ANKER_FARBE[0], "eigener AVWAP 1 · AVWAP 2 orange · dazwischen die Zange"),
             (WENDE_FARBE, "● Wendepunkte: Schwunghochs und -tiefs ab 2 ATR (Livermores 6 Punkte in ATR) – hohl = noch "
              "nicht bestätigt, klein und blass = Secondary (kein neues Extrem); aus ihnen entstehen Notizbuch, Spanne und "
              "Stellungen"),
             (PIVOT_FARBE, "- - Front (◆ auf ihrem Wendepunkt): die Kante, an der die Waage kippt – Livermores letzter "
              "Pivotal Point oben (Livermores Pivot)"),
             (ROT, "— Livermores Pivotal Points (Schalter „Livermore“, auf jeder Ebene aus ihren Kerzen; im Notizbuch doppelt unterstrichen): rot aus "
              "Aufwärtstrend und Reaktion, hell (im Buch schwarz) aus Abwärtstrend und Erholung; jeder, der noch steht, "
              "als Linie ab seinem Tag bis zum rechten Rand – kräftig mit Preis Front und Unterkante und je die nächste "
              "Stellung über dem Kurs (Decke) und darunter (Boden), die übrigen blass; gefallen (Schluss 1 ATR jenseits) = weg"),
             (GRUEN, "Kipp-Zone (Frontkarte): long 1 ATR über der Front grün – ein Hoch darüber bestätigt den Angriff (📒, "
              "Livermores 3 Punkte); 1 ATR darunter rot – ein Schluss darunter ist der Fehlausbruch (🦊). Short "
              "gespiegelt an der Unterkante: ein Tief 1 ATR darunter bestätigt den Rückzug (📒), ein Schluss 1 ATR "
              "darüber ist die Falle (🦊)"),
             (TEXT_2, "Gewicht einer Stellung: „· 4 Böden“ am Etikett = so viele stehende Pivotal Points liegen "
              "innerhalb ½ ATR zusammen"),
             (EINSTIEG_FARBE, "Schlachtplan: grüne Fläche vom Einstieg bis zum Ziel (nächste Stellung in Richtung des Setups; "
              "freie Bahn bis zum Rand), rote Fläche bis zum Stopp (das Risiko)"),
             (GRUEN, "✈️ freie Bahn: keine Stellung über dem Kurs (✈️↓ darunter) – Livermores Linie des geringsten Widerstands"),
             (TEXT_2, "Zeichenleiste: 🦬 Ausbruch · 📒 Livermores Bestätigung (1 ATR über der Front) · 🦊 Fehlausbruch · 🏜️ leisestes Volumen seit 50 Kerzen · ⚡ Kraft ohne Weg · "
              "Halt der Jahreszeit (Zirkel) rechts, jetzt (🏰 hält · 🌊 Welle · ⛈️ Sturm · 🌱 Aufbruch naht) · E Zahlentag (Maus darauf: Reaktion des Kurses), rechts 📅 der "
              "nächste Termin · Momentum 🚀 am Ende der RS-Linie"),
             (SCHNITT_FARBE, "Weiße Linie im Volumen: Schnitt der letzten 50 Tage (Woche: 10 Wochen) – Balken darüber "
              "kräftig, darunter blass · unter dem Profil sein Zeitraum"),
             (TEXT_3, "Über jeder Kerze: Balkennummer (von rechts) für den eigenen AVWAP")]
    return (f'<details><summary style="cursor:pointer;color:{TEXT_2};font-size:14px">Legende</summary>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:8px;font-size:13px;color:{TEXT_2}">'
            + "".join(f'<span><span style="display:inline-block;width:14px;height:4px;background:{f};vertical-align:middle;'
                      f'margin-right:6px"></span>{t(x)}</span>' for f, x in teile) + '</div></details>')
