# Symulacja siatki busów w SUMO

Proponowana siatka busów gminy Koszęcin sprawdzona w **SUMO** (Simulation of Urban MObility, DLR): darmowym symulatorze ruchu używanym przy planowaniu transportu.

Model to **dzień roboczy, wariant pełny, 4:30–24:00**:
- **Drogi:** prawdziwe drogi z OpenStreetMap; 50 km/h w terenie zabudowanym, 90 km/h poza nim.
- **Przejazdy kolejowe:** 74 przejazdy z rogatkami. 4 z nich leżą na trasach busów: przy Lublińcu, w Lisowie, przy Rusinowicach i przy Boronowie.
- **Busy:** 91 kursów wg rozkładu z `out/rozklad_data.json`. Na zwykłych przystankach stoją 10 s. Irki, Płaszczymąka i Prądy to przystanki na żądanie: bus staje tam tylko czasem (Irki ok. 4 razy na dobę, Płaszczymąka 14, Prądy 8), na 6 s. Prądy (linie 1 i 4) nie ma w rozkładzie projektu; czas przejazdu liczony proporcjonalnie do odległości. Na czas z rozkładu czekają tylko w węzłach z zatoką (Rynek, stacje, Strzebiń, Lubliniec PKP); na Rynku dojazdówki czekają do :03.
- **Pociągi:** na przejeździe przy Lublińcu ruch po wszystkich torach, łącznie ok. 9 pociągów na godzinę; co drugi to długi, wolny skład towarowy (600 m, 60 km/h). Na pozostałych przejazdach pociąg co godzinę w każdą stronę. To przybliżenie, nie rzeczywisty rozkład PKP.
- **Ruch tła:** dobrany do pomiarów ruchu (średni dobowy ruch roczny): GPR 2020 na drogach wojewódzkich (ZDW Katowice) i GPR 2020/21 na drogach krajowych (GDDKiA). 18 punktów pomiarowych na DW906, DW907, DW905, DW908, DW789, DK11 i DK46; `routeSampler` z SUMO dobiera trasy aut tak, żeby w każdej godzinie zgadzały się z pomiarem (szczyty 6–8 i 14–17). Ok. 51 tys. aut na dobę, głównie po drogach z pomiarami. Porównanie pomiar/symulacja: `wyniki/kalibracja.json` – na większości punktów różnica do 5%, za mało aut na DK11 (obwodnica Lublińca), DW907 Brusiek – Tworóg i DW908 Kamienica – Piasek (punkty przy brzegu mapy). Ulice osiedlowe nie są mierzone.
- **Skrzyżowania:** 26 skrzyżowań na trasach busów rozbitych w OSM na kilka węzłów (np. Wierzbie, Główna × Cieszowska) jest sklejonych w jedno (`skrzyzowania.py` → `zlacz.nod.xml`).

## Wyniki (23.11.2026, wersja z przystankami na żądanie i ruchem wg korytarzy)

| Linia, kierunek | Plan [min] | Symulacja [min] | Najw. spóźnienie |
|---|---|---|---|
| 1 z Lublińca | 45 | 41,7 | 0 |
| 1 z Piasku | 45 | 32,0 | 0 |
| 2 z Boronowa | 51 | 41,2 | +0,1 |
| 2 z Kalet | 48,4 | 44,2 | 0 |
| 3 z Koszęcina PKP | 26 | 19,1 | 0 |
| 3 z Lisowa | 25 | 23,5 | +0,7 |
| 4 z Piłki | 57 | 55,5 | 0 |
| 4 z Łaz | 47 | 40,6 | 0 |

**Przesiadki:** Rynek 54/54; Strzebiń, linia 4 z Łaz → linia 1 do Lublińca 11/11 (zapas min. 2,2 min); Strzebiń, linia 1 → linia 4 do Łaz 10/10.

**Wnioski:**
- Rozkład ma duże zapasy. Linia 1 z Piasku jedzie w symulacji ok. 13 min szybciej niż w planie, więc czeka ok. 3,5 min w Strzebiniu. Rozkład zakłada 40 km/h i 45 s na każdym przystanku; symulacja nie liczy wsiadania pasażerów ani pogody, więc jest optymistyczna. Przed skróceniem rozkładu warto przejechać trasę ze stoperem.
- Dojazdówki stoją na Rynku od :49 do :03 (ok. 14 min). To założenie pulsu, nie efekt korków.
- W Strzebiniu przy Lublinieckiej potrzebna jest zatoka: czekająca linia 1 stojąca na jezdni blokowała dojazd linii 4 i przesiadka się nie udawała.
- Przy ruchu z pomiarów odcinek Sadów → Wierzbie trwa do 7 min (rozkład: 5); bus traci czas na skręcie z DW906 do Wierzbia. Opóźnienie odrabia do Koszęcina.
- Najciaśniejsze odcinki rozkładu (Lisów PKP → Chwostek, Płaszczymąka → Piasek) przekraczają plan o mniej niż 1 min.

## Jak obejrzeć u siebie

1. Zainstaluj SUMO: https://sumo.dlr.de/docs/Downloads.php (Windows: instalator .msi).
2. Pobierz folder `symulacja/` z repozytorium.
3. Kliknij dwukrotnie `koszecin.sumocfg`, otworzy się **sumo-gui**.
4. Kliknij ▶. Widok startuje na Rynku w Koszęcinie. Kolory: zielony = linia 1, niebieski = 2, żółty = 3, czerwony = 4, szary = pociągi.
5. Czas symulacji to sekundy od północy: 6:00 = 21600, 7:00 = 25200, 15:00 = 54000.

Wyniki zapisują się do `wyniki/przystanki.xml` (każdy przyjazd i odjazd z przystanku) i `wyniki/kursy.xml`.

## Przebudowa od zera

```bash
pip install eclipse-sumo pyproj rtree shapely
bash skrypty/rebuild.sh          # (w katalogu głównym repo) dane siatki w out/
bash symulacja/zbuduj.sh         # sieć, kursy, pociągi, ruch tła, symulacja, analiza
```

| Plik | Co robi |
|---|---|
| `osm_z_geojson.py` | wycinek OSM gminy → plik OSM dla netconvert (drogi, tory, przejazdy) |
| `teren_zabudowany.py` | ograniczenia prędkości 50/90 km/h |
| `scenariusz.py` | przystanki i kursy busów z rozkładu (trasy z projektu, te same węzły OSM) |
| `pociagi.py` | pociągi przez przejazdy na trasach busów |
| `tlo.py` | ruch samochodów tła dobrany do pomiarów GPR |
| `kalibracja.py` | pomiar GPR vs ruch w symulacji na punktach pomiarowych |
| `skrzyzowania.py` | skleja skrzyżowania rozbite w OSM (→ `zlacz.nod.xml`) |
| `analiza.py`, `przesiadki.py` | porównanie z rozkładem, zapis do `wyniki/*.json` |

## Ograniczenia

Model jest dużo bliższy rzeczywistości niż gra, ale nadal opiera się na założeniach:
- **Pociągi i ruch samochodów** są przybliżone, a nie zmierzone.
- **Przystanki** to punkty na drodze, bez zatok. Na węzłach (Rynek, stacje) jest miejsce dla kilku busów.
- **Sygnalizacja świetlna:** wycinek OSM nie ma danych o światłach w Lublińcu, więc skrzyżowania działają na zasadzie pierwszeństwa.
- **Kierowcy** jeżdżą „modelowo”, bez korków przy szkołach i bez pasażerów kupujących bilety.

Najlepsze potwierdzenie to przejazd trasy w godzinach szczytu ze stoperem.
