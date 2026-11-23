"""Ruch tła (samochody) – natężenia dobrane do obserwacji mieszkańca, nie do pomiarów:
- w szczytach duży ruch na korytarzu wschodni Lubliniec ↔ Piasek i dalej na wschód (w obie strony)
  oraz Kalety ↔ Koszęcin (w obie strony);
- umiarkowany ruch po głównych ulicach Lublińca (bez wjeżdżania w każdą osiedlową uliczkę);
- mało ruchu między wsiami i z wsi do Lublińca.
Przejazdy startują i kończą się na drogach co najmniej powiatowych/zbiorczych (priorytet >= 7),
żeby auta nie pojawiały się na bocznych uliczkach, gdzie ruchu zwykle nie ma.
Wynik: tlo.trips.xml → duarouter → tlo.rou.xml(.gz)."""
import os, sys, random, math
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
random.seed(42)
n = sumolib.net.readNet(sys.argv[1] if len(sys.argv) > 1 else 'koszecin.net.xml.gz', withPrograms=False)
E = [e for e in n.getEdges() if e.allows('passenger') and not e.getID().startswith(':') and e.getLength() > 30
     and not e.allows('rail') and e.getPriority() >= 7]
def strefa(lat, lon, r):
    x, y = n.convertLonLat2XY(lon, lat)
    return [e for e in E if math.dist((x, y), e.getFromNode().getCoord()) < r]
LUB = (18.655, 50.640, 18.725, 50.695)
def w_lub(e):
    lon, lat = n.convertXY2LonLat(*e.getFromNode().getCoord())
    return LUB[0] <= lon <= LUB[2] and LUB[1] <= lat <= LUB[3]
miasto = [e for e in E if w_lub(e)]; okolica = [e for e in E if not w_lub(e)]
lub_wsch = strefa(50.672, 18.715, 1200)
piasek = strefa(50.595, 18.985, 1800)      # Piasek i dalej na wschód (krawędź mapy)
kalety = strefa(50.566, 18.888, 1500)
koszecin = strefa(50.636, 18.841, 1200)
def odl(a, b): return math.dist(a.getFromNode().getCoord(), b.getToNode().getCoord())
# udział godziny w dobie (suma = 1): szczyty 6–8 i 14–17
W = [.2, .2, .2, .2, .3, .6, 2, 2, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1.2, 1, .8, .6, .4, .3, .2]
W = [w / sum(W) for w in W]
GRUPY = [  # (nazwa, przejazdów na dobę, skąd, dokąd, min. odległość [m])
    ('lub_piasek', 2500, lub_wsch, piasek, 3000), ('piasek_lub', 2500, piasek, lub_wsch, 3000),
    ('kalety_kosz', 1500, kalety, koszecin, 2000), ('kosz_kalety', 1500, koszecin, kalety, 2000),
    ('miasto', 4000, miasto, miasto, 800),
    ('do_lub', 700, okolica, miasto, 2000), ('z_lub', 700, miasto, okolica, 2000),
    ('okolica', 800, okolica, okolica, 2000),
]
trips = []
for nm, doba, A, B, mind in GRUPY:
    for h in range(24):
        for _ in range(round(doba * W[h] * random.uniform(0.9, 1.1))):
            t = h * 3600 + random.uniform(0, 3600)
            if not (16200 <= t < 86000): continue
            for _ in range(20):
                a, b = random.choice(A), random.choice(B)
                if a != b and odl(a, b) >= mind: trips.append((t, nm, a.getID(), b.getID())); break
trips.sort()
with open('tlo.trips.xml', 'w') as o:
    o.write('<routes>\n  <vType id="auto" vClass="passenger" color="230,200,0"/>\n')
    for i, (t, nm, a, b) in enumerate(trips):
        o.write(f'  <trip id="tlo_{nm}_{i}" type="auto" depart="{t:.0f}" from="{a}" to="{b}" departLane="best"/>\n')
    o.write('</routes>\n')
from collections import Counter
print('przejazdy:', len(trips), dict(Counter(x[1] for x in trips)))
