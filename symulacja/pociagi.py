"""Pociągi przez przejazdy kolejowe leżące na trasach busów (przybliżenie: pociąg co 30 min, 4:30–23:00).
Dla każdego przejazdu: trasa po torach od brzegu mapy do brzegu mapy przez ten przejazd, w obie strony."""
import os, re, sys, random
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
random.seed(7)
n = sumolib.net.readNet('koszecin.net.xml.gz', withPrograms=False)
xmin, ymin, xmax, ymax = n.getBoundary()
def brzeg(node, m=1500):
    x, y = node.getCoord(); return min(x - xmin, xmax - x, y - ymin, ymax - y) < m
rail = [e for e in n.getEdges() if e.allows('rail') and not e.allows('passenger')]
zrodla = [e for e in rail if brzeg(e.getFromNode()) and not any(i.allows('rail') for i in e.getFromNode().getIncoming() if i.getFromNode() != e.getToNode())]
ujscia = [e for e in rail if brzeg(e.getToNode()) and not any(o.allows('rail') for o in e.getToNode().getOutgoing() if o.getToNode() != e.getFromNode())]
uzyte = set()
for m in re.finditer(r'<route edges="([^"]*)"', open('busy.rou.xml').read()): uzyte |= set(m.group(1).split())
klastry = []
for j in n.getNodes():
    if j.getType() != 'rail_crossing' or not ({e.getID() for e in j.getIncoming()} & uzyte): continue
    x, y = j.getCoord(); rin = [e for e in j.getIncoming() if e.allows('rail') and not e.allows('passenger')]
    for k in klastry:   # kilka torów obok siebie = jeden przejazd (wszystkie tory)
        if abs(x - k[0]) < 400 and abs(y - k[1]) < 400: k[2].extend(rin); break
    else: klastry.append((x, y, rin))
trasy = {}
for x, y, rin in klastry:
    for r in rin:
        best_up = min((p for p in (n.getShortestPath(s, r, vClass='rail')[0] for s in zrodla) if p), key=len, default=None)
        best_dn = min((p for p in (n.getShortestPath(r, t, vClass='rail')[0] for t in ujscia) if p), key=len, default=None)
        if best_up and best_dn:
            ed = [e.getID() for e in best_up] + [e.getID() for e in best_dn[1:]]
            trasy.setdefault(tuple(ed), n.convertXY2LonLat(x, y))
# Lubliniec to węzeł kolejowy (magistrala węglowa + linie pasażerskie): na przejeździe przy Kopcach
# łącznie ok. 9 pociągów na godzinę na wszystkich torach, co drugi towarowy (600 m, 60 km/h – długie zamknięcie rogatek).
# Pozostałe przejazdy: pociąg pasażerski co godzinę na każdym torze i kierunku.
LUB = (18.70, 50.66, 18.73, 50.68)
def w_lub(lon, lat): return LUB[0] <= lon <= LUB[2] and LUB[1] <= lat <= LUB[3]
with open('pociagi.rou.xml', 'w') as o:
    o.write('<routes>\n  <vType id="pociag" vClass="rail" length="75" maxSpeed="33" accel="0.6" decel="0.9" guiShape="rail" color="80,80,80"/>\n')
    o.write('  <vType id="towarowy" vClass="rail" length="600" maxSpeed="16.7" accel="0.25" decel="0.5" guiShape="rail/cargo" color="40,40,40"/>\n')
    v = []
    for k, (ed, (lon, lat)) in enumerate(trasy.items()):
        off = random.randint(0, 44) * 60
        if w_lub(lon, lat):
            for i, t in enumerate(range(4 * 3600 + off, 23 * 3600, 45 * 60)):
                v.append((t, f'pociag{k}_{i}', ed, 'towarowy' if i % 2 else 'pociag'))
        else:
            for i, t in enumerate(range(4 * 3600 + off * 3, 23 * 3600, 3600)):
                v.append((t, f'pociag{k}_{i}', ed, 'pociag'))
    for dep, vid, ed, typ in sorted(v):
        o.write(f'  <vehicle id="{vid}" type="{typ}" depart="{dep}" departLane="best"><route edges="{" ".join(ed)}"/></vehicle>\n')
    o.write('</routes>\n')
print('przejazdy na trasach busów:', len(klastry), 'trasy pociągów:', len(trasy), 'pociągów:', len(v))
for ed, (lon, lat) in trasy.items(): print(f'  przez przejazd {lat:.4f},{lon:.4f}: {len(ed)} odcinków')
