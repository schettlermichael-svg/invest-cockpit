"""Auswahl der einsatzbereiten Titel (Seite Setups und Wachen) – Depot immer, dazu Titel mit grünem Setup am Auslöser
oder in der Kaufzone, in Rangfolge. Übrig vom Stab, als der Konferenzraum am 13.11.2026 abgebaut wurde; die Auswahl,
ihre Zonen und die Termin-Regel gelten weiter."""
from datetime import datetime


# Akten des Stabs (Micky 12.11.2026: „Klasse statt Masse – nur das Beste vom Besten im Konferenzraum“): immer das
# Depot; dazu nur einsatzbereite Setups – Setup grün und Kurs am Auslöser oder in der Kaufzone (long −5 bis +5 % zum
# Pivot, Short bis 5 % unter der Unterkante); Volltreffer auch bis 10 % über dem Pivot. Rang (Micky 12.11.2026):
# Zahlen in höchstens 7 Tagen nach hinten, dann Volltreffer, ★ in der Kaufzone, Geld in Richtung des Setups (Short
# gespiegelt: Abfluss zählt), RS (Short gespiegelt: schwächer zählt); die Watchlist gibt keinen Vorteil. Jede Reihe bekommt bis zu 2 Plätze vorab, damit Short und EP nie fehlen; höchstens
# AKTEN_MAX. Alles andere zeigt der Kartentisch; Watchlist-Titel ohne Akte stehen mit festen Ampeln in der Tafel.
AKTEN_MAX = 30


RANG_TEXT = ("Zahlen in höchstens 7 Tagen nach hinten, dann Volltreffer, ★ in der Kaufzone, Geld in Richtung des "
             "Setups (Short: Abfluss), RS-Rang (Short: der schwächere zuerst) – die Watchlist gibt keinen Vorteil")


AKTEN_JE_REIHE = 2


ZONE_LONG, ZONE_SHORT, ZONE_VOLLTREFFER = (-5.0, 5.0), (-5.0, 0.0), (-5.0, 10.0)


HEUTE = lambda: datetime.now().strftime("%Y-%m-%d")                    # noqa: E731


def termin_datum(zahlen, kachel, heute=None):
    """Nächster Zahlentermin als ISO-Datum oder None: aus den Zahlen des Rückenwinds, sonst aus der Kachel „Nächste
    Zahlen“ (deren Wert lautet „in n Tagen“ vom Tag der Kartentisch-Rechnung – das Datum steht im Text, „Do 13.11.2026“).
    Vergangene Termine zählen nicht (12.11.2026: vorher las die Termin-Ampel aus „in 3 Tagen“ kein Datum → grau)."""
    import re
    heute = heute or HEUTE()
    t_ = (zahlen or {}).get("termin")
    if t_ and str(t_)[:10] < heute:                 # Rückenwind behält auch den gestrigen Termin: dann die Kachel
        t_ = None                                   # (Prüf-Agent 12.11.2026)
    if not t_ and kachel:
        teile = [kachel.get("wert"), kachel.get("text")] if isinstance(kachel, dict) else list(kachel)[1:3]
        for teil in teile:
            m_ = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", str(teil or ""))
            if m_:
                t_ = f"{m_.group(3)}-{m_.group(2)}-{m_.group(1)}"
                break
    d = str(t_)[:10] if t_ and re.match(r"\d{4}-\d{2}-\d{2}", str(t_)) else None
    return d if d and d >= heute else None                       # vergangene Termine zählen nicht


def termin_tage(zahlen, kachel, heute=None):
    """Tage bis zu den nächsten Zahlen (0 = heute) oder None."""
    import pandas as pd
    d = termin_datum(zahlen, kachel, heute)
    return None if d is None else (pd.Timestamp(d) - pd.Timestamp(heute or HEUTE())).days


_tage = termin_tage


_GEGEN = {"grün": "rot", "rot": "grün", "gelb": "gelb"}


def auswahl(titel_t, rw_t, drei, wl, pos, mit_rest=False):
    """Welche Titel eine Akte bekommen (eine Funktion für Seite Setups und Wachen). → (Liste in Rangfolge, {Ticker: (beim Stab?, Grund)}) für jeden Titel mit Reihe, auf der Watchlist oder
    im Depot."""
    import kartentisch
    rang = kartentisch.RANG

    def zone(tk):
        x = titel_t.get(tk) or {}
        if x.get("reihe") in ("k_ermuedung", "k_baerenflagge", "k_bruch") or (x.get("reihe") == "zahlen" and x.get("zr_seite") == "short"):
            return ZONE_SHORT
        return ZONE_VOLLTREFFER if tk in drei else ZONE_LONG

    def bereit(tk):
        x = titel_t.get(tk) or {}
        a_ = x.get("abstand_vz")
        if not x.get("reihe") or x.get("reihe") == "vcp" or not x.get("gruen") or a_ is None:
            return False                               # „Base-Ausbruch · nur Muster“ kommt nicht auf die Liste
        lo, hi = zone(tk)
        return lo <= float(a_) <= hi

    def short(tk):
        return zone(tk) == ZONE_SHORT

    def geld_mit(tk):
        """Geld in Richtung des Setups: long grün, Short gespiegelt (Abfluss = rot ist der Rückenwind des Shorts)."""
        g = (rw_t.get(tk) or {}).get("geld_ampel")
        return g == ("rot" if short(tk) else "grün")

    try:
        import zeichen
        kreis_alle = zeichen.laden().get("titel") or {}
    except Exception:  # noqa: BLE001
        kreis_alle = {}

    def kreis_mit(tk):
        """Kreislauf in Richtung des Setups (Prüf-Agent 13.11.2026: die Rangfolge kannte ihn nicht): long Phase 2 oder
        ein Wechsel zu 1/2, Short Phase 3/4 oder ein Wechsel zu 3/4."""
        k = kreis_alle.get(tk) or {}
        p, z = k.get("phase"), k.get("ziel")
        if short(tk):
            return (p in (3, 4) and z not in (1, 2)) or z in (3, 4)
        return (p == 2 and z != 3 and not k.get("rueckschlag")) or z in (1, 2)

    def termin_tage(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        return _tage((r.get("zahlen") or {}), (x.get("kacheln") or {}).get("Nächste Zahlen"))

    def klasse(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        voll = tk in drei and bool(x.get("reihe")) and not short(tk)   # Volltreffer nur long (Prüf-Agent 12.11.2026)
        t_ = termin_tage(tk)
        rs = r.get("rang") or 0
        import gestaltung
        # Rang: Termin nah nach hinten, Volltreffer, ★, Geld in Setup-Richtung, Kreislauf in Setup-Richtung, RS – die
        # Watchlist zählt nicht
        # (Micky 12.11.2026: neutral, die Stärke entscheidet)
        return (t_ is not None and t_ <= gestaltung.TERMIN_ROT, not voll, not x.get("stern"), not geld_mit(tk),
                not kreis_mit(tk), rs if short(tk) else -rs)

    pool = set(titel_t) | set(drei) | set(wl)
    elite = sorted((tk for tk in pool if bereit(tk)), key=klasse)
    alle = list(pos)
    for reihe_ in rang:                                # bis zu 2 Plätze je Reihe vorab
        if reihe_:
            alle += [tk for tk in elite if (titel_t.get(tk) or {}).get("reihe") == reihe_
                     and tk not in alle][:AKTEN_JE_REIHE]
    alle += [tk for tk in elite if tk not in alle]
    alle = alle[:AKTEN_MAX + len(pos)]
    alle = list(pos) + sorted(set(alle) - set(pos), key=klasse)
    drin = set(alle)
    gruende = {}
    for tk in set(titel_t) | set(wl) | set(pos):
        x = titel_t.get(tk) or {}
        if not x.get("reihe") and tk not in pos and tk not in wl:
            continue
        r = rw_t.get(tk) or {}
        merkmale = ((["Volltreffer"] if tk in drei and x.get("reihe") and not short(tk) else []) + ([("★ Short-Zone" if short(tk) else "★ Kaufzone")] if x.get("stern") else [])
                    + ([("Geld fließt ab" if short(tk) else "Geld grün")] if geld_mit(tk) else [])
                    + (["Watchlist"] if tk in wl else []) + ([f'RS {r["rang"]}'] if r.get("rang") else [])
                    + ([f"Zahlen in {termin_tage(tk)} Tagen"] if (termin_tage(tk) is not None and termin_tage(tk) <= 7)
                       else []))
        if tk in drin:
            g = "Depot" if tk in pos else (" · ".join(merkmale) or "einsatzbereit")
        elif not x.get("reihe"):
            g = "kein Setup"
        elif x.get("still"):
            g = "Kurs steht still"
        elif x.get("reihe") == "vcp":
            g = "nur Muster"
        elif not x.get("gruen"):
            g = "Setup gelb"
        elif x.get("abstand_vz") is None:
            g = "kein Pivot"
        else:
            a_ = float(x["abstand_vz"])
            lo, hi = zone(tk)
            if a_ > hi:
                g = f"{'über der Unterkante' if short(tk) else 'gelaufen'} {a_:+.1f} %"
            elif a_ < lo:
                g = f"{'gelaufen' if short(tk) else 'noch weit vor dem Pivot'} {a_:+.1f} %"
            else:
                g = " · ".join(["Platz voll"] + merkmale)
        gruende[tk] = (tk in drin, g.replace(".", ","))
    if mit_rest:                                       # alle Einsatzbereiten in Rangfolge (Seite Setups)
        return alle, gruende, elite
    return alle, gruende

