"""Der Zirkel je Titel (Micky 22.11.2026, löst den Kartentisch ab): ein Nachtlauf-Schritt rechnet für jeden Titel des
Reviers und der Watchlist aus den gespeicherten Tageskursen

  · den Kreislauf (Phase 1–4, Zeichen der Stärke und Schwäche, Keime – zeichen.fuer_titel),
  · das Setup: Zonen-Trade der Tagesebene (zonen.basis, lage, trade) im Einklang mit dem Zirkel (setup) –
    Aufbruch, Fortsetzung, Rücktest, Abbruch, Fortsetzung abwärts – oder keines,
  · ob der Titel heute am 52-Wochen-Hoch oder -Tief steht (Zeichen unter der Markt-Ampel: Hochs gegen Tiefs),
  · den Zirkel der Indizes S&P 500 und Nasdaq – daraus die Markt-Ampel (markt_ampel, Micky 23.11.2026).

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
TRADE_FELDER = ("art", "name", "zeichen", "richtung", "einstieg", "stopp", "pivot", "risiko", "ampel", "wartet")
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
        feld = {"phase": la["phase"] if la else None,
                "trade": {x: t[x] for x in TRADE_FELDER} if t else None,
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
                 "titel": len(feld), "index": indizes()}
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
MARKT_FUEHRT = "S&P 500"                         # er bestimmt die Ampel, der Nasdaq steht daneben (Micky 23.11.2026)
INDEX_FELDER = ("phase", "name", "ziel", "wort", "keim", "traegt", "wochen")


def indizes():
    """Zirkel der Indizes {Name: {phase, name, ziel, wort, keim, traegt, wochen, ampel, kurstag}} – ohne Zeichen
    relativ zum Markt (zeichen.zirkel_index)."""
    import daten
    import zeichen
    aus = {}
    for name, tk in INDIZES.items():
        try:
            df = daten.kurse_gespeichert(tk)
            z = zeichen.zirkel_index(df.dropna(subset=["High", "Low", "Close"]))
        except Exception:  # noqa: BLE001 – ein Index ohne Kurse fehlt in der Ampel
            continue
        if z:
            aus[name] = {**{x: z.get(x) for x in INDEX_FELDER}, "ampel": markt_ampel(z), "ticker": tk,
                         "kurstag": f"{df.index[-1]:%Y-%m-%d}"}
    return aus


# ── Markt-Ampel aus dem Zirkel des Index (Micky 23.11.2026, löst O'Neils Distributionstage und Follow-Through-Day ab):
#   🟢 Angriff   Phase 2 ohne 🍂 · Phase 1 mit gemessenem 🌱 bzw. Wechsel 1 → 2
#   🟡 Vorsicht  Phase 2 mit 🍂 · Phase 1 ohne 🌱 · Phase 3 ohne 🍂 · Phase 4 mit 🌱
#   🔴 Rückzug   Phase 3 mit 🍂 bzw. Wechsel 3 → 4 · Phase 4 ohne 🌱
MARKT_WORT = {"grün": "Angriff", "gelb": "Vorsicht", "rot": "Rückzug"}


def markt_ampel(zk):
    """Zirkel eines Index → "grün" | "gelb" | "rot" (Regel oben); ohne Zirkel "gelb"."""
    p = (zk or {}).get("phase") or 0
    keim, ziel = bool((zk or {}).get("keim")), (zk or {}).get("ziel")
    if p == P_AUF:
        return "gelb" if keim else "grün"
    if p == P_BASIS:
        return "grün" if keim or ziel == P_AUF else "gelb"
    if p == P_VERTEILUNG:
        return "rot" if keim or ziel == P_AB else "gelb"
    if p == P_AB:
        return "gelb" if keim else "rot"
    return "gelb"


def markt():
    """Die eine Markt-Ampel aus dem letzten Zirkel-Lauf → {ampel, wort, fuehrt, indizes, hochs, tiefs} oder None."""
    b = barometer()
    ix = b.get("index") or {}
    f = ix.get(MARKT_FUEHRT)
    if not f:
        return None
    return {"ampel": f["ampel"], "wort": MARKT_WORT[f["ampel"]], "fuehrt": MARKT_FUEHRT, "indizes": ix,
            "hochs": b.get("hochs"), "tiefs": b.get("tiefs")}


def markt_text(m):
    """Markt-Ampel in Worten: Phase und Keim je Index, dann Hochs gegen Tiefs."""
    teile = []
    for name, x in (m or {}).get("indizes", {}).items():
        z = {"grün": "🟢", "gelb": "🟡", "rot": "🔴"}[x["ampel"]]
        teile.append(f'{z} {name}: Phase {x["wort"]} ({x["name"]})'
                     + (f' · Keim: {"; ".join(x["keim"])}' if x.get("keim") else " · kein Keim gemessen"))
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


# ── Das Setup ergibt sich aus dem Zirkel (Micky 22.11.2026): Phase des Zirkels (Woche) + Zone (Tag), bestätigt durch
# Stärke bzw. Schwäche nach unserer Definition (Stärke = Widerstand überwinden und Druck aushalten; ein Keim zählt nur,
# wenn er gemessen ist). Ein Zonen-Trade gegen den Zirkel ist kein Setup und wird nicht gezeigt.
#   1 Basis      + Ausbruch/am Pivot  + 🌱 gemessen (Widerstand überwunden, Rücksetzer gehalten)  → Aufbruch (long)
#   2 Aufwärts   + Ausbruch/am Pivot  + kein 🍂                                                    → Fortsetzung (long)
#   1→2 oder 2   + Rücktest des Pivots                                                             → Rücktest (long)
#   3 Verteilung + Bruch mit Volumen  + 🍂 gemessen (Stützen geben unter Druck nach)               → Abbruch (short)
#   4 Abwärts    + Bruch mit Volumen  + kein 🌱                                                    → Fortsetzung abwärts (short)
# Junge Titel ohne Zirkel (unter einem Jahr Kurse): Ausbruch und Rücktest als Aufbruch bzw. Rücktest (IPO-Base).
SETUP = {"aufbruch": ("🦬", "Aufbruch"), "fortsetzung": ("🦬", "Fortsetzung"), "ruecktest": ("🪝", "Rücktest"),
         "abbruch": ("🐻", "Abbruch"), "abwaerts": ("🐻", "Fortsetzung abwärts")}


def setup(t, zk):
    """Zonen-Trade t (zonen.trade) und Zirkel zk (zeichen.zirkel) → der Trade als Setup (Name und Zeichen des Setups)
    oder None, wenn die Zone gegen den Zirkel steht bzw. die Bedingung fehlt."""
    if not t:
        return None
    p = (zk or {}).get("phase") or 0
    keim = bool((zk or {}).get("keim"))
    ziel = (zk or {}).get("ziel")
    art = None
    if t["art"] == "ausbruch":
        if p == 0 or (p == P_BASIS and (keim or ziel == P_AUF)):
            art = "aufbruch"
        elif p == P_AUF and not keim:
            art = "fortsetzung"
    elif t["art"] == "ruecktest":
        if p in (0, P_AUF) or (p == P_BASIS and ziel == P_AUF):
            art = "ruecktest"
    elif t["art"] == "short":
        if p == P_VERTEILUNG and (keim or ziel == P_AB):
            art = "abbruch"
        elif p == P_AB and not keim:
            art = "abwaerts"
    if not art:
        return None
    return dict(t, art=art, zeichen=SETUP[art][0], name=SETUP[art][1])


HEISS = ("kante", "ausbruch", "ruecktest", "bruch")   # Morgenmeldung: am Pivot, frischer Ausbruch, Rücktest, Bruch


def trade_wort(f):
    """Setup eines Titels aus dem Feld in Worten, mit der Phase der Base: „🦬 Fortsetzung · am Pivot“, „🦬 Aufbruch ·
    Base im Aufbau“, „🦬 Fortsetzung · läuft“, „🐻 Abbruch“; ohne Setup ""."""
    import zonen
    t = (f or {}).get("trade")
    if not t:
        return ""
    if t["art"] not in ("aufbruch", "fortsetzung"):
        return f'{t["zeichen"]} {t["name"]}'
    return f'{t["zeichen"]} {t["name"]} · ' + ("läuft" if not t["wartet"] else zonen.PHASE[f["phase"]][1])


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
                 dreifach(tk, t, rw), gegenwind(tk, t),
                 f'Einstieg {zahl(t["einstieg"])} $ · Stopp {zahl(t["stopp"])} $ {t["ampel"]} {zahl(t["risiko"], 1)} %',
                 rueckenwind_seite.bahn(x.get("frei"), ""),
                 (("🌱 " if zeichen.KEIM_SEITE.get(zk["phase"]) == "stärke" else "🍂 ") + zeichen.kurz(zk["keim"][0]))
                 if zk and zk["keim"] else ""]
        return " · ".join(s for s in teile if s)

    def klasse_nr(tk):
        return (rw.get(tk) or {}).get("klasse") or len(rueckenwind.KLASSEN) + 1   # ohne Klasse ganz hinten

    mit = [tk for tk, x in f_.items() if x.get("trade") and x.get("phase") in HEISS]
    lang = sorted((tk for tk in mit if f_[tk]["trade"]["richtung"] > 0 and klasse_nr(tk) in rueckenwind.VORNE_KLASSEN),
                  key=lambda tk: (not dreifach(tk, f_[tk]["trade"], rw), klasse_nr(tk),   # ▲▲▲ zuerst (23.11.)
                                  -((rw.get(tk) or {}).get("rang") or 0)))[:n]
    kurz = sorted((tk for tk in mit if f_[tk]["trade"]["richtung"] < 0),
                  key=lambda tk: (-klasse_nr(tk), (rw.get(tk) or {}).get("rang") or 0))[:n]
    zeilen = ([zeile(tk, "🦬") for tk in lang] or ["⚪ Long: heute kein Setup am Pivot, im Ausbruch oder Rücktest"]) + \
             ([zeile(tk, "🐻") for tk in kurz] or ["⚪ Short: heute kein Abbruch und keine Fortsetzung abwärts"])
    return "\n".join(zeilen), len(lang) + len(kurz)
