"""Setup-Prüfer (Micky 14.11.2026): ein eigener Prüfstand nur für die Setups – getrennt vom Chart-Prüfer, der Zone,
Zeichen, Zustand und Anker prüft („der Chart-Prüfer soll sich nur um seine Thematik kümmern“). Der Setup-Prüfer prüft
den Angriffsbefehl: Ist das Urteil der App (grün, gelb) nach den Regeln des Meisters, von dem das Setup stammt, richtig?
Sitzen Einstieg, Kaufzone und Stopp dort, wo der Meister sie setzt? Hat die App das richtige Setup gewählt? Und hat sie
bei Titeln ohne Setup eines übersehen? Er erkennt nichts für die App – die Urteile bleiben Code.

Ablauf wie beim Chart-Prüfer: Stichprobe (gleichmäßig über die Reihen des Kartentischs, grün und nicht grün, dazu
OHNE Titel ohne Setup) → je Titel der echte Chart der Titelseite als Bild und das Urteil der App mit allen Regeln beider
Lehrer, Einstieg, Stopp und den Zahlen des Charts → Urteil über ein festes Formular → Bericht in daten/setuppruefer/.
Einzelprüfung per Knopf auf der Titelseite (einmal je Titel und Kurstag). Auswertung bündelt die Widersprüche zu
Befunden über die Regeln (chartpruefer.auswerten mit eigenem Auftrag).

Regeln der Meister, die der Prüfer bekommt (recherchiert 14.11.2026):
  Minervini  Trendvorlage (8 Punkte inkl. RS), VCP mit mindestens 2 Kontraktionen, jede kleiner, Volumen trocknet aus;
             Pivot = Hoch der letzten, engsten Kontraktion; Kauf beim Ausbruch über den Pivot mit steigendem Volumen,
             bis 5 % darüber; Stopp unter dem Tief der letzten Kontraktion, höchstens etwa 8 % (absolut 10 %).
  Kullamägi  Breakout: Lauf von 30–100 % in 1–3 Monaten, danach geordnete Pause mit höheren Tiefs, enger werdend, am
             10er/20er (manchmal 50er), 2 Wochen bis 2 Monate; Einstieg Hoch der Eröffnungsspanne oder Ausbruch im
             Tageschart; Stopp am Tagestief, nie weiter als eine durchschnittliche Tagesspanne (ADR/ATR).
             Episodic Pivot: Lücke ab 10 % bei riesigem Volumen auf eine Nachricht (Zahlen am verlässlichsten);
             Einstieg Hoch der Eröffnungsspanne, Stopp am Tagestief. Short: Stopp am Tageshoch.
  O'Neil     Kauf am Pivot mit Volumen deutlich über dem Schnitt, nicht mehr als 5 % darüber; Verlust höchstens 7–8 %.
  Weinstein  Short beim Bruch aus Stufe 3 bzw. Basis in Stufe 4 (Kurs unter der fallenden 30-Wochen-Linie).
  Zahlen-Reaktion (Micky, nach der Drift nach den Zahlen und Shannons Anker am Ereignistag): Reaktion ab 3 %, Volumen
             über dem Schnitt, Schluss im oberen Drittel, seitdem kein Schluss unter dem Tief bzw. dem AVWAP ab dem
             Reaktionstag, Kurs über dem GD50; Einstieg am AVWAP ab dem Reaktionstag.
"""
import os
import random
import subprocess
import sys
from datetime import datetime

from dateien import json_lesen, json_schreiben
import regelkarte

HIER = os.path.dirname(os.path.abspath(__file__))
ORDNER = os.path.join(HIER, "..", "daten", "setuppruefer")
PROTOKOLL = os.path.join(ORDNER, "lauf.json")
LOG = os.path.join(ORDNER, "lauf.log")
STICHPROBE = 100               # davon OHNE Titel ohne Setup
OHNE = 20
KLEIN = 60                     # kleiner Lauf (Micky 15.11.2026: Guthaben reicht nach Lauf 4 nicht für 100), OHNE anteilig
from chartpruefer import KOSTEN_JE_CHART  # noqa: E402  eine Quelle (chartpruefer)

ELEMENTE = regelkarte.elemente("setup")     # Setups, Wege und Meister aus der Regelkarte (15.11.2026)

SYSTEM = f"""Du bist der Setup-Prüfer des Invest Cockpits. Du erkennst nichts selbst für die App – du prüfst, ob das
Urteil der App über das Setup eines Titels den Regeln der Meister entspricht. Zone, Anker und Zustand prüft ein anderer
Prüfer; du nur das Setup: Urteil, Wahl, Einstieg, Kaufzone, Stopp, und ob ein Setup übersehen wurde.

{regelkarte.block_setups()}

Die Meister:
{regelkarte.block_meister("setup")}

Dein Auftrag: Prüfe das Setup des Titels. Melde nur Widersprüche; was stimmt, fasst du in einem Satz zusammen.
- Grün zu Unrecht: eine Regel ist falsch gemessen oder der Meister würde hier nicht kaufen bzw. leerverkaufen.
- Zu streng: die App sagt nicht grün, obwohl die Regeln des Meisters erfüllt sind.
- Wahl: ein anderes Setup passt klar besser.
- Übersehen: der Titel hat kein Setup in der App, zeigt aber eines nach den Regeln oben (nenne welches, mit Pivot).
- Einstieg, Kaufzone, Stopp: wo der Meister sie setzt, mit Kurs.
Jeder Widerspruch nennt: das Element, was falsch ist (mit Datum und Kurs), die Regel des Meisters, was richtig wäre,
und ob du sicher bist oder es strittig ist. Erfinde keine Zahl: nur aus den Zahlen der App oder klar am Bild ablesbar,
sonst „etwa“. Kein Weichmacher, einfaches Deutsch. Höchstens 8 Widersprüche, die wichtigsten zuerst; jedes Feld
höchstens zwei kurze Sätze."""

SYSTEM_AUSWERTUNG = """Du wertest den Bericht des Setup-Prüfers des Invest Cockpits aus. Der Prüfer hat die Setups der
App (Base-Ausbruch, Flagge, Momentum-Ausbruch, Sprung, Zahlen-Reaktion, Shorts) gegen die Regeln der Meister (Minervini,
O'Neil, Kullamägi, Weinstein) geprüft und jeden Widerspruch gemeldet: Urteil, Wahl, Einstieg, Kaufzone, Stopp,
übersehene Setups. Fasse die Widersprüche zu Befunden über die REGELN der App zusammen – nicht Titel für Titel.
Ein Befund ist ein Muster, das bei mehreren Titeln auftritt und auf eine Ursache in einer Regel der App zurückgeht.
Ordne jeden Befund ein: Regelfehler (die Regel der App widerspricht einem Meister), Darstellung/Material (die Regel
stimmt, aber die App zeigt oder beschreibt es missverständlich), Auslegung (strittig, Micky entscheidet), Prüfer irrt
(der Prüfer hat die Regel der App oder das Bild falsch verstanden). Nenne je Befund die Zahl der Widersprüche, wie
viele davon sicher waren, bis zu 5 Beispieltitel, die Deutung und einen konkreten Vorschlag für die Regel. Sortiere
nach Gewicht (Regelfehler mit vielen sicheren Widersprüchen zuerst). Einfaches Deutsch, kein Weichmacher."""


def _schema():
    import chartpruefer
    return chartpruefer._schema(ELEMENTE)


def _z(x, f=".2f"):
    return format(float(x), f).replace(".", ",")


# ── Stichprobe ──────────────────────────────────────────────────────────────────────────────────────────────────
def stichprobe(n=STICHPROBE, seed=None):
    """Gleichmäßig über die Reihen des Kartentischs (grün und nicht grün getrennt), dazu OHNE Titel ohne Setup:
    [(Ticker, Gruppe)]."""
    import kartentisch
    rnd = random.Random(seed or f"setup-{datetime.now():%Y-%m-%d}")
    t = kartentisch.laden() or {}
    gruppen, ohne = {}, []
    for tk, x in (t.get("titel") or {}).items():
        if x.get("reihe"):
            g = f"{kartentisch.NAME.get(x['reihe'], x['reihe'])} · {'grün' if x.get('gruen') else 'nicht grün'}"
            gruppen.setdefault(g, []).append(tk)
        else:
            ohne.append(tk)
    if not ohne:                                    # Titel des Universums, die nicht auf dem Tisch liegen
        import chartpruefer
        auf = set(t.get("titel") or {})
        ohne = [tk for tk in chartpruefer._ticker() if tk not in auf]
    for v in list(gruppen.values()) + [ohne]:
        rnd.shuffle(v)
    aus = []
    ohne_n = round(n * OHNE / STICHPROBE)            # Titel ohne Setup anteilig (100 → 20, 60 → 12)
    while len(aus) < n - ohne_n and any(gruppen.values()):
        for g in sorted(gruppen):
            if gruppen[g] and len(aus) < n - ohne_n:
                aus.append((gruppen[g].pop(0), g))
    aus += [(tk, "ohne Setup") for tk in ohne[:n - len(aus)]]
    return aus


# ── Material ────────────────────────────────────────────────────────────────────────────────────────────────────
def _regeln(liste):
    return "; ".join(f"{'✓' if ok else '✗'} {name}" + (f" ({text})" if text else "") for name, ok, text in liste or [])


def material(tk, df):
    """Urteil der App mit allen Regeln beider Lehrer, Einstieg, Stopp und die Zahlen des Charts als Text."""
    import atr as atr_
    import depot
    import kartentisch
    import system_kullamaegi
    info = kartentisch._stufe1(tk, regeln=True)
    if not info:
        raise ValueError("Titel nicht rechenbar")
    rg = info.pop("_regeln", {})
    m, k, zr = rg.get("m") or {}, rg.get("k") or {}, rg.get("zr") or {}
    c, h, l = df["Close"], df["High"], df["Low"]
    kurs = float(c.iloc[-1])
    g = {n_: float(c.rolling(n_).mean().iloc[-1]) for n_ in (10, 20, 50, 150, 200)}
    a = atr_.wert(df)
    adr = float(((h / l - 1).iloc[-20:]).mean() * 100)
    v50 = float(df["Volume"].iloc[-50:].mean())
    z = [f"Titel {tk}, Kurs {_z(kurs)} $ am {df.index[-1]:%d.%m.%Y}; GD10 {_z(g[10])}, GD20 {_z(g[20])}, GD50 "
         f"{_z(g[50])}, GD150 {_z(g[150])}, GD200 {_z(g[200])} $; 52-Wochen-Hoch {_z(h.iloc[-252:].max())} $, -Tief "
         f"{_z(l.iloc[-252:].min())} $; ATR {_z(a) if a else '–'} $, ADR (20 Tage) {_z(adr, '.1f')} %; Volumen Schnitt "
         f"50 Tage {f'{v50:,.0f}'.replace(',', '.')}; Phase {info.get('phase')}"]
    r = info.get("reihe")
    if r:
        z.append(f"SETUP DER APP: {kartentisch.NAME.get(r, r)} (Lehrer {kartentisch.LEHRER.get(r, '')}) · "
                 f"{'GRÜN' if info.get('gruen') else 'nicht grün'}{' · ★' if info.get('stern') else ''}"
                 + (f" · fehlt: {'; '.join(info['luecken'])}" if info.get("luecken") else "")
                 + (f" · Scanner: {info['scanner']}" if info.get("scanner") else "")
                 + (f" · Zeichen: {info['ausbruch']}" if info.get("ausbruch") else "")
                 + (f" · auch: {', '.join(info['auch'])}" if info.get("auch") else ""))
        e = info.get("einstieg")
        if e:
            stopp = e["wert"] + depot.ATR_STOPP * a if e["seite"] == "short" else e["wert"] - depot.ATR_STOPP * a
            z.append(f"Plan der App: {e['seite']}, Einstieg {_z(e['wert'])} $ ({e['quelle']}), Kurs "
                     f"{_z(info.get('abstand_vz', 0), '+.1f')} % dazu; Stopp {_z(stopp)} $ (1,5 ATR, "
                     f"{_z(abs(stopp / e['wert'] - 1) * 100, '.1f')} % vom Einstieg)" if a else
                     f"Plan der App: {e['seite']}, Einstieg {_z(e['wert'])} $ ({e['quelle']})")
    else:
        z.append("SETUP DER APP: keines (der Titel liegt in keiner Reihe des Kartentischs) – prüfe, ob eines übersehen ist")
    kl = info.get("_kreislauf") or {}
    au = kl.get("auktion")
    if au:                                       # wo der Titel im Kreislauf steht (Weg des Setups prüfen)
        import auktion
        z.append(f"Zustand im Kreislauf: {auktion.wort(au)} · Phase {kl.get('phase')} · {au.get('unterzeile', '')}"
                 + "".join(f" · Anlass: {x}" for x in au.get("anlass") or [])
                 + "".join(f" · Ende: {x}" for x in au.get("ende") or []))
    if m:
        z.append(f"Lehrer Minervini · Base-Ausbruch: Ampel {m.get('ampel')}; {_regeln(m.get('regeln'))}"
                 + (f"; Pivot {_z(m['pivot'])} $" if m.get("pivot") else "")
                 + (f", Stopp {_z(m['stopp'])} $ (unter dem Tief der letzten Kontraktion)" if m.get("stopp") else ""))
    b = k.get("breakout") or {}
    if b:
        z.append(f"Lehrer Kullamägi · Momentum-Ausbruch: Ampel {b.get('ampel')}; {_regeln(b.get('regeln'))}"
                 + (f"; Pivot {_z(b['pivot'])} $" if b.get("pivot") else ""))
    ep = k.get("ep") or {}
    if ep:
        z.append(f"Lehrer Kullamägi · Sprung (EP): Ampel {ep.get('ampel')}; {_regeln(ep.get('regeln'))}"
                 + (f"; Hoch des Sprungtags {_z(ep['pivot'])} $" if ep.get("pivot") else ""))
    if k.get("fuehrer") is not None:
        fr = k["fuehrer"]
        fr = ", ".join(f"{x}: besser als {_z(y, '.0f')} %" for x, y in fr.items()) if isinstance(fr, dict) else fr
        z.append(f"Führer-Rang (Kullamägi): {fr} · ADTR {_z(k['adtr_pct'], '.1f') if k.get('adtr_pct') else '–'} %")
    for r_s in system_kullamaegi.SHORTS:
        s_ = system_kullamaegi.short_von(k, r_s)
        if s_:
            z.append(f"Short · {kartentisch.NAME.get(r_s, r_s)}: Ampel {s_.get('ampel')}; {_regeln(s_.get('regeln'))}; "
                     f"Unterkante {_z(s_['unten'])} $, Stopp {_z(s_['stopp'])} $ (Hoch des Auslösetags "
                     f"{s_['tag']:%d.%m.})")
    if zr:
        z.append(f"Zahlen-Reaktion: Ampel {zr.get('ampel')} ({zr.get('seite')}, {zr.get('pct')} % am {zr.get('tag')}); "
                 f"{_regeln(zr.get('regeln'))}" + (f"; AVWAP ab dem Reaktionstag {_z(zr['avwap'])} $" if zr.get("avwap")
                                                    else ""))
    letzte = df.iloc[-10:]
    z.append("Letzte 10 Tage (Datum: Eröffnung/Hoch/Tief/Schluss, Volumen zum Schnitt): " + "; ".join(
        f"{d:%d.%m.} {_z(x.Open)}/{_z(x.High)}/{_z(x.Low)}/{_z(x.Close)} {_z(x.Volume / v50, '.1f')}×"
        for d, x in letzte.iterrows()))
    return "\n".join(z)


# ── Prüfung ─────────────────────────────────────────────────────────────────────────────────────────────────────
def pruefen(tk, chart_teil=None):
    """Ein Titel → {tk, stimmt, widersprueche, zahlen} – Bild: der Chart der Titelseite, so wie Micky ihn sieht."""
    import chartpruefer
    import daten
    import modell
    df = daten.kurse_gespeichert(tk)
    text = material(tk, df)
    bilder = []
    try:
        bilder.append(chartpruefer.app_bild(tk, chart_teil))
    except Exception:  # noqa: BLE001 – ohne Bild prüft er die Zahlen
        pass
    hinweis = "Das Bild ist der Chart der App, so wie der Nutzer ihn sieht. " if bilder else ""
    antwort = modell._formular(SYSTEM, f"{hinweis}Zahlen und Urteil der App zu {tk}:\n{text}", "setup_pruefung_melden",
                               _schema(), 3000, bilder=bilder or None)
    return {"tk": tk, "stimmt": antwort.get("stimmt", ""), "widersprueche": antwort.get("widersprueche") or [],
            "zahlen": text}


def lauf(n=STICHPROBE):
    """Prüflauf über die Stichprobe; schreibt Protokoll und Bericht laufend."""
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
    import chartpruefer
    return chartpruefer.stand(PROTOKOLL)


def starten(n=None):
    """Startet werkzeuge/setup_lauf.py als eigenen Prozess (n Titel, sonst STICHPROBE); nie zugleich mit dem
    Chart-Prüfer (Monatsdeckel)."""
    import chartpruefer
    if stand()[0] or chartpruefer.stand()[0]:
        return False
    os.makedirs(ORDNER, exist_ok=True)
    log = open(LOG, "w", encoding="utf-8")
    skript = os.path.join(HIER, "..", "werkzeuge", "setup_lauf.py")
    subprocess.Popen([sys.executable, "-u", os.path.abspath(skript)] + ([str(int(n))] if n else []), cwd=os.path.join(HIER, ".."), stdout=log,
                     stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    return True


def einzeln_gespeichert(tk, stand_):
    return json_lesen(os.path.join(ORDNER, "titel", f"{tk.upper()}_{stand_}.json"), None)


def einzeln(tk, stand_, chart_teil=None):
    """Prüfung eines einzelnen Titels (Knopf auf der Titelseite), einmal je Titel und Kurstag gespeichert."""
    import modell
    alt = einzeln_gespeichert(tk, stand_)
    if alt:
        return alt
    vorher = modell.kosten()["usd"]
    r = pruefen(tk, chart_teil)
    r["stand"] = stand_
    r["kosten"] = round(modell.kosten()["usd"] - vorher, 3)
    os.makedirs(os.path.join(ORDNER, "titel"), exist_ok=True)
    json_schreiben(os.path.join(ORDNER, "titel", f"{tk.upper()}_{stand_}.json"), r, ensure_ascii=False)
    return r


def auswerten(pfad=None):
    import chartpruefer
    return chartpruefer.auswerten(pfad, SYSTEM_AUSWERTUNG, ORDNER)


def letzter_bericht():
    import chartpruefer
    return chartpruefer.letzter_bericht(ORDNER)
