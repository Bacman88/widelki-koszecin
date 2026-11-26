"""Rozkład dojazdów koleją: stacje Rusinowice, Koszęcin, Strzebiń ⇄ Lubliniec, Częstochowa, Tarnowskie Góry, Katowice, Opole.
Na podstawie danych wyszukiwarki (busy z proponowanego rozkładu + pociągi z GTFS). Uruchom z katalogu symulacja/.
Wynik: ../strona/dojazdy/index.html (z szablonu ../strona/dojazdy/szablon.html).
"""
import json,collections
D=json.load(open('../strona/wyszukiwarka/dane.json'))
f=lambda m:f'{m//60}:{m%60:02d}'
NM={k:v['n'].replace(' – stacja kolejowa','') for k,v in D['przystanki'].items()}
def run(dz,BEZ_IC=True):
    K=D['dni'][dz]
    foot=collections.defaultdict(list)
    for a,b,m in D['piesze']: foot[a].append((b,m)); foot[b].append((a,m))
    conns=sorted((da,ab,a,b,ti,i) for ti,k in enumerate(K) if not (BEZ_IC and k['l']=='IC') for i,((a,_,da,_),(b,ab,_,_)) in enumerate(zip(k['p'],k['p'][1:])))
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
        legs.reverse(); return legs
    return csa
def opis(legs):
    out=[]
    for k,bx,bd,ay,a in legs:
        bus=k['l'] in '12345'
        zam=any(p[3] for p in k['p'] if p[0] in (bx,ay))
        out.append({'t':'bus' if bus else k['l'],'l':k['l'] if bus else (k.get('nr','').split(' ')[0] if k['l']!='IC' else 'IC'),
                    'nr':'' if bus else k.get('nr',''),'z':NM[bx],'zt':bd,'do':NM[ay],'dt':a,'zam':bool(zam)})
    return out
ZR={'st_Rusinowice':'Rusinowice','st_Koszęcin':'Koszęcin','st_Strzebiń':'Strzebiń'}
CE={'st_Lubliniec':'Lubliniec','st_Częstochowa':'Częstochowa','st_Tarnowskie Góry':'Tarnowskie Góry','st_Katowice':'Katowice','st_Opole Główne':'Opole Główne'}
WYN={}
for dz in ('wd','sat','sun'):
    csa_r=run(dz); csa_ic=run(dz,False)
    for z in ZR:
        for c in CE:
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
                    fin=[x for x in fin if x[1]-x[0]<=(max(mn+25, mn*2) if 'st_Lubliniec' in (A,B) else max(mn+60, mn*1.7))]   # do Lublińca blisko: bez objazdów
                WYN.setdefault(dz,{}).setdefault(z,{}).setdefault(c,{})[kier]=[{'odj':x[0],'prz':x[1],'czas':x[1]-x[0],'przes':len(x[2])-1,'ic':any(l[0]['l']=='IC' for l in x[2]),'jak':opis(x[2])} for x in fin]
_dane=json.dumps({'ZR':ZR,'CE':CE,'WYN':WYN},ensure_ascii=False,separators=(',',':'))
open('../strona/dojazdy/index.html','w').write(open('../strona/dojazdy/szablon.html').read().replace('__DATA__',_dane))
print('../strona/dojazdy/index.html', {dz:sum(len(WYN[dz][z][c][k]) for z in WYN[dz] for c in WYN[dz][z] for k in WYN[dz][z][c]) for dz in WYN})
