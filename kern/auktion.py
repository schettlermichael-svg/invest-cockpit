"""Der Code für Balance und Ungleichgewicht (Micky 13.11.2026) – eine Zustandsmaschine für Titel, Gruppe und Markt.

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

ZUSTAENDE = ("Balance", "Test am Rand", "abgelehnt", "angenommen", "Ungleichgewicht", "Ende des Laufs")
# Farben aus dem Bild der Zustände: grau = Balance, rot = Ungleichgewicht entsteht/läuft, grün = zurück ins Gleichgewicht
FARBE = {"Balance": "#8B949E", "Test am Rand": "#8B949E", "abgelehnt": "#3FB950", "angenommen": "#F85149",
         "Ungleichgewicht": "#F85149", "Ende des Laufs": "#3FB950", "Anlass": "#A371F7"}
KRAEFTE = ("Gegner antwortet", "Antrieb erlischt", "Wert akzeptiert")

FRISCH = 10            # abgelehnt/angenommen: höchstens 10 Handelstage her (danach Ungleichgewicht bzw. zurück in der Balance)
RAND_PCT = 3.0         # Test am Rand: Kurs höchstens 3 % vom Rand
KOW_VOL, KOW_SPANNE, KOW_TAGE = 1.5, 0.7, 10
EXZESS_ATR, FLACH_PCT = 0.15, 0.1    # Exzess: äußerste Kerze mindestens 15 % der Tagesschwankung (ATR) vor der nächsten
KLIMAX_VOL, KLIMAX_SPANNE, KLIMAX_TAGE = 2.0, 1.5, 15
MAUER_NAH = 3.0        # Gegner antwortet: Kurs höchstens 3 % vor Mauer bzw. Stütze
EIGEN_PCT = 5.0        # eigen: RS-Linie in 20 Tagen mindestens 5 % in Laufrichtung; geliehen: höchstens 1 %
PFEIL = {"aufwärts": "↑", "abwärts": "↓", None: ""}


def _z(x, f=".2f"):
    return format(x, f).replace(".", ",")


def _d(t):
    return f"{pd.Timestamp(t):%d.%m.}"


def _ergebnis(ebene, zustand, richtung=None, **kw):
    e = {"ebene": ebene, "zustand": zustand, "richtung": richtung, "rand": None, "anlass": [], "belege": [],
         "kraft": None, "ende": [], "gegenseite": [], "unterzeile": "", "messung": {}}
    e.update(kw)
    return e


def wort(e):
    """„Ungleichgewicht ↑“, „Test am Rand (oben)“ …"""
    if not e:
        return ""
    w = e["zustand"]
    if e.get("richtung") and w in ("abgelehnt", "angenommen", "Ungleichgewicht", "Ende des Laufs"):
        w += " " + PFEIL[e["richtung"]]
    if w == "Test am Rand" and e.get("rand"):
        w += f" ({e['rand']})"
    return w


def farbe(e):
    return FARBE.get((e or {}).get("zustand"), "#8B949E")


# ── Messungen ───────────────────────────────────────────────────────────────────────────────────────────────────
def _atr(df, n=14):
    h, l, c = (df[x].to_numpy(float) for x in ("High", "Low", "Close"))
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return pd.Series(np.r_[np.nan, tr]).rolling(n).mean().to_numpy()


def kraft_ohne_weg(df, oben, unten):
    """Letzter Tag mit viel Volumen und wenig Weg am Rand der Zone → {tag, rand, volumen, spanne_atr} oder None."""
    if len(df) < 60 or not oben or not unten:
        return None
    h, l, c, v = (df[x].to_numpy(float) for x in ("High", "Low", "Close", "Volume"))
    v50 = pd.Series(v).rolling(50, min_periods=20).mean().shift().to_numpy()
    a = _atr(df)
    for i in range(len(df) - 1, len(df) - 1 - KOW_TAGE, -1):
        if not (v50[i] > 0 and a[i] > 0) or v[i] < KOW_VOL * v50[i] or h[i] - l[i] >= KOW_SPANNE * a[i]:
            continue
        if not unten <= c[i] <= oben:
            continue
        rand = "oben" if h[i] >= oben * (1 - RAND_PCT / 100) else "unten" if l[i] <= unten * (1 + RAND_PCT / 100) else None
        if rand:
            return {"tag": df.index[i], "rand": rand, "volumen": v[i] / v50[i], "spanne_atr": (h[i] - l[i]) / a[i]}
    return None


def klimax_tag(df):
    """Verkaufs-Klimax am Boden bzw. Kauf-Klimax am Hoch in den letzten 15 Tagen → {tag, art, volumen, spanne_atr}."""
    if len(df) < 70:
        return None
    h, l, c, v = (df[x].to_numpy(float) for x in ("High", "Low", "Close", "Volume"))
    v50 = pd.Series(v).rolling(50, min_periods=20).mean().shift().to_numpy()
    a = _atr(df)
    for i in range(len(df) - 1, len(df) - 1 - KLIMAX_TAGE, -1):
        sp = h[i] - l[i]
        if not (v50[i] > 0 and a[i] > 0 and sp > 0) or v[i] < KLIMAX_VOL * v50[i] or sp < KLIMAX_SPANNE * a[i]:
            continue
        lage = (c[i] - l[i]) / sp
        if l[i] <= l[i - 59:i + 1].min() and lage >= 0.5:
            return {"tag": df.index[i], "art": "Verkaufs-Klimax", "volumen": v[i] / v50[i], "spanne_atr": sp / a[i]}
        if h[i] >= h[i - 59:i + 1].max() and lage <= 0.5:
            return {"tag": df.index[i], "art": "Kauf-Klimax", "volumen": v[i] / v50[i], "spanne_atr": sp / a[i]}
    return None


def exzess(df, roh30):
    """Kante am Hoch und am Tief der letzten 20 Tage aus den 30-Minuten-Kerzen → {oben: {...}, unten: {...}}."""
    if roh30 is None or len(df) < 20:
        return {}
    aus = {}
    a = _atr(df)[-1]
    atr_pct = a / float(df["Close"].iloc[-1]) * 100 if a == a else 2.0
    t = df.iloc[-20:]
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
    vor = v[max(0, i - 50):i]
    if len(vor) < 20 or not np.nanmean(vor) > 0:
        return {"wochen": zone.get("wochen"), "volumen": None}
    return {"wochen": zone.get("wochen"), "volumen": float(np.nanmean(v[i:]) / np.nanmean(vor))}


def _rs20(df, idx):
    try:
        c = df["Close"]
        i = idx["Close"].reindex(c.index).ffill()
        if len(c) < 22 or not i.iloc[-21] > 0:
            return None
        t = (c.iloc[-1] / c.iloc[-21] - 1) * 100
        m = (i.iloc[-1] / i.iloc[-21] - 1) * 100
        rs = ((c.iloc[-1] / i.iloc[-1]) / (c.iloc[-21] / i.iloc[-21]) - 1) * 100
        return t, m, rs
    except Exception:  # noqa: BLE001
        return None


def bewegung(zustand, richtung):
    """Richtung, in die sich der Kurs bewegt: nach einer Ablehnung gegen den abgelehnten Ausbruch."""
    if zustand == "abgelehnt" and richtung:
        return "abwärts" if richtung == "aufwärts" else "aufwärts"
    return richtung


def kraft(df, idx, richtung, k=None):
    """Eigen oder geliehen: trägt der Titel die Bewegung selbst oder trägt ihn der Markt?"""
    r = _rs20(df, idx) if idx is not None else None
    if not r:
        return None
    t, m, rs = r
    rel = (k or {}).get("relativ") or {}
    zahl = f"Titel {_z(t, '+.1f')} %, S&P 500 {_z(m, '+.1f')} %, RS-Linie {_z(rs, '+.1f')} % (20 Tage)"
    auf = richtung == "aufwärts" if richtung else t >= 0     # ohne Laufrichtung (Balance): die Richtung des Kurses
    if (auf and rs >= EIGEN_PCT) or (not auf and rs <= -EIGEN_PCT):
        art = "eigen"
    elif (auf and t > 0 and rs <= 1) or (not auf and t < 0 and rs >= -1):
        art = "geliehen"
    else:
        art = "gemischt"
    if auf and rel.get("staerke"):
        art, zahl = "eigen", zahl + " · Stärke in der Schwäche"
    if not auf and rel.get("schwaeche"):
        art, zahl = "eigen", zahl + " · Schwäche in der Stärke"
    text = {"eigen": "eigene Kraft", "geliehen": "geliehen vom Markt", "gemischt": "mit dem Markt"}[art]
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
        return 10 ** 6


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

    # Anlass
    for x in zs:
        if x["art"] == "ereignis" and not x["text"].startswith("Market Profile an der Schwelle"):
            anlass.append(f"Information: {x['text']}")
            break
    if not anlass and zahltag is not None and _seit(df, zahltag) <= FRISCH:
        anlass.append(f"Information: Zahlen am {_d(zahltag)}")
    for vor in ("Spring", "Volumen trocknet aus", "Einquetschung", "3 Wochen eng"):
        x = hat(vor)
        if x:
            anlass.append(f"Verteidiger leer: {x['text']}")
    fa = next((t for t in texte if "Fehlausbruch" in t), None)
    if fa or hat("Schluss unter dem Tief der") or hat("Upthrust"):
        anlass.append("Zwang: gefangene Käufer über dem Rand")

    # Messungen
    if oben and unten:
        kow = kraft_ohne_weg(df, oben, unten)
        if kow:
            mess["kraft_ohne_weg"] = kow
            wer = "Verkäufer schlucken die Nachfrage" if kow["rand"] == "oben" else "Käufer schlucken das Angebot"
            belege.append(("Test am Rand", f"Kraft ohne Weg am {_d(kow['tag'])}: Volumen {_z(kow['volumen'])}-fach, "
                                           f"Spanne {_z(kow['spanne_atr'], '.1f')} ATR am {kow['rand']}en Rand – {wer}"))
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
    nachher = []                                 # Belege, die keinen Zustand setzen (Rücktest, Fortsetzung)
    scanner = bool(zone and zone.get("zone"))

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
            ereignisse.append((s_["tag"], "angenommen", ri, f"Market Profile: {name} {s_['dir']} am {_d(s_['tag'])} – "
                                                            "Tageswert ganz außerhalb der Wertzone"))
        elif s_["art"] == "R" and aktiv and aktiv["dir"] == s_["dir"]:
            nachher.append(("angenommen", f"Rücktest hält am {_d(s_['tag'])} (Market Profile R)"))
        elif s_["art"] in ("F", "B") and aktiv and aktiv["dir"] == s_["dir"]:
            nachher.append(("Ungleichgewicht", f"Market Profile: {'Fortsetzung' if s_['art'] == 'F' else 'Wert gewandert'} "
                                               f"{s_['dir']} am {_d(s_['tag'])}"))
    for vor, zst, ri in (("Spring", "abgelehnt", "abwärts"), ("Upthrust", "abgelehnt", "aufwärts"),
                         ("Schluss unter dem Tief der", "angenommen", "abwärts"),
                         ("Schluss über dem Hoch der Verteilung", "angenommen", "aufwärts")):
        x = hat(vor)
        if x:
            tag = x.get("tag") or _tag_im_text(x["text"], df) or df.index[-1]
            ereignisse.append((pd.Timestamp(tag), zst, ri, x["text"]))
    ereignisse = [e_ for e_ in ereignisse if _seit(df, e_[0]) <= FRISCH]
    ereignisse.sort(key=lambda e_: pd.Timestamp(e_[0]))
    zustand = richtung = rand = None
    if ereignisse:
        _, zustand, richtung, entscheid = ereignisse[-1]
        mess["entscheid"] = entscheid.split(":")[0].split(" am ")[0][:40]
        for _, zst, ri, text in ereignisse[-3:]:          # die drei jüngsten, das jüngste zuletzt
            belege.append((zst, text))
    for zst, text in nachher[-2:]:
        if (zst == "angenommen" and zustand != "angenommen") or (zst == "Balance" and zustand):
            continue
        belege.append((zst, text))
    if zustand == "abgelehnt" and oben and unten:
        ziel = unten if richtung == "aufwärts" else oben
        weg = (ziel / c - 1) * 100
        gegen.append(f"anderer Rand {_z(ziel)} $ " + (f"({_z(weg, '+.1f')} %)" if (weg < 0) == (richtung == "aufwärts")
                                                      else "schon erreicht"))

    # 3. Balance oder Test am Rand: der Kurs steht in der Zone
    in_zone = bool(zone and zone.get("zone") and unten <= c <= oben * 1.005)
    if not zustand and (in_zone or (p in (1, 3) and oben and unten and unten <= c <= oben)
                        or (p in (0, None) and mz.get("wort", "").startswith(("Balance", "an der Schwelle")))):
        zustand = "Balance"
        if oben and c >= oben * (1 - RAND_PCT / 100):
            zustand, rand = "Test am Rand", "oben"
        elif unten and c <= unten * (1 + RAND_PCT / 100):
            zustand, rand = "Test am Rand", "unten"
        if mz.get("wort", "").startswith("an der Schwelle"):
            zustand, rand = "Test am Rand", "oben" if mz.get("dir") == "↑" else "unten"
            belege.append(("Test am Rand", f"Market Profile: {mz['wort']}"))
        if oben and unten:
            belege.insert(0, ("Balance", f"{rahmen}: {_z(unten)}–{_z(oben)} $, Kurs {_z((c / oben - 1) * 100, '+.1f')} % "
                                         f"zum oberen Rand"))

    # 4. Ungleichgewicht oder Ende des Laufs
    if not zustand:
        auf = p == 2 or (p in (0, None) and ((k.get("dow_tag") or {}).get("struktur") == "aufwärts"))
        ab = p == 4 or (p in (0, None) and ((k.get("dow_tag") or {}).get("struktur") == "abwärts"))
        if auf or ab:
            zustand, richtung = "Ungleichgewicht", "aufwärts" if auf else "abwärts"
            belege.append(("Ungleichgewicht", f"Phase {p} ({'Aufwärts' if auf else 'Abwärts'})" if p in (2, 4) else
                           f"Dow-Struktur {'aufwärts' if auf else 'abwärts'}"))
        else:
            zustand = "Balance"
            if oben and unten:
                belege.insert(0, ("Balance", f"{rahmen}: {_z(unten)}–{_z(oben)} $"))

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
                        f"Spanne {_z(kw['spanne_atr'], '.1f')} ATR)")
        if k.get("ziel") == (3 if auf else 1):
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
        if mz.get("wort", "").startswith("Balance") and st and st[-1].get("wochen", 0) >= 3 \
                and st[-1].get("herkunft") == ("↑" if auf else "↓"):
            ende.append(f"Wert akzeptiert: neue Wertzone seit {st[-1]['wochen']} Wochen auf der neuen Höhe")
        if ende and zustand == "Ungleichgewicht":
            zustand = "Ende des Laufs"

    # Wer ist am Rand stärker (Struktur und Volumen)
    st_ = [x for x in zs if x["seite"] == "stärke" and x["art"] in ("struktur", "volumen")]
    sw_ = [x for x in zs if x["seite"] == "schwäche" and x["art"] in ("struktur", "volumen")]
    gs, gw = sum(x["gewicht"] for x in st_), sum(x["gewicht"] for x in sw_)
    if st_ or sw_:
        wer = "Käufer stärker" if gs > gw else "Verkäufer stärker" if gw > gs else "gleichauf"
        schon = {b for _, b in belege} | {a_.split(": ", 1)[-1] for a_ in anlass}
        neu = [x["text"] for x in (st_ + sw_) if x["text"] not in schon][:3]
        belege.append(("Test am Rand" if zustand in ("Balance", "Test am Rand") else zustand,
                       f"{wer} (Gewicht {gs} gegen {gw})" + (": " + "; ".join(neu) if neu else "")))
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
        else:
            belege.append(("Test am Rand", f"Exzess am {'Hoch' if seite == 'oben' else 'Tief'} {_z(x['preis'])} $ am {_d(x['tag'])} "
                           f"(äußerste 30-Minuten-Kerze {_z(x['abstand'], '.1f')} % vor der nächsten) – Auktion dort beendet, Rand verteidigt"))
    if kl and kl["art"] == "Verkaufs-Klimax" and zustand != "Ende des Laufs":
        belege.append(("Ende des Laufs", f"Verkaufs-Klimax am {_d(kl['tag'])} (Volumen {_z(kl['volumen'])}-fach, "
                                         f"Spanne {_z(kl['spanne_atr'], '.1f')} ATR) – der Abwärtslauf brennt aus"))

    unter = [k.get("wort") and (f"Phase {k['wort']}" if not k.get("jung") else "jung")]
    if mz.get("wort"):
        unter.append(f"Market Profile {mz['wort']}")
    e = _ergebnis("titel", zustand, richtung, rand=rand, anlass=anlass, belege=belege, ende=ende, gegenseite=gegen,
                  kraft=kraft(df, idx, bewegung(zustand, richtung), k), unterzeile=" · ".join(x for x in unter if x), messung=mess)
    e["oben"], e["unten"] = oben, unten
    return e


def speicherbar(e):
    """Für JSON: Zeitstempel als Datum, Zahlen als float, Tupel als Listen."""
    if isinstance(e, dict):
        return {k: speicherbar(v) for k, v in e.items()}
    if isinstance(e, (list, tuple)):
        return [speicherbar(v) for v in e]
    if isinstance(e, pd.Timestamp):
        return f"{e:%Y-%m-%d}"
    if isinstance(e, (np.floating, np.integer)):
        return e.item()
    return e


def fuer_titel(tk, df, k, idx=None, mp=None, br=None, zone=None, gewinne=None):
    """titel() mit Verankerung (Zahltag, Profil) und 30-Minuten-Kerzen – für Kartentisch und Titelseite gleich."""
    zahltag = profil = roh = None
    try:
        import avwap
        import volumenprofil
        zahltag = avwap.zahlentag(df, gewinne) if gewinne is not None else None
        profil = volumenprofil.verankert(df, zahltag, (zone.get("start_t") or zone.get("start")) if zone and zone.get("zone")
                                         else None, avwap.wert_beginn(mp))
    except Exception:  # noqa: BLE001
        pass
    try:
        import erkennung
        roh = erkennung._ROH.get(tk)
    except Exception:  # noqa: BLE001
        pass
    return titel(df, k, idx, mp, br, zone, profil, zahltag, roh)


# ── Gruppe ──────────────────────────────────────────────────────────────────────────────────────────────────────
def gruppe(g):
    """Zustand einer Gruppe (Sektor, Branche, Thema) aus der Rotationskarte, der Breite und den Anführern."""
    if not g:
        return None
    f, f4 = g.get("feld"), g.get("feld_vor4")
    br, br4 = g.get("breite"), g.get("breite_vor4")
    zu = g.get("zufluss")
    belege = [("Balance" if f not in ("Führend", "Abgehängt") else "Ungleichgewicht",
               f"Feld {f} seit {g.get('seit_wochen')} Wochen (vor 4 Wochen {f4}), RS-Stärke {_z(g.get('staerke', 0), '.1f')}, "
               f"Schwung {_z(g.get('schwung', 0), '.1f')}")]
    if br is not None:
        belege.append(("folgen die Schwestern", f"Breite: {_z(br, '.0f')} % über dem GD50 (vor 4 Wochen "
                                                f"{_z(br4, '.0f') if br4 is not None else '–'} %)"))
    if zu:
        belege.append(("Geldfluss", f"Zufluss {_z(zu)} (Volumen steigender ÷ fallender Tage, 50 Tage)"))
    anf = g.get("anfuehrer") or []
    if anf:
        belege.append(("Anführer bricht aus", "Anführer: " + ", ".join(anf) + (f" · Verfolger: {', '.join(g['verfolger'])}"
                                                                  if g.get("verfolger") else " · noch keine Verfolger")))
    steigt = br is not None and br4 is not None and br >= br4 + 10
    faellt = br is not None and br4 is not None and br <= br4 - 10
    ende, richtung = [], None
    if f4 == "Erstarkend" and f == "Abgehängt":
        z, richtung = "abgelehnt", "aufwärts"
    elif f == "Erstarkend":
        z, richtung = ("angenommen", "aufwärts") if steigt and (zu or 0) >= 1.1 else ("Test am Rand", None)
    elif f == "Führend":
        z, richtung = "Ungleichgewicht", "aufwärts"
        if faellt:
            z = "Ende des Laufs"
            ende.append(f"Antrieb erlischt: Breite wird schmal ({_z(br4, '.0f')} → {_z(br, '.0f')} %)")
    elif f == "Ermüdend":
        z, richtung = "Ende des Laufs", "aufwärts"
        ende.append("Antrieb erlischt: Feld Ermüdend (RS-Stärke hoch, Schwung fällt)")
    elif f == "Abgehängt" and steigt:
        z, richtung = "Test am Rand", None           # die Schwestern drehen, bevor die Rotationskarte es zeigt
    elif f == "Abgehängt":
        z, richtung = "Ungleichgewicht", "abwärts"
    else:
        z = "Balance"
    if abs(g.get("staerke", 100) - 100) <= 1 and abs(g.get("schwung", 100) - 100) <= 1 and z != "abgelehnt":
        z, richtung = "Balance", None
    e = _ergebnis("gruppe", z, richtung, belege=belege, ende=ende,
                  unterzeile=f"Feld {f}" + (" · stabil" if g.get("stabil") else ""))
    e["rand"] = "oben" if z == "Test am Rand" else None
    return e


# ── Markt ───────────────────────────────────────────────────────────────────────────────────────────────────────
def markt(r, p=None):
    """Ein Marktzustand aus O'Neil (Marktrichtung) und den Marktzonen der Lage (Unterzeile)."""
    if not r:
        return None
    zst = r.get("zustand")
    belege, ende, anlass = [], [], []
    dt = r.get("distributionstage") or {}
    dtt = " · ".join(f"{n} {d}" for n, d in dt.items())
    zone = (p or {}).get("zone")
    if zst == "Korrektur":
        v = r.get("versuch")
        g = r.get("gescheitert")
        if g and (not v or v[0] <= 1):
            z, ri = "abgelehnt", "aufwärts"
            belege.append(("abgelehnt", f"Erholungsversuch am {_d(g)} gescheitert: Schluss unter dem Tief des Versuchs"))
        elif v:
            z, ri = "Test am Rand", None
            belege.append(("Test am Rand", f"Erholungsversuch {v[1]} Tag {v[0]}" +
                           (" – Follow-Through ab Tag 4 möglich" if v[0] < 4 else " – wartet auf den Follow-Through-Day")))
        else:
            z, ri = "Ungleichgewicht", "abwärts"
            belege.append(("Ungleichgewicht", "Korrektur ohne Erholungsversuch"))
        if zone == "Kapitulation":
            ende.append("Antrieb erlischt: Kapitulation (VIX hoch, Breite unten)")
            if z == "Ungleichgewicht":
                z = "Ende des Laufs"
    else:
        f = r.get("ftd")
        if f and _seit_tage(f["tag"]) <= 14:
            z, ri = "angenommen", "aufwärts"
            belege.append(("angenommen", f"Follow-Through-Day am {_d(f['tag'])} ({f['index']}, Tag {f['tag_nr']}, "
                                         f"+{_z(f['plus'], '.1f')} %)"))
        else:
            z, ri = "Ungleichgewicht", "aufwärts"
            belege.append(("Ungleichgewicht", "Bestätigter Aufwärtstrend" if zst.startswith("Bestätigt") else zst))
        if zst == "Aufwärtstrend unter Druck":
            ende.append(f"Gegner antwortet: Abgabe am Rand – Distributionstage {dtt} in 5 Wochen")
        if zone in ("Überhitzung", "Topbildung"):
            ende.append(f"Antrieb erlischt: Marktzone {zone}")
        if ende and z == "Ungleichgewicht":
            z = "Ende des Laufs"
    belege.append(("Abgabe am Rand", f"Distributionstage {dtt} in 5 Wochen"))
    for n, w in (r.get("zonen") or {}).items():
        belege.append(("Balance", f"Wertzone {n}: {w}"))
    m = (p or {}).get("messwerte") or {}
    if m.get("breite") is not None:
        belege.append(("folgen die Schwestern", f"Breite {_z(m['breite'], '.0f')} % (4 Wochen {_z(m['breite_4w'], '+.0f')})"))
    unter = [zst] + ([f"Marktzone {zone} {p.get('pfeil', '')}".strip()] if zone else [])
    return _ergebnis("markt", z, ri, belege=belege, ende=ende, anlass=anlass, unterzeile=" · ".join(unter))


def _seit_tage(tag):
    return int(np.busday_count(pd.Timestamp(tag).date(), pd.Timestamp.today().date()))
