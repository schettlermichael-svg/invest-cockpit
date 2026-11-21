"""Prüflauf des Setup-Prüfers (kern/setuppruefer.py) – von Hand gestartet (der Knopf stand bis 21.11.2026 auf der Seite Setups)."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HIER, "..", "kern"), os.path.join(HIER, "..", "oberflaeche"), HIER]

import setuppruefer  # noqa: E402

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else setuppruefer.STICHPROBE
    print(setuppruefer.lauf(n))
