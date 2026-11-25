"""Dane dla wyszukiwarki połączeń na stronie (strona/wyszukiwarka/dane.json).

Busy: proponowany rozkład dnia roboczego (plan_kursow.json – ten sam, który jedzie w symulacji).
Pociągi KŚ i POLREGIO: rozkład 2026/27 z GTFS (dane/kolej/pociagi.json).
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
          'Kochanowice': ((50.6995, 18.7486), None), 'Kalety': ((50.5663, 18.8883), 'kalp')}

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

# --- busy: dzień roboczy z planu symulacji (plan_kursow.json), sobota i niedziela z rozkładu (out/rozklad_data.json)
def kurs_z_planu(kid, st):
    l = kid.split('_')[0][1:]; p = []
    for i, (sid, t, stale) in enumerate(st):
        kod = sid.split('_')[0]; arr = dep = round(t / 60)
        if kod == 'kosr' and l in '234' and 0 < i < len(st) - 1:   # postój w węźle: przyjazd ok. :49, odjazd :03
            arr = max(round((t - POSTOJ_RYNEK) / 60), p[-1][2] + 1)
        p.append([kod, arr, dep, 0 if stale else 1])
    return {'l': l, 'k': NAZWY[p[-1][0]], 'p': p}

dni = {'wd': [kurs_z_planu(k, st) for k, st in sorted(plan.items(), key=lambda x: x[1][0][1])]}
# czasy przejazdu między kolejnymi przystankami (z dnia roboczego) – do wyliczenia odjazdu z Rynku w weekend
jazda = {}
for k in dni['wd']:
    for a, b in zip(k['p'], k['p'][1:]): jazda.setdefault((k['l'], a[0], b[0]), b[1] - a[2])
KOD = {v: k for k, v in NAZWY.items()}
rd = json.load(open('../out/rozklad_data.json'))['tt']
for dz in ('sat', 'sun'):
    dni[dz] = []
    for l, v in rd.items():
        for kier, x in v[dz].items():
            kody = [KOD[n] for n in x['stops']]
            for czasy, zam in x['trips']:
                p = []
                for i, (kod, t) in enumerate(zip(kody, czasy)):
                    dep = t
                    if kod == 'kosr' and 0 < i < len(kody) - 1 and (l, kod, kody[i + 1]) in jazda:
                        dep = max(t, czasy[i + 1] - jazda[(l, kod, kody[i + 1])])
                    p.append([kod, t, dep, 1 if kod in ('irk', 'psk') else 0])
                k = {'l': l, 'k': NAZWY[kody[-1]], 'p': p}
                if zam: k['zam'] = 1
                dni[dz].append(k)

# --- pociągi: rozkład 2026/27 z GTFS (dane/kolej/pociagi.json, akcja GitHub „Rozkład kolejowy”)
kol = json.load(open('../dane/kolej/pociagi.json'))
for dz, lst in kol['pociagi'].items():
    for x in lst:
        prz = 'KŚ' if 'Śląskie' in x['przewoznik'] else 'PR'
        dni[dz].append({'l': prz, 'nr': f"{x['linia']} {x['nr']}".strip(), 'k': x['kier'],
                        'p': [['st_' + s, a, b, 0] for s, a, b in x['p']]})
for dz, v in dni.items(): v.sort(key=lambda k: k['p'][0][2])
out = {'opis': 'Propozycja siatki busów gminy Koszęcin. Pociągi KŚ i POLREGIO wg rozkładu 2026/27 (GTFS, dni: ' + ', '.join(kol['dni'].values()) + '). Nie obowiązuje.',
       'przystanki': stops, 'piesze': piesze, 'dni': dni}
dst = sys.argv[1] if len(sys.argv) > 1 else '../strona/wyszukiwarka/dane.json'
import os; os.makedirs(os.path.dirname(dst), exist_ok=True)
json.dump(out, open(dst, 'w'), ensure_ascii=False, separators=(',', ':'))
print(dst, len(stops), 'przystanków;', {d: (sum(1 for k in v if k['l'] in '1234'), sum(1 for k in v if k['l'] not in '1234')) for d, v in dni.items()}, piesze)
