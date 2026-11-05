import cv2, re, json, pytesseract, pandas as pd, numpy as np
from concurrent.futures import ProcessPoolExecutor
from panels import panels
import os
W=os.environ.get("BUCHBILDER","/mnt/user-data/uploads/Weiteres Material")+"/"
def seite(i):
    im=cv2.imread(f"{W}IMG_{i}.PNG"); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    d=pytesseract.image_to_data(g,config="--psm 3",output_type=pytesseract.Output.DICT)
    # Zeilen zusammensetzen
    zeilen={}
    for t,b,p,l,x,y,w,h in zip(d['text'],d['block_num'],d['par_num'],d['line_num'],d['left'],d['top'],d['width'],d['height']):
        if t.strip(): zeilen.setdefault((b,p,l),[]).append((x,y,t))
    caps=[]
    keys=sorted(zeilen)
    for idx,k in enumerate(keys):
        ws=zeilen[k]; txt=' '.join(t for _,_,t in ws)
        if re.search(r"Abbildung\s*\d",txt):
            # Text bis zu 3 Folgezeilen dazunehmen
            mehr=' '.join(' '.join(t for _,_,t in zeilen[k2]) for k2 in keys[idx+1:idx+4] if k2[0]==k[0])
            for m in re.finditer(r"Abbildung\s*(\d+)\s*[.,]\s*(\d+[ab]?)",txt):
                x=ws[0][0]; y=ws[0][1]
                caps.append(dict(abb=m.group(1)+'.'+m.group(2),x=x,y=y,text=(txt[m.start():]+' '+mehr)[:260]))
    pn=panels(im)
    out=[]
    for k,(x,y,w,h) in enumerate(pn):
        # Unterschrift: unter der Tafel, im selben Spaltenbereich, am nächsten
        kand=[c for c in caps if c['y']>y+h-40 and x-150<=c['x']<=x+w*0.6]
        c=min(kand,key=lambda c:c['y']) if kand else None
        out.append(dict(seite=i,tafel=k,abb=c['abb'] if c else None,unterschrift=c['text'] if c else None))
    return out
if __name__=="__main__":
    alle=[]
    with ProcessPoolExecutor(2) as ex:
        for o in ex.map(seite, range(2674,2768)): alle+=o
    pd.DataFrame(alle).to_csv('katalog_roh.csv',index=False)
