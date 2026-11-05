import json, pandas as pd, numpy as np
def ref_aus(bars):
    return pd.DataFrame({'High':bars['h'],'Low':bars['l'],'Close':bars['c'],'Volume':bars['v']},index=pd.to_datetime(bars['t'],unit='s').normalize())
def vergleich(df, ref, name=''):
    x=df.set_index(pd.to_datetime(df.Datum))
    out=[]
    for s in range(-3,4):
        r=ref.copy(); r.index=r.index  # verschiebe df um s Handelstage
        xs=x.copy(); idx=list(ref.index); pos={t:i for i,t in enumerate(idx)}
        xs=xs[[t in pos for t in xs.index]]
        xs.index=[idx[pos[t]+s] if 0<=pos[t]+s<len(idx) else pd.NaT for t in xs.index]
        j=xs[xs.index.notna()].join(ref,rsuffix='_r',how='inner')
        if len(j)<10: continue
        k=np.median(j.High_r/j.High)
        out.append((s,len(j),round(k,3),100*(j.High*k/j.High_r-1).abs().median(),100*(j.Low*k/j.Low_r-1).abs().median(),100*(j.Close*k/j.Close_r-1).abs().median(), np.corrcoef(np.log(j.Volume+1),np.log(j.Volume_r+1))[0,1]))
    best=min(out,key=lambda o:o[3])
    print(name,'Versatz',best[0],'n',best[1],'Faktor',best[2],'Hoch %.2f%% Tief %.2f%% Schluss %.2f%% VolKorr %.2f'%best[3:])
    return best
