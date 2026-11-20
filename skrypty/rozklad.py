import json,math
exec(open('skrypty/build.py').read().split('lines={}')[0].replace("print(","(lambda *a,**k:None)("))
# segment km
WPR={'@dw':(50.6248,18.8406),'@tr':(50.6214,18.8415),'@sj':(50.6214,18.8437),'@li':(50.6346,18.8432)}
VIA={('str','kosp'):['@li','@sj','@tr'],('str','kosr'):['@li'],('kosp','bru'):['@tr','@sj'],('kossz','kosp'):['@dw']}
def segkm(a,b):
    v=VIA.get((a,b)) or (VIA.get((b,a)) or [])[::-1]
    return route([S[a][:2]]+[WPR[x] for x in v]+[S[b][:2]])[1]
V=40.0;DW=0.75;CROSS=3.0  # rezerwa na przejazd kolejowy przed Lublińcem
def offsets(seq):
    t=[0.0];km=[0.0]
    for i,(a,b) in enumerate(zip(seq,seq[1:])):
        k=segkm(a,b);km.append(km[-1]+k);t.append(t[-1]+k/V*60+(DW if i>0 else 0)+(CROSS if {a,b}=={'sad','lubpkp'} else 0))
    return t,km
NAME={k:v[2] for k,v in S.items()}
lines={'1':['pia','psk','buk','str','kosr','irk','wie','sad','lubpkp'],'2':['bor','borp','kosr','kossz','kosp','bru','kalp'],'3':['lisp','chw','dol','cie','kosr','kossz','kosp'],'4':['laz','strs','str','kosp','kossz','kosr','irk','wie','rus','pil']}
out={}
for k,seq in lines.items():
    t,km=offsets(seq);out[k]={'seq':seq,'names':[NAME[s] for s in seq],'t':[round(x,1) for x in t],'km':[round(x,2) for x in km]}
    print(k,list(zip([NAME[s] for s in seq],[round(x,1) for x in t],[round(x,1) for x in km])))
json.dump(out,open('out/rozklad_base.json','w'),ensure_ascii=False)
