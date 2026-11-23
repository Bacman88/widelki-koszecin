import json,math,networkx as nx
from shapely.geometry import shape,box,mapping
from shapely.ops import unary_union
d=json.load(open('dane/osm/osm_gmina.geojson'))
B=(18.60,50.52,19.10,50.78)
bb=box(*B)
R=lambda v:round(v,5)
roads={'major':[],'minor':[]};rails=[];forest=[];G=nx.Graph()
drive={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','motorway_link','trunk_link','primary_link','secondary_link','tertiary_link'}
def hav(a,b):
    dx=(a[0]-b[0])*math.cos(math.radians(50.6))*111.32;dy=(a[1]-b[1])*110.57;return math.hypot(dx,dy)
for ft in d['features']:
    g=ft['geometry'];p=ft['properties'];t=g['type']
    if t in('LineString','MultiLineString'):
        hw=p.get('highway');rw=p.get('railway')
        lines=[g['coordinates']] if t=='LineString' else g['coordinates']
        for c in lines:
            if not any(B[0]<=x<=B[2] and B[1]<=y<=B[3] for x,y in c): continue
            if hw in drive:
                f=1 if hw in drive else (1.6 if hw=='service' else (1.4 if p.get('tracktype') in ('grade1',) or p.get('surface') in ('asphalt','paved','concrete') else 4))
                for a,b in zip(c,c[1:]):
                    G.add_edge(tuple(a),tuple(b),w=hav(a,b)*f,km=hav(a,b))
            if hw in drive:
                s=shape({'type':'LineString','coordinates':c}).simplify(0.00008)
                k='major' if hw in('trunk','primary','secondary','tertiary','motorway') else ('minor' if hw in ('unclassified','residential') else None)
                if k: roads[k].append([[R(y),R(x)] for x,y in s.coords])
            elif rw=='rail' and p.get('service') is None:
                s=shape({'type':'LineString','coordinates':c}).simplify(0.00008)
                rails.append([[R(y),R(x)] for x,y in s.coords])
    elif t in('Polygon','MultiPolygon') and (p.get('landuse')=='forest' or p.get('natural')=='wood'):
        try:
            s=shape(g)
            if s.intersects(bb) and s.area>2e-6: forest.append(s.intersection(bb))
        except Exception: pass
fu=unary_union(forest).simplify(0.0009)
fpolys=[]
for poly in getattr(fu,'geoms',[fu]):
    if poly.area<4e-6: continue
    rings=[[[R(y),R(x)] for x,y in poly.exterior.coords]]+[[[R(y),R(x)] for x,y in i.coords] for i in poly.interiors if shape({'type':'Polygon','coordinates':[list(i.coords)]}).area>4e-6]
    fpolys.append(rings)
gm=json.load(open('dane/gmina_koszecin.geojson'))['features'][0]['geometry']
gms=shape(gm).simplify(0.0003)
gmr=[[R(y),R(x)] for x,y in gms.exterior.coords]
# routing
nodes=list(G.nodes)
big=max(nx.connected_components(G),key=len);H=G.subgraph(big)
driveN=set()
hn=[n for n in H.nodes if H.degree(n)>0]
def snap(lat,lon):
    return min(hn,key=lambda n:(n[0]-lon)**2+(n[1]-lat)**2)
def route(pts):
    out=[];km=0
    for a,b in zip(pts,pts[1:]):
        p=nx.shortest_path(H,snap(*a),snap(*b),weight='w');km+=nx.path_weight(H,p,'km')
        out+= [list(x) for x in p] if not out else [list(x) for x in p[1:]]
    s=shape({'type':'LineString','coordinates':out}).simplify(0.00012)
    RAW.append([[round(y,6),round(x,6)] for x,y in out])
    return [[R(y),R(x)] for x,y in s.coords],round(km,1)
RAW=[]
S={ 'lubpkp':(50.6726,18.6910,'Lubliniec PKP','hubz'),'lisp':(50.7211,18.7922,'Lisów PKP','hubz'),'chw':(50.7185,18.8069,'Chwostek','ist'),'moc':(50.7037,18.8211,'Mochała','nowy'),'dol':(50.6949,18.8349,'Hadra','ist'),'sad':(50.6718,18.7409,'Sadów Przedszkole','ist'),'wie':(50.6654,18.7749,'Wierzbie','ist'),
'irk':(50.6502,18.8107,'Rzyce Irki','ist'),'kosr':(50.6362,18.8411,'Koszęcin Rynek','hub'),'kosp':(50.62285,18.83705,'Koszęcin PKP','nowy'),'kossz':(50.6321,18.84156,'Koszęcin Szkoła','ist'),'str':(50.6150,18.9007,'Strzebiń Lubliniecka','ist'),'strs':(50.61755,18.90364,'Strzebiń Szkoła','ist'),
'buk':(50.6071,18.9408,'Bukowiec','ist'),'psk':(50.6018,18.9541,'Płaszczymąka (Psary Skrzyżowanie)','ist'),'pia':(50.5950,18.9675,'Piasek','hubz'),'bor':(50.6739,18.9038,'Boronów','hubz'),'borp':(50.6654,18.9014,'Boronów PKP','nowy'),'bru':(50.5856,18.8115,'Brusiek','hubz'),'kalp':(50.5664,18.8883,'Kalety PKP','hubz'),
'cie':(50.6712,18.8362,'Cieszowa','ist'),'rus':(50.6494,18.7637,'Rusinowice PKP','ist'),'pil':(50.6275,18.7585,'Piłka','ist'),'laz':(50.6345,18.9315,'Łazy','ist'),'psy':(50.6135,18.9664,'Psary (szkoła)','ist')}
L={'1':['pia','psk','buk','str','@li','kosr','irk','wie','sad','lubpkp'],'2':['bor','borp','@sk','kosr','kossz','@dw','kosp','@tr','@sj','bru','kalp'],'3':['lisp','chw','moc','dol','cie','kosr','kossz','@dw','kosp','@tr','@sj','kossz','kosr'],'4':['laz','strs','str','@li','@sj','@tr','kosp','@dw','kossz','kosr','irk','wie','rus','pil'],'1L':['kosr','irk','wie','sad','lubpkp'],'4S':['str','buk','psk','psy'],'4P':['laz','psy']}
lines={}
WP={'@dw':(50.6248,18.8406),'@tr':(50.6214,18.8415),'@sj':(50.6214,18.8437),'@li':(50.6346,18.8432),'@sk':(50.6377,18.8435),'@sjn':(50.6258,18.8431),'@lj':(50.6345,18.8412)}
for k,seq in L.items():
    geom,km=route([(WP[x] if x in WP else S[x][:2]) for x in seq]);lines[k]={'geom':geom,'km':({'4S':10.6,'4P':13.8}.get(k,km)),'stops':[x for x in seq if x not in WP],'path':RAW[-1]};print(k,km,len(geom))
st=[]
for ft in d['features']:
    g=ft['geometry'];p=ft['properties']
    if g['type']=='Point' and p.get('railway') in ('station','halt') and B[0]<=g['coordinates'][0]<=B[2] and B[1]<=g['coordinates'][1]<=B[3]: st.append([R(g['coordinates'][1]),R(g['coordinates'][0]),p.get('name','')])
for k_,v_ in list(S.items()):
    n_=snap(v_[0],v_[1])
    if hav((n_[0],n_[1]),(v_[1],v_[0]))<0.8: S[k_]=(R(n_[1]),R(n_[0]))+tuple(v_[2:])
import os
BS=json.load(open('dane/busstops.json')) if os.path.exists('dane/busstops.json') else []
data={'busstops':BS,'stations':st,'roads':roads,'rails':rails,'forest':fpolys,'gmina':gmr,'stops':{k:list(v) for k,v in S.items()},'lines':lines}
s=json.dumps(data,separators=(',',':'),ensure_ascii=False)
open('out/data.json','w').write(s);print('bytes',len(s),'major',len(roads['major']),'minor',len(roads['minor']),'rails',len(rails),'forest',len(fpolys))
