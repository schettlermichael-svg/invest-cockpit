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

