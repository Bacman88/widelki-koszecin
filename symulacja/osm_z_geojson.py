"""Buduje plik OSM XML (do netconvert) z wycinka osm_gmina.geojson: drogi, tory, przejazdy kolejowe.
Węzły odtwarzane po współrzędnych (wspólne punkty dróg i torów = te same węzły)."""
import json, sys
from xml.sax.saxutils import quoteattr
SRC = sys.argv[1]; OUT = sys.argv[2]
BBOX = (18.66, 50.575, 18.99, 50.755)  # lon_min, lat_min, lon_max, lat_max – obszar linii + Lubliniec, Kalety, Lisów, Psary
DROGI = {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street',
         'motorway_link','trunk_link','primary_link','secondary_link','tertiary_link','service'}
TAGI = {'highway','name','ref','oneway','maxspeed','lanes','junction','railway','service','access','motor_vehicle','layer','bridge','tunnel'}
g = json.load(open(SRC))
def w(lon, lat): return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]
nid = {}; ntag = {}; ways = []
def node(lon, lat):
    k = (round(lon, 7), round(lat, 7))
    if k not in nid: nid[k] = len(nid) + 1
    return nid[k]
for f in g['features']:
    p = f.get('properties', {}); t = f['geometry']['type']
    if t == 'LineString':
        hw = p.get('highway'); rw = p.get('railway')
        if not ((hw in DROGI and p.get('service') not in ('parking_aisle', 'driveway', 'drive-through')) or rw == 'rail'): continue
        if p.get('access') in ('private', 'no') or p.get('motor_vehicle') in ('private', 'no'): continue
        cs = f['geometry']['coordinates']
        if not any(w(x, y) for x, y in cs): continue
        ways.append(([node(x, y) for x, y in cs], {k: v for k, v in p.items() if k in TAGI}))
    elif t == 'Point' and p.get('railway') == 'level_crossing':
        x, y = f['geometry']['coordinates']
        k = (round(x, 7), round(y, 7)); ntag[k] = {'railway': 'level_crossing'}
inv = {v: k for k, v in nid.items()}
with open(OUT, 'w') as o:
    o.write('<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6" generator="widelki-koszecin">\n')
    for i in sorted(inv):
        (x, y) = inv[i]; tg = ntag.get(inv[i])
        if tg: o.write(f' <node id="{i}" lat="{y}" lon="{x}" version="1">' + ''.join(f'<tag k="{k}" v={quoteattr(v)}/>' for k, v in tg.items()) + '</node>\n')
        else: o.write(f' <node id="{i}" lat="{y}" lon="{x}" version="1"/>\n')
    for j, (ns, tg) in enumerate(ways, 1):
        o.write(f' <way id="{j}" version="1">' + ''.join(f'<nd ref="{n}"/>' for n in ns) + ''.join(f'<tag k="{k}" v={quoteattr(str(v))}/>' for k, v in tg.items()) + '</way>\n')
    o.write('</osm>\n')
print('węzły', len(nid), 'drogi/tory', len(ways), 'przejazdy (na mapie)', sum(1 for k in ntag if k in nid))
