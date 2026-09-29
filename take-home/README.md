# Take-Home: Build a Data Dashboard

Build a **Python backend** that pulls data from a public API and computes something new, and a
**React dashboard** that displays it.

**Time:** 3–4 hours. A small, working app beats a big, unfinished one.

## AI

> [!TIP]
> **We highly encourage using AI** if you can. Any assistant or agent is fine, for any part of the
> work. We want to see how you work with it: how you plan, direct it, and review its output.

> [!NOTE]
> **Share how you used it.** Put the key plans, TDDs, or specs you gave the AI in `docs/`.
> You don't need every prompt, just the ones that shaped the work.

## The task

1. **Pick an API.** Use one of our four documented APIs, or another free one from the list below.
2. **Pick a dashboard.** Use one of our ideas or bring your own.
3. **Write a plan or TDD** in `docs/`. Commit it before any code.
4. **Build the backend (Python).** At least 2 endpoints that:
   - call the API
   - transform or compute something (a pass-through doesn't count)
   - return JSON you designed
   - handle errors: timeouts, bad input, rate limits
5. **Build the frontend (React).** It calls your backend only. Include at least one chart and one
   control, such as a filter, date range, or search box.
6. **Write the [docs](#docs).**

### Stack

| Layer | Use | Suggested |
| --- | --- | --- |
| Backend | Python | FastAPI, `httpx` or `requests`, Pydantic, `pytest` |
| Frontend | React | Vite, Recharts or Chart.js |

No database needed. Cache in memory.

## APIs

All free. No key, no sign-up.

| API | Data | Rate limit |
| --- | --- | --- |
| [Open-Meteo](./apis/open-meteo.md) | Weather: forecasts, history since 1940, air quality | 10,000 calls/day |
| [USGS Earthquakes](./apis/usgs-earthquakes.md) | Earthquakes worldwide | None published |
| [Frankfurter](./apis/frankfurter.md) | Exchange rates since 1999 | None published |
| [Jolpica F1](./apis/jolpica-f1.md) | Formula 1 results since 1950 | 500/hour |

### Dashboard ideas

| API | Ideas |
| --- | --- |
| Open-Meteo | Compare cities' weekly weather · Is this week unusually hot or cold? · Best time to go outside (weather + air quality) · A city's 30-year climate trend |
| USGS | Earthquake activity this week · Quakes near a chosen place · Most active regions · Aftershocks after a major quake |
| Frankfurter | Best and worst currencies over a period · What a travel budget is worth now vs last year · Moving averages and trends · Grid of every currency pair |
| Jolpica F1 | Title race, round by round · Teammate head-to-heads · One driver's season report · Which teams dominated which years |

Each API doc has details for its ideas: what to show, an example endpoint, and the backend work.

**Have your own idea? Go for it.** Build any dashboard you like, as long as the backend does real
work. Explain the idea in your plan.

### Other free APIs

You can also use another free API that needs no key. We haven't documented these in depth, so check
that one works before you commit to it.

| API | Data |
| --- | --- |
| [World Bank](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) | Country economics and population, yearly |
| [CityBikes](https://api.citybik.es/v2/) | Live bike-share stations worldwide |
| [Hacker News](https://github.com/HackerNews/API) / [Algolia HN Search](https://hn.algolia.com/api) | Tech news stories and comments |
| [PokéAPI](https://pokeapi.co/docs/v2) | Pokémon stats and types |
| [Open Library](https://openlibrary.org/developers/api) | Books and authors |
| [National Weather Service](https://www.weather.gov/documentation/services-web-api) | US forecasts and alerts. Needs a `User-Agent` header |
| [Nager.Date](https://date.nager.at/Api) | Public holidays by country |
| [Art Institute of Chicago](https://api.artic.edu/docs/) | Artworks and artists |
| [The Met Collection](https://metmuseum.github.io/) | Artworks and departments |
| [US Treasury Fiscal Data](https://fiscaldata.treasury.gov/api-documentation/) | US debt, spending, and revenue |
| [openFDA](https://open.fda.gov/apis/) | Drug and food safety reports |
| [OpenF1](https://openf1.org/) | Live and recent F1 timing data |
| [UK Carbon Intensity](https://carbon-intensity.github.io/api-definitions/) | UK electricity carbon intensity and fuel mix |
| [Open Food Facts](https://openfoodfacts.github.io/openfoodfacts-server/api/) | Food products and nutrition |

Run [`./check-apis.sh`](./check-apis.sh) to check they're reachable from your network.

## Docs

| Path | Contents |
| --- | --- |
| `README.md` | How to run the backend and frontend. What the dashboard shows, with screenshots. |
| `docs/` | Plans, TDDs, decisions, and any key inputs you gave an AI. |

Good things to put in `docs/`:

- **Plan or TDD**, written before coding: endpoints, response shapes, UI layout, risks. Update it as you go.
- **Decisions**: trade-offs, known bugs, next steps.
- **AI inputs**, if you used AI: the plans, specs, or prompts that shaped the work (not every prompt),
  plus a short note on what you changed and where it got things wrong.

**Commit in steps.** Plan first, then small commits. Don't squash.

## What we look for

| Area | Good looks like |
| --- | --- |
| AI use | Clear direction, critical review, honest notes. You can explain every line. |
| Planning | A plan you followed and updated. |
| Backend | Clean endpoints, correct math, validation, error handling, caching. |
| Frontend | Works. Handles loading, empty, and error states. |
| Docs | We can run it in under 5 minutes. |

Tests are optional. A few `pytest` tests on your calculations help.

## Submitting

1. Fork this repo.
2. Add your work in `take-home/solution/`:

   ```text
   solution/
   ├── README.md
   ├── backend/
   ├── frontend/
   └── docs/
   ```

3. Push to your fork and send us the link. No pull request.

**Checklist**

- [ ] Plan or TDD committed before any code
- [ ] 2+ backend endpoints that transform or compute data
- [ ] Backend handles timeouts, bad input, and rate limits
- [ ] Frontend calls only your backend, with at least one chart and one control
- [ ] README explains how to run it in under 5 minutes
- [ ] README includes screenshots of the dashboard
- [ ] `docs/` has your plan, decisions, and key AI inputs (if you used AI)
- [ ] No secrets, `node_modules/`, virtualenvs, or build output

Questions? Ask. It's a good sign.
