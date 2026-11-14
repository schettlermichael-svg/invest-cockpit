"""Chart-Prüfer (Micky 14.11.2026): ein Prüfstand, kein Erkenner. Die Erkennung bleibt Code – nur feste Regeln geben bei
denselben Kursen immer dieselbe Zone, denselben Pivot, dieselben Anker. Der Prüfer schaut sich eine Stichprobe von
Charts mit dem Auge der Meister an und meldet, wo er unseren Regeln widerspricht. Aus den Widersprüchen werden
Regeländerungen im Code, gemessen über alle Titel; strittige Fälle entscheidet Micky.

Ablauf: Stichprobe (etwa 150 Titel, gleichmäßig über Base, Konsolidierung, Flagge, offene Zone, keine Zone und die
Setups des Kartentischs) → je Titel ein Bild (1 Jahr Tageskerzen mit Zone, Pivot, Enge, AVWAP-Ankern, Beginn der
Balance, Wochen-Schwunghochs) und die Zahlen dazu → Urteil über ein festes Formular → Bericht in daten/chartpruefer/.
Kosten etwa 3 Cent je Chart, geprüft gegen den Monatsdeckel des Modells (50 $).

Regeln der Meister, die der Prüfer bekommt (recherchiert 14.11.2026, Quellen im Konzeptdokument):
  O'Neil   Tasse 7–65 Wochen, 12–33 % tief (Bärenmarkt bis 40–50 %); Henkel in der oberen Hälfte, höchstens etwa
           12–15 % tief, Hoch des Henkels höchstens 15 % unter dem Hoch der linken Seite; Pivot = Hoch des Henkels
           (ohne Henkel: Hoch der linken Seite). Doppelboden: das zweite Tief unterschreitet das erste, Pivot = Spitze in
           der Mitte des W. Flache Base ab 5 Wochen, höchstens etwa 15 % tief.
  Minervini VCP: 2–6 Kontraktionen, jede grob halb so tief wie die vorige, das Volumen trocknet aus; Pivot = Hoch der
           letzten Kontraktion. Low Cheat im unteren, Cheat im mittleren, Henkel im oberen Drittel. Nach einer
           gescheiterten Tasse bildet sich eine neue Base.
  Kullamägi Flagge: Fahnenstange ab 30 % in 1–3 Monaten, danach 1–8 Wochen enges Seitwärts mit steigenden Tiefs.
  Shannon  AVWAP-Anker: ein Hoch wird erst durch den Rückgang danach zum Anker; das Pivot-Tief, das einen Trend
           startete; das jüngste große Hoch; der Tag der Zahlen bzw. eine Lücke; mehrere übereinander.
  Dalton   Der Markt geht von Balance zu Balance; Balance = überlappender Wert; das Profil fasst die laufende Balance.
"""
import base64
import io
import json
import os
import random
import subprocess
import sys
from datetime import datetime

import numpy as np
import pandas as pd

from dateien import json_lesen, json_schreiben

HIER = os.path.dirname(os.path.abspath(__file__))
ORDNER = os.path.join(HIER, "..", "daten", "chartpruefer")
PROTOKOLL = os.path.join(ORDNER, "lauf.json")
LOG = os.path.join(ORDNER, "lauf.log")
STICHPROBE = 150
KOSTEN_JE_CHART = 0.03         # $ (Bild ~1.500 Token, Zahlen ~1.500, Antwort ~600)

ELEMENTE = ["Zone: Beginn", "Zone: Unterkante/Tiefe", "Zone: Name", "Zone: keine/offen", "Pivot", "Drittel des Pivots",
            "Enge/Kontraktionen", "Einquetschung", "AVWAP Hoch des Rückgangs", "AVWAP letztes Hoch",
            "AVWAP Tief der Bewegung", "AVWAP Ereignis", "Volumenprofil (Balance)", "Sonstiges"]

SYSTEM = """Du bist der Chart-Prüfer des Invest Cockpits. Du erkennst nichts selbst für die App – du prüfst, ob die
App ihre Zonen, Pivots und Anker nach den Regeln der Meister richtig gesetzt hat. Du bekommst je Titel ein Bild
(1 Jahr Tageskerzen, eingezeichnet: Zone der App als Rahmen, Pivot als Linie, Kontraktionen der Enge, AVWAP-Linien ab
ihren Ankern, Beginn der laufenden Balance, Wochen-Schwunghochs als Dreiecke) und die Zahlen der App.

Die Regeln der Meister:
- O'Neil: Tasse 7–65 Wochen, 12–33 % tief (im Bärenmarkt bis 40–50 %). Der Henkel liegt in der oberen Hälfte der
  Base, höchstens etwa 12–15 % tief, sein Hoch höchstens 15 % unter dem Hoch der linken Seite. Pivot = Hoch des
  Henkels, ohne Henkel das Hoch der linken Seite. Doppelboden: das zweite Tief unterschreitet das erste, Pivot = die
  Spitze in der Mitte des W. Flache Base ab 5 Wochen, höchstens etwa 15 % tief.
- Minervini (VCP): 2–6 Kontraktionen, jede grob halb so tief wie die vorige, das Volumen trocknet aus; Pivot = Hoch
  der letzten Kontraktion. Low Cheat im unteren Drittel, Cheat im mittleren, Henkel im oberen Drittel. Nach einer
  gescheiterten Tasse bildet sich eine neue Base.
- Kullamägi (Flagge): Fahnenstange ab 30 % in 1–3 Monaten, danach 1–8 Wochen enges Seitwärts mit steigenden Tiefs.
- Einquetschung: steigende Tiefs gegen eine flache Oberkante (aufsteigendes Dreieck).
- Shannon (AVWAP): Ein Hoch wird erst durch den Rückgang danach zum Anker. Anker sind das Pivot-Tief, das einen Trend
  startete, das jüngste große Hoch, der Tag der Zahlen bzw. eine Kurslücke; mehrere übereinander.
- Dalton (Profil): Der Markt geht von Balance zu Balance; Balance = überlappender Wert; das Profil fasst die laufende
  Balance zusammen.

Dein Auftrag: Prüfe jedes Element der App gegen diese Regeln. Melde nur Widersprüche – was stimmt, fasst du in einem
Satz zusammen. Jeder Widerspruch nennt: das Element, was falsch ist (mit Datum und Kurs aus Bild oder Zahlen), die
Regel des Meisters, was richtig wäre (Datum, Kurs), und ob du sicher bist oder es strittig ist (Auslegungssache).
Erfinde keine Zahl: Daten und Kurse nur aus den Zahlen der App oder klar am Bild ablesbar, sonst „etwa“.
Kein Weichmacher, einfaches Deutsch."""

SCHEMA = {
    "type": "object",
    "properties": {
        "stimmt": {"type": "string", "description": "ein Satz: was die App richtig gesetzt hat"},
        "widersprueche": {"type": "array", "items": {"type": "object", "properties": {
            "element": {"type": "string", "enum": ELEMENTE},
            "befund": {"type": "string", "description": "was falsch ist, mit Datum und Kurs"},
            "regel": {"type": "string", "description": "Meister und Regel"},
            "richtig": {"type": "string", "description": "was richtig wäre, mit Datum und Kurs"},
            "gewicht": {"type": "string", "enum": ["sicher", "strittig"]}},
            "required": ["element", "befund", "regel", "richtig", "gewicht"]}},
    },
    "required": ["stimmt", "widersprueche"],
}


def _z(x, f=".2f"):
    return format(float(x), f).replace(".", ",")


def _d(t):
    return f"{pd.Timestamp(t):%d.%m.%Y}"


# ── Stichprobe ──────────────────────────────────────────────────────────────────────────────────────────────────
def stichprobe(n=STICHPROBE, seed=None):
    """Gleichmäßig über die Arten der Zone und die Setups des Kartentischs: [(Ticker, Gruppe)]."""
    import daten
    import vcp_zone
    rnd = random.Random(seed or f"{datetime.now():%Y-%m-%d}")
    gruppen = {}
    for tk in _ticker():
        try:
            df = daten.kurse_gespeichert(tk)
            if df is None or len(df) < 120:
                continue
            z = vcp_zone.zone(df)
        except Exception:  # noqa: BLE001
            continue
        g = z.get("name") if z.get("zone") else ("offen" if z.get("offen") else "keine Zone")
        gruppen.setdefault(g, []).append(tk)
    try:
        import kartentisch
        t = kartentisch.laden() or {}
        for tk, x in (t.get("titel") or {}).items():
            if x.get("reihe") and x.get("gruen"):
                gruppen.setdefault("Setup " + str(x["reihe"]), []).append(tk)
    except Exception:  # noqa: BLE001
        pass
    for v in gruppen.values():
        rnd.shuffle(v)
    aus, gesehen = [], set()
    while len(aus) < n and any(gruppen.values()):
        for g in sorted(gruppen):
            while gruppen[g] and gruppen[g][0] in gesehen:
                gruppen[g].pop(0)
            if gruppen[g] and len(aus) < n:
                tk = gruppen[g].pop(0)
                gesehen.add(tk)
                aus.append((tk, g))
    return aus


def _ticker():
    pfad = os.path.join(HIER, "..", "daten", "kurse")
    return sorted(f[:-4] for f in os.listdir(pfad) if f.endswith(".csv"))


# ── Material: Zahlen und Bild ───────────────────────────────────────────────────────────────────────────────────
def material(tk, df):
    """Alles, was die App für diesen Titel setzt → (Marken für das Bild, Zahlen als Text)."""
    import avwap
    import erkennung
    import vcp_zone
    import zeichen
    try:
        import kartentisch
        _, g = kartentisch._fund_gespeichert(tk)
    except Exception:  # noqa: BLE001
        g = None
    df = df.copy()
    df.attrs["ticker"] = tk
    z = vcp_zone.zone(df)
    e = vcp_zone.enge(df, z) if z.get("zone") else {}
    zt = avwap.zahlentag(df, g)
    a = avwap.anker(df, zt)
    try:
        mp = erkennung.mp_von(df)
    except Exception:  # noqa: BLE001
        mp = None
    wb = avwap.wert_beginn(mp)
    pa = avwap.profil_anker(df, zt, z.get("start") if z.get("zone") else None, wb)
    wh = avwap._wochen_hochs(df)[-6:]
    ein = zeichen.einquetschung(df)
    c = df["Close"]
    zeilen = [f"Titel {tk}, letzter Kurs {_z(c.iloc[-1])} $ am {_d(df.index[-1])}, 52-Wochen-Hoch "
              f"{_z(df['High'].iloc[-252:].max())} $, 52-Wochen-Tief {_z(df['Low'].iloc[-252:].min())} $"]
    if z.get("zone"):
        zeilen.append(f"Zone der App: {z['name']} ab {_d(z['start'])}, Oberkante {_z(z['oben'])} $, Unterkante "
                      f"{_z(z['unten'])} $ am {_d(z['tief_datum'])}, {_z(z['wochen'], '.1f')} Wochen, "
                      f"{_z(z['tiefe'], '.1f')} % tief, Länge {z['laenge']}, Vorgeschichte "
                      f"{z['vorgeschichte']['art']} {_z(z['vorgeschichte']['prozent'], '+.0f')} %")
        if z.get("innen"):
            f = z["innen"]
            zeilen.append(f"Darin Flagge ab {_d(f['start'])}, Oberkante {_z(f['oben'])} $, {_z(f['tiefe'], '.1f')} % tief")
    else:
        zeilen.append(f"Keine fertige Zone: {z.get('grund', '')}" + (
            f" (Rahmen ab {_d(df.index[z['start_i']])}, {_z(z['oben'])}–{_z(z['unten'])} $)" if z.get("offen") else ""))
    if e.get("kontraktionen"):
        k = "; ".join(f"{_d(df.index[x['hoch_i']])} {_z(x['hoch'])} $ → {_d(df.index[x['tief_i']])} {_z(x['tief'])} $ "
                      f"(−{_z(x['tiefe'], '.1f')} %)" for x in e["kontraktionen"])
        zeilen.append(f"Enge: {e['zahl']} Kontraktionen: {k}. Pivot {_z(e['pivot'])} $ ({e.get('lage')}), Ampel "
                      f"{e['ampel']}" + (f", fehlt: {', '.join(e['fehlt'])}" if e.get("fehlt") else ""))
    for schl, name in (("gipfel", "Hoch des Rückgangs"), ("hoch", "letztes Hoch"), ("tief", "Tief der Bewegung"),
                       ("ereignis", "Ereignis")):
        if schl in a:
            preis = df["High"][a[schl]] if schl in ("gipfel", "hoch") else df["Low"][a[schl]]
            zeilen.append(f"AVWAP-Anker {name}: {_d(a[schl])} bei {_z(preis)} $")
        else:
            zeilen.append(f"AVWAP-Anker {name}: keiner")
    if pa.get("grau"):
        zeilen.append(f"Volumenprofil der Balance ab {_d(pa['grau'][0])} ({pa['grau'][1]})")
    if wh:
        zeilen.append("Wochen-Schwunghochs: " + ", ".join(f"{_d(d)} {_z(p)} $" for d, p in wh))
    if ein:
        zeilen.append(f"Einquetschung der App: {json.dumps({k: (str(v) if not isinstance(v, (int, float)) else v) for k, v in ein.items()}, ensure_ascii=False)[:300]}")
    else:
        zeilen.append("Einquetschung der App: keine")
    marken = {"zone": z, "enge": e, "anker": a, "profil": pa, "wh": wh}
    return marken, "\n".join(zeilen)


def bild(tk, df, marken):
    """PNG (base64): 1 Jahr Tageskerzen mit den Marken der App."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import avwap
    z, e, a = marken["zone"], marken["enge"], marken["anker"]
    beginn = df.index[-252] if len(df) > 252 else df.index[0]
    if z.get("zone") and z["start"] < beginn:
        beginn = z["start"] - pd.Timedelta(days=30)
    d = df[df.index >= beginn]
    x = np.arange(len(d))
    pos = {t: i for i, t in enumerate(d.index)}
    fig, (ax, av) = plt.subplots(2, 1, figsize=(14, 8), dpi=100, gridspec_kw={"height_ratios": [4, 1]}, sharex=True)
    hoch = d["Close"] >= d["Open"]
    for maske, farbe in ((hoch, "#2E9E5B"), (~hoch, "#D9534F")):
        ax.vlines(x[maske], d["Low"][maske], d["High"][maske], color=farbe, linewidth=0.8)
        ax.vlines(x[maske], d[["Open", "Close"]].min(axis=1)[maske], d[["Open", "Close"]].max(axis=1)[maske],
                  color=farbe, linewidth=3)
    av.bar(x, d["Volume"], color=np.where(hoch, "#2E9E5B", "#D9534F"), width=0.8)
    av.plot(x, d["Volume"].rolling(50, min_periods=10).mean(), color="#333", linewidth=1)

    def px(t):
        t = pd.Timestamp(t)
        return pos.get(t, int(np.searchsorted(d.index, t)))

    if z.get("zone") or z.get("offen"):
        s = px(z["start"] if z.get("zone") else df.index[z["start_i"]])
        ax.add_patch(plt.Rectangle((s, z["unten"]), len(d) - 1 - s, z["oben"] - z["unten"], fill=False,
                                   edgecolor="#1f6fd1", linewidth=1.6, linestyle="-" if z.get("zone") else "--"))
        ax.text(s, z["oben"], f" Zone: {z.get('name', 'offen')} {_z(z['wochen'], '.1f')} W, {_z(z['tiefe'], '.0f')} %",
                color="#1f6fd1", va="bottom", fontsize=9)
    if e.get("pivot"):
        ax.axhline(e["pivot"], color="black", linestyle="--", linewidth=1)
        ax.text(len(d) - 1, e["pivot"], f" Pivot {_z(e['pivot'])} ({e.get('lage')})", fontsize=9, va="bottom", ha="right")
        for k in e.get("kontraktionen") or []:
            i0, i1 = px(df.index[k["hoch_i"]]), px(df.index[k["tief_i"]])
            ax.plot([i0, i1], [k["hoch"], k["tief"]], color="#888", linestyle=":", linewidth=1.2)
    farben = {"gipfel": "#C62828", "hoch": "#EF6C00", "tief": "#00838F", "ereignis": "#B8860B"}
    namen = {"gipfel": "AVWAP Hoch des Rückgangs", "hoch": "AVWAP letztes Hoch", "tief": "AVWAP Tief der Bewegung",
             "ereignis": "AVWAP Ereignis"}
    for k, t in a.items():
        r = avwap.reihe(df, t)
        r = r[r.index >= d.index[0]]
        if len(r):
            ax.plot([px(i) for i in r.index], r.values, color=farben[k], linewidth=1.4, label=f"{namen[k]} ab {_d(t)}")
            ax.plot(px(t), df["High"][t] if k in ("gipfel", "hoch") else df["Low"][t], "o", color=farben[k], ms=6)
    if marken["profil"].get("grau"):
        ax.axvline(px(marken["profil"]["grau"][0]), color="#7B1FA2", linestyle="-.", linewidth=1,
                   label=f"Beginn der Balance (Profil) {_d(marken['profil']['grau'][0])}")
    for t, p in marken["wh"]:
        if t >= d.index[0]:
            ax.plot(px(t), p * 1.01, "v", color="#555", ms=6)
    ticks = list(range(0, len(d), max(1, len(d) // 12)))
    av.set_xticks(ticks)
    av.set_xticklabels([f"{d.index[i]:%d.%m.%y}" for i in ticks], fontsize=8)
    ax.set_title(f"{tk} · Tageskerzen bis {_d(d.index[-1])} · Dreiecke = Wochen-Schwunghochs", fontsize=11)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


# ── Lauf ────────────────────────────────────────────────────────────────────────────────────────────────────────
def pruefen(tk):
    """Ein Titel → {tk, stimmt, widersprueche} oder {tk, fehler}."""
    import daten
    import modell
    df = daten.kurse_gespeichert(tk)
    marken, text = material(tk, df)
    png = bild(tk, df, marken)
    antwort = modell._formular(SYSTEM, f"Zahlen der App zu {tk}:\n{text}", "pruefung_melden", SCHEMA, 3000, bilder=[png])
    return {"tk": tk, "stimmt": antwort.get("stimmt", ""), "widersprueche": antwort.get("widersprueche") or [],
            "zahlen": text}


def lauf(n=STICHPROBE):
    """Prüflauf über die Stichprobe; schreibt Protokoll und Bericht laufend (bricht er ab, bleibt das Geprüfte)."""
    import modell
    os.makedirs(ORDNER, exist_ok=True)
    rest = modell.DECKEL_USD - modell.kosten()["usd"]
    n = int(max(0, min(n, rest // KOSTEN_JE_CHART - 5)))
    probe = stichprobe(n)
    start = datetime.now()
    vorher = modell.kosten()["usd"]
    prot = {"start": f"{start:%d.%m.%Y %H:%M}", "pid": os.getpid(), "n": len(probe), "fertig": 0, "ende": None}
    bericht = {"stand": f"{start:%Y-%m-%d %H:%M}", "titel": []}
    pfad = os.path.join(ORDNER, f"bericht_{start:%Y-%m-%d_%H%M}.json")
    json_schreiben(PROTOKOLL, prot)
    for tk, gruppe in probe:
        try:
            r = pruefen(tk)
        except modell.Deckel as x:
            bericht["abbruch"] = str(x)
            break
        except Exception as x:  # noqa: BLE001 – ein Titel darf den Lauf nicht beenden
            r = {"tk": tk, "fehler": f"{type(x).__name__}: {x}"[:300]}
        r["gruppe"] = gruppe
        bericht["titel"].append(r)
        prot["fertig"] += 1
        bericht["kosten"] = round(modell.kosten()["usd"] - vorher, 2)
        json_schreiben(pfad, bericht, ensure_ascii=False)
        json_schreiben(PROTOKOLL, prot)
    prot["ende"] = f"{datetime.now():%d.%m.%Y %H:%M}"
    prot["bericht"] = os.path.basename(pfad)
    prot["kosten"] = round(modell.kosten()["usd"] - vorher, 2)
    json_schreiben(PROTOKOLL, prot)
    return pfad


def stand():
    """(läuft, Protokoll)."""
    p = json_lesen(PROTOKOLL, None)
    if not p:
        return False, None
    if p.get("ende"):
        return False, p
    try:
        os.kill(p["pid"], 0)
        with open(f"/proc/{p['pid']}/status", encoding="utf-8") as f:
            if any(z.startswith("State:") and "Z" in z.split()[1] for z in f):
                return False, p
    except (OSError, KeyError):
        return False, p
    return True, p


def starten():
    """Startet werkzeuge/chartpruefer.py als eigenen Prozess (die App wartet nicht)."""
    if stand()[0]:
        return False
    os.makedirs(ORDNER, exist_ok=True)
    log = open(LOG, "w", encoding="utf-8")
    skript = os.path.join(HIER, "..", "werkzeuge", "chartpruefer.py")
    subprocess.Popen([sys.executable, "-u", os.path.abspath(skript)], cwd=os.path.join(HIER, ".."), stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return True


def letzter_bericht():
    if not os.path.isdir(ORDNER):
        return None
    b = sorted(f for f in os.listdir(ORDNER) if f.startswith("bericht_"))
    return json_lesen(os.path.join(ORDNER, b[-1]), None) if b else None
