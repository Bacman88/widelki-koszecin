"""Scenariusz SUMO dla proponowanej siatki busów gminy Koszęcin (dzień roboczy, wariant pełny).

Wejście:  koszecin.net.xml (sieć z OpenStreetMap), data.json (trasy i przystanki), rozklad_data.json (rozkład).
Wyjście:  przystanki.add.xml, busy.rou.xml, pociagi.rou.xml (+ tlo.rou.xml z randomTrips), koszecin.sumocfg.

Założenia (do zmiany na górze pliku):
- busy jadą trasami z projektu (te same węzły OSM), na przystanku stoją 20 s,
  nie odjeżdżają przed czasem z rozkładu (until), na Rynku linie 2–4 czekają do :03;
- pociągi: po jednym na godzinę w każdą stronę na każdej linii kolejowej przez obszar (przybliżenie),
  dzięki czemu przejazdy kolejowe zamykają się jak w rzeczywistości;
- ruch tła: losowe samochody na całej sieci (randomTrips), żeby skrzyżowania nie były puste.
"""
import json, math, os, sys
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
from sumolib.route import mapTrace

D = json.load(open(sys.argv[1] if len(sys.argv) > 1 else '../out/data.json'))
R = json.load(open(sys.argv[2] if len(sys.argv) > 2 else '../out/rozklad_data.json'))
NET = sumolib.net.readNet('koszecin.net.xml.gz')
POSTOJ = 20          # s na przystanku
OKNO = (4 * 3600 + 30 * 60, 23 * 3600 + 59 * 60)

S = D['stops']; NAME2ID = {v[2]: k for k, v in S.items()}
def xy(lat, lon): return NET.convertLonLat2XY(lon, lat)
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

def odcinek(P, a, b):
    """Najkrótszy fragment ścieżki P (lub odwróconej) prowadzący od przystanku a do b."""
    best = None
    for seq in (P, P[::-1]):
        pa = xy(*S[a][:2]); pb = xy(*S[b][:2])
        ia = [i for i, q in enumerate(seq) if dist(q, pa) < 90]
        ib = [j for j, q in enumerate(seq) if dist(q, pb) < 90]
        for i in ia:
            for j in ib:
                if j > i:
                    L = sum(dist(seq[k], seq[k + 1]) for k in range(i, j))
                    if best is None or L < best[0]: best = (L, seq[i:j + 1])
    if best is None: raise SystemExit(f'Brak odcinka {a} → {b}')
    return best[1]

def trasa(line, stops):
    P = [xy(*q) for q in D['lines'][line]['path']]
    tr = []
    for a, b in zip(stops, stops[1:]):
        seg = odcinek(P, a, b)
        tr += seg if not tr else seg[1:]
    edges = mapTrace(tr, NET, 30, vClass='bus', fillGaps=600)
    out = []
    for e in edges:
        e = e if isinstance(e, str) else e.getID()
        if not out or out[-1] != e: out.append(e)
    # uzupełnij brakujące połączenia (mapTrace bywa nieciągły na skrzyżowaniach)
    fix = [out[0]]
    for e in out[1:]:
        a = NET.getEdge(fix[-1]); b = NET.getEdge(e)
        if b not in a.getAllowedOutgoing('bus'):
            p, _ = NET.getShortestPath(a, b, vClass='bus')
            if p: fix += [x.getID() for x in p[1:-1]]
        fix.append(e)
    return fix

def przystanek_na_trasie(edges, sid, od):
    """Krawędź z trasy (od indeksu od) najbliższa przystankowi i pozycja na niej."""
    p = xy(*S[sid][:2]); best = None
    for k in range(od, len(edges)):
        e = NET.getEdge(edges[k]); ln = e.getLanes()[0]
        pos, d = sumolib.geomhelper.polygonOffsetAndDistanceToPoint(p, ln.getShape())
        if best is None or d < best[0] - 1: best = (d, k, pos, ln)
        if best and d > best[0] + 800 and k > best[1] + 3: break
    return best

WEZLY = {'kosr', 'kosp', 'lubpkp', 'lisp', 'kalp', 'bor', 'laz', 'pil', 'pia'}   # przystanki z zatoką / pętlą: autobus czekający nie blokuje drogi
stopdefs = {}; vehicles = []
for line, days in R['tt'].items():
    if line not in D['lines']: continue
    for nm, dd in days['wd'].items():
        ids = [NAME2ID.get(s) or NAME2ID[s.split(' (')[0]] for s in dd['stops']]
        edges = trasa(line, ids)
        k0 = 0; stl = []
        for i, sid in enumerate(ids):
            d, k, pos, ln = przystanek_na_trasie(edges, sid, k0)
            dl = 45 if sid in WEZLY else 12
            if ln.getLength() < dl + 5:   # za krótka krawędź – przystanek na sąsiedniej (dłuższej) krawędzi trasy
                cand = [(NET.getEdge(edges[j]).getLength(), j) for j in (k - 1, k + 1) if 0 <= j < len(edges) and j >= k0]
                Lc, j = max(cand)
                if Lc >= dl + 5:
                    ln = NET.getEdge(edges[j]).getLanes()[0]; pos = Lc - 1 if j < k else dl; k = j
                else: dl = max(5, ln.getLength() - 1)
            L = ln.getLength(); pos = min(max(pos, dl), L - 1)
            key = f'{sid}_{ln.getEdge().getID()}'
            stopdefs[key] = (ln.getID(), max(0, pos - dl), pos, S[sid][2])
            stl.append(key); k0 = k
        for n, (t, dm) in enumerate(dd['trips']):
            if dm: continue
            t0 = t[0] * 60
            if not (OKNO[0] <= t0 <= OKNO[1]): continue
            stops = []
            for i, key in enumerate(stl):
                until = t[i] * 60
                if ids[i] == 'kosr' and line in ('2', '3', '4') and 0 < i < len(ids) - 1 and t[i + 1] - t[i] > 6:
                    until = ((t[i] + 11) // 60 * 60 + 3) * 60
                stops.append((key, until))
            vehicles.append((t0 - 60, f'L{line}_{nm.split(" →")[0][:12].replace(" ", "")}_{n:02d}_{t[0]}', edges, stops, line))

with open('przystanki.add.xml', 'w') as o:
    o.write('<additional>\n')
    for key, (lane, a, b, nm) in sorted(stopdefs.items()):
        pl = ' parkingLength="120"' if key.split('_')[0] in WEZLY else ''   # zatoka / plac: miejsce dla kilku czekających busów
        o.write(f'  <busStop id="{key}" lane="{lane}" startPos="{a:.1f}" endPos="{b:.1f}" name="{nm}" friendlyPos="true"{pl}/>\n')
    o.write('</additional>\n')
KOL = {'1': '0,112,79', '2': '31,111,214', '3': '204,138,0', '4': '212,71,58'}
with open('busy.rou.xml', 'w') as o:
    o.write('<routes>\n  <vType id="bus" vClass="bus" length="8.5" maxSpeed="25" accel="1.2" decel="3.5" sigma="0.4" speedFactor="normc(1,0.05,0.9,1.1)" guiShape="bus"/>\n')
    for dep, vid, edges, stops, line in sorted(vehicles):
        o.write(f'  <vehicle id="{vid}" type="bus" depart="{dep}" line="{line}" color="{KOL.get(line, "80,80,80")}" departLane="best" departPos="0">\n')
        o.write(f'    <route edges="{" ".join(edges)}"/>\n')
        for key, until in stops:
            par = ' parking="true"' if key.split('_')[0] in WEZLY else ''
            o.write(f'    <stop busStop="{key}" duration="{POSTOJ}" until="{until}"{par}/>\n')
        o.write('  </vehicle>\n')
    o.write('</routes>\n')
print('przystanki', len(stopdefs), 'kursy', len(vehicles))
