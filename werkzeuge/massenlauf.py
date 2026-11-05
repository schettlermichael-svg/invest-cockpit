"""Massenlauf der Mustererkennung über alle Titel des Reviers (Selbstprüfung, Schritt 5).

Für jeden Titel: Erkennung, frühere Basen und Selbstprüfung, nur aus den gespeicherten Tagesdateien von Massive
(kein Abruf). Ergebnis: daten/massenlauf/bericht_<Datum>.csv (eine Zeile je Titel) und zusammenfassung_<Datum>.txt.
Aufruf (im Ordner der App):  python3 werkzeuge/massenlauf.py  [Anzahl Titel, Standard alle]
In Teilen (wenn ein Lauf zeitlich begrenzt ist):  massenlauf.py --teil START ANZAHL  … dann  massenlauf.py --zusammenfassen
"""
import os
import sys
import time
from collections import Counter

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import daten        # noqa: E402
import erkennung    # noqa: E402
import massive      # noqa: E402

AUS = os.path.join(HIER, "..", "daten", "massenlauf")
TAGE = 495          # alle gespeicherten Tage (Grenze des kostenlosen Massive-Plans)


def main():
    os.makedirs(AUS, exist_ok=True)
    rv = pd.read_csv(os.path.join(HIER, "..", "einstellungen", "revier.csv"), keep_default_na=False)
    ticker = list(rv["ticker"])
    teil = None
    if len(sys.argv) > 1 and sys.argv[1] == "--zusammenfassen":
        b = pd.concat([pd.read_csv(os.path.join(AUS, f)) for f in sorted(os.listdir(AUS)) if f.startswith("teil_")])
        return zusammenfassen(b, len(ticker), 0, open(os.path.join(AUS, "stand.txt")).read().strip())
    if len(sys.argv) > 3 and sys.argv[1] == "--teil":
        teil = int(sys.argv[2])
        ticker = ticker[teil:teil + int(sys.argv[3])]
    elif len(sys.argv) > 1:
        ticker = ticker[:int(sys.argv[1])]
    t0 = time.time()
    m = {sp: massive.kursmatrix(ticker, TAGE, sp) for sp in ("Open", "High", "Low", "Close", "Volume")}
    index = daten.kurse(daten.INDEX)
    stand = str(m["Close"].index[-1].date())
    zeilen = []
    for i, tk in enumerate(ticker):
        if tk not in m["Close"].columns:
            zeilen.append({"ticker": tk, "fehler": "keine Kurse bei Massive"})
            continue
        df = pd.DataFrame({sp: m[sp][tk] for sp in m}).dropna()
        df.index.name = "Datum"
        df.attrs = {"jung": len(df) < 300}
        try:
            erk = erkennung.erkenne(df, index=index)
            hist = erkennung.basen_historie(df, index, TAGE)
            if erk["muster"] and hist and hist[-1]["ende"] >= erk["werte"].get("start_index", len(df)):
                hist = hist[:-1]
            befunde = erkennung.selbstpruefung(df, erk, hist)
            w = erk["werte"]
            zeilen.append({
                "ticker": tk, "tage": len(df), "muster": " + ".join(erk["muster"]), "kaufsetup": erk["kaufsetup"],
                "pivot": round(w["pivot"], 2) if erk["muster"] and "pivot" in w else None,
                "beginn": str(df.index[w["start_index"]].date()) if erk["muster"] else "",
                "ende": str(df.index[w.get("ende_index", len(df) - 1)].date()) if erk["muster"] else "",
                "tiefe_pct": w.get("tiefe_pct") if erk["muster"] else None,
                "kontraktionen": " / ".join(f"{x:.0f}" for x in w.get("kontraktionen", [])) if erk["muster"] else "",
                "fruehere_basen": len(hist), "gelungen": sum(b["ausgang"] == "gelungen" for b in hist),
                "gescheitert": sum(b["ausgang"] == "gescheitert" for b in hist),
                "befunde": " | ".join(befunde), "anzahl_befunde": len(befunde), "fehler": ""})
        except Exception as ex:
            zeilen.append({"ticker": tk, "fehler": repr(ex)[:200]})
        if (i + 1) % 100 == 0:
            print(f"{i + 1} von {len(ticker)} Titeln, {time.time() - t0:.0f} s", flush=True)
    b = pd.DataFrame(zeilen)
    if teil is not None:
        b.to_csv(os.path.join(AUS, f"teil_{teil:05d}.csv"), index=False)
        open(os.path.join(AUS, "stand.txt"), "w").write(stand)
        print(f"Teil ab {teil}: {len(b)} Titel, {time.time() - t0:.0f} s")
        return
    zusammenfassen(b, len(ticker), time.time() - t0, stand)


def zusammenfassen(b, anzahl, dauer, stand):
    b.to_csv(os.path.join(AUS, f"bericht_{stand}.csv"), index=False)
    ok = b[b["fehler"].fillna("") == ""]
    arten = Counter(x.split(":")[0] if ":" in x else " ".join(x.split()[:4])
                    for bef in ok["befunde"].fillna("") for x in bef.split(" | ") if x)
    musterzahl = Counter(m_.split(" + ")[0] for m_ in ok["muster"].fillna("") if m_)
    text = [f"Massenlauf der Mustererkennung, Kursstand {stand}, {anzahl} Titel" + (f", {dauer:.0f} s" if dauer else ""),
            f"gerechnet: {len(ok)}, Programmfehler: {(b['fehler'].fillna('') != '').sum()}",
            f"mit Muster: {(ok['muster'].fillna('') != '').sum()}, davon Kaufsetup: {int(ok['kaufsetup'].fillna(False).sum())}",
            f"Titel mit Befunden der Selbstprüfung: {(ok['anzahl_befunde'] > 0).sum()}", "", "Befunde nach Art:"]
    text += [f"  {v:5d}  {k}" for k, v in arten.most_common()]
    text += ["", "Hauptmuster:"] + [f"  {v:5d}  {k}" for k, v in musterzahl.most_common()]
    fehler = b[b["fehler"].fillna("") != ""]
    if len(fehler):
        text += ["", "Programmfehler (erste 20):"] + [f"  {r.ticker}: {r.fehler}" for r in fehler.head(20).itertuples()]
    open(os.path.join(AUS, f"zusammenfassung_{stand}.txt"), "w", encoding="utf-8").write("\n".join(text) + "\n")
    print("\n".join(text))


if __name__ == "__main__":
    main()
