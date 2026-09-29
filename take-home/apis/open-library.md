# Open Library: Books & Authors

An open catalog of millions of books from the Internet Archive: works, editions, authors,
subjects, and cover images.

- **Official docs:** https://openlibrary.org/developers/api
- **Auth:** none
- **Rate limits:** ~1 request/second by default, and ~3 requests/second if you send a **descriptive `User-Agent`**
  with contact info (e.g. `MyDashboard/1.0 (you@example.com)`). Requests without a User-Agent may be blocked.
- **Format:** JSON

Base URL: `https://openlibrary.org`

## Endpoints

| Route | Purpose |
|-------|---------|
| `GET /search.json` | Search **works** by `q`, `title`, `author`, `subject`, `isbn`, ... |
| `GET /search/authors.json?q=` | Search authors |
| `GET /authors/{OLID}.json` | Author detail (e.g. `OL23919A`) |
| `GET /authors/{OLID}/works.json?limit=&offset=` | An author's works |
| `GET /works/{OLID}.json` | Work detail (e.g. `OL45804W`) |
| `GET /works/{OLID}/editions.json` | Editions of a work |
| `GET /books/{OLID}.json` | Edition detail (e.g. `OL7353617M`) |
| `GET /isbn/{isbn}.json` | Edition by ISBN (redirects to `/books/...`) |
| `GET /subjects/{subject}.json?limit=&offset=` | Works for a subject (`science_fiction`, `love`, `python`) |
| `GET /trending/{daily\|weekly\|monthly}.json` | Currently trending works |
| Covers: `https://covers.openlibrary.org/b/id/{cover_i}-{S\|M\|L}.jpg` | Cover image by cover ID |
| Covers: `https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg` | Cover image by ISBN |

### `/search.json` parameters

| Param | Example | Notes |
|-------|---------|-------|
| `q` | `the lord of the rings` | General query |
| `title`, `author`, `subject`, `isbn`, `publisher` | `author=ursula+le+guin` | Field-specific search |
| `fields` | `key,title,author_name,first_publish_year,edition_count,cover_i` | **Strongly recommended**, because it makes responses much smaller and faster |
| `sort` | `new`, `old`, `rating`, `editions` | |
| `limit`, `page` | `100`, `1` | |
| `lang` | `en` | Prefer a language |

## Example requests

```bash
UA="MyTakeHome/1.0 (you@example.com)"
curl -A "$UA" "https://openlibrary.org/search.json?author=ursula+le+guin&fields=key,title,first_publish_year,edition_count&limit=100"
curl -A "$UA" "https://openlibrary.org/subjects/science_fiction.json?limit=50"
curl -A "$UA" "https://openlibrary.org/search/authors.json?q=octavia+butler"
```

## Response shapes (trimmed)

`/search.json`:

```json
{
  "numFound": 312, "start": 0,
  "docs": [
    { "key": "/works/OL59800W", "title": "A Wizard of Earthsea",
      "author_name": ["Ursula K. Le Guin"], "author_key": ["OL31337A"],
      "first_publish_year": 1968, "edition_count": 142, "cover_i": 8231856,
      "subject": ["Fantasy", "Wizards"], "language": ["eng", "spa"],
      "ratings_average": 4.1 }
  ]
}
```

`/subjects/{subject}.json`:

```json
{
  "name": "science fiction", "work_count": 85000,
  "works": [
    { "key": "/works/OL893415W", "title": "Dune", "edition_count": 120,
      "first_publish_year": 1965, "cover_id": 11481354,
      "authors": [ { "key": "/authors/OL79034A", "name": "Frank Herbert" } ] }
  ]
}
```

## Gotchas

- It's **slow** (often 1–3 s per call). Cache, and show loading states in the UI.
- Many fields are optional. `first_publish_year`, `cover_i`, and `ratings_average` are often missing.
- In search results, the cover field is `cover_i`. In subject results, it's `cover_id`.
- `description` and `bio` on works and authors can be **either a string or
  `{ "type": "/type/text", "value": "..." }`**. Handle both.
- Search results mix works with the same title (translations, duplicates). De-duplicate if needed.
- Keys look like `/works/OL45804W`. Strip the prefix to get the OLID.
