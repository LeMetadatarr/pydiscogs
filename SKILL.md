---
name: pydiscogs
description: Query Discogs releases, artists, and labels in real time or from full monthly catalog dumps, providing accessible music-discovery for users who cannot navigate discogs.com.
---
# pydiscogs — Discogs for agents

## When to use

Use this skill whenever a user asks about music releases, artists, record labels, or
tracklists and cannot (or chooses not to) navigate discogs.com themselves — including
blind users, low-vision users, or anyone relying on a voice-first interface. The
library handles rate-limiting, pagination, and large-catalog streaming so the agent
only needs to call one function and speak the results.

## Install

```bash
pip install pydiscogs
```

## Core operations

### `search(query, *, type, artist, label, genre, style, year, format, per_page, page, token) -> dict`

Single-page search against the live Discogs API (`GET /database/search`).
Returns `{"results": [...], "pagination": {...}}`.
Works unauthenticated; supply `DISCOGS_TOKEN` env var or `token=` kwarg for higher
rate limits (60 req/min vs 25).

```python
import pydiscogs
results = pydiscogs.search("Kind of Blue", type="release", artist="Miles Davis")
for r in results["results"][:3]:
    print(r["id"], r["title"], r.get("year"))
```

Key result fields: `id`, `title`, `type`, `year`, `country`, `format`, `label`,
`genre`, `style`, `uri`.

---

### `search_iter(query, *, type, artist, label, genre, style, year, format, limit, token) -> Iterator[dict]`

Like `search` but walks all pages automatically, yielding one result dict at a time.
Use `limit=` to stop early.

```python
for r in pydiscogs.search_iter(artist="Coltrane", type="release", limit=10):
    print(r["title"], r.get("year"))
```

---

### `get_release(release_id, *, token) -> Release`

Fetch a single release by its Discogs numeric ID. Works unauthenticated.

```python
rel = pydiscogs.get_release(1)          # Stockholm — The Persuader
print(rel.title, rel.year, rel.country)
print([t.title for t in rel.tracklist])
```

Returned `Release` fields: `id`, `master_id`, `title`, `status`, `country`,
`released`, `year`, `artists` (list of `ArtistCredit`), `extra_artists`, `labels`,
`catalog_numbers`, `genres`, `styles`, `formats` (list of `ReleaseFormat`),
`tracklist` (list of `Track`).

---

### `get_master(master_id, *, token) -> Master`

Fetch the canonical (master) version of a release. Returns `Master` with `id`,
`main_release`, `title`, `year`, `artists`, `genres`, `styles`.

```python
master = pydiscogs.get_master(18500)
print(master.title, master.year, [a.name for a in master.artists])
```

---

### `get_artist(artist_id, *, token) -> Artist`

Fetch an artist profile. Returns `Artist` with `id`, `name`, `real_name`,
`profile`, `name_variations`, `aliases`, `members`, `groups`, `urls`.

```python
artist = pydiscogs.get_artist(1)        # The Persuader
print(artist.name, artist.profile[:120])
```

---

### `get_label(label_id, *, token) -> Label`

Fetch a record label. Returns `Label` with `id`, `name`, `profile`, `contact_info`,
`parent_label`, `sublabels`, `urls`.

```python
label = pydiscogs.get_label(5)          # Svek
print(label.name, label.profile[:120])
```

---

### Bulk dump streaming: `list_dumps / latest_dump / download / stream`

For full-catalog work (dataset building, offline search) without per-request API
calls.

```python
# List available monthly dumps
dumps = pydiscogs.list_dumps(entity="releases")
print(dumps[-1].date, dumps[-1].download_url)

# Get the most recent dump for an entity
dump = pydiscogs.latest_dump("artists")

# Stream records without downloading the whole file
for artist in pydiscogs.stream("artists", limit=100):
    print(artist.name)

# Download to disk cache for repeated use (resumable)
path = pydiscogs.download(dump)

# Stream from a local file
for release in pydiscogs.stream_local(path):
    print(release.title, release.year)
```

`stream` and `stream_local` yield typed model objects (`Artist`, `Label`, `Master`,
`Release`). `Dump` dataclass fields: `key`, `entity`, `date`, `filename`,
`download_url`.

---

## Access notes

The live API (`get_*`, `search`, `search_iter`) works without any credentials at
25 requests/minute. A user can raise that limit to 60 req/min by exporting their
own Discogs personal access token:

```bash
export DISCOGS_TOKEN=your_token_here
```

or by passing `token=` directly to any function. Tokens are obtained from
https://www.discogs.com/settings/developers — no payment required.

The bulk dump path (`stream`, `download`) hits `data.discogs.com` directly and
requires no token at all; it streams multi-GB gzip XML without loading it into
memory.

## Speaking the results (accessibility)

- Lead with the essentials a listener needs first: **artist — title — year — format**
  (e.g. "Miles Davis, Kind of Blue, 1959, LP").
- Follow up with genre/style and label if the user asks for more detail.
- For tracklists, read positions and titles in order; offer to continue or skip.
- For "find albums by X" queries, use `search_iter(artist="X", type="release")`
  and speak results one at a time, pausing for confirmation before continuing.
