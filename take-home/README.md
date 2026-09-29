# Take-Home: Build a Data Dashboard

Build a **Python backend** that pulls data from a public API and computes something new, and a
**React dashboard** that displays it.

**Time:** 3–4 hours. A small, working app beats a big, unfinished one.

## AI

> [!TIP]
> **Use AI.** Any assistant or agent is fine, for any part of the work. We're assessing how well
> you work with AI: how you plan, direct it, and review its output.

> [!IMPORTANT]
> **Commit everything you gave the AI.** Every plan, TDD, spec, or prompt file goes in `ai/`.
> Without it, your submission is incomplete.

## The task

1. **Pick an API** from the table below. Each links to a reference doc you can give your AI.
2. **Pick a dashboard.** Each API doc has four ideas, or design your own.
3. **Write a plan** (`PLAN.md` or a TDD). Commit it before any code.
4. **Build the backend (Python).** At least 2 endpoints that:
   - call the API
   - transform or compute something (a pass-through doesn't count)
   - return JSON you designed
   - handle errors: timeouts, bad input, rate limits
5. **Build the frontend (React).** It calls your backend only. Include at least one chart and one
   control, such as a filter, date range, or search box.
6. **Write the docs** listed below.

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

## Required docs

Put these in `solution/`:

| File | Contents |
| --- | --- |
| `README.md` | How to run the backend and frontend. What the dashboard shows. |
| `PLAN.md` | Written before coding: endpoints, response shapes, UI layout, risks. Update it as you go. |
| `ai/` | Every plan, TDD, spec, or prompt you gave an AI, as given. Include revisions. |
| `AI_LOG.md` | Tools used, what you asked for, what you changed, and **at least one thing the AI got wrong**. |
| `DECISIONS.md` | Optional. Trade-offs, known bugs, next steps. |

If it guided the AI, commit it.

**Commit in steps.** Plan first, then small commits. Don't squash.

## What we look for

| Area | Good looks like |
| --- | --- |
| AI use | Clear direction, critical review, honest log. You can explain every line. |
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
   ├── PLAN.md
   ├── AI_LOG.md
   ├── ai/
   ├── backend/
   └── frontend/
   ```

3. Push to your fork and send us the link. No pull request.

**Checklist**

- [ ] Backend and frontend run from your README
- [ ] 2+ endpoints that compute something
- [ ] `PLAN.md` is the first commit
- [ ] Everything you gave the AI is in `ai/`
- [ ] `AI_LOG.md` names something the AI got wrong
- [ ] No secrets, `node_modules/`, virtualenvs, or build output

Questions? Ask. It's a good sign.
