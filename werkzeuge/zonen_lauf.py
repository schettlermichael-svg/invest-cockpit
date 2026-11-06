"""Probelauf VCP-Scanner Baustein 1 über alle Titel in daten/kurse: Zahl der Basen, Flaggen, Konsolidierungen,
offenen Zonen und Titel am Hoch. Aufruf im Ordner InvestCockpit: python3 werkzeuge/zonen_lauf.py"""
import json
import os
import sys
sys.path.insert(0, 'kern')
import pandas as pd
import vcp_zone as vz


def lies(tk):
    teile = [pd.read_csv(p, index_col=0, parse_dates=True) for p in (f'daten/lang/{tk}.csv', f'daten/kurse/{tk}.csv')
             if os.path.exists(p)]
    d = pd.concat(teile)
    d = d[~d.index.duplicated(keep='last')].sort_index()
    return d[['Open', 'High', 'Low', 'Close', 'Volume']].iloc[-756:]


aus = []
for f in sorted(os.listdir('daten/kurse')):
    if not f.endswith('.csv'):
        continue
    tk = f[:-4]
    try:
        k = vz.zone(lies(tk))
    except Exception as e:  # noqa: BLE001
        aus.append({'tk': tk, 'fehler': str(e)})
        continue
    r = {'tk': tk, 'zone': k['zone']}
    if k['zone']:
        v = k['vorgeschichte']
        r.update(name=k['name'], wochen=round(k['wochen'], 1), laenge=k['laenge'], tiefe=round(k['tiefe'], 1),
                 abstand=round(k['abstand'], 1), vg=v['art'], vg_pct=round(v['prozent'], 1),
                 innen=bool(k.get('innen')))
    else:
        r['grund'] = k['grund']
    aus.append(r)
json.dump(aus, open('/tmp/zonen_alle.json', 'w'))
df = pd.DataFrame(aus)
print(len(df), 'Titel')
z = df[df.zone == True]  # noqa: E712
print(z['name'].value_counts().to_string())
print('Flagge in der Zone:', int(z['innen'].sum()))
print(z['laenge'].value_counts().to_string())
print(df[df.zone == False]['grund'].value_counts().to_string())  # noqa: E712
