"""Verbindung zum Modell (Anthropic) – Schlüssel, Aufruf, Kostenbuch und Monatsdeckel. Übrig vom Stab, als der
Konferenzraum am 13.11.2026 abgebaut wurde (Micky: „Der Konferenzraum kann weg“); gebraucht für den künftigen
Strategen-Call. Schlüssel in einstellungen/anthropic_schluessel.txt (nie im Repository), Kostenbuch in
daten/konferenz/kosten.json."""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

from dateien import json_lesen, json_schreiben


HIER = os.path.dirname(os.path.abspath(__file__))


SCHLUESSEL = os.path.join(HIER, "..", "einstellungen", "anthropic_schluessel.txt")


SPEICHER = os.path.join(HIER, "..", "daten", "konferenz")


MODELL = "claude-opus-5-5"                                             # alle Strategen auf Opus (Micky 10.11.2026)


PREIS_EIN, PREIS_AUS, PREIS_SUCHE = 4.0 / 1e6, 20.0 / 1e6, 0.01       # $ je Token bzw. je Suche


DECKEL_USD = 50.0                                                      # Monatsdeckel (Micky 11.11.2026: alle Strategen auf Opus, gemessen ~2,10 $ je Konferenz)


def schluessel():
    try:
        return open(SCHLUESSEL, encoding="utf-8").read().strip() or None
    except OSError:
        return None


def schluessel_speichern(wert):
    os.makedirs(os.path.dirname(SCHLUESSEL), exist_ok=True)
    with open(SCHLUESSEL, "w", encoding="utf-8") as f:
        f.write(wert.strip())
    os.chmod(SCHLUESSEL, 0o600)


def _pfad(name):
    os.makedirs(SPEICHER, exist_ok=True)
    return os.path.join(SPEICHER, name)


def kosten():
    """Kostenbuch des laufenden Monats: {"usd", "aufrufe", "suchen", "ein", "aus"}."""
    return (json_lesen(_pfad("kosten.json"), {}) or {}).get(f"{datetime.now():%Y-%m}",
                                                             {"usd": 0.0, "aufrufe": 0, "suchen": 0, "ein": 0, "aus": 0})


def _buchen(usage):
    buch = json_lesen(_pfad("kosten.json"), {}) or {}
    m = buch.setdefault(f"{datetime.now():%Y-%m}", {"usd": 0.0, "aufrufe": 0, "suchen": 0, "ein": 0, "aus": 0})
    ein = (usage.get("input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0) * 1.25 \
        + (usage.get("cache_read_input_tokens") or 0) * 0.05
    aus = usage.get("output_tokens") or 0
    suchen = ((usage.get("server_tool_use") or {}).get("web_search_requests") or 0)
    usd = ein * PREIS_EIN + aus * PREIS_AUS + suchen * PREIS_SUCHE
    m["usd"] = round(m["usd"] + usd, 4)
    m["aufrufe"] += 1
    m["suchen"] += suchen
    m["ein"] += int(ein)
    m["aus"] += aus
    json_schreiben(_pfad("kosten.json"), buch)
    return usd


class Deckel(Exception):
    pass


def _rufen(system, nachrichten, max_tokens, werkzeuge=None, wahl=None):
    """Ein Aufruf an Claude (mit Fortsetzung bei pause_turn); gibt die Inhaltsblöcke zurück. Bricht vor dem Aufruf ab,
    wenn kein Schlüssel da ist oder der Monatsdeckel erreicht ist."""
    k = schluessel()
    if not k:
        raise RuntimeError("kein API-Schlüssel eingetragen (Seite Setups · ⚙ Verbindungen)")
    if kosten()["usd"] >= DECKEL_USD:
        raise Deckel(f"Monatsdeckel von {DECKEL_USD:.0f} $ erreicht – Modell-Aufrufe ruhen bis zum Monatsende")
    bloecke = []
    for _ in range(4):
        daten = {"model": MODELL, "max_tokens": max_tokens, "system": system, "messages": nachrichten}
        if werkzeuge:
            daten["tools"] = werkzeuge
        if wahl:
            daten["tool_choice"] = wahl
        antwort = _senden(k, daten)
        _buchen(antwort.get("usage") or {})
        bloecke += antwort.get("content", [])
        _LETZTER["stop"] = antwort.get("stop_reason")
        if antwort.get("stop_reason") != "pause_turn":
            break
        nachrichten = nachrichten[:1] + [{"role": "assistant", "content": antwort["content"]}]
    return bloecke


def _anfrage(system, inhalt, max_tokens=3000, suchen=0):
    """Freier Text als Antwort (Probe, Stab fragen, Notizen der Web-Suche)."""
    werkzeuge = [{"type": "web_search_20250305", "name": "web_search", "max_uses": suchen}] if suchen else None
    bloecke = _rufen(system, [{"role": "user", "content": inhalt}], max_tokens, werkzeuge)
    _LETZTER["bloecke"] = [b.get("type") for b in bloecke]               # zur Fehlersuche (Stab fragen, 11.11.)
    return "".join(b.get("text", "") for b in bloecke if b.get("type") == "text").strip()


class Unlesbar(Exception):
    def __init__(self, text, roh):
        super().__init__(text)
        self.roh = roh


_LETZTER = {"stop": None}


def _ordnen(obj, schema):
    """Felder, die das Modell als JSON-Text statt als Liste/Objekt schickt, in Listen/Objekte wandeln (rekursiv)."""
    if not isinstance(obj, dict):
        return obj
    for key, sub in (schema.get("properties") or {}).items():
        v = obj.get(key)
        if isinstance(v, str) and sub.get("type") in ("array", "object"):
            try:
                v = json.loads(v)
            except ValueError:
                continue
        if sub.get("type") == "array" and isinstance(v, list) and (sub.get("items") or {}).get("type") == "object":
            neu = []
            for x in v:
                if isinstance(x, str):
                    try:
                        x = json.loads(x)
                    except ValueError:
                        continue
                if isinstance(x, dict):
                    neu.append(_ordnen(x, sub["items"]))
            v = neu
        if v is not None:
            obj[key] = v
    return obj


def _gueltig(obj, schema):
    """Alle Pflichtfelder da und vom richtigen Typ (Text nicht leer, Liste als Liste)."""
    if not isinstance(obj, dict):
        return False
    for key in schema.get("required", []):
        typ = ((schema.get("properties") or {}).get(key) or {}).get("type")
        v = obj.get(key)
        if v is None or (typ == "string" and not str(v).strip()) or (typ == "array" and not isinstance(v, list)):
            return False
    return True


def _formular(system, inhalt, name, schema, max_tokens=8000):
    """Antwort über ein festes Formular (Werkzeug der Schnittstelle): die Schnittstelle gibt ein fertiges Objekt zurück,
    kein JSON-Text, der an Anführungszeichen zerbrechen kann. Opus 5.5 erlaubt kein erzwungenes Werkzeug
    (tool_choice „tool“/„any“ → Fehler 400, Nachtlauf 11.11.2026) – deshalb „auto“ mit klarer Anweisung; schreibt das
    Modell trotzdem Text, wird ein JSON-Objekt darin gelesen. Jede Meldung wird geprüft (alle Pflichtfelder, Listen als
    Listen); unvollständig – etwa am Token-Limit abgeschnitten (11.11.: leere Meldung des Risikomanagers, Tagesbefehl
    nur mit Lage) – gibt es einen zweiten Versuch mit doppeltem Limit, sonst Unlesbar mit der Rohantwort."""
    werkzeug = [{"name": name, "description": "Meldung an den Stab abgeben – der einzige Weg, die Meldung abzugeben",
                 "input_schema": schema}]
    auftrag = (f"{inhalt}\n\nGib deine Antwort ausschließlich über das Werkzeug „{name}“ ab – genau ein Aufruf, "
               "alle Pflichtfelder ausgefüllt, Listen als echte Listen, kein Text davor oder danach.")
    roh = ""
    for versuch in range(2):
        bloecke = _rufen(system, [{"role": "user", "content": auftrag}], max_tokens, werkzeug, {"type": "auto"})
        kandidaten = [b["input"] for b in bloecke if b.get("type") == "tool_use" and isinstance(b.get("input"), dict)]
        text = "".join(b.get("text", "") for b in bloecke if b.get("type") == "text")
        a, e = text.find("{"), text.rfind("}")
        if a >= 0 and e > a:
            try:
                kandidaten.append(json.loads(text[a:e + 1]))
            except ValueError:
                pass
        for obj in kandidaten:
            obj = _ordnen(obj, schema)
            if _gueltig(obj, schema):
                return obj
        roh = f"stop_reason={_LETZTER['stop']} · " + json.dumps(bloecke, ensure_ascii=False)[:600]
        if _LETZTER["stop"] == "max_tokens":
            max_tokens *= 2
        auftrag = (f"{inhalt}\n\nWICHTIG: Deine letzte Antwort war unvollständig oder kam nicht über das Werkzeug. "
                   f"Rufe jetzt das Werkzeug „{name}“ auf und fülle alle Pflichtfelder aus ({', '.join(schema.get('required', []))}); "
                   "fasse dich kürzer. Kein freier Text.")
    raise Unlesbar("Antwort ohne vollständiges Formular", roh)


def _senden(k, daten):
    roh = json.dumps(daten).encode("utf-8")
    for versuch in range(3):
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=roh, method="POST",
                                     headers={"x-api-key": k, "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503, 504, 529) and versuch < 2:   # überlastet, Rate-Limit oder kurz nicht
                # erreichbar (13.11.2026: 503 „credential validation failed“ mitten in der Konferenz): warten, noch einmal
                time.sleep(20 * (versuch + 1))
                continue
            raise RuntimeError(f"Anthropic antwortet {e.code}: {text}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if versuch < 2:
                time.sleep(10)
                continue
            raise RuntimeError(f"Anthropic nicht erreichbar: {getattr(e, 'reason', e)}") from None
    raise RuntimeError("Anthropic nicht erreichbar")


def probe():
    """Kurzer Test nach dem Eintragen des Schlüssels: Text und Meldeformular. (True, Text) oder (False, Grund). Kostet
    weniger als 1 Cent."""
    try:
        antwort = _anfrage("Antworte nur mit OK.", "Verbindungstest", 5)
    except Exception as e:  # noqa: BLE001
        return False, str(e)
    try:                                         # auch das Formular prüfen – daran scheiterte der Nachtlauf am 11.11.
        f = _formular("Du testest eine Verbindung.", "Melde den Status ok.", "melden",
                      {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}, 200)
    except Exception as e:  # noqa: BLE001
        return False, f"Text geht ({antwort[:10] or 'OK'}), aber das Meldeformular nicht: {e}"
    return True, f"Verbindung steht – {MODELL} antwortet, Meldeformular funktioniert ({f.get('status', 'ok')})"


def _zahl_de(x, n=2):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")

