"""Übersicht „Lage am Abend“ – der breite Rand des Trichters (die Titelseite ist der schmale Hals). Geordnet nach
Stationen, jede mit ihrer Frage, oben eine Sprungleiste (05.11.2026):
  ① Lage           Markt je System (Minervini, Kullamägi), Moral der Truppe, Wirtschaftswetter; darunter der
                   Dalio-Quad als Bild mit Spur der letzten 13 Wochen (quadbild.py)
                   (Stimmungskurve seit 06.11.2026 nicht mehr auf der Übersicht; O'Neils Marktrichtung, Marktbreite und neue Hochs gegen Tiefs seit 06.11.2026 nicht mehr als
                   Kachel – Breite und Hochs/Tiefs rechnen weiter in Minervinis Markt und der Moral der Truppe mit)
  ② Front          Frontkarte, Übergänge, Lagebild nach Sektoren
  ③ Auswahl        Setups, Ausbruchsfelder, ★ Spitze, Watchlist, Weitere, Frühaufklärung, Short (kartentisch.plan)
  ④ Termine        Neu seit gestern, Earnings 14 Tage
  ⑤ Eigene Truppe  Depotleiste mit Depot-Hitze
app.py setzt den Kartentisch (Lagebild bis ④) zwischen „oben“ und „unten“."""
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

import lage                                                  # noqa: E402
import marktdaten                                            # noqa: E402
from frontkarte import frontkarte  # noqa: E402
import uebergaenge                                           # noqa: E402
import quadbild                                              # noqa: E402
import depotleiste                                           # noqa: E402
from gestaltung import (KARTE, RAND, TEXT_2, TEXT_3, AMPEL, ampelzeile, punkt, seite, sprungleiste,
                        station, t, zahl)  # noqa: E402

QUAD_AMPEL = {1: "grün", 2: "grün", 3: "gelb", 4: "rot"}


def _kachel(label, ampel, wert, pfeil, zeile, mehr=""):
    # lange Wörter (z. B. „Abwärtsbeschleunigung“) kleiner setzen und notfalls trennen, damit nichts aus der Kachel ragt
    wort = max((len(w) for w in str(wert).split()), default=0)
    groesse = 26 if wort <= 14 else 22 if wort <= 17 else 19
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:20px;'
            f'display:flex;flex-direction:column;gap:10px">'
            f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;text-transform:uppercase">{t(label)}</div>'
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<span style="width:22px;height:22px;border-radius:50%;background:{AMPEL[ampel]};flex-shrink:0"></span>'
            f'<span lang="de" style="font-size:{groesse}px;font-weight:600;min-width:0;overflow-wrap:anywhere;'
            f'hyphens:auto">{t(wert)}</span>'
            f'<span style="font-size:24px;color:{TEXT_2}">{t(pfeil)}</span></div>'
            f'<div style="font-size:14px;color:{TEXT_2};line-height:1.5">{t(zeile)}</div>'
            + (f'<details><summary style="cursor:pointer;font-size:13px;color:{TEXT_3}">Instrumente</summary>'
               f'<div style="margin-top:8px">{mehr}</div></details>' if mehr else "") + '</div>')


def _pendel_instrumente(m):
    """Die vier Instrumente des Pendels als Ampeln: Name → (Ampel, Text)."""
    stress = lambda rang: "grün" if rang >= 60 else "gelb" if rang >= 30 else "rot"   # noqa: E731
    return {
        "Kreditrisiko": (stress(m["kredit_rang"]),
                         f'Hochzins gegen Staatsanleihen: Rang {zahl(m["kredit_rang"], 0)} von 100 in 10 Jahren '
                         f'(100 = ruhig), {"+" if m["kredit_4w"] >= 0 else "−"}{zahl(abs(m["kredit_4w"]), 1)} Punkte in 4 Wochen'),
        "Angstindex (VIX)": (stress(100 - m["vix_rang"]),
                             f'{zahl(m["vix"], 1)} · Rang {zahl(m["vix_rang"], 0)} von 100 in 10 Jahren (100 = höchste Angst)'),
        "Marktbreite": ("grün" if m["breite"] >= 60 else "gelb" if m["breite"] >= 40 else "rot",
                        f'{zahl(m["breite"], 0)} % über GD200, vor 4 Wochen {zahl(m["breite"] - m["breite_4w"], 0)} %'),
        "Überdehnung (Levy)": ("gelb" if m["levy"] >= 1.10 else "grün" if m["levy"] >= 1.0 else "rot",
                               f'S&P 500 zum 26-Wochen-Schnitt: {zahl(m["levy"], 2)}'),
    }


def _bewegung(vorher, jetzt):
    """Wie sich das Pendel in 4 Wochen bewegt hat, in Worten statt Pfeil."""
    if vorher == jetzt:
        return f"Seit 4 Wochen unverändert {jetzt}."
    schritt = (lage.ZONEN.index(jetzt) - lage.ZONEN.index(vorher)) % len(lage.ZONEN)
    if schritt <= 3:
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
    with gzip.open(ABLAGE + ".neu", "wb", compresslevel=3) as f:
        pickle.dump(teile, f)
    os.replace(ABLAGE + ".neu", ABLAGE)


def abgelegt():
    """Gespeicherte Übersicht oder None (fehlt, älter als heute früh, oder Programm bzw. Depot sind jünger)."""
    import gzip
    import pickle
    import depot
    import titel
    try:
        zeit = os.path.getmtime(ABLAGE)
        juenger = [titel.codezeit()] + ([os.path.getmtime(depot.DATEI)] if os.path.exists(depot.DATEI) else [])
        if zeit < max(juenger) or time.time() - zeit > 30 * 3600:
            return None
        with gzip.open(ABLAGE, "rb") as f:
            return pickle.load(f)
    except Exception:  # noqa: BLE001
        return None


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
        pendel_zeile += " ⚠ Marktbreite unsicher – Zone nur unter Vorbehalt."
        pendel_ampel = schlimmste if pendel_ampel == "grün" or schlimmste == "rot" else pendel_ampel
    if p["ampel"] == "grün" and gegen:
        pendel_zeile += " Gegenstimmen: " + ", ".join(gegen) + "."
    import kartentisch
    b = ((kartentisch.laden() or {}).get("barometer")) or {}
    import markt_systeme
    try:
        mm = markt_systeme.minervini(b.get("hochs"), b.get("tiefs"))
        km = markt_systeme.kullamaegi()
    except Exception:  # noqa: BLE001
        mm = km = None
    pendel = "".join(ampelzeile(n, a, x) for n, (a, x) in instr.items())
    kacheln = [
        _kachel("Markt · Minervini", mm["ampel"], mm["wort"], "", mm["text"]) if mm else "",
        _kachel("Markt · Kullamägi", km["ampel"], km["wort"], "",
                km["text"] + " – Breakout und Episodic Pivot nur im Aufwärtstrend") if km else "",
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
            f'<div style="font-size:13px;letter-spacing:0.12em;text-transform:uppercase;color:{TEXT_3}">SEPA · Invest Cockpit</div>'
            f'<h1 style="margin:0;font-size:32px;font-weight:600">Lage am Abend</h1></div>'
            f'<div style="display:flex;gap:16px;font-size:14px;color:{TEXT_2}">'
            f'<span>Stand {stand:%d.%m.%Y}</span>'
            f'<span title="Datenampel aus dem Protokoll des Nachtlaufs (daten/nachtlauf/protokoll.json)" '
            f'style="display:flex;gap:6px;align-items:center">{punkt(_nacht[0], 10)}{t(_nacht[1])}</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;color:{TEXT_3}">geladen in {zahl(time.time() - start, 1)} s</span>'
            f'</div></header>')
    leiste = (f'<section aria-label="Lageleiste" style="display:grid;grid-template-columns:repeat(auto-fit,'
              f'minmax(240px,1fr));gap:16px">{"".join(kacheln)}</section>')

    try:
        quad_bild = quadbild.bild(q, quadbild.verlauf(lage))
    except Exception:  # noqa: BLE001 – ohne Bild bleibt die Kachel
        quad_bild = ""
    # Der Kartentisch (Lagebild als Ende von ②, dann ③ und ④) steht dazwischen; app.py setzt ihn mit Knöpfen.
    return {"oben": seite(kopf + sprungleiste() + station("lage") + leiste + quad_bild
                          + station("front") + frontkarte(q) + uebergaenge.tafel(q), unten=12),
            "unten": seite(station("truppe") + depotleiste.leiste(), oben=12)}
