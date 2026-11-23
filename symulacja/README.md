# Symulacja siatki busów w SUMO

Proponowana siatka busów gminy Koszęcin sprawdzona w **SUMO** (Simulation of Urban MObility, DLR): darmowym symulatorze ruchu używanym przy planowaniu transportu.

Model to **dzień roboczy, wariant pełny, 4:30–24:00**:
- **Drogi:** prawdziwe drogi z OpenStreetMap; 50 km/h w terenie zabudowanym, 90 km/h poza nim.
- **Przejazdy kolejowe:** 74 przejazdy z rogatkami. 4 z nich leżą na trasach busów: przy Lublińcu, w Lisowie, przy Rusinowicach i przy Boronowie.
- **Busy:** 91 kursów wg rozkładu z `out/rozklad_data.json`. Na przystanku stoją 20 s i nie odjeżdżają przed czasem. Na Rynku dojazdówki czekają do :03.
- **Pociągi:** na przejeździe przy Lublińcu ruch po wszystkich torach, łącznie ok. 9 pociągów na godzinę; co drugi to długi, wolny skład towarowy (600 m, 60 km/h). Na pozostałych przejazdach pociąg co godzinę w każdą stronę. To przybliżenie, nie rzeczywisty rozkład PKP.
- **Ruch tła:** ok. 40 tys. samochodów w ciągu dnia (`tlo.py`): najwięcej jazd wewnątrz Lublińca, mniej dojazdów do Lublińca i z niego, mało ruchu tranzytowego po DW906. W szczytach (6–8, 14–17) ruch ×1,6, w nocy ×0,25.

## Wyniki (23.11.2026)

| Linia, kierunek | Plan [min] | Symulacja [min] | Najw. spóźnienie na przystanku |
|---|---|---|---|
| 1 z Lublińca | 45 | 44,2 | +0,3 |
| 1 z Piasku | 45 | 39,7 | +0,8 |
| 2 z Boronowa | 51 | 44,8 | +0,4 |
| 2 z Kalet | 48,4 | 48,2 | +0,5 |
| 3 z Koszęcina PKP | 26 | 25,6 | 0 |
| 3 z Lisowa | 25 | 23,8 | +0,1 |
| 4 z Piłki | 57 | 57,0 | +1,6 |
| 4 z Łaz | 47 | 46,4 | +0,9 |

Kolumna „Symulacja” to czas od odjazdu z pierwszego przystanku do przyjazdu na ostatni. Busy nie odjeżdżają przed czasem, więc zapas zbiera się na końcu trasy.

**Przesiadki** (3 przebiegi: dwa ziarna losowe i jeden z podwójnym ruchem tła):

| Przesiadka | Wynik | Zapas |
|---|---|---|
| Rynek, dojazdówki 2–4 → linia 1 | 54/54 | wszystkie na czas |
| Strzebiń, linia 4 z Łaz → linia 1 do Lublińca | 11/11 | najmniej 1,9 min |
| Irki, linia 4 z Piłki → linia 1 do Lublińca | 10/10 | – |
| Irki, linia 1 z Lublińca → linia 4 do Piłki | 11/11 | – |

**Odcinki do obserwacji:**
- **Koszęcin PKP → Strzebiń Lubliniecka (linia 4 z Piłki):** symulacja pokazuje do 1,5 min więcej niż rozkład. Nie ma tam przesiadki, w której liczy się minuta.
- **Strzebiń Szkoła → Strzebiń Lubliniecka:** rozkład daje 1 min. Lewoskręt z Szkolnej w Lubliniecką zależy od ruchu na drodze głównej. Przy zbyt szybkich drogach (pierwsza wersja modelu) przesiadka na linię 1 o :45 się nie udawała. Warto sprawdzić w terenie albo przesunąć kurs z Łaz o 1–2 min wcześniej.

**Zapas na przejeździe kolejowym przed Lublińcem** (3 min w rozkładzie) wygląda na wystarczający. Przy ok. 9 pociągach na godzinę odcinek Sadów → Lubliniec PKP zajmuje 4,3–5,0 min (rozkład: 10 min), a w drugą stronę 4,5–6,8 min.

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
| `tlo.py` | ruch samochodów tła wg kierunków i pory dnia |
| `analiza.py`, `przesiadki.py` | porównanie z rozkładem, zapis do `wyniki/*.json` |

## Ograniczenia

Model jest dużo bliższy rzeczywistości niż gra, ale nadal opiera się na założeniach:
- **Pociągi i ruch samochodów** są przybliżone, a nie zmierzone.
- **Przystanki** to punkty na drodze, bez zatok. Na węzłach (Rynek, stacje) jest miejsce dla kilku busów.
- **Sygnalizacja świetlna:** wycinek OSM nie ma danych o światłach w Lublińcu, więc skrzyżowania działają na zasadzie pierwszeństwa.
- **Kierowcy** jeżdżą „modelowo”, bez korków przy szkołach i bez pasażerów kupujących bilety.

Najlepsze potwierdzenie to przejazd trasy w godzinach szczytu ze stoperem.
