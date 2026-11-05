"""Druck in der Zone (grüne Null, 05.11.2026): die Zeichen, aus denen der Zustand „an der Schwelle“ entsteht – Tageswerte
zum Vortag, Tages-POC und Lage im Wertbereich der Zone –, dazu die verlassene Zone und die letzten Auslöser. Sie stehen im
Hinweis der Setup-Kachel; die frühere Karte „Strömung in der Zone“ (mit Tagesspannen und Volumen, Druck ohne Richtung)
liegt in _to_delete/gruene_null_titelseite.
"""


def _z(x, st=2):
    """Zahl deutsch: 1234.5 -> 1.234,50"""
    return f"{x:,.{st}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _worte_folge(auf, ab):
    if auf >= 3 and auf > ab:
        return "Käufer rücken vor"
    if ab >= 3 and ab > auf:
        return "Verkäufer rücken vor"
    return "die Front steht"


def druck(a, df):
    """Liste (Name, Pfeil, Text) aus dem Market Profile a: Tageswerte, Tages-POC, Lage im Wertbereich, verlassene Zone,
    letzte Auslöser."""
    import marketprofile as mp
    tage, st = a["tage"], a["stand"][-1]
    aus = []
    folge = [t["bez"] for t in tage[-10:] if t["bez"]]
    letzte5 = folge[-mp.SCHWELLE_TAGE:]
    auf = sum(b in ("hoch", "ueber") for b in letzte5)
    ab = sum(b in ("tief", "unter") for b in letzte5)
    aus.append(("Tageswerte zum Vortag", "↑" if auf > ab else "↓" if ab > auf else "→",
                " ".join(mp.ZEICHEN[b] for b in folge) + f" (10 Tage) · letzte 5: {auf}× höher, {ab}× tiefer – "
                + _worte_folge(auf, ab)))
    p0, p1 = tage[-1 - mp.SCHWELLE_TAGE]["poc"] if len(tage) > mp.SCHWELLE_TAGE else tage[0]["poc"], tage[-1]["poc"]
    aus.append(("Tages-POC (5 Tage)", "↑" if p1 > p0 * 1.01 else "↓" if p1 < p0 * 0.99 else "→",
                f"{_z(p0)} → {_z(p1)} $ ({(p1 / p0 - 1) * 100:+.1f} %)".replace(".", ",")
                + (" – fairer Preis steigt" if p1 > p0 * 1.01 else " – fairer Preis fällt" if p1 < p0 * 0.99
                   else " – fairer Preis bleibt")))
    k = float(df["Close"].iloc[-1])
    lage = (k - st["val"]) / max(st["vah"] - st["val"], 1e-9)
    aus.append(("Lage im Wertbereich der Zone", "↑" if lage >= 2 / 3 else "↓" if lage <= 1 / 3 else "→",
                f"Kurs {_z(k)} $ · Wert {_z(st['val'])}–{_z(st['vah'])} $ – "
                + ("über dem Wert" if lage > 1 else "oberes Drittel" if lage >= 2 / 3 else "unter dem Wert" if lage < 0
                   else "unteres Drittel" if lage <= 1 / 3 else "Mitte: Balance")))
    if a.get("aktiv"):
        ak = a["aktiv"]
        kante = ak["zone"]["vah"] if ak["dir"] == "↑" else ak["zone"]["val"]
        aus.append(("Verlassene Zone", ak["dir"], f"{'VAH' if ak['dir'] == '↑' else 'VAL'} {_z(kante)} $ · Stopp: Schluss "
                                                   f"{'darunter' if ak['dir'] == '↑' else 'darüber'}"))
    sig = a["signale"][-4:]
    if sig:
        aus.append(("Letzte Auslöser", "→", " · ".join(f"{s['art']}{s['dir']} {s['tag']:%d.%m.%Y}" for s in sig)))
    return aus
