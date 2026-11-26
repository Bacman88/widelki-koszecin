import os
"""Scenariusz SUMO dla proponowanej siatki busów gminy Koszęcin (dzień roboczy, wariant pełny).

Wejście:  koszecin.net.xml (sieć z OpenStreetMap), data.json (trasy i przystanki), rozklad_data.json (rozkład).
Wyjście:  przystanki.add.xml, busy.rou.xml, pociagi.rou.xml (+ tlo.rou.xml z randomTrips), koszecin.sumocfg.

Założenia (do zmiany na górze pliku):
- busy jadą trasami z projektu (te same węzły OSM); na węzłach stoją 20 s i nie odjeżdżają przed czasem
  (until), na zwykłych przystankach 10 s, na żądanie (Irki, Płaszczymąka) zatrzymują się tylko czasem, na 6 s;
  na Rynku linie 2–4 czekają do :03;
- pociągi: po jednym na godzinę w każdą stronę na każdej linii kolejowej przez obszar (przybliżenie),
  dzięki czemu przejazdy kolejowe zamykają się jak w rzeczywistości;
- ruch tła: losowe samochody na całej sieci (randomTrips), żeby skrzyżowania nie były puste.
"""
import json, math, os, sys
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
from sumolib.route import mapTrace

D = json.load(open(sys.argv[1] if len(sys.argv) > 1 else '../out/data.json'))
R = json.load(open(sys.argv[2] if len(sys.argv) > 2 else '../out/rozklad_data.json'))
NET = sumolib.net.readNet('koszecin.net.xml.gz')
POSTOJ = 20          # s na węzłach przesiadkowych (Rynek, stacje, Strzebiń, Lubliniec)
POSTOJ_ZWYKLY = 10   # s na zwykłym przystanku po drodze
POSTOJ_NZ = 6        # s na przystanku na żądanie, gdy ktoś wsiada/wysiada
NA_ZADANIE = {'irk': 3.5, 'psk': 14, 'prad': 8, 'bukz': 4, 'wiel': 3, 'cien': 3}   # przystanek: ile razy na dobę bus faktycznie się zatrzymuje (szacunek mieszkańca)
PUNKTY_CZASOWE = set()        # + WEZLY: tylko tu bus czeka, jeśli jest przed czasem
OKNO = (4 * 3600 + 30 * 60, 23 * 3600 + 59 * 60)

S = D['stops']; NAME2ID = {v[2]: k for k, v in S.items()}
# przystanki istniejące, których nie ma w rozkładzie projektu (tylko główne przystanki) – dokładane w symulacji,
# jeśli trasa linii przechodzi obok; czas przejazdu liczony proporcjonalnie do odległości
DODATKOWE = {}   # Prądy są już w rozkładzie (od 25.11.2026)
S.update({k: list(v) for k, v in DODATKOWE.items()})
def xy(lat, lon): return NET.convertLonLat2XY(lon, lat)
def dist(a, b): return math.hypot(a[0] - b[0], a[1] - b[1])

def odcinek(P, a, b):
    """Najkrótszy fragment ścieżki P (lub odwróconej) prowadzący od przystanku a do b."""
    best = None
    for seq in (P, P[::-1]):
        pa = xy(*S[a][:2]); pb = xy(*S[b][:2])
        ia = [i for i, q in enumerate(seq) if dist(q, pa) < 90]
        ib = [j for j, q in enumerate(seq) if dist(q, pb) < 90]
        for i in ia:
            for j in ib:
                if j > i:
                    L = sum(dist(seq[k], seq[k + 1]) for k in range(i, j))
                    if best is None or L < best[0]: best = (L, seq[i:j + 1])
    if best is None: raise SystemExit(f'Brak odcinka {a} → {b}')
    return best[1]

def trasa(line, stops):
    P = [xy(*q) for q in D['lines'][line]['path']]
    P1P = [xy(*q) for q in D['lines']['1P']['path']] if '1P' in D['lines'] else None
    tr = []
    for a, b in zip(stops, stops[1:]):
        # linia 1 – kursy szkolne przez Psary: odcinki Płaszczymąka – Psary Główna – Piasek po trasie 1P
        seg = odcinek(P1P if (line == '1' and 'psy' in (a, b) and P1P) else P, a, b)
        tr += seg if not tr else seg[1:]
    edges = mapTrace(tr, NET, 30, vClass='bus', fillGaps=600)
    out = []
    for e in edges:
        e = e if isinstance(e, str) else e.getID()
        if not out or out[-1] != e: out.append(e)
    # uzupełnij brakujące połączenia (mapTrace bywa nieciągły na skrzyżowaniach)
    fix = [out[0]]
    for e in out[1:]:
        a = NET.getEdge(fix[-1]); b = NET.getEdge(e)
        if b not in a.getAllowedOutgoing('bus'):
            p, _ = NET.getShortestPath(a, b, vClass='bus')
            if p: fix += [x.getID() for x in p[1:-1]]
        fix.append(e)
    # usuń „wjazdy w boczną uliczkę i zawracanie” (mapTrace bywa zwiedziony na skrzyżowaniach): …P, Y, -Y, Q…
    zmiana = True
    while zmiana:
        zmiana = False
        for i in range(1, len(fix) - 2):
            Y, Yr = NET.getEdge(fix[i]), NET.getEdge(fix[i + 1])
            if Y.getFromNode() == Yr.getToNode() and Y.getToNode() == Yr.getFromNode():
                # prawdziwy wjazd do pętli/stacji w środku trasy (np. linia 2 do Koszęcin PKP) – zostaw
                if any(sumolib.geomhelper.polygonOffsetAndDistanceToPoint(xy(*S[w][:2]), Y.getLanes()[0].getShape())[1] < 60
                       for w in stops[1:-1] if w in WEZLY): continue
                P, Q = NET.getEdge(fix[i - 1]), NET.getEdge(fix[i + 2])
                if Q in P.getAllowedOutgoing('bus'): wst = []
                else:
                    p, _ = NET.getShortestPath(P, Q, vClass='bus')
                    if not p or sum(x.getLength() for x in p[1:-1]) > Y.getLength() * 2 + 200: continue
                    wst = [x.getID() for x in p[1:-1]]
                fix = fix[:i] + wst + fix[i + 2:]; zmiana = True; break
    return fix

def przystanek_na_trasie(edges, sid, od):
    """Krawędź z trasy (od indeksu od) najbliższa przystankowi i pozycja na niej."""
    p = xy(*S[sid][:2]); best = None
    for k in range(od, len(edges)):
        e = NET.getEdge(edges[k]); ln = e.getLanes()[0]
        pos, d = sumolib.geomhelper.polygonOffsetAndDistanceToPoint(p, ln.getShape())
        if best is None or d < best[0] - 1: best = (d, k, pos, ln)
        if best and d > best[0] + 800 and k > best[1] + 3: break
    return best

WSTAW = {}
# Koszęcin Rynek wg mieszkańca: kierunek na południe – zatoka za skrzyżowaniem z Placem Kościuszki (jak było);
# kierunek na północ – zatoka przy placu po wschodniej stronie Powstańców Śląskich, między Placem Kościuszki
# a wjazdem na Boronowską (ok. 37 m, mieszczą się ok. 3 busy).
STALE = {'kosr': {'-271#3': True}}    # kierunek na północ: zatoka przy placu; na południe: zatoka jak dotąd (271#5)
BEZ_ZATOKI = set()
DL_ZATOKI = {'kosr_-271#3': 37}          # długość zatoki przy placu [m] – ok. 3 busy
WEZLY = {'kosr', 'kosp', 'lubpkp', 'lisp', 'kalp', 'bor', 'laz', 'kurz', 'pil', 'pia', 'str'}   # przystanki z zatoką / pętlą: autobus czekający nie blokuje drogi
stopdefs = {}; vehicles = []
for line, days in R['tt'].items():
    if line not in D['lines']: continue
    for nm, dd in days['wd'].items():
        ids = [NAME2ID.get(s) or NAME2ID[s.split(' (')[0]] for s in dd['stops']]
        edges = trasa(line, ids)
        for x in DODATKOWE:
            p = xy(*S[x][:2])
            d, k = min((sumolib.geomhelper.polygonOffsetAndDistanceToPoint(p, NET.getEdge(e).getLanes()[0].getShape())[1], k)
                       for k, e in enumerate(edges))
            if d > 40: continue
            sk = []
            for y in ids: sk.append(przystanek_na_trasie(edges, y, sk[-1] if sk else 0)[1])
            for i in range(1, len(ids)):
                if sk[i - 1] <= k <= sk[i] and sk[i - 1] < sk[i]:
                    ids.insert(i, x); WSTAW[(line, nm)] = (i, edges, sk[i - 1], k, sk[i]); break
        k0 = 0; stl = []
        for i, sid in enumerate(ids):
            d, k, pos, ln = przystanek_na_trasie(edges, sid, k0)
            dl = 45 if sid in WEZLY else 12
            kk = [j for j in range(k0, len(edges)) if edges[j] in STALE.get(sid, ())]
            if kk:                                             # przystanek wskazany ręcznie: cała krawędź
                k = kk[0]
                ln = NET.getEdge(edges[k]).getLanes()[0]; pos = ln.getLength() - 0.5; dl = pos - 0.5
            if not kk and ln.getLength() < dl + 5:   # za krótka krawędź – przystanek na sąsiedniej (dłuższej) krawędzi trasy
                cand = [(NET.getEdge(edges[j]).getLength(), j) for j in (k - 1, k + 1) if 0 <= j < len(edges) and j >= k0]
                Lc, j = max(cand)
                if Lc >= dl + 5:
                    ln = NET.getEdge(edges[j]).getLanes()[0]; pos = Lc - 1 if j < k else dl; k = j
                else: dl = max(5, ln.getLength() - 1)
            L = ln.getLength(); pos = min(max(pos, dl), L - 1)
            key = f'{sid}_{ln.getEdge().getID()}'
            stopdefs[key] = (ln.getID(), max(0, pos - dl), pos, S[sid][2])
            stl.append(key); k0 = k
        for n, (t, dm) in enumerate(dd['trips']):
            if dm: continue
            if (line, nm) in WSTAW:          # czas na dołożonym przystanku: proporcjonalnie do długości trasy
                i, ed, ka, kx, kb = WSTAW[(line, nm)]
                Lk = lambda a, b: sum(NET.getEdge(e).getLength() for e in ed[a:b])
                t = list(t[:i]) + [t[i - 1] + (t[i] - t[i - 1]) * Lk(ka, kx) / max(1, Lk(ka, kb))] + list(t[i:])
            t0 = t[0] * 60
            if not (OKNO[0] <= t0 <= OKNO[1]): continue
            stops = []
            for i, key in enumerate(stl):
                until = round(t[i] * 60)
                if ids[i] == 'kosr' and line in ('2', '3', '4', '5') and 0 < i < len(ids) - 1 and t[i + 1] - t[i] > 6:
                    # odjazd z Rynku: :03 (puls) albo :18 (linia 4 poza szczytem) – najpóźniejszy, który mieści się przed następnym przystankiem
                    kand = [h * 60 + m for h in range(int(t[i] // 60), int(t[i + 1] // 60) + 1) for m in (3, 18)]
                    kand = [x for x in kand if t[i] <= x <= t[i + 1] - 1]
                    until = (max(kand) if kand else ((t[i] + 11) // 60 * 60 + 3)) * 60
                stops.append((key, until))
            vehicles.append((t0 - 60, f'L{line}_{nm.split(" →")[0][:12].replace(" ", "")}_{n:02d}_{t[0]}', edges, stops, line))

with open('przystanki.add.xml', 'w') as o:
    o.write('<additional>\n')
    for key, (lane, a, b, nm) in sorted(stopdefs.items()):
        pl = f' parkingLength="{DL_ZATOKI.get(key, 120)}"' if key.split('_')[0] in WEZLY and key not in BEZ_ZATOKI else ''   # zatoka / plac: miejsce dla kilku czekających busów
        o.write(f'  <busStop id="{key}" lane="{lane}" startPos="{a:.1f}" endPos="{b:.1f}" name="{nm}" friendlyPos="true"{pl}/>\n')
    o.write('</additional>\n')
KOL = {'1': '0,112,79', '2': '31,111,214', '3': '204,138,0', '4': '212,71,58', '5': '124,58,237'}
import random, collections
LOS = random.Random(7); PLAN = {}
PRZEJAZDY = collections.defaultdict(list)
for _, vid_, _, st_, _ in sorted(vehicles):
    for i_, (k, _) in enumerate(st_):
        if k.split('_')[0] in NA_ZADANIE and 0 < i_ < len(st_) - 1: PRZEJAZDY[k.split('_')[0]].append(vid_)
WYBRANE = {s_: set(LOS.sample(v_, min(len(v_), round(NA_ZADANIE[s_])))) for s_, v_ in PRZEJAZDY.items()}
with open('busy.rou.xml', 'w') as o:
    o.write('<routes>\n  <vType id="bus" vClass="bus" length="8.5" maxSpeed="19.44" accel="1.2" decel="3.5" sigma="0.4" speedFactor="normc(1,0.05,0.9,1.1)" guiShape="bus"/>\n')
    for dep, vid, edges, stops, line in sorted(vehicles):
        o.write(f'  <vehicle id="{vid}" type="bus" depart="{dep}" line="{line}" color="{KOL.get(line, "80,80,80")}" departLane="best" departPos="0">\n')
        o.write(f'    <route edges="{" ".join(edges)}"/>\n')
        PLAN[vid] = []
        for i, (key, until) in enumerate(stops):
            sid = key.split('_')[0]; skrajny = i in (0, len(stops) - 1)
            if sid in NA_ZADANIE and not skrajny and vid not in WYBRANE[sid]:
                PLAN[vid].append((key, until, False)); continue          # nikt nie czeka i nikt nie wysiada – przejazd bez zatrzymania
            PLAN[vid].append((key, until, True))
            par = ' parking="true"' if sid in WEZLY and key not in BEZ_ZATOKI else ''
            if i == len(stops) - 1:                                   # pętla końcowa: wysiadka, bez czekania na czas z rozkładu
                o.write(f'    <stop busStop="{key}" duration="{POSTOJ}"{par}/>\n')
            elif sid in WEZLY or sid in PUNKTY_CZASOWE or i == 0:
                o.write(f'    <stop busStop="{key}" duration="{POSTOJ}" until="{until}"{par}/>\n')
            else:
                o.write(f'    <stop busStop="{key}" duration="{POSTOJ_NZ if sid in NA_ZADANIE else POSTOJ_ZWYKLY}"{par}/>\n')
        o.write('  </vehicle>\n')
    o.write('</routes>\n')
json.dump(PLAN, open('plan_kursow.json', 'w'), ensure_ascii=False)
print('przystanki', len(stopdefs), 'kursy', len(vehicles), 'zatrzymania na żądanie:',
      {k: sum(1 for p in PLAN.values() for x in p if x[0].startswith(k + '_') and x[2]) for k in NA_ZADANIE})
