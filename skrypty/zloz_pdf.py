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
if len(r.pages) > PUBLICZNE:
    w2 = PdfWriter()
    for p in r.pages[PUBLICZNE:]:
        w2.add_page(p)
    w2.write('out/Siatka busów – kosztorys, uwagi i źródła (prywatne).pdf')
    print('PDF prywatny:', len(w2.pages), 'stron')
