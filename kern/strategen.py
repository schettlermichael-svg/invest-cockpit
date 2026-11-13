"""Strategen-Call (Micky 13.11.2026): ein Stratege, der die Daten der App richtig deutet – kein Online-Gang, kein
allgemeines Blabla. Auftrag des Snipers: die Ineffizienz und Disbalance finden, die den Kurs aus der Zone ausbrechen
lässt – oder sagen, dass es keinen Schuss gibt.

Material: nur der Zustand aus kern/auktion.py (Code für Balance und Ungleichgewicht) und Felder der App, jedes mit
einer Nummer (F1, F2 …). Die Kette, an der der Stratege entlanggeht:
    Zustand → Anlass → wer ist am Rand stärker → angenommen oder abgelehnt → wo wartet die Gegenseite → eigen oder geliehen.
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

SYSTEM = """Du bist der Stratege des Invest Cockpits – ein Sniper, kein Kommentator. Du bekommst das Material eines Titels:
den Zustand im Code für Balance und Ungleichgewicht und nummerierte Felder der App (F1, F2 …). Nur dieses Material
gilt. Du gehst nicht online, du erfindest keine Zahl, du nennst keine Zahl, die nicht im Material steht.

Der Code: Ein Anlass (Information, leere Verteidiger, Zwang gefangener Händler) bringt die Balance an den Rand. Am Rand
wird getestet. Wird der Ausbruch abgelehnt, läuft der Kurs zurück zum anderen Rand. Wird er angenommen, entsteht ein
Ungleichgewicht, das läuft, bis eine von drei Kräften es beendet: der Gegner antwortet (Mauer, Kraft ohne Weg, Exzess),
der Antrieb erlischt (Klimax, Wechsel der Phase, Rückschlag), der Wert wird akzeptiert (neue Wertzone).

Dein Auftrag: Finde die eine Disbalance, die den Kurs aus der Zone treibt – wer ist am Rand stärker, und warum ist die
Gegenseite schwach, leer oder gefangen? Geh die Kette entlang: Zustand → Anlass → wer ist am Rand stärker → angenommen
oder abgelehnt → wo wartet die Gegenseite → eigen oder geliehen.

Regeln:
1. Kein Weichmacher. Kein „könnte“, „möglicherweise“, „man sollte beobachten“. Du urteilst.
2. „kein Schuss“ ist eine gute Antwort, wenn die Disbalance fehlt. Lieber kein Schuss als ein schwacher.
3. Jeder Beleg nennt sein Feld (F-Nummer) und steht im Material. Höchstens drei – die stärksten.
4. Auslöser: der Kurs und die Bedingung, bei der du abdrückst (z. B. Schluss über dem Rand mit Volumen).
5. Widerlegt bei: der Kurs und die Bedingung, bei der deine Deutung falsch ist.
6. Gegenzeuge: das stärkste Feld gegen deinen Schuss – ehrlich, mit F-Nummer.
7. Geliehene Kraft (der Markt trägt den Titel) ist schwächer als eigene. Sag es, wenn sie geliehen ist.
8. Die Haltung des Marktes gilt für den Markt, nicht für den Titel: Stärke in der Schwäche wird nie wegen des
   Marktes verworfen.
Schreib einfaches Deutsch, kurze Sätze."""

SCHEMA = {
    "type": "object",
    "properties": {
        "schuss": {"type": "string", "enum": ["long", "short", "kein"]},
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
    },
    "required": ["schuss", "disbalance", "belege", "ausloeser", "widerlegt", "gegenzeuge"],
}


def _z(x, f=".2f"):
    return format(x, f).replace(".", ",")


def material(tk, e, kurs, atr=None, rw=None, markt=None, setup=None, termin=None):
    """Nummerierte Felder → (Text, {F-Nummer: Text})."""
    felder = []

    def f(text):
        if text:
            felder.append(str(text))

    f(f"Titel {tk}, Kurs {_z(kurs)} $" + (f", ATR (14 Tage) {_z(atr)} $" if atr else ""))
    if e:
        import auktion
        f(f"Zustand: {auktion.wort(e)} · {e.get('unterzeile', '')}")
        if e.get("oben") and e.get("unten"):
            f(f"Ränder der Balance: unten {_z(e['unten'])} $, oben {_z(e['oben'])} $")
        for x in e.get("anlass") or []:
            f(f"Anlass – {x}")
        for platz, x in e.get("belege") or []:
            f(f"{platz} – {x}")
        for x in e.get("ende") or []:
            f(f"Ende des Laufs – {x}")
        for x in e.get("gegenseite") or []:
            f(f"Gegenseite – {x}")
        if e.get("kraft"):
            f(f"Eigen oder geliehen – {e['kraft']['text']}")
    if setup:
        f(f"Setup der App: {setup}")
    if rw:
        f(f"Rückenwind: RS-Rang {rw.get('rang_vor4')} → {rw.get('rang')} in 4 Wochen, Stufe {rw.get('stufe') or 'keine'}, "
          f"Sektor {rw.get('sektor')} ({rw.get('sektor_feld') or '–'}), Branche {rw.get('branche')} "
          f"({rw.get('branche_feld') or '–'}), Geld-Ampel {rw.get('geld_ampel')}")
    if markt:
        import auktion
        f(f"Markt: {auktion.wort(markt)} · {markt.get('unterzeile', '')}")
    if termin:
        f(f"Nächste Zahlen: {termin}")
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
    a, w = antwort.get("ausloeser_kurs") or 0, antwort.get("widerlegt_kurs") or 0
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


def rufen(tk, stand, e, kurs, **kw):
    """Ein Call (oder der gespeicherte des Tages) → {antwort, pruefung, material, stand, kosten}."""
    alt = gespeichert(tk, stand)
    if alt:
        return alt
    import modell
    text, nummern = material(tk, e, kurs, **kw)
    vorher = modell.kosten()["usd"]
    antwort = modell._formular(SYSTEM, f"Material zu {tk} (Kurstag {stand}):\n{text}", "schuss_melden", SCHEMA, 3000)
    erg = {"antwort": antwort, "pruefung": pruefen(antwort, nummern, kurs), "material": nummern, "stand": stand,
           "kosten": round(modell.kosten()["usd"] - vorher, 4)}
    json_schreiben(_pfad(tk, stand), erg, ensure_ascii=False)
    return erg
