"""Der Code für Balance und Ungleichgewicht (Micky 13.11.2026) – eine Zustandsmaschine für Titel und Gruppe (der
Markt seit 23.11.2026 aus dem Zirkel des Index, zirkel.markt).

Das Bild: Anlass → Balance → Test am Rand → abgelehnt oder angenommen → Ungleichgewicht → eine der drei Kräfte beendet den
Lauf (Gegner antwortet · Antrieb erlischt · Wert akzeptiert) → neue Balance. Dieselben Namen und Farben auf allen drei
Ebenen. Die alten Wörter (Weinstein-Phase, Market Profile, Stufe, Feld, O'Neil, Marktzone) bleiben als Unterzeile.

Jedes Ergebnis: {ebene, zustand, richtung ("aufwärts"/"abwärts"/None), rand ("oben"/"unten"/None), anlass [Text],
belege [(Platz, Text)], kraft (eigen/geliehen: {art, text}), ende (Kraft, die den Lauf beendet) [Text], gegenseite
[Text], unterzeile, satz}. Kein Beleg ohne Zahl oder Datum; was nicht gemessen ist, steht nicht da.

Messungen der Lücken (13.11.2026) – nur hier, für alle drei Ebenen:
  (abgelehnt/angenommen zählen 10 Handelstage: Ausbruch A, Umkehr U, Rücktest R und Scheitern S des Market Profile,
   Ausbruch und Fehlausbruch des VCP-Scanners, Spring, Upthrust, Bruch der Spanne, Ausbruch aus der Verteilung.
   Fortsetzung F und Wert gewandert B sind kein Test am Rand, sondern das laufende Ungleichgewicht.)
  Kraft ohne Weg   ein Tag mit mindestens 1,5-fachem Volumen (50 Tage), Spanne unter 0,7 ATR, Schluss in der Zone,
                   Hoch bzw. Tief höchstens 3 % vom Rand (letzte 10 Tage): die Gegenseite schluckt den Druck.
  Exzess           am Hoch bzw. Tief der letzten 20 Tage (30-Minuten-Kerzen): ragt die äußerste Kerze mindestens 15 %
                   der Tagesschwankung (ATR 14) über die zweitäußerste, endete die Auktion dort mit Wucht (Exzess). Liegen zwei Kerzen höchstens
                   0,1 % auseinander, ist die Kante flach (schwaches Hoch/Tief): die Auktion ist dort unfertig.
  Volumenlücke     Abstand vom Kurs zum nächsten Volumenknoten (Mauer darüber, Stütze darunter, verankertes Profil).
  Verkaufs-Klimax  in den letzten 15 Tagen: Volumen ab 2-fach, Spanne ab 1,5 ATR, Tief am 60-Tage-Tief, Schluss in
                   der oberen Hälfte der Tagesspanne (gespiegelt: Kauf-Klimax am 60-Tage-Hoch).
  anderer Rand     nach einer Ablehnung das Ziel auf der Gegenseite der Zone.
  Ursache          Dauer der Balance in Wochen und ihr Volumen gegen die 50 Tage davor.
"""
import numpy as np
import pandas as pd

# Farben aus dem Bild der Zustände: grau = Balance, rot = Ungleichgewicht entsteht/läuft, grün = zurück ins Gleichgewicht
FARBE = {"Balance": "#8B949E", "Test am Rand": "#8B949E", "abgelehnt": "#3FB950", "angenommen": "#F85149",
         "Ungleichgewicht": "#F85149", "Ende des Laufs": "#3FB950", "Anlass": "#A371F7"}

MP_TAGE = 2            # angenommen aus dem Market Profile erst ab 2 Tagen mit dem Wert außerhalb (Plan 15)
FRISCH = 10            # abgelehnt/angenommen: höchstens 10 Handelstage her (danach Ungleichgewicht bzw. zurück in der Balance)
from vcp_zone import RAND_PCT   # noqa: E402  Test am Rand: Kurs höchstens 3 % vom Rand – eine Quelle (vcp_zone)
from masse import ATR_N, LAGE_MITTE, PHASE_VERTEILUNG, VOL_MIN_TAGE  # noqa: E402
EXZESS_ATR, FLACH_PCT = 0.15, 0.1    # Exzess: äußerste Kerze mindestens 15 % der Tagesschwankung (ATR) vor der nächsten
KLIMAX_VOL, KLIMAX_SPANNE, KLIMAX_TAGE = 2.0, 1.5, 15
MAUER_NAH = 3.0        # Gegner antwortet: Kurs höchstens 3 % vor Mauer bzw. Stütze
EIGEN_PCT = 5.0        # eigen: RS-Linie in 20 Tagen mindestens 5 % in Laufrichtung; geliehen: höchstens 1 %
PFEIL = {"aufwärts": "↑", "abwärts": "↓", None: ""}
# Die Stufe gibt dem Kasten den Namen (Schritt 8, Micky 16.11.2026): Balance in Stufe 1 ist die Basis, in Stufe 2 die
# Fortsetzung, in Stufe 3 die Verteilung, in Stufe 4 die Pause im Fall; ein Lauf aus Stufe 1 ist der Beginn, in Stufe 2
# die Fortsetzung – die übrigen Läufe nach dem, was sie in ihrer Stufe sind
BALANCE_IN_STUFE = {1: "Basis", 2: "Fortsetzung", 3: "Verteilung", 4: "Pause im Fall"}
LAUF_IN_STUFE = {("aufwärts", 1): "Beginn", ("aufwärts", 2): "Fortsetzung", ("aufwärts", 3): "aus der Verteilung",
                 ("aufwärts", 4): "Gegenbewegung im Fall", ("abwärts", 1): "Bruch der Basis",
                 ("abwärts", 2): "Gegenbewegung im Anstieg", ("abwärts", 3): "Beginn des Falls",
                 ("abwärts", 4): "Fortsetzung des Falls"}


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
KLIMAX_EXTREM_TAGE = 59    # Klimax: Tief bzw. Hoch der letzten 60 Tage (Tag selbst + 59)
EXZESS_TAGE = 20       # Exzess: am Hoch bzw. Tief der letzten 20 Tage
URSACHE_VOR_TAGE = 50  # Ursache: Volumen der Balance gegen die 50 Tage davor
RS_TAGE = 21           # Eigen oder geliehen: RS-Linie über 20 Tage (Wert vor 21 Handelstagen)
WEIT_BASIS = 10        # Technik: „sehr weit her“ = 10 hoch 6 Tage
WEIT_HOCH = 6          # Technik: Exponent zu WEIT_BASIS
TEXT_KURZ = 40         # Anzeige: Kurzname des Entscheids höchstens 40 Zeichen
BELEGE_JUENGSTE = 3    # die drei jüngsten Ereignisse am Rand bleiben als Beleg
ZONE_PUFFER = 1.005    # Kurs in der Zone: bis 0,5 % über der Oberkante
WERT_WOCHEN = 3        # Wert akzeptiert: neue Wertzone seit mindestens 3 Wochen
RS_GLEICH = 1      # Kraft: RS-Änderung höchstens 1 Punkt = mit dem Markt
MIT_MEHR = 1       # … mehr Kraft mit als gegen: über 1


def _z(x, f=".2f"):
    return format(x, f).replace(".", ",")


def _d(t):
    return f"{pd.Timestamp(t):%d.%m.}"


def _ergebnis(ebene, zustand, richtung=None, **kw):
    e = {"ebene": ebene, "zustand": zustand, "richtung": richtung, "rand": None, "anlass": [], "belege": [],
         "kraft": None, "ende": [], "gegenseite": [], "unterzeile": "", "messung": {}}
    e.update(kw)
    return e


def stufe_name(zustand, richtung, p):
    """Name des Kastens in seiner Stufe (Gefechtsordnung Schritt 8, Micky 16.11.2026: der Kreislauf läuft in jeder Stufe
    neu ab) – „Basis“, „Fortsetzung“, „Beginn“ …; None ohne Phase."""
    if p not in (1, 2, 3, 4) or not zustand:
        return None
    if zustand in ("Balance", "Test am Rand") or not richtung:
        return BALANCE_IN_STUFE[p]
    return LAUF_IN_STUFE[(richtung, p)]


def wort(e):
    """„Ungleichgewicht ↑ · Beginn“, „Test am Rand (oben) · Basis“ …"""
    if not e:
        return ""
    w = e["zustand"]
    if e.get("richtung") and w in ("abgelehnt", "angenommen", "Ungleichgewicht", "Ende des Laufs"):
        w += " " + PFEIL[e["richtung"]]
    if w == "Test am Rand" and e.get("rand"):
        w += f" ({e['rand']})"
    if e.get("stufe"):
        w += " · " + e["stufe"]
    return w


def farbe(e):
    return FARBE.get((e or {}).get("zustand"), "#8B949E")


# ── Messungen ───────────────────────────────────────────────────────────────────────────────────────────────────
def _atr(df, n=ATR_N):
    """Die eine ATR der App (atr.reihe) als Array."""
    import atr as atr_
    return atr_.reihe(df, n).to_numpy(float)


def klimax_tag(df):
    """Verkaufs-Klimax am Boden bzw. Kauf-Klimax am Hoch in den letzten 15 Tagen → {tag, art, volumen, spanne_atr}."""
    if len(df) < 70:
        return None
    h, l, c, v = (df[x].to_numpy(float) for x in ("High", "Low", "Close", "Volume"))
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().shift().to_numpy()
    a = _atr(df)
    for i in range(len(df) - 1, len(df) - 1 - KLIMAX_TAGE, -1):
        sp = h[i] - l[i]
        if not (v50[i] > 0 and a[i] > 0 and sp > 0) or v[i] < KLIMAX_VOL * v50[i] or sp < KLIMAX_SPANNE * a[i]:
            continue
        lage = (c[i] - l[i]) / sp
        if l[i] <= l[i - KLIMAX_EXTREM_TAGE:i + 1].min() and lage >= LAGE_MITTE:
            return {"tag": df.index[i], "art": "Verkaufs-Klimax", "volumen": v[i] / v50[i], "spanne_atr": sp / a[i]}
        if h[i] >= h[i - KLIMAX_EXTREM_TAGE:i + 1].max() and lage <= LAGE_MITTE:
            return {"tag": df.index[i], "art": "Kauf-Klimax", "volumen": v[i] / v50[i], "spanne_atr": sp / a[i]}
    return None


def exzess(df, roh30):
    """Kante am Hoch und am Tief der letzten 20 Tage aus den 30-Minuten-Kerzen → {oben: {...}, unten: {...}}."""
    if roh30 is None or len(df) < 20:
        return {}
    aus = {}
    a = _atr(df)[-1]
    atr_pct = a / float(df["Close"].iloc[-1]) * 100 if a == a else 2.0
    t = df.iloc[-EXZESS_TAGE:]
    for seite, spalte, fn in (("oben", "High", "idxmax"), ("unten", "Low", "idxmin")):
        tag = getattr(t[spalte], fn)()
        k = roh30[roh30.index.normalize() == pd.Timestamp(tag).normalize()]
        if len(k) < 4:
            continue
        w = np.sort(k[spalte].to_numpy(float))
        a, b = (w[-1], w[-2]) if seite == "oben" else (w[0], w[1])
        abst = abs(a / b - 1) * 100
        art = "Exzess" if abst >= EXZESS_ATR * atr_pct else "flach" if abst <= FLACH_PCT else None
        if art:
            aus[seite] = {"tag": tag, "art": art, "abstand": abst, "preis": float(a)}
    return aus


def ursache(df, zone):
    """Größe der Ursache: Dauer der Balance und ihr Volumen gegen die 50 Tage davor."""
    if not zone or not zone.get("zone"):
        return None
    i = int(zone["start_i"])
    v = df["Volume"].to_numpy(float)
    vor = v[max(0, i - URSACHE_VOR_TAGE):i]
    if len(vor) < 20 or not np.nanmean(vor) > 0:
        return {"wochen": zone.get("wochen"), "volumen": None}
    return {"wochen": zone.get("wochen"), "volumen": float(np.nanmean(v[i:]) / np.nanmean(vor))}


def _rs20(df, idx):
    try:
        c = df["Close"]
        i = idx["Close"].reindex(c.index).ffill()
        if len(c) < 22 or not i.iloc[-RS_TAGE] > 0:
            return None
        t = (c.iloc[-1] / c.iloc[-RS_TAGE] - 1) * 100
        m = (i.iloc[-1] / i.iloc[-RS_TAGE] - 1) * 100
        rs = ((c.iloc[-1] / i.iloc[-1]) / (c.iloc[-RS_TAGE] / i.iloc[-RS_TAGE]) - 1) * 100
        return t, m, rs
    except Exception:  # noqa: BLE001
        return None


def bewegung(zustand, richtung):
    """Richtung, in die sich der Kurs bewegt: nach einer Ablehnung gegen den abgelehnten Ausbruch."""
    if zustand == "abgelehnt" and richtung:
        return "abwärts" if richtung == "aufwärts" else "aufwärts"
    return richtung


def kraft(df, idx, richtung, k=None):
    """Eigen oder geliehen: trägt der Titel die Bewegung selbst oder trägt ihn der Markt? (RS-Linie in 20 Tagen,
    gemessen in Laufrichtung; Chart-Prüfer Lauf 4, 15.11.2026: vorher hieß jeder Rest „mit dem Markt“ – auch +22 % RS
    gegen die Laufrichtung.)
      eigen     RS-Linie mindestens 5 % in Laufrichtung
      geliehen  RS-Linie höchstens ±1 %, der Kurs läuft mit dem Markt
      gemischt  RS-Linie zwischen 1 und 5 % in Laufrichtung (teils eigen)
      gegen     RS-Linie über 1 % gegen die Laufrichtung – Gegenzeichen (die Kraft liegt auf der anderen Seite)
    Stärke in der Schwäche (bzw. Schwäche in der Stärke) macht „eigen“, solange die RS-Linie nicht gegen die
    Laufrichtung läuft (Micky: der stärkste Edge)."""
    r = _rs20(df, idx) if idx is not None else None
    if not r:
        return None
    t, m, rs = r
    rel = (k or {}).get("relativ") or {}
    zahl = f"Titel {_z(t, '+.1f')} %, S&P 500 {_z(m, '+.1f')} %, RS-Linie {_z(rs, '+.1f')} % (20 Tage)"
    auf = richtung == "aufwärts" if richtung else t >= 0     # ohne Laufrichtung (Balance): die Richtung des Kurses
    mit = rs if auf else -rs                                  # RS-Änderung in Laufrichtung
    if mit >= EIGEN_PCT:
        art = "eigen"
    elif abs(rs) <= RS_GLEICH:
        art = "geliehen"
    elif mit > MIT_MEHR:
        art = "gemischt"
    else:
        art = "gegen"
    if art != "gegen" and auf and rel.get("staerke"):
        art, zahl = "eigen", zahl + " · Stärke in der Schwäche"
    if art != "gegen" and not auf and rel.get("schwaeche"):
        art, zahl = "eigen", zahl + " · Schwäche in der Stärke"
    text = {"eigen": "eigene Kraft", "geliehen": "geliehen vom Markt", "gemischt": "teils eigen (RS 1–5 %)",
            "gegen": "RS gegen die Laufrichtung (Gegenzeichen)"}[art]
    return {"art": art, "text": f"{text}: {zahl}"}


# ── Titel ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _rahmen(zone, mp):
    """Ränder der Balance: Zone des Scanners, sonst der Rahmen der Wertzone (Market Profile)."""
    if zone and zone.get("zone"):
        return float(zone["oben"]), float(zone["unten"]), f"{zone.get('name', 'Zone')} des Scanners"
    st = (mp or {}).get("stand") or []
    if st:
        return float(st[-1]["hoch"]), float(st[-1]["tief"]), "Wertzone (Market Profile)"
    return None, None, None


def _seit(df, tag):
    try:
        return int(len(df) - 1 - df.index.get_indexer([pd.Timestamp(tag)], method="nearest")[0])
    except Exception:  # noqa: BLE001
        return WEIT_BASIS ** WEIT_HOCH


def _tag_im_text(text, df):
    import re
    m = re.search(r"am (\d\d)\.(\d\d)\.", text)
    if not m:
        return None
    j = df.index[-1].year
    t = pd.Timestamp(j, int(m.group(2)), int(m.group(1)))
    return t if t <= df.index[-1] else pd.Timestamp(j - 1, int(m.group(2)), int(m.group(1)))


def titel(df, k, idx=None, mp=None, br=None, zone=None, profil=None, zahltag=None, roh30=None):
    """Zustand eines Titels aus dem, was die App schon misst (Kreislauf, Market Profile, VCP-Scanner, Profil)."""
    if df is None or len(df) < 60 or not k:
        return None
    c = float(df["Close"].iloc[-1])
    p = k.get("phase")
    zs = k.get("zeichen") or []
    oben, unten, rahmen = _rahmen(zone, mp)
    mz = (mp or {}).get("zustand") or {}
    sig = [s for s in (mp or {}).get("signale") or [] if _seit(df, s["tag"]) <= FRISCH]
    texte = [x["text"] for x in zs]
    hat = lambda vor: next((x for x in zs if x["text"].startswith(vor)), None)      # noqa: E731
    belege, anlass, ende, gegen = [], [], [], []
    mess = {}

    # Anlass (Plan 15, Micky 16.11.2026): Spring und Upthrust sind Zwang (gefangene Verkäufer bzw. Käufer), nur solange
    # sie gelten; „Verteidiger leer“ nur bei echter Enge (letzte Kontraktion höchstens 10 %, Volumen der Enge unter dem
    # Schnitt); die Information (Zahlen) prüft Zeit und Richtung, sobald der Zustand feststeht
    info = next((x for x in zs if x["art"] == "ereignis" and not x["text"].startswith("Market Profile an der Schwelle")),
                None)
    e_z = {}
    if zone and zone.get("zone"):
        try:
            import vcp_zone
            e_z = vcp_zone.enge(df, zone) or {}
        except Exception:  # noqa: BLE001
            e_z = {}
    echt_eng = bool(e_z.get("eng") and e_z.get("trocken"))
    for vor in ("Volumen trocknet aus", "Einquetschung", "3 Wochen eng"):
        x = hat(vor)
        if x and echt_eng:
            anlass.append(f"Verteidiger leer: {x['text']}")
    sp_ = hat("Spring")
    if sp_:
        anlass.append(f"Zwang: gefangene Verkäufer unter dem Rand: {sp_['text']}")
    fa = next((t for t in texte if "Fehlausbruch" in t), None)
    up_ = hat("Upthrust")
    for x_ in ([fa] if fa else []) + ([up_["text"]] if up_ else []):
        anlass.append(f"Zwang: gefangene Käufer über dem Rand: {x_}")

    # Messungen
    if oben and unten:
        import zeichen
        kow = zeichen.kraft_ohne_weg(df, oben=oben, unten=unten)
        if kow:
            mess["kraft_ohne_weg"] = kow
            wer = "Verkäufer schlucken die Nachfrage" if kow["rand"] == "oben" else "Käufer schlucken das Angebot"
            belege.append(("Test am Rand", f"Kraft ohne Weg am {_d(kow['tag'])}: Volumen {_z(kow['volumen'])}-fach, "
                                           f"Spanne {_z(kow['spanne'] * 100, '.0f')} % des Schnitts an der Marke "
                                           f"{kow['marke']} – {wer}"))
    kl = klimax_tag(df)
    if kl:
        mess["klimax"] = kl
    ex = exzess(df, roh30)
    if ex:
        mess["exzess"] = ex
    ur = ursache(df, zone)
    if ur:
        mess["ursache"] = ur
        belege.append(("Balance", f"Ursache: {round(ur['wochen'])} Wochen Balance" +
                       (f", Volumen {_z(ur['volumen'])}-fach der 50 Tage davor" if ur.get("volumen") else "")))
    vv = profil or {}
    mauer, stuetze = vv.get("mauer"), vv.get("stuetze")
    if mauer:
        mess["mauer_pct"] = (mauer[0] / c - 1) * 100
    if stuetze:
        mess["stuetze_pct"] = (c / stuetze[1] - 1) * 100

    # 1./2. abgelehnt oder angenommen: das jüngste Ereignis am Rand der letzten 20 Tage entscheidet, die älteren
    # bleiben als Beleg (MSFT 04.11.: Spring am 02.11., zwei Tage später Ausbruch – angenommen, mit dem Spring als Beleg)
    ereignisse = []                              # (Tag, Zustand, Richtung, Beleg)
    nachher = []                                 # Belege, die keinen Zustand setzen (Rücktest, Fortsetzung)
    # Ausbruch aus einer Pause tief in der großen Zone (Minervini: Cheat im unteren oder mittleren Drittel der Base) ist
    # ein Einstieg, aber keine Annahme außerhalb der großen Balance – die Zone gilt weiter (Chart-Prüfer 14.11.2026, LUV:
    # „Ausbruch“ über 42,08 $ mitten in der Zone 37,40–52,88 $ neben dem Zustand Balance)
    # die eine Cheat-Regel (vcp_zone.cheat): ausbruch() zählt solche Ausbrüche nicht, hier stehen sie als innere Rotation
    ch_br = None
    if zone and zone.get("zone"):
        try:
            import vcp_zone
            ch_br = vcp_zone.ausbruch(df, jetzt=zone, cheats=True)
        except Exception:  # noqa: BLE001
            ch_br = None
    if ch_br:
        nachher.append(("Balance", f"innere Rotation: {'Fehlausbruch' if ch_br.get('fehl') else 'Ausbruch'} am "
                                   f"{_d(ch_br['tag'])} über {_z(ch_br['pivot'])} $ aus einer Pause in der Zone – "
                                   f"{ch_br['cheat']} der Base, Minervini"))
    if br and br.get("cheat"):
        br = None
    if br and br.get("fehl"):
        ereignisse.append((br["fehl_tag"], "abgelehnt", "aufwärts",
                           f"Fehlausbruch: Ausbruch am {_d(br['tag'])} über den Pivot {_z(br['pivot'])} $, am "
                           f"{_d(br['fehl_tag'])} zurück in der Zone"))
    elif br and c > br["pivot"]:
        ereignisse.append((br["tag"], "angenommen", "aufwärts",
                           f"Ausbruch am {_d(br['tag'])} über den Pivot {_z(br['pivot'])} $"
                           + (f" mit Volumen {_z(br['volumen'])}-fach" if br.get("volumen") else "")
                           + (", Rücktest läuft" if br.get("ruecktest") else "")))
    aktiv = (mp or {}).get("aktiv")
    scanner = bool(zone and zone.get("zone"))
    vorstoss = None

    def am_rand(preis, d):
        """Liegt ein Ereignis des Market Profile am Rand der großen Balance (Zone des Scanners)? Innerhalb der Zone
        sind die kurzen Wertzonen innere Rotation, kein Test am Rand (gemessen 04.11.2026: sonst „angenommen“ bei
        einem Viertel aller Titel)."""
        if not scanner:
            return True
        return preis >= oben * (1 - RAND_PCT / 100) if d == "↑" else preis <= unten * (1 + RAND_PCT / 100)

    for s_ in sig:
        ri = "aufwärts" if s_["dir"] == "↑" else "abwärts"
        if s_["art"] in ("S", "A", "U") and not am_rand(s_["preis"], s_["dir"]):
            nachher.append(("Balance", f"innere Rotation: Market Profile {s_['art']} {s_['dir']} am {_d(s_['tag'])} "
                                       f"bei {_z(s_['preis'])} $, innerhalb der Zone"))
            continue
        if s_["art"] == "S":
            ereignisse.append((s_["tag"], "abgelehnt", ri, f"Market Profile: Ausbruch {s_['dir']} am {_d(s_['tag'])} "
                                                           "gescheitert, Schluss zurück im Wert der verlassenen Wertzone"))
        elif s_["art"] in ("A", "U") and aktiv and aktiv["dir"] == s_["dir"]:
            name = {"A": "Ausbruch", "U": "Umkehr"}[s_["art"]]
            # Plan 15 (Micky 16.11.2026, Dalton: Zeit baut Wert): angenommen erst ab MP_TAGE Tagen mit dem Tageswert
            # außerhalb der Wertzone – der erste Tag ist ein Vorstoß (Test am Rand)
            wz, t_ = aktiv["zone"], (mp or {}).get("tage") or []
            draussen = sum(1 for p_ in t_[aktiv["seit"]:] if (p_["val"] > wz["vah"] if s_["dir"] == "↑"
                                                               else p_["vah"] < wz["val"]))
            if draussen >= MP_TAGE:
                ereignisse.append((s_["tag"], "angenommen", ri, f"Market Profile: {name} {s_['dir']} am {_d(s_['tag'])} – "
                                                                f"Tageswert an {draussen} Tagen ganz außerhalb der Wertzone"))
            else:
                vorstoss = ("oben" if s_["dir"] == "↑" else "unten",
                            f"Vorstoß: Market Profile {name} {s_['dir']} am {_d(s_['tag'])} – Tageswert außerhalb, Tag "
                            f"{draussen} (angenommen ab {MP_TAGE} Tagen, Dalton)")
        elif s_["art"] == "R" and aktiv and aktiv["dir"] == s_["dir"]:
            nachher.append(("angenommen", f"Rücktest hält am {_d(s_['tag'])} (Market Profile R)"))
        elif s_["art"] in ("F", "B") and aktiv and aktiv["dir"] == s_["dir"] and scanner \
                and unten <= s_["preis"] <= oben:
            # Wert wandert innerhalb der Zone: innere Rotation, kein Ungleichgewicht (Chart-Prüfer Lauf 4, 42 Fälle)
            nachher.append(("Balance", f"innere Rotation: Market Profile {'Fortsetzung' if s_['art'] == 'F' else 'Wert gewandert'} "
                                       f"{s_['dir']} am {_d(s_['tag'])} bei {_z(s_['preis'])} $, innerhalb der Zone"))
        elif s_["art"] in ("F", "B") and aktiv and aktiv["dir"] == s_["dir"]:
            nachher.append(("Ungleichgewicht", f"Market Profile: {'Fortsetzung' if s_['art'] == 'F' else 'Wert gewandert'} "
                                               f"{s_['dir']} am {_d(s_['tag'])}"))
    aufgehoben = []                              # Spring/Upthrust, die der Kurs danach widerlegt hat – zählen nicht mehr
    for vor, zst, ri in (("Spring", "abgelehnt", "abwärts"), ("Upthrust", "abgelehnt", "aufwärts"),
                         ("Schluss unter dem Tief der", "angenommen", "abwärts"),
                         ("Schluss über dem Hoch der Verteilung", "angenommen", "aufwärts")):
        x = hat(vor)
        if x:
            tag = x.get("tag") or _tag_im_text(x["text"], df) or df.index[-1]
            if vor in ("Spring", "Upthrust"):
                # aufgehoben (Chart-Prüfer Lauf 4): nach dem Upthrust ein Schluss über seinem Tageshoch, nach dem Spring
                # ein Schluss unter seinem Tagestief – dann gilt der Fehlausbruch nicht mehr
                try:
                    i_ = df.index.get_indexer([pd.Timestamp(tag)], method="nearest")[0]
                    nach = df["Close"].iloc[i_ + 1:]
                    if len(nach) and ((vor == "Upthrust" and nach.max() > df["High"].iloc[i_])
                                      or (vor == "Spring" and nach.min() < df["Low"].iloc[i_])):
                        aufgehoben.append(x["text"])
                        nachher.append(("Balance", f"{vor} am {_d(df.index[i_])} aufgehoben: Schluss "
                                                   f"{'über seinem Tageshoch' if vor == 'Upthrust' else 'unter seinem Tagestief'}"))
                        continue
                except Exception:  # noqa: BLE001
                    pass
            ereignisse.append((pd.Timestamp(tag), zst, ri, x["text"]))
    if aufgehoben:                               # ein widerlegter Spring/Upthrust ist auch kein Anlass mehr
        anlass = [x_ for x_ in anlass if not any(x_.endswith(t_) for t_ in aufgehoben)]
    ereignisse = [e_ for e_ in ereignisse if _seit(df, e_[0]) <= FRISCH]
    ereignisse.sort(key=lambda e_: pd.Timestamp(e_[0]))
    zustand = richtung = rand = None
    t_ereignis = None
    if ereignisse:
        t_ereignis, zustand, richtung, entscheid = ereignisse[-1]
        mess["entscheid"] = entscheid.split(":")[0].split(" am ")[0][:TEXT_KURZ]
        for _, zst, ri, text in ereignisse[-BELEGE_JUENGSTE:]:          # die drei jüngsten, das jüngste zuletzt
            belege.append((zst, text))
    if vorstoss and not zustand:                 # Vorstoß über den Rand, noch nicht angenommen
        zustand, rand = "Test am Rand", vorstoss[0]
        belege.append(("Test am Rand", vorstoss[1]))
    for zst, text in nachher[-2:]:
        if (zst == "angenommen" and zustand != "angenommen") or (zst == "Balance" and zustand):
            continue
        belege.append((zst, text))
    if zustand == "abgelehnt" and oben and unten:
        ziel = unten if richtung == "aufwärts" else oben
        weg = (ziel / c - 1) * 100
        gegen.append(f"anderer Rand {_z(ziel)} $ " + (f"({_z(weg, '+.1f')} %)" if (weg < 0) == (richtung == "aufwärts")
                                                      else "schon erreicht"))

    # angenommen → Ungleichgewicht (Plan 15, Micky 16.11.2026): sobald der Kurs die Kaufzone verlassen hat (mehr als 5 %
    # über dem Pivot bzw. jenseits des Randes) und am 10er/20er reitet – nicht erst nach 10 Tagen
    if zustand == "angenommen":
        import reiten
        import vcp_zone
        ref = (br["pivot"] if br and c > br["pivot"] and richtung == "aufwärts"
               else oben if richtung == "aufwärts" else unten)
        weit = bool(ref) and ((c / ref - 1) * 100 > vcp_zone.KAUFZONE if richtung == "aufwärts"
                              else (1 - c / ref) * 100 > vcp_zone.KAUFZONE)
        rt_ = reiten.ungleichgewicht(df) if weit else None
        if rt_ and rt_["richtung"] == richtung:
            zustand = "Ungleichgewicht"
            belege.append(("Ungleichgewicht", f"Kaufzone verlassen: Kurs {_z(abs(c / ref - 1) * 100, '.1f')} % "
                                              f"{'über' if richtung == 'aufwärts' else 'unter'} {_z(ref)} $, Schluss "
                                              f"{'über dem steigenden' if richtung == 'aufwärts' else 'unter dem fallenden'} "
                                              f"{rt_['linie']} {_z(rt_['wert'])} $ (Kullamägi)"))

    # 3. Balance oder Test am Rand: der Kurs steht in der Zone
    in_zone = bool(zone and zone.get("zone") and unten <= c <= oben * ZONE_PUFFER)
    if not zustand and (in_zone or (p in (1, 3) and oben and unten and unten <= c <= oben)
                        or (p in (0, None) and mz.get("wort", "").startswith(("Balance", "an der Schwelle")))):
        zustand = "Balance"
        if oben and c >= oben * (1 - RAND_PCT / 100):
            zustand, rand = "Test am Rand", "oben"
        elif unten and c <= unten * (1 + RAND_PCT / 100):
            zustand, rand = "Test am Rand", "unten"
        if mz.get("wort", "").startswith("an der Schwelle"):
            r_ = "oben" if mz.get("dir") == "↑" else "unten"
            nah = not (oben and unten) or (c >= oben * (1 - RAND_PCT / 100) if r_ == "oben" else c <= unten * (1 + RAND_PCT / 100))
            if nah:                                      # Test am Rand nur bis 3 % vom Rand (Chart-Prüfer Lauf 4)
                zustand, rand = "Test am Rand", r_
                belege.append(("Test am Rand", f"Market Profile: {mz['wort']}"))
            else:
                belege.append(("Balance", f"Market Profile: {mz['wort']} – innerhalb der Zone, noch nicht am Rand"))
        if oben and unten:
            belege.insert(0, ("Balance", f"{rahmen}: {_z(unten)}–{_z(oben)} $, Kurs {_z((c / oben - 1) * 100, '+.1f')} % "
                                         f"zum oberen Rand"))

    # 4. Ungleichgewicht oder Ende des Laufs
    if not zustand:
        # Kullamägi führt (Gefechtsordnung Schritt 5, Micky 16.11.2026): der Kurs reitet am steigenden 10er bzw. 20er;
        # Phase und Dow-Struktur sind Zeichen (vorher maßen sie das Ungleichgewicht)
        import reiten
        rt = reiten.ungleichgewicht(df)
        if rt:
            zustand, richtung = "Ungleichgewicht", rt["richtung"]
            auf = richtung == "aufwärts"
            belege.append(("Ungleichgewicht", f"Schluss {'über dem steigenden' if auf else 'unter dem fallenden'} "
                                              f"{rt['linie']} {_z(rt['wert'])} $ (Kullamägi)"))
            dow = (k.get("dow_tag") or {}).get("struktur")
            if p in (2, 4) or dow:
                passt = (p == 2 or dow == "aufwärts") if auf else (p == 4 or dow == "abwärts")
                belege.append(("Ungleichgewicht" if passt else "Balance",
                               f"Zeichen: {'Phase ' + str(p) if p in (2, 4) else 'Dow-Struktur ' + str(dow)}"
                               + ("" if passt else " – passt nicht zur Richtung")))
        else:
            zustand = "Balance"
            if oben and unten:
                belege.insert(0, ("Balance", f"{rahmen}: {_z(unten)}–{_z(oben)} $"))

    # Information als Anlass (Plan 15): sie muss vor dem Ereignis am Rand liegen und in Laufrichtung zeigen; gegen die
    # Richtung ist sie ein Gegenzeichen (Zahlen: eine Reaktion, nach dem heutigen Kurs – zeichen.zahlen)
    ri_ = bewegung(zustand, richtung) or {"oben": "aufwärts", "unten": "abwärts"}.get(rand)   # abgelehnt ↑ = Lauf abwärts
    if info:
        seite_ = "aufwärts" if info["seite"] == "stärke" else "abwärts"
        t_info = info.get("tag") or _tag_im_text(info["text"], df)
        spaeter = t_ereignis is not None and t_info is not None and pd.Timestamp(t_info) > pd.Timestamp(t_ereignis)
        if ri_ and seite_ != ri_:
            gegen.append(f"Gegenzeichen: {info['text']}")
        elif spaeter:
            belege.append((zustand or "Balance", f"nach dem Ereignis: {info['text']}"))
        else:
            anlass.insert(0, f"Information: {info['text']}")
    elif zahltag is not None and _seit(df, zahltag) <= FRISCH and (t_ereignis is None
                                                                    or pd.Timestamp(zahltag) <= pd.Timestamp(t_ereignis)):
        anlass.insert(0, f"Information: Zahlen am {_d(zahltag)}")

    # Kräfte, die den Lauf beenden (bei Ungleichgewicht und angenommen)
    if zustand in ("Ungleichgewicht", "angenommen"):
        auf = richtung == "aufwärts"
        if auf and mauer and mess["mauer_pct"] <= MAUER_NAH:
            ende.append(f"Gegner antwortet: Mauer {_z(mauer[0])}–{_z(mauer[1])} $ nur {_z(mess['mauer_pct'], '.1f')} % "
                        f"über dem Kurs (gefangene Käufer seit {_d(mauer[2])})")
        if not auf and stuetze and mess["stuetze_pct"] <= MAUER_NAH:
            ende.append(f"Gegner antwortet: Stütze {_z(stuetze[0])}–{_z(stuetze[1])} $ nur "
                        f"{_z(mess['stuetze_pct'], '.1f')} % unter dem Kurs (Käufer im Gewinn seit {_d(stuetze[2])})")
        if mess.get("kraft_ohne_weg") and mess["kraft_ohne_weg"]["rand"] == ("oben" if auf else "unten"):
            kw = mess["kraft_ohne_weg"]
            ende.append(f"Gegner antwortet: Kraft ohne Weg am {_d(kw['tag'])} (Volumen {_z(kw['volumen'])}-fach, "
                        f"Spanne {_z(kw['spanne'] * 100, '.0f')} % des Schnitts, Marke {kw['marke']})")
        if k.get("ziel") == (PHASE_VERTEILUNG if auf else 1):
            ende.append(f"Antrieb erlischt: Wechsel {p} → {k['ziel']} zeichnet sich ab")
        if auf and k.get("rueckschlag"):
            ende.append("Antrieb erlischt: Rückschlag (Wochenschluss unter dem GD10W, mindestens 15 % unter dem Hoch)")
        if kl and kl["art"] == ("Kauf-Klimax" if auf else "Verkaufs-Klimax"):
            ende.append(f"Antrieb erlischt: {kl['art']} am {_d(kl['tag'])} (Volumen {_z(kl['volumen'])}-fach, "
                        f"Spanne {_z(kl['spanne_atr'], '.1f')} ATR)")
        if auf:
            try:
                import erkennung
                gr = erkennung.klimax(*(df[x].to_numpy(float) for x in ("High", "Low", "Close", "Volume")))
                if gr:
                    ende.append("Antrieb erlischt: Klimax-Verdacht (" + ", ".join(gr) + ")")
            except Exception:  # noqa: BLE001
                pass
        st = (mp or {}).get("stand") or []
        if mz.get("wort", "").startswith("Balance") and st and st[-1].get("wochen", 0) >= WERT_WOCHEN \
                and st[-1].get("herkunft") == ("↑" if auf else "↓"):
            ende.append(f"Wert akzeptiert: neue Wertzone seit {st[-1]['wochen']} Wochen auf der neuen Höhe")
        if ende and zustand == "Ungleichgewicht":
            zustand = "Ende des Laufs"

    # Wer ist stärker – die Waage über alle Zeichen (Struktur, Volumen, RS, Ereignis; Regelkarte). Chart-Prüfer Lauf 4:
    # vorher nur Struktur und Volumen, Zeichen ohne Seite aufgezählt und ein Gleichstand als Beleg
    st_ = [x for x in zs if x["seite"] == "stärke" and x["text"] not in aufgehoben]
    sw_ = [x for x in zs if x["seite"] == "schwäche" and x["text"] not in aufgehoben]
    gs, gw = sum(x["gewicht"] for x in st_), sum(x["gewicht"] for x in sw_)
    if gs != gw:
        wer = "Käufer stärker" if gs > gw else "Verkäufer stärker"
        seite = lambda xs: "; ".join(f"{x['text']} ({x['gewicht']})" for x in xs[:3])  # noqa: E731
        teile = ([f"Käufer: {seite(st_)}"] if st_ else []) + ([f"Verkäufer: {seite(sw_)}"] if sw_ else [])
        platz = "Test am Rand" if zustand == "Test am Rand" else "Balance" if zustand is None or zustand == "Balance" else zustand
        belege.append((platz, f"{wer} (Gewicht {gs} gegen {gw}) – " + " · ".join(teile)))
    mess["gewicht"] = (gs, gw)

    # Gegenseite und Volumenlücke
    bew = bewegung(zustand, richtung)
    if bew is None:                              # Balance: beide Seiten; Test am Rand: die Seite des Randes
        bew = {"oben": "aufwärts", "unten": "abwärts"}.get(rand, "beide")
    auf = bew in ("aufwärts", "beide")
    if auf and mauer:
        gegen.append(f"Angebot wartet: Mauer {_z(mauer[0])}–{_z(mauer[1])} $ ({_z(mess['mauer_pct'], '+.1f')} %), "
                     f"bis dahin kein Volumenknoten")
    if bew in ("abwärts", "beide") and stuetze:
        gegen.append(f"Nachfrage wartet: Stütze {_z(stuetze[0])}–{_z(stuetze[1])} $ (−{_z(mess['stuetze_pct'], '.1f')} %), "
                     f"bis dahin kein Volumenknoten")
    for seite, x in (ex or {}).items():
        if x["art"] == "Exzess" and zustand in ("Ungleichgewicht", "angenommen") and seite == ("oben" if auf else "unten"):
            ende.append(f"Gegner antwortet: Exzess am {'Hoch' if seite == 'oben' else 'Tief'} {_z(x['preis'])} $ am "
                        f"{_d(x['tag'])} (äußerste 30-Minuten-Kerze {_z(x['abstand'], '.1f')} % vor der nächsten)")
            if zustand == "Ungleichgewicht":
                zustand = "Ende des Laufs"
        elif x["art"] == "flach":
            gegen.append(f"schwaches {'Hoch' if seite == 'oben' else 'Tief'} {_z(x['preis'])} $ am {_d(x['tag'])}: "
                         f"flache Kante (30-Minuten-Kerzen {_z(x['abstand'], '.2f')} % auseinander) – Auktion dort unfertig")
        elif x["art"] == "Exzess":
            # nur am Rand der laufenden Zone ein Test am Rand (Chart-Prüfer Lauf 4: Exzesse aus alten Zonen oder mitten
            # in der Zone landeten unter „Test am Rand“)
            if scanner and zone.get("start_i") is not None and _seit(df, x["tag"]) > len(df) - 1 - zone["start_i"]:
                continue                                  # vor Beginn der Zone
            r_nah = oben and unten and (x["preis"] >= oben * (1 - RAND_PCT / 100) if seite == "oben"
                                        else x["preis"] <= unten * (1 + RAND_PCT / 100))
            belege.append(("Test am Rand" if r_nah else "Balance",
                           f"Exzess am {'Hoch' if seite == 'oben' else 'Tief'} {_z(x['preis'])} $ am {_d(x['tag'])} "
                           f"(äußerste 30-Minuten-Kerze {_z(x['abstand'], '.1f')} % vor der nächsten) – Auktion dort beendet"
                           + (", Rand verteidigt" if r_nah else ", innerhalb der Zone")))
    if kl and kl["art"] == "Verkaufs-Klimax" and zustand != "Ende des Laufs":
        belege.append(("Ende des Laufs", f"Verkaufs-Klimax am {_d(kl['tag'])} (Volumen {_z(kl['volumen'])}-fach, "
                                         f"Spanne {_z(kl['spanne_atr'], '.1f')} ATR) – der Abwärtslauf brennt aus"))

    unter = [k.get("wort") and (f"Phase {k['wort']}" if not k.get("jung") else "jung")]
    if mz.get("wort"):
        unter.append(f"Market Profile {mz['wort']}")
    e = _ergebnis("titel", zustand, richtung, rand=rand, anlass=anlass, belege=belege, ende=ende, gegenseite=gegen,
                  kraft=kraft(df, idx, bewegung(zustand, richtung), k), unterzeile=" · ".join(x for x in unter if x), messung=mess)
    e["oben"], e["unten"] = oben, unten
    e["stufe"] = None if k.get("jung") else stufe_name(zustand, richtung, p)
    return e


# ── Gruppe ──────────────────────────────────────────────────────────────────────────────────────────────────────
