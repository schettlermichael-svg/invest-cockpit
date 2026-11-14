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
[class*="st-key-kartentisch"] div[data-testid="stHorizontalBlock"] {{align-items:flex-start}}
[class*="st-key-kartentisch"] div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] {{align-items:center}}
[class*="st-key-kartentisch"] [data-testid="stExpander"] {{max-width:1392px; margin:0 auto; padding:0 24px}}
[class*="st-key-rueckenwind"] [data-testid="stExpander"], [class*="st-key-rueckenwind"] [data-testid="stHorizontalBlock"],
[class*="st-key-rueckenwind"] [data-testid="stRadio"] {{max-width:1392px; margin:0 auto; padding:0 24px}}
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{background:{KARTE}; color:{TEXT};
  border:1px solid {RAND}; border-radius:10px; min-height:44px; font-size:16px}}
.stTextInput label, .stRadio label p {{color:{TEXT_2} !important; font-size:14px}}
div[role="radiogroup"] label {{min-height:44px; padding:0 14px; border:1px solid {RAND}; border-radius:10px;
  background:{KARTE}; margin-right:8px}}
div[role="radiogroup"] label:has(input:checked) {{border-color:{BLAU}}}
</style>""", unsafe_allow_html=True)

ansicht_liste = ["Rückenwind", "Setups", "Titelseite"]   # Rückenwind = Lagezentrum, Setups = Aufklärung und Filter
# (12.11.2026); die Übersicht ist seit 10.11.2026 Teil von Rückenwind; der Konferenzraum wurde am 13.11.2026 abgebaut
ALTE_SEITEN = {"Übersicht": "Rückenwind", "Konferenzraum": "Setups"}                       # alte Lesezeichen
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
    avwap_wahl = None
    if ebene == "Tag":                           # AVWAP nach Shannon (10.11.2026): mehrere Anker, Zange = Hoch + Tief
        zr = (kartentisch.eintrag_von(tk) or {}).get("reihe") == "zahlen"   # Zahlen-Reaktion: Zahlentag vorgewählt
        avwap_wahl = st.pills("AVWAP-Anker", list(chart.AVWAP_KURZ), selection_mode="multi",
                              default=chart.AVWAP_START + (["ereignis"] if zr else []), format_func=chart.AVWAP_KURZ.get,
                              key="avwap_anker_z2" if zr else "avwap_anker2",     # neue Anker 14.11.2026
                              help="Anker nach Brian Shannon, aus der Struktur der Wochenkerzen (nie aus dem Kalender). "
                                   "Hoch des Rückgangs: der Gipfel, von dem die ganze Korrektur ausging. Letztes Hoch: das "
                                   "jüngste Wochen-Schwunghoch, das der Kurs nicht überschritten hat (steht er über allen: "
                                   "der Ausbruchspunkt). Tief der Bewegung: das tiefste Tief seit dem letzten Hoch – mit ihm "
                                   "Shannons Zange. Ereignis: der jüngere von Zahlentag (Reaktion ab 3 %) und Lücke ab 4 % "
                                   "mit doppeltem Volumen.")
    return ebene, aus, zonen_ansicht, gd_kurz, avwap_wahl


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
            systeme_ = ["Base-Ausbruch (Stopp nach Minervini)", "Momentum · Flagge · Sprung · Zahlen-Reaktion (GD10/GD20)"]
            system_ = st.radio("Setup-Art (bestimmt Stopp nachziehen und Ausstieg)", systeme_, horizontal=True,
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
                depot.setzen(tk, seite=seite_, system="K" if system_ == systeme_[1] else "M", stueck=int(stueck),
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
    """Kartentisch (Ränge, alle Setups, Lage) mit den vorhandenen Kursen neu rechnen."""
    laeuft, text = nachtlauf.tisch_lauf_stand()
    if st.session_state.get("tisch_lief") and not laeuft:   # gerade fertig geworden: ganze Seite neu zeigen
        st.session_state.tisch_lief = False
        st.rerun()
    st.session_state.tisch_lief = laeuft
    st.button("↻ Kartentisch neu rechnen", use_container_width=True, disabled=laeuft, on_click=_tisch_starten,
              help="Rechnet RS-Rang, Führer-Rang, den Kartentisch mit allen Setups und die Lage neu – "
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
    """Jüngste Änderungszeit der Programmdateien und der Datendateien, von denen die Seiten abhängen."""
    hier = os.path.dirname(os.path.abspath(__file__))
    code = max(os.path.getmtime(os.path.join(hier, d, f)) for d in ("kern", "oberflaeche")
               for f in os.listdir(os.path.join(hier, d)) if f.endswith(".py"))
    daten = [os.path.join(hier, "daten", "tv", "revier.csv")]
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
        st.markdown(kartentisch.karte_html(x, kartentisch._marken(x) if liste else "", tk), unsafe_allow_html=True)
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
    df = pd.DataFrame([{" ": "", "Titel": z["tk"], "Zustand": z.get("Zustand", ""), "Liste": z.get("Stab", ""),
                        "Setup": z["Setup"], "Befund": z["Befund"],
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


def _kartentisch_zeigen(rollen=None, ohne=()):
    """Teile des Kartentischs: rollen = nur diese (z. B. {"lagekarte"}), ohne = diese nicht; Abschnitte (Reihen,
    Watchlist) haben die Rolle „reihe“."""
    def html(h):
        st.markdown(gestaltung.seite(h, oben=12, unten=12), unsafe_allow_html=True)
    try:
        huelle = st.container(key="kartentisch_" + "_".join(sorted(rollen or ())) + "_ohne_" + "_".join(sorted(ohne)))
    except TypeError:                               # ältere Streamlit-Version ohne key
        huelle = st.container()
    with huelle:
        for nr, teil in enumerate(_tischplan(_codestand(mit_watchlists=True))):
            rolle = teil.get("rolle", "reihe")
            if (rollen is not None and rolle not in rollen) or rolle in ohne:
                continue
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
    """Hinweis am Seitenende (10.11.2026: vorher zusätzlich ein langer Hinweis ganz oben nach jedem Update)."""
    if not alt:
        return "aus dem Schrank"
    return ("aus dem Schrank – vor der letzten Programmänderung gebaut; die Daten sind aktuell, die neue Ansicht "
            "kommt im Hintergrund")


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
            try:                                     # ein Fehler im Rückenwind lässt Lagekarte und Truppe stehen
                rueckenwind_zeigen()
            except Exception as e:  # noqa: BLE001
                _fehler(e)
            _kartentisch_zeigen(rollen={"lagekarte"})   # direkt unter der Wetterkarte (Micky 12.11.2026)
            st.markdown(html["unten"], unsafe_allow_html=True)
        else:
            st.markdown(html, unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)


def rueckenwind_zeigen():
    """Seite „Rückenwind“, ② (KONZEPT_RUECKENWIND.md): Strömungskarte und Gruppen nach Geldfluss; die Titel-Listen stehen
    seit 12.11.2026 auf der Seite Setups. Rechnet nicht – liest den Stand des Frühlaufs."""
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


def rueckenwind_titel_zeigen():
    """Seite Setups, ③ Rückenwind je Titel (bis 12.11.2026 auf der Seite Rückenwind): dreifacher Rückenwind,
    Titel nach Stufe, Logbuch."""
    import rueckenwind as rw_kern
    import rueckenwind_seite as rw
    erg = rw_kern.laden()
    if not erg:
        return
    with st.container(key="rueckenwind_titel"):
        st.markdown(gestaltung.seite("<h3 style='margin:0'>Dreifacher Rückenwind · Kurs, Geld und Zahlen grün</h3>",
                                     oben=16, unten=0), unsafe_allow_html=True)
        st.markdown(rw.dreifach(erg), unsafe_allow_html=True)
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
                                        height=min(560, 35 * (len(df) + 1) + 3),
                                        column_config={"Kreislauf": st.column_config.LineChartColumn(
                                            "Kreislauf (1 Jahr)", help="Wochenschlüsse eines Jahres; die Farben der "
                                            "Phasen zeigt die Titelseite")})
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


ANLEITUNG_SCHLUESSEL = """**So legst du den API-Schlüssel an (einmalig, etwa 5 Minuten):**

1. Öffne **console.anthropic.com** und melde dich an (oder lege dort ein Konto an).
2. Unter **Billing** Guthaben aufladen.
3. Unter **Limits** ein Monatslimit setzen, z. B. 50 $ (zweite Sicherung neben dem Deckel der App).
4. Unter **API Keys** → **Create Key**, Name z. B. „Invest Cockpit“. Den Schlüssel (beginnt mit `sk-ant-`) kopieren –
   er wird nur einmal angezeigt.
5. Hier einfügen und speichern. Er liegt dann nur auf dem Server (nicht in GitHub)."""


def verbindungen_zeigen():
    """⚙ Verbindungen (13.11.2026, aus dem abgebauten Konferenzraum): API-Schlüssel für den künftigen Strategen-Call,
    Verbindungstest und Kostenbuch, Kanal fürs Handy (ntfy)."""
    import meldung
    import modell
    with st.expander("⚙ Verbindungen · API-Schlüssel und Handy"):
        probe_ = st.session_state.pop("modell_probe", None)
        if probe_:
            (st.success if probe_[0] else st.error)(("✓ " if probe_[0] else "⚠ Der Schlüssel geht nicht: ") + probe_[1])
        if not modell.schluessel():
            st.markdown(ANLEITUNG_SCHLUESSEL)
            wert = st.text_input("API-Schlüssel", type="password", placeholder="sk-ant-…", key="modell_schluessel")
            if st.button("Schlüssel speichern", key="modell_speichern"):
                if wert.strip().startswith("sk-ant-"):
                    modell.schluessel_speichern(wert)
                    st.session_state["modell_probe"] = modell.probe()
                    st.rerun()
                else:
                    st.error("Das sieht nicht wie ein Anthropic-Schlüssel aus (er beginnt mit sk-ant-).")
        else:
            ko = modell.kosten()
            st.caption(f"API-Schlüssel liegt auf dem Server · Kosten in diesem Monat {modell._zahl_de(ko['usd'])} $ "
                       f"von {modell._zahl_de(modell.DECKEL_USD, 0)} $ · {ko['aufrufe']} Aufrufe")
            if st.button("Verbindung prüfen", key="modell_pruefen", help="Kurzer Test, ob Schlüssel und Guthaben gehen "
                                                                        "(kostet unter 1 Cent)."):
                st.session_state["modell_probe"] = modell.probe()
                st.rerun()
        st.markdown("**Handy:** Der Frühlauf meldet sich über die kostenlose App **ntfy** (Stand der Lage, Warnungen). "
                    "In ntfy auf **+** tippen und diesen Kanal eintragen (Server bleibt ntfy.sh):")
        st.code(meldung.kanal(), language=None)
        if st.button("Testmeldung senden", key="ntfy_test"):
            if meldung.senden("Test – die Leitung steht.", "Invest Cockpit", False, "Rückenwind"):
                st.success("Gesendet.")
            else:
                st.error("Senden ging nicht – der Server erreicht ntfy.sh nicht.")


def setups_zeigen():
    """Seite „Setups“ (12.11.2026, Micky): Aufklärung und Filter – ① Einsatzbereit (Trichter, Liste), ② Stellung
    (grüne Setups, Reihen, Watchlist mit Marke 🎯), ③ Rückenwind je Titel, ④ Termine."""
    st.markdown(gestaltung.seite(
        '<h1 style="margin:0;font-size:32px;font-weight:600">Setups · Aufklärung und Filter</h1>'
        + gestaltung.sprungleiste(gestaltung.STATIONEN_SETUPS), oben=12, unten=0), unsafe_allow_html=True)
    _kartentisch_zeigen(ohne={"lagekarte", "termine"})
    st.markdown(gestaltung.seite(gestaltung.station("titel"), oben=16, unten=0), unsafe_allow_html=True)
    try:
        rueckenwind_titel_zeigen()
    except Exception as e:  # noqa: BLE001
        _fehler(e)
    _kartentisch_zeigen(rollen={"termine"})
    chartpruefer_zeigen()
    verbindungen_zeigen()


def _pruefer_starten():
    import chartpruefer
    if chartpruefer.starten():
        st.toast("Chart-Prüfer läuft – etwa 150 Charts, die Seite zeigt den Fortschritt")


def _chartpruefer_zeigen():
    """Chart-Prüfer (14.11.2026): Prüfstand, kein Erkenner – eine Stichprobe von Charts gegen die Regeln der Meister;
    gemeldet wird nur, wo der Prüfer der App widerspricht."""
    import chartpruefer
    from html import escape as esc
    laeuft, p = chartpruefer.stand()
    with st.expander("🔎 Chart-Prüfer · Zonen, Pivots und Anker gegen die Regeln der Meister", expanded=laeuft):
        st.caption("Die Erkennung bleibt Code (feste Regeln, immer dasselbe Ergebnis). Der Prüfer schaut sich etwa "
                   f"{chartpruefer.STICHPROBE} Charts mit dem Auge von O'Neil, Minervini, Kullamägi, Shannon und Dalton "
                   "an – die ganze Kette unserer drei Bilder: Zone, Zeichen, Zustand, Anker, dazu 20 Gruppen – und meldet Widersprüche. Echte Regelfehler kommen in den Code, strittige Fälle entscheidest du. "
                   f"Etwa {chartpruefer.STICHPROBE * chartpruefer.KOSTEN_JE_CHART:.0f} \\$ je Lauf (Monatsdeckel 50 \\$). "
                   "Einen einzelnen Titel prüfst du mit dem Knopf unter dem Chart der Titelseite.")
        st.button("Prüflauf starten", disabled=laeuft, on_click=_pruefer_starten, key="pruefer_start")
        if laeuft:
            st.caption(f"Läuft seit {p['start'][-5:]} Uhr · {p.get('fertig', 0)} von {p.get('n')} Charts geprüft")
        elif p and p.get("ende"):
            st.caption(f"Letzter Lauf {p['start']}–{p['ende'][-5:]} · {p.get('fertig')} Charts · "
                       f"{str(p.get('kosten', '')).replace('.', ',')} \\$")
        b = chartpruefer.letzter_bericht()
        if not b or not b.get("titel"):
            return
        alle = [(r["tk"], r.get("gruppe", ""), w) for r in b["titel"] for w in r.get("widersprueche") or []]
        fehler = [r for r in b["titel"] if r.get("fehler")]
        je = {}
        for tk, g, w in alle:
            je.setdefault(w["element"], []).append((tk, g, w))
        st.markdown(f"**Bericht {b['stand']}** · {len(b['titel'])} Charts · {len(alle)} Widersprüche "
                    f"({sum(1 for *_, w in alle if w['gewicht'] == 'sicher')} sicher) · ohne Widerspruch: "
                    f"{sum(1 for r in b['titel'] if not r.get('widersprueche') and not r.get('fehler'))}"
                    + (f" · {len(fehler)} nicht prüfbar" if fehler else ""))
        for element in sorted(je, key=lambda k: -len(je[k])):
            zeilen = "".join(
                f'<tr><td style="padding:3px 8px">'
                + (esc(tk) if ":" in tk else f'<a href="?seite=Titelseite&t={esc(tk)}" target="_blank">{esc(tk)}</a>')
                + (
                f'<br><span style="font-size:11px;opacity:.7">{esc(g)}</span></td>'
                f'<td style="padding:3px 8px">{"●" if w["gewicht"] == "sicher" else "○"} {esc(w["befund"])}</td>'
                f'<td style="padding:3px 8px">{esc(w["richtig"])}</td>'
                f'<td style="padding:3px 8px;font-size:12px;opacity:.8">{esc(w["regel"])}</td></tr>')
                for tk, g, w in je[element])
            st.markdown(f'<details><summary style="cursor:pointer"><b>{esc(element)}</b> · {len(je[element])} '
                        f'({sum(1 for *_, w in je[element] if w["gewicht"] == "sicher")} sicher)</summary>'
                        f'<table style="font-size:13px;border-collapse:collapse"><tr><th>Titel</th><th>Befund</th>'
                        f'<th>Richtig wäre</th><th>Regel</th></tr>{zeilen}</table></details>',
                        unsafe_allow_html=True)


chartpruefer_zeigen = _FRAGMENT(run_every=30)(_chartpruefer_zeigen) if _FRAGMENT else _chartpruefer_zeigen


def chart_pruefen(tk, teile):
    """Knopf „🔎 Chart prüfen lassen“ unter dem Chart (14.11.2026): der Chart-Prüfer urteilt über diesen einen Titel –
    Zone, Zeichen, Zustand, Anker nach den Regeln der Meister; einmal je Titel und Kurstag, danach aus dem Speicher."""
    import chartpruefer
    import zustandsbild
    df = (teile.get("chart") or {}).get("df")
    if df is None:
        return
    stand = f"{df.index[-1]:%Y-%m-%d}"
    r = chartpruefer.einzeln_gespeichert(tk, stand)
    if r is None:
        if not st.button("🔎 Chart prüfen lassen", key=f"pruefen_{tk}",
                         help="Der Chart-Prüfer schaut sich diesen Chart mit dem Auge der Meister an (O'Neil, Minervini, "
                              "Kullamägi, Weinstein, Wyckoff, Shannon, Dalton) und meldet, wo er Zone, Zeichen, "
                              "Zustand oder Anker der App widerspricht. Etwa 5 Cent, einmal je Titel und Kurstag."):
            return
        try:
            with st.spinner("Der Chart-Prüfer schaut hin …"):
                r = chartpruefer.einzeln(tk, stand, teile.get("chart"))
        except Exception as x:  # noqa: BLE001
            st.error(f"Chart-Prüfer ging nicht: {x}")
            return
    st.markdown(zustandsbild.pruef_karte(r), unsafe_allow_html=True)


def strategen_call(tk, teile):
    """Knopf „Strategen-Call“ unter dem Kreislaufbild (Micky 13.11.2026): auf Wunsch die Deutung eines Strategen aus
    dem Material der App; einmal je Titel und Kurstag, danach aus dem Speicher."""
    import strategen
    import zustandsbild
    z = teile.get("chart") or {}
    erk, df = z.get("erk") or {}, z.get("df")
    e = erk.get("auktion")
    if e is None or df is None:
        return
    stand = f"{df.index[-1]:%Y-%m-%d}"
    erg = strategen.gespeichert(tk, stand)
    if erg is None:
        if not st.button("🎯 Strategen-Call", key=f"strategen_{tk}",
                         help="Der Stratege deutet den Zustand aus dem Material der App (kein Online-Gang). Kostet "
                              "einige Cent, einmal je Titel und Kurstag."):
            return
        try:
            rw = titel._rueckenwind(tk) or {}
            mm = titel.maerkte() or {}
            su = erk.get("setup_info") or {}
            import kartentisch
            with st.spinner("Der Stratege deutet …"):
                erg = strategen.rufen(tk, stand, e, float(df["Close"].iloc[-1]), atr=erk.get("atr"), rw=rw,
                                      markt=mm.get("auktion"), setup=kartentisch.NAME.get(su.get("reihe")),
                                      termin=((rw.get("zahlen") or {}).get("termin")))
        except Exception as x:  # noqa: BLE001
            st.error(f"Strategen-Call ging nicht: {x}")
            return
    st.markdown(zustandsbild.strategen_karte(erg), unsafe_allow_html=True)


def datenstand_zeigen():
    """Datenstand-Wache (12.11.2026): eine Zeile oben – mit welchem Handelstag die App rechnet; rot, wenn Teile der
    App verschiedene Tage haben."""
    try:
        ampel, text = nachtlauf.datenstand_zeile()
    except Exception as e:  # noqa: BLE001
        ampel, text = "grau", f"Datenstand nicht lesbar: {e}"
    farbe = {"grün": gestaltung.GRUEN, "rot": gestaltung.ROT, "gelb": gestaltung.GELB}.get(ampel, gestaltung.GRAU)
    hilfe = "Geprüft wird, mit welchem Handelstag jeder Teil rechnet: " + " · ".join(
        f"{k} ({v})" for k, v in nachtlauf.QUELLEN_DATENSTAND.items())
    st.markdown(f'<div title="{gestaltung.t(hilfe)}" style="font-size:13px;color:{TEXT_2};margin:2px 0 6px">'
                f'<span style="color:{farbe}">●</span> {text} <span style="color:{gestaltung.TEXT_3}">ⓘ</span></div>',
                unsafe_allow_html=True)
    try:                                         # Wachen des Frühlaufs (12.11.2026): nur sichtbar, wenn sie etwas melden
        import wachen
        w = wachen.laden()
    except Exception:  # noqa: BLE001
        w = None
    if w and w.get("zeichen"):
        punkt_ = {"rot": "🔴", "gelb": "🟡"}
        with st.expander(f"{punkt_.get(w['ampel'], '⚪')} Wachen vom {w['stand'][8:10]}.{w['stand'][5:7]}. · "
                         f"{len(w['zeichen'])} Meldungen"):
            st.caption("Jeden Morgen geprüft: Gleichlauf von Chart und Kartentisch · Plausibilität der Setups · "
                       "Gegenprobe von 10 Titeln mit TradingView. "
                       "Rot = Fehler der App, gelb = beachten, grau = stiller Hinweis (färbt nichts).")
            for a_, t_ in w["zeichen"]:
                st.markdown(f"{punkt_.get(a_, '⚪')} {gestaltung.t(t_)}")


if ansicht == "Rückenwind":                  # Lagezentrum: Lage, Strömung mit Lagekarte nach Sektoren, Truppe
    _, k_ = st.columns([10, 2])
    with k_:
        konto_knopf()
    zeigen("uebersicht")
elif ansicht == "Setups":                      # Aufklärung und Filter (12.11.2026)
    datenstand_zeigen()
    _, n_, w_ = st.columns([8, 2, 2])
    with n_:
        tisch_knopf()
    with w_:
        watchlists_verwalten()
    try:
        _QUELLE["text"] = "Kartentisch des Frühlaufs"
        setups_zeigen()
    except Exception as e:  # noqa: BLE001
        _fehler(e)
elif ticker:
    datenstand_zeigen()
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
        strategen_call(ticker, teile)
        ebene, aus, zonen_ansicht, gd_kurz, avwap_wahl = chart_knoepfe(ticker)
        st.markdown(titel.chartkarte(teile["chart"], ebene, aus, zonen_ansicht, gd_kurz, avwap_wahl=avwap_wahl),
                    unsafe_allow_html=True)
        chart_pruefen(ticker, teile)
        st.markdown(teile["unten"], unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)


st.caption(f"⏱ Seite in {time.time() - _T0:.1f} s" + (f" · {_QUELLE['text']}" if _QUELLE["text"] else ""))
