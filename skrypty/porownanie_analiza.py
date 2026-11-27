"""Rzetelne porównanie: dzisiejsze kursy GTV przez gminę Koszęcin a proponowana siatka busów.

Dziś:       dane/gtv_dzis/kursy_<data>.txt (gtvbus.kiedyprzyjedzie.pl), typy dni:
            2026-11-30 dzień roboczy z lekcjami, 2026-12-28 dzień roboczy bez lekcji, 2026-12-05 sobota, 2026-12-06 niedziela.
Propozycja: out/rozklad_data.json (wd / sat / sun; kursy na zamówienie liczone osobno).
Pociągi:    dane/kolej/pociagi.json (rozkład 2026/27).
Wyjście:    out/porownanie.json + tabele na ekranie.

Miary dla każdej miejscowości (odjazdy z przystanków w tej miejscowości, każdy kurs liczony raz):
  kursy – liczba kursów zatrzymujących się w miejscowości (oba kierunki razem),
  doK/zK – kursy do centrum Koszęcina / z centrum Koszęcina (Rynek, Ligonia, Szkoła, Lubliniecka),
  doL/zL – kursy do Lublińca / z Lublińca (bez przesiadki),
  pierwszy/ostatni – pierwszy i ostatni odjazd z miejscowości, ostZK/ostZL – ostatni powrót z Koszęcina / z Lublińca,
  przerwa – najdłuższa przerwa między odjazdami z miejscowości w godz. 6:00–20:00 (min),
  godziny – w ilu godzinach z 6–19 jest choć jeden odjazd (na 14).
Przesiadki na pociąg (stacje w promieniu 400 m od przystanku): pociąg z dowozem = bus na stacji 3–20 min przed odjazdem
pociągu; pociąg z odwozem = bus odjeżdża ze stacji 3–20 min po przyjeździe pociągu.
"""
import json, math, re, collections, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = lambda *a: os.path.join(ROOT, *a)

# --- przystanki i współrzędne ---
GST = {}
for l in open(P('dane/gtv_dzis/przystanki.csv'), encoding='utf-8'):
    if l.strip():
        d, nm, lon, lat = l.strip().split(';'); GST[d] = (nm, float(lat), float(lon))
src = open(P('skrypty/build.py')).read()
PST = {m.group(3): (float(m.group(1)), float(m.group(2))) for m in re.finditer(r"'\w+':\(([\d.]+),([\d.]+),'([^']+)'", src)}

def wies(n):
    if 'Bukowiec' in n: return 'Bukowiec'
    if 'Prądy' in n: return 'Prądy'
    if 'Irki' in n: return 'Irki'
    if n.startswith('Rzyce'): return 'Rzyce'
    if n.startswith('Płaszczymąka'): return 'Psary'
    if n.startswith('Stary Strzebiń'): return 'Strzebiń'
    w = n.split(',')[0].split(' ')[0]
    return w if w in WSIE else None
WSIE = ['Strzebiń', 'Prądy', 'Łazy', 'Bukowiec', 'Piasek', 'Psary', 'Koszęcin', 'Irki', 'Rzyce', 'Wierzbie', 'Sadów',
        'Rusinowice', 'Piłka', 'Cieszowa', 'Brusiek', 'Boronów', 'Kalety', 'Lisów', 'Chwostek', 'Hadra', 'Mochała', 'Lubliniec']
def centrum(n): return n.startswith('Koszęcin') and not any(x in n for x in ('PKP', 'Trójca', 'Dworcowa', 'Kolejowa', 'Krokusowa'))
STACJE = {'Koszęcin': (50.6228, 18.8370), 'Strzebiń': (50.6150, 18.9007), 'Rusinowice': (50.6494, 18.7637), 'Boronów': (50.6654, 18.9014),
          'Kalety': (50.5642, 18.8860), 'Lisów': (50.7211, 18.7922), 'Lubliniec': (50.6726, 18.6910)}
def km(a, b): return math.hypot((a[0] - b[0]) * 111.2, (a[1] - b[1]) * 111.2 * math.cos(math.radians(50.64)))
def stacja(lat, lon):
    for s, c in STACJE.items():
        if km((lat, lon), c) < 0.4: return s
    return None

# --- kursy: lista [(nazwa, lat, lon, minuta)] ---
PRZELOTOWE = ('44039', '37618', '53107', '38036')   # kursy jadące dalej poza gminę: Lubliniec – Boronów – Jamki (dalej Częstochowa), Lubliniec – Strzebiń – Piasek – Kalety/Tarnowskie Góry, sobotnie Woźniki/Kalety
def gtv(data, tylko=None):
    out = []
    f = P(f'dane/gtv_dzis/kursy_{data}.txt')
    for l in open(f):
        if not l.strip(): continue
        tid, r = l.strip().split(':')
        prz = tid[:5] in PRZELOTOWE
        if tylko == 'gminne' and prz or tylko == 'przelotowe' and not prz: continue
        out.append([(GST[d][0], GST[d][1], GST[d][2], int(m)) for d, m in (x.split('.') for x in r.split(','))])
    return out
R = json.load(open(P('out/rozklad_data.json')))['tt']
def prop(dz, zam=False):
    out = []
    for ln, days in R.items():
        for nm, dd in days[dz].items():
            for t, z in dd['trips']:
                if bool(z) != zam: continue
                out.append([(s, *PST[s.split(' (')[0]], m) for s, m in zip(dd['stops'], t)])
    return out
POC = json.load(open(P('dane/kolej/pociagi.json')))['pociagi']

def miary(kursy):
    W = collections.defaultdict(lambda: dict(kursy=0, doK=0, zK=0, doL=0, zL=0, odj=[], zKt=[], zLt=[]))
    for k in kursy:
        ik = [i for i, x in enumerate(k) if centrum(x[0])]
        il = [i for i, x in enumerate(k) if x[0].startswith('Lubliniec')]
        byl = set()
        for i, (n, lat, lon, m) in enumerate(k):
            w = wies(n)
            if not w or w in byl: continue
            byl.add(w); M = W[w]; M['kursy'] += 1
            if i < len(k) - 1: M['odj'].append(m)
            if w != 'Koszęcin':
                if any(j > i for j in ik): M['doK'] += 1
                pk = [j for j in ik if j < i]
                if pk: M['zK'] += 1; M['zKt'].append(k[pk[-1]][3])
            if w != 'Lubliniec':
                if any(j > i for j in il): M['doL'] += 1
                pl = [j for j in il if j < i]
                if pl: M['zL'] += 1; M['zLt'].append(k[pl[-1]][3])
    out = {}
    for w, M in W.items():
        o = sorted(M['odj']); g = [6 * 60] + [x for x in o if 360 <= x <= 1200] + [1200]
        out[w] = dict(kursy=M['kursy'], doK=M['doK'], zK=M['zK'], doL=M['doL'], zL=M['zL'],
                      pierwszy=o[0] if o else None, ostatni=o[-1] if o else None,
                      ostZK=max(M['zKt']) if M['zKt'] else None, ostZL=max(M['zLt']) if M['zLt'] else None,
                      przerwa=max(b - a for a, b in zip(g, g[1:])), godziny=len({x // 60 for x in o if 6 * 60 <= x < 20 * 60}))
    return out

def przesiadki(kursy, dz):
    wizyty = collections.defaultdict(list)       # stacja → minuty, kiedy bus jest na przystanku przy stacji
    for k in kursy:
        for n, lat, lon, m in k:
            s = stacja(lat, lon)
            if s: wizyty[s].append(m)
    wyn = {}
    for s in STACJE:
        odj = sorted({q[2] for x in POC[dz] for q in x['p'] if q[0] == s})
        prz = sorted({q[1] for x in POC[dz] for q in x['p'] if q[0] == s})
        v = sorted(wizyty.get(s, []))
        dow = sum(1 for t in odj if any(3 <= t - b <= 20 for b in v))
        odw = sum(1 for t in prz if any(3 <= b - t <= 20 for b in v))
        wyn[s] = dict(pociagi_odj=len(odj), z_dowozem=dow, pociagi_prz=len(prz), z_odwozem=odw)
    return wyn

def wkm(kursy):   # przybliżona długość kursów w linii prostej między przystankami (do porównania, nie do kosztów)
    return round(sum(km(a[1:3], b[1:3]) for k in kursy for a, b in zip(k, k[1:])))

DNI = [('robocze_lekcje', '2026-11-30', 'wd'), ('robocze_bez_lekcji', '2026-12-28', 'wd'), ('sobota', '2026-12-05', 'sat'), ('niedziela', '2026-12-06', 'sun')]
WYN = {}
for nazwa, data, dz in DNI:
    A = gtv(data); B = prop(dz); Bz = prop(dz, True); Ag = gtv(data, 'gminne'); Ap = gtv(data, 'przelotowe')
    BP = B + Ap
    WYN[nazwa] = dict(dzis=dict(n=len(A), km=wkm(A), wsie=miary(A), poc=przesiadki(A, dz),
                                godz=collections.Counter(k[0][3] // 60 for k in A)),
                      dzis_gminne=dict(n=len(Ag), km=wkm(Ag)), dzis_przelotowe=dict(n=len(Ap), km=wkm(Ap)),
                      prop_plus_przel=dict(n=len(BP), km=wkm(BP), wsie=miary(BP), poc=przesiadki(BP, dz),
                                godz=collections.Counter(k[0][3] // 60 for k in BP)),
                      prop=dict(n=len(B), n_zam=len(Bz), km=wkm(B), km_zam=wkm(Bz), wsie=miary(B), wsie_zam=miary(Bz),
                                poc=przesiadki(B, dz), godz=collections.Counter(k[0][3] // 60 for k in B)))
json.dump(WYN, open(P('out/porownanie.json'), 'w'), ensure_ascii=False, indent=1)

hm = lambda m: f'{m // 60}:{m % 60:02d}' if m is not None else '–'
for nazwa, _, _ in DNI:
    D = WYN[nazwa]; A, B = D['dzis'], D['prop']
    print(f"\n=== {nazwa}: dziś gminne {D['dzis_gminne']['n']} ({D['dzis_gminne']['km']} km) + przelotowe {D['dzis_przelotowe']['n']} ({D['dzis_przelotowe']['km']} km)")
    for B in (D['prop'], D['prop_plus_przel']):
      print(f"\n=== {nazwa}: kursy dziś {A['n']} / propozycja {B['n']} (+{B.get('n_zam', '–')} na zamówienie); km (linia prosta) {A['km']} / {B['km']}")
      print(f"{'':11}{'kursy':>9}{'doK':>8}{'zK':>8}{'doL':>8}{'zL':>8}{'pierwszy':>13}{'ostatni':>13}{'ost.zK':>13}{'ost.zL':>13}{'przerwa':>11}{'godz':>8}")
      for w in WSIE:
          a = A['wsie'].get(w, {}); b = B['wsie'].get(w, {})
          if not a and not b: continue
          f = lambda k, h=False: f"{(hm(a.get(k)) if h else a.get(k, 0))}/{(hm(b.get(k)) if h else b.get(k, 0))}"
          print(f"{w:11}{f('kursy'):>9}{f('doK'):>8}{f('zK'):>8}{f('doL'):>8}{f('zL'):>8}{f('pierwszy', 1):>13}{f('ostatni', 1):>13}{f('ostZK', 1):>13}{f('ostZL', 1):>13}{f('przerwa'):>11}{f('godziny'):>8}")
      print('pociągi z dowozem / odwozem (dziś → propozycja):',
            {s: f"{A['poc'][s]['z_dowozem']}→{B['poc'][s]['z_dowozem']} / {A['poc'][s]['z_odwozem']}→{B['poc'][s]['z_odwozem']} (z {A['poc'][s]['pociagi_odj']})" for s in STACJE})
