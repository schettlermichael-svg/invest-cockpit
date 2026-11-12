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
    stand = f'Konferenz vom {k["zeit"]}' if k else "noch keine Konferenz"
    return seite(
        f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
        f'<h1 style="margin:0;font-size:30px;color:{TEXT}">Konferenzraum · MARAGA Investment</h1>'
        f'<div style="color:{TEXT_2};font-size:14px">{stand} · Kosten {ko["usd"]:.2f} $ von {stab.DECKEL_USD:.0f} $ im Monat'
        f' · {ko["aufrufe"]} Aufrufe · {ko["suchen"]} Web-Suchen</div></div>'
        f'<p style="color:{TEXT_2};font-size:15px;margin:8px 0 0">Sechs Strategen lesen nach dem Nachtlauf die Daten der App '
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
             "text": f'{stab.STRATEGEN[nr][0]}: {h.get("text", "")}'} for nr, h in eintraege
            if h.get("datum") and (not bis or str(h["datum"])[:10] <= bis)]


def feldhandbuch():
    """Das Feldhandbuch des Stabs als Text (10.11.2026) – so, wie es die Strategen lesen, mit Quellen. Korrekturen
    Mickys werden hier Sätze (kern/stab.py, MEISTER)."""
    teile = [f"**{nr} · {stab.STRATEGEN[nr][0]}**\n\n{stab.MEISTER[nr]}" for nr in (2, 3, 4, 5, 6, 1)]
    quellen = "\n".join(f"- **{m}:** {q}" for m, q in stab.QUELLEN.items())
    return ("Rangordnung bei Widerspruch: zuerst deine Haltung (Dienstanweisung), dann der Hauptmeister, dann der "
            "Ergänzungsmeister.\n\n" + "\n\n".join(teile) + "\n\n**Quellen**\n\n" + quellen)


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
    mm, mk = m.get("minervini") or {}, m.get("kullamaegi") or {}
    markt_f = {"rot": ROT, "gelb": GELB, "grün": GRUEN}.get(
        "rot" if "rot" in (mm.get("ampel"), mk.get("ampel")) else
        "grün" if mm.get("ampel") == mk.get("ampel") == "grün" else "gelb")
    pe = br.get("pendel") or {}
    ds = br.get("datenstand") or {}
    if isinstance(ds, str):
        ds = {"text": ds}
    return ('<div style="display:flex;flex-wrap:wrap;gap:12px">'
            + _feld("Haltung des Stabs", _h(h or lk.get("lage_kurz") or "—"), HALTUNG_FARBE.get(h, BLAU),
                    _h(lk.get("lage_kurz") if h else "") or "&nbsp;")
            + _feld("Markt", f'{_p(mm.get("ampel"))} M &nbsp; {_p(mk.get("ampel"))} K', markt_f,
                    _h(f'Minervini: {mm.get("wort") or "—"} · Kullamägi: {mk.get("wort") or "—"}'))
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
