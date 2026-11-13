"""Seite Konferenzraum (09.11.2026, Lagekarte seit 12.11.2026): oben die Lagekarte – Lagebrett (Haltung, Markt, Pendel,
Datenstand), Zielliste, Konsens-Matrix (feste Ampeln des Codes links, Urteile der Strategen rechts), am Auslöser,
Gefahren, Bilanz der letzten Ziele; darunter zugeklappt Tagesbefehl und Meldungen im Wortlaut, alle Akten, Feldhandbuch.
Rechnet nicht – liest die Konferenz des Frühlaufs (kern/stab.py)."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
sys.path.insert(0, HIER)

import stab  # noqa: E402
from gestaltung import AMPEL, BLAU, GELB, GRAU, GRUEN, KARTE, RAND, ROT, TEXT, TEXT_2, TEXT_3, seite, t  # noqa: E402

FARBE = {"grün": GRUEN, "gelb": GELB, "rot": ROT}
PUNKT = {"grün": "🟢", "gelb": "🟡", "rot": "🔴"}


def _h(text):
    return t(str(text or "")).replace("<", "&lt;")


def kopf(k):
    ko = stab.kosten()
    if not k or k.get("format") == 2:
        return seite(
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
            f'<h1 style="margin:0;font-size:30px;color:{TEXT}">Konferenzraum · MARAGA Investment</h1>'
            f'<div style="color:{TEXT_2};font-size:14px">{"Konferenz vom " + k["zeit"] if k else "noch keine Konferenz"}'
            f' · Kosten {_zahl(ko["usd"])} $ von {_zahl(stab.DECKEL_USD, 0)} $ im Monat · {ko["aufrufe"]} Aufrufe · '
            f'{ko["suchen"]} Web-Suchen</div></div>'
            f'<p style="color:{TEXT_2};font-size:15px;margin:8px 0 0">Acht Missionen, jede mit einer Frage: Lage, '
            f'Aufklärung, Jäger, Operationsplaner, Gegenspieler, Truppenführung, Kriegsgeschichte, Feldherr. Die App '
            f'misst Phase und Zeichen der Stärke und Schwäche, der Stab urteilt – Chancen zuerst, rot ist nie ein '
            f'Auftrag. Jede Zahl stammt aus der App oder einer genannten Quelle; die Faktenwache markiert, was sie nicht '
            f'findet.</p>', oben=12, unten=8)
    stand = f'Konferenz vom {k["zeit"]}' if k else "noch keine Konferenz"
    return seite(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
        f'<h1 style="margin:0;font-size:30px;color:{TEXT}">Konferenzraum · MARAGA Investment</h1>'
        f'<div style="color:{TEXT_2};font-size:14px">{stand} · Kosten {_zahl(ko["usd"])} $ von {_zahl(stab.DECKEL_USD, 0)} $ im Monat'
        f' · {ko["aufrufe"]} Aufrufe · {ko["suchen"]} Web-Suchen</div></div>'
        f'<p style="color:{TEXT_2};font-size:15px;margin:8px 0 0">Sechs Strategen lesen nach dem Frühlauf die Daten der App '
        f'und erklären die Lage, jeder nach dem Handwerk seiner Meister; ein Gegenspieler sucht die Schwächen. Sie zeigen auf, sie filtern nichts und entscheiden nichts – jede Zahl stammt aus der App '
        f'oder einer genannten Quelle, die Faktenwache markiert, was sie nicht findet.</p>', oben=12, unten=8)


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
            f'<div>{titel_}{tag}{_h(h.get("text"))}{_wache(h)}</div></div>')


def _wache(h):
    """Vermerk der Faktenwache (10.11.2026): was sie in den Daten nicht gefunden hat – nachsehen, nicht unbedingt falsch."""
    w = h.get("wache") or {}
    teile = ([f'Ticker unbekannt: {", ".join(w["ticker"])}'] if w.get("ticker") else []) \
        + ([f'Zahl nicht in den Daten: {"; ".join(w["zahlen"])}'] if w.get("zahlen") else [])
    return (f'<div style="font-size:13px;color:{GELB};margin-top:2px">⚠ Faktenwache · {_h(" · ".join(teile))}</div>'
            if teile else "")


def _einwand(e):
    f = FARBE.get(e.get("ampel"), TEXT_2)
    tks = stab._ticker(e.get("titel"), None)
    titel_ = " · ".join(f'<a href="?seite=Titelseite&t={tk}" target="_self" style="color:{BLAU};font-weight:600;'
                        f'text-decoration:none">{tk}</a>' for tk in tks)
    return (f'<div style="border-left:3px solid {f};padding:2px 0 2px 10px;margin:8px 0;font-size:15px;line-height:1.5">'
            f'{titel_ + " · " if titel_ else ""}<span style="color:{TEXT_2}">Einwand:</span> {_h(e.get("einwand"))}<br>'
            f'<span style="color:{TEXT_2}">Abwägung:</span> {_h(e.get("antwort"))}{_wache(e)}</div>')


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
    if "einwaende" in b:
        liste = b.get("einwaende") or []
        teile += (f'<div style="font-size:14px;font-weight:600;color:{TEXT_2};margin:14px 0 2px">Einwände des '
                  f'Gegenspielers · Abwägung<span style="color:{TEXT_3};font-weight:400"> · {len(liste)}</span></div>'
                  + ("".join(_einwand(e) for e in liste) or f'<div style="font-size:14px;color:{TEXT_3}">keine</div>'))
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
             "text": f'{h.get("von") or stab.STRATEGEN[nr][0]}: {h.get("text", "")}'} for nr, h in eintraege
            if h.get("datum") and (not bis or str(h["datum"])[:10] <= bis)]


ANLEITUNG = """**So legst du den API-Schlüssel an (einmalig, etwa 5 Minuten):**

1. Öffne **console.anthropic.com** und melde dich an (oder lege dort ein Konto an).
2. Unter **Billing** Guthaben aufladen – für den Anfang reichen 50 $.
3. Unter **Limits** ein Monatslimit setzen, z. B. 50 $ (zweite Sicherung neben dem Deckel der App).
4. Unter **API Keys** → **Create Key**, Name z. B. „Invest Cockpit“. Den Schlüssel (beginnt mit `sk-ant-`) kopieren –
   er wird nur einmal angezeigt.
5. Hier unten einfügen und speichern. Er liegt dann nur auf dem Server (nicht in GitHub)."""


# ── Lagekarte (12.11.2026, Micky: „auf einen Blick sofort einen Überblick über die Lage“) ──

HALTUNG_FARBE = {"angreifen": GRUEN, "klein tasten": GELB, "abwarten": GELB, "verteidigen": ROT}
SPALTEN_CODE = ("Setup", "Einstieg", "Geld", "Zahlen", "Termin")
SPALTEN_STAB = ((2, "Strömung"), (3, "Fundament"), (4, "Chart"), (5, "Risiko"), (6, "Gegen­spieler"))
TEIL = {"volltreffer": "Volltreffer", "long": "long", "short": "short"}


def _p(ampel, titel="", groesse=13):
    f = AMPEL.get(ampel or "grau", GRAU)
    return (f'<span title="{_h(titel)}" style="display:inline-block;width:{groesse}px;height:{groesse}px;'
            f'border-radius:50%;background:{f};vertical-align:middle"></span>')


def _tk(tk):
    import html
    tk = html.escape(str(tk or "").strip().upper())        # Ticker kommen auch vom Modell (Prüf-Agent 13.11.2026)
    if not tk:
        return ""
    return (f'<a href="?seite=Titelseite&t={tk}" target="_self" style="color:{BLAU};font-weight:600;'
            f'text-decoration:none">{tk}</a>')


def _zahl(x, n=2):
    return "—" if x is None else f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _feld(kopf, gross, farbe, unter):
    return (f'<div style="flex:1 1 200px;background:{KARTE};border:1px solid {RAND};border-left:4px solid {farbe};'
            f'border-radius:10px;padding:12px 14px"><div style="font-size:12px;color:{TEXT_3};letter-spacing:0.06em;'
            f'text-transform:uppercase">{kopf}</div><div style="font-size:20px;font-weight:600;color:{TEXT};'
            f'margin:4px 0 2px">{gross}</div><div style="font-size:13px;color:{TEXT_2}">{unter}</div></div>')


def _brett(lk):
    br = lk.get("brett") or {}
    h = lk.get("haltung")
    m = br.get("markt") or {}
    mm = m if "ampel" in m else (m.get("minervini") or {})   # alte Konferenzen trugen die Ampel unter „minervini“
    markt_f = AMPEL.get(mm.get("ampel"), GRAU)       # eine Ampel nach O'Neil (Micky 12.11.2026)
    pe = br.get("pendel") or {}
    ds = br.get("datenstand") or {}
    if isinstance(ds, str):
        ds = {"text": ds}
    return ('<div style="display:flex;flex-wrap:wrap;gap:12px">'
            + _feld("Haltung des Stabs", _h(h or lk.get("lage_kurz") or "—"), HALTUNG_FARBE.get(h, BLAU),
                    _h(lk.get("lage_kurz") if h else "") or "&nbsp;")
            + _feld("Markt", f'{_p(mm.get("ampel"))} {_h(mm.get("wort") or "—")}', markt_f,
                    (f'O\'Neil · seit {_h(mm["seit"])}' if mm.get("seit") else "O'Neil") if "ampel" in m
                    else "alte Markt-Regel (Konferenz vor dem 13.11.2026)")
            + _feld("Pendel", _h(f'{pe.get("zone") or "—"} {pe.get("pfeil") or ""}'), AMPEL.get(pe.get("ampel"), GRAU),
                    _h(f'vor 4 Wochen: {pe.get("vor_4_wochen")}') if pe.get("vor_4_wochen") else "&nbsp;")
            + _feld("Datenstand", _p(ds.get("ampel")) + " " + ("gleicher Tag" if ds.get("ampel") == "grün" else
                                                                "prüfen" if ds.get("ampel") else "—"),
                    AMPEL.get(ds.get("ampel"), GRAU), _h(ds.get("text") or ""))
            + "</div>")


def _tabelle(kopf, zeilen, mitte=()):
    th = "".join(f'<th style="text-align:{"center" if i in mitte else "left"};padding:6px 8px;font-weight:500;'
                 f'color:{TEXT_3};font-size:12px;border-bottom:1px solid {RAND};white-space:nowrap">{k}</th>'
                 for i, k in enumerate(kopf))
    tr = "".join("<tr>" + "".join(f'<td style="padding:7px 8px;border-bottom:1px solid {RAND};vertical-align:top;'
                                  f'text-align:{"center" if i in mitte else "left"}">{z}</td>'
                                  for i, z in enumerate(zeile)) + "</tr>" for zeile in zeilen)
    return (f'<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;'
            f'color:{TEXT}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')


def _abschnitt(titel, inhalt, zusatz=""):
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:14px 16px">'
            f'<div style="font-size:15px;font-weight:600;color:{TEXT};margin-bottom:8px">{titel}'
            f'<span style="font-weight:400;color:{TEXT_3};font-size:13px"> {zusatz}</span></div>{inhalt}</div>')


def _ziele(lk):
    zeilen = []
    for i, z in enumerate(lk["ziele"], 1):
        a = z.get("akte") or {}
        amp = a.get("ampeln") or {}
        se, ei = amp.get("Setup") or {}, amp.get("Einstieg") or {}
        e = z.get("einwand")
        einw = (_p(e.get("ampel"), f'Einwand: {e.get("einwand")} – Abwägung: {e.get("antwort")}') if e
                else f'<span style="color:{TEXT_3}">—</span>')
        zeilen.append((f'<b>{i}</b>', _tk(z["titel"]),
                       f'<span style="color:{TEXT_2}">{TEIL[z["teil"]]}</span>',
                       f'{_p(se.get("ampel"), se.get("wert"))} <span style="color:{TEXT_2}">{_h(se.get("wert") or "")}</span>',
                       f'{_p(ei.get("ampel"), ei.get("wert"))} {_h(ei.get("wert") or "—")}',
                       _zahl(a.get("stopp")),
                       f'{_p(z.get("ampel"))} {_h(z["kurz"])}' + _wache(z), einw))
    if not zeilen:
        return _abschnitt("Angriffsziele", f'<div style="color:{TEXT_2};font-size:14px">Der Stab nennt heute kein Ziel.</div>')
    return _abschnitt("Angriffsziele", _tabelle(("#", "Titel", "Seite", "Setup (Code)", "Einstieg (Code)", "Stopp",
                                                 "Kernsatz des Strategen", "Einwand"), zeilen, mitte=(7,)),
                      "· Rang des Strategen · Setup und Einstieg rechnet der Code · Stopp 1,5 ATR")


def _matrix(lk):
    if not lk["zeilen"]:
        return ""
    akten_ = {x["titel"]: x for x in lk["tafel"]}
    kopf = ("Titel",) + SPALTEN_CODE + tuple(n for _, n in SPALTEN_STAB)
    zeilen = []
    for tk in lk["zeilen"]:
        amp = (akten_.get(tk) or {}).get("ampeln") or {}
        code = tuple(_p((amp.get(n) or {}).get("ampel"), f'{n}: {(amp.get(n) or {}).get("wert") or "—"}', 15)
                     for n in SPALTEN_CODE)
        r = lk["matrix"].get(tk) or {}
        stab_ = tuple((_p(r[nr]["ampel"], f'{name}: {r[nr].get("grund")}', 15) if nr in r
                       else f'<span style="color:{TEXT_3}" title="{name}: kein Urteil">·</span>') for nr, name in SPALTEN_STAB)
        depot = f' <span style="color:{TEXT_3};font-size:12px">Depot</span>' if (akten_.get(tk) or {}).get("depot") else ""
        zeilen.append((_tk(tk) + depot,) + code + stab_)
    trenn = len(SPALTEN_CODE)
    html = _tabelle(kopf, zeilen, mitte=tuple(range(1, len(kopf))))
    return _abschnitt("Konsens-Matrix", html, f"· links {trenn} feste Ampeln des Codes, rechts das Urteil je Stratege "
                                              "· Maus auf den Punkt zeigt den Grund · alle grün = der Stab ist sich einig")


def _drei(lk):
    w = lk["warten"]
    warten = "".join(f'<div style="margin:4px 0">{_tk(x["titel"])} · {_h(x["ampeln"]["Einstieg"]["wert"])}'
                     f'<span style="color:{TEXT_3}"> · Pivot {_zahl(x.get("pivot"))} · Stopp {_zahl(x.get("stopp"))}'
                     f'</span></div>' for x in w) or f'<div style="color:{TEXT_3}">keiner</div>'
    gef = "".join(f'<div style="margin:4px 0">{_p(g.get("ampel"))} '
                  f'{" ".join(_tk(t_) for t_ in g["titel"]) + " · " if g["titel"] else ""}{_h(g["kurz"])}</div>'
                  for g in lk["gefahren"]) or f'<div style="color:{TEXT_3}">keine genannt</div>'
    bil = lk.get("bilanz") or {}
    zi = bil.get("ziele") or []
    tr = [z for z in zi if z.get("treffer") is not None]
    bilanz_ = "".join(f'<div style="margin:4px 0">{_tk(z["titel"])} <span style="color:{TEXT_3}">{z["seite"]}</span> · '
                      f'{_zahl(z.get("pct"), 1)} % ' + ("" if z.get("treffer") is None else
                      f'<span style="color:{GRUEN if z["treffer"] else ROT}">{"✓" if z["treffer"] else "✗"}</span>')
                      + "</div>" for z in zi) or f'<div style="color:{TEXT_3}">keine frühere Konferenz</div>'
    zusatz = (f'· seit {bil["konferenz_vom"][8:10]}.{bil["konferenz_vom"][5:7]}. · '
              f'{sum(1 for z in tr if z["treffer"])} von {len(tr)} in Richtung') if bil.get("konferenz_vom") else ""
    sp = lambda inhalt: f'<div style="flex:1 1 280px;min-width:0">{inhalt}</div>'  # noqa: E731
    return ('<div style="display:flex;flex-wrap:wrap;gap:12px">'
            + sp(_abschnitt("Am Auslöser", f'<div style="font-size:14px">{warten}</div>', "· Setup grün, Kurs bis 5 % vor dem Einstieg"))
            + sp(_abschnitt("Gefahren", f'<div style="font-size:14px">{gef}</div>'))
            + sp(_abschnitt("Bilanz der letzten Ziele", f'<div style="font-size:14px">{bilanz_}</div>', zusatz))
            + "</div>")


def lagekarte_html(lk):
    if lk.get("neu"):
        return befehl_neu_html(lk)
    lage = (f'<div style="font-size:15px;line-height:1.55;color:{TEXT_2}">{_h(lk.get("lage"))}</div>'
            if lk.get("lage") else "")
    hinweis = (f'<div style="font-size:12px;color:{GELB}">Diese Konferenz stammt aus der Zeit vor der Lagekarte: '
               f'feste Ampeln mit dem heutigen Stand gerechnet, Urteile aus den Hinweisen der Strategen gelesen.</div>'
               if lk.get("live") else "")
    return seite(_brett(lk) + lage + hinweis + _ziele(lk) + _matrix(lk) + _drei(lk), oben=8, unten=8)


def regeln_text():
    """Die Regeln der festen Ampeln (Legende unter der Matrix)."""
    return "\n".join(f"- **{n}:** {r}" for n, r in stab.FESTE_REGELN) + (
        "\n- **Strategen-Spalten:** jeder Stratege urteilt nur über seine Frage (Strömung, Zahlen und Termine, Chart, "
        "Risiko, Einwand) – nicht über das Setup. Grau = kein Urteil zu diesem Titel.")


def tafel_html(tf):
    """Alle Akten des Stabs: warum der Titel dort liegt und seine festen Ampeln."""
    zeilen = []
    for x in tf:
        amp = x.get("ampeln") or {}
        zeilen.append((_tk(x["titel"]), f'<span style="color:{TEXT_2}">{_h(x.get("warum"))}</span>',
                       _h(x.get("seite") or "—"), _zahl(x.get("kurs")), _zahl(x.get("pivot")), _zahl(x.get("stopp")))
                      + tuple(f'{_p((amp.get(n) or {}).get("ampel"))} <span style="color:{TEXT_2};font-size:13px">'
                              f'{_h((amp.get(n) or {}).get("wert") or "")}</span>' for n in SPALTEN_CODE))
    return seite(_tabelle(("Titel", "Warum beim Stab", "Seite", "Kurs", "Pivot", "Stopp") + SPALTEN_CODE, zeilen),
                 oben=4, unten=4)


# ── Neuer Stab (13.11.2026): Befehl mit Chancen, Kreislaufbild, Leitfrage, Anwärter, Depot, Lehre ──

def _chance(c, kreis):
    import kreislaufbild
    e = c.get("einwand") or {}
    zahlen = []
    if c.get("einstieg") is not None:
        zahlen.append(f'Einstieg {_zahl(c.get("einstieg"))} $')
    if c.get("stopp") is not None:
        zahlen.append(f'Stopp {_zahl(c.get("stopp"))} $')
    app = (f' <span style="color:{TEXT_3}">(App: {_zahl(c.get("einstieg_app"))} / {_zahl(c.get("stopp_app"))})</span>'
           if c.get("einstieg_app") is not None and (c.get("einstieg_app") != c.get("einstieg")
                                                      or c.get("stopp_app") != c.get("stopp")) else "")
    einw = (f'<div style="font-size:14px;color:{TEXT_2};margin-top:4px">{_p(_URTEIL.get(e.get("urteil")))} '
            f'Gegenspieler ({_h(e.get("urteil"))}): {_h(e.get("einwand"))}</div>' if e else "")
    pf = "↓ short" if c.get("seite") == "short" else "↑ long"
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-left:4px solid {GRUEN};border-radius:12px;'
            f'padding:14px 16px;margin:10px 0">'
            f'<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:baseline">'
            f'<div style="font-size:20px">{_tk(c["titel"])} <span style="font-size:14px;color:{TEXT_2}">{pf}</span></div>'
            f'<div style="font-size:14px;color:{TEXT_2}">{_h(c.get("phase"))}</div></div>'
            f'<div style="font-size:16px;line-height:1.55;color:{TEXT};margin:6px 0">{_h(c.get("warum"))}{_wache(c)}</div>'
            f'<div style="font-size:15px;color:{TEXT}"><b>Tun:</b> {_h(c.get("tun"))}</div>'
            f'<div style="font-size:14px;color:{TEXT_2};margin-top:2px">{" · ".join(zahlen)}{app}</div>'
            f'<div style="font-size:14px;color:{GELB};margin-top:4px"><b>Achte auf:</b> {_h(c.get("achte_auf"))}</div>'
            + einw + (kreislaufbild.gross(kreis, c["titel"]) if kreis else "") + "</div>")


_URTEIL = {"hält": "grün", "schwächt": "gelb", "kippt": "rot"}


def befehl_neu_html(lk):
    import kreislaufbild
    k = lk["k"]
    b = k.get("befehl") or {}
    kreis = k.get("kreislauf") or {}
    teile = [_brett(lk)]
    teile.append(f'<div style="background:{KARTE};border:2px solid {BLAU};border-radius:14px;padding:16px 18px;'
                 f'margin-top:12px"><div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;'
                 f'text-transform:uppercase">Tagesbefehl · Feldherr</div><div style="font-size:19px;line-height:1.55;'
                 f'color:{TEXT};margin-top:6px">{_h(b.get("anrede"))}{_wache(b)}</div></div>')
    ch = b.get("chancen") or []
    teile.append(f'<div style="font-size:17px;font-weight:600;color:{TEXT};margin:16px 0 0">Chancen · {len(ch)}</div>'
                 + ("".join(_chance(c, kreis.get(c["titel"])) for c in ch)
                    or f'<div style="font-size:15px;color:{TEXT_2};margin:6px 0">Heute keine Chance, die den '
                       f'Gegenspieler übersteht. Rot ist nie ein Auftrag.</div>'))
    sz = "".join(f'<div style="flex:1 1 280px;border:1px solid {RAND};border-radius:10px;padding:10px 12px">'
                 f'<div style="font-size:13px;color:{TEXT_3}">Szenario {_h(s_.get("name"))} · '
                 f'{_h(s_.get("haltung"))}</div><div style="font-size:15px;color:{TEXT};margin:4px 0">'
                 f'<b>Wenn</b> {_h(s_.get("ausloeser"))}</div><div style="font-size:15px;color:{TEXT_2}">'
                 f'<b>dann</b> {_h(s_.get("tun"))}</div></div>' for s_ in b.get("szenarien") or [])
    teile.append(_abschnitt("Leitfrage", f'<div style="font-size:16px;color:{TEXT};margin-bottom:8px">'
                            f'{_h(b.get("leitfrage"))}</div><div style="display:flex;flex-wrap:wrap;gap:10px">{sz}</div>'))
    anw = b.get("anwaerter") or []
    if anw:
        z = "".join(f'<div style="display:flex;gap:12px;align-items:center;margin:8px 0">'
                    f'<div style="flex:none">{kreislaufbild.mini(kreis.get(a.get("titel")))}</div>'
                    f'<div style="font-size:15px">{_tk(a.get("titel"))} · '
                    f'<span style="color:{TEXT_2}">{_h(kreislaufbild.wort(kreis.get(a.get("titel"))))}</span><br>'
                    f'{_h(a.get("warum"))} <span style="color:{GELB}">Warten auf: {_h(a.get("warten_auf"))}</span>'
                    f'</div></div>' for a in anw)
        teile.append(_abschnitt("Anwärter · frühe Zeichen der Stärke", z, "· der Jäger: wo Stärke entsteht, bevor das Setup steht"))
    dep = b.get("depot") or []
    if dep:
        teile.append(_abschnitt("Depot", "".join(f'<div style="font-size:15px;margin:4px 0">{_tk(d_.get("titel"))} · '
                                                 f'{_h(d_.get("anweisung"))}</div>' for d_ in dep)))
    if b.get("lehre"):
        teile.append(_abschnitt("Lehre aus gestern", f'<div style="font-size:15px">{_h(b.get("lehre"))}</div>'))
    bil = k.get("bilanz") or {}
    if bil.get("ziele"):
        tr = [z for z in bil["ziele"] if z.get("treffer") is not None]
        teile.append(_abschnitt("Bilanz der letzten Ziele", "".join(
            f'<div style="font-size:14px;margin:3px 0">{_tk(z["titel"])} <span style="color:{TEXT_3}">{z["seite"]}</span> · '
            f'{_zahl(z.get("pct"), 1)} % ' + ("" if z.get("treffer") is None else
                                            f'<span style="color:{GRUEN if z["treffer"] else ROT}">{"✓" if z["treffer"] else "✗"}</span>')
            + "</div>" for z in bil["ziele"]),
            f'· seit {str(bil.get("konferenz_vom"))[8:10]}.{str(bil.get("konferenz_vom"))[5:7]}. · '
            f'{sum(1 for z in tr if z["treffer"])} von {len(tr)} in Richtung'))
    if k.get("wache_code"):
        teile.append(f'<div style="font-size:13px;color:{GELB};margin-top:6px">Wache im Code: '
                     + " · ".join(_h(w) for w in k["wache_code"]) + "</div>")
    kosten_ = (f'<div style="font-size:12px;color:{TEXT_3};margin-top:6px">Diese Konferenz kostete '
               f'{_zahl(k["kosten_usd"])} $.</div>' if k.get("kosten_usd") is not None else "")
    return seite("".join(t_ if t_.startswith('<div style="display:flex;flex-wrap:wrap;gap:12px">') else
                         f'<div style="margin-top:12px">{t_}</div>' for t_ in teile) + kosten_, oben=8, unten=8)


def anhang_html(k):
    """Anhang des Befehls: beobachten und verworfen (der Operationsplaner, jede Akte eingeordnet)."""
    an = (k.get("befehl") or {}).get("anhang") or {}
    be = "".join(f'<div style="margin:3px 0">{_tk(x.get("titel"))} · {_h(x.get("warten_auf"))}</div>'
                 for x in an.get("beobachten") or []) or f'<div style="color:{TEXT_3}">keine</div>'
    ve = "".join(f'<div style="margin:3px 0">{_tk(x.get("titel"))} · {_h(x.get("grund"))}</div>'
                 for x in an.get("verworfen") or []) or f'<div style="color:{TEXT_3}">keine</div>'
    return seite('<div style="display:flex;flex-wrap:wrap;gap:12px">'
                 f'<div style="flex:1 1 300px">{_abschnitt("Beobachten", f"<div style=font-size:14px>{be}</div>", "· das Zeichen, auf das wir warten")}</div>'
                 f'<div style="flex:1 1 300px">{_abschnitt("Verworfen", f"<div style=font-size:14px>{ve}</div>")}</div>'
                 '</div>', oben=4, unten=4)


def _wert(v):
    if isinstance(v, dict):
        return " · ".join(f"{k_}: {_wert(x)}" for k_, x in v.items() if x not in (None, "", [], {}))
    if isinstance(v, list):
        return "; ".join(_wert(x) for x in v)
    return str(v)


def mission_html(nr, m):
    """Eine Mission im Wortlaut (neuer Stab)."""
    name, frage_ = stab.MISSIONEN[nr]
    if m.get("fehler") and m.get("meldung"):
        inhalt = f'<p style="color:{ROT}">{_h(m.get("meldung"))}</p>'
    else:
        zeilen = []
        for k_, v in m.items():
            if k_ in ("name", "roh", "wache", "fehler", "kosten_usd", "verbrauch"):
                continue
            if isinstance(v, list):
                zeilen += [f'<div style="margin:4px 0;font-size:14px">{_h(_wert(x))}{_wache(x) if isinstance(x, dict) else ""}</div>'
                           for x in v] or [f'<div style="color:{TEXT_3};font-size:14px">{_h(k_)}: keine</div>']
            elif v not in (None, ""):
                zeilen.append(f'<div style="margin:4px 0;font-size:14px"><b>{_h(k_)}:</b> {_h(_wert(v))}</div>')
        inhalt = "".join(zeilen)
    return (f'<div style="background:{KARTE};border:1px solid {RAND};border-radius:12px;padding:14px 16px;margin-bottom:12px">'
            f'<div style="font-size:13px;color:{TEXT_3};letter-spacing:0.06em;text-transform:uppercase">{nr} · {name}'
            f'</div><div style="font-size:14px;color:{TEXT_2};margin:2px 0 8px">{frage_}'
            + (f' <span style="color:{TEXT_3}">· {_zahl(m["kosten_usd"])} $</span>' if m.get("kosten_usd") is not None
               else "") + f'</div>{inhalt}</div>')


def lehre():
    """Die Lehre des Stabs zum Gegenlesen (ersetzt das Feldhandbuch der Strategen, 13.11.2026)."""
    d = stab.DIENSTANWEISUNG
    lehre_ = d[d.index("UNSERE LEHRE"):d.index("BEGRIFFE DER APP")].strip()
    regeln = d[d.index("REGELN"):].strip()
    teile = [f"**{nr} · {n} – {f}**\n\n{stab.AUFTRAG_MISSION[nr]}\n\n*{stab.LEHRSTELLE[nr]}*"
             for nr, (n, f) in stab.MISSIONEN.items()]
    quellen = "\n".join(f"- **{m}:** {q}" for m, q in stab.QUELLEN.items())
    return lehre_ + "\n\n" + regeln + "\n\n" + "\n\n".join(teile) + "\n\n**Quellen**\n\n" + quellen
