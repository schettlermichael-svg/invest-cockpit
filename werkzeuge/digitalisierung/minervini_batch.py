import cv2, os, json, traceback, pandas as pd, numpy as np, sys
from concurrent.futures import ProcessPoolExecutor
from panels import panels
import bigcharts as b, re
KAT=pd.read_csv('katalog_roh.csv')
FIX={(2680,0):'5.2a',(2693,1):'5.12',(2699,0):'5.18',(2702,0):'5.22',(2726,1):'10.16',(2751,0):'10.43',(2756,0):'10.50'}
import os
W=os.environ.get("BUCHBILDER","/mnt/user-data/uploads/Weiteres Material")+"/"
os.makedirs('mcsv',exist_ok=True); os.makedirs('mov',exist_ok=True)
def eins(i):
    im=cv2.imread(f"{W}IMG_{i}.PNG"); out=[]
    for k,(x,y,w,h) in enumerate(panels(im)):
        c=im[y:y+h,x:x+w].copy()
        try:
            r=KAT[(KAT.seite==i)&(KAT.tafel==k)]
            u=str(r.unterschrift.iloc[0]) if len(r) else ''
            j=re.findall(r'(?:19|20)\d\d',u); jahr=int(j[0]) if j else None
            df,info,(s,wx,kb,weg)=b.lesen(c,jahr)
            df.to_csv(f'mcsv/{i}_{k}.csv',index=False)
            ov=c.copy(); ov[weg]=(ov[weg]*0.5+np.array([0,200,255])*0.5).astype(np.uint8)
            for xx,bb in zip(wx,kb):
                if bb: cv2.line(ov,(xx+2,bb[0]),(xx+2,bb[1]),(255,100,0),2)
            cv2.imwrite(f'mov/{i}_{k}.jpg',cv2.resize(ov,None,fx=0.6,fy=0.6))
            out.append(dict(seite=i,tafel=k,zeilen=len(df),geschaetzt=int(df.geschaetzt.sum()) if len(df) else 0,von=str(df.Datum.iloc[0])[:10] if len(df) else '',**info))
        except Exception as e:
            out.append(dict(seite=i,tafel=k,fehler=repr(e)[:100]))
    return out
if __name__=="__main__":
    alle=[]
    with ProcessPoolExecutor(2) as ex:
        for o in ex.map(eins, range(2674,2768)): alle+=o
    pd.DataFrame(alle).to_csv('m_uebersicht.csv',index=False)
