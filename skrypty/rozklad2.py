import json,math
B=json.load(open('out/rozklad_base.json'))
WD=[6,7,8,10,12,13,14,15,16,17,18,20,22];SAT=[7,9,11,13,15,17,19,21];SUN=[8,11,14,17,20]
DEM={'wd':{'3':[10,12,20]},'sat':{'3':'all','4':'all'},'sun':{'3':'all','4':'all'}}
THROUGH={'1','2','4'}
OFF={'1':((-7,-5),(0,2)),'2':((-11,3),(-11,3)),'4':((-2,3),(-11,3))}
def trips_for(k,H):
    b=B[k];t=b['t'];seq=b['names'];ir=seq.index('Koszęcin Rynek')
    res=[]
    def through(seq_,t_,arr,dep,lab):
        idx=[i for i,n in enumerate(seq_) if n=='Koszęcin Rynek'];jr=idx[0];j2=idx[-1]
        if j2>jr:
            assert arr+(t_[j2]-t_[jr])<=dep, ('loop too long',lab)
            seq_=list(seq_);seq_[j2]='Koszęcin Rynek (odjazd)'
            tt=[(arr-(t_[jr]-x)) if i<jr else ((arr+(x-t_[jr])) if i<j2 else (dep+(x-t_[j2]))) for i,x in enumerate(t_)]
        else:
            tt=[(arr-(t_[jr]-x)) if i<jr else (arr if i==jr else dep+(x-t_[jr])) for i,x in enumerate(t_)]
        res.append((lab,seq_,[round(v) for v in tt],b['km'][-1]))
    if k in THROUGH:
        (a1,d1),(a2,d2)=OFF[k]
        through(seq,t,H*60+a1,H*60+d1,'A')
        rt=[t[-1]-x for x in t][::-1];rs=seq[::-1]
        through(rs,rt,H*60+a2,H*60+d2,'B')
    else:
        arr=H*60-11
        res.append(('do węzła',seq,[round(arr-(t[ir]-x)) for x in t],b['km'][-1]))
        rs=seq[::-1];rt=[t[-1]-x for x in t][::-1];jr=rs.index('Koszęcin Rynek');dep=H*60+3
        res.append(('z węzła',rs,[round(dep-(rt[jr]-x)) for x in rt],b['km'][-1]))
    return res
def build(day,P):
    out={}
    for k in B:
        dem=DEM[day].get(k,[])
        trips=[]
        for H in P:
            d=(dem=='all') or (H in dem)
            for tr in trips_for(k,H): trips.append(tr+(d,))
        out[k]=trips
    return out
def vehicles(trips,lay=4):
    tr=sorted([(x[2][0],x[1][0],x[2][-1],x[1][-1]) for x in trips if not x[4]])
    free=[];n=0
    for s,a,e,b in tr:
        ok=[i for i,(t,p) in enumerate(free) if p==a and t+lay<=s]
        if ok: free.pop(ok[0])
        else: n+=1
        free.append((e,b))
    return n
days={'wd':(WD,250),'sat':(SAT,52),'sun':(SUN,63)}
R={}
for d,(P,nd) in days.items():
    R[d]=build(d,P)
summary={}
for k in B:
    row={}
    for d,(P,nd) in days.items():
        tr=R[d][k];fixed=[x for x in tr if not x[4]];dem=[x for x in tr if x[4]]
        km_fixed=sum(x[3] for x in fixed);km_dem=sum(x[3] for x in dem)*0.5
        row[d]={'kursy':len(fixed),'zam':len(dem),'km_dzien':round(km_fixed+km_dem,1),'bus':vehicles(tr),'dni':nd}
    row['km_rok']=round(sum(row[d]['km_dzien']*days[d][1] for d in days))
    summary[k]=row
    print(k,row)
tot=sum(v['km_rok'] for v in summary.values());print('TOTAL km/rok',tot)
peak=0
# fleet: peak simultaneous over all lines on weekday (sum of per-line vehicles)
print('bus wd',sum(summary[k]['wd']['bus'] for k in summary))
json.dump({'trips':R,'summary':summary,'total':tot},open('out/rozklad_out.json','w'),ensure_ascii=False)
fm=lambda m:f"{m//60}:{m%60:02d}"
for x in R['wd']['1'][:4]: print(x[0],[ (n,fm(t)) for n,t in zip(x[1],x[2])])
for x in R['wd']['5'][:2]: print(x[0],[ (n,fm(t)) for n,t in zip(x[1],x[2])])
