"""Własna, spokojna muzyka do filmu (30 s) – generowana od zera, bez praw autorskich osób trzecich.
Akordy Cmaj7 – Am7 – Fmaj7 – G6 (80 BPM), miękka plama syntezatora, delikatne arpeggio i cichy szum ulicy."""
import numpy as np, wave
SR = 44100; DL = 30.0; N = int(SR * DL)
t = np.arange(N) / SR
def nuta(n): return 440 * 2 ** ((n - 69) / 12)
def lp(x, a):        # filtr dolnoprzepustowy 1. rzędu
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y
AKORDY = [[48, 55, 59, 64], [45, 52, 55, 60], [41, 48, 52, 57], [43, 50, 55, 59]]   # C maj7, A m7, F maj7, G6
TAKT = 3.0
plama = np.zeros(N); arp = np.zeros(N)
for k in range(int(DL / TAKT) + 1):
    t0 = k * TAKT; ak = AKORDY[k % 4]
    i0, i1 = int(t0 * SR), min(N, int((t0 + TAKT + 1.0) * SR))
    if i0 >= N: break
    tt = np.arange(i1 - i0) / SR
    env = np.minimum(1, tt / 0.8) * np.exp(-np.maximum(0, tt - TAKT) * 3)
    for n in ak:
        f = nuta(n + 12)
        plama[i0:i1] += env * (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.003 * tt) + 0.3 * np.sin(2 * np.pi * f * 0.997 * tt + 1))
    # arpeggio: 6 nut na takt
    for j in range(6):
        n = ak[[0, 1, 2, 3, 2, 1][j]] + 24
        s0 = int((t0 + j * TAKT / 6) * SR); s1 = min(N, s0 + int(1.6 * SR))
        if s0 >= N: break
        ts = np.arange(s1 - s0) / SR
        arp[s0:s1] += np.exp(-ts * 3.2) * (np.sin(2 * np.pi * nuta(n) * ts) + 0.25 * np.sin(4 * np.pi * nuta(n) * ts)) * (0.6 if j else 0.8)
plama = lp(plama, 0.05)
# „miasto w tle”: cichy, ciepły szum z wolnym falowaniem
rng = np.random.default_rng(3)
szum = lp(lp(rng.standard_normal(N), 0.02), 0.05) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 9))
mix = 0.16 * plama / np.max(np.abs(plama)) + 0.22 * arp / np.max(np.abs(arp)) + 0.10 * szum / np.max(np.abs(szum))
# proste echo
d = int(0.375 * SR); echo = np.zeros(N); echo[d:] = mix[:-d] * 0.3; mix = mix + echo
fade = np.minimum(1, t / 2.0) * np.minimum(1, (DL - t) / 3.0)
mix = mix * fade; mix = mix / np.max(np.abs(mix)) * 0.8
st = np.stack([mix, np.roll(mix, int(0.012 * SR))], 1)
with wave.open('muzyka.wav', 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('ok')
