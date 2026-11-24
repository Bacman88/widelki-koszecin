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
KOL = {'1': '#00704F', '2': '#1F6FD6', '3': '#CC8A00', '4': '#D4473A'}
TLO = '#F7F6F2'; CIEMNY = '#1E1D1B'
OUT = '../fb'

# --- zdjęcie profilowe: węzeł z 4 liniami ---
fig = plt.figure(figsize=(7.2, 7.2), dpi=100, facecolor=TLO)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_aspect('equal'); ax.axis('off')
ax.add_patch(plt.Circle((0, 0), 1, color=TLO))
kat = {'1': 145, '2': 35, '3': 270, '4': 325}
DY = 0.08
for l, a in kat.items():
    x, y = 0.56 * math.cos(math.radians(a)), 0.56 * math.sin(math.radians(a)) + DY
    ax.plot([0, x], [DY, y], color=KOL[l], lw=26, solid_capstyle='round', zorder=1)
    ax.add_patch(plt.Circle((x, y), 0.17, color=KOL[l], zorder=3, ec='white', lw=5))
    ax.text(x, y - 0.005, l, color='white', fontsize=54, fontweight='bold', ha='center', va='center', zorder=4)
ax.add_patch(plt.Circle((0, DY), 0.25, color=CIEMNY, zorder=5, ec='white', lw=7))
ax.text(0, DY + 0.035, 'BUSY', color='white', fontsize=27, fontweight='bold', ha='center', va='center', zorder=6)
ax.text(0, DY - 0.085, 'Koszęcin', color='#E8E4DA', fontsize=17, ha='center', va='center', zorder=6)
fig.savefig(f'{OUT}/profilowe.png', dpi=100, facecolor=TLO); plt.close(fig)

# --- zdjęcie w tle: mapa siatki + napis ---
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
W, H = 1640, 624
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=TLO)
ax = fig.add_axes([0.46, 0, 0.54, 1]); ax.set_facecolor(TLO); ax.axis('off')
allp = [p for l in tp.values() for s in l for p in s]
xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
hy = (max(ys) - min(ys)) / 2 * 1.16; hx = hy * (0.54 * W) / H
cx -= hx * 0.06
ax.set_xlim(cx - hx, cx + hx); ax.set_ylim(cy - hy, cy + hy)
ax.fill([P(*c)[0] for c in gmina], [P(*c)[1] for c in gmina], color='#EAE7DF', lw=0, zorder=0)
ax.add_collection(LineCollection(drogi, colors='#DEDAD1', linewidths=0.5, zorder=1))
ax.add_collection(LineCollection(glowne, colors='#BDB8AD', linewidths=1.2, zorder=2))
for l in sorted(tp):
    ax.add_collection(LineCollection(tp[l], colors=KOL[l], linewidths=4.5, zorder=3, capstyle='round', alpha=0.9))
s = open('../skrypty/build.py').read()
S = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(r"'(\w+)':\(([\d.]+),([\d.]+),'", s)}
for k, nm in {'lubpkp': 'Lubliniec', 'kosr': 'Koszęcin', 'kalp': 'Kalety', 'bor': 'Boronów', 'pia': 'Piasek', 'lisp': 'Lisów', 'laz': 'Łazy', 'pil': 'Piłka', 'str': 'Strzebiń'}.items():
    x, y = P(S[k][1], S[k][0]); ax.text(x, y + 0.004, nm, fontsize=11, color='#4A4740', ha='center', va='bottom', fontweight='semibold', zorder=5)
x, y = P(S['kosr'][1], S['kosr'][0])
ax.scatter([x], [y], s=260, color=CIEMNY, zorder=6, edgecolors='white', linewidths=2.5)
# gradient przejścia tekst → mapa
import numpy as np
g = fig.add_axes([0.46, 0, 0.08, 1]); g.axis('off')
g.imshow(np.dstack([np.full((10, 100), c) for c in (0xF7 / 255, 0xF6 / 255, 0xF2 / 255)] + [np.tile(np.linspace(1, 0, 100), (10, 1))]), aspect='auto', extent=[0, 1, 0, 1])
fx = 0.135
fig.text(fx, 0.66, 'Busy Koszęcin', fontsize=50, fontweight='bold', color=CIEMNY)
fig.text(fx, 0.54, 'Propozycja siatki busów dla całej gminy', fontsize=21, color='#3A3732')
for i, (l, t) in enumerate([('1', 'co godzinę do Lublińca'), ('2', 'Kalety – Boronów'), ('3', 'Lisów – Cieszowa'), ('4', 'Łazy – Strzebiń – Piłka')]):
    xx = fx + (i % 2) * 0.18; yy = 0.40 - (i // 2) * 0.085
    fig.patches.append(matplotlib.patches.Ellipse((xx + 0.009, yy + 0.022), 0.04 * H / W, 0.04 * 1, transform=fig.transFigure, color=KOL[l], figure=fig))
    fig.text(xx + 0.009, yy + 0.021, l, fontsize=12, color='white', fontweight='bold', ha='center', va='center')
    fig.text(xx + 0.025, yy + 0.008, t, fontsize=13.5, color='#2E2C28')
fig.text(fx, 0.13, 'Wszystkie linie spotykają się na Rynku w Koszęcinie\nbusy-koszecin.smart-ant.pl', fontsize=12, linespacing=1.5, color='#5E5A52')
fig.text(fx, 0.065, 'Propozycja mieszkańców – to nie jest obowiązujący rozkład jazdy', fontsize=12, color='#B3261E', fontweight='semibold')
fig.savefig(f'{OUT}/tlo.png', dpi=100, facecolor=TLO); plt.close(fig)
print('ok')
