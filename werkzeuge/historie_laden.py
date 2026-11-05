"""Einmaliger Abruf: Tageskurse aller US-Aktien von Massive (Kursverwandte, Themen-Gruppen, Phasen der Branchen).

Aufruf im Ordner InvestCockpit (der Mac bleibt dabei wach):
    caffeinate -i python3 -u werkzeuge/historie_laden.py          ein Jahr (260 Handelstage)
    caffeinate -i python3 -u werkzeuge/historie_laden.py 495      knapp zwei Jahre (Grenze des kostenlosen Plans)
Dauer je Jahr rund 45 Minuten (5 Anfragen pro Minute, eine je Handelstag). Schon gespeicherte
Tage werden übersprungen – abbrechen und neu starten ist jederzeit möglich. Danach die Splits des
Zeitraums (wenige Anfragen) und eine Prüfung, ob jeder Revier-Titel genug Tage hat.
"""
import os
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import massive  # noqa: E402

TAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 260   # 260 = ein Börsenjahr; Massive kostenlos: höchstens 2 Jahre


def main():
    start = time.time()
    vorher = sum(1 for d in os.listdir(massive.SPEICHER) if d[:4].isdigit() and d.endswith(".csv"))
    print(f"1/3 Tageskurse: {TAGE} Handelstage, {vorher} Tage liegen schon vor …", flush=True)

    def melden(k, n, t):
        if k % 10 == 0 or k == n:
            print(f"    {k} von {n} ({t:%d.%m.%Y}) – {(time.time() - start) / 60:.0f} min", flush=True)

    tage = massive.letzte_tage(TAGE, melden=melden)
    von, bis = tage[0][0], tage[-1][0]
    print(f"2/3 Splits {von:%d.%m.%Y}–{bis:%d.%m.%Y} …", flush=True)
    sp = massive.splits_zeitraum(von, bis)
    print(f"    {len(sp)} Splits", flush=True)

    print("3/3 Prüfung gegen das Revier …", flush=True)
    revier = pd.read_csv(os.path.join(HIER, "..", "einstellungen", "revier.csv"))
    zaehl = pd.concat([df["Ticker"].str.replace(".", "-", regex=False) for _, df in tage]).value_counts()
    tage_je = revier["ticker"].map(zaehl).fillna(0)
    mindest = int(TAGE * 0.77)
    kurz = revier[tage_je < mindest]
    print(f"\nFertig in {(time.time() - start) / 60:.0f} min: {len(tage)} Handelstage {von:%d.%m.%Y}–{bis:%d.%m.%Y}, "
          f"{len(revier) - len(kurz)} von {len(revier)} Revier-Titeln mit mindestens {mindest} Tagen.")
    if len(kurz):
        print(f"Kürzer gehandelt (junge Börsengänge u. ä.): {len(kurz)} – "
              + ", ".join(f"{tk} ({int(n)})" for tk, n in zip(kurz["ticker"], tage_je[kurz.index]))[:600])


if __name__ == "__main__":
    main()
