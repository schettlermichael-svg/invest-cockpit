"""Der Zonenchart (Micky 21.11.2026): wenig, aber aussagekräftig – dasselbe Bild für Woche, Tag und Stunde.

Kursfeld: Kerzen; die Zone von heute als gelber Rahmen mit P, b oder D und ihr POC; die Zonen der Vergangenheit nach
der PbD-Kette (zonen.kette) als Kästen von Körper zu Körper, die Dochte blass (erledigt blass, offen kräftiger mit 🪝 und
bis zum rechten Rand verlängert – der Magnet); zuschaltbar ihre POCs, die nackten POCs bis rechts, die POC-Treppe und
die Wanderung des POC in der Zone von heute; im Tageschart die Wochenzone als feiner Rahmen; der Trade (Einstieg,
Stopp, Ziel); nach Wahl Durchschnitte und der eigene AVWAP (zwei Anker, Zange). Rechts das eine Profil der Ebene: Zeit
und Volumen gespiegelt, ab Beginn des Impulses. Darunter das Phasenband nach PbD, das Volumen und das Feld der
relativen Stärke gegen den S&P 500 und gestrichelt gegen den Sektor (Punkte RS-Hoch bzw. RS-Tief vor Kurs)."""
import numpy as np
import pandas as pd

from gestaltung import BLAU, GELB, GRUEN, LILA, RAND, ROT, TEXT_2, TEXT_3, zahl

B = 1200                               # Layout: Breite des Bildes
LINKS, RECHTS, PROFIL_W = 56, 190, 110  # Layout: Preisachse, Etiketten, Profil (Zeit links, Volumen rechts)
OBEN, KURS_H = 16, 360                 # Layout: Kursfeld
BAND_H, VOL_H, RS_H = 8, 60, 90        # Layout: Phasenband, Volumen, relative Stärke
LUECKE = 14                            # Layout: Abstand zwischen den Feldern
ZEIGEN = {"Woche": 104, "Tag": 126, "Stunde": 140}   # Kerzen im Bild (2 Jahre, 6 Monate, 20 Handelstage)
JAHR = {"Woche": 52, "Tag": 252, "Stunde": 252 * 7}  # Kerzen je Jahr (RS-Hoch vor Kurs)
PFEIL_N = 10                           # RS-Pfeil: die letzten 10 Kerzen
PFEIL_LEICHT, PFEIL_STARK = 1, 3       # ↗/↘ ab 1 %, ↑/↓ ab 3 % (wie bisher im Cockpit)
ZONE_FARBE = "#EDA100"                 # Zone wie in Vorwalds Bildern gelb
POC_FARBE = "#1BAF7A"
ALT_FARBE = "#8B97A8"
WOCHE_FARBE = "#7DB4FF"
EINSTIEG_FARBE = "#E6EAF0"
RS_HOCH_FARBE, RS_TIEF_FARBE = "#FFD166", "#FF6B6B"
BAND = {"i+": (GRUEN, 1.0), "i-": (ROT, 1.0), "a+": (GRUEN, 0.72), "a-": (ROT, 0.72), "b+": (GRUEN, 0.45),
        "b-": (ROT, 0.45), "b": (GELB, 0.85), "f": ("#F0883E", 0.9)}   # Farbe = Richtung, Stärke = Phase (Micky 21.11.2026)
GD_FARBE = {10: "#F0883E", 20: "#FF7EB6", 50: BLAU, 150: LILA, 200: "#D9B26F"}   # wie bisher im Cockpit
GD_WAHL = (10, 20, 50, 150, 200)
ANKER_FARBE = ("#4DD0E1", "#FF8A65")   # eigener AVWAP: Anker 1 türkis, Anker 2 orange
ZEIT_FARBE = LILA                      # Zeitprofil (Market Profile)
LINIEN_WAHL = {"poc": "POC je Zone", "nackt": "Nackte POCs", "treppe": "POC-Treppe", "wanderung": "Wanderung",
               "korridor": "Korridor", "gedaechtnis": "🧠 Gedächtnis", "details": "Profil-Details",
               "geschichte": "Geschichte"}
FESTUNG_FARBE = "#C9D1DC"              # Festungen der Lagekarte
SCHLUCHT_ETIKETTEN = 2                 # Layout: höchstens 2 Schluchten beschriftet (die breitesten)
WERT_FARBE = "#E6EAF0"                 # VAH, VAL
DUENN_FARBE = "#7DB4FF"                # dünne Stellen (LVN)
EINZEL_FARBE = "#FFFFFF"               # Einzeldrucke im Zeitprofil
LVN_ETIKETTEN = 3                      # Layout: höchstens 3 dünne Stellen beschriftet (die breitesten)
GEDAECHTNIS_FARBE = "#FFD166"
KREIS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
KORRIDOR_FARBE = "#7DB4FF"
STOPP_BAND = 0.25                      # Layout: Festung als Band von ¼ ATR
RAND_SPIEL = 0.04                      # Layout: 4 % Luft über und unter den Kursen


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


def bild(e, la, hist, t=None, laufend=False, woche=None, rs=None, gd=(), anker=(), linien_=(), profil=None, ged=None,
         fest=None):
    """SVG einer Ebene. e = tiefe.ebene, la = zonen.lage, hist = zonen.historie, t = zonen.trade (nur Tag),
    woche = (Lage der Wochenzone, Beginn) für den Tageschart, rs = {"index": Kurse, "sektor": Kurse oder None},
    gd = gewählte Durchschnitte (Kerzen der Ebene), anker = bis zu zwei Zeitpunkte für den eigenen AVWAP (Micky
    21.11.2026: selbst verankert; beide gesetzt = Zange), linien_ = gewählte POC-Linien (LINIEN_WAHL), profil = Profil
    am eigenen Anker (zonen.profil_seit) statt des Profils ab Impulsbeginn, ged = zonen.gedaechtnis der Ebene, fest =
    zonen.festungen der Ebene; woche = (Lage, Beginn, Name) der höheren Ebene als Rahmen."""
    import avwap
    import rueckenwind
    import tiefe
    import zeichen
    import zonen
    if not e or not la:
        return f'<p style="color:{TEXT_2}">ungemessen – zu wenige Kerzen</p>'
    df = e["df"]
    n0 = max(0, len(df) - ZEIGEN[e["name"]])
    pb = e.get("pbd")
    if pb:                                         # die ganze Formation im Bild (Impulsbeginn)
        n0 = min(n0, int(df.index.searchsorted(pb["impuls_tag"])))
    d = df.iloc[n0:]
    N = len(d)
    o, h, l, c, v = (d[k].to_numpy(float) for k in ("Open", "High", "Low", "Close", "Volume"))
    lo, hi = la["zone"]
    kaesten = [z for z in hist if z["ende"] >= d.index[0]]
    werte = [h.max(), l.min(), lo, hi] + ([t["stopp"], t["ziel"]] if t else [])
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
    korridor = zonen.korridor(hist, la["kurs"]) if "korridor" in linien_ else (None, None)
    spanne_ = float(h.max() - l.min())
    korridor = tuple(z if z and l.min() - spanne_ <= z["poc"] <= h.max() + spanne_ else None for z in korridor)  # Layout: höchstens eine Bildhöhe
    werte += [z["poc"] for z in korridor if z]
    pmin, pmax = min(werte), max(werte)
    rand = (pmax - pmin) * RAND_SPIEL or 1
    pmin, pmax = pmin - rand, pmax + rand
    ende = B - RECHTS - PROFIL_W
    breite = ende - LINKS
    X = lambda i: LINKS + breite * (i + 0.5) / N                                   # noqa: E731  # Layout
    Y = lambda y: OBEN + KURS_H * (1 - (y - pmin) / (pmax - pmin))                 # noqa: E731
    pos = lambda t_: min(max(int(d.index.searchsorted(pd.Timestamp(t_))), 0), N - 1)   # noqa: E731
    halb = breite / N / 2
    y_band = OBEN + KURS_H + LUECKE
    y_vol = y_band + BAND_H + LUECKE
    y_rs = y_vol + VOL_H + LUECKE + 14                                              # Layout: Platz für die Überschrift
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
    for z in kaesten:                                                               # Zonen der Vergangenheit
        x0 = X(pos(z["start"])) - halb if z["start"] >= d.index[0] else LINKS
        x1 = X(pos(z["ende"])) + halb
        deck = 0.30 if z["offen"] else 0.16                                         # Layout: gut sichtbar (Micky 21.11.2026)
        if "geschichte" in linien_:                                                 # die alten Kästen nur auf Wunsch
            A(f'<rect x="{x0:.1f}" y="{Y(z["docht_hoch"]):.1f}" width="{max(2, x1 - x0):.1f}" '
              f'height="{max(1, Y(z["docht_tief"]) - Y(z["docht_hoch"])):.1f}" fill="{ALT_FARBE}" fill-opacity="0.07"/>')  # Layout: Dochte blass
            A(f'<rect x="{x0:.1f}" y="{Y(z["hoch"]):.1f}" width="{max(2, x1 - x0):.1f}" height="{max(1, Y(z["tief"]) - Y(z["hoch"])):.1f}" '
              f'fill="{ALT_FARBE}" fill-opacity="{deck}" stroke="{ALT_FARBE}" stroke-width="1.2" stroke-opacity="{min(1, deck * 3):.2f}">'  # Layout
              f'<title>{z["form"]}-Zone {z["start"]:%d.%m.%y}–{z["ende"]:%d.%m.%y}: Körper {zahl(z["tief"])}–{zahl(z["hoch"])} · '
              f'POC {zahl(z["poc"])} · {"offen – seitdem nie wieder angelaufen" if z["offen"] else "erledigt"}</title></rect>'
              f'<text x="{x0 + 3:.1f}" y="{Y(z["docht_hoch"]) - 3:.1f}" fill="#C9D1DC" font-size="12" font-weight="700">{z["form"]}{"⚡" if z.get("blitz") else ""}</text>')  # Layout
        if "poc" in linien_:
            A(f'<line x1="{x0:.1f}" x2="{x1:.1f}" y1="{Y(z["poc"]):.1f}" y2="{Y(z["poc"]):.1f}" stroke="{POC_FARBE}" '
              f'stroke-width="1.4" stroke-opacity="0.8"/>')                         # Layout
        if "nackt" in linien_ and pmin <= z["poc"] <= pmax:                         # nackt bis rechts, sonst bis zur Berührung
            x2 = ende if z["nackt"] else X(pos(z["beruehrt"]))
            if x2 > x1:
                A(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{Y(z["poc"]):.1f}" y2="{Y(z["poc"]):.1f}" stroke="{POC_FARBE}" '
                  f'stroke-width="1.2" stroke-dasharray="4 3" stroke-opacity="{0.9 if z["nackt"] else 0.35}"/>')  # Layout
                if z["nackt"]:
                    etiketten.append((Y(z["poc"]), f"nackter POC {zahl(z['poc'])}", POC_FARBE))
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
          f'<text x="{x0 + 4:.1f}" y="{Y(wl) + 13:.1f}" fill="{WOCHE_FARBE}" font-size="11">{"Wochenzone" if woche[2] == "Woche" else "Tageszone"} {woche[0]["form"]}</text>')  # Layout: unter dem Rahmen
    zs = pd.Timestamp(pb["zone_start"]) if pb else pd.Timestamp(e["struktur"]["balance_start"])
    xz = X(pos(zs)) - halb if zs >= d.index[0] else LINKS
    A(f'<rect x="{xz:.1f}" y="{Y(hi):.1f}" width="{ende - xz:.1f}" height="{max(2, Y(lo) - Y(hi)):.1f}" fill="{ZONE_FARBE}" '
      f'fill-opacity="0.10" stroke="{ZONE_FARBE}" stroke-width="1.8" stroke-dasharray="6 3"/>'  # Layout
      f'<text x="{xz + 6:.1f}" y="{Y(hi) - 6:.1f}" fill="{ZONE_FARBE}" font-size="20" font-weight="700">{la["form"]}{"⚡" if la.get("blitz") else ""}</text>')  # Layout
    A(f'<line x1="{xz:.1f}" x2="{ende}" y1="{Y(la["poc"]):.1f}" y2="{Y(la["poc"]):.1f}" stroke="{POC_FARBE}" '
      f'stroke-width="1.4" stroke-dasharray="2 3"/>')                               # Layout
    etiketten += [(Y(hi), f"Zone oben {zahl(hi)}", ZONE_FARBE), (Y(lo), f"Zone unten {zahl(lo)}", ZONE_FARBE),
                  (Y(la["poc"]), f"POC {zahl(la['poc'])}", POC_FARBE)]
    if "treppe" in linien_:                                                         # POC-Treppe: Wert steigt, fällt, überlappt
        punkte = [((x0_ + x1_) / 2, z) for z in kaesten
                  for x0_, x1_ in [(X(pos(z["start"])) - halb if z["start"] >= d.index[0] else LINKS, X(pos(z["ende"])) + halb)]]
        punkte.append(((xz + ende) / 2, {"poc": la["poc"], "val": la["profil"]["val"], "vah": la["profil"]["vah"]}))
        for (xa, za), (xb, zb) in zip(punkte[:-1], punkte[1:]):
            farbe = {1: GRUEN, -1: ROT, 0: ALT_FARBE}[zonen.treppe(za, zb)]
            A(f'<line x1="{xa:.1f}" y1="{Y(za["poc"]):.1f}" x2="{xb:.1f}" y2="{Y(zb["poc"]):.1f}" stroke="{farbe}" '
              f'stroke-width="1.2" stroke-dasharray="5 3" marker-end="url(#spitze)" stroke-opacity="0.75"/>')  # Layout
    if "gedaechtnis" in linien_ and ged:                                            # Gedächtnis: gleiche Lage früher
        nr_ = 0
        for g_ in ged["treffer"]:
            if g_["ebene"] != e["name"] or g_["ende"] < d.index[0]:
                continue
            x0 = X(pos(g_["start"])) - halb if g_["start"] >= d.index[0] else LINKS
            x1 = X(pos(g_["ende"])) + halb
            A(f'<rect x="{x0:.1f}" y="{Y(g_["hoch"]):.1f}" width="{max(2, x1 - x0):.1f}" height="{max(1, Y(g_["tief"]) - Y(g_["hoch"])):.1f}" '
              f'fill="none" stroke="{GEDAECHTNIS_FARBE}" stroke-width="1.6"/>'      # Layout
              f'<text x="{(x0 + x1) / 2:.1f}" y="{Y(g_["tief"]) + 16:.1f}" fill="{GEDAECHTNIS_FARBE}" font-size="14" '  # Layout
              f'text-anchor="middle">{KREIS[nr_] if nr_ < len(KREIS) else nr_ + 1}<title>{g_["start"]:%d.%m.%y}: danach '
              f'{"↑" if g_["seite"] == "oben" else "↓"} {g_["weite"]:.1f} Zonenhöhen</title></text>')  # Layout
            nr_ += 1
        A(f'<text x="{LINKS + 6}" y="{OBEN + 14}" fill="{GEDAECHTNIS_FARBE}" font-size="12">'  # Layout
          f'{zonen.gedaechtnis_text(ged).replace("&", "&amp;").replace("<", "&lt;")}</text>')   # Layout
    if any(korridor):                                                               # Korridor zwischen den nackten POCs
        oben_, unten_ = korridor
        ya = Y(oben_["poc"]) if oben_ else OBEN
        yb = Y(unten_["poc"]) if unten_ else OBEN + KURS_H
        x_k = X(pos(max(z["ende"] for z in korridor if z))) if max(z["ende"] for z in korridor if z) >= d.index[0] else LINKS
        A(f'<rect x="{x_k:.1f}" y="{ya:.1f}" width="{max(2, ende - x_k):.1f}" height="{max(1, yb - ya):.1f}" '
          f'fill="{KORRIDOR_FARBE}" fill-opacity="0.07"/>')                         # Layout
        for z, pfeil in ((oben_, "↑"), (unten_, "↓")):
            if z:
                A(f'<line x1="{x_k:.1f}" x2="{ende}" y1="{Y(z["poc"]):.1f}" y2="{Y(z["poc"]):.1f}" stroke="{KORRIDOR_FARBE}" '
                  f'stroke-width="1.4" stroke-dasharray="6 3"/>')                   # Layout
                etiketten.append((Y(z["poc"]), f"Korridor {pfeil} {zahl(z['poc'], 0)} · {(z['poc'] / la['kurs'] - 1) * 100:+.0f} %",
                                  KORRIDOR_FARBE))
    if "wanderung" in linien_:                                                      # POC-Wanderung in der Zone von heute
        w_ = zonen.wanderung(e, la["beginn"]).reindex(d.index)
        pkt = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(w_.to_numpy(float)) if not np.isnan(x))
        if pkt:
            A(f'<polyline points="{pkt}" fill="none" stroke="{POC_FARBE}" stroke-width="2.2" stroke-linejoin="round"/>')  # Layout
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
    bw = max(1.0, breite / N * 0.6)                                                 # Layout: Kerzenbreite
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
    if t:                                                                           # der Trade: Einstieg, Stopp, Ziel
        x_t = X(max(0, N - 12))                                                     # Layout: die letzten 12 Kerzen
        for wert, farbe, name in ((t["einstieg"], EINSTIEG_FARBE, "Einstieg"), (t["stopp"], ROT, "Stopp"),
                                  (t["ziel"], GRUEN, "Ziel")):
            A(f'<line x1="{x_t:.1f}" x2="{ende}" y1="{Y(wert):.1f}" y2="{Y(wert):.1f}" stroke="{farbe}" stroke-width="2"/>')
            etiketten.append((Y(wert), f"{name} {zahl(wert)}" + (f' · {t["ampel"]} CRV {zahl(t["crv"] or 0, 1)}'
                                                                 if name == "Ziel" else ""), farbe))
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
    for y_, text, farbe in sorted(etiketten):                                       # rechts, ohne Überlappung
        while any(abs(y_ - b_) < 14 for b_ in belegt):                              # Layout: 14 px je Zeile
            y_ += 14                                                                # Layout
        belegt.append(y_)
        A(f'<text x="{ende + PROFIL_W + 6}" y="{y_ + 4:.1f}" fill="{farbe}" font-size="12">{text}</text>')  # Layout
    band = zonen.band(e, la)[n0:]                                                   # Phasenband nach PbD
    vorher = None
    for i, p_ in enumerate(band):
        if p_:
            farbe, deck = BAND[p_]
            A(f'<rect x="{X(i) - halb:.1f}" y="{y_band}" width="{2 * halb + 0.3:.1f}" height="{BAND_H}" fill="{farbe}" '  # Layout
              f'fill-opacity="{deck}"/>')
            if p_ in ("a+", "a-", "f") and p_ != vorher:                            # erster Ausbruch bzw. Scheitern
                A(f'<text x="{X(i):.1f}" y="{y_band - 2}" font-size="11" text-anchor="middle">{"🦊" if p_ == "f" else "💥"}</text>')  # Layout
        vorher = p_
    A(f'<text x="{ende + 2}" y="{y_band + BAND_H}" fill="{TEXT_3}" font-size="10">Phase</text>')  # Layout
    vmax = v.max() or 1
    schnitt = pd.Series(v).rolling(min(50, N)).mean().to_numpy()                    # Layout: 50 Kerzen Schnitt
    for i in range(N):
        hv = VOL_H * v[i] / vmax
        hoch = not np.isnan(schnitt[i]) and v[i] > schnitt[i]
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y_vol + VOL_H - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" '
          f'fill="{GRUEN if c[i] >= o[i] else ROT}" fill-opacity="{0.85 if hoch else 0.35}"/>')  # Layout
    A(f'<text x="{ende + 2}" y="{y_vol + 12}" fill="{TEXT_3}" font-size="10">Volumen</text>')   # Layout
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
    teile = [(ZONE_FARBE, "Front: Zone von heute (P, b, D aus der Form des Profils, ⚡ = Zeit widerspricht) · POC grün gepunktet"),
             (FESTUNG_FARBE, "Festung ▲▼: bewährter Umkehrpreis, gebrochene Kante einer alten Zone oder AVWAP eines großen "
              "Ereignisses – je Richtung die 2 nächsten, mit Abstand"),
             (DUENN_FARBE, "Schlucht: dünne Stelle des Profils quer über das Gelände – dort fällt der Kurs durch"),
             (GRUEN, "Profil rechts: Zeit (lila) ◂ ▸ Käufer grün | Verkäufer rot – geschätzt aus steigenden und fallenden Kerzen"),
             (ALT_FARBE, "Geschichte (Knopf): die alten Zonen der PbD-Kette als Kästen"),
             (POC_FARBE, "POC je Zone · gestrichelt = nackter POC (seitdem nie berührt) · dicke Linie = Wanderung in der Zone"),
             (GRUEN, "POC-Treppe: grün = Wert steigt über die alte Wertzone, rot = fällt darunter, grau = überlappt"),
             (GEDAECHTNIS_FARBE, "🧠 Gedächtnis: gleiche Lage früher (Impuls davor, Treppe, POC im Bauch) mit ①②③ – "
              "Häufigkeit des Ausgangs, kein Urteil"),
             (WERT_FARBE, "Profil-Details: VAH/VAL = Wertzone (70 % des Volumens, kräftig) · ◀ Knoten (dicke Stellen) · "
              "blauer Streifen = dünne Stelle · weiß im Zeitprofil = Einzeldruck (nur eine Kerze)"),
             (KORRIDOR_FARBE, "Korridor: Raum zwischen dem nächsten nackten POC über und unter dem Kurs, mit Abstand in %"),
             (WOCHE_FARBE, "Rahmen: Front der höheren Ebene (im Tag die Wochenzone, in der Stunde die Tageszone)"),
             (GRUEN, "Phase: Farbe = Richtung (grün auf, rot ab) · kräftig = Impuls, mittel = Ausbruch 💥, blass = Zone in "
              "steigender bzw. fallender Treppe"), (GELB, "Phase: Zone ohne Richtung (überlappt die Zone davor)"),
             ("#F0883E", "Phase: Scheitern 🦊"), (ANKER_FARBE[0], "eigener AVWAP 1 · AVWAP 2 orange · dazwischen die Zange"),
             (TEXT_3, "Über jeder Kerze: Balkennummer (von rechts) für den eigenen AVWAP")]
    return (f'<details><summary style="cursor:pointer;color:{TEXT_2};font-size:14px">Legende</summary>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:8px;font-size:13px;color:{TEXT_2}">'
            + "".join(f'<span><span style="display:inline-block;width:14px;height:4px;background:{f};vertical-align:middle;'
                      f'margin-right:6px"></span>{t(x)}</span>' for f, x in teile) + '</div></details>')
