"""Meldungen aufs Handy über ntfy (10.11.2026): kostenlose App „ntfy“ (iPhone/Android), ohne Konto. Der Server schickt
an einen geheimen Kanal (einstellungen/ntfy_kanal.txt, beim ersten Aufruf zufällig erzeugt, nicht in Git); wer den
Kanalnamen in der App abonniert, bekommt die Meldungen. Fehler beim Senden halten nichts auf."""
import os
import secrets
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
KANAL = os.path.join(HIER, "..", "einstellungen", "ntfy_kanal.txt")
SERVER = "https://ntfy.sh"


def kanal():
    """Geheimer Kanalname; wird beim ersten Aufruf erzeugt."""
    try:
        k = open(KANAL, encoding="utf-8").read().strip()
        if k:
            return k
    except OSError:
        pass
    k = "invest-cockpit-" + secrets.token_hex(8)
    os.makedirs(os.path.dirname(KANAL), exist_ok=True)
    with open(KANAL, "w", encoding="utf-8") as f:
        f.write(k)
    return k


def senden(text, titel="Invest Cockpit", wichtig=False):
    """Meldung an den Kanal; True bei Erfolg."""
    try:
        req = urllib.request.Request(f"{SERVER}/{kanal()}", data=text.encode("utf-8"), method="POST",
                                     headers={"Title": titel.encode("utf-8").decode("latin-1", "ignore"),
                                              "Priority": "high" if wichtig else "default",
                                              "Tags": "warning" if wichtig else "chart_with_upwards_trend"})
        with urllib.request.urlopen(req, timeout=15):
            return True
    except Exception:  # noqa: BLE001 – ohne Meldung läuft alles weiter
        return False
