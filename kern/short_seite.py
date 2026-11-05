"""Short-Seite (Schritt 7, 04.11.2026): drei Einstiege nach Weinstein und O'Neil, dazu O'Neils Short-Regeln.

Einstiege (jeder mit Kursmarke, Stopp und Zustand liegt vor / bildet sich / nicht da):
  1. Bruch der Gipfelzone (Weinstein) – hier die Market-Profile-Zone: Schluss unter der Unterkante; Stopp = Schluss zurück
     über dem VAL (zurück in der Balance)
  2. Gescheiterte Erholung am fallenden Durchschnitt (Weinstein): Phase 4, 30-Wochen-Durchschnitt (GD150) fällt, eine
     Erholung der letzten 15 Tage lief bis auf 3 % an ihn heran und dreht; Einstieg unter dem Tief der letzten 5 Tage,
     Stopp über dem Hoch der Erholung
  3. Schulter-Kopf-Schulter-Top (O'Neil): drei Hochs der letzten 9 Monate, der Kopf das höchste, rechte Schulter unter dem
     Kopf; Einstieg beim Schluss unter der Nackenlinie (tiefstes Tief zwischen den Schultern), Stopp über der rechten Schulter
O'Neils Short-Regeln (Zeichen, kein Filter): früherer Führer (vor dem Top mindestens +100 % in 12 Monaten), 5–7 Monate
nach dem Top, Liquidität (50-Tage-Schnitt ab 5 Mio. Stück grün, ab 1 Mio. gelb).
"""
import re

import numpy as np


def deutsch(text):
    """Dezimalpunkt → Komma (Datumsangaben bleiben)."""
    return re.sub(r"(?<!\.\d)(?<!\.\d\d)(\d)\.(\d+)(?![\d.])", r"\1,\2", text)

SPITZE_FENSTER = 10          # ein Hoch ist eine Spitze, wenn es das höchste in ±10 Tagen ist
SKS_TAGE = 190               # rund 9 Monate
ERHOLUNG_TAGE = 15
ERHOLUNG_NAEHE = 0.03


def _gd(c, n):
    return float(np.mean(c[-n:])) if len(c) >= n else None


def _spitzen(h, a, e):
    s = []
    for i in range(max(a, SPITZE_FENSTER), e - 3):
        f = h[max(0, i - SPITZE_FENSTER):i + SPITZE_FENSTER + 1]
        if h[i] == f.max():
            s.append(i)
    return s


def sks_top(df):
    """Letztes Schulter-Kopf-Schulter-Top der letzten 9 Monate oder None. Strenge nach O'Neil: der Kopf ist das Hoch der
    letzten 12 Monate (Top nach einem Anstieg) und mindestens 3 % über beiden Schultern; die Schultern liegen höchstens
    8 % auseinander, die rechte nicht über der linken (+2 %); die beiden Tiefs der Nackenlinie liegen höchstens 5 %
    auseinander; ein Bruch zählt bis 3 Monate danach."""
    h, l, c = (df[x].to_numpy(float) for x in ("High", "Low", "Close"))
    n = len(c)
    if n < 260:
        return None
    sp = _spitzen(h, n - SKS_TAGE, n)
    best = None
    for k in range(len(sp) - 2):
        ls, kopf, rs = sp[k], sp[k + 1], sp[k + 2]
        if h[kopf] < h[max(0, kopf - 252):kopf + 1].max():
            continue
        if h[kopf] < 1.03 * max(h[ls], h[rs]) or abs(h[ls] - h[rs]) > 0.08 * h[kopf] or h[rs] > 1.02 * h[ls]:
            continue
        if not (10 <= kopf - ls <= 80 and 10 <= rs - kopf <= 80):
            continue
        t1, t2 = float(l[ls:kopf].min()), float(l[kopf:rs].min())
        if abs(t1 - t2) > 0.05 * max(t1, t2):
            continue
        nacken = min(t1, t2)
        if nacken > 0.95 * h[rs]:
            continue
        best = {"links": ls, "kopf": kopf, "rechts": rs, "nacken": nacken, "rechts_hoch": float(h[rs]),
                "kopf_hoch": float(h[kopf])}
    if best is None or c[best["rechts"]:].max() > best["kopf_hoch"] or (c[-1] > best["rechts_hoch"]):
        return None                               # über den Kopf (oder die rechte Schulter) zurück: Form erledigt
    nach = c[best["rechts"]:]
    unter = np.where(nach < best["nacken"])[0]
    best["bruch"] = int(best["rechts"] + unter[0]) if len(unter) else None
    if best["bruch"] is not None and n - 1 - best["bruch"] > 63:
        return None                               # Bruch länger als 3 Monate her: gelaufen
    return best


def erholung_gescheitert(df, phase):
    """Weinstein: in Phase 4 läuft eine Erholung an den fallenden 30-Wochen-Durchschnitt und dreht."""
    h, l, c = (df[x].to_numpy(float) for x in ("High", "Low", "Close"))
    if len(c) < 171:
        return None
    g = _gd(c, 150)
    fallend = g < float(np.mean(c[-170:-20]))
    if phase != 4 or not fallend:
        return {"da": False, "g": g, "fallend": fallend}
    i = len(c) - ERHOLUNG_TAGE + int(np.argmax(h[-ERHOLUNG_TAGE:]))
    hoch = float(h[i])
    heran = hoch >= g * (1 - ERHOLUNG_NAEHE)
    dreht = c[-1] < g and i < len(c) - 1 and c[-1] < hoch * 0.97
    marke = float(l[-5:].min())
    return {"da": bool(heran and dreht), "heran": bool(heran), "g": g, "fallend": fallend, "hoch": hoch,
            "tag": df.index[i], "marke": marke, "unter": bool(c[-1] < marke)}


def _einstiege(df, erk, phase):
    """Liste (Name, Zustand 'liegt vor'/'bildet sich'/'nicht da', Ampel, Text) für die drei Einstiege."""
    c = df["Close"].to_numpy(float)
    k = float(c[-1])
    aus = []
    w = erk.get("werte") or {}
    a = erk.get("mp")
    if a and "zone_unterkante" in w:
        u, val = w["zone_unterkante"], w.get("val") or w["zone_unterkante"]
        ak = a.get("aktiv")
        sig = [x for x in a["signale"] if x["dir"] == "↓" and x["art"] in ("A", "F", "U", "B")]
        if (ak and ak["dir"] == "↓") or k < u:
            lage = (f"Schluss {k:.2f} unter der Unterkante {u:.2f}" if k < u
                    else f"Kurs {(k / u - 1) * 100:.1f} % über der Unterkante {u:.2f}, Bewegung ↓ läuft")
            aus.append(("Bruch der Gipfelzone (Weinstein)", "grün",
                        f"liegt vor: {lage}" + (f", Auslöser {sig[-1]['art']}↓ am {sig[-1]['tag']:%d.%m.}" if sig else "")
                        + f" · Stopp: Schluss zurück über dem VAL {val:.2f}"))
        elif k < u * 1.05:
            aus.append(("Bruch der Gipfelzone (Weinstein)", "gelb",
                        f"bildet sich: Kurs {(k / u - 1) * 100:.1f} % über der Unterkante {u:.2f} · Einstieg beim Schluss "
                        f"darunter, Stopp über dem VAL {val:.2f}"))
        else:
            aus.append(("Bruch der Gipfelzone (Weinstein)", "grau",
                        f"nicht da: Kurs {(k / u - 1) * 100:.1f} % über der Unterkante der Zone {u:.2f}"))
    else:
        aus.append(("Bruch der Gipfelzone (Weinstein)", "grau", "keine Zone (30-Minuten-Kerzen fehlen)"))
    e = erholung_gescheitert(df, phase)
    if e and e["da"]:
        aus.append(("Gescheiterte Erholung am fallenden Durchschnitt (Weinstein)", "grün" if e["unter"] else "gelb",
                    f"{'liegt vor' if e['unter'] else 'bildet sich'}: Erholung bis {e['hoch']:.2f} am {e['tag']:%d.%m.} an den "
                    f"fallenden GD150 ({e['g']:.2f}), gedreht · Einstieg unter {e['marke']:.2f} (Tief 5 Tage), "
                    f"Stopp über {e['hoch']:.2f}"))
    elif e:
        grund = ("nicht Phase 4" if phase != 4 else "GD150 fällt nicht" if not e["fallend"]
                 else "keine Erholung bis an den GD150 in den letzten 3 Wochen")
        aus.append(("Gescheiterte Erholung am fallenden Durchschnitt (Weinstein)", "grau", f"nicht da: {grund}"))
    else:
        aus.append(("Gescheiterte Erholung am fallenden Durchschnitt (Weinstein)", "grau", "zu kurze Historie"))
    s = sks_top(df)
    if s:
        d = df.index
        form = (f"Schultern {d[s['links']]:%d.%m.} / {d[s['rechts']]:%d.%m.}, Kopf {d[s['kopf']]:%d.%m.} "
                f"({s['kopf_hoch']:.2f}), Nackenlinie {s['nacken']:.2f}")
        if s["bruch"] is not None:
            tief = (k / s["nacken"] - 1) * 100
            aus.append(("Schulter-Kopf-Schulter-Top (O'Neil)", "grün" if tief >= -5 else "gelb",
                        f"liegt vor: Bruch der Nackenlinie am {d[s['bruch']]:%d.%m.}"
                        + (f", Kurs {tief:.1f} % darunter – ausgedehnt" if tief < -5 else "")
                        + f" · {form} · Stopp über der rechten Schulter {s['rechts_hoch']:.2f}"))
        else:
            aus.append(("Schulter-Kopf-Schulter-Top (O'Neil)", "gelb",
                        f"bildet sich: {form} · Einstieg beim Schluss unter {s['nacken']:.2f}, Stopp über "
                        f"{s['rechts_hoch']:.2f}"))
    else:
        aus.append(("Schulter-Kopf-Schulter-Top (O'Neil)", "grau", "nicht da: keine SKS-Form in den letzten 9 Monaten"))
    return aus


def _oneil_regeln(df):
    """O'Neils Short-Regeln als Zeilen (Name, Ampel, Text)."""
    h, c, v = (df[x].to_numpy(float) for x in ("High", "Close", "Volume"))
    n = len(c)
    a = max(0, n - 252)
    top = a + int(np.argmax(h[a:]))
    vor = h[max(0, top - 252):top + 1]
    l_vor = df["Low"].to_numpy(float)[max(0, top - 252):top + 1]
    lauf = (vor.max() / l_vor.min() - 1) * 100 if len(l_vor) else 0
    seit = n - 1 - top
    monate = seit / 21
    vol = float(np.mean(v[-50:])) if n >= 50 else 0
    return [
        ("Früherer Führer", "grün" if lauf >= 100 else "gelb" if lauf >= 50 else "rot",
         f"vor dem Top ({df.index[top]:%d.%m.%Y}) +{lauf:.0f} % in 12 Monaten – O'Neil shortet frühere Führer"),
        ("5–7 Monate nach dem Top", "grün" if 5 <= monate <= 7 else "gelb" if 3 <= monate <= 9 else "rot",
         f"{monate:.1f} Monate seit dem Top – zu früh shortet man in die Stützung, zu spät ist der Fall gelaufen"),
        ("Liquidität", "grün" if vol >= 5e6 else "gelb" if vol >= 1e6 else "rot",
         f"{vol / 1e6:.1f} Mio. Stück im 50-Tage-Schnitt – dünne Titel springen bei Eindeckungen"),
    ]


def einstiege(*args):
    return [tuple(deutsch(x) if isinstance(x, str) else x for x in z) for z in _einstiege(*args)]


def oneil_regeln(*args):
    return [tuple(deutsch(x) if isinstance(x, str) else x for x in z) for z in _oneil_regeln(*args)]
