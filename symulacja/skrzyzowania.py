"""Skleja skrzyżowania rozbite w OSM na kilka węzłów (np. Wierzbie: Główna × Cieszowska).
W OSM boczna droga często dochodzi do głównej w 2–3 punktach oddalonych o kilka metrów.
netconvert robi z tego trójkąt z mikroodcinkami i dziwnym pierwszeństwem.
Skrypt szuka na trasach busów węzłów-skrzyżowań połączonych odcinkiem < 12 m
i zapisuje je jako <join> do zlacz.nod.xml (używane w zbuduj.sh).
Uruchom: python3 skrzyzowania.py  (po zbudowaniu sieci i busy.rou.xml)."""
import os, re, collections
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
import sys; sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
n = sumolib.net.readNet('koszecin.net.xml.gz')
ed = set()
for m in re.finditer(r'edges="([^"]+)"', open('busy.rou.xml').read()): ed.update(m.group(1).split())
nodes = {x for e in ed for x in (n.getEdge(e).getFromNode(), n.getEdge(e).getToNode())}
def sasiedzi(nd):
    return {frozenset((e.getFromNode().getID(), e.getToNode().getID())) for e in nd.getIncoming() + nd.getOutgoing() if e.allows('passenger')}
par = {}
def f(x):
    while par.setdefault(x, x) != x: x = par[x]
    return x
for nd in nodes:
    for e in nd.getOutgoing() + nd.getIncoming():
        a, b = e.getFromNode(), e.getToNode()
        if e.allows('passenger') and e.getLength() < 12 and len(sasiedzi(a)) >= 3 and len(sasiedzi(b)) >= 3 \
           and a.getType() not in ('rail_crossing', 'traffic_light') and b.getType() not in ('rail_crossing', 'traffic_light'):
            par[f(a.getID())] = f(b.getID())
cl = collections.defaultdict(list)
for k in list(par): cl[f(k)].append(k)
with open('zlacz.nod.xml', 'w') as o:
    o.write('<nodes>\n')
    for v in sorted(cl.values()):
        if len(v) >= 2:
            lon, lat = n.convertXY2LonLat(*n.getNode(v[0]).getCoord())
            o.write(f'  <join nodes="{" ".join(sorted(v))}"/> <!-- {lat:.5f},{lon:.5f} -->\n')
    o.write('</nodes>\n')
print('sklejone skrzyżowania:', sum(len(v) >= 2 for v in cl.values()))
