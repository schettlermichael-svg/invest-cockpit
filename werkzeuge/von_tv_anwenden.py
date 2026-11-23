"""Änderungen aus TradingView in die Listen der App übernehmen (Abgleich in beide Richtungen, 23.11.2026).
Aufruf auf dem Server (invest-watchlist-ablegen, alle 10 Minuten) als Benutzer cockpit:
    .venv/bin/python werkzeuge/von_tv_anwenden.py /opt/invest-daten/von_tv.json
Die Datei legt die stündliche Claude-Aufgabe auf den Zweig „daten“: {"stand": "<Zeit>", "listen": {"Watchlist":
{"neu": [...], "weg": [...]}, "Trade": {...}}}. Derselbe Stand wird nur einmal angewandt (daten/nachtlauf/von_tv_stand.txt),
falls der Server ihn nach einem gescheiterten Push noch einmal sieht."""
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import watchlists  # noqa: E402

STAND = os.path.join(HIER, "..", "daten", "nachtlauf", "von_tv_stand.txt")


def main(pfad):
    aenderung = json.load(open(pfad, encoding="utf-8"))
    stand = str(aenderung.get("stand", ""))
    if os.path.exists(STAND) and open(STAND, encoding="utf-8").read().strip() == stand:
        return
    zeilen = watchlists.anwenden(aenderung)
    os.makedirs(os.path.dirname(STAND), exist_ok=True)
    with open(STAND, "w", encoding="utf-8") as f:
        f.write(stand)
    print(f"Aus TradingView übernommen ({stand}): " + ("; ".join(zeilen) or "nichts mehr offen"))


if __name__ == "__main__":
    main(sys.argv[1])
