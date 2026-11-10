"""Titelseite eines einzelnen Titels – genau wie die Designvorlage, als HTML.

seite_titel(ticker) lädt alles (Kurse, Index, Fundament), rechnet Mustererkennung,
Phase, Basenzählung und Fundament-Ampeln und liefert die fertige Seite als HTML-Text.
"""
import os
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

import daten                                          # noqa: E402
import erkennung                                      # noqa: E402
import tpo_daten                                      # noqa: E402
import fundament                                      # noqa: E402
import fruehwarnung                                   # noqa: E402
import depotleiste                                    # noqa: E402
import rs_rang                                        # noqa: E402
import phase as phasen_modul                          # noqa: E402
import namen_de                                       # noqa: E402
import marktrichtung                                  # noqa: E402
import marktdaten                                     # noqa: E402
import rudel                                          # noqa: E402
import rudelkarte                                     # noqa: E402
import quellen                                        # noqa: E402
import sektoren                                       # noqa: E402
import sic13                                          # noqa: E402
import lagekarte                                      # noqa: E402
import markt_systeme                                  # noqa: E402
import system_minervini                               # noqa: E402
import system_kullamaegi                              # noqa: E402
import fuehrer_rang                                   # noqa: E402
import gestaltung                                     # noqa: E402
from chart import chart, legende, reaktionen, stunden  # noqa: E402
from gestaltung import (BLAU, GELB, GRUEN, RAND, ROT, TEXT_2, TEXT_3, ampelzeile, kachel, kachel2, karte,  # noqa: E402
                        seite, t, zahl)

PHASENTEXT = {1: "Bodenbildung", 2: "Aufwärtstrend", 3: "Gipfelphase", 4: "Abwärtstrend"}
def _tv_symbol(tk):
    """BÖRSE:TICKER für TradingView aus daten/tv/revier.csv; ohne Eintrag nur der Ticker (TradingView sucht dann)."""
    import watchlists
    if watchlists.zu_tv(tk):                     # Börse außerhalb der USA (z. B. RHM.DE → XETR:RHM)
        return watchlists.zu_tv(tk)
    z = sic13._tv(tk.upper())
    ex = z["exchange"] if z is not None and isinstance(z.get("exchange"), str) else None
    sym = tk.upper().replace("-", ".")
    return f"{ex}:{sym}" if ex else sym


def _termin(fd):
    """„ · Zahlen am Di 12.11. (in 7 Tagen)“ – innerhalb von 10 Tagen gelb markiert (O'Neil: nicht kurz davor kaufen)."""
    termin = (fd or {}).get("termin")
    if termin is None or not len(termin) or not termin["datum"].iloc[0]:
        return ""
    tag = pd.Timestamp(termin["datum"].iloc[0])
    if pd.isna(tag):
        return ""
    bis = (tag.normalize() - pd.Timestamp.today().normalize()).days
    if bis < 0:
        return ""
    farbe = GELB if bis <= 10 else TEXT_2
    return (f' · <span style="color:{farbe}">Zahlen {WOCHENTAGE[tag.weekday()]} {tag:%d.%m.}'
            f' ({"heute" if bis == 0 else "morgen" if bis == 1 else f"in {bis} Tagen"})</span>')


def _kopf(tk, sb, df, fd=None, mit_rueckgang=True):
    """Kopf: Name, Branche, Kurs, Abstand zum 52-Wochen-Hoch (Trendvorlage) und der nächste Zahlentermin."""
    k = df["Close"].iloc[-1]
    letzte = df.iloc[-252:]
    hoch = letzte["High"].max()
    abstand = (1 - k / hoch) * 100
    lage = "am 52-Wochen-Hoch" if abstand < 1 else f"{zahl(abstand, 0)} % unter dem 52-Wochen-Hoch"
    tief_nach = letzte.loc[letzte["High"].idxmax():, "Low"].min()
    rueckgang = (1 - tief_nach / hoch) * 100
    if rueckgang >= 10 and mit_rueckgang:         # mit Base steht der Rückgang in Kachel und Chart (10.11.2026)
        lage += f" · Rückgang Hoch bis Tief {zahl(rueckgang, 0)} % ({zahl(hoch)} → {zahl(tief_nach)} $)"
    zeile = " · ".join(x for x in (namen_de.SEKTOR.get(sb.get("sektor"), sb.get("sektor")),
                                    namen_de.BRANCHE.get(sb.get("branche"), sb.get("branche"))) if x)
    return (f'<header style="display:flex;flex-direction:column;gap:16px;border-bottom:1px solid {RAND};padding-bottom:20px">'
            f'<div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:16px">'
            f'<div style="display:flex;flex-direction:column;gap:6px;flex:1 1 560px;max-width:900px">'
            f'<h1 style="margin:0;font-size:36px;font-weight:600">{t(sb.get("name", tk))} '
            f'<span style="color:{TEXT_3};font-weight:500">· {t(tk.upper())}</span></h1>'
            f'<div style="font-size:15px;color:{TEXT_2};line-height:1.6">{t(zeile)}{_termin(fd)}</div></div>'
            f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex:0 0 auto;margin-left:auto">'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:34px;font-weight:500">{zahl(k)} $</span>'
            f'<span style="font-size:14px;color:{TEXT_2}">'
            + (f'laufender Tag, Stand {df.attrs["stand"]} Uhr (Yahoo, bis 15 Min. verzögert)' if df.attrs.get("laufend")
               else f'Schluss {df.index[-1]:%d.%m.%Y}') + f' · {lage}</span>'
            f'</div></div></header>')


def _widerspruch(ph):
    """Text der Gegenprobe Zahlen gegen Kurs, wenn starke Zahlen auf Phase 3 oder 4 treffen."""
    if ph in (3, 4):
        return (f"Widerspruch: Zahlen stark, Kurs in Phase {ph} – der Kurs läuft den Zahlen meist voraus; "
                "Führer gipfeln oft bei den besten Zahlen (O'Neil)")
    return ""


def _gruppe_korrektur(df, z, markt, rd):
    """Zeichen neben der Buchregel „Korrektur zum Markt“ (O'Neil: höchstens das 2- bis 3-Fache des Marktes), gemessen
    an der Base des Scanners (06.11.2026, vorher Wertzone): Fiel der Titel mehr als doppelt so tief wie der S&P 500,
    wie tief fiel seine Gruppe im selben Zeitraum? Höchstens das 1,5-Fache der Gruppe = Sektor-Korrektur, keine
    Schwäche des Titels."""
    if not rd or not z or markt is None:
        return None
    x_markt = z["tiefe"] / max(markt, 5.0)
    if x_markt <= 2:
        return None
    try:
        g = rudel.gruppenkurs(rd["rudel"]["mitglieder"])
        teil = g[g.index >= df.index[z["start_i"]]]
        if len(teil) < 5:
            return None
        rueck = float((1 - teil / teil.cummax()).max() * 100)
        faktor = z["tiefe"] / max(rueck, 5.0)
        return {"name": rd["rudel"]["name"], "rueckgang": rueck, "faktor": faktor, "sektor": faktor <= 1.5,
                "x_markt": x_markt}
    except Exception:
        return None


PHASE_AMPEL = {1: "gelb", 2: "grün", 3: "gelb", 4: "rot"}


def _seit(ph_reihe):
    if ph_reihe is None or not len(ph_reihe):
        return None
    anders = ph_reihe[ph_reihe != ph_reihe.iloc[-1]]
    return ph_reihe[ph_reihe.index > anders.index[-1]].index[0] if len(anders) else ph_reihe.index[0]


AUSLOESER_HILFE = (
    "A Ausbruch: Ein Tag schließt jenseits des Wertzonenrahmens, und sein eigener Wertbereich liegt ganz außerhalb. "
    "Die Wertzone muss mindestens 3 Wochen alt sein. Die Front bricht.\n"
    "F Fortsetzung: Dasselbe aus einer jüngeren Wertzone (unter 3 Wochen), die selbst aus einem Lauf in dieselbe "
    "Richtung entstand, also eine Flagge. Kurze Rast, dann stößt die Truppe weiter vor.\n"
    "B bestätigt: Der Wertbereich der ganzen Woche liegt außerhalb der Wertzone. Die POC-Treppe macht eine neue Stufe. "
    "Neue Stellung bezogen.\n"
    "R Rücktest hält: Der Kurs kommt zurück an die Kante der verlassenen Wertzone (long: an ihr VAH), schließt aber "
    "jenseits davon. Der Gegner greift die alte Linie an und wird abgewiesen.\n"
    "S gescheitert: Ein Schluss liegt wieder im Wertbereich der verlassenen Wertzone. Das ist der Stopp. Der Durchbruch "
    "ist zurückgeschlagen.\n"
    "U Umkehr: Nach einem gescheiterten Bruch (S) verlässt der Kurs die junge Wertzone in die Gegenrichtung – Schluss "
    "jenseits des Rahmens, Tageswert ganz außerhalb (Dalton: gescheiterte Auktion). Die Verkäufer fanden unten keine "
    "Abnehmer – die Front dreht.\n"
    "Alle Buchstaben gelten in beide Richtungen, mit ↑ oder ↓ dahinter (zum Beispiel A↓ = Bruch nach unten).")

def _k_zone(erk):
    """Wertzonen-Kachel (Market Profile): eines von vier Wörtern – Balance, an der Schwelle, Ausbruch (Tag n), bestätigt –
    mit Richtung; darunter die Belege."""
    a = erk.get("mp")
    if not a:
        return kachel("Wertzone", "grau", "–", "keine 30-Minuten-Kerzen geladen",
                      "Die Wertzonen werden aus 30-Minuten-Kerzen gerechnet (Market Profile). Für diesen Titel fehlen sie; "
                      "werkzeuge/tpo_laden.py lädt sie.")
    z = a["zustand"]
    return kachel("Wertzone", z["ampel"], z["wort"], " · ".join(z["belege"][:3]),
                  "Market Profile (Steidlmayer, Dalton) aus 30-Minuten-Kerzen. Die Wertzone besteht aus Wochen, deren "
                  "Wertbereich (70 % der Zeit) sich überlappt. Balance: Tageswerte wechseln, POC pendelt. An der Schwelle: "
                  "mindestens 3 der letzten 5 Tageswerte höher (tiefer), keiner ganz dagegen, Tages-POC steigt (fällt), "
                  "Kurs im oberen (unteren) Drittel des Wertbereichs. Ausbruch (A): Schluss jenseits des Rahmens und "
                  "Tageswert ganz außerhalb, Wertzone mindestens 3 Wochen alt (F bei jüngerer Wertzone nach einem Lauf in dieselbe "
                  "Richtung). Bestätigt (B): Wochenwert ganz außerhalb, die POC-Treppe macht eine Stufe. Gescheitert (S): "
                  "Schluss zurück im Wertbereich der verlassenen Wertzone.\n\n" + AUSLOESER_HILFE)


def _k_base(erk):
    """Kachel „Base“: die wievielte Base nach IBD/O'Neil, gezählt auf den Scanner-Zonen (basen.py, 06.11.2026)."""
    bs = erk.get("basen") or {}
    liste = bs.get("liste") or []
    z_ = bs.get("bilanz") or {}
    bilanz = (f" Bilanz der abgeschlossenen Zonen der letzten gut zwei Jahre: {z_.get('gelungen', 0)} gelungen, "
              f"{z_.get('gescheitert', 0)} gescheitert, {z_.get('offen', 0)} offen (gelungen = 20 % über dem Pivot, "
              f"bevor ein Schluss 8 % darunter lag)." if liste else "")
    regel = (" Gezählt wird ab dem Beginn der Phase 2 oder dem letzten Markttief nach einer Korrektur ab 15 % – was "
             "später liegt; eine Zone zählt erst als neue Base, wenn ihre Oberkante 20 % über der zuletzt gezählten liegt "
             "(sonst Base auf Base, gleiche Nummer). Basen und Flaggen zählen.")
    bz = bs.get("zahl")
    if not bz:
        if not liste:
            return kachel("Base", "grau", "keine", "auch keine abgeschlossene Zone in gut zwei Jahren", regel)
        b = liste[-1]
        return kachel("Base", {"gelungen": "grün", "gescheitert": "rot"}.get(b["ausgang"], "gelb"),
                      f"vorige {b['ausgang']}",
                      f"{b['name']}{' Nr. ' + str(b['nummer']) if b.get('nummer') else ''} · Pivot {zahl(b['oben'])} $ · "
                      f"Ausbruch {b['ende_t']:%d.%m.%Y}",
                      "Zurzeit keine reife Base. Gezeigt wird die zuletzt abgeschlossene Zone des Scanners und ihr Ausgang "
                      "nach O'Neil. Eine gescheiterte Base ist oft das Ende des Aufwärtstrends." + regel + bilanz)
    z = ((erk.get("systeme") or {}).get("m") or {}).get("zone") or {}
    ampel = "grün" if bz <= 2 else "gelb" if bz == 3 else "rot"
    zeile = f"{z.get('name', 'Base')} · Tiefe {zahl(z.get('tiefe', 0), 0)} %"
    if bs.get("markt") is not None:
        zeile += f" · S&P 500 zugleich −{zahl(bs['markt'], 0)} %"
    return kachel("Base", ampel, f"Nr. {bz} · {'früh' if bz <= 2 else 'handelbar' if bz == 3 else 'spät'}", zeile,
                  "Die wievielte Base seit Beginn des Aufwärtstrends (IBD/O'Neil). Basen 1 und 2 sind früh und am "
                  "ergiebigsten, die dritte ist noch handelbar, ab der vierten scheitern die meisten. Tiefe der Base gegen "
                  "den Rückgang des S&P 500 im selben Zeitraum: O'Neil erlaubt höchstens das 2- bis 3-Fache." + regel + bilanz)


def _k_geld(x):
    """Kachel Geld (09.11.2026, ersetzt „Branche“ nach Weinstein): die Geld-Ampel aus Rückenwind – drei Stimmen
    Sektor, Branche, Thema; grün = zwei vorne und keine im Abfluss."""
    hilfe = ("Geld aus der Seite Rückenwind: Wohin fließt das Geld? Drei Stimmen – Sektor, Branche und Thema, je mit ihrem "
             "Feld in der Strömungskarte (Führend, Erstarkend, Schwächelnd, Zurückfallend). Grün = mindestens zwei vorne "
             "(führend oder erstarkend) und keine schwächelnd; gelb = eine vorne; rot = keine. Stand des Nachtlaufs.")
    if not x:
        return kachel("Geld", "grau", "–", "erst nach dem nächsten Nachtlauf", hilfe)
    wort = {"Führend": "führend", "Erstarkend": "erstarkend", "Ermüdend": "schwächelnd", "Abgehängt": "zurückfallend"}
    zeile = " · ".join(f"{art} {wort.get(x.get(f'{k}_feld'), '–')}"
                       for art, k in (("Sektor", "sektor"), ("Branche", "branche"), ("Thema", "thema")))
    hilfe += (f"\n\nSektor: {x.get('sektor') or '–'} · Branche: {namen_de.branche(x.get('branche') or '') or '–'}"
              + (f" · Thema: {x['thema'].split(' · ')[0]}" if x.get("thema") else ""))
    return kachel("Geld", x["geld_ampel"], {"grün": "Rückenwind", "gelb": "halb", "rot": "Gegenwind"}[x["geld_ampel"]],
                  zeile, hilfe)


def _ereignis(df, gewinne, fund):
    """Die letzten Zahlen als Ereignis, gelesen nach O'Neils Kursreaktion: Tag 1, Tage 2–10 und Erholung; gute Zahlen,
    die der Kurs hält, gegen „gute Nachricht, schlechte Reaktion“. (Ampel, Wert, Zeile, Hilfe) oder None."""
    r = _reaktion_zeilen(df, gewinne)
    if not r:
        return None
    tag, prozent, vor = r["tag"], r["prozent"], r["vor"]
    k = float(df["Close"].iloc[-1])
    tage = len(df) - 1 - df.index.get_loc(tag)
    a_, txt = (fund or {}).get("punkte", {}).get("Quartalsgewinn zum Vorjahr", ("grau", ""))
    gewinn = "" if a_ == "grau" else f" · Gewinn {txt.split(' / ')[-1].split(' (')[0]}"
    zeile = f"Zahlen {tag:%d.%m.}{gewinn} · Tag 1 {'+' if prozent >= 0 else '−'}{zahl(abs(prozent), 1)} %"
    folge = [a for _, a, _ in r["zeilen"][1:]]
    if k < vor:
        ampel, wert = "rot", "Zahlen verworfen"
    elif prozent > 0 and all(a in ("grün", "grau") for a in folge):
        ampel, wert = "grün", "Zahlen angenommen"
    elif prozent > 0:
        ampel, wert = "gelb", "teils angenommen"
    else:
        ampel, wert = "gelb", "Reaktion verhalten"
    if tage > 63:
        ampel = "grau"
    zeile += f" · Kurs {'über' if k >= vor else 'unter'} {zahl(vor)} $ vor den Zahlen"
    ablesung = "\n".join(f"{n}: {x}" for n, _, x in r["zeilen"])
    return (ampel, wert, zeile,
                  "Die letzten Zahlen als Ereignis, das eine Seitwärtsphase brechen kann (O'Neil). Zahlen angenommen: "
                  "positiver erster Tag, die Gewinne halten in den Tagen 2–10, der Kurs fällt nie unter den Schluss vor "
                  "den Zahlen – das ist die Marke für den Stopp. Teils angenommen: positiver erster Tag, danach Gewinne "
                  "abgegeben oder kurz unter den Ausgangskurs. Zahlen verworfen: Kurs darunter, O'Neils „gute Nachricht, "
                  "schlechte Reaktion“. Grau, wenn die Zahlen über drei Monate zurückliegen.\n\n" + ablesung)


def _k_zahlen(fd, fund):
    termin = (fd or {}).get("termin")
    if termin is None or not len(termin) or not termin["datum"].iloc[0]:
        return kachel("Nächste Zahlen", "grau", "–", "kein Termin bekannt", "")
    tag = pd.Timestamp(termin["datum"].iloc[0])
    if pd.isna(tag):
        return kachel("Nächste Zahlen", "grau", "–", "kein Termin bekannt", "")
    bis = (tag.normalize() - pd.Timestamp.today().normalize()).days
    if bis < 0:                                  # Termin liegt hinter uns, Yahoo kennt den nächsten noch nicht
        return kachel("Nächste Zahlen", "grau", "noch offen",
                      f"zuletzt gemeldet {WOCHENTAGE[tag.weekday()]} {tag:%d.%m.%Y}" + _zuletzt(fund),
                      "Der letzte Termin liegt hinter uns; der nächste ist noch nicht angekündigt.")
    nah = 0 <= bis <= 10
    return kachel("Nächste Zahlen", "gelb" if nah else "grün",
                  "heute" if bis == 0 else "morgen" if bis == 1 else f"in {bis} Tagen",
                  f"{WOCHENTAGE[tag.weekday()]} {tag:%d.%m.%Y}" + (" · Ausbruch davor riskant" if nah else _zuletzt(fund)),
                  "Ein Ausbruch in den letzten zehn Tagen vor den Zahlen ist ein Würfelwurf (O'Neil, Minervini).")


def _zuletzt(fund):
    a_, txt = (fund or {}).get("punkte", {}).get("Überraschung", ("grau", ""))
    if a_ == "grau":
        return ""
    x = txt.split(" / ")[-1]
    return f" · zuletzt {x} {'über' if not x.startswith('−') else 'unter'} Erwartung"


# ── Zwei Systeme (05.11.2026): Minervini (M) und Kullamägi (K) getrennt, je Kachel eine Ampel pro System ──
def _k2_markt(mm, km, mr):
    m = (mm["ampel"], mm["wort"]) if mm else ("grau", "–")
    k = (km["ampel"], km["wort"]) if km else ("grau", "–")
    oneil = (f"O'Neil: {mr['zustand']} seit {mr['seit']:%d.%m.%Y}" if mr else "")
    return kachel2("Markt", m, k, oneil,
                   "M – " + (mm["regel"] + "\n" + mm["text"] if mm else "keine Daten") + "\n\nK – "
                   + (km["regel"] + "\n" + km["text"] if km else "keine Daten")
                   + ("\n\nZeichen O'Neil (keine Regel mehr): " + mr["text"] if mr else ""))


def _weinstein_ausbruch(m, ph, df):
    """Zusatz, wenn ein Titel aus Phase 3 nach oben ausbricht (10.11.2026, Micky): die Phasengrenzen bleiben, aber
    Weinstein sieht darin eine mögliche Rückkehr in Phase 2 – bestätigt nur mit Volumen über dem Schnitt und wieder
    steigender 30-Wochen-Linie."""
    br = m.get("ausbruch") or {}
    if ph != 3 or br.get("tag") is None or br.get("fehl") or df is None or len(df) < 170:
        return ""
    v = br.get("volumen")
    gd = df["Close"].rolling(150).mean()
    steigt = bool(gd.iloc[-1] > gd.iloc[-21])
    ok = bool(v and v == v and v >= 1.0) and steigt
    gruende = []
    if v and v == v:
        gruende.append(f"Volumen {zahl(v, 1)}-fach")
    gruende.append("30-Wochen-Linie steigt" if steigt else "30-Wochen-Linie noch flach")
    return (f" · Ausbruch nach oben am {pd.Timestamp(br['tag']):%d.%m.} – Rückkehr in Phase 2 "
            + ("bestätigt" if ok else "möglich, noch nicht bestätigt") + f" ({', '.join(gruende)})")


def _k2_trend(m, ph, ph_reihe, df=None):
    tv = m["trendvorlage"]
    n = sum(tv.values()) if tv else 0
    mm = (("grün" if n == 7 else "gelb" if n >= 5 else "rot"), f"Trendvorlage {n} von 7") if tv else ("grau", "zu kurz")
    seit = _seit(ph_reihe) if ph else None
    zeile = (f"Zeichen Weinstein: Phase {ph} {PHASENTEXT[ph]}"
             + (f" seit KW {seit.isocalendar()[1]}/{seit.year}" if seit is not None else "")
             + _weinstein_ausbruch(m, ph, df)) if ph else ""
    return kachel2("Trend", mm, None, zeile,
                   "M – Minervinis Trendvorlage, sieben Punkte zu Kurs und Durchschnitten (der achte, RS ab 70, steht in "
                   "der Kachel „Stärke“). Sie entspricht Weinsteins Stufe 2: "
                   + "; ".join(f"{n_} {'✓' if ok else '✗'}" for n_, ok in tv.items())
                   + "\n\nK – Kullamägi nutzt keine Trendvorlage; seine Auswahl ist die Stärke (Kachel „Stärke“)."
                   + "\n\nPhase nach Weinstein nur noch als Zeichen. Bricht ein Titel aus Phase 3 nach oben aus, sieht "
                     "Weinstein eine mögliche Rückkehr in Phase 2 – bestätigt mit Volumen über dem Schnitt und wieder "
                     "steigender 30-Wochen-Linie.")


def _k2_staerke(m, k, rang, rw=None):
    mm = (("grün" if rang >= 70 else "gelb" if rang >= 60 else "rot"), f"RS {rang} von 99") if rang is not None \
        else ("grau", "kein RS-Rang")
    fr = k["fuehrer"]
    best = max((v for v in (fr or {}).values() if v == v), default=None)
    # K als „oberste x %“ (10.11.2026): „besser als 92,6 %“ in Rot wirkte widersinnig – Kullamägi will die obersten 1–2 %
    kk = (k["fuehrer_ampel"], f"oberste {zahl(max(0.1, 100 - best), 1 if best >= 90 else 0)} %") \
        if best is not None else ("grau", "–")
    zeile = (f'Rückenwind: {rw["stufe"] or "keine Stufe"} · RS-Rang {rw["rang_vor4"]} → {rw["rang"]} '
             f'({rw["tempo"]:+d} in 4 Wo.)' if rw else fuehrer_rang.text(fr))
    return kachel2("Stärke", mm, kk, zeile,
                   "M – RS-Rang 1–99 wie das RS-Rating von IBD (12 Monate, jüngstes Quartal doppelt), verglichen mit "
                   "unserem Revier. Minervini verlangt mindestens 70 – der achte Punkt der Trendvorlage. Die Zahl ist "
                   "kein Listenplatz: 16 heißt, nur 16 % der Titel liefen schwächer.\n\nK – Kullamägi sucht die ein bis "
                   "zwei Prozent mit den größten Kursanstiegen über 1, 3 und 6 Monate. Grün = in einem Zeitraum unter "
                   "den obersten 2 %, gelb = oberste 5 %. Angezeigt: der beste der drei Zeiträume ("
                   + fuehrer_rang.text(fr) + ").\n\nRückenwind – die Stufe aus der Seite Rückenwind: Entsteht = früh, "
                   "das Geld beginnt zu fließen, auch wenn der RS-Rang noch unter 70 liegt.")


def _k2_fundament(m, k, fund, ph, df, gewinne):
    z = next(r for r in m["regeln"] if r[0] == "Zahlen wachsen")
    if not fund:
        mm = ("grau", "keine Daten")
    else:
        pk = fund["punkte"]
        g, u = pk.get("Quartalsgewinn zum Vorjahr", ("grau", ""))[0], pk.get("Umsatz", ("grau", ""))[0]
        mm = ("grün" if g == "grün" and u == "grün" else "rot" if "rot" in (g, u) else "gelb",
              "wachsen" if z[1] else "zu schwach")
    ep = k.get("ep")
    kk = ((("grün", "Zahlen am Sprungtag") if ep["regeln"][2][1] else ("gelb", "Nachricht prüfen"))
          if ep else None)
    ev = _ereignis(df, gewinne, fund) if (df is not None and fund) else None
    zeile = z[2] + (f" · {ev[1]}" if ev and ev[0] != "grau" else "")
    gruen = sum(1 for a, _ in fund["punkte"].values() if a == "grün") if fund else 0
    return kachel2("Fundament", mm, kk, zeile,
                   "M – Minervini kauft Führer mit wachsenden Zahlen: Quartalsgewinn und Umsatz zum Vorjahr nicht rot "
                   f"(grün ab 25 %). Alle sieben Prüfpunkte: {gruen} von 7 grün (Liste weiter unten). "
                   + (_widerspruch(ph) or "")
                   + "\n\nK – Beim Breakout schaut Kullamägi nicht auf die Zahlen (rein technisch). Beim Episodic Pivot "
                     "braucht er eine Nachricht, die den Markt zur Neubewertung zwingt – oft überraschend starke Zahlen."
                   + (f"\n\nReaktion auf die letzten Zahlen (Zeichen, O'Neil): {ev[1]} – {ev[2]}\n{ev[3]}" if ev else ""))


def _k2_setup(m, k, erk, df):
    mm = (m["ampel"], m["setup"] if m["setup"] != "keines" else "keines")
    em = k.get("ermuedung")
    h = k.get("haupt")
    if em and (not h or h["ampel"] == "rot"):
        kk = (em["ampel"], "Ermüdung (short)" + (f" vor {em['tage_her']} T." if em["tage_her"] else ""))
    else:
        kk = ((h["ampel"], h["art"] + (f" vor {h['tage_her']} T." if h["art"] == "Episodic Pivot" and h["tage_her"] else ""))
              if h and h["ampel"] != "rot" else ("rot", "keines"))
    teile = ([f"Pivot {zahl(m['pivot'])} $ · {m['lage']}"] if m.get("pivot")     # Base und Tiefe stehen in „Base“
             else [next(x for n, _, x in m["regeln"] if n.startswith("Reife Base"))])
    hilfe = ("M – " + system_minervini.kurz(m) + "\n" + "\n".join(f"{'✓' if ok else '✗'} {n} – {x}" for n, ok, x in m["regeln"])
             + "\n\nK – " + "\n".join(
                 f"{x['art']} ({x['ampel']}):\n" + "\n".join(f"{'✓' if ok else '✗'} {n} – {y}" for n, ok, y in x["regeln"])
                 for x in (k.get("ep"), k.get("breakout"), em) if x))
    return kachel2("Setup", mm, kk, " · ".join(x for x in teile if x), hilfe)


def _k2_enge(m, k, erk, df):
    e = m.get("enge") or {}
    eng = next(r for r in m["regeln"] if r[0] == "Enge (VCP)")
    wort = {"grün": "ja", "gelb": "teilweise", "rot": "nein"}
    reif = next(r for r in m["regeln"] if r[0].startswith("Reife Base"))[1]
    mm = (e["ampel"], wort[e["ampel"]]) if reif and e.get("ampel") in wort else ("grau", "nicht messbar")
    b = k.get("breakout") or {}
    kons = next((r for r in b.get("regeln", []) if r[0].startswith("Konsolidierung")), None)
    kk = (("grün" if kons[1] else "gelb" if b.get("wochen") and b["wochen"] <= system_kullamaegi.KONS_GELB else "rot"),
          f"{b['wochen']} Woche{'n' if b['wochen'] != 1 else ''}") if kons and b.get("wochen") else ("grau", "keine Zone")
    zeile = eng[2]
    if reif and e.get("folge"):
        zeile = f"Kontraktionen {e['folge']} %" + (f" · Volumen {zahl(e['volumen'] / 100, 1)}-fach"
                                                     if e.get("volumen") == e.get("volumen") and e.get("volumen") else "")
    return kachel2("Enge", mm, kk, zeile,
                   "M – Minervinis VCP (Baustein 2 des Scanners, wie im Chart): jede Kontraktion höchstens 70 % so tief "
                   "wie die vorige, die letzte höchstens 10 %, das Volumen leiser als in der ersten. Grün = mindestens "
                   "zwei schrumpfende Kontraktionen; rot = die letzte ist tiefer als die vorige.\n\n"
                   "K – Kullamägi: kurze Konsolidierung, meist 1–3 Wochen, nach einem Schub nach oben, vorzugsweise bei "
                   "reduziertem Volumen. Gelb bis 8 Wochen.")


def _kacheln(erk, ph, ph_reihe, fund, df, rd, fd, mr, gewinne, m, k, mm, km, rw=None):
    """Die acht Kacheln der Titelseite (Zwei Systeme, 05.11.2026): sechs mit je einer Ampel für Minervini (M) und
    Kullamägi (K), Branche und Base als Zeichen. Fehlt ein Wert, steht ein grauer Punkt mit dem Grund."""
    _k_zone(erk), _k_zahlen(fd, fund)            # nur mitgeschrieben für die Lagekarte, hier nicht gezeigt
    rang = (erk.get("rs_rang") or (None, ""))[0]
    kl = [_k2_markt(mm, km, mr), _k2_trend(m, ph, ph_reihe, df), _k2_staerke(m, k, rang, rw),
          _k2_fundament(m, k, fund, ph, df, gewinne), _k2_setup(m, k, erk, df), _k2_enge(m, k, erk, df),
          _k_geld(rw), _k_base(erk)]
    return (f'<section aria-label="Lage in fünf Sekunden" style="display:grid;'
            f'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">{"".join(kl)}</section>')


def _regel_ampel(m, fund):
    """Farbe einer Regel im Plan wie in ihrer Kachel (10.11.2026: vorher Kachel gelb, Plan rot oder grün)."""
    tv = m.get("trendvorlage") or {}
    n = sum(tv.values()) if tv else 0
    aus = {"Trendvorlage": "grün" if n == 7 else "gelb" if n >= 5 else "rot",
           "Enge (VCP)": (m.get("enge") or {}).get("ampel")}
    if fund:
        pk = fund["punkte"]
        g, u = pk.get("Quartalsgewinn zum Vorjahr", ("grau", ""))[0], pk.get("Umsatz", ("grau", ""))[0]
        aus["Zahlen wachsen"] = "grün" if g == "grün" and u == "grün" else "rot" if "rot" in (g, u) else "gelb"
    return aus


def _plan(m, k, mm, km, df, marken=None, fund=None):
    """Karte „Plan“ der zwei Systeme und des VCP-Scanners: je System die Regeln (Farbe wie in der Kachel), Einstieg,
    Kaufzone, ein Stopp (1,5 ATR wie im Chart) und Ausstieg – als Zeilen, nicht als Textblock (10.11.2026)."""
    c, h, l = df["Close"], df["High"], df["Low"]
    kurs = float(c.iloc[-1])
    marken = marken or {}
    stopp = marken.get("stopp")
    farbe = _regel_ampel(m, fund)
    teile = []
    # System Minervini
    kopf = {"grün": "🟢 <b>Minervini: Setup steht</b>", "gelb": "🟡 <b>Minervini: eine Regel fehlt</b>",
            "rot": "⚪ <b>Minervini: kein Setup</b>"}[m["ampel"]]
    teile.append(f'<p style="margin:0;font-size:16px">{kopf} · Markt {mm["wort"] if mm else "–"}</p>')
    teile.append("".join(ampelzeile(n, next((f for k_, f in farbe.items() if n.startswith(k_) and f), None)
                                    or ("grün" if ok else "rot"), x) for n, ok, x in m["regeln"]))
    if m.get("pivot"):
        vorbehalt = "" if m["ampel"] == "grün" else " – erst wenn die fehlenden Regeln erfüllt sind, bis dahin nur Marke"
        zeilen = [("blau", f"Kauf über dem Pivot {zahl(m['pivot'])} ${vorbehalt}", ""),
                  ("blau", f"Kaufzone bis {zahl(m['pivot'] * 1.05)} $", m["lage"])]
        if stopp:
            zeilen.append(("rot", f"Stopp {zahl(stopp)} $ (1,5 ATR, {_vorzeichen((stopp / m['pivot'] - 1) * 100)} % "
                                  f"vom Pivot)", "dieselbe Linie wie im Chart"))
        aus_ = m["ausstieg"].replace("Stopp unter dem Tief der letzten Kontraktion, höchstens 8 % unter dem Pivot. ", "")
        zeilen.append(("grau", "Ausstieg", aus_))
        teile.append("".join(ampelzeile(n, a, x) for a, n, x in zeilen))
    elif len(c) >= 260:
        g50, g150, g200 = (float(c.iloc[-n:].mean()) for n in (50, 150, 200))
        tief52, hoch52 = float(l.iloc[-252:].min()), float(h.iloc[-252:].max())
        marken_ = []
        if kurs < max(g150, g200):
            marken_.append((max(g150, g200), "Kurs über GD150 und GD200"))
        if kurs < 1.30 * tief52:
            marken_.append((1.30 * tief52, "mindestens 30 % über dem 52-Wochen-Tief"))
        if kurs < 0.75 * hoch52:
            marken_.append((0.75 * hoch52, "höchstens 25 % unter dem 52-Wochen-Hoch"))
        if kurs < g50:
            marken_.append((g50, "GD50 zurückerobert"))
        if marken_:
            teile.append(f'<p style="margin:0;font-size:15px;color:{TEXT_2}">Marken zur Trendvorlage (die nächste zuerst):</p>'
                         + "".join(ampelzeile(f"{zahl(p_)} $ ({_vorzeichen((p_ / kurs - 1) * 100)} %)", "grau", x)
                                   for p_, x in sorted(marken_)))
    # VCP-Scanner (eigene Reihe „VCP · Enge grün“ im Kartentisch; vorher fehlte sein Urteil auf der Titelseite)
    z_ = next((x for n, ok, x in m["regeln"] if n.startswith("Reife Base") and ok), None)
    e_ = (m.get("enge") or {}).get("ampel")
    if z_ and m.get("pivot") and m.get("abstand") is not None:
        ab = m["abstand"]
        br_ = m.get("ausbruch") or {}
        if br_.get("fehl"):
            urteil, a_ = (f"Fehlausbruch: Kurs {_vorzeichen(ab)} % zum Pivot – zurück in der Zone, kein Einstieg, bis "
                          "der Kurs wieder über dem Pivot schließt"), "rot"
        elif 0 <= ab <= 5:
            urteil, a_ = f"Kurs {_vorzeichen(ab)} % über dem Pivot – in der Kaufzone", "grün" if e_ == "grün" else "gelb"
        elif -5 <= ab < 0:
            urteil, a_ = f"Kurs {_vorzeichen(ab)} % unter dem Pivot – Auslöser in Reichweite", "grün" if e_ == "grün" else "gelb"
        elif ab > 5:
            urteil, a_ = (f"Kurs {_vorzeichen(ab)} % über dem Pivot – über der Kaufzone, ausgedehnt: nach Regel kein "
                          "Einstieg, Rücksetzer Richtung Pivot abwarten"), "gelb"
        else:
            urteil, a_ = f"Kurs {_vorzeichen(ab)} % unter dem Pivot – der Auslöser steht noch aus", "gelb"
        if e_ != "grün" and a_ != "rot":
            a_ = "rot" if e_ == "rot" else "gelb"
        teile.append(f'<p style="margin:12px 0 0;font-size:16px">{ {"grün": "🟢", "gelb": "🟡", "rot": "⚪"}[a_] } '
                     f'<b>VCP-Scanner</b> · {t(z_)} · Enge {"grün" if e_ == "grün" else e_ or "–"}</p>'
                     + ampelzeile(urteil, a_, "Reihe „VCP · Enge grün“: Enge grün und Kurs höchstens 5 % vom Pivot"))
    # System Kullamägi
    hk = k.get("haupt")
    kopf = ("🟢 <b>Kullamägi: " + hk["art"] + " steht</b>" if hk and hk["ampel"] == "grün"
            else "🟡 <b>Kullamägi: " + hk["art"] + " fast</b>" if hk and hk["ampel"] == "gelb"
            else "⚪ <b>Kullamägi: kein Long-Setup</b>")
    teile.append(f'<p style="margin:12px 0 0;font-size:16px">{kopf} · Markt {km["wort"] if km else "–"}'
                 + (" – Breakout und EP nur im Aufwärtstrend" if km and km["ampel"] != "grün" else "") + '</p>')
    for x in (k.get("ep"), k.get("breakout")):
        if x:
            teile.append(f'<p style="margin:0;font-size:14px;color:{TEXT_2}">{x["art"]}</p>'
                         + "".join(ampelzeile(n, "grün" if ok else "rot", y) for n, ok, y in x["regeln"]))
    if hk and hk["ampel"] != "rot":
        ziel = (f'über dem Hoch des Sprungtags {zahl(hk["pivot"])} $' if hk["art"] == "Episodic Pivot"
                else f'beim Ausbruch über die Oberkante {zahl(hk["pivot"])} $' if hk.get("pivot") else "beim Ausbruch")
        teile.append(ampelzeile(f"Einstieg {ziel}", "blau", "über dem Hoch der ersten 5-, 30- oder 60-Minuten-Kerze "
                                                            "(je länger, desto weniger Fehlausbrüche)")
                     + (ampelzeile(f"Stopp {zahl(stopp)} $ (1,5 ATR)", "rot", "dieselbe Linie wie im Chart") if stopp else "")
                     + ampelzeile("Ausstieg", "grau", k["ausstieg"]))
    em = k.get("ermuedung")
    if em:
        teile.append(f'<p style="margin:12px 0 0;font-size:16px">{"🔴" if em["ampel"] == "grün" else "🟡"} '
                     f'<b>Ermüdung nach Überdehnung (Short)</b> – Bruch der Flagge am {em["tag"]:%d.%m.}, '
                     f'Fahnenstange +{zahl(em["stange"], 0)} %</p>'
                     + "".join(ampelzeile(n, "grün" if ok else "gelb", y) for n, ok, y in em["regeln"])
                     + ampelzeile(f"Unterkante {zahl(em['unten'])} $ · Stopp "
                                  f"{zahl(((marken.get('short') or {}).get('stopp')) or em['stopp'])} $ (1,5 ATR)", "rot",
                                  "Die Truppe ist weit vorgestoßen, hat sich eingegraben – jetzt bricht die Stellung "
                                  "nach hinten weg. Dieselbe Stopp-Linie wie im Chart."))
    rand = GRUEN if "grün" in (m["ampel"], (hk or {}).get("ampel")) else ROT if em and em["ampel"] == "grün" else BLAU
    return "".join(teile), rand


def _stellung(df, marken):
    """Was die Stellung heute zeigt (10.11.2026), für Lagezeile und Warnzeichen: [(Ampel, Text)]. Gebrochene Stellung
    (Kurs unter dem Stopp, Fehlausbruch) und Ausbruch ohne Volumen – vorher nur klein im Chart."""
    aus = []
    kurs = float(df["Close"].iloc[-1])
    st_ = (marken or {}).get("stopp")
    if st_ and kurs < st_:
        aus.append(("rot", f"Stellung gebrochen: Kurs {zahl(kurs)} $ unter dem Stopp {zahl(st_)} $ (1,5 ATR)"))
    br = (marken or {}).get("ausbruch") or {}
    if br.get("fehl_tag") is not None:
        aus.append(("rot", f"Fehlausbruch am {pd.Timestamp(br['fehl_tag']):%d.%m.} – der Kurs fiel zurück unter den "
                           f"Pivot {zahl(marken['einstieg'])} $" if marken.get("einstieg") else
                           f"Fehlausbruch am {pd.Timestamp(br['fehl_tag']):%d.%m.}"))
    v = br.get("volumen")
    if br.get("tag") is not None and v and v == v and v < 1.0:
        aus.append(("gelb", f"Ausbruch am {pd.Timestamp(br['tag']):%d.%m.} ohne Volumen: {zahl(v, 1)}-fach des "
                            f"50-Tage-Schnitts (deine Regel: darüber)"))
    return aus


def _lagezeile(tk, rw, stellung):
    """Leiste unter dem Kopf (10.11.2026): dreifacher Rückenwind, Volltreffer, Reihe im Kartentisch, gebrochene
    Stellung – die wichtigsten Aussagen der Seite auf einen Blick."""
    chips = []
    drei = bool(rw and rw.get("stufe") in ("Entsteht", "Läuft") and rw.get("geld_ampel") == "grün"
                and (rw.get("zahlen") or {}).get("ampel") == "grün")
    e = _eintrag(tk) or {}
    reihe = None
    if e.get("reihe"):
        try:
            import kartentisch
            reihe = ({k: n for k, n, _ in kartentisch.REIHEN} | kartentisch.ALTE_REIHEN).get(e["reihe"], e["reihe"])
        except Exception:  # noqa: BLE001
            reihe = e["reihe"]
    if drei and reihe:
        chips.append((GRUEN, "★ Volltreffer: dreifacher Rückenwind und Setup"))
    elif drei:
        chips.append((GRUEN, "▲▲▲ dreifacher Rückenwind (Kurs, Geld, Zahlen grün)"))
    if reihe:
        chips.append((BLAU, f"Kartentisch: {reihe}"))
    for a, text in stellung:
        chips.append((ROT if a == "rot" else GELB, text))
    if not chips:
        return ""
    return ('<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">' + "".join(
        f'<span style="border:1px solid {f};color:{f};border-radius:8px;padding:5px 12px;font-size:15px;'
        f'font-weight:600">{t(x)}</span>' for f, x in chips) + '</div>')


def _ist_warnung(h):
    """Hinweise der Mustererkennung, die warnen; die übrigen stehen schon in den Kacheln."""
    if h.startswith(("Phase ", "Base Nr.", "späte Base", "Ausbruch aus der Base", "in der Kaufzone", "ausgedehnt",
                     "Volumen trocknet aus", "Tiefe grün")):
        return False
    return True


def _warnzeichen(erk, krit=None, stellung=()):
    """Nur Warnungen: Frühwarnzeichen Phase 3/4 (Weinstein), Klimax, Übernahme-Verdacht, gestörte Daten, unsichere
    Mustererkennung und Hinweise, die in keiner Kachel stehen."""
    zeilen = "".join(ampelzeile(text, a, "") for a, text in stellung)
    zeilen += "".join(ampelzeile(text, a, "Weinstein: Frühwarnzeichen für Long-Halter, bevor die Phase wechselt – die "
                                          "Phasengrenzen bleiben unverändert") for a, text in erk.get("fruehwarnung", []))
    zeilen += "".join(ampelzeile(h, "rot" if h.startswith(("Daten gestört", "Klimax", "Übernahme")) or "(rot)" in h
                                else "gelb", "") for h in erk["hinweise"] if _ist_warnung(h))
    gk = erk.get("gruppe_korrektur")
    if gk:
        zeilen += ampelzeile(f'Base {zahl(gk["x_markt"], 1)}-fach so tief wie der S&P 500 · '
                             + ("Sektor-Korrektur: " if gk["sektor"] else "Schwächer als die Gruppe: ")
                             + f'Gruppe {namen_de.branche(gk["name"])} −{zahl(gk["rueckgang"], 0)} %, Titel {zahl(gk["faktor"], 1)}-fach der Gruppe '
                             "(Zeichen neben der Buchregel, ändert die Ampel nicht)", "gelb", "")
    zeilen += "".join(ampelzeile(f"Phase: {w}", "rot", "Warnzeichen der Phase nach Weinstein") for w in (krit or {}).get("warnungen", []))
    zeilen += "".join(ampelzeile(f"Datenampel: {text}", a, "") for a, _, text in erk.get("daten", {}).get("zeichen", []))
    return karte(zeilen or f'<div style="color:{TEXT_2};font-size:15px">Keine Warnzeichen.</div>', "Warnzeichen")



WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


RS_BILDER = [("beide steigen", "Führer im Markt und in seinem Sektor"),
             ("gegen S&P 500 fällt, gegen Sektor steigt", "der Sektor ist schwach, der Titel darin einer der Besten"),
             ("gegen S&P 500 steigt, gegen Sektor fällt", "läuft nur mit dem starken Sektor mit, darin kein Führer"),
             ("beide fallen", "schwächer als Markt und Sektor")]


def _rs_lesart(df, index, sek, etf):
    """Hinweiskasten beim Überfahren des RS-Feldes im Chart: das heutige Bild (Richtung der letzten
    3 Monate; unter ±2 % gilt eine Linie als seitwärts) und die vier Bilder. Die Wertzone liegt genau über
    dem RS-Feld des Charts (SVG-Koordinaten y 604–724 von 760, x von 64 bis zur Etikettenspalte)."""
    if index is None:
        return ""

    def richtung(bezug):
        r = (df["Close"] / bezug.reindex(df.index, method="ffill")).dropna()
        if len(r) < 64:
            return None, None
        a = (r.iloc[-1] / r.iloc[-64] - 1) * 100
        return (1 if a > 2 else -1 if a < -2 else 0), a

    rm, am = richtung(index["Close"])
    rk, ak = richtung(sek) if sek is not None else (None, None)
    if rm is None:
        return ""
    zahlen = f"gegen S&P 500 {_vorzeichen(am, 0)} %" + (f", gegen {etf} {_vorzeichen(ak, 0)} %" if ak is not None else "")
    heute_i = {(1, 1): 0, (-1, 1): 1, (1, -1): 2, (-1, -1): 3}.get((rm, rk)) if rm and rk else None
    heute = (f"{RS_BILDER[heute_i][0]}: {RS_BILDER[heute_i][1]}" if heute_i is not None
             else "kein klares Bild – mindestens eine Linie läuft seitwärts (weniger als ±2 %)")
    liste = "".join(f'<div style="{"color:#E6EAF0;font-weight:600" if i == heute_i else ""}">'
                    f'{"▶ " if i == heute_i else "• "}{t(b)}: {t(m)}</div>' for i, (b, m) in enumerate(RS_BILDER))
    tip = (f'<div class="hinweis-tip"><div style="font-size:14px;color:#E6EAF0;font-weight:600">Heute: {t(heute)}</div>'
           f'<div>Letzte 3 Monate: {t(zahlen)}</div>'
           f'<div style="margin:6px 0 4px">Linie 100 = so stark wie der Index; steigt die Linie, gewinnt der Titel dazu.</div>'
           f'{liste}</div>')
    return (f'<div class="hinweis-zone" style="position:absolute;left:{64 / 1344 * 100:.2f}%;right:{(104 + 200) / 1344 * 100:.2f}%;'
            f'top:{604 / 760 * 100:.2f}%;height:{120 / 760 * 100:.2f}%">{tip}</div>')


def _vorzeichen(x, stellen=1):
    """+1,2 / −1,2 / ±0,0 (10.11.2026: nicht „−0,0“ bei einem Wert, der auf null rundet)."""
    if round(abs(x), stellen) == 0:
        return "±" + zahl(0, stellen)
    return f'{"+" if x >= 0 else "−"}{zahl(abs(x), stellen)}'


def _balken(werte, titel):
    """Kleine Balkenreihe für Wachstumsraten (je Quartal zum Vorjahr)."""
    if not werte:
        return f'<div style="color:{TEXT_3};font-size:14px">{t(titel)}: keine Daten</div>'
    hoechst = max(abs(w) for _, w in werte) or 1
    besch = len(werte) >= 2 and all(b > a for (_, a), (_, b) in zip(werte, werte[1:]))
    spalten = "".join(
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1">'
        f'<span style="font-size:14px;font-family:IBM Plex Mono,monospace">{_vorzeichen(w, 0)} %</span>'
        f'<div style="height:70px;display:flex;align-items:flex-end;width:100%;justify-content:center">'
        f'<div style="width:60%;height:{max(4, 70 * abs(w) / hoechst):.0f}px;border-radius:4px;'
        f'background:{GRUEN if w >= 0 else ROT}"></div></div>'
        f'<span style="font-size:12px;color:{TEXT_3}">{t(q)}</span></div>' for q, w in werte)
    zeichen = " · beschleunigt ✓" if besch else ""
    return (f'<div style="display:flex;flex-direction:column;gap:8px"><div style="font-size:14px;color:{TEXT_2}">'
            f'{t(titel)}{zeichen}</div><div style="display:flex;gap:12px">{spalten}</div></div>')


def _quartal(tag):
    return f"Q{(tag.month - 1) // 3 + 1} {tag.year % 100:02d}"


def _earnings_feld(fd):
    """Termin, letzte Zahlen und Balken (Umsatz, Gewinn je Aktie) – Inhalt der Karte „Zahlen“."""
    if not fd:
        return f'<div style="color:{TEXT_2}">Keine Gewinndaten verfügbar.</div>'
    g = fd["gewinne"]
    zeilen = []
    termin = fd.get("termin")
    if termin is not None and len(termin) and termin["datum"].iloc[0] and not pd.isna(pd.Timestamp(termin["datum"].iloc[0])):
        tag = pd.Timestamp(termin["datum"].iloc[0])
        bis = (tag.normalize() - pd.Timestamp.today().normalize()).days
        ampel = "gelb" if 0 <= bis <= 10 else "grün"
        if bis < 0:                              # Termin vorbei, der neue ist noch nicht gemeldet
            zeilen.append(ampelzeile("Nächster Termin", "grau", f"noch offen (zuletzt {tag:%d.%m.%Y})"))
        else:
            zeilen.append(ampelzeile("Nächster Termin", ampel,
                                     f'{WOCHENTAGE[tag.weekday()]} {tag:%d.%m.%Y} · in {bis} Tagen'
                                     + (" – innerhalb von 10 Tagen: Ausbruch vor Zahlen ist ein Würfelwurf"
                                        if ampel == "gelb" else "")))
    gemeldet = g.dropna(subset=["eps"])
    if len(gemeldet):                            # junge Börsengänge: noch keine gemeldeten Zahlen (TKMS.DE, 10.11.2026)
        letzte = gemeldet.iloc[-1]
        ue, sch = letzte["ueberraschung_pct"], letzte["schaetzung"]
        zeilen.append(ampelzeile("Letzte Zahlen", "grau" if ue != ue else "grün" if ue >= 0 else "rot",
                                 f'{gemeldet.index[-1]:%d.%m.%Y}: {zahl(letzte["eps"])} $ je Aktie'
                                 + (f', erwartet {zahl(sch)} $ ({_vorzeichen(ue)} %)' if sch == sch and ue == ue
                                    else ", keine Schätzung")))
    else:
        zeilen.append(ampelzeile("Letzte Zahlen", "grau", "noch keine gemeldeten Zahlen"))
    eps = fundament._wachstum(g["eps"]).dropna().iloc[-3:]
    # Gemeldet wird etwa einen Monat nach Quartalsende: das berichtete Quartal liegt davor
    eps_w = [(_quartal(i - pd.Timedelta(days=45)), float(v)) for i, v in eps.items()]
    sec = fd.get("sec")
    ums_w = []
    if sec is not None and not sec.empty:
        u = fundament._wachstum(sec["umsatz"].dropna()).dropna().iloc[-3:]
        ums_w = [(_quartal(i), float(v)) for i, v in u.items()]
    balken = (f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">'
              f'{_balken(ums_w, "Umsatzwachstum zum Vorjahr")}{_balken(eps_w, "Gewinn je Aktie zum Vorjahr")}</div>')
    return (f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:28px;'
            f'align-items:start"><div>{"".join(zeilen)}</div>{balken}</div>')


def _reaktion_zeilen(df, gewinne):
    """Die drei Ablesungen der Kursreaktion auf die letzten Zahlen (O'Neil, Kap. 8): Tag 1, Tage 2–10, Erholung."""
    r = reaktionen(df, gewinne)
    if not r:
        return None
    tag, prozent = r[-1]
    i = df.index.get_loc(tag)
    vor = float(df["Close"].iloc[i - 1])
    tag1 = float(df["Close"].iloc[i])
    danach = df.iloc[i + 1:i + 10]
    zeilen = [("Tag 1", "grün" if prozent >= 3 else "rot" if prozent <= -3 else "gelb",
               f'{tag:%d.%m.%Y}: {_vorzeichen(prozent)} %'
               + (" – Absturz um 15 % und mehr nach Zahlen ist ein großes Problem" if prozent <= -15 else ""))]
    if danach.empty:
        zeilen += [("Tage 2–10", "grau", "beginnt mit dem nächsten Handelstag"),
                   ("Erholung", "grau", "beginnt mit dem nächsten Handelstag")]
    else:
        schluss = float(danach["Close"].iloc[-1])
        tage = len(danach) + 1
        drift = (schluss / tag1 - 1) * 100
        ampel = "grün" if schluss >= tag1 else "gelb" if schluss >= vor else "rot"
        bisher = f"bisher {tage - 1} von 9 Tagen: " if tage < 10 else ""
        zeilen.append(("Tage 2–10", ampel, f'{bisher}{_vorzeichen(drift)} % seit Tag 1 – '
                       + {"grün": "die Gewinne halten", "gelb": "Gewinne teils abgegeben, aber über dem Ausgangskurs",
                          "rot": "unter den Kurs vor den Zahlen gefallen"}[ampel]))
        tief = float(danach["Low"].min())
        if tief >= vor:
            zeilen.append(("Erholung", "grün", "nie unter den Kurs vor den Zahlen gefallen"))
        elif schluss >= vor:
            zeilen.append(("Erholung", "gelb", "kurz unter den Ausgangskurs, aber zurückerobert"))
        else:
            zeilen.append(("Erholung", "rot", f'unter dem Ausgangskurs von {zahl(vor)} $ geblieben'))
    return {"tag": tag, "prozent": prozent, "vor": vor, "zeilen": zeilen}


def tv_link(tk):
    """Adresse des Titels in TradingView (mit Börse, z. B. NYSE:HWM) – für den Knopf über dem Chart."""
    return f"https://www.tradingview.com/chart/?symbol={_tv_symbol(tk)}"


ZEICHEN = {"USD": "$", "EUR": "€", "GBp": "p", "CHF": "CHF", "SEK": "kr", "DKK": "kr", "NOK": "kr"}


def waehrung_setzen(html, tk):
    """Titel außerhalb der USA (10.11.2026): Preise trugen fest „$“ – RHM.DE zeigte „1.004,80 $“ statt Euro. Ersetzt
    das Dollarzeichen hinter Zahlen durch das Zeichen der Handelswährung (depot.WAEHRUNG)."""
    import re
    import depot
    w = ZEICHEN.get(depot.waehrung(tk), "$")
    if w == "$":
        return html
    return re.sub(r"(\d)([ \u00a0])\$", lambda m_: m_.group(1) + m_.group(2) + w, html)


def chartkarte(z, ebene="Tag", ausschnitt=None, zonen_ansicht="Aktuell", gd_kurz=False, nadeln=None, avwap_wahl=None):
    """Karte mit Legende und Chart aus dem Zwischenstand von seite_titel; billig, wird bei jedem Knopfdruck neu
    gezeichnet (Zeitebene, Ausschnitt, Zonen, GD10/GD20, AVWAP-Anker), ohne die Seite neu zu rechnen. Darunter der Stundenchart."""
    m = z.get("marken")
    if nadeln:                                    # Konferenzraum: Hinweise der Strategen als Nadeln
        m = dict(m or {}, nadeln=nadeln)
    st_ = stunden(z.get("stunde"), m, bool(z["df"].attrs.get("laufend"))) if ebene == "Tag" else ""
    return waehrung_setzen(seite(karte(f'<details><summary style="cursor:pointer;color:{TEXT_2};font-size:14px">Legende</summary>'
                       f'<div style="display:flex;flex-wrap:wrap;gap:20px;margin-top:10px">{legende(ebene, gd_kurz)}</div>'
                       '</details>'
                       + f'<div style="position:relative">{chart(z["df"], ebene, z["index"], ausschnitt, z.get("sek"), z.get("etf", ""), z.get("zonen"), zonen_ansicht, gd_kurz, m, avwap_wahl)}'
                       f'{z.get("rs_lesart", "")}</div>' + st_), oben=0, unten=0), z["df"].attrs.get("ticker", ""))


ATR_STOPP = 1.5                                  # Stopp 1,5 ATR vom Einstieg, eine Linie für alle Systeme (Micky, 09.11.2026)


def _rueckenwind(tk):
    """Eintrag des Titels im Rückenwind-Stand des Nachtlaufs (Stufe, Tempo, Geld) oder None; je Stand einmal gelesen."""
    import rueckenwind
    try:
        pfad = rueckenwind._pfad("stand.json")
        schluessel = (pfad, os.path.getmtime(pfad))
    except OSError:
        return None
    if _RW_CACHE.get("k") != schluessel:
        _RW_CACHE.update(k=schluessel, titel=((rueckenwind.laden() or {}).get("titel") or {}))
    return _RW_CACHE["titel"].get(tk.upper())


_RW_CACHE = {}


def _zahlenkarte(tk, fund, fd):
    """Karte „Zahlen“ (09.11.2026): die neun Punkte wie in Rückenwind (eine Zahlen-Ampel für die ganze App), darunter
    die Zeichen der Gewinnqualität und S · Angebot (CAN SLIM S, nicht in den neun)."""
    import rueckenwind
    try:
        z = rueckenwind._zahlen(tk, rueckenwind._tv())
    except Exception:  # noqa: BLE001
        z = None
    if z and z.get("punkte"):
        a_ = z.get("ampel", "grau")
        kopf = (f'<div style="font-size:15px;font-weight:600;padding-bottom:4px">'
                f'{ {"grün": "🟢", "gelb": "🟡", "rot": "🔴"}.get(a_, "⚪") } Zahlen-Ampel {a_} · neun Punkte wie in Rückenwind</div>')
        links = kopf + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));column-gap:28px">' \
            + "".join(ampelzeile(n, a, x) for n, (a, x) in z["punkte"].items())
    else:
        links = f'<div style="color:{TEXT_2}">Fundamentdaten nicht verfügbar.</div>'
    if fund and fund["zeichen"]:
        links += "".join(ampelzeile(x, "gelb" if "prüfen" in x else "blau", "") for x in fund["zeichen"])
    s_ = fundament.angebot(sic13._tv(tk))
    links += ampelzeile("S · Angebot (frei handelbare Aktien, Rückkäufe)", s_[0], s_[1],
                        "CAN SLIM S: Weniger Aktien im Umlauf und Rückkäufe verknappen das Angebot; Verwässerung über 2 % "
                        "ist ein Warnzeichen. Quelle TradingView. Zählt nicht zu den neun Punkten.")
    return links + ("</div>" if '<div style="display:grid' in links else "")


def _zahlen_gesamt(tk, fund, fd):
    """Eine Karte „Zahlen“ (10.11.2026, vorher Earnings und Zahlen nebeneinander mit denselben Quartalszahlen): links
    Termin, letzte Zahlen und die Balken als Bild, rechts die neun Punkte mit der Zahlen-Ampel, Gewinnqualität und S."""
    return karte(f'<div>{_earnings_feld(fd)}</div><div>{_zahlenkarte(tk, fund, fd)}</div>', "Zahlen")


def _chartmarken(tk, df, m_, k_, zonen, gewinne, fd, rw=None):
    """Was der Chart über die Zonen hinaus einzeichnet: Einstieg (Pivot) mit Kaufzone bis +5 % und Stopp 1,5 ATR,
    Ausbruchstag, Anker des AVWAP (Beginn der Zone), Earnings mit Reaktion und nächstem Termin, RS-Rang und Tempo aus
    Rückenwind, Short (Ermüdung) mit Stopp 1,5 ATR über der Unterkante. Einstieg: Minervinis Pivot aus der Enge, sonst
    der Pivot des Ausbruchs, sonst Kullamägis Breakout bzw. Episodic Pivot."""
    import atr as atr_modul
    a = atr_modul.wert(df)
    jetzt = (zonen or {}).get("jetzt") or {}
    br = m_.get("ausbruch") or None
    ep = k_.get("ep") or {}
    kontr = ((zonen or {}).get("enge") or {}).get("kontraktionen") or []
    enge_ab = kontr[-1]["hoch_t"] if kontr else None           # Kaufzone und Stopp ab der Enge, nicht über die ganze Base
    import depot
    e, quelle = depot.einstieg_long(m_, k_)          # derselbe Einstieg wie Kartentisch, Plan und Stab
    m = {"einstieg": float(e) if e else None, "quelle": quelle, "atr": a,
         "kz_oben": float(e) * 1.05 if e else None,
         "stopp": float(e) - ATR_STOPP * a if e and a else None,
         "ab": (br or {}).get("erster_tag") or (ep.get("tag") if quelle == "Episodic Pivot" else None) or enge_ab,
         "avwap_ab": jetzt.get("start_t") if jetzt.get("zone") or jetzt.get("offen") else None,
         "ausbruch": {"tag": br["tag"], "volumen": br.get("volumen"), "fehl_tag": br.get("fehl_tag")} if br else None,
         "earnings": reaktionen(df, gewinne) if gewinne is not None else [], "termin": None, "rs": None, "short": None}
    try:
        termin = (fd or {}).get("termin")
        if termin is not None and len(termin) and termin["datum"].iloc[0]:
            t_ = pd.Timestamp(termin["datum"].iloc[0])
            m["termin"] = None if pd.isna(t_) else t_     # 10.11.2026: unbekannter Termin (NaT) ließ den Chart abstürzen
    except Exception:  # noqa: BLE001
        pass
    m["rs"] = rw
    em = k_.get("ermuedung")
    if em and a:
        m["short"] = {"tag": em["tag"], "einstieg": float(em["unten"]), "stopp": float(em["unten"]) + ATR_STOPP * a,
                      "volumen": em.get("volumen")}
    return m


def _stundenkerzen(tk, df):
    """Stundenkerzen der letzten 10 Handelstage aus den 30-Minuten-Kerzen (tpo_daten, auf die Tageskurse ausgerichtet),
    beim laufenden Börsentag mit den heutigen Kerzen von Yahoo. None ohne Daten."""
    try:
        d30 = tpo_daten.kerzen(tk, df.iloc[:-1] if df.attrs.get("laufend") else df, abruf=False)
        if df.attrs.get("laufend"):
            heute = tpo_daten.heute(tk)
            if heute is not None:
                d30 = pd.concat([d30, heute]) if d30 is not None else heute
        if d30 is None or d30.empty:
            return None
        d30 = d30[~d30.index.duplicated(keep="last")].sort_index()
        h1 = d30.resample("60min", offset="30min").agg({"Open": "first", "High": "max", "Low": "min",
                                                       "Close": "last", "Volume": "sum"}).dropna()
        tage = sorted(set(h1.index.date))[-10:]
        return h1[pd.Index(h1.index.date).isin(tage)]
    except Exception:  # noqa: BLE001 – ohne Stundenkerzen kein Stundenchart
        return None


def _eintrag(tk):
    """Eintrag des Titels im jüngsten Kartentisch – bestimmt den Rahmen (long grün, short rot, offen gelb)."""
    try:
        import kartentisch
        return kartentisch.eintrag_von(tk) or {}
    except Exception:  # noqa: BLE001
        return None


# ── Abgelegte Titelseiten (05.11.2026): der Abendlauf baut für jeden Titel des Kartentischs ohnehin die volle
# Titelseite (Stufe 2) – sie wird gespeichert, damit „Deep Dive“ sie sofort zeigt statt sie neu zu rechnen (Kurse,
# 30-Minuten-Kerzen, Zahlen aus dem Netz). Gültig, solange danach weder Programm noch Depot geändert wurden;
# „Kurse aktualisieren“ rechnet wie bisher neu.
ABLAGE = os.path.join(HIER, "..", "daten", "titelseiten")


def codezeit():
    """Jüngste Änderungszeit der Programmdateien (kern, oberflaeche)."""
    return max(os.path.getmtime(os.path.join(HIER, "..", d, f)) for d in ("kern", "oberflaeche")
               for f in os.listdir(os.path.join(HIER, "..", d)) if f.endswith(".py"))


def ablegen(tk, teile):
    import gzip
    import pickle
    os.makedirs(ABLAGE, exist_ok=True)
    pfad = os.path.join(ABLAGE, f"{tk.upper()}.pkl.gz")
    tmp = f"{pfad}.{os.getpid()}.neu"           # App und Hintergrundlauf können gleichzeitig ablegen
    with gzip.open(tmp, "wb", compresslevel=3) as f:
        pickle.dump(teile, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, pfad)


ALTER_MAX = 30 * 3600            # abgelegte Seiten gelten höchstens 30 Stunden (der Nachtlauf baut sie täglich neu)


def ablage_grenze():
    """Abgelegte Titelseiten älter als das Programm oder das Depot gelten als veraltet."""
    import depot
    return max([codezeit()] + ([os.path.getmtime(depot.DATEI)] if os.path.exists(depot.DATEI) else []))


def frisch(tk, grenze=None):
    """Liegt eine gültige Titelseite im Schrank (jünger als Programm, Depot und 30 Stunden)?"""
    try:
        zeit = os.path.getmtime(os.path.join(ABLAGE, f"{tk.upper()}.pkl.gz"))
    except OSError:
        return False
    return zeit >= (grenze or ablage_grenze()) and time.time() - zeit < ALTER_MAX


def abgelegt(tk):
    """Gespeicherte Titelseite als (Teile, veraltet) oder None. Veraltet = vor der letzten Programmänderung gebaut:
    wird trotzdem sofort gezeigt (die Daten sind dieselben), die neue Fassung baut nachtlauf.py --seiten im
    Hintergrund (09.11.2026 – vorher wurde nach jeder Änderung live gerechnet). Nicht gezeigt wird eine Seite, die
    älter als 30 Stunden oder älter als das Depot ist (Positionen und Stückzahl müssen stimmen)."""
    import depot
    import gzip
    import pickle
    pfad = os.path.join(ABLAGE, f"{tk.upper()}.pkl.gz")
    try:
        zeit = os.path.getmtime(pfad)
        if time.time() - zeit >= ALTER_MAX or (os.path.exists(depot.DATEI) and zeit < os.path.getmtime(depot.DATEI)):
            return None
        with gzip.open(pfad, "rb") as f:
            return pickle.load(f), zeit < codezeit()
    except Exception:  # noqa: BLE001 – dann wird gerechnet
        return None

_SPEICHER = {}


def maerkte():
    """Markt je System (Minervini, Kullamägi), einmal je Stunde gerechnet; Hochs/Tiefs aus dem letzten Kartentisch."""
    schluessel = pd.Timestamp.now().strftime("%Y%m%d%H")
    if _SPEICHER.get("markt", (None,))[0] != schluessel:
        try:
            import kartentisch
            b = (kartentisch.laden() or {}).get("barometer") or {}
            mm = markt_systeme.minervini(b.get("hochs"), b.get("tiefs"))
        except Exception:  # noqa: BLE001
            mm = None
        try:
            km = markt_systeme.kullamaegi()
        except Exception:  # noqa: BLE001
            km = None
        _SPEICHER["markt"] = (schluessel, mm, km)
    return _SPEICHER["markt"][1], _SPEICHER["markt"][2]


def seite_titel(ticker, laufend=False, _stand=None):
    """Gibt drei Teile zurück: oben (Kopf bis Kacheln), chart (Zwischenstand für chartkarte), unten (ab Frühere Basen).
    Zwischen oben und Chart setzt app.py die Chart-Knöpfe. laufend=True: mit der unvollständigen Kerze des laufenden Börsentags (Knopf „Kurse aktualisieren“);
    _stand macht jeden Druck auf den Knopf zu einem eigenen Seitenspeicher-Eintrag."""
    tk = ticker.upper().strip()
    df = daten.kurse(tk, laufend=laufend)
    try:
        index = daten.kurse(daten.INDEX)
    except Exception:
        index = None
    sb = daten.steckbrief(tk)
    df.attrs["jung"] = len(df) < 300
    df.attrs["ticker"] = tk                      # für die Gegenprobe der Kurse (Massive)
    try:                                         # 30-Minuten-Kerzen holen bzw. fortsetzen (Wertzonen)
        tpo_daten.merken(tk)                     # geöffnet: gehört ab jetzt zum Abendlauf
        tpo_daten.kerzen(tk, df.iloc[:-1] if df.attrs.get("laufend") else df, abruf=True)
    except Exception:  # noqa: BLE001 – ohne Netz bleibt der Speicher
        pass
    erkennung.mp_vergessen(tk)
    if df.attrs.get("laufend"):                  # Knopf „Kurse aktualisieren“ während der Börse: heutige Kerzen dazu
        try:
            erkennung.mp_heute(tk, tpo_daten.heute(tk))
        except Exception:  # noqa: BLE001
            pass
    erk = erkennung.erkenne(df, index=index)
    erk["kurs"] = float(df["Close"].iloc[-1])
    try:                                          # ein Stopp für Plan, Lagekarte und Stückzahl: 1,5 ATR (depot.plan)
        import atr as atr_modul
        erk["atr"] = atr_modul.wert(df)
    except Exception:  # noqa: BLE001
        erk["atr"] = None
    erk["df_index"] = df.index
    try:                                          # Volumenprofil der letzten 52 Wochen für die Spalte rechts im Chart
        import volumenprofil
        i_vp = max(0, len(df) - volumenprofil.JAHR)
        p_vp = volumenprofil.profil(df, i_vp)
        erk["profil"] = dict(p_vp, anker=i_vp, anker_art="52 Wochen", knoten=volumenprofil.knoten(p_vp)) if p_vp else None
    except Exception:  # noqa: BLE001
        erk["profil"] = None
    try:
        erk["rs_rang"] = rs_rang.rang(tk)
    except Exception:  # noqa: BLE001 – ohne Massive-Dateien bleibt das Glied leer
        erk["rs_rang"] = None
    ph_reihe = phasen_modul.phasen(df) if len(df) >= 300 else None
    ph = int(ph_reihe.iloc[-1]) if ph_reihe is not None else None
    krit = phasen_modul.phase_heute(df) if len(df) >= 300 else None
    try:
        fd = quellen.laden(tk)
        fund = fundament.ampeln(fd)
        gewinne = fd["gewinne"]
    except Exception:
        fd, fund, gewinne = None, None, None
    try:
        mr = marktrichtung.richtung()
    except Exception:
        mr = None
    etf = sektoren.sektor_von(sb.get("sektor", ""))
    try:                                          # Sektor-ETF für die RS-Linie gegen den Sektor
        sek = marktdaten.yahoo(etf) if etf else None
    except Exception:  # noqa: BLE001
        sek = None
    rd = rudelkarte.daten(tk, df, etf)
    hinweis_laufend = ""
    if df.attrs.get("laufend"):
        hinweis_laufend = (f'<div style="border:1px solid #5A4A1A;background:#2A2410;color:#E3B341;border-radius:10px;'
                           f'padding:10px 14px;font-size:14px">Laufender Börsentag, Stand {df.attrs["stand"]} Uhr: Die letzte '
                           f'Kerze ist unvollständig (im Chart hohl). Ausbruch, Volumenfaktoren und Enge '
                           f'sind vorläufig bis Börsenschluss – O\'Neil und Minervini urteilen über Schlusskurs und '
                           f'Tagesvolumen.</div>')
    gtage = [d for d, _ in reaktionen(df, gewinne)] if gewinne is not None else []
    try:                                         # VCP-Scanner: Zone und Enge jetzt, abgeschlossene Zonen (Chart, Minervini)
        import vcp_zone
        zonen = vcp_zone.alles(df)
    except Exception:  # noqa: BLE001 – Chart ohne Zonen, Minervini rechnet selbst
        zonen = None
    scan = (zonen["jetzt"], zonen["enge"]) if zonen else None          # die Zone von heute (für beide Systeme)
    m_ = system_minervini.pruefen(df, erk, (erk.get("rs_rang") or (None,))[0], fund, scan)
    if zonen and m_.get("ausbruch"):               # frischer Ausbruch: der Chart zeigt die Zone vom Vortag weiter
        zonen["jetzt"] = vcp_zone.datiert(df, m_["ausbruch"]["zone"])
    if zonen and (m_["zone"].get("in_zone") or m_.get("ausbruch")):   # der Chart zeigt Minervinis Enge
        bis = m_["ausbruch"]["vortag_i"] if m_.get("ausbruch") else len(df)   # Enge bis zum Vortag des Ausbruchs
        zonen["enge"] = vcp_zone.enge_datiert(df.iloc[:bis], m_["zone"])
    k_ = system_kullamaegi.pruefen(df, erk, gtage, ticker=tk, scan=scan)
    reif = next(ok for n, ok, _ in m_["regeln"] if n.startswith("Reife Base"))
    erk["scanner_zone"] = m_["zone"] if m_["zone"].get("zone") else None   # Frühwarnung: Unterkante der Zone
    erk["fruehwarnung"] = fruehwarnung.zeichen(df, erk, ph)
    try:                                         # IBD-Basenzählung auf den Scanner-Zonen (Kachel Base, Nummern im Chart)
        import basen
        erk["basen"] = basen.zaehlen(df, index, (zonen or {}).get("verlauf"), m_["zone"] if reif else None)
        if reif:
            erk["basen"]["markt"] = basen.markt_rueckgang(index, df.index[m_["zone"]["start_i"]])
    except Exception:  # noqa: BLE001 – Kachel ohne Zählung
        erk["basen"] = None
    erk["gruppe_korrektur"] = _gruppe_korrektur(df, m_["zone"] if reif else None, (erk.get("basen") or {}).get("markt"), rd)
    mm_, km_ = maerkte()
    erk["systeme"] = {"m": m_, "k": k_}
    gestaltung.MITSCHRIFT = {}                  # die Lagekarte liest die Ampeln der Kacheln mit
    try:
        rw = _rueckenwind(tk)
        leiste = _kacheln(erk, ph, ph_reihe, fund, df, rd, fd if fund else None, mr, gewinne, m_, k_, mm_, km_, rw)
        k_info = dict(gestaltung.MITSCHRIFT)
    finally:
        gestaltung.MITSCHRIFT = None
    lk = lagekarte.karte(tk, namen_de.BRANCHE.get(sb.get("branche"), sb.get("branche")) or "", erk, k_info, df)
    marken = _chartmarken(tk, df, m_, k_, zonen, gewinne, fd if fund else None, rw)
    stellung = _stellung(df, marken)
    oben = [_kopf(tk, sb, df, fd, mit_rueckgang=not reif) + _lagezeile(tk, rw, stellung) + hinweis_laufend, leiste]
    zwischen = {"df": df, "erk": erk, "ph_reihe": ph_reihe, "index": index, "gewinne": gewinne, "sek": sek,
                "etf": etf or "", "rs_lesart": _rs_lesart(df, index, sek, etf)}
    if zonen and (erk.get("basen") or {}).get("zahl") and zonen.get("jetzt"):
        zonen["jetzt"] = dict(zonen["jetzt"], nummer=erk["basen"]["zahl"])     # Basennummer an der Zone von heute
    zwischen["zonen"] = zonen
    zwischen["marken"] = marken
    zwischen["stunde"] = _stundenkerzen(tk, df)
    teile = [_zahlen_gesamt(tk, fund, fd if fund else None)]        # Earnings und Zahlen in einer Karte (10.11.2026)
    teile.append(_warnzeichen(erk, krit, stellung))
    plan, rand = _plan(m_, k_, mm_, km_, df, marken, fund)
    teile.append(karte(plan, "Plan", rand=rand))
    teile.append(depotleiste.titelkarte(tk, df, erk))
    return {"oben": waehrung_setzen(seite("".join(oben), unten=8), tk), "chart": zwischen,
            "unten": waehrung_setzen(seite("".join(teile), oben=8), tk),
            "lagekarte": waehrung_setzen(lk, tk), "kacheln": k_info}
