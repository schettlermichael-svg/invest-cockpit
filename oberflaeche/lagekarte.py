"""Lagekarte (4.11.2026): ein Titel auf einen Blick – dieselbe Karte auf Titelseite, Übersicht (Kartentisch) und in
den Watchlists. Aufbau: Kopf mit Setup, Chips (Zone, RS, Phase, Base), Belegzeile der Zone, Kleinchart 6 Monate mit
Zonenrahmen, Wertbereich und POC-Treppe, sechs Ampelpunkte (Markt, Phase, Zone, Branche, RS, Fundament – dieselben
Ampeln wie die Kacheln, Maus darauf zeigt deren Zeile), Abstand zum Pivot bzw. Auslöser, Fußzeile mit Stopp und
nächsten Zahlen. Die Karte erfindet nichts: jeder Wert stammt aus den Kacheln bzw. der Erkennung."""
import re

import numpy as np

from gestaltung import AMPEL, BLAU, GELB, GRAU, KARTE, RAND, ROT, GRUEN, TEXT, TEXT_2, TEXT_3, LILA, punkt, t, zahl

TREPPE = "#FFA657"
PUNKTE = (("Markt", "Markt"), ("Phase", "Phase"), ("Zone", "Zone"), ("Branche", "Branche"),
          ("RS", "Relative Stärke"), ("Fundament", "Fundament"))


RICHTUNG = {"long": GRUEN, "short": ROT}      # Rahmenfarbe eines Titels überall: long grün, short rot, offen gelb
SCHWACH = "66"                                # Abstufung: Setup noch nicht grün → Rahmen in blasser Richtungsfarbe
_SETUP = re.compile(r'(<div title="[^"]*" style="background:#1C2430;border:)1px solid (#[0-9A-Fa-f]{6})'
                    r'(;border-radius:8px;padding:6px 10px;font-size:14px;text-align:right;max-width:55%">)')


def richtung(x):
    """long (Spitze, Weitere, Radar mit Auslöser/Zone ↑), short (Short-Reihe, Radar ↓) oder None (Richtung offen)."""
    x = x or {}
    reihe = x.get("reihe")
    if reihe == "short":
        return "short"
    if reihe in ("konsolidierung", "flagge"):
        return "long" if x.get("bdir") == "↑" else "short" if x.get("bdir") == "↓" else None
    if reihe in ("spitze", "weitere"):
        return "long"
    if reihe == "frueh":
        pfeil = (x.get("angriff") or "")[1:2] or x.get("zdir") or ""
        return "long" if pfeil == "↑" else "short" if pfeil == "↓" else None
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
    if x.get("stern") or x.get("reihe") == "spitze":
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


def _kleinchart(df, erk, tage=126):
    d = df.iloc[-tage:]
    c = d["Close"].to_numpy(float)
    W, H, P = 420, 120, 6
    werte = list(d["High"]) + list(d["Low"])
    mp = erk.get("mp")
    zonen = [z for z in (mp or {}).get("zonen", []) if z["ende"] >= d.index[0]]
    pivot = (erk.get("werte") or {}).get("pivot") if (erk.get("muster") or erk.get("short")) else None
    lo, hi = min(werte), max(werte)
    if pivot:
        lo, hi = min(lo, pivot), max(hi, pivot)
    lo, hi = lo * 0.985, hi * 1.015

    def X(i):
        return P + (W - 2 * P) * i / max(1, len(c) - 1)

    def Y(p):
        return P + (H - 2 * P) * (1 - (np.log(p) - np.log(lo)) / (np.log(hi) - np.log(lo)))

    def pos(tag):
        return min(int(d.index.searchsorted(tag)), len(c) - 1)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="display:block;margin:10px 0 6px" role="img" '
         f'aria-label="Kleinchart 6 Monate mit Zonen">']
    treppe, vor = [], None
    for k, z in enumerate(zonen):
        letzte = k == len(zonen) - 1
        x0 = X(pos(z["beginn"])) if z["beginn"] >= d.index[0] else P
        x1 = W - P if letzte else X(pos(z["ende"]))
        s.append(f'<rect x="{x0:.1f}" y="{Y(z["vah"]):.1f}" width="{max(1, x1 - x0):.1f}" '
                 f'height="{max(1, Y(z["val"]) - Y(z["vah"])):.1f}" fill="{BLAU}" fill-opacity="0.13"/>'
                 f'<rect x="{x0:.1f}" y="{Y(z["hoch"]):.1f}" width="{max(1, x1 - x0):.1f}" '
                 f'height="{max(1, Y(z["tief"]) - Y(z["hoch"])):.1f}" fill="none" stroke="{BLAU}" '
                 f'stroke-opacity="{0.9 if letzte else 0.35}" stroke-width="1"'
                 + (' stroke-dasharray="4 3"' if letzte else "") + '/>')
        if vor is not None and treppe:
            treppe.append((x0, Y(vor["poc"])))
        treppe += [(x0, Y(z["poc"])), (x1, Y(z["poc"]))]
        vor = z
    if len(treppe) >= 2:
        s.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in treppe)}" fill="none" '
                 f'stroke="{TREPPE}" stroke-width="2"/>')
    if pivot:
        s.append(f'<line x1="{P}" x2="{W - P}" y1="{Y(pivot):.1f}" y2="{Y(pivot):.1f}" stroke="{TEXT_2}" '
                 f'stroke-width="1" stroke-dasharray="5 4"/>')
    s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(x):.1f}" for i, x in enumerate(c))}" fill="none" '
             f'stroke="{TEXT}" stroke-width="1.5"/>')
    s.append("</svg>")
    return "".join(s)


def _abstand(erk, kurs):
    """(Beschriftung, Wert, Anteil 0–1 für die Leiste, Farbe)."""
    w = erk.get("werte") or {}
    if erk.get("short") and "pivot" in w:
        ab = (kurs / w["pivot"] - 1) * 100
        anteil = min(1.0, max(0.0, 1 - ab / 10)) if ab >= 0 else 1.0
        return "Abstand zum Auslöser (short)", f"{'+' if ab >= 0 else '−'}{zahl(abs(ab), 1)} %", anteil, ROT
    if erk.get("muster") and "pivot" in w:
        ab = (kurs / w["pivot"] - 1) * 100
        anteil = min(1.0, max(0.0, 1 + ab / 10)) if ab <= 0 else 1.0
        return "Abstand zum Pivot (long)", f"{'+' if ab >= 0 else '−'}{zahl(abs(ab), 1)} %", anteil, \
            (GRUEN if 0 <= ab <= 5 else BLAU)
    return "Abstand zum Pivot", "kein Setup", 0.0, GRAU


def _stopp(erk):
    w = erk.get("werte") or {}
    if erk.get("short") and "pivot" in w:
        p, val = w["pivot"], w.get("val")
        if val and val <= p * 1.08:
            return f"Stopp: Schluss über {zahl(val)} $ (VAL)"
        return f"Stopp: {zahl(p * 1.08)} $ (+8 %)"
    if erk.get("muster") and "pivot" in w:
        p, vah = w["pivot"], w.get("vah")
        if vah and p * 0.92 <= vah < p:
            return f"Stopp: Schluss unter {zahl(vah)} $ (VAH)"
        return f"Stopp: {zahl(p * 0.92)} $ (−8 %)"
    return "kein Einstieg"


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
    """Zeichen unten auf der Lagekarte: Gelände (Zone, Raum, Überhang, Stellung hinter dem Stopp, dünne Spitze), geplantes
    CRV und ATR (Stopp im Rauschen, zu weit gelaufen, Enge, Überdehnung) – Zeichen, kein Filter."""
    import atr
    import depot
    a = atr.wert(df)
    if not a:
        return ""
    pl = depot.plan(erk)
    import crv
    z = crv.zeichen(erk, df, a) + [atr.stopp(pl[1], pl[2], a) if pl else None,
         atr.nachjagen(kurs, pl[1], a, pl[0]) if pl else None,
         atr.enge(df), atr.ueberdehnung(df, a)]
    zeilen = "".join(f'<div style="display:flex;gap:6px;align-items:center">{punkt(x[0], 9)}<span>{t(x[1])}</span></div>'
                     for x in z if x)
    return (f'<div title="Gelände (Zonen + Volumen), CRV und ATR (14 Tage) = übliche Tagesbewegung des Titels – Zeichen, '
            f'kein Filter" style="display:flex;flex-direction:column;gap:3px;font-size:13px;color:{TEXT_2}">'
            f'<span style="color:{TEXT_3}">ATR {zahl(a)} $ ({zahl(a / kurs * 100, 1)} % je Tag)</span>{zeilen}</div>')


def karte(tk, branche, erk, kacheln, df, liste=None):
    """kacheln: {Beschriftung: (Ampel, Wert, Zeile)} aus gestaltung.MITSCHRIFT."""
    def kz(name, default=("grau", "–", "")):
        return kacheln.get(name, default)
    setup = kz("Setup")
    zone = kz("Zone")
    rs = kz("Relative Stärke")
    phase = kz("Phase")
    base = kz("Base")
    kurs = float(df["Close"].iloc[-1])
    titel_, wert_, anteil, farbe_ = _abstand(erk, kurs)
    punkte = "".join(
        f'<div title="{t(name)}: {t(kz(k)[1])} · {t(kz(k)[2])}" style="display:flex;flex-direction:column;'
        f'align-items:center;gap:5px;font-size:12px;color:{TEXT_2};cursor:help">{punkt(kz(k)[0], 14)}{name}</div>'
        for name, k in PUNKTE)
    zahlen = kz("Nächste Zahlen")
    zahlen_text = f"Zahlen {zahlen[1]}" if zahlen[1] != "–" else "kein Zahlentermin"
    return (
        f'<article aria-label="Lagekarte {t(tk)}" style="background:{KARTE};border:1px solid {RAND};border-radius:14px;'
        f'padding:16px 18px;display:flex;flex-direction:column;gap:8px;box-sizing:border-box">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">'
        f'<div><div style="font-size:26px;font-weight:600">{t(tk.upper())}</div>'
        f'<div style="font-size:14px;color:{TEXT_2}">{t(branche)}</div>'
        + (f'<div style="font-size:14px;color:{LILA}">Liste: {t(liste)}</div>' if liste else "") +
        f'</div><div title="{t(setup[2])}" style="background:#1C2430;border:1px solid {RAND};'
        f'border-radius:8px;padding:6px 10px;font-size:14px;text-align:right;max-width:55%">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:'
        f'{AMPEL.get(setup[0], GRAU)};margin-right:6px"></span>{t(setup[1])}</div></div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px">{_chip("Zone: " + zone[1], zone[0])}'
        f'{_chip(rs[1], rs[0])}{_chip(phase[1], phase[0])}{_chip("Base " + base[1], base[0])}</div>'
        f'<div style="font-size:13px;color:{TEXT_2}">{t(zone[2])}</div>'
        f'{_kleinchart(df, erk)}'
        f'<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:4px">{punkte}</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:14px;margin-top:8px">'
        f'<span>{titel_}</span><span style="font-family:IBM Plex Mono,monospace">{wert_}</span></div>'
        f'<div style="height:6px;background:#0F141B;border-radius:3px"><div style="width:{anteil * 100:.0f}%;height:6px;'
        f'background:{farbe_};border-radius:3px"></div></div>'
        f'<div style="display:flex;justify-content:space-between;gap:10px;font-size:13px;color:{TEXT_2};'
        f'border-top:1px solid {RAND};padding-top:8px;margin-top:4px"><span>{_stopp(erk)}</span>'
        f'<span>{t(zahlen_text)}</span></div>{_groesse(tk, erk)}{_atr_zeilen(erk, df, kurs)}</article>')
