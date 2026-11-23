"""Ograniczenia prędkości jak w Polsce: 50 km/h w terenie zabudowanym, 90 km/h poza nim (droga krajowa/wojewódzka).
Wycinek OSM nie ma tagów maxspeed, więc teren zabudowany = obszary landuse=residential/retail/commercial (z buforem 50 m).
Wynik: predkosci.edg.xml do nałożenia na sieć (netconvert -s ... -e predkosci.edg.xml)."""
import json, os, sys
from shapely.geometry import shape, Point, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
g = json.load(open(sys.argv[1]))
n = sumolib.net.readNet('koszecin.net.xml', withPrograms=False)   # przed spakowaniem (zbuduj.sh)
P = [shape(f['geometry']) for f in g['features'] if f['geometry']['type'] in ('Polygon', 'MultiPolygon')
     and f['properties'].get('landuse') in ('residential', 'retail', 'commercial')]
P = [p.buffer(0.0007) for p in P if p.is_valid or p.buffer(0).is_valid]
tree = STRtree(P)
zm = 0
with open('predkosci.edg.xml', 'w') as o:
    o.write('<edges>\n')
    for e in n.getEdges():
        if not e.allows('passenger') or e.getID().startswith(':'): continue
        sh = [n.convertXY2LonLat(x, y) for x, y in e.getShape()]
        mid = LineString(sh).interpolate(0.5, normalized=True)
        wew = any(P[i].contains(mid) for i in tree.query(mid))
        v = e.getSpeed()
        nowa = min(v, 13.89) if wew else min(v, 25.0)   # 50 km/h zabudowa, 90 km/h poza
        if abs(nowa - v) > 0.01:
            o.write(f'  <edge id="{e.getID()}" speed="{nowa:.2f}"/>\n'); zm += 1
    o.write('</edges>\n')
print('zmienione krawędzie:', zm)
