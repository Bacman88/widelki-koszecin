"""Przykładowy rozkład okolicznościowy na imprezę na Rynku w Koszęcinie (Święto Śląska 2027).

Zasada: w dniu imprezy obowiązuje zwykły rozkład weekendowy, kursy na zamówienie (linie 3, 4, 5) jadą bez zamawiania,
a brakujące dojazdy na Rynek i wieczorne powroty z Rynku są dodane jako kursy dodatkowe (te same przystanki i czasy
przejazdu co w zwykłym rozkładzie). Wynik: strona HTML (ścieżka w argumencie, domyślnie out/imprezy.html).
Uruchom z katalogu repozytorium: python3 skrypty/imprezy.py [plik.html]
"""
import json, sys, html

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out/imprezy.html'
D = json.load(open('out/rozklad_data.json'))
TT = D['tt']; STAT = D['var']['pelny'][0]
RYN = 'Koszęcin Rynek'
KOL = {'1': '#00704f', '2': '#1f6fd1', '3': '#c98a00', '4': '#d4473a', '5': '#7c3aed'}
LINIA = {'1': 'Piasek – Strzebiń – Koszęcin – Sadów – Lubliniec', '2': 'Boronów – Koszęcin – Brusiek – Kalety',
         '3': 'Lisów – Cieszowa – Koszęcin', '4': 'Łazy – Strzebiń – Koszęcin', '5': 'Koszęcin – Wierzbie – Rusinowice – Piłka – Sadów – Lubliniec'}
# dzień imprezy: (klucz rozkładu, nazwa, okna dojazdu (od, do – przyjazd na Rynek), cel dodatkowego dojazdu, powroty z Rynku)
DNI = [('sat', 'Sobota 26 czerwca 2027', [(11 * 60, 13 * 60 + 30), (17 * 60, 19 * 60)], [11 * 60 + 49, 17 * 60 + 49], [21 * 60 + 15, 23 * 60 + 15]),
       ('sun', 'Niedziela 27 czerwca 2027', [(11 * 60, 13 * 60 + 30), (17 * 60, 19 * 60)], [11 * 60 + 49, 17 * 60 + 49], [21 * 60 + 15])]
KM_ZL = (4, 5, 6)   # zł za wozokilometr – warianty kosztu


def hm(m): return f'{m // 60}:{m % 60:02d}'


def km_na_min(l):
    """Średnia liczba km na minutę jazdy linii (z dnia roboczego: km / suma czasu kursów)."""
    mins = 0
    for x in TT[l]['wd'].values():
        for t, _ in x['trips']:
            v = [a for a in t if a is not None]
            mins += v[-1] - v[0]
    return STAT[l]['wd']['km'] / mins


def kierunki(l, dz):
    """(do Rynku: [(nazwa, stops, trips)], z Rynku: [...]) – odcinki tras od/do Rynku."""
    do, od = [], []
    for nazwa, x in TT[l][dz].items():
        st = x['stops']
        if RYN not in st: continue
        i = st.index(RYN)
        if i > 0: do.append((nazwa.split(' → ')[0], st[:i + 1], [(t[:i + 1], z) for t, z in x['trips']]))
        if i < len(st) - 1: od.append((nazwa.split(' → ')[1], st[i:], [(t[i:], z) for t, z in x['trips']]))
    return do, od


def wzor(trips):
    """Względne czasy przejazdu z pierwszego pełnego kursu."""
    for t, _ in trips:
        if all(a is not None for a in t): return [a - t[0] for a in t]
    t = trips[0][0]; b = next(a for a in t if a is not None)
    return [None if a is None else a - b for a in t]


def tabela(stops, kursy):
    """kursy: [(czasy, etykieta)] → HTML tabela: wiersze = przystanki, kolumny = kursy."""
    h = ['<div class="scroll"><table><tr><th>Przystanek</th>' + ''.join(f'<th>{html.escape(e)}</th>' for _, e in kursy) + '</tr>']
    for i, s in enumerate(stops):
        h.append('<tr><td>' + html.escape(s) + '</td>' + ''.join(f'<td>{hm(c[i]) if c[i] is not None else "–"}</td>' for c, _ in kursy) + '</tr>')
    return ''.join(h) + '</table></div>'


sekcje, km_dod, liczby = [], 0.0, {'dod': 0, 'zam': 0}
for dz, nazwa_dnia, okna, cele, powroty in DNI:
    s = [f'<h2>{nazwa_dnia}</h2>']
    for l in ('1', '2', '3', '4', '5'):
        kpm = km_na_min(l)
        do, od = kierunki(l, dz)
        s.append(f'<h3><span class="bd" style="background:{KOL[l]}">{l}</span> {html.escape(LINIA[l])}</h3>')
        for skad, stops, trips in do:
            kursy = []
            for (a, b), cel in zip(okna, cele):
                w = [(t, z) for t, z in trips if t[-1] is not None and a <= t[-1] <= b]
                if w:
                    for t, z in w:
                        kursy.append((t, 'bez zamawiania' if z else 'zwykły kurs'))
                        liczby['zam'] += z
                else:
                    wz = wzor(trips); t = [None if x is None else cel - wz[-1] + x for x in wz]
                    kursy.append((t, 'dodatkowy')); liczby['dod'] += 1
                    km_dod += 2 * (wz[-1] - wz[0]) * kpm      # kurs + dojazd busa na początek trasy
            kursy.sort(key=lambda k: k[0][-1])
            s.append(f'<p class="op">Na Rynek z kierunku: <b>{html.escape(skad)}</b></p>' + tabela(stops, kursy))
        for dokad, stops, trips in od:
            wz = wzor(trips); kursy = []
            for p in powroty:
                kursy.append(([None if x is None else p + x for x in wz], 'powrót')); liczby['dod'] += 1
                km_dod += 2 * (wz[-1] - wz[0]) * kpm          # kurs + zjazd busa z powrotem
            s.append(f'<p class="op">Powrót z Rynku w kierunku: <b>{html.escape(dokad)}</b></p>' + tabela(stops, kursy))
    sekcje.append(''.join(s))

koszt = ' – '.join(f'{round(km_dod * z, -2):,.0f}'.replace(',', ' ') + ' zł' for z in (KM_ZL[0], KM_ZL[2]))
podsum = (f'<div class="grid"><div class="card"><div class="big">{liczby["dod"]}</div>kursów dodatkowych (dojazdy, których brakuje w zwykłym rozkładzie, i wieczorne powroty) w dwa dni imprezy</div>'
          f'<div class="card"><div class="big">ok. {round(km_dod, -1):.0f} km</div>dodatkowo, razem z dojazdami busów na początek trasy i zjazdami po ostatnim kursie</div>'
          f'<div class="card"><div class="big">{koszt}</div>szacunkowy koszt dodatkowych kursów (przy {KM_ZL[0]}–{KM_ZL[2]} zł za km). Kursy na zamówienie, które tego dnia jadą bez zamawiania, są już w rocznym planie kilometrów siatki.</div></div>')

strona = f'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<title>Busami na Święto Śląska – przykładowy rozkład okolicznościowy (propozycja)</title>
<meta name="description" content="Przykładowy rozkład busów na Święto Śląska w Koszęcinie: dojazdy z całej gminy i wieczorne powroty z Rynku. Propozycja mieszkańców – nie obowiązujący rozkład.">
<link rel="canonical" href="https://busy-koszecin.smart-ant.pl/imprezy/">
<style>
:root{{--ink:#10201c;--mut:#5d665f;--paper:#f7f4ec;--rule:#e2ddd0;--g:#00704f;--warn:#b3261e}}
*{{box-sizing:border-box}}
body{{margin:0;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--paper)}}
.bar{{position:sticky;top:0;z-index:1000;background:var(--warn);color:#fff;text-align:center;font-weight:700;font-size:14px;padding:8px 12px}}.bar a{{color:#fff}}
main{{max-width:1100px;margin:0 auto;padding:22px 18px 60px}}
h1{{font-size:30px;line-height:1.15;margin:6px 0}}
.lead{{margin:0 0 14px;max-width:860px}}
h2{{font-size:24px;margin:34px 0 4px;border-top:2px solid var(--ink);padding-top:14px}}
h3{{font-size:18px;margin:22px 0 4px;display:flex;gap:8px;align-items:center}}
.bd{{display:inline-grid;place-items:center;min-width:1.8em;height:1.5em;border-radius:6px;color:#fff;font-size:14px;font-weight:800}}
.op{{color:var(--mut);font-size:14px;margin:10px 0 4px}}
.scroll{{overflow-x:auto;background:#fff;border:1px solid var(--rule);border-radius:12px}}
table{{border-collapse:collapse;font-size:14px;white-space:nowrap}}
th,td{{padding:5px 10px;border-bottom:1px solid #eee9dc;text-align:center}}
th{{font-size:12px;color:var(--mut);font-weight:600}}
th:first-child,td:first-child{{position:sticky;left:0;background:#fff;text-align:left;font-weight:600;border-right:1px solid var(--rule)}}
tr:last-child td{{border-bottom:0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:16px 0}}
.card{{background:#fff;border:1px solid var(--rule);border-radius:12px;padding:16px}}
.card .big{{font-size:26px;font-weight:700;color:var(--g)}}
.free{{background:#eef5d8;border:1px solid #cfe0a4;border-radius:12px;padding:12px 16px;font-weight:600}}
.note{{font-size:13px;color:var(--mut);margin-top:24px;max-width:860px}}
a{{color:var(--g)}}
</style></head><body>
<div class="bar">⚠️ Propozycja mieszkańców – to nie jest obowiązujący rozkład jazdy · <a href="../">strona główna</a></div>
<main>
<h1>Busami na Święto Śląska</h1>
<p class="lead">Przykład, jak siatka busów może obsłużyć dużą imprezę w Koszęcinie. Wzorem jest tegoroczne Święto Śląska (27–28 czerwca 2026, siedziba Zespołu „Śląsk”, ul. Zamkowa 3, kilka minut pieszo od Rynku). Termin na 2027 rok nie jest jeszcze ogłoszony, więc przyjęto pierwszy weekend wakacji, 26–27 czerwca 2027, a godziny powrotów dobrano do zeszłorocznego programu: koncert Zespołu „Śląsk” o 19:00 i nocne zwiedzanie pałacu do 23:00.</p>
<p class="free">W dni imprezy przejazdy wszystkimi liniami są bezpłatne dla wszystkich.</p>
<p class="lead">Jak to działa: obowiązuje zwykły rozkład weekendowy, ale kursy na zamówienie linii 3, 4 i 5 jadą bez zamawiania. Tam, gdzie zwykły rozkład nie dowozi na Rynek przed 13:30 albo przed 19:00, jest kurs dodatkowy. Wieczorem wszystkie linie odjeżdżają z Rynku razem o 21:15, a w sobotę także o 23:15, po nocnym zwiedzaniu, do każdej miejscowości w gminie oraz do Lublińca, Kalet i Lisowa.</p>
{podsum}
{''.join(sekcje)}
<p class="note">Rozkład przykładowy, ułożony według <a href="../rozklad/">proponowanego rozkładu weekendowego</a>. Ten sam schemat, czyli wspólny wieczorny odjazd wszystkich linii z Rynku, pasuje do innych imprez: Międzynarodowego Festiwalu Folklorystycznego „Silesia” (w 2027 r. 19–25 lipca), dożynek i festynów. Koszt kursów dodatkowych można dzielić z organizatorem imprezy albo sponsorem. Liczba kilometrów jest szacunkowa (średnia prędkość linii z rozkładu dnia roboczego).</p>
</main></body></html>'''
open(OUT, 'w').write(strona)
print(OUT, liczby, f'{km_dod:.0f} km', koszt)
