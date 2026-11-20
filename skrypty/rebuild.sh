#!/usr/bin/env bash
# Przebudowa wszystkiego: trasy → rozkład → planer → mapy PDF → raport → PDF publiczny. Wyniki w out/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p out
bash skrypty/pobierz_dane.sh
python3 skrypty/build.py          # trasy po drogach OSM, przystanki → out/data.json
python3 skrypty/rozklad.py        # czasy przejazdów między przystankami → out/rozklad_base.json
python3 skrypty/plan.py           # rozkład w takcie, warianty pełny/oszczędny → out/rozklad_data.json
python3 skrypty/planer.py > out/dojazdy.txt   # przykładowe dojazdy do / z Lublińca
python3 skrypty/mapa_pdf.py       # mapy → out/mapy.pdf
python3 skrypty/raport.py         # rozkłady, przykłady, zakres → out/raport.pdf
SKROT=1 python3 skrypty/raport.py && mv out/raport.pdf out/raport_skrot.pdf && python3 skrypty/raport.py   # wersja do druku (numeracja bez map)
python3 skrypty/zloz_pdf.py       # PDF publiczny (+ prywatny, jeśli są skrypty prywatne)
cp out/data.json strona/mapa/data.json
