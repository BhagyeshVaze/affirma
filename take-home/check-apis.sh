#!/usr/bin/env bash
# Quick reachability check for the keyless APIs listed in APIS.md.
# Usage: ./check-apis.sh
UA="TakeHomeApiCheck/1.0"

check() {
  local name="$1" url="$2"
  local code
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 15 "$url" 2>/dev/null)
  if [[ "$code" == 2* ]]; then
    printf "  OK   %-22s %s\n" "$name" "$code"
  else
    printf "  FAIL %-22s %s\n" "$name" "${code:-000}"
  fi
}

echo "Checking public APIs..."
check "Open-Meteo"         "https://api.open-meteo.com/v1/forecast?latitude=41.88&longitude=-87.63&daily=temperature_2m_max&timezone=auto"
check "USGS Earthquakes"   "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
check "Frankfurter"        "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR"
check "CoinGecko"          "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
check "Jolpica F1"         "https://api.jolpi.ca/ergast/f1/current/driverStandings.json"
check "World Bank"         "https://api.worldbank.org/v2/country/USA/indicator/SP.POP.TOTL?format=json&date=2023"
check "REST Countries"     "https://restcountries.com/v3.1/alpha/JPN?fields=name,population"
check "CityBikes"          "https://api.citybik.es/v2/networks?fields=id"
check "Hacker News"        "https://hacker-news.firebaseio.com/v0/topstories.json"
check "HN Algolia"         "https://hn.algolia.com/api/v1/search?query=react&tags=story&hitsPerPage=1"
check "PokeAPI"            "https://pokeapi.co/api/v2/pokemon/pikachu"
check "Open Library"       "https://openlibrary.org/search.json?q=dune&limit=1"
check "NWS (weather.gov)"  "https://api.weather.gov/alerts/active?area=CA"
