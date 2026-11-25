"""Film z symulacji (widok całej sieci): busy w kolorach linii, pociągi, korki na drogach, zegar.

Wejście (z przebiegu symulacji z zapisem pozycji – patrz README, sekcja „Film”):
  /tmp/fcd.xml     pozycje busów i pociągów co 10 s (fcd-output, geo)
  /tmp/ed120.xml   prędkości na drogach w przedziałach 2-minutowych (edgeData period=120)
Wyjście: wyniki/film.mp4 (H.264, do strony WWW) i wyniki/film_kadr.png (kadr na plakat/miniaturę).
Uruchom: python3 film.py [od_godz] [do_godz] [nazwa]   np. python3 film.py 5.5 10.5 film; python3 film.py 13 18 film_popoludnie
"""
import os, sys, math, json, re, collections, xml.etree.ElementTree as ET
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import font_manager as fm
from matplotlib.animation import FFMpegWriter

OD = float(sys.argv[1]) * 3600 if len(sys.argv) > 1 else 5.5 * 3600
DO = float(sys.argv[2]) * 3600 if len(sys.argv) > 2 else 10.5 * 3600
NAZWA = sys.argv[3] if len(sys.argv) > 3 else 'film'
KROK = int(os.environ.get('KROK', 20))   # s symulacji na klatkę (30 kl./s; 20 → 10 min symulacji w 1 s filmu)
MIN_S = f'{KROK * 30 // 60} min'
FCD = os.environ.get('FCD', '/tmp/fcd.xml'); ED = os.environ.get('ED', '/tmp/ed120.xml')
# tryb „przykładowa podróż”: PODROZ=plik.json – odcinki z wyróżnionym busem (patrz przyklady_film.py)
PODROZ = json.load(open(os.environ['PODROZ'])) if os.environ.get('PODROZ') else None
if PODROZ:
    OD = min(o['od'] for o in PODROZ['odcinki']); DO = max(o['do'] for o in PODROZ['odcinki'])
    OKNA = [(o['od'] - 20, o['do'] + 20) for o in PODROZ['odcinki']]
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
plt.rcParams['font.family'] = ['Inter', 'DejaVu Sans']
KOL = {'1': '#00704F', '2': '#1F6FD6', '3': '#CC8A00', '4': '#D4473A', '5': '#7C3AED'}
TLO, DROGA, DROGA_GL, TOR = '#F7F6F2', '#D9D6CE', '#B3AEA3', '#6B675F'

net = sumolib.net.readNet('koszecin.net.xml.gz', withPrograms=False)
lat0 = 50.64; kx = math.cos(math.radians(lat0))
def P(lon, lat): return (lon * kx, lat)

# --- tło: drogi, tory, granica gminy, nazwy miejscowości ---
drogi, glowne, tory, kraw_seg, kraw_lim = [], [], [], [], []
for e in net.getEdges():
    if e.getID().startswith(':'): continue
    pts = [P(*net.convertXY2LonLat(x, y)) for x, y in e.getShape()]
    if e.allows('rail') and not e.allows('passenger'): tory.append(pts)
    elif e.allows('passenger'):
        (glowne if e.getPriority() >= 7 else drogi).append(pts)
        if e.getPriority() >= 5:
            kraw_seg.append((e.getID(), pts)); kraw_lim.append(e.getSpeed())
gmina = json.load(open('../dane/gmina_koszecin.geojson'))['features'][0]['geometry']['coordinates'][0]
s = open('../skrypty/build.py').read()
S = {m.group(1): (float(m.group(2)), float(m.group(3)), m.group(4)) for m in re.finditer(r"'(\w+)':\(([\d.]+),([\d.]+),'([^']+)'", s)}
NAZWY = {'lubpkp': 'Lubliniec', 'kosr': 'Koszęcin', 'kalp': 'Kalety', 'bor': 'Boronów', 'pia': 'Piasek', 'str': 'Strzebiń',
         'laz': 'Łazy', 'pil': 'Piłka', 'sad': 'Sadów', 'bru': 'Brusiek', 'lisp': 'Lisów', 'buk': 'Bukowiec', 'wie': 'Wierzbie'}

# --- prędkości na drogach (korki) ---
idx = {k: i for i, (k, _) in enumerate(kraw_seg)}
korki = {}                      # początek przedziału → lista (indeks krawędzi, poziom 0..1)
for _, el in ET.iterparse(ED):
    if el.tag == 'interval':
        b = float(el.get('begin')); lst = []
        for e in el:
            i = idx.get(e.get('id'))
            if i is None or e.get('speed') is None: continue
            r = float(e.get('speed')) / kraw_lim[i]
            occ = float(e.get('occupancy', 0) or 0)
            if r < 0.5 and occ > 8: lst.append((i, min(1, (0.5 - r) / 0.4)))
        korki[b] = lst; el.clear()

# --- pozycje busów i pociągów ---
poz = collections.defaultdict(list)
for _, el in ET.iterparse(FCD):
    if el.tag == 'timestep':
        t = float(el.get('time'))
        if (OD - 10 <= t <= DO + 10) and (not PODROZ or any(a <= t <= b for a, b in OKNA)):
            for v in el: poz[t].append((v.get('id'), float(v.get('x')), float(v.get('y')), float(v.get('speed'))))
        el.clear()

# --- rysunek ---
PION = os.environ.get('PION') == '1'          # pionowa wersja 1080×1920 na rolki (Reels)
W, H, DPI = (1080, 1920, 100) if PION else (1280, 720, 100)
AX = [0.0, 0.37, 1.0, 0.44] if PION else [0.0, 0.0, 0.62, 1.0]
fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=TLO)
ax = fig.add_axes(AX); ax.set_facecolor(TLO); ax.set_axis_off()
# trasy linii (blado, pod busami) i kadr dopasowany do zasięgu busów
trasy = collections.defaultdict(list)
for m in re.finditer(r'<vehicle id="L(\d)[^"]*".*?edges="([^"]+)"', open('busy.rou.xml').read(), re.S):
    for e in set(m.group(2).split()): trasy[m.group(1)].append(e)
trasy_pts = {l: [[P(*net.convertXY2LonLat(x, y)) for x, y in net.getEdge(e).getShape()] for e in set(es)] for l, es in trasy.items()}
allpts = [p for l in trasy_pts.values() for seg in l for p in seg]
xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
axw, axh = AX[2] * W, AX[3] * H
span = max(max(xs) - min(xs), (max(ys) - min(ys)) * axw / axh) / 2 * (1.13 if PION else 1.10)
if not PION: cx -= span * 0.03
ax.set_xlim(cx - span, cx + span); ax.set_ylim(cy - span * axh / axw, cy + span * axh / axw)
ax.fill([P(*c)[0] for c in gmina], [P(*c)[1] for c in gmina], color='#EAE7DF', zorder=0, lw=0)
ax.plot([P(*c)[0] for c in gmina], [P(*c)[1] for c in gmina], color='#C9C3B6', lw=1, ls=(0, (4, 3)), zorder=1)
ax.add_collection(LineCollection(drogi, colors=DROGA, linewidths=0.5, zorder=2))
ax.add_collection(LineCollection(glowne, colors=DROGA_GL, linewidths=1.3, zorder=3))
ax.add_collection(LineCollection(tory, colors=TOR, linewidths=0.8, linestyles=(0, (3, 2)), zorder=3))
for l in sorted(trasy_pts):
    ax.add_collection(LineCollection(trasy_pts[l], colors=KOL[l], linewidths=2.2, alpha=0.28, zorder=3, capstyle='round'))
lc_korki = LineCollection([], linewidths=3.2, zorder=4, capstyle='round'); ax.add_collection(lc_korki)
for k, nm in NAZWY.items():
    lat, lon, _ = S[k]; x, y = P(lon, lat)
    ax.text(x, y + 0.0042, nm, fontsize=12 if PION else 8.5, color='#5E5A52', ha='center', va='bottom', zorder=5, fontweight='semibold')
SK = 1.5 if PION else 1.0
bus_sc = ax.scatter([], [], s=150 * SK * SK, zorder=7, edgecolors='white', linewidths=1.2)
poc_sc = ax.scatter([], [], s=16 * (2 if PION else 1), marker='s', c='#8A857B', zorder=6, edgecolors='white', linewidths=0.4)   # towarowe
KOL_POC = {'K': '#F2B705', 'P': '#7A2E8E'}     # Koleje Śląskie / POLREGIO
pas_sc = ax.scatter([], [], s=230 * SK * SK, marker='s', zorder=6.5, edgecolors='#1E1D1B', linewidths=0.8)
pas_txt = [ax.text(0, 0, '', fontsize=6.3 * SK, ha='center', va='center', zorder=6.6, fontweight='bold', visible=False) for _ in range(30)]
bus_txt = [ax.text(0, 0, '', fontsize=7.5 * SK, color='white', ha='center', va='center', zorder=8, fontweight='bold', visible=False)
           for _ in range(40)]

# panel boczny
if not PION:
    px = 0.645
    fig.text(px, 0.93, 'Proponowana siatka busów', fontsize=17, fontweight='bold', color='#1E1D1B')
    fig.text(px, 0.885, 'gminy Koszęcin – symulacja ruchu (SUMO)', fontsize=12, color='#4A4740')
    zegar = fig.text(px, 0.74, '', fontsize=44, fontweight='bold', color='#1E1D1B')
    fig.text(px, 0.705, f'dzień roboczy · 1 s filmu = {MIN_S}', fontsize=9.5, color='#77736A')
    ly = 0.62
    for l, nazwa in [('1', 'Linia 1: Lubliniec – Koszęcin – Piasek'), ('2', 'Linia 2: Kalety – Koszęcin – Boronów'),
                     ('3', 'Linia 3: Lisów – Koszęcin PKP'), ('4', 'Linia 4: Łazy – Strzebiń – Koszęcin'),
                     ('5', 'Linia 5: Koszęcin – Piłka – Lubliniec')]:
        fig.patches.append(matplotlib.patches.Ellipse((px + 0.012, ly + 0.012), 0.022 * H / W, 0.022, transform=fig.transFigure, color=KOL[l], figure=fig))
        fig.text(px + 0.012, ly + 0.012, l, fontsize=8, color='white', ha='center', va='center', fontweight='bold')
        fig.text(px + 0.032, ly + 0.003, nazwa, fontsize=10, color='#2E2C28'); ly -= 0.045
    for k, nazwa in (('K', 'pociąg Kolei Śląskich (rozkład 2026/27)'), ('P', 'pociąg POLREGIO (rozkład 2026/27)')):
        fig.patches.append(plt.Rectangle((px + 0.003, ly + 0.002), 0.019, 0.02, transform=fig.transFigure, facecolor=KOL_POC[k], edgecolor='#1E1D1B', lw=0.8, figure=fig))
        fig.text(px + 0.0125, ly + 0.012, 'KŚ' if k == 'K' else 'PR', fontsize=6, ha='center', va='center', fontweight='bold', color='#1E1D1B' if k == 'K' else 'white')
        fig.text(px + 0.032, ly + 0.003, nazwa, fontsize=10, color='#2E2C28'); ly -= 0.045
    fig.patches.append(plt.Rectangle((px + 0.008, ly + 0.007), 0.009, 0.01, transform=fig.transFigure, color='#8A857B', figure=fig))
    fig.text(px + 0.032, ly + 0.003, 'pociąg towarowy (przybliżony)', fontsize=10, color='#2E2C28'); ly -= 0.045
    fig.lines.append(plt.Line2D([px + 0.003, px + 0.022], [ly + 0.012, ly + 0.012], transform=fig.transFigure, color='#D6452F', lw=3.5, figure=fig))
    fig.text(px + 0.032, ly + 0.003, 'wolny ruch / korek', fontsize=10, color='#2E2C28')
    fig.text(px, 0.135, 'To NIE jest aktualny rozkład jazdy.', fontsize=11.5, fontweight='bold', color='#B3261E')
    fig.text(px, 0.098, 'Propozycja mieszkańców; ruch aut wg pomiarów GPR 2020/21,', fontsize=9, color='#5E5A52')
    fig.text(px, 0.072, 'pociągi towarowe i rogatki w przybliżeniu.', fontsize=9, color='#5E5A52')
    fig.text(px, 0.03, 'busy-koszecin.smart-ant.pl', fontsize=9.5, color='#3D6B4F', fontweight='semibold')
else:
    fx = 0.06
    fig.text(fx, 0.9, 'Proponowana siatka busów', fontsize=34, fontweight='bold', color='#1E1D1B')
    fig.text(fx, 0.877, PODROZ['tytul'] if PODROZ else 'gminy Koszęcin – symulacja ruchu', fontsize=21, color='#4A4740')
    zegar = fig.text(fx, 0.82, '', fontsize=72, fontweight='bold', color='#1E1D1B')
    fig.text(fx + 0.36, 0.83, f'dzień roboczy\n1 s filmu = {MIN_S}', linespacing=1.4, fontsize=16, color='#77736A')
    ly = 0.348
    for l, nazwa in [('1', 'Lubliniec – Koszęcin – Piasek'), ('2', 'Kalety – Koszęcin – Boronów'),
                     ('3', 'Lisów – Koszęcin PKP'), ('4', 'Łazy – Strzebiń – Koszęcin'),
                     ('5', 'Koszęcin – Piłka – Lubliniec')]:
        fig.patches.append(matplotlib.patches.Ellipse((fx + 0.016, ly + 0.006), 0.022 * H / W, 0.022, transform=fig.transFigure, color=KOL[l], figure=fig))
        fig.text(fx + 0.016, ly + 0.006, l, fontsize=13, color='white', ha='center', va='center', fontweight='bold')
        fig.text(fx + 0.045, ly + 0.001, nazwa, fontsize=15, color='#2E2C28'); ly -= 0.0245
    px2, ly = 0.56, 0.348
    for k, nazwa in (('K', 'Koleje Śląskie'), ('P', 'POLREGIO')):
        fig.patches.append(plt.Rectangle((px2, ly - 0.004), 0.05, 0.02, transform=fig.transFigure, facecolor=KOL_POC[k], edgecolor='#1E1D1B', lw=1, figure=fig))
        fig.text(px2 + 0.025, ly + 0.006, 'KŚ' if k == 'K' else 'PR', fontsize=11, ha='center', va='center', fontweight='bold', color='#1E1D1B' if k == 'K' else 'white')
        fig.text(px2 + 0.065, ly + 0.001, nazwa, fontsize=15, color='#2E2C28'); ly -= 0.026
    fig.patches.append(plt.Rectangle((px2 + 0.015, ly), 0.02, 0.011, transform=fig.transFigure, color='#8A857B', figure=fig))
    fig.text(px2 + 0.065, ly + 0.001, 'pociąg towarowy', fontsize=15, color='#2E2C28'); ly -= 0.026
    fig.lines.append(plt.Line2D([px2, px2 + 0.05], [ly + 0.006, ly + 0.006], transform=fig.transFigure, color='#D6452F', lw=5, figure=fig))
    fig.text(px2 + 0.065, ly + 0.001, 'wolny ruch / korek', fontsize=15, color='#2E2C28')
    fig.text(fx, 0.215, 'To NIE jest aktualny rozkład jazdy – propozycja mieszkańców.', fontsize=17, fontweight='bold', color='#B3261E')
    # ciemne pasy na dole i u góry: Facebook kładzie tam biały opis rolki i białe ikonki
    import numpy as np
    for y0, hgt, kier in ((0.0, 0.165, 1), (0.955, 0.045, -1)):
        gax = fig.add_axes([0, y0, 1, hgt]); gax.axis('off')
        alfa = np.linspace(1, 0, 200) if kier == 1 else np.linspace(0, 1, 200)
        alfa = np.clip(alfa * 1.6, 0, 1)[:, None] * np.ones((200, 10))
        rgb = np.ones((200, 10, 3)) * np.array([0x1E, 0x1D, 0x1B]) / 255
        gax.imshow(np.dstack([rgb, alfa]), aspect='auto', extent=[0, 1, 0, 1], origin='lower')
    fig.text(fx, 0.19, 'busy-koszecin.smart-ant.pl', fontsize=17, color='#3D6B4F', fontweight='semibold')

# --- tryb podróży: wyróżniony bus, ślad trasy, przystanki, karta z opisem ---
ODC = None
if PODROZ:
    bus_sc.set_alpha(0.45)
    hl_slad = LineCollection([], linewidths=7 * SK, zorder=6.8, capstyle='round', joinstyle='round', alpha=0.85); ax.add_collection(hl_slad)
    hl_sc = ax.scatter([], [], s=420 * SK * SK, zorder=9, edgecolors='#1E1D1B', linewidths=3.5)
    hl_txt = ax.text(0, 0, '', fontsize=12 * SK, color='white', ha='center', va='center', zorder=9.1, fontweight='bold')
    pin_sc = ax.scatter([], [], s=260 * SK * SK, marker='o', zorder=8.8, facecolors='white', edgecolors='#1E1D1B', linewidths=3)
    pin_txt = [ax.text(0, 0, '', fontsize=13 * SK, color='#1E1D1B', ha='center', va='top', zorder=9.2, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='none', alpha=0.9)) for _ in range(4)]
    k_tyt = fig.text(0.5, 0.466, '', fontsize=30, fontweight='bold', color='white', ha='center', va='center', zorder=20,
                     bbox=dict(boxstyle='round,pad=0.45', fc='#1E1D1B', ec='none', alpha=0.88))
    k_op = fig.text(0.5, 0.442, '', fontsize=22, color='#1E1D1B', ha='center', va='top', zorder=20, linespacing=1.35,
                    bbox=dict(boxstyle='round,pad=0.5', fc='white', ec='#1E1D1B', lw=1.5, alpha=0.95))
    def ustaw_odcinek(o):
        global ODC
        ODC = o; k_tyt.set_text(o['naglowek']); k_op.set_text(o['opis'])
        pin_sc.set_offsets([P(*xy) for xy in o['punkty']])
        for i, t in enumerate(pin_txt):
            if i < len(o['punkty']):
                x, y = P(*o['punkty'][i]); t.set_position((x, y - 0.006)); t.set_text(o['nazwy'][i]); t.set_visible(True)
            else: t.set_visible(False)

czasy = sorted(poz)
import bisect
def pozycje(t):
    """Pozycje w chwili t, liniowo między zapisami co 10 s (płynny ruch przy wolnym tempie)."""
    i = bisect.bisect_right(czasy, t)
    if i == 0 or i == len(czasy): return poz[czasy[min(i, len(czasy) - 1)]]
    t0, t1 = czasy[i - 1], czasy[i]
    if t1 - t0 > 30: return poz[t0 if t - t0 < t1 - t else t1]
    w = (t - t0) / (t1 - t0); nast = {v[0]: v for v in poz[t1]}
    out = []
    for vid, lon, lat, v in poz[t0]:
        n = nast.get(vid)
        out.append((vid, lon + (n[1] - lon) * w, lat + (n[2] - lat) * w, v) if n else (vid, lon, lat, v))
    return out
def klatka(t):
    b, p, kol, tx, pp, pk = [], [], [], [], [], []
    for vid, lon, lat, v in pozycje(t):
        if vid.startswith('L'):
            b.append(P(lon, lat)); kol.append(KOL[vid[1]]); tx.append(vid[1])
        elif '_p' in vid: pp.append(P(lon, lat)); pk.append(vid[-1])
        else: p.append(P(lon, lat))
    pas_sc.set_offsets(pp if pp else [[None, None]]); pas_sc.set_color([KOL_POC[k] for k in pk] if pk else ['none']); pas_sc.set_edgecolor('#1E1D1B')
    for i, txt in enumerate(pas_txt):
        if i < len(pp):
            txt.set_position(pp[i]); txt.set_text('KŚ' if pk[i] == 'K' else 'PR'); txt.set_color('#1E1D1B' if pk[i] == 'K' else 'white'); txt.set_visible(True)
        else: txt.set_visible(False)
    # busy stojące razem (np. przesiadka na Rynku) rozsuwamy w kółko, żeby było widać każdy
    gr = []
    for i, (x, y) in enumerate(b):
        for g in gr:
            if math.dist((x, y), b[g[0]]) < 0.004: g.append(i); break
        else: gr.append([i])
    for g in gr:
        if len(g) > 1:
            mx = sum(b[i][0] for i in g) / len(g); my = sum(b[i][1] for i in g) / len(g)
            for j, i in enumerate(sorted(g, key=lambda i: tx[i])):
                a = 2 * math.pi * j / len(g) + math.pi / 2
                b[i] = (mx + 0.0026 * math.cos(a), my + 0.0026 * math.sin(a) / kx * kx)
    bus_sc.set_offsets(b if b else [[None, None]]); bus_sc.set_color(kol if kol else ['none']); bus_sc.set_edgecolor('white')
    poc_sc.set_offsets(p if p else [[None, None]])
    for i, txt in enumerate(bus_txt):
        if i < len(b): txt.set_position(b[i]); txt.set_text(tx[i]); txt.set_visible(True)
        else: txt.set_visible(False)
    kb = korki.get(t // 120 * 120, [])
    lc_korki.set_segments([kraw_seg[i][1] for i, _ in kb])
    lc_korki.set_color([(0.84, 0.27 + 0.35 * (1 - z), 0.18, 0.55 + 0.4 * z) for _, z in kb])
    zegar.set_text(f'{int(t // 3600)}:{int(t % 3600 // 60):02d}')
    if PODROZ and ODC:
        segs, cur = [], None
        for kurs, a, z in ODC['kursy']:
            if t < a: break
            pts = [P(x[1], x[2]) for c in czasy[bisect.bisect_left(czasy, a):bisect.bisect_right(czasy, min(t, z))] for x in poz[c] if x[0] == kurs]
            if len(pts) > 1: segs.append((pts, KOL[kurs[1]]))
            cur = kurs
        if cur is None: cur = ODC['kursy'][0][0]
        hl_slad.set_segments([sg for sg, _ in segs]); hl_slad.set_color([c for _, c in segs])
        # czekanie na przesiadkę: pasażer stoi na przystanku (znacznik w kolorze następnej linii), bus jedzie dalej bez niego
        ks = ODC['kursy']; ci = [k[0] for k in ks].index(cur)
        if t > ks[ci][2] and ci + 1 < len(ks) and t < ks[ci + 1][1]:
            nast = ks[ci + 1][0]; pp_ = P(*ODC['punkty'][ci + 1])
            hl_sc.set_offsets([pp_]); hl_sc.set_color(KOL[nast[1]]); hl_sc.set_edgecolor('#1E1D1B'); hl_sc.set_alpha(0.55)
            hl_txt.set_position(pp_); hl_txt.set_text(nast[1]); hl_txt.set_visible(True)
            zegar.set_text(f'{int(t // 3600)}:{int(t % 3600 // 60):02d}'); return
        hl_sc.set_alpha(1)
        here = [P(x[1], x[2]) for x in pozycje(t) if x[0] == cur]
        if here:
            hl_sc.set_offsets(here); hl_sc.set_color(KOL[cur[1]]); hl_sc.set_edgecolor('#1E1D1B')
            hl_txt.set_position(here[0]); hl_txt.set_text(cur[1]); hl_txt.set_visible(True)
        else:
            hl_sc.set_offsets([[None, None]]); hl_txt.set_visible(False)

os.makedirs('wyniki', exist_ok=True)
if PODROZ:
    o = PODROZ['odcinki'][0]; ustaw_odcinek(o); klatka((o['od'] + o['do']) / 2)
else: klatka((OD // 3600 + 2) * 3600 + 50 * 60)
fig.savefig(f'wyniki/{NAZWA}_kadr.png', dpi=DPI, facecolor=TLO)
wr = FFMpegWriter(fps=30, codec='libx264', extra_args=['-preset', 'veryfast', '-crf', '26', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'])
n = 0
with wr.saving(fig, f'wyniki/{NAZWA}.mp4', DPI):
    if PODROZ:
        for o in PODROZ['odcinki']:
            ustaw_odcinek(o); krok = o.get('krok', KROK)
            klatka(o['od'])
            for _ in range(int(30 * o.get('pauza_przed', 1.2))): wr.grab_frame(); n += 1
            t = o['od']
            while t <= o['do']:
                klatka(t); wr.grab_frame(); t += krok; n += 1
            for _ in range(int(30 * o.get('pauza_po', 2.0))): wr.grab_frame(); n += 1
    else:
        t = OD
        while t <= DO:
            klatka(t); wr.grab_frame(); t += KROK; n += 1
print(f'wyniki/{NAZWA}.mp4', round(n / 30, 1), 's')
