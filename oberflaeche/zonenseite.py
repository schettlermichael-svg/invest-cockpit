"""Titelseite des schlanken Cockpits (Micky 21.11.2026): Kopfzeile mit den drei Ebenen als Zeichen, der eine
Zonen-Trade mit Einigkeit, darunter der Zonenchart mit Reitern Woche · Tag · Stunde. Wenig Text, das Bild führt."""
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
    return {"tk": tk, "df": df, "ebenen": ebenen, "fuehrte": zonen.fuehrte(ebenen), "cmf": tiefe.cmf(df)["wert"],
            "laufend": bool(df.attrs.get("laufend"))}


def _karte_ebene(name, la, aktiv=False):
    if not la:
        return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:10px;padding:10px 12px">'
                f'<div style="font-size:12px;color:{TEXT_3}">{name} · {EBENE_ROLLE[name]}</div>'
                f'<div style="font-size:18px">⚪</div></div>')
    lo, hi = la["zone"]
    return (f'<div style="background:{KARTE};border:{2 if aktiv else 1}px solid {BLAU if aktiv else RAND};border-radius:10px;'
            f'padding:10px 12px"><div style="font-size:12px;color:{TEXT_3}">{name} · {EBENE_ROLLE[name]}</div>'
            f'<div style="font-size:20px;margin:2px 0">{la["pfeil"]} {la["zeichen"]} <span style="font-size:15px">'
            f'{t(la["wort"])} · {la["form"]}</span></div>'
            f'<div style="font-size:13px;color:{TEXT_2}">{zahl(lo)} – {zahl(hi)} · POC {zahl(la["poc"])}</div></div>')


def kopf(r):
    """Kopfzeile: Titel, Kurs, Einigkeit, Geld; je Ebene Phase und Zone; der Trade; Muster und Gedächtnis."""
    import zonen
    f, df = r["fuehrte"], r["df"]
    kurs = float(df["Close"].iloc[-1])
    c = r["cmf"]
    import tiefe
    geld = "🌞" if c is not None and c > tiefe.CMF_GRENZE else "❄️" if c is not None and c < -tiefe.CMF_GRENZE else "🟡"
    tr = f["trade"]
    if tr:
        seite_ = "long" if tr["richtung"] > 0 else "short"
        trade_html = (f'<div style="font-size:20px">{tr["zeichen"]} {t(tr["name"])} {seite_}</div>'
                      f'<div style="font-size:13px;color:{TEXT_2}">Einstieg {zahl(tr["einstieg"])} · Stopp '
                      f'{zahl(tr["stopp"])} · Ziel {zahl(tr["ziel"])} · CRV {zahl(tr["crv"] or 0, 1)}</div>')
    else:
        trade_html = '<div style="font-size:20px">⚪ kein Zonen-Trade</div>'
    alt = zonen.naechste(f["alt"]["Tag"], kurs) + zonen.naechste(f["alt"]["Woche"], kurs)
    naechste = min(alt, key=lambda z: abs((z["val"] + z["vah"]) / 2 - kurs), default=None)
    gedaechtnis = (f'🪝 offene alte Zone {zahl(naechste["val"], 0)}–{zahl(naechste["vah"], 0)}' if naechste else
                   "🟢 keine offene alte Zone")
    muster = {"innen": "🟢 Tageszone in der Wochenzone", "darüber": "🦬 Tageszone über der Wochenzone",
              "darunter": "🐻 Tageszone unter der Wochenzone", "überlappend": "🟡 Tageszone am Rand der Wochenzone",
              None: "⚪ Muster ungemessen"}[f["muster"]]
    zellen = "".join(_karte_ebene(n, f["lage"][n], n == "Tag") for n in zonen.EBENEN)
    return (f'<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">'
            f'<span style="font-size:28px;font-weight:600">{t(r["tk"])}</span>'
            f'<span style="font-size:18px;color:{TEXT}">{zahl(kurs)} $</span>'
            f'<span style="font-size:22px" title="Einigkeit der Ebenen">{zonen.einig_zeichen(f)}</span>'
            f'<span style="font-size:20px" title="Geld (CMF 20)">{geld}</span>'
            f'<span style="font-size:13px;color:{TEXT_3}">{df.index[-1]:%d.%m.%Y}{" · läuft" if r["laufend"] else ""}</span></div>'
            f'<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:12px">{zellen}'
            f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:10px;padding:10px 12px">'
            f'<div style="font-size:12px;color:{TEXT_3}">Trade</div>{trade_html}</div></div>'
            f'<div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;font-size:14px;color:{TEXT_2}">'
            f'<span>{muster}</span><span>{gedaechtnis}</span></div>')


def seite_zonen(tk, laufend=False, _stand=None):
    """{"kopf": HTML, "charts": {Ebene: SVG}} – app.py setzt die Reiter dazwischen."""
    import zonen
    import zonenchart
    r = rechnen(tk.upper().strip(), laufend)
    f = r["fuehrte"]
    charts = {n: zonenchart.bild(r["ebenen"][n], f["lage"][n], f["alt"][n], f["trade"] if n == "Tag" else None,
                                 r["laufend"] and n != "Woche") for n in zonen.EBENEN}
    return {"kopf": seite(karte(kopf(r)), oben=8, unten=0), "charts": charts,
            "legende": gestaltung.zeichen_legende()}
