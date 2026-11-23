"""Porównanie: ruch zmierzony (GPR) vs przejazdy aut w symulacji na punktach pomiarowych (cała doba 4:30–24:00)."""
import json, collections, xml.etree.ElementTree as ET
P = json.load(open('wyniki/punkty_pomiarowe.json'))
cnt = collections.Counter()
for iv in ET.parse('wyniki/natezenia.xml').getroot():
    for e in iv: cnt[e.get('id')] += float(e.get('entered', 0))
W = [.25, .2, .2, .25, .45, 1.1, 2.6, 2.4, 1.6, 1.4, 1.4, 1.5, 1.6, 1.8, 2.2, 2.4, 2.3, 1.9, 1.5, 1.2, .9, .7, .5, .35]
udz = sum(W[4:]) / sum(W)            # symulacja zaczyna się o 4:30
wyn = []
print(f'{"droga":5} {"odcinek":48} {"pomiar":>7} {"symul.":>7}')
for p in P:
    s = sum(cnt[k] for k in p['krawedzie']); m = p['sdrr'] * udz
    wyn.append({**p, 'pomiar_4_24': round(m), 'symulacja': round(s)})
    print(f'{p["droga"]:5} {p["opis"][:48]:48} {m:7.0f} {s:7.0f}')
json.dump(wyn, open('wyniki/kalibracja.json', 'w'), ensure_ascii=False, indent=1)
