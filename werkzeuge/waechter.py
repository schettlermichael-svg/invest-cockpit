"""Der Wächter (Micky 26.11.2026): ein Lauf über die Titel mit Alarm (kern/waechter.py). Der Server startet ihn
Mo–Fr während der US-Börse jede Minute (waechter.timer) und um 15:45 New York mit „schluss“ (waechter-schluss.timer)."""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))

import waechter  # noqa: E402

if __name__ == "__main__":
    for text in waechter.pruefen(schluss="schluss" in sys.argv[1:]):
        print(text)
