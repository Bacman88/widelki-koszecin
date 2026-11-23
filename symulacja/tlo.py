"""Ruch tła (samochody) skalibrowany do pomiarów ruchu.

Źródła natężeń (średni dobowy ruch roczny, SDRR, pojazdy/dobę, oba kierunki razem):
- drogi wojewódzkie: GPR 2020, Zarząd Dróg Wojewódzkich w Katowicach,
  „Zestawienie wartości średniodobowego ruchu w roku na drogach wojewódzkich województwa śląskiego”
  https://bip.slaskie.pl/resource/46056/ (tabela 1.2);
- drogi krajowe: GPR 2020/21, GDDKiA, „SDRR w punktach pomiarowych na drogach krajowych”
  https://www.gov.pl/attachment/dfa8d8ef-b8e6-44ce-98e7-eb2d3a4a11e8

Metoda (narzędzia SUMO):
1. Każdy punkt pomiarowy przypisany do krawędzi sieci (oba kierunki) na właściwej drodze (ref z OSM).
2. Doba rozłożona na godziny (szczyty 6–8 i 14–17), w każdą stronę połowa SDRR.
3. Pula kandydujących tras: losowe przejazdy między drogami zbiorczymi i wyższymi, z przewagą wjazdów
   z krawędzi mapy (ruch z zewnątrz), wyznaczone duarouterem.
4. routeSampler.py dobiera z puli tyle tras na godzinę, żeby liczby aut na punktach zgadzały się z pomiarem.
Ulice osiedlowe nie są mierzone, więc auta jeżdżą głównie drogami z pomiarami i ich dojazdami.

Wynik: tlo.rou.xml.gz (oraz wyniki/kalibracja.json: pomiar vs symulowany ruch na punktach).
"""
import os, sys, json, math, random, subprocess, gzip, shutil
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
random.seed(42)
NETF = 'koszecin.net.xml.gz'
GJ = '../dane/osm/osm_gmina.geojson'
n = sumolib.net.readNet(NETF, withPrograms=False)

# (droga, punkt GPR, opis, SDRR, przybliżone położenie odcinka lat, lon)
POMIARY = [
    ('906', 24247, 'Lubliniec, przejście 1: DK46 – Skłodowskiej', 8966, 50.6690, 18.6700),
    ('906', 24248, 'Lubliniec, przejście 2: Skłodowskiej – rondo JP II', 11324, 50.6680, 18.6760),
    ('906', 24253, 'Lubliniec, przejście 3: rondo JP II – Stalmacha', 10556, 50.6688, 18.6830),
    ('906', 24118, 'Lubliniec Stalmacha – Sadów Podlesie', 13333, 50.6705, 18.7200),
    ('906', 24119, 'Sadów, przejście', 8839, 50.6716, 18.7450),
    ('906', 24120, 'Sadów Rusinowicka – Koszęcin', 6789, 50.6580, 18.7950),
    ('906', 24121, 'Koszęcin – Bukowiec', 5209, 50.6240, 18.8720),
    ('906', 24122, 'Bukowiec – Piasek', 5708, 50.6010, 18.9550),
    ('907', 24125, 'Boronów – Koszęcin', 3395, 50.6550, 18.8700),
    ('907', 24126, 'Koszęcin – Brusiek', 4587, 50.6100, 18.8250),
    ('907', 24127, 'Brusiek – Tworóg', 2653, 50.5650, 18.7900),
    ('789', 24055, 'Brusiek – Kalety Koszęcińska', 1522, 50.5760, 18.8500),
    ('789', 24056, 'Kalety, przejście', 3761, 50.5640, 18.8950),
    ('908', 24135, 'Kamienica – Piasek', 2891, 50.6150, 18.9750),
    ('908', 24136, 'Piasek – Sośnica', 7054, 50.5800, 18.9700),
    ('905', 24115, 'Herby – Boronów', 2764, 50.7050, 18.9000),
    ('905', 24117, 'Boronów – Bukowiec', 3054, 50.6400, 18.9250),
    ('11', 78141105, 'Olesno – Lubliniec', 4318, 50.7100, 18.6350),
    ('11', 78240413, 'Lubliniec, obwodnica 1: DK46 – DK46/DW906', 8137, 50.6800, 18.6560),
    ('11', 78340401, 'Lubliniec, obwodnica 2: DW906 – Stalmacha', 5546, 50.6570, 18.6650),
    ('11', 78440414, 'Lubliniec Stalmacha – Tworóg', 6636, 50.6200, 18.7000),
    ('46', 151240405, 'Pawonków – Lubliniec', 6297, 50.6800, 18.6350),
    ('46', 151340722, 'Lubliniec – Kochanowice', 5270, 50.7100, 18.7300),
]
# udział godziny w dobie (dzień roboczy, szczyty rano i po południu)
W = [.25, .2, .2, .25, .45, 1.1, 2.6, 2.4, 1.6, 1.4, 1.4, 1.5, 1.6, 1.8, 2.2, 2.4, 2.3, 1.9, 1.5, 1.2, .9, .7, .5, .35]
W = [w / sum(W) for w in W]

# --- 1. punkt pomiarowy → krawędzie sieci (oba kierunki) ---
from shapely.geometry import shape, Point
from shapely.ops import nearest_points
refs = {}
for f in json.load(open(GJ))['features']:
    r = f['properties'].get('ref'); g = f['geometry']
    if r and g['type'] == 'LineString':
        for x in r.split(';'): refs.setdefault(x, []).append(shape(g))
E = [e for e in n.getEdges() if e.allows('passenger') and not e.allows('rail') and not e.getID().startswith(':')]
punkty = []
for droga, nr, opis, sdrr, lat, lon in POMIARY:
    p = Point(lon, lat)
    q = min((nearest_points(p, g)[1] for g in refs[droga]), key=p.distance)   # najbliższy punkt na drodze o tym numerze
    x, y = n.convertLonLat2XY(q.x, q.y)
    kand = sorted((sumolib.geomhelper.distancePointToPolygon((x, y), e.getShape()), e) for e in E if e.getPriority() >= 7 and e.getLength() > 20)
    d, e = kand[0]
    odwr = [o for o in e.getToNode().getOutgoing() if o.getToNode() == e.getFromNode()]
    kraw = [e.getID()] + [o.getID() for o in odwr[:1]]
    punkty.append({'droga': droga, 'punkt': nr, 'opis': opis, 'sdrr': sdrr, 'krawedzie': kraw, 'ulica': e.getName(), 'odl_m': round(d)})
    if d > 60 or len(kraw) < 2:          # tej drogi nie ma w wycinku sieci albo jest jednokierunkowa – pomijamy
        print('pominięty punkt:', droga, opis, f'(najbliższa krawędź {round(d)} m)'); punkty.pop()

# --- 2. liczniki godzinowe ---
with open('pomiary.edgedata.xml', 'w') as o:
    o.write('<data>\n')
    for h in range(4, 24):
        o.write(f'  <interval id="h{h}" begin="{h * 3600}" end="{(h + 1) * 3600}">\n')
        for p in punkty:
            for k in p['krawedzie']:
                o.write(f'    <edge id="{k}" entered="{p["sdrr"] / len(p["krawedzie"]) * W[h]:.1f}"/>\n')
        o.write('  </interval>\n')
    o.write('</data>\n')

# --- 3. pula tras kandydujących ---
glowne = [e for e in E if e.getPriority() >= 7 and e.getLength() > 30]
def sasiedzi(nd): return {x.getFromNode() for x in nd.getIncoming()} | {x.getToNode() for x in nd.getOutgoing()}
brzeg = [e for e in glowne if len(sasiedzi(e.getFromNode())) == 1]     # droga ucięta na brzegu wycinka mapy: wjazd z zewnątrz
brzeg_do = {e.getID() for e in glowne if len(sasiedzi(e.getToNode())) == 1}
print('krawędzie główne', len(glowne), 'przy brzegu mapy', len(brzeg), 'punkty pomiarowe', len(punkty))
with open('kandydaci.trips.xml', 'w') as o:
    o.write('<routes>\n')
    for i in range(30000):
        a = random.choice(brzeg if random.random() < 0.6 else glowne)
        b = random.choice(glowne)
        if random.random() < 0.6:
            b = random.choice([x for x in glowne if x.getID() in brzeg_do] or glowne)
        if a != b and math.dist(a.getFromNode().getCoord(), b.getToNode().getCoord()) > 1500:
            o.write(f'  <trip id="k{i}" depart="0" from="{a.getID()}" to="{b.getID()}"/>\n')
    o.write('</routes>\n')
B = os.path.join(SUMO_HOME, 'bin')
subprocess.run([f'{B}/duarouter', '-n', NETF, '-r', 'kandydaci.trips.xml', '-o', 'kandydaci.rou.xml', '--ignore-errors',
                '--no-warnings', '--no-step-log', '--repair'], check=True, stderr=subprocess.DEVNULL)

# --- 4. dobór tras do liczników ---
subprocess.run([sys.executable, os.path.join(SUMO_HOME, 'tools', 'routeSampler.py'), '-r', 'kandydaci.rou.xml',
                '--edgedata-files', 'pomiary.edgedata.xml', '-o', 'tlo.rou.xml', '--prefix', 'tlo', '--attributes',
                'type="auto" departLane="best"', '--seed', '42', '--minimize-vehicles', '0.5', '--write-flows', 'number'],
               check=True, stdout=open('wyniki/routeSampler.log', 'w'))
txt = open('tlo.rou.xml').read()
if 'vType id="auto"' not in txt:
    i = txt.index('>', txt.index('<routes')) + 1
    txt = txt[:i] + '\n  <vType id="auto" vClass="passenger" color="230,200,0"/>' + txt[i:]
with gzip.open('tlo.rou.xml.gz', 'wt') as o: o.write(txt)
for f in ('tlo.rou.xml', 'kandydaci.trips.xml', 'kandydaci.rou.xml', 'kandydaci.rou.alt.xml'):
    if os.path.exists(f): os.remove(f)
json.dump(punkty, open('wyniki/punkty_pomiarowe.json', 'w'), ensure_ascii=False, indent=1)
print('ok')
