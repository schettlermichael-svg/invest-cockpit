"""Gegenbeispiele (Gruppe GN) aus O'Neils Buchcharts: Charts, bei denen das Buch ausdrücklich NICHT kaufen sagt
(fehlerhafte Basen, Angebotsüberhang, scheinbar günstige Aktien, Tops, Leerverkaufsmuster). Die App darf im
angegebenen Zeitfenster nie ein Kaufsetup melden. Kurse: digitalisierte Wochenkurse, als Tageskurse abgeleitet."""
import json, os, sys
import numpy as np, pandas as pd

CSV, QUAL, AUS = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(AUS + "/daten", exist_ok=True)


def tage(w):
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


# nr, Datei, Firma, Fenster (fest oder "top" = Monat des Hochs bis +1 Monat, "nach_top" = 1–3 Monate danach,
# "ende" = letzte 2 Monate des Charts), Begründung aus dem Buch (eigene Worte)
FAELLE = [
    (149, "IMG_2343", "Veritas Software", "2000-10/2000-10", "lockere, fehlerhafte Konsolidierung; verführt zum Kauf im Oktober 2000"),
    (150, "IMG_2344", "Anaren Microwave", "2000-12/2001-01", "breite, fehlerhafte W-Formation; verführt zum Kauf Ende Dezember 2000"),
    (151, "IMG_2345", "Comverse Technology", "2001-01/2001-01", "fehlerhafte Konsolidierung; verführt zum Kauf im Januar 2001"),
    (156, "IMG_2353", "Global Crossing", "ende", "Henkel klettert an den Tiefs entlang nach oben – fehlerhaft"),
    (157, "IMG_2355", "At Home", "ende", "Angebotsüberhang von oben"),
    (164, "IMG_2395", "Halliburton", "1981-09/1981-10", "scheinbar günstig unter dem Hoch – Falle"),
    (165, "IMG_2396", "Comdata Network", "1985-05/1985-05", "nahe den Tiefs – Falle"),
    (152, "IMG_2346", "Houston Oil & Minerals", "1975-06/1975-11", "breite, erratische Formationen vor der richtigen Base"),
    (155, "IMG_2352", "Alexander & Alexander", "ende", "Schulter-Kopf-Schulter-Top"),
    (206, "IMG_2527", "Lucent", "2000-07/2000-09", "Schulter-Kopf-Schulter-Top, Leerverkaufspunkt"),
    (207, "IMG_2528", "Yahoo", "2000-08/2000-09", "Leerverkaufsmuster nach Klimax-Top"),
    (186, "IMG_2492", "Utah Securities", "top", "Klimax-Top"),
    (187, "IMG_2493", "Food Fair", "top", "Klimax-Top mit Kurslücke und breitester Wochenspanne"),
    (188, "IMG_2494", "Topps Chewing Gum", "top", "Verkauf an der oberen Kanalbegrenzung"),
    (189, "IMG_2495", "TCBY", "top", "Klimax-Top, Kanallinie und Splits"),
    (190, "IMG_2496", "Corrections Corp of America", "top", "Klimax-Top und gehäufte Splits"),
    (191, "IMG_2497", "Analog Devices", "top", "Eisenbahnschienen-Top"),
    (192, "IMG_2498", "Human Genome Sciences", "top", "Eisenbahnschienen-Top"),
    (193, "IMG_2499", "Qlogic", "top", "Insel-Top"),
    (194, "IMG_2500", "Hansen Natural", "top", "Top"),
    (196, "IMG_2513", "WorldCom", "nach_top", "Top-Bildung, mehrere Verkaufsgründe"),
    (197, "IMG_2514", "Enron", "nach_top", "Top-Bildung, mehrere Verkaufsgründe"),
    (198, "IMG_2515", "American International Group", "nach_top", "Top-Bildung, mehrere Verkaufsgründe"),
    (199, "IMG_2516", "Citigroup", "nach_top", "Top-Bildung, mehrere Verkaufsgründe"),
    (200, "IMG_2517", "General Motors", "nach_top", "Top-Bildung, mehrere Verkaufsgründe"),
]
q = pd.read_csv(QUAL)
faelle = []
for nr, datei, firma, fenster, warum in FAELLE:
    t = q[q.datei == datei + ".PNG"]
    if not len(t):
        print("fehlt", datei); continue
    t = t.iloc[0]
    w = pd.read_csv(f"{CSV}/{datei}_{int(t.tafel)}.csv", parse_dates=["Datum"])
    vp = w.Vol_px.where(w.Vol_px > 0)
    w["Volume"] = (1e5 * np.exp(2.5 * vp / vp.max())).fillna(vp.min() if vp.notna().any() else 1e5).fillna(1e5)
    d = tage(w)
    if fenster in ("top", "nach_top"):
        top = w.loc[w.High.idxmax(), "Datum"]
        a = top if fenster == "top" else top + pd.DateOffset(months=1)
        e = top + pd.DateOffset(months=1 if fenster == "top" else 3)
        fenster = f"{a:%Y-%m}/{e:%Y-%m}"
    elif fenster == "ende":
        e = w.Datum.iloc[-1]
        fenster = f"{e - pd.DateOffset(months=2):%Y-%m}/{e:%Y-%m}"
    a_, e_ = fenster.split("/")
    if pd.Timestamp(e_ + "-01") < w.Datum.iloc[0] or pd.Timestamp(a_ + "-01") > w.Datum.iloc[-1]:
        print("Fenster außerhalb der Kurse", nr, firma, fenster, w.Datum.iloc[0].date(), w.Datum.iloc[-1].date()); continue
    fid = f"GN{nr}"
    d.to_csv(f"{AUS}/daten/{fid}.csv", index=False)
    faelle.append({"id": fid, "gruppe": "GN", "ticker": "BUCH", "alias": None, "titel": firma,
                   "von": str((d.Datum.iloc[0] + pd.Timedelta(days=430)).date()), "bis": str(d.Datum.iloc[-1].date()),
                   "chart": "Woche", "muster": "Gegenbeispiel: " + warum, "erwartung": "ablehnen", "pivot_ca": fenster,
                   "kennzahlen": {}, "vergleichsindex": None, "img": datei[4:],
                   "notiz": f"O'Neil-Chartkatalog Nr. {nr}; laut Buch nicht kaufen ({warum}). Kurse aus dem Buchchart gelesen "
                            f"(Güte {t.stufe}); geprüft wird das Fenster {fenster}: dort darf kein Kaufsetup erscheinen."})
json.dump({"stand": str(pd.Timestamp.today().date()),
           "quelle": "O'Neil, Wie man mit Aktien Geld verdient – Negativbeispiele, Tops und Leerverkaufsmuster, digitalisiert",
           "hinweis": "Gegenbeispiele messen Fehlalarme: im Fenster darf die App kein Kaufsetup melden (erkannte Muster mit "
                      "Warnzeichen sind erlaubt). Unabhängig davon, ob es die Firma noch gibt.",
           "faelle": faelle}, open(f"{AUS}/faelle_gegen.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(faelle), "Gegenbeispiele"); print([(f["id"], f["titel"], f["pivot_ca"]) for f in faelle])
