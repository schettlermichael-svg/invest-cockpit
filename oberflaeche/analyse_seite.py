"""Seite „Analyse“ (Micky 21.11.2026): die Tiefenanalyse der App „Titel-Analyse“ im Cockpit – je Titel die
Aussagezeilen mit genau einem Zeichen der Zeichenliste (gestaltung.ZEICHEN_LISTE).

Reihenfolge wie in der Titel-Analyse: Struktur nach Dalton · PbD nach Tom Vorwald (Tag, Woche, Stunde) · Wertwanderung
(Tag, Woche) · AVWAP nach Shannon mit Zange · Relative Stärke (Tabelle, Stärke in der Schwäche, RS-Linie) · Geldfluss
(Rückenwind, Rangtabelle der Sektoren, CMF). Die Einschätzung (Stratege mit Websuche) setzt app.py darunter.
Gerechnet in kern/tiefe.py; Fallen (Spring, Upthrust, Fehlausbruch) und Pivot der Enge nach den Regeln des Cockpits.
"""
import pandas as pd

import gestaltung
from gestaltung import TEXT_2, karte, seite, t, zeilen

# ── Feste Regeln der Anzeige ─────────────────────────────────────────────────────────────────────────────────────────
WANDER_LETZTE = 5            # Wertwanderung: die letzten 5 Kerzen
WANDER_SEITE = 4             # … ab 4 von 5 höher bzw. tiefer: 🦬 bzw. 🐻
SIS_ZEIGEN = 4               # Stärke in der Schwäche: die letzten 4 Abgabetage nennen
RS_UNTER_HOCH = -10          # RS-Linie bis 10 % unter ihrem Hoch: gemischt (🟡), darunter Schwäche (🔴)
PFEIL_TAGE = ("1W", "1M", "3M")   # RS gegen den Index über 1W, 1M, 3M


def _d(x, fmt="%d.%m."):
    return f"{pd.Timestamp(x):{fmt}}"


def _k(x):
    return gestaltung.zahl(float(x))


def _p(x):
    if x is None:
        return "⚪"
    return f"{'+' if x >= 0 else '−'}{gestaltung.zahl(abs(x), 1)} %"


# ── Struktur nach Dalton ─────────────────────────────────────────────────────────────────────────────────────────
def struktur_zeilen(st_, alt, fallen, enge, kurs):
    import tiefe
    pr = st_["profil"]
    z = [("🟡", f"Anker {_d(st_['anker'])} – {st_['anker_grund']}"),
         ("🟡", f"Profil aus {pr['kerzen']} {pr['quelle']} ab {_d(pr['ab'])}, Stufen {_k(pr['schritt'])} $: POC "
                f"{_k(pr['poc'])} · Wertzone 70 % {_k(pr['val'])}–{_k(pr['vah'])}")]
    if kurs > pr["vah"]:
        z.append(("🦬", f"Kurs über der Wertzone ({_p((kurs / pr['vah'] - 1) * 100)} über der Oberkante)"))
    elif kurs < pr["val"]:
        z.append(("🐻", f"Kurs unter der Wertzone ({_p((kurs / pr['val'] - 1) * 100)} unter der Unterkante)"))
    else:
        z.append(("🟡", f"Kurs {_k(kurs)} in der Wertzone – {_p((kurs / pr['vah'] - 1) * 100)} zur Oberkante, "
                        f"{_p((kurs / pr['val'] - 1) * 100)} zur Unterkante"))
    for lo, hi in pr["duenn"]:
        z.append(("🟡", f"Dünne Zone {_k(lo)}–{_k(hi)} (weniger als ⅓ des POC-Volumens) – hier läuft der Kurs schnell"))
    if pr["docht_unten"]:
        z.append(("🟢", f"Docht unten {_k(pr['docht_unten'][0])}–{_k(pr['docht_unten'][1])}: dort zurückgekauft"))
    if pr["docht_oben"]:
        z.append(("🔴", f"Docht oben {_k(pr['docht_oben'][0])}–{_k(pr['docht_oben'][1])}: dort abverkauft"))
    z.append(("🟡", f"Balance seit {_d(st_['balance_roh'])} (überlappender Wert, Regel des Cockpits) · Pivots ab "
                    f"{_d(st_['balance_start'])}"))
    z.append(("🦬", f"Pivot long am Rand der Balance {_k(st_['pivot'])} ({_d(st_['pivot_tag'])}, "
                    f"{_tests(st_['tests_oben'])}: {', '.join(_d(x) for x in st_['tests_oben'])}) · Pivot short "
                    f"{_k(st_['short_pivot'])} ({_d(st_['short_pivot_tag'])}, {_tests(st_['tests_unten'])})"))
    if enge and enge.get("pivot"):
        z.append(("🦬", f"Pivot (Livermores Pivotal Point oben) {_k(enge['pivot'])}" + (f" · Unterkante der Zone {_k(enge['unten'])}"
                                                                          if enge.get("unten") else "")))
    q = st_["quetsch"]
    if q and q["art"] == "aufsteigend":
        z.append(("🦈", f"Einquetschen seit {_d(q['ab'])}: Tiefs der Drittel steigen "
                        f"{' → '.join(_k(x) for x in q['tiefs'])}, Hochs bleiben bei {_k(min(q['hochs']))}–{_k(max(q['hochs']))}"))
    elif q:
        z.append(("🦈", f"Einquetschen nach unten seit {_d(q['ab'])}: Hochs der Drittel fallen "
                        f"{' → '.join(_k(x) for x in q['hochs'])}, Tiefs bleiben bei {_k(min(q['tiefs']))}–{_k(max(q['tiefs']))}"))
    elif st_["drittel"]:
        ti, ho = st_["drittel"]
        z.append(("🟡", f"Kein Einquetschen seit {_d(st_['anker'])}: Tiefs der Drittel {' / '.join(_k(x) for x in ti)}, "
                        f"Hochs {' / '.join(_k(x) for x in ho)}"))
    else:
        z.append(("🟡", "Kein Einquetschen: seit dem Anker zu wenige Kerzen für drei Drittel"))
    for f in fallen:
        z.append(("🦊", f))
    if not fallen:
        z.append(("🟢", "Keine Falle: kein Spring, Upthrust oder Fehlausbruch nach den Regeln des Cockpits"))
    if alt:
        nah = abs(alt["poc"] / kurs - 1) <= tiefe.NAH_PCT
        z.append(("🪝" if nah else "🟡", f"Alte Wertzone (Balance {_d(alt['start'])}–{_d(alt['ende'])}): POC {_k(alt['poc'])}, "
                                         f"Wertzone {_k(alt['val'])}–{_k(alt['vah'])}"))
    else:
        z.append(("⚪", "Alte Wertzone: keine Balance von mindestens 10 Tagen vor dem Anker"))
    return z


def _tests(liste):
    return f"{len(liste)} {'Test' if len(liste) == 1 else 'Tests'}"


def fallen_texte(df):
    """Spring, Upthrust und Fehlausbruch nach den Regeln des Cockpits (vcp_zone, Micky 21.11.2026)."""
    import vcp_zone
    aus = []
    try:
        su = vcp_zone.spring_upthrust(df)
        if su:
            aus.append(f"{su['art']} am {_d(su['tag'])}: Schluss zurück in der Zone am {_d(su['zurueck_tag'])} · "
                       f"Einstieg {_k(su['einstieg'])}, Stopp {_k(su['stopp'])}, Ziel {_k(su['ziel'])}")
        a = vcp_zone.ausbruch(df)
        if a and a.get("fehl"):
            aus.append(f"Fehlausbruch: Ausbruch über den Pivot {_k(a['pivot'])} am {_d(a['tag'])}, am "
                       f"{_d(a['fehl_tag'])} wieder darunter")
    except Exception:  # noqa: BLE001 – Technik: ohne Zone keine Falle
        pass
    return aus


# ── PbD nach Tom Vorwald ─────────────────────────────────────────────────────────────────────────────────────────


# ── Wertwanderung ────────────────────────────────────────────────────────────────────────────────────────────────
def wander_zeilen(w, kurs, kerze, quelle):
    import tiefe
    if w is None:
        return [("⚪", f"Wertwanderung je {kerze}: ungemessen (keine {quelle} für genug Kerzen)")]
    z = []
    letzte = w["klassen"][-WANDER_LETZTE:]
    hoch = sum(k in ("höher", "überlappend höher") for _, k in letzte)
    tief = sum(k in ("tiefer", "überlappend tiefer") for _, k in letzte)
    z.append(("🦬" if hoch >= WANDER_SEITE else "🐻" if tief >= WANDER_SEITE else "🟡",
              f"Wertzone je {kerze} gegen die vorige (letzte {len(letzte)}): " + ", ".join(f"{_d(t_)} {k}" for t_, k in letzte)))
    richt, n = w["treppe"]
    if n >= tiefe.TREPPE:
        z.append(("🦬" if richt > 0 else "🐻", f"POC-Treppe je {kerze} {'aufwärts' if richt > 0 else 'abwärts'}: {n} POCs in "
                  f"Folge {'höher' if richt > 0 else 'tiefer'} – der Markt akzeptiert {'höhere' if richt > 0 else 'tiefere'} Preise"))
    if w["ballen"]:
        z.append(("🟡", f"POCs ballen sich: die letzten {tiefe.BALLEN_N} innerhalb {_k(w['ballen_spanne'])} $ (≤ 1 ATR) – "
                        "Balance, Wert ist hier akzeptiert"))
    if n < tiefe.TREPPE and not w["ballen"]:
        z.append(("🟡", f"Keine Treppe und kein Ballen: POCs der letzten {tiefe.BALLEN_N} streuen über "
                        f"{_k(w['ballen_spanne'])} $ – der Markt sucht"))
    if w["abtasten"]:
        z.append(("🪝", f"Abtasten {w['abtasten']}: Schluss {_k(kurs)} {'über' if w['abtasten'] == 'oben' else 'unter'} der "
                        f"vorigen Wertzone, eigener POC {_k(w['poc_heute'])} noch darin – Kurs ohne Akzeptanz, Rückkehr "
                        "wahrscheinlich"))
    for x, wo in ((w["nackt_ueber"], "darüber"), (w["nackt_unter"], "darunter")):
        if x:
            z.append(("🪝", f"Nackter POC {wo}: {_k(x[1])} ({_d(x[0])}) – nie wieder erreicht, Preismagnet "
                            "(Praxisbegriff, keine Regel nach Dalton)"))
    return z


# ── AVWAP nach Shannon ───────────────────────────────────────────────────────────────────────────────────────────
def avwap_zeilen(av, zange, pr):
    import chart
    import tiefe
    z = []
    for e in av:
        ueber = e["abstand"] >= 0
        haken = (not ueber) and e["abstand"] >= -tiefe.DECKEL_PCT
        z.append(("🪝" if haken else "🟢" if ueber else "🔴",
                  f"AVWAP {chart.AVWAP_KURZ.get(e['anker'], e['anker'])} ({_d(e['tag'])}): {_k(e['wert'])} – Kurs "
                  f"{_p(e['abstand'])}" + (" (nächster Deckel)" if haken else "")))
    if zange:
        schliesst = zange["heute"] < zange["vorher"]
        seite_ = ("über beiden Linien – die Käufer gewinnen" if zange["ueber"] else
                  "unter beiden Linien – die Verkäufer gewinnen" if zange["unter"] else "zwischen den Linien – offen")
        z.append(("🦈" if schliesst else "🟡",
                  f"Zange (letztes Hoch ↔ Tief der Bewegung): Abstand vor {zange['tage']} Tagen {_k(zange['vorher'])} → "
                  f"heute {_k(zange['heute'])} $ – {'schließt sich' if schliesst else 'öffnet sich'}; Kurs {seite_}"))
    else:
        z.append(("⚪", "Zange: ungemessen (kein letztes Hoch oder kein Tief der Bewegung)"))
    for e in av:
        if e["anker"] == "zahlen" and (abs(e["wert"] / pr["poc"] - 1) <= tiefe.DOPPEL_PCT
                                       or pr["val"] <= e["wert"] <= pr["val"] * (1 + tiefe.DOPPEL_PCT)):
            z.append(("🪝", f"AVWAP vom Zahlentag ({_k(e['wert'])}) liegt an POC bzw. Unterkante der Wertzone – doppelte Marke"))
    return z


# ── Relative Stärke und Geldfluss ────────────────────────────────────────────────────────────────────────────────
def rs_zeilen(df, idx, sis, rel, gegen):
    import tiefe
    z = []
    t_, s_ = tiefe.leistung(df["Close"]), tiefe.leistung(idx["Close"])
    for k in PFEIL_TAGE:
        if t_[k] is not None and s_[k] is not None:
            d = t_[k] - s_[k]
            z.append(("🟢" if d > 0 else "🔴", f"{k}: {_p(d)[:-2]} Prozentpunkte gegenüber dem S&P 500 (Titel {_p(t_[k])}, "
                                                f"S&P 500 {_p(s_[k])})"))
    if sis and sis["n"]:
        z.append(("🦈" if sis["besser"] * 2 > sis["n"] else "🟡" if sis["besser"] else "🔴",
                  f"Stärke in der Schwäche (Abgabetage): an {sis['besser']} von {sis['n']} Distributionstagen des S&P 500 "
                  "(25 Sitzungen) besser als der Index – " + ", ".join(
                      f"{_d(x['tag'])} {_p(x['titel'])} vs. {_p(x['index'])}" for x in sis["tage"][-SIS_ZEIGEN:])))
    elif sis is not None:
        z.append(("🟢", "Keine Distributionstage des S&P 500 in den letzten 25 Sitzungen"))
    for x in gegen:
        z.append(("🦈" if x["seite"] == "stärke" else "🐻", f"Stärke in der Schwäche (schwere Tage): {x['text']}"
                  if x["seite"] == "stärke" else f"Schwäche in der Stärke: {x['text']}"))
    for x in (rel or {}).get("staerke") or []:
        z.append(("🦈", f"Stärke in der Korrektur: {x}"))
    for x in (rel or {}).get("schwaeche") or []:
        z.append(("🐻", f"Schwäche in der Stärke: {x}"))
    from masse import JAHR_TAGE as jahr
    c = (df["Close"] / idx["Close"].reindex(df.index).ffill()).dropna()
    if len(c) < jahr:
        z.append(("⚪", "RS-Linie: ungemessen (weniger als ein Jahr gemeinsame Kerzen mit dem S&P 500)"))
    else:
        import rueckenwind
        import zeichen
        hoch = float(c.iloc[-jahr:].max())
        abst = (float(c.iloc[-1]) / hoch - 1) * 100
        neu = c.iloc[-1] >= hoch * zeichen.RS_HOCH
        vor = neu and float(df["Close"].iloc[-1]) < float(df["High"].iloc[-jahr:].max()) * rueckenwind.KURS_NAH
        z.append(("🦈" if vor else "🟢" if neu else "🟡" if abst > RS_UNTER_HOCH else "🔴",
                  f"RS-Linie (Titel ÷ S&P 500): {'am 52W-Hoch' if neu else _p(abst) + ' unter ihrem 52W-Hoch'} "
                  f"({_d(c.iloc[-jahr:].idxmax())})" + (" – neues Hoch vor dem Kurs" if vor else "")))
    return z


def rs_tabelle(zeilen_):
    zelle = lambda x: "⚪" if x is None else _p(x)                         # noqa: E731
    kopf = "".join(f'<th style="padding:4px 10px;text-align:right">{k}</th>' for k in ("1W", "1M", "3M", "6M", "YTD"))
    reihen = "".join(f'<tr><td style="padding:4px 10px">{t(n)}</td>' + "".join(
        f'<td style="padding:4px 10px;text-align:right">{zelle(w[k])}</td>' for k in ("1W", "1M", "3M", "6M", "YTD"))
        + "</tr>" for n, w in zeilen_)
    return (f'<table style="border-collapse:collapse;font-size:14px"><tr><th style="padding:4px 10px;text-align:left">'
            f'</th>{kopf}</tr>{reihen}</table>')


def geld_zeilen(rang, sek, rw, cmf_liste):
    import sektoren
    import tiefe
    z = []
    if rw:
        import rueckenwind
        k_ = rueckenwind.klasse(rw)                  # Schlachtordnung statt Stufe (22.11.2026)
        z.append(("🌞" if k_ in rueckenwind.ANGRIFF_KLASSEN else "❄️" if k_ in (4, 5) else "🟡",  # Technik: Klassennummern
                  "Rückenwind (das Urteil des Cockpits): "
                  + (f"{k_} · {rueckenwind.KLASSEN[k_ - 1]}" if k_ else "ohne Klasse") + (f" · RS-Rang {rw['rang']}" if rw.get("rang") is not None else "")
                  + (f" · Tempo {rw['tempo']:+d} in 4 Wochen" if isinstance(rw.get("tempo"), int) else "")))
    else:
        z.append(("⚪", "Rückenwind: noch kein Stand des Nachtlaufs für diesen Titel"))
    if sek in rang:
        r = rang[sek]
        mittel = sum(r.get(f"rang_{k}", len(rang)) for k in ("1M", "3M", "6M")) / 3
        z.append(("🌞" if mittel <= tiefe.RANG_SONNE else "❄️" if mittel >= tiefe.RANG_SCHNEE else "🟡",
                  f"Sektor {sektoren.SEKTOREN.get(sek, sek)} ({sek}): Rang {r.get('rang_1M')}/{r.get('rang_3M')}/"
                  f"{r.get('rang_6M')} von {len(rang)} über 1M/3M/6M ({_p(r['1M'])} / {_p(r['3M'])} / {_p(r['6M'])})"))
    else:
        z.append(("⚪", "Sektor des Titels unbekannt"))
    reihe = sorted(rang, key=lambda s: rang[s].get("rang_1M", len(rang) + 1))
    if reihe:
        n = tiefe.RANG_SEITE
        z.append(("🟡", "Geld fließt im letzten Monat vor allem in " + ", ".join(
            f"{sektoren.SEKTOREN.get(s, s)} {_p(rang[s]['1M'])}" for s in reihe[:n]) + " – und kommt aus " + ", ".join(
            f"{sektoren.SEKTOREN.get(s, s)} {_p(rang[s]['1M'])}" for s in reihe[-n:][::-1])))
    for name, sym, c in cmf_liste:
        if c is None:
            z.append(("⚪", f"CMF(20) {name}: ungemessen" + (" (kein Branchen-ETF)" if name == "Branche" else "")))
            continue
        w = c["wert"] or 0
        trei = ", ".join(f"{_d(d)} {'+' if x > 0 else '−'}{gestaltung.zahl(abs(x) / 1e6, 2)} Mio." for d, x in c["plus"][:2] + c["minus"][:2])  # Layout
        z.append(("🟢" if w > tiefe.CMF_GRENZE else "🔴" if w < -tiefe.CMF_GRENZE else "🟡",
                  f"CMF(20) {name} {sym}: {'+' if w > 0 else '−' if w < 0 else ''}{gestaltung.zahl(abs(w), 3)} – Treiber: {trei}"))  # Layout
    return z


def rang_tabelle(rang, sek):
    import sektoren
    reihe = sorted(rang, key=lambda s: rang[s].get("rang_1M", len(rang) + 1))
    zellen = lambda s, k: f'{rang[s].get("rang_" + k, "–")} ({_p(rang[s][k])})'   # noqa: E731
    return ('<table style="border-collapse:collapse;font-size:14px"><tr><th style="padding:4px 10px;text-align:left">'
            'Sektor</th><th style="padding:4px 10px">Rang 1M</th><th style="padding:4px 10px">Rang 3M</th>'
            '<th style="padding:4px 10px">Rang 6M</th></tr>' + "".join(
                f'<tr style="{"font-weight:600" if s == sek else ""}"><td style="padding:4px 10px">'
                f'{t(sektoren.SEKTOREN.get(s, s))} ({s})</td>' + "".join(
                    f'<td style="padding:4px 10px;text-align:right">{zellen(s, k)}</td>' for k in ("1M", "3M", "6M"))
                + "</tr>" for s in reihe) + "</table>")


# ── Daten und Seite ──────────────────────────────────────────────────────────────────────────────────────────────
def rechnen(tk):
    """Alles, was die Seite und der Chart brauchen (Tageskurse, 30-Minuten-Kerzen, drei Ebenen, AVWAP, RS, Geld)."""
    import avwap
    import daten
    import quellen
    import sektoren
    import tiefe
    import tpo_daten
    import vcp_zone
    df = daten.kurse(tk)
    df.attrs["ticker"] = tk
    idx = daten.kurse(daten.INDEX)
    sb = daten.steckbrief(tk) or {}
    try:
        tpo_daten.merken(tk)
        d30 = tpo_daten.kerzen(tk, df, abruf=True)
    except Exception:  # noqa: BLE001 – Technik: ohne Netz bleibt der Speicher
        d30 = tiefe.dreissig(df)
    try:
        zt = avwap.zahlentag(df, quellen.laden(tk)["gewinne"])
    except Exception:  # noqa: BLE001 – ohne Zahlen kein Zahlentag
        zt = None
    zone_start, enge = None, None
    try:
        zone_start = tiefe.zone_beginn(df)
        a_ = vcp_zone.ausbruch(df)
        z_ = vcp_zone.datiert(df, a_["zone"] if a_ else vcp_zone.zone(df))
        if zone_start is not None:                 # Pivot und Unterkante: Livermores Pivotal Points (vcp_zone.zone)
            enge = {"pivot": (a_ or {}).get("pivot") or z_.get("pivot"), "unten": z_.get("unten")}
    except Exception:  # noqa: BLE001 – Technik: ohne Zone kein Zonenbeginn
        pass
    ebenen = {"Tag": tiefe.ebene("Tag", df, d30, zt, zone_start=zone_start),
              "Woche": tiefe.ebene("Woche", tiefe.woche(df), d30, zt, tage=df),
              "Stunde": tiefe.ebene("Stunde", tiefe.stunde(d30), d30, zt)}
    sek = sektoren.sektor_von(sb.get("sektor", ""))
    bra = sektoren.BRANCHEN_ETF.get(sb.get("branche"))
    alle = {}
    for s in list(sektoren.SEKTOREN) + ([bra] if bra else []):
        try:
            alle[s] = daten.kurse(s)
        except Exception:  # noqa: BLE001 – ein fehlender ETF bleibt ungemessen
            alle[s] = None
    av, zange = tiefe.avwap_liste(df, zt)
    return {"tk": tk, "df": df, "idx": idx, "sb": sb, "d30": d30, "zahltag": zt, "ebenen": ebenen, "avwap": av,
            "zange": zange, "sek": sek, "bra": bra, "alle": alle, "enge": enge,
            "fallen": fallen_texte(df), "sis": tiefe.staerke_in_schwaeche(df, idx),
            "rang": tiefe.sektor_rang({s: alle[s] for s in sektoren.SEKTOREN if alle.get(s) is not None})}


def seite_analyse(tk):
    """HTML der Seite Analyse für einen Titel."""
    import tiefe
    import titel
    import zeichen
    import sektoren
    r = rechnen(tk.upper().strip())
    df, idx = r["df"], r["idx"]
    kurs = float(df["Close"].iloc[-1])
    et = r["ebenen"]["Tag"]
    teile = [karte(f'<div style="color:{TEXT_2};font-size:14px">Kurs {_k(kurs)} $ am {_d(df.index[-1], "%d.%m.%Y")} · '
                   f'Sektor {t(sektoren.SEKTOREN.get(r["sek"], "–"))} ({r["sek"] or "–"}) · Branche '
                   f'{t(r["sb"].get("branche") or "–")} ({r["bra"] or "kein Branchen-ETF"}) · Tagesebene; Woche und Stunde '
                   f'mit denselben Regeln · Chart mit allen Bausteinen auf der Titelseite</div>'
                   + gestaltung.zeichen_legende(), f"{r['tk']} · Tiefenanalyse")]
    if et:
        st_ = et["struktur"]
        teile.append(karte(zeilen(struktur_zeilen(st_, et["alt"], r["fallen"], r["enge"], kurs)),
                           "Struktur nach Dalton"))
        ew = r["ebenen"]["Woche"]
        teile.append(karte('<div style="font-weight:600">je Tag</div>'
                           + zeilen(wander_zeilen(et["wander"], kurs, "Tag", "30-Minuten-Kerzen"))
                           + '<div style="font-weight:600;margin-top:10px">je Woche</div>'
                           + zeilen(wander_zeilen(ew["wander"] if ew else None, kurs, "Woche", "Stundenkerzen")),
                           "Wertwanderung · POC je Kerze"))
        teile.append(karte(zeilen(avwap_zeilen(r["avwap"], r["zange"], st_["profil"])), "AVWAP nach Shannon · Zange"))
    else:
        teile.append(karte(zeilen([("⚪", "Zu wenige Tageskerzen für die Tiefenanalyse")]), "Struktur nach Dalton"))
    tab = [(f"Titel {r['tk']}", tiefe.leistung(df["Close"])), ("S&P 500", tiefe.leistung(idx["Close"]))]
    for name, sym in ((f"Sektor {sektoren.SEKTOREN.get(r['sek'], '')}", r["sek"]), ("Branche", r["bra"])):
        if sym and r["alle"].get(sym) is not None:
            tab.append((f"{name} ({sym})", tiefe.leistung(r["alle"][sym]["Close"])))
    try:
        rel = zeichen.relativ(df, idx)
    except Exception:  # noqa: BLE001
        rel = None
    teile.append(karte(rs_tabelle(tab) + zeilen(rs_zeilen(df, idx, r["sis"], rel, zeichen.tage_gegen_markt(df, idx))),
                       "Relative Stärke"))
    cmf_l = [("Sektor", r["sek"], tiefe.cmf(r["alle"][r["sek"]]) if r["sek"] and r["alle"].get(r["sek"]) is not None else None),
             ("Branche", r["bra"], tiefe.cmf(r["alle"][r["bra"]]) if r["bra"] and r["alle"].get(r["bra"]) is not None else None),
             ("Titel", r["tk"], tiefe.cmf(df))]
    teile.append(karte(rang_tabelle(r["rang"], r["sek"]) + zeilen(geld_zeilen(r["rang"], r["sek"], titel._rueckenwind(r["tk"]),
                                                                              cmf_l)), "Geldfluss"))
    return seite("".join(teile), oben=8, unten=8)  # Layout



def material(tk):
    """Die Aussagezeilen der Seite als Text (für den Strategen, Micky 21.11.2026: die Einschätzung aus dem Material
    der Tiefenanalyse) – dieselben Zeilen wie auf der Seite."""
    import tiefe
    import titel
    import zeichen
    r = rechnen(tk.upper().strip())
    df, idx = r["df"], r["idx"]
    kurs = float(df["Close"].iloc[-1])
    et = r["ebenen"]["Tag"]
    z = []
    if et:
        z += struktur_zeilen(et["struktur"], et["alt"], r["fallen"], r["enge"], kurs)
        z += wander_zeilen(et["wander"], kurs, "Tag", "30-Minuten-Kerzen")
        z += avwap_zeilen(r["avwap"], r["zange"], et["struktur"]["profil"])
    try:
        rel = zeichen.relativ(df, idx)
    except Exception:  # noqa: BLE001
        rel = None
    z += rs_zeilen(df, idx, r["sis"], rel, zeichen.tage_gegen_markt(df, idx))
    cmf_l = [("Titel", r["tk"], tiefe.cmf(df))]
    z += geld_zeilen(r["rang"], r["sek"], titel._rueckenwind(r["tk"]), cmf_l)
    return [f"{a} {b}" for a, b in z]
