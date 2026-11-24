"""Film z symulacji (widok całej sieci): busy w kolorach linii, pociągi, korki na drogach, zegar.

Wejście (z przebiegu symulacji z zapisem pozycji – patrz README, sekcja „Film”):
  /tmp/fcd.xml     pozycje busów i pociągów co 10 s (fcd-output, geo)
  /tmp/ed120.xml   prędkości na drogach w przedziałach 2-minutowych (edgeData period=120)
Wyjście: wyniki/film.mp4 (H.264, do strony WWW) i wyniki/film_kadr.png (kadr na plakat/miniaturę).
Uruchom: python3 film.py [od_godz] [do_godz]   np. python3 film.py 5.5 10.5
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
KROK = 20          # s symulacji na klatkę (30 kl./s → 10 min symulacji w 1 s filmu)
FCD, ED = '/tmp/fcd.xml', '/tmp/ed120.xml'
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
plt.rcParams['font.family'] = ['Inter', 'DejaVu Sans']
KOL = {'1': '#00704F', '2': '#1F6FD6', '3': '#CC8A00', '4': '#D4473A'}
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
        if OD - 10 <= t <= DO + 10:
            for v in el: poz[t].append((v.get('id'), float(v.get('x')), float(v.get('y')), float(v.get('speed'))))
        el.clear()

# --- rysunek ---
W, H, DPI = 1280, 720, 100
fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=TLO)
ax = fig.add_axes([0.0, 0.0, 0.62, 1.0]); ax.set_facecolor(TLO); ax.set_axis_off()
# trasy linii (blado, pod busami) i kadr dopasowany do zasięgu busów
trasy = collections.defaultdict(list)
for m in re.finditer(r'<vehicle id="L(\d)[^"]*".*?edges="([^"]+)"', open('busy.rou.xml').read(), re.S):
    for e in set(m.group(2).split()): trasy[m.group(1)].append(e)
trasy_pts = {l: [[P(*net.convertXY2LonLat(x, y)) for x, y in net.getEdge(e).getShape()] for e in set(es)] for l, es in trasy.items()}
allpts = [p for l in trasy_pts.values() for seg in l for p in seg]
xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
span = max(max(xs) - min(xs), (max(ys) - min(ys)) * 0.62 * W / H) / 2 * 1.10
cx -= span * 0.03
ax.set_xlim(cx - span, cx + span); ax.set_ylim(cy - span * H / (0.62 * W), cy + span * H / (0.62 * W))
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
    ax.text(x, y + 0.0042, nm, fontsize=8.5, color='#5E5A52', ha='center', va='bottom', zorder=5, fontweight='semibold')
bus_sc = ax.scatter([], [], s=150, zorder=7, edgecolors='white', linewidths=1.2)
poc_sc = ax.scatter([], [], s=22, marker='s', c='#2B2926', zorder=6, edgecolors='white', linewidths=0.5)
bus_txt = [ax.text(0, 0, '', fontsize=7.5, color='white', ha='center', va='center', zorder=8, fontweight='bold', visible=False)
           for _ in range(40)]

# panel boczny
px = 0.645
fig.text(px, 0.93, 'Proponowana siatka busów', fontsize=17, fontweight='bold', color='#1E1D1B')
fig.text(px, 0.885, 'gminy Koszęcin – symulacja ruchu (SUMO)', fontsize=12, color='#4A4740')
zegar = fig.text(px, 0.74, '', fontsize=44, fontweight='bold', color='#1E1D1B')
fig.text(px, 0.705, 'dzień roboczy · 1 s filmu = 10 min', fontsize=9.5, color='#77736A')
ly = 0.62
for l, nazwa in [('1', 'Linia 1: Lubliniec – Koszęcin – Piasek'), ('2', 'Linia 2: Kalety – Koszęcin – Boronów'),
                 ('3', 'Linia 3: Lisów – Koszęcin PKP'), ('4', 'Linia 4: Łazy – Koszęcin – Piłka')]:
    fig.patches.append(matplotlib.patches.Ellipse((px + 0.012, ly + 0.012), 0.022 * H / W, 0.022, transform=fig.transFigure, color=KOL[l], figure=fig))
    fig.text(px + 0.012, ly + 0.012, l, fontsize=8, color='white', ha='center', va='center', fontweight='bold')
    fig.text(px + 0.032, ly + 0.003, nazwa, fontsize=10, color='#2E2C28'); ly -= 0.05
fig.patches.append(plt.Rectangle((px + 0.006, ly + 0.005), 0.012, 0.014, transform=fig.transFigure, color='#2B2926', figure=fig))
fig.text(px + 0.032, ly + 0.003, 'pociąg (przybliżony ruch, nie rozkład PKP)', fontsize=10, color='#2E2C28'); ly -= 0.05
fig.lines.append(plt.Line2D([px + 0.003, px + 0.022], [ly + 0.012, ly + 0.012], transform=fig.transFigure, color='#D6452F', lw=3.5, figure=fig))
fig.text(px + 0.032, ly + 0.003, 'wolny ruch / korek', fontsize=10, color='#2E2C28')
fig.text(px, 0.135, 'To NIE jest aktualny rozkład jazdy.', fontsize=11.5, fontweight='bold', color='#B3261E')
fig.text(px, 0.098, 'Propozycja mieszkańca; ruch aut wg pomiarów GPR 2020/21,', fontsize=9, color='#5E5A52')
fig.text(px, 0.072, 'pociągi i rogatki w przybliżeniu.', fontsize=9, color='#5E5A52')
fig.text(px, 0.03, 'busy-koszecin.smart-ant.pl', fontsize=9.5, color='#3D6B4F', fontweight='semibold')

czasy = sorted(poz)
def klatka(t):
    tt = min(czasy, key=lambda c: abs(c - t))
    b, p, kol, tx = [], [], [], []
    for vid, lon, lat, v in poz[tt]:
        if vid.startswith('L'):
            b.append(P(lon, lat)); kol.append(KOL[vid[1]]); tx.append(vid[1])
        else: p.append(P(lon, lat))
    # busy stojące razem (np. przesiadka na Rynku) rozsuwamy w kółko, żeby było widać każdy
    gr = []
    for i, (x, y) in enumerate(b):
        for g in gr:
            if math.dist((x, y), b[g[0]]) < 0.0025: g.append(i); break
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

os.makedirs('wyniki', exist_ok=True)
klatka(7 * 3600 + 50 * 60); fig.savefig('wyniki/film_kadr.png', dpi=DPI, facecolor=TLO)
wr = FFMpegWriter(fps=30, codec='libx264', extra_args=['-preset', 'veryfast', '-crf', '26', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'])
with wr.saving(fig, 'wyniki/film.mp4', DPI):
    t = OD
    while t <= DO:
        klatka(t); wr.grab_frame(); t += KROK
print('wyniki/film.mp4', round((DO - OD) / KROK / 30, 1), 's')
