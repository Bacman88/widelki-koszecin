"""Przejazdy kolejowe: jeden przejazd zamiast kilku i dłużej zamknięte rogatki.

1. W OSM każdy tor na przejeździe to osobny węzeł, więc netconvert robi z jednego przejazdu przez 3–5 torów
   kilka osobnych przejazdów z kawałkami drogi między nimi (auta stawały „w środku” przejazdu).
   Węzły rail_crossing bliżej niż 45 m od siebie sklejamy w jeden przejazd.
2. SUMO domyślnie zamyka rogatki ok. 15 s przed pociągiem. Na prawdziwych przejazdach (zwłaszcza przy stacji
   Lubliniec) rogatki opadają dużo wcześniej i otwierają się z opóźnieniem.

Uruchom: python3 przejazdy.py koszecin.net.xml   (zmienia sieć na miejscu i zapisuje przejazdy.add.xml; używane w zbuduj.sh)
"""
import os, sys, math, re, subprocess, collections
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
NETF = sys.argv[1] if len(sys.argv) > 1 else 'koszecin.net.xml'
B = os.path.join(SUMO_HOME, 'bin')
CZAS_PRZED = 60          # s: rogatki zamknięte tyle przed nadjechaniem pociągu
CZAS_PRZED_STACJA = 120  # s: przejazdy przy stacji Lubliniec (pociągi zwalniają/stają, rogatki stoją długo)
OPOZNIENIE_OTWARCIA = 15 # s po przejechaniu pociągu
STACJA_LUB = (50.6726, 18.691)

def netconvert(*args):
    subprocess.run([f'{B}/netconvert', '-s', NETF, '-o', NETF, '--no-warnings', *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

n = sumolib.net.readNet(NETF, withPrograms=False)
rc = [x for x in n.getNodes() if x.getType() == 'rail_crossing']
par = {}
def f(x):
    while par.setdefault(x, x) != x: x = par[x]
    return x
for a in rc:
    for b in rc:
        if a.getID() < b.getID() and math.dist(a.getCoord(), b.getCoord()) < 45: par[f(a.getID())] = f(b.getID())
gr = collections.defaultdict(list)
for x in rc: gr[f(x.getID())].append(x.getID())
grupy = [sorted(v) for v in gr.values() if len(v) > 1]
with open('przejazdy_zlacz.nod.xml', 'w') as o:
    o.write('<nodes>\n' + ''.join(f'  <join nodes="{" ".join(v)}"/>\n' for v in grupy) + '</nodes>\n')
netconvert('-n', 'przejazdy_zlacz.nod.xml')
# sklejony węzeł dostaje typ „priority” – przywracamy rail_crossing
n = sumolib.net.readNet(NETF, withPrograms=False)
nowe = [x.getID() for x in n.getNodes() if x.getID().startswith('cluster_')
        and any(e.allows('rail') for e in x.getIncoming()) and any(e.allows('passenger') for e in x.getIncoming())]
with open('przejazdy_typ.nod.xml', 'w') as o:
    o.write('<nodes>\n' + ''.join(f'  <node id="{x}" type="rail_crossing"/>\n' for x in nowe) + '</nodes>\n')
netconvert('-n', 'przejazdy_typ.nod.xml')
# czasy zamykania rogatek (parametry programu rail_crossing w SUMO)
n = sumolib.net.readNet(NETF, withPrograms=False)
sx, sy = n.convertLonLat2XY(STACJA_LUB[1], STACJA_LUB[0])
blisko = {x.getID() for x in n.getNodes() if x.getType() == 'rail_crossing' and math.dist(x.getCoord(), (sx, sy)) < 3500}
with open('przejazdy.add.xml', 'w') as o:     # parametry rogatek (MSRailCrossing): plik dodatkowy wczytywany w koszecin.sumocfg
    o.write('<additional>\n')
    for x in sorted(x.getID() for x in n.getNodes() if x.getType() == 'rail_crossing'):
        tg = CZAS_PRZED_STACJA if x in blisko else CZAS_PRZED
        o.write(f'  <tlLogic id="{x}" programID="0" type="rail_crossing"><param key="time-gap" value="{tg}"/>'
                f'<param key="opening-delay" value="{OPOZNIENIE_OTWARCIA}"/></tlLogic>\n')
    o.write('</additional>\n')
print('sklejone przejazdy:', len(grupy), '| przejazdy przy stacji Lubliniec (rogatki', CZAS_PRZED_STACJA, 's przed pociągiem):', len(blisko))
