"""Karuzela „Jak wypełnić ankietę w 4 krokach” (1080×1350, FB 4:5).
Zrzuty k1–k4.png robi /tmp/ank/zrzuty.py (Playwright, telefon 390 px ×3).
Uruchom: python3 ankieta_karuzela.py <katalog_zrzutów> → fb/karuzela/01…06.png"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ank'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'karuzela'); os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1350
TLO = (247, 246, 242); CIEMNY = (30, 29, 27); SZARY = (78, 74, 66); ZIEL = (0, 112, 79); ZOLTY = (245, 196, 0); CZERW = (179, 38, 30)
KOL = [(0, 112, 79), (31, 111, 214), (204, 138, 0), (212, 71, 58), (124, 58, 237)]
F = '/usr/share/fonts/opentype/inter/Inter-%s.otf'
def font(w, s): return ImageFont.truetype(F % w, s)


def baza():
    im = Image.new('RGB', (W, H), TLO); d = ImageDraw.Draw(im)
    for i, c in enumerate(KOL): d.rounded_rectangle((80 + i * 56, 70, 80 + i * 56 + 44, 80), 5, fill=c)
    d.text((80, H - 118), 'busy-koszecin.smart-ant.pl/ankieta', font=font('Bold', 34), fill=ZIEL)
    d.text((80, H - 66), 'Propozycja inicjatywy Widełki Koszęcin i mieszkańców – to nie jest obowiązujący rozkład jazdy', font=font('SemiBold', 19), fill=CZERW)
    return im, d


def pigulka(d, x, y, txt, fc, tc, fs=28):
    f = font('Bold', fs); w = d.textlength(txt, font=f)
    d.rounded_rectangle((x, y, x + w + 44, y + fs + 26), (fs + 26) // 2, fill=fc)
    d.text((x + 22, y + 11), txt, font=f, fill=tc)
    return x + w + 44


def tekst(d, x, y, linie, f, kol, odst):
    for l in linie: d.text((x, y), l, font=f, fill=kol); y += odst
    return y


def zrzut(im, sciezka, y0, y_max, gora=0, wys=None, szer=820):
    """Wycinek zrzutu (od piksela `gora`, `wys` pikseli) w zaokrąglonej karcie z cieniem."""
    z = Image.open(sciezka).convert('RGB')
    if wys: z = z.crop((0, gora, z.width, min(z.height, gora + wys)))
    s = szer / z.width; z = z.resize((szer, round(z.height * s)), Image.LANCZOS)
    if y0 + z.height > y_max: z = z.crop((0, 0, szer, y_max - y0))
    x0 = (W - szer) // 2
    cien = Image.new('L', (W, H), 0); ImageDraw.Draw(cien).rounded_rectangle((x0, y0 + 10, x0 + szer, y0 + z.height + 10), 34, fill=70)
    cien = cien.filter(ImageFilter.GaussianBlur(18)); im.paste((0, 0, 0), (0, 0), cien.point(lambda v: v // 2))
    m = Image.new('L', z.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, z.width - 1, z.height - 1), 30, fill=255)
    im.paste(z, (x0, y0), m)
    if z.height >= y_max - y0 - 2:   # ucięte – miękkie wygaszenie na dole
        g = Image.new('L', (szer + 60, 120)); gd = ImageDraw.Draw(g)
        for k in range(120): gd.line((0, k, szer + 60, k), fill=round(255 * (k / 119) ** 1.3))
        im.paste(TLO, (x0 - 30, y_max - 120), g)


# 1. okładka
im, d = baza()
pigulka(d, 80, 130, 'ANKIETA · 2–3 minuty', ZOLTY, CIEMNY)
y = tekst(d, 80, 240, ['Jak wypełnić', 'ankietę?'], font('Bold', 104), CIEMNY, 118)
y = tekst(d, 80, y + 30, ['4 proste kroki – i od razu widzisz,', 'czy bus pasuje do Twojej trasy.'], font('Regular', 40), SZARY, 56)
for i, (nr, t) in enumerate([('1', 'Kilka słów o Tobie'), ('2', 'Skąd, dokąd i o której'), ('3', 'Twoje połączenia'), ('4', 'Pojechałbyś?')]):
    yy = y + 70 + i * 104
    d.ellipse((80, yy, 152, yy + 72), fill=CIEMNY); d.text((116, yy + 36), nr, font=font('Bold', 38), fill='white', anchor='mm')
    d.text((180, yy + 36), t, font=font('SemiBold', 42), fill=CIEMNY, anchor='lm')
d.text((W - 80, H - 170), 'przesuń →', font=font('SemiBold', 30), fill=SZARY, anchor='rm')
im.save(f'{OUT}/01.png')

KROKI = [
    ('k1.png', 'Kilka słów o Tobie', ['Kim jesteś, ile masz lat i gdzie', 'mieszkasz. Bez imienia i nazwiska.'], 0, None),
    ('k2.png', 'Skąd, dokąd i o której', ['Wybierz przystanek, cel i godzinę,', 'o której musisz być na miejscu.'], 0, None),
    ('k3.png', 'Twoje połączenia', ['Od razu widzisz busy (i pociągi),', 'którymi byś pojechał – i wrócił.'], 0, 1500),
    ('k4.png', 'Pojechałbyś?', ['Tak albo nie, bo… – kilka krótkich', 'pytań i przycisk „Wyślij”. Gotowe!'], 0, 1450),
]
for n, (plik, tyt, opis, gora, wys) in enumerate(KROKI, 1):
    im, d = baza()
    pigulka(d, 80, 120, f'KROK {n} z 4', CIEMNY, (255, 255, 255), 26)
    d.text((80, 196), tyt, font=font('Bold', 64), fill=CIEMNY)
    y = tekst(d, 80, 286, opis, font('Regular', 36), SZARY, 50)
    zrzut(im, f'{SRC}/{plik}', y + 34, H - 150, gora, wys)
    im.save(f'{OUT}/{n + 1:02d}.png')

# 6. zakończenie
im, d = baza()
pigulka(d, 80, 130, 'ANKIETA · 2–3 minuty', ZOLTY, CIEMNY)
y = tekst(d, 80, 250, ['A Twoja', 'trasa?'], font('Bold', 110), CIEMNY, 124)
y = tekst(d, 80, y + 30, ['Im więcej odpowiedzi, tym lepiej widać,', 'gdzie i o której busy są naprawdę', 'potrzebne.'], font('Regular', 40), SZARY, 56)
y = tekst(d, 80, y + 40, ['Liczy się też głos osób,', 'które dziś busem nie jeżdżą.'], font('SemiBold', 40), CIEMNY, 56)
d.rounded_rectangle((80, y + 60, W - 80, y + 190), 28, fill=ZIEL)
d.text((W // 2, y + 125), 'Wypełnij ankietę →', font=font('Bold', 52), fill='white', anchor='mm')
im.save(f'{OUT}/06.png')
print('ok', OUT)
