"""Sicheres Schreiben und Lesen der JSON-Speicherdateien (09.11.2026).

Anlass: „Expecting value: line 1 column 399475“ – eine Speicherdatei war abgeschnitten, weil ein Prozess sie gerade
schrieb (oder beim Neustart der App mitten im Schreiben beendet wurde), während ein anderer sie las.
json_schreiben schreibt erst in eine eigene Datei daneben und ersetzt dann in einem Schritt (os.replace) – ein Leser sieht
immer die alte oder die neue Datei, nie eine halbe. json_lesen gibt bei einer kaputten Datei `ersatz` zurück und legt sie
als <name>.kaputt beiseite, damit der Zwischenspeicher neu geholt wird statt die Seite zu sprengen.
"""
import json
import os


def json_schreiben(pfad, daten, **kw):
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
