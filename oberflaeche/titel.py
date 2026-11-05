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
import short_seite                                    # noqa: E402
import avwap as avwap_modul                           # noqa: E402
import depotleiste                                    # noqa: E402
import depot                                          # noqa: E402
import fussabdruck                                    # noqa: E402
import freie_bahn                                     # noqa: E402
import gelaende                                       # noqa: E402
import absorption                                     # noqa: E402
import rs_rang                                        # noqa: E402
import phase as phasen_modul                          # noqa: E402
import marktdaten                                     # noqa: E402
import namen_de                                       # noqa: E402
import marktrichtung                                  # noqa: E402
import rudel                                          # noqa: E402
import rudelkarte                                     # noqa: E402
import quellen                                        # noqa: E402
import sektoren                                       # noqa: E402
import sic13                                          # noqa: E402
import stroemung as stroemung_modul                   # noqa: E402
import stroemungsbild                                 # noqa: E402
import lagekarte                                      # noqa: E402
import gestaltung                                     # noqa: E402
import lage as lage_modul                             # noqa: E402
from chart import chart, legende, reaktionen           # noqa: E402
from stimmung import kurve                             # noqa: E402
from gestaltung import (BLAU, GELB, GRUEN, RAND, ROT, TEXT_2, TEXT_3, ampelzeile, basename, form_hinweis, kachel, karte, seite,  # noqa: E402
                        t, zahl)

PHASENTEXT = {1: "Bodenbildung", 2: "Aufwärtstrend", 3: "Gipfelphase", 4: "Abwärtstrend"}
PHASENAMPEL = {1: "grau", 2: "grün", 3: "gelb", 4: "rot"}


def _sic13_karte(k):
    """SIC-13 · Sovereign Investment Compass: fünf Ebenen, elf Kriterien, bei jedem Titel dieselben."""
    from gestaltung import AMPEL
    spalten = ""
    for ebene, nummern in sic13.EBENEN:
        zeilen = ""
        for n in nummern:
            v = k["kriterien"][n]
            zeilen += (f'<div title="{t(sic13.FRAGE[n])}" style="display:flex;flex-direction:column;gap:3px;padding:8px 0;'
                       f'border-top:1px solid {RAND}">'
                       f'<div style="display:flex;align-items:center;gap:8px">'
                       f'<span style="width:12px;height:12px;border-radius:50%;flex-shrink:0;background:{AMPEL[v["ampel"]]}"></span>'
                       f'<span style="font-size:14px;font-weight:600;flex:1">{n} · {t(sic13.NAMEN[n])}</span>'
                       f'<span style="font-size:13px;color:{TEXT_2}">{t(v["wort"])}</span></div>'
                       f'<div style="font-size:13px;color:{TEXT_2};line-height:1.5">{t(v["zeile"])}</div>'
                       f'<div style="font-size:11px;color:{TEXT_3};letter-spacing:0.04em">{t(v["art"])}</div></div>')
        spalten += (f'<div style="display:flex;flex-direction:column"><div style="font-size:12px;letter-spacing:0.06em;'
                    f'text-transform:uppercase;color:{TEXT_3};padding-bottom:6px">{t(ebene)}</div>{zeilen}</div>')
    tor = k["torwaechter"]
    kopf = ""
    if tor == "rot":
        kopf = (f'<div style="font-size:14px;color:#FF7B72">Ebene 0 nicht bestanden – nach SIC-13 K.O. '
                f'Alle Angaben bleiben sichtbar.</div>')
    elif tor == "gelb":
        kopf = f'<div style="font-size:14px;color:#E3B341">Ebene 0 nur zur Hälfte bestanden.</div>'
    fuss = (f'<div style="font-size:12px;color:{TEXT_3}">Einschätzung: Claude (Wissensstand Juni 2026, aus Beschreibung '
            f'und Branchenkenntnis), wird vom Nachtlauf aus Jahresbericht und Telefonkonferenz zu den Zahlen erneuert. '
            f'Gemessen: Kurse (10 Jahre), SEC-Quartalszahlen, TradingView. Maus auf ein Kriterium zeigt seine Frage aus SIC-13 '
            f'und die Schwellen.</div>')
    return karte(kopf + f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px">'
                 f'{spalten}</div>' + fuss, "SIC-13 · Strukturelle Überlegenheit vor der technischen Analyse")


def _tv_symbol(tk):
    """BÖRSE:TICKER für TradingView aus daten/tv/revier.csv; ohne Eintrag nur der Ticker (TradingView sucht dann)."""
    import watchlists
    if watchlists.zu_tv(tk):                     # Börse außerhalb der USA (z. B. RHM.DE → XETR:RHM)
        return watchlists.zu_tv(tk)
    z = sic13._tv(tk.upper())
    ex = z["exchange"] if z is not None and isinstance(z.get("exchange"), str) else None
    sym = tk.upper().replace("-", ".")
    return f"{ex}:{sym}" if ex else sym


def _kopf(tk, sb, df):
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
            f'<div style="font-size:15px;color:{TEXT_2};line-height:1.6">{t(zeile)}</div>{_steckbrief(tk, sb)}</div>'
            f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex:0 0 auto;margin-left:auto">'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:34px;font-weight:500">{zahl(k)} $</span>'
            f'<span style="font-size:14px;color:{TEXT_2}">'
            + (f'laufender Tag, Stand {df.attrs["stand"]} Uhr (Yahoo, bis 15 Min. verzögert)' if df.attrs.get("laufend")
               else f'Schluss {df.index[-1]:%d.%m.%Y}') + f' · {lage}</span>'
            f'</div></div></header>')


def _rs_richtung(df, index):
    if index is None:
        return "grau", "–", "kein Index"
    rs = (df["Close"] / index["Close"].reindex(df.index, method="ffill")).dropna()
    if len(rs) < 70:
        return "grau", "–", "zu kurze Historie"
    aend = (rs.iloc[-1] / rs.iloc[-64] - 1) * 100
    neu_hoch = rs.iloc[-1] >= rs.iloc[-252:].max() * 0.99
    if neu_hoch:
        return "grün", "Hoch", "RS-Linie am 52-Wochen-Hoch"
    return ("grün" if aend > 2 else "rot" if aend < -2 else "gelb",
            f'{"+" if aend >= 0 else "−"}{zahl(abs(aend), 0)} %', "RS gegen S&P 500, letzte 3 Monate")


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


def _mio(x):
    return f"{zahl(x / 1e6, 1)} Mio." if x >= 1e6 else f"{zahl(x / 1e3, 0)} Tsd."


PHASE_AMPEL = {1: "gelb", 2: "grün", 3: "gelb", 4: "rot"}


def _seit(ph_reihe):
    if ph_reihe is None or not len(ph_reihe):
        return None
    anders = ph_reihe[ph_reihe != ph_reihe.iloc[-1]]
    return ph_reihe[ph_reihe.index > anders.index[-1]].index[0] if len(anders) else ph_reihe.index[0]


def _k_markt(mr):
    if not mr:
        return kachel("Markt", "grau", "–", "Marktrichtung nicht verfügbar", "")
    dt = mr.get("distributionstage") or {}
    kurz = {"Bestätigter Aufwärtstrend": "Aufwärtstrend", "Aufwärtstrend unter Druck": "unter Druck"}.get(mr["zustand"], mr["zustand"])
    zeile = f"{mr['zustand']} seit {mr['seit']:%d.%m.%Y}" + (f" · Verteilungstage {max(dt.values())}" if dt else "")
    zeile += "".join(f" · {n} {w}" for n, w in (mr.get("zonen") or {}).items())
    return kachel("Markt", mr["ampel"], kurz, zeile,
                  "Marktrichtung nach O'Neil aus S&P 500 und Nasdaq: Verteilungstage (Index fällt mit mehr Volumen), "
                  "Erholungsversuch, Follow-Through-Day. Drei von vier Aktien folgen dem Markt; gekauft wird im "
                  "bestätigten Aufwärtstrend. Korrektur erst, wenn zu den Verteilungstagen die Zone (Market Profile) von "
                  "S&P 500 oder Nasdaq nach unten bricht – sonst bleibt es „unter Druck“ (wie IBD bei Indizes nahe am Hoch).")


def _k_phase(ph, ph_reihe, tvp):
    if not ph:
        return kachel("Phase", "grau", "–", "zu kurze Historie")
    seit = _seit(ph_reihe)
    return kachel("Phase", PHASE_AMPEL[ph], f"Phase {ph}",
                  PHASENTEXT[ph] + (f" seit {seit:%d.%m.%Y}" if seit is not None else "")
                  + f" · Trendvorlage {sum(tvp.values())} von 7",
                  "Phasen nach Weinstein: gekauft wird in Phase 2, geshortet in Phase 4. Vorlage = Minervinis "
                  "Trendvorlage (sieben Punkte zu Kurs und Durchschnitten); was fehlt, steht in „Lage und Plan“.")


AUSLOESER_HILFE = (
    "A Ausbruch: Ein Tag schließt jenseits des Zonenrahmens, und sein eigener Wertbereich liegt ganz außerhalb. "
    "Die Zone muss mindestens 3 Wochen alt sein. Die Front bricht.\n"
    "F Fortsetzung: Dasselbe aus einer jüngeren Zone (unter 3 Wochen), die selbst aus einem Lauf in dieselbe "
    "Richtung entstand, also eine Flagge. Kurze Rast, dann stößt die Truppe weiter vor.\n"
    "B bestätigt: Der Wertbereich der ganzen Woche liegt außerhalb der Zone. Die POC-Treppe macht eine neue Stufe. "
    "Neue Stellung bezogen.\n"
    "R Rücktest hält: Der Kurs kommt zurück an die Kante der verlassenen Zone (long: an ihr VAH), schließt aber "
    "jenseits davon. Der Gegner greift die alte Linie an und wird abgewiesen.\n"
    "S gescheitert: Ein Schluss liegt wieder im Wertbereich der verlassenen Zone. Das ist der Stopp. Der Durchbruch "
    "ist zurückgeschlagen.\n"
    "U Umkehr: Nach einem gescheiterten Bruch (S) verlässt der Kurs die junge Zone in die Gegenrichtung – Schluss "
    "jenseits des Rahmens, Tageswert ganz außerhalb (Dalton: gescheiterte Auktion). Die Verkäufer fanden unten keine "
    "Abnehmer – die Front dreht.\n"
    "Alle Buchstaben gelten in beide Richtungen, mit ↑ oder ↓ dahinter (zum Beispiel A↓ = Bruch nach unten).")

def _k_zone(erk):
    """Zonen-Kachel (Market Profile): eines von vier Wörtern – Balance, an der Schwelle, Ausbruch (Tag n), bestätigt –
    mit Richtung; darunter die Belege."""
    a = erk.get("mp")
    if not a:
        return kachel("Zone", "grau", "–", "keine 30-Minuten-Kerzen geladen",
                      "Die Zonen werden aus 30-Minuten-Kerzen gerechnet (Market Profile). Für diesen Titel fehlen sie; "
                      "werkzeuge/tpo_laden.py lädt sie.")
    z = a["zustand"]
    g_ = (erk.get("gelaende") or {}).get("aktuell") or {}
    art_ = (f'{g_["art"] if g_["art"] != "normal" else "Zone"} {zahl(g_["volumen"], 2)}×, {gelaende.lesart_text(g_)}'
            if g_.get("art") and g_.get("volumen") is not None else "")     # Gelände: Besatzung und Fährte der Zone
    return kachel("Zone", z["ampel"], z["wort"], " · ".join(([art_] if art_ else []) + z["belege"][:2]),
                  "Market Profile (Steidlmayer, Dalton) aus 30-Minuten-Kerzen. Die Zone besteht aus Wochen, deren "
                  "Wertbereich (70 % der Zeit) sich überlappt. Balance: Tageswerte wechseln, POC pendelt. An der Schwelle: "
                  "mindestens 3 der letzten 5 Tageswerte höher (tiefer), keiner ganz dagegen, Tages-POC steigt (fällt), "
                  "Kurs im oberen (unteren) Drittel des Wertbereichs. Ausbruch (A): Schluss jenseits des Rahmens und "
                  "Tageswert ganz außerhalb, Zone mindestens 3 Wochen alt (F bei jüngerer Zone nach einem Lauf in dieselbe "
                  "Richtung). Bestätigt (B): Wochenwert ganz außerhalb, die POC-Treppe macht eine Stufe. Gescheitert (S): "
                  "Schluss zurück im Wertbereich der verlassenen Zone.\n\n" + AUSLOESER_HILFE)


def _k_setup(erk, ph):
    """Setup-Kachel long/short: Seite nach Weinstein (Phase 1/2 long, 3/4 short), Ampeln der jeweiligen Meister."""
    w, sh = erk["werte"], erk.get("short")
    if sh:
        ab = sh["abstand_pct"]
        return kachel("Setup", "grün" if sh["setup"] else "gelb", f"short · {'Zone' if sh['art'] == 'Base' else sh['art']} "
                      f"{w.get('wochen')} W.", f"Auslöser {zahl(w['pivot'])} $ · {sh['lage'].replace('.', ',')}",
                      "Short nach Weinstein und O'Neil: Phase 3 oder 4, Kurs unter dem fallenden 30-Wochen-Durchschnitt, "
                      "Auslöser = Unterkante des Rahmens der Zone (A↓: Schluss darunter, Tageswert ganz darunter). "
                      "Verkaufszone bis −5 %. Grün = alle Regeln erfüllt: "
                      + "; ".join(f"{n} {'✓' if ok else '✗'} ({x})" for n, ok, x in sh["regeln"]))
    if erk["muster"]:
        ab = (erk["kurs"] / w["pivot"] - 1) * 100
        lage = ("in der Kaufzone" if 0 <= ab <= 5 else f"{zahl(ab, 1)} % über Pivot, ausgedehnt" if ab > 5
                else f"Kurs {zahl(-ab, 1)} % darunter")
        art = "Zone" if erk["muster"][0] == "Base" else erk["muster"][0]
        return kachel("Setup", "grün" if erk["kaufsetup"] else "gelb", f"long · {art} {w.get('wochen')} W.",
                      f"Pivot {zahl(w['pivot'])} $ · {lage}",
                      "Long nach O'Neil und Minervini: Pivot = Oberkante des Rahmens der Zone (A↑: Schluss darüber, "
                      "Tageswert ganz darüber), Kaufzone bis +5 %. Zone ab 3 Wochen = Base; jüngere Zone nach einem Lauf "
                      "nach oben = Flagge. Grün = Kaufsetup (alle Regeln erfüllt), gelb = eine Regel fehlt (siehe „Lage und Plan“).")
    grund = next((h for h in erk["hinweise"]), "keine reife Zone")
    return kachel("Setup", "grau", f"{erk.get('seite', 'long')} · keines", grund,
                  "Seite nach Weinstein: Phase 1 und 2 long, Phase 3 und 4 short.")


def _k_base(erk):
    w = erk["werte"]
    if erk["muster"] and erk["muster"][0] == "Umkehr":
        sig = (erk.get("mp") or {}).get("signale") or []
        s_ = next((x for x in reversed(sig) if x["art"] == "S"), None)
        u_ = next((x for x in reversed(sig) if x["art"] == "U"), None)
        zeile = (f"Bruch {s_['dir']} am {s_['tag']:%d.%m.} gescheitert" if s_ else "") + \
                (f" · Umkehr {u_['dir']} am {u_['tag']:%d.%m.}" if u_ else "")
        return kachel("Base", "grau", "keine – Umkehr", zeile,
                      "Keine Base: Die Zone ist erst eine Woche alt. Sie entstand aus einem Bruch, der gescheitert ist; "
                      "der Kurs hat sie in die Gegenrichtung verlassen (Umkehr nach einer gescheiterten Auktion, Dalton). "
                      "Eine Basennummer gibt es dafür nicht.")
    hist_ = erk.get("historie") or []
    zaehl = {a: sum(1 for b in hist_ if b["ausgang"] == a) for a in ("gelungen", "gescheitert", "offen")}
    bilanz = (f" Bilanz der verlassenen Zonen der letzten drei Jahre: {zaehl['gelungen']} gelungen, "
              f"{zaehl['gescheitert']} gescheitert, {zaehl['offen']} offen (gelungen = 20 % jenseits des Pivots, "
              f"bevor ein Schluss 8 % dagegen lag). Einzelheiten: Maus auf einen Zonenrahmen im Chart." if hist_ else "")
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


def _k_rs(erk, rs):
    rang = (erk.get("rs_rang") or (None, ""))[0]
    if rang is None:
        return kachel("Relative Stärke", rs[0], rs[1], rs[2], "")
    return kachel("Relative Stärke", "grün" if rang >= 90 else "gelb" if rang >= 80 else "rot", f"Rang {rang}",
                  f"12 Monate besser als {rang} % von {tausend(len(rs_rang.raenge()[0]))} Titeln"
                  + (" · Linie am Hoch" if rs[1] == "Hoch" else ""),
                  "RS-Rang 1–99 wie das RS-Rating von IBD: Kursentwicklung der letzten zwölf Monate, das jüngste "
                  "Quartal doppelt gewichtet, verglichen mit den Titeln unseres Reviers (größere US-Werte; IBD "
                  "vergleicht mit über 6.000 Aktien, unser Rang ist daher strenger). O'Neil kauft ab 80, am liebsten "
                  "ab 90.")


def tausend(n):
    return f"{int(n):,}".replace(",", ".")


def _k_absorption(erk, df):
    """Nehmen die Käufer das Angebot auf? Am rechten Rand der Base: Tiefs, Spanne und Volumen (gemessen, sie tragen die
    Ampel), dazu die Kauf- und Verkaufstage mit hohem Volumen als Beleg. Ohne Base dieselbe Frage am rechten Rand des
    Kurses (Zeichen, nicht gemessen)."""
    fu = erk.get("fuss") or {}
    tage = (f" · {fu['akk']} Kauf- gegen {fu['dist']} Verkaufstage" if fu.get("verhaeltnis") is not None else "")
    a = erk.get("absorption")
    wort = {"grün": "aufgenommen", "gelb": "teilweise", "rot": "nicht aufgenommen"}
    if erk["muster"] and a:
        tiefs = "steigen" if a["steigend"] else "halten" if a["halten"] else "fallen"
        tiefe = a["eng"] / a["verhaeltnis"] if a["verhaeltnis"] else None
        t = a["trocken"]
        zeile = (f"Tiefs {tiefs} · Spanne 2 Wochen {zahl(a['eng'], 0)} %" + (f" (Base {zahl(tiefe, 0)} %)" if tiefe else "")
                 + (f" · Volumen {zahl(t, 1)}-fach" if t is not None else "") + tage)
        return kachel("Absorption", a["ampel"], wort[a["ampel"]], zeile,
                      "Nehmen die Käufer das Angebot der Base auf? Ja, wenn am rechten Rand die Tiefs halten oder steigen, "
                      "die Spanne der letzten zwei Wochen auf ein Drittel der Base schrumpft (oder unter 5 % liegt) und das "
                      "Volumen unter dem 50-Tage-Schnitt bleibt (bis 0,8-fach grün). Kauf- und Verkaufstage: Volumen "
                      "mindestens 1,25-fach, Schluss höher bzw. tiefer (O'Neil, Minervini).")
    l, v = df["Low"].to_numpy(float), df["Volume"].to_numpy(float)
    if len(l) < 60:
        return kachel("Absorption", "grau", "–", "zu kurze Historie", "")
    t3 = [l[-30:-20].min(), l[-20:-10].min(), l[-10:].min()]
    halten = t3[1] >= t3[0] * 0.99 and t3[2] >= t3[1] * 0.99
    steigen = halten and t3[2] > t3[0] * 1.01
    vol = v[-10:].mean() / v[-60:-10].mean()
    ampel = "grün" if halten and vol <= 0.8 else "rot" if not halten and vol > 1.0 else "gelb"
    return kachel("Absorption", ampel, wort[ampel],
                  f"Tiefs {'steigen' if steigen else 'halten' if halten else 'fallen'} · Volumen {zahl(vol, 1)}-fach"
                  + (tage + " seit dem Hoch" if tage else ""),
                  "Ohne Base: Halten die Tiefs der letzten sechs Wochen, und wird das Volumen der letzten zwei Wochen "
                  "ruhiger als der 50-Tage-Schnitt? Erst dann kann sich eine Base bilden. Zeichen, ohne Base nicht auf "
                  "dem Prüfstand gemessen.")


def _k_ausbruch(erk):
    fu = erk.get("fuss") or {}
    if not erk["muster"]:
        hist = erk.get("historie") or []
        x = hist[-1].get("vol_ausbruch") if hist else None
        if x is None:
            return kachel("Ausbruch", "grau", "keiner", "keine Base, kein früherer Ausbruch in drei Jahren", "")
        return kachel("Ausbruch", _vol_ampel(x), f"vorheriger {zahl(x, 1)}-fach",
                      f"Volumen am {erk['df_index'][hist[-1]['ausbruch']]:%d.%m.%Y} · {hist[-1]['ausgang']}",
                      "Zurzeit keine Base und damit kein Ausbruch. Gezeigt wird das Volumen am letzten Ausbruch gegen den "
                      "50-Tage-Schnitt und wie er ausging. Grün: über dem Schnitt (Minervini); O'Neil verlangt 40–50 % "
                      "darüber.")
    a = fu.get("ausbruch")
    hilfe = ("Volumen am Ausbruchstag gegen den 50-Tage-Schnitt: grün darüber (Minervini: mehr als üblich), rot darunter. "
             "O'Neil verlangt 40–50 % darüber. Spanne: wie weit der Kurs am Ausbruchstag lief, gemessen an der "
             "durchschnittlichen Tagesspanne (ATR, 14 Tage) – über 1 × ATR ein Vorstoß mit Kraft.")
    if a:
        return kachel("Ausbruch", a["ampel"], f"{zahl(a['faktor'], 1)}-faches Volumen",
                      f"am {erk['df_index'][a['index']]:%d.%m.%Y}"
                      + (" · " + fussabdruck.spanne_text(a["atr"]) if a.get("atr") else "")
                      + ("" if a["schluss_darueber"] else " · Schluss unter Pivot"),
                      hilfe)
    return kachel("Ausbruch", "grau", "noch nicht",
                  f"über {zahl(erk['werte']['pivot'])}\u00a0$ mit mehr als {_mio(fu['noetig'])} Stück" if fu.get("noetig")
                  else "Pivot noch nicht überschritten", hilfe)


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


def _k_fundament(fund, ph):
    if not fund:
        return kachel("Fundament", "grau", "–", "keine Daten", "")
    gruen = sum(1 for a, _ in fund["punkte"].values() if a == "grün")
    rot = sum(1 for a, _ in fund["punkte"].values() if a == "rot")
    ampel = "grün" if gruen >= 5 and rot == 0 else "rot" if rot >= 3 else "gelb"
    def letzt(name):
        a_, txt = fund["punkte"].get(name, ("grau", ""))
        return None if a_ == "grau" else txt.split(" / ")[-1].split(" (")[0]
    teile = [f"{n} {x}" for n, x in (("Gewinn", letzt("Quartalsgewinn zum Vorjahr")), ("Umsatz", letzt("Umsatz"))) if x]
    zeile = (" · ".join(teile) + " zum Vorjahr") if teile else "Gewinn, Umsatz, Marge, Schätzungen"
    if ampel == "grün" and _widerspruch(ph):
        ampel, zeile = "gelb", "Widerspruch: Zahlen stark, Kurs fällt"
    return kachel("Fundament", ampel, f"{gruen} von 7 grün", zeile,
                  "Sieben Prüfpunkte zu Gewinn, Umsatz, Marge und Schätzungen (Liste weiter unten). "
                  + (_widerspruch(ph) if _widerspruch(ph) else ""))


def _gelaende_karte(erk):
    """Karte „Gelände“: alle Zeichen und der Steckbrief der letzten Zonen (Volumen, Druck, Art, Lesart)."""
    import gelaende
    g = erk.get("gelaende")
    if not g:
        return ""
    zeilen = "".join(ampelzeile(f"{t_}: {x_}", a_, "") for a_, t_, x_ in g["zeichen"])
    kopf = ("<tr>" + "".join(f'<th style="text-align:left;padding:4px 8px;color:{TEXT_3};font-weight:500">{h}</th>'
                             for h in ("Zone", "Spanne $", "Wert (VAL–VAH)", "Zeit-POC", "Volumen-POC ◆",
                                       "Lage Zeit / ◆", "Volumen", "Tage V/K", "Art", "Lesart")) + "</tr>")
    reihen = ""
    for z in reversed(g["zonen"][-6:]):
        reihen += ("<tr>" + "".join(f'<td style="padding:4px 8px;border-top:1px solid {RAND}">{c}</td>' for c in (
            f'{z["beginn"]:%d.%m.}–{z["ende"]:%d.%m.%y}', f'{zahl(z["tief"], 0)}–{zahl(z["hoch"], 0)}',
            f'{zahl(z["val"])}–{zahl(z["vah"])}', zahl(z["poc"]), zahl(z["vpoc"]) if z.get("vpoc") else "–",
            (f'{zahl(z["lage_zeit"] * 100, 0)} % / {zahl(z["lage_vol"] * 100, 0)} %' + (" ◆" if z.get("raute") else ""))
            if z.get("lage_vol") is not None else "–",
            f'{zahl(z["volumen"], 2)} ×' if z.get("volumen") else "–", f'{z["ab"]}/{z["auf"]}', t(z.get("art") or "–"),
            t((z["zeichen"] + " · " if z.get("zeichen") else "") + gelaende.lesart_text(z)))) + "</tr>")
    tabelle = (f'<div style="overflow-x:auto"><table style="border-collapse:collapse;font-size:13px;width:100%">{kopf}{reihen}'
               f'</table></div>')
    hinweis = (f'<div style="font-size:13px;color:{TEXT_2}">Volumen = mittleres Tagesvolumen der Zone ÷ Median der 12 Monate '
               f'bis zu ihrem Ende (Festung ab 1,2 ×, Wartesaal bis 0,9 ×). Tage V/K = Tage mit Verkaufs- bzw. Kaufdruck '
               f'(O\'Neil: Schluss ±0,2 % bei mehr Volumen als am Vortag). Volumen-POC (◆) aus den 30-Minuten-Kerzen der Zone; '
               f'Lage = Höhe von Zeit-POC und ◆ in der Zonenspanne (0 % = Tief, 100 % = Hoch). Lesart aus den Tagen; '
               f'„◆ bestätigt“, wenn die Raute mindestens 20 % neben dem Zeit-POC liegt und die Richtung passt (Zeit oben, '
               f'Geschäft unten + Verkaufsdruck = Verteilung; Geschäft oben + Kaufdruck = Akkumulation), sonst „nur Tage“.</div>')
    return karte(zeilen + tabelle + hinweis, "Gelände · Zonen und Volumen")


def _k_gelaende(erk, ph):
    """Kachel „Gelände“ (05.11.2026, ersetzt „Freie Bahn“): Zone, in der der Kurs steht (Festung/Wartesaal, Lesart),
    Raum bis zur nächsten Festung in Laufrichtung, Überhang. Im Hinweis bleibt alles, was die Freie Bahn wusste:
    Wendepunkte der letzten drei Jahre, alte Pivots, AVWAP ab dem 52-Wochen-Hoch, doppelt/dreifach, dünn/verdeckt."""
    g = erk.get("gelaende")
    fb = erk.get("bahn") or {}
    if not g:
        return kachel("Gelände", "grau", "–", "keine Zonen (30-Minuten-Kerzen fehlen)", "")
    zei = {t_: (a_, x_) for a_, t_, x_ in g["zeichen"]}
    z = g["aktuell"]
    import gelaende
    wert = (z.get("zeichen") or (f'{z["art"]}, {gelaende.lesart_text(z)}' if z.get("art") else "Zone ohne Volumen"))
    raum = zei.get("Lawinengefahr ↓") if (erk.get("short") or erk.get("seite") == "short") else zei.get("Freie Bahn ↑")
    ampel = zei.get("Zone", ("grau", ""))[0]
    if ampel == "grau" and raum:
        ampel = raum[0]
    zeile = (raum[1] if raum else "") + (f' · Überhang {zei["Überhang"][1].split(" –")[0]}' if "Überhang" in zei else "")
    L, S = fb.get("long") or {}, fb.get("short") or {}
    marken = (("\n\nFrühere Marken: " + (f'Widerstand {zahl(L["marke"])} $ ({L["art"]})' if L.get("marke") else "kein Widerstand")
               + " · " + (f'Unterstützung {zahl(S["marke"])} $ ({S["art"]})' if S.get("marke") else "keine Unterstützung"))
              if fb else "")
    return kachel("Gelände", ampel, wert, zeile,
                  "Zonen des Market Profile mit ihrem Volumen (Auction Market Theory): Festung = viel Zeit und viel Volumen "
                  "(feste Stellung), Wartesaal = viel Zeit, wenig Volumen (schwach), Niemandsland = kaum Handel (der Kurs "
                  "läuft durch). Lesart aus O'Neils Verteilungs- und Akkumulationstagen; Lawinenhang = Wartesaal mit "
                  "Verteilung, stille Akkumulation = Wartesaal mit Akkumulation (Minervini). Freie Bahn ↑ / "
                  "Lawinengefahr ↓ = schwaches Gelände (Wartesaal, Niemandsland) bis zur nächsten Festung bzw. zum "
                  "nächsten Volumenknoten, in % und in ATR; Überhang = Festungen bis +25 % über "
                  "dem Kurs (O'Neil: overhead supply). Zeichen, kein Filter." + marken)


def _k_ereignis(df, gewinne, fund):
    """Die letzten Zahlen als Ereignis (Auction Market Theory: das Ereignis, das die Balance bricht), gelesen nach
    O'Neils Kursreaktion: Tag 1, Tage 2–10 und Erholung; gute Zahlen, die der Kurs hält, gegen „gute Nachricht,
    schlechte Reaktion“."""
    r = _reaktion_zeilen(df, gewinne)
    if not r:
        return kachel("Ereignis", "grau", "–", "keine Gewinnmeldung im Kurszeitraum", "")
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
    return kachel("Ereignis", ampel, wert, zeile,
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


def _kacheln(erk, ph, ph_reihe, tvp, fund, rs, df, rd, fd, mr, gewinne):
    """Die dreizehn Kacheln der Titelseite: bei jedem Titel dieselben, in derselben Reihenfolge, gleich groß.
    Fehlt ein Wert, steht ein grauer Punkt mit dem Grund. Erklärung und Zahlen stehen im Hinweis (Maus darauf)."""
    # Reihenfolge der Knoten: Erlaubnis, Führung, Reife, Auslöser, Raum, Treibstoff
    k = [_k_markt(mr), _k_phase(ph, ph_reihe, tvp), _k_zone(erk),
         _k_setup(erk, ph),   # Erlaubnis
         _k_rs(erk, rs), _k_branche(df, rd),                           # Führung
         _k_base(erk), _k_absorption(erk, df),                        # Reife
         _k_ausbruch(erk), _k_ereignis(df, gewinne, fund), _k_zahlen(fd, fund),   # Auslöser
         _k_gelaende(erk, ph),                                         # Raum
         _k_fundament(fund, ph)]                                       # Treibstoff
    return (f'<section aria-label="Lage in fünf Sekunden" style="display:grid;'
            f'grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;flex:1 1 600px">{"".join(k)}</section>')


ZYKLUS = [(1, "Boden"), (2, "Aufwärts"), (3, "Gipfel"), (4, "Abwärts")]


def _marktzeichen(mr):
    """Zeichen „Markt in Korrektur“ / „Markt unter Druck“ (O'Neil: 3 von 4 Aktien folgen dem Markt) – kein Filter."""
    if not mr or mr["ampel"] == "grün":
        return None
    return (mr["ampel"], f'Markt {"in Korrektur" if mr["zustand"] == "Korrektur" else "unter Druck"} seit '
                         f'{mr["seit"]:%d.%m.%Y} – 3 von 4 Aktien folgen dem Markt (O\'Neil)')


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


def _stimmung_punkte(tk, df, ph_reihe, etf, branche=None):
    """Titel und seine Branche (sonst sein Sektor) als Punkte der Stimmungskurve, je mit dem Stand vor 4 Wochen."""
    punkte = []
    zone = phasen_modul.stimmungszone(df, ph_reihe)
    if zone:
        punkte.append({"zone": zone, "vorher": phasen_modul.stimmungszone(df, ph_reihe, df.index[-21]),
                       "name": tk, "farbe": "#7DB4FF"})
    bdf = rudel.branche_kurse(branche) if branche else None
    if bdf is not None and len(bdf) >= 300:
        bph = phasen_modul.phasen(bdf)
        bzone = phasen_modul.stimmungszone(bdf, bph)
        if bzone:
            punkte.append({"zone": bzone, "vorher": phasen_modul.stimmungszone(bdf, bph, bdf.index[-21]),
                           "name": f"Branche {namen_de.branche(branche)}", "farbe": "#D2A8FF"})
    elif etf:
        try:
            sdf = daten.kurse(etf)
            sph = phasen_modul.phasen(sdf)
            szone = phasen_modul.stimmungszone(sdf, sph)
            if szone:
                punkte.append({"zone": szone, "vorher": phasen_modul.stimmungszone(sdf, sph, sdf.index[-21]),
                               "name": f"{sektoren.SEKTOREN[etf]} ({etf})", "farbe": "#D2A8FF"})
        except Exception:
            pass
    return punkte


def _phase_zyklus(tk, df, ph, ph_reihe, krit, etf, branche=None):
    """Phase und Zyklus: wo Titel und Branche auf der Stimmungskurve stehen (Bild), die sechs Merkmale eines
    Aufwärtstrends mit ✓/✗ und die Warnzeichen der Phase."""
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
    punkte = _stimmung_punkte(tk, df, ph_reihe, etf, branche)
    bild = ""
    if punkte:
        zeile = " · ".join(f'{p["name"]}: {p["zone"]}' + (f' (vor 4 Wochen {p["vorher"]})' if p["vorher"] and
                                                           p["vorher"] != p["zone"] else "") for p in punkte)
        legende_text = (f'Aus Phase, Überdehnung und Volumen. Überhitzung: Kurs mindestens '
                        f'{phasen_modul.UEBERDEHNT_GD200 * 100:.0f} % über dem GD200 oder mindestens '
                        f'{phasen_modul.CLIMAX_ANSTIEG * 100:.0f} % Anstieg in drei Wochen; Kapitulation: mindestens '
                        f'{phasen_modul.KAPITULATION_RUECKGANG * 100:.0f} % unter dem Hoch und ein Abwärtstag mit '
                        f'{phasen_modul.KAPITULATION_VOLUMEN:.0f}-fachem Volumen. Hohler Punkt: Stand vor 4 Wochen.')
        bild = (f'<div style="font-size:15px;font-weight:500">{t(zeile)}</div>' + kurve(punkte)
                + f'<div style="font-size:13px;color:{TEXT_3};line-height:1.5">{t(legende_text)}</div>')
    k = krit["kriterien"]
    merkmale = (f'<div style="font-size:15px;font-weight:600;padding-top:6px">{sum(k.values())} von 6 Merkmalen eines '
                f'Aufwärtstrends erfüllt</div>' + "".join(ampelzeile(n, "grün" if ok else "rot", "") for n, ok in k.items())
                + "".join(ampelzeile(w, "rot", "") for w in krit.get("warnungen", [])))
    kopf = (f'<p style="margin:0;font-size:14px;color:{TEXT_2};line-height:1.6">'
            f'{t((f"Phase {ph}: {PHASENTEXT[ph]}. " if ph else "") + satz)}</p>')
    return karte(kopf + bild + merkmale, "Phase und Zyklus")


RS_BILDER = [("beide steigen", "Führer im Markt und in seinem Sektor"),
             ("gegen S&P 500 fällt, gegen Sektor steigt", "der Sektor ist schwach, der Titel darin einer der Besten"),
             ("gegen S&P 500 steigt, gegen Sektor fällt", "läuft nur mit dem starken Sektor mit, darin kein Führer"),
             ("beide fallen", "schwächer als Markt und Sektor")]


def _rs_lesart(df, index, sek, etf):
    """Hinweiskasten beim Überfahren des RS-Feldes im Chart: das heutige Bild (Richtung der letzten
    3 Monate; unter ±2 % gilt eine Linie als seitwärts) und die vier Bilder. Die Zone liegt genau über
    dem RS-Feld des Charts (SVG-Koordinaten y 600–724 von 760, x ab 64 von 1344)."""
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
    return (f'<div class="hinweis-zone" style="position:absolute;left:{64 / 1344 * 100:.2f}%;right:{24 / 1344 * 100:.2f}%;'
            f'top:{600 / 760 * 100:.2f}%;height:{124 / 760 * 100:.2f}%">{tip}</div>')


def _trendvorlage(df):
    """Die sieben Punkte der Trendvorlage (ohne RS-Rating): Kurzname → erfüllt?"""
    c, h, l = (df[s].to_numpy(float) for s in ("Close", "High", "Low"))
    if len(c) < 260:
        return {}
    g50, g150, g200 = c[-50:].mean(), c[-150:].mean(), c[-200:].mean()
    g200_vor = c[-222:-22].mean()
    k = c[-1]
    return {"Kurs über GD150/200": k > g150 and k > g200, "GD150 über GD200": g150 > g200,
            "GD200 steigt": g200 > g200_vor, "GD50 über GD150/200": g50 > g150 and g50 > g200,
            "Kurs über GD50": k > g50, "30 % über Tief": k >= 1.30 * l[-252:].min(),
            "höchstens 25 % unter Hoch": k >= 0.75 * h[-252:].max()}


def _fehlt_zum_kaufsetup(erk, ph, tv=None):
    """Gründe, warum ein erkanntes Muster kein Kaufsetup ist (dieselben Bedingungen wie in der Erkennung)."""
    w, gruende = erk["werte"], []
    if ph and ph != 2:
        gruende.append(f"Phase {ph} statt Phase 2")
    if tv is not None and tv < 7:
        gruende.append(f"Trendvorlage nur {tv} von 7")
    if not erk["muster"]:
        gruende.append("keine Base")
    if (w.get("korrektur_x_markt") or 0) > 3:
        gruende.append(f'Korrektur {zahl(w["korrektur_x_markt"], 1)}-fach zum Markt (Buch: höchstens 2–3-fach)')
    if (w.get("tiefe_pct") or 0) > 50:
        gruende.append(f'Base {zahl(w["tiefe_pct"], 0)} % tief (über 50 %)')
    gruende += [h for h in erk["hinweise"] if h.startswith("Daten gestört")]
    return gruende


def _lagebeurteilung(ph, erk, tv, fund):
    saetze = [f"Phase {ph}: {PHASENTEXT.get(ph, '')}." if ph else ""]
    if erk.get("mp"):
        z_ = erk["mp"]["zustand"]
        saetze.append(f"Zone: {z_['wort']} ({z_['belege'][0]}).")
    sh_ = erk.get("short")
    if sh_:
        fehlt_ = [n for n, ok, _ in sh_["regeln"] if not ok]
        saetze.append(f"Seite short (Phase {ph}): Auslöser {zahl(erk['werte']['pivot'])} $ (Unterkante der Zone), "
                      f"{sh_['lage'].replace('.', ',')}. " + ("Alle Regeln für ein Short-Setup sind erfüllt."
                      if sh_["setup"] else "Kein Short-Setup: " + ", ".join(fehlt_) + " fehlt."))
        return " ".join(s for s in saetze if s)
    if erk["muster"]:
        w = erk["werte"]
        fh = form_hinweis(erk["muster"])
        saetze.append(f'Erkannt: {basename(erk["muster"])} Nr. {w.get("basenzahl", "–")}'
                      + (f' ({fh.replace("Form-Hinweis: ", "Form: ")})' if fh else "") + f', Pivot {zahl(w["pivot"])} $.')
    else:
        saetze.append("Keine kaufbare Base erkannt.")
    if erk["kaufsetup"]:
        saetze.append("Alle Bedingungen für ein Kaufsetup sind erfüllt.")
    else:
        gruende = _fehlt_zum_kaufsetup(erk, ph, tv)
        saetze.append("Kein Kaufsetup: " + ", ".join(gruende) + "." if gruende else "Kein Kaufsetup.")
    if fund:
        rot = [n for n, (a, _) in fund["punkte"].items() if a == "rot"]
        if rot:
            saetze.append("Fundament rot bei: " + ", ".join(rot) + ".")
        gruen = sum(1 for a, _ in fund["punkte"].values() if a == "grün")
        if gruen >= 5 and not rot and _widerspruch(ph):
            saetze.append(f"Gegenprobe: Die Zahlen sind stark ({gruen} von 7 grün), der Kurs steht aber in Phase {ph}. "
                          "Der Markt nimmt eine Abschwächung vorweg; die Zahlen allein sind kein Kaufgrund.")
    return " ".join(s for s in saetze if s)


WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _steckbrief(tk, sb):
    """Was die Firma macht, auf Deutsch; solange keine deutsche Fassung vorliegt, die ersten zwei Sätze von Yahoo."""
    de = namen_de.beschreibung(tk)
    if de:
        return f'<div style="font-size:14px;color:{TEXT_2};line-height:1.6;max-width:900px">{t(de)}</div>'
    text = (sb.get("beschreibung") or "").strip()
    if not text:
        return ""
    saetze = [s.strip() for s in text.replace("Inc.", "Inc").split(". ") if s.strip()]
    kurz = ". ".join(saetze[:2]).rstrip(".") + "."
    return (f'<div style="font-size:14px;color:{TEXT_2};line-height:1.6;max-width:900px">{t(kurz)} '
            f'<span style="color:{TEXT_3}">(noch englisch – die deutsche Fassung ergänzt der Nachtlauf)</span></div>')


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
    if termin is not None and len(termin) and termin["datum"].iloc[0]:
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


def _noetig_text(erk):
    fu = erk.get("fuss") or {}
    a = fu.get("ausbruch")
    if a:
        return f' (am Ausbruch {zahl(a["faktor"], 1)}-fach)'
    return f' (mindestens {_mio(fu["noetig"])} Stück)' if fu.get("noetig") else ""


def _szenario(df, erk, ph, mr=None, rd=None, gewinne=None):
    """Wann ein Long- (oder Short-) Szenario aktiv wird – mit Kursmarken aus den Regeln. Liefert Inhalt und
    Rahmenfarbe für die Karte „Lage und Plan“."""
    c, h, l = df["Close"], df["High"], df["Low"]
    k = float(c.iloc[-1])
    g50, g150, g200 = (float(c.iloc[-n:].mean()) for n in (50, 150, 200))
    tief52, hoch52 = float(l.iloc[-252:].min()), float(h.iloc[-252:].max())
    w = erk["werte"]
    if erk["kaufsetup"]:
        p = w["pivot"]
        lage = w.get("kontraktionen_lage") or []
        # Stopp: unter dem Tief der letzten Kontraktion (Minervini), wenn es unter dem Pivot liegt; sonst die
        # Verlustgrenze 8 % unter dem Kaufpunkt (O'Neil) – beides offen benannt
        tief_k = float(df["Low"].iloc[lage[-1][1]]) if lage else None
        if erk.get("mp") and "vah" in w and p * 0.92 <= w["vah"] < p:
            # Market Profile: der Ausbruch ist gescheitert, sobald ein Schluss zurück im Wertbereich der Zone liegt
            stopp, stopp_text = w["vah"], "bei einem Schluss unter dem VAH der Zone (zurück in der Balance)"
        elif tief_k is not None and tief_k < p:
            stopp, stopp_text = tief_k, "unter dem Tief der letzten Kontraktion"
        else:
            stopp, stopp_text = p * 0.92, "an der Verlustgrenze 8 % unter dem Kaufpunkt (O'Neil)"
        abstand = (k / p - 1) * 100
        markt = f' ⚠ {t(_marktzeichen(mr)[1])}.' if _marktzeichen(mr) else ""
        regel = rudelkarte.gruppenregel(rd, mr, ph, "long")
        if abstand > 5:
            # Ausbruch erfolgt, Kurs über der Kaufzone: nicht nachlaufen (Minervini, O'Neil)
            return (f'<p style="margin:0;font-size:16px;line-height:1.65">🟡 <b>Ausgebrochen, Kurs ausgedehnt:</b> '
                         f'{zahl(k)} $ liegt {zahl(abstand, 1)} % über dem Pivot {zahl(p)} $ und damit über der Kaufzone '
                         f'(bis {zahl(p * 1.05)} $). Kein Nachkauf: Einstieg erst bei einem Rücksetzer in die Kaufzone '
                         f'oder aus der nächsten Base. Wer seit dem Ausbruch dabei ist: Stopp {stopp_text} bei '
                         f'{zahl(stopp)} $.{markt}</p>' + regel, GELB)
        return (f'<p style="margin:0;font-size:16px;line-height:1.65">🟢 <b>Long-Szenario aktiv:</b> Kauf über dem '
                     f'Pivot {zahl(p)} $, Kaufzone bis {zahl(p * 1.05)} $. Stopp {stopp_text} '
                     f'bei {zahl(stopp)} $ ({_vorzeichen((stopp / p - 1) * 100)} % vom Pivot). Ausbruch mit Volumen '
                     f'deutlich über dem 50-Tage-Schnitt{_noetig_text(erk)}.{markt}</p>' + regel, GRUEN)
    marken = []                                   # Kursleiter: die nächste Hürde zuerst
    if k < max(g150, g200):
        marken.append((max(g150, g200), "Kurs über GD150 und GD200"))
    if k < 1.30 * tief52:
        marken.append((1.30 * tief52, "mindestens 30 % über dem 52-Wochen-Tief"))
    if k < 0.75 * hoch52:
        marken.append((0.75 * hoch52, "höchstens 25 % unter dem 52-Wochen-Hoch"))
    if k < g50:
        marken.append((g50, "GD50 zurückerobert"))
    leiter = [f"{zahl(preis)} $ ({_vorzeichen((preis / k - 1) * 100)} %) · {text}" for preis, text in sorted(marken)]
    bedingungen = []
    if ph and ph != 2:
        bedingungen.append("alle sechs Merkmale eines Aufwärtstrends erfüllt sind, einschließlich steigendem GD200")
    if not erk["muster"]:
        bedingungen.append("sich eine Base von mindestens 3 Wochen mit kleiner werdenden Rücksetzern und "
                           "versiegendem Volumen bildet")
    elif not erk["kaufsetup"]:
        if k >= w["pivot"]:
            # Ausbruch schon erfolgt: dann fehlt nicht der Ausbruch, sondern eine andere Bedingung – die nennen
            fehlt = _fehlt_zum_kaufsetup(erk, ph)
            bedingungen.append(f'der Ausbruch über den Pivot {zahl(w["pivot"])} $ ist schon erfolgt '
                               f'(Kurs {zahl((k / w["pivot"] - 1) * 100, 1)} % darüber); kein Kaufsetup, weil: '
                               + (", ".join(fehlt) if fehlt else "die Trendvorlage nicht erfüllt ist")
                               + " – Einstieg erst aus der nächsten Base")
        else:
            bedingungen.append(f'der Kurs über den Pivot {zahl(w["pivot"])} $ ausbricht, solange die übrigen Bedingungen erfüllt sind')
    liste = lambda zeilen: (f'<ul style="margin:0;padding-left:22px;font-size:15px;line-height:1.7">'   # noqa: E731
                            + "".join(f"<li>{t(z)}</li>" for z in zeilen) + "</ul>")
    ausgebrochen = bool(erk["muster"] and not erk["kaufsetup"] and k >= w["pivot"] and not leiter)
    kopf = ("🟡 <b>Ausgebrochen, aber kein Kaufsetup</b>" if ausgebrochen
            else "🟢 <b>Long-Szenario wird aktiv, wenn</b>")
    teile = [f'<p style="margin:0;font-size:16px;line-height:1.65">{kopf}</p>']
    if leiter:
        teile.append(f'<p style="margin:0;font-size:15px;color:{TEXT_2}">der Kurs diese Marken überwindet '
                     f'(Abstand vom heutigen Schluss, die nächste Hürde zuerst):</p>' + liste(leiter))
    if bedingungen:
        teile.append(f'<p style="margin:0;font-size:15px;color:{TEXT_2}">{"und wenn außerdem" if leiter else ""}'
                     f'</p>' + liste(bedingungen))
    teile.append(rudelkarte.gruppenregel(rd, mr, ph, "long"))
    if ph in (3, 4) or erk.get("seite") == "short":
        zr = _reaktion_zeilen(df, gewinne)
        if zr and zr["prozent"] > 0 and k >= zr["vor"] and len(df) - 1 - df.index.get_loc(zr["tag"]) <= 63:
            teile.append(f'<p style="margin:0;font-size:15px;color:#E3B341">⚠ Zahlen am {zr["tag"]:%d.%m.} angenommen '
                         f'(Tag 1 +{zahl(zr["prozent"], 1)} %, Kurs über {zahl(zr["vor"])} $ vor den Zahlen) – O\'Neil '
                         f'shortet nicht gegen eine positive Zahlenreaktion.</p>')
        teile.append(_short_seite(df, erk, ph, rd, mr))
    return "".join(teile), BLAU


def _avwap_karte(df, erk):
    """AVWAP-Liste (aus dem SEPA-Scanner): feste Anker in der Zone, alle zugleich; Ampel über allen / dazwischen / unter."""
    al = avwap_modul.liste(df, erk)
    k = float(df["Close"].iloc[-1])
    zeilen = "".join(ampelzeile(f'{x["name"]} ({x["tag"]:%d.%m.%Y})', "grün" if x["abstand"] >= 0 else "rot",
                                f'{zahl(x["wert"])} $ · Kurs {_vorzeichen(x["abstand"])} %') for x in al["anker"])
    kopf = ampelzeile(f'Kurs {zahl(k)} $ über {al["ueber"]} von {al["von"]} AVWAP', al["ampel"],
                      "über allen: Käufer aller Anker im Gewinn, kein Angebot von oben · dazwischen: Kampfzone · unter "
                      "allen: jeder Anstieg trifft auf Verkäufer, die raus wollen (für Shorts umgekehrt)",
                      "Anchored VWAP = volumengewichteter Durchschnittspreis ab dem Anker: der Einstand aller, die "
                      "seitdem gekauft haben. Anker: Beginn, Tief, größtes Volumen und Hoch der aktuellen Zone sowie das "
                      "52-Wochen-Hoch.")
    return karte(kopf + zeilen, "AVWAP-Liste")


def _short_seite(df, erk, ph, rd, mr):
    """Short-Seite nach Weinstein und O'Neil: drei Einstiege mit Kursmarke und Stopp, O'Neils Regeln, Gruppenregel."""
    ein = short_seite.einstiege(df, erk, ph)
    da = [n for n, a, _ in ein if a == "grün"]
    kopf = (f'<p style="margin:0;font-size:16px;line-height:1.65">🔴 <b>Short-Seite:</b> '
            + (f'{" · ".join(da)} liegt vor.' if da else "kein Einstieg liegt vor – Marken für den Fall der Fälle:")
            + '</p>')
    zeilen = "".join(ampelzeile(n, a, x) for n, a, x in ein)
    import atr
    ue = atr.ueberdehnung(df)
    if ue:                                       # Überdehnung: der Boden, auf dem ein Bruch gedeiht (Zeichen)
        # über dem GD50 überdehnt: günstig für Short (grün); unter dem GD50 überdehnt: der Bruch ist gelaufen (rot)
        a_ue = {"rot": "grün", "grün": "grau"}.get(ue[0], ue[0]) if ue[2] >= 0 else ue[0]
        zeilen += ampelzeile(f"Überdehnung: {ue[1]}" + (" – nicht nachjagen" if ue[2] < 0 and ue[0] == "rot" else ""),
                             a_ue, "Abstand vom 50-Tage-Durchschnitt in ATR. Weit über dem GD50 ist eine Überdehnung für "
                                   "die Short-Seite günstig (grün ab 6 × ATR, gelb ab 4); weit darunter ist der Bruch "
                                   "schon gelaufen – ein Zeichen, kein Einstieg.")
    g_ = erk.get("gelaende")
    if g_:
        z_ = g_["aktuell"]
        if z_.get("lesart") == "Verteilung":
            zeilen += ampelzeile(f'Gelände: Zone mit {gelaende.lesart_text(z_)} ({z_.get("zeichen") or z_.get("art")}) – die späten Käufer '
                                 f'werden zum Angebot', "grün", "O'Neil: Verteilungstage; Auction Market Theory: Akzeptanz "
                                                                   "wird geräumt")
        h_ = g_["halt"]
        zeilen += ampelzeile(("Gelände darunter: " + (f'{zahl(g_["raum_ab"] * 100, 1)} % bis {h_[1]} bei {zahl(h_[0])} $'
                                                        if h_ else "keine Festung darunter – Niemandsland")),
                             "grün" if not h_ or g_["raum_ab"] >= 0.10 else "gelb" if g_["raum_ab"] >= 0.05 else "rot",
                             "Raum bis zur nächsten festen Stellung darunter – so weit kann ein Bruch laufen")
        if g_["raum_auf"] is not None and g_["raum_auf"] >= 0.08:
            zeilen += ampelzeile(f'Squeeze-Raum: {zahl(g_["raum_auf"] * 100, 1)} % ohne feste Stellung darüber', "gelb",
                                 "Scheitert der Bruch, steigt der Kurs schnell durch Niemandsland – Stopp knapp setzen")
    regeln = "".join(ampelzeile(n, a, x, "O'Neil: Shorts nur in früheren Führern, rund 5–7 Monate nach dem Top, wenn "
                                         "die ersten Erholungen gescheitert sind, und nur in liquiden Titeln.")
                     for n, a, x in short_seite.oneil_regeln(df))
    return (kopf + zeilen + f'<p style="margin:8px 0 0;font-size:15px;color:{TEXT_2}">Regeln nach O\'Neil:</p>' + regeln
            + rudelkarte.gruppenregel(rd, mr, ph, "short"))


def _vol_ampel(x):
    return "grün" if x > 1.0 else "rot"         # über dem 50-Tage-Schnitt (05.11.2026)


def tv_link(tk):
    """Adresse des Titels in TradingView (mit Börse, z. B. NYSE:HWM) – für den Knopf über dem Chart."""
    return f"https://www.tradingview.com/chart/?symbol={_tv_symbol(tk)}"


def chartkarte(z, ebene="Tag", ausschnitt=None, kurz=()):
    """Karte mit Legende und Chart aus dem Zwischenstand von seite_titel; billig, wird bei jedem Knopfdruck neu
    gezeichnet (Zeitebene, Ausschnitt, GD10/GD20), ohne die Seite neu zu rechnen."""
    return seite(karte(f'<div style="display:flex;flex-wrap:wrap;gap:20px">{legende(z["erk"], ebene, kurz)}</div>'
                       + f'<div style="position:relative">{chart(z["df"], ebene, z["erk"], z["ph_reihe"], z["index"], z["gewinne"], z["sek"], z["etf"], ausschnitt, kurz)}'
                       f'{z["rs_lesart"]}</div>'), oben=0, unten=0)


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


def abgelegt(tk):
    """Gespeicherte Titelseite oder None (fehlt, oder Programm bzw. Depot sind jünger)."""
    import gzip
    import pickle
    import depot
    pfad = os.path.join(ABLAGE, f"{tk.upper()}.pkl.gz")
    try:
        zeit = os.path.getmtime(pfad)
        juenger = [codezeit()] + ([os.path.getmtime(depot.DATEI)] if os.path.exists(depot.DATEI) else [])
        if zeit < max(juenger):
            return None
        with gzip.open(pfad, "rb") as f:
            return pickle.load(f)
    except Exception:  # noqa: BLE001 – dann wird gerechnet
        return None


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
    try:                                         # 30-Minuten-Kerzen holen bzw. fortsetzen (Market-Profile-Zonen)
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
    erk["bahn"] = freie_bahn.freie_bahn(df, w_.get("pivot") if erk["muster"] else None, bool(erk["muster"]), historie)
    try:                                          # Gelände: Zonen + Volumen (Rückgrat um die Meister)
        import gelaende
        pl_ = depot.plan(erk)
        erk["gelaende"] = gelaende.gelaende(tk, df, erk, stopp=pl_[2] if pl_ else None, seite=pl_[0] if pl_ else None)
    except Exception:  # noqa: BLE001 – ohne 30-Minuten-Kerzen arbeitet das Cockpit mit den übrigen Ampeln
        erk["gelaende"] = None
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
    tvp = _trendvorlage(df)
    tv = sum(tvp.values())
    try:
        mr = marktrichtung.richtung()
    except Exception:
        mr = None
    etf = sektoren.sektor_von(sb.get("sektor", ""))
    try:
        sek = marktdaten.yahoo(etf) if etf else None
    except Exception:
        sek = None
    rd = rudelkarte.daten(tk, df, etf)
    erk["gruppe_korrektur"] = _gruppe_korrektur(df, erk, rd)

    try:
        quad, rot_sek = lage_modul.quadrant(), sektoren.rotation()
    except Exception:
        quad, rot_sek = None, None
    spy = (rd or {}).get("spy")
    if spy is None:
        try:
            spy = marktdaten.yahoo("SPY")
        except Exception:
            spy = None
    kompass = sic13.kompass(tk, df, spy, sb.get("sektor", ""), etf, fund, quad, rot_sek)
    hinweis_laufend = ""
    if df.attrs.get("laufend"):
        hinweis_laufend = (f'<div style="border:1px solid #5A4A1A;background:#2A2410;color:#E3B341;border-radius:10px;'
                           f'padding:10px 14px;font-size:14px">Laufender Börsentag, Stand {df.attrs["stand"]} Uhr: Die letzte '
                           f'Kerze ist unvollständig (im Chart hohl). Ausbruch, Volumenfaktoren, Fußabdruck und Absorption '
                           f'sind vorläufig bis Börsenschluss – O\'Neil und Minervini urteilen über Schlusskurs und '
                           f'Tagesvolumen.</div>')
    erk["fruehwarnung"] = fruehwarnung.zeichen(df, erk, ph)
    gestaltung.MITSCHRIFT = {}                  # die Lagekarte liest die Ampeln der Kacheln mit
    try:
        leiste = _kacheln(erk, ph, ph_reihe, tvp, fund, _rs_richtung(df, index), df, rd, fd if fund else None, mr, gewinne)
        k_info = dict(gestaltung.MITSCHRIFT)
    finally:
        gestaltung.MITSCHRIFT = None
    lk = lagekarte.karte(tk, namen_de.BRANCHE.get(sb.get("branche"), sb.get("branche")) or "", erk, k_info, df)
    lage_block = (f'<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start">'
                  f'<div style="flex:0 1 460px;min-width:340px">{lagekarte.faerben(lk, _eintrag(tk))}</div>'
                  f'{leiste}</div>')
    oben = [_kopf(tk, sb, df) + hinweis_laufend, _sic13_karte(kompass), lage_block]
    zwischen = {"df": df, "erk": erk, "ph_reihe": ph_reihe, "index": index, "gewinne": gewinne, "sek": sek,
                "etf": etf or "", "rs_lesart": _rs_lesart(df, index, sek, etf)}
    # Strömung in der Zone: Base, sonst Base im Aufbau, sonst die letzten 60 Tage
    z_start = w_.get("start_index") if "start_index" in w_ else len(df) - 60
    if erk.get("mp"):
        a_mp = erk["mp"]
        z_beginn = a_mp["wochen"][a_mp["stand"][-1]["von"]]["tag"]
        alt_ = stroemung_modul.stroemung(df, int(df.index.searchsorted(z_beginn)), index, erk.get("fuss"))
        strom = stroemung_modul.stroemung_mp(a_mp, df) + [r for r in alt_ if r[0].startswith(("Fußabdruck", "RS"))]
        einleitung = ((f'<b>Vorläufig (Stand {a_mp["vorlaeufig"]} Uhr):</b> mit den 30-Minuten-Kerzen des laufenden Tages '
                       f'(Yahoo, bis 15 Minuten verzögert); Auslöser gelten erst mit dem Schlusskurs. ')
                      if a_mp.get("vorlaeufig") is not None else "") + (
                      f'Zone seit {z_beginn:%d.%m.%Y} (Market Profile: Wochen aus 30-Minuten-Kerzen, Wertbereich 70 % der '
                      f'Zeit). Tageswert zum Vortag: ▲ ganz höher · △ überlappend höher · ▬ unverändert · ▽ überlappend '
                      f'tiefer · ▼ ganz tiefer. ↑ Long, ↓ Short, ◆ Druck ohne Richtung.')
    else:
        strom = stroemung_modul.stroemung(df, z_start, index, erk.get("fuss"))
        einleitung = (f'Für diesen Titel fehlen die 30-Minuten-Kerzen (werkzeuge/tpo_laden.py). Bis dahin: Zeichen der letzten '
                      f'60 Tage seit {df.index[max(0, z_start)]:%d.%m.%Y}. ↑ Long, ↓ Short, ◆ Druck ohne Richtung.')
    bild_ = stroemungsbild.bild(erk["mp"]) if erk.get("mp") else ""
    teile = [karte(f'<div style="font-size:14px;color:{TEXT_2}">{einleitung}</div>' + bild_
                   + "".join(ampelzeile(f"{pf} {name}", amp, txt,
                                        AUSLOESER_HILFE if name == "Letzte Auslöser" else
                                        stroemung_modul.HILFE.get(name, ""))
                             for name, amp, pf, txt in strom),
                   "Strömung in der Zone")]
    teile.append(_gelaende_karte(erk))
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
    branche = rd["rudel"]["name"] if rd and rd["rudel"]["art"] == "Branche" else None
    teile.append(f'{raster}{_phase_zyklus(tk, df, ph, ph_reihe, krit, etf, branche)}'
                 f'{rudelkarte.karte_rudel(rd)}</div>')
    teile.append(f'{raster}{_avwap_karte(df, erk)}{_warnzeichen(erk)}</div>')
    lage = f'<p style="margin:0;font-size:16px;line-height:1.65">{t(_lagebeurteilung(ph, erk, tv, fund))}</p>'
    plan, rand = _szenario(df, erk, ph, mr, rd, gewinne) if len(df) >= 260 else ("", BLAU)
    teile.append(karte(lage + plan, "Lage und Plan", rand=rand))
    teile.append(depotleiste.titelkarte(tk, df, erk))
    return {"oben": seite("".join(oben), unten=8), "chart": zwischen, "unten": seite("".join(teile), oben=8),
            "lagekarte": lk, "kacheln": k_info}
