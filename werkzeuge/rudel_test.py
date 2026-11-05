"""Abnahme Schritt 4: Kursverwandte, Themen-Gruppen und Rudel an bekannten Zusammenhängen.

Aufruf im Ordner InvestCockpit:  python3 werkzeuge/rudel_test.py      Ergebnis: werkzeuge/rudel_test.txt
Prüfungen (Konzept, Schritt 4):
  1. HWM läuft eher mit Triebwerks- und Luftfahrtzulieferern als mit dem Industriesektor als Ganzem
  2. eine KI-Gruppe bildet sich von selbst (mindestens 3 bekannte KI-Titel in einer Themen-Gruppe)
  3. Gegenproben: Großbanken laufen zusammen (JPM–BAC eng), Ölkonzerne (XOM–CVX eng),
     Gold-Minen bilden eine Gruppe (NEM, AEM, KGC)
  4. Gegenprobe gegen Zufall: Titel aus völlig verschiedenen Branchen sind nicht verwandt (XOM–ADBE)
"""
import os
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))
import rudel  # noqa: E402

KI = {"NVDA", "AVGO", "TSM", "MU", "AMD", "ASML", "LRCX", "AMAT", "KLAC", "VRT", "GEV", "CRWV", "NBIS", "ANET",
      "SMCI", "COHR", "LITE", "CIEN", "IREN", "ETN", "PWR", "CEG", "VST", "DELL", "ORCL"}
LUFTFAHRT = {"Aerospace & Defense", "Metal Fabrication", "Specialty Industrial Machinery"}


def gleichlauf(a, b):
    c = rudel._laden()
    return float(c["A"][c["idx"][a], c["idx"][b]])


def main():
    aus, ok_alle = [], []
    c = rudel._laden()
    rv = c["rv"]
    aus.append(f"Stand {rudel.stand():%d.%m.%Y}: {len(c['idx'])} Titel mit mindestens {rudel.MIN_TAGE} Tagen")

    # 1. HWM
    kv = rudel.kursverwandte("HWM")
    luft = sum(1 for k in kv if k["branche"] in LUFTFAHRT)
    sektor = [t for t in rv.index[rv["etf"] == "XLI"] if t in c["idx"] and t != "HWM"]
    zum_sektor = float(np.nanmean([gleichlauf("HWM", t) for t in sektor]))
    zu_verwandten = float(np.mean([k["wert"] for k in kv])) if kv else 0
    ok = luft >= 3 and zu_verwandten > 2 * zum_sektor
    ok_alle.append(ok)
    liste = ", ".join("%s %.2f %s (%s)" % (k["ticker"], k["wert"], k["grad"], k["branche"]) for k in kv)
    aus.append(f"{'🟢' if ok else '🔴'} 1. HWM: {liste}")
    aus.append(f"      Ø Gleichlauf zu den Verwandten {zu_verwandten:.2f} gegen Ø zum Industriesektor ({len(sektor)} Titel) "
               f"{zum_sektor:.2f}; Thema: {(rudel.thema_von('HWM') or {}).get('name', 'keins')}")

    # 2. KI-Gruppe
    treffer = sorted(((len(KI & set(g["mitglieder"])), g) for g in rudel.themen()), key=lambda x: -x[0])
    ki_gruppen = [(n, g) for n, g in treffer if n >= 3]
    ok = bool(ki_gruppen)
    ok_alle.append(ok)
    aus.append(f"{'🟢' if ok else '🔴'} 2. KI-Gruppen von selbst: {len(ki_gruppen)}")
    for n, g in ki_gruppen:
        aus.append(f"      Thema {g['nr']} „{g['name']}“ ({len(g['mitglieder'])} Titel, Gleichlauf {g['gleichlauf']}): "
                   f"{n} KI-Titel – {', '.join(sorted(KI & set(g['mitglieder'])))}")

    # 3. Gegenproben
    for a, b, schwelle in [("JPM", "BAC", rudel.ENG), ("XOM", "CVX", rudel.ENG)]:
        w = gleichlauf(a, b)
        ok = w >= schwelle
        ok_alle.append(ok)
        aus.append(f"{'🟢' if ok else '🔴'} 3. {a}–{b}: {w:.2f} (erwartet ab {schwelle})")
    gold = rudel.thema_von("NEM")
    ok = bool(gold) and {"AEM", "KGC"} <= set(gold["mitglieder"])
    ok_alle.append(ok)
    aus.append(f"{'🟢' if ok else '🔴'} 3. Gold-Minen gemeinsam: {gold['name'] if gold else 'keine Gruppe'}")

    # 4. Gegenprobe gegen Zufall
    w = gleichlauf("XOM", "ADBE")
    ok = w < rudel.MITTEL
    ok_alle.append(ok)
    aus.append(f"{'🟢' if ok else '🔴'} 4. XOM–ADBE: {w:.2f} (erwartet unter {rudel.MITTEL})")

    # Übersicht
    th = rudel.themen()
    aus.append(f"\nThemen-Gruppen: {len(th)}, darin {sum(len(g['mitglieder']) for g in th)} Titel")
    for g in th:
        aus.append(f"  {g['nr']:>2}. {g['name'][:60]:60} {len(g['mitglieder']):>3} Titel, Gleichlauf {g['gleichlauf']}: "
                   + " ".join(g["mitglieder"][:10]))
    r = rudel.rudel("HWM")
    m = rudel.gruppen_mansfield(r["mitglieder"])
    aus.append(f"\nRudel HWM ({r['art']} {r['name']}): {r['im_trend']} von {r['anzahl']} im Trend, "
               f"{r['nahe_hoch']} nahe am Hoch, Ampel {r['ampel']}, Einsamer Wolf: {r['einsamer_wolf']}; "
               f"Mansfield der Gruppe {m}")
    aus.append(f"Mansfield HWM: {rudel.mansfield(rudel.kurse()['HWM'], rudel.kurse()['SPY'])}")
    woelfe = [t for t in rv.index if t in c["idx"] and (rudel.rudel(t) or {}).get("einsamer_wolf")]
    aus.append(f"Einsame Wölfe im Revier: {len(woelfe)} – {', '.join(woelfe[:25])}")
    aus.append(f"\nErgebnis: {sum(ok_alle)} von {len(ok_alle)} Prüfungen bestanden")
    text = "\n".join(aus)
    print(text)
    open(os.path.join(HIER, "rudel_test.txt"), "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()
