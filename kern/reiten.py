"""Der 10er und 20er (Gefechtsordnung Schritt 5, Micky 14./16.11.2026; Kullamägi führt).

Eine Quelle für zwei Fragen:
  ungleichgewicht(df)  Reitet der Kurs? Aufwärts, wenn der Schluss über dem steigenden 10er oder 20er liegt
                       (steigend = höher als vor einer Woche); abwärts gespiegelt. Der Kasten „Ungleichgewicht“.
  nachgezogen(...)     Der Stopp nach dem Kauf: bis Tag 3 der Anfangsstopp; danach folgt er der Linie, an der der
                       Kurs reitet – dem 10er, solange seit Tag 3 kein Schluss darunter lag, sonst dem 20er (Wechsel nur
                       von 10 auf 20). Er steigt nur (short: fällt nur), ein Schluss jenseits der Linie heißt raus. Mauer
                       (höchstens 3 % über dem Kurs), Kraft ohne Weg am oberen Rand und Kauf-Klimax ziehen ihn sofort
                       unter das Tief des Tages, an dem das Zeichen kam (Stopp im Markt); short gespiegelt.
"""
import numpy as np
import pandas as pd

from masse import WOCHE  # noqa: E402

GD10 = 10                   # schnelle Titel reiten am 10er (Kullamägi)
GD20 = 20                   # sonst am 20er
NACHZIEHEN_AB_TAG = 3       # bis Tag 3 nach dem Kauf gilt der Anfangsstopp (Kullamägi: Teilgewinn Tag 3–5)


def linien(df):
    """10er und 20er als Reihen der Schlusskurse."""
    c = df["Close"].astype(float)
    return c.rolling(GD10).mean(), c.rolling(GD20).mean()


def ungleichgewicht(df):
    """→ {richtung: "aufwärts"|"abwärts", linie: "10er"|"20er", wert} oder None (Kurs reitet an keiner Linie)."""
    if df is None or len(df) < GD20 + WOCHE:
        return None
    g10, g20 = linien(df)
    c = float(df["Close"].iloc[-1])
    for name, g in (("10er", g10), ("20er", g20)):
        jetzt, vor = float(g.iloc[-1]), float(g.iloc[-1 - WOCHE])
        if c > jetzt and jetzt > vor:
            return {"richtung": "aufwärts", "linie": name, "wert": jetzt}
    for name, g in (("10er", g10), ("20er", g20)):
        jetzt, vor = float(g.iloc[-1]), float(g.iloc[-1 - WOCHE])
        if c < jetzt and jetzt < vor:
            return {"richtung": "abwärts", "linie": name, "wert": jetzt}
    return None


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


def ende_zeichen(df, seite="long", messung=None, profil=None, zone=None):
    """Die drei Ende-Zeichen, wie der Zustand sie misst (auktion): Mauer höchstens MAUER_NAH % über dem Kurs (short:
    Stütze darunter), Kraft ohne Weg am oberen (unteren) Rand, Kauf-Klimax (Verkaufs-Klimax). → [(art, tag)].
    messung: auktion-Messung des Titels, wenn sie vorliegt; sonst rechnet die Funktion selbst."""
    import auktion
    lang = seite != "short"
    aus = []
    m = messung or {}
    if not messung:
        import vcp_zone
        z = zone or vcp_zone.zone(df)
        if z.get("zone"):
            kw = auktion.kraft_ohne_weg(df, z["oben"], z["unten"])
            if kw:
                m["kraft_ohne_weg"] = kw
        kl = auktion.klimax_tag(df)
        if kl:
            m["klimax"] = kl
    kw = m.get("kraft_ohne_weg")
    if kw and kw["rand"] == ("oben" if lang else "unten"):
        aus.append(("Kraft ohne Weg", kw["tag"]))
    kl = m.get("klimax")
    if kl and kl["art"] == ("Kauf-Klimax" if lang else "Verkaufs-Klimax"):
        aus.append((kl["art"], kl["tag"]))
    if profil is None and not messung:
        try:
            import volumenprofil
            profil = volumenprofil.verankert(df)
        except Exception:  # noqa: BLE001
            profil = None
    knoten = (profil or {}).get("mauer" if lang else "stuetze")
    if knoten:
        c = df["Close"].to_numpy(float)
        grenze = knoten[0] if lang else knoten[1]
        nah = (c >= grenze * (1 - auktion.MAUER_NAH / 100)) if lang else (c <= grenze * (1 + auktion.MAUER_NAH / 100))
        if nah[-1]:                            # seit wann der Kurs vor der Mauer steht
            i = len(nah) - 1
            while i > 0 and nah[i - 1]:
                i -= 1
            aus.append(("Mauer" if lang else "Stütze", df.index[i]))
    return aus
