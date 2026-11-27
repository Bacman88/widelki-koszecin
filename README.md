# Szprychy Koszęcin – siatka busów gminy Koszęcin

Oddolna **propozycja nowej siatki busów gminy Koszęcin** (GTV) z węzłem przesiadkowym na **Koszęcin Rynek** i przesiadkami na kolej, a w kolejnym kroku **aplikacja „skąd – dokąd” dla mieszkańców** (busy gminne + Koleje Śląskie, PolRegio, PKP Intercity).

Projekt ma charakter **propozycji do dyskusji** z gminą. Czasy przejazdów są policzone (40 km/h + postój na przystanku), a nie zmierzone – przed wdrożeniem wymagają sprawdzenia w terenie.

**Gotowy dokument:** [`dokumenty/Siatka busów gmina Koszęcin – propozycja.pdf`](dokumenty/) – schemat linii, mapy, rozkłady, przykładowe dojazdy z każdej miejscowości, przesiadki na kolej, zakres przewozów.

## Siatka w skrócie

| Linia | Trasa | Częstotliwość |
|---|---|---|
| **1** | Piasek – Płaszczymąka – Bukowiec – Strzebiń Lubliniecka – Koszęcin Rynek – Rzyce Irki – Wierzbie – Sadów – Lubliniec PKP | co godzinę, cały dzień |
| **2** | Boronów – Koszęcin Rynek – Koszęcin Szkoła – Koszęcin PKP – Brusiek – Kalety PKP | co 2 h; w szczytach dodatkowe kursy Kalety – Brusiek – Rynek |
| **3** | Lisów PKP – Chwostek – Mochała – Hadra – Cieszowa – Koszęcin Rynek – Koszęcin Szkoła – Koszęcin PKP | co 2 h; w szczytach szkolnych co godzinę |
| **4** | Łazy – Strzebiń Szkoła – Strzebiń Lubliniecka – Koszęcin PKP – Koszęcin Szkoła – Koszęcin Rynek – Rzyce Irki – Wierzbie – Rusinowice PKP – Piłka | co 2 h; w szczytach w obie strony |

Takt w węźle Koszęcin Rynek: linie 2–4 przyjeżdżają o :49 i odjeżdżają o :03, linia 1 przejeżdża bez czekania. 6 autobusów przez cały dzień, 7 w szczytach. Propozycje poza siatką podstawową (linie przerywane): **1L** (wzmocnienie Rynek – Lubliniec w szczycie), **4L** (ewentualność: bezpośrednio Piłka – Rusinowice – Sadów – Lubliniec w dni nauki), **4S** (kursy szkolne do Psar), **4P** (pętla Łazy – Psary po utwardzeniu drogi).

## Co jest w środku

| Folder | Zawartość |
|---|---|
| `skrypty/` | cały proces: trasy → czasy → rozkład → planer dojazdów → mapy → raport → PDF |
| `dane/` | przystanki, podkład mapy (`baza.json`), granica gminy, schemat linii |
| `strona/mapa/` | interaktywna mapa linii (Leaflet) |
| `aplikacja/` | aplikacja dla mieszkańców – plan i (wkrótce) kod |
| `dokumenty/` | gotowy PDF propozycji |
| `symulacja/` | symulacja ruchu w SUMO: czy rozkład i przesiadki działają (wyniki w `symulacja/README.md`) |
| `fonts/` | krój Inter (SIL OFL) |

Wycinek OpenStreetMap całej gminy (`dane/osm/`, ok. 33 MB) nie jest trzymany w tym repozytorium – `skrypty/pobierz_dane.sh` pobiera go z [rowerowy-strzebin](https://github.com/Bacman88/rowerowy-strzebin).

## Jak przebudować

Wymagania: Python 3.10+, pakiety:

```bash
pip install networkx shapely matplotlib numpy reportlab pypdf
```

Przebudowa (wyniki w `out/`):

```bash
bash skrypty/rebuild.sh
```

| Skrypt | Co robi |
|---|---|
| `build.py` | prowadzi linie po drogach OSM, przystanki → `out/data.json` |
| `rozklad.py` | czasy przejazdu między przystankami → `out/rozklad_base.json` |
| `plan.py` | rozkład w takcie, warianty pełny / oszczędny, liczba busów → `out/rozklad_data.json` |
| `planer.py` | wyszukiwarka połączeń (connection scan) – przykładowe dojazdy do / z Lublińca |
| `mapa_pdf.py` | mapa ogólna i przybliżenie Koszęcina → `out/mapy.pdf` |
| `raport.py` + `raport2.py` | podsumowanie, rozkłady, przykłady, kolej, zakres → `out/raport.pdf` |
| `zloz_pdf.py` | składa PDF publiczny |

Kosztorys ze stawkami jest prywatny i nie jest częścią repozytorium.

## Licencje

Kod: MIT (plik `LICENSE`). Dane mapy © współtwórcy OpenStreetMap (ODbL). Krój Inter: SIL Open Font License. Rozkłady kolejowe (aplikacja): dane PKP PLK wg warunków ponownego wykorzystania informacji sektora publicznego, GTFS: Mikołaj Kuranowski (mkuran.pl).
