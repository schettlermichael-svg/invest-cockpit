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
import depotleiste                                    # noqa: E402
import rs_rang                                        # noqa: E402
import phase as phasen_modul                          # noqa: E402
import namen_de                                       # noqa: E402
import marktdaten                                     # noqa: E402
import rudelkarte                                     # noqa: E402
import quellen                                        # noqa: E402
import sektoren                                       # noqa: E402
import tv_kennzahlen                                  # noqa: E402
import lagekarte                                      # noqa: E402
import marktklima                                     # noqa: E402
import system_minervini                               # noqa: E402
import system_kullamaegi                              # noqa: E402
import fuehrer_rang                                   # noqa: E402
import gestaltung                                     # noqa: E402
from chart import chart, legende, reaktionen, stunden  # noqa: E402
from gestaltung import (BLAU, GELB, GRUEN, KARTE, RAND, ROT, TEXT_2, TEXT_3, ampelzeile, kachel, kachel2, karte,  # noqa: E402
                        seite, t, zahl)

from zeichen import PHASE_NAME as PHASENTEXT   # noqa: E402  Basis · Aufwärts · Verteilung · Abwärts – ein Name je Phase in der App
def _tv_symbol(tk):
    """BÖRSE:TICKER für TradingView aus daten/tv/revier.csv; ohne Eintrag nur der Ticker (TradingView sucht dann)."""
    import watchlists
    if watchlists.zu_tv(tk):                     # Börse außerhalb der USA (z. B. RHM.DE → XETR:RHM)
        return watchlists.zu_tv(tk)
    z = tv_kennzahlen.zeile(tk.upper())
    ex = z["exchange"] if z is not None and isinstance(z.get("exchange"), str) else None
    sym = tk.upper().replace("-", ".")
    return f"{ex}:{sym}" if ex else sym


def _termin(fd):
    """„ · Zahlen am Di 12.11. (in 7 Tagen)“ – Farbe nach gestaltung.termin_ampel (bis 7 Tage rot, bis 14 gelb)."""
    termin = (fd or {}).get("termin")
    if termin is None or not len(termin) or not termin["datum"].iloc[0]:
        return ""
    tag = pd.Timestamp(termin["datum"].iloc[0])
    if pd.isna(tag):
        return ""
    bis = (tag.normalize() - pd.Timestamp.today().normalize()).days
    if bis < 0:
        return ""
    farbe = {"rot": ROT, "gelb": GELB}.get(gestaltung.termin_ampel(bis), TEXT_2)
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
             "(führend oder erstarkend) und keine schwächelnd; gelb = eine vorne, oder zwei vorne und eine schwächelnd; rot = "
             "keine vorne. Beim Short gespiegelt: Abfluss ist Rückenwind. Stand des Nachtlaufs.")
    if not x:
        return kachel("Geld", "grau", "–", "erst nach dem nächsten Nachtlauf", hilfe)
    wort = {"Führend": "führend", "Erstarkend": "erstarkend", "Ermüdend": "schwächelnd", "Abgehängt": "zurückfallend"}
    zeile = " · ".join(f"{art} {wort.get(x.get(f'{k}_feld'), '–')}"
                       for art, k in (("Sektor", "sektor"), ("Branche", "branche"), ("Thema", "thema")))
    hilfe += (f"\n\nSektor: {x.get('sektor') or '–'} · Branche: {namen_de.branche(x.get('branche') or '') or '–'}"
              + (f" · Thema: {x['thema'].split(' · ')[0]}" if x.get("thema") else ""))
    ampel, wort_ = x["geld_ampel"], {"grün": "Rückenwind", "gelb": "halb", "rot": "Gegenwind"}[x["geld_ampel"]]
    if gestaltung.SYSTEM_SHORT:                     # Short: Abfluss ist Rückenwind (Prüf-Agent 12.11.2026 – wie die
        ampel = gestaltung._GEGEN.get(ampel, ampel)  # feste Ampel beim Stab; vorher zeigte die Kachel long)
        wort_ = {"grün": "Rückenwind (Abfluss)", "gelb": "halb", "rot": "Gegenwind (Zufluss)"}[ampel]
        zeile = "für Short gespiegelt · " + zeile
    return kachel("Geld", ampel, wort_, zeile, hilfe)


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
    amp = gestaltung.termin_ampel(bis)
    nah = amp in ("rot", "gelb")
    return kachel("Nächste Zahlen", amp,
                  "heute" if bis == 0 else "morgen" if bis == 1 else f"in {bis} Tagen",
                  f"{WOCHENTAGE[tag.weekday()]} {tag:%d.%m.%Y}" + (" · Ausbruch davor riskant" if nah else _zuletzt(fund)),
                  gestaltung.TERMIN_TEXT)


def _zuletzt(fund):
    a_, txt = (fund or {}).get("punkte", {}).get("Überraschung", ("grau", ""))
    if a_ == "grau":
        return ""
    x = txt.split(" / ")[-1]
    return f" · zuletzt {x} {'über' if not x.startswith('−') else 'unter'} Erwartung"


def _k2_markt(mm):
    """Markt: eine Ampel nach O'Neil (12.11.2026); beim Short gespiegelt (gestaltung.kachel2)."""
    m = (mm["ampel"], mm["wort"]) if mm else ("grau", "–")
    zeile = f"O'Neil seit {mm['seit']}" if mm else ""
    return kachel2("Markt", m, None, zeile,
                   (mm["regel"] + "\n\nHeute: " + mm["text"] + ("\n\nZeichen ohne Urteil: " + mm["zeichen"]
                                                               if mm["zeichen"] else "")) if mm else "keine Daten")


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
                   "Base-Ausbruch – Minervinis Trendvorlage, sieben Punkte zu Kurs und Durchschnitten (der achte, RS ab 70, steht in "
                   "der Kachel „Stärke“). Sie entspricht Phase 2 (Aufwärts) nach Weinstein: "
                   + "; ".join(f"{n_} {'✓' if ok else '✗'}" for n_, ok in tv.items())
                   + "\n\nFlagge · Momentum · Sprung · Zahlen-Reaktion – Kullamägi nutzt keine Trendvorlage; seine Auswahl ist die Stärke (Kachel „Stärke“)."
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
                   "Base-Ausbruch – RS-Rang 1–99 wie das RS-Rating von IBD (12 Monate, jüngstes Quartal doppelt), verglichen mit "
                   "unserem Revier. Minervini verlangt mindestens 70 – der achte Punkt der Trendvorlage. Die Zahl ist "
                   "kein Listenplatz: 16 heißt, nur 16 % der Titel liefen schwächer.\n\nFlagge · Momentum · Sprung · Zahlen-Reaktion – Kullamägi sucht die ein bis "
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
    kk = ((("grün", "Zahlen am Sprungtag" if ep["regeln"][2][2].startswith("Zahlen") else
             "ohne Zahlen, 5-fach Volumen, Schluss oben") if ep["regeln"][2][1] else ("gelb", "Nachricht prüfen"))
          if ep else None)
    ev = _ereignis(df, gewinne, fund) if (df is not None and fund) else None
    zeile = z[2] + (f" · {ev[1]}" if ev and ev[0] != "grau" else "")
    gruen = sum(1 for a, _ in fund["punkte"].values() if a == "grün") if fund else 0
    return kachel2("Fundament", mm, kk, zeile,
                   "Base-Ausbruch – Minervini kauft Führer mit wachsenden Zahlen: Quartalsgewinn und Umsatz zum Vorjahr nicht rot "
                   f"(grün ab 25 %). Alle sieben Prüfpunkte: {gruen} von 7 grün (Liste weiter unten). "
                   + (_widerspruch(ph) or "")
                   + "\n\nFlagge · Momentum · Sprung · Zahlen-Reaktion – Beim Breakout schaut Kullamägi nicht auf die Zahlen (rein technisch). Beim Episodic Pivot "
                     "braucht er eine Nachricht, die den Markt zur Neubewertung zwingt – oft überraschend starke Zahlen."
                   + (f"\n\nReaktion auf die letzten Zahlen (Zeichen, O'Neil): {ev[1]} – {ev[2]}\n{ev[3]}" if ev else ""))


def _k2_setup(m, k, erk, df):
    mm = (m["ampel"], m["setup"] if m["setup"] != "keines" else "keines")
    em = system_kullamaegi.short_von(k)
    h = k.get("haupt")
    if em and (not h or h["ampel"] == "rot"):
        kk = (em["ampel"], em["art"] + " (short)" + (f" vor {em['tage_her']} T." if em["tage_her"] else ""))
    else:
        kk = ((h["ampel"], h["art"] + (f" vor {h['tage_her']} T." if h["art"] == "Episodic Pivot" and h["tage_her"] else ""))
              if h and h["ampel"] != "rot" else ("rot", "keines"))
    teile = ([f"Pivot {zahl(m['pivot'])} $ · {m['lage']}"] if m.get("pivot")     # Base und Tiefe stehen in „Base“
             else [next(x for n, _, x in m["regeln"] if n.startswith("Reife Base"))])
    hilfe = ("Base-Ausbruch – " + system_minervini.kurz(m) + "\n" + "\n".join(f"{'✓' if ok else '✗'} {n} – {x}" for n, ok, x in m["regeln"])
             + "\n\nFlagge · Momentum · Sprung · Zahlen-Reaktion – " + "\n".join(
                 f"{x['art']} ({x['ampel']}):\n" + "\n".join(f"{'✓' if ok else '✗'} {n} – {y}" for n, ok, y in x["regeln"])
                 for x in (k.get("ep"), k.get("breakout"), em) if x))
    su = erk.get("setup_info")
    if gestaltung.SYSTEM and su is not None:         # ein eigenes System: das eine Setup mit seinem Namen
        import kartentisch
        r_ = su.get("reihe")
        name = kartentisch.NAME.get(r_, "kein Setup")
        ampel = ("grün" if su.get("gruen") else "grau" if r_ == "vcp" else "gelb") if r_ else "rot"
        zeile_ = [su["scanner"]] if su.get("scanner") else (teile if r_ in ("m_spitze", "m_weitere") else [])
        if su.get("ausbruch") and r_ not in ("m_spitze", "m_weitere"):
            zeile_.append(su["ausbruch"])
        if su.get("luecken") and not su.get("gruen"):
            zeile_.append("Es fehlt: " + "; ".join(su["luecken"]))
        if su.get("auch"):
            zeile_.append("Auch: " + ", ".join(su["auch"]))
        return kachel("Setup", ampel, name, " · ".join(x for x in zeile_ if x), hilfe, ganz=True)
    f_ = fehlt(m, k)
    if f_:
        teile.append("Es fehlt: " + "; ".join(f_))
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
                   "Base-Ausbruch – Minervinis VCP (Baustein 2 des Scanners, wie im Chart): jede Kontraktion höchstens 70 % so tief "
                   "wie die vorige, die letzte höchstens 10 %, das Volumen leiser als in der ersten. Grün = mindestens "
                   "zwei schrumpfende Kontraktionen; rot = die letzte ist tiefer als die vorige.\n\n"
                   "Flagge · Momentum · Sprung · Zahlen-Reaktion – Kullamägi: kurze Konsolidierung, meist 1–3 Wochen, nach einem Schub nach oben, vorzugsweise bei "
                   "reduziertem Volumen. Gelb bis 8 Wochen.")


def _k_trend50(df, short=False):
    """Trend für Flagge, Momentum-Ausbruch, Sprung und Zahlen-Reaktion (Kullamägi): Kurs über dem GD50 (Short: darunter)."""
    c = df["Close"]
    if len(c) < 50:
        return kachel("Trend", "grau", "zu kurze Historie", "")
    g50, kurs = float(c.iloc[-50:].mean()), float(c.iloc[-1])
    ueber = kurs > g50
    ok = (not ueber) if short else ueber
    return kachel("Trend", "grün" if ok else "rot", f"Kurs {'über' if ueber else 'unter'} GD50",
                  f"GD50 {zahl(g50)} $ · {_vorzeichen((kurs / g50 - 1) * 100)} %",
                  "Momentum-Setups (Kullamägi): Kurs über dem 50-Tage-Durchschnitt, beim Short darunter. Die volle "
                  "Trendvorlage gilt nur für den Base-Ausbruch.", ganz=True)


def _k_enge_zahlen(zr):
    """Enge-Kachel der Zahlen-Reaktion: hält der Kurs Tief (Short: Hoch) und AVWAP des Reaktionstags?"""
    return kachel("Enge", "grün" if zr.get("halten") else "rot",
                  "hält den AVWAP" if zr.get("halten") else "AVWAP gebrochen",
                  f"AVWAP Zahlentag {zahl(zr['avwap'])} $" if zr.get("avwap") else "",
                  "Zahlen-Reaktion: Seit dem Reaktionstag kein Schluss unter dessen Tief und unter dem AVWAP ab diesem "
                  "Tag (Short: über dem Hoch und über dem AVWAP) – Bondes „Delayed Reaction“, Shannons Anker.", ganz=True)


def _kacheln(erk, ph, ph_reihe, fund, df, rd, fd, gewinne, m, k, mm, rw=None):
    """Die acht Kacheln der Titelseite. Seit 12.11.2026 (ein eigenes System) urteilt jede Kachel mit einer Ampel für das
    eine Setup des Titels (gestaltung.SYSTEM: aus wessen Regeln); Geld und Base als Zeichen. Fehlt ein Wert, steht ein
    grauer Punkt mit dem Grund."""
    _k_zone(erk), _k_zahlen(fd, fund)            # nur mitgeschrieben für die Lagekarte, hier nicht gezeigt
    rang = (erk.get("rs_rang") or (None, ""))[0]
    su = erk.get("setup_info") or {}
    trend = _k2_trend(m, ph, ph_reihe, df) if gestaltung.SYSTEM != "K" else _k_trend50(df, gestaltung.SYSTEM_SHORT)
    enge = (_k_enge_zahlen(su["zr"]) if su.get("reihe") == "zahlen" and su.get("zr") else _k2_enge(m, k, erk, df))
    kl = [_k2_markt(mm), trend, _k2_staerke(m, k, rang, rw),
          _k2_fundament(m, k, fund, ph, df, gewinne), _k2_setup(m, k, erk, df), enge,
          _k_geld(rw), _k_base(erk)]
    return (f'<section aria-label="Lage in fünf Sekunden" style="display:grid;'
            f'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">{"".join(kl)}</section>')


def fehlt(m, k):
    """Was dem Setup fehlt, für die Setup-Kachel (12.11.2026, vorher in der Karte „Plan“): die Regeln, die nicht erfüllt
    sind – Minervini, wenn genau eine fehlt; Kullamägi und Ermüdung, wenn ihr Setup gelb ist."""
    aus = []
    if m.get("ampel") == "gelb":
        aus += [f"M {n}" for n, ok, _ in m["regeln"] if not ok]
    for x in ((k.get("haupt") or {}), (system_kullamaegi.short_von(k) or {})):
        if x.get("ampel") == "gelb":
            aus += [f"K {n}" for n, ok, _ in x.get("regeln", []) if not ok]
    return aus


def planzeile(m, k, df, marken=None, zr=None, su=None):
    """Plan in Zeilen unter dem Chart: zuerst DAS Setup des Titels – Einstieg aus depot.einstieg_setup, dieselbe Linie
    wie Chart, Kartentisch und Auswahl (Prüf-Agent 12.11.2026: vorher nahm die erste Zeile bei Sprung + Momentum-Ausbruch
    den Pivot des Momentum-Ausbruchs, und die Short-Zeile fehlte bei gelbem Breakout) –, darunter „Auch · …“ die
    übrigen Setups mit dem Stopp IHRES Einstiegs; ohne Pivot die Marken zur Trendvorlage."""
    import depot as depot_
    import kartentisch
    marken = marken or {}
    a = marken.get("atr")
    c, h, l = df["Close"], df["High"], df["Low"]
    kurs = float(c.iloc[-1])
    su = su or {}
    r_ = su.get("reihe")
    em = system_kullamaegi.short_von(k, r_) if r_ in system_kullamaegi.SHORTS else system_kullamaegi.short_von(k)

    def st(e, short=False):
        return f" · Stopp {zahl(e + ATR_STOPP * a if short else e - ATR_STOPP * a)} $ (1,5 ATR)" if a and e else ""

    def zone(e, short=False):
        return (f" · Short-Zone bis {zahl(e * 0.95)} $" if short else f" · Kaufzone bis {zahl(e * 1.05)} $") if e else ""

    zeilen = []
    seite, e, quelle = depot_.einstieg_setup(su, m, k, zr, kurs)
    if r_ and e:                                         # das aktive Setup
        kurz_ = seite == "short"
        import re as re_
        k_aus = re_.sub(r"^Stopp am Tagestief des Einstiegstags \([^)]*\)\. ", "", str(k.get("ausstieg", "")))   # der Stopp
        if r_ == "zahlen":
            regel = (f" · gescheitert bei Schluss {'über dem Hoch' if kurz_ else 'unter dem Tief'} des Reaktionstags "
                     f"{zahl((zr or {}).get('hoch') if kurz_ else (zr or {}).get('tief'))} $ oder "
                     f"{'über' if kurz_ else 'unter'} dem AVWAP")
        elif r_ in ("k_ermuedung", "k_baerenflagge", "k_bruch"):
            regel = (f" · Setup erlischt bei Kurs über dem Hoch des Auslösetags {zahl(em['stopp'])} $"
                     if (em or {}).get("stopp") else "")
        elif r_ in ("k_ep", "k_breakout", "flagge"):
            regel = f" · Ausstieg: {k_aus}" if k_aus else ""
        else:
            regel = " · Ausstieg: " + str(m.get("ausstieg", "")).replace(
                "Stopp unter dem Tief der letzten Kontraktion, höchstens 8 % unter dem Pivot. ", "")
        name = kartentisch.NAME.get(r_, r_).replace(" ★", "")
        if r_ == "zahlen":
            name += f" ({seite})"
        zeilen.append((name, f"Einstieg {zahl(e)} $ ({quelle})" + zone(e, kurz_) + st(e, kurz_) + regel))
    # übrige Setups, die der Titel zeigt („Auch“)
    if em and em.get("ampel") in ("grün", "gelb") and r_ not in ("k_ermuedung", "k_baerenflagge", "k_bruch"):
        zeilen.append((f"Auch · Short ({em['art']})", f"Einstieg unter der Unterkante {zahl(em['unten'])} $"
                       + st(em["unten"], True)))
    if m.get("pivot") and r_ not in ("m_spitze", "m_weitere"):
        zeilen.append(("Auch · Base-Ausbruch", f"Pivot der Base {zahl(m['pivot'])} $" + zone(m["pivot"]) + st(m["pivot"])))
    elif not m.get("pivot") and len(c) >= 260 and r_ not in ("m_spitze", "m_weitere"):
        g50, g150, g200 = (float(c.iloc[-n:].mean()) for n in (50, 150, 200))
        tief52, hoch52 = float(l.iloc[-252:].min()), float(h.iloc[-252:].max())
        marken_ = [(p_, x) for p_, x, f in ((max(g150, g200), "GD150/200", kurs < max(g150, g200)),
                                            (1.30 * tief52, "+30 % über dem Tief", kurs < 1.30 * tief52),
                                            (0.75 * hoch52, "−25 % unter dem Hoch", kurs < 0.75 * hoch52),
                                            (g50, "GD50", kurs < g50)) if f]
        if marken_:
            zeilen.append(("Auch · Base-Ausbruch", "Marken zur Trendvorlage: " + " · ".join(
                f"{zahl(p_)} $ ({x})" for p_, x in sorted(marken_))))
    for art, schluessel in (("Episodic Pivot", "k_ep"), (None, "k_breakout")):
        x_ = k.get("ep") if art else k.get("breakout")
        if x_ and x_.get("ampel") != "rot" and x_.get("pivot") and r_ != schluessel:
            zeilen.append(("Auch · " + kartentisch.NAME[schluessel],
                           (f"Hoch des Sprungtags {zahl(x_['pivot'])} $" if art else f"Pivot der Konsolidierung "
                            f"{zahl(x_['pivot'])} $") + st(x_["pivot"])))
    if zr and zr.get("ampel") != "rot" and zr.get("avwap") and r_ != "zahlen":
        kurz_ = zr["seite"] == "short"
        zeilen.append((f"Auch · Zahlen-Reaktion ({zr['seite']})", f"AVWAP vom Zahlentag {zahl(zr['avwap'])} $"
                       + st(zr["avwap"], kurz_)))
    if not zeilen:
        return ""
    return ('<div style="display:flex;flex-direction:column;gap:6px;margin-top:10px;padding-top:10px;'
            f'border-top:1px solid {RAND}">'
            + "".join(f'<div style="font-size:14px;line-height:1.5"><b>{t(n)}</b> '
                      f'<span style="color:{TEXT_2}">{t(x)}</span></div>' for n, x in zeilen) + '</div>')


WARNUNG_ANFAENGE = ("Daten gestört", "Klimax", "Übernahme")


def warnung_kopf(erk):
    """Echte Warnungen als roter Hinweis im Kopf der Titelseite – nur, wenn es eine gibt (12.11.2026, statt der Karte
    „Warnzeichen“): gestörte Daten, Klimax, Übernahme-Verdacht, rote Datenampel."""
    w = [h for h in erk.get("hinweise", []) if h.startswith(WARNUNG_ANFAENGE)]
    w += [f"Datenampel: {text}" for a, _, text in erk.get("daten", {}).get("zeichen", []) if a == "rot"]
    if not w:
        return ""
    return (f'<div style="background:{KARTE};border:2px solid {ROT};border-radius:12px;padding:10px 16px;'
            f'font-size:15px;line-height:1.5">' + "".join(f'<div>⚠ {t(x)}</div>' for x in w) + '</div>')


def _stellung(df, marken):
    """Was die Stellung heute zeigt (10.11.2026), für Lagezeile und Warnzeichen: [(Ampel, Text)]. Gebrochene Stellung
    (Kurs unter dem Stopp, Fehlausbruch) und Ausbruch ohne Volumen – vorher nur klein im Chart."""
    aus = []
    kurs = float(df["Close"].iloc[-1])
    st_ = (marken or {}).get("stopp")
    if st_ and kurs < st_:
        aus.append(("rot", f"Stellung gebrochen: Kurs {zahl(kurs)} $ unter dem Stopp {zahl(st_)} $ (1,5 ATR)"))
    sst = ((marken or {}).get("short") or {}).get("stopp")
    if sst and kurs > sst:
        aus.append(("rot", f"Short-Stellung gebrochen: Kurs {zahl(kurs)} $ über dem Stopp {zahl(sst)} $ (1,5 ATR)"))
    br = (marken or {}).get("ausbruch") or {}
    if br.get("fehl_tag") is not None:
        aus.append(("rot", f"Fehlausbruch am {pd.Timestamp(br['fehl_tag']):%d.%m.} – Schluss unter dem Tief des "
                           f"Ausbruchstags bzw. mehr als 3 % unter dem Pivot; kein Kauf, weiter beobachten"))
    elif br.get("rueck_tag") is not None:
        aus.append(("gelb", f"Rücktest seit {pd.Timestamp(br['rueck_tag']):%d.%m.} – knapp unter dem Pivot, das Tief des "
                            f"Ausbruchstags hält"))
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
    kurz_ = e.get("reihe") in ("k_ermuedung", "k_baerenflagge", "k_bruch") or (e.get("reihe") == "zahlen" and e.get("zr_seite") == "short")
    if drei and reihe and not kurz_:                    # Volltreffer nur mit Long-Setup (Prüf-Agent 12.11.2026)
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
        ampel = gestaltung.termin_ampel(bis)
        if bis < 0:                              # Termin vorbei, der neue ist noch nicht gemeldet
            zeilen.append(ampelzeile("Nächster Termin", "grau", f"noch offen (zuletzt {tag:%d.%m.%Y})"))
        else:
            zeilen.append(ampelzeile("Nächster Termin", ampel,
                                     f'{WOCHENTAGE[tag.weekday()]} {tag:%d.%m.%Y} · in {bis} Tagen'
                                     + (" – Ausbruch vor Zahlen ist ein Würfelwurf"
                                        if ampel in ("rot", "gelb") else "")))
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


def chartkarte(z, ebene="Tag", ausschnitt=None, zonen_ansicht="Aktuell", gd_kurz=False, avwap_wahl=None):
    """Karte mit Legende und Chart aus dem Zwischenstand von seite_titel; billig, wird bei jedem Knopfdruck neu
    gezeichnet (Zeitebene, Ausschnitt, Zonen, GD10/GD20, AVWAP-Anker), ohne die Seite neu zu rechnen. Darunter der Stundenchart."""
    m = z.get("marken")
    st_ = stunden(z.get("stunde"), m, bool(z["df"].attrs.get("laufend"))) if ebene == "Tag" else ""
    return waehrung_setzen(seite(karte(f'<details><summary style="cursor:pointer;color:{TEXT_2};font-size:14px">Legende</summary>'
                       f'<div style="display:flex;flex-wrap:wrap;gap:20px;margin-top:10px">{legende(ebene, gd_kurz)}</div>'
                       '</details>'
                       + f'<div style="position:relative">{chart(z["df"], ebene, z["index"], ausschnitt, z.get("sek"), z.get("etf", ""), z.get("zonen"), zonen_ansicht, gd_kurz, m, avwap_wahl)}'
                       f'{z.get("rs_lesart", "")}{z.get("plan", "")}</div>' + st_), oben=0, unten=0), z["df"].attrs.get("ticker", ""))


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
    s_ = fundament.angebot(tv_kennzahlen.zeile(tk))
    links += ampelzeile("S · Angebot (frei handelbare Aktien, Rückkäufe)", s_[0], s_[1],
                        "CAN SLIM S: Weniger Aktien im Umlauf und Rückkäufe verknappen das Angebot; Verwässerung über 2 % "
                        "ist ein Warnzeichen. Quelle TradingView. Zählt nicht zu den neun Punkten.")
    return links + ("</div>" if '<div style="display:grid' in links else "")


def _zahlen_gesamt(tk, fund, fd):
    """Eine Karte „Zahlen“ (10.11.2026, vorher Earnings und Zahlen nebeneinander mit denselben Quartalszahlen): links
    Termin, letzte Zahlen und die Balken als Bild, rechts die neun Punkte mit der Zahlen-Ampel, Gewinnqualität und S."""
    return karte(f'<div>{_earnings_feld(fd)}</div><div>{_zahlenkarte(tk, fund, fd)}</div>', "Zahlen")


def _chartmarken(tk, df, m_, k_, zonen, gewinne, fd, rw=None, su=None, zr=None):
    """Was der Chart über die Zonen hinaus einzeichnet: Einstieg und Stopp 1,5 ATR des EINEN Setups (12.11.2026,
    depot.einstieg_setup – vorher die alte Kette Sprung → Base → Momentum, die bei HWM in der Zahlen-Reaktion den Pivot
    einer alten Base und einen Stopp über dem Kurs zeichnete), long mit Kaufzone bis +5 %, short mit Stopp über dem
    Einstieg; Ausbruchstag, Earnings mit Reaktion und nächstem Termin, RS-Rang und Tempo aus Rückenwind."""
    import atr as atr_modul
    import depot
    a = atr_modul.wert(df)
    br = m_.get("ausbruch") or None
    ep = k_.get("ep") or {}
    kontr = ((zonen or {}).get("enge") or {}).get("kontraktionen") or []
    enge_ab = kontr[-1]["hoch_t"] if kontr else None           # Kaufzone und Stopp ab der Enge, nicht über die ganze Base
    r_ = (su or {}).get("reihe")
    seite, e, quelle = depot.einstieg_setup(su, m_, k_, zr, float(df["Close"].iloc[-1]))
    lang = seite == "long" and e
    ab = (pd.Timestamp((zr or {})["tag"]) if r_ == "zahlen" and (zr or {}).get("tag") else
          ep.get("tag") if r_ == "k_ep" else (br or {}).get("erster_tag") or enge_ab)
    m = {"einstieg": float(e) if lang else None, "quelle": quelle, "atr": a,
         "kz_oben": float(e) * 1.05 if lang else None,
         "stopp": float(e) - ATR_STOPP * a if lang and a else None,
         "ab": ab,
         "ausbruch": {"tag": br["tag"], "volumen": br.get("volumen"), "fehl_tag": br.get("fehl_tag"),
                      "rueck_tag": br.get("rueck_tag")}
         if br and r_ in ("m_spitze", "m_weitere", "vcp", "flagge") else None,
         "earnings": reaktionen(df, gewinne) if gewinne is not None else [], "termin": None, "rs": None, "short": None}
    try:
        termin = (fd or {}).get("termin")
        if termin is not None and len(termin) and termin["datum"].iloc[0]:
            t_ = pd.Timestamp(termin["datum"].iloc[0])
            m["termin"] = None if pd.isna(t_) else t_     # 10.11.2026: unbekannter Termin (NaT) ließ den Chart abstürzen
    except Exception:  # noqa: BLE001
        pass
    m["rs"] = rw
    if seite == "short" and e and a:
        em = system_kullamaegi.short_von(k_, r_) or {}
        m["short"] = {"tag": em.get("tag") if r_ != "zahlen" else pd.Timestamp(zr["tag"]), "einstieg": float(e),
                      "stopp": float(e) + ATR_STOPP * a, "volumen": em.get("volumen") if r_ != "zahlen" else None,
                      "art": __import__("kartentisch").NAME.get(r_, "Short").split(" (")[0]}
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
    """Die eine Markt-Ampel (O'Neil, marktklima.py), einmal je Stunde gerechnet; Hochs/Tiefs aus dem letzten Kartentisch."""
    schluessel = pd.Timestamp.now().strftime("%Y%m%d%H")
    if _SPEICHER.get("markt", (None,))[0] != schluessel:
        try:
            import kartentisch
            b = (kartentisch.laden() or {}).get("barometer") or {}
            mm = marktklima.markt(b.get("hochs"), b.get("tiefs"))
        except Exception:  # noqa: BLE001
            mm = None
        _SPEICHER["markt"] = (schluessel, mm)
    return _SPEICHER["markt"][1]


def _kreislauf_box(tk, df, index, gewinne, m_):
    """Kreislaufbild unter den Kacheln, über dem Chart (13.11.2026): Phase, Wechsel, Zeichen (bis 13.11.2026 mit dem
    Satz des Stabs; der Konferenzraum wurde abgebaut)."""
    try:
        import kreislaufbild
        import zeichen
        br = (m_ or {}).get("ausbruch")
        k = zeichen.fuer_titel(tk, df, index, gewinne,
                               fehlausbruch=vcp_zone_text(br) if br and br.get("fehl") else None)
        if not k:
            return ""
        return kreislaufbild.gross(k, tk)
    except Exception:  # noqa: BLE001 – die Seite steht auch ohne Bild
        return ""


def vcp_zone_text(br):
    import vcp_zone
    return vcp_zone.ausbruch_text(br)


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
    try:
        erk["rs_rang"] = rs_rang.rang(tk)
    except Exception:  # noqa: BLE001 – ohne Massive-Dateien bleibt das Glied leer
        erk["rs_rang"] = None
    ph_reihe = phasen_modul.phasen(df) if len(df) >= 300 else None
    ph = phasen_modul.aktuell(df, ph_reihe) if ph_reihe is not None else None   # wie Karte und Kreislauf
    try:
        fd = quellen.laden(tk)
        fund = fundament.ampeln(fd)
        gewinne = fd["gewinne"]
    except Exception:
        fd, fund, gewinne = None, None, None
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
    try:                       # Volumenprofil, verankert nach Ereignis und Struktur (13.11.2026, vorher starr 52 Wochen)
        import avwap
        import volumenprofil
        z_j = (zonen or {}).get("jetzt") or {}
        erk["zahltag"] = avwap.zahlentag(df, gewinne) if gewinne is not None else None
        vv = volumenprofil.verankert(df, erk["zahltag"], z_j.get("start_t") if z_j.get("zone") else None)
        erk["profil"] = {"knoten": vv["knoten"], "verankert": vv} if vv else None
    except Exception:  # noqa: BLE001
        erk["profil"] = None
    reif = next(ok for n, ok, _ in m_["regeln"] if n.startswith("Reife Base"))
    erk["scanner_zone"] = m_["zone"] if m_["zone"].get("zone") else None   # Frühwarnung: Unterkante der Zone
    try:                                         # IBD-Basenzählung auf den Scanner-Zonen (Kachel Base, Nummern im Chart)
        import basen
        erk["basen"] = basen.zaehlen(df, index, (zonen or {}).get("verlauf"), m_["zone"] if reif else None)
        if reif:
            erk["basen"]["markt"] = basen.markt_rueckgang(index, df.index[m_["zone"]["start_i"]])
    except Exception:  # noqa: BLE001 – Kachel ohne Zählung
        erk["basen"] = None
    mm_ = maerkte()
    erk["systeme"] = {"m": m_, "k": k_}
    import kartentisch
    import zahlen_reaktion
    zr_ = zahlen_reaktion.pruefen(df, gewinne)
    su = kartentisch.setup_feststellen(df, m_, k_, zr_, scan)       # das eine Setup (12.11.2026), wie im Kartentisch
    erk["setup_info"] = su
    erk["zahlen_reaktion"] = zr_
    gestaltung.MITSCHRIFT = {}                  # die Lagekarte liest die Ampeln der Kacheln mit
    gestaltung.SYSTEM = kartentisch.LEHRER.get(su.get("reihe"), "M")
    gestaltung.SYSTEM_SHORT = lagekarte.richtung(su) == "short"
    gestaltung.SYSTEM_JE = {"Stärke": "M"} if su.get("reihe") in ("zahlen", "k_ep") else {}
    try:
        rw = _rueckenwind(tk)
        leiste = _kacheln(erk, ph, ph_reihe, fund, df, rd, fd if fund else None, gewinne, m_, k_, mm_, rw)
        k_info = dict(gestaltung.MITSCHRIFT)
    finally:
        gestaltung.MITSCHRIFT = None
        gestaltung.SYSTEM, gestaltung.SYSTEM_SHORT, gestaltung.SYSTEM_JE = None, False, {}
    lk = lagekarte.karte(tk, namen_de.BRANCHE.get(sb.get("branche"), sb.get("branche")) or "", erk, k_info, df)
    marken = _chartmarken(tk, df, m_, k_, zonen, gewinne, fd if fund else None, rw, su, zr_)
    marken["profil"] = (erk.get("profil") or {}).get("verankert")
    marken["zahltag"] = erk.get("zahltag")
    stellung = _stellung(df, marken)
    oben = [_kopf(tk, sb, df, fd, mit_rueckgang=not reif) + _lagezeile(tk, rw, stellung) + warnung_kopf(erk)
            + hinweis_laufend, leiste, _kreislauf_box(tk, df, index, gewinne, m_)]
    zwischen = {"df": df, "erk": erk, "ph_reihe": ph_reihe, "index": index, "gewinne": gewinne, "sek": sek,
                "etf": etf or "", "rs_lesart": _rs_lesart(df, index, sek, etf)}
    if zonen and (erk.get("basen") or {}).get("zahl") and zonen.get("jetzt"):
        zonen["jetzt"] = dict(zonen["jetzt"], nummer=erk["basen"]["zahl"])     # Basennummer an der Zone von heute
    zwischen["zonen"] = zonen
    zwischen["marken"] = marken
    zwischen["plan"] = planzeile(m_, k_, df, marken, zr_, su)        # Plan unter dem Chart (12.11.2026)
    zwischen["stunde"] = _stundenkerzen(tk, df)
    teile = [_zahlen_gesamt(tk, fund, fd if fund else None)]        # Earnings und Zahlen in einer Karte (10.11.2026)
    teile.append(depotleiste.titelkarte(tk, df, erk))
    return {"oben": waehrung_setzen(seite("".join(oben), unten=8), tk), "chart": zwischen,
            "unten": waehrung_setzen(seite("".join(teile), oben=8), tk),
            "lagekarte": waehrung_setzen(lk, tk), "kacheln": k_info}
