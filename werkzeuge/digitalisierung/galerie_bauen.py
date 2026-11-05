"""Baut aus den digitalisierten O'Neil-Wochencharts die Galeriegruppe OD:
faelle_oneil_digital.json + daten/OD<nr>.csv (Tageskurse, aus Wochenkursen abgeleitet)."""
import json, os, re, sys
import numpy as np, pandas as pd

KAT = sys.argv[1]; CSV = sys.argv[2]; QUAL = sys.argv[3]; AUS = sys.argv[4]
os.makedirs(AUS + "/daten", exist_ok=True)
MON = {"jan": 1, "feb": 2, "mär": 3, "mar": 3, "mrz": 3, "apr": 4, "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
       "sep": 9, "mae": 3, "maer": 3, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12}
MUSTER = {"Tasse mit Henkel": "Tasse mit Henkel", "Tasse ohne Henkel": "Tasse ohne Henkel", "Doppelboden": "Doppelboden",
          "hohe enge Flagge": "Hohe enge Flagge", "flache Base": "Flache Base", "Base auf Base": "Base auf Base",
          "ansteigende Base": "Ansteigende Base", "Quadrat": "Quadrat", "Untertasse": "Untertasse (Tasse)"}


def pivot_lesen(text):
    """„~Jul/Aug 1885“ -> 1885-07/1885-08; „~Okt 1900“ -> 1900-10 (erster Kaufpunkt zählt)."""
    t = str(text).split(";")[0].lower().replace("maerz", "mär")
    j = re.search(r"(18|19|20)\d\d", t)
    if not j:
        return None
    ms = [MON[m] for m in re.findall(r"[a-zä]{3}", t) if m in MON]
    if "ende" in t and not ms:
        return f"{j.group(0)}-10/{j.group(0)}-12"
    if not ms:                                   # nur das Jahr bekannt
        return f"{j.group(0)}-01/{j.group(0)}-12"
    y = int(j.group(0))
    if len(ms) >= 2 and ms[1] < ms[0]:
        return f"{y - 1}-{ms[0]:02d}/{y}-{ms[1]:02d}"
    return f"{y}-{ms[0]:02d}" if len(ms) == 1 else f"{y}-{ms[0]:02d}/{y}-{ms[1]:02d}"


def tage(w):
    """Wochenbalken -> 5 Tagesbalken. Weg innerhalb der Woche: Vorwochenschluss -> erst das Extrem gegen die
    Richtung -> dann das andere -> Schluss. Wochenhoch und -tief bleiben exakt erhalten."""
    zeilen, vor = [], None
    for _, r in w.iterrows():
        o = vor if vor is not None else (r.High + r.Low) / 2
        o = min(max(o, r.Low), r.High)
        auf = r.Close >= o
        a, b = (r.Low, r.High) if auf else (r.High, r.Low)
        pfad = [o, (o + a) / 2, a, (a + b) / 2, b, r.Close]   # Stützpunkte; Tag i: pfad[i] -> pfad[i+1] (5 Tage)
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


kat = pd.read_csv(KAT, sep=";", encoding="utf-8-sig")
kat = kat[(kat.chartart == "Woche") & kat.muster.isin(MUSTER)]
qual = pd.read_csv(QUAL)
faelle, ohne = [], []
for _, k in kat.iterrows():
    stamm = os.path.splitext(k.datei)[0]
    tafeln = qual[qual.datei == k.datei].sort_values("tafel")
    piv = pivot_lesen(k.kaufpunkt_datum)
    if not len(tafeln) or piv is None:
        ohne.append((k.nr, k.firma, "nicht lesbar" if not len(tafeln) else "Kaufpunkt ohne Datum"))
        continue
    # Tafel: die, deren Zeitraum den Kaufpunkt enthält (Katalogmonate können bis zu 2 Monate zu spät liegen:
    # beim Erfassen galt der Quartalskasten noch als erster statt als letzter Monat)
    p0 = pd.Timestamp(piv.split("/")[0] + "-01") - pd.DateOffset(months=2)
    p1 = pd.Timestamp(piv.split("/")[-1] + "-01") + pd.offsets.MonthEnd(0)
    von_t, bis_t = pd.to_datetime(tafeln.von), pd.to_datetime(tafeln.bis)
    passt = tafeln[(von_t <= p1) & (bis_t >= p0)]
    if not len(passt):
        ohne.append((k.nr, k.firma, f"Kaufpunkt {piv} liegt nicht im gelesenen Chart"))
        continue
    t = passt.iloc[min(int(k.nr_im_bild), len(passt)) - 1] if len(passt) > 1 else passt.iloc[0]
    ende_m = pd.Timestamp(t.bis).to_period("M").to_timestamp()
    piv_neu = f"{p0:%Y-%m}/{min(p1.to_period('M').to_timestamp(), ende_m):%Y-%m}"
    w = pd.read_csv(f"{CSV}/{stamm}_{int(t.tafel)}.csv", parse_dates=["Datum"])
    vp = w.Vol_px.where(w.Vol_px > 0)
    # Volumenskalen im Buch sind logarithmisch; ohne gelesene Skala gilt: volle Feldhöhe ≈ Faktor e^2,5
    w["Volume"] = (1e5 * np.exp(2.5 * vp / vp.max())).fillna(vp.min() if vp.notna().any() else 1e5).fillna(1e5)
    d = tage(w)
    fid = f"OD{int(k.nr)}"
    d.to_csv(f"{AUS}/daten/{fid}.csv", index=False)
    start, ende = d.Datum.iloc[0], d.Datum.iloc[-1]
    faelle.append({"id": fid, "gruppe": "OD", "ticker": "BUCH", "alias": None, "titel": str(k.firma),
                   "von": str((start + pd.Timedelta(days=420 if len(d) >= 300 else 400)).date()), "bis": str(ende.date()),
                   "chart": "Woche",
                   # nur „Tasse“ beschriftet: ob mit oder ohne Henkel, sagt das Buch nicht – beides zählt
                   "muster": "Tasse ohne Henkel oder Tasse mit Henkel"
                   if k.muster == "Tasse ohne Henkel" and "ohne henkel" not in str(k.muster_original).lower() else MUSTER[k.muster],
                   "erwartung": "ablehnen" if re.search(r"negativ|nicht kaufen", str(k.anmerkung), re.I) else "erkennen",
                   "pivot_ca": piv_neu,
                   "kennzahlen": {}, "vergleichsindex": None, "img": stamm.replace("IMG_", ""),
                   "notiz": f"O'Neil-Chartkatalog Nr. {int(k.nr)} ({k.jahr}), aus dem Buchchart digitalisiert "
                            f"(Tafel {int(t.tafel)}, Güte {t.stufe}); Kaufpunkt laut Katalog {k.kaufpunkt_datum}, geprüft {piv_neu}"
                            + (" (nur aufs Jahr bekannt)" if piv.endswith("-12") and piv[5:7] == "01" else "") + f"; Ergebnis {k.ergebnis}"})
json.dump({"stand": str(pd.Timestamp.today().date()),
           "quelle": "O'Neil, Wie man mit Aktien Geld verdient – Wochencharts, digitalisiert (werkzeuge/digitalisierung)",
           "hinweis": "Kurse aus den Buchcharts gelesen (Hoch/Tief geprüft gegen TradingView: Abweichung im Median 0,1–0,6 %). "
                      "Tageskurse aus Wochenkursen abgeleitet: 5 Tage je Woche, Wochenhoch und -tief exakt. "
                      "Volumen nur grob aus der Balkenhöhe. Unabhängig davon, ob es die Firma noch gibt.",
           "faelle": faelle}, open(f"{AUS}/faelle_oneil_digital.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(faelle), "Fälle;", len(ohne), "ohne:", ohne)
print(pd.Series([f["muster"] for f in faelle]).value_counts().to_dict())
