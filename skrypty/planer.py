import json
D=json.load(open('out/rozklad_data.json'))['tt']
def norm(n): return 'Koszęcin Rynek' if n.startswith('Koszęcin Rynek') else n
conns=[];tid=0
for k,days in D.items():
    for dr,v in days['wd'].items():
        for t,z in v['trips']:
            st=[norm(x) for x in v['stops']]
            for i in range(len(st)-1):
                dep=t[i]
                if st[i]=='Koszęcin Rynek' and t[i+1]-t[i]>6: dep=((t[i]+11)//60)*60+3
                conns.append((dep,t[i+1],st[i],st[i+1],tid,k,z))
            tid+=1
conns.sort()
MT=2
def earliest(src,t0,dst):
    best={src:t0};trip={};prev={}
    for dep,arr,a,b,ti,k,z in conns:
        if dep<t0: continue
        ok = ti in trip or (a in best and best[a]+(0 if a==src and best[a]==t0 else MT)<=dep)
        if not ok: continue
        if ti not in trip: trip[ti]=(a,dep,k)
        if arr<best.get(b,10**9):
            best[b]=arr;prev[b]=(ti,trip[ti],a)
    if dst not in best: return None
    # reconstruct legs
    legs=[];cur=dst
    while cur!=src:
        ti,(ba,bd,k),a=prev[cur]
        legs.append((k,ba,bd));
        # find board stop
        cur=ba
    return best[dst],legs[::-1]
def latest_by(src,dst,dead):
    deps=sorted({c[0] for c in conns if c[2]==src and c[0]<=dead},reverse=True)
    for d in deps:
        r=earliest(src,d,dst)
        if r and r[0]<=dead: return d,r
    return None
f=lambda t:'%d:%02d'%divmod(t,60)
ORIG=['Strzebiń Lubliniecka','Strzebiń Szkoła','Bukowiec','Łazy','Koszęcin Rynek','Rzyce Irki','Wierzbie','Sadów Przedszkole','Rusinowice PKP','Piłka','Cieszowa','Doły','Brusiek']
L='Lubliniec PKP'
def desc(legs):
    return ' → '.join(f"linia {k} {f(d)} z {s}" for k,s,d in legs)
print('=== DO LUBLIŃCA: praca na 7:00 (przyjazd do 6:40), szkoła na 8:00 (przyjazd do 7:40)')
for o in ORIG:
    out=[]
    for dead in (6*60+40,7*60+40):
        r=latest_by(o,L,dead)
        out.append(f"{f(r[0])}→{f(r[1][0])} [{desc(r[1][1])}]" if r else '—')
    print(o,'|',out[0],'|',out[1])
print('=== Z LUBLIŃCA')
for t0 in (14*60+30,15*60+30,16*60+30):
    print('--- odjazd po',f(t0))
    for o in ORIG:
        r=earliest(L,t0,o)
        print(o,'|',f"{f(r[1][0][2])}→{f(r[0])} [{desc(r[1])}]" if r else '—')
