"""Wycinek rozkładu kolejowego (GTFS) dla stacji w gminie Koszęcin i okolicy → dane/kolej/pociagi.json.

Uruchamia go akcja GitHub (.github/workflows/kolej.yml), bo pobranie GTFS wymaga dostępu do sieci.
Dla wybranych dni (roboczy, sobota, niedziela – z pliku dane/kolej/DNI) zapisuje pociągi, które stają
na co najmniej dwóch stacjach z listy, z godzinami przyjazdu i odjazdu na tych stacjach.
Uruchom: python3 skrypty/gtfs_wycinek.py plik.zip RRRRMMDD RRRRMMDD RRRRMMDD
"""
import csv, io, json, sys, zipfile, datetime as dt

ZIP = sys.argv[1]
DNI = {'wd': sys.argv[2], 'sat': sys.argv[3], 'sun': sys.argv[4]}
STACJE = ['Lubliniec', 'Kochanowice', 'Lisów', 'Rusinowice', 'Koszęcin', 'Strzebiń', 'Boronów', 'Kalety']
# stacje docelowe dalej od gminy: dla pociągów z wycinka zapisujemy też godziny na nich (pole 'cele')
CELE = ['Częstochowa', 'Częstochowa Stradom', 'Herby Nowe', 'Tarnowskie Góry', 'Katowice', 'Opole Główne', 'Kłobuck', 'Bytom']
z = zipfile.ZipFile(ZIP)

def rd(n):
    if n not in z.namelist(): return []
    return list(csv.DictReader(io.TextIOWrapper(z.open(n), 'utf-8-sig')))

stops = rd('stops.txt')
idn = {s['stop_id']: s['stop_name'].strip() for s in stops if s['stop_name'].strip() in STACJE}
idc = {s['stop_id']: s['stop_name'].strip() for s in stops if s['stop_name'].strip() in CELE}
for s in stops:   # perony / tory z polem parent_station
    if s.get('parent_station') in idn: idn[s['stop_id']] = idn[s['parent_station']]
    if s.get('parent_station') in idc: idc[s['stop_id']] = idc[s['parent_station']]
print('cele:', sorted(set(idc.values())))
print('stacje:', sorted(set(idn.values())), len(idn), 'id')

cal = {r['service_id']: r for r in rd('calendar.txt')}
ex = {}
for r in rd('calendar_dates.txt'): ex.setdefault(r['service_id'], {})[r['date']] = r['exception_type']
daty = sorted([r['start_date'] for r in cal.values()] + [r['end_date'] for r in cal.values()] + [d for v in ex.values() for d in v])
print('zakres dat w GTFS:', daty[0] if daty else '-', '…', daty[-1] if daty else '-')
DNI_TYG = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

def aktywny(sid, d):
    e = ex.get(sid, {}).get(d)
    if e == '1': return True
    if e == '2': return False
    c = cal.get(sid)
    if not c or not (c['start_date'] <= d <= c['end_date']): return False
    return c[DNI_TYG[dt.date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday()]] == '1'

routes = {r['route_id']: r for r in rd('routes.txt')}
agency = {r['agency_id']: r['agency_name'] for r in rd('agency.txt')}
trips = {t['trip_id']: t for t in rd('trips.txt')}
st = {}; sc = {}
for r in rd('stop_times.txt'):
    if r['stop_id'] in idc: sc.setdefault(r['trip_id'], []).append(r)
    if r['stop_id'] in idn and not (r.get('pickup_type', '0') == '1' and r.get('drop_off_type', '0') == '1'):
        st.setdefault(r['trip_id'], []).append(r)

def mn(t):
    h, m, *_ = map(int, t.split(':')); return h * 60 + m

out = {'zrodlo': 'GTFS polish_trains (mkuran.pl), dane PKP PLK', 'pobrano': dt.date.today().isoformat(), 'dni': DNI, 'pociagi': {}}
for tid, rows in st.items():
    rows.sort(key=lambda r: int(r['stop_sequence']))
    if len(rows) < 2: continue
    t = trips[tid]; ro = routes.get(t['route_id'], {})
    for k, d in DNI.items():
        if not aktywny(t['service_id'], d): continue
        out['pociagi'].setdefault(k, []).append({
            'nr': t.get('trip_short_name', ''), 'kier': t.get('trip_headsign', ''),
            'przewoznik': agency.get(ro.get('agency_id', ''), ro.get('agency_id', '')),
            'linia': ro.get('route_short_name', '') or ro.get('route_long_name', ''),
            'p': [[idn[r['stop_id']], mn(r['arrival_time']), mn(r['departure_time'])] for r in rows],
            'cele': [[idc[r['stop_id']], mn(r['arrival_time']), mn(r['departure_time'])] for r in sorted(sc.get(tid, []), key=lambda r: int(r['stop_sequence']))]})
for k in DNI:
    v = out['pociagi'].get(k, [])
    v.sort(key=lambda x: x['p'][0][2])
    print(k, DNI[k], len(v), 'pociągów')
json.dump(out, open('dane/kolej/pociagi.json', 'w'), ensure_ascii=False, indent=0)
