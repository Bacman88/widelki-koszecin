"""Porównanie symulacji SUMO z proponowanym rozkładem: czas przejazdu kursów, punktualność na przystankach, przesiadki."""
import re, json, statistics as st, collections
import xml.etree.ElementTree as ET

plan = {v: [(k, u) for k, u, stoi in p if stoi] for v, p in json.load(open('plan_kursow.json')).items()}   # vid -> [(busStop, planowy czas)]
sim = collections.defaultdict(list)
for e in ET.parse('wyniki/przystanki.xml').getroot():
    if e.get('id', '').startswith('L') or e.get('id', '').startswith('L'):
        pass
    v = e.get('id')
    if v in plan: sim[v].append((e.get('busStop'), float(e.get('started')), float(e.get('ended'))))
fm = lambda s: f'{int(s // 3600)}:{int(s % 3600 // 60):02d}'
wynik = {'linie': {}, 'kursy': []}
po_linii = collections.defaultdict(list)
spoz = collections.defaultdict(list)    # przystanek -> opóźnienia przyjazdu [min]
for v, pl in plan.items():
    s = sim.get(v)
    if not s or len(s) != len(pl): continue
    t_plan = (int(pl[-1][1]) - int(pl[0][1])) / 60
    t_sim = (s[-1][1] - s[0][2]) / 60
    late = [max(0, (s[i][1] - int(pl[i][1])) / 60) for i in range(1, len(pl))]
    line = v.split('_')[0]; kier = v.split('_')[1]
    po_linii[(line, kier)].append((t_plan, t_sim, max(late)))
    for i in range(1, len(pl)):
        nm = pl[i][0].split('_')[0]
        if not (nm == 'kosr' and line in ('L2', 'L3', 'L4')):   # na Rynku dojazdówki mają czas odjazdu, nie przyjazdu
            spoz[nm].append((s[i][1] - int(pl[i][1])) / 60)
    wynik['kursy'].append({'kurs': v, 'odjazd': fm(int(pl[0][1])), 'plan_min': round(t_plan, 1), 'symulacja_min': round(t_sim, 1),
                           'maks_spoznienie_min': round(max(late), 1)})
print('LINIA / KIERUNEK                      kursów  plan  symul.  różnica  maks. spóźn.')
for (line, kier), xs in sorted(po_linii.items()):
    p = st.mean(x[0] for x in xs); s_ = st.mean(x[1] for x in xs); mx = max(x[2] for x in xs)
    wynik['linie'][f'{line} {kier}'] = {'kursy': len(xs), 'plan': round(p, 1), 'symulacja': round(s_, 1), 'maks_spoznienie': round(mx, 1)}
    print(f'{line:4} z {kier:30} {len(xs):4}  {p:5.1f}  {s_:5.1f}  {s_ - p:+6.1f}   {mx:+5.1f}')
NAZ = {k: v[2] for k, v in json.load(open('../out/data.json'))['stops'].items()}
print('\nPrzystanki z największym średnim spóźnieniem przyjazdu (min):')
for nm, xs in sorted(spoz.items(), key=lambda kv: -st.mean(kv[1]))[:8]:
    print(f'  {NAZ.get(nm, nm):34} śr. {st.mean(xs):+5.1f}  maks. {max(xs):+5.1f}  (n={len(xs)})')
# przesiadki na Rynku: dojazdówki muszą być na Rynku przed :51 (linia 1 na Lubliniec :53/:55)
prz = []
for v, pl in plan.items():
    s = sim.get(v); line = v.split('_')[0]
    if not s or line not in ('L2', 'L3', 'L4'): continue
    for i, (bs, until) in enumerate(pl):
        if bs.startswith('kosr') and 0 < i < len(pl) - 1:
            arr = s[i][1]; mn = arr % 3600 / 60
            prz.append((v, fm(arr), mn))
# linia 4 z Łaz przyjeżdża z założenia o :58 (po pętli przez PKP), pozostałe dojazdówki o :49
late = [(v, t) for v, t, mn in prz if (51 < mn < 60 and not v.startswith('L4_Łazy')) or (v.startswith('L4_Łazy') and 58.5 < mn < 60)]
print(f'\nPrzesiadki na Rynku: {len(prz) - len(late)} z {len(prz)} kursów dojazdówek zdąża na czas')
for v, t in late: print('  za późno:', v, t)
wynik['rynek'] = {'kursow': len(prz), 'spoznione': late}
json.dump(wynik, open('wyniki/podsumowanie.json', 'w'), ensure_ascii=False, indent=1)

# --- odcinki między przystankami: czas jazdy w symulacji vs w rozkładzie (rozkład zawiera 45 s postoju) ---
seg = collections.defaultdict(list)
for v, pl in plan.items():
    s = sim.get(v)
    if not s or len(s) != len(pl): continue
    for i in range(len(pl) - 1):
        a, b = pl[i][0].split('_')[0], pl[i + 1][0].split('_')[0]
        p = (int(pl[i + 1][1]) - int(pl[i][1])) / 60
        if a == 'kosr' and v.split('_')[0] in ('L2', 'L3', 'L4') and i > 0: continue   # postój w węźle
        jazda = (s[i + 1][1] - s[i][2]) / 60
        seg[(NAZ.get(a, a), NAZ.get(b, b))].append((p, jazda))
print('\nOdcinki z najmniejszym zapasem (rozkład – jazda w symulacji, min; ujemny = rozkład za ciasny):')
rows = []
for k, xs in seg.items():
    p = st.mean(x[0] for x in xs); j = max(x[1] for x in xs); rows.append((p - j, k, p, j, len(xs)))
for zap, (a, b), p, j, n in sorted(rows)[:10]:
    print(f'  {a:28} → {b:28} rozkład {p:4.1f}  najdłuższa jazda {j:4.1f}  zapas {zap:+4.1f}  (n={n})')
wynik['odcinki'] = [{'z': a, 'do': b, 'rozklad': round(p, 1), 'najdluzsza_jazda': round(j, 1), 'zapas': round(z, 1)} for z, (a, b), p, j, n in sorted(rows)]
json.dump(wynik, open('wyniki/podsumowanie.json', 'w'), ensure_ascii=False, indent=1)
