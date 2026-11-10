"""Invest Cockpit – Startdatei.

Start im Ordner InvestCockpit:
    streamlit run app.py --server.port 8510

Streamlit liefert nur die Bedienelemente; alles Sichtbare kommt als HTML aus oberflaeche/
und sieht aus wie die Designvorlage.
"""
import os
import sys
import time

import streamlit as st

_T0 = time.time()                                # Stoppuhr (09.11.2026): wie lange die Seite gebraucht hat
_QUELLE = {"text": ""}

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "oberflaeche"))
sys.path.insert(0, os.path.join(HIER, "kern"))

from gestaltung import BLAU, KARTE, RAND, SEITE, TEXT, TEXT_2  # noqa: E402
import chart  # noqa: E402
import titel  # noqa: E402
import uebersicht  # noqa: E402
import kartentisch  # noqa: E402
import gestaltung  # noqa: E402
import watchlists  # noqa: E402
import depot  # noqa: E402

st.set_page_config(page_title="Invest Cockpit", layout="wide", initial_sidebar_state="collapsed")

# Streamlit-Rahmen ausblenden, Hintergrund und Bedienelemente wie die Designvorlage
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {{display:none !important}}
.stApp {{background:{SEITE}; color:{TEXT}; font-family:'IBM Plex Sans',system-ui,sans-serif}}
.block-container {{max-width:1440px; padding:16px 0 0 0 !important}}
div[data-testid="stHorizontalBlock"] {{max-width:1392px; margin:0 auto; padding:0 24px; align-items:end}}
div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] {{padding:0; max-width:none; align-items:center}}
.st-key-kartentisch div[data-testid="stHorizontalBlock"] {{align-items:flex-start}}
.st-key-kartentisch div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] {{align-items:center}}
.st-key-kartentisch [data-testid="stExpander"] {{max-width:1392px; margin:0 auto; padding:0 24px}}
.st-key-rueckenwind [data-testid="stExpander"], .st-key-rueckenwind [data-testid="stHorizontalBlock"],
.st-key-rueckenwind [data-testid="stRadio"] {{max-width:1392px; margin:0 auto; padding:0 24px}}
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{background:{KARTE}; color:{TEXT};
  border:1px solid {RAND}; border-radius:10px; min-height:44px; font-size:16px}}
.stTextInput label, .stRadio label p {{color:{TEXT_2} !important; font-size:14px}}
div[role="radiogroup"] label {{min-height:44px; padding:0 14px; border:1px solid {RAND}; border-radius:10px;
  background:{KARTE}; margin-right:8px}}
div[role="radiogroup"] label:has(input:checked) {{border-color:{BLAU}}}
</style>""", unsafe_allow_html=True)

ansicht_liste = ["Rückenwind", "Titelseite", "Konferenzraum"]   # Übersicht ist seit 10.11.2026 Teil von Rückenwind
ALTE_SEITEN = {"Übersicht": "Rückenwind"}                       # alte Lesezeichen
# Startwerte einmal aus der Adresszeile übernehmen; danach führt Streamlit den Zustand selbst.
# (Ein index= aus der Adresszeile bei jedem Lauf legte das Bedienelement neu an – dann brauchte
# ein Wechsel zwei Klicks.)
if "ansicht" not in st.session_state:
    seite = ALTE_SEITEN.get(st.query_params.get("seite", "Rückenwind"), st.query_params.get("seite", "Rückenwind"))
    st.session_state.ansicht = seite if seite in ansicht_liste else "Rückenwind"
    st.session_state.ticker = st.query_params.get("t", "HWM")
spalte0, spalte1, _ = st.columns([4, 2, 6])
with spalte0:
    ansicht = st.radio("Ansicht", ansicht_liste, horizontal=True, key="ansicht")
with spalte1:
    ticker = st.text_input("Titel", max_chars=12, key="ticker").strip().upper()
st.query_params["t"] = ticker
st.query_params["seite"] = ansicht


@st.cache_data(ttl=3600, show_spinner=False)
def _gebaut(name, codestand, *args):
    """Fertig gebaute Seite für eine Stunde im Speicher: ein Wechsel zwischen Seiten, Titeln oder Zeitebenen, die
    schon einmal offen waren, braucht dann keine Rechnung mehr. codestand ändert sich mit jeder Code-Änderung, damit
    nach einer Änderung nie eine alte Seite gezeigt wird."""
    return {"uebersicht": uebersicht.seite_uebersicht, "titel": titel.seite_titel}[name](*args)


def _fehler(e):
    st.markdown(f'<div style="max-width:1392px;margin:24px auto;padding:20px;background:{KARTE};'
                f'border:1px solid {RAND};border-radius:12px;color:{TEXT}">Die Seite ließ sich nicht bauen: '
                f'{e}</div>', unsafe_allow_html=True)


def _aktualisieren(tk):
    """Knopf „Kurse aktualisieren“ (als Rückruf, damit die Seite im selben Lauf schon mit den neuen Kursen gebaut
    wird): lädt den Titel samt laufender Tageskerze neu; gilt für diesen Titel, bis ein anderer gewählt wird."""
    st.session_state.laufend = (tk, time.time())


def chart_knoepfe(tk):
    """Knöpfe direkt über dem Chart: Zeitebene, Ausschnitt, Kurse aktualisieren, TradingView, Watchlist, Position."""
    k0, k1, k2, k7, k3, k4, k5, k6 = st.columns([2, 3, 2, 2, 2, 2, 2, 2])
    with k0:
        ebene = st.radio("Zeitebene", ["Tag", "Woche"], horizontal=True, key="ebene")
    with k1:
        wahl = list(chart.AUSSCHNITT[ebene])
        aus = st.radio("Ausschnitt", wahl, horizontal=True, key=f"ausschnitt_{ebene}",
                       index=wahl.index(chart.AUSSCHNITT_START[ebene]))
    with k2:
        zonen_ansicht = st.radio("Zonen", chart.ZONE_ANSICHT, horizontal=True, key="zonen_ansicht",
                          help="Aktuell: nur das Setup jetzt (Zone, Vorgeschichte, Fahnenstange). Historie: dazu alle "
                               "abgeschlossenen Basen und Flaggen mit ↑ am Ausbruch.")
    with k7:
        gd_kurz = st.checkbox("GD10 · GD20", key="gd_kurz", help="Kullamägis Linien (nur im Tageschart)")
    with k3:
        st.button("↻ Kurse aktualisieren", use_container_width=True, on_click=_aktualisieren, args=(tk,))
    with k4:
        st.link_button("TradingView ↗", titel.tv_link(tk), use_container_width=True)
    with k5:
        watchlist_knopf(tk)
    with k6:
        position_knopf(tk)
    return ebene, aus, zonen_ansicht, gd_kurz


def _fenster(titel_):
    return (st.popover(titel_, use_container_width=True) if hasattr(st, "popover")   # ab Streamlit 1.31
            else st.expander(titel_))


def position_knopf(tk):
    """„＋ Position“ / „● Position“: anlegen, Stopp nachziehen, schließen (bis Scalable verbunden ist, von Hand)."""
    p = depot.position(tk)
    with _fenster("● Position" if p else "＋ Position"):
        with st.form(f"pos_{tk}"):
            seite_ = st.radio("Seite", ["long", "short"], horizontal=True,
                              index=0 if not p or p.get("seite", "long") == "long" else 1)
            systeme_ = ["Minervini", "Kullamägi"]
            system_ = st.radio("System (bestimmt Stopp nachziehen und Ausstieg)", systeme_, horizontal=True,
                               index=1 if (p or {}).get("system") == "K" else 0)
            stueck = st.number_input("Stück", min_value=0, step=1, value=int(p["stueck"]) if p else 0)
            einstieg = st.number_input("Einstieg (Kurs des Titels)", min_value=0.0, format="%.2f",
                                       value=float(p["einstieg"] or 0) if p else 0.0)
            stopp = st.number_input("Stopp (Kurs des Titels)", min_value=0.0, format="%.2f",
                                    value=float(p["stopp"] or 0) if p else 0.0)
            ko = (p or {}).get("ko") or {}
            schwelle = st.number_input("Knock-out-Schwelle (leer lassen bei Aktie)", min_value=0.0, format="%.2f",
                                       value=float(ko.get("schwelle") or 0))
            bezug = st.number_input("Bezugsverhältnis (z. B. 0,1)", min_value=0.0, format="%.3f",
                                    value=float(ko.get("bezug") or 0))
            if st.form_submit_button("Speichern", use_container_width=True):
                depot.setzen(tk, seite=seite_, system="K" if system_ == "Kullamägi" else "M", stueck=int(stueck),
                             einstieg=einstieg or None, stopp=stopp or None,
                             ko={"schwelle": schwelle, "bezug": bezug} if schwelle and bezug else None)
                st.rerun()
        if p:
            with st.form(f"zu_{tk}"):
                aus = st.number_input("Ausstiegskurs (für deine Bilanz, Minervini-Abgleich)", min_value=0.0,
                                      format="%.2f", value=0.0)
                if st.form_submit_button("Position schließen", use_container_width=True):
                    depot.schliessen(tk, aus or None)
                    st.rerun()


def watchlists_verwalten():
    """Übersicht: die Watchlist pflegen – Ticker einfügen (auch ganze Listen), Titel herausnehmen. Einzelne Titel auch
    über „☆ Watchlist“ auf der Titelseite. Herausgenommen = gelöscht (ohne Revier fällt der Titel aus dem Abendlauf)."""
    drin = watchlists.alle()
    with _fenster(f"◆ Watchlist ({len(drin)})"):
        st.caption(f"{len(drin)} Titel: " + ", ".join(drin[:60]) + (" …" if len(drin) > 60 else ""))
        with st.form("wl_verw_neu", clear_on_submit=True):
            text = st.text_area("Ticker hinzufügen", height=70, placeholder="z. B. NVDA, ANET, XETR:RHM – auch ganze Listen "
                                "aus Finviz oder TradingView einfügen")
            if st.form_submit_button("Hinzufügen", use_container_width=True):
                st.toast(f"{watchlists.einfuegen(text)} Titel neu auf der Watchlist")
                st.rerun()
        if drin:
            with st.form("wl_verw_weg"):
                weg = st.multiselect("Titel herausnehmen", drin)
                if st.form_submit_button("Herausnehmen", use_container_width=True) and weg:
                    for tk in weg:
                        watchlists.setzen(tk, False)
                    st.toast(f"{len(weg)} Titel von der Watchlist genommen")
                    st.rerun()


sys.path.insert(0, os.path.join(HIER, "werkzeuge"))
import nachtlauf  # noqa: E402


def _tisch_starten():
    if nachtlauf.tisch_lauf_starten():
        st.session_state.tisch_lief = True
        st.toast("Kartentisch wird neu gerechnet – dauert eine Weile, die Seite füllt sich danach von selbst")


def _tisch_knopf():
    """Übersicht: Kartentisch (Ränge, Erkennung beider Systeme, Lage) mit den vorhandenen Kursen neu rechnen."""
    laeuft, text = nachtlauf.tisch_lauf_stand()
    if st.session_state.get("tisch_lief") and not laeuft:   # gerade fertig geworden: ganze Seite neu zeigen
        st.session_state.tisch_lief = False
        st.rerun()
    st.session_state.tisch_lief = laeuft
    st.button("↻ Kartentisch neu rechnen", use_container_width=True, disabled=laeuft, on_click=_tisch_starten,
              help="Rechnet RS-Rang, Führer-Rang, den Kartentisch mit beiden Systemen und die Lage neu – "
                   "mit den Kursen des letzten Nachtlaufs, ohne neuen Download. Läuft auf dem Server weiter, auch wenn "
                   "du die Seite schließt.")
    if text:
        st.caption(text)
    schrank = nachtlauf.seiten_lauf_stand()
    if schrank:
        st.caption(schrank)


@st.cache_resource(show_spinner=False)
def _schrank_fuellen(grenze):
    """Einmal je Programm- bzw. Depotstand: veraltete Titelseiten im Hintergrund neu ablegen (06.11.2026)."""
    try:
        return nachtlauf.seiten_lauf_starten()
    except Exception:  # noqa: BLE001
        return False


_FRAGMENT = getattr(st, "fragment", None)
tisch_knopf = _FRAGMENT(run_every=30)(_tisch_knopf) if _FRAGMENT else _tisch_knopf
_schrank_fuellen(titel.ablage_grenze())


def konto_knopf():
    """Übersicht: Konto und Risiko je Trade (Voreinstellung 1 %, auf Wunsch einstellbar)."""
    d = depot.laden()
    with _fenster("⚙ Konto und Risiko"):
        with st.form("konto"):
            konto = st.number_input("Tradingkonto (€)", min_value=0.0, step=1000.0, format="%.0f",
                                    value=float(d.get("konto") or 0))
            risiko = st.number_input("Risiko je Trade (% des Kontos)", min_value=0.1, max_value=5.0, step=0.25,
                                     format="%.2f", value=float(d.get("risiko_pct") or 1.0))
            if st.form_submit_button("Speichern", use_container_width=True):
                depot.einstellen(konto=konto, risiko_pct=risiko)
                st.rerun()


def _watch_umschalten(tk):
    auf = not watchlists.drin(tk)
    watchlists.setzen(tk, auf)
    st.toast(f"{tk} {'auf die Watchlist gesetzt' if auf else 'von der Watchlist genommen'}")


def watchlist_knopf(tk, schluessel=""):
    """Ein Knopf: „☆ Auf die Watchlist“ oder „★ Auf der Watchlist“ (Klick nimmt ihn herunter – ohne Revier fällt der
    Titel dann aus dem Abendlauf)."""
    drin = watchlists.drin(tk)
    st.button("★ Auf der Watchlist" if drin else "☆ Auf die Watchlist", key=f"{schluessel}wl_{tk}",
              use_container_width=True, type="primary" if drin else "secondary", on_click=_watch_umschalten, args=(tk,),
              help="Klick nimmt den Titel von der Watchlist" if drin else "Klick setzt den Titel auf die Watchlist")


def _codestand(mit_watchlists=False):
    """Jüngste Änderungszeit der Programmdateien und der von Claude gelieferten Datendateien."""
    hier = os.path.dirname(os.path.abspath(__file__))
    code = max(os.path.getmtime(os.path.join(hier, d, f)) for d in ("kern", "oberflaeche")
               for f in os.listdir(os.path.join(hier, d)) if f.endswith(".py"))
    daten = [os.path.join(hier, "daten", x) for x in ("sic13/einschaetzung.json", "tv/revier.csv",
                                                       "steckbrief_de/beschreibungen.json")]
    daten += [depot.DATEI] + ([watchlists.DATEI] if mit_watchlists else [])   # Depot geändert: Seiten neu bauen;
    # Watchlists nur für den Kartentisch (Übersicht und Titelseiten hängen nicht von ihnen ab)
    tisch = os.path.join(hier, "daten", "kartentisch")
    if os.path.isdir(tisch):                     # neuer Kartentisch aus dem Abendlauf: Übersicht neu bauen
        daten += [os.path.join(tisch, f) for f in os.listdir(tisch) if f.endswith(".json")]
    return max([code] + [os.path.getmtime(x) for x in daten if os.path.exists(x)])


# ── Kartentisch auf der Übersicht: Karten mit Knöpfen, übrige Titel als Tabelle, Lagekarte im Pop-up ──
@st.cache_resource(show_spinner=False, max_entries=2)
def _tischplan(codestand):
    """Kartentisch-Plan einmal je Code-/Datenstand (cache_resource: die großen Karten werden nicht kopiert)."""
    return kartentisch.plan()


def _rgba(farbe):
    """'#3FB95066' → 'rgba(63,185,80,0.4)' (die Tabelle versteht keine achtstelligen Farben)."""
    h = farbe.lstrip("#")
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a:.2f})"


def _knopfleiste(tk, liste, schluessel):
    a, b = st.columns(2)
    with a:
        watchlist_knopf(tk, schluessel)
    with b:
        st.link_button("Deep Dive →", f"?seite=Titelseite&t={tk}", use_container_width=True)


_DIALOG = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)


def _karte_zeigen(tk, x, liste):
    """Lagekarte eines Tabellen-Titels im Pop-up (✕ oben rechts schließt es), darunter dieselben Knöpfe."""
    if x and x.get("karte"):
        st.markdown(kartentisch.karte_html(x, kartentisch._marken(x) if liste else ""), unsafe_allow_html=True)
    else:
        st.markdown(f"**{tk}**: noch keine Lagekarte – sie wird im Abendlauf gerechnet.")
    _knopfleiste(tk, liste, "dlg_")


if _DIALOG:
    try:                                    # ✕ löst einen Lauf aus: danach steht die Tabelle ohne Auswahl bereit
        _karte_zeigen = _DIALOG("Lagekarte", width="large", on_dismiss="rerun")(_karte_zeigen)
    except TypeError:                       # ältere Streamlit-Version
        _karte_zeigen = _DIALOG("Lagekarte", width="large")(_karte_zeigen)


def _tabelle(teil, nr):
    """Die übrigen Titel eines Abschnitts als Tabelle, in derselben Rangfolge wie die Karten. Farbfeld links =
    Rahmenstufe. Klick auf eine Zeile öffnet die Lagekarte im Pop-up."""
    import pandas as pd
    zeilen = teil["zeilen"]
    if not zeilen:
        return
    df = pd.DataFrame([{" ": "", "Titel": z["tk"], "Setup": z["Setup"], "Befund": z["Befund"],
                        "Abstand %": z["Abstand %"], "Was fehlt": z["Was fehlt"]} for z in zeilen])
    farben = [_rgba(z["farbe"] + ("66" if z.get("blass") else "")) for z in zeilen]
    stil = df.style.apply(lambda spalte: [f"background-color:{f}" for f in farben], subset=[" "])
    zaehler = f"tab_n_{nr}"
    n = st.session_state.setdefault(zaehler, 0)
    # Zweite Stufe im Ausklappmenü des Abschnitts: Streamlit erlaubt kein Ausklappmenü im Ausklappmenü, daher ein
    # Schalter, der genauso auf- und zuklappt (06.11.2026)
    schalter = getattr(st, "toggle", st.checkbox)
    if not schalter(f"▸ alle weiteren {len(zeilen)} als Liste · Zeile anklicken öffnet die Lagekarte", key=f"weitere_{nr}"):
        return
    ereignis = st.dataframe(stil, hide_index=True, use_container_width=True, on_select="rerun",
                            selection_mode="single-row", key=f"tab_{nr}_{n}",
                            height=min(420, 35 * (len(zeilen) + 1) + 3),
                            column_config={" ": st.column_config.TextColumn(" ", width="small")})
    reihen = ereignis.selection.rows if ereignis is not None else []
    schluessel = f"tab_{nr}_{n}"
    if st.session_state.get("tab_offen") == schluessel:
        # Erster Lauf nach dem Pop-up (✕ oder ein Knopf darin): Auswahl verwerfen und die Tabelle sofort frisch
        # aufbauen – der nächste Klick, auch auf dieselbe Zeile, öffnet das Pop-up mit einem Klick.
        st.session_state.tab_offen = None
        st.session_state[zaehler] = n + 1
        st.rerun()
    if reihen:
        tk = zeilen[reihen[0]]["tk"]
        st.session_state.tab_offen = schluessel
        if _DIALOG:
            _karte_zeigen(tk, teil["titel"].get(tk), teil["liste"])
        else:
            st.link_button(f"{tk}: Deep Dive →", f"?seite=Titelseite&t={tk}")


def _kartentisch_zeigen():
    def html(h):
        st.markdown(gestaltung.seite(h, oben=12, unten=12), unsafe_allow_html=True)
    try:
        huelle = st.container(key="kartentisch")
    except TypeError:                               # ältere Streamlit-Version ohne key
        huelle = st.container()
    with huelle:
        for nr, teil in enumerate(_tischplan(_codestand(mit_watchlists=True))):
            if teil["art"] == "html":
                html(teil["html"])
                continue
            # Ausklappmenü je Setup (06.11.2026): zu Name, Zahl und Regel, aufgeklappt die Karten; alle zu, auch die Watchlist
            kopf = f"**{teil['name']} · {teil['zahl']}** — {teil['text']}"
            with st.expander(kopf, expanded=False):
                if not (teil["karten"] or teil["zeilen"]):
                    st.caption("zurzeit keine")
                name = f"{nr}_{teil['liste'] or 'reihe'}"
                karten = teil["karten"]
                for i in range(0, len(karten), 3):
                    for spalte, (tk, x, h) in zip(st.columns(3), karten[i:i + 3]):
                        with spalte:
                            st.markdown(h, unsafe_allow_html=True)
                            _knopfleiste(tk, teil["liste"], f"k{name}_")
                _tabelle(teil, name)


def _schrank_text(alt):
    if not alt:
        return "aus dem Schrank"
    _hinweis_alt()
    return "aus dem Schrank (vor der letzten Programmänderung gebaut, neue Fassung im Hintergrund)"


def _hinweis_alt():
    st.caption("Diese Seite wurde vor der letzten Programmänderung abgelegt und deshalb sofort gezeigt – die Daten sind "
               "aktuell, neue Ansichten erscheinen, sobald der Schrank im Hintergrund neu gefüllt ist.")


def zeigen(name, *args):
    """Seite als HTML ausgeben. st.markdown statt st.html: st.html entfernt die Inhalte
    eingebetteter SVG-Grafiken (den Chart)."""
    try:
        ab = uebersicht.abgelegt() if name == "uebersicht" else None   # vom Abendlauf gebaut: sofort da
        if ab is not None and "lage" not in ab[0]:   # abgelegt vor dem Zusammenlegen (10.11.2026): neu bauen
            ab = None
        if ab is not None:
            html, alt = ab
            _QUELLE["text"] = _schrank_text(alt)
        else:
            t0 = time.time()
            with st.spinner("Lade und rechne …"):
                html = _gebaut(name, _codestand(), *args)
            _QUELLE["text"] = "frisch gerechnet" if time.time() - t0 > 0.5 else "aus dem Zwischenspeicher"
        if isinstance(html, dict):                   # Seite Rückenwind: ① Lage, ② Rückenwind, ③ Stellung, ④, ⑤
            st.markdown(html["lage"], unsafe_allow_html=True)
            st.markdown(gestaltung.seite(gestaltung.station("wind"), oben=16, unten=0), unsafe_allow_html=True)
            try:                                     # ein Fehler im Rückenwind lässt Stellung und Truppe stehen
                rueckenwind_zeigen()
            except Exception as e:  # noqa: BLE001
                _fehler(e)
            _kartentisch_zeigen()
            st.markdown(html["unten"], unsafe_allow_html=True)
        else:
            st.markdown(html, unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)


def rueckenwind_zeigen():
    """Seite „Rückenwind“ (KONZEPT_RUECKENWIND.md): Strömungskarte, Gruppen nach Geldfluss, dreifacher Rückenwind,
    Titel je Stufe, Logbuch. Rechnet nicht – liest den Stand des Nachtlaufs."""
    import rueckenwind as rw_kern
    import rueckenwind_seite as rw
    erg = rw_kern.laden()
    if not erg:
        st.markdown(gestaltung.seite("<p>Noch kein Stand – der Rückenwind wird im Nachtlauf (oder mit „Kartentisch neu "
                                     "rechnen“) gerechnet.</p>"), unsafe_allow_html=True)
        return
    with st.container(key="rueckenwind"):
        st.markdown(rw.kopf(erg, titel=False), unsafe_allow_html=True)
        st.markdown(gestaltung.seite("<h3 style='margin:0'>Wetterkarte der Strömung · wohin das Geld fließt</h3>", oben=8,
                                     unten=0), unsafe_allow_html=True)
        art = st.radio("Ebene", ["Sektor", "Branche", "Thema"], horizontal=True, key="rw_ebene", index=1)
        st.markdown(rw.wetterkarte(erg, art), unsafe_allow_html=True)
        with st.expander(f"Alle {'Sektoren' if art == 'Sektor' else 'Branchen' if art == 'Branche' else 'Themen'} "
                         f"nach Geldfluss"):
            st.dataframe(rw.gruppen(erg, art), hide_index=True, use_container_width=True)
        st.markdown(gestaltung.seite("<h3 style='margin:0'>Dreifacher Rückenwind · Kurs, Geld und Zahlen grün</h3>",
                                     oben=16, unten=0), unsafe_allow_html=True)
        st.markdown(rw.dreifach(erg), unsafe_allow_html=True)
        st.markdown(gestaltung.seite("<h3 style='margin:0'>Schnellsuche · die Besten auf einen Blick</h3>", oben=16,
                                     unten=0), unsafe_allow_html=True)
        knopf = getattr(st, "segmented_control", None)
        wahl = (knopf("Schnellsuche", ["Anführer", "Verfolger"], key="rw_schnell", label_visibility="collapsed")
                if knopf else st.radio("Schnellsuche", ["–", "Anführer", "Verfolger"], horizontal=True, key="rw_schnell"))
        if wahl in rw.SCHNELL_TEXT:
            df, tks = rw.schnell(erg, wahl)
            st.caption(rw.SCHNELL_TEXT[wahl] + " · Zeile anklicken → Titelseite")
            ereignis = st.dataframe(df, hide_index=True, use_container_width=True, on_select="rerun",
                                    selection_mode="single-row", key=f"rw_schnell_tab_{wahl}",
                                    height=min(560, 35 * (len(df) + 1) + 3))
            reihen = ereignis.selection.rows if ereignis is not None else []
            if reihen:
                st.link_button(f"{tks[reihen[0]]}: Titelseite →", f"?seite=Titelseite&t={tks[reihen[0]]}")
        st.markdown(gestaltung.seite("<h3 style='margin:0'>Titel nach Stufe</h3>", oben=16, unten=4),
                    unsafe_allow_html=True)
        st.caption("◆ = auf der Watchlist")
        for nr, name in enumerate(list(rw_kern.STUFEN) + [None]):     # zuletzt: ohne Stufe (nichts weggelassen)
            df, tks = rw.stufe(erg, name)
            with st.expander(f"**{name or 'Ohne Stufe'} · {len(df)}** — {rw.STUFE_TEXT[name]}", expanded=False):
                if not len(df):
                    st.caption("zurzeit keine")
                    continue
                st.caption("Sortiert: Geld, dann Zahlen, dann Tempo · Zeile anklicken → Titelseite")
                ereignis = st.dataframe(df, hide_index=True, use_container_width=True, on_select="rerun",
                                        selection_mode="single-row", key=f"rw_tab_{nr}",
                                        height=min(560, 35 * (len(df) + 1) + 3))
                reihen = ereignis.selection.rows if ereignis is not None else []
                if reihen:
                    tk = tks[reihen[0]]
                    st.link_button(f"{tk}: Titelseite →", f"?seite=Titelseite&t={tk}")
        with st.expander("Logbuch · wann ein Titel in eine Stufe kam und wo er heute steht (Beobachtung, kein Urteil)"):
            lb = rw.logbuch(erg)
            if len(lb):
                st.dataframe(lb, hide_index=True, use_container_width=True)
            else:
                st.caption("Das Logbuch beginnt mit dem ersten Nachtlauf.")


def konferenz_zeigen():
    """Seite „Konferenzraum“ (09.11.2026): Tagesbefehl, Lagemeldungen, Akten mit Nadeln, Stab fragen, Kostenbuch."""
    import stab
    import konferenz_seite as ks
    k = stab.letzte()
    st.markdown(ks.kopf(k), unsafe_allow_html=True)
    if not stab.schluessel():
        with st.container(border=True):
            st.markdown(ks.ANLEITUNG)
            wert = st.text_input("API-Schlüssel", type="password", placeholder="sk-ant-…", key="stab_schluessel")
            if st.button("Schlüssel speichern", key="stab_speichern"):
                if wert.strip().startswith("sk-ant-"):
                    stab.schluessel_speichern(wert)
                    st.session_state["stab_probe"] = stab.probe()   # sofort prüfen, ob der Schlüssel wirklich geht
                    st.rerun()
                else:
                    st.error("Das sieht nicht wie ein Anthropic-Schlüssel aus (er beginnt mit sk-ant-).")
        return
    probe_ = st.session_state.pop("stab_probe", None)
    if probe_:
        (st.success if probe_[0] else st.error)(("✓ " if probe_[0] else "⚠ Der Schlüssel geht nicht: ") + probe_[1])
    laeuft = nachtlauf.konferenz_laeuft()
    pruef_, handy_, knopf_ = st.columns([3, 5, 3])
    with pruef_:
        if st.button("Verbindung prüfen", key="stab_pruefen", help="Kurzer Test, ob Schlüssel und Guthaben gehen (kostet unter 1 Cent)."):
            st.session_state["stab_probe"] = stab.probe()
            st.rerun()
    with handy_:
        import meldung
        with st.popover("📱 Meldung aufs Handy"):
            st.markdown(
                "Nach jedem Nachtlauf und jeder Konferenz kommt eine kurze Meldung aufs Handy – auch wenn etwas schiefging.\n\n"
                "1. Im App Store die kostenlose App **ntfy** laden.\n"
                "2. In ntfy auf **+** tippen und diesen Kanal eintragen (Server bleibt ntfy.sh):")
            st.code(meldung.kanal(), language=None)
            st.markdown("3. Hier auf „Testnachricht senden“ drücken – sie sollte sofort ankommen.\n\n"
                        "Der Kanalname ist zufällig – wer ihn nicht kennt, sieht nichts.")
            if st.button("Testnachricht senden", key="ntfy_test"):
                if meldung.senden("Test aus dem Konferenzraum – die Leitung steht.", "Invest Cockpit"):
                    st.success("Gesendet.")
                else:
                    st.error("Senden ging nicht – der Server erreicht ntfy.sh nicht.")
    with knopf_:
        if st.button("↻ Konferenz jetzt einberufen", use_container_width=True, disabled=laeuft,
                     help="Die fünf Strategen lesen den Stand des letzten Nachtlaufs (rund 2–5 Minuten, wenige Cent). "
                          "Läuft auf dem Server weiter, auch wenn du die Seite schließt."):
            nachtlauf.konferenz_starten()
            st.rerun()
        if laeuft:
            st.caption("Der Stab tagt gerade … (Seite mit ⌘ R neu laden)")
    prot, zeilen = nachtlauf.konferenz_protokoll()
    if prot:
        with st.expander(f"Protokoll des Stabs · gestartet {prot.get('start')}"
                         + (f" · fertig {prot['ende']}" if prot.get("ende") else " · läuft noch oder abgebrochen")
                         + (" · ⚠ Fehler" if prot.get("fehler") else "")):
            if prot.get("fehler"):
                st.error(prot["fehler"])
            st.code("\n".join(zeilen) or "noch keine Ausgabe", language=None)
    if not k:
        st.info("Noch keine Konferenz – sie läuft jede Nacht nach dem Nachtlauf, oder jetzt über den Knopf.")
    else:
        st.markdown(ks.befehl(k), unsafe_allow_html=True)
        sp = st.columns(2)
        for i, nr in enumerate((2, 3, 4, 5)):
            m = (k.get("meldungen") or {}).get(str(nr))
            if m:
                with sp[i % 2]:
                    st.markdown(ks.meldung(nr, m), unsafe_allow_html=True)
        st.markdown(gestaltung.seite("<h2 style='margin:0'>Akten · Hinweise je Titel, als Nadeln im Chart</h2>", oben=16,
                                     unten=0), unsafe_allow_html=True)
        akten = sorted(stab.akten(k).items(), key=lambda p: -len(p[1]))
        st.caption("Nummer der Nadel = Stratege: 1 Stratege · 2 Strömung · 3 Fundament · 4 Chart · 5 Risiko")
        for tk, eintraege in akten:
            with st.expander(f"**{tk}** · {len(eintraege)} Hinweis{'e' if len(eintraege) > 1 else ''}"):
                st.markdown(ks.akte_text(eintraege), unsafe_allow_html=True)
                ab = titel.abgelegt(tk)
                if ab:
                    st.markdown(titel.chartkarte(ab[0]["chart"], "Tag", "6 M", nadeln=ks.nadeln(eintraege)),
                                unsafe_allow_html=True)
                st.link_button(f"{tk}: Titelseite →", f"?seite=Titelseite&t={tk}")
    st.markdown(gestaltung.seite("<h2 style='margin:0'>Stab fragen</h2>", oben=16, unten=0), unsafe_allow_html=True)
    with st.form("stab_frage", clear_on_submit=True):
        text = st.text_area("Frage an den Stab", placeholder="z. B. Welche Branche kippt gerade, und welche Titel "
                                                            "hängen daran?", key="stab_text")
        tk_ = st.text_input("Titel (optional)", max_chars=12, key="stab_tk")
        los = st.form_submit_button("Fragen")
    if los and text.strip():
        with st.spinner("Der Stab berät …"):
            try:
                stab.frage(text.strip(), tk_.strip() or None)
            except Exception as e:  # noqa: BLE001
                st.error(str(e))
    for f in stab.fragen()[:10]:
        with st.container(border=True):
            st.markdown(f"**{f['zeit']}{' · ' + f['titel'] if f.get('titel') else ''} — {f['frage']}**")
            st.markdown(f["antwort"])


if ansicht == "Konferenzraum":
    try:
        _QUELLE["text"] = "Konferenz des Nachtlaufs"
        konferenz_zeigen()
    except Exception as e:  # noqa: BLE001
        _fehler(e)
elif ansicht == "Rückenwind":                  # seit 10.11.2026 mit der Übersicht: Lage, Rückenwind, Stellung, …
    _, n_, w_, k_ = st.columns([6, 2, 2, 2])
    with n_:
        tisch_knopf()
    with w_:
        watchlists_verwalten()
    with k_:
        konto_knopf()
    zeigen("uebersicht")
elif ticker:
    lauf = st.session_state.get("laufend")
    args = (ticker, True, lauf[1]) if lauf and lauf[0] == ticker else (ticker,)
    try:
        ab = titel.abgelegt(ticker) if len(args) == 1 else None   # vom Abendlauf fertig gebaut: sofort da
        if ab is not None:
            teile, alt = ab
            _QUELLE["text"] = _schrank_text(alt)
        else:
            t0 = time.time()
            with st.spinner("Lade und rechne …"):
                teile = _gebaut("titel", _codestand(), *args)
            frisch_ = time.time() - t0 > 0.5
            _QUELLE["text"] = "frisch gerechnet" if frisch_ else "aus dem Zwischenspeicher"
            if frisch_ and len(args) == 1:
                try:                             # beim nächsten Mal sofort da
                    titel.ablegen(ticker, teile)
                except Exception:  # noqa: BLE001
                    pass
        st.markdown(teile["oben"], unsafe_allow_html=True)
        ebene, aus, zonen_ansicht, gd_kurz = chart_knoepfe(ticker)
        st.markdown(titel.chartkarte(teile["chart"], ebene, aus, zonen_ansicht, gd_kurz), unsafe_allow_html=True)
        st.markdown(teile["unten"], unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)


st.caption(f"⏱ Seite in {time.time() - _T0:.1f} s" + (f" · {_QUELLE['text']}" if _QUELLE["text"] else ""))
