"""Der Zirkel je Titel (Micky 22.11.2026, löst den Kartentisch ab): ein Nachtlauf-Schritt rechnet für jeden Titel des
Reviers und der Watchlist aus den gespeicherten Tageskursen

  · den Kreislauf (Phase 1–4, Zeichen der Stärke und Schwäche, Keime – zeichen.fuer_titel),
  · das Setup: Livermores Trade der Tagesebene (zonen.basis, lage, trade), benannt nach seiner Pivot-Art, vom Zirkel
    mit ✓/✗ bestätigt (setup) – Aufbruch, Fortsetzung, Rücktest, Abbruch, Fortsetzung abwärts,
  · ob der Titel heute am 52-Wochen-Hoch oder -Tief steht (Zeichen unter der Markt-Ampel: Hochs gegen Tiefs),
  · die Markt-Ampel: Livermores Notizbuch auf S&P 500 und Nasdaq, der Zirkel der Indizes bestätigt (Micky 25.11.2026),
    dazu die Führer (Garde und Angriff) im Aufwärts- bzw. Abwärtstrend des Notizbuchs.

Abgelegt mit dem Kreislauf in daten/kreislauf/<stand>.json (zeichen.ablegen): {"titel": Kreisläufe, "feld": je Titel
Phase und Trade, "barometer": Hochs, Tiefs, Titel, Zirkel der Indizes}. Die Morgenmeldung (heisse) liest Feld und Rückenwind.
"""
import functools
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from masse import JAHR_TAGE

KURSE_MIN = 60                  # Technik: darunter weder Base noch Kreislauf
TRADE_FELDER = ("art", "name", "zeichen", "richtung", "einstieg", "stopp", "pivot", "risiko", "ampel", "wartet", "zirkel",
                "zirkel_grund", "aufstocken", "aufgestockt")
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
        t = setup(zonen.trade(e, la, ba), zeichen.zirkel(k))
        h, l = df["High"].to_numpy(float), df["Low"].to_numpy(float)
        nb_ = ba.get("nb") or {}
        feld = {"phase": la["phase"] if la else None, "lv_spalte": nb_.get("spalte"),   # Livermores Spalte = Lage
                "pivot": la["pivot"] if la else None, "kurs": la["kurs"] if la else None,   # ▲▲▲-Liste (23.11.2026)
                "trade": {x: t.get(x) for x in TRADE_FELDER} if t else None,
                "hoch52": bool(len(h) >= JAHR_TAGE and h[-1] >= h[-JAHR_TAGE:].max()),
                "tief52": bool(len(l) >= JAHR_TAGE and l[-1] <= l[-JAHR_TAGE:].min())}
        return tk, k, feld
    except Exception:  # noqa: BLE001 – ein Titel scheitert, der Lauf steht trotzdem
        return None


def liste(revier):
    """Titel des Zirkel-Laufs: Revier, Watchlist und die Positionen des Depots (Führung nach dem Kauf, 23.11.2026)."""
    import depot
    import watchlists
    return sorted(set(revier) | set(watchlists.alle()) | {p["ticker"] for p in depot.laden()["positionen"]})


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
                 "titel": len(feld), "index": indizes(), "fuehrer": fuehrer(feld), "heer": heer(feld)}
    stand = pd.Timestamp.now().strftime("%Y-%m-%d")   # Datei je Lauftag: die jüngste gilt (zeichen.laden)
    try:                                            # Kurstag für die Datenstand-Wache
        kurstag = f"{daten.kurse_gespeichert(daten.INDEX).index[-1]:%Y-%m-%d}"
    except Exception:  # noqa: BLE001
        kurstag = None
    zeichen.ablegen(stand, {tk: k for tk, k, _ in erg if k}, feld=feld, barometer=barometer, kurstag=kurstag)
    trades = sum(1 for f in feld.values() if f["trade"])
    melden(f"  {len(feld)} Titel in {time.time() - beginn:.0f} s, {trades} mit Setup")
    return {"stand": stand, "kurstag": kurstag, "titel": len(feld), "trades": trades, "barometer": barometer}


P_BASIS, P_AUF, P_VERTEILUNG, P_AB = 1, 2, 3, 4   # Technik: Phasen des Zirkels
INDIZES = {"S&P 500": "SPY", "Nasdaq": "QQQ"}     # über die ETFs (gespeicherte Tageskurse mit echtem Volumen)
INDEX_FELDER = ("phase", "name", "ziel", "wort", "keim", "traegt", "wochen", "gewicht_keim", "gewicht_traegt")


def indizes():
    """Der Durchschnitt (Schicht 3 der Lage, Micky 26.11.2026): je Index Livermores Notizbuch (ampel, spalte, trend)
    und sein Zirkel als Zeichen (phase, name, ziel, wort, keim, traegt, wochen) → {Name: {…, ticker, kurstag}}."""
    import daten
    import livermore
    import zeichen
    aus = {}
    for name, tk in INDIZES.items():
        try:
            df = daten.kurse_gespeichert(tk).dropna(subset=["High", "Low", "Close"])
            nb = livermore.notizbuch(df)
            z = zeichen.zirkel_index(df)
        except Exception:  # noqa: BLE001 – ein Index ohne Kurse fehlt in der Ampel
            continue
        if not nb:
            continue
        aus[name] = {**{x: (z or {}).get(x) for x in INDEX_FELDER}, "ampel": LIVERMORE_AMPEL.get(nb["spalte"], "gelb"),
                     "spalte": livermore.spalte_text(nb), "trend": nb["trend"], "ticker": tk,
                     "kurstag": f"{df.index[-1]:%Y-%m-%d}"}
    return aus


def spalte(x):
    """Livermores Spalte eines Titels aus dem Feld (ältere Läufe: der Trend)."""
    return x.get("lv_spalte", x.get("lv_trend"))


def _zaehlen(xs):
    """{auf, pause, ab}: wie viele im Vormarsch (Spalte Aufwärtstrend), in der Gefechtspause, im Rückzug – dieselbe
    Sprache wie der Lagebericht des Titels (livermore.lage, Micky 26.11.2026)."""
    sp = [spalte(x) for x in xs]
    return {"auf": sp.count("AT"), "pause": sum(1 for s_ in sp if s_ and s_ not in ("AT", "AB")), "ab": sp.count("AB")}


def fuehrer(f_):
    """Die Spitze (Schicht 1 der Lage): die Führer – Garde und Angriff im Rückenwind – im Notizbuch → {auf, pause, ab}."""
    import rueckenwind
    rw = (rueckenwind.laden() or {}).get("titel") or {}
    return _zaehlen([f_[tk] for tk, x in rw.items() if x.get("klasse") in rueckenwind.ANGRIFF_KLASSEN and tk in f_])


def heer(f_):
    """Das Heer (Schicht 2 der Lage): alle Titel des Laufs (Revier, Watchlist, Depot) im Notizbuch → {auf, pause, ab}."""
    return _zaehlen(list(f_.values()))


# ── Markt-Ampel: das Lagebild in drei Schichten (Micky 26.11.2026; Livermore las den Markt an den Führern, nie am
# Index – How to Trade in Stocks, Kap. I und III; Weinstein: vom Wald zu den Bäumen). Davor 25.11. das Notizbuch des
# S&P 500, 23.–25.11. der Zirkel des Index, bis 23.11. O'Neil.
#   Spitze (fuehrer) und Heer (heer) bestimmen nach der Mehrheit im Notizbuch, je Titel die Spalte von heute
#   (livermore.lage: Aufwärtstrend = Vormarsch, Rally und Reaktion = Gefechtspause, Abwärtstrend = Rückzug) – keine
#   eigene Prozentzahl, ungemessen:
#   🟢 Vormarsch      in beiden mehr Titel im Vormarsch als im Rückzug
#   🔴 Rückzug        in beiden mehr im Rückzug
#   🟡 Gefechtspause  sonst (auch wenn Spitze und Heer uneins sind)
#   Der Durchschnitt (indizes: Notizbuch des S&P 500 und des Nasdaq) bestätigt mit ✓ (dieselbe Farbe) oder ✗.
LIVERMORE_AMPEL = {"AT": "grün", "AB": "rot"}
MARKT_WORT = {"grün": "Vormarsch", "gelb": "Gefechtspause", "rot": "Rückzug"}


def lage_ampel(spitze, heer_):
    """Ampel aus Spitze und Heer ({auf, ab} je Schicht) → "grün" | "gelb" | "rot"."""
    if not spitze or not heer_:
        return "gelb"
    if spitze["auf"] > spitze["ab"] and heer_["auf"] > heer_["ab"]:
        return "grün"
    if spitze["ab"] > spitze["auf"] and heer_["ab"] > heer_["auf"]:
        return "rot"
    return "gelb"


def livermore_ampel(df):
    """Livermores Frontbericht eines Index aus Tageskerzen → "grün" | "gelb" | "rot"; ohne Notizbuch "gelb"."""
    import livermore
    nb = livermore.notizbuch(df.dropna(subset=["High", "Low", "Close"]))
    return LIVERMORE_AMPEL.get((nb or {}).get("spalte"), "gelb")


def markt():
    """Die eine Markt-Ampel aus dem letzten Zirkel-Lauf (Lagebild in drei Schichten) → {ampel, wort, fuehrer, heer,
    indizes (je mit bestaetigt ✓/✗), hochs, tiefs} oder None (ältere Läufe ohne das Heer)."""
    b = barometer()
    if not b.get("heer") or not b.get("fuehrer"):
        return None
    ampel = lage_ampel(b["fuehrer"], b["heer"])
    ix = {n: {**x, "bestaetigt": "✓" if x.get("ampel") == ampel else "✗"} for n, x in (b.get("index") or {}).items()}
    return {"ampel": ampel, "wort": MARKT_WORT[ampel], "fuehrer": b["fuehrer"], "heer": b["heer"], "indizes": ix,
            "hochs": b.get("hochs"), "tiefs": b.get("tiefs")}


def markt_text(m):
    """Markt-Ampel in Worten: Spitze, Heer, dann je Index Livermores Spalte mit ✓/✗ und dem Zirkel als Zeichen."""
    teile = []
    for wort, k in (("Spitze (Garde und Angriff)", "fuehrer"), ("Heer (alle Titel)", "heer")):
        x = (m or {}).get(k)
        if x:
            teile.append(f'{wort}: {x["auf"]} im Vormarsch, {x.get("pause", 0)} in der Gefechtspause, {x["ab"]} im Rückzug')
    for name, x in (m or {}).get("indizes", {}).items():
        teile.append(f'{name}: {x.get("spalte", "")} {x.get("bestaetigt", "")}'
                     + (f' · Zirkel Phase {x["wort"]} ({x["name"]})' if x.get("wort") else "")
                     + (f' · Keim: {"; ".join(x["keim"])}' if x.get("keim") else ""))
    if (m or {}).get("hochs") is not None:
        teile.append(f'neue 52-Wochen-Hochs : Tiefs {m["hochs"]} : {m["tiefs"]}')
    return teile


def feld(tk=None):
    """Phase und Trade aus dem letzten Lauf: alle {tk: feld} oder der eine Titel (dict oder {})."""
    import zeichen
    f = zeichen.laden().get("feld") or {}
    return f if tk is None else (f.get(tk) or {})


def barometer():
    import zeichen
    return zeichen.laden().get("barometer") or {}


# ── Das Setup (Micky 25.11.2026: Livermore liefert das System, der Zirkel bestätigt nur): jedes Signal aus Livermores
# Spanne ist ein Setup. Der Name kommt aus der Art seines Pivotal Points – Livermores Trend im Notizbuch, als die Spanne
# stand (zone["trend"]):
#   Ausbruch über den Pivotal Point oben, Trend aufwärts   → Fortsetzung (long, Fortsetzungs-Pivotal-Point)
#   Ausbruch über den Pivotal Point oben, Trend abwärts    → Aufbruch (long, Umkehr – Regel 10d)
#   Rücktest des Pivots nach dem Ausbruch                   → Rücktest (long)
#   Bruch des Pivotal Points unten, Trend aufwärts          → Abbruch (short, Umkehr – Regel 10b)
#   Bruch des Pivotal Points unten, Trend abwärts           → Fortsetzung abwärts (short)
# Der Zirkel (Woche) bestätigt mit ✓ (trägt) oder ✗ (steht dagegen, mit Grund) – nichts wird weggelassen. ✓ wie bis
# 25.11.2026 die Bedingung des Setups: long 1 Basis mit 🌱 oder Wechsel zu 2, 2 Aufwärts ohne 🍂 (Rücktest: 2, oder 1
# mit Wechsel zu 2); short 3 Verteilung mit 🍂 oder Wechsel zu 4, 4 Abwärts ohne 🌱; junge Titel ohne Zirkel: long ✓.
SETUP = {"aufbruch": ("🦬", "Aufbruch"), "fortsetzung": ("🦬", "Fortsetzung"), "ruecktest": ("🪝", "Rücktest"),
         "abbruch": ("🐻", "Abbruch"), "abwaerts": ("🐻", "Fortsetzung abwärts")}


def bestaetigt(t, zk):
    """Bestätigt der Zirkel den Zonen-Trade t? → (True|False, Grund)."""
    p = (zk or {}).get("phase") or 0
    keim = bool((zk or {}).get("keim"))
    ziel = (zk or {}).get("ziel")
    if t["art"] == "ausbruch":
        ja = p == 0 or (p == P_BASIS and (keim or ziel == P_AUF)) or (p == P_AUF and not keim)
    elif t["art"] == "ruecktest":
        ja = p in (0, P_AUF) or (p == P_BASIS and ziel == P_AUF)
    else:
        ja = (p == P_VERTEILUNG and (keim or ziel == P_AB)) or (p == P_AB and not keim)
    if p == 0:                                    # wie bis 25.11.: junge Titel nur long (IPO-Base)
        return t["art"] != "short", "junger Titel ohne Zirkel"
    grund = f'Phase {p} {zk.get("name") or ""}'.strip() + (f', Wechsel zu {ziel}' if ziel else "") \
        + (f', Keim: {(zk.get("keim") or [""])[0].split(":")[0]}' if keim else "")
    return ja, grund


def setup(t, zk):
    """Zonen-Trade t (zonen.trade, mit zone_trend = Livermores Trend der Spanne) und Zirkel zk (zeichen.zirkel) → der
    Trade als Setup: Name nach Livermores Pivot-Art, dazu zirkel ✓/✗ und zirkel_grund; None nur ohne Trade."""
    if not t:
        return None
    auf = t.get("zone_trend", "AT") == "AT"
    art = {"ausbruch": "fortsetzung" if auf else "aufbruch", "ruecktest": "ruecktest",
           "short": "abbruch" if auf else "abwaerts"}[t["art"]]
    ja, grund = bestaetigt(t, zk)
    return dict(t, art=art, zeichen=SETUP[art][0], name=SETUP[art][1], zirkel="✓" if ja else "✗", zirkel_grund=grund)


HEISS = ("kante", "ausbruch", "ruecktest", "bruch")   # Morgenmeldung: am Pivot, frischer Ausbruch, Rücktest, Bruch


def trade_wort(f):
    """Setup eines Titels aus dem Feld in Worten mit der Bestätigung des Zirkels: „🦬 Fortsetzung ✓ · am Pivot“,
    „🦬 Aufbruch ✗ · Spanne im Aufbau“, „🐻 Abbruch ✓“; ohne Setup ""."""
    import zonen
    t = (f or {}).get("trade")
    if not t:
        return ""
    z = f' {t["zirkel"]}' if t.get("zirkel") else ""
    if t["art"] not in ("aufbruch", "fortsetzung"):
        return f'{t["zeichen"]} {t["name"]}{z}'
    return f'{t["zeichen"]} {t["name"]}{z} · ' + ("läuft" if not t["wartet"] else zonen.PHASE[f["phase"]][1])


_GRUPPEN = {}


def branche(tk):
    """Zirkel der Branche eines Titels aus dem letzten Rückenwind-Lauf ({phase, name, ziel, wort, keim, traegt,
    wochen, gruppe}) oder None – je Stand einmal gelesen."""
    import rueckenwind
    try:
        pfad = rueckenwind._pfad("stand.json")
        schluessel = (pfad, os.path.getmtime(pfad))
    except OSError:
        return None
    if _GRUPPEN.get("k") != schluessel:
        erg = rueckenwind.laden() or {}
        zk = {g["name"]: g.get("zirkel") for g in erg.get("gruppen") or [] if g["art"] == "Branche"}
        _GRUPPEN.update(k=schluessel, titel={t: x.get("branche") for t, x in (erg.get("titel") or {}).items()}, zk=zk)
    name = _GRUPPEN["titel"].get(tk)
    z = _GRUPPEN["zk"].get(name) if name else None
    return dict(z, gruppe=name) if z else None


def dreifach(tk, t, rw=None):
    """▲▲▲ am Long-Setup (Micky 23.11.2026): der Titel hat dreifachen Rückenwind – Kurs, Geld und Zahlen grün
    (rueckenwind.dreifach). rw = Titel des Rückenwinds, sonst aus dem letzten Lauf. Short-Setups: leer."""
    if not t or t["richtung"] <= 0:
        return ""
    import rueckenwind
    rw = rw if rw is not None else (rueckenwind.laden() or {}).get("titel") or {}
    return "▲▲▲" if rueckenwind.dreifach(rw.get(tk)) else ""


GEGEN = {1: (P_VERTEILUNG, P_AB), -1: (P_BASIS, P_AUF)}   # Phasen der Branche gegen long bzw. short …
MIT = {1: (P_AUF,), -1: (P_VERTEILUNG, P_AB)}               # … außer der Wechsel läuft schon in die Richtung


def gegenwind(tk, t):
    """Zeichen am Setup, wenn die Branche gegen seine Richtung steht (Micky 23.11.2026, Weinstein: keine Aktie in
    einer schwachen Gruppe kaufen – gezeigt, nicht gefiltert): long in Phase 3/4, short in Phase 1/2, außer der
    Wechsel der Branche läuft schon in die Richtung des Setups (3 → 2 für long; 1 → 4, 2 → 3 für short) → „🟡 Branche
    4 (Abwärts)“, sonst ""."""
    z = branche(tk) if t else None
    r = 1 if t and t["richtung"] > 0 else -1
    if not z or z.get("phase") not in GEGEN[r] or z.get("ziel") in MIT[r]:
        return ""
    return f'🟡 Branche {z["wort"]} ({z["name"]})'


def heisse(n=MELDUNG_JE_SEITE):
    """Die Morgenmeldung (Micky 22.11.2026: Schlachtordnung, Zirkel, ✈️): Long = Titel am Pivot, frisch ausgebrochen
    (in der Kaufzone) oder im Rücktest – ▲▲▲ dreifacher Rückenwind zuerst, dann Garde und Angriff vor der Vorhut,
    dann nach Rang; Short = Bruch der Unterkante
    mit Volumen, Rückzug zuerst; je Seite die vom Zirkel bestätigten (✓) vor den übrigen (✗). Spannen im Aufbau kommen
    nicht in die Meldung (sie stehen in der Liste).
    Je Titel: Kürzel mit Firmenname (26.11.2026), Klasse, Trade, Lage, ½ antasten · ½ aufstocken bei 📒 (sonst Einstieg),
    Stopp mit Risiko, ✈️ und Keim.
    → (Text, Anzahl)."""
    import daten
    import livermore
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
        nm = daten.kurzname(tk)                                                     # Name hinter dem Kürzel (26.11.)
        teile = [f"{sym} {tk}" + (f" ({nm})" if nm else ""), f"{kl} · {rueckenwind.KLASSEN[kl - 1]}" if kl else "", trade_wort(f_[tk]),
                 dreifach(tk, t, rw), gegenwind(tk, t),
                 " ".join(livermore.lage(spalte(f_[tk]))) if spalte(f_[tk]) else "",      # Lage (26.11.)
                 (f'½ antasten {zahl(t["einstieg"])} $ · ½ aufstocken bei 📒 {zahl(t["aufstocken"])} $'
                  + (" ✓" if t.get("aufgestockt") else "") if t.get("aufstocken")      # Livermore: erst die Probe,
                  else f'Einstieg {zahl(t["einstieg"])} $')                              # nachlegen nur im Gewinn
                 + f' · Stopp {zahl(t["stopp"])} $ {t["ampel"]} {zahl(t["risiko"], 1)} %',
                 rueckenwind_seite.bahn(x.get("frei"), ""),
                 " ".join(x for x in zeichen.halt(zk)[0::2] if x)]   # Halt der Phase in Klartext (24.11.2026)
        return " · ".join(s for s in teile if s)

    def klasse_nr(tk):
        return (rw.get(tk) or {}).get("klasse") or len(rueckenwind.KLASSEN) + 1   # ohne Klasse ganz hinten

    mit = [tk for tk, x in f_.items() if x.get("trade") and x.get("phase") in HEISS]
    lang = sorted((tk for tk in mit if f_[tk]["trade"]["richtung"] > 0 and klasse_nr(tk) in rueckenwind.VORNE_KLASSEN),
                  key=lambda tk: (f_[tk]["trade"].get("zirkel") == "✗",                # ✓ zuerst (25.11.)
                                  not dreifach(tk, f_[tk]["trade"], rw), klasse_nr(tk),   # ▲▲▲ zuerst (23.11.)
                                  -((rw.get(tk) or {}).get("rang") or 0)))[:n]
    kurz = sorted((tk for tk in mit if f_[tk]["trade"]["richtung"] < 0),
                  key=lambda tk: (f_[tk]["trade"].get("zirkel") == "✗", -klasse_nr(tk),
                                  (rw.get(tk) or {}).get("rang") or 0))[:n]
    zeilen = ([zeile(tk, "🦬") for tk in lang] or ["⚪ Long: heute kein Setup am Pivot, im Ausbruch oder Rücktest"]) + \
             ([zeile(tk, "🐻") for tk in kurz] or ["⚪ Short: heute kein Abbruch und keine Fortsetzung abwärts"])
    return "\n".join(zeilen), len(lang) + len(kurz)
