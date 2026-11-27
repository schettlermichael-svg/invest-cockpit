"""Meldungen aufs Handy über ntfy (10.11.2026): kostenlose App „ntfy“ (iPhone/Android), ohne Konto. Der Server schickt
an einen geheimen Kanal (einstellungen/ntfy_kanal.txt, beim ersten Aufruf zufällig erzeugt, nicht in Git); wer den
Kanalnamen in der App abonniert, bekommt die Meldungen. Fehler beim Senden halten nichts auf."""
import os
import secrets
import urllib.parse
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
KANAL = os.path.join(HIER, "..", "einstellungen", "ntfy_kanal.txt")
SERVER = "https://ntfy.sh"
NTFY_GRENZE = 4096                                 # Technik: größte Meldung, die ntfy als Text zeigt (Bytes)
APP = "https://invest.themaraga-group.de"           # Adresse der App (Tipp auf die Meldung öffnet sie; seit 27.11.2026)


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


def _kopfwert(x):
    """Umlaute und „·“ im Titel: ntfy liest Kopfzeilen nach RFC 2047 (12.11.2026 – vorher kam „Â·“ an)."""
    import base64
    return x if x.isascii() else "=?UTF-8?B?" + base64.b64encode(x.encode("utf-8")).decode("ascii") + "?="


def senden(text, titel="MARAGA INVESTMENT APP", wichtig=False, seite=None, warnung=None):
    """Meldung an den Kanal; True bei Erfolg. seite: Ansicht der App, die ein Tipp auf die Meldung öffnet. wichtig = hohe
    Priorität (kommt als Push durch); warnung = ⚠️-Zeichen (Standard: wie wichtig)."""
    try:
        kopf = {"Title": _kopfwert(titel),
                "Priority": "high" if wichtig else "default",
                "Tags": "warning" if (wichtig if warnung is None else warnung) else "chart_with_upwards_trend"}
        if seite:
            kopf["Click"] = f"{APP}/?seite={urllib.parse.quote(seite)}"
        roh = text.encode("utf-8")
        if len(roh) > NTFY_GRENZE:                 # längere Meldungen macht ntfy zum Anhang – kürzen statt verlieren
            roh = roh[:NTFY_GRENZE - 40].decode("utf-8", "ignore").rsplit("\n", 1)[0].encode("utf-8") + \
                "\n… (gekürzt – alles in der App)".encode("utf-8")
        req = urllib.request.Request(f"{SERVER}/{kanal()}", data=roh, method="POST", headers=kopf)
        with urllib.request.urlopen(req, timeout=15):
            return True
    except Exception:  # noqa: BLE001 – ohne Meldung läuft alles weiter
        return False
