"""Ruch tła (samochody), bliższy rzeczywistości niż losowe przejazdy przez całą mapę:
- dużo krótkich przejazdów w samym Lublińcu (miasto ~22 tys. mieszkańców),
- przejazdy z okolicy do Lublińca i z powrotem,
- mniej przejazdów między wsiami i tranzytu po drogach wojewódzkich,
- rano 6–8 i po południu 14–17 ruch większy, w nocy mały.
Wynik: tlo.trips.xml → duarouter → tlo.rou.xml(.gz)."""
import os, sys, random, math
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
random.seed(42)
n = sumolib.net.readNet(sys.argv[1] if len(sys.argv) > 1 else 'koszecin.net.xml.gz', withPrograms=False)
LUB = (18.655, 50.640, 18.725, 50.695)          # Lubliniec (lon_min, lat_min, lon_max, lat_max)
def w_lub(e):
    lon, lat = n.convertXY2LonLat(*e.getFromNode().getCoord())
    return LUB[0] <= lon <= LUB[2] and LUB[1] <= lat <= LUB[3]
E = [e for e in n.getEdges() if e.allows('passenger') and not e.getID().startswith(':') and e.getLength() > 30 and not e.allows('rail')]
miasto = [e for e in E if w_lub(e)]; okolica = [e for e in E if not w_lub(e)]
def odl(a, b): return math.dist(a.getFromNode().getCoord(), b.getToNode().getCoord())
def profil(t):                                   # mnożnik natężenia wg godziny
    h = t / 3600
    if h < 5.5 or h >= 22: return 0.25
    if 6 <= h < 8 or 14 <= h < 17: return 1.6
    return 1.0
GRUPY = [  # (nazwa, co ile sekund przy mnożniku 1, skąd, dokąd, min. odległość [m])
    ('miasto',   3.0, miasto, miasto, 600),
    ('do_lub',  12.0, okolica, miasto, 2000),
    ('z_lub',   12.0, miasto, okolica, 2000),
    ('okolica', 14.0, okolica, okolica, 2000),
]
trips = []
for nm, co, A, B, mind in GRUPY:
    t = 16200.0
    while t < 86000:
        t += random.expovariate(profil(t) / co)
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
