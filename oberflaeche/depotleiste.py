"""Depotleiste und Depot-Hitze (Übersicht) und Karte „Position und Risiko“ (Titelseite) – Schritt 9, 04.11.2026."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import daten  # noqa: E402
import depot  # noqa: E402
from gestaltung import RAND, TEXT_2, TEXT_3, ampelzeile, karte, punkt, t, zahl  # noqa: E402


def _datum(x):
    import pandas as pd
    try:
        return f"{pd.Timestamp(x):%d.%m.%Y}"
    except Exception:  # noqa: BLE001
        return x or ""


def _kurs(tk):
    df = daten.kurse_gespeichert(tk)
    return (float(df["Close"].iloc[-1]), df) if df is not None and len(df) else (None, None)


def leiste():
    """Übersicht: Depot-Hitze und je Position eine Zeile mit Abstand zum Stopp und dem wichtigsten Zeichen."""
    d = depot.laden()
    if not d.get("konto"):
        return karte(f'<div style="font-size:15px;color:{TEXT_2}">Noch kein Konto eingetragen – oben „⚙ Konto und Risiko“. '
                     f'Danach rechnet die App Stückzahl und Risiko auf jeder Karte und die Depot-Hitze.</div>', "Depot")
    h = depot.hitze(d)
    kopf = (f'<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:baseline">'
            f'<div title="Summe des offenen Risikos (Einstieg bis Stopp) aller Positionen gegen das Konto; Grenze '
            f'{zahl(h["max"], 0)} %" style="display:flex;gap:10px;align-items:center">{punkt(h["ampel"], 16)}'
            f'<span style="font-size:26px;font-weight:600">{zahl(h["pct"] or 0, 1)} %</span>'
            f'<span style="color:{TEXT_2}">Depot-Hitze · {zahl(h["euro"], 0)} € offenes Risiko von höchstens '
            f'{zahl(h["max"], 0)} %</span></div>'
            f'<span style="color:{TEXT_3};font-size:14px">Konto {zahl(d["konto"], 0)} € · Risiko je Trade '
            f'{zahl(d["risiko_pct"], 2)} % = {zahl(depot.risiko_euro(d), 0)} € · Quelle {t(d["quelle"])}'
            + (f' · Stand {t(d["stand"])}' if d.get("stand") else "") + '</span></div>')
    vb = depot.verlustbremse(d)
    if vb:
        kopf += ampelzeile(vb[1], vb[0])
    if h["ohne_stopp"]:
        kopf += ampelzeile("Ohne Stopp: " + ", ".join(h["ohne_stopp"]), "rot", "jede Position braucht einen Stopp")
    zeilen = []
    for p in d["positionen"]:
        k, df = _kurs(p["ticker"])
        if k is None:
            zeilen.append((p["ticker"], "grau", "keine Kurse", ""))
            continue
        w = depot.zeichen_w(depot.waehrung(p["ticker"]))
        lang = p.get("seite", "long") == "long"
        ab = ((k / p["stopp"] - 1) if lang else (1 - k / p["stopp"])) * 100 if p.get("stopp") else None
        g = ((k / p["einstieg"] - 1) if lang else (1 - k / p["einstieg"])) * 100 if p.get("einstieg") else 0
        z = depot.nach_dem_kauf(p, df)
        wichtig = next((x for x in z if x[0] == "rot"), None) or next((x for x in z if x[0] == "gelb"), None) or z[0]
        ko = p.get("ko") or {}
        zeilen.append((p["ticker"], wichtig[0],
                       f'{"long" if lang else "short"} · {p["stueck"]} Stück{" Knock-out" if ko else ""} · Kurs {zahl(k)} {w} '
                       f'({"+" if g >= 0 else "−"}{zahl(abs(g), 1)} %) · Stopp '
                       + (f'{zahl(p["stopp"])} {w}, {zahl(ab, 1)} % entfernt' if ab is not None else "fehlt"),
                       wichtig[1]))
    liste = "".join(
        f'<a href="?seite=Titelseite&t={tk}" target="_self" style="display:grid;grid-template-columns:22px 90px 1fr;'
        f'gap:10px;align-items:center;padding:8px 4px;border-top:1px solid {RAND};color:inherit;text-decoration:none">'
        f'{punkt(a, 12)}<b>{t(tk)}</b><span>{t(text)}<br><span style="color:{TEXT_2};font-size:14px">{t(zz)}</span>'
        f'</span></a>' for tk, a, text, zz in zeilen) or f'<div style="color:{TEXT_2}">keine offenen Positionen</div>'
    return karte(kopf + liste, "Depot · Positionen und Hitze")


def titelkarte(tk, df, erk):
    """Titelseite: gehaltene Position mit Nach-dem-Kauf-Zeichen, sonst Stückzahl für das Setup."""
    d = depot.laden()
    p = depot.position(tk)
    w = depot.zeichen_w(depot.waehrung(tk))
    if p:
        lang = p.get("seite", "long") == "long"
        ko = p.get("ko") or {}
        r = depot.offenes_risiko(p)
        kopf = (f'<p style="margin:0;font-size:16px">{"Long" if lang else "Short"} {p["stueck"]} Stück'
                + (f' Knock-out (Schwelle {zahl(ko.get("schwelle"))} {w}, Bezug {zahl(ko.get("bezug"), 3)})' if ko else "")
                + f' · Einstieg {zahl(p["einstieg"])} {w} am {t(_datum(p.get("datum")))} · Stopp '
                + (f'{zahl(p["stopp"])} {w}' if p.get("stopp") else "fehlt")
                + (f' · offenes Risiko {zahl(r, 0)} €' if r is not None else "") + '</p>')
        if ko and p.get("stopp") and ko.get("schwelle"):
            puffer = abs(p["stopp"] / ko["schwelle"] - 1) * 100
            kopf += ampelzeile(f'Abstand Stopp → Knock-out {zahl(puffer, 1)} %', "grün" if puffer >= 3 else "rot",
                               "der eigene Stopp muss vor der Knock-out-Schwelle liegen, mit Puffer für Lücken (ab 3 %)")
        return karte(kopf + "".join(ampelzeile(x, a) for a, x in depot.nach_dem_kauf(p, df, erk)),
                     "Position und Risiko · nach dem Kauf")
    pl = depot.plan(erk)
    if not d.get("konto"):
        return karte(f'<div style="color:{TEXT_2};font-size:15px">Kein Konto eingetragen (Übersicht, „⚙ Konto und '
                     f'Risiko“) – dann steht hier die Stückzahl für das Setup.</div>', "Position und Risiko")
    if not pl:
        return karte(f'<div style="color:{TEXT_2};font-size:15px">Kein Setup mit Einstieg und Stopp – keine Stückzahl. '
                     f'Risiko je Trade {zahl(depot.risiko_euro(d), 0)} €.</div>', "Position und Risiko")
    seite_, e, s, regel = pl
    a = depot.stueckzahl(tk, e, s)
    ko = depot.stueckzahl(tk, e, s, bezug=0.1)
    if not a:
        return karte(f'<div style="color:{TEXT_2}">Kein Wechselkurs für {depot.waehrung(tk)} – Stückzahl offen.</div>',
                     "Position und Risiko")
    schwelle = s * (0.97 if seite_ == "long" else 1.03)
    text = (f'<p style="margin:0;font-size:16px;line-height:1.65">{seite_.capitalize()} bei {zahl(e)} {w}, Stopp '
            f'{zahl(s)} {w} ({t(regel)}, {zahl(abs(s / e - 1) * 100, 1)} %). Risiko je Trade '
            f'{zahl(depot.risiko_euro(d), 0)} € ({zahl(d["risiko_pct"], 2)} %).</p>')
    zeilen = ampelzeile(f'Aktie: {a["stueck"]} Stück', "gelb" if (a.get("anteil") or 0) > depot.KLUMPEN else "grün",
                        f'Positionswert {zahl(a["wert"], 0)} € = {zahl(a["anteil"], 0)} % des Kontos'
                        + (" – Klumpen (Minervini: höchstens 20–25 % je Titel)" if (a.get("anteil") or 0) > depot.KLUMPEN
                           else "") + f' · Risiko {zahl(a["risiko"], 0)} €')
    zeilen += ampelzeile(f'Knock-out (Bezug 0,1): {ko["stueck"]} Stück', "blau",
                         f'Schwelle {"unter" if seite_ == "long" else "über"} {zahl(schwelle)} {w} wählen (mindestens 3 % '
                         f'hinter dem Stopp) · Risiko {zahl(ko["risiko"], 0)} € · bei anderem Bezug: Stück × 0,1 / Bezug')
    h = depot.hitze(d)
    if h["pct"] is not None:
        nachher = h["pct"] + a["risiko"] / d["konto"] * 100
        zeilen += ampelzeile(f'Depot-Hitze danach {zahl(nachher, 1)} %', "grün" if nachher <= h["max"] else "rot",
                             f'heute {zahl(h["pct"], 1)} %, Grenze {zahl(h["max"], 0)} %')
    return karte(text + zeilen, "Position und Risiko · Stückzahl für das Setup")
