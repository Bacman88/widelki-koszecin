"""Scenariusze filmów „przykładowa podróż” dla film.py (tryb PODROZ).

Dla każdej podróży wybiera kursy z planu (przyklady.szukaj), bierze z symulacji rzeczywiste
odjazdy/przyjazdy (wyniki/przystanki.xml) i pozycje przystanków (FCD), i zapisuje wyniki/podroz_<nazwa>.json.
Uruchom: python3 przyklady_film.py [nazwa ...]; potem np.
  PION=1 KROK=6 PODROZ=wyniki/podroz_strzebin.json FCD=/tmp/fcd_dz.xml ED=/tmp/ed120_dz.xml python3 film.py 0 0 podroz_strzebin
"""
import json, os, re, sys, xml.etree.ElementTree as ET
from przyklady import plan, sym, szukaj, kod, linia, kier, hm, przyj, NAZWY

FCD = os.environ.get('FCD', '/tmp/fcd_dz.xml')
H = 3600
KROTKIE = dict(NAZWY, lubpkp='Lubliniec PKP', str='Strzebiń', kosr='Koszęcin Rynek', rus='Rusinowice', bor='Boronów', wie='Wierzbie')

# nazwa: (tytuł, [(nagłówek, skąd, dokąd, szukaj_od, szukaj_do, preferowana przesiadka)])
PODROZE = {
    'strzebin': ('Strzebiń ⇄ Lubliniec – do pracy i z powrotem', [
        ('RANO · do pracy lub szkoły', 'str', 'lubpkp', 6.7 * H, 6.8 * H, None),
        ('PO POŁUDNIU · powrót do domu', 'lubpkp', 'str', 15.5 * H, 15.6 * H, None)]),
    'pilka': ('Piłka ⇄ Lubliniec – przesiadka w Wierzbiu', [
        ('RANO · z Piłki do Lublińca', 'pil', 'lubpkp', 6.4 * H, 6.6 * H, 'wie'),
        ('PO POŁUDNIU · z Lublińca do Piłki', 'lubpkp', 'pil', 15.5 * H, 15.6 * H, 'wie')]),
    'ankieta': ('Przykładowe połączenia – a Twoja trasa?', [
        ('RANO · z Piasku do Lublińca', 'pia', 'lubpkp', 6.4 * H, 6.6 * H, None),
        ('RANO · z Piłki do szkoły w Lublińcu', 'pil', 'lubpkp', 7.4 * H, 7.6 * H, None),
        ('PO POŁUDNIU · z Lublińca do Boronowa', 'lubpkp', 'bor', 15.4 * H, 15.7 * H, 'kosr'),
        ('WIECZOREM · z pracy w Koszęcinie do Łaz', 'kosr', 'laz', 21.2 * H, 21.4 * H, None)]),
    'ankieta2': ('Przykładowe połączenia – a Twoja trasa?', [
        ('RANO · z Piłki do pracy w Lublińcu na 7:00', 'pil', 'lubp1', 6.5 * H, 6.6 * H, None),
        ('RANO · ze Strzebinia do Lublińca', 'str', 'lubpkp', 6.7 * H, 6.8 * H, None),
        ('PRZED POŁUDNIEM · z Piasku do Koszęcina', 'pia', 'kosr', 8.5 * H, 8.6 * H, None),
        ('NA 14:00 · do pracy w Koszęcinie', 'str', 'kosr', 13.7 * H, 13.75 * H, None),
        ('PO PRACY DO 14:00 · z Koszęcina do Strzebinia', 'kosl', 'str', 14.2 * H, 14.3 * H, None),
        ('Z KOSZĘCINA DO CZĘSTOCHOWY · przez Lisów', 'kosr', 'lisp', 14.0 * H, 14.1 * H, None)]),
    'boronow': ('Boronów ⇄ Lubliniec – przez węzeł Koszęcin Rynek', [
        ('RANO · z Boronowa do Lublińca', 'bor', 'lubpkp', 6.5 * H, 6.7 * H, 'kosr'),
        ('PO POŁUDNIU · z Lublińca do Boronowa', 'lubpkp', 'bor', 15.5 * H, 15.6 * H, 'kosr')]),
}

def symt(k, i, co):
    """Czas z symulacji: 'odj' lub 'prz' kursu k na i-tym przystanku (gdy brak – z planu)."""
    v = sym.get((k, plan[k][i][0]))
    if not v: return plan[k][i][1] if co == 'odj' else przyj(k, i)
    return v[1] if co == 'odj' else v[0]

def main(nazwy):
    potrzebne = {}
    scen = {}
    for nazwa in nazwy:
        tytul, odc = PODROZE[nazwa]
        out = []
        for nag, a, b, od, do, prz in odc:
            war = szukaj(a, b, od, do)
            war = [x for x in war if prz is None or x['przes'] == prz] or war
            x = min(war, key=lambda x: (x['przyjazd'] - x['odjazd'], len(x['kursy'])))
            kursy, linie_op = [], []
            for k, i, j in x['kursy']:
                t0, t1 = symt(k, i, 'odj'), symt(k, j, 'prz')
                kursy.append([k, t0, t1])
                potrzebne.setdefault(k, set()).update([round(t0 / 10) * 10, round(t1 / 10) * 10])
                linie_op.append(f"linia {linia(k)}: {KROTKIE[kod(plan[k][i][0])]} {hm(plan[k][i][1])} → {KROTKIE[kod(plan[k][j][0])]} {hm(przyj(k, j))}")
            czas = round((x['przyjazd'] - x['odjazd']) / 60)
            if x['przes']:
                (k1, _, p), (k2, i2, _) = x['kursy']
                opis = f"{linie_op[0]}\nprzesiadka {KROTKIE[x['przes']]} ({round(x['czekanie'] / 60)} min)\n{linie_op[1]}\nrazem {czas} min"
            else:
                opis = f"{linie_op[0]}\n{czas} min, bez przesiadki"
            pkt = [(kursy[0][0], kursy[0][1])] + [(k, t1) for k, _, t1 in kursy]
            nz = [KROTKIE[a]] + ([KROTKIE[x['przes']]] if x['przes'] else []) + [KROTKIE[b]]
            out.append({'naglowek': nag, 'opis': opis, 'kursy': kursy, 'od': kursy[0][1] - 4 * 60, 'do': kursy[-1][2] + 90,
                        '_pkt': pkt[:1] + pkt[-1:] if not x['przes'] else [pkt[0], pkt[1], pkt[-1]], 'nazwy': nz})
        scen[nazwa] = {'tytul': tytul, 'odcinki': out}
    # pozycje przystanków z FCD (pozycja busa w chwili odjazdu / przyjazdu)
    pos = {}
    for _, el in ET.iterparse(FCD):
        if el.tag == 'timestep':
            t = round(float(el.get('time')))
            for v in el:
                if v.get('id') in potrzebne and t in potrzebne[v.get('id')]:
                    pos[(v.get('id'), t)] = (float(v.get('x')), float(v.get('y')))
            el.clear()
    for nazwa, sc in scen.items():
        for o in sc['odcinki']:
            o['punkty'] = []
            for k, t in o.pop('_pkt'):
                tt = round(t / 10) * 10
                o['punkty'].append(pos.get((k, tt)) or min(((abs(tt2 - tt), p) for (kk, tt2), p in pos.items() if kk == k))[1])
        json.dump(sc, open(f'wyniki/podroz_{nazwa}.json', 'w'), ensure_ascii=False, indent=1)
        print(f'wyniki/podroz_{nazwa}.json')
        for o in sc['odcinki']: print(' ', o['naglowek'], '|', o['opis'].replace('\n', ' | '))

if __name__ == '__main__':
    main(sys.argv[1:] or list(PODROZE))
