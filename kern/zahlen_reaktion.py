"""Zahlen-Reaktion (12.11.2026, Micky): Setup nach einem Zahlentermin, long und short – die Drift nach den Zahlen
(Post-Earnings-Announcement Drift: Ball und Brown 1968, Bernard und Thomas 1989; Bondes „Delayed Reaction“, Shannons
Anker am Ereignistag). Reagiert der Kurs klar auf die Zahlen, kaufen bzw. verkaufen die Fonds oft über Wochen nach.

Reaktionstag = erster Handelstag nach der Meldung (nach Börsenschluss gemeldet → Folgetag), wie „E +x %“ im Chart.
Voraussetzung: Reaktion ab REAKTION_PCT (Short ab −REAKTION_PCT) vor höchstens FENSTER Handelstagen (jüngste Meldung).
Regeln für grün (long; Short gespiegelt):
  1. Volumen am Reaktionstag über dem 50-Tage-Schnitt (Mickys Maßstab)
  2. Schluss im oberen Drittel der Tagesspanne (Short: unteres Drittel) – ein abverkaufter Tag zeigt keine Nachfrage
  3. Seitdem kein Schluss unter dem Tief des Reaktionstags und keiner unter dem AVWAP ab dem Reaktionstag
     (Short: über dem Hoch bzw. über dem AVWAP)
  4. Kurs über dem GD50 (Short: darunter) – Kullamägis Maßstab für Momentum, nicht die volle Trendvorlage
gelb = genau eine Regel fehlt; sonst rot (keine Reihe).
Einstieg: der ruhige Rücksetzer an den AVWAP ab dem Reaktionstag – „pivot“ ist dieser AVWAP, die Zone reicht bis 5 %
darüber (Short: darunter). Stopp im Chart wie überall 1,5 ATR; zusätzlich das Tief (Short: Hoch) des Reaktionstags.
Ohne Gewinndaten (Termin unbekannt) kein Setup – erfunden wird nichts."""
import pandas as pd

REAKTION_PCT = 3.0            # Micky 12.11.2026


# ── Feste Regeln (Generalinventur Stufe 2, 15.11.2026) ────────────────────────────────────────────────────────────


def reaktionstag(df, gewinne):
    """Jüngster Reaktionstag: (Index-Position, Prozent) oder None."""
    if gewinne is None or getattr(gewinne, "empty", True) or df is None or len(df) < 60:
        return None
    best = None
    for tag, z in gewinne.iterrows():
        pos = int(df.index.searchsorted(pd.Timestamp(tag)))
        if z.get("nach_schluss", 0) and pos < len(df) and df.index[pos] == pd.Timestamp(tag):
            pos += 1
        if 0 < pos < len(df):
            pct = (float(df["Close"].iloc[pos]) / float(df["Close"].iloc[pos - 1]) - 1) * 100
            if best is None or pos > best[0]:
                best = (pos, pct)
    return best




