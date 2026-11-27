"""Pociągi: przelotowe kursy po liniach kolejowych od brzegu do brzegu mapy, z krótkimi postojami na stacjach.

Linie (numery wg OSM / PKP PLK) i stacje w wycinku mapy:
- 131 Magistrala Węglowa: (Herby) → Boronów → Strzebiń → (Kalety, Tarnowskie Góry)
- 143: (Ciasna) → Kochcice → Lubliniec → Rusinowice → Koszęcin → (Kalety, Tarnowskie Góry)
- 61:  Lubliniec → Kochanowice → Lisów → (Herby Stare, Częstochowa)
Mapa kończy się tuż przed Kaletami i na zachód od Lublińca, więc tam pociągi wjeżdżają / zjeżdżają z mapy.
- 152: Lubliniec → (Pyskowice) – tylko towarowe
Pasażerskie wg rozkładu 2026/27 (patrz PASAZERSKIE), towarowe – szacunek. Pasażerskie stają na każdej stacji na 30 s,
towarowe przejeżdżają bez zatrzymania. Wynik: pociagi.rou.xml + stacje.add.xml.
"""
import os, sys, random, json
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
random.seed(7)
n = sumolib.net.readNet('koszecin.net.xml.gz', withPrograms=False)
RAIL = [e for e in n.getEdges() if e.allows('rail') and not e.allows('passenger') and not e.getID().startswith(':')]

STACJE = {'Herby': None, 'Boronów': (18.9014, 50.6654), 'Strzebiń': (18.9000, 50.6184), 'Kalety': (18.8883, 50.5663),
          'Kochcice-Glinica': (18.6576, 50.7138), 'Lubliniec': (18.6910, 50.6726), 'Rusinowice': (18.7638, 50.6490),
          'Koszęcin': (18.8359, 50.6230), 'Kochanowice': (18.7486, 50.6995), 'Lisów': (18.7911, 50.7208)}
# linia: punkty po kolei (lon, lat) – brzeg mapy, stacje, brzeg mapy; nazwy z STACJE oznaczają postój pasażerskich
LINIE = {
    '131': [(18.8497, 50.7557), 'Boronów', 'Strzebiń', 'Kalety', (18.8927, 50.5530)],
    '143': [(18.6335, 50.7507), 'Kochcice-Glinica', 'Lubliniec', 'Rusinowice', 'Koszęcin', 'Kalety', (18.8927, 50.5530)],
    '61':  ['Lubliniec', 'Kochanowice', 'Lisów', 'Herby Stare', (18.9553, 50.7695)],
    '152': ['Lubliniec', (18.6269, 50.5685)],
}
# towarowe na godzinę w każdą stronę – szacunek (brak publicznych rozkładów towarowych)
TOWAROWE = {'131': 1.0, '143': 1.0, '61': 0.5, '152': 0.5}
# Pociągi pasażerskie wg rozkładu (dzień roboczy, poniedziałek 14.12.2026): odjazdy ze stacji odniesienia.
# Źródła: e-podroznik.pl (tablice odjazdów Strzebiń, Lisów – rozkład 2026/27 od 13.12.2026);
# Koszęcin: koleo.pl, tablica z 24.11.2026 (rozkład 2025/26 – do sprawdzenia po 13.12).
# a = kierunek jak w LINIE (131: na południe; 143: Lubliniec → Koszęcin → Kalety; 61: Lubliniec → Lisów → Częstochowa), b = odwrotnie.
PASAZERSKIE = {
    ('131', 'a'): ('Strzebiń', '04:58 05:39 06:22 06:58 07:25 08:03 09:39 10:00 11:41 12:50 13:19 13:35 14:54 16:26 16:49 17:26 18:23 20:36 21:29'),
    ('131', 'b'): ('Strzebiń', '05:42 07:03 07:27 08:38 09:27 09:38 11:46 12:37 14:37 14:49 15:48 16:35 17:41 18:34 19:08 20:34 22:37'),
    ('143', 'a'): ('Koszęcin', '05:01 06:02 06:58 08:06 08:56 10:01 11:01 11:59 13:01 13:56 15:01 15:59 16:58 17:54 18:58 19:58 21:02 21:56 22:40'),
    ('143', 'b'): ('Koszęcin', '05:17 06:07 07:01 07:58 09:04 10:05 11:04 11:58 12:58 13:58 15:09 16:04 16:58 18:07 18:58 19:58 21:02 21:50 22:57'),
    ('61', 'a'):  ('Lisów', '04:51 05:48 07:01 09:07 10:44 12:48 14:38 15:48 16:46 17:44 19:46 20:52 22:01'),
    ('61', 'b'):  ('Lisów', '05:59 06:59 07:32 08:25 10:15 12:19 14:05 15:14 16:16 17:15 18:47 20:13 21:07 21:59 23:09'),
}
# przewoźnik: PR = POLREGIO, reszta = Koleje Śląskie (KŚ)
PR = {('131', 'a'): '04:58 06:58 08:03 10:00 12:50 13:35 14:54 16:49 17:26',
      ('131', 'b'): '07:03 09:38 11:46 14:49 15:48 17:41 19:08',
      ('61', 'a'): '14:38 16:46', ('61', 'b'): '06:59 07:32 14:05 16:16'}
# Nowy rozkład 2026/27 z GTFS (dane/kolej/pociagi.json – akcja GitHub „Rozkład kolejowy”): nadpisuje tablice powyżej.
# Każdy pociąg pasażerski jedzie swoją trasą z prawdziwymi godzinami (postój do godziny odjazdu z rozkładu).
# Pociąg zmieniający kierunek (POLREGIO Lubliniec – Lisów – Herby Stare – Boronów – Strzebiń – Kalety) to dwa
# przejazdy: do Herb Starych i – po postoju – z Herb Starych na Boronów.
STACJE.update({'Herby Stare': (18.8821, 50.7477), 'Herby Nowe': (18.8545, 50.7473), 'Kalety': (18.8885, 50.5663)})
POLUDNIE, CZESTOCHOWA, WIELUN = (18.8927, 50.5530), (18.9553, 50.7695), (18.8497, 50.7557)
WYJAZD = {**{s: POLUDNIE for s in ('Miasteczko Śląskie', 'Tarnowskie Góry', 'Bytom', 'Chorzów Batory', 'Katowice', 'Gliwice', 'Kalety Drutarnia')},
          'Częstochowa': CZESTOCHOWA, 'Częstochowa Stradom': CZESTOCHOWA, 'Kłobuck': WIELUN, 'Wieluń Dąbrowa': WIELUN}
NA_MAPIE = {'Lubliniec', 'Kochanowice', 'Lisów', 'Herby Stare', 'Herby Nowe', 'Rusinowice', 'Koszęcin', 'Boronów', 'Strzebiń', 'Kalety'}
LINIE_ST = {'143': ['Lubliniec', 'Rusinowice', 'Koszęcin', 'Kalety'], '131': ['Herby Nowe', 'Boronów', 'Strzebiń', 'Kalety'],
            '61': ['Lubliniec', 'Kochanowice', 'Lisów', 'Herby Stare']}
def klucz(nazwy, wyj=None):
    """Linia i kierunek (jak w LINIE) – do nazwy pojazdu (przesiadki_kolej.py)."""
    for lin in ('143', '131', '61'):
        lst = [x for x in nazwy if x in LINIE_ST[lin]]
        if lin == '143' and not set(lst) & {'Rusinowice', 'Koszęcin'}: continue
        if lin == '131' and not set(lst) & {'Boronów', 'Strzebiń'}: continue
        if lin == '61' and not lst: continue
        if len(lst) >= 2: return lin + ('a' if LINIE_ST[lin].index(lst[0]) < LINIE_ST[lin].index(lst[1]) else 'b')
        return lin + ('a' if wyj == CZESTOCHOWA else 'b')
    return None
def z_gtfs(plik='../dane/kolej/pociagi.json', dzien='wd'):
    """Lista przejazdów: (klucz, nr, przewoźnik K/P/I, punkt wjazdu, [(stacja, przyjazd, odjazd) min], punkt wyjazdu)."""
    import json
    wyn = []
    for x in json.load(open(plik))['pociagi'][dzien]:
        st = sorted([tuple(q) for q in x['p']] + [tuple(q) for q in x['cele'] if q[0] in NA_MAPIE], key=lambda q: (q[1], q[2]))
        if not st: continue
        przed = [q for q in x['cele'] if q[2] <= st[0][1] and q[0] not in NA_MAPIE]
        po = [q for q in x['cele'] if q[1] >= st[-1][2] and q[0] not in NA_MAPIE]
        wj = WYJAZD.get(max(przed, key=lambda q: q[2])[0]) if przed else None
        wy = WYJAZD.get(min(po, key=lambda q: q[1])[0]) if po else None
        if len(st) == 1 and not (wj or wy): continue          # np. Lubliniec – Opole: poza mapą
        pz = x['przewoznik'].upper()
        k = 'P' if 'POLREGIO' in pz else 'I' if 'INTERCITY' in pz or x.get('linia', '').startswith(('IC', 'TLK', 'EIP')) else 'K'
        nazwy = [q[0] for q in st]
        # zmiana kierunku w Herbach Starych (linia 61 ↔ 131)
        if 'Herby Stare' in nazwy and 0 < nazwy.index('Herby Stare') < len(nazwy) - 1:
            i = nazwy.index('Herby Stare'); a, b = st[:i + 1], st[i:]
            if {'Boronów', 'Strzebiń', 'Herby Nowe'} & {q[0] for q in a + b} and {'Lisów', 'Kochanowice'} & {q[0] for q in a + b}:
                a[-1] = (a[-1][0], a[-1][1], a[-1][2] - 2)   # pierwszy przejazd znika chwilę przed odjazdem drugiego
                wyn.append((klucz([q[0] for q in a]), x['nr'], k, wj, a, None))
                wyn.append((klucz([q[0] for q in b]), x['nr'] + 'z', k, None, b, wy)); continue
        wyn.append((klucz(nazwy, wy), x['nr'], k, wj, st, wy))
    return wyn
POCIAGI = z_gtfs()

def kandydaci(lon, lat, r=400):
    """Krawędzie torów przy punkcie (oba kierunki, wszystkie tory szlaku)."""
    x, y = n.convertLonLat2XY(lon, lat)
    kand = sorted((sumolib.geomhelper.distancePointToPolygon((x, y), e.getShape()), e) for e in RAIL)
    kand = [k for k in kand if k[0] < r]
    if not kand: raise SystemExit(f'brak torów przy {lat},{lon}')
    d0 = kand[0][0]
    return [e for d, e in kand if d < d0 + 30][:8]

import heapq, collections
UZYTE = set()   # krawędzie już użyte przez trasy w jakimś kierunku – jazda „pod prąd” po nich jest karana
def bidi(e):
    return [o for o in e.getToNode().getOutgoing() if o.getToNode() == e.getFromNode() and o in RAILSET]
RAILSET = set(RAIL)
KARA = [25]
def koszt(e):
    return e.getLength() * (KARA[0] if any(b in UZYTE for b in bidi(e)) else 1)
def droga(a, b):
    """Dijkstra po torach; tor używany już w przeciwnym kierunku jest drogi (dwutorowe szlaki: każdy kierunek swoim torem)."""
    if a == b: return [a], 0
    dist = {a: 0}; prev = {}; pq = [(0, id(a), a)]
    while pq:
        d, _, e = heapq.heappop(pq)
        if e == b: break
        if d > dist[e]: continue
        for o in e.getOutgoing():
            if o not in RAILSET: continue
            nd = d + koszt(o)
            if nd < dist.get(o, 1e18): dist[o] = nd; prev[o] = e; heapq.heappush(pq, (nd, id(o), o))
    if b not in dist: return None, None
    p = [b]
    while p[-1] != a: p.append(prev[p[-1]])
    return p[::-1], dist[b]

_TR = {}
def trasa(punkty):
    """Jak trasa0, ale bez długich objazdów: jeśli kara za jazdę „pod prąd” wydłuża trasę o ponad 10 %, bierzemy najkrótszą."""
    k = tuple(punkty)
    if k in _TR: return _TR[k]
    ed, kr = trasa0(punkty)
    dl = sum(e.getLength() for e in ed)
    KARA[0] = 1; ed2, kr2 = trasa0(punkty, zapisz=False); KARA[0] = 25
    if dl > 1.1 * sum(e.getLength() for e in ed2): ed, kr = ed2, kr2
    _TR[k] = (ed, kr); return ed, kr
def trasa0(punkty, zapisz=True):
    """Najkrótszy przejazd przez kolejne punkty (programowanie dynamiczne po kandydatach) – bez zawracania."""
    C = [kandydaci(*(STACJE[p] if isinstance(p, str) else p)) for p in punkty]
    best = {e: (0.0, [e]) for e in C[0]}
    best = {e: (koszt(e), [e]) for e in C[0]}
    for warstwa in C[1:]:
        nowe = {}
        for b in warstwa:
            opcje = []
            for a, (kk, sciezka) in best.items():
                if a == b: opcje.append((kk, sciezka)); continue
                p, c = droga(a, b)
                if p: opcje.append((kk + c, sciezka + list(p[1:])))
            if opcje: nowe[b] = min(opcje, key=lambda o: o[0])
        if not nowe: raise SystemExit('brak przejazdu po torach')
        best = nowe
    _, ed = min(best.values(), key=lambda o: o[0])
    if zapisz: UZYTE.update(ed)
    kr = []
    for warstwa in C:
        kr.append(next((e for e in ed if e in warstwa), warstwa[0]))
    return ed, kr

def odwrotna(punkty): return list(reversed(punkty))

def peron(p, ed):
    x, y = n.convertLonLat2XY(*STACJE[p])
    e2 = min(ed, key=lambda q: sumolib.geomhelper.distancePointToPolygon((x, y), q.getShape()))
    ln = e2.getLanes()[0]; pos, _ = sumolib.geomhelper.polygonOffsetAndDistanceToPoint((x, y), ln.getShape())
    L = ln.getLength(); a = max(0, min(pos - 40, L - 81)); b = min(L, a + 80)
    sid = f'st_{p}_{e2.getID()}'.replace(' ', '')
    stacje_def[sid] = (ln.getID(), a, b, p)
    return sid, e2, b

def czas_do(ed, e_cel, poz, postoje_przed):
    """Przybliżony czas jazdy pociągu pasażerskiego od początku trasy do peronu (s)."""
    t = 0.0
    for e in ed:
        v = min(e.getSpeed(), 33) * 0.85
        if e == e_cel: return t + poz / v + 30 * postoje_przed + 40
        t += e.getLength() / v
    return t

def hm(s): h, m = s.split(':'); return int(h) * 3600 + int(m) * 60

stacje_def = {}; v = []
for linia, pkt in LINIE.items():
    for kier in ('a', 'b'):
        # towarowe: od brzegu do brzegu, bez postojów
        pk = pkt if kier == 'a' else odwrotna(pkt)
        ed, _ = trasa(pk); ids = [e.getID() for e in ed]
        co = int(3600 / TOWAROWE[linia]); off = random.randrange(0, co, 60)
        for i, t in enumerate(range(4 * 3600 + off, 23 * 3600, co)):
            v.append((t, f'poc{linia}{kier}_t{i:02d}', ids, 'towarowy', []))

# pasażerskie wg rozkładu – każdy pociąg osobno
NR_LINIA = {x['nr']: x.get('linia', '') for x in json.load(open('../dane/kolej/pociagi.json'))['pociagi']['wd']}
ETYK_LINII = {}   # numer linii na filmach (S1, S13, S8, S82, IC, TLK, EIC; POLREGIO bez numeru → PR)
licz = collections.Counter()
for kl, nr, prz, wj, st, wy in POCIAGI:
    pkt = ([wj] if wj else []) + [q[0] for q in st] + ([wy] if wy else [])
    try: ed, _ = trasa(pkt)
    except SystemExit as e: print('pomijam', nr, pkt, e); continue
    ids = [e.getID() for e in ed]
    postoje = []
    for j, (p, a_, d_) in enumerate(st):
        sid, e2, poz = peron(p, ed)
        if j == 0: t0 = czas_do(ed, e2, poz, 0) if wj else 0
        postoje.append((sid, d_ * 60))
    dep = st[0][1] * 60 - t0 - 30 if wj else st[0][2] * 60 - 60
    licz[kl] += 1
    vid = f'poc{kl}_{"x" if prz == "I" else "p"}{licz[kl]:02d}{prz}'
    lin = NR_LINIA.get(nr.rstrip('z'), '')
    ETYK_LINII[vid] = 'PR' if prz == 'P' else (lin.replace('ZKA ', '') or ('IC' if prz == 'I' else 'KŚ'))
    v.append((max(0, round(dep)), vid, ids, 'pociag', postoje))
print('pasażerskie:', dict(licz))

with open('stacje.add.xml', 'w') as o:
    o.write('<additional>\n')
    for sid, (ln, a, b, nm) in sorted(stacje_def.items()):
        o.write(f'  <trainStop id="{sid}" lane="{ln}" startPos="{a:.1f}" endPos="{b:.1f}" name="{nm}" friendlyPos="true"/>\n')
    o.write('</additional>\n')
with open('pociagi.rou.xml', 'w') as o:
    o.write('<routes>\n  <vType id="pociag" vClass="rail" length="75" maxSpeed="33" accel="0.6" decel="0.9" guiShape="rail" color="80,80,80"/>\n')
    o.write('  <vType id="towarowy" vClass="rail" length="600" maxSpeed="16.7" accel="0.25" decel="0.5" guiShape="rail/cargo" color="40,40,40"/>\n')
    for dep, vid, ed, typ, st in sorted(v):
        o.write(f'  <vehicle id="{vid}" type="{typ}" depart="{dep}" departLane="best" insertionChecks="collision"><route edges="{" ".join(ed)}"/>')
        o.write(''.join(f'<stop trainStop="{s}" duration="20" until="{u}"/>' for s, u in st) + '</vehicle>\n')
    o.write('</routes>\n')
json.dump(ETYK_LINII, open('pociagi_linie.json', 'w'), ensure_ascii=False, indent=0)
print('pociągów:', len(v), '| stacji:', len(stacje_def))
