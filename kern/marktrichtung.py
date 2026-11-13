"""Marktrichtung nach O'Neil (CAN SLIM, „M“): Distributionstage, Erholungsversuch, Follow-Through-Day.

Distributionstag: Schluss mindestens 0,2 % tiefer bei höherem Volumen als am Vortag, oder Stautag (höchstens +0,4 %
bei höherem Volumen, Schluss in der unteren Hälfte, nahe am Hoch); er verfällt nach 25 Handelstagen oder wenn der
Index seither 5 % gestiegen ist.

Gelesen werden S&P 500 und Nasdaq Composite (Tageskerzen mit Volumen von Yahoo). Ein Index genügt
(O'Neil): Distributionstage zählen im Index mit den meisten, der Follow-Through-Day im ersten Index,
der ihn zeigt.

Zustände (Ampel):
    Bestätigter Aufwärtstrend   grün   nach einem Follow-Through-Day, höchstens 3 Distributionstage
    Aufwärtstrend unter Druck   gelb   4 Distributionstage in einem Index
    Korrektur                   rot    5 Distributionstage in einem Index UND die Wertzone (Market Profile) von S&P 500
                                       oder Nasdaq ist nach unten gebrochen (A↓, F↓ oder B↓, nicht zurückgeholt);
                                       oder ein Index schließt unter dem Tief, von dem der letzte Follow-Through-Day
                                       ausging
    Ergänzung 4.11.2026 (nicht aus dem Buch): IBD selbst bleibt bei vielen Verteilungstagen „unter Druck“, solange
    die Indizes nahe am Hoch stehen. Ohne Bruch der Wertzone bleibt die Ampel deshalb gelb. Wertzonen aus SPY und QQQ
    (30-Minuten-Kerzen); fehlen sie für einen Tag, gilt die Wertzone als gebrochen (Regel wie vorher).

Ende der Korrektur: Follow-Through-Day ab Tag 4 (Tag 3 nur, wenn die Tage 1–3 im Schnitt mindestens +2 %
brachten – O'Neils seltene Ausnahme), oder – Ergänzung, nicht aus dem Buch – ein Index schließt über dem
Hoch vor der Korrektur („Aufwärtstrend wieder aufgenommen“; ein Index auf neuem Hoch ist nicht in Korrektur).

richtung(bis=None)   Zustand am Stichtag (Standard: letzter Handelstag) mit Text und Zeichen
verlauf(daten)       Zustand an jedem Tag
Regeln: pruefgalerie/oneil/regelkatalog_oneil.md, Abschnitt 7 (M – Marktrichtung).
"""
import pandas as pd

import marktdaten as md

INDIZES = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC"}
ZONEN_TITEL = {"S&P 500": "SPY", "Nasdaq": "QQQ"}     # Wertzonen der Indizes über die ETFs
DT_SCHWELLE = -0.2      # Distributionstag: Schluss mindestens 0,2 % tiefer bei höherem Volumen als am Vortag
DT_FENSTER = 25         # er zählt 25 Handelstage (5 Wochen) …
DT_VERFALL = 0.05       # … oder bis der Index seither um mehr als 5 % gestiegen ist (O'Neil; bis 13.11.2026: 10 %)
STAU_PLUS = 0.4         # Stautag (Stalling, O'Neil): höchstens +0,4 % bei höherem Volumen als am Vortag, Schluss in der
STAU_HOCH = 3.0         # unteren Hälfte der Tagesspanne, Index höchstens 3 % unter dem Hoch der 60 Tage – zählt wie
                        # ein Distributionstag (Prüf-Agent 13.11.2026: fehlte)
DRUCK, KORREKTUR = 4, 5
FTD_AB_TAG = 4          # Follow-Through-Day frühestens an Tag 4 des Erholungsversuchs …
FTD_SCHWELLE = 1.7      # … mit mindestens +1,7 % bei höherem Volumen als am Vortag (Buch: früher 1 %, heute deutlich
                        # über 1,5 %; Abnahme an den Fällen aus O'Neils Buch: 11 von 11, mit 1,0–1,5 % je 10 von 11)
TAG3_SCHNITT = 2.0      # Ausnahme Tag 3: Tage 1–3 im Schnitt mindestens +2 %
HOCH_FENSTER = 60       # Hoch vor der Korrektur: höchster Schluss der letzten 60 Handelstage beim Wechsel
VORLAUF = 520           # der Zustand hängt an der Vorgeschichte: so viele Tage werden vor dem Stichtag durchlaufen
AMPEL = {"Bestätigter Aufwärtstrend": "grün", "Aufwärtstrend unter Druck": "gelb", "Korrektur": "rot"}


def _angleichen(daten):
    tage = sorted(set.intersection(*(set(d.index) for d in daten.values())))
    return pd.DatetimeIndex(tage), {n: d.loc[tage] for n, d in daten.items()}


def zonen_bruch():
    """Für S&P 500 und Nasdaq: (Analyse, Liste der Wertzonen-Ereignisse) – Ereignis = (Tag, 'ab' oder 'auf')."""
    import marketprofile
    import tpo_daten
    aus = {}
    for name, tk in ZONEN_TITEL.items():
        df30 = tpo_daten.lesen(tk)
        a = marketprofile.analyse(df30) if df30 is not None else None
        if a is None:
            continue
        ev = []
        for x in a["signale"]:
            if x["art"] in ("A", "F", "B", "U") and x["dir"] == "↓":
                ev.append((x["tag"], "ab"))
            elif (x["art"] in ("A", "F", "B", "U") and x["dir"] == "↑") or (x["art"] == "S" and x["dir"] == "↓"):
                ev.append((x["tag"], "auf"))
        aus[name] = (a, ev, a["tage"][0]["tag"] if a["tage"] else None)
    return aus


def _gebrochen(bruch, tag):
    """True, wenn an diesem Tag die Wertzone eines Index nach unten gebrochen ist; ohne Wertzonendaten True (alte Regel)."""
    if not bruch:
        return True
    ohne = True
    for a, ev, beginn in bruch.values():
        if beginn is None or tag < beginn:
            continue
        ohne = False
        letzt = [e for t, e in ev if t <= tag]
        if letzt and letzt[-1] == "ab":
            return True
    return ohne


def verlauf(daten, bruch=None):
    """Läuft Tag für Tag durch; liefert eine Liste (Datum, Zustand, Zähler je Index, FTD, Erholungsversuch).
    bruch: zonen_bruch() – Korrektur durch Verteilungstage nur bei gebrochener Wertzone."""
    tage, daten = _angleichen(daten)
    namen = list(daten)
    C = {n: daten[n]["Close"].to_numpy(float) for n in namen}
    L = {n: daten[n]["Low"].to_numpy(float) for n in namen}
    H = {n: daten[n]["High"].to_numpy(float) for n in namen}
    V = {n: daten[n]["Volume"].to_numpy(float) for n in namen}
    zustand, dts, versuch, boden, ftd = "Korrektur", {n: [] for n in namen}, {n: None for n in namen}, None, None
    hoch = {n: float("inf") for n in namen}             # Hoch vor der Korrektur je Index
    wieder = None                                       # Tag der Wiederaufnahme ohne Follow-Through-Day
    aus = []
    for i in range(1, len(tage)):
        neuer_ftd = None
        for n in namen:
            c, c0, v, v0 = C[n][i], C[n][i - 1], V[n][i], V[n][i - 1]
            pct = (c / c0 - 1) * 100
            dts[n] = [(j, cj) for j, cj in dts[n] if j > i - DT_FENSTER and c <= cj * (1 + DT_VERFALL)]
            spanne = H[n][i] - L[n][i]
            stau = (DT_SCHWELLE < pct <= STAU_PLUS and v > v0 and spanne > 0 and (c - L[n][i]) / spanne < 0.5
                    and c >= C[n][max(0, i - 60):i + 1].max() * (1 - STAU_HOCH / 100))
            if (pct <= DT_SCHWELLE and v > v0) or stau:
                dts[n].append((i, c))
            if zustand != "Korrektur":
                continue
            w = versuch[n]
            if w is None or c < w["tief"] or (w["tag1"] is not None and L[n][i] < w["tief_low"]):
                versuch[n] = {"tief": c, "tief_low": L[n][i], "tag1": None}
            elif w["tag1"] is None:
                if c > c0:
                    w["tag1"] = i
            elif neuer_ftd is None and pct >= FTD_SCHWELLE and v > v0:
                nr = i - w["tag1"] + 1
                tag3 = nr == 3 and (C[n][i] / C[n][w["tag1"] - 1] - 1) * 100 / 3 >= TAG3_SCHNITT
                if nr >= FTD_AB_TAG or tag3:
                    neuer_ftd = {"tag": tage[i], "index": n, "tag_nr": nr, "plus": round(pct, 1)}
                    boden = (n, w["tief_low"])
        neues_hoch = zustand == "Korrektur" and any(C[n][i] > hoch[n] for n in namen)
        if neuer_ftd or neues_hoch:
            zustand, ftd = "Bestätigter Aufwärtstrend", neuer_ftd
            wieder = None if neuer_ftd else tage[i]
            dts = {n: [] for n in namen}                       # Zählung beginnt neu
        elif zustand != "Korrektur":
            meiste = max(len(x) for x in dts.values())
            if (meiste >= KORREKTUR and _gebrochen(bruch, tage[i])) or (boden and C[boden[0]][i] < boden[1]):
                zustand, boden, wieder = "Korrektur", None, None
                versuch = {n: {"tief": C[n][i], "tief_low": L[n][i], "tag1": None} for n in namen}
                hoch = {n: C[n][max(0, i - HOCH_FENSTER):i + 1].max() for n in namen}
            else:
                zustand = "Aufwärtstrend unter Druck" if meiste >= DRUCK else "Bestätigter Aufwärtstrend"
        lauf = None
        if zustand == "Korrektur":
            laeufe = [(i - w["tag1"] + 1, n) for n, w in versuch.items() if w and w["tag1"] is not None]
            lauf = max(laeufe) if laeufe else None
        aus.append({"tag": tage[i], "zustand": zustand, "dt": {n: [tage[j] for j, _ in x] for n, x in dts.items()},
                    "ftd": ftd if zustand != "Korrektur" else None, "versuch": lauf,
                    "wieder": wieder if zustand != "Korrektur" else None})
    return aus


def _vollstaendig(df):
    """Ein letzter Tag mit auffällig wenig Volumen (unter 40 % des 50-Tage-Schnitts) gilt als unvollständig."""
    if len(df) > 51 and df["Volume"].iloc[-1] < 0.4 * df["Volume"].iloc[-51:-1].mean():
        return df.iloc[:-1], True
    return df, False


def richtung(bis=None):
    daten, zeichen = {}, []
    for name, tk in INDIZES.items():
        df = md.yahoo_ohlc(tk)
        df = df[df.index <= pd.Timestamp(bis)] if bis else df
        df, kurz = _vollstaendig(df)
        if kurz:
            zeichen.append(("gelb", f"{name}: Volumen des letzten Tages unvollständig – Tag noch nicht gezählt"))
        daten[name] = df.iloc[-VORLAUF:]
    try:
        bruch = zonen_bruch()
    except Exception:  # noqa: BLE001 – ohne Wertzonen gilt die Regel wie vorher
        bruch = {}
    tage = verlauf(daten, bruch)
    heute = tage[-1]
    seit = heute["tag"]
    for x in reversed(tage):
        if x["zustand"] != heute["zustand"]:
            break
        seit = x["tag"]
    teile = ["Distributionstage " + " · ".join(f"{n} {len(d)}" for n, d in heute["dt"].items()) + " in 5 Wochen"]
    for n_, (a_, _, _) in bruch.items():          # Wertzone je Index (Market Profile), z. B. „S&P 500: Balance“
        teile.append(f"{n_}: {a_['zustand']['wort']}")
    if heute["zustand"] == "Korrektur":
        if heute["versuch"]:
            nr, n = heute["versuch"]
            teile.append(f"Erholungsversuch {n} Tag {nr}" + (" – Follow-Through ab Tag 4 möglich" if nr < FTD_AB_TAG else ""))
        else:
            teile.append("noch kein Erholungsversuch")
    elif heute["ftd"]:
        f = heute["ftd"]
        teile.append(f"Follow-Through-Day {f['tag']:%d.%m.%Y} ({f['index']}, Tag {f['tag_nr']}, +{zahl_de(f['plus'])} %)")
    elif heute["wieder"]:
        teile.append(f"Aufwärtstrend am {heute['wieder']:%d.%m.%Y} mit neuem Hoch wieder aufgenommen (ohne Follow-Through-Day)")
    if bis is None:
        zeichen += _gegenprobe(daten["S&P 500"])
    return {"zustand": heute["zustand"], "ampel": AMPEL[heute["zustand"]], "seit": seit,
            "zonen": {n_: a_["zustand"]["wort"] for n_, (a_, _, _) in bruch.items()},
            "distributionstage": {n: len(d) for n, d in heute["dt"].items()}, "dt_daten": heute["dt"],
            "ftd": heute["ftd"], "text": " · ".join(teile), "zeichen": zeichen}


def zahl_de(x):
    return f"{x:.1f}".replace(".", ",")


def _gegenprobe(d):
    """Volumenrichtung des letzten Tages gegen das Gesamtvolumen aller US-Aktien bei Massive (zweite Quelle)."""
    import massive
    if len(d) < 2:
        return []
    try:
        heute, gestern = massive.tag(d.index[-1]), massive.tag(d.index[-2])
    except Exception:
        return [("gelb", "Volumen-Gegenprobe mit Massive nicht möglich")]
    if heute is None or gestern is None or heute.empty or gestern.empty:
        return []
    massiv_hoeher = heute["Volume"].sum() > gestern["Volume"].sum()
    yahoo_hoeher = d["Volume"].iloc[-1] > d["Volume"].iloc[-2]
    if massiv_hoeher != yahoo_hoeher:
        return [("gelb", f"Volumen am {d.index[-1]:%d.%m.%Y}: Yahoo {'höher' if yahoo_hoeher else 'tiefer'} als am Vortag, "
                         f"Gesamtmarkt bei Massive {'höher' if massiv_hoeher else 'tiefer'} – Distributionstag unsicher")]
    return []
