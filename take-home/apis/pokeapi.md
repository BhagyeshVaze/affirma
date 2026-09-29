# PokéAPI

Complete Pokémon data: species, stats, types, abilities, moves, evolutions, and more. The data is static
and deeply linked (resources reference each other by URL).

- **Official docs:** https://pokeapi.co/docs/v2
- **Auth:** none
- **Rate limits:** no hard limit, but the fair-use policy asks you to **cache locally**.
  The data almost never changes, so caching it indefinitely is fine.
- **Format:** JSON

Base URL: `https://pokeapi.co/api/v2`

## Endpoints

Every resource supports `/{resource}/{id or name}`. Lists support `?limit=&offset=`.

| Route | Purpose |
|-------|---------|
| `GET /pokemon?limit=100&offset=0` | Paginated list of `{name, url}` (about 1,300 total) |
| `GET /pokemon/{name\|id}` | Stats, types, abilities, sprites, height/weight, moves |
| `GET /pokemon-species/{name\|id}` | Generation, legendary/mythical flags, flavor text, evolution chain URL |
| `GET /evolution-chain/{id}` | Nested evolution tree |
| `GET /type/{name}` | **Damage relations** and every Pokémon of that type |
| `GET /ability/{name}` | Ability effect text and Pokémon that have it |
| `GET /move/{name}` | Power, accuracy, PP, type, damage class |
| `GET /generation/{id}` | Species and types introduced in that generation |
| `GET /item/{name}`, `/berry/{name}`, `/location/{id}` | Other resources |

## Example requests

```bash
curl "https://pokeapi.co/api/v2/pokemon/pikachu"
curl "https://pokeapi.co/api/v2/type/fire"
curl "https://pokeapi.co/api/v2/pokemon?limit=151"
```

## Response shapes (trimmed)

`/pokemon/pikachu`:

```json
{
  "id": 25, "name": "pikachu", "height": 4, "weight": 60, "base_experience": 112,
  "types": [ { "slot": 1, "type": { "name": "electric", "url": "https://pokeapi.co/api/v2/type/13/" } } ],
  "stats": [
    { "base_stat": 35, "effort": 0, "stat": { "name": "hp" } },
    { "base_stat": 55, "effort": 0, "stat": { "name": "attack" } },
    { "base_stat": 40, "effort": 0, "stat": { "name": "defense" } },
    { "base_stat": 50, "effort": 0, "stat": { "name": "special-attack" } },
    { "base_stat": 50, "effort": 0, "stat": { "name": "special-defense" } },
    { "base_stat": 90, "effort": 2, "stat": { "name": "speed" } }
  ],
  "abilities": [ { "ability": { "name": "static" }, "is_hidden": false } ],
  "sprites": { "front_default": "https://raw.githubusercontent.com/PokeAPI/sprites/.../25.png",
               "other": { "official-artwork": { "front_default": "https://.../official-artwork/25.png" } } },
  "species": { "name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon-species/25/" },
  "moves": [ "... very long ..." ]
}
```

`/type/fire`:

```json
{
  "name": "fire",
  "damage_relations": {
    "double_damage_to":   [ { "name": "grass" }, { "name": "ice" }, { "name": "bug" }, { "name": "steel" } ],
    "half_damage_to":     [ { "name": "fire" }, { "name": "water" }, { "name": "rock" }, { "name": "dragon" } ],
    "no_damage_to":       [],
    "double_damage_from": [ { "name": "water" }, { "name": "ground" }, { "name": "rock" } ],
    "half_damage_from":   [ { "name": "fire" }, { "name": "grass" }, { "name": "ice" }, { "name": "bug" }, { "name": "steel" }, { "name": "fairy" } ],
    "no_damage_from":     []
  },
  "pokemon": [ { "pokemon": { "name": "charmander", "url": "..." }, "slot": 1 } ]
}
```

## Gotchas

- Names are **lowercase and hyphenated** (`mr-mime`, `tapu-koko`). Normalize user input.
- `height` is in **decimetres** and `weight` in **hectograms** (divide both by 10 for m and kg).
- `/pokemon/{x}` responses are large, mostly because of `moves`. Strip what you don't need before
  sending data to the frontend.
- A dual-type Pokémon's weakness to an attacking type = the **product** of the multipliers for
  both of its types (e.g. 2 × 2 = 4×, 2 × 0.5 = 1×, anything × 0 = immune).
- The list endpoint only returns `{name, url}`. Getting stats for many Pokémon means one request per
  Pokémon, so cache them and limit concurrency.
- An unknown name returns HTTP 404 with the plain-text body `Not Found`.
