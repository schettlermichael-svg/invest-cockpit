"""Zahlen-Reaktion (12.11.2026, Micky): Setup nach einem Zahlentermin, long und short – die Drift nach den Zahlen
(Post-Earnings-Announcement Drift: Ball und Brown 1968, Bernard und Thomas 1989; Bondes „Delayed Reaction“, Shannons
Anker am Ereignistag). Reagiert der Kurs klar auf die Zahlen, kaufen bzw. verkaufen die Fonds oft über Wochen nach.

Reaktionstag = erster Handelstag nach der Meldung (nach Börsenschluss gemeldet → Folgetag), wie „E +x %“ im Chart.
Voraussetzung: Reaktion ab REAKTION_PCT (Short ab −REAKTION_PCT) vor höchstens FENSTER Handelstagen (jüngste Meldung).
Regeln für grün (long; Short gespiegelt):
  1. Volumen am Reaktionstag über dem 50-Tage-Schnitt (Mickys Maßstab)
  2. Schluss im oberen Drittel der Tagesspanne (Short: unteres Drittel) – ein abverkaufter Tag zeigt keine Nachfrage
  3. Seitdem kein Schluss unter dem Tief des Reaktionstags und keiner unter dem AVWAP ab dem Reaktionstag
     (Short: über dem Hoch bzw. über dem AVWAP)
  4. Kurs über dem GD50 (Short: darunter) – Kullamägis Maßstab für Momentum, nicht die volle Trendvorlage
gelb = genau eine Regel fehlt; sonst rot (keine Reihe).
Einstieg: der ruhige Rücksetzer an den AVWAP ab dem Reaktionstag – „pivot“ ist dieser AVWAP, die Zone reicht bis 5 %
darüber (Short: darunter). Stopp im Chart wie überall 1,5 ATR; zusätzlich das Tief (Short: Hoch) des Reaktionstags.
Ohne Gewinndaten (Termin unbekannt) kein Setup – erfunden wird nichts."""
import pandas as pd

REAKTION_PCT = 3.0            # Micky 12.11.2026
FENSTER = 20                  # Handelstage nach dem Reaktionstag (Micky 12.11.2026)


def reaktionstag(df, gewinne):
    """Jüngster Reaktionstag: (Index-Position, Prozent) oder None."""
    if gewinne is None or getattr(gewinne, "empty", True) or df is None or len(df) < 60:
        return None
    best = None
    for tag, z in gewinne.iterrows():
        pos = int(df.index.searchsorted(pd.Timestamp(tag)))
        if z.get("nach_schluss", 0) and pos < len(df) and df.index[pos] == pd.Timestamp(tag):
            pos += 1
        if 0 < pos < len(df):
            pct = (float(df["Close"].iloc[pos]) / float(df["Close"].iloc[pos - 1]) - 1) * 100
            if best is None or pos > best[0]:
                best = (pos, pct)
    return best


def pruefen(df, gewinne):
    """Ergebnis oder None: {ampel, seite, tag, pct, volumen, schluss_lage, tage_her, avwap, pivot, abstand, tief, hoch,
    regeln [(Name, ok, Text)], fehlt, text}."""
    import avwap
    rt = reaktionstag(df, gewinne)
    if rt is None:
        return None
    pos, pct = rt
    n = len(df)
    tage_her = n - 1 - pos
    if tage_her > FENSTER or abs(pct) < REAKTION_PCT:
        return None
    short = pct < 0
    o, h, l, c = (df[s].to_numpy(float) for s in ("Open", "High", "Low", "Close"))
    v = df["Volume"].to_numpy(float)
    v50 = pd.Series(v).rolling(50, min_periods=20).mean().shift().to_numpy()
    vol = v[pos] / v50[pos] if v50[pos] == v50[pos] and v50[pos] else None
    spanne = h[pos] - l[pos]
    lage = (c[pos] - l[pos]) / spanne if spanne > 0 else 0.5          # 0 = Tief, 1 = Hoch
    av = avwap.reihe(df, df.index[pos])
    w = float(av.iloc[-1]) if len(av) else None
    danach = slice(pos + 1, n)
    if short:
        halten = not (c[danach] > h[pos]).any() and (len(av) < 2 or not (c[danach] > av.to_numpy()[1:]).any())
        trend = n >= 50 and c[-1] < c[-50:].mean()
        lage_ok = lage <= 1 / 3
    else:
        halten = not (c[danach] < l[pos]).any() and (len(av) < 2 or not (c[danach] < av.to_numpy()[1:]).any())
        trend = n >= 50 and c[-1] > c[-50:].mean()
        lage_ok = lage >= 2 / 3
    k = lambda x: f"{x:.1f}".replace(".", ",")         # noqa: E731
    drittel = "oberen" if lage >= 2 / 3 else "unteren" if lage <= 1 / 3 else "mittleren"
    regeln = [("Volumen über dem 50-Tage-Schnitt", bool(vol and vol > 1),
               f"{k(vol)}-fach" if vol else "Volumen unbekannt"),
              (f"Schluss im {'unteren' if short else 'oberen'} Drittel", lage_ok, f"Schluss im {drittel} Drittel"),
              (f"hält {'Hoch' if short else 'Tief'} und AVWAP des Reaktionstags", halten,
               "gehalten" if halten else "gebrochen"),
              (f"Kurs {'unter' if short else 'über'} GD50", trend, "ja" if trend else "nein")]
    regeln = [(n_, bool(ok), t_) for n_, ok, t_ in regeln]          # JSON: keine numpy-Wahrheitswerte
    fehlt = sum(1 for _, ok, _ in regeln if not ok)
    ampel = "grün" if fehlt == 0 else "gelb" if fehlt == 1 else "rot"
    abstand = float((c[-1] / w - 1) * 100) if w else None
    tag = df.index[pos]
    text = (f"⚡ Zahlen-Reaktion {'+' if pct >= 0 else '−'}{k(abs(pct))} % am {tag:%d.%m.} (vor {tage_her} T.)"
            + (f" · Volumen {k(vol)}-fach" if vol else "") + f" · Schluss im {drittel} Drittel"
            + (f" · AVWAP {w:.2f} $ ".replace(".", ",") + _avwap_lage(halten, short, c[-1], w) if w else ""))
    return {"ampel": ampel, "seite": "short" if short else "long", "tag": f"{tag:%Y-%m-%d}", "pct": round(pct, 1),
            "volumen": round(vol, 2) if vol else None, "schluss_lage": round(lage, 2), "tage_her": tage_her,
            "avwap": round(w, 2) if w else None, "pivot": w, "abstand": abstand, "tief": float(l[pos]),
            "hoch": float(h[pos]), "regeln": regeln, "halten": bool(halten), "fehlt": fehlt, "text": text,
            "luecken": [f"Zahlen-Reaktion: {n_}" for n_, ok, _ in regeln if not ok]}


def _avwap_lage(halten, short, kurs, w):
    """Wort zum AVWAP (12.11.2026: HWM stand bei 224 $ über dem AVWAP 211,46 $, der Text sagte „bricht den AVWAP“ –
    gemeint war: seit dem Reaktionstag einmal darunter geschlossen)."""
    if halten:
        return "gehalten"
    zurueck = kurs < w if short else kurs > w
    return ("einmal gebrochen, Kurs wieder " + ("darunter" if short else "darüber")) if zurueck else \
        ("gebrochen, Kurs " + ("darüber" if short else "darunter"))
