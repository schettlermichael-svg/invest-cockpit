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
        with st.form("wl_verw_liste_weg", clear_on_submit=True):
            sicher = st.checkbox(f"Liste „{name}“ wirklich löschen")
            if st.form_submit_button("Liste löschen", use_container_width=True) and sicher:
                n = watchlists.liste_loeschen(name)
                st.toast(f"„{name}“ gelöscht · {n} Titel standen in keiner anderen Liste und fallen aus dem Abendlauf "
                         "(außer sie gehören zum Revier)")
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


def _verschieben(tk, von, nach):
    watchlists.setzen(tk, nach, True)
    watchlists.setzen(tk, von, False)
    st.toast(f"{tk}: „{von}“ → „{nach}“")


def _herausnehmen(tk, liste):
    watchlists.setzen(tk, liste, False)
    st.toast(f"{tk} aus „{liste}“ genommen")


def _watch_aktionen(tk, liste, schluessel):
    """Im Watchlist-Abschnitt: in eine andere Liste verschieben oder herausnehmen. Sonst: je Liste ein Haken."""
    namen = list(watchlists.laden()) or [watchlists.STANDARD]
    if liste:
        with _fenster(f"◆ {liste}"):
            for n in namen:
                if n != liste:
                    st.button(f"→ nach „{n}“ verschieben", key=f"{schluessel}mv_{tk}_{n}", use_container_width=True,
                              on_click=_verschieben, args=(tk, liste, n))
            st.button(f"✕ aus „{liste}“ herausnehmen", key=f"{schluessel}rm_{tk}", use_container_width=True,
                      on_click=_herausnehmen, args=(tk, liste))
        return
    drin = watchlists.listen_von(tk)
    with _fenster(f"★ Watchlist ({len(drin)})" if drin else "☆ Watchlist"):
        for n in namen:
            sl = f"{schluessel}wl_{tk}_{n}"
            st.session_state[sl] = n in drin
            st.checkbox(n, key=sl, on_change=_watch_setzen, args=(tk, n, sl))


def _knopfleiste(tk, liste, schluessel):
    a, b = st.columns(2)
    with a:
        _watch_aktionen(tk, liste, schluessel)
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
    df = pd.DataFrame([{" ": "", "Titel": z["tk"], "Setup": z["Setup"], "Zone": z["Zone"],
                        "Abstand %": z["Abstand %"], "Was fehlt": z["Was fehlt"]} for z in zeilen])
    farben = [_rgba(z["farbe"] + ("66" if z.get("blass") else "")) for z in zeilen]
    stil = df.style.apply(lambda spalte: [f"background-color:{f}" for f in farben], subset=[" "])
    zaehler = f"tab_n_{nr}"
    n = st.session_state.setdefault(zaehler, 0)
    with st.expander(f"alle weiteren {len(zeilen)} zeigen · Zeile anklicken öffnet die Lagekarte"):
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
        for nr, teil in enumerate(_tischplan(_codestand())):
            if teil["art"] == "html":
                html(teil["html"])
                continue
            html(teil["kopf"] + ("" if teil["karten"] or teil["zeilen"]
                                 else f'<div style="color:{TEXT_2};font-size:15px">zurzeit keine</div>'))
            name = f"{nr}_{teil['liste'] or 'reihe'}"
            karten = teil["karten"]
            for i in range(0, len(karten), 3):
                for spalte, (tk, x, h) in zip(st.columns(3), karten[i:i + 3]):
                    with spalte:
                        st.markdown(h, unsafe_allow_html=True)
                        _knopfleiste(tk, teil["liste"], f"k{name}_")
            _tabelle(teil, name)


def zeigen(name, *args):
    """Seite als HTML ausgeben. st.markdown statt st.html: st.html entfernt die Inhalte
    eingebetteter SVG-Grafiken (den Chart)."""
    try:
        with st.spinner("Lade und rechne …"):
            html = _gebaut(name, _codestand(), *args)
        if isinstance(html, dict):                   # Übersicht: oben, Kartentisch mit Knöpfen, unten
            st.markdown(html["oben"], unsafe_allow_html=True)
            _kartentisch_zeigen()
            st.markdown(html["unten"], unsafe_allow_html=True)
        else:
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
        teile = titel.abgelegt(ticker) if len(args) == 1 else None   # vom Abendlauf fertig gebaut: sofort da
        if teile is None:
            with st.spinner("Lade und rechne …"):
                teile = _gebaut("titel", _codestand(), *args)
        st.markdown(teile["oben"], unsafe_allow_html=True)
        ebene, aus, kurz = chart_knoepfe(ticker)
        st.markdown(titel.chartkarte(teile["chart"], ebene, aus, kurz), unsafe_allow_html=True)
        st.markdown(teile["unten"], unsafe_allow_html=True)
    except Exception as e:  # noqa: BLE001
        _fehler(e)
