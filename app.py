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
/* Seitenwahl: alle Seiten in einer Reihe (Micky 16.11.2026) – auf schmalem Schirm seitlich schieben statt umbrechen */
.st-key-ansicht {{max-width:1392px; width:100%; box-sizing:border-box; margin:0 auto; padding:0 24px}}
.st-key-ansicht div[role="radiogroup"] {{flex-wrap:nowrap !important; overflow-x:auto; scrollbar-width:thin}}
.st-key-ansicht div[role="radiogroup"] label {{white-space:nowrap; flex:0 0 auto}}
</style>""", unsafe_allow_html=True)

ansicht_liste = ["Rückenwind", "Titelseite", "Analyse", "Depot", "Performance"]   # Rückenwind = Lagezentrum; Depot und
# Performance seit 16.11.2026; die Übersicht ist seit 10.11.2026 Teil von Rückenwind; der Konferenzraum wurde am 13.11.2026
# abgebaut, die Seite Setups am 21.11.2026 (Micky: Auswahl und Chart statt Setup-Listen)
ALTE_SEITEN = {"Übersicht": "Rückenwind", "Konferenzraum": "Rückenwind", "Setups": "Rückenwind"}   # alte Lesezeichen
# Startwerte einmal aus der Adresszeile übernehmen; danach führt Streamlit den Zustand selbst.
# (Ein index= aus der Adresszeile bei jedem Lauf legte das Bedienelement neu an – dann brauchte
# ein Wechsel zwei Klicks.)
if "ansicht" not in st.session_state:
    seite = ALTE_SEITEN.get(st.query_params.get("seite", "Rückenwind"), st.query_params.get("seite", "Rückenwind"))
    st.session_state.ansicht = seite if seite in ansicht_liste else "Rückenwind"
    st.session_state.titel_tk = st.query_params.get("t", "HWM")
if "titel_tk" not in st.session_state:          # offene Sitzungen von vor dem 16.11.2026
    st.session_state.titel_tk = (st.session_state.get("ticker") or st.query_params.get("t", "HWM")).strip().upper()
ansicht = st.radio("Ansicht", ansicht_liste, horizontal=True, key="ansicht")      # alle Seiten nebeneinander
if ansicht in ("Titelseite", "Analyse"):        # das Titelfeld gehört zur Titelseite (Micky 16.11.2026) – der gewählte
    if "ticker" not in st.session_state:        # Titel bleibt erhalten, während eine andere Seite offen ist
        st.session_state.ticker = st.session_state.titel_tk
    feld, _ = st.columns([2, 10])
    with feld:
        st.text_input("Titel", max_chars=12, key="ticker")
    st.session_state.titel_tk = st.session_state.ticker.strip().upper()
ticker = st.session_state.titel_tk
st.query_params["t"] = ticker
st.query_params["seite"] = ansicht


@st.cache_data(ttl=3600, show_spinner=False)
def _gebaut(name, codestand, *args):
    """Fertig gebaute Seite für eine Stunde im Speicher: ein Wechsel zwischen Seiten, Titeln oder Zeitebenen, die
    schon einmal offen waren, braucht dann keine Rechnung mehr. codestand ändert sich mit jeder Code-Änderung, damit
    nach einer Änderung nie eine alte Seite gezeigt wird."""
    import analyse_seite
    import zonenseite
    return {"uebersicht": uebersicht.seite_uebersicht, "titel": titel.seite_titel,
            "analyse": analyse_seite.seite_analyse, "zonen": zonenseite.seite_zonen}[name](*args)


def _fehler(e):
    st.markdown(f'<div style="max-width:1392px;margin:24px auto;padding:20px;background:{KARTE};'
                f'border:1px solid {RAND};border-radius:12px;color:{TEXT}">Die Seite ließ sich nicht bauen: '
                f'{e}</div>', unsafe_allow_html=True)


def _aktualisieren(tk):
    """Knopf „Kurse aktualisieren“ (als Rückruf, damit die Seite im selben Lauf schon mit den neuen Kursen gebaut
    wird): lädt den Titel samt laufender Tageskerze neu; gilt für diesen Titel, bis ein anderer gewählt wird."""
    st.session_state.laufend = (tk, time.time())




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
            # die Setup-Art (M/K) entfällt seit 16.11.2026: ein System, der Stopp folgt dem 10er/20er (Schritt 5)
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
                depot.setzen(tk, seite=seite_, stueck=int(stueck),
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


def depot_zeigen():
    """Seite Depot: Konto und Risiko, Depot-Hitze und Positionen; für die gewählte Position der Chart der Position
    (Einstieg, Anfangsstopp, Stopp jetzt am 10er/20er, Ende-Zeichen), „Nach dem Kauf“, TradingView und Deep Dive."""
    import depotleiste
    _, k_ = st.columns([10, 2])
    with k_:
        konto_knopf()
    st.markdown(gestaltung.seite(depotleiste.leiste(), oben=0, unten=12), unsafe_allow_html=True)
    pos = [p["ticker"] for p in depot.laden()["positionen"]]
    if not pos:
        return
    with st.container(key="depot_wahl"):
        tk = st.radio("Position", pos, horizontal=True, key="depot_tk")
    p = depot.position(tk)
    _, df = depotleiste._kurs(tk)                 # dieselben Kurse wie die Liste darüber
    if df is None or not len(df):
        st.warning(f"Keine Kurse für {tk}")
        return
    df.attrs["ticker"] = tk
    a_, b_, c_, _ = st.columns([2, 2, 2, 6])
    with a_:
        st.link_button("TradingView →", titel.tv_link(tk), use_container_width=True)
    with b_:
        st.link_button("Deep Dive →", f"?seite=Titelseite&t={tk}", use_container_width=True)
    with c_:
        position_knopf(tk)
    marken = depotleiste.positionsmarken(p, df)
    svg = chart.chart(df, "Tag", None, "6 M", gd_kurz=True, marken=marken)
    st.markdown(gestaltung.seite(gestaltung.karte(
        f'<div style="color:{TEXT_2};font-size:14px;margin-bottom:6px">Chart der Position · GD10 orange, GD20 rosa · '
        f'Einstieg blau, Anfangsstopp grau, Stopp jetzt rot, Ende-Zeichen gelb</div>' + svg, f"{tk} · Chart der Position")
        + depotleiste.titelkarte(tk, df, {}), oben=0, unten=12), unsafe_allow_html=True)


def performance_zeigen():
    """Seite Performance: Eingaben (Start und Ziel, Woche eintragen) und die Seite aus
    performance_seite (Kurve gegen Zielpfad, Hochrechnung auf ein Jahr, Unterwasser, Bilanz)."""
    import datetime as dt
    import performance
    import performance_seite
    d = performance.laden()
    a_, b_, _ = st.columns([2, 2, 8])
    with a_:
        with _fenster("⚙ Start und Ziel"):
            with st.form("perf_start"):
                start = st.number_input("Startkapital (€)", min_value=0.0, step=100.0, format="%.2f",
                                        value=float(d.get("start") or 0))
                ziel = st.number_input("Ziel-Rendite je Woche (%)", min_value=-100.0, step=1.0, format="%.2f",
                                       value=float((d.get("ziel_woche") or 0) * 100))
                if st.form_submit_button("Speichern", use_container_width=True):
                    d["start"], d["ziel_woche"] = start or None, ziel / 100
                    performance.speichern(d)
                    st.rerun()
    with b_:
        with _fenster("＋ Woche eintragen"):
            with st.form("perf_woche"):
                heute = dt.date.today()
                freitag = heute - dt.timedelta(days=(heute.weekday() - 4) % 7)
                tag = st.date_input("Freitag", value=freitag, format="DD.MM.YYYY")
                wert = st.number_input("Depotwert (€)", min_value=0.0, step=10.0, format="%.2f")
                ein = st.number_input("Einzahlung (+) bzw. Auszahlung (−) in dieser Woche (€)", step=10.0, format="%.2f")
                if st.form_submit_button("Speichern", use_container_width=True) and wert:
                    performance.woche_setzen(tag.isoformat(), wert, ein)
                    st.rerun()
            if d["wochen"]:
                with st.form("perf_weg"):
                    weg = st.selectbox("Woche löschen", [w["datum"] for w in reversed(d["wochen"])])
                    if st.form_submit_button("Löschen", use_container_width=True):
                        performance.woche_loeschen(weg)
                        st.rerun()
    st.markdown(performance_seite.seite_performance(), unsafe_allow_html=True)


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


















@st.cache_resource(show_spinner=False, max_entries=2)
def _lagekarte_html(codestand):
    """Lagekarte nach Sektoren (Seite Rückenwind) einmal je Code-/Datenstand."""
    return kartentisch.lagekarte_html()


def _lagekarte_zeigen():
    st.markdown(gestaltung.seite(_lagekarte_html(_codestand(mit_watchlists=True)), oben=12, unten=12),
                unsafe_allow_html=True)


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
            _lagekarte_zeigen()                         # direkt unter der Wetterkarte (Micky 12.11.2026)
            st.markdown(html["unten"], unsafe_allow_html=True)
        else:
            st.markdown(html, unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)


def rueckenwind_zeigen():
    """Seite „Rückenwind“, ② (KONZEPT_RUECKENWIND.md): Strömungskarte, Gruppen nach Geldfluss und die Titel in der
    Rangfolge des Rückenwinds (21.11.2026). Rechnet nicht – liest den Stand des Frühlaufs."""
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
        st.markdown(gestaltung.seite("<h3 style='margin:0'>Titel mit Rückenwind</h3>"
                                     f"<p style='color:{gestaltung.TEXT_2};font-size:14px;margin:6px 0 0'>Rangfolge: 🦈 "
                                     "RS-Linie am Hoch vor dem Kurs zuerst, dann die Richtung der RS-Linie, dann der Rang "
                                     "als Kraft. Alle Titel, nichts gefiltert; Zeile anklicken → Knopf zur Titelseite."
                                     "</p>", oben=8, unten=0), unsafe_allow_html=True)
        df, tks = rw.liste(erg)
        wahl = st.dataframe(df, hide_index=True, use_container_width=True, height=560, on_select="rerun",  # Layout
                            selection_mode="single-row", key="rw_liste")
        reihen = wahl.selection.rows if wahl is not None else []
        if reihen:
            tk = tks[reihen[0]]
            st.link_button(f"{tk}: Titelseite →", f"?seite=Titelseite&t={tk}")




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
            (st.success if probe_[0] else st.error)(("🟢 " if probe_[0] else "🔴 Der Schlüssel geht nicht: ") + probe_[1])
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
        st.markdown("**Handy:** Jeden Morgen kommen über die kostenlose App **ntfy** die heißen Titel (5 Long, 5 Short), "
                    "dazu Warnungen, wenn der Nachtlauf scheitert. "
                    "In ntfy auf **+** tippen und diesen Kanal eintragen (Server bleibt ntfy.sh):")
        st.code(meldung.kanal(), language=None)
        if st.button("Testmeldung senden", key="ntfy_test"):
            if meldung.senden("Test – die Leitung steht.", "Invest Cockpit", False, "Setups"):
                st.success("Gesendet.")
            else:
                st.error("Senden ging nicht – der Server erreicht ntfy.sh nicht.")


























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
        if not st.button("🎯 Einschätzung mit Recherche (Websuche, kostet API-Guthaben)", key=f"strategen_{tk}",
                         help="Der Stratege deutet Zustand und Tiefenanalyse aus dem Material der App: long, short, "
                              "abwarten (mit Auslöser und Tendenz) oder kein Schuss, höchstens drei Belege, Auslöser, "
                              "Widerlegung, Gegenzeuge. Dazu recherchiert er im Netz Unternehmen, letztes Quartal und "
                              "Wettbewerber (höchstens 8 Suchen) und schreibt das Fazit. Einmal je Titel und Kurstag."):
            return
        try:
            rw = titel._rueckenwind(tk) or {}
            mm = titel.maerkte() or {}
            su = erk.get("setup_info") or {}
            import analyse_seite
            import kartentisch
            with st.spinner("Recherche im Netz und Einschätzung (1–3 Minuten) …"):
                erg = strategen.rufen(tk, stand, e, float(df["Close"].iloc[-1]), atr=erk.get("atr"), rw=rw,
                                      markt=mm.get("auktion"), setup=kartentisch.NAME.get(su.get("reihe")),
                                      termin=((rw.get("zahlen") or {}).get("termin")), tiefe=analyse_seite.material(tk))
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
    zeigen("uebersicht")
    _, n_, w_ = st.columns([8, 2, 2])          # seit der Seite Setups (abgebaut 21.11.2026) hier: Tisch, Watchlists, Verbindungen
    with n_:
        tisch_knopf()
    with w_:
        watchlists_verwalten()
    verbindungen_zeigen()
elif ansicht == "Depot":                       # Depot (16.11.2026): Konto, Hitze, Positionen, Chart der Position
    try:
        depot_zeigen()
    except Exception as e:  # noqa: BLE001
        _fehler(e)
elif ansicht == "Performance":                 # Performance (16.11.2026): Kurve, Hochrechnung, Unterwasser, Bilanz
    try:
        performance_zeigen()
    except Exception as e:  # noqa: BLE001
        _fehler(e)
elif ansicht == "Analyse" and ticker:         # Tiefenanalyse (Micky 21.11.2026, aus der App Titel-Analyse)
    datenstand_zeigen()
    try:
        t0 = time.time()
        with st.spinner("Lade und rechne …"):
            st.markdown(_gebaut("analyse", _codestand(), ticker), unsafe_allow_html=True)
        _QUELLE["text"] = "frisch gerechnet" if time.time() - t0 > 0.5 else "aus dem Zwischenspeicher"
        ab = titel.abgelegt(ticker)              # der Stratege braucht den Zustand der Titelseite
        teile = ab[0] if ab is not None else _gebaut("titel", _codestand(), ticker)
        st.markdown(gestaltung.seite("<h2 style='margin:0;font-size:20px;font-weight:600'>Einschätzung</h2>", oben=8,
                                     unten=0), unsafe_allow_html=True)
        strategen_call(ticker, teile)
    except Exception as e:  # noqa: BLE001
        _fehler(e)
elif ticker:                                  # Titelseite des schlanken Cockpits (Micky 21.11.2026): Zonen, Phasen
    datenstand_zeigen()                       # und Strömung auf drei Ebenen, darunter der Zonenchart
    lauf = st.session_state.get("laufend")
    args = (ticker, True, lauf[1]) if lauf and lauf[0] == ticker else (ticker,)
    try:
        t0 = time.time()
        with st.spinner("Lade und rechne …"):
            teile = _gebaut("zonen", _codestand(), *args)
        _QUELLE["text"] = "frisch gerechnet" if time.time() - t0 > 0.5 else "aus dem Zwischenspeicher"
        st.markdown(teile["kopf"], unsafe_allow_html=True)
        import zonenchart
        import zonenseite
        k0, k1, k2, k3 = st.columns([4, 2, 2, 2])
        with k0:
            ebene = st.radio("Ebene", ["Woche", "Tag", "Stunde"], index=1, horizontal=True, key="zonen_ebene")
        with k1:
            st.button("↻ Kurse aktualisieren", use_container_width=True, on_click=_aktualisieren, args=(ticker,))
        with k2:
            st.link_button("TradingView ↗", titel.tv_link(ticker), use_container_width=True)
        with k3:
            watchlist_knopf(ticker)
        e_ = teile["r"]["ebenen"][ebene]
        g0, g3 = st.columns([1, 1])
        g1, g2, g4, _ = st.columns([2, 2, 2, 4])
        with g0:                                 # Durchschnitte nach Wahl (Micky 21.11.2026), in Kerzen der Ebene
            gd = st.pills("Durchschnitte", list(zonenchart.GD_WAHL), selection_mode="multi", default=[],
                          format_func=lambda g: f"GD{g}", key="zonen_gd") or []
        with g3:                                 # POC-Linien der Zonen nach Wahl (Micky 21.11.2026)
            poc_wahl = st.pills("POC-Linien", list(zonenchart.LINIEN_WAHL), selection_mode="multi", default=[],
                                format_func=zonenchart.LINIEN_WAHL.get, key="zonen_poc") or []
        anker = zonenseite.anker_laden(ticker, ebene)
        hilfe = ("Nummer aus dem Hinweis über der Kerze (1 = letzte Kerze); 0 löscht den Anker. Sind beide gesetzt, ist "
                 "der Raum dazwischen die Zange.",) * 2 + ("Nummer aus dem Hinweis über der Kerze (1 = letzte Kerze): Zeit- "
                 "und Volumenprofil ab dieser Kerze. 0 = automatisch ab Beginn des Impulses.",)
        for k, spalte in enumerate((g1, g2, g4)):   # eigene Anker: Balkennummer von rechts, gespeichert als Zeitpunkt
            with spalte:
                nr_jetzt = zonenchart.nummer(e_["df"], anker[k]) if e_ is not None and anker[k] is not None else 0
                nr = st.number_input(f"AVWAP {k + 1} · Balken-Nr." if k < zonenseite.PROFIL_PLATZ else "Profil · Balken-Nr.",
                                     min_value=0, step=1, value=int(nr_jetzt), key=f"zonen_anker_{ticker}_{ebene}_{k}",
                                     help=hilfe[k])
                if e_ is not None and int(nr) != int(nr_jetzt):
                    zonenseite.anker_setzen(ticker, ebene, k, zonenchart.zeitpunkt(e_["df"], nr) if nr else None)
                    anker = zonenseite.anker_laden(ticker, ebene)
        st.markdown(gestaltung.seite(gestaltung.karte(zonenseite.chart(teile["r"], ebene, sorted(gd), anker[:zonenseite.PROFIL_PLATZ],
                                                                       set(poc_wahl), anker[zonenseite.PROFIL_PLATZ])
                                                      + teile["legende"]), oben=0, unten=12),
                    unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)


st.caption(f"⏱ Seite in {time.time() - _T0:.1f} s" + (f" · {_QUELLE['text']}" if _QUELLE["text"] else ""))
