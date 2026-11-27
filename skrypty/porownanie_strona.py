"""Podstrona „Dziś i w propozycji”: obecne kursy GTV przez gminę Koszęcin obok proponowanej siatki.

Wejście: dane/gtv_dzis/{przystanki.csv,kursy.txt} (gtvbus.kiedyprzyjedzie.pl, dzień roboczy z lekcjami 30.11.2026),
         out/rozklad_data.json (propozycja), strona/imprezy/index.html (styl i wspólne elementy strony).
Wyjście: strona/porownanie/index.html
Liczone są kursy dnia roboczego (bez kursów na zamówienie w propozycji).
"""
import json, re, collections, os, html
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
P = lambda *a: os.path.join(ROOT, *a)
S = {l.split(';')[0]: l.split(';')[1] for l in open(P('dane/gtv_dzis/przystanki.csv'), encoding='utf-8') if l.strip()}
GTV = []
for l in open(P('dane/gtv_dzis/kursy.txt')):
    tid, r = l.strip().split(':'); GTV.append([(S[d], int(m)) for d, m in (x.split('.') for x in r.split(','))])
R = json.load(open(P('out/rozklad_data.json')))['tt']
PROP = []
for ln, days in R.items():
    for nm, dd in days['wd'].items():
        for t, zam in dd['trips']:
            if not zam: PROP.append([(s, m) for s, m in zip(dd['stops'], t)])

WSIE = ['Strzebiń', 'Prądy', 'Łazy', 'Bukowiec', 'Piasek', 'Psary', 'Sadów', 'Wierzbie', 'Rzyce', 'Rusinowice', 'Piłka',
        'Cieszowa', 'Brusiek', 'Boronów', 'Kalety', 'Lubliniec']
def wies(n):
    for w in ('Bukowiec', 'Prądy'):
        if w in n: return w
    for w in WSIE:
        if n.startswith(w): return w
    return None
def koszecin(n):   # centrum Koszęcina (bez stacji i Św. Trójcy)
    return n.startswith('Koszęcin') and not any(x in n for x in ('PKP', 'Trójca', 'Dworcowa', 'Kolejowa', 'Krokusowa'))

def statystyki(kursy):
    do, z, ost_do, ost_z, pierw_do = collections.Counter(), collections.Counter(), {}, {}, {}
    godz = collections.Counter()
    for k in kursy:
        godz[int(k[0][1] // 60)] += 1
        ik = [i for i, (s, _) in enumerate(k) if koszecin(s)]
        if not ik: continue
        s_do, s_z = set(), set()
        for i, (s, m) in enumerate(k):
            w = wies(s)
            if not w: continue
            nast = [j for j in ik if j > i]; pop = [j for j in ik if j < i]
            if nast and w not in s_do:
                s_do.add(w); do[w] += 1; t = k[nast[0]][1]
                ost_do[w] = max(ost_do.get(w, 0), t); pierw_do[w] = min(pierw_do.get(w, 9999), t)
            if pop and w not in s_z:
                s_z.add(w); z[w] += 1; ost_z[w] = max(ost_z.get(w, 0), k[pop[-1]][1])
    return dict(do=do, z=z, ost_z=ost_z, pierw_do=pierw_do, godz=godz, n=len(kursy),
                po19=sum(1 for k in kursy if k[0][1] >= 19 * 60), ostatni=max(k[0][1] for k in kursy))
A, B = statystyki(GTV), statystyki(PROP)
hm = lambda m: f'{int(m) // 60}:{int(m) % 60:02d}' if m else '–'

# --- wykres kursów wg godzin (SVG) ---
H0, H1 = 5, 23
mx = max(max(A['godz'].values()), max(B['godz'].values()))
W, Hh, L, BOT = 760, 240, 34, 30
bw = (W - L - 10) / (H1 - H0)
svg = [f'<svg viewBox="0 0 {W} {Hh}" role="img" aria-label="Kursy w każdej godzinie: dziś i w propozycji" style="width:100%;height:auto;max-width:{W}px">']
for v in range(0, mx + 1, 2):
    y = Hh - BOT - v / mx * (Hh - BOT - 14)
    svg.append(f'<line x1="{L}" x2="{W - 10}" y1="{y:.1f}" y2="{y:.1f}" stroke="#ece7da"/><text x="{L - 6}" y="{y + 4:.1f}" font-size="11" text-anchor="end" fill="#5d665f">{v}</text>')
for i, h in enumerate(range(H0, H1)):
    x = L + i * bw
    for j, (st, c) in enumerate(((A, '#4B5563'), (B, '#00704F'))):
        v = st['godz'].get(h, 0); hh = v / mx * (Hh - BOT - 14)
        svg.append(f'<rect x="{x + 3 + j * (bw - 6) / 2:.1f}" y="{Hh - BOT - hh:.1f}" width="{(bw - 6) / 2 - 1:.1f}" height="{hh:.1f}" rx="2" fill="{c}"><title>{h}:00 – {"dziś" if j == 0 else "propozycja"}: {v}</title></rect>')
    svg.append(f'<text x="{x + bw / 2:.1f}" y="{Hh - BOT + 16}" font-size="11" text-anchor="middle" fill="#5d665f">{h}</text>')
svg.append('</svg>')

wiersze = []
for w in WSIE:
    a_do, b_do = A['do'].get(w, 0), B['do'].get(w, 0)
    if not (a_do or b_do): continue
    wiersze.append(f'<tr><td>{w}</td><td>{a_do}</td><td class="p">{b_do}</td><td>{A["z"].get(w, 0)}</td><td class="p">{B["z"].get(w, 0)}</td>'
                   f'<td>{hm(A["ost_z"].get(w))}</td><td class="p">{hm(B["ost_z"].get(w))}</td></tr>')

szablon = open(P('strona/imprezy/index.html'), encoding='utf-8').read()
glowa = szablon[:szablon.index('</head>')]
glowa = re.sub(r'<title>.*?</title>', '<title>Dziś i w propozycji – porównanie kursów busów w gminie Koszęcin</title>', glowa, flags=re.S)
glowa = re.sub(r'<meta name="description" content="[^"]*"', '<meta name="description" content="Ten sam dzień, dwa rozkłady: obecne kursy GTV przez gminę Koszęcin obok proponowanej siatki busów – liczby, wykres i film z symulacji."', glowa)
glowa = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\1Dziś i w propozycji – busy w gminie Koszęcin', glowa)
glowa = re.sub(r'(<meta property="og:url" content=")[^"]*', r'\1https://busy-koszecin.smart-ant.pl/porownanie/', glowa)
glowa = re.sub(r'(<link rel="canonical" href=")[^"]*', r'\1https://busy-koszecin.smart-ant.pl/porownanie/', glowa)
glowa = glowa.replace('og-siatka.png', 'og-porownanie.png')
glowa = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\1Ten sam dzień, dwa rozkłady: obecne kursy GTV obok proponowanej siatki busów.', glowa)
glowa = glowa.replace('</style>', '''.p{background:#eef6f1;font-weight:700;color:#00704f}
th.p{color:#00704f}
.dz{display:inline-block;width:12px;height:12px;border-radius:3px;background:#4B5563;vertical-align:-1px}
.pr{display:inline-block;width:12px;height:12px;border-radius:3px;background:#00704F;vertical-align:-1px}
.vid{width:100%;border-radius:12px;border:1px solid var(--rule);background:#fff;display:block}
.vid.pion{display:none;max-width:420px;margin:0 auto}
@media (max-width:700px){.vid.poz{display:none}.vid.pion{display:block}}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0}
.two .card h3{margin:0 0 6px}
@media (max-width:600px){.two{grid-template-columns:1fr}}
</style>''', 1)
cia = szablon[szablon.index('</head>'):]
pocz = cia[:cia.index('<main')]; kon = cia[cia.index('</main>'):]
pocz = pocz.replace('<div class="bar">⚠️ Propozycja inicjatywy Widełki Koszęcin i mieszkańców – to nie jest obowiązujący rozkład jazdy',
                    '<div class="bar">⚠️ Po prawej propozycja inicjatywy Widełki Koszęcin i mieszkańców – to nie jest obowiązujący rozkład jazdy')

tresc = f'''<main>
<h1>Dziś i w propozycji</h1>
<p class="lead">Ten sam dzień roboczy, dwa rozkłady. <span class="dz"></span> <b>Dziś</b> – wszystkie kursy GTV przejeżdżające przez gminę Koszęcin według rozkładu na poniedziałek 30 listopada 2026 (dzień z lekcjami, razem z kursami szkolnymi). <span class="pr"></span> <b>Propozycja</b> – proponowana siatka 5 linii z przesiadkami na Rynku w Koszęcinie.</p>

<video class="vid poz" src="../symulacja/porownanie.mp4" poster="../symulacja/porownanie_kadr.jpg" controls muted playsinline preload="none"></video>
<video class="vid pion" src="../symulacja/porownanie_pion.mp4" poster="../symulacja/porownanie_pion_kadr.jpg" controls muted playsinline preload="none"></video>
<p class="op">Film z symulacji ruchu (5:00–21:30, 1 s filmu = 20 min): po lewej (na telefonie u góry) dzisiejsze kursy, po prawej (na dole) propozycja. Busy jadą po prawdziwych drogach, razem z samochodami i pociągami. <a href="../#jak-liczona">Jak liczona jest symulacja</a>.</p>

<h2>W liczbach</h2>
<div class="grid">
<div class="card"><div class="op">Kursy przez gminę w dzień roboczy</div><div class="big"><span style="color:#4B5563">{A["n"]}</span> → {B["n"]}</div></div>
<div class="card"><div class="op">Ostatni odjazd</div><div class="big"><span style="color:#4B5563">{hm(A["ostatni"])}</span> → {hm(B["ostatni"])}</div></div>
<div class="card"><div class="op">Kursy po 19:00</div><div class="big"><span style="color:#4B5563">{A["po19"]}</span> → {B["po19"]}</div></div>
<div class="card"><div class="op">Rozkład w ciągu dnia</div><div style="font-weight:600">dziś: szczyty rano i po lekcjach<br>propozycja: podobnie przez cały dzień</div></div>
</div>

<h3>Kursy w każdej godzinie <small style="font-weight:400;color:var(--mut)">(<span class="dz"></span> dziś, <span class="pr"></span> propozycja; według godziny rozpoczęcia kursu)</small></h3>
<div class="card">{"".join(svg)}</div>

<h2>Dojazd do Koszęcina i powrót</h2>
<p class="op">Ile kursów dziennie dojeżdża z danej miejscowości do centrum Koszęcina (Rynek, Ligonia, Szkoła, Lubliniecka), ile wraca i o której jest ostatni powrót z Koszęcina. Dzień roboczy.</p>
<div class="scroll"><table>
<tr><th rowspan="2">Miejscowość</th><th colspan="2">do Koszęcina</th><th colspan="2">z Koszęcina</th><th colspan="2">ostatni powrót</th></tr>
<tr><th>dziś</th><th class="p">propozycja</th><th>dziś</th><th class="p">propozycja</th><th>dziś</th><th class="p">propozycja</th></tr>
{"".join(wiersze)}
</table></div>

<p class="note"><b>Skąd dane.</b> Dziś: rozkład przewoźnika GTV z serwisu gtvbus.kiedyprzyjedzie.pl na 30.11.2026, wszystkie kursy przejeżdżające przez gminę Koszęcin – także linie, których organizatorem nie jest gmina, i krótkie kursy szkolne. Propozycja: rozkład dnia roboczego z tej strony, bez kursów na zamówienie. Liczby mogą się różnić od rozkładów na przystankach w dniach wolnych od nauki. Propozycja inicjatywy Widełki Koszęcin i mieszkańców – <b>to nie jest obowiązujący rozkład jazdy</b>.</p>
'''
os.makedirs(P('strona/porownanie'), exist_ok=True)
open(P('strona/porownanie/index.html'), 'w', encoding='utf-8').write(glowa + pocz + tresc + kon)
print('ok', A['n'], B['n'], {w: (A['do'].get(w, 0), B['do'].get(w, 0)) for w in WSIE})
