"""Der Wächter (Micky 26.11.2026): Knopf „🔔 Alarm“ auf der Titelseite. Der Server schaut während der US-Börse jede
Minute auf die Titel mit Alarm und meldet aufs Handy (ntfy, meldung.py):

  Kreuzen    im Tagesverlauf: der Kurs kreuzt die Front (aufwärts) bzw. die Unterkante (abwärts) – einmal je Tag und
             Linie. Der Auslöser bleibt der Tagesschluss (Messung 26.11.2026: Kauf am Schluss +0,16 R je Ausbruch,
             Sharps Stopp-Kauf beim Kreuzen des Hochs +0,10 R) – die Meldung sagt: jetzt hinschauen.
  Schluss    um 15:45 New York: der Kurs steht über der Front bzw. unter der Unterkante – schließt er dort, ist das
             unser Auslöser (½ antasten).

Linien aus Livermores Frontkarte auf den abgeschlossenen Tageskerzen (livermore.front) – dieselbe Rechnung wie Chart
und Bericht. Gemeldet wird nur ein frisches Kreuzen: lag der letzte Schluss schon jenseits, ist es kein Auslöser mehr.
Kurse: Yahoo 1-Minuten-Kerzen; die Verzögerung (Zeit der letzten Kerze gegen jetzt) wird je Lauf gespeichert.
"""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from tiefe import FREITAG   # Wochentag des Freitags – eine Quelle

HIER = os.path.dirname(os.path.abspath(__file__))
DATEI = os.path.join(HIER, "..", "einstellungen", "alarme.json")       # Titel mit Alarm (persönlich, nicht in Git)
STAND = os.path.join(HIER, "..", "daten", "waechter", "stand.json")    # Linien des Tages, Gemeldetes, Verzögerung
NY = ZoneInfo("America/New_York")
BOERSE = ((9, 30), (16, 0))           # Technik: reguläre Handelszeit New York
MINUTE = 60                           # Technik: Sekunden je Minute


def laden():
    from dateien import json_lesen
    return sorted(set(json_lesen(DATEI, []) or []))


def aktiv(tk):
    return tk.upper() in laden()


def umschalten(tk):
    """Alarm an oder aus → neuer Zustand (True = an)."""
    from dateien import json_schreiben
    alle = set(laden())
    tk = tk.upper()
    an = tk not in alle
    (alle.add if an else alle.discard)(tk)
    os.makedirs(os.path.dirname(DATEI), exist_ok=True)
    json_schreiben(DATEI, sorted(alle))
    return an


def linien(tk):
    """Front und Unterkante aus den abgeschlossenen Tageskerzen → {front, unterkante, schluss, tag} oder None."""
    import daten
    import livermore
    df = daten.kurse(tk)
    df = df.dropna(subset=["High", "Low", "Close"])
    fr = livermore.front(df)
    if not fr:
        return None
    return {"front": (fr["oben"] or {}).get("preis"), "unterkante": (fr["unten"] or {}).get("preis"),
            "schluss": float(df["Close"].iloc[-1]), "tag": f"{df.index[-1]:%Y-%m-%d}"}


def kurse_jetzt(titel):
    """Heutige 1-Minuten-Kerzen von Yahoo → {Titel: {hoch, tief, kurs, zeit}}; zeit = letzte Kerze (New York)."""
    import pandas as pd
    import yfinance as yf
    roh = yf.download(titel, period="1d", interval="1m", progress=False, threads=False, group_by="ticker")
    aus = {}
    for tk in titel:
        try:
            d = roh[tk] if isinstance(roh.columns, pd.MultiIndex) else roh
            d = d.dropna(subset=["Close"])
            if not len(d):
                continue
            zeit = pd.Timestamp(d.index[-1])
            zeit = zeit.tz_convert(NY) if zeit.tzinfo else zeit.tz_localize(NY)
            aus[tk] = {"hoch": float(d["High"].max()), "tief": float(d["Low"].min()), "kurs": float(d["Close"].iloc[-1]),
                       "zeit": zeit}
        except Exception:  # noqa: BLE001 – ein Titel ohne Kurse hält die anderen nicht auf
            continue
    return aus


def _z(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pruefen(schluss=False, jetzt=None):
    """Ein Lauf des Wächters → Liste der gesendeten Meldungen. schluss=True: die Meldung vor Handelsschluss."""
    from dateien import json_lesen, json_schreiben
    import meldung
    jetzt = jetzt or datetime.now(NY)
    titel = laden()
    if not titel or jetzt.weekday() > FREITAG or not (BOERSE[0] <= (jetzt.hour, jetzt.minute) < BOERSE[1]):
        return []
    heute = f"{jetzt:%Y-%m-%d}"
    st = json_lesen(STAND, {}) or {}
    if st.get("heute") != heute:
        st = {"heute": heute, "linien": {}, "gemeldet": []}
    kj = kurse_jetzt(titel)
    gesendet = []
    for tk in titel:
        if tk not in st["linien"]:
            try:
                st["linien"][tk] = linien(tk)
            except Exception:  # noqa: BLE001 – ohne Kurse kein Alarm für diesen Titel
                st["linien"][tk] = None
        li, k = st["linien"][tk], kj.get(tk)
        if not li or not k or f'{k["zeit"]:%Y-%m-%d}' != heute:     # Feiertag: keine Kerze von heute
            continue
        for art, preis, ueber in (("front", li["front"], True), ("unterkante", li["unterkante"], False)):
            if not preis or (li["schluss"] > preis if ueber else li["schluss"] < preis):
                continue                                              # kein frisches Kreuzen mehr
            wort = "Front" if ueber else "Unterkante"
            if schluss:
                schl = f"{tk}:{art}:schluss"
                if (k["kurs"] > preis if ueber else k["kurs"] < preis) and schl not in st["gemeldet"]:
                    text = (f'{tk} steht um 15:45 bei {_z(k["kurs"])} {"über der Front" if ueber else "unter der Unterkante"} '
                            f'{_z(preis)}. Schließt er dort, ist das der Auslöser: ½ antasten {"long" if ueber else "short"}.')
                    meldung.senden(text, f"🔔 {tk} · Schluss {'über der Front' if ueber else 'unter der Unterkante'}",
                                   wichtig=True, seite="Titelseite")
                    st["gemeldet"].append(schl)
                    gesendet.append(text)
                continue
            schl = f"{tk}:{art}"
            if (k["hoch"] >= preis if ueber else k["tief"] <= preis) and schl not in st["gemeldet"]:
                text = (f'{tk} kreuzt die {wort} {_z(preis)} – jetzt {_z(k["kurs"])} ({k["zeit"]:%H:%M} New York). '
                        f'Auslöser bleibt der Tagesschluss {"darüber" if ueber else "darunter"}.')
                meldung.senden(text, f"🔔 {tk} kreuzt die {wort}", wichtig=True, seite="Titelseite")
                st["gemeldet"].append(schl)
                gesendet.append(text)
    verz = [(jetzt - k["zeit"]).total_seconds() / MINUTE for k in kj.values() if f'{k["zeit"]:%Y-%m-%d}' == heute]
    if verz:
        st.setdefault("verzoegerung", []).append([f"{jetzt:%H:%M}", round(min(verz), 1)])
    os.makedirs(os.path.dirname(STAND), exist_ok=True)
    json_schreiben(STAND, st)
    return gesendet


def verzoegerung():
    """Gemessene Verzögerung der Kurse des letzten Wächter-Tags → (Tag, Median in Minuten, Läufe) oder None."""
    from dateien import json_lesen
    st = json_lesen(STAND, {}) or {}
    v = sorted(x[1] for x in st.get("verzoegerung") or [])
    return (st.get("heute"), v[len(v) // 2], len(v)) if v else None
