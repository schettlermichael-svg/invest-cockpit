"""Titelseite: Karte „Rudel und Rotation“ (Breite, Einsamer Wolf, Feld und Tür von Titel, Branche, Sektor und
Themen-Gruppe, Mansfield-RS, Kursverwandte) und die Gruppenregel als eine Zeile in „Lage und Plan“ (Schritt 4).

Rechenkern: kern/rudel.py. Hier nur Anzeige – nichts davon wirkt auf Muster, Kaufsetup oder Phase.
"""
import marktdaten
import rudel
import sektoren
import namen_de
import uebergaenge
from frontkarte import _pfeil
from gestaltung import AMPEL, RAND, TEXT_2, TEXT_3, ampelzeile, karte, punkt, t, zahl

STATUS_TEXT = {"grün": "im Aufwärtstrend, nahe am Hoch", "gelb": "im Aufwärtstrend", "rot": "nicht im Aufwärtstrend",
               "grau": "zu kurze Historie"}


def _status(lage, tk):
    if tk not in lage.index or lage.loc[tk, "historie"] < 200:
        return "grau"
    z = lage.loc[tk]
    return "grün" if z["trend"] and z["nahe_hoch"] else "gelb" if z["trend"] else "rot"


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


def _rot_text(r):
    """„Erstarkend ↗ · an der Tür zu Führend“ – Feld, Bewegung der letzten 5 Wochen und Stand an der Tür."""
    if not r or not r.get("schweif"):
        return "zu kurze Historie"
    x = uebergaenge.tuer(r)
    tuer = (f" · an der Tür zu {x[1]}" if x and x[0] == "Tür" else f" · ↩ Haken zurück nach {x[1]}" if x else "")
    return f'{r["feld"]} {_pfeil(r)}{tuer}'


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


def _v(x):
    return f'{"+" if x >= 0 else "−"}{zahl(abs(x), 1)}'


def _m_text(m):
    """Mansfield immer mit beiden Werten (vor 4 Wochen → heute), damit „von minus zu minus steigend“ eindeutig ist."""
    if not m:
        return "zu kurze Historie"
    return f'{_v(m["wert"] - m["richtung"])} → {_v(m["wert"])} in 4 Wochen'


def _rang_text(d):
    """„Platz 7 von 8, Führer HEI (+0,8)“ – Vorhut oder Nachzügler in der eigenen Themen-Gruppe."""
    v = d.get("vorhut") or []
    namen = [m for m, _ in v]
    if d["tk"] not in namen:
        return "Rang in der Gruppe nicht berechenbar"
    platz = namen.index(d["tk"]) + 1
    if platz == 1:
        return f"Platz 1 von {len(v)}: der Titel führt die Gruppe"
    return f"Platz {platz} von {len(v)}, Führer {v[0][0]} (Mansfield {_v(v[0][1])})"


def karte_rudel(d):
    if not d:
        return karte(f'<div style="color:{TEXT_2}">Der Titel gehört nicht zum Revier – kein Rudel, keine Rotation.</div>',
                     "Rudel und Rotation")
    r = d["rudel"]
    z = ampelzeile(f'Rudel: {r["art"]} {namen_de.branche(r["name"])}', r["ampel"],
                   f'{r["im_trend"]} von {r["anzahl"]} im Aufwärtstrend (über steigendem GD200), '
                   f'{r["nahe_hoch"]} höchstens 15 % unter dem 52-Wochen-Hoch'
                   + (f'; der Titel ist Nr. {r["platz"]} von {r["platz_von"]} nach 3 Monaten' if r.get("platz") else ""))
    if r["einsamer_wolf"]:
        z += ampelzeile("Einsamer Wolf", "gelb", "Der Titel ist stark, sein Rudel nicht: weniger als ein Drittel "
                                                  "der Branche im Aufwärtstrend. O'Neil kauft nie ohne eine zweite starke "
                                                  "Aktie aus derselben Gruppe.")
    z += (f'<div style="font-size:14px;font-weight:600;padding-top:6px">Rotation und relative Stärke</div>'
          f'<div style="font-size:13px;color:{TEXT_3}">Feld und Pfeil wie in der Frontkarte (letzte 5 Wochen), Tür wie '
          f'in der Tafel „Übergänge“; Ampel = Mansfield-RS nach Weinstein.</div>')
    reihen = [("Titel", d["rot_titel"], d["m_titel"]),
              (f'{r["art"]} {namen_de.branche(r["name"])}', d["rot_gruppe"], d["m_gruppe"])]
    if d["etf"]:
        reihen.append((f'Sektor {sektoren.SEKTOREN.get(d["etf"], "")} ({d["etf"]})', d["rot_sektor"], d["m_sektor"]))
    for name, rot, m in reihen:
        z += ampelzeile(name, m["ampel"] if m else "grau", f'{_rot_text(rot)} · Mansfield {_m_text(m)}')
    th = d["thema"]
    if th:
        b = rudel.breite(th["mitglieder"])
        andere = [m for m in th["mitglieder"] if m != d["tk"]][:12]
        z += ampelzeile(f'Themen-Gruppe {th["nr"]}: ' + " · ".join([m for m in th["mitglieder"] if m != d["tk"]][:3])
                        + (f' +{len(th["mitglieder"]) - 4}' if len(th["mitglieder"]) > 4 else ""), d["m_thema"]["ampel"] if d["m_thema"] else "blau",
                        f'{_rot_text(th)} · {_rang_text(d)} · {b["im_trend"]} von {b["anzahl"]} im Aufwärtstrend'
                        + (f' · Mansfield {_m_text(d["m_thema"])}' if d["m_thema"] else "")
                        + f' · {len(th["mitglieder"])} Titel, die eng zusammenlaufen (Gleichlauf {zahl(th["gleichlauf"], 2)}), '
                        + f'Branchen der Mitglieder: {namen_de.branche(th["name"])}: '
                        + ", ".join(andere) + (" …" if len(th["mitglieder"]) > 13 else ""))
    else:
        z += ampelzeile("Thema", "grau", "gehört zu keiner Themen-Gruppe (mindestens 5 eng zusammenlaufende Titel)")
    if d["kv"] is None:
        verwandte = f'<div style="color:{TEXT_2};font-size:14px">Zu kurze Historie für Kursverwandte (mindestens 120 Tage).</div>'
    elif not d["kv"]:
        verwandte = f'<div style="color:{TEXT_2};font-size:14px">Kein Titel läuft auch nur mittel eng mit (Gleichlauf unter 0,35).</div>'
    else:
        verwandte = '<div style="display:flex;flex-wrap:wrap;gap:6px">' + "".join(
            f'<a href="?seite=Titelseite&t={t(k["ticker"])}" target="_self" '
            f'title="{t(k["name"])} · {t(k["branche"])} · {t(STATUS_TEXT[_status(d["lage"], k["ticker"])])}" '
            f'style="display:inline-flex;gap:6px;align-items:center;padding:4px 8px;border:1px solid {RAND};'
            f'border-radius:6px;text-decoration:none;color:inherit;font-size:13px">'
            f'{punkt(_status(d["lage"], k["ticker"]), 10)}<span style="font-family:IBM Plex Mono,monospace">'
            f'{t(k["ticker"])}</span><span style="color:{TEXT_3}">{k["grad"]} {zahl(k["wert"], 2)}</span></a>'
            for k in d["kv"]) + "</div>"
    kopf = (f'<div style="font-size:14px;font-weight:600;padding-top:6px">Kursverwandte</div>'
            f'<div style="font-size:13px;color:{TEXT_3}">Gleichlauf nach Abzug der Marktbewegung, ein Jahr; eng ab 0,50, '
            f'mittel ab 0,35. Punkt = Lage, Maus = Name und Branche, Klick öffnet die Titelseite.</div>')
    return karte(z + kopf + verwandte, "Rudel und Rotation")


def gruppenregel(d, mr, ph, seite="long"):
    """Gruppenregel nach Weinstein als eine Zeile für Long oder Short: Markt (O'Neil), Gruppe und Titel (Weinstein).
    Gruppe = die Themen-Gruppe (die Titel, die mit ihm laufen), sonst die Branche; die Branche steht als Zusatz dabei.
    ✓ erfüllt, ✗ nicht erfüllt, ⚠ zur Hälfte erfüllt mit ausgeschriebener Warnung. Zeichen, kein Filter."""
    long = seite == "long"
    zeilen, warnungen = [], []
    if mr:
        gut, schlecht = ("grün", "rot") if long else ("rot", "grün")
        a = "grün" if mr["ampel"] == gut else "rot" if mr["ampel"] == schlecht else "gelb"
        zeilen.append(("Markt", a, mr["zustand"]))
        if a == "gelb":
            warnungen.append(f"Markt {mr['zustand']}")

    def gruppe(name, unter, m):
        lage_ok = (not unter) if long else unter
        rs_ok = bool(m and m["ampel"] == ("grün" if long else "rot"))
        a = "grün" if lage_ok and rs_ok else "gelb" if lage_ok or rs_ok else "rot"
        text = (f'{"unter" if unter else "über"} ihrem GD30W {"✓" if lage_ok else "✗"}, Mansfield {_m_text(m)} '
                f'{"✓" if rs_ok else "✗"}')
        if a == "gelb" and m:
            dreht = m["richtung"] > 0
            warn = ("holt auf – Gegenwind für den Short" if not long and dreht else
                    "lässt nach – Gegenwind für den Long" if long and not dreht else "nur zur Hälfte erfüllt")
            warnungen.append(f"{name}: {warn}")
        return a, text
    if d:
        th = d.get("thema")
        if th and d.get("m_thema"):
            kopf = " · ".join([x for x in th["mitglieder"] if x != d["tk"]][:3])
            a, x = gruppe("Themen-Gruppe", d.get("thema_unter_gd30w"), d["m_thema"])
            zeilen.append((f"Themen-Gruppe ({kopf} …)", a, x))
        else:
            r = d["rudel"]
            a, x = gruppe(f'Branche {namen_de.branche(r["name"])}', d["gruppe_unter_gd30w"], d["m_gruppe"])
            zeilen.append((f'Branche {namen_de.branche(r["name"])}', a, x))
    ziel = 2 if long else 4
    a = "grün" if ph == ziel else "gelb" if ph in ((1, 3) if long else (3,)) else "rot"
    zeilen.append(("Titel", a, f"Phase {ph}" if ph else "Phase unbekannt"))
    zeichen = {"grün": "✓", "gelb": "⚠", "rot": "✗"}
    handel = "Long" if long else "Short"
    erfuellt = sum(1 for _, a, _ in zeilen if a == "grün")
    teile = " · ".join(f'<span style="color:{AMPEL[a]};font-weight:600">{zeichen[a]}</span> {t(n)} '
                       f'<span style="color:{TEXT_2}">({t(x)})</span>' for n, a, x in zeilen)
    zusatz = ""
    if d and d.get("thema") and d.get("m_thema"):
        r = d["rudel"]
        zusatz = (f'<div style="font-size:13px;color:{TEXT_2}">Zusatz Branche {t(namen_de.branche(r["name"]))} '
                  f'({r["anzahl"]} Titel): {"unter" if d["gruppe_unter_gd30w"] else "über"} ihrem GD30W, '
                  f'Mansfield {t(_m_text(d["m_gruppe"]))}</div>')
    warn = (f'<div style="font-size:14px;color:#E3B341">⚠ {t("; ".join(warnungen))}</div>' if warnungen else "")
    return (f'<div style="font-size:15px;line-height:1.7;padding-top:6px"><b>Rückenwind für einen {handel}</b> '
            f'({erfuellt} von {len(zeilen)} erfüllt): {teile}</div>{warn}{zusatz}')


