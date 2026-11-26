"""Gestaltung nach der Designvorlage: Farben, Schrift, Grundbausteine als HTML.

Alle sichtbaren Bausteine entstehen hier als HTML/SVG – keine Streamlit-Diagramme.
Werte aus dem Konzept (Abschnitt „Gestaltung: verbindlich wie die Designvorlage“).
"""
from html import escape
from masse import ZEILENUMBRUCH  # noqa: E402

SEITE = "#0E1217"
KARTE = "#161C24"
RAND = "#263040"
TEXT = "#E6EAF0"
TEXT_2 = "#A9B4C4"
TEXT_3 = "#8B97A8"
GRUEN = "#3FB950"
GELB = "#D29922"
ROT = "#F85149"
BLAU = "#7DB4FF"
LILA = "#D2A8FF"
GRAU = "#5A6475"
AMPEL = {"grün": GRUEN, "gelb": GELB, "rot": ROT, "grau": GRAU, "blau": BLAU}
SCHRIFT = "'IBM Plex Sans', system-ui, sans-serif"

KOPF = (
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600"
    "&family=IBM+Plex+Mono:wght@400;500&display=swap');"
    f".ic a{{color:{BLAU}}}.ic a:hover{{color:#A9CDFF}}"
    ".ic .hinweis-tip{display:none;position:absolute;right:0;bottom:calc(100% + 6px);z-index:5;width:min(560px,90%);"
    f"background:#1C2430;border:1px solid #2F3B4E;border-radius:10px;padding:12px 14px;font-size:13px;"
    f"line-height:1.6;color:{TEXT_2};box-shadow:0 8px 24px rgba(0,0,0,.45)}}"
    ".ic .hinweis-zone:hover .hinweis-tip{display:block}"
    "</style>"
)


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────
PUNKT = 18          # Ampelpunkt: Größe in Pixeln
PUNKT_KLEIN = 14    # Ampelpunkt in einer Ampelzeile
SEITE_OBEN = 32           # Seitenrand oben
SEITE_UNTEN = 48          # Seitenrand unten


def t(text):
    """Text sicher für HTML."""
    return escape(str(text))


def zahl(x, stellen=2):
    """Deutsche Zahl: 1.234,56"""
    s = f"{x:,.{stellen}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def punkt(farbe, groesse=PUNKT):
    f = AMPEL.get(farbe, farbe)
    return (f'<span style="display:inline-block;width:{groesse}px;height:{groesse}px;'
            f'border-radius:50%;background:{f};flex-shrink:0"></span>')


def seite(inhalt, oben=SEITE_OBEN, unten=SEITE_UNTEN):
    """Äußerer Rahmen: Seitenhintergrund, Schrift, maximale Breite 1392 px. oben/unten: Innenabstand (die Titelseite
    besteht aus drei Blöcken mit den Chart-Knöpfen von Streamlit dazwischen)."""
    return (f'{KOPF}<div class="ic" style="background:{SEITE};color:{TEXT};font-family:{SCHRIFT};'
            f'box-sizing:border-box;padding:{oben}px 24px {unten}px">'
            f'<div style="max-width:1392px;margin:0 auto;display:flex;flex-direction:column;gap:24px">'
            f'{inhalt}</div></div>')


def karte(inhalt, titel=None, rand=RAND):
    kopf = (f'<h2 style="margin:0;font-size:20px;font-weight:600">{t(titel)}</h2>' if titel else "")
    return (f'<section style="background:{KARTE};border:1px solid {rand};border-radius:12px;'
            f'padding:20px;display:flex;flex-direction:column;gap:14px">{kopf}{inhalt}</section>')


# Namen der vier Felder auf dem Bildschirm (10.11.2026, Micky): intern bleiben die Schlüssel „Ermüdend“ und „Abgehängt“,
# gezeigt wird überall „Schwächelnd“ und „Zurückfallend“ – „Ermüd…“ gehörte der Stufe „Ermüdet“ (bis 22.11.2026)
# und dem Short-Setup „Ermüdung nach Überdehnung“.
FELD_NAME = {"Führend": "Führend", "Erstarkend": "Erstarkend", "Ermüdend": "Schwächelnd", "Abgehängt": "Zurückfallend"}


def feld_name(f):
    return FELD_NAME.get(f, f) if f else f


STATIONEN = (("lage", "①", "Lage", "Darf ich angreifen?"),          # Seite Rückenwind = Lagezentrum (12.11.2026)
             ("wind", "②", "Rückenwind", "Wohin fließt das Geld, welche Titel haben ihn im Rücken?"))


def station(anker):
    """Überschrift einer Station der Übersicht (Trichter: breit oben, schmal auf der Titelseite) mit Sprungmarke."""
    _, nr, name, frage = next(x for x in STATIONEN if x[0] == anker)
    return (f'<div id="st-{anker}" style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;'
            f'border-bottom:1px solid {RAND};padding:8px 0 10px;margin-top:8px;scroll-margin-top:60px">'
            f'<h2 style="margin:0;font-size:28px;font-weight:600">{(nr + " " + t(name)).strip()}</h2>'
            f'<span style="font-size:17px;color:{TEXT_2}">{t(frage)}</span></div>')


def sprungleiste(stationen=STATIONEN):
    """Leiste unter dem Kopf: je Station ein Sprung."""
    return ('<nav aria-label="Stationen" style="display:flex;flex-wrap:wrap;gap:8px">' + "".join(
        f'<a href="#st-{a}" target="_self" style="border:1px solid {RAND};border-radius:8px;padding:6px 12px;'
        f'font-size:15px;color:{TEXT};text-decoration:none;background:{KARTE}">{(nr + " " + t(n)).strip()} '
        f'<span style="color:{TEXT_3}">· {t(f)}</span></a>' for a, nr, n, f in stationen) + '</nav>')


def klapp(titel, zeile_, inhalt):
    """Karte zum Aufklappen: zu sieht man Titel und eine Zeile, aufgeklappt den Inhalt."""
    return (f'<details style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 20px">'
            f'<summary style="cursor:pointer;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap">'
            f'<span style="font-size:20px;font-weight:600">{t(titel)} ▾</span>'
            f'<span style="font-size:15px;color:{TEXT_2}">{t(zeile_)}</span></summary>'
            f'<div style="margin-top:14px">{inhalt}</div></details>')






TERMIN_ROT, TERMIN_GELB = 7, 14     # Zahlen nah: eine Regel für die ganze App (Prüf-Agent 12.11.2026: vorher 7/10/14)


def termin_ampel(tage):
    """Ampel der nächsten Zahlen: höchstens 7 Tage rot, 8–14 Tage gelb, später grün, unbekannt grau."""
    if tage is None or tage < 0:
        return "grau"
    return "rot" if tage <= TERMIN_ROT else "gelb" if tage <= TERMIN_GELB else "grün"




def ampelzeile(name, ampel, text="", hilfe=""):
    """hilfe: Erklärung als Hinweis am kleinen ⓘ hinter dem Namen (Maus darauf)."""
    unter = f'<span style="font-size:14px;color:{TEXT_2}">{t(text)}</span>' if text else ""
    i_ = (f' <span title="{t(hilfe).replace(chr(ZEILENUMBRUCH), "&#10;")}" style="color:{TEXT_3};cursor:help;font-weight:400">ⓘ</span>'
          if hilfe else "")
    return (f'<div style="display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-top:1px solid {RAND}">'
            f'<span style="margin-top:3px;display:flex">{punkt(ampel, PUNKT_KLEIN)}</span>'
            f'<div style="display:flex;flex-direction:column;gap:2px">'
            f'<span style="font-size:15px;font-weight:500">{t(name)}{i_}</span>{unter}</div></div>')






# Zeichenliste (Micky 21.11.2026, aus der Titel-Analyse, gilt im ganzen Cockpit): jede Aussagezeile beginnt mit genau
# einem Zeichen, immer in derselben Bedeutung; Bildzeichen sparsam, sonst die Ampel.
ZEICHEN_LISTE = (("🦬", "Käufer haben die Kontrolle (long)"), ("🐻", "Verkäufer haben die Kontrolle (short)"),
                 ("🦈", "früher Vorteil – ein Signal, das die Masse noch nicht sieht"),
                 ("🔥", "Beschleunigung (Gewinn, Umsatz, Volumen ab 1,5-fach)"), ("🦊", "Falle"),
                 ("🌞", "Rückenwind, Geldzufluss"), ("❄️", "Gegenwind, Geldabfluss"), ("🪝", "Widerstand oder Unterstützung"),
                 ("🟢", "Stärke"), ("🟡", "gemischt"), ("🔴", "Schwäche"), ("⚪", "ungemessen"),
                 ("⚡", "Zeit und Volumen widersprechen sich"),
                 ("🐺", "Einzelkämpfer – stark, aber die Branche liegt hinten"),
                 ("🏜️", "Volumen trocknet aus – kaum noch Verkäufer (Minervini)"),
                 ("✈️", "freie Bahn – keine Stellung über dem Kurs (↓ darunter), Livermores Linie des geringsten Widerstands"))
ZEICHEN = tuple(z for z, _ in ZEICHEN_LISTE)


def zeilen(liste, leer="⚪ ungemessen"):
    """Aussagezeilen [(Zeichen, Text)] als HTML – ein Zeichen je Zeile (ZEICHEN_LISTE)."""
    if not liste:
        liste = [(leer[0], leer[2:])]
    return "".join(f'<div style="display:flex;gap:10px;padding:6px 0;border-top:1px solid {RAND};font-size:15px;'
                   f'line-height:1.45"><span style="flex:0 0 22px">{z}</span><span>{t(x)}</span></div>' for z, x in liste)


def zeichen_legende():
    """Die Zeichenliste als eine Zeile zum Aufklappen."""
    return (f'<details><summary style="cursor:pointer;color:{TEXT_2};font-size:14px">Zeichen</summary>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:8px;font-size:14px;color:{TEXT_2}">'
            + "".join(f'<span>{z} {t(b)}</span>' for z, b in ZEICHEN_LISTE) + '</div></details>')
