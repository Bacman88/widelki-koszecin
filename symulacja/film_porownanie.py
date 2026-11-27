"""Film porównawczy: po lewej dzisiejsze kursy GTV, po prawej proponowana siatka – ten sam dzień, ten sam zegar.

Wejście: FCD_DZIS (/tmp/fcd_dzis.xml, z busy_dzis.rou.xml), FCD (/tmp/fcd_dz.xml, propozycja), oba z pociągami.
Wyjście: wyniki/<nazwa>.mp4 i <nazwa>_kadr.png.  Domyślnie 1920×1080 (dwie mapy obok siebie);
PION=1 → 1080×1920 (dziś u góry, propozycja na dole – na rolki).
Uruchom: python3 film_porownanie.py [od_godz] [do_godz] [nazwa]
"""
import os, sys, math, json, re, bisect, collections, xml.etree.ElementTree as ET
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import font_manager as fm
from matplotlib.animation import FFMpegWriter

OD = float(sys.argv[1]) * 3600 if len(sys.argv) > 1 else 5 * 3600
DO = float(sys.argv[2]) * 3600 if len(sys.argv) > 2 else 21 * 3600
NAZWA = sys.argv[3] if len(sys.argv) > 3 else 'porownanie'
KROK = int(os.environ.get('KROK', 40))
MIN_S = f'{KROK * 30 // 60} min'
PION = os.environ.get('PION') == '1'
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
plt.rcParams['font.family'] = ['Inter', 'DejaVu Sans']
KOL = {'1': '#00704F', '2': '#1F6FD6', '3': '#CC8A00', '4': '#D4473A', '5': '#7C3AED'}
SZARY = '#4B5563'
TLO, DROGA, DROGA_GL, TOR = '#F7F6F2', '#D9D6CE', '#B3AEA3', '#6B675F'
KOL_POC = {'K': '#F2B705', 'P': '#7A2E8E', 'I': '#1F3A93'}; ETYK = {'K': 'KŚ', 'P': 'PR', 'I': 'IC'}
LIN_POC = json.load(open('pociagi_linie.json')) if os.path.exists('pociagi_linie.json') else {}

net = sumolib.net.readNet('koszecin.net.xml.gz', withPrograms=False)
kx = math.cos(math.radians(50.64))
def P(lon, lat): return (lon * kx, lat)
drogi, glowne, tory = [], [], []
for e in net.getEdges():
    if e.getID().startswith(':'): continue
    pts = [P(*net.convertXY2LonLat(x, y)) for x, y in e.getShape()]
    if e.allows('rail') and not e.allows('passenger'): tory.append(pts)
    elif e.allows('passenger'): (glowne if e.getPriority() >= 7 else drogi).append(pts)
gmina = json.load(open('../dane/gmina_koszecin.geojson'))['features'][0]['geometry']['coordinates'][0]
s = open('../skrypty/build.py').read()
S = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(r"'(\w+)':\(([\d.]+),([\d.]+),'([^']+)'", s)}
NAZWY = {'lubpkp': 'Lubliniec', 'kosr': 'Koszęcin', 'kalp': 'Kalety', 'bor': 'Boronów', 'pia': 'Piasek', 'str': 'Strzebiń',
         'laz': 'Łazy', 'pil': 'Piłka', 'sad': 'Sadów', 'bru': 'Brusiek', 'lisp': 'Lisów', 'wie': 'Wierzbie', 'cie': 'Cieszowa'}

def wczytaj(fcd):
    poz = collections.defaultdict(list)
    for _, el in ET.iterparse(fcd):
        if el.tag == 'timestep':
            t = float(el.get('time'))
            if OD - 10 <= t <= DO + 10:
                for v in el: poz[t].append((v.get('id'), float(v.get('x')), float(v.get('y'))))
            el.clear()
    return poz
POZ = {'dzis': wczytaj(os.environ.get('FCD_DZIS', '/tmp/fcd_dzis.xml')), 'prop': wczytaj(os.environ.get('FCD', '/tmp/fcd_dz.xml'))}
CZASY = {k: sorted(v) for k, v in POZ.items()}

def trasy(plik, wzor):
    out = collections.defaultdict(set)
    for m in re.finditer(wzor, open(plik).read(), re.S):
        for e in m.group(2).split(): out[m.group(1)].add(e)
    return {l: [[P(*net.convertXY2LonLat(x, y)) for x, y in net.getEdge(e).getShape()] for e in es] for l, es in out.items()}
TR = {'dzis': trasy('busy_dzis.rou.xml', r'<vehicle id="(G)_[^"]*".*?edges="([^"]+)"'),
      'prop': trasy('busy.rou.xml', r'<vehicle id="L(\d)[^"]*".*?edges="([^"]+)"')}
# odjazdy kursów (do licznika „kursów od rana”)
def starty(plik, wzor):
    return sorted(int(m.group(1)) + 60 for m in re.finditer(wzor, open(plik).read()))
START = {'dzis': starty('busy_dzis.rou.xml', r'<vehicle id="G_[^"]*" type="bus" depart="([\d.]+)"'),
         'prop': starty('busy.rou.xml', r'<vehicle id="L\d[^"]*" type="bus" depart="([\d.]+)"')}
START = {k: [int(float(x)) for x in v] for k, v in START.items()}

# --- układ ---
if PION:
    W, H = 1080, 1920
    AXS = {'dzis': [0.0, 0.525, 1.0, 0.285], 'prop': [0.0, 0.215, 1.0, 0.27]}
else:
    W, H = 1920, 1080
    AXS = {'dzis': [0.005, 0.12, 0.49, 0.665], 'prop': [0.505, 0.12, 0.49, 0.665]}
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=TLO)
# wspólny kadr: gmina + Lubliniec + Kalety + Boronów
xs, ys = [], []
for lon, lat in ((18.672, 50.672), (18.99, 50.595), (18.885, 50.556), (18.94, 50.69), (18.80, 50.585), (18.835, 50.70)):
    x_, y_ = P(lon, lat); xs.append(x_); ys.append(y_)
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
A = {}
for k, r in AXS.items():
    ax = fig.add_axes(r); ax.set_facecolor(TLO); ax.set_axis_off(); A[k] = ax
    axw, axh = r[2] * W, r[3] * H
    span = max(max(xs) - min(xs), (max(ys) - min(ys)) * axw / axh) / 2 * 1.06
    ax.set_xlim(cx - span, cx + span); ax.set_ylim(cy - span * axh / axw, cy + span * axh / axw)
    ax.fill([P(*c)[0] for c in gmina], [P(*c)[1] for c in gmina], color='#EAE7DF', zorder=0, lw=0)
    ax.plot([P(*c)[0] for c in gmina], [P(*c)[1] for c in gmina], color='#C9C3B6', lw=1, ls=(0, (4, 3)), zorder=1)
    ax.add_collection(LineCollection(drogi, colors=DROGA, linewidths=0.5, zorder=2))
    ax.add_collection(LineCollection(glowne, colors=DROGA_GL, linewidths=1.2, zorder=3))
    ax.add_collection(LineCollection(tory, colors=TOR, linewidths=0.8, linestyles=(0, (3, 2)), zorder=3))
    for l, segs in TR[k].items():
        ax.add_collection(LineCollection(segs, colors=SZARY if l == 'G' else KOL[l], linewidths=2.2, alpha=0.22, zorder=3, capstyle='round'))
    for kk, nm in NAZWY.items():
        lat, lon = S[kk]; x, y = P(lon, lat)
        ax.text(x, y + 0.0035, nm, fontsize=10.5 if PION else 9.5, color='#5E5A52', ha='center', va='bottom', zorder=5, fontweight='semibold', clip_on=True)
SK = 1.15
EL = {}
for k, ax in A.items():
    EL[k] = dict(
        bus=ax.scatter([], [], s=120 * SK * SK, zorder=7, edgecolors='white', linewidths=1.1),
        btx=[ax.text(0, 0, '', fontsize=7 * SK, color='white', ha='center', va='center', zorder=8, fontweight='bold', visible=False, clip_on=True) for _ in range(40)],
        tow=ax.scatter([], [], s=14, marker='s', c='#8A857B', zorder=6, edgecolors='white', linewidths=0.4),
        ptx=[ax.text(0, 0, '', fontsize=6 * SK, ha='center', va='center', zorder=6.6, fontweight='bold', visible=False, clip_on=True) for _ in range(30)])

# --- napisy ---
C = '#1E1D1B'
if PION:
    fig.text(0.5, 0.925, 'Ten sam dzień – dwa rozkłady', fontsize=34, fontweight='bold', color=C, ha='center')
    zegar = fig.text(0.5, 0.845, '', fontsize=58, fontweight='bold', color=C, ha='center')
    lab = {'dzis': (0.05, 0.815, 'DZIŚ · kursy GTV przez gminę', SZARY),
           'prop': (0.05, 0.49, 'PROPOZYCJA · 5 linii, przesiadki na Rynku', KOL['1'])}
    cnt = {'dzis': (0.05, 0.53), 'prop': (0.05, 0.222)}
    FS_LAB, FS_CNT = 19, 16
else:
    fig.text(0.5, 0.945, 'Ten sam dzień – dwa rozkłady busów', fontsize=28, fontweight='bold', color=C, ha='center')
    zegar = fig.text(0.5, 0.83, '', fontsize=46, fontweight='bold', color=C, ha='center')
    lab = {'dzis': (0.02, 0.80, 'DZIŚ · kursy GTV przez gminę Koszęcin', SZARY),
           'prop': (0.98, 0.80, 'PROPOZYCJA · 5 linii, przesiadki na Rynku', KOL['1'])}
    cnt = {'dzis': (0.02, 0.125), 'prop': (0.52, 0.125)}
    FS_LAB, FS_CNT = 18, 15
for k, (x, y, t, c) in lab.items():
    fig.text(x, y, t, fontsize=FS_LAB, fontweight='bold', color='white', va='bottom', ha='right' if x > 0.9 else 'left',
             bbox=dict(boxstyle='round,pad=0.4', fc=c, ec='none'))
licz = {k: fig.text(x, y, '', fontsize=FS_CNT, color='#2E2C28', fontweight='semibold', va='bottom') for k, (x, y) in cnt.items()}
fig.text(0.5, 0.905 if not PION else 0.902, f'dzień roboczy · 1 s filmu = {MIN_S}', fontsize=12, color='#77736A', ha='center')
stopka_y = 0.045 if not PION else 0.166
fig.text(0.5, stopka_y + (0.03 if not PION else 0.016), 'Po lewej: kursy GTV wg rozkładu z gtvbus.kiedyprzyjedzie.pl (dzień roboczy z lekcjami). Po prawej: propozycja Widełek Koszęcin i mieszkańców – to NIE jest obowiązujący rozkład.' if not PION else
         'Dziś: kursy GTV wg rozkładu z gtvbus.kiedyprzyjedzie.pl (dzień roboczy z lekcjami).\nPropozycja Widełek Koszęcin i mieszkańców – to NIE jest obowiązujący rozkład.',
         fontsize=11.5 if not PION else 13, color='#5E5A52', ha='center', linespacing=1.4)
fig.text(0.5, stopka_y - 0.005, 'busy-koszecin.smart-ant.pl', fontsize=14 if not PION else 17, color='#3D6B4F', fontweight='semibold', ha='center')
if PION:   # ciemne pasy pod napisy Reelsów
    for y0, hgt, kier in ((0.0, 0.165, 1), (0.955, 0.045, -1)):
        gax = fig.add_axes([0, y0, 1, hgt]); gax.axis('off')
        alfa = (np.linspace(1, 0, 200) if kier == 1 else np.linspace(0, 1, 200))
        alfa = np.clip(alfa * 1.6, 0, 1)[:, None] * np.ones((200, 10))
        gax.imshow(np.dstack([np.ones((200, 10, 3)) * np.array([0x1E, 0x1D, 0x1B]) / 255, alfa]), aspect='auto', extent=[0, 1, 0, 1], origin='lower')

def pozycje(k, t):
    cz = CZASY[k]; poz = POZ[k]
    i = bisect.bisect_right(cz, t)
    if i == 0 or i == len(cz): return poz[cz[min(i, len(cz) - 1)]] if cz else []
    t0, t1 = cz[i - 1], cz[i]
    if t1 - t0 > 30: return poz[t0 if t - t0 < t1 - t else t1]
    w = (t - t0) / (t1 - t0); nast = {v[0]: v for v in poz[t1]}
    return [(vid, x + (nast[vid][1] - x) * w, y + (nast[vid][2] - y) * w) if vid in nast else (vid, x, y) for vid, x, y in poz[t0]]

def klatka(t):
    for k in A:
        b, kol, tx, pp, pv, tw = [], [], [], [], [], []
        for vid, lon, lat in pozycje(k, t):
            if vid.startswith('G_'): b.append(P(lon, lat)); kol.append(SZARY); tx.append('')
            elif vid.startswith('L'): b.append(P(lon, lat)); kol.append(KOL[vid[1]]); tx.append(vid[1])
            elif '_p' in vid or '_x' in vid: pp.append(P(lon, lat)); pv.append(vid)
            else: tw.append(P(lon, lat))
        e = EL[k]
        # rozsuń stojące razem
        gr = []
        for i, (x, y) in enumerate(b):
            for g in gr:
                if math.dist((x, y), b[g[0]]) < 0.004: g.append(i); break
            else: gr.append([i])
        for g in gr:
            if len(g) > 1:
                mx = sum(b[i][0] for i in g) / len(g); my = sum(b[i][1] for i in g) / len(g)
                for j, i in enumerate(g):
                    a = 2 * math.pi * j / len(g) + math.pi / 2
                    b[i] = (mx + 0.0024 * math.cos(a), my + 0.0024 * math.sin(a))
        e['bus'].set_offsets(b if b else [[None, None]]); e['bus'].set_color(kol if kol else ['none']); e['bus'].set_edgecolor('white')
        for i, txt in enumerate(e['btx']):
            if i < len(b) and tx[i]: txt.set_position(b[i]); txt.set_text(tx[i]); txt.set_visible(True)
            else: txt.set_visible(False)
        e['tow'].set_offsets(tw if tw else [[None, None]])
        for i, txt in enumerate(e['ptx']):
            if i < len(pp):
                c = pv[i][-1]
                txt.set_position(pp[i]); txt.set_text(LIN_POC.get(pv[i], ETYK[c])); txt.set_color(C if c == 'K' else 'white')
                txt.set_bbox(dict(boxstyle='round,pad=0.3,rounding_size=0.15', fc=KOL_POC[c], ec=C, lw=0.7)); txt.set_visible(True)
            else: txt.set_visible(False)
        n_jedzie = len(b); n_od = bisect.bisect_right(START[k], t) - bisect.bisect_right(START[k], OD - 1)
        licz[k].set_text(f'busów w trasie: {n_jedzie}   ·   kursów od {int(OD // 3600)}:00: {n_od}')
    zegar.set_text(f'{int(t // 3600)}:{int(t % 3600 // 60):02d}')

os.makedirs('wyniki', exist_ok=True)
klatka(7 * 3600 + 30 * 60 if OD <= 7.5 * 3600 <= DO else (OD + DO) / 2)
fig.savefig(f'wyniki/{NAZWA}_kadr.png', dpi=100, facecolor=TLO)
if os.environ.get('TYLKO_KADR'): sys.exit(0)
wr = FFMpegWriter(fps=30, codec='libx264', extra_args=['-preset', 'veryfast', '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'])
n = 0
with wr.saving(fig, f'wyniki/{NAZWA}.mp4', 100):
    t = OD
    while t <= DO:
        klatka(t); wr.grab_frame(); t += KROK; n += 1
    for _ in range(60): wr.grab_frame(); n += 1      # 2 s stopklatki z licznikami na koniec
print(f'wyniki/{NAZWA}.mp4', round(n / 30, 1), 's')
