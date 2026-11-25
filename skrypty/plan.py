import json, os
exec(open('skrypty/rozklad2.py').read().split("days={'wd'")[0])
ALT={'2','4'}
X2={7,16}
X4={6,7,15,16}   # linia 4: w szczytach oba kierunki (praca 7:00 z Piłki, szkoły w Lublińcu z Łaz, powroty)   # linia 2: w szczycie szkolnym oba kierunki (Brusiek – Lubliniec)
def build2(day,P,dem,LH=None):
    out={}
    for k in B:
        d_=dem.get(day,{}).get(k,[]);trips=[]
        PL=[H for H in P if (LH is None or k not in LH.get(day,{}) or H in LH[day][k])]
        for i,H in enumerate(PL):
            d=(d_=='all') or (H in d_)
            tr=trips_for(k,H)
            if k in ALT:
                j=(H%2) if day=='wd' else i%2   # dni robocze: kierunek wg parzystości godziny (pod szkoły)
                if k=='2' and day=='wd' and H in X2:
                    ex=tr[j]; tr=[tr[(j+1)%2]]
                    lab,seq,t,km=ex; kc=B['2']['km']; r=seq.index('Koszęcin Rynek'); kr=kc[B['2']['names'].index('Koszęcin Rynek')]
                    if seq[0]=='Kalety PKP': part=(lab+'S',seq[:r+1],t[:r+1],round(2*(kc[-1]-kr),1))   # + dojazd techniczny
                    else: part=(lab+'S',seq[r:],[t[r+1]-1]+t[r+1:],round(2*(kc[-1]-kr),1))
                    tr.append(part)
                elif k=='4' and day=='wd' and H in X4: pass
                else: tr=[tr[(j+1)%2]] if k=='2' else [tr[j]]
            for x in tr: trips.append(x+(d,))
        if k=='1' and day=='wd' and P and P[-1]==22: trips.append(trips_for('1',23)[1]+(False,))
        out[k]=trips
    return out
VAR={'pelny':({'wd':list(range(6,23)),'sat':[8,10,12,14,16,18,20,22],'sun':[9,12,15,18,20,22]},{'wd':{'3':[10,20]},'sat':{'3':'all','4':'all'},'sun':{'3':'all','4':'all'}},{'wd':{'3':[6,7,8,10,12,14,15,16,18,20]}}),
     'oszczedny':({'wd':[6,7,8,10,12,13,14,15,16,17,18,20,22],'sat':[8,10,12,14,16,18,20],'sun':[10,13,16,19]},{'wd':{'3':[18]},'sat':{'3':'all','4':'all'},'sun':{'3':'all','4':'all'}},{'wd':{'3':[6,7,8,12,14,16,18],'4':[7,8,13,14,15,16,17,18],'2':[7,8,13,14,15,16,17,18]}})}
DH={frozenset(('Koszęcin Rynek','Kalety PKP')):22,frozenset(('Piłka','Łazy')):41}   # przejazd techniczny (min)
def vehicles(trips,lay=3):
    tr=sorted([(x[2][0],x[1][0],x[2][-1],x[1][-1]) for x in trips if not x[4]])
    free=[];n=0
    for s_,a,e,b in tr:
        ok=[i for i,(t,p) in enumerate(free) if p==a and t+lay<=s_] or [i for i,(t,p) in enumerate(free) if frozenset((p,a)) in DH and t+DH[frozenset((p,a))]+lay<=s_]
        if ok: free.pop(max(ok,key=lambda i:free[i][0]))
        else: n+=1
        free.append((e,b))
    return n
ND={'wd':250,'sat':52,'sun':63}
res={};tt={}
for v,(P,dem,LH) in VAR.items():
    S={};tot=0;fleet=0
    for k in B:
        row={};kmr=0
        for d in ND:
            tr=build2(d,P[d],dem,LH)[k];fx=[x for x in tr if not x[4]];dm=[x for x in tr if x[4]]
            kd=sum(x[3] for x in fx)+0.5*sum(x[3] for x in dm)+(24.7 if (k=='4' and d=='wd') else 0)   # linia 4: przejazd techniczny drugiego busa Piłka → Łazy
            row[d]={'kursy':len(fx),'zam':len(dm),'km':round(kd,1),'bus':vehicles(tr,lay=3)};kmr+=kd*ND[d]
        row['km_rok']=round(kmr);S[k]=row;tot+=kmr;fleet+=row['wd']['bus']
    res[v]=[S,round(tot),fleet]
    print(v,round(tot),fleet,{k:(x['km_rok'],x['wd']['bus'],x['wd']['kursy']) for k,x in S.items()})
# timetable export for 'pelny'
P,dem,LH=VAR['pelny']
for k in B:
    tt[k]={}
    for d in ND:
        dirs={}
        for lab,seq,t,km,dm in build2(d,P[d],dem,LH)[k]:
            dirs.setdefault(seq[0]+' → '+seq[-1],{'stops':seq,'trips':[]})['trips'].append([t,dm])
        tt[k][d]=dirs
exec(open('skrypty/build.py').read().split('lines={}')[0].replace('print(','(lambda *a,**k:None)('))
_WP={'@tr':(50.6214,18.8415),'@sj':(50.6214,18.8437)}
_km=route([S['kosp'][:2],_WP['@tr'],_WP['@sj'],S['kossz'][:2],S['kosr'][:2]])[1]
RET3=round(_km/40*60+2*0.75)
print('RET3',RET3,_km)
# Koszęcin: dojazd do PKP pętlą (w dół Sobieskiego przez Szkołę, powrót Św. Trójcy – Leśna – Wojska Polskiego)
for d in ND:
    for name,v in tt['3'][d].items():
        st=v['stops']
        if st[0]=='Koszęcin PKP':
            r=st.index('Koszęcin Rynek');j=st.index('Koszęcin Szkoła')
            jt=st.index('Koszęcin Święta Trójca') if 'Koszęcin Święta Trójca' in st else None
            for tr in v['trips']:
                t=tr[0];t[j]=t[r]-1;t[0]=t[r]-RET3
                if jt is not None: t[jt]=t[0]+2
# Linia 4 w stronę Łaz czeka na Koszęcin PKP do :13 (zamiast odjazdu :07), żeby łapać pociągi przyjeżdżające o :04–:10
POSTOJ_KOSP_L4 = int(os.environ.get('POSTOJ_KOSP_L4', 4))   # do :11 (po dodaniu przystanków 25.11.2026 – zapas na zawrócenie w Łazach)
for d in ND:
    for name,v in tt['4'][d].items():
        st=v['stops']
        if st[-1]=='Łazy' and 'Koszęcin PKP' in st:
            j=st.index('Koszęcin PKP')
            for tr in v['trips']:
                for i in range(j,len(st)): tr[0][i]+=POSTOJ_KOSP_L4

# Kurzychowe: tylko kursy szkolne w dni robocze (rano 7:34 do szkół, po południu 13:33 i 16:33 z powrotem).
# Kurs poranny z Łaz przesunięty o 1 min (Kurzychowe 7:33, Łazy 7:35), kurs z Łaz o 13:34 przesunięty na 13:38, żeby bus zdążył zawrócić.
KURZ_RANO={7*60+34:1}; KURZ_PRZYJ={13*60+31,16*60+31}; PRZESUN={13*60+34:4}
d4=tt['4']['wd']; nowe={}
for name,v in list(d4.items()):
    st=v['stops']
    if st[0]=='Łazy':
        zost=[]
        for tr in v['trips']:
            t0=tr[0][0]
            if t0 in PRZESUN: tr[0]=[x+PRZESUN[t0] for x in tr[0]]
            if t0 in KURZ_RANO:
                t=[x+KURZ_RANO[t0] for x in tr[0]]
                nowe.setdefault('Łazy Kurzychowe → '+st[-1],{'stops':['Łazy Kurzychowe']+st,'trips':[]})['trips'].append([[t[0]-2]+t,tr[1]])
            else: zost.append(tr)
        v['trips']=zost
    elif st[-1]=='Łazy':
        zost=[]
        for tr in v['trips']:
            if tr[0][-1] in KURZ_PRZYJ:
                nowe.setdefault(st[0]+' → Łazy Kurzychowe',{'stops':st+['Łazy Kurzychowe'],'trips':[]})['trips'].append([tr[0]+[tr[0][-1]+2],tr[1]])
            else: zost.append(tr)
        v['trips']=zost
d4.update(nowe)
json.dump({'tt':tt,'var':res},open('out/rozklad_data.json','w'),ensure_ascii=False,separators=(',',':'))
