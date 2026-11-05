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

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "oberflaeche"))
sys.path.insert(0, os.path.join(HIER, "kern"))

from gestaltung import BLAU, KARTE, RAND, SEITE, TEXT, TEXT_2  # noqa: E402
import chart  # noqa: E402
import titel  # noqa: E402
import uebersicht  # noqa: E402
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
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {{background:{KARTE}; color:{TEXT};
  border:1px solid {RAND}; border-radius:10px; min-height:44px; font-size:16px}}
.stTextInput label, .stRadio label p {{color:{TEXT_2} !important; font-size:14px}}
div[role="radiogroup"] label {{min-height:44px; padding:0 14px; border:1px solid {RAND}; border-radius:10px;
  background:{KARTE}; margin-right:8px}}
div[role="radiogroup"] label:has(input:checked) {{border-color:{BLAU}}}
</style>""", unsafe_allow_html=True)

ansicht_liste = ["Übersicht", "Titelseite"]
# Startwerte einmal aus der Adresszeile übernehmen; danach führt Streamlit den Zustand selbst.
# (Ein index= aus der Adresszeile bei jedem Lauf legte das Bedienelement neu an – dann brauchte
# ein Wechsel zwei Klicks.)
if "ansicht" not in st.session_state:
    seite = st.query_params.get("seite", "Übersicht")
    st.session_state.ansicht = seite if seite in ansicht_liste else "Übersicht"
    st.session_state.ticker = st.query_params.get("t", "HWM")
spalte0, spalte1, _ = st.columns([3, 2, 7])
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
    """Knöpfe direkt über dem Chart: Zeitebene, Ausschnitt, GD10/GD20 (nur Tag), Kurse aktualisieren, TradingView,
    Watchlist."""
    k0, k1, k2, k3, k4, k5, k6 = st.columns([2, 3, 2, 2, 2, 2, 2])
    with k0:
        ebene = st.radio("Zeitebene", ["Tag", "Woche"], horizontal=True, key="ebene")
    with k1:
        wahl = list(chart.AUSSCHNITT[ebene])
        aus = st.radio("Ausschnitt", wahl, horizontal=True, key=f"ausschnitt_{ebene}",
                       index=wahl.index(chart.AUSSCHNITT_START[ebene]))
    kurz = ()
    with k2:
        if ebene == "Tag":
            a, b = st.columns(2)
            with a:
                g10 = st.checkbox("GD10", key="gd10")
            with b:
                g20 = st.checkbox("GD20", key="gd20")
            kurz = tuple(k for k, an in ((10, g10), (20, g20)) if an)
    with k3:
        st.button("↻ Kurse aktualisieren", use_container_width=True, on_click=_aktualisieren, args=(tk,))
    with k4:
        st.link_button("TradingView ↗", titel.tv_link(tk), use_container_width=True)
    with k5:
        watchlist_knopf(tk)
    with k6:
        position_knopf(tk)
    return ebene, aus, kurz


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
                depot.setzen(tk, seite=seite_, stueck=int(stueck), einstieg=einstieg or None, stopp=stopp or None,
                             ko={"schwelle": schwelle, "bezug": bezug} if schwelle and bezug else None)
                st.rerun()
        if p and st.button("Position schließen", key=f"zu_{tk}", use_container_width=True):
            depot.schliessen(tk)
            st.rerun()


def watchlists_verwalten():
    """Übersicht: alle Watchlists pflegen – Liste wählen, Ticker einfügen, Titel herausnehmen, neue Liste anlegen.
    (Einzelne Titel auch über „☆ Watchlist“ auf der Titelseite.) Herausgenommen aus der letzten Liste = gelöscht."""
    w = watchlists.laden()
    with _fenster(f"◆ Watchlists ({len(watchlists.alle())})"):
        namen = list(w) or [watchlists.STANDARD]
        name = st.selectbox("Liste", namen, key="wl_verw_liste")
        drin = w.get(name, [])
        st.caption(f"{len(drin)} Titel: " + ", ".join(drin[:60]) + (" …" if len(drin) > 60 else ""))
        with st.form("wl_verw_neu", clear_on_submit=True):
            text = st.text_area("Ticker hinzufügen", height=70, placeholder="z. B. NVDA, ANET, XETR:RHM – auch ganze Listen "
                                "aus Finviz oder TradingView einfügen")
            if st.form_submit_button("Hinzufügen", use_container_width=True):
                st.toast(f"{watchlists.einfuegen(text, name)} Titel neu in „{name}“")
                st.rerun()
        if drin:
            with st.form("wl_verw_weg"):
                weg = st.multiselect("Titel herausnehmen", drin)
                if st.form_submit_button("Herausnehmen", use_container_width=True) and weg:
                    for tk in weg:
                        watchlists.setzen(tk, name, False)
                    st.toast(f"{len(weg)} Titel aus „{name}“ genommen")
                    st.rerun()
        with st.form("wl_verw_liste_neu", clear_on_submit=True):
            neu = st.text_input("Neue Liste anlegen", placeholder="Name")
            erster = st.text_input("erster Titel", placeholder="Ticker")
            if st.form_submit_button("Anlegen", use_container_width=True) and neu.strip() and erster.strip():
                watchlists.einfuegen(erster, neu.strip())
                st.rerun()


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


def _watch_setzen(tk, name, schluessel):
    watchlists.setzen(tk, name, st.session_state[schluessel])


def _watch_neu(tk, schluessel):
    name = st.session_state[schluessel].strip()
    if name:
        watchlists.setzen(tk, name, True)
        st.session_state[schluessel] = ""


def watchlist_knopf(tk):
    """„☆ Watchlist“ / „★ in n Listen“: je Liste ein Haken, darunter eine neue Liste. Herausnehmen aus der letzten
    Liste löscht den Titel aus dem Abendlauf (außer er gehört zum Revier)."""
    drin = watchlists.listen_von(tk)
    with _fenster(f"★ Watchlist ({len(drin)})" if drin else "☆ Watchlist"):
        for name in list(watchlists.laden()) or [watchlists.STANDARD]:
            sl = f"wl_{tk}_{name}"
            st.session_state[sl] = name in drin
            st.checkbox(name, key=sl, on_change=_watch_setzen, args=(tk, name, sl))
        st.text_input("neue Liste", key=f"wl_neu_{tk}", placeholder="Name, Enter", on_change=_watch_neu,
                      args=(tk, f"wl_neu_{tk}"))
        with st.form(f"wl_text_{tk}", clear_on_submit=True):
            text = st.text_area("Ticker einfügen (Finviz, SEPA-Scanner, TradingView)", height=80,
                                placeholder="z. B. NVDA, ANET, XETR:RHM")
            ziel = st.selectbox("in Liste", list(watchlists.laden()) or [watchlists.STANDARD])
            if st.form_submit_button("Hinzufügen", use_container_width=True):
                st.toast(f"{watchlists.einfuegen(text, ziel)} Titel neu in „{ziel}“")


def _codestand():
    """Jüngste Änderungszeit der Programmdateien und der von Claude gelieferten Datendateien."""
    hier = os.path.dirname(os.path.abspath(__file__))
    code = max(os.path.getmtime(os.path.join(hier, d, f)) for d in ("kern", "oberflaeche")
               for f in os.listdir(os.path.join(hier, d)) if f.endswith(".py"))
    daten = [os.path.join(hier, "daten", x) for x in ("sic13/einschaetzung.json", "tv/revier.csv",
                                                       "steckbrief_de/beschreibungen.json")]
    daten += [watchlists.DATEI, depot.DATEI]     # Watchlist oder Depot geändert: Seiten neu bauen
    tisch = os.path.join(hier, "daten", "kartentisch")
    if os.path.isdir(tisch):                     # neuer Kartentisch aus dem Abendlauf: Übersicht neu bauen
        daten += [os.path.join(tisch, f) for f in os.listdir(tisch) if f.endswith(".json")]
    return max([code] + [os.path.getmtime(x) for x in daten if os.path.exists(x)])


def zeigen(name, *args):
    """Seite als HTML ausgeben. st.markdown statt st.html: st.html entfernt die Inhalte
    eingebetteter SVG-Grafiken (den Chart)."""
    try:
        with st.spinner("Lade und rechne …"):
            html = _gebaut(name, _codestand(), *args)
        st.markdown(html, unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)


if ansicht == "Übersicht":
    _, w_, k_ = st.columns([8, 2, 2])
    with w_:
        watchlists_verwalten()
    with k_:
        konto_knopf()
    zeigen("uebersicht")
elif ticker:
    lauf = st.session_state.get("laufend")
    args = (ticker, True, lauf[1]) if lauf and lauf[0] == ticker else (ticker,)
    try:
        with st.spinner("Lade und rechne …"):
            teile = _gebaut("titel", _codestand(), *args)
        st.markdown(teile["oben"], unsafe_allow_html=True)
        ebene, aus, kurz = chart_knoepfe(ticker)
        st.markdown(titel.chartkarte(teile["chart"], ebene, aus, kurz), unsafe_allow_html=True)
        st.markdown(teile["unten"], unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)
