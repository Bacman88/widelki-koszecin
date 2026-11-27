"""Scenariusz SUMO „dziś”: obecne kursy GTV przez gminę Koszęcin (dzień roboczy z nauką szkolną, 30.11.2026).

Wejście:  ../dane/gtv_dzis/przystanki.csv, ../dane/gtv_dzis/kursy.txt (z gtvbus.kiedyprzyjedzie.pl), koszecin.net.xml.gz
Wyjście:  przystanki_dzis.add.xml, busy_dzis.rou.xml, plan_kursow_dzis.json

Trasa każdego kursu: najkrótsza droga dla autobusu między kolejnymi przystankami (przystanek przypisany do
najbliższej krawędzi drogi w promieniu 80 m; z kilku kandydatów wybierane te, które dają najkrótszy przejazd).
Na przystankach bus stoi 10 s i nie odjeżdża przed czasem z rozkładu (until) – jak kierowca trzymający się rozkładu.
"""
import json, math, os, sys
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
from sumolib.geomhelper import polygonOffsetAndDistanceToPoint as odl

NET = sumolib.net.readNet('koszecin.net.xml.gz')
POSTOJ = 10
ST = {}
for l in open('../dane/gtv_dzis/przystanki.csv', encoding='utf-8'):
    if l.strip():
        d, nm, lon, lat = l.strip().split(';'); ST[d] = (nm, float(lon), float(lat))
KURSY = []
for l in open('../dane/gtv_dzis/kursy.txt'):
    tid, r = l.strip().split(':')
    KURSY.append((tid, [(d, int(m)) for d, m in (x.split('.') for x in r.split(','))]))

def kandydaci(d):
    x, y = NET.convertLonLat2XY(ST[d][1], ST[d][2])
    out = []
    for e, dd in NET.getNeighboringEdges(x, y, 80):
        if not e.allows('bus') or e.getFunction() == 'internal': continue
        ln = e.getLanes()[0]; pos, dist = odl((x, y), ln.getShape())
        out.append((dist, e, pos))
    out.sort(key=lambda t: t[0])
    return out[:4]

KAND = {d: kandydaci(d) for d in ST}
brak = [d for d, k in KAND.items() if not k]
if brak: print('przystanki poza siecią (pominięte):', [ST[d][0] for d in brak])

SP = {}
def droga(a, b):
    if (a, b) not in SP:
        if a == b: SP[(a, b)] = ([a], 0.0)
        else:
            p, c = NET.getShortestPath(a, b, vClass='bus')
            SP[(a, b)] = (p, c if p else float('inf'))
    return SP[(a, b)]

stopdefs = {}; vehicles = []; PLAN = {}
for tid, v in KURSY:
    v = [(d, t) for d, t in v if KAND.get(d)]
    # kolejne odwiedziny tego samego przystanku w 1 min – zostaw jedną
    v2 = []
    for d, t in v:
        if v2 and v2[-1][0] == d: continue
        v2.append((d, t))
    v = v2
    if len(v) < 2: continue
    # DP po kandydatach krawędzi
    best = [{i: (c[0] * 3, None) for i, c in enumerate(KAND[v[0][0]])}]
    for k in range(1, len(v)):
        cur = {}
        for j, cj in enumerate(KAND[v[k][0]]):
            opt = None
            for i, (koszt, _) in best[-1].items():
                ci = KAND[v[k - 1][0]][i]
                p, c = droga(ci[1], cj[1])
                if not p: continue
                if ci[1] == cj[1] and cj[2] < ci[2] - 5: continue        # cofanie się na tej samej krawędzi
                kk = koszt + c + cj[0] * 3
                if opt is None or kk < opt[0]: opt = (kk, i)
            if opt: cur[j] = opt
        if not cur: break
        best.append(cur)
    if len(best) < len(v):
        print('kurs', tid, 'przerwany po', len(best), 'z', len(v)); v = v[:len(best)]
        if len(v) < 2: continue
    # odtwórz wybór
    j = min(best[-1], key=lambda i: best[-1][i][0]); wyb = [j]
    for k in range(len(best) - 1, 0, -1):
        j = best[k][j][1]; wyb.append(j)
    wyb = wyb[::-1]
    edges = []; stops = []
    for k, (d, t) in enumerate(v):
        dist, e, pos = KAND[d][wyb[k]]
        if k:
            p, _ = droga(KAND[v[k - 1][0]][wyb[k - 1]][1], e)
            edges += [x.getID() for x in p[1:]]
        else: edges.append(e.getID())
        ln = e.getLanes()[0]; L = ln.getLength(); pos = min(max(pos, 13), L - 0.5)
        key = f'G{d}_{e.getID()}'
        stopdefs[key] = (ln.getID(), max(0, pos - 12), pos, ST[d][0])
        stops.append((key, t * 60))
    vid = f'G_{tid}_{v[0][1]}'
    vehicles.append((v[0][1] * 60 - 60, vid, edges, stops))
    PLAN[vid] = [(k, u, True) for k, u in stops]

with open('przystanki_dzis.add.xml', 'w') as o:
    o.write('<additional>\n')
    for key, (lane, a, b, nm) in sorted(stopdefs.items()):
        o.write(f'  <busStop id="{key}" lane="{lane}" startPos="{a:.1f}" endPos="{b:.1f}" name="{nm}" friendlyPos="true"/>\n')
    o.write('</additional>\n')
with open('busy_dzis.rou.xml', 'w') as o:
    o.write('<routes>\n  <vType id="bus" vClass="bus" length="8.5" maxSpeed="19.44" accel="1.2" decel="3.5" sigma="0.4" speedFactor="normc(1,0.05,0.9,1.1)" guiShape="bus">\n    <param key="has.fcd.device" value="true"/>\n  </vType>\n')
    for dep, vid, edges, stops in sorted(vehicles):
        o.write(f'  <vehicle id="{vid}" type="bus" depart="{dep}" color="75,85,99" departLane="best" departPos="0">\n')
        o.write(f'    <route edges="{" ".join(edges)}"/>\n')
        for i, (key, until) in enumerate(stops):
            if i == len(stops) - 1: o.write(f'    <stop busStop="{key}" duration="{POSTOJ}"/>\n')
            else: o.write(f'    <stop busStop="{key}" duration="{POSTOJ}" until="{until}"/>\n')
        o.write('  </vehicle>\n')
    o.write('</routes>\n')
json.dump(PLAN, open('plan_kursow_dzis.json', 'w'), ensure_ascii=False)
print('przystanki', len(stopdefs), 'kursy', len(vehicles))
