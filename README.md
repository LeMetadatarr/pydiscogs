# pydiscogs

Streaming Python client for the **Discogs monthly data dumps** — the official,
key-free, CC0 bulk export of the Discogs music database (Artists, Labels,
Masters, Releases).

The dumps are gzip-compressed XML, multiple gigabytes each (the Releases dump is
~10 GB). pydiscogs **stream-parses** them: it inflates and parses the XML
incrementally over HTTP and clears each record as soon as it is yielded, so
memory stays flat and a smoke run reads only the first few KB off the socket —
never the whole file.

## Install

```bash
pip install -e .
pip install -e ".[lxml]"      # optional faster XML
pip install -e ".[dataset]"   # optional HuggingFace datasets
pip install -e ".[test]"      # pytest
```

Requires Python >= 3.8. HTTP goes through `unblock_requests.CloudflareSession`
(the dump index is Cloudflare-fronted).

## Quick start

```python
import pydiscogs

# what dumps are available this year?
for d in pydiscogs.list_dumps():
    print(d.date, d.entity, d.filename)

# stream the first 100 labels — no full download
for label in pydiscogs.stream("labels", limit=100):
    print(label.id, label.name)

# canonical join-id anchor for metadatarr ExternalIds.extra
release = next(pydiscogs.stream("releases", limit=1))
print(pydiscogs.release_to_extra(release))
# {'discogs_release_id': '...', 'discogs_master_id': '...', ...}
```

## Entities & canonical ids

| dump        | model     | canonical id          |
| ----------- | --------- | --------------------- |
| `artists`   | `Artist`  | `discogs_artist_id`   |
| `labels`    | `Label`   | `discogs_label_id`    |
| `masters`   | `Master`  | `discogs_master_id`   |
| `releases`  | `Release` | `discogs_release_id`  |

`discogs_artist_id` / `discogs_release_id` / `discogs_master_id` are the de-facto
join keys across the music-metadata ecosystem.

## Dataset export

```python
import pydiscogs
pydiscogs.export_jsonl("labels", "labels.jsonl", limit=10_000)
```

Four streaming dataset configs (`artists`, `labels`, `masters`, `releases`) — see
[docs/dataset.md](docs/dataset.md).

## Optional supplement: the gated REST API

For per-record live lookups Discogs also offers a REST API at
`https://api.discogs.com` — but that one **requires a token** and is rate
limited. pydiscogs targets the no-key bulk dumps; the REST API is noted only as
an optional supplement.

## Docs

See [docs/](docs/) and runnable [examples/](examples/).

## License

Apache-2.0. The Discogs data itself is CC0.
