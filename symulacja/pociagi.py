"""Pociągi: przelotowe kursy po liniach kolejowych od brzegu do brzegu mapy, z krótkimi postojami na stacjach.

Linie (numery wg OSM / PKP PLK) i stacje w wycinku mapy:
- 131 Magistrala Węglowa: (Herby) → Boronów → Strzebiń → (Kalety, Tarnowskie Góry)
- 143: (Ciasna) → Kochcice → Lubliniec → Rusinowice → Koszęcin → (Kalety, Tarnowskie Góry)
- 61:  Lubliniec → Kochanowice → Lisów → (Herby Stare, Częstochowa)
Mapa kończy się tuż przed Kaletami i na zachód od Lublińca, więc tam pociągi wjeżdżają / zjeżdżają z mapy.
- 152: Lubliniec → (Pyskowice) – tylko towarowe
Częstotliwości są PRZYBLIŻONE (nie rozkład PKP / KŚ / PR / IC). Pasażerskie stają na każdej stacji na 30 s,
towarowe przejeżdżają bez zatrzymania. Wynik: pociagi.rou.xml + stacje.add.xml.
"""
import os, sys, random
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
    '131': [(18.8497, 50.7557), 'Boronów', 'Strzebiń', (18.8885, 50.6007)],
    '143': [(18.6335, 50.7507), 'Kochcice-Glinica', 'Lubliniec', 'Rusinowice', 'Koszęcin', (18.8852, 50.5740)],
    '61':  ['Lubliniec', 'Kochanowice', 'Lisów', (18.9553, 50.7695)],
    '152': ['Lubliniec', (18.6269, 50.5685)],
}
# (pasażerskie na godzinę w każdą stronę, towarowe na godzinę w każdą stronę) – szacunek do czasu wgrania rozkładów
RUCH = {'131': (0.5, 1.0), '143': (1.0, 1.0), '61': (1.0, 0.5), '152': (0.0, 0.5)}

def kandydaci(lon, lat, r=400):
    """Krawędzie torów przy punkcie (oba kierunki, wszystkie tory szlaku)."""
    x, y = n.convertLonLat2XY(lon, lat)
    kand = sorted((sumolib.geomhelper.distancePointToPolygon((x, y), e.getShape()), e) for e in RAIL)
    kand = [k for k in kand if k[0] < r]
    if not kand: raise SystemExit(f'brak torów przy {lat},{lon}')
    d0 = kand[0][0]
    return [e for d, e in kand if d < d0 + 30][:8]

def trasa(punkty):
    """Najkrótszy przejazd przez kolejne punkty (programowanie dynamiczne po kandydatach) – bez zawracania."""
    C = [kandydaci(*(STACJE[p] if isinstance(p, str) else p)) for p in punkty]
    best = {e: (0.0, [e]) for e in C[0]}
    for warstwa in C[1:]:
        nowe = {}
        for b in warstwa:
            opcje = []
            for a, (koszt, sciezka) in best.items():
                if a == b: opcje.append((koszt, sciezka)); continue
                p, c = n.getShortestPath(a, b, vClass='rail')
                if p: opcje.append((koszt + c, sciezka + list(p[1:])))
            if opcje: nowe[b] = min(opcje, key=lambda o: o[0])
        if not nowe: raise SystemExit('brak przejazdu po torach')
        best = nowe
    koszt, ed = min(best.values(), key=lambda o: o[0])
    kr = []
    for warstwa in C:
        kr.append(next((e for e in ed if e in warstwa), warstwa[0]))
    return ed, kr

def odwrotna(punkty): return list(reversed(punkty))

stacje_def = {}; v = []
for linia, pkt in LINIE.items():
    pas, tow = RUCH[linia]
    for kier, pk in (('a', pkt), ('b', odwrotna(pkt))):
        ed, kr = trasa(pk)
        ids = [e.getID() for e in ed]
        postoje = []
        for p, e in zip(pk, kr):
            if not isinstance(p, str) or e.getID() not in ids: continue
            # peron: krawędź z trasy najbliższa stacji
            x, y = n.convertLonLat2XY(*STACJE[p])
            e2 = min(ed, key=lambda q: sumolib.geomhelper.distancePointToPolygon((x, y), q.getShape()))
            ln = e2.getLanes()[0]; pos, _ = sumolib.geomhelper.polygonOffsetAndDistanceToPoint((x, y), ln.getShape())
            L = ln.getLength(); a = max(0, min(pos - 40, L - 81)); b = min(L, a + 80)
            sid = f'st_{p}_{e2.getID()}'.replace(' ', '')
            stacje_def[sid] = (ln.getID(), a, b, p); postoje.append(sid)
        for typ, na_godz, off0 in (('pociag', pas, 7), ('towarowy', tow, 31)):
            if not na_godz: continue
            co = int(3600 / na_godz); off = random.randrange(0, co, 60)
            for i, t in enumerate(range(4 * 3600 + off, 23 * 3600, co)):
                v.append((t, f'poc{linia}{kier}_{typ[0]}{i:02d}', ids, typ, postoje if typ == 'pociag' else []))
        print(f'linia {linia}{kier}: {len(ids)} odcinków, {sum(e.getLength() for e in ed)/1000:.1f} km, stacje: {", ".join(p for p in pk if isinstance(p, str))}')

with open('stacje.add.xml', 'w') as o:
    o.write('<additional>\n')
    for sid, (ln, a, b, nm) in sorted(stacje_def.items()):
        o.write(f'  <trainStop id="{sid}" lane="{ln}" startPos="{a:.1f}" endPos="{b:.1f}" name="{nm}" friendlyPos="true"/>\n')
    o.write('</additional>\n')
with open('pociagi.rou.xml', 'w') as o:
    o.write('<routes>\n  <vType id="pociag" vClass="rail" length="75" maxSpeed="33" accel="0.6" decel="0.9" guiShape="rail" color="80,80,80"/>\n')
    o.write('  <vType id="towarowy" vClass="rail" length="600" maxSpeed="16.7" accel="0.25" decel="0.5" guiShape="rail/cargo" color="40,40,40"/>\n')
    for dep, vid, ed, typ, st in sorted(v):
        o.write(f'  <vehicle id="{vid}" type="{typ}" depart="{dep}" departLane="best"><route edges="{" ".join(ed)}"/>')
        o.write(''.join(f'<stop trainStop="{s}" duration="30"/>' for s in st) + '</vehicle>\n')
    o.write('</routes>\n')
print('pociągów:', len(v), '| stacji:', len(stacje_def))
