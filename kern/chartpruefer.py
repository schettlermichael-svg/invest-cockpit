"""Chart-Prüfer (Micky 14.11.2026): ein Prüfstand, kein Erkenner. Die Erkennung bleibt Code – nur feste Regeln geben bei
denselben Kursen immer dieselbe Zone, denselben Pivot, dieselben Anker. Der Prüfer schaut sich eine Stichprobe von
Charts mit dem Auge der Meister an und meldet, wo er unseren Regeln widerspricht. Aus den Widersprüchen werden
Regeländerungen im Code, gemessen über alle Titel; strittige Fälle entscheidet Micky.

Ablauf: Stichprobe (etwa 130 Titel, gleichmäßig über Base, Konsolidierung, Flagge, offene Zone, keine Zone und die
Setups des Kartentischs, dazu 20 Gruppen über die Felder der Rotationskarte) → je Titel ein Bild (1 Jahr Tageskerzen mit
Zone, Pivot, Enge, AVWAP-Ankern, Beginn der Balance, Mauer und Stütze, Marken für Ausbruch, Fehlausbruch, Signale des
Market Profile, Spring, Upthrust, Kraft ohne Weg, Klimax, Exzess, Wochen-Schwunghochs) und die Zahlen der ganzen Kette
(Kreislauf, Zeichen, Short-Formen, Zustand mit Anlass, Belegen, Ende, Gegenseite, eigen/geliehen); je Gruppe ein Bild
(Index der Mitglieder, RS-Linie, Breite) mit Feld, Zufluss, Breite, Anführern und Zustand → Urteil über ein festes
Formular → Bericht in daten/chartpruefer/. Etwa 5 Cent je Chart, geprüft gegen den Monatsdeckel (50 $). Erweitert am
14.11.2026 auf die ganze Kette der drei Bilder (vorher nur Zone, Pivot, Enge, Anker), dann auf den echten Chart der
Titelseite als erstes Bild (SVG → PNG mit cairosvg, ohne Browser); das eigene Bild bleibt als Hilfsbild für die Marken
der Ereignisse, die der Chart nicht zeigt (Spring, Klimax, Exzess, Signale des Market Profile). Dazu die Prüfung eines
einzelnen Titels per Knopf auf der Titelseite (daten/chartpruefer/titel/, einmal je Titel und Kurstag).

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
STICHPROBE = 150               # davon GRUPPEN Gruppen
KOSTEN_JE_CHART = 0.05         # $ (zwei Bilder ~3.000 Token, Zahlen und Kette ~2.500, Antwort ~800)

ELEMENTE = ["Zustand", "Anlass", "Zone: Beginn", "Zone: Unterkante/Tiefe", "Zone: Name", "Zone: keine/offen", "Pivot",
            "Drittel des Pivots", "Enge/Kontraktionen", "Einquetschung", "Test am Rand: Zeichen",
            "abgelehnt/angenommen", "Ende des Laufs", "Gegenseite (Mauer/Stütze)", "Eigen oder geliehen",
            "Kreislauf/Phase", "Short-Form", "AVWAP Hoch des Rückgangs", "AVWAP letztes Hoch",
            "AVWAP Tief der Bewegung", "AVWAP Ereignis", "Volumenprofil (Balance)", "Sonstiges"]
ELEMENTE_GRUPPE = ["Zustand der Gruppe", "Feld (Rotation)", "Breite", "Anführer/Verfolger", "Geldfluss", "Sonstiges"]
GRUPPEN = 20

SYSTEM = """Du bist der Chart-Prüfer des Invest Cockpits. Du erkennst nichts selbst für die App – du prüfst, ob die
App ihre Zonen, Zeichen, Pivots, Anker und ihren Zustand nach den Regeln der Meister richtig gesetzt hat. Du bekommst
je Titel ein Bild (1 Jahr Tageskerzen; eingezeichnet: Zone der App als Rahmen, Pivot als Linie, Kontraktionen der
Enge, AVWAP-Linien ab ihren Ankern, Beginn der laufenden Balance, Mauer rot und Stütze grün als Bänder rechts, Marken
für die Ereignisse der App, Wochen-Schwunghochs als Dreiecke) und die Zahlen der App.

Unser Bild – der Code für Balance und Ungleichgewicht: Ein Anlass (Information wie Zahlen oder eine Lücke; leere
Verteidiger; Zwang gefangener Händler) bringt die Balance an den Rand. Am Rand wird getestet. Wird der Ausbruch
abgelehnt, läuft der Kurs zum anderen Rand. Wird er angenommen, entsteht ein Ungleichgewicht, das läuft, bis eine von
drei Kräften es beendet: der Gegner antwortet (Mauer, Kraft ohne Weg, Exzess), der Antrieb erlischt (Klimax, Wechsel
der Phase, Rückschlag), der Wert wird akzeptiert (neue Wertzone). Zustände: Balance, Test am Rand, abgelehnt,
angenommen, Ungleichgewicht, Ende des Laufs.

Die Regeln der Meister:
- O'Neil: Tasse 7–65 Wochen, 12–33 % tief (im Bärenmarkt bis 40–50 %). Der Henkel liegt in der oberen Hälfte der
  Base, höchstens etwa 12–15 % tief, sein Hoch höchstens 15 % unter dem Hoch der linken Seite. Pivot = Hoch des
  Henkels, ohne Henkel das Hoch der linken Seite. Doppelboden: das zweite Tief unterschreitet das erste, Pivot = die
  Spitze in der Mitte des W. Flache Base ab 5 Wochen, höchstens etwa 15 % tief. Ausbruch mit Volumen über dem
  Schnitt; Fehlausbruch: zurück unter den Pivot. Distributionstage: fallender Schluss bei höherem Volumen als am Vortag.
- Minervini (VCP): 2–6 Kontraktionen, jede grob halb so tief wie die vorige, das Volumen trocknet aus; Pivot = Hoch
  der letzten Kontraktion. Low Cheat im unteren Drittel, Cheat im mittleren, Henkel im oberen Drittel. Nach einer
  gescheiterten Tasse bildet sich eine neue Base.
- Kullamägi (Flagge): Fahnenstange ab 30 % in 1–3 Monaten, danach 1–8 Wochen enges Seitwärts mit steigenden Tiefs.
  Episodic Pivot: Lücke mit sehr hohem Volumen auf eine Nachricht.
- Weinstein (Phasen): 1 Basis seitwärts um die flache 30-Wochen-Linie, 2 Aufwärts über der steigenden Linie,
  3 Verteilung seitwärts, die Linie flacht ab, 4 Abwärts unter der fallenden Linie.
- Wyckoff: Spring = Tief kurz unter der Unterkante der Spanne, schnell zurückgekauft; Upthrust = Hoch kurz über der
  Oberkante, Schluss zurück in der Spanne. Kraft ohne Weg: viel Volumen, wenig Kursweg.
- Morales/Kacher (Pocket Pivot): Volumen des Anstiegstags über dem höchsten Volumen der Abwärtstage der letzten 10 Tage.
- Einquetschung: steigende Tiefs gegen eine flache Oberkante (aufsteigendes Dreieck).
- Shannon (AVWAP): Ein Hoch wird erst durch den Rückgang danach zum Anker. Anker sind das Pivot-Tief, das einen Trend
  startete, das jüngste große Hoch, der Tag der Zahlen bzw. eine Kurslücke; mehrere übereinander.
- Dalton: Der Markt geht von Balance zu Balance; Balance = überlappender Wert; das Profil fasst die laufende Balance.
  Exzess = scharfe Ablehnung am Extrem (Auktion dort beendet); flache Kante (schwaches Hoch/Tief) = Auktion unfertig.

Wie die App ihre Anker setzt (damit du die Absicht kennst; prüfe trotzdem gegen die Meister): letztes Hoch = jüngstes
Wochen-Schwunghoch (2 Wochen davor und danach tiefer, also erst nach 2 Wochen bestätigt), das der Kurs nicht
überschritten hat; Hoch des Rückgangs = der Gipfel der ganzen Korrektur (fehlt, wenn er dasselbe ist wie das letzte
Hoch); Tief der Bewegung = tiefstes Tief seit dem letzten Hoch, sobald der Kurs 1 ATR darüber steht. Zone der App:
beginnt am ältesten Hoch ohne Schlusskurs darüber (ein Hoch darüber ohne Schluss darüber bricht sie nicht).

Dein Auftrag: Prüfe jedes Element der App gegen diese Regeln – auch, ob der Zustand zu den Belegen passt und ob die
Belege am richtigen Platz der Kette stehen. Melde nur Widersprüche; was stimmt, fasst du in einem Satz zusammen. Jeder
Widerspruch nennt: das Element, was falsch ist (mit Datum und Kurs), die Regel des Meisters, was richtig wäre (Datum,
Kurs), und ob du sicher bist oder es strittig ist (Auslegungssache). Erfinde keine Zahl: Daten und Kurse nur aus den
Zahlen der App oder klar am Bild ablesbar, sonst „etwa“. Kein Weichmacher, einfaches Deutsch."""

SYSTEM_GRUPPE = """Du bist der Chart-Prüfer des Invest Cockpits für Gruppen (Sektoren, Branchen, Themen). Unser Bild: Geld
fließt in eine Gruppe – der Anführer bricht aus, folgen die Schwestern? Derselbe Code wie beim Titel: Balance, Test am
Rand (Feld Erstarkend), angenommen (Breite steigt, Zufluss), Ungleichgewicht (Feld Führend), Ende des Laufs (Feld
Ermüdend, Breite wird schmal), abgelehnt (Erstarkend kippt zurück nach Abgehängt). Felder der Rotationskarte:
RS-Stärke und Schwung je um 100 (über 100 = besser als der Markt bzw. steigend). Meister: O'Neil – die führenden
Aktien kommen aus führenden Gruppen, eine Gruppe ist stark, wenn mehrere Mitglieder zugleich stark sind; Weinstein –
Gruppenanalyse mit der relativen Stärke der Gruppe. Du bekommst ein Bild (gleichgewichteter Index der Mitglieder, seine
RS-Linie zum S&P 500, die Breite = Anteil der Mitglieder über dem GD50) und die Zahlen der App. Prüfe, ob der Zustand
und seine Belege zum Bild passen. Melde nur Widersprüche (Element, Befund mit Datum/Zahl, Regel, was richtig wäre,
sicher/strittig); was stimmt, in einem Satz. Erfinde keine Zahl. Einfaches Deutsch."""

def _schema(elemente):
    return {
        "type": "object",
        "properties": {
            "stimmt": {"type": "string", "description": "ein Satz: was die App richtig gesetzt hat"},
            "widersprueche": {"type": "array", "items": {"type": "object", "properties": {
                "element": {"type": "string", "enum": elemente},
                "befund": {"type": "string", "description": "was falsch ist, mit Datum und Kurs"},
                "regel": {"type": "string", "description": "Meister und Regel"},
                "richtig": {"type": "string", "description": "was richtig wäre, mit Datum und Kurs"},
                "gewicht": {"type": "string", "enum": ["sicher", "strittig"]}},
                "required": ["element", "befund", "regel", "richtig", "gewicht"]}},
        },
        "required": ["stimmt", "widersprueche"],
    }


SCHEMA = _schema(ELEMENTE)
SCHEMA_GRUPPE = _schema(ELEMENTE_GRUPPE)


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
        elif schl == "gipfel" and "hoch" in a:          # gleich dem letzten Hoch – die App zeigt dann nur eine Linie
            zeilen.append(f"AVWAP-Anker {name}: derselbe Punkt wie das letzte Hoch (nur eine Linie)")
        elif schl == "tief":
            zeilen.append(f"AVWAP-Anker {name}: keiner – der Kurs steht noch nicht 1 ATR über dem tiefsten Tief seit "
                          "dem letzten Hoch (keine Bewegung begonnen)")
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
    # Die Kette (13./14.11.2026): Kreislauf, Zeichen, Zustand mit Belegen, Short-Formen, Market Profile
    import auktion
    import daten
    import volumenprofil
    idx = daten.kurse_gespeichert(daten.INDEX)
    br = vcp_zone.ausbruch(df, jetzt=z)
    fa = vcp_zone.ausbruch_text(br) if br and br.get("fehl") else None
    k = zeichen.fuer_titel(tk, df, idx, g, fehlausbruch=fa)
    zst = auktion.fuer_titel(tk, df, k, idx, mp, br, z, g) if k else None
    vv = volumenprofil.verankert(df, zt, z.get("start") if z.get("zone") else None, wb) or {}
    if k:
        zeilen.append(f"Kreislauf (Weinstein): Phase {k['phase']} {zeichen.PHASE_NAME.get(k['phase'], '')}"
                      + (f", Wechsel zu {k['ziel']} zeichnet sich ab" if k.get("ziel") else "")
                      + (", Rückschlag" if k.get("rueckschlag") else ""))
        for x in k.get("zeichen") or []:
            zeilen.append(f"Zeichen der App ({x['seite']}, {x['art']}): {x['text']}")
    if br:
        zeilen.append(f"Ausbruch des Scanners: {_d(br['tag'])} über {_z(br['pivot'])} $"
                      + (f", Fehlausbruch am {_d(br['fehl_tag'])}" if br.get("fehl") else "")
                      + (f", Volumen {_z(br['volumen'])}-fach" if br.get("volumen") else ""))
    sig = (mp or {}).get("signale") or []
    if sig:
        zeilen.append("Signale des Market Profile (letzte 60 Tage): " + ", ".join(
            f"{x['art']} {x['dir']} {_d(x['tag'])}" for x in sig if pd.Timestamp(x["tag"]) >= df.index[-60]))
    if (mp or {}).get("zustand"):
        zeilen.append(f"Market Profile heute: {mp['zustand'].get('wort')}")
    for name, fn in (("Ermüdung", vcp_zone.ermuedung), ("Bärenflagge", vcp_zone.baerenflagge),
                     ("Bruch der Spanne", vcp_zone.spannenbruch)):
        try:
            r = fn(df)
        except Exception:  # noqa: BLE001
            r = None
        if r:
            zeilen.append(f"Short-Form {name}: Bruch am {_d(r['tag'])}, Spanne {_z(r['unten'])}–{_z(r['oben'])} $, "
                          f"Ampel {r['ampel']}")
    if vv.get("mauer"):
        zeilen.append(f"Mauer (Volumenknoten über dem Kurs): {_z(vv['mauer'][0])}–{_z(vv['mauer'][1])} $")
    if vv.get("stuetze"):
        zeilen.append(f"Stütze (Volumenknoten unter dem Kurs): {_z(vv['stuetze'][0])}–{_z(vv['stuetze'][1])} $")
    if zst:
        zeilen.append(f"ZUSTAND DER APP: {auktion.wort(zst)} · {zst.get('unterzeile', '')}")
        for x in zst.get("anlass") or []:
            zeilen.append(f"  Anlass: {x}")
        for platz, x in zst.get("belege") or []:
            zeilen.append(f"  Beleg [{platz}]: {x}")
        for x in zst.get("ende") or []:
            zeilen.append(f"  Ende des Laufs: {x}")
        for x in zst.get("gegenseite") or []:
            zeilen.append(f"  Gegenseite: {x}")
        if zst.get("kraft"):
            zeilen.append(f"  Eigen oder geliehen: {zst['kraft']['text']}")
    marken = {"zone": z, "enge": e, "anker": a, "profil": pa, "wh": wh, "vv": vv, "br": br, "sig": sig,
              "mess": (zst or {}).get("messung") or {}, "zeichen": (k or {}).get("zeichen") or []}
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
        if r.empty:
            continue
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
    vv = marken.get("vv") or {}
    for schl, farbe, wort in (("mauer", "#D32F2F", "Mauer"), ("stuetze", "#388E3C", "Stütze")):
        if vv.get(schl):
            u, o = vv[schl][0], vv[schl][1]
            ax.axhspan(u, o, xmin=0.85, xmax=1.0, color=farbe, alpha=0.18)
            ax.text(len(d) - 1, o, f"{wort} {_z(u)}–{_z(o)}", color=farbe, fontsize=8, ha="right", va="bottom")

    def marke(t, text, farbe, oben=True):
        t = pd.Timestamp(t)
        if t < d.index[0] or t > d.index[-1]:
            return
        i = px(t)
        y = d["High"].iloc[min(i, len(d) - 1)] * 1.025 if oben else d["Low"].iloc[min(i, len(d) - 1)] * 0.975
        ax.annotate(text, (i, y), color=farbe, fontsize=8, ha="center", va="bottom" if oben else "top",
                    fontweight="bold")

    br = marken.get("br")
    if br:
        marke(br["tag"], "Ausbruch", "#1565C0")
        if br.get("fehl"):
            marke(br["fehl_tag"], "Fehlausbruch", "#B71C1C", oben=False)
    for x in marken.get("sig") or []:                 # nur die letzten 60 Tage (wie in den Zahlen), sonst zu voll
        if x["art"] in ("A", "U", "S", "R") and pd.Timestamp(x["tag"]) >= df.index[-60]:
            marke(x["tag"], f"MP {x['art']}{x['dir']}", "#6A1B9A", oben=x["dir"] == "↑")
    m = marken.get("mess") or {}
    if m.get("kraft_ohne_weg"):
        marke(m["kraft_ohne_weg"]["tag"], "Kraft ohne Weg", "#E65100", oben=m["kraft_ohne_weg"]["rand"] == "oben")
    if m.get("klimax"):
        marke(m["klimax"]["tag"], m["klimax"]["art"], "#AD1457", oben=m["klimax"]["art"] == "Kauf-Klimax")
    for seite, x in (m.get("exzess") or {}).items():
        marke(x["tag"], "Exzess" if x["art"] == "Exzess" else "flache Kante", "#00695C", oben=seite == "oben")
    for z_ in marken.get("zeichen") or []:
        for vor in ("Spring", "Upthrust"):
            if z_["text"].startswith(vor) and z_.get("tag"):
                marke(z_["tag"], vor, "#2E7D32" if vor == "Spring" else "#C62828", oben=vor == "Upthrust")
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



# ── Gruppen (Geldfluss in Sektoren, Branchen, Themen) ───────────────────────────────────────────────────────────
def gruppen_stichprobe(n=GRUPPEN, seed=None):
    """Gleichmäßig über die Felder der Rotationskarte, nur Gruppen mit mindestens 5 Mitgliedern."""
    import rueckenwind
    erg = rueckenwind.laden() or {}
    rnd = random.Random(seed or f"{datetime.now():%Y-%m-%d}")
    je = {}
    for g in erg.get("gruppen") or []:
        if len(g.get("mitglieder") or []) >= 5:
            je.setdefault(g.get("feld"), []).append(g)
    for v in je.values():
        rnd.shuffle(v)
    aus = []
    while len(aus) < n and any(je.values()):
        for f in sorted(je, key=str):
            if je[f] and len(aus) < n:
                aus.append(je[f].pop(0))
    return aus


def _gruppen_reihen(g):
    import daten
    kurse = {}
    for tk in g.get("mitglieder") or []:
        try:
            df = daten.kurse_gespeichert(tk)
        except Exception:  # noqa: BLE001
            df = None
        if df is not None and len(df) >= 60:
            kurse[tk] = df["Close"]
    C = pd.DataFrame(kurse).iloc[-260:]
    norm = C / C.bfill().iloc[0]
    index = norm.mean(axis=1)
    spx = daten.kurse_gespeichert(daten.INDEX)["Close"].reindex(index.index).ffill()
    rs = index / (spx / spx.iloc[0])
    alle = pd.DataFrame(kurse)
    breite = (alle > alle.rolling(50, min_periods=40).mean()).where(alle.notna()).mean(axis=1).reindex(index.index) * 100
    return index, rs, breite


def gruppen_bild(g):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    index, rs, breite = _gruppen_reihen(g)
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(14, 8), dpi=100, sharex=True,
                                     gridspec_kw={"height_ratios": [3, 1.5, 1.5]})
    a1.plot(index.index, index.values, color="#1565C0")
    a1.set_title(f"{g.get('art')} {g.get('name')} · gleichgewichteter Index der {len(g.get('mitglieder') or [])} "
                 f"Mitglieder bis {_d(index.index[-1])}", fontsize=11)
    a2.plot(rs.index, rs.values, color="#6A1B9A")
    a2.set_ylabel("RS zum S&P 500", fontsize=8)
    a3.plot(breite.index, breite.values, color="#2E7D32")
    a3.axhline(50, color="#999", linewidth=0.8)
    a3.set_ylabel("% über GD50", fontsize=8)
    for a in (a1, a2, a3):
        a.grid(alpha=0.25)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def gruppen_material(g):
    import auktion
    e = auktion.gruppe(g)
    z = [f"{g.get('art')} {g.get('name')}: {len(g.get('mitglieder') or [])} Mitglieder",
         f"Feld {g.get('feld')} seit {g.get('seit_wochen')} Wochen (vor 4 Wochen {g.get('feld_vor4')}), RS-Stärke "
         f"{_z(g.get('staerke', 0), '.1f')}, Schwung {_z(g.get('schwung', 0), '.1f')}, stabil: {bool(g.get('stabil'))}",
         f"Zufluss (Volumen steigender ÷ fallender Tage, 50 Tage): {g.get('zufluss')}",
         f"Breite: {g.get('breite')} % über dem GD50 (vor 4 Wochen {g.get('breite_vor4')} %)",
         f"Anführer: {', '.join(g.get('anfuehrer') or []) or 'keine'} · Verfolger: "
         f"{', '.join(g.get('verfolger') or []) or 'keine'} · vorne: {g.get('vorne')}"]
    if e:
        z.append(f"ZUSTAND DER APP: {auktion.wort(e)} · {e.get('unterzeile', '')}")
        z += [f"  Beleg [{p}]: {x}" for p, x in e.get("belege") or []] + [f"  Ende: {x}" for x in e.get("ende") or []]
    return "\n".join(z)


def pruefen_gruppe(g):
    import modell
    text = gruppen_material(g)
    png = gruppen_bild(g)
    antwort = modell._formular(SYSTEM_GRUPPE, f"Zahlen der App:\n{text}", "pruefung_melden", SCHEMA_GRUPPE, 2500,
                               bilder=[png])
    return {"tk": f"{g.get('art')}: {g.get('name')}", "gruppe": f"Gruppe {g.get('feld')}",
            "stimmt": antwort.get("stimmt", ""), "widersprueche": antwort.get("widersprueche") or [], "zahlen": text}

def app_bild(tk, chart_teil=None):
    """Der Chart der Titelseite, so wie Micky ihn sieht (Tageskerzen, 1 Jahr, Voreinstellung der Knöpfe), als PNG
    (base64). Die Grafik ist SVG; cairosvg wandelt sie ohne Browser um. Der Schriftsaum (paint-order) kann cairosvg nicht
    – ohne ihn bleibt die Schrift lesbar. chart_teil: teile["chart"] der Titelseite, sonst wird die Seite gebaut."""
    import re
    import cairosvg
    import titel
    if chart_teil is None:
        chart_teil = titel.seite_titel(tk)["chart"]
    h = titel.chartkarte(chart_teil, "Tag", "1 J")
    svg = re.search(r"<svg.*?</svg>", h, flags=re.S).group(0)
    svg = re.sub(r"<style>text\{[^}]*\}</style>", "", svg, count=1)
    svg = re.sub(r'viewBox="0 0 (\d+) (\d+)"', lambda m: f'viewBox="0 0 {int(m.group(1)) + 140} {m.group(2)}"', svg,
                 count=1)                                    # Platz für die Beschriftungen rechts
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=1600, background_color="#161C24")
    return base64.b64encode(png).decode()


# ── Lauf ────────────────────────────────────────────────────────────────────────────────────────────────────────
def pruefen(tk, chart_teil=None):
    """Ein Titel → {tk, stimmt, widersprueche} oder {tk, fehler}. Zwei Bilder: der Chart der Titelseite (so wie Micky
    ihn sieht) und das Hilfsbild mit den Marken der Ereignisse, die der Chart nicht zeigt."""
    import daten
    import modell
    df = daten.kurse_gespeichert(tk)
    marken, text = material(tk, df)
    bilder = []
    try:
        bilder.append(app_bild(tk, chart_teil))
    except Exception:  # noqa: BLE001 – ohne cairosvg bzw. ohne Seite: nur das Hilfsbild
        pass
    bilder.append(bild(tk, df, marken))
    hinweis = ("Bild 1 ist der Chart der App, so wie der Nutzer ihn sieht; Bild 2 ist ein Hilfsbild mit den Marken der "
               "Ereignisse. " if len(bilder) == 2 else "")
    antwort = modell._formular(SYSTEM, f"{hinweis}Zahlen der App zu {tk}:\n{text}", "pruefung_melden", SCHEMA, 3000,
                               bilder=bilder)
    return {"tk": tk, "stimmt": antwort.get("stimmt", ""), "widersprueche": antwort.get("widersprueche") or [],
            "zahlen": text}


def lauf(n=STICHPROBE):
    """Prüflauf über die Stichprobe; schreibt Protokoll und Bericht laufend (bricht er ab, bleibt das Geprüfte)."""
    import modell
    os.makedirs(ORDNER, exist_ok=True)
    rest = modell.DECKEL_USD - modell.kosten()["usd"]
    n = int(max(0, min(n, rest // KOSTEN_JE_CHART - 5)))
    probe = [(tk, g) for tk, g in stichprobe(max(0, n - GRUPPEN))] + [(g, None) for g in gruppen_stichprobe()]
    start = datetime.now()
    vorher = modell.kosten()["usd"]
    prot = {"start": f"{start:%d.%m.%Y %H:%M}", "pid": os.getpid(), "n": len(probe), "fertig": 0, "ende": None}
    bericht = {"stand": f"{start:%Y-%m-%d %H:%M}", "titel": []}
    pfad = os.path.join(ORDNER, f"bericht_{start:%Y-%m-%d_%H%M}.json")
    json_schreiben(PROTOKOLL, prot)
    for tk, gruppe in probe:
        try:
            r = pruefen(tk) if gruppe is not None else pruefen_gruppe(tk)
        except modell.Deckel as x:
            bericht["abbruch"] = str(x)
            break
        except Exception as x:  # noqa: BLE001 – ein Titel darf den Lauf nicht beenden
            r = {"tk": tk if gruppe is not None else f"{tk.get('art')}: {tk.get('name')}",
                 "fehler": f"{type(x).__name__}: {x}"[:300]}
        r.setdefault("gruppe", gruppe)
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
    """Startet werkzeuge/pruefer_lauf.py als eigenen Prozess (die App wartet nicht)."""
    if stand()[0]:
        return False
    os.makedirs(ORDNER, exist_ok=True)
    log = open(LOG, "w", encoding="utf-8")
    skript = os.path.join(HIER, "..", "werkzeuge", "pruefer_lauf.py")
    subprocess.Popen([sys.executable, "-u", os.path.abspath(skript)], cwd=os.path.join(HIER, ".."), stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return True


def einzeln_gespeichert(tk, stand):
    return json_lesen(os.path.join(ORDNER, "titel", f"{tk.upper()}_{stand}.json"), None)


def einzeln(tk, stand, chart_teil=None):
    """Prüfung eines einzelnen Titels (Knopf auf der Titelseite), einmal je Titel und Kurstag gespeichert."""
    import modell
    alt = einzeln_gespeichert(tk, stand)
    if alt:
        return alt
    vorher = modell.kosten()["usd"]
    r = pruefen(tk, chart_teil)
    r["stand"] = stand
    r["kosten"] = round(modell.kosten()["usd"] - vorher, 3)
    os.makedirs(os.path.join(ORDNER, "titel"), exist_ok=True)
    json_schreiben(os.path.join(ORDNER, "titel", f"{tk.upper()}_{stand}.json"), r, ensure_ascii=False)
    return r


SYSTEM_AUSWERTUNG = """Du wertest den Bericht des Chart-Prüfers des Invest Cockpits aus. Der Prüfer hat Charts gegen die Regeln
der Meister (O'Neil, Minervini, Kullamägi, Weinstein, Wyckoff, Shannon, Dalton) geprüft und jeden Widerspruch zur App
gemeldet. Deine Aufgabe: Fasse die Widersprüche zu Befunden über die REGELN der App zusammen – nicht Titel für Titel.
Ein Befund ist ein Muster, das bei mehreren Titeln auftritt und auf eine Ursache in einer Regel der App zurückgeht.
Ordne jeden Befund ein: Regelfehler (die Regel der App widerspricht einem Meister), Darstellung/Material (die Regel
stimmt, aber die App zeigt oder beschreibt es missverständlich), Auslegung (strittig, Micky entscheidet), Prüfer irrt
(der Prüfer hat die Regel der App oder das Bild falsch verstanden). Nenne je Befund die Zahl der Widersprüche, wie
viele davon sicher waren, bis zu 5 Beispieltitel, die Deutung und einen konkreten Vorschlag für die Regel. Sortiere
nach Gewicht (Regelfehler mit vielen sicheren Widersprüchen zuerst). Einfaches Deutsch, kein Weichmacher."""

SCHEMA_AUSWERTUNG = {
    "type": "object",
    "properties": {
        "fazit": {"type": "string", "description": "zwei bis drei Sätze"},
        "befunde": {"type": "array", "items": {"type": "object", "properties": {
            "titel": {"type": "string", "description": "das Muster in wenigen Worten"},
            "element": {"type": "string"},
            "art": {"type": "string", "enum": ["Regelfehler", "Darstellung/Material", "Auslegung", "Prüfer irrt"]},
            "anzahl": {"type": "integer"}, "sicher": {"type": "integer"},
            "beispiele": {"type": "array", "items": {"type": "string"}},
            "deutung": {"type": "string"}, "vorschlag": {"type": "string"}},
            "required": ["titel", "element", "art", "anzahl", "sicher", "beispiele", "deutung", "vorschlag"]}},
    },
    "required": ["fazit", "befunde"],
}


def _bericht_pfad():
    if not os.path.isdir(ORDNER):
        return None
    b = sorted(f for f in os.listdir(ORDNER) if f.startswith("bericht_"))
    return os.path.join(ORDNER, b[-1]) if b else None


def auswerten(pfad=None):
    """Widersprüche des Berichts zu Befunden über die Regeln der App bündeln (ein Modellaufruf, wenige Cent);
    das Ergebnis steht im Bericht unter "auswertung"."""
    import modell
    pfad = pfad or _bericht_pfad()
    b = json_lesen(pfad, None)
    if not b or not b.get("titel"):
        return None
    zeilen = [f"{r['tk']} [{r.get('gruppe', '')}] {w['element']} ({w['gewicht']}): {w['befund']} → richtig: "
              f"{w['richtig']} · Regel: {w['regel']}" for r in b["titel"] for w in r.get("widersprueche") or []]
    ohne = sum(1 for r in b["titel"] if not r.get("widersprueche") and not r.get("fehler"))
    inhalt = (f"Bericht {b['stand']}: {len(b['titel'])} Charts, {len(zeilen)} Widersprüche, {ohne} ohne Widerspruch.\n"
              + "\n".join(zeilen))
    vorher = modell.kosten()["usd"]
    a = modell._formular(SYSTEM_AUSWERTUNG, inhalt, "auswertung_melden", SCHEMA_AUSWERTUNG, 8000)
    a["kosten"] = round(modell.kosten()["usd"] - vorher, 3)
    a["stand"] = f"{datetime.now():%Y-%m-%d %H:%M}"
    b["auswertung"] = a
    json_schreiben(pfad, b, ensure_ascii=False)
    return a


def letzter_bericht():
    if not os.path.isdir(ORDNER):
        return None
    b = sorted(f for f in os.listdir(ORDNER) if f.startswith("bericht_"))
    return json_lesen(os.path.join(ORDNER, b[-1]), None) if b else None
