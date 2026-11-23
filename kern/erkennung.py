"""Market-Profile-Analyse je Titel für den Kreislauf (Wertzone, zeichen.fuer_titel) – seit dem 23.11.2026 der einzige
Rest der alten Erkennung (Klimax-Verdacht und Hinweise entfernt; die Klimax misst reiten.klimax_tag)."""

_MP, _ROH = {}, {}


def mp_von(df):
    """Market-Profile-Analyse der Reihe (gekappt am letzten Tag von df, kein Blick in die Zukunft); None ohne Kerzen."""
    tk = df.attrs.get("ticker") or df.attrs.get("tk_mp")
    if not tk or not len(df):
        return None
    schluessel = (tk, len(df), df.index[-1], float(df["Close"].iloc[-1]))
    if schluessel not in _MP:
        import marketprofile
        import tpo_daten
        if len(_MP) > 500:
            _MP.clear()
        if tk not in _ROH:
            if len(_ROH) > 50:                   # Massenlauf (Kartentisch, Kreislauf): Speicher begrenzen
                _ROH.clear()
            _ROH[tk] = tpo_daten.lesen(tk)
        roh = _ROH[tk]
        a = None
        if roh is not None:
            teil = roh[roh.index.normalize() <= df.index[-1]]
            if len(teil):
                a = marketprofile.analyse(tpo_daten.ausrichten(teil, df), df)
        if a is not None and df.attrs.get("laufend") and roh.index[-1].normalize() == df.index[-1]:
            # mit der unvollständigen Kerze von heute: alles am rechten Rand ist vorläufig bis Börsenschluss
            a["vorlaeufig"] = df.attrs.get("stand", "")
            w = a["zustand"]["wort"]
            a["zustand"]["wort"] = (w[:-1] + ", vorläufig)") if w.endswith(")") else w + " (vorläufig)"
        _MP[schluessel] = a
    return _MP[schluessel]
