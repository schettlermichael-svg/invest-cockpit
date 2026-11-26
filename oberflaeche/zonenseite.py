"""Titelseite des schlanken Cockpits (Micky 21./22.11.2026; seit 26.11.2026 der Lagebericht über vier Ebenen): Kopfzeile,
darunter der Bericht (Urteil mit den drei Toren, Woche · Tag · 4 Stunden · Stunde neben der Leiter, Beobachten, Story und
Strömung), darunter der Zonenchart mit Reitern je Ebene."""
import os
import time

import pandas as pd

import gestaltung
from gestaltung import (BLAU, GELB, GRUEN, PUNKT_KLEIN, RAND, ROT, TEXT, TEXT_2, TEXT_3, karte, punkt, seite,
                        t, zahl)

HIER = os.path.dirname(os.path.abspath(__file__))

def rechnen(tk, laufend=False):
    """Kurse, feinere Kerzen, drei Ebenen (tiefe.ebene) und die Fährte (zonen.fuehrte)."""
    import avwap
    import daten
    import quellen
    import tiefe
    import tpo_daten
    import zonen
    df = daten.kurse(tk, laufend=laufend)
    df.attrs["ticker"] = tk
    try:
        tpo_daten.merken(tk)
        d30 = tpo_daten.kerzen(tk, df.iloc[:-1] if df.attrs.get("laufend") else df, abruf=True)
        if df.attrs.get("laufend"):
            heute = tpo_daten.heute(tk)
            if heute is not None:
                d30 = pd.concat([d30, heute]) if d30 is not None else heute
        if d30 is not None:
            d30 = d30[~d30.index.duplicated(keep="last")].sort_index()
    except Exception:  # noqa: BLE001 – ohne Netz bleibt der Speicher
        d30 = tiefe.dreissig(df)
    try:
        zt = avwap.zahlentag(df, quellen.laden(tk)["gewinne"])
    except Exception:  # noqa: BLE001 – ohne Zahlen kein Zahlentag
        zt = None
    ebenen = {"Woche": tiefe.ebene("Woche", tiefe.woche(df), d30, zt, tage=df),
              "Tag": tiefe.ebene("Tag", df, d30, zt),
              "4 Stunden": tiefe.ebene("4 Stunden", tiefe.vier_stunden(d30), d30, zt),
              "Stunde": tiefe.ebene("Stunde", tiefe.stunde(d30), d30, zt)}
    import sektoren
    try:
        index = daten.kurse(daten.INDEX)["Close"]
    except Exception:  # noqa: BLE001 – ohne Index keine RS-Linie
        index = None
    etf = sektoren.sektor_von((daten.steckbrief(tk) or {}).get("sektor", ""))
    try:
        sektor = daten.kurse(etf)["Close"] if etf else None
    except Exception:  # noqa: BLE001
        sektor = None
    rs = {"Woche": {"index": index, "sektor": sektor}, "Tag": {"index": index, "sektor": sektor},
          **{n: {"index": _stunde_bezug("SPY", n), "sektor": _stunde_bezug(etf, n) if etf else None}
             for n in tiefe.INTRADAY}}
    f = zonen.fuehrte(ebenen)
    import zeichen
    import zirkel                                   # Livermore liefert das Setup, der Zirkel bestätigt (Micky 25.11.2026)
    f["trade"] = zirkel.setup(f["trade"], zeichen.zirkel(zeichen.von(tk)))
    cmf = tiefe.cmf(df)["wert"]
    return {"tk": tk, "df": df, "ebenen": ebenen, "fuehrte": f, "cmf": cmf,
            "laufend": bool(df.attrs.get("laufend")), "rs": rs}


def _stunde_bezug(symbol, ebene="Stunde"):
    """Stunden- bzw. 4-Stunden-Schlüsse eines Bezugs (SPY, Sektor-ETF) aus den gespeicherten 30-Minuten-Kerzen oder
    None."""
    import daten
    import tiefe
    import tpo_daten
    try:
        tages = daten.kurse_gespeichert(symbol)
        takt = tiefe.vier_stunden if ebene == "4 Stunden" else tiefe.stunde
        h = takt(tpo_daten.kerzen(symbol, tages, abruf=False)) if tages is not None else None
        return h["Close"] if h is not None and len(h) else None
    except Exception:  # noqa: BLE001 – Technik: ohne Datei keine Linie
        return None


def _setup_html(r):
    """Unser Setup in Zeilen (Livermores zwei Hälften, Stopp, Risiko, Zirkel, dreifacher Rückenwind, Gegenwind der
    Gruppe) – oder "" ohne Setup."""
    tr = r["fuehrte"]["trade"]
    if not tr:
        return ""
    ueber_ = "über" if tr["richtung"] > 0 else "unter"
    if tr.get("aufstocken"):
        ein_ = ("½ antasten + ½ aufgestockt – 📒 erreicht" if tr.get("aufgestockt") else
                f'½ antasten beim Schluss {ueber_} {zahl(tr["pivot"])}' + (" mit Volumen" if tr["wartet"] else "")
                + f' · ½ aufstocken bei 📒 {zahl(tr["aufstocken"])}')
    else:
        ein_ = f'Einstieg {zahl(tr["einstieg"])}'
    z = [f'<span title="Livermore: erst eine Probe, nur im Gewinn nachlegen, nie verbilligen – kommt der Fehlausbruch, '
         f'ist nur die Hälfte im Feuer">{t(ein_)}</span> · Stopp {zahl(tr["stopp"])} · {tr["ampel"]} Risiko '
         f'{zahl(tr["risiko"], 1)} %']
    if tr.get("zirkel"):
        z.append(f'<span style="color:{GRUEN if tr["zirkel"] == "✓" else GELB}">{tr["zirkel"]} '
                 f'{"der Zirkel trägt" if tr["zirkel"] == "✓" else "gegen den Zirkel"}: {t(tr["zirkel_grund"])}</span>')
    import zirkel
    if zirkel.dreifach(r["tk"], tr):               # Kurs, Geld und Zahlen grün (Micky 23.11.2026)
        z.append(f'<span style="color:{GRUEN}">▲▲▲ dreifacher Rückenwind – Kurs, Geld und Zahlen grün</span>')
    gw = zirkel.gegenwind(r["tk"], tr)              # die Branche steht gegen die Richtung (Weinstein)
    if gw:
        z.append(f'<span style="color:{GELB}">{t(gw)} – Gegenwind der Gruppe</span>')
    return "".join(f'<div style="font-size:14px;color:{TEXT_2};margin-top:2px">{x}</div>' for x in z)


def _marke(text, farbe, grund=""):
    return (f'<span title="{t(grund)}" style="background:{farbe}1F;color:{farbe};border-radius:8px;padding:5px 11px;'
            f'font-weight:600;font-size:14px">{t(text)}</span>')


def _urteil(r, be):
    """Urteil · drei Tore (Sharp): Richtung, Ort, Auslöser als drei Marken, darunter ein Satz zur Richtung und unser
    Setup."""
    import tore
    tr = r["fuehrte"]["trade"]
    df = r["df"].dropna(subset=["High", "Low", "Close"])
    to = tore.tore(df, tr, bool(r.get("laufend")))
    ri, ot = to["richtung"], to["ort"]
    wert = (ri or {}).get("wert")
    f_r = GRUEN if wert == "auf" else ROT if wert == "ab" else GELB
    m_r = _marke(f'Richtung {to["r"] + " " if to["r"] else ""}{ {"auf": "aufwärts", "ab": "abwärts"}.get(wert, "offen")}',
                 f_r, "Zwei-Kerzen-Regel: letzte abgeschlossene Wochen- und Tageskerze; bei gemischt entscheidet die "
                      "Lage der Woche, ruht sie, die Tageskerze")
    ort_ = tore.ort_text(ot, (tr or {}).get("richtung"))
    f_o = ROT if to["o"] == "✗" else GRUEN if to["o"] == "✓" else (GELB if ot and (ot["chop"] or ot["weit"]) else TEXT_2)
    m_o = _marke(f'Ort {to["o"] + " " if to["o"] else ""}{ort_ or "–"}', f_o,
                 "Lage in der Spanne, Weg voraus (3 ATR: sauber oder unruhig), Chop, weit gelaufen")
    if tr:
        m_a = _marke(f'Auslöser {to["a"]} {tr["zeichen"]} {tr["name"]} {"long" if tr["richtung"] > 0 else "short"}',
                     GRUEN if to["a"].startswith("✓") else BLAU, "unser Setup: ½ antasten an der Kante, ½ aufstocken bei 📒")
    else:
        m_a = _marke("Auslöser: keiner – kein Setup", TEXT_2, "kein Setup auf dem Tag")
    satz = []
    if ri:
        k_ = ri["kerzen"]
        satz.append(f'Woche {tore.KERZE[k_["woche"]]}, Tag {tore.KERZE[k_["tag"]]}: {ri["grund"]}.')
    ei = r["fuehrte"].get("einigkeit")
    if ei and ei["alle"]:
        satz.append("⬆ Einigkeit: Vormarsch auf allen Ebenen." if ei["alle"] == "auf" else
                    "⬇ Einigkeit: Rückzug auf allen Ebenen.")
    return (f'<div style="font-size:12px;font-weight:600;letter-spacing:.06em;color:{TEXT_3}">URTEIL · DREI TORE</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:6px 0">{m_r}{m_o}{m_a}</div>'
            f'<div style="font-size:14px;color:{TEXT_2}">{t(" ".join(satz))}</div>' + _setup_html(r))


EBENE_TITEL = {"Woche": "Woche · das große Bild", "Tag": "Tag · das Schlachtfeld",
               "4 Stunden": "4 Stunden · die Fronten verschieben sich", "Stunde": "Stunde · wo der nächste Schuss fällt"}


def _ebene_html(n, b):
    import bericht
    farbe = {"AT": GRUEN, "AB": ROT}.get((b or {}).get("spalte"), GELB)
    kopf_ = (f'<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap">'
             f'<b style="font-size:15px">{EBENE_TITEL[n]}</b>'
             f'<span style="font-size:13px;color:{farbe}">{t(bericht.kurzurteil(b))}</span></div>')
    text = " ".join(bericht.saetze(b)) if b else "Zu wenige Kerzen für das Notizbuch."
    return (f'<div style="border:1px solid {RAND};border-radius:10px;padding:12px 14px">{kopf_}'
            f'<div style="font-size:14px;color:{TEXT_2};margin-top:4px;line-height:1.5">{t(text)}</div></div>')


def _beobachten_html(be, r):
    import bericht
    import tore
    tr = r["fuehrte"]["trade"]
    ri = tore.richtung(r["df"].dropna(subset=["High", "Low", "Close"]), bool(r.get("laufend")))
    bo = bericht.beobachten(be, tr)
    spalten = (("Long beobachten", GRUEN, bo["long"]), ("Short beobachten", ROT, bo["short"]),
               ("Gegenzeichen", GELB, bericht.gegenzeichen(be, (ri or {}).get("wert"))))
    return ('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px">'
            + "".join(f'<div><b style="color:{f_}">{k_}</b>'
                      + "".join(f'<div style="font-size:14px;color:{TEXT_2};margin-top:3px">{t(z)}</div>' for z in zs)
                      + '</div>' for k_, f_, zs in spalten) + '</div>')


def _zirkel_zeile(tk):
    """Der Zirkel in einer Zeile (Micky 26.11.2026): Jahreszeit, Dauer, was sich abzeichnet, der Halt – Träger und
    Keime im Hinweis."""
    import zeichen
    z = zeichen.zirkel(zeichen.von(tk))
    if not z:
        return "🔄 Zirkel: noch kein Kreislauf aus dem Nachtlauf", ""
    if not z["phase"]:
        return "🔄 Zirkel: jung – noch keine Jahreszeit (unter 300 Handelstagen)", ""
    sym, wort, grund = zeichen.halt(z)
    return (f'🔄 Zirkel: Jahreszeit {z["phase"]} · {zeichen.PHASE_NAME[z["phase"]]}'
            + (f' · {z["wochen"]} Wo.' if z["wochen"] else "") + (f' · → {z["ziel"]} zeichnet sich ab' if z["ziel"] else "")
            + (f' · {sym} {wort}' + (f' – {grund}' if grund else "") if sym else ""),
            f'{z["rolle"][0]}: {"; ".join(z["traegt"]) or "–"} · {z["rolle"][1]}: {"; ".join(z["keim"]) or "–"}')


def _key_price(r):
    import livermore
    nb = livermore.notizbuch(r["df"])
    try:
        kp = livermore.key_price(r["tk"], r["df"])            # Key Price mit der Schwesteraktie
    except Exception:  # noqa: BLE001 – ohne Rückenwind-Lauf oder Kurse der Schwester: ohne Key Price
        kp = None
    if not (kp and kp["nb"] and nb):
        return ""
    gleich = kp["nb"].get("trend") == nb.get("trend")
    return (f'🔑 Key Price mit {kp["schwester"]} ({kp["branche"]}): {livermore.spalte_text(kp["nb"])} · '
            + ("✓ bestätigt den Trend" if gleich else "✗ bestätigt den Trend nicht – vielleicht ein Einzelfall"))


def _story_html(r):
    """Story und Strömung: die drei Fragen des Rückenwinds (Kraft, Nachschub, Fundament) mit allen ihren Zeilen, das
    Geld des Titels (CMF 20), der Zirkel und der Key Price in je einer Zeile."""
    import rueckenwind_seite
    import tiefe
    karten_ = rueckenwind_seite.titel_karten(r["tk"], r["fuehrte"].get("frei"))
    c = r["cmf"]
    geld = ("🌞 Geld fließt zu" if c is not None and c > tiefe.CMF_GRENZE else
            "❄️ Geld fließt ab" if c is not None and c < -tiefe.CMF_GRENZE else "🟡 Geld neutral")
    geld += f' (CMF 20 {zahl(c, 2)})' if c is not None else ""
    spalten = []
    for i, (kopf_, amp, zeilen_) in enumerate(karten_):
        zeilen_ = list(zeilen_) + ([geld] if i == 1 else [])
        spalten.append(f'<div><div style="display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600">'
                       f'{punkt(amp, PUNKT_KLEIN)}{t(kopf_)}</div>'
                       + "".join(f'<div style="font-size:13px;color:{TEXT_2};margin-top:3px">{t(z)}</div>' for z in zeilen_)
                       + '</div>')
    inhalt = ('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px">'
              + "".join(spalten) + '</div>') if spalten else (
        f'<div style="font-size:14px;color:{TEXT_3}">Rückenwind: noch kein Stand des Nachtlaufs · {t(geld)}</div>')
    zz, zz_hinweis = _zirkel_zeile(r["tk"])
    kp = _key_price(r)
    unten = (f'<div style="font-size:13px;color:{TEXT_2};margin-top:10px" title="{t(zz_hinweis)}">{t(zz)}</div>'
             + (f'<div style="font-size:13px;color:{TEXT_2};margin-top:2px" title="Livermore: ein Trendwechsel gilt erst, '
                f'wenn auch der Key Price (zwei Aktien einer Gruppe zusammen) ihn zeigt">{t(kp)}</div>' if kp else ""))
    return f'<b style="font-size:15px">Story und Strömung</b><div style="margin-top:8px">{inhalt}</div>{unten}'


def _block(inhalt):
    return f'<div style="border:1px solid {RAND};border-radius:12px;padding:14px 16px;margin-top:12px">{inhalt}</div>'


def lagebericht(r):
    """Der Lagebericht über alle Ebenen (Micky 26.11.2026, Analyse HWM): Urteil mit den drei Toren, je Ebene zwei, drei
    Sätze neben der Leiter aller Stellungen, was ich beobachten würde (long, short, Gegenzeichen), Story und Strömung.
    Dieselben Regeln auf jeder Ebene (bericht.py) – Titelseite, Depot und Analyse zeigen ihn gleich."""
    import bericht
    import leiter
    be = bericht.alle(r)
    ebenen_ = "".join(_ebene_html(n, b) for n, b in be.items())
    mitte = (f'<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:12px;align-items:flex-start">'
             f'<div style="flex:999 1 560px;min-width:0;display:flex;flex-direction:column;gap:10px">{ebenen_}</div>'
             f'<div style="flex:1 1 340px;min-width:0;border:1px solid {RAND};border-radius:10px;padding:12px 14px">'
             f'<b style="font-size:15px">Die Leiter · alle Ebenen</b>{leiter.bild(bericht.leiter(be))}</div></div>')
    return (_block(_urteil(r, be)) + mitte + _block(_beobachten_html(be, r)) + _block(_story_html(r)))


def kopf(r):
    """Kopfzeile (Titel, Name, Kurs, Stand) und darunter der Lagebericht – Kacheln, Zirkel-Block und die alten
    Kopfzeilen sind im Bericht aufgegangen (Micky 26.11.2026)."""
    import daten
    import titel
    df = r["df"]
    kurs = float(df["Close"].iloc[-1])
    name = daten.kurzname(r["tk"])
    return (f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">'
            f'<span style="font-size:28px;font-weight:700">{t(r["tk"])}</span>'
            + (f'<span style="font-size:15px;color:{TEXT_2}">{t(name)}</span>' if name else "")
            + f'<span style="font-size:22px;font-weight:600;color:{TEXT}">{zahl(kurs)} $</span>'
            f'<span style="font-size:13px;color:{TEXT_3}">Schluss {df.index[-1]:%d.%m.%Y}'
            f'{" · läuft" if r["laufend"] else ""}</span>'
            f'<a href="{titel.tv_link(r["tk"])}" target="_blank" rel="noopener" style="margin-left:auto;font-size:14px;'
            f'font-weight:600;text-decoration:none;border:1px solid {RAND};border-radius:8px;padding:6px 14px;'
            f'color:{BLAU}">TradingView ↗</a></div>' + lagebericht(r))


def seite_zonen(tk, laufend=False, _stand=None):
    """{"kopf": HTML, "r": Rechnung, "legende": HTML} – den Chart zeichnet app.py mit chart() (Durchschnitte und
    eigener AVWAP nach Wahl, ohne neue Rechnung)."""
    r = rechnen(tk.upper().strip(), laufend)
    import zonenchart
    return {"kopf": seite(karte(kopf(r)), oben=8, unten=0), "r": r,  # Layout
            "legende": zonenchart.legende() + gestaltung.zeichen_legende()}


# ── Schrank (06.11.2026, seit 22.11.2026 für diese Titelseite): der Nachtlauf baut die Titelseiten der Rückenwind-Titel
# in Garde, Angriff und Vorhut und der Watchlist vor und legt sie ab, damit ein Klick sofort öffnet. Gültig, solange
# danach weder Programm noch Depot geändert wurden und höchstens 30 Stunden; „Kurse aktualisieren“ rechnet neu.
ABLAGE = os.path.join(HIER, "..", "daten", "schrank")
ALTER_MAX = 30 * 3600            # abgelegte Seiten gelten höchstens 30 Stunden (der Nachtlauf baut sie täglich neu)


def codezeit():
    """Jüngste Änderungszeit der Programmdateien (kern, oberflaeche)."""
    return max(os.path.getmtime(os.path.join(HIER, "..", d, f)) for d in ("kern", "oberflaeche")
               for f in os.listdir(os.path.join(HIER, "..", d)) if f.endswith(".py"))


def ablage_grenze():
    """Abgelegte Titelseiten älter als das Programm oder das Depot gelten als veraltet."""
    import depot
    return max([codezeit()] + ([os.path.getmtime(depot.DATEI)] if os.path.exists(depot.DATEI) else []))


def _pfad(tk):
    return os.path.join(ABLAGE, f"{tk.upper()}.pkl.gz")


def vorbauen(tk):
    """Titelseite bauen und in den Schrank legen (Nachtlauf, Schrank-Lauf) → True, wenn abgelegt."""
    import gzip
    import pickle
    try:
        teile = seite_zonen(tk)
        os.makedirs(ABLAGE, exist_ok=True)
        tmp = f"{_pfad(tk)}.{os.getpid()}.neu"        # App und Hintergrundlauf können gleichzeitig ablegen
        with gzip.open(tmp, "wb", compresslevel=3) as f:  # Layout
            pickle.dump(teile, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, _pfad(tk))
        return True
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Schrank steht trotzdem
        return False


def frisch(tk, grenze=None):
    """Liegt eine gültige Titelseite im Schrank (jünger als Programm, Depot und 30 Stunden)?"""
    try:
        zeit = os.path.getmtime(_pfad(tk))
    except OSError:
        return False
    return zeit >= (grenze or ablage_grenze()) and time.time() - zeit < ALTER_MAX


def abgelegt(tk):
    """Gültige Titelseite aus dem Schrank oder None (dann wird gerechnet)."""
    import gzip
    import pickle
    if not frisch(tk):
        return None
    try:
        with gzip.open(_pfad(tk), "rb") as f:
            return pickle.load(f)
    except Exception:  # noqa: BLE001 – dann wird gerechnet
        return None


def chart(r, ebene, gd=(), anker=(), linien_=(), profil_ab=None, position=None):
    """Zonenchart einer Ebene aus der Rechnung von seite_zonen; position = die gehaltene Position (Depot-Seite) – dann
    zeichnet der Chart ihre Linien statt des Schlachtplans eines neuen Setups."""
    import zonen
    import zonenchart
    f = r["fuehrte"]
    rahmen = None                                                     # in der Stunde die Base des Tages als Rahmen
    la_tag = f["lage"]["Tag"]
    import tiefe
    if ebene in tiefe.INTRADAY and la_tag and la_tag["zone"]:
        rahmen = (la_tag, pd.Timestamp(la_tag["beginn"]), "Tag")
    return zonenchart.bild(r["ebenen"][ebene], f["lage"][ebene], f["trade"] if ebene == "Tag" and not position else None,
                           r["laufend"] and ebene != "Woche", rahmen, r["rs"][ebene], gd, anker, linien_,
                           zonen.profil_seit(r["ebenen"][ebene], profil_ab) if profil_ab is not None else None,
                           f["stellungen"][ebene], f["basis"], r["tk"], position if ebene == "Tag" else None)


# ── Eigene Anker (Micky 21.11.2026): AVWAP 1 und 2, dazu das Profil – je Titel und Ebene, als Zeitpunkt gespeichert ──
ANKER_DATEI = "avwap_anker.json"
ANKER_PLAETZE = 3          # AVWAP 1, AVWAP 2, Profil
PROFIL_PLATZ = 2


def _anker_pfad():
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daten", ANKER_DATEI)


def anker_laden(tk, ebene):
    """[AVWAP 1, AVWAP 2, Profil] – je Zeitpunkt oder None."""
    from dateien import json_lesen
    w = ((json_lesen(_anker_pfad(), {}) or {}).get(tk.upper()) or {}).get(ebene) or []
    return [pd.Timestamp(x) if x else None for x in (list(w) + [None] * ANKER_PLAETZE)[:ANKER_PLAETZE]]


def anker_setzen(tk, ebene, k, tag):
    """Anker k (0, 1 = AVWAP, 2 = Profil) auf den Zeitpunkt tag setzen (None löscht ihn)."""
    from dateien import json_lesen, json_schreiben
    alle = json_lesen(_anker_pfad(), {}) or {}
    w = (list(alle.setdefault(tk.upper(), {}).get(ebene) or []) + [None] * ANKER_PLAETZE)[:ANKER_PLAETZE]
    w[k] = f"{pd.Timestamp(tag):%Y-%m-%d %H:%M}" if tag is not None else None
    alle[tk.upper()][ebene] = w
    json_schreiben(_anker_pfad(), alle)


# ── Livermores Notizbuch auf der Titelseite (Micky 25.11.2026): Spalte im Kopf, Tabelle unter dem Chart ──
NOTIZBUCH_ZEILEN = 30      # Layout: die letzten 30 Einträge in der Tabelle


def notizbuch_tabelle(r):
    """Livermores Notizbuch wie im Buch: je Eintrag eine Zeile, der Kurs in seiner Spalte; Pivotal Points mit ═."""
    import livermore
    df = r.get("df")
    nb = livermore.notizbuch(df) if df is not None else None
    if not nb:
        return None
    pp = {(p_["tag"], round(p_["preis"], 2)): p_["farbe"] for p_ in nb["pivotal"]}
    zeilen = []
    for tag, sp, preis in nb["eintraege"][-NOTIZBUCH_ZEILEN:]:
        z_ = {"Tag": f"{tag:%d.%m.%Y}"} | {livermore.SPALTEN[k]: "" for k in livermore.REIHE}
        marke = pp.get((tag, round(preis, 2)))
        z_[livermore.SPALTEN[sp]] = f'{zahl(preis)}' + (" ═" if marke else "")
        zeilen.append(z_)
    return pd.DataFrame(zeilen[::-1])
