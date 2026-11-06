"""Probelauf VCP-Scanner Baustein 1 und 2 über alle Titel in daten/kurse: Zonen (Base, Flagge, Konsolidierung,
offen, am Hoch) und die Ampel der Enge. Aufruf im Ordner InvestCockpit: python3 werkzeuge/zonen_lauf.py"""
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
        df = lies(tk)
        k = vz.zone(df)
        e = vz.enge(df, k)
    except Exception as ex:  # noqa: BLE001
        aus.append({'tk': tk, 'fehler': str(ex)})
        continue
    r = {'tk': tk, 'zone': k['zone'], 'enge': e['ampel'], 'kontraktionen': e.get('zahl', 0), 'folge': e.get('folge', ''),
         'abstand_pivot': round(e['abstand'], 1) if 'abstand' in e else None, 'fehlt': ', '.join(e.get('fehlt', []))}
    if k['zone']:
        r.update(name=k['name'], wochen=round(k['wochen'], 1), laenge=k['laenge'], tiefe=round(k['tiefe'], 1),
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
print(df[df.zone == False]['grund'].value_counts().to_string())  # noqa: E712
print('\nEnge:', z['enge'].value_counts().to_string())
print(pd.crosstab(z['name'], z['enge']).to_string())
print('\nKontraktionen:', z['kontraktionen'].value_counts().sort_index().to_string())
print('\nfehlt (gelb):', z[z.enge == 'gelb']['fehlt'].str.split(', ').explode().value_counts().to_string())
g = z[(z.enge == 'grün') & (z.abstand_pivot > -5)].sort_values('abstand_pivot', ascending=False)
print('\ngrün, Kurs bis 5 % unter dem Pivot:', len(g))
print(g[['name', 'wochen', 'tiefe', 'folge', 'abstand_pivot']].head(15).to_string())
