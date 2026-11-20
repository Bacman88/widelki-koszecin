"""Składa PDF publiczny (schemat + 2 mapy + strony raportu) i – jeśli są strony prywatne – PDF „dla mnie”."""
import os
from pypdf import PdfReader, PdfWriter

PUBLICZNE = 10  # stron raportu w PDF publicznym (podsumowanie … zakres przewozów)

m = PdfReader('out/mapy.pdf'); r = PdfReader('out/raport.pdf'); s = PdfReader('dane/schemat.pdf')
w = PdfWriter()
for p in [s.pages[0], m.pages[0], m.pages[1]] + list(r.pages[:PUBLICZNE]):
    w.add_page(p)
w.write('out/Siatka busów gmina Koszęcin – propozycja.pdf')
print('PDF publiczny:', len(w.pages), 'stron')
# wersja skrócona do druku (schemat + raport, bez map) – raport z numeracją od 2 (SKROT=1)
if os.path.exists('out/raport_skrot.pdf'):
    rs = PdfReader('out/raport_skrot.pdf'); w3 = PdfWriter()
    for p in [s.pages[0]] + list(rs.pages[:PUBLICZNE]): w3.add_page(p)
    w3.write('out/Siatka busów gmina Koszęcin – wersja do druku.pdf'); print('PDF do druku:', len(w3.pages), 'stron')
if len(r.pages) > PUBLICZNE:
    w2 = PdfWriter()
    for p in r.pages[PUBLICZNE:]:
        w2.add_page(p)
    w2.write('out/Siatka busów – kosztorys, uwagi i źródła (prywatne).pdf')
    print('PDF prywatny:', len(w2.pages), 'stron')
