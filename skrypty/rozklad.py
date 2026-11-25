import json,math
exec(open('skrypty/build.py').read().split('lines={}')[0].replace("print(","(lambda *a,**k:None)("))
# segment km
WPR={'@dw':(50.6248,18.8406),'@tr':(50.6214,18.8415),'@sj':(50.6214,18.8437),'@li':(50.6346,18.8432)}
VIA={('str','kosp'):['@li','@sj','@tr'],('str','kosr'):['@li'],('kosp','bru'):['@tr','@sj'],('kossz','kosp'):['@dw'],('kost','kosp'):['@sj','@tr']}
def segkm(a,b):
    v=VIA.get((a,b)) or (VIA.get((b,a)) or [])[::-1]
    return route([S[a][:2]]+[WPR[x] for x in v]+[S[b][:2]])[1]
V=40.0;DW=0.75;CROSS=3.0
# postój: przystanki z pierwszej wersji 0,75 min; dodane 25.11.2026 – zwykłe 0,5 min, na żądanie 0,25 min (średnio, nie zawsze staje)
NOWE={'kurz','strst','strb','strd','kosl','kosll','kost','rusp','sadsk','sadsz','sadk','lubp1','bruk','dru','kalm'}
ZAD={'bukz','prad','wiel','cien'}
def dw(s_): return 0.25 if s_ in ZAD else (0.5 if s_ in NOWE else DW)  # rezerwa na przejazd kolejowy przed Lublińcem
def offsets(seq):
    t=[0.0];km=[0.0]
    for i,(a,b) in enumerate(zip(seq,seq[1:])):
        k=segkm(a,b);km.append(km[-1]+k);t.append(t[-1]+k/V*60+(dw(a) if i>0 else 0)+(CROSS if b=='lubpkp' or a=='lubpkp' else 0))
    return t,km
NAME={k:v[2] for k,v in S.items()}
lines={'1':['pia','psk','buk','bukz','strd','str','strb','prad','kosl','kosr','kosll','irk','wiel','wie','sadsk','sadsz','sad','sadk','lubp1','lubpkp'],'2':['bor','borp','kosr','kossz','kost','kosp','bru','bruk','dru','kalm','kalp'],'3':['lisp','chw','moc','dol','cien','cie','kosr','kossz','kost','kosp'],'4':['laz','strst','strs','str','strb','prad','kosl','kost','kosp','kossz','kosr'],'5':['lubpkp','lubp1','sadk','sad','sadsz','sadsk','rus','rusp','pil','rusp','rus','wie','wiel','irk','kosll','kosr']}
out={}
for k,seq in lines.items():
    t,km=offsets(seq);out[k]={'seq':seq,'names':[NAME[s] for s in seq],'t':[round(x,1) for x in t],'km':[round(x,2) for x in km]}
    print(k,list(zip([NAME[s] for s in seq],[round(x,1) for x in t],[round(x,1) for x in km])))
json.dump(out,open('out/rozklad_base.json','w'),ensure_ascii=False)
