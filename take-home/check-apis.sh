#!/usr/bin/env bash
# Quick reachability check for the APIs documented in apis/.
# Usage: ./check-apis.sh

check() {
  local name="$1" url="$2"
  local code
  code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 15 "$url" 2>/dev/null)
  if [[ "$code" == 2* ]]; then
    printf "  OK   %-18s %s\n" "$name" "$code"
  else
    printf "  FAIL %-18s %s\n" "$name" "${code:-000}"
  fi
}

echo "Checking public APIs..."
check "Open-Meteo"       "https://api.open-meteo.com/v1/forecast?latitude=41.88&longitude=-87.63&daily=temperature_2m_max&timezone=auto"
check "Open-Meteo geo"   "https://geocoding-api.open-meteo.com/v1/search?name=Chicago&count=1"
check "USGS Earthquakes" "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
check "Frankfurter"      "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR"
check "Jolpica F1"       "https://api.jolpi.ca/ergast/f1/current/driverStandings.json"
