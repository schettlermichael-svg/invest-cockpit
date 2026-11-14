"""Anzeige des Zustands im Code für Balance und Ungleichgewicht (13.11.2026) – dieselbe Kette auf allen drei Ebenen:
Anlass → Balance → Test am Rand → abgelehnt | angenommen → Ungleichgewicht → Ende des Laufs. Zuerst der Zustand, die
alten Wörter als Unterzeile, darunter die Belege an ihrem Platz in der Kette."""
from html import escape as t

import auktion
from gestaltung import KARTE, RAND, TEXT, TEXT_2, TEXT_3

KETTE = ("Anlass", "Balance", "Test am Rand", "abgelehnt", "angenommen", "Ungleichgewicht", "Ende des Laufs")
PLATZ_REIHE = ("Anlass", "Balance", "Test am Rand", "abgelehnt", "angenommen", "Ungleichgewicht", "Abgabe am Rand",
               "Anführer bricht aus", "folgen die Schwestern", "Geldfluss", "Ende des Laufs")


def pille(e, klein=False, mit_belegen=False):
    """Farbiges Wort, z. B. für Tabellen: „Ungleichgewicht ↑“; mit_belegen: die Belege beim Darüberfahren."""
    if not e:
        return ""
    f = auktion.farbe(e)
    gr = "12px" if klein else "13px"
    titel = ""
    if mit_belegen:
        z = [f"{p}: {x}" for p, x in e.get("belege") or []] + list(e.get("ende") or [])
        titel = f' title="{t(chr(10).join(z))}"'
    return (f'<span{titel} style="display:inline-block;border:1px solid {f};color:{f};border-radius:999px;padding:1px 9px;'
            f'font-size:{gr};white-space:nowrap">{t(auktion.wort(e))}</span>')


def _kette(e):
    jetzt = e["zustand"]
    teile = []
    for i, s in enumerate(KETTE):
        an = s == jetzt or (s == "Anlass" and e.get("anlass"))
        f = auktion.FARBE[s]
        stil = (f"background:{f}22;border:1px solid {f};color:{TEXT};font-weight:600" if s == jetzt else
                f"border:1px solid {f};color:{TEXT_2}" if an else f"border:1px solid {RAND};color:{TEXT_3}")
        teile.append(f'<span style="{stil};border-radius:6px;padding:3px 8px;font-size:12px;white-space:nowrap">'
                     f'{t(s)}</span>')
        if i < len(KETTE) - 1:
            teile.append(f'<span style="color:{TEXT_3};font-size:12px">{"|" if s == "abgelehnt" else "→"}</span>')
    return f'<div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center">{"".join(teile)}</div>'


def _zeilen(titel, texte, farbe=TEXT_3):
    if not texte:
        return ""
    li = "".join(f'<li style="margin:2px 0">{t(x)}</li>' for x in texte)
    return (f'<div style="margin-top:8px"><div style="font-size:12px;color:{farbe};text-transform:uppercase;'
            f'letter-spacing:.04em">{t(titel)}</div><ul style="margin:2px 0 0 18px;padding:0;color:{TEXT_2};'
            f'font-size:13px;line-height:1.45">{li}</ul></div>')


def box(e, ueberschrift="Zustand"):
    """Karte mit Zustand, Unterzeile, Kette und Belegen je Platz."""
    if not e:
        return ""
    f = auktion.farbe(e)
    kopf = (f'<div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap">'
            f'<span style="font-size:12px;color:{TEXT_3}">{t(ueberschrift)}</span>'
            f'<span style="font-size:20px;font-weight:600;color:{f}">{t(auktion.wort(e))}</span>'
            f'<span style="font-size:13px;color:{TEXT_3}">{t(e.get("unterzeile") or "")}</span></div>')
    teile = [kopf, f'<div style="margin-top:8px">{_kette(e)}</div>']
    teile.append(_zeilen("Anlass", e.get("anlass"), auktion.FARBE["Anlass"]))
    je = {}
    for platz, text in e.get("belege") or []:
        je.setdefault(platz, []).append(text)
    for platz in PLATZ_REIHE:
        if platz in je:
            teile.append(_zeilen(platz, je.pop(platz), auktion.FARBE.get(platz, TEXT_3)))
    for platz, texte in je.items():
        teile.append(_zeilen(platz, texte))
    teile.append(_zeilen("Was den Lauf beendet", e.get("ende"), auktion.FARBE["Ende des Laufs"]))
    teile.append(_zeilen("Wo die Gegenseite wartet", e.get("gegenseite")))
    if e.get("kraft"):
        teile.append(_zeilen("Eigen oder geliehen", [e["kraft"]["text"]]))
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-left:3px solid {f};border-radius:10px;'
            f'padding:12px 14px;margin:8px 0">{"".join(teile)}</div>')


def strategen_karte(erg):
    """Antwort des Strategen-Calls mit Prüfbefund des Codes."""
    if not erg:
        return ""
    a = erg.get("antwort") or {}
    s = a.get("schuss", "kein")
    f = {"long": auktion.FARBE["angenommen"], "short": auktion.FARBE["angenommen"]}.get(s, TEXT_3)
    wort = {"long": "Schuss long", "short": "Schuss short", "kein": "kein Schuss"}.get(s, s)
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
        zeilen.append(f'<div style="margin-top:6px;font-size:13px;color:{TEXT_2}">Auslöser: '
                      f'{t(str(a.get("ausloeser_kurs", "")).replace(".", ","))} $ – {t(a.get("ausloeser", ""))}<br>'
                      f'Widerlegt bei: {t(str(a.get("widerlegt_kurs", "")).replace(".", ","))} $ – '
                      f'{t(a.get("widerlegt", ""))}</div>')
    if a.get("gegenzeuge"):
        zeilen.append(f'<div style="margin-top:6px;font-size:13px;color:{TEXT_2}">Gegenzeuge: {feld(a["gegenzeuge"])}</div>')
    p = erg.get("pruefung") or []
    zeilen.append(f'<div style="margin-top:8px;font-size:12px;color:{auktion.FARBE["Ende des Laufs"] if not p else "#D29922"}">'
                  + ("✓ Prüfung bestanden: Felder, Zahlen und Seiten stimmen mit dem Material"
                     if not p else "⚠ Prüfung: " + t(" · ".join(p))) + "</div>")
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-left:3px solid {f};border-radius:10px;'
            f'padding:12px 14px;margin:8px 0">{"".join(zeilen)}</div>')


def kopfzeile(e):
    """Eine Zeile unter dem Kopf der Titelseite: der Zustand zuerst, die alten Wörter dahinter."""
    if not e:
        return ""
    return (f'<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0 2px">'
            f'<span style="font-size:12px;color:{TEXT_3}">Zustand</span>{pille(e)}'
            f'<span style="font-size:13px;color:{TEXT_3}">{t(e.get("unterzeile") or "")}</span></div>')


def pruef_karte(r):
    """Urteil des Chart-Prüfers für einen Titel (Knopf auf der Titelseite)."""
    if not r:
        return ""
    if r.get("fehler"):
        return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:10px;padding:12px 14px;'
                f'margin:8px 0;color:{TEXT_2}">Chart-Prüfer: {t(r["fehler"])}</div>')
    w = r.get("widersprueche") or []
    f = "#3FB950" if not w else "#D29922"
    kopf = (f'<div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap"><span style="font-size:12px;'
            f'color:{TEXT_3}">🔎 Chart-Prüfer · Kurstag {t(r.get("stand", ""))}</span><span style="font-size:16px;'
            f'font-weight:600;color:{f}">{"kein Widerspruch" if not w else f"{len(w)} Widerspruch" + ("e" if len(w) > 1 else "")}'
            f'</span></div><div style="margin-top:6px;color:{TEXT_2};font-size:13px">✓ {t(r.get("stimmt", ""))}</div>')
    zeilen = "".join(
        f'<li style="margin:4px 0"><b>{t(x["element"])}</b> {"●" if x["gewicht"] == "sicher" else "○ strittig"} – '
        f'{t(x["befund"])}<br><span style="color:{TEXT_3}">Richtig wäre: {t(x["richtig"])} · {t(x["regel"])}</span></li>'
        for x in w)
    liste = f'<ul style="margin:8px 0 0 18px;padding:0;color:{TEXT_2};font-size:13px">{zeilen}</ul>' if zeilen else ""
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-left:3px solid {f};border-radius:10px;'
            f'padding:12px 14px;margin:8px 0">{kopf}{liste}</div>')
