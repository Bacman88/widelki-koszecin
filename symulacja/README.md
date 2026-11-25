# Symulacja siatki busów w SUMO

Proponowana siatka busów gminy Koszęcin sprawdzona w **SUMO** (Simulation of Urban MObility, DLR): otwartym (open source) symulatorze ruchu używanym przy planowaniu transportu.

Model to **dzień roboczy, wariant pełny, 4:30–24:00**:
- **Drogi:** prawdziwe drogi z OpenStreetMap; 50 km/h w terenie zabudowanym, 90 km/h poza nim.
- **Przejazdy kolejowe:** 74 przejazdy z rogatkami. 4 z nich leżą na trasach busów: przy Lublińcu, w Lisowie, przy Rusinowicach i przy Boronowie.
- **Busy:** 91 kursów wg rozkładu z `out/rozklad_data.json`. Na zwykłych przystankach stoją 10 s. Irki, Płaszczymąka i Prądy to przystanki na żądanie: bus staje tam tylko czasem (Irki ok. 4 razy na dobę, Płaszczymąka 14, Prądy 8), na 6 s. Prądy (linie 1 i 4) nie ma w rozkładzie projektu; czas przejazdu liczony proporcjonalnie do odległości. Na czas z rozkładu czekają tylko w węzłach z zatoką (Rynek, stacje, Strzebiń, Lubliniec PKP); na Rynku dojazdówki czekają do :03.
- **Pociągi pasażerskie wg rozkładu 2026/27** (od 13.12.2026, dzień roboczy): Koleje Śląskie i POLREGIO na liniach 131 (Herby – Boronów – Strzebiń – Kalety), 143 (S8 Lubliniec – Rusinowice – Koszęcin – Kalety) i 61 (Lubliniec – Kochanowice – Lisów – Częstochowa). Źródło: oficjalny rozkład PKP PLK 2026/27 w formacie GTFS (polish_trains, mkuran.pl), wycinek pobierany co tydzień akcją GitHub „Rozkład kolejowy” do `dane/kolej/pociagi.json` (gałąź `kolej-dane`); `pociagi.py` bierze z niego dzień roboczy 14.12.2026. Pociągi przejeżdżają przelotowo, na każdej stacji stoją 30 s; w symulacji trzymają rozkład z dokładnością ok. ±1 min. Każdy kierunek jedzie swoim torem tam, gdzie szlak jest dwutorowy (`pociagi.py`, `stacje.add.xml`). **Towarowe** (600 m) – szacunek: 131 i 143 co godzinę w każdą stronę, 61 i 152 co 2 godziny. Bez PKP Intercity (nie zatrzymują się na stacjach w gminie).
- **Ruch tła:** dobrany do pomiarów ruchu (średni dobowy ruch roczny): GPR 2020 na drogach wojewódzkich (ZDW Katowice) i GPR 2020/21 na drogach krajowych (GDDKiA). 18 punktów pomiarowych na DW906, DW907, DW905, DW908, DW789, DK11 i DK46; `routeSampler` z SUMO dobiera trasy aut tak, żeby w każdej godzinie zgadzały się z pomiarem (szczyty 6–8 i 14–17). Ok. 51 tys. aut na dobę, głównie po drogach z pomiarami. Porównanie pomiar/symulacja: `wyniki/kalibracja.json` – na większości punktów różnica do 5%, za mało aut na DK11 (obwodnica Lublińca), DW907 Brusiek – Tworóg i DW908 Kamienica – Piasek (punkty przy brzegu mapy). Ulice osiedlowe nie są mierzone.
- **Koszęcin Rynek:** w stronę południa zatoka za skrzyżowaniem z Placem Kościuszki, w stronę północy zatoka przy placu między Placem Kościuszki a Boronowską (ok. 37 m, 3 busy). Drogi wewnętrzne na posesjach przy Rynku usunięte.
- **Przejazdy kolejowe:** przejazd przez kilka torów to jeden przejazd (`przejazdy.py`; wcześniej każdy tor był osobnym przejazdem i auta stawały między torami). Rogatki zamykają się 60 s przed pociągiem, w Lublińcu 120 s, i otwierają 15 s po nim (`przejazdy.add.xml`).
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

**Przesiadki:** Rynek 54/54 (w zatoce w stronę północy stoją naraz najwyżej 3 busy, czyli tyle, ile się mieści); Strzebiń, linia 4 z Łaz → linia 1 do Lublińca 11/11 (zapas min. 2,2 min); Strzebiń, linia 1 → linia 4 do Łaz 10/10.

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
| `przesiadki_kolej.py` | przesiadki bus ↔ pociąg na stacjach (3–20 min) → `wyniki/przesiadki_kolej.json` |
| `przejazdy.py` | jeden przejazd przez kilka torów, czasy rogatek (→ `przejazdy.add.xml`) |
| `skrzyzowania.py` | skleja skrzyżowania rozbite w OSM (→ `zlacz.nod.xml`) |
| `analiza.py`, `przesiadki.py` | porównanie z rozkładem, zapis do `wyniki/*.json` |

## Ograniczenia

Model jest dużo bliższy rzeczywistości niż gra, ale nadal opiera się na założeniach:
- **Pociągi i ruch samochodów** są przybliżone, a nie zmierzone.
- **Przystanki** to punkty na drodze, bez zatok. Na węzłach (Rynek, stacje) jest miejsce dla kilku busów.
- **Sygnalizacja świetlna:** wycinek OSM nie ma danych o światłach w Lublińcu, więc skrzyżowania działają na zasadzie pierwszeństwa.
- **Kierowcy** jeżdżą „modelowo”, bez korków przy szkołach i bez pasażerów kupujących bilety.

Najlepsze potwierdzenie to przejazd trasy w godzinach szczytu ze stoperem.

## Film (widok całej sieci)

`film.py` rysuje film z przebiegu symulacji: busy w kolorach linii, pociągi, odcinki z wolnym ruchem i zegar. Wynik to `wyniki/film.mp4` (H.264, 1280×720, ok. 0,6 MB, 30 s = poranek 5:30–10:30) i kadr `wyniki/film_kadr.png`. Film jest na stronie busy-koszecin.smart-ant.pl, w sekcji „Symulacja ruchu”.

Przebieg z zapisem pozycji (busy i pociągi co 10 s, prędkości na drogach co 2 min):

```bash
sed 's#guiShape="bus"/>#guiShape="bus"><param key="has.fcd.device" value="true"/></vType>#' busy.rou.xml > /tmp/busy_fcd.rou.xml
sed -E 's#(<vType id="(pociag|towarowy)"[^>]*)/>#\1><param key="has.fcd.device" value="true"/></vType>#' pociagi.rou.xml > /tmp/pociagi_fcd.rou.xml
echo '<additional><edgeData id="ed" period="120" file="/tmp/ed120.xml" excludeEmpty="true"/></additional>' > /tmp/ed.add.xml
sumo -c koszecin.sumocfg -r /tmp/pociagi_fcd.rou.xml,/tmp/busy_fcd.rou.xml,tlo.rou.xml.gz \
  -a przystanki.add.xml,przejazdy.add.xml,/tmp/ed.add.xml --end 37800 \
  --fcd-output /tmp/fcd.xml --device.fcd.probability 0 --device.fcd.period 10 --fcd-output.geo true
python3 film.py 5.5 10.5
```
