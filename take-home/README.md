# Full-Stack Take-Home: Build a Data Dashboard

Welcome! In this exercise you'll build a small full-stack app: a **Python backend** that pulls
data from a free public API and turns it into something new, and a **React frontend** dashboard
that displays the results.

## You can use AI, and we want you to

**Using AI tools is allowed and encouraged.** Use Claude, ChatGPT, Copilot, Cursor, Claude Code,
or any other assistant or agent you like, for planning, design, writing code, tests, and debugging.
We're not testing whether you can build this without AI. We're testing **how well you work
with it**: how you plan, how clearly you direct it, and how critically you review what it produces.

**Because of that, documenting how you worked with AI is required.** Every plan, technical design
document (TDD), spec, task list, or prompt file you gave to an AI must be committed with your
submission (see [Required documentation](#required-documentation)). A submission without these
documents is incomplete, even if the app works perfectly.

**Suggested time box:** 3–4 hours. We care more about clear thinking and a working
slice than a large feature list.

---

## The task

1. **Pick an API.** Choose **one** of the four APIs in [`apis/`](./apis/README.md): Open-Meteo
   (weather), USGS Earthquakes, Frankfurter (exchange rates), or Jolpica F1. All are free
   and need **no API key and no sign-up**. Each API's file lists its routes, response
   shapes, and gotchas. It's written so you can hand it straight to your AI assistant.
2. **Pick a dashboard.** Each API file ends with four **dashboard ideas**. Build one of them,
   combine ideas, or design your own. Your backend must **transform, combine, or compute**
   something. A pass-through proxy doesn't count.
3. **Plan it (with AI if you like) and commit the plan first.** Write your plan or TDD before
   writing code, and commit it as your first commit.
4. **Build the backend in Python.** Expose **at least 2 of your own endpoints** that:
   - call the upstream API
   - reshape the data and/or calculate something (aggregates, rankings, rolling
     averages, % change, distances, etc.)
   - return a clean JSON shape that *you* designed for the frontend
   - handle upstream failures gracefully (timeouts, bad input, rate limits)
5. **Build the frontend in React.** Build a simple dashboard that calls **your** backend (not the
   upstream API directly) and shows the data. Include at least one chart or visual
   plus some way for the user to interact, such as a filter, date range, search, or
   selector.
6. **Document it.** Add the docs described below.

### Tech stack

| Layer    | Required    | Suggested tools |
| -------- | ----------- | --------------- |
| Backend  | **Python**  | **FastAPI** (recommended) or Flask; `httpx` or `requests` for upstream calls; Pydantic for response models; `pytest` for tests |
| Frontend | **React**   | **Vite** to scaffold (`npm create vite@latest`), JavaScript or TypeScript; Recharts, Chart.js, or Plotly for charts |

A database is **not** required. In-memory caching is plenty.

---

## Required documentation

These are **required**. Put them in your `solution/` folder (see [Submitting](#submitting)):

| File | What goes in it |
| ---- | --------------- |
| `README.md` | How to install and run the backend and frontend (ideally one or two commands each), plus a short description of what the dashboard shows. |
| `PLAN.md` (or a TDD) | Your plan or technical design, **written before you started coding**: the chosen API and dashboard, the endpoint designs (routes, params, response shapes), the frontend layout, and the risks or open questions. Update it as you go. We want to see how the plan changed. |
| `ai/` folder | **Every plan, TDD, spec, task list, or prompt file you handed to an AI**, exactly as you gave it. Examples: an implementation plan you asked an agent to follow, a spec you pasted into a chat, `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, agent-generated plan files. If you revised one, commit the revisions too (git history is fine for this). Exported chat transcripts are welcome. |
| `AI_LOG.md` | A short narrative of how you used AI: which tools, what you asked for at each stage (you can link to files in `ai/`), what you accepted as-is, what you changed, and **at least one place where the AI was wrong or unhelpful** and how you noticed and fixed it. |
| `DECISIONS.md` *(optional)* | Trade-offs, things you'd do with more time, known bugs. |

If a document guided the AI's work, we want to see it. When in doubt, commit it.

**Commit history counts.** Commit in steps: commit `PLAN.md` first, then
commit your work as you go. Don't squash everything into one commit.

---

## What we look for

- **AI collaboration:** clear plans and specs that you gave the AI, thoughtful and critical review of
  its output, and honest documentation of what worked and what didn't. You should understand and be
  able to explain every line you commit.
- **Planning:** a clear plan that you actually followed and updated.
- **Backend design:** sensible endpoints and response shapes, correct calculations,
  input validation, and error handling. Bonus points for caching so you don't
  hammer the free APIs.
- **Frontend:** it works, it's readable, and it handles loading, empty, and error states.
- **Communication:** we can run your project from the README in under 5 minutes.

Tests are welcome but not required. One or two `pytest` tests on your calculation logic go a long way.

---

## Submitting

1. **Fork** this repository.
2. Add your project to your fork in a `solution/` folder next to this README:

   ```
   take-home/solution/
   ├── README.md
   ├── PLAN.md
   ├── AI_LOG.md
   ├── ai/          # plans, TDDs, specs and prompts you gave the AI
   ├── backend/     # Python
   └── frontend/    # React
   ```

3. Commit your work in steps and push to your fork.
4. Send us the link to your fork. No pull request is needed.

Don't commit secrets, `node_modules/`, virtual environments, or build output.

## Tips

- Free public APIs have rate limits and sometimes go down. Cache responses and
  show a friendly error when an upstream call fails.
- Run `./check-apis.sh` to quickly see whether the four APIs are reachable from your network.
- Give your AI the API reference file for your chosen API. It lists the real response shapes and the
  gotchas that commonly cause bugs.

Questions? Reach out. Asking a clarifying question is a good sign, not a bad one.
