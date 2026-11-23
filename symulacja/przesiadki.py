"""Czy przesiadki z rozkładu działają w symulacji: przyjazd linii dowozowej vs odjazd linii docelowej (min. 1 min na przejście)."""
import re, collections, json
import xml.etree.ElementTree as ET
fm = lambda s: f'{int(s // 3600)}:{int(s % 3600 // 60):02d}'
plan = {v: {k: u for k, u, _ in p} for v, p in json.load(open('plan_kursow.json')).items()}
sim = collections.defaultdict(dict)
for e in ET.parse('wyniki/przystanki.xml').getroot():
    sim[e.get('id')][e.get('busStop').split('_')[0]] = (float(e.get('started')), float(e.get('ended')))
def pu(v, st): return next(int(u) for k, u in plan[v].items() if k.split('_')[0] == st)
PRZ = [('Strzebiń: linia 4 z Łaz → linia 1 do Lublińca', 'L4_Łazy', 'L1_Piasek', 'str'),
       ('Strzebiń: linia 1 z Lublińca → linia 4 do Łaz', 'L1_LubliniecPK', 'L4_Piłka', 'str')]
wynik = []
for opis, a, b, st in PRZ:
    ok = 0; n = 0; marg = []
    for va in [v for v in plan if v.startswith(a) and st in sim[v]]:
        arr = sim[va][st][0]; parr = pu(va, st)
        # docelowy kurs z planu: pierwszy odjazd linii b z tego przystanku >= planowy przyjazd
        cand = sorted((pu(vb, st), vb) for vb in plan if vb.startswith(b) and any(k.split('_')[0] == st for k in plan[vb]) and pu(vb, st) >= parr)
        if not cand or cand[0][0] - parr > 20 * 60: continue
        vb = cand[0][1]
        if st not in sim[vb]: continue
        dep = sim[vb][st][1]; n += 1; m = (dep - arr) / 60; marg.append(m)
        if m >= 1: ok += 1
    if n:
        wynik.append({'przesiadka': opis, 'kursy': n, 'udane': ok, 'min_zapas_min': round(min(marg), 1)})
        print(f'{opis:52} {ok}/{n} udanych, najmniejszy zapas {min(marg):+.1f} min')
json.dump(wynik, open('wyniki/przesiadki.json', 'w'), ensure_ascii=False, indent=1)
