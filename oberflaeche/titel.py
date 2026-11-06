"""Titelseite eines einzelnen Titels – genau wie die Designvorlage, als HTML.

seite_titel(ticker) lädt alles (Kurse, Index, Fundament), rechnet Mustererkennung,
Phase, Basenzählung und Fundament-Ampeln und liefert die fertige Seite als HTML-Text.
"""
import os
import sys

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
import fussabdruck                                    # noqa: E402
import absorption                                     # noqa: E402
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
import stroemung as stroemung_modul                   # noqa: E402
import lagekarte                                      # noqa: E402
import markt_systeme                                  # noqa: E402
import system_minervini                               # noqa: E402
import system_kullamaegi                              # noqa: E402
import fuehrer_rang                                   # noqa: E402
import gestaltung                                     # noqa: E402
from chart import chart, legende, reaktionen           # noqa: E402
from gestaltung import (BLAU, GELB, GRUEN, RAND, ROT, TEXT_2, TEXT_3, ampelzeile, basename, kachel, kachel2, karte,  # noqa: E402
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


def _kopf(tk, sb, df, fd=None):
    """Kopf: Name, Branche, Kurs, Abstand zum 52-Wochen-Hoch (Trendvorlage) und der nächste Zahlentermin."""
    k = df["Close"].iloc[-1]
    letzte = df.iloc[-252:]
    hoch = letzte["High"].max()
    abstand = (1 - k / hoch) * 100
    lage = "am 52-Wochen-Hoch" if abstand < 1 else f"{zahl(abstand, 0)} % unter dem 52-Wochen-Hoch"
    tief_nach = letzte.loc[letzte["High"].idxmax():, "Low"].min()
    rueckgang = (1 - tief_nach / hoch) * 100
    if rueckgang >= 10:
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


def _gruppe_korrektur(df, erk, rd):
    """Zeichen neben der Buchregel „Korrektur zum Markt“: Wie tief fiel die eigene Gruppe im selben Zeitraum?
    Fiel der Titel kaum stärker als seine Gruppe (höchstens das 1,5-Fache), war es eine Sektor-Korrektur und keine
    Schwäche des Titels. Die Ampel der Buchregel bleibt unverändert (eigene Ableitung, nicht aus dem Buch)."""
    w = erk["werte"]
    if not rd or "korrektur_x_markt" not in w:
        return None
    try:
        g = rudel.gruppenkurs(rd["rudel"]["mitglieder"])
        ab = df.index[w["start_index"]]
        teil = g[g.index >= ab]
        if len(teil) < 5:
            return None
        rueck = float((1 - teil / teil.cummax()).max() * 100)
        faktor = w["tiefe_pct"] / max(rueck, 5.0)
        return {"name": rd["rudel"]["name"], "rueckgang": rueck, "faktor": faktor, "sektor": faktor <= 1.5}
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
    w = erk["werte"]
    if erk["muster"] and erk["muster"][0] == "Umkehr":
        sig = (erk.get("mp") or {}).get("signale") or []
        s_ = next((x for x in reversed(sig) if x["art"] == "S"), None)
        u_ = next((x for x in reversed(sig) if x["art"] == "U"), None)
        if s_ and u_ and s_["tag"] == u_["tag"]:
            zeile = f"am {u_['tag']:%d.%m.}: Bruch {s_['dir']} gescheitert, Umkehr {u_['dir']}"
        else:
            zeile = " · ".join(t for t in (
                f"Bruch {s_['dir']} gescheitert am {s_['tag']:%d.%m.}" if s_ else "",
                f"Umkehr {u_['dir']} am {u_['tag']:%d.%m.}" if u_ else "") if t)
        return kachel("Base", "grau", "keine – Umkehr", zeile,
                      "Keine Base: Die Wertzone ist jünger als drei Wochen. Sie entstand aus einem Bruch, der gescheitert ist; "
                      "der Kurs hat sie in die Gegenrichtung verlassen (Umkehr nach einer gescheiterten Auktion, Dalton). "
                      "Eine Basennummer gibt es dafür nicht.")
    hist_ = erk.get("historie") or []
    zaehl = {a: sum(1 for b in hist_ if b["ausgang"] == a) for a in ("gelungen", "gescheitert", "offen")}
    bilanz = (f" Bilanz der verlassenen Wertzonen der letzten drei Jahre: {zaehl['gelungen']} gelungen, "
              f"{zaehl['gescheitert']} gescheitert, {zaehl['offen']} offen (gelungen = 20 % jenseits des Pivots, "
              f"bevor ein Schluss 8 % dagegen lag)." if hist_ else "")
    bz = w.get("basenzahl") if erk["muster"] else None
    if not bz:
        hist = erk.get("historie") or []
        if not hist:
            return kachel("Base", "grau", "keine", "auch keine frühere in drei Jahren", "")
        b = hist[-1]
        return kachel("Base", {"gelungen": "grün", "gescheitert": "rot"}.get(b["ausgang"], "gelb"),
                      f"vorige {b['ausgang']}",
                      f"{basename(b['muster'])} · Pivot {zahl(b['pivot'])} $ · Ausbruch {erk['df_index'][b['ausbruch']]:%d.%m.%Y}",
                      "Zurzeit keine Base. Gezeigt wird die letzte Base der drei Jahre und ihr Ausgang nach O'Neil "
                      "(gelungen = 20 % über dem Pivot, bevor ein Schluss 8 % darunter liegt). Eine gescheiterte Base "
                      "ist oft das Ende des Aufwärtstrends." + bilanz)
    ampel = "grün" if bz <= 2 else "gelb" if bz == 3 else "rot"
    zeile = f"Tiefe {zahl(w['tiefe_pct'], 0)} %"
    if "index_rueckgang_pct" in w:
        zeile += f" · S&P 500 zugleich −{zahl(w['index_rueckgang_pct'], 0)} %"
    return kachel("Base", ampel, f"Nr. {bz} · {'früh' if bz <= 2 else 'handelbar' if bz == 3 else 'spät'}", zeile,
                  "Die wievielte Base seit Beginn des Aufwärtstrends. O'Neil: Basen 1 und 2 sind früh und am "
                  "ergiebigsten, die dritte ist noch handelbar, ab der vierten scheitern die meisten. Tiefe der Base gegen den Rückgang des S&P 500 im selben Zeitraum: "
                  "O'Neil erlaubt höchstens das 2- bis 3-Fache." + bilanz)


def _k_branche(df, rd):
    r = (rd or {}).get("rudel")
    mg = (rd or {}).get("m_gruppe")
    if not r or r["art"] != "Branche" or not mg:
        return kachel("Branche", "grau", "–", "Branche zu klein", "")
    wert = {"grün": "Rückenwind", "gelb": "neutral", "rot": "Gegenwind"}[mg["ampel"]]
    g, t = rd["kurs_gruppe"].dropna(), df["Close"].dropna()
    vorher = mg["wert"] - mg["richtung"]
    zeile = (f"Mansfield {'+' if vorher >= 0 else '−'}{zahl(abs(vorher), 1)} → "
             f"{'+' if mg['wert'] >= 0 else '−'}{zahl(abs(mg['wert']), 1)} in 4 Wochen")
    if len(g) > 64 and len(t) > 64:
        d = ((t.iloc[-1] / t.iloc[-64]) / (g.iloc[-1] / g.iloc[-64]) - 1) * 100
        zeile += f" · Titel {'+' if d >= 0 else '−'}{zahl(abs(d), 0)} % zur Branche"
    return kachel("Branche", mg["ampel"], wert, zeile,
                  f"{namen_de.branche(r['name'])}. Stärke zum Markt = Mansfield-RS (Weinstein): die Linie Branche ÷ S&P 500 gegen ihr "
                  "52-Wochen-Mittel. Rückenwind = über dem Mittel (Wert über 0) und steigend, Gegenwind = darunter und fallend. Angezeigt: Wert vor 4 Wochen → heute. "
                  "Weinstein: Gekauft wird nur in einer starken Gruppe. Titel zur Branche: letzte 3 Monate.")


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


def _k2_trend(m, ph, ph_reihe):
    tv = m["trendvorlage"]
    n = sum(tv.values()) if tv else 0
    mm = (("grün" if n == 7 else "gelb" if n >= 5 else "rot"), f"Trendvorlage {n} von 7") if tv else ("grau", "zu kurz")
    seit = _seit(ph_reihe) if ph else None
    zeile = (f"Weinstein: Phase {ph} {PHASENTEXT[ph]}"
             + (f" seit KW {seit.isocalendar()[1]}/{seit.year}" if seit is not None else "")) if ph else ""
    return kachel2("Trend", mm, None, zeile,
                   "M – Minervinis Trendvorlage, sieben Punkte zu Kurs und Durchschnitten (der achte, RS ab 70, steht in "
                   "der Kachel „Stärke“). Sie entspricht Weinsteins Stufe 2: "
                   + "; ".join(f"{n_} {'✓' if ok else '✗'}" for n_, ok in tv.items())
                   + "\n\nK – Kullamägi nutzt keine Trendvorlage; seine Auswahl ist die Stärke (Kachel „Stärke“)."
                   + "\n\nPhase nach Weinstein nur noch als Zeichen.")


def _k2_staerke(m, k, rang):
    mm = (("grün" if rang >= 70 else "gelb" if rang >= 60 else "rot"), f"RS {rang} von 99") if rang is not None \
        else ("grau", "kein RS-Rang")
    fr = k["fuehrer"]
    best = max((v for v in (fr or {}).values() if v == v), default=None)
    kk = (k["fuehrer_ampel"], f"besser als {zahl(best, 1 if best >= 90 else 0)} %") if best is not None else ("grau", "–")
    return kachel2("Stärke", mm, kk, fuehrer_rang.text(fr),
                   "M – RS-Rang 1–99 wie das RS-Rating von IBD (12 Monate, jüngstes Quartal doppelt), verglichen mit "
                   "unserem Revier. Minervini verlangt mindestens 70 – der achte Punkt der Trendvorlage. Die Zahl ist "
                   "kein Listenplatz: 16 heißt, nur 16 % der Titel liefen schwächer.\n\nK – Kullamägi sucht die ein bis "
                   "zwei Prozent mit den größten Kursanstiegen über 1, 3 und 6 Monate. Grün = in einem Zeitraum unter "
                   "den obersten 2 %, gelb = oberste 5 %. Angezeigt: der beste der drei Zeiträume.")


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
    z = (erk.get("mp") or {}).get("zustand") or {}
    teile = [z.get("wort", "")]
    if m.get("pivot"):
        teile.append(f"Pivot {zahl(m['pivot'])} $ · {m['lage']}")
    hilfe = ("M – " + system_minervini.kurz(m) + "\n" + "\n".join(f"{'✓' if ok else '✗'} {n} – {x}" for n, ok, x in m["regeln"])
             + "\n\nK – " + "\n".join(
                 f"{x['art']} ({x['ampel']}):\n" + "\n".join(f"{'✓' if ok else '✗'} {n} – {y}" for n, ok, y in x["regeln"])
                 for x in (k.get("ep"), k.get("breakout"), em) if x))
    if erk.get("mp") and df is not None:
        hilfe += "\n\nDruck in der Wertzone:\n" + "\n".join(f"{pf} {n}: {x}" for n, pf, x in stroemung_modul.druck(erk["mp"], df))
    return kachel2("Setup", mm, kk, " · ".join(x for x in teile if x), hilfe + "\n\n" + AUSLOESER_HILFE)


def _k2_enge(m, k, erk, df):
    a = erk.get("absorption")
    eng = next(r for r in m["regeln"] if r[0] == "Enge (VCP)")
    wort = {"grün": "ja", "gelb": "teilweise", "rot": "nein"}
    mm = (a["ampel"], wort[a["ampel"]]) if a else ("grau", "nicht messbar")
    b = k.get("breakout") or {}
    kons = next((r for r in b.get("regeln", []) if r[0].startswith("Konsolidierung")), None)
    kk = (("grün" if kons[1] else "gelb" if b.get("wochen") and b["wochen"] <= system_kullamaegi.KONS_GELB else "rot"),
          f"{b['wochen']} Woche{'n' if b['wochen'] != 1 else ''}") if kons and b.get("wochen") else ("grau", "keine Wertzone")
    zeile = eng[2]
    if a:
        tiefs = "steigen" if a["steigend"] else "halten" if a["halten"] else "fallen"
        zeile = f"Tiefs {tiefs}" + (f" · Volumen {zahl(a['trocken'], 1)}-fach" if a.get("trocken") is not None else "")
    return kachel2("Enge", mm, kk, zeile,
                   "M – Minervinis VCP: am rechten Rand halten oder steigen die Tiefs, die Spanne schrumpft auf ein "
                   "Drittel der Base (oder unter 5 %), das Volumen trocknet aus (bis 0,8-fach des 50-Tage-Schnitts).\n\n"
                   "K – Kullamägi: kurze Konsolidierung, meist 1–3 Wochen, nach einem Schub nach oben, vorzugsweise bei "
                   "reduziertem Volumen. Gelb bis 8 Wochen.")


def _kacheln(erk, ph, ph_reihe, fund, df, rd, fd, mr, gewinne, m, k, mm, km):
    """Die acht Kacheln der Titelseite (Zwei Systeme, 05.11.2026): sechs mit je einer Ampel für Minervini (M) und
    Kullamägi (K), Branche und Base als Zeichen. Fehlt ein Wert, steht ein grauer Punkt mit dem Grund."""
    _k_zone(erk), _k_zahlen(fd, fund)            # nur mitgeschrieben für die Lagekarte, hier nicht gezeigt
    rang = (erk.get("rs_rang") or (None, ""))[0]
    kl = [_k2_markt(mm, km, mr), _k2_trend(m, ph, ph_reihe), _k2_staerke(m, k, rang),
          _k2_fundament(m, k, fund, ph, df, gewinne), _k2_setup(m, k, erk, df), _k2_enge(m, k, erk, df),
          _k_branche(df, rd), _k_base(erk)]
    return (f'<section aria-label="Lage in fünf Sekunden" style="display:grid;'
            f'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">{"".join(kl)}</section>')


def _plan(m, k, mm, km, df):
    """Karte „Plan“ der zwei Systeme: je System die Regeln mit ✓/✗, Marken, Stopp und Ausstieg."""
    c, h, l = df["Close"], df["High"], df["Low"]
    kurs = float(c.iloc[-1])
    teile = []
    # System Minervini
    kopf = {"grün": "🟢 <b>Minervini: Setup steht</b>", "gelb": "🟡 <b>Minervini: eine Regel fehlt</b>",
            "rot": "⚪ <b>Minervini: kein Setup</b>"}[m["ampel"]]
    teile.append(f'<p style="margin:0;font-size:16px">{kopf} · Markt {mm["wort"] if mm else "–"}</p>')
    teile.append("".join(ampelzeile(n, "grün" if ok else "rot", x) for n, ok, x in m["regeln"]))
    if m.get("pivot"):
        vorbehalt = ("" if m["ampel"] == "grün" else
                     "Erst wenn die fehlenden Regeln erfüllt sind – bis dahin nur Marken: ")
        teile.append(f'<p style="margin:0;font-size:15px;line-height:1.6">{vorbehalt}Kauf über dem Pivot '
                     f'{zahl(m["pivot"])} $, Kaufzone bis {zahl(m["pivot"] * 1.05)} $ ({t(m["lage"])}). Stopp '
                     f'{zahl(m["stopp"])} $ ({_vorzeichen((m["stopp"] / m["pivot"] - 1) * 100)} % vom Pivot). '
                     f'{t(m["ausstieg"])}</p>')
    elif len(c) >= 260:
        g50, g150, g200 = (float(c.iloc[-n:].mean()) for n in (50, 150, 200))
        tief52, hoch52 = float(l.iloc[-252:].min()), float(h.iloc[-252:].max())
        marken = []
        if kurs < max(g150, g200):
            marken.append((max(g150, g200), "Kurs über GD150 und GD200"))
        if kurs < 1.30 * tief52:
            marken.append((1.30 * tief52, "mindestens 30 % über dem 52-Wochen-Tief"))
        if kurs < 0.75 * hoch52:
            marken.append((0.75 * hoch52, "höchstens 25 % unter dem 52-Wochen-Hoch"))
        if kurs < g50:
            marken.append((g50, "GD50 zurückerobert"))
        if marken:
            teile.append(f'<p style="margin:0;font-size:15px;color:{TEXT_2}">Marken zur Trendvorlage (die nächste zuerst):</p>'
                         + "".join(ampelzeile(f"{zahl(p_)} $ ({_vorzeichen((p_ / kurs - 1) * 100)} %)", "grau", x)
                                   for p_, x in sorted(marken)))
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
        teile.append(f'<p style="margin:0;font-size:15px;line-height:1.6">Einstieg {ziel}: über dem Hoch der ersten '
                     f'5-, 30- oder 60-Minuten-Kerze (je länger, desto weniger Fehlausbrüche). {t(k["ausstieg"])}</p>')
    em = k.get("ermuedung")
    if em:
        teile.append(f'<p style="margin:12px 0 0;font-size:16px">{"🔴" if em["ampel"] == "grün" else "🟡"} '
                     f'<b>Ermüdung nach Überdehnung (Short)</b> – Bruch der Flagge am {em["tag"]:%d.%m.}, '
                     f'Fahnenstange +{zahl(em["stange"], 0)} %</p>'
                     + "".join(ampelzeile(n, "grün" if ok else "gelb", y) for n, ok, y in em["regeln"])
                     + f'<p style="margin:0;font-size:15px">Die Truppe ist weit vorgestoßen, hat sich eingegraben – '
                       f'jetzt bricht die Stellung nach hinten weg. Unterkante {zahl(em["unten"])} $, Stopp über dem '
                       f'Hoch des Auslösetags {zahl(em["stopp"])} $ (Kullamägi: Stopp am Tageshoch).</p>')
    rand = GRUEN if "grün" in (m["ampel"], (hk or {}).get("ampel")) else ROT if em and em["ampel"] == "grün" else BLAU
    return "".join(teile), rand


def _ist_warnung(h):
    """Hinweise der Mustererkennung, die warnen; die übrigen stehen schon in den Kacheln."""
    if h.startswith(("Phase ", "Base Nr.", "späte Base", "Ausbruch aus der Base", "in der Kaufzone", "ausgedehnt",
                     "Volumen trocknet aus", "Tiefe grün")):
        return False
    return True


def _warnzeichen(erk):
    """Nur Warnungen: Frühwarnzeichen Phase 3/4 (Weinstein), Klimax, Übernahme-Verdacht, gestörte Daten, unsichere
    Mustererkennung und Hinweise, die in keiner Kachel stehen."""
    zeilen = "".join(ampelzeile(text, a, "Weinstein: Frühwarnzeichen für Long-Halter, bevor die Phase wechselt – die "
                                         "Phasengrenzen bleiben unverändert") for a, text in erk.get("fruehwarnung", []))
    zeilen += "".join(ampelzeile(h, "rot" if h.startswith(("Daten gestört", "Klimax", "Übernahme")) or "(rot)" in h
                                else "gelb", "") for h in erk["hinweise"] if _ist_warnung(h))
    gk = erk.get("gruppe_korrektur")
    if gk and (erk["werte"].get("korrektur_x_markt") or 0) > 2:
        zeilen += ampelzeile(("Sektor-Korrektur: " if gk["sektor"] else "Schwächer als die Gruppe: ")
                             + f'Gruppe {namen_de.branche(gk["name"])} −{zahl(gk["rueckgang"], 0)} %, Titel {zahl(gk["faktor"], 1)}-fach der Gruppe '
                             "(Zeichen neben der Buchregel, ändert die Ampel nicht)", "gelb", "")
    zeilen += "".join(ampelzeile(f"Datenampel: {text}", a, "") for a, _, text in erk.get("daten", {}).get("zeichen", []))
    for b in erk.get("selbstpruefung") or []:
        zeilen += ampelzeile(f"Base-Erkennung unsicher: {b}", "gelb",
                             "Die Selbstprüfung fand einen inneren Widerspruch – Base im Chart prüfen")
    return karte(zeilen or f'<div style="color:{TEXT_2};font-size:15px">Keine Warnzeichen.</div>', "Warnzeichen")


def _phase_zyklus(ph, krit):
    """Phase (Weinstein): die sechs Merkmale eines Aufwärtstrends mit ✓/✗ und die Warnzeichen der Phase."""
    if not krit or not krit.get("kriterien"):
        return karte(f'<div style="color:{TEXT_2}">Zu kurze Historie für Phase und Zyklus.</div>', "Phase und Zyklus")
    satz = {
        2: "Der Titel steht in Phase 2. Die sechs Merkmale zeigen, ob der Aufwärtstrend trägt.",
        3: "Phase 3 ist die Gipfelphase: Der Aufwärtstrend verliert Merkmal für Merkmal.",
        4: "Nach Phase 4 folgt in der Regel zuerst Phase 1, der Boden. Als Phase 2 zählt der Titel erst wieder, wenn "
           "das Bild eines Aufwärtstrends vier Wochen steht, der Kurs mindestens 25 % über dem 52-Wochen-Tief liegt "
           "und ein Wochenschluss das Hoch der letzten 26 Wochen übertrifft.",
        1: "Phase 1 ist der Boden. Phase 2 beginnt, wenn das Bild eines Aufwärtstrends vier Wochen steht, der Kurs "
           "mindestens 25 % über dem 52-Wochen-Tief liegt und ein Wochenschluss das Hoch der letzten 26 Wochen "
           "übertrifft.",
    }.get(ph, "")
    k = krit["kriterien"]
    merkmale = (f'<div style="font-size:15px;font-weight:600;padding-top:6px">{sum(k.values())} von 6 Merkmalen eines '
                f'Aufwärtstrends erfüllt</div>' + "".join(ampelzeile(n, "grün" if ok else "rot", "") for n, ok in k.items())
                + "".join(ampelzeile(w, "rot", "") for w in krit.get("warnungen", [])))
    kopf = (f'<p style="margin:0;font-size:14px;color:{TEXT_2};line-height:1.6">'
            f'{t((f"Phase {ph}: {PHASENTEXT[ph]}. " if ph else "") + satz)}</p>')
    return karte(kopf + merkmale, "Phase und Trend")


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
    if not fd:
        return karte(f'<div style="color:{TEXT_2}">Keine Gewinndaten verfügbar.</div>', "Earnings")
    g = fd["gewinne"]
    zeilen = []
    termin = fd.get("termin")
    if termin is not None and len(termin) and termin["datum"].iloc[0] and not pd.isna(pd.Timestamp(termin["datum"].iloc[0])):
        tag = pd.Timestamp(termin["datum"].iloc[0])
        bis = (tag.normalize() - pd.Timestamp.today().normalize()).days
        ampel = "gelb" if 0 <= bis <= 10 else "grün"
        zeilen.append(ampelzeile("Nächster Termin", ampel,
                                 f'{WOCHENTAGE[tag.weekday()]} {tag:%d.%m.%Y} · in {bis} Tagen'
                                 + (" – innerhalb von 10 Tagen: Ausbruch vor Zahlen ist ein Würfelwurf" if ampel == "gelb" else "")))
    letzte = g.dropna(subset=["eps"]).iloc[-1]
    zeilen.append(ampelzeile("Letzte Zahlen", "grün" if letzte["ueberraschung_pct"] >= 0 else "rot",
                             f'{g.dropna(subset=["eps"]).index[-1]:%d.%m.%Y}: {zahl(letzte["eps"])} $ je Aktie, '
                             f'erwartet {zahl(letzte["schaetzung"])} $ ({_vorzeichen(letzte["ueberraschung_pct"])} %)'))
    eps = fundament._wachstum(g["eps"]).dropna().iloc[-3:]
    # Gemeldet wird etwa einen Monat nach Quartalsende: das berichtete Quartal liegt davor
    eps_w = [(_quartal(i - pd.Timedelta(days=45)), float(v)) for i, v in eps.items()]
    sec = fd.get("sec")
    ums_w = []
    if sec is not None and not sec.empty:
        u = fundament._wachstum(sec["umsatz"].dropna()).dropna().iloc[-3:]
        ums_w = [(_quartal(i), float(v)) for i, v in u.items()]
    balken = (f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;padding-top:12px">'
              f'{_balken(ums_w, "Umsatzwachstum zum Vorjahr")}{_balken(eps_w, "Gewinn je Aktie zum Vorjahr")}</div>')
    return karte("".join(zeilen) + balken, "Earnings")


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


def chartkarte(z, ebene="Tag", ausschnitt=None, zonen_ansicht="Aktuell", gd_kurz=False):
    """Karte mit Legende und Chart aus dem Zwischenstand von seite_titel; billig, wird bei jedem Knopfdruck neu
    gezeichnet (Zeitebene, Ausschnitt, Zonen, GD10/GD20), ohne die Seite neu zu rechnen."""
    return seite(karte(f'<div style="display:flex;flex-wrap:wrap;gap:20px">{legende(ebene, gd_kurz)}</div>'
                       + f'<div style="position:relative">{chart(z["df"], ebene, z["index"], ausschnitt, z.get("sek"), z.get("etf", ""), z.get("zonen"), zonen_ansicht, gd_kurz)}'
                       f'{z.get("rs_lesart", "")}</div>'), oben=0, unten=0)


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
    with gzip.open(pfad + ".neu", "wb", compresslevel=3) as f:
        pickle.dump(teile, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(pfad + ".neu", pfad)


def ablage_grenze():
    """Abgelegte Titelseiten älter als das Programm oder das Depot gelten nicht mehr."""
    import depot
    return max([codezeit()] + ([os.path.getmtime(depot.DATEI)] if os.path.exists(depot.DATEI) else []))


def frisch(tk, grenze=None):
    """Liegt eine gültige Titelseite im Schrank?"""
    try:
        return os.path.getmtime(os.path.join(ABLAGE, f"{tk.upper()}.pkl.gz")) >= (grenze or ablage_grenze())
    except OSError:
        return False


def abgelegt(tk):
    """Gespeicherte Titelseite oder None (fehlt, oder Programm bzw. Depot sind jünger). Nach einer Änderung füllt
    nachtlauf.py --seiten den Schrank im Hintergrund neu (06.11.2026)."""
    import gzip
    import pickle
    pfad = os.path.join(ABLAGE, f"{tk.upper()}.pkl.gz")
    try:
        if not frisch(tk):
            return None
        with gzip.open(pfad, "rb") as f:
            return pickle.load(f)
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
    historie = erkennung.basen_historie(df, index, 780)
    if erk["muster"] and historie and historie[-1]["ende"] >= erk["werte"].get("start_index", len(df)):
        historie = historie[:-1]                 # die gerade ausgebrochene Base ist die aktuelle, nicht doppelt zeigen
    erk["historie"] = historie
    erk["selbstpruefung"] = erkennung.selbstpruefung(df, erk, historie)
    erk["df_index"] = df.index
    w_ = erk["werte"]
    if erk["muster"] and "start_index" in w_:
        erk["fuss"] = fussabdruck.fussabdruck(df, w_["start_index"], w_.get("ende_index"), w_["pivot"])
    for b in historie:
        # Volumen am Ausbruchstag der Tabelle (erster Schluss über dem Pivot), damit Datum und Volumen zusammenpassen
        s50 = fussabdruck._schnitt50(df["Volume"].to_numpy(float), b["ausbruch"])
        b["vol_ausbruch"] = float(df["Volume"].iloc[b["ausbruch"]]) / s50 if s50 else None
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
    erk["absorption"] = (absorption.absorption(df, w_["start_index"], w_["pivot"], w_.get("ende_index"))
                         if erk["muster"] and "start_index" in w_ else None)
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
    erk["gruppe_korrektur"] = _gruppe_korrektur(df, erk, rd)
    hinweis_laufend = ""
    if df.attrs.get("laufend"):
        hinweis_laufend = (f'<div style="border:1px solid #5A4A1A;background:#2A2410;color:#E3B341;border-radius:10px;'
                           f'padding:10px 14px;font-size:14px">Laufender Börsentag, Stand {df.attrs["stand"]} Uhr: Die letzte '
                           f'Kerze ist unvollständig (im Chart hohl). Ausbruch, Volumenfaktoren, Fußabdruck und Absorption '
                           f'sind vorläufig bis Börsenschluss – O\'Neil und Minervini urteilen über Schlusskurs und '
                           f'Tagesvolumen.</div>')
    erk["fruehwarnung"] = fruehwarnung.zeichen(df, erk, ph)
    gtage = [d for d, _ in reaktionen(df, gewinne)] if gewinne is not None else []
    m_ = system_minervini.pruefen(df, erk, (erk.get("rs_rang") or (None,))[0], fund)
    k_ = system_kullamaegi.pruefen(df, erk, gtage, ticker=tk)
    mm_, km_ = maerkte()
    erk["systeme"] = {"m": m_, "k": k_}
    gestaltung.MITSCHRIFT = {}                  # die Lagekarte liest die Ampeln der Kacheln mit
    try:
        leiste = _kacheln(erk, ph, ph_reihe, fund, df, rd, fd if fund else None, mr, gewinne, m_, k_, mm_, km_)
        k_info = dict(gestaltung.MITSCHRIFT)
    finally:
        gestaltung.MITSCHRIFT = None
    lk = lagekarte.karte(tk, namen_de.BRANCHE.get(sb.get("branche"), sb.get("branche")) or "", erk, k_info, df)
    oben = [_kopf(tk, sb, df, fd) + hinweis_laufend, leiste]
    zwischen = {"df": df, "erk": erk, "ph_reihe": ph_reihe, "index": index, "gewinne": gewinne, "sek": sek,
                "etf": etf or "", "rs_lesart": _rs_lesart(df, index, sek, etf)}
    try:                                         # VCP-Scanner Baustein 1: Zone jetzt und abgeschlossene Zonen
        import vcp_zone
        zwischen["zonen"] = vcp_zone.alles(df)
    except Exception:  # noqa: BLE001 – Chart ohne Zonen
        zwischen["zonen"] = None
    teile = []
    links = "".join(ampelzeile(n, a, x) for n, (a, x) in fund["punkte"].items()) if fund else \
        f'<div style="color:{TEXT_2}">Fundamentdaten nicht verfügbar.</div>'
    if fund and fund["zeichen"]:
        links += "".join(ampelzeile(z, "gelb" if "prüfen" in z else "blau", "") for z in fund["zeichen"])
    s_ = fundament.angebot(sic13._tv(tk))
    i_ = fundament.institutionen((fd or {}).get("institutionen") if fund else None)
    links += (ampelzeile("S · Angebot (frei handelbare Aktien, Rückkäufe)", s_[0], s_[1],
                         "CAN SLIM S: Weniger Aktien im Umlauf und Rückkäufe verknappen das Angebot; Verwässerung über 2 % "
                         "ist ein Warnzeichen. Quelle TradingView. Zählt nicht zu den sieben Prüfpunkten.")
              + ampelzeile("I · Institutionen (Fonds)", i_[0], i_[1],
                           "CAN SLIM I: Führer brauchen Fonds als Käufer – ein Anteil zwischen 20 und 90 %, der zunimmt. "
                           "Über 90 % ist überbesetzt (wer verkauft, drückt). Quelle Yahoo (13F-Meldungen der zehn größten "
                           "Halter). Zählt nicht zu den sieben Prüfpunkten."))
    raster = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:24px">'
    teile.append(f'{raster}{_earnings_feld(fd if fund else None)}{karte(links, "Fundament-Ampeln")}</div>')
    teile.append(f'{raster}{_phase_zyklus(ph, krit)}{_warnzeichen(erk)}</div>')
    plan, rand = _plan(m_, k_, mm_, km_, df)
    teile.append(karte(plan, "Plan", rand=rand))
    teile.append(depotleiste.titelkarte(tk, df, erk))
    return {"oben": seite("".join(oben), unten=8), "chart": zwischen, "unten": seite("".join(teile), oben=8),
            "lagekarte": lk, "kacheln": k_info}
