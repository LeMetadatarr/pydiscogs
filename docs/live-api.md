# Live Discogs API

`pydiscogs` supports two complementary data paths:

| Path | Source | Key required? | Speed |
|------|--------|---------------|-------|
| Bulk dumps | `data.discogs.com` (CC0 gzip XML) | No | Slow (GBs) |
| Live API | `api.discogs.com` (JSON REST) | Recommended | Fast (single records) |

The live path is implemented in `pydiscogs.live`.

---

## Token setup

Discogs accepts unauthenticated requests but applies a stricter rate limit
(25 req/min vs 60 req/min with a token).  Get a **personal access token** from
<https://www.discogs.com/settings/developers> and export it:

```bash
export DISCOGS_TOKEN=your_token_here
```

All functions accept an optional `token=` keyword argument if you prefer not to
use an environment variable.

---

## Lookup methods

```python
from pydiscogs import get_artist, get_release, get_master, get_label

artist  = get_artist(1)         # → Artist(id=1, name="The Persuader", ...)
release = get_release(1)        # → Release(id=1, title="Stockholm", year=1999, ...)
master  = get_master(18500)     # → Master(id=18500, title="New Soil", year=2001, ...)
label   = get_label(5)          # → Label(id=5, name="Svek", ...)
```

All four functions return the same model classes used by the bulk-dump path
(`Artist`, `Release`, `Master`, `Label`), so downstream code works with either
source interchangeably.

---

## Search

```python
from pydiscogs import search, search_iter

# Single page
resp = search("Stockholm", type="release", genre="Electronic", per_page=10)
for r in resp["results"]:
    print(r["id"], r["title"])

# All pages, up to a limit
for result in search_iter("Svek", type="release", limit=100):
    print(result["id"], result["title"])
```

### `search()` parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | str | Free-text query (`q`) |
| `type` | str | `"release"`, `"master"`, `"artist"`, `"label"` |
| `title` | str | Search in title field only |
| `artist` | str | Filter by artist name |
| `label` | str | Filter by label name |
| `genre` | str | e.g. `"Electronic"` |
| `style` | str | e.g. `"Techno"` |
| `country` | str | e.g. `"Sweden"` |
| `year` | str | e.g. `"1999"` |
| `format` | str | e.g. `"Vinyl"` |
| `per_page` | int | 1–100 (default 50) |
| `page` | int | Page number (default 1) |
| `token` | str | Override `DISCOGS_TOKEN` env |

`search()` returns the raw API dict with `"results"` and `"pagination"` keys.
`search_iter()` takes the same arguments plus `limit=` and yields individual
result dicts across all pages.

---

## Rate limiting

- Without token: 25 req/min.
- With token: 60 req/min.
- The client enforces a ~1.1 s inter-request delay by default (≈54 req/min).
- On HTTP 429, one automatic retry after 5 s.
- Set `PYDISCOGS_ANON=1` to route through rotating proxies (requires
  `anon_requests`) for sustained high-volume use.

---

## Verified live

The following endpoints were called directly during development (no token
needed for individual-entity GETs):

- `GET /artists/1` — returns The Persuader
- `GET /releases/1` — returns Stockholm (Svek SK032, 1999)
- `GET /masters/18500` — returns New Soil (Samuel L Session, 2001)
- `GET /labels/5` — returns Svek
- `GET /database/search?q=Stockholm&type=release&per_page=2` — returns
  paginated results including release 1

Responses are captured as JSON fixtures in `tests/fixtures/live_*.json` and
used by the offline test suite.

---

## Running tests

```bash
# Offline only (no token needed)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -m "not live" -q

# Include live smoke tests (requires DISCOGS_TOKEN)
DISCOGS_TOKEN=your_token python -m pytest -m "live" -q
```
