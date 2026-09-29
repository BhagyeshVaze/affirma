# Full-Stack Take-Home: Build a Data Dashboard

Welcome! In this exercise you'll build a small full-stack app: a **backend** that pulls
data from one or more free public APIs and turns it into something new, plus a
**frontend dashboard** that displays the results.

We want to see how you plan, build, and document work **with AI tools**. Using
AI assistants (Claude, ChatGPT, Copilot, Cursor, etc.) is expected and encouraged.
You also need to include your plans and documentation in the submission (see
[Required documentation](#required-documentation)).

**Suggested time box:** 3–4 hours. We care more about clear thinking and a working
slice than a large feature list.

---

## The task

1. **Pick a data source.** Choose one or more APIs from [`APIS.md`](./APIS.md). Every
   API on that list is free and needs **no API key and no sign-up**. Detailed route
   references for each API are in [`apis/`](./apis/README.md). Feed them to your AI assistant. You may use another
   keyless public API if you prefer. Tell us why in your plan.
2. **Pick a challenge.** Use one of the example challenges in `APIS.md` or come up
   with your own. Your challenge should require the backend to **transform, combine,
   or compute** something. A pass-through proxy doesn't count.
3. **Build the backend.** Expose **at least 2 of your own endpoints** that:
   - call the upstream API(s)
   - reshape the data and/or calculate something (aggregates, rankings, rolling
     averages, % change, distances, joins across APIs, etc.)
   - return a clean JSON shape that *you* designed for the frontend
   - handle upstream failures gracefully (timeouts, bad input, rate limits)
4. **Build the frontend.** Build a simple dashboard that calls **your** backend (not the
   upstream APIs directly) and shows the data. Include at least one chart or visual
   plus some way for the user to interact, such as a filter, date range, search, or
   selector.
5. **Document it.** Add the docs described below.

### Tech stack

You can use any language or framework. If you don't have a preference, here are some
suggestions:

| Layer    | Python option                     | JavaScript/TypeScript option                   |
| -------- | --------------------------------- | ---------------------------------------------- |
| Backend  | **FastAPI** (or Flask)            | **Express**, **Fastify**, or **Hono** on Node  |
| Frontend | **React + Vite**                  | **React + Vite** (or Next.js if you prefer)    |
| Charts   | Recharts, Chart.js, or Plotly     | Recharts, Chart.js, or Plotly                  |

A database is **not** required. In-memory caching is plenty.

---

## Required documentation

Put these files in your submission folder (see [Submitting](#submitting)):

| File | What goes in it |
| ---- | --------------- |
| `README.md` | How to install and run the backend and frontend (ideally one or two commands each), plus a short description of what the dashboard shows. |
| `PLAN.md` | Your plan **written before you started coding**: the chosen API(s) and challenge, the endpoint designs (routes, params, response shapes), the frontend layout, and the risks or open questions. Update it as you go. We want to see how the plan changed. |
| `AI_LOG.md` | How you used AI: which tools, the important prompts (copied or summarized), what you accepted as-is, what you changed, and **at least one place where the AI was wrong or unhelpful** and how you noticed and fixed it. |
| `DECISIONS.md` *(optional)* | Trade-offs, things you'd do with more time, known bugs. |

You may also commit any AI artifacts you produced, such as agent plan files,
`CLAUDE.md` or `.cursorrules`, or exported chat transcripts. More context helps us.

**Commit history counts.** Please commit in steps: commit `PLAN.md` first, then
commit your work as you go. Don't squash everything into one commit.

---

## What we look for

- **Planning:** a clear plan that you actually followed and updated.
- **Backend design:** sensible endpoints and response shapes, correct calculations,
  input validation, and error handling. Bonus points for caching so you don't
  hammer the free APIs.
- **Frontend:** it works, it's readable, and it handles loading, empty, and error states.
- **AI usage:** thoughtful, critical use. You understand and can explain every line
  you commit.
- **Communication:** we can run your project from the README in under 5 minutes.

Tests are welcome but not required. One or two tests on your calculation logic go a long way.

---

## Submitting

1. **Fork** this repository.
2. Put your project in `take-home/submissions/<your-name>/`, for example
   `take-home/submissions/jane-doe/backend`, `.../frontend`, `.../PLAN.md`.
3. Commit your work in steps and push to your fork.
4. Send us the link to your fork (or open a pull request against this repo if we asked you to).

Don't commit secrets, `node_modules/`, virtual environments, or build output.

## Tips

- Free public APIs have rate limits and sometimes go down. Cache responses and
  show a friendly error when an upstream call fails.
- Some APIs ask for a descriptive `User-Agent` header (noted in `APIS.md`).
- Run `./check-apis.sh` to quickly see which APIs are reachable from your network.

Questions? Reach out. Asking a clarifying question is a good sign, not a bad one.
