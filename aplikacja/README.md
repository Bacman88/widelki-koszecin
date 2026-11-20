# Aplikacja „skąd – dokąd” dla mieszkańców gminy Koszęcin

Cel: mieszkaniec wpisuje **skąd, dokąd i na którą**, a aplikacja podaje gotowe połączenie z przesiadkami, np. *„5:36 linia 4 z Łaz, w Strzebiniu linia 1, Lubliniec PKP 6:20”*.

## Założenia

- **Strona do zainstalowania na telefonie (PWA):** działa offline, bez sklepu Google Play. Później opcjonalnie APK budowany automatycznie (jak w rowerowy-strzebin).
- **Dwa tryby rozkładu:** *dziś* (obecny rozkład GTV) i *propozycja* (siatka z tego repozytorium, wyraźnie oznaczona) – można porównać, jak zmienia się dojazd.
- **Kolej z węzłów:** Koszęcin, Strzebiń, Lisów, Rusinowice, Kalety, Boronów, Lubliniec, a dalej Tarnowskie Góry, Częstochowa, Katowice.
- **Wyszukiwarka w przeglądarce:** algorytm connection scan (ten sam co `skrypty/planer.py`), na małym pliku danych – bez serwera.

## Źródła danych

| Przewoźnik | Źródło |
|---|---|
| busy gminne (propozycja) | `out/rozklad_data.json` z tego repozytorium |
| busy gminne (dziś) | rozkład GTV – do pozyskania z gminy / przepisania z tabliczek |
| Koleje Śląskie, PolRegio, PKP Intercity | GTFS „polish_trains” (mkuran.pl) albo GTFS Kolei Śląskich (aktualizacja przy zmianie rozkładu w grudniu) |

Raz na dobę akcja GitHub pobiera GTFS, wycina stacje z okolicy i zapisuje mały plik dla aplikacji.

## Plan prac

1. Format danych aplikacji (przystanki, kursy, przesiadki piesze, np. Rynek ↔ Szkoła 450 m).
2. Eksport rozkładu busów do tego formatu + wycinek GTFS kolei.
3. Wyszukiwarka i widok „odjazdy z przystanku”.
4. PWA (offline, ikona na ekranie), hosting na smart-ant.pl.
5. Tryb „dziś” po pozyskaniu aktualnego rozkładu GTV.
