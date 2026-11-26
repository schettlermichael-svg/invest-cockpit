"""Hilfen rund um einen Titel (seit 22.11.2026; die alte Titelseite mit Kacheln und Setup-Reihen ist abgebaut, die
Titelseite ist zonenseite.py): TradingView-Link, Rückenwind-Eintrag und die Markt-Ampel aus dem Zirkel des Index."""
import os
import sys


HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

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


def maerkte():
    """Die eine Markt-Ampel: Lagebild in drei Schichten (zirkel.markt, Micky 26.11.2026) oder None."""
    try:
        import zirkel
        return zirkel.markt()
    except Exception:  # noqa: BLE001
        return None
