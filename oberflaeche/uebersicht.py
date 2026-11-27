"""Teile der Seite Rückenwind, die früher die Übersicht „Lageeinschätzung“ waren (zusammengelegt am 10.11.2026):
  ① Lage           Markt (Indizes und Hochs/Tiefs), Moral der Truppe, Wirtschaftswetter; aufklappbar das
                   Wirtschaftswetter im Einzelnen (Dalio-Quad mit Spur, Instrumente, Abgleich mit den Sektoren)
  ② Rückenwind     rueckenwind_seite.py (Wetterkarte, Gruppen nach Geldfluss, Titel in der Schlachtordnung; die
                   Lagekarte nach Sektoren aus dem Kartentisch stand dort bis 22.11.2026)
Die Vier-Felder-Tafel der Sektoren und die Themen-Gruppen der früheren Frontkarte zeigt die Wetterkarte (Ebene Sektor,
Thema); app.py setzt ② unter „lage“."""
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

import lage                                                  # noqa: E402
STRESS_GRUEN, STRESS_GELB = 60, 30   # Pendel: Rang ab 60 von 100 grün, ab 30 gelb (Kredit, VIX gespiegelt)
BREITE_GRUEN, BREITE_GELB = 60, 40   # Pendel: Marktbreite ab 60 % über GD200 grün, ab 40 % gelb
LEVY_HEISS = 1.10                    # Pendel: S&P 500 ab 10 % über dem 26-Wochen-Schnitt überdehnt (gelb)
import marktdaten                                            # noqa: E402
from frontkarte import quad_abgleich  # noqa: E402
import quadbild                                              # noqa: E402
from gestaltung import (KARTE, RAND, TEXT, GRUEN, GELB, TEXT_2, TEXT_3, AMPEL, PUNKT_KLEIN, ampelzeile, punkt, seite, sprungleiste,
                        station, t, zahl)  # noqa: E402

QUAD_AMPEL = {1: "grün", 2: "grün", 3: "gelb", 4: "rot"}


def _kachel(label, ampel, wert, pfeil, zeile, mehr="", zeile_html=""):
    # lange Wörter (z. B. „Abwärtsbeschleunigung“) kleiner setzen und notfalls trennen, damit nichts aus der Kachel ragt
    wort = max((len(w) for w in str(wert).split()), default=0)
    groesse = 26 if wort <= 14 else 22 if wort <= 17 else 19  # Layout
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:20px;'
            f'display:flex;flex-direction:column;gap:10px">'
            f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;text-transform:uppercase">{t(label)}</div>'
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<span style="width:22px;height:22px;border-radius:50%;background:{AMPEL[ampel]};flex-shrink:0"></span>'
            f'<span lang="de" style="font-size:{groesse}px;font-weight:600;min-width:0;overflow-wrap:anywhere;'
            f'hyphens:auto">{t(wert)}</span>'
            f'<span style="font-size:24px;color:{TEXT_2}">{t(pfeil)}</span></div>'
            + (zeile_html or f'<div style="font-size:14px;color:{TEXT_2};line-height:1.5">{t(zeile)}</div>')
            + (f'<details><summary style="cursor:pointer;font-size:13px;color:{TEXT_3}">Instrumente</summary>'
               f'<div style="margin-top:8px">{mehr}</div></details>' if mehr else "") + '</div>')


def _markt_spalten(mm):
    """Markt-Kachel (Micky 26.11.2026: Lagebild in drei Schichten): oben Spitze und Heer, die die Ampel bestimmen, darunter
    S&P 500 und Nasdaq nebeneinander – je Index Livermores Spalte mit ✓/✗ (bestätigt die Lage oder nicht), der Zirkel
    als Zeichen (Phase und Halt: 🏰 hält · 🌊 Welle · ⛈️ Sturm, Zeichen in Klartext); unten Hochs : Tiefs."""
    import zeichen
    schichten = "".join(
        f'<div style="font-size:14px;color:{TEXT}">{wort}: <b>{x["auf"]}</b> im Vormarsch · <b>{x.get("pause", 0)}</b> in der Gefechtspause · <b>{x["ab"]}</b> im Rückzug</div>'
        for wort, x in (("Spitze (Garde und Angriff)", mm.get("fuehrer")), ("Heer (alle Titel)", mm.get("heer"))) if x)
    spalten = []
    for name, x in (mm.get("indizes") or {}).items():
        seite_k = zeichen.KEIM_SEITE.get(x.get("phase"), "schwäche")
        seite_t = "stärke" if seite_k == "schwäche" else "schwäche"
        sym, wort, _ = zeichen.halt(x)
        zeilen_ = ([(sym, wort)] if sym else []) + \
                  [("dagegen:", zeichen.klartext(k, seite_k)) for k in x.get("keim") or []] + \
                  [("trägt:", zeichen.klartext(k, seite_t)) for k in x.get("traegt") or []]
        phase = f'Zirkel: Jahreszeit {x["wort"]}' if x.get("wort") else "Zirkel: jung"
        b_ = x.get("bestaetigt", "")
        spalten.append(
            f'<div style="flex:1 1 140px;min-width:0;display:flex;flex-direction:column;gap:4px">'
            f'<div style="font-size:13px;color:{TEXT_3}">{t(name)}</div>'
            f'<div style="display:flex;align-items:center;gap:8px">{punkt(x["ampel"], PUNKT_KLEIN)}'
            f'<span style="font-size:15px;font-weight:600">{t(x.get("spalte") or "")}</span>'
            f'<span style="color:{GRUEN if b_ == "✓" else GELB}">{b_}</span></div>'
            f'<div style="font-size:13px;color:{TEXT_2}">{t(phase)} ({t(x.get("name") or "")})</div>'
            + "".join(f'<div style="font-size:13px;color:{TEXT_2};line-height:1.4">{z} {t(k)}</div>'
                      for z, k in dict.fromkeys(zeilen_))
            + ("" if zeilen_ else f'<div style="font-size:13px;color:{TEXT_3}">keine Zeichen gemessen</div>')
            + '</div>')
    hochs = (f'<div style="font-size:13px;color:{TEXT_2};border-top:1px solid {RAND};padding-top:6px">'
             f'neue 52-Wochen-Hochs : Tiefs {mm["hochs"]} : {mm["tiefs"]}</div>' if mm.get("hochs") is not None else "")
    return (f'<div style="display:flex;flex-direction:column;gap:2px;margin-bottom:8px">{schichten}</div>'
            f'<div style="display:flex;gap:16px;flex-wrap:wrap">{"".join(spalten)}</div>' + hochs)


def _pendel_instrumente(m):
    """Die vier Instrumente des Pendels als Ampeln: Name → (Ampel, Text)."""
    stress = lambda rang: "grün" if rang >= STRESS_GRUEN else "gelb" if rang >= STRESS_GELB else "rot"   # noqa: E731
    return {
        "Kreditrisiko": (stress(m["kredit_rang"]),
                         f'Hochzins gegen Staatsanleihen: Rang {zahl(m["kredit_rang"], 0)} von 100 in 10 Jahren '
                         f'(100 = ruhig), {"+" if m["kredit_4w"] >= 0 else "−"}{zahl(abs(m["kredit_4w"]), 1)} Punkte in 4 Wochen'),
        "Angstindex (VIX)": (stress(100 - m["vix_rang"]),
                             f'{zahl(m["vix"], 1)} · Rang {zahl(m["vix_rang"], 0)} von 100 in 10 Jahren (100 = höchste Angst)'),
        "Marktbreite": ("grün" if m["breite"] >= BREITE_GRUEN else "gelb" if m["breite"] >= BREITE_GELB else "rot",
                        f'{zahl(m["breite"], 0)} % über GD200, vor 4 Wochen {zahl(m["breite"] - m["breite_4w"], 0)} %'),
        "Überdehnung (Levy)": ("gelb" if m["levy"] >= LEVY_HEISS else "grün" if m["levy"] >= 1.0 else "rot",
                               f'S&P 500 zum 26-Wochen-Schnitt: {zahl(m["levy"], 2)}'),
    }


def _bewegung(vorher, jetzt):
    """Wie sich das Pendel in 4 Wochen bewegt hat, in Worten statt Pfeil."""
    if vorher == jetzt:
        return f"Seit 4 Wochen unverändert {jetzt}."
    schritt = (lage.ZONEN.index(jetzt) - lage.ZONEN.index(vorher)) % len(lage.ZONEN)
    if schritt <= 3:  # Layout
        return f"Vor 4 Wochen {vorher}: Der Zyklus läuft weiter."
    if vorher in ("Überhitzung", "Topbildung"):
        return f"Vor 4 Wochen {vorher}: Das Pendel schwingt zurück, die Überhitzung baut sich ab."
    if vorher in ("Frühe Erholung", "Gesunder Aufwärtstrend"):
        return f"Vor 4 Wochen {vorher}: Die Erholung hat einen Rückschlag erlitten."
    return f"Vor 4 Wochen {vorher}: Das Pendel schwingt zurück."


ABLAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "daten", "uebersicht.pkl.gz")


def ablegen(teile):
    """Vom Abendlauf gebaute Übersicht (ohne Kartentisch) speichern – die App zeigt sie dann sofort."""
    import gzip
    import pickle
    os.makedirs(os.path.dirname(ABLAGE), exist_ok=True)
    tmp = f"{ABLAGE}.{os.getpid()}.neu"
    with gzip.open(tmp, "wb", compresslevel=3) as f:  # Layout
        pickle.dump(teile, f)
    os.replace(tmp, ABLAGE)


def abgelegt():
    """Gespeicherte Übersicht als (Teile, veraltet) oder None (fehlt, älter als 30 Stunden oder älter als das Depot).
    Veraltet = vor der letzten Programmänderung gebaut: wird sofort gezeigt, nachtlauf.py --seiten baut sie im
    Hintergrund neu (09.11.2026)."""
    import gzip
    import pickle
    import depot
    import zonenseite
    try:
        zeit = os.path.getmtime(ABLAGE)
        if time.time() - zeit > 30 * 3600 or (os.path.exists(depot.DATEI) and zeit < os.path.getmtime(depot.DATEI)):  # Layout
            return None
        with gzip.open(ABLAGE, "rb") as f:
            return pickle.load(f), zeit < zonenseite.codezeit()
    except Exception:  # noqa: BLE001
        return None


def veraltet():
    """Fehlt die abgelegte Übersicht oder ist sie älter als das Programm?"""
    import zonenseite
    try:
        return os.path.getmtime(ABLAGE) < zonenseite.ablage_grenze()
    except OSError:
        return True


def seite_uebersicht():
    start = time.time()
    q, p = lage.quadrant(), lage.pendel()
    br = marktdaten.breite()
    breite_zeichen = marktdaten.breite_pruefung()       # Plausibilitätswächter (Abdeckung, Sprünge, Quelle)
    schlimmste = "rot" if any(a == "rot" for a, _ in breite_zeichen) else "gelb" if breite_zeichen else None
    m = p["messwerte"]
    stand = br.index[-1]

    w, i = q["wachstum"], q["inflation"]

    def achse(name, a):
        zahl_dafuer = a["steigt"] if a["richtung"] == "steigt" else a["fällt"]
        return f'{name} {a["richtung"]} ({zahl_dafuer} von {a["von"]})'

    amtlich = (f'Amtliche Zahlen noch Quad {q["amtlich"]}: Wechsel möglich.' if q["wechsel_moeglich"]
               else f'Amtliche Zahlen bestätigen Quad {q["amtlich"]}.')
    quad_zeile = f'{achse("Wachstum", w)}, {achse("Inflation", i)}. {amtlich} Typische Führer: {q["fuehrer"]}.'

    instr = _pendel_instrumente(m)
    gegen = [n for n, (a, _) in instr.items() if a != "grün"]
    pendel_ampel = "gelb" if p["ampel"] == "grün" and len(gegen) >= 2 else p["ampel"]
    pendel_zeile = _bewegung(p["vor_4_wochen"], p["zone"])
    if breite_zeichen:
        pendel_zeile += " 🟡 Marktbreite unsicher – Zone nur unter Vorbehalt."
        pendel_ampel = schlimmste if pendel_ampel == "grün" or schlimmste == "rot" else pendel_ampel
    if p["ampel"] == "grün" and gegen:
        pendel_zeile += " Gegenstimmen: " + ", ".join(gegen) + "."
    import zirkel
    try:                                         # Markt-Ampel: Lagebild in drei Schichten (26.11.2026)
        mm = zirkel.markt()
    except Exception:  # noqa: BLE001
        mm = None
    markt_mehr = "".join(ampelzeile(f'{n}: {x.get("spalte", "")} {x.get("bestaetigt", "")} · Zirkel {x["name"]} ({x["wort"]})',
                                    x["ampel"],
                                    " · ".join([f"trägt – {y}" for y in x.get("traegt") or []]
                                               + [f"Keim – {y}" for y in x.get("keim") or []]) or "keine Zeichen gemessen")
                         for n, x in ((mm or {}).get("indizes") or {}).items())
    pendel = "".join(ampelzeile(n, a, x) for n, (a, x) in instr.items())
    kacheln = [
        _kachel("Markt", mm["ampel"], mm["wort"], "", "", markt_mehr, _markt_spalten(mm))
        if mm else "",   # eine Ampel (Micky 12.11.2026), seit 26.11.2026 Spitze und Heer
        _kachel("Moral der Truppe", pendel_ampel, p["zone"], "", pendel_zeile, pendel),
        _kachel("Wirtschaftswetter", "gelb" if q["wechsel_moeglich"] else QUAD_AMPEL[q["quad"]],
                f'Quad {q["quad"]} · {q["name"]}', "", quad_zeile),
    ]
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "werkzeuge"))
    import nachtlauf
    _nacht = nachtlauf.stand()
    kopf = (f'<header style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;'
            f'gap:16px;border-bottom:1px solid {RAND};padding-bottom:16px">'
            f'<div style="display:flex;flex-direction:column;gap:4px">'
            f'<div style="font-size:13px;letter-spacing:0.12em;text-transform:uppercase;color:{TEXT_3}">MARAGA INVESTMENT APP</div>'
            f'<h1 style="margin:0;font-size:32px;font-weight:600">Rückenwind</h1></div>'
            f'<div style="display:flex;gap:16px;font-size:14px;color:{TEXT_2}">'
            f'<span>Stand {stand:%d.%m.%Y}</span>'
            f'<span title="Datenampel aus dem Protokoll des Nachtlaufs (daten/nachtlauf/protokoll.json)" '
            f'style="display:flex;gap:6px;align-items:center">{punkt(_nacht[0], 10)}{t(_nacht[1])}</span>'  # Layout
            f'<span style="font-family:IBM Plex Mono,monospace;color:{TEXT_3}">geladen in {zahl(time.time() - start, 1)} s</span>'
            f'</div></header>')
    leiste = (f'<section aria-label="Lageleiste" style="display:grid;grid-template-columns:repeat(auto-fit,'
              f'minmax(240px,1fr));gap:16px">{"".join(kacheln)}</section>')

    try:
        quad_bild = quadbild.bild(q, quadbild.verlauf(lage))
    except Exception:  # noqa: BLE001 – ohne Bild bleibt die Kachel
        quad_bild = ""
    try:
        abgleich = quad_abgleich(q)
    except Exception:  # noqa: BLE001
        abgleich = ""
    from gestaltung import klapp
    einzeln = klapp("Wirtschaftswetter im Einzelnen", f"Dalio-Quad mit Spur, Instrumenten und Abgleich mit den Sektoren · "
                    f"heute Quad {q['quad']} · {q['name']}", quad_bild + abgleich)
    # Seite Rückenwind (22.11.2026): ① Lage hier, ② Rückenwind (Strömung und Titel) aus rueckenwind_seite über app.py.
    return {"lage": seite(kopf + sprungleiste() + station("lage") + leiste + '<div style="height:12px"></div>' + einzeln,
                          unten=12)}  # Layout
