"""Lange Kurshistorie für die Gegenproben: Tageskurse aller Revier-Titel und des S&P 500 von Yahoo, zehn Jahre.

Wozu: Die Massive-Tagesdateien reichen nur knapp zwei Jahre zurück (Grenze des kostenlosen Plans) – zu wenig, um
Regeln über mehrere Marktphasen zu prüfen (Corona-Crash 2020, Bärenmarkt 2022, Hausse 2023–2025). Gespeichert wird
in daten/lang/<TICKER>.csv; die App selbst nutzt diese Dateien nicht, nur die Prüfwerkzeuge.

Aufruf im Ordner InvestCockpit, im Terminal des Mac (Yahoo ist von dort erreichbar; der Mac bleibt wach):
    caffeinate -i python3 -u werkzeuge/historie_lang.py
Schon geladene Titel werden übersprungen – abbrechen und neu starten ist jederzeit möglich.
Dauer: etwa 20–40 Minuten (Pakete zu 20 Titeln nacheinander, kurze Pausen, bis zu drei Durchgänge).
"""
import os
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
AUS = os.path.join(HIER, "..", "daten", "lang")
JAHRE = 10
PAKET = 20
DURCHGAENGE = 3      # was im ersten Durchgang fehlt, wird bis zu zweimal nachgeladen


def speichern(df, ticker):
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    if len(df) < 60:
        return False
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "Datum"
    df.to_csv(os.path.join(AUS, ticker.replace("^", "_") + ".csv"))
    return True


def main():
    import yfinance as yf
    os.makedirs(AUS, exist_ok=True)
    # Eigener Zwischenspeicher für Yahoos Zeitzonen-Datenbank: der Standardort ist bei parallelen Abrufen gesperrt
    # („unable to open database file“)
    cache = os.path.join(AUS, "_yahoo_cache")
    os.makedirs(cache, exist_ok=True)
    yf.set_tz_cache_location(cache)
    rv = pd.read_csv(os.path.join(HIER, "..", "einstellungen", "revier.csv"), keep_default_na=False)
    alle = ["^GSPC"] + list(rv["ticker"])
    start = time.time()
    for durchgang in range(1, DURCHGAENGE + 1):
        offen = [t for t in alle if not os.path.exists(os.path.join(AUS, t.replace("^", "_") + ".csv"))]
        print(f"Durchgang {durchgang}: {len(alle)} Titel, {len(alle) - len(offen)} geladen, {len(offen)} offen", flush=True)
        if not offen:
            break
        gut, fehlt = laden(yf, offen, start)
        print(f"   Durchgang {durchgang}: {gut} geladen, {len(fehlt)} ohne Daten", flush=True)
        time.sleep(30)                                   # Yahoo eine Pause gönnen, dann den Rest nachladen
    offen = [t for t in alle if not os.path.exists(os.path.join(AUS, t.replace("^", "_") + ".csv"))]
    print(f"Fertig: {len(alle) - len(offen)} von {len(alle)} Titeln geladen"
          + (f"; ohne Daten (meist nicht mehr gehandelt oder Yahoo kennt das Kürzel nicht): {', '.join(offen[:40])}"
             if offen else ""))


def laden(yf, offen, start):
    gut, fehlt = 0, []
    for k in range(0, len(offen), PAKET):
        teil = offen[k:k + PAKET]
        try:
            d = yf.download(teil, period=f"{JAHRE}y", auto_adjust=True, progress=False, threads=False,
                            group_by="ticker")
        except Exception as e:  # noqa: BLE001
            print("   Paket fehlgeschlagen:", e, flush=True)
            fehlt += teil
            time.sleep(30)
            continue
        for t in teil:
            try:
                ok = speichern(d[t] if len(teil) > 1 else d, t)
            except Exception:  # noqa: BLE001
                ok = False
            gut += ok
            if not ok:
                fehlt.append(t)
        print(f"   {min(k + PAKET, len(offen))} von {len(offen)} – {(time.time() - start) / 60:.1f} min", flush=True)
        time.sleep(3)
    return gut, fehlt


if __name__ == "__main__":
    sys.exit(main())
