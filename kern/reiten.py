"""Der nachgezogene Stopp und die Reibung nach dem Kauf (Gefechtsordnung Schritt 5, Micky 14./16.11.2026; Kullamägi
führt beim 10er und 20er; seit 23.11.2026 auch die Klimax, vorher in der Zustandsmaschine).

  nachgezogen(...)     Der Stopp nach dem Kauf nach Livermore (Micky 25.11.2026, vorher 10er/20er nach Kullamägi): er
                       folgt Livermores Pivotal Points unten (¼ ATR darunter), raus bei Regel 10b, Gefahrensignal 10e
                       zieht ihn eng; der 20er bleibt als Notbremse ab Tag 3. Short gespiegelt.
  ende_zeichen(...)    Mauer, Kraft ohne Weg und Klimax – seit 25.11.2026 nur noch Zeichen (sie ziehen den Stopp nicht).
"""
import numpy as np
import pandas as pd

from masse import ATR_N, LAGE_MITTE, VOL_MIN_TAGE  # noqa: E402

GD20 = 20                   # Notbremse nach dem Kauf: Schluss jenseits des 20er (Micky 25.11.2026)
KLIMAX_VOL, KLIMAX_SPANNE, KLIMAX_TAGE = 2.0, 1.5, 15   # Klimax: Volumen 2-fach, Spanne 1,5 ATR, letzte 15 Tage
KLIMAX_EXTREM_TAGE = 59     # Klimax: Tief bzw. Hoch der letzten 60 Tage (Tag selbst + 59)
MAUER_NAH = 3.0             # Mauer: Kurs höchstens 3 % vor dem Knoten (short: Stütze)
NACHZIEHEN_AB_TAG = 3       # die Notbremse am 20er greift ab Tag 3 nach dem Kauf


def nachgezogen(df, kauf_tag, einstieg, anfang, seite="long"):
    """Nachgezogener Stopp einer Position nach Livermore (Micky 25.11.2026) → {stopp, linie, regel, raus, raus_grund,
    tag_nr, enger: {art, tag, stopp} oder None}.
      Stopp      der Anfangsstopp (Stopp des Setups); jede Reaktion nach dem Kauf, die Livermore als Pivotal Point unten
                 einträgt, hebt ihn auf ¼ ATR darunter (short: Pivotal Point oben, ¼ ATR darüber) – er steigt nur.
      raus       Schluss jenseits des Stopps · Regel 10b nach dem Kauf: die Reaktion fällt 1 ATR unter das letzte
                 Reaktionstief, der Aufwärtstrend ist vorbei (short: 10d) · Notbremse ab Tag 3: Schluss unter dem 20er
                 (short: darüber) – falls der Lauf steil ist und der nächste Pivotal Point weit weg liegt.
      enger      Gefahrensignal nach dem Kauf (Regel 10e, short 10f): die Erholung stockte knapp unter dem Pivotal Point
                 – Stopp eng unter das Tief jenes Tages (short: über das Hoch); überholt, sobald der Kurs danach ein neues
                 Hoch macht (short: Tief)."""
    import livermore
    import vcp_zone
    from tiefe import STOPP_ATR
    if df is None or not len(df):
        return None
    df = df.dropna(subset=["High", "Low", "Close"])
    lang = seite != "short"
    kauf_i = int(df.index.searchsorted(pd.Timestamp(kauf_tag))) if kauf_tag is not None else len(df) - 1
    tag_nr = len(df) - 1 - kauf_i
    c = df["Close"].astype(float).to_numpy()
    a = vcp_zone.atr(df).to_numpy(float)
    nb = livermore.notizbuch(df) or {"pivotal": [], "ereignisse": []}
    aus = {"stopp": anfang, "linie": None, "regel": "Anfangsstopp (Stopp des Setups)", "raus": False, "raus_grund": "",
           "tag_nr": tag_nr, "enger": None}
    if anfang is None:
        return aus
    for p_ in nb["pivotal"]:                   # Livermores Pivotal Points nach dem Kauf heben den Stopp
        if p_["art"] != ("tief" if lang else "hoch") or p_["i"] < kauf_i or not a[p_["i"]] == a[p_["i"]]:
            continue
        kand = p_["preis"] - STOPP_ATR * a[p_["i"]] if lang else p_["preis"] + STOPP_ATR * a[p_["i"]]
        if (kand > aus["stopp"]) if lang else (kand < aus["stopp"]):
            aus.update(stopp=float(kand), linie="Livermore",
                       regel=f"¼ ATR {'unter' if lang else 'über'} Livermores Pivotal Point {'unten' if lang else 'oben'} "
                             f"{p_['preis']:.2f} ({p_['tag']:%d.%m.})")
    seit_kauf = [(t_, k_, w_) for t_, k_, w_ in nb["ereignisse"] if df.index.searchsorted(t_) > kauf_i]
    vorbei = next((x for x in seit_kauf if x[1] == ("auf_vorbei" if lang else "ab_vorbei")), None)
    gefahr = [x for x in seit_kauf if x[1] == ("gefahr_auf" if lang else "gefahr_ab")]
    g20 = df["Close"].astype(float).rolling(GD20).mean().to_numpy()
    if (c[-1] < aus["stopp"]) if lang else (c[-1] > aus["stopp"]):
        aus.update(raus=True, raus_grund=f"Schluss {'unter' if lang else 'über'} dem Stopp {aus['stopp']:.2f} ({aus['regel']})")
    elif vorbei:
        aus.update(raus=True, raus_grund=f"{livermore.EREIGNIS[vorbei[1]]} am {vorbei[0]:%d.%m.} bei {vorbei[2]:.2f}")
    elif tag_nr >= NACHZIEHEN_AB_TAG and g20[-1] == g20[-1] and ((c[-1] < g20[-1]) if lang else (c[-1] > g20[-1])):
        aus.update(raus=True, raus_grund=f"Notbremse: Schluss {'unter' if lang else 'über'} dem 20er {g20[-1]:.2f}")
    h_, l_ = df["High"].to_numpy(float), df["Low"].to_numpy(float)
    for t_, k_, _ in gefahr:                   # Gefahrensignal: Stopp im Markt eng an das Extrem jenes Tages – bis der
        j = int(df.index.searchsorted(t_))     # Kurs danach ein neues Hoch (short: Tief) macht, dann ist es überholt
        if (h_[j + 1:].max(initial=-np.inf) > h_[:j + 1].max()) if lang else (l_[j + 1:].min(initial=np.inf) < l_[:j + 1].min()):
            continue
        eng = float(df.loc[t_, "Low"] if lang else df.loc[t_, "High"])
        if (eng > aus["stopp"]) if lang else (eng < aus["stopp"]):
            if not aus["enger"] or ((eng > aus["enger"]["stopp"]) if lang else (eng < aus["enger"]["stopp"])):
                aus["enger"] = {"art": "Gefahrensignal (Regel " + ("10e" if lang else "10f") + ")", "tag": t_, "stopp": eng}
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
