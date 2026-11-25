"""Przykładowe podróże w proponowanej siatce (plan + wynik symulacji).

Szuka połączeń bez przesiadki albo z jedną przesiadką (min. 2 min wg planu)
i sprawdza, czy w symulacji przesiadka by się udała (zapas wg wyniki/przystanki.xml).
Wynik: wyniki/przyklady.json i wyniki/przyklady.md
"""
import json, re, sys
from collections import defaultdict

NAZWY = {'bor': 'Boronów', 'borp': 'Boronów PKP', 'bru': 'Brusiek', 'buk': 'Bukowiec', 'chw': 'Chwostek',
         'cie': 'Cieszowa', 'dol': 'Hadra', 'irk': 'Rzyce Irki', 'kalp': 'Kalety PKP', 'kosp': 'Koszęcin PKP',
         'kosr': 'Koszęcin Rynek', 'kossz': 'Koszęcin Szkoła', 'laz': 'Łazy', 'lisp': 'Lisów PKP',
         'lubpkp': 'Lubliniec PKP', 'moc': 'Mochała', 'pia': 'Piasek', 'pil': 'Piłka', 'prad': 'Prądy',
         'psk': 'Płaszczymąka', 'rus': 'Rusinowice PKP', 'sad': 'Sadów', 'str': 'Strzebiń Lubliniecka',
         'strs': 'Strzebiń Szkoła', 'wie': 'Wierzbie'}
MIN_PRZES = 120

plan = json.load(open('plan_kursow.json'))
sym = {}   # (kurs, przystanek_id) -> (przyjazd, odjazd)
for m in re.finditer(r'<stopinfo id="([^"]+)" type="bus"[^>]*started="([\d.]+)" ended="([\d.]+)"[^>]*busStop="([^"]+)"',
                     open('wyniki/przystanki.xml', encoding='utf-8').read()):
    sym[(m[1], m[4])] = (float(m[2]), float(m[3]))

def kod(sid): return sid.split('_')[0]
def linia(k): return k.split('_')[0][1:]
def kier(k): return NAZWY[kod(plan[k][-1][0])]
POSTOJ_RYNEK = 14 * 60   # linie 2–4: w planie na Rynku jest odjazd :03, przyjazd o :49

def przyj(k, i):
    """Planowy przyjazd kursu k na i-ty przystanek."""
    t = plan[k][i][1]
    if kod(plan[k][i][0]) == 'kosr' and linia(k) in '234' and 0 < i < len(plan[k]) - 1: t -= POSTOJ_RYNEK
    return t
def hm(t): t = int(round(t / 60)); return f'{t // 60}:{t % 60:02d}'

def odcinki(skad, dokad):
    """Wszystkie przejazdy jednym kursem: (kurs, i_od, i_do)."""
    for k, st in plan.items():
        for i, a in enumerate(st):
            if kod(a[0]) != skad: continue
            for j in range(i + 1, len(st)):
                if kod(st[j][0]) == dokad:
                    yield k, i, j

def szukaj(skad, dokad, od, do):
    wyn = []
    for k, i, j in odcinki(skad, dokad):
        st = plan[k]
        if od <= st[i][1] <= do:
            wyn.append({'odjazd': st[i][1], 'przyjazd': przyj(k, j), 'kursy': [(k, i, j)], 'przes': None, 'czekanie': 0})
    # jedna przesiadka
    for k1, st1 in plan.items():
        for i, a in enumerate(st1):
            if kod(a[0]) != skad or not od <= a[1] <= do: continue
            for p in range(i + 1, len(st1)):
                w = kod(st1[p][0])
                if w == dokad: break
                for k2, i2, j2 in odcinki(w, dokad):
                    if linia(k2) == linia(k1): continue
                    st2 = plan[k2]; cz = st2[i2][1] - przyj(k1, p)
                    if cz < MIN_PRZES or cz > 35 * 60: continue
                    wyn.append({'odjazd': a[1], 'przyjazd': przyj(k2, j2), 'kursy': [(k1, i, p), (k2, i2, j2)], 'przes': w, 'czekanie': cz})
    # najlepsze: dla każdego przyjazdu najpóźniejszy odjazd, potem bez zdominowanych
    # bez przesiadki lepsze od przesiadki przy tych samych godzinach; warianty z inną przesiadką i tymi samymi godzinami zostają
    def lepszy(y, x):
        if y['odjazd'] < x['odjazd'] or y['przyjazd'] > x['przyjazd']: return False
        if (y['odjazd'], y['przyjazd']) != (x['odjazd'], x['przyjazd']): return True
        return len(y['kursy']) < len(x['kursy']) or (y['przes'] == x['przes'] and y['czekanie'] < x['czekanie'])
    dobre = [x for x in wyn if not any(lepszy(y, x) for y in wyn if y is not x)]
    u = {}
    for x in dobre: u.setdefault((x['odjazd'], x['przyjazd'], x['przes']), x)
    dobre = list(u.values())
    return sorted(dobre, key=lambda x: (x['odjazd'], x['czekanie']))

def opis(x):
    cz = []
    for k, i, j in x['kursy']:
        st = plan[k]
        cz.append(f"linia {linia(k)} (kier. {kier(k)}): {NAZWY[kod(st[i][0])]} {hm(st[i][1])} → {NAZWY[kod(st[j][0])]} {hm(przyj(k, j))}")
    s = {'tekst': '; przesiadka, '.join(cz), 'czas_min': round((x['przyjazd'] - x['odjazd']) / 60),
         'odjazd': hm(x['odjazd']), 'przyjazd': hm(x['przyjazd'])}
    if x['przes']:
        (k1, _, p), (k2, i2, _) = x['kursy']
        s['przesiadka'] = NAZWY[x['przes']]
        s['zapas_plan_min'] = round(x['czekanie'] / 60, 1)
        a = sym.get((k1, plan[k1][p][0])); b = sym.get((k2, plan[k2][i2][0]))
        if a and b:
            s['zapas_symulacja_min'] = round((b[1] - a[0]) / 60, 1)
    return s

H = 3600
PRZYKLADY = [
    ('Ze Strzebinia do Lublińca rano (praca na 7:00 / 8:00, szkoła na 8:00)', 'str', 'lubpkp', 5 * H, 7.6 * H),
    ('Z Piłki do Lublińca rano – przesiadka w Wierzbiu', 'pil', 'lubpkp', 5 * H, 7.6 * H),
    ('Z Rusinowic do Lublińca rano – przesiadka w Wierzbiu', 'rus', 'lubpkp', 5 * H, 7.6 * H),
    ('Z Boronowa do Lublińca rano', 'bor', 'lubpkp', 5 * H, 7.6 * H),
    ('Z Łaz do szkoły w Koszęcinie (na 8:00)', 'laz', 'kossz', 6 * H, 7.8 * H),
    ('Z Lublińca do Strzebinia po południu', 'lubpkp', 'str', 14 * H, 17.5 * H),
    ('Z Lublińca do Piłki po południu – przesiadka w Wierzbiu', 'lubpkp', 'pil', 14 * H, 17.5 * H),
    ('Z Lublińca do Boronowa po południu', 'lubpkp', 'bor', 14 * H, 17.5 * H),
]
if __name__ == '__main__':
    out, md = [], ['# Przykładowe podróże w proponowanej siatce busów\n',
                   'Wg planu kursów (`plan_kursow.json`); zapas przesiadki sprawdzony w symulacji SUMO (dzień roboczy). Propozycja mieszkańców – nie obowiązujący rozkład.\n']
    for tyt, a, b, od, do in PRZYKLADY:
        poj = [opis(x) for x in szukaj(a, b, od, do)]
        out.append({'tytul': tyt, 'skad': NAZWY[a], 'dokad': NAZWY[b], 'polaczenia': poj})
        md.append(f'\n## {tyt}\n')
        for s in poj:
            z = ''
            if 'przesiadka' in s:
                z = f" — przesiadka {s['przesiadka']}: {s['zapas_plan_min']} min wg planu"
                if 'zapas_symulacja_min' in s: z += f", {s['zapas_symulacja_min']} min w symulacji"
            md.append(f"- **{s['odjazd']} → {s['przyjazd']}** ({s['czas_min']} min): {s['tekst']}{z}")
    json.dump(out, open('wyniki/przyklady.json', 'w'), ensure_ascii=False, indent=1)
    open('wyniki/przyklady.md', 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md))
