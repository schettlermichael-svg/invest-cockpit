import cv2, numpy as np
def panels(im):
    g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    b=(g<200).astype(np.uint8)*255
    hz=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(250,1)))
    vt=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,150)))
    m=cv2.dilate(hz|vt,np.ones((9,9),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    out=[]
    for k in range(1,n):
        x,y,w,h,a=st[k]
        if w>400 and h>300: out.append((x,y,w,h))
    # verschachtelte entfernen
    out=[a for a in out if not any(b!=a and b[0]<=a[0] and b[1]<=a[1] and b[0]+b[2]>=a[0]+a[2] and b[1]+b[3]>=a[1]+a[3] for b in out)]
    return sorted(out,key=lambda r:(r[0]//300, r[1]))


def erweitern(im, box, leer=14):
    """Tafel nach außen erweitern, solange Tinte folgt (Kopfzeile, Achsenbeschriftung, Volumenfeld außerhalb des
    erkannten Rahmens). Stopp nach `leer` Zeilen bzw. Spalten ohne Tinte."""
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    H, W = g.shape
    x, y, w, h = map(int, box)
    tinte = g < 150

    def wachsen(start, schritt, grenze, linie):
        p, frei, letzt = start, 0, start
        while 0 <= p + schritt < grenze and frei < leer:
            p += schritt
            if linie(p).sum() >= 2:
                letzt, frei = p, 0
            else:
                frei += 1
        return letzt

    unten = wachsen(y + h - 1, 1, H, lambda r: tinte[r, x:x + w])
    oben = wachsen(y, -1, H, lambda r: tinte[r, x:x + w])
    rechts = wachsen(x + w - 1, 1, W, lambda q: tinte[oben:unten, q])
    links = wachsen(x, -1, W, lambda q: tinte[oben:unten, q])
    return (links, oben, rechts - links + 1, unten - oben + 1)
