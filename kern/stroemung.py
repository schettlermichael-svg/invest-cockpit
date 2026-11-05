"""Strömung in der Zone (03.11.2026): Zeichen am rechten Rand, bevor der Ausbruch sichtbar wird – je eine Ampel mit
Richtung (↑ für Long, ↓ für Short, → ohne Richtung). Keine Punktzahl, kein Filter.

Zone = die erkannte Base (Beginn bis heute), sonst die Base im Aufbau (seit dem Hoch), sonst die letzten 60 Tage.
Richtung gemessen an 2.768 Zonen aus 315 Titeln über 10 Jahre (20 Tage vor dem Ende: Kippen nach oben gegen
Auflösung, werkzeuge/messung_balance.py, nur Richtung, keine Erträge):
  Wertwanderung an   45 % vor Kippen nach oben gegen 14 % vor Auflösung  → zeigt die Richtung
  Steigende Tiefs    70 % gegen 40 %                                     → zeigt die Richtung
  Schlusslage oben   17 % gegen  6 %                                     → zeigt die Richtung, selten
  Enge               72 % gegen 91 %                                     → Druck, keine Richtung
  Volumen trocken    32 % gegen 28 %                                     → keine Richtung
Fußabdruck und RS-Linie: hier nicht gemessen (Fußabdruck geprüft gegen TradingView-Zählungen).
"""
import numpy as np

KURZ = 10                    # zwei Wochen am rechten Rand


def _z(x, st=2):
    """Zahl deutsch: 1234.5 -> 1.234,50"""
    return f"{x:,.{st}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _poc(h, l, c, v, a, b, unten, oben, fach=24):
    tp = (h[a:b + 1] + l[a:b + 1] + c[a:b + 1]) / 3
    kanten = np.linspace(unten, oben, fach + 1)
    i = np.clip(np.digitize(tp, kanten) - 1, 0, fach - 1)
    vol = np.bincount(i, weights=v[a:b + 1], minlength=fach)
    k = int(np.argmax(vol))
    return float((kanten[k] + kanten[k + 1]) / 2), float(kanten[1] - kanten[0])


def _clv(h, l, c, a, b):
    r = np.maximum(h[a:b + 1] - l[a:b + 1], 1e-9)
    return float(((c[a:b + 1] - l[a:b + 1]) / r).mean())


def stroemung(df, start, index=None, fuss=None):
    """Liefert Liste (Name, Ampel, Pfeil, Text) für die Zone ab start bis heute."""
    h, l, c, v = (df[x].to_numpy(float) for x in ("High", "Low", "Close", "Volume"))
    n = len(c)
    start = max(0, min(int(start), n - 1))
    if n - start < 2 * KURZ:
        start = max(0, n - 60)
    e = n - 1
    a = e - KURZ + 1
    zo, zu = float(h[start:].max()), float(l[start:].min())
    aus = []

    # Wertwanderung: POC der letzten zwei Wochen gegen POC der Zone
    p_zone, fach = _poc(h, l, c, v, start, e, zu, zo)
    p_kurz, _ = _poc(h, l, c, v, a, e, zu, zo)
    if p_kurz > p_zone + fach / 2:
        aus.append(("Wertwanderung", "grün", "↑", f"fairer Preis zieht nach oben: POC der Zone {_z(p_zone, 2)} $ → "
                                                  f"letzte 2 Wochen {_z(p_kurz, 2)} $"))
    elif p_kurz < p_zone - fach / 2:
        aus.append(("Wertwanderung", "rot", "↓", f"fairer Preis zieht nach unten: POC der Zone {_z(p_zone, 2)} $ → "
                                                 f"letzte 2 Wochen {_z(p_kurz, 2)} $"))
    else:
        aus.append(("Wertwanderung", "gelb", "→", f"fairer Preis bleibt: POC der Zone {_z(p_zone, 2)} $, letzte 2 Wochen {_z(p_kurz, 2)} $"))

    # Steigende Tiefs: Tiefs der letzten drei Zwei-Wochen-Abschnitte
    t3 = [float(l[max(start, e + 1 - KURZ * (k + 1)):e + 1 - KURZ * k].min()) for k in (2, 1, 0)
          if e + 1 - KURZ * k > max(start, e + 1 - KURZ * (k + 1))]
    if len(t3) == 3:
        txt = f"Tiefs {_z(t3[0], 2)} → {_z(t3[1], 2)} → {_z(t3[2], 2)} $"
        if t3[1] >= t3[0] * 0.99 and t3[2] >= t3[1] * 0.99 and t3[2] > t3[0] * 1.01:
            aus.append(("Steigende Tiefs", "grün", "↑", "Käufer kommen früher: " + txt))
        elif t3[1] <= t3[0] * 1.01 and t3[2] <= t3[1] * 1.01 and t3[2] < t3[0] * 0.99:
            aus.append(("Steigende Tiefs", "rot", "↓", "Tiefs fallen, Verkäufer drücken: " + txt))
        else:
            aus.append(("Steigende Tiefs", "gelb", "→", "Tiefs halten: " + txt))

    # Schlusslage: Lage des Schlusses in der Tagesspanne (0 = Tief, 1 = Hoch), zwei Wochen davor → letzte zwei Wochen
    jetzt = _clv(h, l, c, a, e)
    vorher = _clv(h, l, c, max(0, a - KURZ), a - 1) if a - KURZ >= 0 else None
    txt = (f"Schluss in der Tagesspanne {_z(vorher, 2)} → {_z(jetzt, 2)} (0 = am Tief, 1 = am Hoch)" if vorher is not None
           else f"Schluss in der Tagesspanne {_z(jetzt, 2)} (0 = am Tief, 1 = am Hoch)")
    if jetzt >= 0.6:
        aus.append(("Schlusslage", "grün", "↑", "Käufer behalten das letzte Wort: " + txt))
    elif jetzt <= 0.4:
        aus.append(("Schlusslage", "rot", "↓", "Verkäufer behalten das letzte Wort: " + txt))
    else:
        aus.append(("Schlusslage", "gelb", "→", txt))

    # Enge: Druck ohne Richtung
    eng = (h[a:].max() / l[a:].min() - 1) * 100
    ganz = (zo / zu - 1) * 100 if zu > 0 else 0
    verh = eng / ganz if ganz > 0 else 1
    aus.append(("Enge", "grün" if verh <= 1 / 3 else "gelb" if verh <= 0.5 else "grau", "◆",
                f"Spanne letzte 2 Wochen {_z(eng, 1)} % gegen {_z(ganz, 1)} % der Zone ({_z(verh, 2)}-fach) – Druck baut sich auf, "
                "zeigt aber keine Richtung (gemessen)"))

    # Volumen: ohne Richtung
    if a >= 50:
        vf = float(v[a:].mean() / v[a - 50:a].mean())
        aus.append(("Volumen", "grün" if vf <= 0.8 else "gelb" if vf <= 1.0 else "grau", "◆",
                    f"letzte 2 Wochen {_z(vf, 2)}-fach des 50-Tage-Schnitts – "
                    + ("ruhig" if vf <= 0.8 else "normal" if vf <= 1.0 else "lebhaft") + ", zeigt aber keine Richtung (gemessen)"))

    # Fußabdruck (Kauf- gegen Verkaufstage mit hohem Volumen)
    if fuss and fuss.get("verhaeltnis") is not None:
        k_, d_ = fuss["akk"], fuss["dist"]
        aus.append(("Fußabdruck", "grün" if k_ > d_ else "rot" if d_ > k_ else "gelb", "↑" if k_ > d_ else "↓" if d_ > k_ else "→",
                    f"{k_} Kauf- gegen {d_} Verkaufstage mit hohem Volumen in der Zone (Richtung hier nicht gemessen)"))

    # RS-Linie vor dem Kurs
    if index is not None:
        ic = index["Close"].reindex(df.index, method="ffill").to_numpy(float)
        rs = c / ic
        if n >= 60 and np.isfinite(rs[-60:]).all():
            rs_hoch = rs[-20:].max() >= np.nanmax(rs[max(0, n - 250):]) * 0.999
            kurs_hoch = h[-20:].max() >= h[max(0, n - 250):].max() * 0.999
            r_alt, r_neu = rs[-21], rs[-1]
            txt = f"RS-Linie 100 → {_z(r_neu * 100 / rs[-21], 1)} in 20 Tagen (Start = 100)"
            if rs_hoch and not kurs_hoch:
                aus.append(("RS-Linie", "grün", "↑", "RS-Linie auf 52-Wochen-Hoch vor dem Kurs – Fonds kaufen früher; " + txt))
            elif r_neu > r_alt * 1.02:
                aus.append(("RS-Linie", "grün", "↑", txt))
            elif r_neu < r_alt * 0.98:
                aus.append(("RS-Linie", "rot", "↓", txt))
            else:
                aus.append(("RS-Linie", "gelb", "→", txt))
    return aus


HILFE = {
    "Zustand der Zone": (
        "Was: der Zustand der Zone nach dem Market Profile.\n"
        "Balance: Tageswerte wechseln, der POC pendelt – die Front steht.\n"
        "An der Schwelle ↑/↓: mindestens 3 der letzten 5 Tageswerte in eine Richtung, keiner ganz dagegen, Tages-POC "
        "zieht mit, Kurs im oberen (unteren) Drittel des Wertbereichs – eine Seite rückt Graben um Graben vor.\n"
        "Ausbruch (Tag n): A oder F – die Front ist gebrochen. Umkehr (Tag n): U – nach einem gescheiterten Bruch dreht "
        "die Front in die Gegenrichtung.\n"
        "Bestätigt: B, der Wochenwert liegt außerhalb – neue Stellung bezogen.\n"
        "Gescheitert: Schluss zurück im Wertbereich der verlassenen Zone – der Durchbruch ist zurückgeschlagen."),
    "Tageswerte zum Vortag": (
        "Was: der Wertbereich jedes Tages (die 70 % der Handelszeit, in denen gehandelt wurde) gegen den des Vortags.\n"
        "▲ ganz höher: kein Überlappen, der Wert ist nach oben gewandert – Gelände genommen.\n"
        "△ überlappend höher: Ober- und Unterkante höher – Graben um Graben vor.\n"
        "▬ unverändert: innen oder außen gleich – die Front steht.\n"
        "▽ überlappend tiefer: beide Kanten tiefer – Rückzug Graben um Graben.\n"
        "▼ ganz tiefer: kein Überlappen nach unten – Gelände verloren.\n"
        "Pfeil: Richtung der letzten 5 Tage. Gelb ab 3 von 5 in eine Richtung (Schwelle)."),
    "Tages-POC (5 Tage)": (
        "Was: der Preis, an dem an einem Tag am längsten gehandelt wurde (Point of Control) – der faire Preis des Tages.\n"
        "Heute gegen vor 5 Tagen. Steigt er, verschieben die Käufer den fairen Preis nach oben – die Front rückt vor; "
        "fällt er, rücken die Verkäufer vor. Gelb ab 1 % Bewegung."),
    "Lage im Wertbereich der Zone": (
        "Was: wo der Schlusskurs im Wertbereich der Zone steht (Wert = 70 % der Zeit aller Wochen der Zone, POC = "
        "längster Handel, Rahmen = höchster und tiefster Kurs).\n"
        "Oberes Drittel oder darüber ↑: die Truppen stehen am vorderen Graben, Druck nach oben. Unteres Drittel oder "
        "darunter ↓: Druck nach unten. Mitte →: Balance."),
    "Tagesspannen": (
        "Was: die mittlere Spanne Hoch bis Tief in Prozent, letzte 5 Tage gegen die 20 davor.\n"
        "◆ enger (unter 80 %): Ruhe vor dem Sturm – Druck baut sich auf, ohne Richtung. → gleich oder weiter."),
    "Volumen": (
        "Was: das Volumen der letzten 5 Tage gegen den 50-Tage-Schnitt.\n"
        "◆ unter 0,8-fach: trocknet aus – das Angebot ist erschöpft, wenige wollen noch verkaufen (Druck ohne "
        "Richtung). Über 1,4-fach: große Hände sind aktiv – die Richtung zeigen Tageswerte und Fußabdruck."),
    "Verlassene Zone": (
        "Was: die Kante der Zone, aus der der Kurs ausgebrochen ist (long: VAH, short: VAL).\n"
        "Solange kein Schluss zurück im alten Wertbereich liegt, hält der Durchbruch. Ein Schluss dahinter ist S "
        "(gescheitert) und damit der Stopp."),
    "Fußabdruck": (
        "Was: Tage mit hohem Volumen in der Zone, nach oben (Kauftage, Akkumulation) gegen nach unten (Verkaufstage, "
        "Distribution) – das Gegenstück zu O'Neils Acc/Dis.\n"
        "↑ mehr Kauftage: Fonds bauen auf. ↓ mehr Verkaufstage: Fonds bauen ab."),
    "RS-Linie": (
        "Was: der Kurs geteilt durch den S&P 500 (relative Stärke), vor 20 Tagen = 100.\n"
        "↑ steigt: stärker als der Markt. Auf einem 52-Wochen-Hoch vor dem Kurs: Fonds kaufen früher (O'Neil). "
        "↓ fällt: schwächer als der Markt."),
}


def _worte_folge(auf, ab):
    if auf >= 3 and auf > ab:
        return "Käufer rücken vor"
    if ab >= 3 and ab > auf:
        return "Verkäufer rücken vor"
    return "die Front steht"


def stroemung_mp(a, df):
    """Strömung aus dem Market Profile (4.11.2026): Zustand der Zone und seine Belege – Tageswerte zum Vortag,
    Tages-POC, Lage im Wertbereich der Zone, Tagesspannen, Volumen, verlassene Zone mit Stopp, letzte Auslöser.
    Liefert Liste (Name, Ampel, Pfeil, Text) wie stroemung(); die Erklärung je Zeile steht in HILFE."""
    import marketprofile as mp
    tage, z, st = a["tage"], a["zustand"], a["stand"][-1]
    aus = []
    pf = {"↑": "↑", "↓": "↓", None: "→"}
    extra = [b for b in z["belege"] if b.startswith(("Ausbruch", "verlassene"))]
    aus.append(("Zustand der Zone", z["ampel"], pf[z["dir"]], " · ".join([z["wort"]] + extra)))
    folge = [t["bez"] for t in tage[-10:] if t["bez"]]
    letzte5 = folge[-mp.SCHWELLE_TAGE:]
    auf = sum(b in ("hoch", "ueber") for b in letzte5)
    ab = sum(b in ("tief", "unter") for b in letzte5)
    richtung = "↑" if auf > ab else "↓" if ab > auf else "→"
    aus.append(("Tageswerte zum Vortag", "gelb" if max(auf, ab) >= mp.SCHWELLE_MIN else "grau", richtung,
                " ".join(mp.ZEICHEN[b] for b in folge) + f" (10 Tage) · letzte 5: {auf}× höher, {ab}× tiefer – "
                + _worte_folge(auf, ab)))
    p0, p1 = tage[-1 - mp.SCHWELLE_TAGE]["poc"] if len(tage) > mp.SCHWELLE_TAGE else tage[0]["poc"], tage[-1]["poc"]
    wort = "fairer Preis steigt" if p1 > p0 * 1.01 else "fairer Preis fällt" if p1 < p0 * 0.99 else "fairer Preis bleibt"
    aus.append(("Tages-POC (5 Tage)", "gelb" if abs(p1 / p0 - 1) > 0.01 else "grau",
                "↑" if p1 > p0 * 1.01 else "↓" if p1 < p0 * 0.99 else "→",
                f"{_z(p0)} → {_z(p1)} $ ({(p1 / p0 - 1) * 100:+.1f} %)".replace(".", ",") + f" – {wort}"))
    k = float(df["Close"].iloc[-1])
    lage = (k - st["val"]) / max(st["vah"] - st["val"], 1e-9)
    wort = ("über dem Wert: Druck nach oben" if lage > 1 else "oberes Drittel: Druck nach oben" if lage >= 2 / 3 else
            "unter dem Wert: Druck nach unten" if lage < 0 else "unteres Drittel: Druck nach unten" if lage <= 1 / 3
            else "Mitte: Balance")
    aus.append(("Lage im Wertbereich der Zone", "gelb" if lage >= 2 / 3 or lage <= 1 / 3 else "grau",
                "↑" if lage >= 2 / 3 else "↓" if lage <= 1 / 3 else "→",
                f"Kurs {_z(k)} $ · Wert {_z(st['val'])}–{_z(st['vah'])} $ · POC {_z(st['poc'])} $ · Rahmen "
                f"{_z(st['tief'])}–{_z(st['hoch'])} $ · Zone {st['wochen']} Woche{'n' if st['wochen'] != 1 else ''} – {wort}"))
    h, l, c, v = (df[x].to_numpy(float) for x in ("High", "Low", "Close", "Volume"))
    if len(c) >= 50:
        sp = (h - l) / c * 100
        vorher, heute = float(sp[-25:-5].mean()), float(sp[-5:].mean())
        eng = heute < 0.8 * vorher
        aus.append(("Tagesspannen", "gelb" if eng else "grau", "◆" if eng else "→",
                    f"vorher {_z(vorher, 1)} % → heute {_z(heute, 1)} % (Schnitt 20 Tage → 5 Tage) – "
                    + ("enger: Ruhe vor dem Sturm" if eng else "weiter: Unruhe" if heute > 1.2 * vorher else "unverändert")))
        s50 = float(v[-50:].mean())
        x = float(v[-5:].mean()) / s50 if s50 else 1.0
        aus.append(("Volumen", "gelb" if x < 0.8 else "grau", "◆" if x < 0.8 else "→",
                    f"{_z(x, 2)}-fach des 50-Tage-Schnitts (5 Tage) – "
                    + ("trocknet aus: Angebot erschöpft" if x < 0.8 else "erhöht: große Hände aktiv" if x > 1.4
                       else "normal")))
    if a.get("aktiv"):
        ak = a["aktiv"]
        kante = ak["zone"]["vah"] if ak["dir"] == "↑" else ak["zone"]["val"]
        aus.append(("Verlassene Zone", "grün", ak["dir"],
                    f"{'VAH' if ak['dir'] == '↑' else 'VAL'} {_z(kante)} $ · Stopp: Schluss "
                    f"{'darunter' if ak['dir'] == '↑' else 'darüber'} (zurück in der alten Balance)"))
    sig = a["signale"][-4:]
    if sig:
        aus.append(("Letzte Auslöser", "grau", "→",
                    " · ".join(f"{s['art']}{s['dir']} {s['tag']:%d.%m.%Y}" for s in sig)))
    return aus
