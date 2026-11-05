import os
import cv2, sys, numpy as np, pandas as pd, importlib, digitalisieren as d
def tv(modul):
    m=importlib.import_module(modul)
    n=min(len(m.h),len(m.l))
    t=pd.to_datetime([m.t0+7*86400*i for i in range(n)],unit='s').normalize()
    t=t-pd.to_timedelta(t.dayofweek,unit='D')
    return pd.DataFrame({'High':m.h[:n],'Low':m.l[:n]},index=t)
def pruef(pfad, nr, modul, drehen=True):
    ref=tv(modul); best=None
    for df,*_ in d.digitalisieren(pfad):
        df=df.set_index(pd.to_datetime(df['Datum'])) if 'Datum' in df else df
        df.index=pd.to_datetime(df.index); n=len(df.index.intersection(ref.index))
        if best is None or n>best[0]: best=(n,df)
    df=best[1]; df.index=df.index-pd.to_timedelta(df.index.dayofweek,unit='D')
    j=df.join(ref,rsuffix='_tv',how='inner').dropna()
    k=np.median(j['High_tv']/j['High'])
    eh=(j['High']*k/j['High_tv']-1).abs(); el=(j['Low']*k/j['Low_tv']-1).abs()
    print(modul, 'Wochen', len(df), 'gemeinsam', len(j), 'High med %.2f%%'%(100*eh.median()), 'Low med %.2f%%'%(100*el.median()), 'p90 %.1f/%.1f%%'%(100*eh.quantile(.9),100*el.quantile(.9)))
W = os.environ.get("BUCHBILDER", "/mnt/user-data/uploads/Weiteres Material") + "/"
def pruef_amzn():
    ref=tv('tv_amzn')*240
    df=d.digitalisieren(W+'IMG_2535.PNG')[1][0]; df=df.set_index(pd.to_datetime(df['Datum']))
    j=df.join(ref,rsuffix='_tv',how='inner')
    print('tv_amzn Wochen',len(df),'gemeinsam',len(j),'High med %.2f%%'%(100*(j.High/j.High_tv-1).abs().median()),'Low med %.2f%%'%(100*(j.Low/j.Low_tv-1).abs().median()))
if __name__=="__main__": pruef(W+"IMG_2293.PNG",0,"tv_aapl"); pruef(W+"IMG_2247.PNG",0,"tv_csco"); pruef_amzn()

def versatz(pfad, modul):
    ref=tv(modul)
    for df,*_ in d.digitalisieren(pfad):
        df=df.set_index(pd.to_datetime(df['Datum'])) if 'Datum' in df else df
        df.index=pd.to_datetime(df.index); df.index=df.index-pd.to_timedelta(df.index.dayofweek,unit='D')
        for s in range(-3,4):
            dd=df.copy(); dd.index=dd.index+pd.Timedelta(weeks=s)
            j=dd.join(ref,rsuffix='_tv',how='inner').dropna()
            if len(j)<10: continue
            k=np.median(j['High_tv']/j['High']); e=(j['High']*k/j['High_tv']-1).abs().median()
            print(modul,s,len(j),'%.2f%%'%(100*e))
