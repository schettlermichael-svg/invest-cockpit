"""Strategen-Call (Micky 13.11.2026): ein Stratege, der die Daten der App richtig deutet – kein Online-Gang, kein
allgemeines Blabla. Auftrag des Snipers: die Ineffizienz und Disbalance finden, die den Kurs aus der Spanne ausbrechen
lässt – oder sagen, dass es keinen Schuss gibt.

Material (seit 22.11.2026 dasselbe wie Titelseite und Chart): Zirkel, Spanne und Phase auf Woche, Tag und Stunde, der
Setup, Stellungen und freie Bahn, Schlachtordnung und Geld, Tiefenanalyse – jedes Feld mit einer Nummer (F1, F2 …).
Die Kette, an der der Stratege entlanggeht:
    Zirkel → Spanne und Phase → Trade → Reibung (Stellungen, freie Bahn) → Truppe (Klasse, Geld) → wo wartet die Gegenseite.
Antwort über ein festes Formular: Schuss (long/short/kein), Disbalance, höchstens 3 Belege mit Feldnummer, Auslöser
(Kurs und Bedingung), widerlegt bei (Kurs und Bedingung), Gegenzeuge mit Feldnummer.

Der Code prüft die Antwort gegen das Material: jede Feldnummer muss es geben, jede Zahl in den Belegen muss im Material
stehen, Auslöser und Widerlegung müssen auf der richtigen Seite des Kurses liegen (long: Auslöser über dem
Widerlegungskurs, short umgekehrt). Was nicht besteht, steht als Prüfbefund unter der Antwort – nichts wird still
geglättet. Gespeichert je Titel und Kurstag (daten/strategen/), Kosten im Kostenbuch des Modells (Deckel 50 $).
"""
import os
import re

from dateien import json_lesen, json_schreiben

HIER = os.path.dirname(os.path.abspath(__file__))
SPEICHER = os.path.join(HIER, "..", "daten", "strategen")

SUCHEN = 8                      # höchstens 8 Websuchen je Titel (Quartal, Segmente, Konsens, Vorquartale, Burggraben,
                                # Bedrohung, Wettbewerber – Titel-Analyse 18.11.2026)
KURS_SPANNE = 0.4               # Prüfung: Zahlen bis 40 % um den Kurs in Fazit und Auslöser sind Kursmarken
KURS_GENAU = 0.005              # … und müssen auf 0,5 % genau im Material stehen
WETTBEWERBER = 5                # höchstens 5 Wettbewerber

SYSTEM = """Du bist der Stratege des Invest Cockpits – ein Sniper, kein Kommentator. Du bekommst das Material eines Titels
als nummerierte Felder (F1, F2 …): den Zirkel (Jahreszeit 1 Basis, 2 Aufwärts, 3 Verteilung, 4 Abwärts, mit den Zeichen,
die ihn tragen, und dem Keim des Gegenteils), Spanne und Phase auf Woche, Tag und Stunde (Livermores Spanne zwischen
seinem letzten Pivotal Point oben und unten, in der Stunde die Balance), das Setup der App (Livermores Signal, benannt
nach der Art seines Pivotal Points: Aufbruch, Fortsetzung, Rücktest, Abbruch, Fortsetzung abwärts – der Zirkel bestätigt mit ✓ oder
steht mit ✗ dagegen), die Stellungen (Livermores noch nicht durchbrochene Pivotal Points) und die freie Bahn, die
Schlachtordnung (Klasse 1 Garde bis 5 Rückzug), Rückenwind und Geldfluss, den Markt und die Tiefenanalyse.
Die Sprache der App (Micky 26.11.2026): Lage = Livermores Spalte – 🟢 Vormarsch (Aufwärtstrend), 🟡 Gefechtspause
(Rally oder Reaktion), 🔴 Rückzug (Abwärtstrend); sie gilt für Titel, Ebenen und Markt. Der Lagebericht ist die
Frontkarte: die Front (Livermores letzter Pivotal Point oben) und die Unterkante, die nächste stehende Stellung darüber und darunter (ein Pivotal Point
fällt erst mit einem Schluss 1 ATR jenseits). Die Kipp-Zone liegt je 1 ATR um die Kante: jenseits bestätigt 📒
(Livermores 3 Punkte), ein Schluss zurück auf der falschen Seite ist der 🦊 Fehlausbruch. Livermore baut die Position
in zwei Hälften: ½ antasten an der Kante, ½ aufstocken bei 📒 – nachgelegt wird nur im Gewinn, nie verbilligt. Einigkeit
der Ebenen (Woche, Tag, Stunde alle im Vormarsch oder alle im Rückzug) ist eigene Kraft. Der Markt ist das Lagebild:
Spitze (Garde und Angriff) und Heer (alle Titel) bestimmen, der Index bestätigt ✓ oder steht ✗ dagegen.
Vor jedem Trade drei Tore (Harry Sharp): Richtung (letzte abgeschlossene Wochen- und Tageskerze, bei gemischt
entscheidet die Lage der Woche) → Ort (Lage in der Spanne, Weg voraus sauber oder unruhig, ⚪ Chop, ⚠ weit gelaufen)
→ Auslöser (unser Setup). Ein Tor mit ✗ ist ein Gegenargument, kein Verbot. Für Kurse,
Spannen, Volumen, RS und Geldfluss gilt nur dieses Material: du erfindest keine Zahl und keine Kursmarke.
Im Netz recherchierst du nur das Unternehmen und das letzte Quartal (Micky 21.11.2026, aus der Titel-Analyse):
  Unternehmen: Geschäftsmodell, Burggraben und was ihn bedroht, Wachstumstreiber.
  Quartal: Umsatz organisch, EPS bereinigt gegen den Konsens, Margen, stärkstes Segment, Prognose alt → neu,
  Rückkäufe/Dividende; Wachstum von Umsatz und EPS über die letzten 3 Quartale – beschleunigend oder bremsend.
  Dazu 3–5 direkte Wettbewerber als US-Börsenkürzel. Primärquellen zuerst: Quartalsbericht, 8-K/10-Q bei der SEC.
Jede Zeile in Unternehmen und Quartal beginnt mit genau einem Zeichen, immer in derselben Bedeutung:
  🦬 Käufer haben die Kontrolle · 🐻 Verkäufer haben die Kontrolle · 🦈 früher Vorteil, den die Masse noch nicht sieht ·
  🔥 Beschleunigung · 🦊 Falle · 🌞 Rückenwind/Geldzufluss · ❄️ Gegenwind/Geldabfluss ·
  🪝 Widerstand/Unterstützung · sonst 🟢 Stärke, 🟡 gemischt, 🔴 Schwäche · ⚪ ungemessen. Veränderungen als vorher → heute.

Das System: Livermore liefert die Signale (Notizbuch, Pivotal Points, Tape Reading), der Zirkel deutet und bestätigt –
alles läuft im Zirkel, jede Phase trägt den Keim der nächsten. Ein Trend bleibt in Bewegung, bis eine Gegenkraft ihn
bremst (Dow, Newton). In der Spanne (Balance) sind Käufer und Verkäufer einig; an der Front kippt die Waage (Livermores
Pivotal Point). Reibung frisst Kraft: Decken mit wartenden Verkäufern, Kraft ohne Weg. Der Kurs läuft
entlang der Linie des geringsten Widerstands – freie Bahn ohne Stellung darüber, trockenes Volumen, Zufluss.

Dein Auftrag: Finde die eine Disbalance, die den Kurs aus der Spanne treibt – wer ist am Rand stärker, und warum ist die
Gegenseite schwach, leer oder gefangen? Geh die Kette entlang: Markt (Lagebild) → Lage und Frontkarte des Titels →
Spanne und Phase (sind die Ebenen einig?) → Setup und Kipp-Zone → Reibung (nächste Stellung) → Truppe → wo wartet die
Gegenseite → eigen oder geliehen. Auslöser und Widerlegung nimmst du aus Kipp-Zone und Frontkarte.

Regeln:
1. Kein Weichmacher. Kein „könnte“, „möglicherweise“, „man sollte beobachten“. Du urteilst.
2. „kein Schuss“ ist eine gute Antwort, wenn die Disbalance fehlt. Lieber kein Schuss als ein schwacher. „Abwarten“
   nur mit dem Auslöser, der die Entscheidung bringt, und der Richtung, in die du dann schießt (Tendenz).
3. Jeder Beleg nennt sein Feld (F-Nummer) und steht im Material. Höchstens drei – die stärksten.
4. Auslöser: der Kurs und die Bedingung, bei der du abdrückst (z. B. Schluss über dem Rand mit Volumen).
5. Widerlegt bei: der Kurs und die Bedingung, bei der deine Deutung falsch ist.
6. Gegenzeuge: das stärkste Feld gegen deinen Schuss – ehrlich, mit F-Nummer.
7. Geliehene Kraft (der Markt trägt den Titel) ist schwächer als eigene. Sag es, wenn sie geliehen ist.
8. Die Haltung des Marktes gilt für den Markt, nicht für den Titel: Stärke in der Schwäche wird nie wegen des
   Marktes verworfen.
9. Fazit: 2–3 Sätze, Long- und Short-Szenario mit den entscheidenden Kursmarken aus dem Material.
Schreib einfaches Deutsch, kurze Sätze."""

ZEILEN = {"type": "array", "items": {"type": "string"},
          "description": "Aussagezeilen, jede beginnt mit genau einem Zeichen der Liste"}

SCHEMA = {
    "type": "object",
    "properties": {
        "schuss": {"type": "string", "enum": ["long", "short", "abwarten", "kein"]},
        "richtung": {"type": "string", "enum": ["long", "short"], "description": "Tendenz bei abwarten"},
        "disbalance": {"type": "string", "description": "die eine Disbalance in einem oder zwei Sätzen"},
        "belege": {"type": "array", "maxItems": 3, "items": {
            "type": "object", "properties": {"feld": {"type": "string"}, "text": {"type": "string"}},
            "required": ["feld", "text"]}},
        "ausloeser_kurs": {"type": "number", "description": "Kurs des Auslösers (0 bei kein Schuss)"},
        "ausloeser": {"type": "string", "description": "Bedingung des Auslösers"},
        "widerlegt_kurs": {"type": "number", "description": "Kurs, bei dem die Deutung falsch ist (0 bei kein Schuss)"},
        "widerlegt": {"type": "string", "description": "Bedingung der Widerlegung"},
        "gegenzeuge": {"type": "object", "properties": {"feld": {"type": "string"}, "text": {"type": "string"}},
                       "required": ["feld", "text"]},
        "unternehmen": ZEILEN,
        "quartal": ZEILEN,
        "wettbewerber": {"type": "array", "items": {"type": "string"},
                         "description": "3–5 direkte Wettbewerber als US-Börsenkürzel"},
        "fazit": {"type": "string", "description": "2–3 Sätze: Long- und Short-Szenario mit Kursmarken aus dem Material"},
        "quellen": {"type": "array", "items": {"type": "string"}, "description": "URLs der genutzten Primärquellen"},
    },
    "required": ["schuss", "disbalance", "belege", "ausloeser", "widerlegt", "gegenzeuge", "unternehmen", "quartal",
                 "wettbewerber", "fazit"],
}


def _z(x, f=".2f"):
    return format(x, f).replace(".", ",")


def material(tk, r, kurs, atr=None, rw=None, markt=None, termin=None, tiefe=None):
    """Nummerierte Felder → (Text, {F-Nummer: Text}); r = zonenseite.rechnen (dieselbe Fährte wie Titelseite und Chart)."""
    import zeichen
    felder = []

    def f(text):
        if text:
            felder.append(str(text))

    f(f"Titel {tk}, Kurs {_z(kurs)} $" + (f", ATR (14 Tage) {_z(atr)} $" if atr else ""))
    zk = zeichen.zirkel(zeichen.von(tk))
    if zk:
        f(f"Zirkel: Jahreszeit {zk['phase']} {zk['name']}" + (f" seit {zk['wochen']} Wochen" if zk.get("wochen") else ""))
        for x in zk["traegt"][:3]:
            f(f"Zirkel trägt – {x}")
        for x in zk["keim"][:3]:
            f(f"Keim des Gegenteils – {x}")
    fu = (r or {}).get("fuehrte") or {}
    for eb, la in (fu.get("lage") or {}).items():
        if not la:
            continue
        rand = (f", Spanne {_z(la['zone'][0])}–{_z(la['zone'][1])} $" if la.get("zone") else "") + \
               (f", Front {_z(la['pivot'])} $" if la.get("pivot") else "")
        f(f"{eb}: {la['name'] or 'keine Spanne'} – {la['wort']}{rand}" + (f" · {la['info']}" if la.get("info") else ""))
        for x in ((fu.get("stellungen") or {}).get(eb) or {}).get("oben", []):
            f(f"{eb}: Decke (Stellung über dem Kurs) {_z(x['preis'])} $ ({', '.join(x['grund'])}, {_z(x['abstand'], '+.1f')} %)")
        for x in ((fu.get("stellungen") or {}).get(eb) or {}).get("unten", []):
            f(f"{eb}: Boden (Stellung unter dem Kurs) {_z(x['preis'])} $ ({', '.join(x['grund'])}, {_z(x['abstand'], '+.1f')} %)")
    fr = fu.get("frei") or {}
    if fr.get("oben") or fr.get("unten"):
        f("Freie Bahn: keine Stellung " + ("über" if fr.get("oben") else "unter") + " dem Kurs (Tageschart, zwei Jahre)")
    import livermore
    df_ = (r or {}).get("df")
    try:                                          # Frontkarte (Micky 26.11.2026): dieselben Linien wie der Lagebericht
        d_ = df_.dropna(subset=["High", "Low", "Close"])
        nb = livermore.notizbuch(d_)
        fk = livermore.front(d_, nb) if nb else None
        fb_ = livermore.frei(d_, nb) if nb else None
    except Exception:  # noqa: BLE001 – ohne Notizbuch keine Frontkarte
        nb, fk, fb_ = None, None, None
    if fk:
        p_ = lambda x: f"{_z(x['preis'])} $" if x else "–"                         # noqa: E731
        f(f"Lagebericht (Livermores Notizbuch, Tag): {' '.join(livermore.lage(nb['spalte']))}"
          + (f", Front {p_(fk['oben'])}" if fk["oben"] else "") + (f", Unterkante {p_(fk['unten'])}" if fk["unten"] else "")
          + (f", nächste Decke {p_(fk['ziel'])}" if fk["ziel"] else ", darüber ✈️ freie Bahn" if fb_["oben"] else "")
          + (f", nächster Boden {p_(fk['boden'])}" if fk["boden"] else ", darunter ✈️ freie Bahn" if fb_["unten"] else ""))
    if df_ is not None and nb:                    # die drei Tore (Sharp, Micky 26.11.2026)
        try:
            import tore
            tz = tore.zeile(tore.tore(d_, fu.get("trade")), fu.get("trade"))
            if tz:
                f("Tore " + tz.replace("🚦 ", ""))
        except Exception:  # noqa: BLE001 – ohne Tore bleibt das übrige Material
            pass
    ei = fu.get("einigkeit")
    if ei:
        f("Ebenen: " + " · ".join(f"{n} {w_}" for n, (_, w_) in ei["ebenen"].items())
          + {"auf": " – Einigkeit: Vormarsch auf allen drei", "ab": " – Einigkeit: Rückzug auf allen drei"}.get(ei["alle"], ""))
    t = fu.get("trade")
    if t:
        f(f"Setup der App (Livermore, der Zirkel bestätigt {t.get('zirkel') or '–'}): {t['name']} "
          f"{'long' if t['richtung'] > 0 else 'short'}, "
          + (f"½ antasten {_z(t['einstieg'])} $, ½ aufstocken bei 📒 {_z(t['aufstocken'])} $"
             + (" (erreicht)" if t.get("aufgestockt") else "") if t.get("aufstocken") else f"Einstieg {_z(t['einstieg'])} $")
          + f", Stopp {_z(t['stopp'])} $, Risiko {_z(t['risiko'], '.1f')} %" + (" – wartet auf den Auslöser" if t["wartet"] else ""))
        kante = t.get("pivot")
        if kante and atr:
            b_ = livermore.BESTAETIGUNG * atr
            f(f"Kipp-Zone um {'die Front' if t['richtung'] > 0 else 'die Unterkante'} {_z(kante)} $: "
              + (f"📒 bestätigt bei einem Hoch über {_z(kante + b_)} $, 🦊 Fehlausbruch bei einem Schluss unter {_z(kante - b_)} $"
                 if t["richtung"] > 0 else
                 f"📒 bestätigt bei einem Tief unter {_z(kante - b_)} $, 🦊 Falle bei einem Schluss über {_z(kante + b_)} $"))
    if rw:
        import rueckenwind
        kl = rw.get("klasse")
        f(f"Rückenwind: Klasse {f'{kl} {rueckenwind.KLASSEN[kl - 1]}' if kl else 'keine'}, RS-Rang {rw.get('rang_vor4')} → "
          f"{rw.get('rang')} in 4 Wochen, RS-Linie {rw.get('richtung') or '–'}, Sektor {rw.get('sektor')} "
          f"({rw.get('sektor_feld') or '–'}), Branche {rw.get('branche')} ({rw.get('branche_feld') or '–'}), "
          f"Geld-Ampel {rw.get('geld_ampel')}")
    if markt:
        import zirkel
        f(f"Markt-Ampel (Lagebild: Spitze und Heer bestimmen, der Index bestätigt): {markt['wort']} · " + " · ".join(zirkel.markt_text(markt)))
    if termin:
        f(f"Nächste Zahlen: {termin}")
    for x in tiefe or []:                         # Aussagezeilen der Seite Analyse (Tiefenanalyse, 21.11.2026)
        f(f"Tiefenanalyse – {x}")
    nummern = {f"F{i + 1}": x for i, x in enumerate(felder)}
    return "\n".join(f"{n}: {x}" for n, x in nummern.items()), nummern


_ZAHL = re.compile(r"\d+(?:[.,]\d+)?")


def _zahlen(text):
    return {z.replace(",", ".").rstrip("0").rstrip(".") for z in _ZAHL.findall(text or "")}


def pruefen(antwort, nummern, kurs):
    """Prüfbefunde (Liste von Texten, leer = bestanden)."""
    fehl = []
    erlaubt = set().union(*(_zahlen(x) for x in nummern.values())) | {"1", "2", "3", "4", "5", "10", "20", "50"}
    s = antwort.get("schuss")
    for b in (antwort.get("belege") or []) + [antwort.get("gegenzeuge") or {}]:
        feld = str(b.get("feld", "")).strip().upper()
        if feld and feld not in nummern:
            fehl.append(f"Feld {feld} gibt es im Material nicht")
        fremd = _zahlen(b.get("text")) - erlaubt
        if fremd:
            fehl.append(f"Zahl nicht im Material: {', '.join(sorted(fremd))} ({feld})")
    if len(antwort.get("belege") or []) > 3:
        fehl.append("mehr als drei Belege")
    import gestaltung
    for feld_ in ("unternehmen", "quartal"):
        for z in antwort.get(feld_) or []:
            if not str(z).startswith(gestaltung.ZEICHEN):
                fehl.append(f"Zeile ohne Zeichen ({feld_}): {str(z)[:60]}")
    marken = [float(x) for x in erlaubt if x.replace(".", "", 1).isdigit()]
    for z in _zahlen(antwort.get("fazit")) | _zahlen(antwort.get("ausloeser")):
        x = float(z)
        if (1 - KURS_SPANNE) * kurs <= x <= (1 + KURS_SPANNE) * kurs and not any(abs(x - m) <= KURS_GENAU * m for m in marken):
            fehl.append(f"Kursmarke {z} steht nicht im Material")
    antwort["wettbewerber"] = [w_.strip().upper() for w_ in antwort.get("wettbewerber") or []
                               if re.fullmatch(r"[A-Za-z.\-]{1,6}", str(w_).strip())][:WETTBEWERBER]
    a, w = antwort.get("ausloeser_kurs") or 0, antwort.get("widerlegt_kurs") or 0
    if s == "abwarten":
        s = antwort.get("richtung")
        if not a:
            fehl.append("abwarten ohne Kurs des Auslösers")
        if s not in ("long", "short"):
            fehl.append("abwarten ohne Richtung")
    if s in ("long", "short"):
        if not (a and w):
            fehl.append("Auslöser oder Widerlegung ohne Kurs")
        elif s == "long" and not a > w:
            fehl.append("long: der Auslöser muss über dem Widerlegungskurs liegen")
        elif s == "short" and not a < w:
            fehl.append("short: der Auslöser muss unter dem Widerlegungskurs liegen")
        elif s == "long" and w >= kurs:
            fehl.append("long: der Widerlegungskurs liegt nicht unter dem Kurs")
        elif s == "short" and w <= kurs:
            fehl.append("short: der Widerlegungskurs liegt nicht über dem Kurs")
    weich = [x for x in ("könnte", "möglicherweise", "eventuell", "vielleicht", "sollte man beobachten")
             if x in (antwort.get("disbalance") or "").lower()]
    if weich:
        fehl.append("Weichmacher in der Disbalance: " + ", ".join(weich))
    return fehl


def _pfad(tk, stand):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, f"{tk.upper()}_{stand}.json")


def gespeichert(tk, stand):
    return json_lesen(_pfad(tk, stand), None)


def rufen(tk, stand, r, kurs, **kw):
    """Ein Call (oder der gespeicherte des Tages) → {antwort, pruefung, material, stand, kosten}."""
    alt = gespeichert(tk, stand)
    if alt:
        return alt
    import modell
    text, nummern = material(tk, r, kurs, **kw)
    vorher = modell.kosten()["usd"]
    antwort = modell._formular(SYSTEM, f"Material zu {tk} (Kurstag {stand}):\n{text}\n\nRecherchiere Unternehmen, Quartal "
                               "und Wettbewerber im Netz und schreibe Einschätzung und Fazit aus dem Material.",
                               "schuss_melden", SCHEMA, 8000, suchen=SUCHEN)
    gefunden = list(modell._LETZTER.get("urls") or [])
    antwort["quellen"] = [q for q in antwort.get("quellen") or [] if q in gefunden] or gefunden[:6]   # Technik: 6 Quellen
    erg = {"antwort": antwort, "pruefung": pruefen(antwort, nummern, kurs), "material": nummern, "stand": stand,
           "kosten": round(modell.kosten()["usd"] - vorher, 4)}
    json_schreiben(_pfad(tk, stand), erg, ensure_ascii=False)
    return erg
