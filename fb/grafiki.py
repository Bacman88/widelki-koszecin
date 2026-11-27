"""Grafiki na stronę FB: zdjęcie profilowe (720×720) i zdjęcie w tle (1640×624, ważne treści w środkowym pasie)."""
import os, sys, re, math, json, collections
SUMO_HOME = os.environ.get('SUMO_HOME') or __import__('sumo').SUMO_HOME
sys.path.append(os.path.join(SUMO_HOME, 'tools'))
import sumolib
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import font_manager as fm
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
plt.rcParams['font.family'] = ['Inter', 'DejaVu Sans']
KOL = {'1': '#00704F', '2': '#1F6FD6', '3': '#CC8A00', '4': '#D4473A', '5': '#7C3AED'}
TLO = '#F7F6F2'; CIEMNY = '#1E1D1B'
OUT = '../fb'

# --- zdjęcie profilowe: węzeł z 5 liniami ---
fig = plt.figure(figsize=(7.2, 7.2), dpi=100, facecolor=TLO)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-0.86, 0.86); ax.set_ylim(-0.86, 0.86); ax.set_aspect('equal'); ax.axis('off')
ax.add_patch(plt.Circle((0, 0), 1, color=TLO))
kat = {'1': 126, '2': 54, '3': 270, '4': 342, '5': 198}
DY = 0.055
for l, a in kat.items():
    x, y = 0.56 * math.cos(math.radians(a)), 0.56 * math.sin(math.radians(a)) + DY
    ax.plot([0, x], [DY, y], color=KOL[l], lw=33, solid_capstyle='round', zorder=1)
    ax.add_patch(plt.Circle((x, y), 0.17, color=KOL[l], zorder=3, ec='white', lw=6))
    ax.text(x, y - 0.005, l, color='white', fontsize=68, fontweight='bold', ha='center', va='center', zorder=4)
ax.add_patch(plt.Circle((0, DY), 0.25, color=CIEMNY, zorder=5, ec='white', lw=9))
ax.text(0, DY + 0.035, 'BUSY', color='white', fontsize=34, fontweight='bold', ha='center', va='center', zorder=6)
ax.text(0, DY - 0.085, 'Koszęcin', color='#E8E4DA', fontsize=21, ha='center', va='center', zorder=6)
fig.savefig(f'{OUT}/profilowe.png', dpi=100, facecolor=TLO); plt.close(fig)

# --- zdjęcie w tle: mapa siatki + napis ---
# Facebook na komputerze pokazuje tylko pas ok. 1640×315 (połowa wysokości), na telefonie prawie całość,
# a na środku na dole kładzie zdjęcie profilowe. Dlatego: napisy przy lewej krawędzi w środkowym pasie
# (y 0.25–0.75), mapa po prawej z Koszęcinem dokładnie w połowie wysokości.
net = sumolib.net.readNet('koszecin.net.xml.gz', withPrograms=False)
kx = math.cos(math.radians(50.64))
def P(lon, lat): return (lon * kx, lat)
drogi, glowne = [], []
for e in net.getEdges():
    if e.getID().startswith(':') or not e.allows('passenger'): continue
    pts = [P(*net.convertXY2LonLat(x, y)) for x, y in e.getShape()]
    (glowne if e.getPriority() >= 7 else drogi).append(pts)
trasy = collections.defaultdict(set)
for m in re.finditer(r'<vehicle id="L(\d)[^"]*".*?edges="([^"]+)"', open('busy.rou.xml').read(), re.S):
    trasy[m.group(1)] |= set(m.group(2).split())
tp = {l: [[P(*net.convertXY2LonLat(x, y)) for x, y in net.getEdge(e).getShape()] for e in es] for l, es in trasy.items()}
gmina = json.load(open('../dane/gmina_koszecin.geojson'))['features'][0]['geometry']['coordinates'][0]
s_ = open('../skrypty/build.py').read()
S = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(r"'(\w+)':\(([\d.]+),([\d.]+),'", s_)}
W, H = 1640, 624
AX0, AXW = 0.40, 0.60          # mapa: od 40% szerokości do prawej krawędzi
HUBX = 0.78                    # Koszęcin w 78% szerokości obrazka i w połowie wysokości
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=TLO)
ax = fig.add_axes([AX0, 0, AXW, 1]); ax.set_facecolor(TLO); ax.axis('off')
hx = 0.125; hy = hx * H / (AXW * W)
kx0, ky0 = P(S['kosr'][1], S['kosr'][0])
f = (HUBX - AX0) / AXW
ax.set_xlim(kx0 - 2 * hx * f, kx0 + 2 * hx * (1 - f)); ax.set_ylim(ky0 - hy, ky0 + hy)
ax.fill([P(*c)[0] for c in gmina], [P(*c)[1] for c in gmina], color='#EAE7DF', lw=0, zorder=0)
ax.add_collection(LineCollection(drogi, colors='#DEDAD1', linewidths=0.5, zorder=1))
ax.add_collection(LineCollection(glowne, colors='#BDB8AD', linewidths=1.2, zorder=2))
for l in sorted(tp):
    ax.add_collection(LineCollection(tp[l], colors=KOL[l], linewidths=4.5, zorder=3, capstyle='round', alpha=0.9))
for k, nm in {'lubpkp': 'Lubliniec', 'kosr': 'Koszęcin', 'kalp': 'Kalety', 'bor': 'Boronów', 'pia': 'Piasek', 'lisp': 'Lisów', 'laz': 'Łazy', 'pil': 'Piłka', 'str': 'Strzebiń'}.items():
    x, y = P(S[k][1], S[k][0]); ax.text(x, y + 0.003, nm, fontsize=11, color='#4A4740', ha='center', va='bottom', fontweight='semibold', zorder=5)
# mniejsze miejscowości przy trasach: (lat, lon, nazwa, przesunięcie x, y w stopniach, wyrównanie)
MNIEJSZE = [(S['sad'][0], S['sad'][1], 'Sadów', 0, 0.003, 'center'), (S['wie'][0], S['wie'][1], 'Wierzbie', 0.004, 0.002, 'left'),
            (S['cie'][0], S['cie'][1], 'Cieszowa', 0.004, 0, 'left'), (50.62416, 18.87249, 'Prądy', 0.002, 0.003, 'left'),
            (S['buk'][0], S['buk'][1], 'Bukowiec', -0.002, 0.0045, 'center'), (S['bru'][0], S['bru'][1], 'Brusiek', -0.004, 0, 'right'),
            (S['rus'][0], S['rus'][1], 'Rusinowice', 0.004, -0.002, 'left'), (S['chw'][0], S['chw'][1], 'Chwostek', 0.004, 0, 'left')]
for lat, lon, nm, dx, dy, ha in MNIEJSZE:
    x, y = P(lon + dx, lat + dy)
    ax.scatter([P(lon, lat)[0]], [P(lon, lat)[1]], s=14, color='#6B675F', zorder=4.5, edgecolors='white', linewidths=0.8)
    ax.text(x, y, nm, fontsize=9, color='#5E5A52', ha=ha, va='center', zorder=5)
ax.scatter([kx0], [ky0], s=260, color=CIEMNY, zorder=6, edgecolors='white', linewidths=2.5)
import numpy as np
g = fig.add_axes([AX0, 0, 0.10, 1]); g.axis('off')
g.imshow(np.dstack([np.full((10, 100), c) for c in (0xF7 / 255, 0xF6 / 255, 0xF2 / 255)] + [np.tile(np.linspace(1, 0, 100), (10, 1))]), aspect='auto', extent=[0, 1, 0, 1])
fx = 0.035
fig.text(fx, 0.66, 'Busy Koszęcin', fontsize=42, fontweight='bold', color=CIEMNY)
fig.text(fx, 0.608, 'Propozycja połączeń busów dla całej gminy', fontsize=15, color='#3A3732')
for i, (l, t) in enumerate([('1', 'Piasek – Strzebiń – Koszęcin – Lubliniec, co godzinę'), ('2', 'Kalety – Koszęcin – Boronów'),
                            ('3', 'Lisów – Cieszowa – Koszęcin'), ('4', 'Łazy – Strzebiń – Koszęcin, co godzinę'),
                            ('5', 'Koszęcin – Rusinowice – Piłka – Sadów – Lubliniec')]):
    yy = 0.53 - i * 0.048
    fig.patches.append(matplotlib.patches.Ellipse((fx + 0.008, yy + 0.014), 0.032 * H / W, 0.032, transform=fig.transFigure, color=KOL[l], figure=fig))
    fig.text(fx + 0.008, yy + 0.013, l, fontsize=10, color='white', fontweight='bold', ha='center', va='center')
    fig.text(fx + 0.02, yy + 0.003, t, fontsize=12, color='#2E2C28')
fig.text(fx, 0.285, 'Propozycja inicjatywy Szprychy Koszęcin i mieszkańców – to nie jest obowiązujący rozkład jazdy', fontsize=11, color='#B3261E', fontweight='semibold')
fig.text(fx, 0.252, 'busy-koszecin.smart-ant.pl', fontsize=11, color='#5E5A52')
fig.savefig(f'{OUT}/tlo.png', dpi=100, facecolor=TLO); plt.close(fig)
print('ok')
