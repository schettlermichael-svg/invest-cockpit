"""Prüflauf des Chart-Prüfers (kern/chartpruefer.py) – gestartet vom Knopf auf der Seite Setups oder von Hand."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HIER, "..", "kern"), os.path.join(HIER, "..", "oberflaeche")]

import chartpruefer  # noqa: E402

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else chartpruefer.STICHPROBE
    print(chartpruefer.lauf(n))
