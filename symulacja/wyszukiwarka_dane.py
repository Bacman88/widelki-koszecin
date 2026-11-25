"""Dane dla wyszukiwarki połączeń na stronie (strona/wyszukiwarka/dane.json).

Busy: proponowany rozkład dnia roboczego (plan_kursow.json – ten sam, który jedzie w symulacji).
Pociągi KŚ i POLREGIO: postoje na stacjach z symulacji (wyniki/przystanki.xml, rozkład 2026/27, ±1 min).
Przejścia piesze: przystanek przy stacji ↔ peron, Koszęcin Rynek ↔ Koszęcin Szkoła.
Uruchom po pełnym przebiegu symulacji (cała doba, patrz README „Film”):  python3 wyszukiwarka_dane.py
"""
import json, math, re, sys
sys.path.insert(0, '../skrypty')

plan = json.load(open('plan_kursow.json'))
NAZWY = {'bor': 'Boronów', 'borp': 'Boronów PKP', 'bru': 'Brusiek', 'buk': 'Bukowiec', 'chw': 'Chwostek',
         'cie': 'Cieszowa', 'dol': 'Hadra', 'irk': 'Rzyce Irki', 'kalp': 'Kalety PKP', 'kosp': 'Koszęcin PKP',
         'kosr': 'Koszęcin Rynek', 'kossz': 'Koszęcin Szkoła', 'laz': 'Łazy', 'lisp': 'Lisów PKP',
         'lubpkp': 'Lubliniec PKP', 'moc': 'Mochała', 'pia': 'Piasek', 'pil': 'Piłka', 'prad': 'Prądy',
         'psk': 'Płaszczymąka (Psary Skrzyżowanie)', 'rus': 'Rusinowice PKP', 'sad': 'Sadów Przedszkole',
         'str': 'Strzebiń Lubliniecka', 'strs': 'Strzebiń Szkoła', 'wie': 'Wierzbie'}
# miejscowość / gmina do podpowiedzi w polu wyszukiwania
GDZIE = {'lubpkp': 'Lubliniec', 'kalp': 'Kalety', 'lisp': 'Lisów, gm. Herby', 'psk': 'Psary', 'bru': 'gm. Koszęcin'}
POSTOJ_RYNEK = 14 * 60
S = {k: (float(a), float(b)) for k, a, b in re.findall(r"'(\w+)':\(([\d.]+),([\d.]+),'", open('../skrypty/build.py').read())}
S['prad'] = (50.62416, 18.87249)   # Prądy: przystanek dodany w symulacji (scenariusz.py)
STACJE = {'Lubliniec': ((50.6726, 18.6910), 'lubpkp'), 'Rusinowice': ((50.6490, 18.7638), 'rus'),
          'Koszęcin': ((50.6230, 18.8359), 'kosp'), 'Strzebiń': ((50.6184, 18.9000), 'str'),
          'Boronów': ((50.6654, 18.9014), 'borp'), 'Lisów': ((50.7208, 18.7911), 'lisp'),
          'Kochanowice': ((50.6995, 18.7486), None)}

def m(a, b):   # metry
    return math.hypot((a[0] - b[0]) * 111200, (a[1] - b[1]) * 111200 * math.cos(math.radians(50.65)))

stops = {}   # id → {n: nazwa, lat, lon}
for k, n in NAZWY.items(): stops[k] = {'n': n, 'lat': S[k][0], 'lon': S[k][1]}
for st, (p, _) in STACJE.items(): stops['st_' + st] = {'n': f'{st} – stacja kolejowa', 'lat': p[0], 'lon': p[1], 'kolej': 1}
for k, g in GDZIE.items(): stops[k]['g'] = g

piesze = []   # [a, b, minuty] w obie strony
for st, (p, bus) in STACJE.items():
    if bus:
        d = m(p, S[bus]); piesze.append(['st_' + st, bus, max(2, round(d / 70 + 1))])
piesze.append(['kosr', 'kossz', 6])

kursy = []   # {l: linia, k: kierunek, p: [[przystanek, przyjazd, odjazd, na_żądanie]]}
for kid, st in sorted(plan.items(), key=lambda x: x[1][0][1]):
    l = kid.split('_')[0][1:]
    p = []
    for i, (sid, t, stale) in enumerate(st):
        kod = sid.split('_')[0]
        arr = dep = round(t / 60)
        if kod == 'kosr' and l in '234' and 0 < i < len(st) - 1:   # postój w węźle: przyjazd ok. :49, odjazd :03
            arr = max(round((t - POSTOJ_RYNEK) / 60), p[-1][2] + 1)
        p.append([kod, arr, dep, 0 if stale else 1])
    assert all(b[1] >= a[2] for a, b in zip(p, p[1:])), kid
    kursy.append({'l': l, 'k': NAZWY[p[-1][0]], 'p': p})

# pociągi pasażerskie z symulacji
KIER = {('131', 'a'): 'Tarnowskie Góry', ('131', 'b'): 'Herby Nowe', ('143', 'a'): 'Kalety, Tarnowskie Góry',
        ('143', 'b'): 'Lubliniec', ('61', 'a'): 'Częstochowa', ('61', 'b'): 'Lubliniec'}
poc = {}
for mm in re.finditer(r'<stopinfo id="(poc(\d+)([ab])_p\d+(\w))" type="pociag"[^>]*started="([\d.]+)" ended="([\d.]+)"[^>]*busStop="st_([^_"]+)',
                      open('wyniki/przystanki.xml', encoding='utf-8').read()):
    vid, lin, kier, prz, a, b, st = mm.groups()
    if st not in STACJE: continue
    poc.setdefault(vid, {'l': 'KŚ' if prz == 'K' else 'PR', 'tor': lin, 'k': KIER.get((lin, kier), ''), 'p': []})['p'].append(
        ['st_' + st, round(float(a) / 60), round(float(b) / 60), 0])
for v in poc.values():
    v['p'].sort(key=lambda x: x[1])
    if len(v['p']) > 1: kursy.append(v)

out = {'opis': 'Propozycja siatki busów gminy Koszęcin – dzień roboczy. Pociągi KŚ i POLREGIO wg rozkładu 2026/27 (w przybliżeniu). Nie obowiązuje.',
       'przystanki': stops, 'piesze': piesze, 'kursy': kursy}
dst = sys.argv[1] if len(sys.argv) > 1 else '../strona/wyszukiwarka/dane.json'
import os; os.makedirs(os.path.dirname(dst), exist_ok=True)
json.dump(out, open(dst, 'w'), ensure_ascii=False, separators=(',', ':'))
print(dst, len(stops), 'przystanków,', sum(1 for k in kursy if k['l'] in '1234'), 'kursów busów,', len(poc), 'pociągów,', piesze)
