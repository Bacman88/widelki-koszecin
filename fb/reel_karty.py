"""Plansze do Reelsa (1080×1920): otwierająca i końcowa z zachętą do ankiety.
Uruchom z katalogu fb/: python3 reel_karty.py → reel_start.png, reel_ankieta.png"""
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib import font_manager as fm
import numpy as np
for f in fm.findSystemFonts():
    if 'Inter' in f: fm.fontManager.addfont(f)
plt.rcParams['font.family'] = ['Inter', 'DejaVu Sans']
TLO = '#F7F6F2'; CIEMNY = '#1E1D1B'; ZIEL = '#00704F'; ZOLTY = '#F5C400'; CZERW = '#B3261E'
KOL = ['#00704F', '#1F6FD6', '#CC8A00', '#D4473A', '#7C3AED']
W, H = 1080, 1920


def plansza():
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=TLO)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    # ciemne pasy u góry i u dołu jak w filmie (strefy, które zasłania interfejs Reelsów)
    for y0, y1, odwr in ((H - 90, H, False), (0, 330, True)):
        g = np.linspace(1, 0, 100)[:, None] if not odwr else np.linspace(0, 1, 100)[:, None]
        ax.imshow(np.dstack([np.full((100, 2), 0x1E / 255)] * 3 + [g ** 1.6 * np.ones((100, 2))]),
                  extent=[0, W, y0, y1], aspect='auto', zorder=5)
    # pasek z kolorami linii
    for i, c in enumerate(KOL):
        ax.add_patch(Rectangle((90 + i * 60, 1600), 48, 12, color=c, lw=0))
    return fig, ax


def pigulka(ax, x, y, txt, fc, tc, fs, pad=26):
    t = ax.text(x, y, txt, fontsize=fs, fontweight='bold', color=tc, ha='left', va='center', zorder=3)
    t.set_bbox(dict(boxstyle=f'round,pad=0.45,rounding_size=0.9', fc=fc, ec='none'))
    return t


# --- otwierająca ---
fig, ax = plansza()
ax.text(90, 1450, 'Pojechałbyś', fontsize=92, fontweight='bold', color=CIEMNY, va='center')
ax.text(90, 1310, 'busem?', fontsize=92, fontweight='bold', color=CIEMNY, va='center')
ax.text(90, 1080, 'Zobacz przykładowe połączenia\nw proponowanej siatce busów\ngminy Koszęcin', fontsize=34, color='#3A3732', va='center', linespacing=1.4)
pigulka(ax, 90, 900, 'symulacja ruchu · dzień roboczy', '#EAE7DF', '#3A3732', 26)
ax.text(90, 440, 'Propozycja inicjatywy Widełki Koszęcin i mieszkańców –\nto nie jest obowiązujący rozkład jazdy', fontsize=22, color=CZERW, fontweight='bold', va='center', linespacing=1.4)
fig.savefig('reel_start.png', dpi=100, facecolor=TLO); plt.close(fig)

# --- końcowa: ankieta ---
fig, ax = plansza()
pigulka(ax, 90, 1530, 'ANKIETA · 2–3 minuty', ZOLTY, CIEMNY, 30)
ax.text(90, 1380, 'A Twoja trasa?', fontsize=88, fontweight='bold', color=CIEMNY, va='center')
ax.text(90, 1110, 'Wpisz, skąd i dokąd jeździsz\ni o której. Od razu zobaczysz\nswoje połączenie i ocenisz,\nczy byś nim pojechał.', fontsize=36, color='#3A3732', va='center', linespacing=1.4)
# karta „połączenia” jak w ankiecie
ax.add_patch(FancyBboxPatch((90, 720), 900, 200, boxstyle='round,pad=0,rounding_size=28', fc='white', ec='#E2DED4', lw=2, zorder=2))
ax.text(130, 875, 'Twoja trasa, Twoja godzina', fontsize=24, color='#6B675F', va='center', zorder=3)
pigulka(ax, 130, 785, '✓  Tak, pojechałbym', '#E7F2D8', ZIEL, 28)
pigulka(ax, 560, 785, 'Nie, bo…', '#F1EFEA', CIEMNY, 28)
ax.text(90, 630, 'busy-koszecin.smart-ant.pl/ankieta', fontsize=36, fontweight='bold', color=ZIEL, va='center')
ax.text(90, 555, 'Liczy się też głos osób, które dziś busem nie jeżdżą.', fontsize=26, color='#3A3732', va='center')
ax.text(90, 440, 'Propozycja inicjatywy Widełki Koszęcin i mieszkańców –\nto nie jest obowiązujący rozkład jazdy', fontsize=22, color=CZERW, fontweight='bold', va='center', linespacing=1.4)
fig.savefig('reel_ankieta.png', dpi=100, facecolor=TLO); plt.close(fig)
print('ok')
