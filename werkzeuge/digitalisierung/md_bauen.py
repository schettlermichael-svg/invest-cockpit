"""Galeriegruppe MD: Minervinis Buchcharts (BigCharts), digitalisiert. Je Buchfall aus faelle_buch.json und je
passender Abbildung ein Fall – unabhängig davon, ob es die Firma noch gibt."""
import json, re, os, sys
import numpy as np, pandas as pd

BUCH, AUS = sys.argv[1], sys.argv[2]
os.makedirs(AUS + "/daten", exist_ok=True)
FIX = {(2680, 0): '5.2a', (2693, 1): '5.12', (2699, 0): '5.18', (2702, 0): '5.22', (2726, 1): '10.16',
       (2751, 0): '10.43', (2756, 0): '10.50'}
GLEICH = {"FSID": "FSII", "MAG": "MGA", "NGA": "MGA", "BREW": "HOOK", "TASR": "AXON", "ANSC": "AMSC", "ILNN": "ILMN",
          "T200": "TZOO", "AFEY": "AFFY", "SHN": "SWN"}


def tage(w):
    """Wochenbalken -> 5 Tagesbalken; Wochenhoch und -tief bleiben exakt (wie Gruppe OD)."""
    zeilen, vor = [], None
    for _, r in w.iterrows():
        o = vor if vor is not None else (r.High + r.Low) / 2
        o = min(max(o, r.Low), r.High)
        a, b = (r.Low, r.High) if r.Close >= o else (r.High, r.Low)
        pfad = [o, a, (a + b) / 2, b, (b + r.Close) / 2, r.Close]
        for i in range(5):
            op, cl = pfad[i], pfad[i + 1]
            hi, lo = max(op, cl), min(op, cl)
            if hi == lo:                          # kein Tag ohne Spanne (sonst schlägt die Datenprüfung an): 0,05 %
                hi, lo = hi * 1.00025, lo * 0.99975
            hi, lo = min(hi, r.High), max(lo, r.Low)  # Wochenhoch und -tief bleiben die Grenze
            zeilen.append({"Datum": r.Datum + pd.Timedelta(days=i), "Open": op, "High": hi, "Low": lo,
                           "Close": cl, "Volume": r.Volume / 5})
        vor = r.Close
    return pd.DataFrame(zeilen)


u = pd.read_csv(os.environ.get("UEBERSICHT", "m_uebersicht.csv")); u = u[u.fehler.isna()]
k = pd.read_csv("katalog_roh.csv")
for (s_, t_), a_ in FIX.items():
    k.loc[(k.seite == s_) & (k.tafel == t_), "abb"] = a_
u = u.merge(k, on=["seite", "tafel"], how="left")
u = u.drop_duplicates(subset=["abb"], keep="first")          # Mehrfachfotos derselben Abbildung
buch = json.load(open(BUCH))["faelle"]
faelle, zuordnung = [], []
for _, r in u.iterrows():
    if pd.isna(r.abb):
        continue
    tk = re.findall(r"\(([A-Z]{1,5})\)", str(r.unterschrift))
    tk = tk[0] if tk else str(r.ticker)
    tk = GLEICH.get(tk, tk)
    df = pd.read_csv(f"mcsv/{r.seite}_{r.tafel}.csv", parse_dates=["Datum"])
    if len(df) < 15:
        continue
    kurz = r.art == "Tag" and len(df) < 40          # zu kurz für eine Base (z. B. ein Monat Tageskurse)
    a, e = df.Datum.iloc[0], df.Datum.iloc[-1]
    passend = [f for f in buch if f.get("ticker") == tk and f.get("von") and
               pd.Timestamp(f["von"]) <= e + pd.Timedelta(days=60) and pd.Timestamp(f["bis"]) >= a - pd.Timedelta(days=60)]
    for f in passend:
        if r.art == "Woche":
            d = tage(df)
        else:
            d = df[["Datum", "High", "Low", "Close", "Volume"]].copy()
            d.insert(1, "Open", d.Close.shift(1).fillna((d.High + d.Low) / 2).clip(d.Low, d.High))
        jung = bool(re.search(r"IPO|Primaer|junges", f.get("muster") or ""))
        if kurz and not jung:
            continue
        fid = f"MD_{f['id']}_{str(r.abb).replace('.', '_')}"
        d.to_csv(f"{AUS}/daten/{fid}.csv", index=False)
        neu = dict(f)
        neu.update(id=fid, gruppe="MD", chart="Woche" if r.art == "Woche" else "Tag",
                   von=f["von"] if jung else str((d.Datum.iloc[0] + pd.Timedelta(days=430)).date()),
                   img=str(r.seite),
                   notiz=f"Minervini, Abb. {r.abb} (Foto IMG_{r.seite}, Tafel {r.tafel}), aus dem Buchchart gelesen; "
                         f"Datum aus {r.datum_aus}; Fall {f['id']}")
        faelle.append(neu)
        zuordnung.append((fid, f["id"], r.abb, tk, str(a.date()), str(e.date()), len(d)))
json.dump({"stand": str(pd.Timestamp.today().date()),
           "quelle": "Minervini, Handeln wie ein Market Wizard – Abbildungen Kap. 5 und 10 (BigCharts), digitalisiert",
           "hinweis": "Kurse aus den Buchcharts gelesen. Gegenprobe mit TradingView: MELI, NFLX, DECK, CRUS, CROX – Hoch/Tief "
                      "im Median 0,04–1,1 %, Datum meist tagesgenau (eine von sieben Tafeln einen Tag versetzt). "
                      "Wochencharts als Tageskurse abgeleitet. Unabhängig davon, ob es die Firma noch gibt.",
           "faelle": faelle}, open(f"{AUS}/faelle_minervini_digital.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
z = pd.DataFrame(zuordnung, columns=["md", "fall", "abb", "ticker", "von", "bis", "tage"])
print(z.to_string()); print(len(faelle), "Fälle")
