"""Prüfung der Marktrichtung (kern/marktrichtung.py) an den Fällen aus O'Neils Buch.

Aufruf im Ordner InvestCockpit:  python3 werkzeuge/markt_test.py
Der erste Lauf holt S&P 500 und Nasdaq mit Volumen ab 1985 von Yahoo (2 Abrufe).
Geprüft wird für mehrere Schwellen des Follow-Through-Days:
  1. Follow-Through-Days aus dem Buch: erkannt innerhalb von 2 Handelstagen um das Buchdatum
  2. Markt-Tops aus dem Buch: Zustand „Korrektur“ spätestens 30 Handelstage nach dem Hoch
  3. Zur Orientierung: Zahl der Korrekturen je Jahr, Anteil der Tage je Zustand, gescheiterte FTDs
Ergebnis: Terminal und werkzeuge/markt_test.txt
"""
import os
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import marktdaten as md      # noqa: E402
import marktrichtung as mr   # noqa: E402

FTD_FAELLE = [("1990-10-18", "Boden Okt. 1990 (Buch: Tag 5)"),
              ("1998-09-08", "1. Versuch Sept. 1998 (Buch: Tag 5, scheiterte)"),
              ("1998-10-15", "Boden Okt. 1998 (Buch: Tag 5/6)"),
              ("2003-03-17", "Boden März 2003, Nasdaq (Buch: Tag 4)"),
              ("2009-03-12", "Boden März 2009 (IBD-Datum)")]
TOP_FAELLE = [("1990-07-16", "S&P 500 Juli 1990"), ("1994-02-02", "S&P 500 Febr. 1994"),
              ("1998-07-17", "S&P 500 Juli 1998"), ("2000-03-10", "Nasdaq März 2000"),
              ("2000-09-01", "Nasdaq Sept. 2000"), ("2007-10-31", "Nasdaq Okt. 2007")]
SCHWELLEN = [1.0, 1.25, 1.5, 1.7]


def pruefen(daten, schwelle, aus):
    mr.FTD_SCHWELLE = schwelle
    v = mr.verlauf(daten)
    tage = pd.DatetimeIndex([x["tag"] for x in v])
    ftds = sorted({x["ftd"]["tag"] for x in v if x["ftd"]})
    treffer = 0
    aus.append(f"\nFollow-Through-Schwelle +{schwelle} %")
    for datum, name in FTD_FAELLE:
        i = tage.searchsorted(pd.Timestamp(datum))
        nah = [f for f in ftds if abs(tage.searchsorted(f) - i) <= 2]
        ok = bool(nah)
        treffer += ok
        if nah:
            info = next(x["ftd"] for x in v if x["ftd"] and x["ftd"]["tag"] == nah[0])
            text = f"FTD {nah[0]:%d.%m.%Y} ({info['index']}, Tag {info['tag_nr']}, +{info['plus']} %)"
        else:
            vorher = [f for f in ftds if f <= pd.Timestamp(datum) + pd.Timedelta(days=60)]
            text = f"kein FTD in ±2 Tagen; letzter davor {vorher[-1]:%d.%m.%Y}" if vorher else "kein FTD"
        aus.append(f"  {'🟢' if ok else '🔴'} {name:44} {text}")
    for datum, name in TOP_FAELLE:
        i = tage.searchsorted(pd.Timestamp(datum))
        vorher = v[max(i - 6, 0)]["zustand"]
        korr = next((k for k in range(max(i - 5, 0), min(i + 31, len(v))) if v[k]["zustand"] == "Korrektur"), None)
        ok = korr is not None and vorher != "Korrektur"
        treffer += ok
        meiste = max(len(d) for d in v[i]["dt"].values())
        text = (f"vor dem Hoch: {vorher}, am Hoch {meiste} Distributionstage; Korrektur ab {tage[korr]:%d.%m.%Y} "
                f"({korr - i:+d} Tage)" if korr is not None else f"vor dem Hoch: {vorher}; keine Korrektur in 30 Tagen")
        aus.append(f"  {'🟢' if ok else '🔴'} {name:44} {text}")
    # Orientierung
    z = pd.Series([x["zustand"] for x in v], index=tage)
    z = z[z.index >= "1990-01-01"]
    wechsel = z[(z == "Korrektur") & (z.shift() != "Korrektur")]
    jahre = (z.index[-1] - z.index[0]).days / 365.25
    gescheitert = 0
    for f in ftds:
        k = tage.searchsorted(f)
        if f >= pd.Timestamp("1990-01-01") and any(v[j]["zustand"] == "Korrektur" for j in range(k, min(k + 25, len(v)))):
            gescheitert += 1
    anzahl_ftd = sum(1 for f in ftds if f >= pd.Timestamp("1990-01-01"))
    anteil = z.value_counts(normalize=True) * 100
    aus.append(f"  Orientierung seit 1990: {len(wechsel) / jahre:.1f} Korrekturen je Jahr, {anzahl_ftd / jahre:.1f} FTD je Jahr, "
               f"davon {gescheitert / max(anzahl_ftd, 1) * 100:.0f} % binnen 25 Tagen gescheitert; Tage: "
               + ", ".join(f"{k} {w:.0f} %" for k, w in anteil.items()))
    return treffer


def main():
    daten = {n: md.yahoo_ohlc(tk) for n, tk in mr.INDIZES.items()}
    aus = ["Daten: " + ", ".join(f"{n} {d.index[0]:%d.%m.%Y}–{d.index[-1]:%d.%m.%Y}, Volumen ab "
                                  f"{d.index[(d['Volume'] > 0).argmax()]:%Y}" for n, d in daten.items())]
    gewaehlt = mr.FTD_SCHWELLE
    ergebnis = {s: pruefen(daten, s, aus) for s in SCHWELLEN}
    gesamt = len(FTD_FAELLE) + len(TOP_FAELLE)
    aus.append("\nTreffer je Schwelle: " + ", ".join(f"+{s} %: {t}/{gesamt}" for s, t in ergebnis.items()))
    mr.FTD_SCHWELLE = gewaehlt
    aus.append(f"Gewählt: +{gewaehlt} %")
    heute = mr.richtung()
    aus.append(f"\nHeute: {heute['zustand']} seit {heute['seit']:%d.%m.%Y} · {heute['text']}"
               + "".join(f" · ⚠ {t}" for _, t in heute["zeichen"]))
    text = "\n".join(aus)
    print(text)
    with open(os.path.join(HIER, "markt_test.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
