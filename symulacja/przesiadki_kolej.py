"""Przesiadki bus ↔ pociąg na stacjach (z przebiegu symulacji: busy wg proponowanego rozkładu, pociągi pasażerskie wg rozkładu 2026/27).
Przesiadka udana: od 3 do 20 minut na przejście i czekanie. Wynik: wyniki/przesiadki_kolej.json + tabela na ekranie."""
import json, collections, xml.etree.ElementTree as ET
STACJE = {'Koszęcin': ('Koszęcin', 'kosp'), 'Strzebiń': ('Strzebiń', 'str'), 'Lisów': ('Lisów', 'lisp'),
          'Boronów': ('Boronów', 'borp'), 'Rusinowice': ('Rusinowice', 'rus'), 'Lubliniec': ('Lubliniec', 'lubpkp')}
KIER = {'131a': 'w stronę Tarnowskich Gór / Bytomia', '131b': 'w stronę Herb (Wieluń, Chorzew)',
        '143a': 'w stronę Kalet / Tarnowskich Gór', '143b': 'w stronę Lublińca',
        '61a': 'w stronę Częstochowy', '61b': 'w stronę Lublińca'}
MIN, MAX = int(__import__("os").environ.get("MIN_PRZES", 3)), 20
poc = collections.defaultdict(list); bus = collections.defaultdict(list)
for e in ET.parse('wyniki/przystanki.xml').getroot():
    vid = e.get('id'); st = e.get('busStop') or e.get('trainStop') or ''
    a, d = float(e.get('started')) / 60, float(e.get('ended')) / 60
    if vid.startswith('poc') and '_p' in vid:
        for nm, (ts, _) in STACJE.items():
            if st.startswith(f'st_{ts}_'): poc[nm].append((vid[3:].split('_')[0], a, d))
    elif vid.startswith('L'):
        for nm, (_, bs) in STACJE.items():
            if st.split('_')[0] == bs: bus[nm].append((vid[1], a, d))
def hm(m): return f'{int(m // 60)}:{int(m % 60):02d}'
wynik = {}
print(f'{"stacja":11} {"kierunek pociągu":36} {"pociąg→bus":>11} {"bus→pociąg":>11}')
for nm in STACJE:
    for k in sorted({x[0] for x in poc[nm]}):
        tr = [x for x in poc[nm] if x[0] == k]
        z_poc = sum(1 for _, a, _ in tr if any(MIN <= bd - a <= MAX for _, _, bd in bus[nm]))
        do_poc = sum(1 for _, _, d in tr if any(MIN <= d - ba <= MAX for _, ba, _ in bus[nm]))
        szczeg = [{'pociag_przyjazd': hm(a), 'bus_odjazd': next((hm(bd) for _, _, bd in sorted(bus[nm], key=lambda b: b[2]) if MIN <= bd - a <= MAX), None),
                   'bus_przyjazd': next((hm(ba) for _, ba, _ in sorted(bus[nm], key=lambda b: -b[1]) if MIN <= d - ba <= MAX), None)} for _, a, d in sorted(tr, key=lambda t: t[1])]
        wynik.setdefault(nm, {})[KIER[k]] = {'pociagow': len(tr), 'z_pociagu_na_busa': z_poc, 'z_busa_na_pociag': do_poc, 'szczegoly': szczeg}
        print(f'{nm:11} {KIER[k]:36} {z_poc:4}/{len(tr):<3}    {do_poc:4}/{len(tr):<3}')
json.dump(wynik, open('wyniki/przesiadki_kolej.json', 'w'), ensure_ascii=False, indent=1)
