#!/usr/bin/env bash
# Przebudowa scenariusza SUMO od zera (sieć z OSM, przystanki, kursy, pociągi, ruch tła) i uruchomienie symulacji.
# Wymaga: pip install eclipse-sumo pyproj rtree shapely  (oraz wcześniej: bash skrypty/rebuild.sh – dane w out/)
set -euo pipefail
cd "$(dirname "$0")"
export SUMO_HOME="${SUMO_HOME:-$(python3 -c 'import sumo;print(sumo.SUMO_HOME)')}"
B="$SUMO_HOME/bin"; T="$SUMO_HOME/data/typemap"
GJ=../dane/osm/osm_gmina.geojson
python3 osm_z_geojson.py $GJ koszecin.osm
"$B/netconvert" --osm-files koszecin.osm --type-files $T/osmNetconvert.typ.xml,$T/osmNetconvertRailUsage.typ.xml \
  --geometry.remove --roundabouts.guess --ramps.guess --tls.guess-signals --tls.discard-simple \
  --railway.topology.repair --railway.topology.all-bidi --remove-edges.isolated --output.street-names -o koszecin.net.xml
"$B/netconvert" -s koszecin.net.xml -n przejazdy.nod.xml -o koszecin.net.xml          # przejazdy kolejowe z rogatkami
python3 teren_zabudowany.py $GJ                                                          # 50 km/h w zabudowie, 90 poza
"$B/netconvert" -s koszecin.net.xml -e predkosci.edg.xml -o koszecin.net.xml
"$B/netconvert" -s koszecin.net.xml -n zlacz.nod.xml -o koszecin.net.xml          # sklejone skrzyżowania rozbite w OSM (skrzyzowania.py)
"$B/netconvert" -s koszecin.net.xml --remove-edges.explicit 353,-353,2613,-2613 -o koszecin.net.xml   # Rynek: drogi wewnętrzne na posesjach (wg mieszkańca)
python3 przejazdy.py koszecin.net.xml       # jeden przejazd przez kilka torów, dłużej zamknięte rogatki → przejazdy.add.xml
gzip -9 -f koszecin.net.xml && rm -f koszecin.osm
python3 scenariusz.py                     # przystanki.add.xml, busy.rou.xml (z out/data.json i out/rozklad_data.json)
python3 pociagi.py                        # pociagi.rou.xml
python3 tlo.py                             # ruch tła dobrany do pomiarów GPR (routeSampler) → tlo.rou.xml.gz
rm -f trips.trips.xml
mkdir -p wyniki && "$B/sumo" -c koszecin.sumocfg
python3 analiza.py && python3 przesiadki.py && python3 kalibracja.py
