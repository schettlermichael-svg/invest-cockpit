"""Der nachgezogene Stopp und die Reibung nach dem Kauf (Gefechtsordnung Schritt 5, Micky 14./16.11.2026; Kullamägi
führt beim 10er und 20er; seit 23.11.2026 auch die Klimax, vorher in der Zustandsmaschine).

  nachgezogen(...)     Der Stopp nach dem Kauf: bis Tag 3 der Anfangsstopp; danach folgt er der Linie, an der der
                       Kurs reitet – dem 10er, solange seit Tag 3 kein Schluss darunter lag, sonst dem 20er (Wechsel nur
                       von 10 auf 20). Er steigt nur (short: fällt nur), ein Schluss jenseits der Linie heißt raus. Mauer
                       (höchstens 3 % über dem Kurs), Kraft ohne Weg am oberen Rand und Kauf-Klimax ziehen ihn sofort
                       unter das Tief des Tages, an dem das Zeichen kam (Stopp im Markt); short gespiegelt.
"""
import numpy as np
import pandas as pd

from masse import ATR_N, LAGE_MITTE, VOL_MIN_TAGE  # noqa: E402

GD10 = 10                   # schnelle Titel reiten am 10er (Kullamägi)
GD20 = 20                   # sonst am 20er
KLIMAX_VOL, KLIMAX_SPANNE, KLIMAX_TAGE = 2.0, 1.5, 15   # Klimax: Volumen 2-fach, Spanne 1,5 ATR, letzte 15 Tage
KLIMAX_EXTREM_TAGE = 59     # Klimax: Tief bzw. Hoch der letzten 60 Tage (Tag selbst + 59)
MAUER_NAH = 3.0             # Mauer: Kurs höchstens 3 % vor dem Knoten (short: Stütze)
NACHZIEHEN_AB_TAG = 3       # bis Tag 3 nach dem Kauf gilt der Anfangsstopp (der Stopp des Setups)


def linien(df):
    """10er und 20er als Reihen der Schlusskurse."""
    c = df["Close"].astype(float)
    return c.rolling(GD10).mean(), c.rolling(GD20).mean()




def nachgezogen(df, kauf_tag, einstieg, anfang, seite="long", ende=None):
    """Nachgezogener Stopp einer Position → {stopp, linie, regel, raus, tag_nr, enger: {art, tag, stopp} oder None}.
    ende: Ende-Zeichen [(art, tag)] (aus ende_zeichen) – sie ziehen den Stopp unter das Tief jenes Tages."""
    if df is None or not len(df):
        return None
    lang = seite != "short"
    seit = df[df.index >= pd.Timestamp(kauf_tag)] if kauf_tag is not None else df.iloc[-1:]
    tag_nr = len(seit) - 1
    c = df["Close"].astype(float)
    g10, g20 = linien(df)
    aus = {"stopp": anfang, "linie": None, "regel": "Anfangsstopp (bis Tag 3)", "raus": False, "tag_nr": tag_nr,
           "enger": None}
    if tag_nr >= NACHZIEHEN_AB_TAG and anfang:
        ab = seit.index[NACHZIEHEN_AB_TAG]
        teil = df.index >= ab
        cc, a10, a20 = c[teil].to_numpy(), g10[teil].to_numpy(), g20[teil].to_numpy()
        unter10 = np.nonzero((cc < a10) if lang else (cc > a10))[0]
        if len(unter10):                       # einmal jenseits des 10er: ab da gilt der 20er (nur von 10 auf 20)
            name, reihe = "20er", a20[unter10[0]:]
        else:
            name, reihe = "10er", a10
        reihe = reihe[~np.isnan(reihe)]
        if len(reihe):
            hoch = float(reihe.max() if lang else reihe.min())          # der Stopp steigt nur (short: fällt nur)
            stopp = max(anfang, hoch) if lang else min(anfang, hoch)
            raus = bool((cc[-1] < stopp) if lang else (cc[-1] > stopp))
            aus.update(stopp=stopp, linie=name, raus=raus,
                       regel=f"folgt dem {name} (Schluss {'darunter' if lang else 'darüber'} heißt raus)"
                       + ("" if stopp != anfang else " – noch unter dem Anfangsstopp, der gilt"))
    for art, tag in ende or []:                # Ende-Zeichen: Stopp im Markt unter das Tief jenes Tages
        if kauf_tag is not None and pd.Timestamp(tag) < pd.Timestamp(kauf_tag):
            continue
        zeile = df.loc[pd.Timestamp(tag)] if pd.Timestamp(tag) in df.index else None
        if zeile is None:
            continue
        eng = float(zeile["Low"] if lang else zeile["High"])
        if (eng > aus["stopp"]) if lang else (eng < aus["stopp"]):
            if not aus["enger"] or ((eng > aus["enger"]["stopp"]) if lang else (eng < aus["enger"]["stopp"])):
                aus["enger"] = {"art": art, "tag": pd.Timestamp(tag), "stopp": eng}
    return aus


def ende_zeichen(df, seite="long", profil=None, zone=None):
    """Die drei Ende-Zeichen (Reibung): Mauer höchstens MAUER_NAH % über dem Kurs (short: Stütze darunter), Kraft ohne
    Weg am oberen (unteren) Rand, Kauf-Klimax (Verkaufs-Klimax). → [(art, tag)]."""
    import vcp_zone
    import zeichen
    lang = seite != "short"
    aus = []
    z = zone or vcp_zone.zone(df)
    kw = zeichen.kraft_ohne_weg(df, oben=z["oben"], unten=z["unten"]) if z.get("zone") else None
    if kw and kw["rand"] == ("oben" if lang else "unten"):
        aus.append(("Kraft ohne Weg", kw["tag"]))
    kl = klimax_tag(df)
    if kl and kl["art"] == ("Kauf-Klimax" if lang else "Verkaufs-Klimax"):
        aus.append((kl["art"], kl["tag"]))
    if profil is None:
        try:
            import volumenprofil
            profil = volumenprofil.verankert(df)
        except Exception:  # noqa: BLE001
            profil = None
    knoten = (profil or {}).get("mauer" if lang else "stuetze")
    if knoten:
        c = df["Close"].to_numpy(float)
        grenze = knoten[0] if lang else knoten[1]
        nah = (c >= grenze * (1 - MAUER_NAH / 100)) if lang else (c <= grenze * (1 + MAUER_NAH / 100))
        if nah[-1]:                            # seit wann der Kurs vor der Mauer steht
            i = len(nah) - 1
            while i > 0 and nah[i - 1]:
                i -= 1
            aus.append(("Mauer" if lang else "Stütze", df.index[i]))
    return aus


def klimax_tag(df):
    """Verkaufs-Klimax am Boden bzw. Kauf-Klimax am Hoch in den letzten 15 Tagen → {tag, art, volumen, spanne_atr}."""
    if len(df) < 70:
        return None
    h, l, c, v = (df[x].to_numpy(float) for x in ("High", "Low", "Close", "Volume"))
    v50 = pd.Series(v).rolling(50, min_periods=VOL_MIN_TAGE).mean().shift().to_numpy()
    import atr as atr_
    a = atr_.reihe(df, ATR_N).to_numpy(float)
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
