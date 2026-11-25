"""Depotleiste und Depot-Hitze (Übersicht) und Karte „Position und Risiko“ (Titelseite) – Schritt 9, 04.11.2026."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import daten  # noqa: E402
import depot  # noqa: E402
from gestaltung import GRUEN, KARTE, RAND, ROT, TEXT, TEXT_2, TEXT_3, ampelzeile, karte, punkt, t, zahl  # noqa: E402


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
BEZUG_STELLEN = 3  # Bezugsverhältnis mit 3 Stellen zeigen
KO_PUFFER = 3      # Abstand Stopp → Knock-out mindestens 3 % (grün)


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
        return karte(f'<div style="font-size:15px;color:{TEXT_2}">Noch kein Konto eingetragen – Seite Depot oben, „⚙ Konto und Risiko“. '
                     f'Danach rechnet die App Stückzahl und Risiko auf jeder Karte und die Depot-Hitze.</div>', "Depot")
    h = depot.hitze(d)
    kopf = (f'<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:baseline">'
            f'<div title="Summe des offenen Risikos (Einstieg bis Stopp) aller Positionen gegen das Konto; Grenze '
            f'{zahl(h["max"], 0)} %" style="display:flex;gap:10px;align-items:center">{punkt(h["ampel"], 16)}'  # Layout
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
        zeilen.append((p["ticker"], lang, wichtig[0],
                       f'{"long" if lang else "short"} · {p["stueck"]} Stück{" Knock-out" if ko else ""} · Kurs {zahl(k)} {w} '
                       f'({"+" if g >= 0 else "−"}{zahl(abs(g), 1)} %) · Stopp '
                       + (f'{zahl(p["stopp"])} {w}, {zahl(ab, 1)} % entfernt' if ab is not None else "fehlt"),
                       wichtig[1]))
    liste = "".join(
        f'<div style="display:grid;grid-template-columns:22px 90px 1fr 120px;gap:10px;align-items:center;'
        f'padding:8px 4px 8px 10px;border-top:1px solid {RAND};border-left:3px solid {GRUEN if lang else ROT}">'
        f'{punkt(a, 12)}<b>{t(tk)}</b><span>{t(text)}<br><span style="color:{TEXT_2};font-size:14px">{t(zz)}</span>'  # Layout
        f'</span>{_deepdive(tk, lang)}</div>' for tk, lang, a, text, zz in zeilen) or f'<div style="color:{TEXT_2}">keine offenen Positionen</div>'
    return karte(kopf + liste, "Depot · Positionen und Hitze")


def positionsmarken(p, df):
    """Marken für den Chart der Position (Depot-Seite): Einstieg, Anfangsstopp, Stopp jetzt (reiten.nachgezogen,
    Livermore) und die enge Linie nach einem Gefahrensignal – dieselbe Rechnung wie „Nach dem Kauf“."""
    import reiten
    if df is None or not p.get("einstieg"):
        return {}
    nz = reiten.nachgezogen(df, p.get("datum"), float(p["einstieg"]), float(p["stopp"]) if p.get("stopp") else None,
                            p.get("seite", "long")) if p.get("stopp") else None
    return {"position": {"einstieg": float(p["einstieg"]), "anfang": p.get("stopp"), "seite": p.get("seite", "long"),
                         "tag": p.get("datum"), "stopp": (nz or {}).get("stopp"), "linie": (nz or {}).get("linie"),
                         "enger": ((nz or {}).get("enger") or {}).get("stopp"),
                         "enger_art": ((nz or {}).get("enger") or {}).get("art", "")}}


def _deepdive(tk, lang):
    """Knopf „Deep Dive →“ zur Titelseite, neuer Tab, Rahmen long grün / short rot."""
    return (f'<a href="?seite=Titelseite&t={tk}" target="_blank" rel="noopener" style="border:1px solid '
            f'{GRUEN if lang else ROT};border-radius:8px;padding:2px 8px;font-size:13px;font-weight:600;color:{TEXT};'
            f'text-decoration:none;background:{KARTE};white-space:nowrap;text-align:center">Deep Dive →</a>')


def titelkarte(tk, df):
    """Seite Depot: die gehaltene Position mit Risiko und Nach-dem-Kauf-Zeichen ("" ohne Position)."""
    p = depot.position(tk)
    w = depot.zeichen_w(depot.waehrung(tk))
    if not p:
        return ""
    if p:
        lang = p.get("seite", "long") == "long"
        ko = p.get("ko") or {}
        r = depot.offenes_risiko(p)
        kopf = (f'<p style="margin:0;font-size:16px">{"Long" if lang else "Short"} {p["stueck"]} Stück'
                + (f' Knock-out (Schwelle {zahl(ko.get("schwelle"))} {w}, Bezug {zahl(ko.get("bezug"), BEZUG_STELLEN)})' if ko else "")
                + f' · Einstieg {zahl(p["einstieg"])} {w} am {t(_datum(p.get("datum")))} · Stopp '
                + (f'{zahl(p["stopp"])} {w}' if p.get("stopp") else "fehlt")
                + (f' · offenes Risiko {zahl(r, 0)} €' if r is not None else "") + '</p>')
        if ko and p.get("stopp") and ko.get("schwelle"):
            puffer = abs(p["stopp"] / ko["schwelle"] - 1) * 100
            kopf += ampelzeile(f'Abstand Stopp → Knock-out {zahl(puffer, 1)} %', "grün" if puffer >= KO_PUFFER else "rot",
                               "der eigene Stopp muss vor der Knock-out-Schwelle liegen, mit Puffer für Lücken (ab 3 %)")
        import atr
        a_ = atr.wert(df)
        st_ = atr.stopp(float(df["Close"].iloc[-1]), p.get("stopp"), a_) if p.get("stopp") else None
        if st_:                                  # Abstand vom heutigen Kurs zum Stopp, gemessen an der ATR
            kopf += ampelzeile(st_[1].replace("vom Einstieg", "vom Kurs"), st_[0],
                               f"ATR (14 Tage) {zahl(a_)} {w}: übliche Tagesbewegung – unter 1 × ATR liegt der Stopp im "
                               f"Rauschen")
        return karte(kopf + "".join(ampelzeile(x, a) for a, x in depot.nach_dem_kauf(p, df)),
                     "Position und Risiko · nach dem Kauf")



