"""Hilfen rund um einen Titel (seit 22.11.2026; die alte Titelseite mit Kacheln und Setup-Reihen ist abgebaut, die
Titelseite ist zonenseite.py): TradingView-Link, Rückenwind-Eintrag und die Markt-Ampel nach O'Neil."""
import os
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

import marktklima                                     # noqa: E402
import rueckenwind                                    # noqa: E402
import tv_kennzahlen                                  # noqa: E402


def _tv_symbol(tk):
    """BÖRSE:TICKER für TradingView aus daten/tv/revier.csv; ohne Eintrag nur der Ticker (TradingView sucht dann)."""
    import watchlists
    if watchlists.zu_tv(tk):                     # Börse außerhalb der USA (z. B. RHM.DE → XETR:RHM)
        return watchlists.zu_tv(tk)
    z = tv_kennzahlen.zeile(tk.upper())
    ex = z["exchange"] if z is not None and isinstance(z.get("exchange"), str) else None
    sym = tk.upper().replace("-", ".")
    return f"{ex}:{sym}" if ex else sym


def tv_link(tk):
    """Adresse des Titels in TradingView (mit Börse, z. B. NYSE:HWM) – für den Knopf über dem Chart."""
    return f"https://www.tradingview.com/chart/?symbol={_tv_symbol(tk)}"


_RW_CACHE = {}


def _rueckenwind(tk):
    """Eintrag des Titels im Rückenwind-Stand des Nachtlaufs (Klasse, Tempo, Geld) oder None; je Stand einmal gelesen."""
    try:
        pfad = rueckenwind._pfad("stand.json")
        schluessel = (pfad, os.path.getmtime(pfad))
    except OSError:
        return None
    if _RW_CACHE.get("k") != schluessel:
        _RW_CACHE.update(k=schluessel, titel=((rueckenwind.laden() or {}).get("titel") or {}))
    return _RW_CACHE["titel"].get(tk.upper())


_SPEICHER = {}


def maerkte():
    """Die eine Markt-Ampel (O'Neil, marktklima.py), einmal je Stunde gerechnet; Hochs/Tiefs aus dem letzten Zirkel-Lauf."""
    schluessel = pd.Timestamp.now().strftime("%Y%m%d%H")
    if _SPEICHER.get("markt", (None,))[0] != schluessel:
        try:
            import zirkel
            b = zirkel.barometer()
            mm = marktklima.markt(b.get("hochs"), b.get("tiefs"))
        except Exception:  # noqa: BLE001
            mm = None
        _SPEICHER["markt"] = (schluessel, mm)
    return _SPEICHER["markt"][1]
