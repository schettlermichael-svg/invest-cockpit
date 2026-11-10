"""Seite Konferenzraum (09.11.2026): Tagesbefehl des Strategen, die vier Lagemeldungen, Akten je Titel mit Nadeln im
Chart, „Stab fragen“ und Kostenbuch. Rechnet nicht – liest die Konferenz des Nachtlaufs (kern/stab.py)."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

import stab  # noqa: E402
from gestaltung import BLAU, GELB, GRUEN, KARTE, RAND, ROT, TEXT, TEXT_2, TEXT_3, seite, t  # noqa: E402

FARBE = {"grün": GRUEN, "gelb": GELB, "rot": ROT}
PUNKT = {"grün": "🟢", "gelb": "🟡", "rot": "🔴"}


def _h(text):
    return t(str(text or "")).replace("<", "&lt;")


def kopf(k):
    ko = stab.kosten()
    stand = f'Konferenz vom {k["zeit"]}' if k else "noch keine Konferenz"
    return seite(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
        f'<h1 style="margin:0;font-size:30px;color:{TEXT}">Konferenzraum · MARAGA Investment</h1>'
        f'<div style="color:{TEXT_2};font-size:14px">{stand} · Kosten {ko["usd"]:.2f} $ von {stab.DECKEL_USD:.0f} $ im Monat'
        f' · {ko["aufrufe"]} Aufrufe · {ko["suchen"]} Web-Suchen</div></div>'
        f'<p style="color:{TEXT_2};font-size:15px;margin:8px 0 0">Fünf Strategen lesen nach dem Nachtlauf die Daten der App '
        f'und erklären die Lage. Sie zeigen auf, sie filtern nichts und entscheiden nichts – jede Zahl stammt aus der App '
        f'oder einer genannten Quelle.</p>', oben=12, unten=8)


def _hinweis(nr, h, mit_titel=True):
    f = FARBE.get(h.get("ampel"), TEXT_2)
    tks = stab._ticker(h.get("titel"), None)
    titel_ = (" · ".join(f'<a href="?seite=Titelseite&t={tk}" target="_self" style="color:{BLAU};font-weight:600;'
                         f'text-decoration:none">{tk}</a>' for tk in tks) + " · " if mit_titel and tks else "")
    tag = f'<span style="color:{TEXT_3}">{h["datum"][8:10]}.{h["datum"][5:7]}. · </span>' if h.get("datum") else ""
    nadel = (f'<span style="display:inline-flex;width:20px;height:20px;border-radius:50%;border:2px solid {f};color:{f};'
             f'font-size:12px;font-weight:700;align-items:center;justify-content:center;margin-right:8px;flex:none">'
             f'{nr}</span>' if nr else f'<span style="margin-right:8px">{PUNKT.get(h.get("ampel"), "⚪")}</span>')
    return (f'<div style="display:flex;align-items:flex-start;font-size:15px;line-height:1.5;margin:6px 0">{nadel}'
            f'<div>{titel_}{tag}{_h(h.get("text"))}</div></div>')


def befehl(k):
    """Tagesbefehl in fester Gliederung (seit 10.11.2026): Lage, Volltreffer, long, short, Gefahren; ältere
    Konferenzen mit drei freien Hinweisen werden weiter gezeigt."""
    b = (k or {}).get("befehl") or {}
    teile = "".join(_hinweis(None, h) for h in b.get("hinweise") or [])
    for teil, titel_ in stab.BEFEHL_TEILE:
        liste = b.get(teil) or []
        if teil in b:
            teile += (f'<div style="font-size:14px;font-weight:600;color:{TEXT_2};margin:14px 0 2px">{titel_}'
                      f'<span style="color:{TEXT_3};font-weight:400"> · {len(liste)}</span></div>'
                      + ("".join(_hinweis(None, h) for h in liste)
                         or f'<div style="font-size:14px;color:{TEXT_3}">keine</div>'))
    return seite(
        f'<div style="background:{KARTE};border:2px solid {BLAU};border-radius:14px;padding:18px 20px">'
        f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;text-transform:uppercase">1 · Stratege · '
        f'Tagesbefehl</div><p style="font-size:17px;line-height:1.6;margin:8px 0 10px;color:{TEXT}">{_h(b.get("lage"))}</p>'
        + teile + "</div>", oben=8, unten=8)


def meldung(nr, m):
    name, frage = stab.STRATEGEN[nr]
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 18px;margin-bottom:12px">'
            f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;text-transform:uppercase">{nr} · {name}'
            f'</div><div style="font-size:14px;color:{TEXT_2};margin:2px 0 8px">{frage}</div>'
            f'<p style="font-size:15px;line-height:1.6;margin:0 0 8px;color:{TEXT}">{_h(m.get("meldung"))}</p>'
            + "".join(_hinweis(None, h) for h in (m.get("hinweise") or [])) + "</div>")


def akte_text(eintraege):
    """Die Hinweise eines Titels, nummeriert nach Stratege (wie die Nadeln im Chart)."""
    return seite("".join(_hinweis(nr, h, mit_titel=False) for nr, h in eintraege), oben=4, unten=4)


def nadeln(eintraege, bis=None):
    """Nadeln für den Chart – nur Hinweise mit einem Tag, der im Chart liegt (bis = Stand der Konferenz). Hinweise auf
    künftige Tage (Termine) stehen nur im Text: früher landeten sie auf der letzten Kerze und sahen aus wie heute."""
    return [{"datum": h.get("datum"), "nr": nr, "ampel": h.get("ampel"),
             "text": f'{stab.STRATEGEN[nr][0]}: {h.get("text", "")}'} for nr, h in eintraege
            if h.get("datum") and (not bis or str(h["datum"])[:10] <= bis)]


ANLEITUNG = """**So legst du den API-Schlüssel an (einmalig, etwa 5 Minuten):**

1. Öffne **console.anthropic.com** und melde dich an (oder lege dort ein Konto an).
2. Unter **Billing** Guthaben aufladen – für den Anfang reichen 20 $.
3. Unter **Limits** ein Monatslimit setzen, z. B. 20 $ (zweite Sicherung neben dem Deckel der App).
4. Unter **API Keys** → **Create Key**, Name z. B. „Invest Cockpit“. Den Schlüssel (beginnt mit `sk-ant-`) kopieren –
   er wird nur einmal angezeigt.
5. Hier unten einfügen und speichern. Er liegt dann nur auf dem Server (nicht in GitHub)."""
