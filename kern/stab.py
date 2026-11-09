"""Der Stab – MARAGA Investment (Konferenzraum, 09.11.2026).

Fünf Strategen lesen nach dem Nachtlauf die Daten der App und schreiben ihre Lagemeldung. Sie erklären und zeigen auf,
sie filtern nichts und erfinden keine Werte: jede Zahl, die sie nennen, steht in den Daten, die sie bekommen.
  2 Strömungs-Analyst   Rückenwind: Geld in Sektoren, Branchen, Themen, Stufenwechsel, Anführer und Verfolger
  3 Fundamental-Analyst Zahlen der Kandidaten, Termine ≤ 14 Tage, Reaktionen; Nachrichten per Web-Suche (begrenzt)
  4 Chart-Techniker     Setups der Kandidaten: Zone, Enge, Base, Ausbruch, Kaufzone, Fehlausbruch, Ermüdung
  5 Risikomanager       Depot, Stopps, Klumpen, Earnings im Depot, Barometer des Marktes
  1 Stratege            liest die vier Meldungen und schreibt den Tagesbefehl (Lage in 3 Sätzen, 3 wichtigste Hinweise)
Jeder Hinweis kann einen Titel und einen Tag tragen – daraus werden die Nadeln im Chart der Akte.

Modell: Claude Sonnet 5.5 über die Anthropic-Schnittstelle (2 $ je Million Eingabe-, 10 $ je Million Ausgabe-Token,
Web-Suche 10 $ je 1.000). Kostenbuch je Monat in daten/konferenz/kosten.json; ab dem Deckel (DECKEL_USD) ruft der
Stab nicht mehr an bis zum Monatsende. Schlüssel: einstellungen/anthropic_schluessel.txt (nicht in Git), in der App
auf der Seite Konferenzraum eingetragen.
"""
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
MODELL = "claude-sonnet-5-5"
PREIS_EIN, PREIS_AUS, PREIS_SUCHE = 2.0 / 1e6, 10.0 / 1e6, 0.01       # $ je Token bzw. je Suche
DECKEL_USD = 20.0                                                      # Monatsdeckel (Micky: Empfehlung übernommen)
SUCHEN_NACHT = 10                                                      # Web-Suchen je Nacht (Fundamental-Analyst)
SUCHEN_FRAGE = 3
KANDIDATEN_MAX = 40

STRATEGEN = {
    1: ("Stratege", "Tagesbefehl"),
    2: ("Strömungs-Analyst", "Wohin fließt das Geld?"),
    3: ("Fundamental-Analyst", "Tragen die Zahlen?"),
    4: ("Chart-Techniker", "Wo steht der Angriff?"),
    5: ("Risikomanager", "Was kann uns treffen?"),
}

GRUNDSATZ = (
    "Du bist Mitglied im Stab von MARAGA Investment, dem Handelsstab eines Swing-Traders (long und short, Systeme "
    "Minervini und Kullamägi, Rückenwind aus relativer Stärke und Geldfluss). Du arbeitest im Invest Cockpit, seiner App. "
    "Regeln: 1. Schreibe auf Deutsch, klar und knapp, ohne Floskeln. 2. Verwende nur Zahlen und Fakten aus den Daten, "
    "die du bekommst (bei Web-Suche: nur aus den Fundstellen) – erfinde nichts; fehlt etwas, sage es. 3. Du erklärst und "
    "zeigst auf, du filterst nichts weg und gibst keine Kauf- oder Verkaufsbefehle – die Entscheidung trifft der Trader. "
    "4. Ampeln statt Punktzahlen: grün = spricht dafür, gelb = beachten, rot = Warnung. 5. Eine kurze Kriegs- oder "
    "Schlachtanalogie ist erlaubt, wenn sie die Lage schneller erklärt. 6. Antworte ausschließlich mit gültigem JSON "
    "im verlangten Format, ohne Text davor oder danach.")

FORMAT_MELDUNG = (
    'Format: {"meldung": "3 bis 6 Sätze Lage aus deiner Sicht", "hinweise": [{"titel": "Ticker oder null", '
    '"datum": "YYYY-MM-DD des Tages, auf den sich der Hinweis bezieht, oder null", "ampel": "grün|gelb|rot", '
    '"text": "1 bis 2 Sätze"}]} – höchstens 12 Hinweise, die wichtigsten zuerst.')

AUFTRAG = {
    2: "Du bist der Strömungs-Analyst. Lies den Rückenwind: Welche Sektoren, Branchen und Themen ziehen Geld an, welche "
       "verlieren es, welche haben das Feld gewechselt? Welche Titel sind neu in eine Stufe gekommen? Wer führt "
       "(Anführer), wer holt am schnellsten auf (Verfolger)? Zeige frühe Strömungen, bevor sie sichtbar sind.",
    3: "Du bist der Fundamental-Analyst. Prüfe die Zahlen der Kandidaten (neun Punkte), die Reaktion auf die letzten "
       "Zahlen und Termine in den nächsten 14 Tagen. Tragen die Zahlen den Kurs (Superperformance nach O'Neil und "
       "Minervini) oder läuft der Kurs ohne Fundament? Nutze die Web-Suche sparsam nur für wichtige aktuelle Nachrichten "
       "zu den stärksten Kandidaten (Übernahmen, Prognosen, Ereignisse) und nenne dann die Quelle im Text.",
    4: "Du bist der Chart-Techniker. Lies die Setups der Kandidaten: Zone und Enge des VCP-Scanners, Basennummer, "
       "Ausbruch mit Volumen, Fehlausbruch, Kaufzone, Ermüdung (Short). Wo steht ein Angriff unmittelbar bevor, wo ist "
       "er schon zu weit gelaufen, wo bricht eine Stellung? Nenne beim Ausbruch den Tag als datum.",
    5: "Du bist der Risikomanager. Prüfe das Depot (Stopps, Abstand, Earnings vor dem Stopp), Klumpen in einem Sektor "
       "oder Thema, die Lage des Gesamtmarkts (Barometer) und Kandidaten mit Warnzeichen. Was kann uns treffen, wo ist "
       "die Rückzugslinie zu eng oder zu weit?",
}


# ── Schlüssel, Kosten ──

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


def _anfrage(system, inhalt, max_tokens=3000, suchen=0):
    """Ein Aufruf an Claude; gibt den Text der Antwort zurück. Web-Suche als Server-Werkzeug, pause_turn wird
    fortgesetzt. Bricht vor dem Aufruf ab, wenn der Monatsdeckel erreicht ist."""
    k = schluessel()
    if not k:
        raise RuntimeError("kein API-Schlüssel eingetragen (Seite Konferenzraum)")
    if kosten()["usd"] >= DECKEL_USD:
        raise Deckel(f"Monatsdeckel von {DECKEL_USD:.0f} $ erreicht – der Stab ruht bis zum Monatsende")
    nachrichten = [{"role": "user", "content": inhalt}]
    werkzeuge = [{"type": "web_search_20250305", "name": "web_search", "max_uses": suchen}] if suchen else []
    texte = []
    for _ in range(4):                                       # pause_turn bei langen Suchen fortsetzen
        daten = {"model": MODELL, "max_tokens": max_tokens, "system": system, "messages": nachrichten}
        if werkzeuge:
            daten["tools"] = werkzeuge
        antwort = _senden(k, daten)
        _buchen(antwort.get("usage") or {})
        texte += [b.get("text", "") for b in antwort.get("content", []) if b.get("type") == "text"]
        if antwort.get("stop_reason") != "pause_turn":
            break
        nachrichten = nachrichten[:1] + [{"role": "assistant", "content": antwort["content"]}]
    return "".join(texte).strip()


def _senden(k, daten):
    roh = json.dumps(daten).encode("utf-8")
    for versuch in range(5):
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=roh, method="POST",
                                     headers={"x-api-key": k, "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 529) and versuch < 4:     # überlastet oder Rate-Limit: warten und noch einmal
                time.sleep(20 * (versuch + 1))
                continue
            raise RuntimeError(f"Anthropic antwortet {e.code}: {text}") from None
        except urllib.error.URLError as e:
            if versuch < 4:
                time.sleep(10)
                continue
            raise RuntimeError(f"Anthropic nicht erreichbar: {e.reason}") from None
    raise RuntimeError("Anthropic nicht erreichbar")


def _json(text):
    """JSON aus der Antwort (auch wenn sie in ``` eingefasst ist)."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        t = t[t.find("{"):]
    a, b = t.find("{"), t.rfind("}")
    return json.loads(t[a:b + 1])


# ── Lagebild aus den Daten der App ──

def _knapp(x, n=200):
    return str(x)[:n] if x is not None else None


def lagebild():
    """Alles, was der Stab liest, als dict – nur aus gespeicherten Daten des Nachtlaufs (kein Abruf)."""
    import depot
    import kartentisch
    import rueckenwind
    import rueckenwind_seite
    import watchlists
    rw = rueckenwind.laden() or {}
    tisch = kartentisch.laden() or {}
    rang = kartentisch.RANG
    titel_t = tisch.get("titel") or {}
    rw_t = rw.get("titel") or {}
    kand = sorted((tk for tk, x in titel_t.items() if rang.get(x.get("reihe"), 0) >= 4),
                  key=lambda tk: -rang.get(titel_t[tk].get("reihe"), 0))
    drei = [tk for tk, _ in rueckenwind_seite.dreifach_liste(rw)] if rw else []
    dep = depot.laden()
    pos = [p["ticker"] for p in dep.get("positionen", [])]
    alle = list(dict.fromkeys(pos + kand + drei))[:KANDIDATEN_MAX]
    wl = set(watchlists.alle())

    def akte(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        z = r.get("zahlen") or {}
        return {"titel": tk, "reihe": x.get("reihe"), "watchlist": tk in wl, "depot": tk in pos,
                "kacheln": {k: [v[0] if not isinstance(v[0], list) else "/".join(str(a) for a in v[0]), _knapp(v[1], 60),
                                _knapp(v[2], 160)] for k, v in (x.get("kacheln") or {}).items()},
                "ausbruch": _knapp(x.get("ausbruch"), 200), "scanner": _knapp(x.get("scanner"), 200),
                "rueckenwind": {k: r.get(k) for k in ("stufe", "rang", "rang_vor4", "tempo", "beschleunigung",
                                                       "rs_hoch_vor_kurs", "geld_ampel", "sektor", "sektor_feld",
                                                       "branche", "branche_feld", "thema", "zufluss", "kurs", "jung")}
                if r else None,
                "zahlen": {"ampel": z.get("ampel"), "punkte": z.get("punkte"), "termin": z.get("termin"),
                           "reaktion": z.get("reaktion")} if z else None}
    gruppen = [{k: g.get(k) for k in ("art", "name", "feld", "feld_vor4", "seit_wochen", "weg", "zufluss",
                                      "rueckschlag", "stabil")} for g in rw.get("gruppen", [])]
    wechsel = [{"titel": tk, **e[-1]} for tk, e in (rw.get("logbuch") or {}).items()
               if e and e[-1].get("seit") and e[-1]["seit"] >= (rw.get("stand") or "")[:10]][:40]
    schnell = {a: [tk for tk in rueckenwind_seite.schnell(rw, a)[1]][:15] for a in ("Anführer", "Verfolger")} if rw else {}
    return {"stand_rueckenwind": rw.get("stand"), "stand_kartentisch": tisch.get("stand"),
            "barometer": tisch.get("barometer"), "gruppen": gruppen, "stufenwechsel_heute": wechsel,
            "schnellsuche": schnell, "kandidaten": [akte(tk) for tk in alle],
            "depot": {"konto": dep.get("konto"), "risiko_pct": dep.get("risiko_pct"),
                      "positionen": dep.get("positionen", [])}}


def _ausschnitt(lb, nr):
    """Was jeder Stratege liest (spart Token)."""
    if nr == 2:
        return {k: lb[k] for k in ("stand_rueckenwind", "gruppen", "stufenwechsel_heute", "schnellsuche")} | {
            "kandidaten": [{"titel": a["titel"], "rueckenwind": a["rueckenwind"]} for a in lb["kandidaten"]]}
    if nr == 3:
        return {"stand": lb["stand_rueckenwind"], "kandidaten": [{"titel": a["titel"], "zahlen": a["zahlen"],
                                                                  "depot": a["depot"]} for a in lb["kandidaten"]]}
    if nr == 4:
        return {"stand": lb["stand_kartentisch"], "kandidaten": [
            {"titel": a["titel"], "reihe": a["reihe"], "kacheln": a["kacheln"], "ausbruch": a["ausbruch"],
             "scanner": a["scanner"], "stufe": (a["rueckenwind"] or {}).get("stufe")} for a in lb["kandidaten"]]}
    return {"barometer": lb["barometer"], "depot": lb["depot"], "kandidaten": [
        {"titel": a["titel"], "depot": a["depot"], "markt": (a["kacheln"] or {}).get("Markt"),
         "sektor": (a["rueckenwind"] or {}).get("sektor"), "thema": (a["rueckenwind"] or {}).get("thema"),
         "termin": (a["zahlen"] or {}).get("termin")} for a in lb["kandidaten"]]}


# ── Konferenz (Nachtlauf) und Fragen ──

def konferenz():
    """Alle fünf Strategen; speichert daten/konferenz/<datum>.json und gibt das Ergebnis zurück."""
    lb = lagebild()
    heute = f"{datetime.now():%Y-%m-%d}"
    erg = {"stand": heute, "zeit": f"{datetime.now():%d.%m.%Y %H:%M}", "modell": MODELL, "meldungen": {}}
    for nr in (2, 3, 4, 5):
        name = STRATEGEN[nr][0]
        inhalt = (f"{AUFTRAG[nr]}\n\n{FORMAT_MELDUNG}\n\nDaten der App (Stand des Nachtlaufs):\n"
                  + json.dumps(_ausschnitt(lb, nr), ensure_ascii=False, default=str))
        try:
            m = _json(_anfrage(GRUNDSATZ, inhalt, 3000, SUCHEN_NACHT if nr == 3 else 0))
        except Deckel:
            raise
        except Exception as e:  # noqa: BLE001 – eine Meldung fehlt, die anderen laufen weiter
            m = {"meldung": f"Keine Meldung: {e}", "hinweise": [], "fehler": True}
        erg["meldungen"][str(nr)] = {"name": name, **m}
    inhalt = ("Du bist der Stratege und führst den Stab. Lies die vier Lagemeldungen und schreibe den Tagesbefehl: "
              "die Lage in drei Sätzen und die drei wichtigsten Hinweise des Tages (mit Titel und Tag, wenn es um einen "
              'Titel geht). Format: {"lage": "drei Sätze", "hinweise": [{"titel": "Ticker oder null", "datum": '
              '"YYYY-MM-DD oder null", "ampel": "grün|gelb|rot", "text": "1 bis 2 Sätze"}]} – genau drei Hinweise.\n\n'
              + json.dumps({"barometer": lb["barometer"], "meldungen": erg["meldungen"]}, ensure_ascii=False,
                           default=str))
    try:
        erg["befehl"] = _json(_anfrage(GRUNDSATZ, inhalt, 1500))
    except Exception as e:  # noqa: BLE001
        erg["befehl"] = {"lage": f"Kein Tagesbefehl: {e}", "hinweise": []}
    json_schreiben(_pfad(f"{heute}.json"), erg, ensure_ascii=False)
    return erg


def letzte():
    """Jüngste Konferenz oder None."""
    if not os.path.isdir(SPEICHER):
        return None
    for f in sorted((f for f in os.listdir(SPEICHER) if f[:4].isdigit() and f.endswith(".json")), reverse=True):
        k = json_lesen(os.path.join(SPEICHER, f))
        if k:
            return k
    return None


def akten(k):
    """Hinweise je Titel aus einer Konferenz: {Ticker: [(Nr. des Strategen, Hinweis)]}, Stratege zuerst."""
    aus = {}
    quellen = [(1, (k.get("befehl") or {}).get("hinweise") or [])] + [
        (int(nr), m.get("hinweise") or []) for nr, m in sorted((k.get("meldungen") or {}).items())]
    for nr, liste in quellen:
        for h in liste:
            tk = (h.get("titel") or "").upper().strip()
            if tk and tk != "NULL":
                aus.setdefault(tk, []).append((nr, h))
    return aus


def frage(text, tk=None):
    """„Stab fragen“: freie Frage an den Stab, auf Wunsch zu einem Titel. Antwort als Text, gespeichert."""
    lb = lagebild()
    k = letzte() or {}
    kontext = {"tagesbefehl": k.get("befehl"), "meldungen": {nr: m.get("meldung") for nr, m in
                                                            (k.get("meldungen") or {}).items()},
               "barometer": lb["barometer"]}
    if tk:
        tk = tk.upper().strip()
        kontext["titel"] = next((a for a in lb["kandidaten"] if a["titel"] == tk), None) or _einzelakte(tk)
    inhalt = ("Der Trader fragt den Stab. Antworte als Stab (der Stratege führt, die Fachleute ergänzen) in höchstens "
              "12 Sätzen, auf Deutsch, nur mit Fakten aus den Daten oder aus Web-Fundstellen (dann Quelle nennen). "
              'Format: {"antwort": "Text"}\n\nFrage: ' + text + "\n\nDaten der App:\n"
              + json.dumps(kontext, ensure_ascii=False, default=str))
    antwort = _json(_anfrage(GRUNDSATZ, inhalt, 1500, SUCHEN_FRAGE)).get("antwort", "")
    buch = json_lesen(_pfad("fragen.json"), []) or []
    buch.insert(0, {"zeit": f"{datetime.now():%d.%m.%Y %H:%M}", "titel": tk, "frage": text, "antwort": antwort})
    json_schreiben(_pfad("fragen.json"), buch[:50], ensure_ascii=False)
    return antwort


def fragen():
    return json_lesen(_pfad("fragen.json"), []) or []


def _einzelakte(tk):
    """Titel außerhalb der Kandidaten: Rückenwind-Eintrag und Kacheln der abgelegten Titelseite."""
    import rueckenwind
    r = ((rueckenwind.laden() or {}).get("titel") or {}).get(tk)
    kach = None
    try:
        import titel
        ab = titel.abgelegt(tk)
        kach = ab[0].get("kacheln") if ab else None
    except Exception:  # noqa: BLE001
        pass
    return {"titel": tk, "rueckenwind": r, "kacheln": kach}
