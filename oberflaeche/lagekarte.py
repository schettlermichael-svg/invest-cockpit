"""Lagekarte (4.11.2026, Zwei Systeme seit 05.11.2026): ein Titel auf einen Blick – dieselbe Karte auf Titelseite,
Übersicht (Kartentisch) und in den Watchlists. Aufbau: Kopf mit dem Setup je System (M = Minervini, K = Kullamägi),
Chips (Auktion, Stärke, Trend, Base), Befund des VCP-Scanners, Kleinchart 6 Monate mit der Zone des Scanners und dem
Pivot (seit 06.11.2026; die Wertzone ist nur noch das Zeichen „Auktion“), acht Ampelpunkte wie die Kacheln (geteilter Punkt: links M, rechts K; Maus darauf zeigt die Zeile),
Abstand zum Pivot, Fußzeile mit Stopp und nächsten Zahlen. Die Karte erfindet nichts: jeder Wert stammt aus den
Kacheln bzw. der Erkennung."""
import re

import numpy as np

from gestaltung import AMPEL, BLAU, GELB, GRAU, KARTE, RAND, ROT, GRUEN, TEXT, TEXT_2, TEXT_3, LILA, punkt, punkt2, t, zahl

PUNKTE = ("Markt", "Trend", "Stärke", "Fundament", "Setup", "Enge", "Geld", "Base")


RICHTUNG = {"long": GRUEN, "short": ROT}      # Rahmenfarbe eines Titels überall: long grün, short rot, offen gelb
SCHWACH = "66"                                # Abstufung: Setup noch nicht grün → Rahmen in blasser Richtungsfarbe
_SETUP = re.compile(r'(<div title="[^"]*" style="background:#1C2430;border:)1px solid (#[0-9A-Fa-f]{6})'
                    r'(;border-radius:8px;padding:6px 10px;font-size:14px;text-align:right;max-width:55%">)')


def richtung(x):
    """long (Reihen der Systeme und des VCP-Scanners), short (Ermüdung nach Überdehnung) oder None (Richtung offen)."""
    x = x or {}
    reihe = x.get("reihe")
    if reihe == "k_ermuedung":
        return "short"
    if reihe in ("m_spitze", "m_weitere", "k_breakout", "k_ep", "vcp", "flagge"):
        return "long"
    return None


def rahmen(x):
    """(Farbe, Dicke) des Titelrahmens – drei Stufen je Richtung:
    kräftig (★ Spitze bzw. Short im Ausbruch) · voll (Setup grün) · blass (Setup noch nicht grün);
    gelb, wenn keine Reihe oder die Richtung offen ist."""
    x = x or {}
    r = richtung(x)
    if r is None:
        return GELB, 1
    f = RICHTUNG[r]
    if x.get("stern") or x.get("reihe") == "m_spitze":
        return f, 2
    return (f, 1) if x.get("gruen") else (f + SCHWACH, 1)


def grund(x):
    """Was dem Titel zur nächsten Stufe fehlt (leer, wenn das Setup grün ist)."""
    x = x or {}
    luecken = x.get("luecken") or []
    if richtung(x) is None:
        kopf = "noch keine Reihe" if not x.get("reihe") else "Richtung offen"
        return kopf + (" · " + "; ".join(luecken) if luecken else "")
    if x.get("gruen") or not luecken:
        return ""
    return f'{len(luecken)} Regel{"n" if len(luecken) > 1 else ""} fehl{"en" if len(luecken) > 1 else "t"}: ' + "; ".join(luecken)


def faerben(html, x):
    """Rahmen der Lagekarte und ihres Setup-Kastens in der Stufe des Titels (rahmen). Die Setup-Ampel bleibt als
    Punkt im Kasten erhalten (auch bei Karten, die noch mit Ampelrahmen gespeichert wurden)."""
    if not html or x is None:
        return html
    f, d = rahmen(x)
    html = html.replace(f'border:1px solid {RAND};border-radius:14px', f'border:{d}px solid {f};border-radius:14px', 1)

    def setup(m):
        alt = m.group(2)
        ampel = "" if alt.upper() == RAND.upper() else (f'<span style="display:inline-block;width:10px;height:10px;'
                                                        f'border-radius:50%;background:{alt};margin-right:6px"></span>')
        return f'{m.group(1)}1px solid {f}{m.group(3)}{ampel}'
    return _SETUP.sub(setup, html, count=1)


def _chip(text, ampel=None):
    f = AMPEL.get(ampel) if ampel else None
    rand = f if f else RAND
    farbe = f if f else TEXT_2
    return (f'<span style="border:1px solid {rand};color:{farbe};border-radius:6px;padding:3px 9px;font-size:13px;'
            f'white-space:nowrap">{t(text)}</span>')


def _zone(erk):
    """Die Zone des Systems, das das Setup liefert: Minervini, sonst die Konsolidierung des Kullamägi-Breakouts."""
    sy = erk.get("systeme") or {}
    z = (sy.get("m") or {}).get("zone") or {}
    if z.get("zone"):
        return z
    return ((sy.get("k") or {}).get("breakout") or {}).get("zone")


def _kleinchart(df, erk, tage=126):
    """Kleinchart 6 Monate: Kurs, Zone des VCP-Scanners (Rahmen von der Oberkante bis heute) und Pivot."""
    d = df.iloc[-tage:]
    c = d["Close"].to_numpy(float)
    W, H, P = 420, 120, 6
    werte = list(d["High"]) + list(d["Low"])
    z = _zone(erk)
    pivot = _pivot(erk)
    lo, hi = min(werte), max(werte)
    if pivot:
        lo, hi = min(lo, pivot), max(hi, pivot)
    lo, hi = lo * 0.985, hi * 1.015

    def X(i):
        return P + (W - 2 * P) * i / max(1, len(c) - 1)

    def Y(p):
        return P + (H - 2 * P) * (1 - (np.log(p) - np.log(lo)) / (np.log(hi) - np.log(lo)))

    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;margin:10px 0 6px" role="img" '
         f'aria-label="Kleinchart 6 Monate mit der Zone des Scanners">']
    if z and z.get("start_i") is not None and z["start_i"] < len(df):
        start = df.index[z["start_i"]]
        x0 = X(int(d.index.searchsorted(start))) if start >= d.index[0] else P
        oben, unten = float(z["oben"]), max(float(z["unten"]), lo)
        s.append(f'<rect x="{x0:.1f}" y="{Y(oben):.1f}" width="{max(1, W - P - x0):.1f}" '
                 f'height="{max(1, Y(unten) - Y(oben)):.1f}" fill="{BLAU}" fill-opacity="0.10" stroke="{BLAU}" '
                 f'stroke-opacity="0.8" stroke-width="1"/>')
    if pivot:
        s.append(f'<line x1="{P}" x2="{W - P}" y1="{Y(pivot):.1f}" y2="{Y(pivot):.1f}" stroke="{TEXT_2}" '
                 f'stroke-width="1" stroke-dasharray="5 4"/>')
    s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(c))}" fill="none" '
             f'stroke="{TEXT}" stroke-width="1.5"/>')
    s.append("</svg>")
    return "".join(s)


def _pivot(erk):
    """Pivot des Systems, das das Setup liefert: Minervini zuerst, dann Kullamägi (EP: Hoch des Sprungtags, Breakout:
    Oberkante der Zone des Scanners); sonst keiner."""
    sy = erk.get("systeme") or {}
    m, k = sy.get("m") or {}, sy.get("k") or {}
    if m.get("pivot"):
        return m["pivot"]
    h = k.get("haupt") or {}
    if h.get("pivot") and h.get("ampel") != "rot":
        return h["pivot"]
    return None


def _abstand(erk, kurs):
    """(Beschriftung, Wert, Anteil 0–1 für die Leiste, Farbe)."""
    em = ((erk.get("systeme") or {}).get("k") or {}).get("ermuedung")
    p = _pivot(erk)
    if p:
        ab = (kurs / p - 1) * 100
        anteil = min(1.0, max(0.0, 1 + ab / 10)) if ab <= 0 else 1.0
        return "Abstand zum Pivot (long)", f"{'+' if ab >= 0 else '−'}{zahl(abs(ab), 1)} %", anteil, \
            (GRUEN if 0 <= ab <= 5 else BLAU)
    if em:
        ab = (kurs / em["unten"] - 1) * 100
        return "Abstand zur Unterkante (short)", f"{'+' if ab >= 0 else '−'}{zahl(abs(ab), 1)} %", 1.0, ROT
    return "Abstand zum Pivot", "kein Setup", 0.0, GRAU


def _stopp(erk):
    import depot
    pl = depot.plan(erk)
    if not pl:
        return "kein Einstieg"
    return f"Stopp {zahl(pl[2])} $ · {pl[3]}"


def _groesse(tk, erk):
    """Stückzahl und Risiko für das Setup (Schritt 9) – nur mit eingetragenem Konto."""
    import depot
    pl = depot.plan(erk)
    if not pl:
        return ""
    sz = depot.stueckzahl(tk, pl[1], pl[2])
    if not sz:
        return ""
    anteil = f" · {zahl(sz['anteil'], 0)} % des Kontos" if sz.get("anteil") else ""
    return (f'<div style="font-size:13px;color:{TEXT_2}">Stück {sz["stueck"]} · Risiko {zahl(sz["risiko"], 0)} €'
            f'{anteil}</div>')


def _atr_zeilen(erk, df, kurs):
    """Zeichen unten auf der Lagekarte: Stopps, nächster Widerstand (Weinstein), Minervini-Abgleich und ATR (Stopp im
    Rauschen, zu weit gelaufen, Enge, Überdehnung) – Zeichen, kein Filter."""
    import atr
    import depot
    a = atr.wert(df)
    if not a:
        return ""
    pl = depot.plan(erk)
    import stopps
    z = stopps.zeichen(erk, df, a) + [atr.stopp(pl[1], pl[2], a) if pl else None,
         atr.nachjagen(kurs, pl[1], a, pl[0]) if pl else None,
         atr.enge(df), atr.ueberdehnung(df, a)]
    zeilen = "".join(f'<div style="display:flex;gap:6px;align-items:center">{punkt(x[0], 9)}<span>{t(x[1])}</span></div>'
                     for x in z if x)
    return (f'<div title="Stopps, nächster Widerstand und ATR (14 Tage) = übliche Tagesbewegung des Titels – Zeichen, '
            f'kein Filter" style="display:flex;flex-direction:column;gap:3px;font-size:13px;color:{TEXT_2}">'
            f'<span style="color:{TEXT_3}">ATR {zahl(a)} $ ({zahl(a / kurs * 100, 1)} % je Tag)</span>{zeilen}</div>')


def _setup_kasten(kacheln, erk):
    """Kasten oben rechts: das Setup je System. Der äußere Rahmen wird von faerben() eingefärbt."""
    sy = erk.get("systeme") or {}
    m, k = sy.get("m") or {}, sy.get("k") or {}
    s_ = kacheln.get("Setup", ((None, None), "", ""))
    zeile = s_[2]
    am = s_[0][0] if isinstance(s_[0], tuple) else s_[0]
    ak = s_[0][1] if isinstance(s_[0], tuple) else None
    kw = (k.get("haupt") or {}).get("art") if (k.get("haupt") or {}).get("ampel") not in (None, "rot") else None
    if not kw and k.get("ermuedung"):
        kw = "Ermüdung (short)"
    zeilen = (f'<div><span style="color:{TEXT_3};font-size:12px">M</span> '
              f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'
              f'{AMPEL.get(am or "grau", GRAU)};margin:0 4px"></span>{t(m.get("setup", "–"))}</div>'
              f'<div><span style="color:{TEXT_3};font-size:12px">K</span> '
              f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'
              f'{AMPEL.get(ak or "grau", GRAU)};margin:0 4px"></span>{t(kw or "keines")}</div>')
    return (f'<div title="{t(zeile)}" style="background:#1C2430;border:1px solid {RAND};'
            f'border-radius:8px;padding:6px 10px;font-size:14px;text-align:right;max-width:55%">{zeilen}</div>')


def _befund(erk):
    """Befund des Scanners unter den Chips: Base des Systems und Ausbruch."""
    sy = erk.get("systeme") or {}
    m = sy.get("m") or {}
    b = (sy.get("k") or {}).get("breakout") or {}
    teile = [next((x for n, _, x in m.get("regeln", []) if n.startswith("Reife Base")), "")]
    if not (m.get("zone") or {}).get("zone") and b.get("zone"):
        teile = [next((x for n, _, x in b.get("regeln", []) if n.startswith("Konsolidierung")), "")]
    if m.get("ausbruch") or b.get("ausbruch"):
        import vcp_zone
        teile.append(vcp_zone.ausbruch_text(m.get("ausbruch") or b.get("ausbruch")))
    return " · ".join(x for x in teile if x)


def karte(tk, branche, erk, kacheln, df, liste=None):
    """kacheln: {Beschriftung: (Ampel oder (Ampel M, Ampel K), Wert, Zeile)} aus gestaltung.MITSCHRIFT."""
    def kz(name, default=("grau", "–", "")):
        return kacheln.get(name, default)
    zone = kz("Wertzone")
    staerke, trend, base = kz("Stärke"), kz("Trend"), kz("Base")

    def ampel_m(x):
        return x[0][0] if isinstance(x[0], tuple) else x[0]

    def wort_m(x):
        return x[1].split(" · K ")[0].replace("M ", "", 1) if isinstance(x[0], tuple) else x[1]
    kurs = float(df["Close"].iloc[-1])
    titel_, wert_, anteil, farbe_ = _abstand(erk, kurs)

    def pkt(x):
        return punkt2(x[0][0], x[0][1], 14) if isinstance(x[0], tuple) else punkt(x[0], 14)
    punkte = "".join(
        f'<div title="{t(name)}: {t(kz(name)[1])} · {t(kz(name)[2])}" style="display:flex;flex-direction:column;'
        f'align-items:center;gap:5px;font-size:12px;color:{TEXT_2};cursor:help">{pkt(kz(name))}{name}</div>'
        for name in PUNKTE)
    zahlen = kz("Nächste Zahlen")
    zahlen_text = f"Zahlen {zahlen[1]}" if zahlen[1] != "–" else "kein Zahlentermin"
    return (
        f'<article aria-label="Lagekarte {t(tk)}" style="background:{KARTE};border:1px solid {RAND};border-radius:14px;'
        f'padding:16px 18px;display:flex;flex-direction:column;gap:8px;box-sizing:border-box">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">'
        f'<div><div style="font-size:26px;font-weight:600">{t(tk.upper())}</div>'
        f'<div style="font-size:14px;color:{TEXT_2}">{t(branche)}</div>'
        + (f'<div style="font-size:14px;color:{LILA}">Liste: {t(liste)}</div>' if liste else "") +
        f'</div>{_setup_kasten(kacheln, erk)}</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px">{_chip("Auktion: " + zone[1], zone[0])}'
        f'{_chip(wort_m(staerke), ampel_m(staerke))}{_chip(wort_m(trend), ampel_m(trend))}'
        f'{_chip("Base " + base[1], base[0])}</div>'
        f'<div style="font-size:13px;color:{TEXT_2}">{t(_befund(erk))}</div>'
        f'{_kleinchart(df, erk)}'
        f'<div title="Geteilter Punkt: links Minervini (M), rechts Kullamägi (K); grau = gilt für das System nicht" '
        f'style="display:grid;grid-template-columns:repeat(8,1fr);gap:4px">{punkte}</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:14px;margin-top:8px">'
        f'<span>{titel_}</span><span style="font-family:IBM Plex Mono,monospace">{wert_}</span></div>'
        f'<div style="height:6px;background:#0F141B;border-radius:3px"><div style="width:{anteil * 100:.0f}%;height:6px;'
        f'background:{farbe_};border-radius:3px"></div></div>'
        f'<div style="display:flex;justify-content:space-between;gap:10px;font-size:13px;color:{TEXT_2};'
        f'border-top:1px solid {RAND};padding-top:8px;margin-top:4px"><span>{t(_stopp(erk))}</span>'
        f'<span>{t(zahlen_text)}</span></div>{_groesse(tk, erk)}{_atr_zeilen(erk, df, kurs)}</article>')
