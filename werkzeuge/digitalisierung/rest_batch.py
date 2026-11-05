"""Zweiter Durchgang für die Minervini-Tafeln, die der BigCharts-Leser nicht lesen konnte:
1) BigCharts-Leser auf der nach außen erweiterten Tafel (Kopf und Achsen lagen außerhalb des erkannten Rahmens),
2) allgemeiner Leser (StockCharts und Charts mit Zeitachse ohne Kopfdatum), auf Tafel und erweiterter Tafel.
Ein Ergebnis zählt nur mit Gütegrenzen: gelesene Balken >= 60 %, beim allgemeinen Leser außerdem mindestens
8 stimmende Tagesmarken und mindestens die Hälfte aller Marken."""
import cv2, re, os, json, traceback, pandas as pd, numpy as np
from panels import panels, erweitern
import bigcharts as b, allgemein as a
W = os.environ.get("BUCHBILDER", "/mnt/user-data/uploads/Weiteres Material") + "/"
KAT = pd.read_csv('katalog_roh.csv')
U = pd.read_csv('m_uebersicht.csv')
offen = U[U.fehler.notna()][['seite', 'tafel']].values.tolist()
os.makedirs('mcsv', exist_ok=True); os.makedirs('aov', exist_ok=True)
aus = []
for i, k in offen:
    r = KAT[(KAT.seite == i) & (KAT.tafel == k)]; u = str(r.unterschrift.iloc[0]) if len(r) else ''
    jahre = [int(x) for x in re.findall(r'(?:19|20)\d\d', u)[:2]]
    im = cv2.imread(f'{W}IMG_{i}.PNG'); bx = panels(im)[k]
    versuche = []
    for nm, box in (('Tafel', bx), ('erweitert', erweitern(im, bx))):
        x, y, w, h = box; c = im[y:y + h, x:x + w]
        for leser in ('BigCharts', 'allgemein'):
            try:
                if leser == 'BigCharts':
                    df, info, _ = b.lesen(c, jahre[-1] if jahre else None)
                    ok = info['gelesen'] >= 0.6 * info['balken']
                    guete = info['gelesen'] / info['balken']
                else:
                    df, info, _ = a.lesen(c, jahre or None)
                    ok = (info['gelesen'] >= 0.6 * info['balken'] and info['marken_passend'] >= 8
                          and info['marken_passend'] >= 0.38 * info['marken'])
                    guete = info['marken_passend'] / info['marken']
                versuche.append((ok, guete, nm, leser, df, info))
            except Exception as e:
                versuche.append((False, -1, nm, leser, None, {'fehler': repr(e)[:80]}))
    gut = [v for v in versuche if v[0]]
    if gut:
        ok, guete, nm, leser, df, info = max(gut, key=lambda v: v[1])
        df.to_csv(f'mcsv/{i}_{k}.csv', index=False)
        zeile = dict(seite=i, tafel=k, zeilen=len(df), geschaetzt=int(df.geschaetzt.sum()), von=str(df.Datum.iloc[0])[:10],
                     **{kk: info.get(kk) for kk in ('ticker', 'art', 'ende', 'achse', 'achse_rest_px', 'achse_n', 'balken', 'gelesen')},
                     datum_aus=(info.get('datum_aus') or '') + f' ({leser}, {nm})', leser=leser,
                     marken=info.get('marken'), marken_passend=info.get('marken_passend'), kalender=info.get('kalender'))
    else:
        zeile = dict(seite=i, tafel=k, fehler='; '.join(f"{v[3]}/{v[2]}: {v[5].get('fehler', 'Güte zu gering')}" for v in versuche)[:300])
    aus.append(zeile); print(i, k, u[:45], {kk: zeile.get(kk) for kk in ('leser', 'ende', 'zeilen', 'marken_passend', 'marken', 'gelesen', 'balken', 'fehler')}, flush=True)
pd.DataFrame(aus).to_csv('rest_uebersicht.csv', index=False)
