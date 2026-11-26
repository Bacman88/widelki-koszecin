import json, os
exec(open('skrypty/rozklad2.py').read().split("days={'wd'")[0])
ALT={'2'}
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
VAR={'pelny':({'wd':list(range(6,23)),'sat':[8,10,12,14,16,18,20,22],'sun':[9,12,15,18,20,22]},{'wd':{'3':[10,20]},'sat':{'3':'all','4':'all','5':'all'},'sun':{'3':'all','4':'all','5':'all'}},{'wd':{'3':[6,7,8,10,12,14,15,16,18,20],'5':[6,7,8,10,12,14,15,16,17,18,20]},'sat':{'5':[8,10,12,14,16,18,20,22]}}),
     'oszczedny':({'wd':[6,7,8,10,12,13,14,15,16,17,18,20,22],'sat':[8,10,12,14,16,18,20],'sun':[10,13,16,19]},{'wd':{'3':[18]},'sat':{'3':'all','4':'all'},'sun':{'3':'all','4':'all'}},{'wd':{'3':[6,7,8,12,14,16,18],'4':[6,7,8,10,12,14,15,16,17,18],'5':[6,7,8,12,14,15,16,18],'2':[7,8,13,14,15,16,17,18]}})}
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
            kd=sum(x[3] for x in fx)+0.5*sum(x[3] for x in dm)   # linia 4: przejazd techniczny drugiego busa Piłka → Łazy
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
# 25.11.2026: Kurzychowe jako opcja (przystanek Łazy ok. 300 m dalej) – w rozkładzie podstawowym bez kursów; KURZ=1 włącza
if os.environ.get('KURZ') == '1': KURZ_RANO={7*60+34:1}; KURZ_PRZYJ={13*60+31,16*60+31}; PRZESUN={13*60+34:4}
else: KURZ_RANO={}; KURZ_PRZYJ=set(); PRZESUN={}
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
# 25.11.2026: podział dawnej linii 4 – linia 4 Łazy – Strzebiń – Koszęcin PKP – Rynek (jeden bus, kółko w godzinę),
# linia 5 Koszęcin – Wierzbie – Rusinowice – Piłka – Sadów – Lubliniec (co 2 h, w szczytach co godzinę).
# Linia 4: w szczytach w pulsie (przesiadka do Lublińca w Strzebiniu, powroty z Rynku :03), poza szczytem 15 min później,
# żeby nie jechać razem z linią 1. Wariant A: poza szczytem co godzinę, B: co ok. 2 h.
WAR = os.environ.get('WARIANT', 'A')
hm = lambda x: int(x.split(':')[0])*60 + int(x.split(':')[1])
L4_WD = {'A': ('5:34 6:34 7:34 8:49 9:49 10:49 11:49 13:34 14:34 15:34 16:34 17:49 18:49 19:49',
               '6:03 7:03 8:03 9:18 10:18 11:18 12:18 14:03 15:03 16:03 17:03 18:18 19:18 20:18'),
         'B': ('5:34 6:34 7:34 8:49 10:49 13:34 14:34 15:34 16:34 17:49 19:49',
               '6:03 7:03 8:03 10:18 12:18 14:03 15:03 16:03 17:03 18:18 20:18')}[WAR]
def l4_set(dz, eastbound, starts):
    for name, v in tt['4'][dz].items():
        if (v['stops'][0] == 'Łazy') != eastbound: continue
        wzor = v['trips'][0]; base = wzor[0]
        ref = base[0] if eastbound else base[v['stops'].index('Koszęcin Rynek')]
        v['trips'] = [[[x - ref + st for x in base], wzor[1]] for st in starts]
l4_set('wd', True, [hm(x) for x in L4_WD[0].split()])
l4_set('wd', False, [hm(x) for x in L4_WD[1].split()])
for dz in ('sat', 'sun'):          # weekend: linia 4 15 min później
    for name, v in tt['4'][dz].items():
        for tr in v['trips']: tr[0] = [x + 15 for x in tr[0]]
# bez późnych wieczornych kursów linii 4 i 5 (odjazd po 20:30) – 25.11.2026
for dz in ('wd', 'sat', 'sun'):
  for ln in ('4', '5'):
    for name, v in tt[ln][dz].items():
        v['trips'] = [tr for tr in v['trips'] if tr[0][0] < 20*60+30]
# linia 5: przesunięcie kursów (L5_SA – z Lublińca do Koszęcina, L5_SB – z Koszęcina do Lublińca), np. dłuższy postój na Koszęcinie PKP
_sA=int(os.environ.get('L5_SA',0)); _sB=int(os.environ.get('L5_SB',8))
for dz in ND:
    for name, v in tt['5'][dz].items():
        s_=_sA if v['stops'][0]=='Lubliniec PKP' else _sB
        for tr in v['trips']: tr[0]=[x+s_ for x in tr[0]]
# 26.11.2026: linia 1 w dni nauki przez Psary (przystanek Psary Główna przy ul. Głównej, ok. 650 m do szkoły):
# Płaszczymąka – DW905 Poznańska – Psary Główna – Powstańców – Strażacka – Piasek (+2,5 km, +5 min).
# Rano kursy do Piasku (Psary ok. 7:23 i 8:23), po południu z Piasku 5 min wcześniej (Psary ok. 14:32 i 15:32).
PSARY_DO = {6*60+33, 7*60+33}          # odjazd z Lublińca
PSARY_Z = {14*60+33, 15*60+33}         # planowy odjazd z Piasku
for name, v in list(tt['1']['wd'].items()):
    st = v['stops']
    if st[0] == 'Lubliniec PKP':
        i = st.index('Płaszczymąka'); wyb = [t for t in v['trips'] if t[0][0] in PSARY_DO]
        if not wyb: continue
        v['trips'] = [t for t in v['trips'] if t[0][0] not in PSARY_DO]
        nst = st[:i+1] + ['Psary Główna'] + st[i+1:]
        ntr = [[t[0][:i+1] + [t[0][i] + 3] + [t[0][i] + 7], t[1]] for t in wyb]
        tt['1']['wd'][name + ' (przez Psary)'] = {**{k: x for k, x in v.items() if k not in ('stops', 'trips')}, 'stops': nst, 'trips': ntr}
    elif st[0] == 'Piasek':
        i = st.index('Płaszczymąka'); wyb = [t for t in v['trips'] if t[0][0] in PSARY_Z]
        if not wyb: continue
        v['trips'] = [t for t in v['trips'] if t[0][0] not in PSARY_Z]
        nst = ['Piasek', 'Psary Główna'] + st[i:]
        ntr = [[[t[0][i] - 7, t[0][i] - 4] + t[0][i:], t[1]] for t in wyb]
        tt['1']['wd'][name + ' (przez Psary)'] = {**{k: x for k, x in v.items() if k not in ('stops', 'trips')}, 'stops': nst, 'trips': ntr}
# 26.11.2026: wieczorne kursy linii 1 z Koszęcina Rynku w stronę Piasku o :15 zamiast o pełnej (od 21:00) – +15 min;
# w dni robocze także ostatni kurs z Piasku (21:33 → 21:48), żeby te same 2 busy obsłużyły obieg
for dz in ('wd', 'sat', 'sun'):
    for name, v in tt['1'][dz].items():
        st = v['stops']
        if 'Psary' in name: continue
        if st[0] == 'Lubliniec PKP':
            i = st.index('Koszęcin Rynek')
            for tr in v['trips']:
                if tr[0][i] >= 21*60: tr[0] = [x + 15 for x in tr[0]]
        elif st[0] == 'Piasek' and dz == 'wd':
            for tr in v['trips']:
                if tr[0][0] == 21*60+33: tr[0] = [x + 15 for x in tr[0]]
# zestawienie wariantu pełnego po poprawkach (kursy, km, busy) – z gotowego rozkładu
_BASE=json.load(open('out/rozklad_base.json'));_S={};_tot=0;_fl=0
for k in tt:
    row={};kmr=0;km=_BASE[k]['km'][-1]
    for d in ND:
        tr=[(None,v['stops'],t[0],km,t[1]) for v in tt[k][d].values() for t in v['trips']]
        fx=[x for x in tr if not x[4]];dm=[x for x in tr if x[4]]
        kd=km*(len(fx)+0.5*len(dm));row[d]={'kursy':len(fx),'zam':len(dm),'km':round(kd,1),'bus':vehicles(tr,lay=3)};kmr+=kd*ND[d]
    row['km_rok']=round(kmr);_S[k]=row;_tot+=kmr;_fl+=row['wd']['bus']
res['pelny']=[_S,round(_tot),_fl]
print('pelny (po poprawkach)',round(_tot),_fl,{k:(x['km_rok'],x['wd']['bus'],x['wd']['kursy']) for k,x in _S.items()})
json.dump({'tt':tt,'var':res},open('out/rozklad_data.json','w'),ensure_ascii=False,separators=(',',':'))
