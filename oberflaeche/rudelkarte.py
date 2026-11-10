"""Titelseite: Daten zu Rudel und Rotation eines Titels (Branche, Sektor, Themen-Gruppe, Mansfield-RS) – genutzt für
das Warnzeichen „Gruppe in Korrektur“. Die frühere Karte „Rudel und Rotation“ und die Gruppenregel nach Weinstein
wurden nicht mehr gezeigt und liegen seit der Gesamtprüfung am 10.11.2026 in _to_delete.

Rechenkern: kern/rudel.py. Hier nur Anzeige – nichts davon wirkt auf Muster, Kaufsetup oder Phase.
"""
import marktdaten
import rudel
import sektoren


def _rot(kurs, markt):
    """Stärke, Schwung, Feld und Schweif im Rotationsbild (wie die Frontkarte) für eine beliebige Kursreihe."""
    try:
        r = sektoren.reihen(kurs, markt)
        if len(r) < sektoren.SCHWEIF:
            return None
        s = r.iloc[-sektoren.SCHWEIF:]
        d = {"staerke": float(s["staerke"].iloc[-1]), "schwung": float(s["schwung"].iloc[-1]),
             "schweif": [(float(a), float(b)) for a, b in s[["staerke", "schwung"]].to_numpy()]}
        d["feld"] = sektoren.feld(d["staerke"], d["schwung"])
        return d
    except Exception:
        return None




def _unter_gd30w(kurs):
    return bool(kurs.iloc[-1] < kurs.rolling(150, min_periods=150).mean().iloc[-1]) if len(kurs) >= 150 else None


def _vorhut(mitglieder):
    """Rang der Mitglieder einer Themen-Gruppe nach Mansfield-RS (Massive-Kurse gegen SPY), stärkster zuerst."""
    C = rudel.kurse()
    werte = []
    for m in mitglieder:
        if m in C.columns:
            x = rudel.mansfield(C[m].dropna(), C[rudel.MARKT])
            if x:
                werte.append((m, x["wert"]))
    return sorted(werte, key=lambda v: -v[1])


def daten(tk, df, etf):
    """Alles für Kachel und Karte; None, wenn der Titel nicht im Revier ist oder Daten fehlen."""
    try:
        r = rudel.rudel(tk)
        if r is None:
            return None
        spy = marktdaten.yahoo("SPY")
        gruppe = rudel.gruppenkurs(r["mitglieder"])
        th = rudel.thema_von(tk)
        d = {"tk": tk, "rudel": r, "kv": rudel.kursverwandte(tk), "thema": th, "lage": rudel._laden()["lage"],
             "m_titel": rudel.mansfield(df["Close"], spy), "m_gruppe": rudel.mansfield(gruppe, rudel.kurse()[rudel.MARKT]),
             "m_sektor": rudel.mansfield(marktdaten.yahoo(etf), spy) if etf else None,
             "m_thema": rudel.gruppen_mansfield(th["mitglieder"]) if th else None,
             "rot_titel": _rot(df["Close"], spy), "rot_gruppe": _rot(gruppe, rudel.kurse()[rudel.MARKT]),
             "rot_sektor": sektoren.rotation().get(etf) if etf else None,
             "vorhut": _vorhut(th["mitglieder"]) if th else None,
             "thema_unter_gd30w": _unter_gd30w(rudel.gruppenkurs(th["mitglieder"])) if th else None,
             "gruppe_unter_gd30w": _unter_gd30w(gruppe), "etf": etf, "kurs_gruppe": gruppe}
        return d
    except Exception:
        return None








