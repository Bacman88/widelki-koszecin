#!/usr/bin/env bash
# Pobiera wycinek OpenStreetMap całej gminy (z repozytorium rowerowy-strzebin), potrzebny do prowadzenia tras po drogach.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p dane/osm
URL=https://raw.githubusercontent.com/Bacman88/rowerowy-strzebin/main/dane/osm_gmina.geojson
[ -f dane/osm/osm_gmina.geojson ] || curl -fL "$URL" -o dane/osm/osm_gmina.geojson
echo "OK: dane/osm/osm_gmina.geojson"
