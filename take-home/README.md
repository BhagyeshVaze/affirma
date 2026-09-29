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

1. **Pick an API** from the table below. Each links to a reference doc you can give your AI.
2. **Pick a dashboard.** Each API doc has four ideas, or design your own.
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

Run [`./check-apis.sh`](./check-apis.sh) to check they're reachable from your network.

## Docs

| Path | Contents |
| --- | --- |
| `README.md` | How to run the backend and frontend. What the dashboard shows. |
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

- [ ] Backend and frontend run from your README
- [ ] 2+ endpoints that compute something
- [ ] Your plan is the first commit
- [ ] `docs/` has your plan, decisions, and key AI inputs
- [ ] No secrets, `node_modules/`, virtualenvs, or build output

Questions? Ask. It's a good sign.
