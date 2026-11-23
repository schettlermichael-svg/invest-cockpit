"""Die Karte des Strategen-Calls (seit 23.11.2026 ohne die Zustandsmaschine nach Auktionsart – die App urteilt mit dem
Zirkel)."""
from html import escape as t

from gestaltung import GELB, GRUEN, KARTE, RAND, ROT, TEXT, TEXT_2, TEXT_3


def _zeilen(titel, texte, farbe=TEXT_3):
    if not texte:
        return ""
    li = "".join(f'<li style="margin:2px 0">{t(x)}</li>' for x in texte)
    return (f'<div style="margin-top:8px"><div style="font-size:12px;color:{farbe};text-transform:uppercase;'
            f'letter-spacing:.04em">{t(titel)}</div><ul style="margin:2px 0 0 18px;padding:0;color:{TEXT_2};'
            f'font-size:13px;line-height:1.45">{li}</ul></div>')


def strategen_karte(erg):
    """Antwort des Strategen-Calls mit Prüfbefund des Codes."""
    if not erg:
        return ""
    a = erg.get("antwort") or {}
    s = a.get("schuss", "kein")
    f = {"long": GRUEN, "short": ROT}.get(s, TEXT_3)
    wort = {"long": "Schuss long", "short": "Schuss short", "kein": "kein Schuss",
            "abwarten": f"Abwarten mit Tendenz {a.get('richtung', '–')}"}.get(s, s)
    mat = erg.get("material") or {}

    def feld(b):
        n = str(b.get("feld", "")).upper()
        q = mat.get(n, "")
        return f'<span title="{t(q)}" style="color:{TEXT_3}">{t(n)}</span> {t(b.get("text", ""))}'

    zeilen = [f'<div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap"><span style="font-size:12px;'
              f'color:{TEXT_3}">Strategen-Call · Kurstag {t(erg.get("stand", ""))}</span><span style="font-size:18px;'
              f'font-weight:600;color:{f}">{t(wort)}</span></div>',
              f'<div style="margin-top:6px;color:{TEXT};font-size:14px">{t(a.get("disbalance", ""))}</div>']
    li = "".join(f'<li>{feld(b)}</li>' for b in a.get("belege") or [])
    if li:
        zeilen.append(f'<ul style="margin:6px 0 0 18px;padding:0;color:{TEXT_2};font-size:13px">{li}</ul>')
    if s != "kein":
        seite_z = "🦬" if s == "long" else "🐻" if s == "short" else "🟡"
        zeilen.append(f'<div style="margin-top:6px;font-size:13px;color:{TEXT_2}">{seite_z} Auslöser: '
                      f'{t(str(a.get("ausloeser_kurs", "")).replace(".", ","))} $ – {t(a.get("ausloeser", ""))}<br>'
                      f'Widerlegt bei: {t(str(a.get("widerlegt_kurs", "")).replace(".", ","))} $ – '
                      f'{t(a.get("widerlegt", ""))}</div>')
    if a.get("gegenzeuge"):
        zeilen.append(f'<div style="margin-top:6px;font-size:13px;color:{TEXT_2}">Gegenzeuge: {feld(a["gegenzeuge"])}</div>')
    for kopf_, schl in (("Unternehmen", "unternehmen"), ("Letztes Quartal", "quartal")):   # Recherche (21.11.2026)
        if a.get(schl):
            zeilen.append(f'<div style="margin-top:8px;font-size:13px;font-weight:600">{kopf_}</div>'
                          + "".join(f'<div style="font-size:13px;color:{TEXT_2}">{t(z)}</div>' for z in a[schl]))
    if a.get("wettbewerber"):
        zeilen.append(f'<div style="margin-top:6px;font-size:13px;color:{TEXT_2}">Wettbewerber: '
                      + ", ".join(f'<a href="?seite=Analyse&t={t(w)}">{t(w)}</a>' for w in a["wettbewerber"]) + "</div>")
    if a.get("fazit"):
        zeilen.append(f'<div style="margin-top:8px;font-size:14px"><b>Fazit:</b> {t(a["fazit"])}</div>')
    if a.get("quellen"):
        zeilen.append(f'<div style="margin-top:6px;font-size:12px;color:{TEXT_3}">Quellen: '
                      + " · ".join(f'<a href="{t(q)}" target="_blank">{t(q[:60])}</a>' for q in a["quellen"]) + "</div>")  # Layout
    p = erg.get("pruefung") or []
    zeilen.append(f'<div style="margin-top:8px;font-size:12px;color:{GRUEN if not p else GELB}">'
                  + ("🟢 Prüfung bestanden: Felder, Zahlen und Seiten stimmen mit dem Material"
                     if not p else "🦊 Prüfung: " + t(" · ".join(p))) + "</div>")
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-left:3px solid {f};border-radius:10px;'
            f'padding:12px 14px;margin:8px 0">{"".join(zeilen)}</div>')


