# Hacker News (Official Firebase API + Algolia Search)

Two complementary, free, keyless APIs for Hacker News:

1. **Official HN API** (Firebase): live front-page lists, items, and users. Simple, but lists
   return **IDs only**, so you fetch each item separately.
2. **Algolia HN Search**: full-text search with date and points filters, and aggregated results.

- **Official docs:** https://github.com/HackerNews/API and https://hn.algolia.com/api
- **Auth:** none
- **Rate limits:** Firebase has no published limit. Algolia allows ~10,000 requests/hour per IP.
- **Format:** JSON

---

## 1. Official API

Base URL: `https://hacker-news.firebaseio.com/v0`

| Route | Returns |
|-------|---------|
| `GET /topstories.json` | Up to 500 story IDs (front-page ranking) |
| `GET /newstories.json` | Up to 500 newest story IDs |
| `GET /beststories.json` | Best story IDs |
| `GET /askstories.json`, `/showstories.json`, `/jobstories.json` | Up to 200 IDs each |
| `GET /item/{id}.json` | One story, comment, job, poll, or poll option |
| `GET /user/{username}.json` | User profile |
| `GET /maxitem.json` | Current largest item ID |
| `GET /updates.json` | Recently changed items and profiles |

Item shape:

```json
{
  "id": 8863, "type": "story", "by": "dhouston", "time": 1175714200,
  "title": "My YC app: Dropbox - Throw away your USB drive",
  "url": "http://www.getdropbox.com/u/2/screencast.html",
  "score": 104, "descendants": 71, "kids": [9224, 8917, 8884]
}
```

- `type`: `story` | `comment` | `job` | `poll` | `pollopt`
- `time` is **Unix seconds**.
- `kids` are child comment IDs, and `descendants` is the total comment count.
- Ask HN posts have `text` (HTML) and no `url`.
- An item can be `null`, or have `"deleted": true` or `"dead": true`.

User shape: `{ "id": "pg", "created": 1160418092, "karma": 157000, "about": "...", "submitted": [ ...ids ] }`

## 2. Algolia HN Search

Base URL: `https://hn.algolia.com/api/v1`

| Route | Purpose |
|-------|---------|
| `GET /search` | Search sorted by relevance (then points) |
| `GET /search_by_date` | Search sorted newest first |
| `GET /items/{id}` | One item with its **full nested comment tree** in one call |
| `GET /users/{username}` | User info |

Search parameters:

| Param | Example | Notes |
|-------|---------|-------|
| `query` | `rust` | Full text. Can be empty. |
| `tags` | `story`, `comment`, `ask_hn`, `show_hn`, `front_page`, `author_pg`, `story_8863` | Comma = AND, `(a,b)` = OR |
| `numericFilters` | `created_at_i>1735689600,points>100` | Filter on `created_at_i`, `points`, `num_comments` |
| `hitsPerPage` | `50` | Max 1000 |
| `page` | `0` | 0-based |

Search response:

```json
{
  "hits": [
    { "objectID": "8863", "title": "My YC app: Dropbox ...", "url": "http://...",
      "author": "dhouston", "points": 104, "num_comments": 71,
      "created_at": "2007-04-04T19:16:40.000Z", "created_at_i": 1175714200,
      "_tags": ["story", "author_dhouston", "story_8863"] }
  ],
  "nbHits": 1234, "page": 0, "nbPages": 25, "hitsPerPage": 50
}
```

## Example requests

```bash
curl "https://hacker-news.firebaseio.com/v0/topstories.json"
curl "https://hacker-news.firebaseio.com/v0/item/8863.json"
curl "https://hn.algolia.com/api/v1/search?tags=front_page"
curl "https://hn.algolia.com/api/v1/search_by_date?query=rust&tags=story&numericFilters=created_at_i>1735689600&hitsPerPage=100"
```

## Gotchas

- Loading the front page from Firebase is **1 request for IDs + N requests for items**. Fetch items
  **concurrently with a cap** (e.g. 10 at a time) and cache them. `tags=front_page` on Algolia
  gets it in one call.
- For counts over time (e.g. "stories per month about X"), Algolia is much easier. Run one query per
  time bucket using `numericFilters=created_at_i>A,created_at_i<B` and read `nbHits`.
- Algolia won't page past about 1,000 results for a query. Narrow the query with filters.
- Extract a story's domain from `url` with a URL parser (and strip `www.`).
