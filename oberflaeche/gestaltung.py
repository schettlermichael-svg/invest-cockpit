"""Gestaltung nach der Designvorlage: Farben, Schrift, Grundbausteine als HTML.

Alle sichtbaren Bausteine entstehen hier als HTML/SVG – keine Streamlit-Diagramme.
Werte aus dem Konzept (Abschnitt „Gestaltung: verbindlich wie die Designvorlage“).
"""
from html import escape

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
ORANGE = "#F0883E"
GRAU = "#5A6475"
AMPEL = {"grün": GRUEN, "gelb": GELB, "rot": ROT, "grau": GRAU, "blau": BLAU}
SCHRIFT = "'IBM Plex Sans', system-ui, sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, monospace"

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


def t(text):
    """Text sicher für HTML."""
    return escape(str(text))


def zahl(x, stellen=2):
    """Deutsche Zahl: 1.234,56"""
    s = f"{x:,.{stellen}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def punkt(farbe, groesse=18):
    f = AMPEL.get(farbe, farbe)
    return (f'<span style="display:inline-block;width:{groesse}px;height:{groesse}px;'
            f'border-radius:50%;background:{f};flex-shrink:0"></span>')


def punkt2(m, k, groesse=18):
    """Geteilter Punkt der zwei Systeme: links Minervini, rechts Kullamägi (None = gilt für das System nicht, grau)."""
    fm, fk = AMPEL.get(m or "grau", GRAU), AMPEL.get(k or "grau", GRAU)
    return (f'<span style="display:inline-block;width:{groesse}px;height:{groesse}px;border-radius:50%;flex-shrink:0;'
            f'background:linear-gradient(90deg,{fm} 50%,{fk} 50%);box-shadow:inset 0 0 0 1px #0E1217"></span>')


def seite(inhalt, oben=32, unten=48):
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


STATIONEN = (("lage", "①", "Lage", "Darf ich angreifen?"),
             ("front", "②", "Front", "Wo ist Rückenwind?"),
             ("auswahl", "③", "Auswahl", "Wer führt, wer steht am Auslöser?"),
             ("termine", "④", "Termine", "Was hat sich bewegt, was steht an?"),
             ("truppe", "⑤", "Eigene Truppe", "Wie stehen meine Positionen?"),
             ("anhang", "", "Anhang", "Wie lese ich die Instrumente?"))


def station(anker):
    """Überschrift einer Station der Übersicht (Trichter: breit oben, schmal auf der Titelseite) mit Sprungmarke."""
    _, nr, name, frage = next(x for x in STATIONEN if x[0] == anker)
    return (f'<div id="st-{anker}" style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;'
            f'border-bottom:1px solid {RAND};padding:8px 0 10px;margin-top:8px;scroll-margin-top:60px">'
            f'<h2 style="margin:0;font-size:28px;font-weight:600">{(nr + " " + t(name)).strip()}</h2>'
            f'<span style="font-size:17px;color:{TEXT_2}">{t(frage)}</span></div>')


def sprungleiste():
    """Leiste unter dem Kopf: je Station ein Sprung."""
    return ('<nav aria-label="Stationen" style="display:flex;flex-wrap:wrap;gap:8px">' + "".join(
        f'<a href="#st-{a}" target="_self" style="border:1px solid {RAND};border-radius:8px;padding:6px 12px;'
        f'font-size:15px;color:{TEXT};text-decoration:none;background:{KARTE}">{(nr + " " + t(n)).strip()} '
        f'<span style="color:{TEXT_3}">· {t(f)}</span></a>' for a, nr, n, f in STATIONEN) + '</nav>')


def klapp(titel, zeile_, inhalt):
    """Karte zum Aufklappen: zu sieht man Titel und eine Zeile, aufgeklappt den Inhalt."""
    return (f'<details style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:16px 20px">'
            f'<summary style="cursor:pointer;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap">'
            f'<span style="font-size:20px;font-weight:600">{t(titel)} ▾</span>'
            f'<span style="font-size:15px;color:{TEXT_2}">{t(zeile_)}</span></summary>'
            f'<div style="margin-top:14px">{inhalt}</div></details>')


MITSCHRIFT = None             # dict, solange die Kacheln einer Titelseite gebaut werden


def kachel(beschriftung, ampel, wert, zeile="", hilfe=""):
    """Kachel der Leiste „Lage in fünf Sekunden“: feste Höhe, ein Wert, eine Zeile; die Erklärung als Hinweis
    (Maus darauf, kleines ⓘ)."""
    if MITSCHRIFT is not None:                   # die Lagekarte liest Ampel, Wert und Zeile jeder Kachel mit
        MITSCHRIFT[beschriftung] = (ampel, str(wert), str(zeile))
    titel = f' title="{t(hilfe).replace(chr(10), "&#10;")}"' if hilfe else ""
    zeile = str(zeile).replace(" %", "\u00a0%").replace(" $", "\u00a0$").replace(" Mio.", "\u00a0Mio.")  # Zahl und Einheit nie getrennt
    zeichen = f'<span style="float:right;color:{TEXT_3};text-transform:none">ⓘ</span>' if hilfe else ""
    return (f'<div{titel} style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:14px 16px;'
            f'display:flex;flex-direction:column;gap:6px;height:136px;box-sizing:border-box;overflow:hidden">'
            f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;text-transform:uppercase">{t(beschriftung)}{zeichen}</div>'
            f'<div style="display:flex;align-items:center;gap:10px;min-width:0">{punkt(ampel)}'
            f'<span style="font-size:22px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{t(wert)}</span></div>'
            f'<div style="font-size:14px;color:{TEXT_2};line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;'
            f'-webkit-box-orient:vertical;overflow:hidden">{t(zeile)}</div></div>')


SYSTEM = {"M": "Minervini", "K": "Kullamägi"}


def kachel2(beschriftung, m, k, zeile="", hilfe=""):
    """Kachel der zwei Systeme (05.11.2026): je eine Zeile mit Ampel und Wort für Minervini (M) und Kullamägi (K).
    m, k = (Ampel, Wort) oder None, wenn das System diesen Punkt nicht kennt (grau, „gilt nicht“)."""
    m_, k_ = m or ("grau", "gilt nicht"), k or ("grau", "gilt nicht")
    if MITSCHRIFT is not None:
        MITSCHRIFT[beschriftung] = ((m_[0] if m else None, k_[0] if k else None), f"M {m_[1]} · K {k_[1]}", str(zeile))
    titel = f' title="{t(hilfe).replace(chr(10), "&#10;")}"' if hilfe else ""
    zeile = str(zeile).replace(" %", "\u00a0%").replace(" $", "\u00a0$")
    zeichen = f'<span style="float:right;color:{TEXT_3};text-transform:none">ⓘ</span>' if hilfe else ""

    def reihe(kurz, x, gilt):
        farbe = TEXT if gilt else TEXT_3
        return (f'<div style="display:flex;align-items:center;gap:8px;min-width:0">'
                f'<span style="font-size:12px;color:{TEXT_3};width:12px">{kurz}</span>{punkt(x[0], 14)}'
                f'<span style="font-size:18px;font-weight:600;color:{farbe};white-space:nowrap;overflow:hidden;'
                f'text-overflow:ellipsis">{t(x[1])}</span></div>')
    return (f'<div{titel} style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:12px 16px;'
            f'display:flex;flex-direction:column;gap:4px;height:136px;box-sizing:border-box;overflow:hidden">'
            f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;text-transform:uppercase">{t(beschriftung)}{zeichen}</div>'
            + reihe("M", m_, bool(m)) + reihe("K", k_, bool(k)) +
            f'<div style="font-size:13px;color:{TEXT_2};line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;'
            f'-webkit-box-orient:vertical;overflow:hidden">{t(zeile)}</div></div>')


def ampelzeile(name, ampel, text="", hilfe=""):
    """hilfe: Erklärung als Hinweis am kleinen ⓘ hinter dem Namen (Maus darauf)."""
    unter = f'<span style="font-size:14px;color:{TEXT_2}">{t(text)}</span>' if text else ""
    i_ = (f' <span title="{t(hilfe).replace(chr(10), "&#10;")}" style="color:{TEXT_3};cursor:help;font-weight:400">ⓘ</span>'
          if hilfe else "")
    return (f'<div style="display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-top:1px solid {RAND}">'
            f'<span style="margin-top:3px;display:flex">{punkt(ampel, 14)}</span>'
            f'<div style="display:flex;flex-direction:column;gap:2px">'
            f'<span style="font-size:15px;font-weight:500">{t(name)}{i_}</span>{unter}</div></div>')


SETUPS = ("Flagge", "Powerplay", "Umkehr")      # eigenes Setup (Trendfortsetzung), behält seinen Namen


def basename(muster):
    """Anzeige-Name einer erkannten Base: „Base“ – nur Flagge und Powerplay heißen weiter so (eigenes Setup).
    Die O'Neil/Minervini-Form ist nur noch ein Hinweis (form_hinweis), Pivot einheitlich (siehe erkennung.py)."""
    if not muster:
        return "–"
    if muster[0].startswith("Zone"):
        return muster[0]
    return muster[0] if muster[0] in SETUPS else "Base"


def form_hinweis(muster):
    """Lesart der Form als Hinweistext, z. B. „Form-Hinweis: Cup+Handle (auch: Base auf Base)“."""
    if not muster or muster == ["Base"] or muster[0] in SETUPS and len(muster) == 1:
        return ""
    rest = [m for m in muster if m not in SETUPS and m != "Base"]
    return ("Form-Hinweis: " + " + ".join(rest)) if rest else ""

