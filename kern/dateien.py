"""Sicheres Schreiben und Lesen der JSON-Speicherdateien (09.11.2026).

Anlass: „Expecting value: line 1 column 399475“ – eine Speicherdatei war abgeschnitten, weil ein Prozess sie gerade
schrieb (oder beim Neustart der App mitten im Schreiben beendet wurde), während ein anderer sie las.
json_schreiben schreibt erst in eine eigene Datei daneben und ersetzt dann in einem Schritt (os.replace) – ein Leser sieht
immer die alte oder die neue Datei, nie eine halbe. json_lesen gibt bei einer kaputten Datei `ersatz` zurück und legt sie
als <name>.kaputt beiseite, damit der Zwischenspeicher neu geholt wird statt die Seite zu sprengen.
"""
import json
import os


def _wandeln(x):
    """Werte, die JSON nicht kennt (numpy-Ja/Nein, -Zahlen, Zeitstempel), in normale umwandeln (10.11.2026).
    Anlass: der Kartentisch scheiterte seit dem 05.11. beim Speichern an einem numpy-Ja/Nein-Wert."""
    for art, f in (("bool_", bool), ("integer", int), ("floating", float)):
        try:
            import numpy as np
            if isinstance(x, getattr(np, art)):
                return f(x)
        except ImportError:
            break
    if hasattr(x, "isoformat"):
        return x.isoformat()
    if hasattr(x, "tolist"):
        return x.tolist()
    if isinstance(x, (set, tuple)):
        return list(x)
    raise TypeError(f"Object of type {type(x).__name__} is not JSON serializable")


def json_schreiben(pfad, daten, **kw):
    kw.setdefault("default", _wandeln)
    tmp = f"{pfad}.{os.getpid()}.neu"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(daten, f, **kw)
    os.replace(tmp, pfad)


def json_lesen(pfad, ersatz=None):
    try:
        with open(pfad, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return ersatz
    except ValueError:
        try:
            os.replace(pfad, pfad + ".kaputt")
        except OSError:
            pass
        return ersatz
