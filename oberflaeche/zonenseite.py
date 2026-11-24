"""Titelseite des schlanken Cockpits (Micky 21./22.11.2026): Kopfzeile mit Rückenwind und den drei Ebenen (Base nach
Minervini/O'Neil in Woche und Tag, Balance in der Stunde), das eine Setup (Zone im Einklang mit dem Zirkel), darunter der Zonenchart mit Reitern Woche ·
Tag · Stunde. Wenig Text, das Bild führt."""
import os
import time

import pandas as pd

import gestaltung
from gestaltung import (BLAU, GELB, GRUEN, KARTE, PUNKT_KLEIN, RAND, ROT, TEXT, TEXT_2, TEXT_3, karte, punkt, seite,
                        t, zahl)

HIER = os.path.dirname(os.path.abspath(__file__))

EBENE_ROLLE = {"Woche": "Strömung", "Tag": "Zone", "Stunde": "Einstieg"}


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
          "Stunde": {"index": _stunde_bezug("SPY"), "sektor": _stunde_bezug(etf) if etf else None}}
    f = zonen.fuehrte(ebenen)
    import zeichen
    import zirkel                                   # das Setup ergibt sich aus dem Zirkel (Micky 22.11.2026)
    f["zone"] = f["trade"]                          # der Trade der Zone: der Chart zeichnet ihn immer (Micky 22.11.2026)
    f["trade"] = zirkel.setup(f["trade"], zeichen.zirkel(zeichen.von(tk)))
    cmf = tiefe.cmf(df)["wert"]
    return {"tk": tk, "df": df, "ebenen": ebenen, "fuehrte": f, "cmf": cmf,
            "laufend": bool(df.attrs.get("laufend")), "rs": rs}


def _stunde_bezug(symbol):
    """Stundenschlüsse eines Bezugs (SPY, Sektor-ETF) aus den gespeicherten 30-Minuten-Kerzen oder None."""
    import daten
    import tiefe
    import tpo_daten
    try:
        tages = daten.kurse_gespeichert(symbol)
        h = tiefe.stunde(tpo_daten.kerzen(symbol, tages, abruf=False)) if tages is not None else None
        return h["Close"] if h is not None and len(h) else None
    except Exception:  # noqa: BLE001 – Technik: ohne Datei keine Linie
        return None


def _karte_ebene(name, la, aktiv=False):
    rahmen = (f'background:{KARTE};border:{2 if aktiv else 1}px solid {BLAU if aktiv else RAND};border-radius:10px;'
              f'padding:10px 12px')
    kopf_ = f'<div style="font-size:12px;color:{TEXT_3}">{name} · {EBENE_ROLLE[name]}</div>'
    if not la:
        return f'<div style="{rahmen}">{kopf_}<div style="font-size:18px">⚪</div></div>'
    zeile2 = ""
    if la["zone"]:
        lo, hi = la["zone"]
        zeile2 = (f'{zahl(lo)} – {zahl(hi)}' + (f' · Pivot {zahl(la["pivot"])}' if la.get("pivot") and la["pivot"] < hi else "")
                  + f' · POC {zahl(la["poc"])}')
    return (f'<div style="{rahmen}">{kopf_}'
            f'<div style="font-size:20px;margin:2px 0">{la["pfeil"]} {la["zeichen"]} <span style="font-size:15px">'
            f'{t(la["wort"])}{(" · " + t(la["name"])) if la["name"] else ""}</span></div>'
            f'<div style="font-size:13px;color:{TEXT_2}">{zeile2}</div>'
            + (f'<div style="font-size:12px;color:{TEXT_3};margin-top:2px">{t(la["info"])}</div>' if la.get("info") else "")
            + '</div>')


def zirkel_html(tk):
    """Der Zirkel des Titels (Micky 22.11.2026): Leiste Basis → Aufwärts → Verteilung → Abwärts mit der laufenden Phase,
    darunter die Zeichen, die die Phase tragen, und die Keime des Gegenteils (gespeicherter Kreislauf des Nachtlaufs)."""
    import zeichen
    k = zeichen.von(tk)
    z = zeichen.zirkel(k)
    if not z:
        return (f'<div style="margin-top:10px;font-size:14px;color:{TEXT_3}">Zirkel: noch kein Kreislauf aus dem '
                f'Nachtlauf</div>')
    farbe = {1: TEXT_2, 2: GRUEN, 3: GELB, 4: ROT}
    teile = []
    for p_ in farbe:                                  # die vier Phasen in ihrer Reihenfolge
        an = p_ == z["phase"]
        teile.append(f'<div style="flex:1;text-align:center;padding:6px 4px;border-radius:8px;'
                     f'border:{2 if an else 1}px solid {farbe[p_] if an else RAND};'
                     f'color:{farbe[p_] if an else TEXT_3};font-size:{14 if an else 13}px">'  # Layout
                     f'{p_} · {zeichen.PHASE_NAME[p_]}'
                     + (f'<br><span style="font-size:12px">{z["wochen"]} Wo.</span>' if an and z["wochen"] else "")
                     + (f'<br><span style="font-size:12px">→ {z["ziel"]} zeichnet sich ab</span>'
                        if an and z["ziel"] else "") + '</div>')
    leiste = ('<div style="display:flex;gap:6px;align-items:stretch">' + '<span style="align-self:center">→</span>'.join(teile)
              + '<span style="align-self:center;color:' + TEXT_3 + '">↻</span></div>')
    if not z["phase"]:
        leiste = f'<div style="font-size:14px;color:{TEXT_2}">jung – noch keine Phase (unter 300 Handelstagen)</div>'
    keim_z = "🌱" if zeichen.KEIM_SEITE.get(z["phase"]) == "stärke" else "🍂"

    def spalte(titel, liste, zeichen_):
        inhalt = "".join(f'<div style="margin:2px 0">{zeichen_} {t(x)}</div>' for x in liste) or (
            f'<div style="color:{TEXT_3}">–</div>')
        return (f'<div style="flex:1;min-width:260px"><div style="font-size:12px;color:{TEXT_3};margin-bottom:2px">'
                f'{titel}</div><div style="font-size:13px;color:{TEXT_2}">{inhalt}</div></div>')
    traeger_z = "🍂" if keim_z == "🌱" else "🌱"
    sym, wort, grund = zeichen.halt(z)                # Halt der Phase (Micky 24.11.2026)
    halt_html = (f'<div style="margin-top:8px;font-size:14px;color:{TEXT}">{sym} <b>{wort}</b>'
                 + (f' – {t(grund)}' if grund else "") + f'<span style="color:{TEXT_3};font-size:12px"> · 🏰 hält · '
                 f'🌊 Welle: ein Riss, die Phase trägt mehr · ⛈️ Sturm: der Riss wiegt so schwer wie das, was trägt'
                 f'</span></div>') if sym else ""
    return (f'<div style="margin-top:12px"><div style="font-size:12px;color:{TEXT_3};margin-bottom:4px">Zirkel · Stand '
            f'{k.get("stand", "")}</div>{leiste}{halt_html}'
            f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px">'
            + spalte(z["rolle"][0], z["traegt"], traeger_z if z["phase"] else "•")
            + (spalte(z["rolle"][1], z["keim"], keim_z) if z["phase"] else "") + '</div></div>')


def kopf(r):
    """Kopfzeile: Titel, Kurs, Geld; die Rückenwind-Zeile wie in der Liste; je Ebene Zone und Phase; der Trade.
    Aufgeräumt 22.11.2026: ohne Lagebeurteilung, Gedächtnis, PbD, Einigkeit und Muster."""
    import tiefe
    import zonen
    f, df = r["fuehrte"], r["df"]
    kurs = float(df["Close"].iloc[-1])
    c = r["cmf"]
    geld = "🌞" if c is not None and c > tiefe.CMF_GRENZE else "❄️" if c is not None and c < -tiefe.CMF_GRENZE else "🟡"
    tr = f["trade"]
    if tr:
        seite_ = "long" if tr["richtung"] > 0 else "short"
        trade_html = (f'<div style="font-size:20px">{tr["zeichen"]} {t(tr["name"])} {seite_}</div>'
                      f'<div style="font-size:13px;color:{TEXT_2}">{"Auslöser" if tr["wartet"] else "Einstieg"} '
                      f'{zahl(tr["einstieg"])}{" (Schluss darüber mit Volumen)" if tr["wartet"] else ""} · Stopp '
                      f'{zahl(tr["stopp"])} · {tr["ampel"]} Risiko {zahl(tr["risiko"], 1)} %</div>')
        import zirkel
        if zirkel.dreifach(r["tk"], tr):               # Kurs, Geld und Zahlen grün (Micky 23.11.2026)
            trade_html += (f'<div style="font-size:13px;color:{GRUEN}">▲▲▲ dreifacher Rückenwind – Kurs, Geld und '
                           f'Zahlen grün</div>')
        gw = zirkel.gegenwind(r["tk"], tr)              # die Branche steht gegen die Richtung (Weinstein)
        if gw:
            trade_html += f'<div style="font-size:13px;color:{GELB}">{t(gw)} – Gegenwind der Gruppe</div>'
    else:
        trade_html = '<div style="font-size:20px">⚪ kein Setup</div>'
    import rueckenwind_seite
    karten_ = rueckenwind_seite.titel_karten(r["tk"])   # drei Karten Front · Nachschub · Fundament (Micky 23.11.2026)
    wind_html = ('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;'
                 'margin-top:10px">'   # Layout
                 + "".join(f'<div style="border:1px solid {RAND};border-radius:10px;padding:10px 12px">'
                           f'<div style="display:flex;align-items:center;gap:8px;font-size:14px;font-weight:600">'
                           f'{punkt(amp, PUNKT_KLEIN)}{t(kopf_)}</div>'
                           + "".join(f'<div style="font-size:13px;color:{TEXT_2};margin-top:4px;line-height:1.4">{t(z)}</div>'
                                     for z in zeilen_) + '</div>' for kopf_, amp, zeilen_ in karten_)
                 + '</div>') if karten_ else (
        f'<div style="margin-top:10px;font-size:14px;color:{TEXT_3}">Rückenwind: noch kein Stand des Nachtlaufs</div>')
    zellen = "".join(_karte_ebene(n, f["lage"][n], n == "Tag") for n in zonen.EBENEN)
    return (f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">'
            f'<span style="font-size:28px;font-weight:600">{t(r["tk"])}</span>'
            f'<span style="font-size:18px;color:{TEXT}">{zahl(kurs)} $</span>'
            f'<span style="font-size:20px" title="Geld (CMF 20)">{geld}</span>'
            f'<span style="font-size:15px;color:{TEXT}" title="keine Festung über (✈️) bzw. unter (✈️↓) dem Kurs – '
            f'Livermores Linie des geringsten Widerstands">{rueckenwind_seite.bahn(f.get("frei"))}</span>'
            f'<span style="font-size:13px;color:{TEXT_3}">{df.index[-1]:%d.%m.%Y}{" · läuft" if r["laufend"] else ""}</span></div>'
            f'{wind_html}{zirkel_html(r["tk"])}'
            f'<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px">{zellen}'
            f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:10px;padding:10px 12px">'
            f'<div style="font-size:12px;color:{TEXT_3}">Setup</div>{trade_html}</div></div>')


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


def chart(r, ebene, gd=(), anker=(), linien_=(), profil_ab=None):
    """Zonenchart einer Ebene aus der Rechnung von seite_zonen."""
    import zonen
    import zonenchart
    f = r["fuehrte"]
    rahmen = None                                                     # in der Stunde die Base des Tages als Rahmen
    la_tag = f["lage"]["Tag"]
    if ebene == "Stunde" and la_tag and la_tag["zone"]:
        rahmen = (la_tag, pd.Timestamp(la_tag["beginn"]), "Tag")
    linie = f["trade"] or (f.get("zone") and dict(f["zone"], kein_setup=True))   # immer Linien (Micky 22.11.2026)
    return zonenchart.bild(r["ebenen"][ebene], f["lage"][ebene], linie if ebene == "Tag" else None,
                           r["laufend"] and ebene != "Woche", rahmen, r["rs"][ebene], gd, anker, linien_,
                           zonen.profil_seit(r["ebenen"][ebene], profil_ab) if profil_ab is not None else None,
                           f["festungen"][ebene], f["basis"], r["tk"])


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
