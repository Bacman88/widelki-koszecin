import json,math
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MPoly, FancyBboxPatch
import matplotlib.patheffects as pe
from shapely.geometry import LineString
for f in ['Inter-Regular.ttf','Inter-SemiBold.ttf','Inter-Bold.ttf']: fm.fontManager.addfont('fonts/'+f)
plt.rcParams['font.family']='Inter'
D=json.load(open('out/data.json'));B=json.load(open('dane/baza.json'))
K=math.cos(math.radians(50.63))
P=lambda la,lo:(lo*K,la)   # local equirectangular
LN={'1':('#00704f','Piasek – Płaszczymąka – Bukowiec – Strzebiń – Koszęcin Rynek – Irki – Wierzbie – Sadów – Lubliniec PKP','co godzinę, 2 busy, bez czekania na Rynku; Strzebiń → Lubliniec 35 min',0),
'2':('#1f6fd1','Boronów – Boronów PKP – Koszęcin Rynek – Koszęcin PKP – Brusiek – Kalety PKP','co 2 h w każdą stronę, w szczytach dodatkowe kursy Kalety – Brusiek – Rynek; 2 busy',0),
'3':('#c98a00','Lisów PKP – Chwostek – Mochała – Hadra – Cieszowa – Koszęcin Rynek – Koszęcin PKP','co 2 godziny, w szczytach szkolnych (rano 5–8, po południu 13–16) co godzinę; 1 bus',-1.4),
'4':('#d4473a','Łazy – Strzebiń – Koszęcin PKP – Koszęcin Rynek – Irki – Wierzbie – Rusinowice PKP – Piłka','co 2 h w każdą stronę, w szczytach (rano 6–8, po południu 14–17) w obie strony; 1 bus, w szczytach 2',2.4)}
LN['4S']=('#d4473a','Propozycja 4S: kursy szkolne Łazy – Strzebiń – Bukowiec – Płaszczymąka – Psary','poza siatką podstawową; przerywana: Strzebiń Lubliniecka – Psary; Łazy → Psary 20 min',-1.4)
LN['4P']=('#8e3b8a','Propozycja 4P: pętla Strzebiń – Łazy – Psary – Płaszczymąka – Strzebiń','poza siatką podstawową; po utwardzeniu ok. 1,4 km drogi Łazy – ul. Poznańska (gm. Woźniki)',0)
LN['4k']=('#d4473a','','',1.4)
LN['1L']=('#00704f','Propozycja 1L: wzmocnienie Koszęcin Rynek – Irki – Wierzbie – Sadów – Lubliniec PKP','poza siatką podstawową; w pół taktu w szczytach (dni nauki), w Wierzbiu przesiadka z linii 4',-2.4)
LN['4L']=('#d4473a','Propozycja 4L: Piłka – Rusinowice PKP – Sadów – Lubliniec PKP','poza siatką podstawową; ewentualność w dni nauki, bez przesiadki i bez postoju w Wierzbiu, ok. 22 min',2.4)
LN['4e']=LN['4'];LN['4r']=LN['4'][:3]+(-LN['4'][3],);LN['3r']=LN['3'][:3]+(-LN['3'][3],)
DASH={'1L':(0,(3,2.2)),'4L':(0,(3,2.2)),'4S':(0,(3,2.2)),'4P':(0,(1,1.6))}
PAPER='#f7f4ec'
def page_map(pdf,ext,title,sub,fname=None,lab_scale=1.0,inset=False):
    fig=plt.figure(figsize=(16.54,11.69));fig.patch.set_facecolor(PAPER)
    ax=fig.add_axes([0.01,0.01,0.98,0.98]);ax.set_facecolor(PAPER)
    x0,x1,y0,y1=ext;ax.set_xlim(x0*K,x1*K);ax.set_ylim(y0,y1);ax.set_aspect('equal');ax.axis('off')
    def poly(rings,fc,z):
        for r in rings[:1]:
            ax.add_patch(MPoly([P(*q) for q in r],closed=True,fc=fc,ec='none',zorder=z))
    for p in B['zab']: poly(p,'#e9dfcf',1)
    for p in B['las']: poly(p,'#d3e6c6',1.1)
    for p in B['woda']: poly(p,'#a9d0ef',1.2)
    for l in B['rzeki']: ax.plot(*zip(*[P(*q) for q in l]),color='#8fc0e6',lw=.8,zorder=1.3)
    ax.plot(*zip(*[P(*q) for q in D['gmina']]),color='#9a6b3c',lw=1.6,ls=(0,(5,4)),zorder=2)
    for l in D['roads']['minor']: ax.plot(*zip(*[P(*q) for q in l]),color='#dcd5c7',lw=.6,zorder=3)
    for l in D['roads']['major']: ax.plot(*zip(*[P(*q) for q in l]),color='#bdb4a3',lw=2.6,zorder=3.1,solid_capstyle='round')
    for l in D['roads']['major']: ax.plot(*zip(*[P(*q) for q in l]),color='#ffffff',lw=1.4,zorder=3.2,solid_capstyle='round')
    for l in D['rails']:
        xy=list(zip(*[P(*q) for q in l]));ax.plot(*xy,color='#222',lw=2.4,zorder=4);ax.plot(*xy,color='#fff',lw=1.1,ls=(0,(4,4)),zorder=4.1)
    # place names
    used={s[2].split(' ')[0] for s in D['stops'].values()}
    for la,lo,t,r in B['nazwy']:
        if r>3 or t in used: continue
        x,y=P(la,lo)
        if not(x0*K<x<x1*K and y0<y<y1): continue
        ax.text(x,y,t,fontsize=(11 if r==1 else 7.2)*lab_scale,color='#6f6a5e',ha='center',va='center',weight='bold' if r==1 else 'normal',zorder=5,path_effects=[pe.withStroke(linewidth=2.5,foreground=PAPER)])
    # linie: wspólne odcinki jako stykające się paski na osi drogi (jak w hubie rowerowym)
    import collections
    u=max((x1-x0)*K/(16.54*.98*72),(y1-y0)/(11.69*.98*72))   # jednostki mapy na 1 pt
    BW={'1':4.6,'2':2.4,'3':2.4,'4':2.4,'1L':2.2,'4L':2.2,'4S':2.2,'4P':2.2}
    ORD=['1','4','2','3','1L','4L','4S','4P'];GAP=0.9   # propozycje zawsze na zewnątrz; odstęp między paskami (pt)
    PTH={k:[tuple(q) for q in l['path']] for k,l in D['lines'].items()}
    # propozycje: obetnij krótkie końcówki biegnące wspólnie z liniami podstawowymi (np. 1L między Rynkiem a skrzyżowaniem)
    CORE=set()
    for k,p in PTH.items():
        if k not in DASH: CORE|={frozenset((q,r)) for q,r in zip(p,p[1:])}
    CU=collections.defaultdict(set)
    for k,p in PTH.items():
        if k not in DASH:
            for q,r in zip(p,p[1:]): CU[frozenset((q,r))].add(k)
    for k in list(PTH):
        if k not in DASH: continue
        p=PTH[k]
        for rev in (0,1):
            if rev: p=p[::-1]
            # zestaw linii podstawowych dalej na trasie (ok. 400 m od końca)
            d=0;j=0
            while j<len(p)-2 and d<0.005: d+=math.hypot((p[j+1][1]-p[j][1])*K,p[j+1][0]-p[j][0]);j+=1
            ref=CU.get(frozenset((p[j],p[j+1])),set())
            cut=0
            while len(p)>2 and CU.get(frozenset((p[0],p[1])),set())-ref and cut<0.004:
                cut+=math.hypot((p[1][1]-p[0][1])*K,p[1][0]-p[0][0]);p=p[1:]
            if rev: p=p[::-1]
            PTH[k]=p
    USE=collections.defaultdict(set)
    for k,p in PTH.items():
        for q,r in zip(p,p[1:]):
            if q!=r: USE[frozenset((q,r))].add(k)
    # 1. odcinki o stałym zestawie linii; kolejność pasków = jak linie się później rozjeżdżają (bez zbędnych przecięć)
    PP={k:[P(*q) for q in p] for k,p in PTH.items()}
    IDX={k:collections.defaultdict(list) for k in PTH}
    for k,p in PTH.items():
        for j,q in enumerate(p): IDX[k][q].append(j)
    def farpt(pp,j,step,d=0.0005):
        x0_,y0_=pp[j];m=j
        while 0<=m+step<len(pp):
            m+=step
            if math.hypot(pp[m][0]-x0_,pp[m][1]-y0_)>=d: break
        return pp[m]
    def ang(o_,inn,out):
        vx,vy=o_[0]-inn[0],o_[1]-inn[1];wx,wy=out[0]-o_[0],out[1]-o_[1]
        return math.atan2(vx*wy-vy*wx,vx*wx+vy*wy)
    def side(i,j,ix,step):
        """+1: linia i po lewej od j (w kierunku jazdy i), -1 po prawej, 0 nie wiadomo"""
        p=PTH[i];pp=PP[i];m=ix[-1] if step>0 else ix[0];dist=0
        while 0<=m+step<len(p):
            e=frozenset((p[m],p[m+step]))
            if p[m]!=p[m+step] and j not in USE[e]:
                node=p[m];inn=farpt(pp,m,-step);oi=farpt(pp,m,step)
                best=None
                for jj in IDX[j].get(node,[]):
                    for st in (1,-1):
                        if 0<=jj+st<len(PTH[j]) and frozenset((node,PTH[j][jj+st])) in USE and i not in USE[frozenset((node,PTH[j][jj+st]))]:
                            best=farpt(PP[j],jj,st)
                if best is None: return (0,9)
                d=ang(pp[m],inn,oi)-ang(pp[m],inn,best)
                if abs(d)<1e-6: return (0,9)
                return ((1 if d>0 else -1)*(1 if step>0 else -1),dist)
            dist+=math.hypot(pp[m+step][0]-pp[m][0],pp[m+step][1]-pp[m][1]);m+=step
        return (0,9)
    def side2(i,j,ix):
        a_=side(i,j,ix,1);b_=side(i,j,ix,-1)
        c_=[x for x in (a_,b_) if x[0]]
        return min(c_,key=lambda x:x[1])[0] if c_ else 0
    MAN={frozenset(x):x for x in (['1L','4','1'],['3','4','1'],['1L','3','4','1'],['1','4','3','2'],['1','4'],['4','3','2'],['4','3'])}
    BRK=set()
    for k,p in PTH.items():
        BRK|={p[0],p[-1]};prev=None
        for j in range(len(p)-1):
            if p[j]==p[j+1]: continue
            s_=frozenset(USE[frozenset((p[j],p[j+1]))])
            if prev is not None and s_!=prev: BRK.add(p[j])
            prev=s_
    RUNS={};ORDK={}
    for k,p in PTH.items():
        runs=[];cur=[0];cs=None
        for j in range(len(p)-1):
            if p[j]==p[j+1]: continue
            s_=frozenset(USE[frozenset((p[j],p[j+1]))])
            if cs is not None and (s_!=cs or p[j] in BRK): runs.append((cs,cur));cur=[j]
            cur.append(j+1);cs=s_
        runs.append((cs,cur));RUNS[k]=[]
        for s_,ix in runs:
            if len(ix)<2: continue
            ns=[p[j] for j in ix];flip=(ns[0],ns[-1])>(ns[-1],ns[0])
            cn=ns[::-1] if flip else ns;e0=frozenset((cn[0],cn[1]));kk=(s_,e0)
            RUNS[k].append((kk,ns,flip))
            if kk in ORDK or len(s_)<2: continue
            win=collections.Counter()
            others=[x for x in s_ if x!=k]
            for jx in others:
                sd=side2(k,jx,ix)
                if flip: sd=-sd
                win[k]+=sd;win[jx]-=sd
            for q1 in others:
                for q2 in others:
                    if q1<q2:
                        # wyznacz z perspektywy q1 na jego własnym przebiegu
                        jl=[jj for jj in IDX[q1].get(ns[0],[])]+[jj for jj in IDX[q1].get(ns[-1],[])]
                        sd=0
                        for jj in IDX[q1].get(ns[0],[]):
                            for st in (1,-1):
                                if 0<=jj+st<len(PTH[q1]) and PTH[q1][jj+st]==ns[1]:
                                    L_=len(ns)-1;ixx=list(range(jj,jj+st*L_+st,st)) if st>0 else list(range(jj+st*L_,jj+1))
                                    if not(0<=min(ixx) and max(ixx)<len(PTH[q1])): continue
                                    s1=side2(q1,q2,ixx)
                                    if s1: sd=s1*(1 if st>0 else -1)*(-1 if flip else 1)
                        win[q1]+=sd;win[q2]-=sd
            ORDK[kk]=sorted(s_,key=lambda x:(-win[x],ORD.index(x)))
    # 2. rysowanie: kolejność pasków wg strony zjazdu (mniej przecięć), potem stała kolejność
    drawn=set()
    for k,p in PTH.items():
        chain=[]
        for kk,ns,flip in RUNS[k]:
            s_=kk[0]
            if flip: ns=ns[::-1]
            ids=list(ORDK.get(kk,sorted(s_,key=ORD.index)))
            if s_ in MAN:   # ręczna kolejność: od zachodu (drogi N–S) / od północy (drogi W–E)
                (ax_,ay_),(bx_,by_)=P(*ns[0]),P(*ns[-1]);vx,vy=bx_-ax_,by_-ay_
                ids=list(MAN[s_])
                # kanoniczny kierunek: indeks 0 = lewa strona; lista MAN jest 'lewa' dla jazdy na północ / na wschód
                if (abs(vy)>abs(vx) and vy<0) or (abs(vy)<=abs(vx) and vx<0): ids=ids[::-1]
            ws=[BW[i] for i in ids];tot=sum(ws)+GAP*(len(ws)-1)
            prop=[i for i in ids if i in DASH]
            if prop:   # propozycje zawsze z brzegu (po tej stronie, po której wypadły)
                pos={i:ids.index(i) for i in prop};core=[i for i in ids if i not in DASH]
                ids=[i for i in prop if pos[i]<len(ids)/2]+core+[i for i in prop if pos[i]>=len(ids)/2]
                ws=[BW[i] for i in ids]
            ln=LineString([P(*q) for q in ns]).simplify(0.4*u)
            if kk not in drawn:
                drawn.add(kk)
                ax.plot(*ln.xy,color='white',lw=tot+1.6,zorder=6,solid_capstyle='round',solid_joinstyle='round')
            i=ids.index(k);o=(-tot/2+sum(ws[:i])+GAP*i+ws[i]/2)*u
            try:
                g=ln.offset_curve(-o,join_style=1,quad_segs=4) if abs(o)>1e-12 else ln
                if g.is_empty: g=ln
            except Exception: g=ln
            if g.geom_type!='LineString': g=max(g.geoms,key=lambda x:x.length)
            cc=list(g.coords)
            if flip: cc=cc[::-1]
            chain.append(cc)
        # jedna ciągła linia: końce sąsiednich odcinków łączone krótkim skosem
        # propozycje: pomiń krótkie końcówki wspólne z węzłem (np. 1L na odcinku Rynek – skrzyżowanie)
        if k in DASH:
            while len(chain)>1 and LineString(chain[0]).length<0.0018: chain.pop(0)
            while len(chain)>1 and LineString(chain[-1]).length<0.0018: chain.pop()
        # łagodne przejścia między odcinkami: przytnij końce przy węzłach, połącz skosem
        from shapely.ops import substring
        t=4*u;sm=[]
        for n_,cc in enumerate(chain):
            g_=LineString(cc) if len(cc)>1 else None
            if g_ is None or g_.length==0: continue
            a_=t if n_>0 else 0;b_=g_.length-(t if n_<len(chain)-1 else 0)
            if b_-a_<=g_.length*0.1: sm.append([g_.interpolate(0.5,normalized=True).coords[0]]);continue
            sm.append(list(substring(g_,a_,b_).coords))
        chain=sm
        xy=[]
        for cc in chain:
            if xy and len(cc)>1:
                # zjazd z pasa przed węzłem: obetnij ostatni/pierwszy kawałek o 1,5 szerokości pakietu
                pass
            xy+=cc
        X,Y=zip(*xy);c=LN[k][0]
        if k in DASH: ax.plot(X,Y,color=c,lw=BW[k],zorder=6.1,ls=DASH[k],dash_capstyle='butt')
        else: ax.plot(X,Y,color=c,lw=BW[k],zorder=6.1,solid_capstyle='butt',solid_joinstyle='round')
    for la,lo,nm in D.get('busstops',[]):
        x,y=P(la,lo)
        if not(x0*K<x<x1*K and y0<y<y1): continue
        ax.scatter([x],[y],s=(9 if not inset else 14),c='white',edgecolors='#555',linewidths=0.8,zorder=6.5)
    # stations not in stops
    for la,lo,t in D['stations']:
        if t in ['Koszęcin','Lubliniec','Boronów','Kalety','Rusinowice','Lisów']: continue
        x,y=P(la,lo)
        if not(x0*K<x<x1*K and y0<y<y1): continue
        ax.scatter([x],[y],s=40,c='white',edgecolors='#222',linewidths=2,zorder=7)
        st_=t=='Strzebiń'
        ax.text(x-0.0012 if st_ else x+0.0012,y+(0.0012 if st_ else 0),('obecny przyst. kolejowy Strzebiń' if st_ else t+' (stacja)'),fontsize=7.5*lab_scale,va='center',ha='right' if st_ else 'left',zorder=8,path_effects=[pe.withStroke(linewidth=2.5,foreground=PAPER)])
    served={}
    for k,l in D['lines'].items():
        for s in l['stops']: served.setdefault(s,[]).append(k)
    for sid,(la,lo,t,kind) in D['stops'].items():
        x,y=P(la,lo)
        if not(x0*K<x<x1*K and y0<y<y1): continue
        if kind=='hub': ax.scatter([x],[y],s=420,c='#00463c',edgecolors='#e6f5c8',linewidths=3.5,zorder=9);fs=13;wt='bold';col='#10201c'
        elif kind=='hubz': ax.scatter([x],[y],s=170,c='#e6f5c8',edgecolors='#1c2420',linewidths=3.5,zorder=9);fs=10.5;wt='bold';col='#10201c'
        elif kind=='nowy': ax.scatter([x],[y],s=110,c='white',edgecolors='#ff6f59',linewidths=3,zorder=9);fs=9;wt='bold';col='#b8321f'
        else: ax.scatter([x],[y],s=45,c='white',edgecolors='#1c2420',linewidths=1.8,zorder=9);fs=8.5;wt='semibold';col='#1c2420'
        lab=t+(' (proponowany)' if kind=='nowy' and 'nowa' not in t else '')
        dx,dy,ha=0.0016,0.0,'left'
        if sid in('kosr',):dx,dy,ha=0.0,0.0042,'center'
        if sid in('kosp','irk','lisp'):dx,ha=-0.0016,'right'
        if sid=='sad':dx,dy,ha=0.0,0.0035,'center'
        if sid=='strw':dx,dy,ha=-0.0016,-0.0022,'right'
        if sid=='str':dy=-0.0018
        if sid=='strs':dy=0.0016;ha='left'
        ax.text(x+dx,y+dy,lab,fontsize=fs*lab_scale,weight=wt,color=col,ha=ha,va='center',zorder=10,path_effects=[pe.withStroke(linewidth=3,foreground=PAPER)])
    # header box
    ax.text(0.015,0.975,title,transform=ax.transAxes,fontsize=22,weight='bold',va='top',color='#10201c',zorder=11,path_effects=[pe.withStroke(linewidth=5,foreground=PAPER)])
    ax.text(0.015,0.935,sub,transform=ax.transAxes,fontsize=10.5,va='top',color='#4a524c',zorder=11,path_effects=[pe.withStroke(linewidth=4,foreground=PAPER)])
    # legend
    lx,ly=0.015,(0.395 if not inset else 0.30)
    ax.add_patch(FancyBboxPatch((lx,0.02),0.33,ly,transform=ax.transAxes,boxstyle='round,pad=0.006',fc=PAPER,ec='#d9d3c5',zorder=11))
    yy=0.02+ly-0.025
    for k,(c,n,f,o) in LN.items():
        if (inset and k in DASH) or k in('4k','4e','4r','3r'): continue
        ax.add_patch(FancyBboxPatch((lx+0.008,yy-0.011),0.022,0.022,transform=ax.transAxes,boxstyle='round,pad=0.002',fc=c,ec='none',zorder=12))
        ax.text(lx+0.019,yy,k,transform=ax.transAxes,ha='center',va='center',color='white',weight='bold',fontsize=10,zorder=13)
        ax.text(lx+0.038,yy+0.004,n,transform=ax.transAxes,va='center',fontsize=7.4,zorder=13,wrap=True)
        ax.text(lx+0.038,yy-0.012,f"{str(D['lines'][k]['km']).replace('.',',')} km · {f}",transform=ax.transAxes,va='center',fontsize=6.6,color='#5d665f',zorder=13)
        yy-=0.042
    keys=[('#00463c','#e6f5c8',13,'główny węzeł Koszęcin Rynek'),('#e6f5c8','#1c2420',10,'węzeł zewnętrzny'),('white','#ff6f59',9,'proponowany przystanek przy stacji'),('white','#1c2420',7,'przystanek węzłowy/główny'),('white','#555',3,'istniejące przystanki po drodze (OSM, niepełne)')]
    for i,(fc,ec,s,t) in enumerate(keys):
        cx=lx+0.012+(i%2)*0.165;cy=0.066-(i//2)*0.02
        ax.scatter([cx],[cy],s=s*9,c=fc,edgecolors=ec,linewidths=2.2,transform=ax.transAxes,zorder=13)
        ax.text(cx+0.012,cy,t,transform=ax.transAxes,va='center',fontsize=7,zorder=13)
    ax.text(0.985,0.012,'Dane mapy © współtwórcy OpenStreetMap (ODbL) · propozycja do dyskusji · 19.11.2026',transform=ax.transAxes,ha='right',fontsize=7,color='#6f6a5e',zorder=11)
    pdf.savefig(fig,facecolor=PAPER);
    if fname: fig.savefig(fname,dpi=110,facecolor=PAPER)
    plt.close(fig)

def page_text(pdf):
    fig=plt.figure(figsize=(16.54,11.69));fig.patch.set_facecolor('white')
    T=lambda x,y,s,**k:fig.text(x,y,s,**k)
    T(0.04,0.94,'Propozycja siatki busów gminy Koszęcin: węzeł Koszęcin Rynek',fontsize=22,weight='bold',color='#10201c')
    T(0.04,0.905,'Wszystkie linie spotykają się na Rynku w stałym takcie co godzinę. Trzy jadą dalej do stacji Koszęcin PKP. Na obrzeżach węzły zewnętrzne: Lubliniec PKP, Piasek, Boronów, Kalety PKP.',fontsize=11,color='#3d4540')
    y=0.85
    T(0.04,y,'Linia',fontsize=9.5,color='#6b736e',weight='bold');T(0.09,y,'Trasa',fontsize=9.5,color='#6b736e',weight='bold');T(0.56,y,'Długość',fontsize=9.5,color='#6b736e',weight='bold');T(0.62,y,'Częstotliwość',fontsize=9.5,color='#6b736e',weight='bold')
    y-=0.012;fig.add_artist(plt.Line2D([0.04,0.96],[y,y],color='#d0d6d2',lw=1))
    for k,(c,n,f,o) in LN.items():
        if k in('4k','4e','4r','3r'): continue
        y-=0.045
        fig.add_artist(FancyBboxPatch((0.04,y-0.012),0.028,0.028,boxstyle='round,pad=0.002',fc=c,ec='none',transform=fig.transFigure))
        T(0.054,y+0.002,k,ha='center',va='center',color='white',weight='bold',fontsize=12)
        T(0.09,y+0.002,n,va='center',fontsize=10.5);T(0.56,y+0.002,(str(D['lines'][k]['km'])+' km').replace('.',','),va='center',fontsize=10.5)
        import textwrap;T(0.62,y+0.002,textwrap.fill(f,62),va='center',fontsize=9.5,color='#3d4540',linespacing=1.3)
        fig.add_artist(plt.Line2D([0.04,0.96],[y-0.02,y-0.02],color='#e6eae7',lw=.8))
    y-=0.08
    T(0.04,y,'Takt w węźle Koszęcin Rynek',fontsize=15,weight='bold',color='#10201c')
    tx=['Przyjazdy busów około :45–:50, odjazdy około :05–:10. W tym oknie przesiadka z każdej linii na każdą inną.',
        'Na pracę i szkołę od pełnej godziny przyjazd z kwadransem zapasu, a po pracy kończonej o pełnej godzinie odjazd 5–10 minut później.',
        'Linie 1, 2 i 3 dojeżdżają do Koszęcin PKP, gdzie pociągi Kolei Śląskich do Lublińca i Tarnowskich Gór odjeżdżają w okolicach pełnej godziny.',
        'Dokładną minutę taktu trzeba dopasować do rozkładu kolejowego obowiązującego od 13.12.2026.']
    for i,t in enumerate(tx): T(0.04,y-0.035-i*0.03,'•  '+t,fontsize=10.5,color='#2a322d')
    y2=y-0.2
    T(0.04,y2,'Co się zmienia względem dziś',fontsize=15,weight='bold',color='#10201c')
    ch=['Dziś linie gminne kończą się w Sadowie i są ustawione pod Lubliniec. Ze Strzebinia na 8:00 i 14:00 do Koszęcina nie da się dojechać na czas (przyjazdy 8:18 i 14:02).',
        'Dziś ostatni powrót z Koszęcina do Strzebinia jest o 19:04, w niedzielę nie jeździ nic. W propozycji kursy do około 22:30 i w weekendy.',
        'Kursy do Łaz jeżdżą dziś tylko w dni nauki szkolnej. W propozycji linia 5 przez cały rok, z dojazdem do Rusinowic i Piłki.',
        'Przystanki przy stacjach: Koszęcin PKP, Boronów PKP, Kalety PKP, a w Strzebiniu przy nowej lokalizacji przystanku kolejowego przy wiadukcie ul. Lublinieckiej.',
        'W 2024 r. gmina wydała na lokalny transport zbiorowy 1 348 590 zł (sprawozdanie z wykonania budżetu, rozdz. 60004).']
    for i,t in enumerate(ch): T(0.04,y2-0.035-i*0.03,'•  '+t,fontsize=10.5,color='#2a322d')
    T(0.04,0.05,'Uwagi do planu transportowego ZPG „Jedźmy razem!” można składać do 7.12.2026: ul. Pułaskiego 6, 42-300 Myszków (pok. 608), formularz w BIP związku.',fontsize=10,color='#00463c',weight='bold')
    T(0.04,0.025,'Źródła: tabliczki przystankowe GTVBUS (lokalnie-gtvbus.pl, 19.11.2026), transportpowiat.pl, TED 31.01.2025, budżet Gminy Koszęcin 2024, OpenStreetMap. Trasy, takt i częstotliwości to propozycja do dyskusji.',fontsize=8,color='#6b736e')
    pdf.savefig(fig);plt.close(fig)

with PdfPages('out/mapy.pdf') as pdf:
    page_map(pdf,(18.595,19.041,50.545,50.745),'Propozycja siatki busów gminy Koszęcin','Węzeł główny Koszęcin Rynek · gruba linia: co godzinę, cienka: co 2 godziny, przerywana: propozycje · trasy po drogach z OpenStreetMap',fname='out/mapa_ogolna.png')
    page_map(pdf,(18.79,18.92,50.597,50.656),'Koszęcin i Strzebiń – przybliżenie','Węzeł Koszęcin Rynek, dojazd do stacji Koszęcin PKP, przystanki w Strzebiniu',fname='out/mapa_przyblizenie.png',lab_scale=1.15,inset=True)
    page_text(pdf)
    d=pdf.infodict();d['Title']='Propozycja siatki busów gminy Koszęcin';d['Author']='Bartosz'
print('ok')
