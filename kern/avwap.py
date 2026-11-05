"""AVWAP-Liste (Schritt 7, 04.11.2026, aus dem SEPA-Scanner übernommen): Anchored VWAP von festen Ankern, alle zugleich –
kein Auswahlfeld. Anker innerhalb der aktuellen Zone (Market Profile), sonst der letzten 60 Tage:
  Zonenbeginn · Zonentief · größtes Volumen in der Zone · Deckel (Zonenhoch) · 52-Wochen-Hoch
Ampel: Kurs über allen grün, dazwischen gelb, unter allen rot (long gelesen; short umgekehrt).
"""
import numpy as np


def avwap(df, i):
    t = df.iloc[i:]
    tp = (t["High"] + t["Low"] + t["Close"]) / 3
    s = float(t["Volume"].sum())
    return float((tp * t["Volume"]).sum() / s) if s > 0 else None


def liste(df, erk):
    n = len(df)
    w = erk.get("werte") or {}
    a = int(w["start_index"]) if "start_index" in w else max(0, n - 60)
    b = df.iloc[a:]
    anker = [("Zonenbeginn" if "start_index" in w else "Beginn 60 Tage", a),
             ("Zonentief", a + int(np.argmin(b["Low"].to_numpy(float)))),
             ("größtes Volumen", a + int(np.argmax(b["Volume"].to_numpy(float)))),
             ("Deckel (Zonenhoch)", a + int(np.argmax(b["High"].to_numpy(float))))]
    j = max(0, n - 252)
    anker.append(("52-Wochen-Hoch", j + int(np.argmax(df["High"].to_numpy(float)[j:]))))
    k = float(df["Close"].iloc[-1])
    aus, gesehen = [], set()
    for name, i in anker:
        if i in gesehen or i >= n - 1:
            continue
        gesehen.add(i)
        v = avwap(df, i)
        if v:
            aus.append({"name": name, "tag": df.index[i], "wert": v, "abstand": (k / v - 1) * 100})
    ueber = [x["abstand"] >= 0 for x in aus]
    ampel = "grün" if ueber and all(ueber) else "rot" if ueber and not any(ueber) else "gelb"
    return {"anker": aus, "ampel": ampel, "ueber": sum(ueber), "von": len(ueber)}
