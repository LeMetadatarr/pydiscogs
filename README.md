# pydiscogs

pydiscogs is a streaming Python client for the Discogs monthly data dumps. The dumps live at [data.discogs.com](https://data.discogs.com/). They are the official, key-free, CC0 bulk export of the Discogs music database (Artists, Labels, Masters, Releases).

The dumps are gzip-compressed XML, multiple gigabytes each. The Releases dump is about 10 GB. pydiscogs stream-parses them.

It inflates and parses the XML incrementally over HTTP. It clears each record as soon as it yields the record, so memory stays flat. A smoke run reads only the first few KB off the socket, never the whole file.

## Install

```bash
pip install -e .
pip install -e ".[lxml]"      # optional faster XML
pip install -e ".[dataset]"   # optional HuggingFace datasets
pip install -e ".[test]"      # pytest
```

pydiscogs requires Python 3.8 or later. HTTP goes through `unblock_requests.CloudflareSession` (the dump index is Cloudflare-fronted).

## Quick start

```python
import pydiscogs
# what dumps are available this year?
for d in pydiscogs.list_dumps():
    print(d.date, d.entity, d.filename)
# stream the first 100 labels, no full download
for label in pydiscogs.stream("labels", limit=100):
    print(label.id, label.name)
# flat str->str dict of namespaced external IDs, anchor key discogs_id
release = next(pydiscogs.stream("releases", limit=1))
print(pydiscogs.release_to_extra(release))
# {'discogs_release_id': '...', 'discogs_master_id': '...', ...}
```

## Entities and canonical ids

| dump        | model     | canonical id          |
| ----------- | --------- | ---------------------- |
| `artists`   | `Artist`  | `discogs_artist_id`   |
| `labels`    | `Label`   | `discogs_label_id`    |
| `masters`   | `Master`  | `discogs_master_id`   |
| `releases`  | `Release` | `discogs_release_id`  |

`discogs_artist_id`, `discogs_release_id`, and `discogs_master_id` are the de-facto join keys across the music-metadata ecosystem.

## Dataset export

```python
import pydiscogs
pydiscogs.export_jsonl("labels", "labels.jsonl", limit=10_000)
```

pydiscogs exposes four streaming dataset configs: `artists`, `labels`, `masters`, and `releases`. See [docs/dataset.md](docs/dataset.md).

## Optional supplement: the gated REST API

For per-record live lookups, Discogs also offers a REST API at `https://api.discogs.com`. This API requires a token and is rate limited. pydiscogs targets the no-key bulk dumps. The REST API is an optional supplement, documented in [docs/live-api.md](docs/live-api.md).

## Related projects

- [TigreGotico/pymusicbrainz](https://github.com/TigreGotico/pymusicbrainz): a sibling streaming dump client for MusicBrainz, using the same memory-safe streaming and external-id pattern.
- [TigreGotico/pyrateyourmusic](https://github.com/TigreGotico/pyrateyourmusic): a complementary RateYourMusic scraper for community ratings and descriptors.
- [TigreGotico/unblock_requests](https://github.com/TigreGotico/unblock_requests): the HTTP session library pydiscogs uses to reach the Cloudflare-fronted dump index.

## Docs

See [docs/](docs/) and runnable [examples/](examples/).

## Known limitations

Streaming is verified against dump fixtures and has been smoke-tested over HTTP. The Discogs download front rate-limits aggressively (HTTP 429). A full live download may be interrupted. Install `unblock_requests[anon]` (proxy rotation) to retry after a 429. No clean full run has been recorded against the live dumps.

## License

Apache-2.0. The Discogs data itself is CC0.
