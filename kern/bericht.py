"""Lagebericht über alle Ebenen (Micky 26.11.2026: „so und genauso möchte ich in der app informiert werden“ – die
Analyse von HWM über Woche, Tag, 4 Stunden und Stunde). Ein System mit wenig Variablen (Sharp): jede Ebene wird mit
denselben Regeln gelesen – Livermores Notizbuch auf den Kerzen der Ebene – und in Sätzen erzählt.

  Je Ebene  Lage (🟢 Vormarsch · 🟡 Gefechtspause · 🔴 Rückzug), letzte abgeschlossene Kerze, Spanne (Front und
            Unterkante) mit dem Drittel des Kurses, die Treppe der letzten Pivotal Points (Hochs und Tiefs steigend
            oder fallend), die nächste Decke und der nächste Boden mit ihren Abprallern, die alte Plattform
            (livermore.gefallene, Rollentausch) und in der Woche der Abstand zum Jahreshoch.
  Leiter    alle Stellungen aller Ebenen auf einer Preisachse (oberflaeche/leiter.py).
  Urteil    die drei Tore (tore.py).
  Beobachten  long und short: der erste Schritt auf der Stunde, der Auslöser auf dem Tag (Front bzw. Unterkante oder
            unser Setup), der Weg danach; Gegenzeichen = was auf den Ebenen gegen die Richtung spricht.

Kein neuer Rechenweg: Notizbuch, Frontkarte, Stellungen, Ort, Tore – alles aus livermore.py und tore.py.
"""
import livermore
import tore
import vcp_zone
from masse import JAHR_WOCHEN   # Abstand zum Hoch der letzten 52 Wochen – eine Quelle

TREPPE_PUNKTE = 3          # die letzten 3 Hochs und 3 Tiefs des Notizbuchs bilden die Treppe (zwei Stufen je Seite)
TREPPE_WORT = {("auf", "auf"): "Treppe aufwärts", ("ab", "ab"): "Treppe abwärts",
               ("ab", "auf"): "eingequetscht – fallende Hochs, steigende Tiefs",
               ("auf", "ab"): "die Spanne weitet sich"}


def _zahl(x, n=2):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pz(x, kurs):
    return tore._pz((x / kurs - 1) * 100)


def _gang(werte):
    """auf, ab oder None (nicht durchgehend) für eine Folge von Preisen."""
    if len(werte) < 2:
        return None
    if all(b > a for a, b in zip(werte, werte[1:])):
        return "auf"
    if all(b < a for a, b in zip(werte, werte[1:])):
        return "ab"
    return None


def treppe(nb):
    """Die letzten TREPPE_PUNKTE Hochs und Tiefs des Notizbuchs → {hochs, tiefs, gang_h, gang_t, wort}."""
    hochs = [p_["preis"] for p_ in nb["pivotal"] if p_["art"] == "hoch"][-TREPPE_PUNKTE:]
    tiefs = [p_["preis"] for p_ in nb["pivotal"] if p_["art"] == "tief"][-TREPPE_PUNKTE:]
    gh, gt = _gang(hochs), _gang(tiefs)
    return {"hochs": hochs, "tiefs": tiefs, "gang_h": gh, "gang_t": gt, "wort": TREPPE_WORT.get((gh, gt))}


def _kerze(name, df, laufend):
    """Farbe der letzten abgeschlossenen Kerze der Ebene: Woche und Tag wie die Zwei-Kerzen-Regel (tore.zwei_kerzen),
    4 Stunden und Stunde die letzte Kerze."""
    if name in ("Woche", "Tag"):
        zk = tore.zwei_kerzen(df, laufend)
        return (zk or {}).get("woche" if name == "Woche" else "tag")
    return tore._farbe(float(df["Open"].iloc[-1]), float(df["Close"].iloc[-1]))


def ebene(name, df, tage=None, laufend=False):
    """Eine Ebene in Zahlen → dict oder None (zu wenig Kerzen). df = Kerzen der Ebene, tage = Tageskerzen (für die
    Kerzenfarbe der Woche)."""
    if df is None or not len(df):
        return None
    df = df.dropna(subset=["High", "Low", "Close"])
    nb = livermore.notizbuch(df)
    if not nb:
        return None
    fr = livermore.front(df, nb)
    ot = livermore.ort(df, nb, fr)
    kurs = fr["kurs"]
    gr = ot["gruppen"]
    decke = min((g for g in gr if g["preis"] > kurs), key=lambda g: g["preis"], default=None)
    boden = max((g for g in gr if g["preis"] < kurs), key=lambda g: g["preis"], default=None)
    alt = livermore.gefallene(df, nb)
    hoch = None
    if name == "Woche":
        h_ = float(df["High"].iloc[-JAHR_WOCHEN:].max())
        hoch = {"preis": h_, "abstand": (kurs / h_ - 1) * 100}
    return {"name": name, "df": df, "nb": nb, "lage": livermore.lage(nb["spalte"]), "spalte": nb["spalte"],
            "kerze": _kerze(name, tage if name == "Woche" and tage is not None else df, laufend),
            "front": (fr["oben"] or {}).get("preis"), "unterkante": (fr["unten"] or {}).get("preis"),
            "drittel": ot["drittel"], "chop": ot["chop"], "weg": ot["weg"], "gruppen": gr, "kurs": kurs,
            "decke": decke, "boden": boden, "alt": {r_: next((g for g in alt if g["rolle"] == r_), None)
                                                    for r_ in ("decke", "boden")},
            "treppe": treppe(nb), "hoch": hoch, "atr": float(vcp_zone.atr(df).iloc[-1] or 0)}


IM = {"unteres Drittel": "im unteren Drittel", "Mitte": "in der Mitte", "oberes Drittel": "im oberen Drittel"}


def _stelle(g, wort, kurs, kante=None, atr=0):
    """„Decke 212,00 (+0,4 % · 2 🛡)“; liegt sie an der Kante (innerhalb ½ ATR), heißt sie „Decke = Front“."""
    if not g:
        return ""
    pr = g["preis"]
    if kante and abs(pr - kante) <= atr * livermore.STELLUNG_ATR:
        wort += " = Front" if wort == "Decke" else " = Unterkante"
    zus = [_pz(pr, kurs)] + ([f'{g["abpraller"]} 🛡'] if g.get("abpraller") else []) + (
        [f'{g["gewicht"]} Punkte'] if g.get("gewicht", 1) > 1 else [])
    return f'{wort} {_zahl(pr)} ({" · ".join(zus)})'


def _plattform(g):
    return _zahl(g["unten"]) if g["unten"] == g["oben"] else f'{_zahl(g["unten"])}–{_zahl(g["oben"])}'


def saetze(b):
    """Die Ebene in zwei, drei Sätzen – immer in derselben Reihenfolge: Spanne, Treppe, Decke und Boden, alte
    Plattform, (Woche) Jahreshoch."""
    if not b:
        return []
    kurs, aus = b["kurs"], []
    if b["front"] and b["unterkante"]:
        aus.append(f'Spanne {_zahl(b["unterkante"])}–{_zahl(b["front"])}, Kurs {_zahl(kurs)} '
                   + IM.get(b["drittel"], b["drittel"] or "") + "."
                   + (" ⚪ Chop: viele Stellungen in der Spanne." if b["chop"] else ""))
    elif b["front"]:
        aus.append(f'Front {_zahl(b["front"])} ({_pz(b["front"], kurs)}), keine Unterkante mehr.')
    elif b["unterkante"]:
        aus.append(f'Unterkante {_zahl(b["unterkante"])} ({_pz(b["unterkante"], kurs)}), keine Front mehr.')
    tr = b["treppe"]
    if len(tr["hochs"]) > 1 and len(tr["tiefs"]) > 1:
        pf = lambda xs: " → ".join(_zahl(x) for x in xs)                                   # noqa: E731
        aus.append(f'Hochs {pf(tr["hochs"])} · Tiefs {pf(tr["tiefs"])}' + (f': {tr["wort"]}.' if tr["wort"] else "."))
    st_ = [x for x in (_stelle(b["decke"], "Decke", kurs, b["front"], b["atr"]),
                       _stelle(b["boden"], "Boden", kurs, b["unterkante"], b["atr"])) if x]
    if not b["decke"]:
        st_.insert(0, "✈️ keine Decke – freie Bahn nach oben")
    if not b["boden"]:
        st_.append("✈️↓ kein Boden – freie Bahn nach unten")
    aus.append(" · ".join(st_) + ".")
    for r_, wort in (("decke", "über dem Kurs: gebrochene Unterstützung, jetzt Decke"),
                     ("boden", "unter dem Kurs: überwundene Decke, jetzt Boden")):
        g = b["alt"][r_]
        if g:
            aus.append(f'Alte Plattform {_plattform(g)} {wort}.')
    if b["hoch"]:
        aus.append(f'{_zahl(abs(b["hoch"]["abstand"]), 1)} % unter dem Hoch der letzten 52 Wochen '
                   f'({_zahl(b["hoch"]["preis"])}).' if b["hoch"]["abstand"] < 0 else "Kurs am Hoch der letzten 52 Wochen.")
    return aus


def kurzurteil(b):
    """Die Zeile rechts im Kopf der Ebene: letzte Kerze und Lage, dazu die Treppe in einem Wort."""
    if not b:
        return ""
    k = {"grün": "🟢 letzte Kerze grün", "rot": "🔴 letzte Kerze rot", "doji": "⚪ letzte Kerze Doji"}.get(b["kerze"], "")
    return " · ".join(x for x in (k, f'{b["lage"][0]} {b["lage"][1]}') if x)


def alle(r):
    """Alle Ebenen der Titelseite (zonenseite.rechnen) → {Name: ebene()}."""
    import zonen
    aus = {}
    for n in zonen.EBENEN:
        e_ = (r.get("ebenen") or {}).get(n)
        try:
            aus[n] = ebene(n, e_["df"] if e_ else None, r["df"], bool(r.get("laufend")))
        except Exception:  # noqa: BLE001 – eine Ebene ohne Kerzen bleibt leer, der Bericht steht trotzdem
            aus[n] = None
    return aus


def beobachten(be, tr=None):
    """Was ich beobachten würde → {"long": [...], "short": [...]}: der erste Schritt auf der Stunde, der Auslöser auf
    dem Tag (unser Setup, sonst Front bzw. Unterkante), der Weg dahinter (Weg voraus ab der Kante)."""
    t_, h_ = be.get("Tag"), be.get("Stunde")
    aus = {"long": [], "short": []}
    if not t_:
        return aus
    kurs = t_["kurs"]
    for seite, sg, kante, wort in (("long", 1, t_["front"], "über der Front"), ("short", -1, t_["unterkante"],
                                                                                 "unter der Unterkante")):
        z = aus[seite]
        naechst = (h_ or {}).get("decke" if sg > 0 else "boden")
        if naechst and (not kante or sg * (kante - naechst["preis"]) > 0):
            z.append(f'Erster Schritt: Stundenschluss {"über" if sg > 0 else "unter"} {_zahl(naechst["preis"])}.')
        if tr and (tr["richtung"] > 0) == (sg > 0):
            z.append(f'Unser Setup {tr["zeichen"]} {tr["name"]}: ½ antasten beim Schluss '
                     f'{"über" if sg > 0 else "unter"} {_zahl(tr["pivot"])}'
                     + (f', ½ aufstocken bei 📒 {_zahl(tr["aufstocken"])}' if tr.get("aufstocken") else "")
                     + f' · Stopp {_zahl(tr["stopp"])}.')
        elif kante:
            dazw = [g for g in t_["gruppen"] if sg * (g["preis"] - kurs) > 0 and sg * (kante - g["preis"]) > 0]
            z.append(f'Auslöser: Tagesschluss {wort} {_zahl(kante)} ({_pz(kante, kurs)})'
                     + (f' – bis dahin {len(dazw)} {"Stellung" if len(dazw) == 1 else "Stellungen"} im Weg.'
                        if dazw else "."))
        else:
            z.append("Keine Kante mehr – ✈️ freie Bahn." if sg > 0 else "Keine Kante mehr – ✈️↓ freie Bahn.")
        if kante:
            jenseits = [g for g in t_["gruppen"] if sg * (g["preis"] - kante) > t_["atr"] * livermore.STELLUNG_ATR]
            ziel = min(jenseits, key=lambda g: abs(g["preis"] - kante), default=None)
            alt = t_["alt"]["decke" if sg > 0 else "boden"]
            if alt and sg * (alt["unten" if sg > 0 else "oben"] - kante) > 0 and (
                    not ziel or abs(alt["unten" if sg > 0 else "oben"] - kante) < abs(ziel["preis"] - kante)):
                z.append(f'Dahinter wartet die alte Plattform {_plattform(alt)}.')
            elif ziel:
                z.append(f'Dahinter die nächste Stellung {_zahl(ziel["preis"])} ({_pz(ziel["preis"], kurs)}).')
            else:
                z.append("Dahinter sauber – keine Stellung mehr." if sg > 0 else "Dahinter sauber – kein Boden mehr.")
    return aus


def gegenzeichen(be, richtung):
    """Was auf den Ebenen gegen die Richtung spricht (richtung = "auf"/"ab"/None): Treppen in Gegenrichtung, Stellungen
    in Richtung, an denen Dochte mehrfach abprallten, die alte Plattform im Weg."""
    if richtung not in ("auf", "ab"):
        return ["Richtung offen – beide Seiten beobachten, erst die Kerze entscheidet."]
    gegen, aus = ("ab" if richtung == "auf" else "auf"), []
    for n, b in be.items():
        if not b:
            continue
        tr = b["treppe"]
        reihe = tr["hochs"] if richtung == "auf" else tr["tiefs"]
        if (tr["gang_h"] if richtung == "auf" else tr["gang_t"]) == gegen and len(reihe) > 1:
            aus.append(f'{n}: {"Hochs fallen" if richtung == "auf" else "Tiefs steigen"} '
                       + " → ".join(_zahl(x) for x in reihe) + ".")
        g = b["decke" if richtung == "auf" else "boden"]
        if g and g.get("abpraller", 0) >= 2:
            aus.append(f'{n}: {"Decke" if richtung == "auf" else "Boden"} {_zahl(g["preis"])} – {g["abpraller"]} Abpraller.')
    t_ = be.get("Tag")
    if t_:
        alt = t_["alt"]["decke" if richtung == "auf" else "boden"]
        if alt:
            aus.append(f'Alte Plattform {_plattform(alt)} {"über" if richtung == "auf" else "unter"} dem Kurs.')
    return aus or ["Keine Gegenzeichen auf den Ebenen."]


def leiter(be):
    """Alle Stellungen aller Ebenen für die Leiter → [{preis, art, ebenen, abpraller}] plus alte Plattformen
    [{unten, oben, rolle, ebenen}] – Stellungen innerhalb ½ Tages-ATR werden eine Sprosse."""
    import vcp_zone
    t_ = be.get("Tag")
    if not t_:
        return None
    a = float(vcp_zone.atr(t_["df"]).iloc[-1] or 0)
    kurz = {"Woche": "W", "Tag": "T", "4 Stunden": "4h", "Stunde": "1h"}
    roh = []
    for n, b in be.items():
        if not b:
            continue
        for art, pr in (("front", b["front"]), ("unterkante", b["unterkante"])):
            if pr:
                roh.append({"preis": pr, "art": art, "ebene": kurz[n], "abpraller": 0})
        for g in (b["decke"], b["boden"]):
            if g:
                roh.append({"preis": g["preis"], "art": "decke" if g["preis"] > t_["kurs"] else "boden",
                            "ebene": kurz[n], "abpraller": g.get("abpraller", 0)})
    rang = {"front": 0, "unterkante": 0, "decke": 1, "boden": 1}
    sprossen = []
    for x in sorted(roh, key=lambda x: (rang[x["art"]], x["preis"])):
        s_ = next((s_ for s_ in sprossen if abs(s_["preis"] - x["preis"]) <= a * livermore.STELLUNG_ATR), None)
        if s_:
            if x["ebene"] not in s_["ebenen"]:
                s_["ebenen"].append(x["ebene"])
            s_["abpraller"] += x["abpraller"]
            continue
        sprossen.append({"preis": x["preis"], "art": x["art"], "ebenen": [x["ebene"]], "abpraller": x["abpraller"]})
    alt = []
    for n in ("Woche", "Tag"):
        b = be.get(n)
        for g in ((b or {}).get("alt") or {}).values():
            if g and not any(abs(x["unten"] - g["unten"]) <= a and abs(x["oben"] - g["oben"]) <= a for x in alt):
                alt.append(dict(g, ebenen=[kurz[n]]))
    return {"sprossen": sprossen, "alt": alt, "kurs": t_["kurs"], "atr": a}

