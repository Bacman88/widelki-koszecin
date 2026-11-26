"""Rozkład dojazdów koleją: stacje Rusinowice, Koszęcin, Strzebiń ⇄ Lubliniec, Częstochowa, Tarnowskie Góry, Katowice, Opole.
Na podstawie danych wyszukiwarki (busy z proponowanego rozkładu + pociągi z GTFS). Uruchom z katalogu symulacja/.
Wynik: ../strona/dojazdy/index.html (z szablonu ../strona/dojazdy/szablon.html).
"""
import json,collections
D=json.load(open('../strona/wyszukiwarka/dane.json'))
f=lambda m:f'{m//60}:{m%60:02d}'
NM={k:v['n'].replace(' – stacja kolejowa','') for k,v in D['przystanki'].items()}
def run(dz,BEZ_IC=True,BEZ_BUS=False):
    K=D['dni'][dz]
    foot=collections.defaultdict(list)
    for a,b,m in D['piesze']: foot[a].append((b,m)); foot[b].append((a,m))
    conns=sorted((da,ab,a,b,ti,i) for ti,k in enumerate(K) if not (BEZ_IC and k['l']=='IC') and not (BEZ_BUS and k['l'] in '12345') for i,((a,_,da,_),(b,ab,_,_)) in enumerate(zip(k['p'],k['p'][1:])))
    def csa(src,t0,dst):
        INF=10**9; T=collections.defaultdict(lambda:INF); P={}
        T[src]=t0
        for b,m in foot[src]: T[b]=t0+m; P[b]=('pieszo',src,t0,t0+m)
        trip={}
        for d,a,x,y,ti,i in conns:
            if d<t0 or d>T[dst]: 
                if d>T[dst]: break
                continue
            k=K[ti]; bus=k['l'] in '12345'
            if ti not in trip:
                prev=P.get(x); margin=2 if bus else 4
                if prev and prev[0]=='pieszo': margin=2 if bus else 3
                if x==src: margin=0
                if T[x]+margin<=d: trip[ti]=(x,d)
                else: continue
            if a<T[y]:
                T[y]=a; P[y]=('jazda',ti,trip[ti][0],trip[ti][1],a)
                for b,m in foot[y]:
                    if a+m<T[b]: T[b]=a+m; P[b]=('pieszo',y,a,a+m)
        if T[dst]>=INF: return None
        legs=[]; s=dst
        while s!=src:
            p=P[s]
            if p[0]=='pieszo': s=p[1]; continue
            _,ti,bx,bd,a=p; legs.append((K[ti],bx,bd,s,a)); s=bx
        legs.reverse()
        # przesiadka na pierwszej wspólnej stacji (bez dojeżdżania dalej i cofania się drugim pociągiem)
        for j in range(len(legs)-1):
            k1,bx,bd,ay,a=legs[j]; k2,bx2,bd2,ay2,a2=legs[j+1]
            if k1['l'] in '12345' or k2['l'] in '12345' or bx2!=ay: continue
            s1=[q[0] for q in k1['p']]; s2=[q[0] for q in k2['p']]
            i0,i1=s1.index(bx),s1.index(ay); j0,j1=s2.index(bx2),s2.index(ay2)
            for i in range(i0+1,i1):
                st_=s1[i]
                if st_ in s2[j0:j1] and s2.index(st_)<j1:
                    jj=s2.index(st_)
                    if k1['p'][i][1]+3<=k2['p'][jj][2]:
                        legs[j]=(k1,bx,bd,st_,k1['p'][i][1]); legs[j+1]=(k2,st_,k2['p'][jj][2],ay2,a2); break
        return legs
    return csa
def opis(legs):
    out=[]
    for k,bx,bd,ay,a in legs:
        bus=k['l'] in '12345'
        zam=any(p[3] for p in k['p'] if p[0] in (bx,ay))
        out.append({'t':'bus' if bus else k['l'],'l':k['l'] if bus else (k.get('nr','').split(' ')[0] if k['l']!='IC' else 'IC'),
                    'nr':'' if bus else k.get('nr',''),'z':NM[bx],'zt':bd,'do':NM[ay],'dt':a,'zam':bool(zam)})
    return out
TRYBY={'kolej':{'st_Rusinowice':'Rusinowice','st_Koszęcin':'Koszęcin','st_Strzebiń':'Strzebiń','st_Lubliniec':'Lubliniec'},
       'bus':{'kosr':'Koszęcin (Rynek)','str':'Strzebiń (Centrum)','rus':'Rusinowice','sad':'Sadów','wie':'Wierzbie','pil':'Piłka',
              'cie':'Cieszowa','laz':'Łazy','buk':'Bukowiec','pia':'Piasek','bor':'Boronów','bru':'Brusiek','lubpkp':'Lubliniec'}}
CE={'st_Lubliniec':'Lubliniec','st_Częstochowa':'Częstochowa','st_Tarnowskie Góry':'Tarnowskie Góry','st_Katowice':'Katowice','st_Opole Główne':'Opole Główne'}
CEL={'st_Koszęcin':'Koszęcin','st_Strzebiń':'Strzebiń','st_Rusinowice':'Rusinowice','st_Boronów':'Boronów','st_Kalety':'Kalety',
     'st_Lisów':'Lisów','st_Kochanowice':'Kochanowice','st_Herby Stare':'Herby Stare','st_Herby Nowe':'Herby Nowe'}
TEN_SAM={('kosr','st_Koszęcin'),('str','st_Strzebiń'),('rus','st_Rusinowice'),('lubpkp','st_Lubliniec')}
BLISKO={'st_Lubliniec',*CEL}
WYN={}
for tryb,ZR in TRYBY.items():
  bez_bus=tryb=='kolej'
  for dz in ('wd','sat','sun'):
    csa_r=run(dz,True,bez_bus); csa_ic=run(dz,False,bez_bus)
    for z in ZR:
        for c in {**CE,**CEL}:
            if z==c or (z,c) in TEN_SAM: continue
            csa=csa_ic if c=='st_Opole Główne' else csa_r
            for kier,(A,B) in (('tam',(z,c)),('powrot',(c,z))):
                best={}
                for t0 in range(4*60,23*60):
                    L=csa(A,t0,B)
                    if not L: continue
                    dep=L[0][2]; arr=L[-1][4]
                    if dep<t0: continue
                    key=arr
                    if key not in best or best[key][0]<dep or (best[key][0]==dep and len(best[key][2])>len(L)): best[key]=(dep,arr,L)
                lst=sorted(best.values())
                # usuń zdominowane (późniejszy wyjazd i wcześniejszy przyjazd) i bardzo długie
                fin=[x for x in lst if not any(y[0]>=x[0] and y[1]<=x[1] and y!=x for y in lst)]
                if fin:
                    mn=min(x[1]-x[0] for x in fin)
                    fin=[x for x in fin if x[1]-x[0]<=(max(mn+25, mn*2) if c in BLISKO else max(mn+60, mn*1.7))]   # do Lublińca blisko: bez objazdów
                WYN.setdefault(tryb,{}).setdefault(dz,{}).setdefault(z,{}).setdefault(c,{})[kier]=[{'odj':x[0],'prz':x[1],'czas':x[1]-x[0],'przes':len(x[2])-1,'ic':any(l[0]['l']=='IC' for l in x[2]),'jak':opis(x[2])} for x in fin]
_dane=json.dumps({'TRYBY':TRYBY,'CE':CE,'CEL':CEL,'WYN':WYN},ensure_ascii=False,separators=(',',':'))
open('../strona/dojazdy/index.html','w').write(open('../strona/dojazdy/szablon.html').read().replace('__DATA__',_dane))
print('../strona/dojazdy/index.html', {t:{dz:sum(len(v) for z in WYN[t][dz].values() for c in z.values() for v in c.values()) for dz in WYN[t]} for t in WYN})
