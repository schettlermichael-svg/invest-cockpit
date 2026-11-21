"""Prüflauf des Chart-Prüfers (kern/chartpruefer.py) – von Hand gestartet (der Knopf stand bis 21.11.2026 auf der Seite Setups). Eigener
Name, damit „import chartpruefer“ immer das Modul in kern/ findet (14.11.2026: gleicher Name verdeckte es)."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HIER, "..", "kern"), os.path.join(HIER, "..", "oberflaeche"), HIER]

import chartpruefer  # noqa: E402

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else chartpruefer.STICHPROBE
    print(chartpruefer.lauf(n))
