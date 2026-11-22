"""Der Zirkel je Titel (Micky 22.11.2026, löst den Kartentisch ab): ein Nachtlauf-Schritt rechnet für jeden Titel des
Reviers und der Watchlist aus den gespeicherten Tageskursen

  · den Kreislauf (Phase 1–4, Zeichen der Stärke und Schwäche, Keime – zeichen.fuer_titel),
  · den Zonen-Trade der Tagesebene mit derselben Regel wie Titelseite und Chart (zonen.basis, lage, trade):
    Ausbruch long, Rücktest, Short am Bruch – oder keinen,
  · ob der Titel heute am 52-Wochen-Hoch oder -Tief steht (für O'Neils Markt-Ampel: Hochs gegen Tiefs).

Abgelegt mit dem Kreislauf in daten/kreislauf/<stand>.json (zeichen.ablegen): {"titel": Kreisläufe, "feld": je Titel
Phase und Trade, "barometer": Hochs, Tiefs, Titel}. Die Morgenmeldung (heisse) liest Feld und Rückenwind.
"""
import functools
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from masse import JAHR_TAGE

KURSE_MIN = 60                  # Technik: darunter weder Base noch Kreislauf
TRADE_FELDER = ("art", "name", "zeichen", "richtung", "einstieg", "stopp", "risiko", "ampel", "wartet")
MELDUNG_JE_SEITE = 5           # Morgenmeldung: die ersten 5 Long und 5 Short


def _gewinne(tk):
    """Gewinnreihe aus dem Zwischenspeicher der Fundamentaldaten, ohne Abruf (für Zahlentage im Kreislauf)."""
    import quellen
    pfad = os.path.join(quellen.SPEICHER, f"{tk.upper()}.json")
    if not os.path.exists(pfad):
        return None
    try:
        return quellen._aus_json(json.load(open(pfad, encoding="utf-8"))).get("gewinne")
    except Exception:  # noqa: BLE001 – ohne Zahlen rechnet der Kreislauf ohne Zahlentage
        return None


def _titel(tk, start=None):
    """Kreislauf, Phase, Trade und Hoch/Tief eines Titels → (tk, kreislauf, feld) oder None."""
    import atr as atr_modul
    import daten
    import vcp_zone
    import zeichen
    import zonen
    try:
        df = daten.kurse_gespeichert(tk)
        if df is None or len(df) < KURSE_MIN:
            return None
        df = df.dropna(subset=["High", "Low", "Close"])
        df.attrs.update(ticker=tk, jung=len(df) < JAHR_TAGE)
        index = daten.kurse_gespeichert(daten.INDEX)
        ba = zonen.basis(df)
        a = ba["ausbruch"]
        fehl = vcp_zone.ausbruch_text(a) if a and a["fehl"] else None
        try:
            k = zeichen.fuer_titel(tk, df, index, _gewinne(tk), start=start, fehlausbruch=fehl)
        except Exception:  # noqa: BLE001 – ohne Kreislauf stehen Trade und Hoch/Tief trotzdem
            k = None
        e = {"name": "Tag", "df": df, "atr": atr_modul.wert(df)}
        la = zonen.lage(e, ba, profil=False)
        t = zonen.trade(e, la, ba)
        h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
        feld = {"phase": la["phase"] if la else None,
                "trade": {x: t[x] for x in TRADE_FELDER} if t else None,
                "hoch52": bool(len(h) >= JAHR_TAGE and h[-1] >= h[-JAHR_TAGE:].max()),
                "tief52": bool(len(l) >= JAHR_TAGE and l[-1] <= l[-JAHR_TAGE:].min())}
        return tk, k, feld
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Lauf steht trotzdem
        return None


def rechnen(ticker_liste, prozesse=None, melden=print):
    """Alle Titel in mehreren Prozessen; legt Kreislauf, Feld und Barometer ab → Zusammenfassung."""
    import daten
    import zeichen
    beginn = time.time()
    try:                                            # Beginn der Marktschwäche einmal für alle Titel
        start = zeichen.startdatum(daten.kurse_gespeichert(daten.INDEX))
    except Exception:  # noqa: BLE001
        start = zeichen.KEIN
    with ProcessPoolExecutor(prozesse or max(1, (os.cpu_count() or 2) - 1)) as ex:
        erg = [x for x in ex.map(functools.partial(_titel, start=start), ticker_liste, chunksize=20) if x]  # Technik
    feld = {tk: f for tk, _, f in erg}
    barometer = {"hochs": sum(f["hoch52"] for f in feld.values()), "tiefs": sum(f["tief52"] for f in feld.values()),
                 "titel": len(feld)}
    try:                                            # Stand = Kurstag (Datenstand-Wache), nicht der Tag des Laufs
        stand = f"{daten.kurse_gespeichert(daten.INDEX).index[-1]:%Y-%m-%d}"
    except Exception:  # noqa: BLE001
        stand = pd.Timestamp.now().strftime("%Y-%m-%d")
    zeichen.ablegen(stand, {tk: k for tk, k, _ in erg if k}, feld=feld, barometer=barometer)
    trades = sum(1 for f in feld.values() if f["trade"])
    melden(f"  {len(feld)} Titel in {time.time() - beginn:.0f} s, {trades} mit Trade")
    return {"stand": stand, "titel": len(feld), "trades": trades, "barometer": barometer}


def feld(tk=None):
    """Phase und Trade aus dem letzten Lauf: alle {tk: feld} oder der eine Titel (dict oder {})."""
    import zeichen
    f = zeichen.laden().get("feld") or {}
    return f if tk is None else (f.get(tk) or {})


def barometer():
    import zeichen
    return zeichen.laden().get("barometer") or {}


HEISS = ("kante", "ausbruch", "ruecktest", "bruch")   # Morgenmeldung: am Pivot, frischer Ausbruch, Rücktest, Bruch


def trade_wort(f):
    """Trade eines Titels aus dem Feld in Worten, mit der Phase der Base: „💥 Ausbruch · am Pivot“, „💥 Ausbruch ·
    Base im Aufbau“, „💥 Ausbruch · läuft“, „🐻 Bruch der Unterkante“; ohne Trade ""."""
    import zonen
    t = (f or {}).get("trade")
    if not t:
        return ""
    if t["art"] != "ausbruch":
        return f'{t["zeichen"]} {t["name"]}'
    return f'{t["zeichen"]} {t["name"]} · ' + ("läuft" if not t["wartet"] else zonen.PHASE[f["phase"]][1])


def heisse(n=MELDUNG_JE_SEITE):
    """Die Morgenmeldung (Micky 22.11.2026: Schlachtordnung, Zirkel, ✈️): Long = Titel am Pivot, frisch ausgebrochen
    (in der Kaufzone) oder im Rücktest – Garde und Angriff vor der Vorhut, dann nach Rang; Short = Bruch der Unterkante
    mit Volumen, Rückzug zuerst. Bases im Aufbau kommen nicht in die Meldung (sie stehen in der Liste).
    Je Titel: Klasse, Trade, Einstieg, Stopp mit Risiko, ✈️ und Keim. → (Text, Anzahl)."""
    import rueckenwind
    import rueckenwind_seite
    import zeichen
    from gestaltung import zahl
    rw = (rueckenwind.laden() or {}).get("titel") or {}
    f_ = feld()

    def zeile(tk, sym):
        x, t = rw.get(tk) or {}, f_[tk]["trade"]
        zk = zeichen.zirkel(zeichen.von(tk))
        kl = x.get("klasse")
        teile = [f"{sym} {tk}", f"{kl} · {rueckenwind.KLASSEN[kl - 1]}" if kl else "", trade_wort(f_[tk]),
                 f'Einstieg {zahl(t["einstieg"])} $ · Stopp {zahl(t["stopp"])} $ {t["ampel"]} {zahl(t["risiko"], 1)} %',
                 rueckenwind_seite.bahn(x.get("frei"), ""),
                 (("🌱 " if zeichen.KEIM_SEITE.get(zk["phase"]) == "stärke" else "🍂 ") + zeichen.kurz(zk["keim"][0]))
                 if zk and zk["keim"] else ""]
        return " · ".join(s for s in teile if s)

    def klasse_nr(tk):
        return (rw.get(tk) or {}).get("klasse") or len(rueckenwind.KLASSEN) + 1   # ohne Klasse ganz hinten

    mit = [tk for tk, x in f_.items() if x.get("trade") and x.get("phase") in HEISS]
    lang = sorted((tk for tk in mit if f_[tk]["trade"]["richtung"] > 0 and klasse_nr(tk) in rueckenwind.VORNE_KLASSEN),
                  key=lambda tk: (klasse_nr(tk), -((rw.get(tk) or {}).get("rang") or 0)))[:n]
    kurz = sorted((tk for tk in mit if f_[tk]["trade"]["richtung"] < 0),
                  key=lambda tk: (-klasse_nr(tk), (rw.get(tk) or {}).get("rang") or 0))[:n]
    zeilen = ([zeile(tk, "🦬") for tk in lang] or ["⚪ Long: heute kein Titel am Pivot, im Ausbruch oder Rücktest"]) + \
             ([zeile(tk, "🐻") for tk in kurz] or ["⚪ Short: heute kein Bruch mit Volumen"])
    return "\n".join(zeilen), len(lang) + len(kurz)
