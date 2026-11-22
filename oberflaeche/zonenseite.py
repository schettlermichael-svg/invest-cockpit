"""Titelseite des schlanken Cockpits (Micky 21./22.11.2026): Kopfzeile mit Rückenwind und den drei Ebenen (Base nach
Minervini/O'Neil in Woche und Tag, Balance in der Stunde), der eine Trade, darunter der Zonenchart mit Reitern Woche ·
Tag · Stunde. Wenig Text, das Bild führt."""
import pandas as pd

import gestaltung
from gestaltung import BLAU, KARTE, RAND, TEXT, TEXT_2, TEXT_3, karte, seite, t, zahl

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
    try:
        avwaps = tiefe.avwap_liste(df, zt)[0]
    except Exception:  # noqa: BLE001 – Technik: ohne AVWAP keine AVWAP-Festung
        avwaps = []
    f = zonen.fuehrte(ebenen, avwaps)
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
    else:
        trade_html = '<div style="font-size:20px">⚪ kein Trade</div>'
    import rueckenwind_seite
    wind = rueckenwind_seite.titel_zeile(r["tk"])
    wind_html = (f'<div style="margin-top:10px;font-size:15px;color:{TEXT}">Rückenwind: '
                 + ' <span style="color:{0}">·</span> '.format(TEXT_3).join(t(w) for w in wind) + '</div>') if wind else (
        f'<div style="margin-top:10px;font-size:14px;color:{TEXT_3}">Rückenwind: noch kein Stand des Nachtlaufs</div>')
    zellen = "".join(_karte_ebene(n, f["lage"][n], n == "Tag") for n in zonen.EBENEN)
    return (f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">'
            f'<span style="font-size:28px;font-weight:600">{t(r["tk"])}</span>'
            f'<span style="font-size:18px;color:{TEXT}">{zahl(kurs)} $</span>'
            f'<span style="font-size:20px" title="Geld (CMF 20)">{geld}</span>'
            f'<span style="font-size:13px;color:{TEXT_3}">{df.index[-1]:%d.%m.%Y}{" · läuft" if r["laufend"] else ""}</span></div>'
            f'{wind_html}'
            f'<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px">{zellen}'
            f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:10px;padding:10px 12px">'
            f'<div style="font-size:12px;color:{TEXT_3}">Trade</div>{trade_html}</div></div>')


def seite_zonen(tk, laufend=False, _stand=None):
    """{"kopf": HTML, "r": Rechnung, "legende": HTML} – den Chart zeichnet app.py mit chart() (Durchschnitte und
    eigener AVWAP nach Wahl, ohne neue Rechnung)."""
    r = rechnen(tk.upper().strip(), laufend)
    import zonenchart
    return {"kopf": seite(karte(kopf(r)), oben=8, unten=0), "r": r,  # Layout
            "legende": zonenchart.legende() + gestaltung.zeichen_legende()}


def chart(r, ebene, gd=(), anker=(), linien_=(), profil_ab=None):
    """Zonenchart einer Ebene aus der Rechnung von seite_zonen."""
    import zonen
    import zonenchart
    f = r["fuehrte"]
    rahmen = None                                                     # in der Stunde die Base des Tages als Rahmen
    la_tag = f["lage"]["Tag"]
    if ebene == "Stunde" and la_tag and la_tag["zone"]:
        rahmen = (la_tag, pd.Timestamp(la_tag["beginn"]), "Tag")
    return zonenchart.bild(r["ebenen"][ebene], f["lage"][ebene], f["trade"] if ebene == "Tag" else None,
                           r["laufend"] and ebene != "Woche", rahmen, r["rs"][ebene], gd, anker, linien_,
                           zonen.profil_seit(r["ebenen"][ebene], profil_ab) if profil_ab is not None else None,
                           f["festungen"][ebene])


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
