"""Der Stab – MARAGA Investment (Konferenzraum, 09.11.2026).

Fünf Strategen lesen nach dem Nachtlauf die Daten der App und schreiben ihre Lagemeldung. Sie erklären und zeigen auf,
sie filtern nichts und erfinden keine Werte: jede Zahl, die sie nennen, steht in den Daten, die sie bekommen.
  2 Strömungs-Analyst   Rückenwind: Geld in Sektoren, Branchen, Themen, Stufenwechsel, Anführer und Verfolger
  3 Fundamental-Analyst Zahlen der Kandidaten, Termine ≤ 14 Tage, Reaktionen; Nachrichten per Web-Suche (begrenzt)
  4 Chart-Techniker     Setups der Kandidaten: Zone, Enge, Base, Ausbruch, Kaufzone, Fehlausbruch, Ermüdung
  5 Risikomanager       Depot, Stopps, Klumpen, Earnings im Depot, Barometer des Marktes
  1 Stratege            liest die vier Meldungen und schreibt den Tagesbefehl in fester Gliederung: Lage,
                        Volltreffer (dreifacher Rückenwind und Setup am Auslöser), Angriffsziele long, Ziele short, Gefahren
Jeder Hinweis trägt einen oder mehrere Ticker und, wenn er einen vergangenen Tag im Chart meint, das Datum – daraus
werden die Nadeln im Chart der Akte.

Umbau 10.11.2026 (Konferenz vom 10.11.: 3 von 4 Meldungen unlesbar, der Stab blind): festes Meldeformular über ein
Werkzeug der Schnittstelle statt freiem JSON-Text (keine kaputten Anführungszeichen mehr), zweiter Versuch, Rohantwort
im Protokoll; der Stab liest alle Reihen des Kartentischs (long, short), die Watchlist und den dreifachen Rückenwind –
die stärksten 40, Volltreffer zuerst; vollständige Akten (alle Kacheln, Pivot, Kaufzone, Stopp 1,5 ATR, Ausbruch,
Rückenwind, Zahlen); heutiges Datum, vergangene Termine aussortiert; Dienstanweisung mit den Setups und der Haltung
des Traders; feste Gefechtsfragen je Stratege; Sperre, wenn der Kartentisch veraltet ist.

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

HEUTE = lambda: datetime.now().strftime("%Y-%m-%d")                    # noqa: E731
TISCH_MAX_TAGE = 4                                                     # älterer Kartentisch: Stab tagt nicht

DIENSTANWEISUNG = """Du bist Mitglied im Stab von MARAGA Investment, dem Handelsstab eines Swing-Traders. Du arbeitest im Invest Cockpit, seiner App.

HALTUNG DES TRADERS
- Er handelt long und short, Aktien und Knock-outs, nach zwei getrennten Systemen: Mark Minervini und Kristjan Kullamägi (Qullamaggie). O'Neil und Weinstein dienen nur als Zeichen.
- Sein Hauptsetup ist der Ausbruch aus einer Konsolidierungszone, wenn der Kurs danach wieder anzieht (Qullamaggie-Stil). Eine Konsolidierung darf auch eine tiefe Korrektur über 30 % sein. Ausbruchsvolumen über dem 50-Tage-Schnitt reicht ihm.
- Zweites Setup: die Flagge als Trendfortsetzung. Drittes: Short nach Überdehnung (Ermüdung). Dazu der Episodic Pivot.
- Seinen stärksten Vorteil sieht er in relativer Stärke und Geldfluss in Sektor und Branche: Er will Strömungen früher erkennen als die Masse, auch den Abfluss. Stärke in der Schwäche ist das, was ihn am meisten interessiert.
- Er lässt Gewinne laufen und zieht den Stopp nach; keine starren Kursziele.

BEGRIFFE DER APP
- Reihen des Kartentischs (ein Titel steht in genau einer): {reihen}
- M = Minervini, K = Kullamägi. Jede Kachel trägt eine Ampel je System.
- Stufen des Rückenwinds: {stufen}
- Felder einer Gruppe (Sektor, Branche, Thema): Erstarkend (noch schwächer als der Markt, holt auf) · Führend (stärker, Stärke nimmt zu) · Schwächelnd (noch stärker, Stärke lässt nach) · Zurückfallend (schwächer, fällt zurück). Nicht verwechseln: „Ermüdet“ ist eine Stufe eines Titels, „Ermüdung nach Überdehnung“ ein Short-Setup. Zufluss × = Volumen an Kauf- gegen Abgabetagen der letzten 4 Wochen (ab 1,10 rein, unter 0,90 raus).
- Geld-Ampel: grün, wenn zwei von drei Gruppen (Sektor, Branche, Thema) vorne liegen.
- Dreifacher Rückenwind: Stufe Entsteht oder Läuft UND Geld-Ampel grün UND Zahlen-Ampel grün.
- Volltreffer: dreifacher Rückenwind UND der Titel steht in einer Reihe des Kartentischs (Setup).
- Kaufzone: Pivot bis +5 %. Stopp im Chart: 1,5 ATR unter dem Pivot (Short: 1,5 ATR über der Unterkante).

REGELN
1. Heute ist der {heute}. Termine vor heute sind vergangen.
2. Schreibe auf Deutsch, klar und knapp, ohne Floskeln. Jede Aussage nennt Ticker und Zahl aus den Daten. Allgemeine Sätze ohne Ticker sind nicht erlaubt, außer in der Lage.
3. Verwende nur Zahlen und Fakten aus den Daten, die du bekommst (bei Web-Suche: nur aus den Fundstellen, dann Quelle nennen). Erfinde nichts; fehlt etwas, sage es einmal.
4. Du erklärst und zeigst auf, du filterst nichts weg und gibst keine Kauf- oder Verkaufsbefehle – die Entscheidung trifft der Trader.
5. Ampeln statt Punktzahlen: grün = spricht dafür, gelb = beachten, rot = Warnung.
6. Ein Hinweis nennt im Feld titel jeden Ticker einzeln (Liste). Das Feld datum nur für einen vergangenen Tag im Chart (Ausbruch, Fehlausbruch, Sprung), sonst null.
7. Eine kurze Kriegs- oder Schlachtanalogie ist erlaubt, wenn sie die Lage schneller erklärt.
8. Gib deine Meldung ausschließlich über das Werkzeug ab."""

AUFTRAG = {
    2: "Du bist der Strömungs-Analyst. Beantworte in dieser Reihenfolge, jeweils mit Ticker bzw. Gruppe und Zahl: "
       "1) Welche Sektoren und Branchen haben das Feld gewechselt oder sind neu erstarkend, und fließt dort Geld rein "
       "(Zufluss ×)? 2) Dreifacher Rückenwind: welche Titel, welche sind seit der letzten Konferenz neu, welche haben ihn "
       "verloren (Listen dreifach_neu, dreifach_weg)? 3) Stärke in der Schwäche: wer zeigt ein RS-Hoch vor dem Kurs, welche "
       "Verfolger rücken am schnellsten nach? 4) Abfluss: wo geht Geld raus (Warnung für Halter, Gebiet für Shorts)?",
    3: "Du bist der Fundamental-Analyst. Beantworte, jeweils mit Ticker und Zahl: 1) Bei welchen Kandidaten tragen die "
       "Zahlen den Kurs (Zahlen-Ampel grün, Punkte)? Bei welchen läuft der Kurs ohne Fundament? 2) Welche Termine liegen in "
       "den nächsten 14 Tagen (Datum, in wie vielen Tagen)? 3) Wie reagierte der Kurs auf die letzten Zahlen? "
       "4) Nachrichten aus der Web-Suche zu höchstens fünf Volltreffern oder Spitzenkandidaten (Übernahmen, Prognosen, "
       "Ereignisse) – immer mit Quelle.",
    4: "Du bist der Chart-Techniker. Beantworte, jeweils mit Ticker und Zahl: 1) Wer steht am nächsten am Pivot "
       "(Abstand in %, Kaufzone bis …) – wo steht ein Angriff unmittelbar bevor? 2) Wer ist schon über die Kaufzone "
       "gelaufen? 3) Ausbrüche der letzten Tage: welche hielten, welche wurden zum Fehlausbruch (Tag als datum)? "
       "4) Short: wo zeigt sich Ermüdung nach Überdehnung? 5) Wie gut ist die Enge der besten Setups "
       "(Kontraktionen, Volumen)?",
    5: "Du bist der Risikomanager. Beantworte, jeweils mit Ticker und Zahl: 1) Depot: Stopps, Abstand, Earnings vor dem "
       "Stopp. Ist kein Depot oder Konto eingetragen, sage das einmal und prüfe stattdessen die Kandidaten am Auslöser: "
       "Stopp 1,5 ATR und Abstand in %. 2) Klumpen: stehen mehrere Volltreffer oder Spitzenkandidaten im selben Sektor, "
       "in derselben Branche oder im selben Thema? 3) Marktlage (Barometer, Markt Minervini und Kullamägi): was heißt das "
       "für long und für short? 4) Welche Kandidaten am Auslöser haben Zahlen vor dem Stopp?",
}

HINWEIS = {"type": "object", "properties": {
    "titel": {"type": "array", "items": {"type": "string"}, "description": "Ticker, jeder einzeln; leer, wenn kein Titel"},
    "datum": {"type": ["string", "null"], "description": "YYYY-MM-DD eines vergangenen Tages im Chart, sonst null"},
    "ampel": {"type": "string", "enum": ["grün", "gelb", "rot"]},
    "text": {"type": "string", "description": "1 bis 2 Sätze mit Zahl"}},
    "required": ["titel", "ampel", "text"]}
MELDUNG = {"type": "object", "properties": {
    "meldung": {"type": "string", "description": "3 bis 6 Sätze Lage aus deiner Sicht, mit Tickern und Zahlen"},
    "hinweise": {"type": "array", "items": HINWEIS, "description": "höchstens 12, die wichtigsten zuerst"}},
    "required": ["meldung", "hinweise"]}
BEFEHL = {"type": "object", "properties": {
    "lage": {"type": "string", "description": "die Lage in drei Sätzen"},
    "volltreffer": {"type": "array", "items": HINWEIS, "description": "dreifacher Rückenwind und Setup am Auslöser"},
    "long": {"type": "array", "items": HINWEIS, "description": "bis 5 Angriffsziele long"},
    "short": {"type": "array", "items": HINWEIS, "description": "bis 3 Ziele short"},
    "gefahren": {"type": "array", "items": HINWEIS, "description": "bis 3 Gefahren"}},
    "required": ["lage", "volltreffer", "long", "short", "gefahren"]}
BEFEHL_TEILE = (("volltreffer", "Volltreffer · dreifacher Rückenwind und Setup am Auslöser"),
                ("long", "Angriffsziele long"), ("short", "Ziele short"), ("gefahren", "Gefahren"))


def dienstanweisung():
    import kartentisch
    import rueckenwind_seite
    reihen = " · ".join(f"{n}: {r}" for _, n, r in kartentisch.REIHEN)
    stufen = " · ".join(f"{k}: {v}" for k, v in rueckenwind_seite.STUFE_TEXT.items() if k)
    return DIENSTANWEISUNG.format(reihen=reihen, stufen=stufen, heute=HEUTE())


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


def _rufen(system, nachrichten, max_tokens, werkzeuge=None, wahl=None):
    """Ein Aufruf an Claude (mit Fortsetzung bei pause_turn); gibt die Inhaltsblöcke zurück. Bricht vor dem Aufruf ab,
    wenn kein Schlüssel da ist oder der Monatsdeckel erreicht ist."""
    k = schluessel()
    if not k:
        raise RuntimeError("kein API-Schlüssel eingetragen (Seite Konferenzraum)")
    if kosten()["usd"] >= DECKEL_USD:
        raise Deckel(f"Monatsdeckel von {DECKEL_USD:.0f} $ erreicht – der Stab ruht bis zum Monatsende")
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
        if antwort.get("stop_reason") != "pause_turn":
            break
        nachrichten = nachrichten[:1] + [{"role": "assistant", "content": antwort["content"]}]
    return bloecke


def _anfrage(system, inhalt, max_tokens=3000, suchen=0):
    """Freier Text als Antwort (Probe, Stab fragen, Notizen der Web-Suche)."""
    werkzeuge = [{"type": "web_search_20250305", "name": "web_search", "max_uses": suchen}] if suchen else None
    bloecke = _rufen(system, [{"role": "user", "content": inhalt}], max_tokens, werkzeuge)
    return "".join(b.get("text", "") for b in bloecke if b.get("type") == "text").strip()


class Unlesbar(Exception):
    def __init__(self, text, roh):
        super().__init__(text)
        self.roh = roh


def _formular(system, inhalt, name, schema, max_tokens=4000):
    """Antwort über ein festes Formular (Werkzeug der Schnittstelle, erzwungen): die Schnittstelle gibt ein fertiges
    Objekt zurück, kein JSON-Text, der an Anführungszeichen zerbrechen kann. Ein zweiter Versuch, sonst Unlesbar mit
    der Rohantwort."""
    werkzeug = [{"name": name, "description": "Meldung an den Stab abgeben", "input_schema": schema}]
    roh = ""
    for _ in range(2):
        bloecke = _rufen(system, [{"role": "user", "content": inhalt}], max_tokens, werkzeug,
                         {"type": "tool", "name": name})
        for b in bloecke:
            if b.get("type") == "tool_use" and isinstance(b.get("input"), dict):
                return b["input"]
        roh = json.dumps(bloecke, ensure_ascii=False)[:600]
    raise Unlesbar("Antwort ohne ausgefülltes Formular", roh)


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
            if e.code in (429, 500, 529) and versuch < 2:     # überlastet oder Rate-Limit: warten und noch einmal
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
    """Kurzer Test nach dem Eintragen des Schlüssels: (True, Text) oder (False, Grund). Kostet weniger als 1 Cent."""
    try:
        antwort = _anfrage("Antworte nur mit OK.", "Verbindungstest", 5)
        return True, f"Verbindung steht – {MODELL} antwortet ({antwort[:20] or 'OK'})"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


# ── Lagebild aus den Daten der App ──

def _zahl(x, n=2):
    try:
        return round(float(x), n)
    except (TypeError, ValueError):
        return None


def _termin_ok(text_oder_datum):
    """Vergangene Termine aussortieren (die alte Liste trug Termine aus 2018/2019 und „in -1 Tagen“)."""
    if not text_oder_datum:
        return None
    s_ = str(text_oder_datum)
    if s_.startswith("in -"):
        return None
    try:
        import pandas as pd
        d = pd.to_datetime(s_[:10], errors="coerce")
        if not pd.isna(d) and d.strftime("%Y-%m-%d") < HEUTE():
            return None
    except Exception:  # noqa: BLE001
        pass
    return s_


def _seite(x):
    """Long oder short aus der Reihe des Setups (10.11.2026) – nicht aus der Weinstein-Phase, die nur Zeichen ist."""
    try:
        import lagekarte
        return lagekarte.richtung(x) or "offen"
    except Exception:  # noqa: BLE001
        return "offen"


class Aufklaerung(Exception):
    """Kartentisch fehlt oder ist veraltet – der Stab tagt nicht (keine Kosten für leere Antworten)."""


def lagebild():
    """Alles, was der Stab liest, als dict – nur aus gespeicherten Daten des Nachtlaufs (kein Abruf)."""
    import atr as atr_modul
    import daten
    import depot
    import kartentisch
    import pandas as pd
    import rueckenwind
    import rueckenwind_seite
    import watchlists
    rw = rueckenwind.laden() or {}
    tisch = kartentisch.laden() or {}
    heute = HEUTE()
    if not tisch or not tisch.get("stand"):
        raise Aufklaerung("Aufklärung fehlt: kein Kartentisch")
    alter = (pd.Timestamp(heute) - pd.Timestamp(tisch["stand"])).days
    if alter > TISCH_MAX_TAGE:
        raise Aufklaerung(f"Aufklärung fehlt: Kartentisch vom {pd.Timestamp(tisch['stand']):%d.%m.%Y} ist {alter} Tage alt")
    namen = {k: n for k, n, _ in kartentisch.REIHEN} | kartentisch.ALTE_REIHEN
    rang = kartentisch.RANG
    titel_t = tisch.get("titel") or {}
    rw_t = rw.get("titel") or {}
    drei = {tk for tk, _ in rueckenwind_seite.dreifach_liste(rw)} if rw else set()
    dep = depot.laden()
    pos = [p["ticker"] for p in dep.get("positionen", [])]
    wl = set(watchlists.alle())
    pool = set(titel_t) | drei | wl
    def ordnung(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        voll = tk in drei and bool(x.get("reihe"))
        return (not voll, -rang.get(x.get("reihe"), 0), not x.get("gruen"), tk not in drei, -(r.get("rang") or 0))
    alle = list(dict.fromkeys(pos + sorted(pool - set(pos), key=ordnung)))[:KANDIDATEN_MAX + len(pos)]

    def akte(tk):
        x, r = titel_t.get(tk) or {}, rw_t.get(tk) or {}
        z = r.get("zahlen") or {}
        kurs = pivot = a = None
        try:
            df = daten.kurse_gespeichert(tk)
            if df is not None and len(df):
                kurs = float(df["Close"].iloc[-1])
                a = atr_modul.wert(df)
        except Exception:  # noqa: BLE001
            pass
        abst = x.get("abstand_vz")                      # mit Vorzeichen; „abstand“ ist nur der Betrag (10.11.2026)
        if kurs and abst is not None:
            pivot = kurs / (1 + float(abst) / 100)
        stopp = pivot - 1.5 * a if pivot and a else None
        kacheln = {}
        for k_, v in (x.get("kacheln") or {}).items():
            amp = v[0] if not isinstance(v[0], list) else {"M": v[0][0], "K": v[0][1] if len(v[0]) > 1 else None}
            wert = v[1] if len(v) > 1 else None
            text = v[2] if len(v) > 2 else None
            if k_ == "Nächste Zahlen" and not _termin_ok(wert):
                wert, text = "unbekannt", None
            kacheln[k_] = {"ampel": amp, "wert": wert, "text": text}
        return {"titel": tk, "depot": tk in pos, "watchlist": tk in wl,
                "reihe": namen.get(x.get("reihe"), x.get("reihe")) if x.get("reihe") else "keine Reihe",
                "dreifacher_rueckenwind": tk in drei, "volltreffer": tk in drei and bool(x.get("reihe")),
                "seite": _seite(x), "setup_minervini": x.get("m"), "setup_kullamaegi": x.get("k"),
                "luecken": x.get("luecken"), "wertzone": x.get("zustand"),
                "kurs": _zahl(kurs), "pivot": _zahl(pivot), "abstand_zum_pivot_pct": _zahl(abst, 1),
                "kaufzone_bis": _zahl(pivot * 1.05) if pivot else None, "atr": _zahl(a),
                "stopp_1_5_atr": _zahl(stopp), "abstand_kurs_stopp_pct": _zahl((kurs / stopp - 1) * 100, 1)
                if kurs and stopp else None,
                "ausbruch": x.get("ausbruch"), "kacheln": kacheln,
                "rueckenwind": {k_: ({"Ermüdend": "Schwächelnd", "Abgehängt": "Zurückfallend"}.get(r.get(k_), r.get(k_))
                                     if k_.endswith("_feld") else r.get(k_))
                                for k_ in ("stufe", "rang", "rang_vor4", "tempo", "beschleunigung",
                                                         "rs_hoch_vor_kurs", "geld_ampel", "sektor", "sektor_feld",
                                                         "branche", "branche_feld", "thema", "thema_feld", "zufluss",
                                                         "jung")} if r else None,
                "zahlen": {"ampel": z.get("ampel"), "punkte": z.get("punkte"), "termin": _termin_ok(z.get("termin")),
                           "reaktion": z.get("reaktion")} if z else None}

    fn = {"Ermüdend": "Schwächelnd", "Abgehängt": "Zurückfallend"}       # Namen wie auf dem Bildschirm
    gruppen = [{k: (fn.get(g.get(k), g.get(k)) if k in ("feld", "feld_vor4") else g.get(k))
                for k in ("art", "name", "anzahl", "feld", "feld_vor4", "seit_wochen", "weg", "zufluss",
                          "rueckschlag", "stabil")} for g in rw.get("gruppen", [])]
    wechsel = [{"titel": tk, **e[-1]} for tk, e in (rw.get("logbuch") or {}).items()
               if e and e[-1].get("seit") and e[-1]["seit"] >= (rw.get("stand") or "")[:10]][:60]
    schnell = {a: list(rueckenwind_seite.schnell(rw, a)[1])[:15] for a in ("Anführer", "Verfolger")} if rw else {}
    vorher = set((letzte() or {}).get("dreifach") or [])
    markt = {}
    try:
        import markt_systeme
        b = tisch.get("barometer") or {}
        markt = {"minervini": markt_systeme.minervini(b.get("hochs"), b.get("tiefs")),
                 "kullamaegi": markt_systeme.kullamaegi()}
    except Exception:  # noqa: BLE001
        pass
    return {"heute": heute, "stand_rueckenwind": rw.get("stand"), "stand_kartentisch": tisch.get("stand"),
            "barometer": tisch.get("barometer"), "markt": markt, "gruppen": gruppen, "stufenwechsel_heute": wechsel,
            "schnellsuche": schnell, "dreifach": sorted(drei), "dreifach_neu": sorted(drei - vorher) if vorher else [],
            "dreifach_weg": sorted(vorher - drei) if vorher else [],
            "kandidaten": [akte(tk) for tk in alle],
            "depot": {"konto": dep.get("konto"), "risiko_pct": dep.get("risiko_pct"),
                      "positionen": dep.get("positionen", []),
                      "hinweis": None if dep.get("konto") else "kein Kontostand eingetragen"}}


def _ausschnitt(lb, nr):
    """Was jeder Stratege liest (spart Token, schärft den Blick)."""
    k = lb["kandidaten"]
    if nr == 2:
        return {x: lb[x] for x in ("heute", "stand_rueckenwind", "gruppen", "stufenwechsel_heute", "schnellsuche",
                                   "dreifach", "dreifach_neu", "dreifach_weg")} | {
            "kandidaten": [{a: c[a] for a in ("titel", "reihe", "dreifacher_rueckenwind", "volltreffer", "rueckenwind")}
                           for c in k]}
    if nr == 3:
        return {"heute": lb["heute"], "kandidaten": [
            {a: c[a] for a in ("titel", "reihe", "volltreffer", "depot", "zahlen")}
            | {"kacheln": {n: c["kacheln"].get(n) for n in ("Fundament", "Nächste Zahlen") if n in c["kacheln"]}}
            for c in k]}
    if nr == 4:
        return {"heute": lb["heute"], "stand_kartentisch": lb["stand_kartentisch"], "kandidaten": [
            {a: c[a] for a in ("titel", "reihe", "seite", "volltreffer", "setup_minervini", "setup_kullamaegi",
                               "luecken", "wertzone", "kurs", "pivot", "abstand_zum_pivot_pct", "kaufzone_bis", "atr",
                               "stopp_1_5_atr", "ausbruch", "kacheln")}
            | {"stufe": (c["rueckenwind"] or {}).get("stufe")} for c in k]}
    return {"heute": lb["heute"], "barometer": lb["barometer"], "markt": lb["markt"], "depot": lb["depot"],
            "kandidaten": [{a: c[a] for a in ("titel", "depot", "reihe", "volltreffer", "kurs", "pivot", "stopp_1_5_atr",
                                              "abstand_kurs_stopp_pct")}
                           | {"markt": c["kacheln"].get("Markt"), "naechste_zahlen": c["kacheln"].get("Nächste Zahlen"),
                              "sektor": (c["rueckenwind"] or {}).get("sektor"),
                              "branche": (c["rueckenwind"] or {}).get("branche"),
                              "thema": (c["rueckenwind"] or {}).get("thema"),
                              "termin": (c["zahlen"] or {}).get("termin")} for c in k]}


# ── Konferenz (Nachtlauf) und Fragen ──

def konferenz(melden=lambda text: None):
    """Alle fünf Strategen; speichert daten/konferenz/<datum>.json und gibt das Ergebnis zurück. `melden` schreibt
    jeden Schritt ins Protokoll (Knopf-Lauf), damit ein Hänger sichtbar wird. Ist der Kartentisch veraltet, tagt der
    Stab nicht (Aufklaerung)."""
    melden(f"{datetime.now():%H:%M:%S} Lagebild wird gelesen …")
    lb = lagebild()
    voll = [c["titel"] for c in lb["kandidaten"] if c["volltreffer"]]
    melden(f"{datetime.now():%H:%M:%S} Lagebild: {len(lb['kandidaten'])} Kandidaten ({len(voll)} Volltreffer), "
           f"{len(lb['dreifach'])} mit dreifachem Rückenwind, {len(lb['gruppen'])} Gruppen")
    heute = lb["heute"]
    system = dienstanweisung()
    erg = {"stand": heute, "zeit": f"{datetime.now():%d.%m.%Y %H:%M}", "modell": MODELL, "meldungen": {},
           "dreifach": lb["dreifach"]}
    for nr in (2, 3, 4, 5):
        name = STRATEGEN[nr][0]
        melden(f"{datetime.now():%H:%M:%S} {name} liest …")
        daten_ = json.dumps(_ausschnitt(lb, nr), ensure_ascii=False, default=str)
        try:
            vorlauf = ""
            if nr == 3:                                  # erst die Web-Suche als Notizen, dann das Formular
                ziele = (voll + [c["titel"] for c in lb["kandidaten"]])[:5]
                vorlauf = _anfrage(system, "Suche aktuelle Nachrichten (Übernahmen, Prognosen, Ereignisse) zu diesen "
                                   f"Titeln: {', '.join(ziele)}. Schreibe knappe Notizen je Titel mit Quelle (URL). "
                                   "Nichts erfinden.", 2000, SUCHEN_NACHT)
                vorlauf = "\n\nNotizen aus der Web-Suche:\n" + (vorlauf or "keine Fundstellen")
            m = _formular(system, f"{AUFTRAG[nr]}\n\nDaten der App (Stand des Nachtlaufs):\n{daten_}{vorlauf}",
                          "melden", MELDUNG)
        except Deckel:
            raise
        except Unlesbar as e:
            m = {"meldung": f"Keine Meldung: {e}", "hinweise": [], "fehler": True, "roh": e.roh}
            melden(f"   Rohantwort: {e.roh}")
        except Exception as e:  # noqa: BLE001 – eine Meldung fehlt, die anderen laufen weiter
            m = {"meldung": f"Keine Meldung: {e}", "hinweise": [], "fehler": True}
        melden(f"{datetime.now():%H:%M:%S} {name}: {'Fehler – ' + m['meldung'] if m.get('fehler') else 'fertig'}")
        erg["meldungen"][str(nr)] = {"name": name, **m}
    inhalt = ("Du bist der Stratege und führst den Stab. Lies die vier Lagemeldungen und schreibe den Tagesbefehl in "
              "fester Gliederung: lage (drei Sätze: Marktlage, wo die Strömung hingeht, was das für heute heißt); "
              "volltreffer (alle Titel mit dreifachem Rückenwind und Setup am Auslöser – die Liste steht in den Daten; je "
              "Titel Setup, Abstand zum Pivot, Stufe); long (bis 5 Angriffsziele); short (bis 3 Ziele); gefahren (bis 3). "
              "Wiederhole nicht einfach eine Meldung, sondern wäge ab und verbinde: Wind, Stellung, Zahlen, Risiko. Jeder "
              "Hinweis mit Ticker und Zahl.\n\n"
              + json.dumps({"heute": heute, "barometer": lb["barometer"], "markt": lb["markt"], "volltreffer": [
                  {a: c[a] for a in ("titel", "reihe", "abstand_zum_pivot_pct", "kaufzone_bis", "stopp_1_5_atr")}
                  | {"stufe": (c["rueckenwind"] or {}).get("stufe")} for c in lb["kandidaten"] if c["volltreffer"]],
                  "meldungen": {nr: {k_: v for k_, v in m.items() if k_ != "roh"}
                                for nr, m in erg["meldungen"].items()}}, ensure_ascii=False, default=str))
    melden(f"{datetime.now():%H:%M:%S} Stratege schreibt den Tagesbefehl …")
    try:
        erg["befehl"] = _formular(system, inhalt, "tagesbefehl", BEFEHL, 3000)
    except Deckel:
        raise
    except Exception as e:  # noqa: BLE001
        erg["befehl"] = {"lage": f"Kein Tagesbefehl: {e}", "volltreffer": [], "long": [], "short": [], "gefahren": []}
    json_schreiben(_pfad(f"{heute}.json"), erg, ensure_ascii=False)
    melden(f"{datetime.now():%H:%M:%S} fertig · Monat {kosten()['usd']:.2f} $")
    return erg


def letzte():
    """Jüngste gespeicherte Konferenz oder None."""
    if not os.path.isdir(SPEICHER):
        return None
    for f in sorted((f for f in os.listdir(SPEICHER) if f[:4].isdigit() and f.endswith(".json")), reverse=True):
        k = json_lesen(os.path.join(SPEICHER, f))
        if k:
            return k
    return None


def _ticker(feld, bekannt):
    """Ticker aus einem Hinweis: Liste (neues Formular) oder Text der alten Konferenzen („COP / PR“,
    „GESUNDHEIT: THC, BTSG, PACS“) – nur Ticker, die die App kennt."""
    import re
    teile = feld if isinstance(feld, list) else re.split(r"[\s,/;:·]+", str(feld or ""))
    return [x for x in (str(t_).upper().strip() for t_ in teile) if x and x != "NULL" and (not bekannt or x in bekannt)]


def hinweise(k):
    """Alle Hinweise einer Konferenz als [(Nr. des Strategen, Hinweis)], Tagesbefehl zuerst (alt und neu)."""
    b = k.get("befehl") or {}
    liste = [(1, h) for h in b.get("hinweise") or []] + [(1, h) for teil, _ in BEFEHL_TEILE for h in b.get(teil) or []]
    return liste + [(int(nr), h) for nr, m in sorted((k.get("meldungen") or {}).items()) for h in m.get("hinweise") or []]


def akten(k):
    """Hinweise je Titel aus einer Konferenz: {Ticker: [(Nr. des Strategen, Hinweis)]} – ein Hinweis zu mehreren
    Titeln steht in der Akte jedes einzelnen."""
    bekannt = set()
    try:
        import kartentisch
        import rueckenwind
        bekannt = set((rueckenwind.laden() or {}).get("titel") or {}) | set((kartentisch.laden() or {}).get("titel") or {})
    except Exception:  # noqa: BLE001
        pass
    aus = {}
    for nr, h in hinweise(k):
        for tk in _ticker(h.get("titel"), bekannt):
            aus.setdefault(tk, []).append((nr, h))
    return aus


def frage(text, tk=None):
    """„Stab fragen“: freie Frage an den Stab, auf Wunsch zu einem Titel. Antwort als Text, gespeichert."""
    try:
        lb = lagebild()
    except Aufklaerung:
        lb = {"barometer": None, "kandidaten": []}
    k = letzte() or {}
    kontext = {"tagesbefehl": k.get("befehl"), "meldungen": {nr: m.get("meldung") for nr, m in
                                                            (k.get("meldungen") or {}).items()},
               "barometer": lb["barometer"]}
    if tk:
        tk = tk.upper().strip()
        kontext["titel"] = next((a for a in lb["kandidaten"] if a["titel"] == tk), None) or _einzelakte(tk)
    inhalt = ("Der Trader fragt den Stab. Antworte als Stab (der Stratege führt, die Fachleute ergänzen) in höchstens "
              "12 Sätzen, auf Deutsch, nur mit Fakten aus den Daten oder aus Web-Fundstellen (dann Quelle nennen). "
              "Antworte als Klartext, ohne Werkzeug.\n\nFrage: " + text + "\n\nDaten der App:\n"
              + json.dumps(kontext, ensure_ascii=False, default=str))
    antwort = _anfrage(dienstanweisung().replace("8. Gib deine Meldung ausschließlich über das Werkzeug ab.", ""),
                       inhalt, 1500, SUCHEN_FRAGE)
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
