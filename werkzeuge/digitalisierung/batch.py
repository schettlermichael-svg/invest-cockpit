import sys, os, traceback, time, cv2, numpy as np, pandas as pd, digitalisieren as d
from concurrent.futures import ProcessPoolExecutor
W = os.environ.get("BUCHBILDER", "/mnt/user-data/uploads/Weiteres Material") + "/"
AUS = os.environ.get("DIGI_AUS", "batch"); os.makedirs(AUS + "/ov", exist_ok=True); os.makedirs(AUS + "/csv", exist_ok=True)

def eins(datei):
    zeilen = []
    try:
        res = d.digitalisieren(W + datei)
    except Exception as e:
        return [{"datei": datei, "tafel": -1, "fehler": repr(e)[:120]}]
    for i, (df, info, img, (a, wx, kb, po, pu, weg)) in enumerate(res):
        stem = f"{os.path.splitext(datei)[0]}_{i}"
        df.to_csv(f"{AUS}/csv/{stem}.csv", index=False)
        ov = img.copy(); ov[weg] = (ov[weg] * 0.6 + np.array([0, 200, 255]) * 0.4).astype(np.uint8)
        for x, b in zip(wx, kb):
            if b:
                cv2.line(ov, (x + 4, b[0]), (x + 4, b[1]), (255, 120, 0), 2); cv2.line(ov, (x + 4, b[2]), (x + 9, b[2]), (0, 170, 0), 2)
        cv2.imwrite(f"{AUS}/ov/{stem}.jpg", cv2.resize(ov, None, fx=0.5, fy=0.5), [cv2.IMWRITE_JPEG_QUALITY, 80])
        z = dict(datei=datei, tafel=i, zeilen=len(df), **info)
        if len(df):
            z.update(von=str(df.Datum.iloc[0])[:10], bis=str(df.Datum.iloc[-1])[:10], pmin=round(df.Low.min(), 3), pmax=round(df.High.max(), 3),
                     sprung=round(float((np.log(df.High).diff().abs()).max()), 2))
        zeilen.append(z)
    return zeilen

if __name__ == "__main__":
    k = pd.read_csv(os.environ.get("KATALOG", "../../pruefgalerie/oneil/chartkatalog.csv"), sep=";", encoding="utf-8-sig")
    dateien = sorted(k[k.chartart == "Woche"].datei.unique())
    t = time.time(); alle = []
    with ProcessPoolExecutor(max(2, os.cpu_count() - 1)) as ex:
        for z in ex.map(eins, dateien):
            alle += z
    pd.DataFrame(alle).to_csv(AUS + "/uebersicht.csv", index=False)
    print(len(dateien), "Dateien", len(alle), "Tafeln", round(time.time() - t), "s")
