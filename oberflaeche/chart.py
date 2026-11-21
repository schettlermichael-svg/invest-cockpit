"""Der Chart der Titelseite als SVG – VCP-Scanner (06.11.2026): nur, was wir gerade erarbeiten.

Hauptfenster: Kerzen, GD50/150/200 (Woche: GD10W/30W/40W), auf Wunsch GD10 und GD20 (Kullamägi, nur Tageschart), die
Zonen des VCP-Scanners (Baustein 1: Base, Flagge, Konsolidierung mit Vorgeschichte, Fahnenstange und grobem ZigZag) –
„Aktuell“ nur das Setup jetzt, „Historie“ dazu alle abgeschlossenen Zonen mit ↑ am Ausbruch.
Darunter Volumen mit 50er-Schnitt und dem Volumenband (türkis = Ruhe, grün/rot = viel Volumen am Aufwärts-/Abwärtstag), ganz unten die relative Stärke gegen den S&P 500 und gestrichelt gegen den eigenen
Sektor-ETF (beide links bei 100).
Erweitert 09.11.2026 (Lagekarte des Setups): Kaufzone Pivot bis +5 %, eine Stopp-Linie 1,5 ATR vom Einstieg (Short darüber),
Ausbruchstag mit Volumen-Vielfachem, Fehlausbruch, Ermüdungstag, Basennummer an der Zone, AVWAP nach Wahl (Hoch, Tief, Ereignistag), Earnings
mit Kursreaktion und nächstem Termin, RS-Rang/Tempo und „RS-Hoch vor Kurs“ an der RS-Linie, Volumen nach Schluss zum
Vortag gefärbt; darunter der Stundenchart der letzten 10 Handelstage (stunden()).
Erweitert 13.11.2026 (Blinde Flecken): S&P 500 gestrichelt im Kurschart (am linken Rand auf den Kurs gelegt), die
gemessenen Zeichen aus zeichen.py (Schwungpunkte, Pocket Pivot, Spring/Upthrust, höheres Tief bzw. tieferes Hoch gegen
den Index), Abgabetage und verdeckte Abgabe über dem Volumen, „RS-Tief vor Kurs“ als Spiegel des RS-Hochs.
Der frühere Chart (Market-Profile-Zonen, POC-Treppe, Pivot, Stopps, Volumenprofil, Phasenband, Zahlentermine) liegt in
_to_delete/chart_vor_vcp_2026-11-06.py.
"""
import numpy as np
import pandas as pd


from gestaltung import BLAU, GELB, GRUEN, LILA, RAND, ROT, TEXT, TEXT_2, TEXT_3, zahl

from masse import JAHR_TAGE  # noqa: E402
VOL_RUHE, VOL_EHER_RUHIG, VOL_HOCH = 0.5, 0.75, 1.5   # Volumenband: Ruhe bis 50 %, eher ruhig bis 75 %, deutlich ab 150 %
RS_PFEIL, RS_PFEIL_STARK = 1, 3     # RS-Pfeil: ↗/↘ ab 1 Punkt, ↑/↓ ab 3 Punkten Änderung
RS_PFEIL_TAGE, RS_PFEIL_WOCHEN = 10, 3   # RS-Pfeil: Änderung der letzten 10 Tage (Wochenchart: 3 Wochen)
SCHWUNG_N = 5                     # Dow-Schwungpunkte im Chart: 5 Tage links und rechts
try:
    from zeichen import RS_HOCH as RS_MASS       # RS-Linie „am Hoch“: ein Maßstab für die ganze App (0,99)
except Exception:  # noqa: BLE001
    RS_MASS = 0.99

MONATE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
B, LINKS, RECHTS = 1344, 64, 104
ETIKETT = 120               # Spalte rechts neben den Kerzen für die Pfeile der RS-Linien
SAND = "#D9B26F"             # GD200 / GD40W: Trennlinie des langfristigen Trends, kräftig
TUERKIS = "#2EC4B6"          # Ruhe im Volumenband
GD_KURZ = {10: "#F0883E", 20: "#FF7EB6"}   # GD10 orange, GD20 rosa (Kullamägi)
# Anchored VWAP nach Shannon (10.11.2026): Wahlschalter über dem Chart, mehrere gleichzeitig (Zange = Hoch + Tief)
AVWAP_FARBEN = {"gipfel": "#E57373", "hoch": "#FF8A65", "tief": "#4DD0E1", "hoeher": "#81C784", "zahlen": "#FFD54F",
                "ereignis": "#BA68C8", "ipo": "#B0BEC5", "ausbruch": "#64B5F6"}
# Anker aus Ereignis und Struktur, nie aus dem Kalender (13.11.2026, kern/avwap.py): Hoch, von dem der Fall ausging;
# Tief, von dem die Bewegung ausging; Ereignis = jüngere von Zahlenreaktion ab 3 % und Lücke ab 4 % mit Volumen ×2
AVWAP_KURZ = {"gipfel": "Hoch des Rückgangs", "hoch": "letztes Hoch", "tief": "Tief der Bewegung",
              "hoeher": "letztes höheres Tief", "zahlen": "Zahlentag", "ereignis": "Lücke/Volumen",
              "ipo": "Börsengang", "ausbruch": "Ausbruch (Handoff)"}
PROFIL_FARBE = "#8FA3BF"
LINIEN_SPIEL = 0.30   # Skala: Linien bis 30 % unter dem tiefsten bzw. über dem höchsten Kurs des Ausschnitts
AVWAP_START = ["hoch", "tief", "hoeher", "ipo", "ausbruch"]   # Voreinstellung: Shannons Zange und das letzte höhere Tief (Plan 20, Micky
# 16.11.2026: beide Tiefs); Gipfel und Ereignis zuschaltbar
RS_HOCH = "#FFD166"          # RS-Hoch vor Kurs
RS_TIEF = "#FF6B6B"          # RS-Tief vor Kurs (Spiegelbild, 13.11.2026)
INDEX_SCHATTEN = "#9AA3AF"   # S&P 500 im Kurschart, gestrichelt, am linken Rand auf den Kurs gelegt
KAUFZONE_FARBE = GRUEN
ZONE_FARBE = {"Base": BLAU, "Flagge": GELB, "Konsolidierung": LILA}
ZONE_ANSICHT = ["Aktuell", "Historie"]   # Knopf über dem Chart: nur das Setup jetzt oder alle Zonen

# Ausschnitte je Zeitebene: Knopf → Zahl der Balken (feste Knöpfe statt Regler)
AUSSCHNITT = {"Tag": {"3 M": 63, "6 M": 126, "1 J": 252, "2 J": 504},
              "Woche": {"1 J": 52, "3 J": 156, "5 J": 260},
              "Stunde": {"10 T": 70, "20 T": 140, "200 Std": 200}}   # Stunde: 7 Kerzen je Tag (Titel-Analyse: 70–200)
AUSSCHNITT_START = {"Tag": "6 M", "Woche": "3 J", "Stunde": "20 T"}   # 6 Monate: das Setup groß genug (09.11.2026)
EBENEN = ("Woche", "Tag", "Stunde")      # Reiter über dem Chart, Tag vorausgewählt (Micky 20./21.11.2026)
SEITE_PROFIL = 124                       # Spalten rechts für Zeit- und Volumenprofil der PbD-Formation (Titel-Analyse)
PBD_FARBE = "#EDA100"                    # PbD: Impuls, faire Zone, Ziel (wie in Vorwalds Bildern gelb)
WERT_FARBE = "#1BAF7A"                   # Wertzone und POC (Dalton)
DUENN_FARBE = "#898781"                  # dünne Zone
DOCHT_FARBE = "#2A78D6"                  # Docht (dünner Rand des Profils)
ALT_FARBE = "#E34948"                    # alte Wertzone
PIVOT_SHORT_FARBE = "#9085E9"            # Pivot short am Rand der Balance
POC_KERZE = "#E8E6DC"                    # POC je Kerze, nackter POC
ZEIT_FARBE = "#7DB4FF"                   # Zeitprofil
GD_EBENE = {"Tag": (50, 150, 200), "Woche": (10, 30, 40), "Stunde": (50, 150, 200)}   # Durchschnitte in Kerzen der Ebene
VOL_SCHNITT = {"Tag": 50, "Woche": 10, "Stunde": 50}                                  # Volumen-Schnitt in Kerzen
STUNDE_ACHSE = 5                         # Zeitachse Stunde: jeder 5. Handelstag beschriftet


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
          zonen_ansicht="Aktuell", gd_kurz=False, marken=None, avwap_wahl=None, tiefe_=None):
    """Kerzen mit GD, Zonen des VCP-Scanners, Volumen mit 50er-Schnitt, RS-Linien. ausschnitt: Knopf aus AUSSCHNITT.
    marken (titel._chartmarken, 09.11.2026): Kaufzone, Stopp 1,5 ATR, Ausbruchstag, AVWAP, Earnings, RS-Rang, Short.
    ebene „Stunde“: df, index und sektor sind Stundenkerzen. tiefe_ (tiefe.ebene, Micky 21.11.2026): Dalton-Flächen
    und -Linien, PbD auf den Kerzen mit Zeit- und Volumenprofil rechts, POC je Kerze und nackte POCs."""
    marken = marken or {}
    tag_ebene = ebene == "Tag"
    preis_ebene = ebene in ("Tag", "Stunde")    # Kaufzone, Stopp und Position sind Preise: auch im Stundenchart
    voll = _woche(_verlaengert(df)) if ebene == "Woche" else df
    n_zeigen = AUSSCHNITT[ebene].get(ausschnitt or AUSSCHNITT_START[ebene], AUSSCHNITT[ebene][AUSSCHNITT_START[ebene]])
    gd = GD_EBENE[ebene]
    linien = {k: voll["Close"].rolling(k).mean() for k in gd}
    kurz = {k: voll["Close"].rolling(k).mean() for k in GD_KURZ} if gd_kurz and ebene == "Tag" else {}
    d = voll.iloc[-n_zeigen:]
    N = len(d)
    o, h, l, c, v = (d[s_].to_numpy(float) for s_ in ("Open", "High", "Low", "Close", "Volume"))
    breite = B - LINKS - RECHTS - ETIKETT
    ENDE = LINKS + breite

    def X(i):
        return LINKS + breite * (i + 0.5) / N  # Layout

    def pos(tag):
        """Index des Balkens, der den Tag enthält (Woche: Freitag danach)."""
        return min(int(d.index.searchsorted(pd.Timestamp(tag))), N - 1)

    grenzen = [x for x in (marken.get("kz_oben"), marken.get("stopp"), (marken.get("short") or {}).get("stopp"),
                           *(w_["wert"] for w_ in (marken.get("short") or {}).get("weitere") or []),
                           (marken.get("struktur") or {}).get("stopp"),
                           ((marken.get("short") or {}).get("struktur") or {}).get("stopp"))
               + tuple(w_["wert"] for w_ in marken.get("weitere") or [])
               + tuple(x_ for x_ in ((marken.get("position") or {}).get(k_) for k_ in ("einstieg", "anfang", "stopp", "enger"))
                       if x_) if x and preis_ebene] + _tiefe_grenzen(tiefe_)
    # Linien im Ausschnitt (Durchschnitte, Anchored VWAP) gehören in die Skala (WST 16.11.2026: GD150, GD200 und AVWAP
    # Tief begannen mitten im Bild am unteren Rand, weil die Skala nur die Kerzen fasste) – höchstens LINIEN_SPIEL weiter
    import avwap
    # dieselben Anker wie die Lagekarte, aus Tageskerzen; Woche und Stunde rechnen die Linie in ihren Kerzen ab dem
    # Ankertag (Micky 21.11.2026: je Ebene dieselben Regeln)
    anker = (marken.get("anker") or {}) if ebene == "Stunde" else avwap.anker(df, marken.get("zahltag"))
    reihen = {k: avwap.reihe(voll, anker[k]) for k in (AVWAP_START if avwap_wahl is None else avwap_wahl)
              if k in anker and isinstance(anker[k], pd.Timestamp)}
    werte_l = [float(x) for r_ in list(linien.values()) + list(kurz.values()) + list((reihen or {}).values())
               for x in r_.reindex(d.index).to_numpy(float) if x == x]
    unten_l = min([l.min()] + [x for x in werte_l if x >= l.min() * (1 - LINIEN_SPIEL)])
    oben_l = max([h.max()] + [x for x in werte_l if x <= h.max() * (1 + LINIEN_SPIEL)])
    pmax, pmin = max([oben_l] + grenzen) * 1.04, min([unten_l] + grenzen) * 0.97  # Layout

    def Y(y):
        return 30 + 400 * (1 - (np.log(y) - np.log(pmin)) / (np.log(pmax) - np.log(pmin)))  # Layout

    belegt = []                                  # gesetzte Beschriftungen (x0, x1, y), damit sich keine überlappen

    def platz(x, y, text, groesse, anker="middle", nach_oben=True):
        b_ = len(text) * groesse * 0.55  # Layout
        x0 = x - b_ / 2 if anker == "middle" else (x - b_ if anker == "end" else x)
        x1 = x0 + b_
        for _ in range(12):  # Layout
            if all(x1 < a0 - 4 or x0 > a1 + 4 or abs(y - ay) >= groesse + 2 for a0, a1, ay in belegt):  # Layout
                break
            y += -(groesse + 2) if nach_oben else groesse + 2
        belegt.append((x0, x1, y))
        return y

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {B + SEITE_PROFIL} 760" width="100%" role="img" aria-label="Kurschart" '
         f'style="display:block;font-family:IBM Plex Sans,sans-serif">'
         '<style>text{paint-order:stroke;stroke:#161C24;stroke-width:4px;stroke-linejoin:round}</style>'
         + "<defs>" + "".join(f'<marker id="spitze{n_}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                              f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{f_}"/></marker>'
                              for n_, f_ in (("G", GRUEN), ("Y", GELB))) + "</defs>"]
    A = s.append
    for k in range(5):  # Layout
        yv = pmin * (pmax / pmin) ** (k / 4)  # Layout
        A(f'<line x1="{LINKS}" x2="{ENDE}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}" stroke="{RAND}"/>')
        A(f'<text x="{LINKS - 8}" y="{Y(yv) + 4:.1f}" fill="{TEXT_3}" font-size="12" text-anchor="end">{yv:.0f}</text>')  # Layout

    spaete = []                                  # Beschriftungen, die über den Kerzen liegen müssen
    if zonen:
        _zonen(zonen, zonen_ansicht, d, pos, X, Y, A, spaete, platz, ENDE, breite / N / 2)

    if tag_ebene:
        _profil(marken.get("profil"), d, pos, X, Y, A, spaete, platz, ENDE, pmin, pmax)
    if preis_ebene:
        _kaufzone(marken, d, pos, X, Y, A, spaete, platz, ENDE)
        _position(marken.get("position"), d, pos, X, Y, A, spaete, platz, ENDE)
    _tiefe_flaechen(tiefe_, d, pos, X, Y, A, spaete, platz, ENDE, pmin, pmax, tag_ebene and marken.get("profil"))

    # Kerzen
    bw = breite / N * 0.6  # Layout
    for i in range(N):
        f = GRUEN if c[i] >= o[i] else ROT
        A(f'<line x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{Y(h[i]):.1f}" y2="{Y(l[i]):.1f}" stroke="{f}"/>')
        y1, y2 = sorted([Y(o[i]), Y(c[i])])
        hohl = i == N - 1 and df.attrs.get("laufend") and preis_ebene
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{max(1, y2 - y1):.1f}" '
          + (f'fill="none" stroke="{f}" stroke-width="1.2"/>' if hohl else f'fill="{f}"/>'))

    def linie(reihe, farbe, dicke=1.6):  # Layout
        r = reihe.reindex(d.index)
        pkt = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(r.to_numpy(float))
                       if not np.isnan(x) and pmin <= x <= pmax)
        if pkt:
            A(f'<polyline points="{pkt}" fill="none" stroke="{farbe}" stroke-width="{dicke}"/>')

    for k, farbe, dicke in zip(gd[::-1], (SAND, LILA, BLAU), (2.4, 1.6, 1.6)):  # Layout
        linie(linien[k], farbe, dicke)
    for k, reihe in kurz.items():
        linie(reihe, GD_KURZ[k], 1.4)  # Layout
    if index is not None:                  # S&P 500 als Schatten (13.11.2026: der Fall HWM sofort sichtbar)
        ix_ = index["Close"].resample("W-FRI").last() if ebene == "Woche" else index["Close"]
        ix_ = ix_.reindex(d.index, method="ffill")
        if ix_.notna().sum() > 5:  # Layout
            erst = ix_.first_valid_index()
            sch = ix_ * (float(d["Close"].loc[erst]) / float(ix_.loc[erst]))
            pkt = " ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(sch.to_numpy(float))
                           if not np.isnan(x) and pmin <= x <= pmax)
            if pkt:
                A(f'<polyline points="{pkt}" fill="none" stroke="{INDEX_SCHATTEN}" stroke-width="1.3" '
                  f'stroke-dasharray="6 4" opacity="0.8"><title>S&amp;P 500, am linken Rand auf den Kurs gelegt – liegt '
                  f'der Kurs darüber, ist der Titel stärker als der Markt</title></polyline>')
                t_k, t_i = (float(d["Close"].iloc[-1]) / float(d["Close"].loc[erst]) - 1) * 100, \
                           (float(sch.iloc[-1]) / float(sch.loc[erst]) - 1) * 100
                y_ = Y(min(max(float(sch.iloc[-1]), pmin), pmax))
                text = f"S&P 500 {'+' if t_i >= 0 else '−'}{zahl(abs(t_i), 0)} % · Titel {'+' if t_k >= 0 else '−'}{zahl(abs(t_k), 0)} %"
                y2, strich = _rechts(platz, ENDE, y_, text, nach_oben=y_ > 230)  # Layout
                spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y2:.1f}" fill="{INDEX_SCHATTEN}" font-size="12">'  # Layout
                              f'{text.replace("&", "&amp;")}</text>')
    if reihen:                                                     # Anchored VWAP: Anker nach Wahl (Shannon)
        if "hoch" in reihen and "tief" in reihen and len(reihen["hoch"]) and len(reihen["tief"]):
            o_, u_ = reihen["hoch"].reindex(d.index), reihen["tief"].reindex(d.index)   # Zange schattiert
            pkt = [(X(i), Y(a_), Y(b_)) for i, (a_, b_) in enumerate(zip(o_.to_numpy(float), u_.to_numpy(float)))
                   if not (np.isnan(a_) or np.isnan(b_)) and pmin <= min(a_, b_) and max(a_, b_) <= pmax]
            if len(pkt) >= 2:
                A('<polygon points="' + " ".join(f"{x:.1f},{a_:.1f}" for x, a_, _ in pkt) + " "
                  + " ".join(f"{x:.1f},{b_:.1f}" for x, _, b_ in reversed(pkt))
                  + f'" fill="{AVWAP_FARBEN["tief"]}" fill-opacity="0.07" stroke="none"/>')
        for k, av in reihen.items():
            if not len(av):
                continue
            farbe = AVWAP_FARBEN[k]
            linie(av, farbe, 1.8)  # Layout
            if av.index[0] >= d.index[0]:                          # Ankerpunkt im Ausschnitt: kleiner Ring
                i_ = pos(anker[k])
                A(f'<circle cx="{X(i_):.1f}" cy="{Y(float(av.iloc[0])):.1f}" r="4" fill="none" stroke="{farbe}" '
                  f'stroke-width="2"/>')
            w = float(av.iloc[-1])
            if pmin <= w <= pmax:
                name_ = "Ausbruchspunkt" if k == "hoch" and anker.get("ausbruchspunkt") else AVWAP_KURZ[k]
                text = f"AVWAP {name_} {zahl(w)} $"
                y_, strich = _rechts(platz, ENDE, Y(w), text, nach_oben=Y(w) > 230)   # oben: nach unten ausweichen · Layout
                spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{farbe}" font-size="12" '  # Layout
                              f'font-weight="600">{text}</text>')
    _tiefe_linien(tiefe_, d, pos, X, Y, A, spaete, platz, ENDE, pmin, pmax)
    if ebene != "Stunde":
        _earnings(marken, d, pos, X, A, spaete, ENDE, platz)
    tm = {}
    if tag_ebene:
        _zeichen(marken, d, pos, X, Y, A, spaete, platz, ENDE, h, l)
        tm = _signale(voll, d, index, pos, X, Y, A, spaete, platz, h, l)
    for t_ in spaete:
        A(t_)

    # Volumen mit 50er-Schnitt (Woche: 10 Wochen)
    vmax = v.max() or 1
    A(f'<text x="{LINKS}" y="474" fill="{TEXT_3}" font-size="12">VOLUMEN · grün = Kauftag, rot = Abgabetag (Schluss zum '
      f'Vortag) · Linie = Schnitt {VOL_SCHNITT[ebene]} {_einheit(ebene)}</text>')
    vorschluss = voll["Close"].shift().reindex(d.index).to_numpy(float)
    for i in range(N):
        hv = 90 * v[i] / vmax  # Layout
        auf_ = c[i] >= (vorschluss[i] if not np.isnan(vorschluss[i]) else o[i])
        A(f'<rect x="{X(i) - bw / 2:.1f}" y="{570 - hv:.1f}" width="{bw:.1f}" height="{hv:.1f}" '  # Layout
          f'fill="{GRUEN if auf_ else ROT}" fill-opacity="0.75"/>')
    v50 = voll["Volume"].rolling(VOL_SCHNITT[ebene]).mean().reindex(d.index).to_numpy(float)
    pkt = " ".join(f"{X(i):.1f},{570 - 90 * x / vmax:.1f}" for i, x in enumerate(v50) if not np.isnan(x))  # Layout
    A(f'<polyline points="{pkt}" fill="none" stroke="{TEXT}" stroke-width="1.2"/>')
    for t_ in tm.get("abgabe", []):            # Abgabetage des Titels (Distribution): roter Punkt über dem Balken
        if t_ >= d.index[0]:
            i = pos(t_)
            A(f'<circle cx="{X(i):.1f}" cy="{570 - 90 * v[i] / vmax - 5:.1f}" r="2.6" fill="{ROT}"><title>{t_:%d.%m.%Y}: '  # Layout
              f'Abgabetag – Schluss tiefer, Volumen über dem Schnitt, Schluss im unteren Drittel</title></circle>')
    for t_ in tm.get("churning", []):          # verdeckte Abgabe: im Plus, aber Schluss unten bei viel Volumen
        if t_ >= d.index[0]:
            i = pos(t_)
            A(f'<circle cx="{X(i):.1f}" cy="{570 - 90 * v[i] / vmax - 5:.1f}" r="2.6" fill="none" stroke="{ROT}" '  # Layout
              f'stroke-width="1.3"><title>{t_:%d.%m.%Y}: verdeckte Abgabe (Churning) – im Plus, Volumen über dem '
              f'Schnitt, Schluss im unteren Drittel</title></circle>')
    # Volumenband je Balken, am Schnitt gemessen: Ruhe türkis (kräftig bis 50 %, blass bis 75 %), viel Volumen in
    # Richtung des Tages (Schluss zum Vortag) grün bzw. rot (blass über dem Schnitt, kräftig ab 1,5-fach), sonst grau
    cv = voll["Close"].shift().reindex(d.index).to_numpy(float)
    for i in range(N):
        if np.isnan(v50[i]) or not v50[i]:
            continue
        q = v[i] / v50[i]
        auf = c[i] >= (cv[i] if not np.isnan(cv[i]) else o[i])
        if q <= VOL_RUHE:
            farbe, deck, wort = TUERKIS, 0.95, "Ruhe"  # Layout
        elif q <= VOL_EHER_RUHIG:
            farbe, deck, wort = TUERKIS, 0.4, "eher ruhig"  # Layout
        elif q <= 1.0:
            farbe, deck, wort = TEXT_3, 0.25, "normal"  # Layout
        else:
            farbe, deck = (GRUEN if auf else ROT), (0.95 if q >= VOL_HOCH else 0.4)  # Layout
            wort = ("deutlich erhöht" if q >= VOL_HOCH else "über dem Schnitt") + (" ↑" if auf else " ↓")
        A(f'<rect x="{X(i) - breite / N / 2:.1f}" y="577" width="{breite / N + 0.3:.1f}" height="9" fill="{farbe}" '  # Layout
          f'fill-opacity="{deck}"><title>{d.index[i]:%d.%m.%Y}: Volumen {zahl(q * 100, 0)} % vom Schnitt – {wort}'
          f'</title></rect>')
    A(f'<text x="{ENDE + 8:.1f}" y="585" fill="{TEXT_3}" font-size="11">Volumen</text>')  # Layout

    # RS-Linien gegen den S&P 500 und gestrichelt gegen den Sektor-ETF, beide links bei 100
    if index is not None:
        def relativ(bezug):
            bx = bezug.resample("W-FRI").last() if ebene == "Woche" else bezug
            r = (voll["Close"] / bx.reindex(voll.index, method="ffill")).reindex(d.index).to_numpy(float)
            gueltig = np.flatnonzero(~np.isnan(r))
            return r / r[gueltig[0]] * 100 if len(gueltig) > 5 else None

        rs = relativ(index["Close"])
        rk = relativ(sektor) if sektor is not None else None
        if rs is not None:
            alle = np.concatenate([rs[~np.isnan(rs)], rk[~np.isnan(rk)] if rk is not None else [], [100.0]])
            lo, hi = alle.min(), alle.max()
            rand = (hi - lo) * 0.06 or 1  # Layout
            lo, hi = lo - rand, hi + rand
            YR = lambda y: 618 + 102 * (1 - (y - lo) / (hi - lo))          # noqa: E731 · Layout
            kurz_ = RS_PFEIL_WOCHEN if ebene == "Woche" else RS_PFEIL_TAGE

            def pfeil(r, farbe, name):
                """Dynamik der letzten 10 Tage (3 Wochen) am Linienende: Pfeil und beide Werte (vorher → heute)."""
                g = r[~np.isnan(r)]
                if len(g) <= kurz_:
                    return
                alt, neu = g[-1 - kurz_], g[-1]
                pr = (neu / alt - 1) * 100
                p_ = ("↑" if pr >= RS_PFEIL_STARK else "↗" if pr >= RS_PFEIL else "↓" if pr <= -RS_PFEIL_STARK
                      else "↘" if pr <= -RS_PFEIL else "→")
                A(f'<g><title>{name}: {zahl(alt, 0)} → {zahl(neu, 0)} in {kurz_} {_einheit(ebene)} '
                  f'({"+" if pr >= 0 else "−"}{zahl(abs(pr), 1)} %); 100 = so stark wie am linken Rand</title>'
                  f'<text x="{ENDE + 8:.1f}" y="{platz(ENDE + 8, YR(neu) + 5, "↗ 000 → 000", 12, "start"):.1f}" '  # Layout
                  f'fill="{farbe}" font-size="12"><tspan font-size="15" font-weight="700">{p_}</tspan> '
                  f'{zahl(alt, 0)} → {zahl(neu, 0)}</text></g>')

            rsm = marken.get("rs") or {}
            rang_ = (f' · <tspan fill="{TEXT}" font-weight="600">RS-Rang {rsm["rang"]} · Tempo {rsm["tempo"]:+d} in 4 Wochen'
                     f'</tspan>' if rsm.get("rang") is not None and rsm.get("tempo") is not None else "")
            A(f'<text x="{LINKS}" y="608" fill="{TEXT_3}" font-size="12">RELATIVE STÄRKE SEIT {d.index[0]:%m/%Y}{rang_} · '
              f'<tspan fill="{BLAU}">— gegen S&amp;P 500</tspan>'
              + (f'  <tspan fill="{LILA}">- - gegen Sektor {sektor_name}</tspan>' if rk is not None else "")
              + f'  · Pfeil = letzte {kurz_} {_einheit(ebene)}</text>')
            A(f'<line x1="{LINKS}" x2="{ENDE}" y1="{YR(100):.1f}" y2="{YR(100):.1f}" stroke="{TEXT_3}" '
              f'stroke-width="1" stroke-dasharray="2 4"/>'
              f'<text x="{LINKS - 6}" y="{YR(100) + 4:.1f}" fill="{TEXT_3}" font-size="11" text-anchor="end">100</text>')  # Layout
            if rk is not None:
                A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(rk) if not np.isnan(x))
                  + f'" fill="none" stroke="{LILA}" stroke-width="1.5" stroke-dasharray="5 4"/>')
            A('<polyline points="' + " ".join(f"{X(i):.1f},{YR(x):.1f}" for i, x in enumerate(rs) if not np.isnan(x))
              + f'" fill="none" stroke="{BLAU}" stroke-width="1.8"/>')
            if tag_ebene:                       # RS-Linie am Jahreshoch, der Kurs noch nicht (Rückenwind: 99 % / 97 %)
                rv = voll["Close"] / index["Close"].reindex(voll.index, method="ffill")
                import rueckenwind
                hoch = rv >= RS_MASS * rv.rolling(JAHR_TAGE, min_periods=JAHR_TAGE).max()
                kurs_tief = voll["Close"] < rueckenwind.KURS_NAH * voll["Close"].rolling(JAHR_TAGE, min_periods=JAHR_TAGE).max()
                fl = (hoch & kurs_tief).reindex(d.index).fillna(False).to_numpy(bool)
                for i in np.flatnonzero(fl):
                    if not np.isnan(rs[i]):
                        A(f'<circle cx="{X(i):.1f}" cy="{YR(rs[i]):.1f}" r="3.2" fill="{RS_HOCH}"><title>{d.index[i]:%d.%m.%Y}: '
                          f'RS-Linie am Jahreshoch, Kurs noch nicht – das frühe Zeichen</title></circle>')
                if fl.any():
                    i = int(np.flatnonzero(fl)[-1])
                    t_ = "● RS-Hoch vor Kurs"
                    A(f'<text x="{X(i):.1f}" y="{YR(rs[i]) - 9:.1f}" fill="{RS_HOCH}" font-size="12" font-weight="600" '  # Layout
                      f'text-anchor="end">{t_}</text>')
                # Spiegelbild (13.11.2026): RS-Linie am Jahrestief, der Kurs noch nicht – Schwäche kündigt sich an
                tief = rv <= rv.rolling(JAHR_TAGE, min_periods=JAHR_TAGE).min() / RS_MASS
                kurs_hoch = voll["Close"] > (2 - rueckenwind.KURS_NAH) * voll["Close"].rolling(JAHR_TAGE,
                                                                                            min_periods=JAHR_TAGE).min()
                ft = (tief & kurs_hoch).reindex(d.index).fillna(False).to_numpy(bool)
                for i in np.flatnonzero(ft):
                    if not np.isnan(rs[i]):
                        A(f'<circle cx="{X(i):.1f}" cy="{YR(rs[i]):.1f}" r="3.2" fill="{RS_TIEF}"><title>{d.index[i]:%d.%m.%Y}: '
                          f'RS-Linie am Jahrestief, Kurs noch nicht – das frühe Zeichen der Schwäche</title></circle>')
                if ft.any():
                    i = int(np.flatnonzero(ft)[-1])
                    A(f'<text x="{X(i):.1f}" y="{YR(rs[i]) + 16:.1f}" fill="{RS_TIEF}" font-size="12" font-weight="600" '  # Layout
                      f'text-anchor="end">● RS-Tief vor Kurs</text>')
            pfeil(rs, BLAU, "gegen S&amp;P 500")
            if rk is not None:
                pfeil(rk, LILA, f"gegen Sektor {sektor_name}")

    # Zeitachse: Monatsanfänge (Stunde: jeder 5. Handelstag)
    letzter = None
    if ebene == "Stunde":
        tage_ = sorted(set(d.index.normalize()))
        for k_, tag in enumerate(tage_):
            if k_ % STUNDE_ACHSE == 0:
                A(f'<text x="{X(int(d.index.searchsorted(tag))):.1f}" y="748" fill="{TEXT_3}" font-size="12">{tag:%d.%m.}</text>')
        A("</svg>")
        return "".join(s)
    for i, tag in enumerate(d.index):
        schluessel = (tag.year, tag.month) if ebene == "Tag" else (tag.year, (tag.month - 1) // 3)  # Layout
        if schluessel != letzter:
            if letzter is not None:
                text = MONATE[tag.month - 1] + (f" {tag.year % 100:02d}" if tag.month <= 3 or ebene == "Woche" else "")  # Layout
                A(f'<text x="{X(i):.1f}" y="748" fill="{TEXT_3}" font-size="12">{text}</text>')
            letzter = schluessel
    A("</svg>")
    return "".join(s)


def _zonen(ka, ansicht, d, pos, X, Y, A, spaete, platz, ENDE, halb):
    """VCP-Scanner Baustein 1 im Chart: Zone (Base blau, Flagge gelb, Konsolidierung lila), Vorgeschichte als gelber
    Pfeil, Fahnenstange als grüner Pfeil, grobes ZigZag grau. Aktuell = nur das Setup jetzt (ZigZag ab der Vorgeschichte),
    Historie = dazu alle abgeschlossenen Zonen im Ausschnitt mit ↑ am Ausbruch, davor die Basennummer (IBD, basen.py)."""
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
        ab = max(erster, v_.get("von_t") or jetzt.get("start_t") or d.index[max(0, len(d) - 60)])  # Layout
    zz = [(X(pos(t)), Y(p)) for t, p in ka.get("zigzag") or [] if t >= ab]
    if len(zz) >= 2:
        A(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in zz)}" fill="none" stroke="{TEXT_3}" '
          f'stroke-width="1.2" stroke-opacity="0.8"/>')

    if ansicht == "Historie":
        stangen_ende = []
        for b in ka.get("verlauf") or []:
            if b.get("cheat"):                   # Cheat in einer größeren Zone: dünn gestrichelt, ohne Nummer (Gefechtsordnung)
                x0 = rahmen(b, X(pos(b["ende_t"])), 0.8, 0.0, "3 3")  # Layout
                if x0 is not None:
                    spaete.append(f'<text x="{X(pos(b["ende_t"])):.1f}" y="{Y(b["oben"]) - 4:.1f}" fill="{TEXT_2}" '  # Layout
                                  f'font-size="12" text-anchor="middle">Cheat</text>')
                continue
            x0 = rahmen(b, X(pos(b["ende_t"])), 1.2, 0.07)  # Layout
            if x0 is None:
                continue
            spaete.append(f'<text x="{X(pos(b["ende_t"])):.1f}" y="{Y(b["oben"]) - 4:.1f}" fill="{GRUEN}" font-size="15" '  # Layout
                          f'font-weight="700" text-anchor="middle">{str(b["nummer"]) + ". " if b.get("nummer") else ""}↑</text>')
            st_ = b.get("stange") or {}
            if b["name"] == "Flagge" and st_ and not any(st_["von_t"] < e for e in stangen_ende):
                pfeil(st_["von_t"], st_["von"], b["start_t"], b["oben"], GRUEN, "G", 1.6)  # Layout
            if b["name"] == "Flagge":
                stangen_ende.append(b["ende_t"])

    if jetzt.get("zone") or jetzt.get("offen"):
        offen = not jetzt.get("zone")
        x0 = rahmen(jetzt, ENDE, 2 if not offen else 1.4, 0.09 if not offen else 0, "6 4" if offen else "")  # Layout
        if x0 is not None:
            if offen:
                text_ = f'Zone offen · Rücksetzer {zahl(jetzt["tiefe"], 1)} % · noch keine Erholung'
            else:
                text_ = (f'{str(jetzt["nummer"]) + ". " if jetzt.get("nummer") else ""}'
                         f'{jetzt["name"]} · {zahl(jetzt["wochen"], 1)} W · {zahl(jetzt["tiefe"], 0)} %'
                         + (" · zu kurz" if jetzt["laenge"] == "zu kurz" else ""))
                inn_ = jetzt.get("innen")
                if inn_ and inn_["start_t"] >= erster:      # Flagge in der Zone: ein Etikett statt zwei übereinander
                    text_ += f' · darin Flagge {zahl(inn_["wochen"], 1)} W · {zahl(inn_["tiefe"], 0)} %'
            fa = ZONE_FARBE.get(jetzt.get("name"), TEXT_2)
            rechts = x0 + len(text_) * 6.6 > ENDE            # schmale Zone am rechten Rand: Text endet am Rand · Layout
            xt, anker = (ENDE, "end") if rechts else (x0 + 4, "start")  # Layout
            oben_ = max([jetzt["oben"]] + list(d["High"][d.index >= jetzt["start_t"]]))   # über allen Kerzen der Zone
            spaete.append(f'<text x="{xt:.1f}" y="{platz(xt, Y(oben_) - 8, text_, 12, anker):.1f}" '  # Layout
                          f'fill="{fa}" font-size="12" font-weight="600" text-anchor="{anker}">{text_}</text>')
            v_ = jetzt.get("vorgeschichte") or {}
            st_ = jetzt.get("stange") or {}
            if jetzt.get("name") == "Flagge" and st_:
                pfeil(st_["von_t"], st_["von"], jetzt["start_t"], jetzt["oben"], GRUEN, "G", 2.2)  # Layout
            elif v_.get("von_t") is not None:
                pfeil(v_["von_t"], v_["von"], v_["bis_t"], v_["bis"], GELB, "Y", 2)
        _enge(ka.get("enge") or {}, x0, d, pos, X, Y, A, spaete, platz, ENDE, erster)
        innen = jetzt.get("innen")
        if innen and innen["start_t"] >= erster:
            rahmen(innen, ENDE, 1.8, 0.0)  # Layout
            st_ = innen.get("stange") or {}
            if st_:
                pfeil(st_["von_t"], st_["von"], innen["start_t"], innen["oben"], GRUEN, "G", 2)


AMPEL_FARBE = {"grün": GRUEN, "gelb": GELB, "rot": ROT, "grau": TEXT_3}


def _enge(e, x0, d, pos, X, Y, A, spaete, platz, ENDE, erster):
    """Baustein 2 im Chart: jede Kontraktion als feine Linie Hoch → Tief mit ihrer Tiefe, die Enge (letzte
    Kontraktion) als eigener Rahmen bis heute, Pivot als gestrichelte Linie mit Preis, Ampel der Enge am Rahmen."""
    kontr = e.get("kontraktionen") or []
    if not kontr or x0 is None:
        return
    for k in kontr:
        if k["hoch_t"] < erster:
            continue
        xa, xb = X(pos(k["hoch_t"])), X(pos(k["tief_t"]))
        A(f'<line x1="{xa:.1f}" y1="{Y(k["hoch"]):.1f}" x2="{xb:.1f}" y2="{Y(k["tief"]):.1f}" stroke="{TEXT_2}" '
          f'stroke-width="1.3" stroke-dasharray="4 3"/>')
        t_ = f'−{zahl(k["tiefe"], 0)} %'
        spaete.append(f'<text x="{xb:.1f}" y="{platz(xb, Y(k["tief"]) + 16, t_, 12, nach_oben=False):.1f}" fill="{TEXT}" '  # Layout
                      f'font-size="12" font-weight="600" text-anchor="middle">{t_}</text>')
    letzte = kontr[-1]
    farbe = AMPEL_FARBE.get(e.get("ampel"), TEXT_3)
    if letzte["hoch_t"] >= erster:
        xe = X(pos(letzte["hoch_t"])) - 3  # Layout
        A(f'<rect x="{xe:.1f}" y="{Y(letzte["hoch"]):.1f}" width="{ENDE - xe:.1f}" '
          f'height="{Y(letzte["tief"]) - Y(letzte["hoch"]):.1f}" fill="{farbe}" fill-opacity="0.10" stroke="{farbe}" '
          f'stroke-width="1.6"><title>Enge: {zahl(letzte["tiefe"], 1)} % · Pivot {zahl(e["pivot"])} $</title></rect>')
        A(f'<line x1="{xe:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(e["pivot"]):.1f}" y2="{Y(e["pivot"]):.1f}" stroke="{TEXT}" '  # Layout
          f'stroke-width="1.4" stroke-dasharray="6 4"/>')
        wort = e["lage"] if "Cheat" in str(e.get("lage")) else "Pivot der Base"   # eine Cheat-Regel (vcp_zone.drittel)
        t_ = f'{wort} {zahl(e["pivot"])} $'       # 12.11.2026: nicht mit dem Einstieg verwechseln; Drittel 14.11.2026
        y_, strich = _rechts(platz, ENDE, Y(e["pivot"]), t_)
        spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{TEXT}" font-size="12" font-weight="600">{t_}</text>')  # Layout
    t_ = f'● Enge {e.get("ampel", "")} · {e.get("text", "")}'
    spaete.append(f'<text x="{ENDE:.1f}" y="{platz(ENDE, 20, t_, 12, "end", False):.1f}" fill="{farbe}" font-size="12" '  # Layout
                  f'font-weight="600" text-anchor="end">{t_}</text>')

def _rechts(platz, ENDE, y_linie, text, nach_oben=True):
    """Etikett in der Spalte rechts neben dem Chart: y der Schrift und – wenn es wegen eines anderen Etiketts verschoben
    werden musste – ein feiner Strich zurück zur Höhe seiner Linie, damit klar bleibt, wozu es gehört."""
    y = platz(ENDE + 8, y_linie + 4, text, 12, "start", nach_oben)  # Layout
    strich = (f'<line x1="{ENDE + 1:.1f}" y1="{y_linie:.1f}" x2="{ENDE + 7:.1f}" y2="{y - 4:.1f}" stroke="{TEXT_3}" '  # Layout
              f'stroke-width="0.8"/>' if abs(y - 4 - y_linie) > 3 else "")  # Layout
    return y, strich


def _x0(m, d, pos, X):
    """Linker Rand der Linien am Einstieg: erster Ausbruchstag oder Beginn der Zone, sonst die letzten 30 Balken."""
    ab = m.get("ab")
    if ab is not None and pd.Timestamp(ab) >= d.index[0]:
        return X(pos(ab))
    return X(max(0, len(d) - 30))  # Layout


def _position(p, d, pos, X, Y, A, spaete, platz, ENDE):
    """Chart der Position (Depot-Seite, 16.11.2026): Einstieg ab dem Kauftag, Anfangsstopp gestrichelt, der Stopp, der
    jetzt gilt (10er/20er, reiten.nachgezogen), durchgezogen und – wenn ein Ende-Zeichen ihn enger zieht – die enge Linie."""
    if not p or not p.get("einstieg"):
        return
    x0 = X(pos(p["tag"])) if p.get("tag") is not None and pd.Timestamp(p["tag"]) >= d.index[0] else X(0)
    lang = p.get("seite", "long") == "long"
    for wert, farbe, strich, dicke, vor, fett in (
            (p["einstieg"], BLAU, "6 4", 1.6, "Einstieg", False),  # Layout
            (p.get("anfang"), TEXT_3, "4 4", 1.2, "Anfangsstopp", False),  # Layout
            (p.get("stopp"), ROT, "", 2.2, "Stopp jetzt", True),  # Layout
            (p.get("enger"), GELB, "", 2.0, f'enger: {p.get("enger_art", "")}', True)):
        if not wert or (vor == "Anfangsstopp" and wert == p.get("stopp")):
            continue
        text = f'{vor} {zahl(wert)}' + (f' · {p.get("linie") or "Anfang"}' if vor == "Stopp jetzt" else "")
        A(f'<line x1="{x0:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(wert):.1f}" y2="{Y(wert):.1f}" stroke="{farbe}" '  # Layout
          f'stroke-width="{dicke}"' + (f' stroke-dasharray="{strich}"' if strich else "") + f'><title>{text}</title></line>')
        y_, strich_ = _rechts(platz, ENDE, Y(wert), text, nach_oben=(wert >= p["einstieg"]) == lang)
        spaete.append(f'{strich_}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{farbe}" font-size="12"'  # Layout
                      + (' font-weight="600"' if fett else "") + f'>{text}</text>')
    if p.get("tag") is not None and pd.Timestamp(p["tag"]) >= d.index[0]:
        A(f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="30" y2="430" stroke="{BLAU}" stroke-opacity="0.5" stroke-dasharray="2 4">'
          f'<title>Kauf am {pd.Timestamp(p["tag"]):%d.%m.%Y}</title></line>')


def _kaufzone(m, d, pos, X, Y, A, spaete, platz, ENDE):
    """Kaufzone (Pivot bis +5 %) als grünes Band und eine Stopp-Linie 1,5 ATR unter dem Einstieg (Micky, 09.11.2026:
    eine Linie für alle Systeme); Short: Stopp 1,5 ATR über der Unterkante der Flagge."""
    e, st = m.get("einstieg"), m.get("stopp")
    if e:
        x0 = _x0(m, d, pos, X)
        if m.get("kz_oben"):
            A(f'<rect x="{x0:.1f}" y="{Y(m["kz_oben"]):.1f}" width="{ENDE - x0:.1f}" height="{Y(e) - Y(m["kz_oben"]):.1f}" '
              f'fill="{KAUFZONE_FARBE}" fill-opacity="0.14"><title>Kaufzone: Pivot {zahl(e)} $ bis +5 % = '
              f'{zahl(m["kz_oben"])} $ ({m.get("quelle", "")})</title></rect>')
            t_ = f'Kaufzone bis {zahl(m["kz_oben"])} $'
            y_, strich = _rechts(platz, ENDE, Y(m["kz_oben"]), t_)
            spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{KAUFZONE_FARBE}" font-size="12" '  # Layout
                          f'font-weight="600">{t_}</text>')
            t_ = f'Einstieg {zahl(e)} $'                  # Einstieg des Setups beschriftet (12.11.2026)
            y_, strich = _rechts(platz, ENDE, Y(e), t_, nach_oben=False)
            spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{KAUFZONE_FARBE}" font-size="12" '  # Layout
                          f'font-weight="600"><title>{m.get("quelle", "")}</title>{t_}</text>')
        if st:                                     # 1,5 ATR gestrichelt (Schritt 3: neben dem Struktur-Stopp)
            A(f'<line x1="{x0:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(st):.1f}" y2="{Y(st):.1f}" stroke="{ROT}" stroke-width="1.6" '  # Layout
              f'stroke-dasharray="7 4"><title>Stopp 1,5 ATR unter dem Einstieg {zahl(e)} $ (ATR {zahl(m.get("atr"))} $)</title></line>')
            t_ = f'Stopp 1,5 ATR {zahl(st)} $ · −{zahl((1 - st / e) * 100, 1)} %'
            y_, strich = _rechts(platz, ENDE, Y(st), t_, False)
            spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{ROT}" font-size="12">{t_}</text>')  # Layout
        sx = m.get("struktur") or {}
        if sx.get("stopp"):                        # Struktur-Stopp durchgezogen
            A(f'<line x1="{x0:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(sx["stopp"]):.1f}" y2="{Y(sx["stopp"]):.1f}" stroke="{ROT}" '  # Layout
              f'stroke-width="2"><title>Stopp Struktur: {sx["regel"]}'
              + (f' – weiter als {sx["grenze"]}, die Meister nehmen den Trade so nicht' if sx.get("zu_weit") else "")
              + '</title></line>')
            t_ = (f'Stopp Struktur {zahl(sx["stopp"])} $ · −{zahl((1 - sx["stopp"] / e) * 100, 1)} %'
                  + (" · zu weit" if sx.get("zu_weit") else ""))
            y_, strich = _rechts(platz, ENDE, Y(sx["stopp"]), t_, False)
            spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{ROT}" font-size="12" font-weight="600">{t_}</text>')  # Layout
    for w_ in m.get("weitere") or []:            # zweiter Einstieg (Cheat bzw. Ausbruch), gestrichelt, ohne eigene Kaufzone
        x0 = _x0(m, d, pos, X)
        A(f'<line x1="{x0:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(w_["wert"]):.1f}" y2="{Y(w_["wert"]):.1f}" stroke="{KAUFZONE_FARBE}" '  # Layout
          f'stroke-width="1.4" stroke-dasharray="6 4"><title>{w_["quelle"]} {zahl(w_["wert"])} $'
          + (f' · Stopp 1,5 ATR {zahl(w_["stopp"])} $' if w_.get("stopp") else "") + '</title></line>')
        t_ = f'{w_["quelle"].split(":")[0].replace("Ausbruch über die Oberkante", "Ausbruch")} {zahl(w_["wert"])} $'
        y_, strich = _rechts(platz, ENDE, Y(w_["wert"]), t_)
        spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{KAUFZONE_FARBE}" font-size="12">{t_}</text>')  # Layout
    sh = m.get("short") or {}
    if sh.get("stopp") and pd.Timestamp(sh["tag"]) >= d.index[0]:
        x0 = X(pos(sh["tag"]))
        A(f'<line x1="{x0:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(sh["stopp"]):.1f}" y2="{Y(sh["stopp"]):.1f}" stroke="{ROT}" '  # Layout
          f'stroke-width="1.8" stroke-dasharray="7 4"><title>Short-Stopp 1,5 ATR über dem Einstieg {zahl(sh["einstieg"])} $'
          f'</title></line>')
        t_ = f'Einstieg Short {zahl(sh["einstieg"])} $'      # 12.11.2026: Einstieg des Short-Setups beschriftet
        y_, strich = _rechts(platz, ENDE, Y(sh["einstieg"]), t_, nach_oben=False)
        spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{ROT}" font-size="12" font-weight="600">{t_}</text>')  # Layout
        t_ = f'Stopp Short 1,5 ATR {zahl(sh["stopp"])} $ · +{zahl((sh["stopp"] / sh["einstieg"] - 1) * 100, 1)} %'
        y_, strich = _rechts(platz, ENDE, Y(sh["stopp"]), t_)
        spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{ROT}" font-size="12">{t_}</text>')  # Layout
        for w_ in sh.get("weitere") or []:         # zweiter Short-Einstieg (früher Short bzw. Bruch), gestrichelt
            A(f'<line x1="{x0:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(w_["wert"]):.1f}" y2="{Y(w_["wert"]):.1f}" stroke="{ROT}" '  # Layout
              f'stroke-width="1.4" stroke-dasharray="6 4"><title>{w_["quelle"]} {zahl(w_["wert"])} $</title></line>')
            t_ = f'{w_["quelle"].split(":")[0]} {zahl(w_["wert"])} $'
            y_, strich = _rechts(platz, ENDE, Y(w_["wert"]), t_, nach_oben=False)
            spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{ROT}" font-size="12">{t_}</text>')  # Layout
        sx = sh.get("struktur") or {}
        if sx.get("stopp"):                        # Struktur-Stopp (Schritt 3) durchgezogen
            A(f'<line x1="{x0:.1f}" x2="{ENDE + 4:.1f}" y1="{Y(sx["stopp"]):.1f}" y2="{Y(sx["stopp"]):.1f}" stroke="{ROT}" '  # Layout
              f'stroke-width="2"><title>Short-Stopp Struktur: {sx["regel"]}</title></line>')
            t_ = f'Stopp Short Struktur {zahl(sx["stopp"])} $ · +{zahl((sx["stopp"] / sh["einstieg"] - 1) * 100, 1)} %'
            y_, strich = _rechts(platz, ENDE, Y(sx["stopp"]), t_)
            spaete.append(f'{strich}<text x="{ENDE + 8:.1f}" y="{y_:.1f}" fill="{ROT}" font-size="12" font-weight="600">{t_}</text>')  # Layout


def _earnings(m, d, pos, X, A, spaete, ENDE, platz):
    """Frühere Zahlen als senkrechte Linie mit der Kursreaktion, der nächste Termin rechts in derselben Zeile unter dem Kurs."""
    for tag, pr in m.get("earnings") or []:
        tag = pd.Timestamp(tag)
        if tag < d.index[0]:
            continue
        x = X(pos(tag))
        A(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="34" y2="430" stroke="{GELB}" stroke-width="1" stroke-opacity="0.55" '
          f'stroke-dasharray="3 4"/>')
        vz = "±" if round(abs(pr), 1) == 0 else "+" if pr >= 0 else "−"
        t_ = f'E {vz}{zahl(abs(pr), 1)} %'
        spaete.append(f'<text x="{x:.1f}" y="{platz(x, 448, t_, 12, nach_oben=False):.1f}" fill="{GRUEN if pr >= 0 else ROT}" font-size="12" font-weight="600" '  # Layout
                      f'text-anchor="middle"><title>Zahlen {tag:%d.%m.%Y}: Kurs am Reaktionstag {vz}'
                      f'{zahl(abs(pr), 1)} %</title>{t_}</text>')
    termin = m.get("termin")
    if termin is not None:
        termin = pd.Timestamp(termin)
        tage = -1 if pd.isna(termin) else (termin.normalize() - pd.Timestamp.now().normalize()).days
        if tage >= 0:
            import gestaltung
            amp = gestaltung.termin_ampel(tage)
            nah = amp in ("rot", "gelb")
            t_ = f'{"🔴 " if nah else ""}E in {tage} T · {termin:%d.%m.}'
            spaete.append(f'<text x="{ENDE + 8:.1f}" y="{platz(ENDE + 8, 448, t_, 12, "start", False):.1f}" '  # Layout
                          f'fill="{ROT if amp == "rot" else GELB if nah else TEXT_3}" font-size="12" font-weight="600">{t_}</text>')


def _zeichen(m, d, pos, X, Y, A, spaete, platz, ENDE, h, l):
    """Ausbruchstag mit dem Vielfachen des Volumens, Fehlausbruch, Ermüdungstag (Short)."""
    br = m.get("ausbruch") or {}
    if br.get("tag") is not None and pd.Timestamp(br["tag"]) >= d.index[0]:
        i = pos(br["tag"])
        v_ = br.get("volumen")
        t_ = "↑ Ausbruch" + (f' {zahl(v_, 1)}×' if v_ else "")
        spaete.append(f'<text x="{X(i):.1f}" y="{platz(X(i), Y(min([l[i:].min()] + ([m["stopp"]] if m.get("stopp") else []))) + 18, t_, 12, nach_oben=False):.1f}" '  # Layout
                      f'fill="{GRUEN if v_ and v_ > 1 else GELB}" font-size="12" font-weight="700" text-anchor="middle">'
                      f'<title>Ausbruch {pd.Timestamp(br["tag"]):%d.%m.%Y} über den Pivot · Volumen '
                      f'{zahl(v_, 1) + "-fach vom Schnitt" if v_ else "unbekannt"}</title>{t_}</text>')
    if br.get("fehl_tag") is not None and pd.Timestamp(br["fehl_tag"]) >= d.index[0]:
        i = pos(br["fehl_tag"])
        t_ = "✕ Fehlausbruch"
        spaete.append(f'<text x="{X(i):.1f}" y="{platz(X(i), Y(l[i]) + 18, t_, 12, nach_oben=False):.1f}" fill="{ROT}" '  # Layout
                      f'font-size="12" font-weight="700" text-anchor="middle">{t_}</text>')
    sh = m.get("short") or {}
    if sh.get("tag") is not None and not sh.get("vor_bruch") and pd.Timestamp(sh["tag"]) >= d.index[0]:
        i = pos(sh["tag"])
        v_ = sh.get("volumen")
        t_ = "↓ " + sh.get("art", "Ermüdung") + (f' {zahl(v_, 1)}×' if v_ else "")
        spaete.append(f'<text x="{X(i):.1f}" y="{platz(X(i), Y(h[i]) - 10, t_, 12):.1f}" fill="{ROT}" font-size="12" '  # Layout
                      f'font-weight="700" text-anchor="middle">{t_}</text>')


def _profil(vv, d, pos, X, Y, A, spaete, platz, ENDE, pmin, pmax, breite=150):  # Layout
    """Verankertes Volumenprofil (13.11.2026, Dalton 14.11.2026): grau ab dem Beginn der laufenden Balance als durchscheinende Balken von rechts mit dem
    akzeptierten Wert, die Mauer (Knoten seit dem Hoch über dem Kurs) rot und die Stütze (Knoten seit dem Tief unter dem
    Kurs) grün als schmale Bänder am rechten Rand. Der Chart behält seine Breite."""
    if not vv:
        return
    g = vv.get("grau") or {}
    p = g.get("profil")
    if p:
        # die Balance selbst (Dalton): Zeitraum ab ihrem Beginn mit dem Wertbereich (70 %) als Feld – Micky 14.11.2026
        # (LUV: das Profil war als blasser Streifen am rechten Rand kaum zu sehen)
        try:
            x0 = X(pos(pd.Timestamp(g["ab"]))) if pd.Timestamp(g["ab"]) >= d.index[0] else X(0)
        except Exception:  # noqa: BLE001
            x0 = ENDE - breite
        wu, wo = max(p["wert_unten"], pmin), min(p["wert_oben"], pmax)
        if wo > wu:
            A(f'<rect x="{x0:.1f}" y="{Y(wo):.1f}" width="{max(1, ENDE - x0):.1f}" height="{Y(wu) - Y(wo):.1f}" '
              f'fill="{PROFIL_FARBE}" fill-opacity="0.10" stroke="{PROFIL_FARBE}" stroke-opacity="0.5" '
              f'stroke-dasharray="4 3"/>')
            A(f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="{Y(pmax):.1f}" y2="{Y(pmin):.1f}" stroke="{PROFIL_FARBE}" '
              f'stroke-opacity="0.5" stroke-dasharray="2 4"/>')
        vmax = float(max(p["volumen"])) or 1.0
        for k in range(len(p["volumen"])):
            lo_, hi_ = float(p["grenzen"][k]), float(p["grenzen"][k + 1])
            if hi_ < pmin or lo_ > pmax:
                continue
            w = breite * float(p["volumen"][k]) / vmax
            y1, y2 = Y(min(hi_, pmax)), Y(max(lo_, pmin))
            A(f'<rect x="{ENDE - w:.1f}" y="{y1:.1f}" width="{w:.1f}" height="{max(1, y2 - y1 - 1):.1f}" '
              f'fill="{PROFIL_FARBE}" fill-opacity="0.45"/>')
        if pmin <= p["poc"] <= pmax:
            y_ = Y(p["poc"])
            A(f'<line x1="{ENDE - breite}" x2="{ENDE}" y1="{y_:.1f}" y2="{y_:.1f}" stroke="{PROFIL_FARBE}" stroke-width="1.5"/>')
            t_ = f"akzeptierter Wert {zahl(p['poc'])} $"
            spaete.append(f'<text x="{ENDE - breite - 4}" y="{platz(ENDE - breite - 4, y_ - 4, t_, 11, "end"):.1f}" '  # Layout
                          f'fill="{TEXT_2}" font-size="11" text-anchor="end">{t_}</text>')
        art = {"Balance": "der Balance seit", "Balance, Wert wandert": "der Balance seit",
               "verlassene Balance": "der verlassenen Balance seit", "Zone": "seit Beginn der Zone", "Tief": "seit dem Tief",
               "Hoch": "seit dem Hoch"}.get(g.get("art"), "")
        spaete.append(f'<text x="{ENDE - 4}" y="44" fill="{TEXT_3}" font-size="12" text-anchor="end">VOLUMEN {art.upper()} '  # Layout
                      f'{pd.Timestamp(g["ab"]):%d.%m.} ({g.get("tage")} Tage)</text>')
    for schl, farbe, wort in (("mauer", ROT, "Mauer seit Hoch"), ("stuetze", GRUEN, "Stütze seit Tief")):  # Hoch: Gipfel bzw. letztes
        k_ = vv.get(schl)
        if not k_:
            continue
        k0, k1, ab = k_
        if k1 < pmin or k0 > pmax:
            continue
        y1, y2 = Y(min(k1, pmax)), Y(max(k0, pmin))
        hoehe = max(2, y2 - y1)
        A(f'<rect x="{ENDE - 6}" y="{y1:.1f}" width="6" height="{hoehe:.1f}" fill="{farbe}" fill-opacity="0.85"/>'  # Layout
          f'<rect x="{X(0) - 4:.1f}" y="{y1:.1f}" width="{ENDE - X(0) + 4:.1f}" height="{hoehe:.1f}" fill="{farbe}" '  # Layout
          f'fill-opacity="0.06"/>')
        t_ = f"{wort} {pd.Timestamp(ab):%d.%m.}: {zahl(k0)}–{zahl(k1)} $"
        spaete.append(f'<text x="{ENDE - 10}" y="{platz(ENDE - 10, (y1 + y2) / 2 + 4, t_, 11, "end"):.1f}" fill="{farbe}" '  # Layout
                      f'font-size="11" font-weight="600" text-anchor="end">{t_}</text>')


def _signale(voll, d, index, pos, X, Y, A, spaete, platz, h, l):
    """Die gemessenen Zeichen im Kurschart (Prüf-Agent 13.11.2026: der Chart zeigte sie nicht): Schwungpunkte (Dow,
    n = 5) als kleine Ringe, Pocket Pivot „PP“, Spring „S“ und Upthrust „U“, höheres Tief bzw. tieferes Hoch gegen den
    Index „◆“. Abgabetage kommen ins Volumen (Rückgabe). Alles nach den Regeln von zeichen.py."""
    import zeichen
    tm = zeichen.tagesmarken(voll)
    hs, ts = zeichen.schwungpunkte(voll["High"], voll["Low"], SCHWUNG_N)
    erst = len(voll) - len(d)
    for liste, oben in ((hs, True), (ts, False)):
        for i_, p_ in liste:
            if i_ >= erst:
                i = i_ - erst
                A(f'<circle cx="{X(i):.1f}" cy="{Y(p_) + (-6 if oben else 6):.1f}" r="2.4" fill="none" stroke="{TEXT_2}" '  # Layout
                  f'stroke-width="1"><title>{d.index[i]:%d.%m.%Y}: Schwung{"hoch" if oben else "tief"} {zahl(p_)} $ '
                  f'(Dow-Struktur)</title></circle>')
    for t_ in tm["pocket"]:
        if t_ >= d.index[0]:
            i = pos(t_)
            spaete.append(f'<text x="{X(i):.1f}" y="{platz(X(i), Y(l[i]) + 15, "PP", 10, nach_oben=False):.1f}" '  # Layout
                          f'fill="{GRUEN}" font-size="10" font-weight="700" text-anchor="middle"><title>{t_:%d.%m.%Y}: '
                          f'Pocket Pivot – Volumen über dem größten Abgabetag der 10 Tage davor</title>PP</text>')
    for u in zeichen.umkehr(voll):             # Urvater Homma: Umkehrkerzen an Marken (Regeln nach Nison)
        t_ = u["tag"]
        if t_ < d.index[0]:
            continue
        i = pos(t_)
        stark = u["seite"] == "stärke"
        stand = {True: "bestätigt", False: "nicht bestätigt", None: "Bestätigung steht aus"}[u["bestaetigt"]]
        y_ = platz(X(i), Y(l[i]) + 15 if stark else Y(h[i]) - 9, u["kurz"], 10, nach_oben=not stark)  # Layout
        spaete.append(f'<text x="{X(i):.1f}" y="{y_:.1f}" fill="{GRUEN if stark else ROT}" font-size="10" '
                      f'font-weight="700" text-anchor="middle" fill-opacity="{1 if u["bestaetigt"] else 0.55}">'  # Layout
                      f'<title>{t_:%d.%m.%Y}: {u["name"]} an der Marke {u["marke"]} ({stand})</title>{u["kurz"]}</text>')
    for kw in zeichen.kraft_ohne_weg(voll, zeichen.MARKEN_TAGE, alle=True):   # Urvater Wyckoff: Kraft ohne Weg
        t_ = kw["tag"]
        if t_ < d.index[0]:
            continue
        i = pos(t_)
        stark = kw["seite"] == "stärke"
        y_ = platz(X(i), Y(l[i]) + 15 if stark else Y(h[i]) - 9, "KW", 10, nach_oben=not stark)  # Layout
        spaete.append(f'<text x="{X(i):.1f}" y="{y_:.1f}" fill="{GRUEN if stark else ROT}" font-size="10" '
                      f'font-weight="700" text-anchor="middle"><title>{t_:%d.%m.%Y}: Kraft ohne Weg an der Marke '
                      f'{kw["marke"]} – Volumen {zahl(kw["volumen"], 1)}-fach, Spanne {zahl(kw["spanne"] * 100, 0)} % '
                      f'des Schnitts (Wyckoff)</title>KW</text>')
    marken = []
    sp = zeichen.spring(voll)
    if sp:
        marken.append(sp)
    if index is not None:
        try:
            rel = zeichen.relativ(voll, index[index.index <= voll.index[-1]]) or {}
            marken += [z_ for z_ in rel.get("zeichen", []) if z_.get("tag")]
        except Exception:  # noqa: BLE001
            pass
    for z_ in marken:
        t_ = pd.Timestamp(z_["tag"])
        if t_ < d.index[0]:
            continue
        i = pos(t_)
        stark = z_["seite"] == "stärke"
        wort = "S" if z_["text"].startswith("Spring") else "U" if z_["text"].startswith("Upthrust") else "◆"
        txt = z_["text"].replace("&", "&amp;").replace("<", "&lt;")
        y_ = platz(X(i), Y(l[i]) + 28 if stark else Y(h[i]) - 22, wort, 13, nach_oben=not stark)  # Layout
        spaete.append(f'<text x="{X(i):.1f}" y="{y_:.1f}" fill="{GRUEN if stark else ROT}" font-size="13" '
                      f'font-weight="700" text-anchor="middle"><title>{txt}</title>{wort}</text>')
    return tm



def _einheit(ebene):
    return {"Tag": "Tage", "Woche": "Wochen", "Stunde": "Stunden"}[ebene]


def _tiefe_grenzen(t):
    """Preise der Tiefenanalyse, die in die Skala gehören (die alte Wertzone immer, Titel-Analyse 18.11.2026)."""
    if not t:
        return []
    st_, pb, alt = t["struktur"], t.get("pbd"), t.get("alt")
    w = [st_["pivot"], st_["short_pivot"], st_["profil"]["val"], st_["profil"]["vah"]]
    w += [alt["val"], alt["vah"]] if alt else []
    w += [pb["zone_tief"], pb["zone_hoch"], pb["impuls_kurs"]] if pb else []
    return w


def _tiefe_flaechen(t, d, pos, X, Y, A, spaete, platz, ENDE, pmin, pmax, profil_da):
    """Flächen nach Dalton (Micky 21.11.2026, aus der Titel-Analyse): alte Wertzone rot, Wertzone grün (im Tageschart
    zeichnet sie das graue Volumenprofil – dieselbe Regel), dünne Zonen grau, Dochte blau – ab dem Anker."""
    if not t:
        return
    pr, alt = t["struktur"]["profil"], t.get("alt")
    ab = pd.Timestamp(pr["ab"])
    x0 = X(pos(ab)) if ab >= d.index[0] else X(0)  # Layout

    def feld(a, b, farbe, deck, text, von=None):
        a, b = max(a, pmin), min(b, pmax)
        if b <= a:
            return
        x_ = von if von is not None else x0
        A(f'<rect x="{x_:.1f}" y="{Y(b):.1f}" width="{max(1, ENDE - x_):.1f}" height="{Y(a) - Y(b):.1f}" fill="{farbe}" '  # Layout
          f'fill-opacity="{deck}"><title>{text}</title></rect>')
        spaete.append(f'<text x="{x_ + 4:.1f}" y="{platz(x_ + 4, Y(b) + 12, text, 11, "start", False):.1f}" fill="{TEXT_2}" '  # Layout
                      f'font-size="11">{text}</text>')  # Layout
    if alt:
        feld(alt["val"], alt["vah"], ALT_FARBE, 0.13, f"Alte Wertzone {zahl(alt['val'])}–{zahl(alt['vah'])} (POC {zahl(alt['poc'])})",  # Layout
             X(0))  # Layout
    if not profil_da:
        feld(pr["val"], pr["vah"], WERT_FARBE, 0.16, f"Wertzone {zahl(pr['val'])}–{zahl(pr['vah'])}")  # Layout
    for lo, hi in pr["duenn"]:
        feld(lo, hi, DUENN_FARBE, 0.16, f"Dünne Zone {zahl(lo)}–{zahl(hi)}")  # Layout
    for z in (pr["docht_unten"], pr["docht_oben"]):
        if z:
            feld(z[0], z[1], DOCHT_FARBE, 0.14, f"Docht {zahl(z[0])}–{zahl(z[1])}")  # Layout


def _tiefe_linien(t, d, pos, X, Y, A, spaete, platz, ENDE, pmin, pmax):
    """Linien und PbD (Micky 21.11.2026, aus der Titel-Analyse): POC grün gepunktet, Pivot long rot und Pivot short
    violett gestrichelt (Rand der Balance), POC je Kerze als weißer Strich, nackte POCs weiß gepunktet bis zum rechten
    Rand; PbD nach Vorwald: Impuls als gelber Strich, faire Zone gelb gestrichelt mit dem Buchstaben, Ziel am
    Impulsbeginn bei gescheiterter Form, rechts neben dem Chart Zeit- und Volumenprofil seit Impulsbeginn."""
    if not t:
        return
    st_, pb, w = t["struktur"], t.get("pbd"), t.get("wander")
    N = len(d)
    halb = (X(1) - X(0)) / 2 if N > 1 else 4  # Layout
    for y_, farbe, strich, text in ((st_["profil"]["poc"], WERT_FARBE, "2 3", f"POC {zahl(st_['profil']['poc'])}"),  # Layout
                                    (st_["pivot"], ROT, "5 3", f"Pivot long {zahl(st_['pivot'])}"),  # Layout
                                    (st_["short_pivot"], PIVOT_SHORT_FARBE, "5 3", f"Pivot short {zahl(st_['short_pivot'])}")):  # Layout
        if pmin <= y_ <= pmax:
            A(f'<line x1="{X(0) - halb:.1f}" x2="{ENDE:.1f}" y1="{Y(y_):.1f}" y2="{Y(y_):.1f}" stroke="{farbe}" '  # Layout
              f'stroke-width="1.4" stroke-dasharray="{strich}"><title>{text}</title></line>')  # Layout
            x_t = X(0) - halb + 4  # Layout: am linken Rand über der Linie (rechts drängen sich Kurse und Etiketten)
            y2 = platz(x_t, Y(y_) - 4, text, 11, "start")  # Layout
            spaete.append(f'<text x="{x_t:.1f}" y="{y2:.1f}" fill="{farbe}" font-size="11">{text}</text>')  # Layout
    if w:
        for i, tag in enumerate(d.index):
            poc = (w["werte"].get(tag) or (None,))[0]  # Layout
            if poc is not None and pmin <= poc <= pmax:
                A(f'<line x1="{X(i) - halb * 0.8:.1f}" x2="{X(i) + halb * 0.8:.1f}" y1="{Y(poc):.1f}" y2="{Y(poc):.1f}" '  # Layout
                  f'stroke="{POC_KERZE}" stroke-width="2"/>')  # Layout
        for tag, poc in w["nackt"]:
            if tag >= d.index[0] and pmin <= poc <= pmax:  # Layout
                A(f'<line x1="{X(pos(tag)):.1f}" x2="{ENDE:.1f}" y1="{Y(poc):.1f}" y2="{Y(poc):.1f}" stroke="{POC_KERZE}" '  # Layout
                  f'stroke-opacity="0.55" stroke-dasharray="1 3"><title>nackter POC {zahl(poc)} ({tag:%d.%m.}) – nie wieder '  # Layout
                  f'erreicht</title></line>')
    if not pb:
        return
    i0, i1 = pos(pb["impuls_tag"]), pos(pb["impuls_ende_tag"])
    if pb["impuls_tag"] >= d.index[0]:  # Layout
        A(f'<line x1="{X(i0):.1f}" y1="{Y(pb["impuls_kurs"]):.1f}" x2="{X(i1):.1f}" y2="{Y(pb["impuls_ende_kurs"]):.1f}" '  # Layout
          f'stroke="{PBD_FARBE}" stroke-width="2.5"><title>PbD-Impuls {pb["impuls_tag"]:%d.%m.} → '  # Layout
          f'{pb["impuls_ende_tag"]:%d.%m.}</title></line>')
    zs = pd.Timestamp(pb["zone_start"])
    xl = (X(pos(zs)) - halb) if zs >= d.index[0] else X(0) - halb  # Layout
    yo, yu = Y(min(pb["zone_hoch"], pmax)), Y(max(pb["zone_tief"], pmin))
    A(f'<rect x="{xl:.1f}" y="{yo:.1f}" width="{max(2, ENDE - xl):.1f}" height="{max(1, yu - yo):.1f}" fill="none" '  # Layout
      f'stroke="{PBD_FARBE}" stroke-width="1.8" stroke-dasharray="6 3"><title>PbD: Form {pb["form"]} · faire Zone '  # Layout
      f'{zahl(pb["zone_tief"])}–{zahl(pb["zone_hoch"])}</title></rect>')
    spaete.append(f'<text x="{xl + 4:.1f}" y="{(yu + 20) if pb["form"] == "b" else (yo - 5):.1f}" fill="{PBD_FARBE}" '  # Layout
                  f'font-size="20" font-weight="700">{pb["form"]}</text>')  # Layout
    if pb["gescheitert"] and pmin <= pb["impuls_kurs"] <= pmax:
        A(f'<line x1="{X(0) - halb:.1f}" x2="{ENDE:.1f}" y1="{Y(pb["impuls_kurs"]):.1f}" y2="{Y(pb["impuls_kurs"]):.1f}" '  # Layout
          f'stroke="{PBD_FARBE}" stroke-width="1.4" stroke-dasharray="1 3"><title>Ziel am Impulsbeginn '  # Layout
          f'{zahl(pb["impuls_kurs"])}</title></line>')
    # Zeit- und Volumenprofil seit Impulsbeginn rechts neben dem Chart (Spalten nach den Etiketten)
    x_sp = B + 4  # Layout
    breite_ = (SEITE_PROFIL - 12) / 2  # Layout
    for j, (name, sil, farbe) in enumerate((("Zeit", pb.get("profil_zeit"), ZEIT_FARBE),
                                           ("Volumen", pb.get("profil_vol"), DUENN_FARBE))):
        x0 = x_sp + j * (breite_ + 4)  # Layout
        A(f'<text x="{x0:.1f}" y="26" fill="{TEXT_3}" font-size="10">{name}</text>'  # Layout
          f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="30" y2="430" stroke="{RAND}"/>')  # Layout
        if not sil:
            A(f'<text x="{x0 + 2:.1f}" y="230" fill="{TEXT_3}" font-size="10">ungemessen</text>')  # Layout
            continue
        poc = st_["profil"]["poc"]
        for lo, hi, anteil in sil:
            if hi < pmin or lo > pmax:
                continue
            y1, y2 = Y(min(hi, pmax)), Y(max(lo, pmin))
            A(f'<rect x="{x0:.1f}" y="{y1 + 0.5:.1f}" width="{max(1, anteil * breite_):.1f}" height="{max(1, y2 - y1 - 1):.1f}" '  # Layout
              f'fill="{farbe}" fill-opacity="{0.95 if lo <= poc <= hi else 0.5}"/>')  # Layout
    A(f'<text x="{x_sp:.1f}" y="446" fill="{PBD_FARBE}" font-size="10">Form {pb["form"]} seit {pb["impuls_tag"]:%d.%m.}</text>')  # Layout

def legende(ebene="Tag", gd_kurz=False):
    from gestaltung import t
    namen = {"Tag": ("GD50", "GD150", "GD200"), "Woche": ("GD10W", "GD30W", "GD40W"),
             "Stunde": ("GD50 Std.", "GD150 Std.", "GD200 Std.")}[ebene]
    eintraege = [(BLAU, namen[0]), (LILA, namen[1]), (SAND, namen[2] + " (langfristiger Trend)")]
    if gd_kurz and ebene == "Tag":
        eintraege += [(GD_KURZ[10], "GD10"), (GD_KURZ[20], "GD20")]
    eintraege += [(BLAU, "Base"), (GELB, "Flagge"), (LILA, "Konsolidierung (nach Absturz)"),
                  (GELB, "Pfeil gelb = Vorgeschichte"), (GRUEN, "Pfeil grün = Fahnenstange · ↑ = Ausbruch"),
                  (TEXT_3, "ZigZag (2 × ATR)"),
                  (TEXT_2, "Kontraktionen mit Tiefe (gestrichelt) · Rahmen der Enge in der Ampelfarbe · Pivot gestrichelt"),
                  (TUERKIS, "Band unter dem Volumen: Ruhe – kräftig bis 50 % vom Schnitt, blass bis 75 %"),
                  (GRUEN, "Band: viel Volumen am Aufwärtstag (blass über dem Schnitt, kräftig ab 1,5-fach), rot am Abwärtstag")]
    if ebene != "Woche":
        eintraege += [(KAUFZONE_FARBE, "Kaufzone (Pivot bis +5 %)"), (ROT, "Stopp 1,5 ATR vom Einstieg (Short gestrichelt)")]
    if ebene == "Tag":
        eintraege += [
                      (AVWAP_FARBEN["gipfel"], "AVWAP ab dem Hoch des Rückgangs (Gipfel der ganzen Korrektur, Wochen-Schwunghoch)"),
                      (AVWAP_FARBEN["hoch"], "AVWAP ab dem letzten Hoch (jüngstes nicht überschrittenes Wochen-Schwunghoch)"),
                      (AVWAP_FARBEN["tief"], "AVWAP ab dem Tief der Bewegung (Tief, an dem der Trend zum letzten Hoch begann; mit ihm: Zange)"),
                      (AVWAP_FARBEN["hoeher"], "AVWAP ab dem letzten höheren Tief (Tief des letzten Rückgangs ab 8 %, aus dem der Anstieg kam)"),
                      (AVWAP_FARBEN["zahlen"], "AVWAP ab dem letzten Zahlentag"),
                      (AVWAP_FARBEN["ereignis"], "AVWAP ab der jüngsten Lücke ab 4 % oder Volumenspitze (ohne Zahlen)"),
                      (AVWAP_FARBEN["ipo"], "AVWAP ab dem Börsengang (junge Aktien)"),
                      (AVWAP_FARBEN["ausbruch"], "AVWAP ab dem Ausbruchstag (Shannons Handoff)"),
                      (PROFIL_FARBE, "Volumenprofil der laufenden Balance (überlappende Tage nach Dalton), Linie = akzeptierter Wert"),
                      (ROT, "Band rechts rot: Mauer (Knoten seit dem Hoch des Rückgangs) · grün: Stütze (Knoten seit dem Tief der Bewegung)"), (GRUEN, "↑ Ausbruch mit Volumen-Vielfachem · ✕ Fehlausbruch"),
                      (RS_HOCH, "● RS-Hoch vor Kurs"), (RS_TIEF, "● RS-Tief vor Kurs"),
                      (TEXT_2, "○ Schwungpunkte (Dow) · PP = Pocket Pivot · S = Spring · U = Upthrust · ◆ = höheres Tief "
                               "(grün) bzw. tieferes Hoch (rot) gegen den Index"),
                      (ROT, "● über dem Volumen: Abgabetag · ○ verdeckte Abgabe"),
                      (TEXT_2, "an Marken: H = Hammer · SS = Shooting Star · E↑/E↓ = Engulfing · MS/ES = Morning/Evening "
                               "Star (Homma/Nison); blass = nicht bestätigt · KW = Kraft ohne Weg (Wyckoff)")]
    eintraege += [(WERT_FARBE, "Wertzone 70 % und POC (gepunktet) ab dem Anker – Dalton, im Tageschart das Volumenprofil"),
                  (DUENN_FARBE, "Dünne Zone (unter ⅓ des POC-Volumens)"), (DOCHT_FARBE, "Docht (dünner Rand des Profils)"),
                  (ALT_FARBE, "Alte Wertzone (letzte Balance ab 10 Kerzen vor dem Anker) · Pivot long gestrichelt"),
                  (PIVOT_SHORT_FARBE, "Pivot short (Tief der Balance) gestrichelt"),
                  (POC_KERZE, "Strich je Kerze = POC der Kerze · gepunktet = nackter POC (nie wieder erreicht)"),
                  (PBD_FARBE, "PbD (Vorwald): Impuls als Strich, faire Zone gestrichelt mit P, b oder D; rechts Zeit- und "
                              "Volumenprofil seit Impulsbeginn")]
    eintraege += [(INDEX_SCHATTEN, "S&P 500 gestrichelt, am linken Rand auf den Kurs gelegt")]
    eintraege += [(GELB, "E = Zahlen mit Kursreaktion unter dem Kurs, rechts daneben der nächste Termin")]
    return "".join(f'<span style="display:inline-flex;align-items:center;gap:8px;font-size:14px;color:{TEXT_2}">'
                   f'<span style="width:18px;height:4px;border-radius:2px;background:{f}"></span>{t(n)}</span>'
                   for f, n in eintraege)
